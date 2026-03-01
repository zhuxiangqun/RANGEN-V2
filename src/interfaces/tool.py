"""
Tool Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

class ToolCategory(Enum):
    RETRIEVAL = "retrieval"
    COMPUTE = "compute"
    UTILITY = "utility"
    API = "api"

class ToolConfig(BaseModel):
    name: str
    description: str
    category: ToolCategory
    version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    success: bool
    output: Any
    execution_time: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ITool(ABC):
    def __init__(self, config: ToolConfig):
        self.config = config

    @abstractmethod
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON schema for parameters"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool"""
        pass
