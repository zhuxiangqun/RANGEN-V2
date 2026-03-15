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

# ============================================================================
# 核心 Agent (生产使用)
# ============================================================================

from .base_agent import BaseAgent
from .reasoning_agent import ReasoningAgent
from .rag_agent import RAGAgent
from .citation_agent import CitationAgent
from .validation_agent import ValidationAgent
from .chief_agent import ChiefAgent

# React Agent (别名，保持向后兼容)
try:
    from .react_agent import ReActAgent
except ImportError:
    warnings.warn("ReActAgent not available - using ReasoningAgent as fallback", DeprecationWarning)
    ReActAgent = ReasoningAgent

# ============================================================================
# 工厂与构建器
# ============================================================================

from .agent_factory import AgentFactory
from .agent_builder import (
    AgentBuilder,
    AgentDirector,
    get_agent_director,
    create_agent_builder
)

# ============================================================================
# 新系统 - 统一执行器 (试验性)
# ============================================================================

try:
    from .unified_executor import (
        UnifiedExecutor,
        get_unified_executor,
        execute_tool,
        ExecutionResult
    )
    _HAS_UNIFIED_EXECUTOR = True
except ImportError:
    _HAS_UNIFIED_EXECUTOR = False
    UnifiedExecutor = None
    get_unified_executor = None
    execute_tool = None
    ExecutionResult = None
    warnings.warn("UnifiedExecutor not available - using core agents", ImportWarning)

# ============================================================================
# 便捷函数
# ============================================================================

def create_agent(
    agent_type: str,
    config: dict = None
):
    """创建 Agent 工厂函数"""
    factory = AgentFactory()
    return factory.create_agent(agent_type, config or {})


# ============================================================================
# 导出列表
# ============================================================================

__all__ = [
    # 核心 Agent
    'BaseAgent',
    'ReActAgent',
    'ReasoningAgent',
    'RAGAgent',
    'CitationAgent',
    'ValidationAgent',
    'ChiefAgent',
    
    # 工厂
    'AgentFactory',
    'AgentBuilder',
    
    # 建造者模式
    'AgentDirector',
    'get_agent_director',
    'create_agent_builder',
    
    # 新系统 (可能为None)
    'UnifiedExecutor',
    'get_unified_executor',
    'execute_tool',
    'ExecutionResult',
    '_HAS_UNIFIED_EXECUTOR',
    
    # 便捷函数
    'create_agent',
]

# ============================================================================
# 版本信息
# ============================================================================

__version__ = "2.0.0"
