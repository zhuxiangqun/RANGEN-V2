"""
RANGEN Core Interfaces
======================

统一的标准接口定义，确保所有组件遵循一致的协议。

Interface Standards:
    - IAgent: Agent 标准接口
    - ITool: Tool 标准接口  
    - ISkill: Skill 标准接口
    - ICoordinator: 协调器标准接口
    - IAdapter: 适配器接口 (用于吸收新标准)
"""

from .agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
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
    # Agent
    "IAgent",
    "AgentConfig", 
    "AgentResult",
    "ExecutionStatus",
    
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
