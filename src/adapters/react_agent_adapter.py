#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ReActAgent → ReasoningExpert 迁移适配器

将 ReActAgent 的调用适配到 ReasoningExpert，实现平滑迁移。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.reasoning_expert import ReasoningExpert
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class ReActAgentAdapter(MigrationAdapter):
    """ReActAgent → ReasoningExpert 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="ReActAgent",
            target_agent_name="ReasoningExpert"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（ReasoningExpert）"""
        return ReasoningExpert()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        ReActAgent 参数格式:
        {
            'query': str,  # 必需
            'max_iterations': int,  # 可选
            'tools': List[str],  # 可选
            ...
        }
        
        ReasoningExpert 参数格式:
        {
            'query': str,  # 必需
            'reasoning_type': str,  # 可选，默认自动分析
            'complexity': str,  # 可选，默认自动分析
            'max_parallel_paths': int,  # 可选，默认3
            'use_cache': bool,  # 可选，默认True
            'use_graph': bool,  # 可选，默认False
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        query = old_context.get("query", "")
        max_iterations = old_context.get("max_iterations", 10)
        tools = old_context.get("tools", [])
        
        # 转换参数格式
        adapted.update({
            "query": query,
            # ReasoningExpert的参数
            "reasoning_type": old_context.get("reasoning_type"),  # 可选，让ReasoningExpert自动分析
            "complexity": old_context.get("complexity"),  # 可选，让ReasoningExpert自动分析
            "max_parallel_paths": min(max_iterations, 6),  # 将max_iterations转换为max_parallel_paths
            "use_cache": old_context.get("use_cache", True),
            "use_graph": old_context.get("use_graph", False),
            # 保留原始参数供参考
            "max_iterations": max_iterations,
            "tools": tools,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "query_length": len(query),
            "max_iterations": max_iterations
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        ReasoningExpert 返回格式:
        {
            'success': bool,
            'data': {
                'answer': str,
                'reasoning_paths': List,
                'confidence': float,
                ...
            },
            'confidence': float,
            ...
        }
        
        ReActAgent 期望格式:
        {
            'success': bool,
            'data': {
                'answer': str,
                'observations': List,
                'thoughts': List,
                'actions': List,
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
            
            # 提取答案和推理信息
            answer_data = self._extract_answer_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": answer_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取答案和推理信息
            answer_data = self._extract_answer_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": answer_data,
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
    
    def _extract_answer_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从ReasoningExpert的结果中提取答案数据"""
        answer_data = {}
        
        # 🛡️ 防御性编程：处理 None
        if data is None:
            return answer_data
        
        # 提取答案
        if "answer" in data:
            answer_data["answer"] = data["answer"]
        elif "final_answer" in data:
            answer_data["answer"] = data["final_answer"]
        elif "result" in data:
            if isinstance(data["result"], str):
                answer_data["answer"] = data["result"]
            elif isinstance(data["result"], dict):
                answer_data["answer"] = data["result"].get("answer", "")
        
        # 将推理路径转换为observations格式（ReActAgent期望的格式）
        if "reasoning_paths" in data:
            reasoning_paths = data["reasoning_paths"]
            observations = []
            thoughts = []
            actions = []
            
            for path in reasoning_paths:
                if isinstance(path, dict):
                    # 提取观察
                    if "observations" in path:
                        observations.extend(path["observations"])
                    elif "steps" in path:
                        for step in path["steps"]:
                            if isinstance(step, dict):
                                if "observation" in step:
                                    observations.append(step["observation"])
                                if "thought" in step:
                                    thoughts.append(step["thought"])
                                if "action" in step:
                                    actions.append(step["action"])
            
            if observations:
                answer_data["observations"] = observations
            if thoughts:
                answer_data["thoughts"] = thoughts
            if actions:
                answer_data["actions"] = actions
        
        # 如果没有找到答案，返回空结构
        if not answer_data:
            answer_data = {
                "answer": "",
                "observations": [],
                "thoughts": [],
                "actions": []
            }
        
        return answer_data

