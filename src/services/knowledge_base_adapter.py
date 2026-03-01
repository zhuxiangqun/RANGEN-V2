#!/usr/bin/env python3
"""
知识库适配器
将核心系统对旧知识库模块的调用转换为对知识库管理系统的调用
保持接口兼容性，内部使用知识库管理系统（第四系统）
"""

from typing import List, Dict, Any, Optional
import asyncio
from ..utils.research_logger import log_info, log_warning, log_error

try:
    from knowledge_management_system.api.service_interface import get_knowledge_service
    KMS_AVAILABLE = True
    _get_knowledge_service_func = get_knowledge_service  # 保存引用
except ImportError:
    KMS_AVAILABLE = False
    _get_knowledge_service_func = None
    log_warning("知识库管理系统不可用，适配器将无法工作")


class KnowledgeBaseAdapter:
    """知识库适配器 - 兼容旧接口，内部使用知识库管理系统"""
    
    def __init__(self):
        """初始化适配器"""
        if not KMS_AVAILABLE or _get_knowledge_service_func is None:
            self.kms_service = None
            log_warning("知识库管理系统不可用，适配器功能受限")
        else:
            try:
                self.kms_service = _get_knowledge_service_func()
                log_info("知识库适配器初始化完成（使用知识库管理系统）")
            except Exception as e:
                self.kms_service = None
                log_error("knowledge_base_adapter", f"知识库管理系统初始化失败: {e}")
    
    def is_available(self) -> bool:
        """检查知识库管理系统是否可用"""
        return self.kms_service is not None
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        搜索知识（兼容旧接口）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            similarity_threshold: 相似度阈值
        
        Returns:
            搜索结果列表（转换为旧格式）
        """
        if not self.is_available():
            log_warning("知识库管理系统不可用，返回空结果")
            return []
        
        try:
            # 调用知识库管理系统
            if not self.kms_service:
                return []
            # 🚀 启用rerank，在知识库管理系统中完成
            results = self.kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=top_k,
                similarity_threshold=similarity_threshold,
                use_rerank=True  # 🚀 在知识库管理系统中完成rerank
            )
            
            # 转换为旧格式（兼容enhanced_faiss_memory的返回格式）
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'content': result.get('content', ''),
                    'source': result.get('metadata', {}).get('source', 'knowledge_management_system'),
                    'score': result.get('similarity_score', 0.0),
                    'similarity': result.get('similarity_score', 0.0),
                    'confidence': result.get('similarity_score', 0.0),
                    'metadata': result.get('metadata', {}),
                    'knowledge_id': result.get('knowledge_id', ''),
                    'rank': result.get('rank', 0)
                })
            
            return formatted_results
            
        except Exception as e:
            log_error("knowledge_base_adapter", f"知识库搜索失败: {e}")
            return []
    
    async def get_instance(self):
        """获取实例（兼容FAISSService接口）"""
        return self
    
    def search_sync(
        self, 
        query: str, 
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        同步搜索（兼容旧接口）
        
        Args:
            query: 查询文本
            top_k: 返回数量
        
        Returns:
            搜索结果列表
        """
        if not self.is_available():
            return []
        
        try:
            # 同步调用知识库管理系统
            if not self.kms_service:
                return []
            # 🚀 启用rerank，在知识库管理系统中完成
            results = self.kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=top_k,
                use_rerank=True  # 🚀 在知识库管理系统中完成rerank
            )
            
            # 转换为旧格式
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'content': result.get('content', ''),
                    'metadata': result.get('metadata', {}),
                    'score': result.get('similarity_score', 0.0)
                })
            
            return formatted_results
            
        except Exception as e:
            log_error("knowledge_base_adapter", f"知识库同步搜索失败: {e}")
            return []
    
    async def ensure_index_ready(self):
        """确保索引就绪（兼容旧接口）"""
        if not self.is_available():
            return False
        
        try:
            # 检查知识库管理系统状态
            if not self.kms_service:
                return False
            stats = self.kms_service.get_statistics()
            vector_index_size = stats.get('vector_index_size', 0)
            log_info(f"知识库索引就绪，大小: {vector_index_size}")
            return vector_index_size > 0
        except Exception as e:
            log_error("knowledge_base_adapter", f"检查索引状态失败: {e}")
            return False

