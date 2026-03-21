#!/usr/bin/env python3
"""
智能体模块 - 统一导入

核心 Agent (推荐使用):
  - BaseAgent: 基类
  - ReasoningAgent: 推理 (ReAct循环)
  - RAGAgent: 知识检索
  - CitationAgent: 引用
  - ValidationAgent: 验证
  - ChiefAgent: 多Agent协调
  
工厂与构建器:
  - AgentFactory: 工厂模式
  - AgentBuilder: 建造者模式
  
新系统 (试验性):
  - UnifiedExecutor: 统一执行器
"""

import warnings

__version__ = "2.0.0"
__all__ = []  # 延迟导出，避免循环依赖


def __getattr__(name):
    """延迟导入以避免循环依赖"""
    
    # 核心 Agent
    if name == 'BaseAgent':
        from .base_agent import BaseAgent
        return BaseAgent
    elif name == 'ReasoningAgent':
        from .reasoning_agent import ReasoningAgent
        return ReasoningAgent
    elif name == 'RAGAgent':
        from .rag_agent import RAGAgent
        return RAGAgent
    elif name == 'CitationAgent':
        from .citation_agent import CitationAgent
        return CitationAgent
    elif name == 'ValidationAgent':
        from .validation_agent import ValidationAgent
        return ValidationAgent
    elif name == 'ChiefAgent':
        from .chief_agent import ChiefAgent
        return ChiefAgent
    elif name == 'ReActAgent':
        try:
            from .react_agent import ReActAgent
            return ReActAgent
        except ImportError:
            warnings.warn("ReActAgent not available", DeprecationWarning)
            raise AttributeError(f"module 'src.agents' has no attribute '{name}'")
    
    # 工厂
    elif name == 'AgentFactory':
        from .agent_factory import AgentFactory
        return AgentFactory
    elif name == 'AgentBuilder':
        from .agent_builder import AgentBuilder
        return AgentBuilder
    elif name in ('AgentDirector', 'get_agent_director', 'create_agent_builder'):
        from .agent_builder import get_agent_director, create_agent_builder, AgentDirector
        if name == 'AgentDirector':
            return AgentDirector
        elif name == 'get_agent_director':
            return get_agent_director
        elif name == 'create_agent_builder':
            return create_agent_builder
    
    # 便捷函数
    elif name == 'create_agent':
        def create_agent(agent_type: str, config: dict = None):
            factory = AgentFactory()
            return factory.create_agent(agent_type, config or {})
        return create_agent
    
    raise AttributeError(f"module 'src.agents' has no attribute '{name}'")
