#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KnowledgeRetrievalAgent → RAGExpert 迁移适配器

将 KnowledgeRetrievalAgent 的调用适配到 RAGExpert，实现平滑迁移。
注意：RAGExpert包含知识检索和答案生成，而KnowledgeRetrievalAgent只做知识检索。
适配器将只使用RAGExpert的知识检索部分。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.rag_agent import RAGExpert
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class KnowledgeRetrievalAgentAdapter(MigrationAdapter):
    """KnowledgeRetrievalAgent → RAGExpert 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="KnowledgeRetrievalAgent",
            target_agent_name="RAGExpert"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（RAGExpert）"""
        return RAGExpert()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        KnowledgeRetrievalAgent 参数格式:
        {
            'query': str,  # 必需
            'type': str,  # 可选，默认"knowledge_retrieval"
            'max_results': int,  # 可选
            'threshold': float,  # 可选
            ...
        }
        
        RAGExpert 参数格式:
        {
            'query': str,  # 必需
            'type': str,  # 可选，默认为"rag"
            'use_cache': bool,  # 可选，默认为True
            'use_parallel': bool,  # 可选，默认为True
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        query = old_context.get("query", "")
        max_results = old_context.get("max_results")
        threshold = old_context.get("threshold")
        
        # 转换参数格式
        adapted.update({
            "query": query,
            # RAGExpert的参数
            "type": old_context.get("type", "rag"),  # 保持type，但默认为"rag"
            "use_cache": old_context.get("use_cache", True),
            "use_parallel": old_context.get("use_parallel", True),
            # 保留原始参数供参考
            "max_results": max_results,
            "threshold": threshold,
            # 标记只做知识检索（不生成答案）
            "_knowledge_retrieval_only": True,
        })
        
        # 调试日志：确保query不为空
        if not query:
            logger.warning(f"⚠️ 适配器警告: query为空，RAGExpert可能会失败")
        else:
            logger.debug(f"✅ 适配器: query已传递，长度={len(query)}")
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "query_length": len(query),
            "max_results": max_results
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        RAGExpert 返回格式:
        {
            'success': bool,
            'data': {
                'answer': str,  # RAGExpert会生成答案
                'sources': List,  # 知识源
                'evidence': List,  # 证据
                'confidence': float,
                ...
            },
            'confidence': float,
            ...
        }
        
        KnowledgeRetrievalAgent 期望格式:
        {
            'success': bool,
            'data': {
                'sources': List,  # 知识源（主要关注这个）
                'count': int,
                'query': str,
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            # 安全获取data，确保不是None
            data = new_result.data if hasattr(new_result, 'data') and new_result.data is not None else {}
            if not isinstance(data, dict):
                data = {}
            
            # 提取知识检索相关数据（忽略答案生成部分）
            retrieval_data = self._extract_retrieval_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": retrieval_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data")
            # 确保data不是None
            if data is None:
                data = {}
            elif not isinstance(data, dict):
                data = {}
            
            # 提取知识检索相关数据
            retrieval_data = self._extract_retrieval_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": retrieval_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_sources": "sources" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_retrieval_data(self, data: Any) -> Dict[str, Any]:
        """从RAGExpert的结果中提取知识检索数据"""
        retrieval_data = {}
        
        # 处理None或非字典类型的数据
        if data is None:
            data = {}
        elif not isinstance(data, dict):
            # 如果不是字典，尝试转换为字典或使用默认值
            data = {}
        
        # 提取sources（知识源）
        if isinstance(data, dict):
            if "sources" in data:
                retrieval_data["sources"] = data["sources"]
            elif "evidence" in data:
                # 如果RAGExpert返回evidence，也作为sources
                retrieval_data["sources"] = data["evidence"]
            elif "knowledge" in data:
                # 如果RAGExpert返回knowledge，也作为sources
                retrieval_data["sources"] = data["knowledge"]
            
            # 提取query（如果存在）
            if "query" in data:
                retrieval_data["query"] = data["query"]
        
        # 提取count
        sources = retrieval_data.get("sources", [])
        retrieval_data["count"] = len(sources) if isinstance(sources, list) else 0
        
        # 如果没有找到sources，返回空结构
        if not retrieval_data:
            retrieval_data = {
                "sources": [],
                "count": 0,
                "query": ""
            }
        
        return retrieval_data

