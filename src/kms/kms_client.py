"""
KMS API Client

KMS（知识管理系统）API客户端
用于 RANGEN AI 中台调用独立的 KMS 服务

配置:
    KMS_API_URL: KMS服务地址，默认 http://localhost:8080
"""

import os
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_KMS_API_URL = os.environ.get("KMS_API_URL", "http://localhost:8080")


class KMSClient:
    """
    KMS API 客户端
    
    通过 HTTP API 调用独立的 KMS 服务
    """
    
    def __init__(
        self,
        api_url: str = DEFAULT_KMS_API_URL,
        timeout: int = 30,
        api_key: Optional[str] = None
    ):
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key or os.environ.get("KMS_API_KEY")
        
        # 验证连接
        if not self._check_connection():
            logger.warning(f"KMS service not available at {self.api_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _check_connection(self) -> bool:
        """检查 KMS 服务连接"""
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """检查 KMS 是否可用"""
        return self._check_connection()
    
    # ==================== 知识管理 ====================
    
    def import_knowledge(
        self,
        data: Any,
        modality: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        导入知识
        
        Args:
            data: 知识数据
            modality: 模态类型 (text/image/audio/video)
            metadata: 元数据
        """
        response = requests.post(
            f"{self.api_url}/api/v1/knowledge/import",
            json={
                "data": data,
                "modality": modality,
                "metadata": metadata or {}
            },
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def query_knowledge(
        self,
        query: str,
        modality: str = "text",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        查询知识
        
        Args:
            query: 查询文本
            modality: 模态类型
            top_k: 返回结果数量
        """
        response = requests.get(
            f"{self.api_url}/api/v1/knowledge/query",
            params={
                "q": query,
                "modality": modality,
                "top_k": top_k
            },
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def delete_knowledge(self, knowledge_id: str) -> Dict[str, Any]:
        """删除知识"""
        response = requests.delete(
            f"{self.api_url}/api/v1/knowledge/{knowledge_id}",
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== PageIndex 功能 ====================
    
    def pageindex_index_document(
        self,
        document_path: str,
        document_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        索引文档
        
        Args:
            document_path: 文档路径
            document_description: 文档描述
        """
        response = requests.post(
            f"{self.api_url}/api/v1/pageindex/index",
            json={
                "document_path": document_path,
                "document_description": document_description
            },
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def pageindex_query(
        self,
        query: str,
        document_path: Optional[str] = None,
        mode: str = "auto",
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        PageIndex 查询
        
        Args:
            query: 查询文本
            document_path: 指定文档路径
            mode: 检索模式 (vector_only/pageindex_only/hybrid/auto)
            top_k: 返回结果数量
        """
        response = requests.post(
            f"{self.api_url}/api/v1/pageindex/query",
            json={
                "query": query,
                "document_path": document_path,
                "mode": mode,
                "top_k": top_k
            },
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def pageindex_list_documents(self) -> Dict[str, Any]:
        """列出已索引文档"""
        response = requests.get(
            f"{self.api_url}/api/v1/pageindex/documents",
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def pageindex_get_tree(self, document_path: str) -> Dict[str, Any]:
        """获取文档树结构"""
        response = requests.get(
            f"{self.api_url}/api/v1/pageindex/tree",
            params={"document_path": document_path},
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== 向量检索 ====================
    
    def vector_search(
        self,
        query: str,
        collection: str = "default",
        top_k: int = 10
    ) -> Dict[str, Any]:
        """向量检索"""
        response = requests.post(
            f"{self.api_url}/api/v1/vector/search",
            json={
                "query": query,
                "collection": collection,
                "top_k": top_k
            },
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    # ==================== 混合检索 ====================
    
    def hybrid_search(
        self,
        query: str,
        vector_weight: float = 0.5,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """混合检索"""
        response = requests.post(
            f"{self.api_url}/api/v1/search/hybrid",
            json={
                "query": query,
                "vector_weight": vector_weight,
                "top_k": top_k
            },
            headers=self._get_headers(),
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()


# ==================== 全局客户端 ====================

_kms_client: Optional[KMSClient] = None


def get_kms_client() -> KMSClient:
    """获取 KMS 客户端单例"""
    global _kms_client
    if _kms_client is None:
        _kms_client = KMSClient()
    return _kms_client


def reset_kms_client():
    """重置 KMS 客户端"""
    global _kms_client
    _kms_client = None
