#!/usr/bin/env python3
"""
统一检索系统 (Unified Retrieval System)

结合向量检索和PageIndex推理检索的混合检索系统
- 自动选择最佳检索方式
- 向量检索: 快速、适合语义模糊匹配
- PageIndex: 精准、适合结构化文档、可解释

使用方式:
    from src.kms.unified_retrieval import UnifiedRetrieval
    
    retrieval = UnifiedRetrieval()
    
    # 自动模式
    results = await retrieval.search("问题", mode="auto")
    
    # 指定模式
    results = await retrieval.search("问题", mode="hybrid")
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class RetrievalMode(Enum):
    """检索模式"""
    VECTOR = "vector"           # 仅向量
    PAGEINDEX = "pageindex"     # 仅PageIndex
    HYBRID = "hybrid"          # 混合
    AUTO = "auto"              # 自动选择


@dataclass
class SearchResult:
    """统一搜索结果"""
    content: str
    score: float
    source: str  # "vector" | "pageindex"
    document: Optional[str] = None
    page_ref: Optional[str] = None  # 页码引用
    node_id: Optional[str] = None   # PageIndex节点ID
    chunk_id: Optional[str] = None   # 向量库chunk ID
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "document": self.document,
            "page_ref": self.page_ref,
            "node_id": self.node_id,
            "chunk_id": self.chunk_id,
            "metadata": self.metadata
        }


@dataclass
class SearchOptions:
    """搜索选项"""
    mode: RetrievalMode = RetrievalMode.AUTO
    top_k: int = 5
    min_score: float = 0.3
    document_path: Optional[str] = None  # 指定文档
    document_type: Optional[str] = None  # 文档类型: "structured" | "general"
    use_reasoning: bool = True  # PageIndex是否使用推理
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SearchOptions':
        if isinstance(data.get("mode"), str):
            data["mode"] = RetrievalMode(data["mode"])
        return cls(**data)


class UnifiedRetrieval:
    """
    统一检索系统
    
    整合向量检索和PageIndex，提供智能选择
    """
    
    def __init__(
        self,
        vector_service=None,
        pageindex_config: Optional[Dict] = None,
        llm_client=None
    ):
        """初始化"""
        self.vector_service = vector_service
        self.pageindex = None
        self.pageindex_config = pageindex_config or {}
        self.llm_client = llm_client
        
        # 索引状态
        self._vector_ready = False
        self._pageindex_ready = False
        
        # 统计信息
        self.stats = {
            "vector_queries": 0,
            "pageindex_queries": 0,
            "hybrid_queries": 0,
            "auto_selections": {"vector": 0, "pageindex": 0}
        }
        
        # 🚀 KMS 深度集成：跟踪已索引的文档
        self._indexed_documents: Dict[str, List[str]] = {
            "vector": [],
            "pageindex": []
        }
    
    async def initialize(self):
        """初始化服务"""
        # 检查向量服务
        if self.vector_service:
            try:
                self._vector_ready = True
                logger.info("✅ Vector service ready")
            except Exception as e:
                logger.warning(f"⚠️ Vector service unavailable: {e}")
        
        # 初始化PageIndex
        try:
            from src.kms.pageindex import PageIndex, PageIndexConfig
            
            config = PageIndexConfig(
                index_storage_path=self.pageindex_config.get(
                    "index_storage_path",
                    "./data/pageindex"
                ),
                model=self.pageindex_config.get("model", "deepseek-chat"),
                max_pages_per_node=self.pageindex_config.get("max_pages_per_node", 10)
            )
            
            self.pageindex = PageIndex(config, llm_client=self.llm_client)
            
            # 加载所有已存在的索引
            loaded = await self.pageindex.load_all_indexes()
            logger.info(f"Loaded {loaded} indexes")
            
            self._pageindex_ready = True
            logger.info("✅ PageIndex ready")
        except Exception as e:
            logger.warning(f"⚠️ PageIndex initialization failed: {e}")
            self._pageindex_ready = False
    
    async def search(
        self,
        query: str,
        mode: str = "auto",
        top_k: int = 5,
        options: Optional[SearchOptions] = None
    ) -> List[SearchResult]:
        """搜索接口"""
        if options:
            mode = options.mode.value if isinstance(options.mode, RetrievalMode) else options.mode
            top_k = options.top_k or top_k
        
        results = []
        
        # 根据模式选择检索方式
        if mode == "auto":
            # 自动选择：先尝试两种方式，比较结果
            vector_results, pageindex_results = await asyncio.gather(
                self._search_vector(query, top_k),
                self._search_pageindex(query, top_k)
            )
            
            # 统计自动选择
            self.stats["auto_selections"]["vector"] += 1
            self.stats["auto_selections"]["pageindex"] += 1
            
            # 合并结果
            results = self._merge_results(vector_results, pageindex_results)
            self.stats["hybrid_queries"] += 1
            
        elif mode == "vector":
            results = await self._search_vector(query, top_k)
            self.stats["vector_queries"] += 1
            
        elif mode == "pageindex":
            results = await self._search_pageindex(query, top_k)
            self.stats["pageindex_queries"] += 1
            
        elif mode == "hybrid":
            # 混合模式：同时执行，合并结果
            vector_results, pageindex_results = await asyncio.gather(
                self._search_vector(query, top_k),
                self._search_pageindex(query, top_k)
            )
            results = self._merge_results(vector_results, pageindex_results)
            self.stats["hybrid_queries"] += 1
        
        return results[:top_k]
    
    async def _search_vector(self, query: str, top_k: int) -> List[SearchResult]:
        """向量检索"""
        results = []
        
        if not self._vector_ready or not self.vector_service:
            return results
        
        try:
            # 调用向量服务
            if hasattr(self.vector_service, 'search'):
                vector_results = await self.vector_service.search(query, top_k=top_k)
            elif hasattr(self.vector_service, 'retrieve'):
                vector_results = await self.vector_service.retrieve(query, top_k=top_k)
            else:
                logger.warning("Vector service does not have search or retrieve method")
                return results
            
            # 转换为统一格式
            for r in vector_results:
                results.append(SearchResult(
                    content=r.get("content", str(r)),
                    score=r.get("score", 0.0),
                    source="vector",
                    document=r.get("document"),
                    chunk_id=r.get("chunk_id"),
                    metadata=r
                ))
                
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
        
        return results
    
    async def _search_pageindex(self, query: str, top_k: int) -> List[SearchResult]:
        """PageIndex检索"""
        results = []
        
        if not self._pageindex_ready or not self.pageindex:
            return results
        
        try:
            # 调用PageIndex
            pageindex_results = await self.pageindex.search(
                query=query,
                top_k=top_k
            )
            
            # 转换为统一格式
            for r in pageindex_results:
                results.append(SearchResult(
                    content=r.get("content", str(r)),
                    score=r.get("score", 0.0),
                    source="pageindex",
                    document=r.get("document"),
                    page_ref=r.get("page_ref"),
                    node_id=r.get("node_id"),
                    metadata=r
                ))
                
        except Exception as e:
            logger.error(f"PageIndex search failed: {e}")
        
        return results
    
    def _merge_results(
        self,
        vector_results: List[SearchResult],
        pageindex_results: List[SearchResult]
    ) -> List[SearchResult]:
        """合并搜索结果"""
        # 简单合并：按分数排序
        all_results = vector_results + pageindex_results
        all_results.sort(key=lambda x: x.score, reverse=True)
        return all_results
    
    async def list_indexed_documents(self) -> Dict[str, List[str]]:
        """列出已索引的文档"""
        docs = {"vector": [], "pageindex": []}
        
        if self._pageindex_ready and self.pageindex:
            try:
                docs["pageindex"] = self.pageindex.get_indexed_documents()
            except Exception as e:
                logger.warning(f"获取 PageIndex 文档列表失败: {e}")
        
        # 🚀 KMS 深度集成：获取向量库的文档列表
        if self._vector_ready and self.vector_service:
            try:
                # 尝试从向量服务获取文档列表
                if hasattr(self.vector_service, 'get_indexed_documents'):
                    docs["vector"] = self.vector_service.get_indexed_documents()
                elif hasattr(self.vector_service, 'list_documents'):
                    docs["vector"] = self.vector_service.list_documents()
                else:
                    # 使用内部跟踪的文档列表
                    docs["vector"] = self._indexed_documents.get("vector", [])
            except Exception as e:
                logger.warning(f"获取向量库文档列表失败: {e}")
        else:
            # 使用内部跟踪的文档列表
            docs["vector"] = self._indexed_documents.get("vector", [])
        
        return docs
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "services": {
                "vector": self._vector_ready,
                "pageindex": self._pageindex_ready
            },
            "indexed_documents": {
                "vector_count": len(self._indexed_documents.get("vector", [])),
                "pageindex_count": len(self._indexed_documents.get("pageindex", []))
            }
        }


# ==================== 便捷函数 ====================

_unified_retrieval: Optional[UnifiedRetrieval] = None


def get_unified_retrieval(
    vector_service=None,
    pageindex_config: Optional[Dict] = None
) -> UnifiedRetrieval:
    """获取统一检索实例"""
    global _unified_retrieval
    if _unified_retrieval is None:
        _unified_retrieval = UnifiedRetrieval(
            vector_service=vector_service,
            pageindex_config=pageindex_config
        )
    return _unified_retrieval
