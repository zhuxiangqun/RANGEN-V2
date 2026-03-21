"""
PageIndex 与现有 RAG 系统的集成

混合检索：向量检索 + PageIndex 推理检索

⚠️ 此模块现在通过 HTTP API 调用独立的 KMS 服务
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .kms_client import KMSClient, get_kms_client

logger = logging.getLogger(__name__)


class RetrievalMode(Enum):
    """检索模式"""
    VECTOR_ONLY = "vector_only"           # 仅向量
    PAGEINDEX_ONLY = "pageindex_only"      # 仅 PageIndex
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
    
    结合向量检索和 PageIndex 推理检索的优势
    ⚠️ 现在通过 KMS API 调用独立服务
    """
    
    def __init__(
        self,
        kms_client: Optional[KMSClient] = None,
        api_url: Optional[str] = None,
        mode: RetrievalMode = RetrievalMode.HYBRID
    ):
        """
        初始化混合检索器
        
        Args:
            kms_client: KMS 客户端实例
            api_url: KMS API 地址
            mode: 默认检索模式
        """
        if kms_client:
            self.client = kms_client
        elif api_url:
            self.client = KMSClient(api_url=api_url)
        else:
            self.client = get_kms_client()
        
        self.mode = mode
    
    def retrieve(
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
            use_reasoning: 是否使用 PageIndex 推理
            document_path: 指定文档路径
        """
        mode = mode or self.mode
        
        if mode == RetrievalMode.VECTOR_ONLY:
            return self._vector_retrieve(query, top_k)
        
        elif mode == RetrievalMode.PAGEINDEX_ONLY:
            return self._pageindex_retrieve(query, top_k, use_reasoning, document_path)
        
        elif mode == RetrievalMode.HYBRID:
            return self._hybrid_retrieve(query, top_k, use_reasoning, document_path)
        
        elif mode == RetrievalMode.AUTO:
            return self._auto_retrieve(query, top_k, document_path)
        
        else:
            raise ValueError(f"Unknown mode: {mode}")
    
    def _vector_retrieve(
        self,
        query: str,
        top_k: int
    ) -> List[HybridRetrievalResult]:
        """向量检索"""
        try:
            result = self.client.vector_search(query=query, top_k=top_k)
            results = result.get("results", [])
            
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
    
    def _pageindex_retrieve(
        self,
        query: str,
        top_k: int,
        use_reasoning: bool,
        document_path: Optional[str]
    ) -> List[HybridRetrievalResult]:
        """PageIndex 检索"""
        try:
            mode = "pageindex_only" if use_reasoning else "vector_only"
            result = self.client.pageindex_query(
                query=query,
                document_path=document_path,
                mode=mode,
                top_k=top_k
            )
            
            results = result.get("results", [])
            
            return [
                HybridRetrievalResult(
                    content=r.get("content", ""),
                    source="pageindex",
                    relevance_score=r.get("relevance_score", 0.0),
                    page_reference=r.get("page_reference"),
                    node_id=r.get("node_id"),
                    reasoning=r.get("reasoning"),
                    metadata=r
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"PageIndex retrieval failed: {e}")
            return []
    
    def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        use_reasoning: bool,
        document_path: Optional[str]
    ) -> List[HybridRetrievalResult]:
        """混合检索"""
        try:
            result = self.client.hybrid_search(
                query=query,
                top_k=top_k
            )
            
            results = result.get("results", [])
            
            return [
                HybridRetrievalResult(
                    content=r.get("content", ""),
                    source=r.get("source", "hybrid"),
                    relevance_score=r.get("relevalence_score", 0.0),
                    page_reference=r.get("page_reference"),
                    node_id=r.get("node_id"),
                    reasoning=r.get("reasoning"),
                    metadata=r
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Hybrid retrieval failed: {e}")
            return []
    
    def _auto_retrieve(
        self,
        query: str,
        top_k: int,
        document_path: Optional[str]
    ) -> List[HybridRetrievalResult]:
        """自动选择检索模式"""
        try:
            result = self.client.pageindex_query(
                query=query,
                document_path=document_path,
                mode="auto",
                top_k=top_k
            )
            
            results = result.get("results", [])
            
            return [
                HybridRetrievalResult(
                    content=r.get("content", ""),
                    source=r.get("source", "auto"),
                    relevance_score=r.get("relevance_score", 0.0),
                    page_reference=r.get("page_reference"),
                    node_id=r.get("node_id"),
                    reasoning=r.get("reasoning"),
                    metadata=r
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Auto retrieval failed: {e}")
            return []
    
    def is_available(self) -> bool:
        """检查 KMS 服务是否可用"""
        return self.client.is_available()


# ==================== 便捷函数 ====================

_hybrid_retriever: Optional[HybridRetriever] = None


def get_hybrid_retriever(
    kms_client: Optional[KMSClient] = None,
    api_url: Optional[str] = None,
    mode: RetrievalMode = RetrievalMode.HYBRID
) -> HybridRetriever:
    """获取混合检索器实例"""
    global _hybrid_retriever
    if _hybrid_retriever is None:
        _hybrid_retriever = HybridRetriever(kms_client=kms_client, api_url=api_url, mode=mode)
    return _hybrid_retriever


def reset_hybrid_retriever():
    """重置混合检索器"""
    global _hybrid_retriever
    _hybrid_retriever = None
