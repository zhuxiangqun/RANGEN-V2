"""
KMS 模块 - RANGEN AI 中台的 KMS 集成层

⚠️ 此模块现在是通过 HTTP API 调用独立的 KMS 服务

配置:
    KMS_API_URL: KMS 服务地址，默认 http://localhost:8080

使用方式:
    from src.kms import KMSClient, get_kms_client
    
    # 获取客户端
    client = get_kms_client()
    
    # 查询知识
    results = client.query_knowledge("问题", top_k=5)
    
    # PageIndex 检索
    results = client.pageindex_query("问题")
"""

from .kms_client import KMSClient, get_kms_client, reset_kms_client
from .pageindex_mcp import PageIndexMCPTools, get_pageindex_mcp_tools, reset_pageindex_mcp_tools
from .pageindex_mcp import PageIndexMCPServer
from .pageindex_rag_integration import HybridRetriever, RetrievalMode, get_hybrid_retriever, reset_hybrid_retriever
from .unified_retrieval import UnifiedRetrieval, get_unified_retrieval, reset_unified_retrieval
from .web_crawler import WebCrawler, get_web_crawler, reset_web_crawler

__version__ = "2.0.0"

__all__ = [
    # 客户端
    "KMSClient",
    "get_kms_client",
    "reset_kms_client",
    
    # PageIndex
    "PageIndexMCPTools",
    "get_pageindex_mcp_tools",
    "reset_pageindex_mcp_tools",
    "PageIndexMCPServer",
    
    # 混合检索
    "HybridRetriever",
    "RetrievalMode",
    "get_hybrid_retriever",
    "reset_hybrid_retriever",
    
    # 统一检索
    "UnifiedRetrieval",
    "get_unified_retrieval",
    "reset_unified_retrieval",
    
    # 网页抓取
    "WebCrawler",
    "get_web_crawler",
    "reset_web_crawler",
]
