"""
RANGEN Router Interface Definition
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class RouteTarget(Enum):
    DIRECT = "direct"
    COT = "cot"
    REACT = "react"
    PLAN_AND_SOLVE = "plan_and_solve"
    CUSTOM = "custom"

class IRouter(ABC):
    """Interface for routing logic"""
    
    @abstractmethod
    async def route(self, query: str, context: Optional[Dict] = None) -> RouteTarget:
        """Determine the execution path for a query"""
        pass
