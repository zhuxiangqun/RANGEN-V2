#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LearningSystem → LearningOptimizer 迁移适配器

将 LearningSystem 的调用适配到 LearningOptimizer，实现平滑迁移。
注意：LearningSystem专注于学习，而LearningOptimizer专注于学习和优化。
适配器将学习任务转换为学习优化任务。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.learning_optimizer import LearningOptimizer
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class LearningSystemAdapter(MigrationAdapter):
    """LearningSystem → LearningOptimizer 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="LearningSystem",
            target_agent_name="LearningOptimizer"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（LearningOptimizer）"""
        return LearningOptimizer()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        LearningSystem 参数格式:
        {
            'action': str,  # 'learn', 'update', 'analyze', 'optimize'
            'data': Any,  # 学习数据
            'model_id': str,  # 模型ID
            'parameters': Dict,  # 参数
            'performance_data': Dict,  # 性能数据
            ...
        }
        
        LearningOptimizer 参数格式:
        {
            'action': str,  # 'incremental_learning', 'detect_patterns', 'create_ab_test', 'run_ab_test', 'adaptive_optimization', 'register_model', 'stats'
            'model_id': str,  # 模型ID (incremental_learning时需要)
            'new_data': Any,  # 新数据 (incremental_learning时需要)
            'performance_data': Dict,  # 性能数据 (detect_patterns/adaptive_optimization时需要)
            'test_name/description/variants/target_metric/baseline_variant': Dict,  # A/B测试信息 (create_ab_test时需要)
            'test_id': str,  # 测试ID (run_ab_test时需要)
            'model_name/parameters/learning_mode': Dict,  # 模型信息 (register_model时需要)
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        action = old_context.get("action", "learn")
        data = old_context.get("data")
        model_id = old_context.get("model_id", "")
        parameters = old_context.get("parameters", {})
        performance_data = old_context.get("performance_data", {})
        
        # 将action映射到LearningOptimizer的action
        action_mapping = {
            "learn": "incremental_learning",
            "update": "incremental_learning",
            "analyze": "detect_patterns",
            "optimize": "adaptive_optimization",
            "register": "register_model",
        }
        mapped_action = action_mapping.get(action, "incremental_learning")
        
        # 转换参数格式
        adapted.update({
            "action": mapped_action,
            # 对于incremental_learning操作
            "model_id": model_id,
            "new_data": data,
            # 对于detect_patterns/adaptive_optimization操作
            "performance_data": performance_data or data,
            # 对于register_model操作
            "model_name": old_context.get("model_name", model_id),
            "parameters": parameters,
            "learning_mode": old_context.get("learning_mode", "incremental"),
            # 保留原始参数供参考
            "data": data,
            "_original_action": action,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "original_action": action,
            "mapped_action": mapped_action
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        LearningOptimizer 返回格式:
        {
            'success': bool,
            'data': {
                'model_id': str,  # 模型ID
                'learning_result': Dict,  # 学习结果
                'patterns': List,  # 检测到的模式
                'optimization_result': Dict,  # 优化结果
                'ab_test_result': Dict,  # A/B测试结果
                ...
            },
            'confidence': float,
            ...
        }
        
        LearningSystem 期望格式:
        {
            'success': bool,
            'data': {
                'learning_result': Dict,  # 学习结果
                'updated_model': Dict,  # 更新的模型
                'insights': List,  # 洞察
                'optimization_suggestions': List,  # 优化建议
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
            
            # 提取学习相关数据
            learning_data = self._extract_learning_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": learning_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取学习相关数据
            learning_data = self._extract_learning_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": learning_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_learning_result": "learning_result" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_learning_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从LearningOptimizer的结果中提取学习数据"""
        learning_data = {}
        
        # 提取learning_result
        if "learning_result" in data:
            learning_data["learning_result"] = data["learning_result"]
            learning_data["updated_model"] = data["learning_result"]
        elif "model_id" in data:
            learning_data["updated_model"] = {"model_id": data["model_id"]}
        
        # 提取patterns（转换为insights）
        if "patterns" in data:
            learning_data["insights"] = data["patterns"]
        
        # 提取optimization_result（转换为optimization_suggestions）
        if "optimization_result" in data:
            opt_result = data["optimization_result"]
            if isinstance(opt_result, dict):
                suggestions = []
                if "suggestions" in opt_result:
                    suggestions = opt_result["suggestions"]
                elif "recommendations" in opt_result:
                    suggestions = opt_result["recommendations"]
                else:
                    # 从优化结果中提取建议
                    for key, value in opt_result.items():
                        if "suggestion" in key.lower() or "recommendation" in key.lower():
                            suggestions.append(value)
                learning_data["optimization_suggestions"] = suggestions
        
        # 提取ab_test_result（如果有）
        if "ab_test_result" in data:
            learning_data["ab_test_result"] = data["ab_test_result"]
        
        # 如果没有找到学习数据，返回空结构
        if not learning_data:
            learning_data = {
                "learning_result": {},
                "updated_model": {},
                "insights": [],
                "optimization_suggestions": []
            }
        
        return learning_data

