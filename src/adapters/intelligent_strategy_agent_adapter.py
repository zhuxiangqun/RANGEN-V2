#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntelligentStrategyAgent → AgentCoordinator 迁移适配器

将 IntelligentStrategyAgent 的调用适配到 AgentCoordinator，实现平滑迁移。
注意：IntelligentStrategyAgent专注于策略制定，而AgentCoordinator专注于Agent协调和任务管理。
适配器将策略制定任务转换为Agent协调任务。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class IntelligentStrategyAgentAdapter(MigrationAdapter):
    """IntelligentStrategyAgent → AgentCoordinator 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="IntelligentStrategyAgent",
            target_agent_name="AgentCoordinator"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（AgentCoordinator）"""
        return AgentCoordinator()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        IntelligentStrategyAgent 参数格式:
        {
            'query': str,  # 查询内容
            'strategy_type': str,  # 策略类型
            'context': Dict,  # 上下文信息
            'goals': List,  # 目标列表
            'constraints': Dict,  # 约束条件
            ...
        }
        
        AgentCoordinator 参数格式:
        {
            'action': str,  # 必需，协调动作 ("register_agent", "submit_task", "get_stats"等)
            'task': Dict,  # submit_task时需要
            'agent_id': str,  # register_agent时需要
            'capabilities': List,  # register_agent时需要
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        query = old_context.get("query", "")
        strategy_type = old_context.get("strategy_type", "")
        context = old_context.get("context", {})
        goals = old_context.get("goals", [])
        constraints = old_context.get("constraints", {})
        
        # 判断操作类型
        # 如果context中有action字段，直接使用
        # 否则，根据query推断为submit_task操作
        action = old_context.get("action", "submit_task")
        
        # 转换参数格式
        if action == "submit_task":
            # 将策略制定任务转换为Agent协调任务
            adapted.update({
                "action": "submit_task",
                "task": {
                    "id": f"strategy_task_{hash(query) % 10000}",
                    "description": query or f"制定{strategy_type}策略",
                    "priority": constraints.get("priority", "normal"),
                    "metadata": {
                        "strategy_type": strategy_type,
                        "goals": goals,
                        "constraints": constraints,
                        "source": "IntelligentStrategyAgent",
                        **context
                    }
                }
            })
        elif action == "register_agent":
            # Agent注册操作
            adapted.update({
                "action": "register_agent",
                "agent_id": old_context.get("agent_id", ""),
                "capabilities": old_context.get("capabilities", []),
                "specialization_scores": old_context.get("specialization_scores")
            })
        else:
            # 其他操作，直接传递
            adapted.update({
                "action": action,
                **{k: v for k, v in old_context.items() if k != "action"}
            })
        
        # 保留原始参数供参考
        adapted["_original_query"] = query
        adapted["_strategy_type"] = strategy_type
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "action_type": action,
            "strategy_type": strategy_type
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        AgentCoordinator 返回格式:
        {
            'success': bool,
            'data': {
                'status': str,  # "submitted", "registered"等
                'task_id': str,  # submit_task时返回
                'agent_id': str,  # register_agent时返回
                ...
            },
            'confidence': float,
            ...
        }
        
        IntelligentStrategyAgent 期望格式:
        {
            'success': bool,
            'data': {
                'strategy': Dict,  # 制定的策略
                'plan': List,  # 执行计划
                'recommendations': List,  # 推荐建议
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
            
            # 提取策略相关数据
            strategy_data = self._extract_strategy_data(data, new_result)
            
            adapted.update({
                "success": new_result.success,
                "data": strategy_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取策略相关数据
            strategy_data = self._extract_strategy_data(data, new_result)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": strategy_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_strategy": "strategy" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_strategy_data(self, data: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """从AgentCoordinator的结果中提取策略数据"""
        strategy_data = {}
        
        # 如果data中有task_id，说明是任务提交成功
        if "task_id" in data:
            strategy_data["task_id"] = data["task_id"]
            strategy_data["status"] = data.get("status", "submitted")
            # 对于策略Agent，可能需要等待任务完成才能获取策略
            # 这里先返回任务ID，实际策略需要后续查询
            strategy_data["strategy"] = {"task_id": data["task_id"], "status": "submitted"}
            strategy_data["plan"] = []
            strategy_data["recommendations"] = []
        
        # 如果data中有agent_id，说明是Agent注册成功
        elif "agent_id" in data:
            strategy_data["agent_id"] = data["agent_id"]
            strategy_data["status"] = data.get("status", "registered")
            strategy_data["strategy"] = {"agent_id": data["agent_id"], "status": "registered"}
        
        # 如果data中有stats，说明是统计信息
        elif "stats" in data or isinstance(data, dict) and any(k.startswith("total") or k.startswith("active") for k in data.keys()):
            strategy_data["stats"] = data
            strategy_data["strategy"] = {"stats": data}
        
        # 如果没有找到特定数据，返回通用格式
        if not strategy_data:
            strategy_data = {
                "strategy": {},
                "plan": [],
                "recommendations": [],
                "status": data.get("status", "unknown")
            }
        
        return strategy_data

