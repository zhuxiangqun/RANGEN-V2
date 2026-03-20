"""
RANGEN Core Interfaces
=====================

统一的标准接口定义，确保所有组件遵循一致的协议。

Interface Standards:
    - IAgent: Agent 标准接口 (使用 unified_agent 中的统一接口)
    - ITool: Tool 标准接口  
    - ISkill: Skill 标准接口
    - ICoordinator: 协调器标准接口
    - IAdapter: 适配器接口 (用于吸收新标准)

Migration Guide:
    旧: from src.interfaces.agent import IAgent
    新: from src.interfaces.unified_agent import IAgent
    或: from src.interfaces import IAgent  (推荐)
"""

# 优先使用统一接口
from .unified_agent import (
    IAgent,
    UnifiedAgentConfig,
    UnifiedAgentResult,
    AgentConfig,
    AgentResult,
    ExecutionStatus,
    AgentCapability,
)

# 保留其他接口
from .tool import ITool, ToolConfig, ToolResult, ToolCategory
from .skill import ISkill, SkillMetadata, SkillResult, SkillScope, SkillCategory, ToolSchema
from .coordinator import ICoordinator
from .adapter import (
    IAdapter, 
    AdapterRegistry, 
    AdapterMetadata, 
    StandardVersion,
    get_adapter_registry
)


__all__ = [
    # Agent (统一接口 - 优先)
    "IAgent",
    "UnifiedAgentConfig",
    "UnifiedAgentResult",
    "AgentConfig",      # Alias for UnifiedAgentConfig
    "AgentResult",      # Alias for UnifiedAgentResult
    "ExecutionStatus",
    "AgentCapability",
    
    # Tool
    "ITool",
    "ToolConfig",
    "ToolResult",
    "ToolCategory",
    
    # Skill
    "ISkill",
    "SkillMetadata",
    "SkillResult",
    "SkillScope",
    "SkillCategory",
    "ToolSchema",
    
    # Coordinator
    "ICoordinator",
    
    # Adapter
    "IAdapter",
    "AdapterRegistry",
    "AdapterMetadata",
    "StandardVersion",
    "get_adapter_registry",
]
