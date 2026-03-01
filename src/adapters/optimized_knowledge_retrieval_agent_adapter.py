#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OptimizedKnowledgeRetrievalAgent → RAGExpert 迁移适配器

将 OptimizedKnowledgeRetrievalAgent 的调用适配到 RAGExpert，实现平滑迁移。
注意：OptimizedKnowledgeRetrievalAgent是KnowledgeRetrievalAgent的优化版本，功能类似。
适配器将只使用RAGExpert的知识检索部分。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.rag_agent import RAGExpert
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class OptimizedKnowledgeRetrievalAgentAdapter(MigrationAdapter):
    """OptimizedKnowledgeRetrievalAgent → RAGExpert 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="OptimizedKnowledgeRetrievalAgent",
            target_agent_name="RAGExpert"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（RAGExpert）"""
        return RAGExpert()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        OptimizedKnowledgeRetrievalAgent 参数格式:
        {
            'query': str,  # 必需
            'type': str,  # 可选，默认"knowledge_retrieval"
            'max_results': int,  # 可选
            'threshold': float,  # 可选
            'optimization_params': Dict,  # 可选，优化参数
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
        optimization_params = old_context.get("optimization_params", {})
        
        # 转换参数格式
        adapted.update({
            "query": query,
            # RAGExpert的参数
            "type": old_context.get("type", "rag"),
            "use_cache": optimization_params.get("use_cache", True),
            "use_parallel": optimization_params.get("use_parallel", True),
            # 保留原始参数供参考
            "max_results": max_results,
            "threshold": threshold,
            "optimization_params": optimization_params,
            # 标记只做知识检索（不生成答案）
            "_knowledge_retrieval_only": True,
        })
        
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
        
        OptimizedKnowledgeRetrievalAgent 期望格式:
        {
            'success': bool,
            'data': {
                'sources': List,  # 知识源（主要关注这个）
                'count': int,
                'query': str,
                'optimization_metrics': Dict,  # 优化指标
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            data = new_result.data if hasattr(new_result, 'data') else {}
            
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
            data = new_result.get("data", {})
            
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
    
    def _extract_retrieval_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从RAGExpert的结果中提取知识检索数据"""
        retrieval_data = {}
        
        # 提取sources（知识源）
        if "sources" in data:
            retrieval_data["sources"] = data["sources"]
        elif "evidence" in data:
            retrieval_data["sources"] = data["evidence"]
        elif "knowledge" in data:
            retrieval_data["sources"] = data["knowledge"]
        
        # 提取count
        sources = retrieval_data.get("sources", [])
        retrieval_data["count"] = len(sources) if isinstance(sources, list) else 0
        
        # 提取query（如果存在）
        if "query" in data:
            retrieval_data["query"] = data["query"]
        
        # 提取优化指标（从confidence等字段推断）
        retrieval_data["optimization_metrics"] = {
            "confidence": data.get("confidence", 0.7),
            "retrieval_count": retrieval_data["count"],
            "cache_hit": data.get("cache_hit", False),
        }
        
        # 如果没有找到sources，返回空结构
        if not retrieval_data:
            retrieval_data = {
                "sources": [],
                "count": 0,
                "query": "",
                "optimization_metrics": {}
            }
        
        return retrieval_data

