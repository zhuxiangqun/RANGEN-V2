"""
统一检索系统 (Unified Retrieval System)

⚠️ 此模块现在通过 HTTP API 调用独立的 KMS 服务

结合向量检索和 PageIndex 推理检索的混合检索系统：
- 自动选择最佳检索方式
- 向量检索: 快速、适合语义模糊匹配
- PageIndex: 精准、适合结构化文档、可解释

使用方式:
    from src.kms.unified_retrieval import UnifiedRetrieval
    
    retrieval = UnifiedRetrieval()
    
    # 自动模式
    results = retrieval.search("问题", mode="auto")
    
    # 指定模式
    results = retrieval.search("问题", mode="hybrid")
"""

import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from .kms_client import KMSClient, get_kms_client

logger = logging.getLogger(__name__)


class RetrievalMode(Enum):
    """检索模式"""
    VECTOR = "vector"           # 仅向量
    PAGEINDEX = "pageindex"     # 仅 PageIndex
    HYBRID = "hybrid"          # 混合
    AUTO = "auto"              # 自动选择


@dataclass
class SearchResult:
    """统一搜索结果"""
    content: str
    score: float
    source: str  # "vector" | "pageindex"
    document: Optional[str] = None
    page_ref: Optional[str] = None
    node_id: Optional[str] = None
    chunk_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class UnifiedRetrieval:
    """
    统一检索系统
    
    ⚠️ 现在通过 KMS API 调用独立服务
    """
    
    def __init__(
        self,
        kms_client: Optional[KMSClient] = None,
        api_url: Optional[str] = None,
        default_mode: RetrievalMode = RetrievalMode.HYBRID
    ):
        """
        初始化统一检索系统
        
        Args:
            kms_client: KMS 客户端实例
            api_url: KMS API 地址
            default_mode: 默认检索模式
        """
        if kms_client:
            self.client = kms_client
        elif api_url:
            self.client = KMSClient(api_url=api_url)
        else:
            self.client = get_kms_client()
        
        self.default_mode = default_mode
    
    def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        document_path: Optional[str] = None
    ) -> List[SearchResult]:
        """
        搜索
        
        Args:
            query: 查询文本
            mode: 检索模式 (vector/pageindex/hybrid/auto)
            top_k: 返回结果数量
            document_path: 指定文档路径
        """
        try:
            if mode == "vector":
                result = self.client.vector_search(query=query, top_k=top_k)
            elif mode == "pageindex":
                result = self.client.pageindex_query(
                    query=query,
                    document_path=document_path,
                    mode="pageindex_only",
                    top_k=top_k
                )
            elif mode == "hybrid":
                result = self.client.hybrid_search(query=query, top_k=top_k)
            else:  # auto
                result = self.client.pageindex_query(
                    query=query,
                    document_path=document_path,
                    mode="auto",
                    top_k=top_k
                )
            
            results = result.get("results", [])
            
            return [
                SearchResult(
                    content=r.get("content", ""),
                    score=r.get("relevance_score", r.get("score", 0.0)),
                    source=r.get("source", mode),
                    document=r.get("document"),
                    page_ref=r.get("page_reference"),
                    node_id=r.get("node_id"),
                    chunk_id=r.get("chunk_id"),
                    metadata=r
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def search_by_document(
        self,
        query: str,
        document_path: str,
        mode: str = "auto",
        top_k: int = 10
    ) -> List[SearchResult]:
        """在指定文档中搜索"""
        return self.search(
            query=query,
            mode=mode,
            top_k=top_k,
            document_path=document_path
        )
    
    def is_available(self) -> bool:
        """检查 KMS 服务是否可用"""
        return self.client.is_available()


# ==================== 便捷函数 ====================

_unified_retrieval: Optional[UnifiedRetrieval] = None


def get_unified_retrieval(
    kms_client: Optional[KMSClient] = None,
    api_url: Optional[str] = None
) -> UnifiedRetrieval:
    """获取统一检索系统实例"""
    global _unified_retrieval
    if _unified_retrieval is None:
        _unified_retrieval = UnifiedRetrieval(kms_client=kms_client, api_url=api_url)
    return _unified_retrieval


def reset_unified_retrieval():
    """重置统一检索系统"""
    global _unified_retrieval
    _unified_retrieval = None
