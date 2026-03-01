#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
StrategicChiefAgent → AgentCoordinator 迁移适配器

将 StrategicChiefAgent 的调用适配到 AgentCoordinator，实现平滑迁移。
注意：StrategicChiefAgent专注于战略决策，而AgentCoordinator专注于Agent协调和任务管理。
适配器将战略决策任务转换为Agent协调任务。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class StrategicChiefAgentAdapter(MigrationAdapter):
    """StrategicChiefAgent → AgentCoordinator 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="StrategicChiefAgent",
            target_agent_name="AgentCoordinator"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（AgentCoordinator）"""
        return AgentCoordinator()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        StrategicChiefAgent 参数格式:
        {
            'query': str,  # 查询内容
            'strategic_goal': str,  # 战略目标
            'context': Dict,  # 上下文信息
            'resources': Dict,  # 资源信息
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
        strategic_goal = old_context.get("strategic_goal", "")
        context = old_context.get("context", {})
        resources = old_context.get("resources", {})
        constraints = old_context.get("constraints", {})
        
        # 判断操作类型
        # 如果context中有action字段，直接使用
        # 否则，根据query推断为submit_task操作
        action = old_context.get("action", "submit_task")
        
        # 转换参数格式
        if action == "submit_task":
            # 将战略决策任务转换为Agent协调任务
            adapted.update({
                "action": "submit_task",
                "task": {
                    "id": f"strategic_task_{hash(query) % 10000}",
                    "description": query or strategic_goal or "执行战略任务",
                    "priority": constraints.get("priority", "high"),  # 战略任务通常是高优先级
                    "metadata": {
                        "strategic_goal": strategic_goal,
                        "resources": resources,
                        "constraints": constraints,
                        "source": "StrategicChiefAgent",
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
        adapted["_strategic_goal"] = strategic_goal
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "action_type": action,
            "strategic_goal": strategic_goal
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
        
        StrategicChiefAgent 期望格式:
        {
            'success': bool,
            'data': {
                'strategic_plan': Dict,  # 战略计划
                'decision': Dict,  # 决策结果
                'execution_plan': List,  # 执行计划
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
            
            # 提取战略相关数据
            strategic_data = self._extract_strategic_data(data, new_result)
            
            adapted.update({
                "success": new_result.success,
                "data": strategic_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取战略相关数据
            strategic_data = self._extract_strategic_data(data, new_result)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": strategic_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_strategic_plan": "strategic_plan" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_strategic_data(self, data: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """从AgentCoordinator的结果中提取战略数据"""
        strategic_data = {}
        
        # 构建战略计划
        strategic_plan = {}
        
        # 如果data中有task_id，说明是任务提交成功
        if "task_id" in data:
            strategic_plan["task_id"] = data["task_id"]
            strategic_plan["status"] = data.get("status", "submitted")
            strategic_data["decision"] = {"task_id": data["task_id"], "status": "submitted"}
            strategic_data["execution_plan"] = [{"task_id": data["task_id"], "action": "execute"}]
        
        # 如果data中有agent_id，说明是Agent注册成功
        elif "agent_id" in data:
            strategic_plan["agent_id"] = data["agent_id"]
            strategic_plan["status"] = data.get("status", "registered")
            strategic_data["decision"] = {"agent_id": data["agent_id"], "status": "registered"}
        
        # 如果data中有stats，说明是统计信息
        elif "stats" in data or isinstance(data, dict) and any(k.startswith("total") or k.startswith("active") for k in data.keys()):
            strategic_plan["stats"] = data
            strategic_data["decision"] = {"stats": data}
        
        strategic_data["strategic_plan"] = strategic_plan
        
        # 如果没有找到特定数据，返回通用格式
        if not strategic_data:
            strategic_data = {
                "strategic_plan": {},
                "decision": {},
                "execution_plan": []
            }
        
        return strategic_data

