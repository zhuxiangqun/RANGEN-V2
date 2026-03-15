"""
上下文构建器模块

从 UnifiedResearchSystem 拆分出来的上下文构建功能
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class ContextBuilder:
    """
    上下文构建器
    
    构建:
    - Agent 上下文
    - MAS (多智能体系统) 上下文
    - ReAct 上下文
    """
    
    def __init__(self):
        # 默认系统提示
        self._default_system_prompt = """You are a helpful research assistant.
Your goal is to provide accurate, well-reasoned responses based on available evidence."""
    
    def _build_context(
        self, 
        request: Any
    ) -> Dict[str, Any]:
        """
        构建通用上下文
        """
        # 提取查询和元数据
        query = request.query
        timeout = getattr(request, "timeout", 1800)
        
        # 获取上下文
        context = getattr(request, "context", {}) or {}
        metadata = getattr(request, "metadata", {}) or {}
        
        # 构建基础上下文
        built_context = {
            "query": query,
            "timeout": timeout,
            "timestamp": datetime.now().isoformat(),
            # 用户信息
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id"),
            # 历史记录
            "history": context.get("history", []),
            # 优先级
            "priority": metadata.get("priority", "normal"),
            # 其他配置
            "max_iterations": metadata.get("max_iterations", 10),
        }
        
        return built_context
    
    def build_mas_context(
        self,
        request: Any,
        chief_agent: Any = None
    ) -> Dict[str, Any]:
        """
        构建多智能体系统 (MAS) 上下文
        """
        # 基础上下文
        context = self._build_context(request)
        
        # MAS 特定配置
        mas_config = {
            "use_mas": True,
            "max_agents": 4,
            "coordination_mode": "sequential",  # 或 "parallel"
            
            # 子 Agent 配置
            "sub_agents": {
                "knowledge": {
                    "enabled": True,
                    "timeout": 300,
                },
                "reasoning": {
                    "enabled": True,
                    "timeout": 600,
                },
                "answer": {
                    "enabled": True,
                    "timeout": 300,
                },
                "citation": {
                    "enabled": True,
                    "timeout": 180,
                },
            },
        }
        
        context.update(mas_config)
        
        # 添加 ChiefAgent 信息
        if chief_agent:
            context["chief_agent_available"] = True
            context["chief_agent_type"] = type(chief_agent).__name__
        
        return context
    
    def build_react_context(
        self,
        request: Any,
        tool_registry: Any = None,
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        构建 ReAct Agent 上下文
        """
        # 基础上下文
        context = self._build_context(request)
        
        # ReAct 特定配置
        react_config = {
            "use_react": True,
            "max_iterations": max_iterations,
            "enable_thinking": True,
            
            # 工具配置
            "tools_enabled": tool_registry is not None,
        }
        
        context.update(react_config)
        
        return context
    
    def build_traditional_context(
        self,
        request: Any,
        agent_type: str
    ) -> Dict[str, Any]:
        """
        构建传统流程上下文
        """
        # 基础上下文
        context = self._build_context(request)
        
        # 传统流程特定配置
        traditional_config = {
            "mode": "traditional",
            "agent_type": agent_type,
        }
        
        context.update(traditional_config)
        
        return context
    
    def add_history_context(
        self,
        context: Dict[str, Any],
        history: List[Dict[str, Any]],
        max_history: int = 5
    ) -> Dict[str, Any]:
        """
        添加历史上下文
        """
        # 只保留最近 N 条
        recent_history = history[-max_history:] if history else []
        
        # 格式化历史
        formatted_history = []
        for item in recent_history:
            formatted_history.append({
                "query": item.get("query", ""),
                "answer": item.get("answer", "")[:200],  # 截断
                "timestamp": item.get("timestamp", ""),
            })
        
        context["history"] = formatted_history
        context["history_count"] = len(formatted_history)
        
        return context
    
    def add_user_preferences(
        self,
        context: Dict[str, Any],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        添加用户偏好
        """
        # 复制偏好
        pref_copy = dict(preferences)
        
        # 添加到上下文
        context["user_preferences"] = pref_copy
        
        # 提取常用偏好
        if "language" in pref_copy:
            context["language"] = pref_copy["language"]
        
        if "detail_level" in pref_copy:
            context["detail_level"] = pref_copy["detail_level"]
        
        return context
    
    def extract_key_context(
        self,
        request: Any
    ) -> Dict[str, Any]:
        """
        提取关键上下文信息
        """
        context = getattr(request, "context", {}) or {}
        metadata = getattr(request, "metadata", {}) or {}
        
        return {
            "query": request.query,
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id"),
            "priority": metadata.get("priority", "normal"),
            "timeout": getattr(request, "timeout", 1800),
            "has_history": bool(context.get("history")),
        }
