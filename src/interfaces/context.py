"""
Context Interface
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class IContext(ABC):
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        pass

    @abstractmethod
    def update(self, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
