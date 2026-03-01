#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IntelligentCoordinatorAgent → AgentCoordinator 迁移适配器

将 IntelligentCoordinatorAgent 的调用适配到 AgentCoordinator，实现平滑迁移。
注意：IntelligentCoordinatorAgent和AgentCoordinator功能相似，都是Agent协调，但接口略有不同。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class IntelligentCoordinatorAgentAdapter(MigrationAdapter):
    """IntelligentCoordinatorAgent → AgentCoordinator 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="IntelligentCoordinatorAgent",
            target_agent_name="AgentCoordinator"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（AgentCoordinator）"""
        return AgentCoordinator()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        IntelligentCoordinatorAgent 参数格式:
        {
            'action': str,  # 协调动作
            'task': Dict,  # 任务信息
            'agents': List,  # Agent列表
            'coordination_strategy': str,  # 协调策略
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
        action = old_context.get("action", "submit_task")
        task = old_context.get("task", {})
        agents = old_context.get("agents", [])
        coordination_strategy = old_context.get("coordination_strategy", "")
        
        # 转换参数格式
        if action == "submit_task":
            # 任务提交操作
            adapted.update({
                "action": "submit_task",
                "task": task or {
                    "id": f"coordinated_task_{hash(str(old_context)) % 10000}",
                    "description": old_context.get("description", ""),
                    "priority": old_context.get("priority", "normal"),
                    "metadata": {
                        "coordination_strategy": coordination_strategy,
                        "agents": agents,
                        "source": "IntelligentCoordinatorAgent",
                        **old_context
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
        adapted["_coordination_strategy"] = coordination_strategy
        adapted["_agents"] = agents
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "action_type": action
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
        
        IntelligentCoordinatorAgent 期望格式:
        {
            'success': bool,
            'data': {
                'coordination_result': Dict,  # 协调结果
                'task_status': str,  # 任务状态
                'agent_status': Dict,  # Agent状态
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
            
            # 提取协调相关数据
            coordination_data = self._extract_coordination_data(data, new_result)
            
            adapted.update({
                "success": new_result.success,
                "data": coordination_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取协调相关数据
            coordination_data = self._extract_coordination_data(data, new_result)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": coordination_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_coordination": "coordination_result" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_coordination_data(self, data: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """从AgentCoordinator的结果中提取协调数据"""
        coordination_data = {}
        
        # 构建协调结果
        coordination_result = {}
        
        # 如果data中有task_id，说明是任务提交成功
        if "task_id" in data:
            coordination_result["task_id"] = data["task_id"]
            coordination_result["status"] = data.get("status", "submitted")
            coordination_data["task_status"] = data.get("status", "submitted")
        
        # 如果data中有agent_id，说明是Agent注册成功
        elif "agent_id" in data:
            coordination_result["agent_id"] = data["agent_id"]
            coordination_result["status"] = data.get("status", "registered")
            coordination_data["agent_status"] = {data["agent_id"]: data.get("status", "registered")}
        
        # 如果data中有stats，说明是统计信息
        elif "stats" in data or isinstance(data, dict) and any(k.startswith("total") or k.startswith("active") for k in data.keys()):
            coordination_result["stats"] = data
            coordination_data["agent_status"] = data
        
        coordination_data["coordination_result"] = coordination_result
        
        # 如果没有找到特定数据，返回通用格式
        if not coordination_data:
            coordination_data = {
                "coordination_result": {},
                "task_status": "unknown",
                "agent_status": {}
            }
        
        return coordination_data

