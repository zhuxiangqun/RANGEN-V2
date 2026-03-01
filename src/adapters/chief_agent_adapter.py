#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ChiefAgent → AgentCoordinator 迁移适配器

将 ChiefAgent 的调用适配到 AgentCoordinator，实现平滑迁移。
注意：ChiefAgent主要用于多智能体协作，而AgentCoordinator主要用于Agent协调和任务管理。
适配器需要将ChiefAgent的协作任务转换为AgentCoordinator的任务提交。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.agent_coordinator import AgentCoordinator
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class ChiefAgentAdapter(MigrationAdapter):
    """ChiefAgent → AgentCoordinator 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="ChiefAgent",
            target_agent_name="AgentCoordinator"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（AgentCoordinator）"""
        return AgentCoordinator()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        ChiefAgent 参数格式:
        {
            'query': str,  # 必需，查询内容
            'session_id': str,  # 可选，会话ID
            'dependencies': Dict,  # 可选，依赖信息
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
        session_id = old_context.get("session_id", "")
        dependencies = old_context.get("dependencies", {})
        
        # 判断操作类型
        # 如果context中有action字段，直接使用
        # 否则，根据query推断为submit_task操作
        action = old_context.get("action", "submit_task")
        
        # 转换参数格式
        if action == "submit_task":
            # 将ChiefAgent的查询转换为AgentCoordinator的任务
            adapted.update({
                "action": "submit_task",
                "task": {
                    "id": f"task_{session_id}_{hash(query) % 10000}" if session_id else f"task_{hash(query) % 10000}",
                    "description": query,
                    "priority": old_context.get("priority", "normal"),
                    "metadata": {
                        "session_id": session_id,
                        "dependencies": dependencies,
                        "source": "ChiefAgent",
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
        adapted["_original_query"] = query
        adapted["_original_session_id"] = session_id
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "action_type": action,
            "query_length": len(query)
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
        
        ChiefAgent 期望格式:
        {
            'success': bool,
            'data': {
                'answer': str,  # 答案
                'subtasks': List,  # 子任务列表
                'observations': List,  # 观察结果
                'thoughts': List,  # 思考过程
                'actions': List,  # 执行的动作
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
            
            # 提取ChiefAgent期望的结果格式
            chief_data = self._extract_chief_data(data, new_result)
            
            adapted.update({
                "success": new_result.success,
                "data": chief_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取ChiefAgent期望的结果格式
            chief_data = self._extract_chief_data(data, new_result)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": chief_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_answer": "answer" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_chief_data(self, data: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """从AgentCoordinator的结果中提取ChiefAgent期望的数据"""
        chief_data = {}
        
        # 如果data中有task_id，说明是任务提交成功
        if "task_id" in data:
            chief_data["task_id"] = data["task_id"]
            chief_data["status"] = data.get("status", "submitted")
            # 对于ChiefAgent，可能需要等待任务完成才能获取答案
            # 这里先返回任务ID，实际答案需要后续查询
            chief_data["answer"] = f"任务已提交: {data['task_id']}"
            chief_data["subtasks"] = []
        
        # 如果data中有agent_id，说明是Agent注册成功
        elif "agent_id" in data:
            chief_data["agent_id"] = data["agent_id"]
            chief_data["status"] = data.get("status", "registered")
            chief_data["answer"] = f"Agent已注册: {data['agent_id']}"
        
        # 如果data中有stats，说明是统计信息
        elif "stats" in data or isinstance(data, dict) and any(k.startswith("total") or k.startswith("active") for k in data.keys()):
            chief_data["stats"] = data
            chief_data["answer"] = "统计信息已获取"
        
        # 如果没有找到特定数据，返回通用格式
        if not chief_data:
            chief_data = {
                "answer": "",
                "subtasks": [],
                "observations": [],
                "thoughts": [],
                "actions": [],
                "status": data.get("status", "unknown")
            }
        
        return chief_data

