"""
Coordinator Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any

class ICoordinator(ABC):
    @abstractmethod
    async def run_task(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        pass
