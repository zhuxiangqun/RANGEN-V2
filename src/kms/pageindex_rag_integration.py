"""
PageIndex与现有RAG系统的集成

混合检索：向量检索 + PageIndex推理检索
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.kms.pageindex import (
    PageIndex, 
    PageIndexConfig, 
    RetrievalResult as PageIndexResult,
    TreeNode
)

logger = logging.getLogger(__name__)


class RetrievalMode(Enum):
    """检索模式"""
    VECTOR_ONLY = "vector_only"           # 仅向量
    PAGEINDEX_ONLY = "pageindex_only"      # 仅PageIndex
    HYBRID = "hybrid"                      # 混合模式
    AUTO = "auto"                          # 自动选择


@dataclass
class HybridRetrievalResult:
    """混合检索结果"""
    content: str
    source: str  # "vector" or "pageindex"
    relevance_score: float
    page_reference: Optional[str] = None
    node_id: Optional[str] = None
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """
    混合检索器
    
    结合向量检索和PageIndex推理检索的优势：
    - 向量检索：快速、适合语义相似
    - PageIndex：精准、适合结构化文档
    """
    
    def __init__(
        self,
        pageindex: Optional[PageIndex] = None,
        vector_service=None,  # 现有向量服务
        mode: RetrievalMode = RetrievalMode.HYBRID
    ):
        self.pageindex = pageindex
        self.vector_service = vector_service
        self.mode = mode
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        mode: Optional[RetrievalMode] = None,
        use_reasoning: bool = True,
        document_path: Optional[str] = None
    ) -> List[HybridRetrievalResult]:
        """
        混合检索
        
        Args:
            query: 查询
            top_k: 返回数量
            mode: 检索模式（可选，覆盖默认）
            use_reasoning: 是否使用PageIndex推理
            document_path: 指定文档路径
        """
        mode = mode or self.mode
        
        if mode == RetrievalMode.VECTOR_ONLY:
            return await self._vector_retrieve(query, top_k)
        
        elif mode == RetrievalMode.PAGEINDEX_ONLY:
            return await self._pageindex_retrieve(query, top_k, use_reasoning, document_path)
        
        elif mode == RetrievalMode.HYBRID:
            return await self._hybrid_retrieve(query, top_k, use_reasoning, document_path)
        
        elif mode == RetrievalMode.AUTO:
            return await self._auto_retrieve(query, top_k, document_path)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    async def _vector_retrieve(
        self,
        query: str,
        top_k: int
    ) -> List[HybridRetrievalResult]:
        """纯向量检索"""
        if not self.vector_service:
            logger.warning("Vector service not available")
            return []
        
        try:
            results = await self.vector_service.query(query, top_k=top_k)
            
            return [
                HybridRetrievalResult(
                    content=r.get("content", ""),
                    source="vector",
                    relevance_score=r.get("score", 0.0),
                    metadata=r
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Vector retrieval failed: {e}")
            return []
    
    async def _pageindex_retrieve(
        self,
        query: str,
        top_k: int,
        use_reasoning: bool,
        document_path: Optional[str]
    ) -> List[HybridRetrievalResult]:
        """纯PageIndex检索"""
        if not self.pageindex:
            logger.warning("PageIndex not initialized")
            return []
        
        try:
            results = await self.pageindex.retrieve(
                query=query,
                document_path=document_path,
                top_k=top_k
            )
            
            return [
                HybridRetrievalResult(
                    content=r.content,
                    source="pageindex",
                    relevance_score=r.relevance_score,
                    page_reference=r.page_range,
                    node_id=r.node_id,
                    reasoning=r.reasoning,
                    metadata={"title": r.title}
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"PageIndex retrieval failed: {e}")
            return []
    
    async def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        use_reasoning: bool,
        document_path: Optional[str]
    ) -> List[HybridRetrievalResult]:
        """混合检索"""
        all_results = []
        
        # 并行执行两种检索
        vector_task = self._vector_retrieve(query, top_k) if self.vector_service else None
        pageindex_task = self._pageindex_retrieve(query, top_k, use_reasoning, document_path)
        
        import asyncio
        
        if vector_task:
            vector_results, pageindex_results = await asyncio.gather(
                vector_task, pageindex_task, return_exceptions=True
            )
            
            # 处理异常
            if isinstance(vector_results, Exception):
                logger.error(f"Vector retrieval error: {vector_results}")
                vector_results = []
            
            if isinstance(pageindex_results, Exception):
                logger.error(f"PageIndex retrieval error: {pageindex_results}")
                pageindex_results = []
            
            all_results = vector_results + pageindex_results
        else:
            all_results = await pageindex_task
        
        # 合并去重并排序
        return self._merge_and_rank(all_results, top_k)
    
    async def _auto_retrieve(
        self,
        query: str,
        top_k: int,
        document_path: Optional[str]
    ) -> List[HybridRetrievalResult]:
        """
        自动选择检索模式
        
        规则：
        - 有指定文档 → 使用PageIndex
        - 查询涉及数字/具体信息 → 使用PageIndex
        - 其他 → 使用混合模式
        """
        # 检测是否涉及具体信息（如数字、金额、日期）
        import re
        has_numbers = bool(re.search(r'\d+', query))
        
        if document_path:
            # 有指定文档，优先PageIndex
            return await self._pageindex_retrieve(query, top_k, True, document_path)
        
        elif has_numbers:
            # 涉及数字，可能需要精确查找
            results = await self._pageindex_retrieve(query, top_k, True, None)
            if results:
                return results
            # 回退到向量
            return await self._vector_retrieve(query, top_k)
        
        else:
            # 默认使用混合
            return await self._hybrid_retrieve(query, top_k, True, None)
    
    def _merge_and_rank(
        self,
        results: List[HybridRetrievalResult],
        top_k: int
    ) -> List[HybridRetrievalResult]:
        """合并结果并排序"""
        
        # 按相关性排序
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # 去重（基于内容相似）
        unique_results = []
        seen_content = set()
        
        for r in results:
            # 简单去重：取前100个字符的hash
            content_hash = hash(r.content[:100])
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(r)
        
        return unique_results[:top_k]


class PageIndexRAGIntegration:
    """
    PageIndex与RANGEN RAG系统的完整集成
    
    提供统一的接口，同时支持向量和PageIndex检索
    """
    
    def __init__(
        self,
        pageindex: Optional[PageIndex] = None,
        vector_service=None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or {}
        
        # 初始化PageIndex
        if pageindex:
            self.pageindex = pageindex
        else:
            pageindex_config = PageIndexConfig(
                index_storage_path=self.config.get(
                    "index_storage_path", 
                    "./data/pageindex"
                ),
                model=self.config.get("model", "deepseek-chat"),
                max_pages_per_node=self.config.get("max_pages_per_node", 10)
            )
            self.pageindex = PageIndex(pageindex_config)
        
        # 初始化混合检索器
        self.retriever = HybridRetriever(
            pageindex=self.pageindex,
            vector_service=vector_service,
            mode=RetrievalMode(
                self.config.get("retrieval_mode", "hybrid")
            )
        )
    
    async def index_document(
        self,
        document_path: str,
        document_description: str = ""
    ) -> TreeNode:
        """
        为文档建立索引
        
        同时创建向量索引和PageIndex树索引
        """
        # PageIndex索引
        tree = await self.pageindex.index_document(
            document_path=document_path,
            document_description=document_description
        )
        
        # 🚀 KMS 深度集成：同时创建向量索引
        if self.retriever.vector_service:
            try:
                if hasattr(self.retriever.vector_service, 'index_document'):
                    await self.retriever.vector_service.index_document(document_path)
                    logger.info(f"✅ 向量索引创建成功: {document_path}")
                elif hasattr(self.retriever.vector_service, 'add_documents'):
                    # 如果是批量添加文档的方式
                    await self.retriever.vector_service.add_documents([document_path])
                    logger.info(f"✅ 向量索引添加成功: {document_path}")
            except Exception as e:
                logger.warning(f"⚠️ 向量索引创建失败: {e}")
        
        return tree
        tree = await self.pageindex.index_document(
            document_path=document_path,
            document_description=document_description
        )
        
        # TODO: 同时创建向量索引
        # if self.vector_service:
        #     await self.vector_service.index_document(document_path)
        
        return tree
    
    async def query(
        self,
        query: str,
        mode: str = "auto",
        top_k: int = 5,
        document_path: Optional[str] = None
    ) -> List[HybridRetrievalResult]:
        """
        查询
        
        统一的查询接口
        """
        return await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            mode=RetrievalMode(mode),
            document_path=document_path
        )
    
    def get_indexed_documents(self) -> List[str]:
        """获取已索引的文档"""
        return self.pageindex.get_indexed_documents()


# ==================== 便捷函数 ====================

_integration: Optional[PageIndexRAGIntegration] = None


def get_pageindex_rag_integration(
    pageindex: Optional[PageIndex] = None,
    vector_service = None,
    config: Optional[Dict[str, Any]] = None
) -> PageIndexRAGIntegration:
    """获取集成实例"""
    global _integration
    if _integration is None:
        _integration = PageIndexRAGIntegration(
            pageindex=pageindex,
            vector_service=vector_service,
            config=config
        )
    return _integration
