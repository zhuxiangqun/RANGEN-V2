"""
Agent Interface
==============

⚠️ DEPRECATED: 请使用 src.interfaces.unified_agent 替代
    - 统一接口: UnifiedAgentConfig, UnifiedAgentResult, IAgent
    - 迁移: from src.interfaces.unified_agent import IAgent

此文件保留以向后兼容，新代码请使用 unified_agent.py
"""
import warnings
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

# 发出弃用警告
warnings.warn(
    "src.interfaces.agent is deprecated. Please use src.interfaces.unified_agent instead.\n"
    "Migration: from src.interfaces.unified_agent import IAgent, UnifiedAgentConfig",
    DeprecationWarning,
    stacklevel=2
)


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentConfig(BaseModel):
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_name: str
    status: ExecutionStatus
    output: Any
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IAgent(ABC):
    """
    ⚠️ DEPRECATED: 请使用 src.interfaces.unified_agent.IAgent
    
    这个接口缺少 agent_id 和 is_enabled()，请迁移到 unified_agent.IAgent
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """Execute the agent's task"""
        pass


# 向后兼容导出
__all__ = ["IAgent", "AgentConfig", "AgentResult", "ExecutionStatus"]
