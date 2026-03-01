#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAGAgent → RAGExpert 迁移适配器

注意：RAGAgent实际上是RAGExpert的别名（向后兼容），所以这个适配器主要是为了保持迁移框架的一致性。
实际上可以直接使用RAGExpert，但通过适配器可以统一管理迁移过程。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.rag_agent import RAGExpert
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class RAGAgentAdapter(MigrationAdapter):
    """RAGAgent → RAGExpert 适配器
    
    注意：由于RAGAgent = RAGExpert（别名），这个适配器主要是为了保持迁移框架的一致性。
    参数和结果格式完全兼容，直接传递即可。
    """
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="RAGAgent",
            target_agent_name="RAGExpert"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
        logger.info("注意：RAGAgent是RAGExpert的别名，参数完全兼容")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（RAGExpert）"""
        return RAGExpert()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        由于RAGAgent = RAGExpert（别名），参数格式完全兼容，直接传递即可。
        
        RAGAgent/RAGExpert 参数格式:
        {
            'query': str,  # 必需
            'type': str,  # 可选，默认为"rag"
            'use_cache': bool,  # 可选，默认为True
            'use_parallel': bool,  # 可选，默认为True
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 由于完全兼容，直接传递所有参数
        adapted.update(old_context)
        
        # 确保type字段存在（如果不存在，设置为"rag"）
        if "type" not in adapted:
            adapted["type"] = "rag"
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "query_length": len(adapted.get("query", "")),
            "note": "RAGAgent是RAGExpert的别名，参数完全兼容"
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        由于RAGAgent = RAGExpert（别名），结果格式完全兼容，直接传递即可。
        
        RAGExpert/RAGAgent 返回格式:
        {
            'success': bool,
            'data': {
                'answer': str,
                'evidence': List,
                'confidence': float,
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
            
            adapted.update({
                "success": new_result.success,
                "data": data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果，直接传递
            adapted.update(new_result)
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_answer": "answer" in str(adapted.get("data", {})),
            "note": "RAGAgent是RAGExpert的别名，结果格式完全兼容"
        })
        
        return adapted

