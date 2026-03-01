"""
Agent Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

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
    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """Execute the agent's task"""
        pass
