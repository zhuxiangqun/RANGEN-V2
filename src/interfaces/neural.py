"""
Neural Interfaces
Defines contracts for DL/ML components.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any

class IIntentClassifier(ABC):
    """Interface for Intent Classification Models"""
    
    @abstractmethod
    async def classify(self, query: str) -> Dict[str, float]:
        """
        Classify the intent of a query.
        Returns a dictionary of {label: probability}.
        """
        pass

class IReranker(ABC):
    """Interface for Neural Reranking Models"""
    
    @abstractmethod
    async def rerank(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        """
        Rerank a list of documents based on relevance to the query.
        Returns a list of (document, score) tuples, sorted by score.
        """
        pass

class IAnomalyDetector(ABC):
    """Interface for System Anomaly Detection"""
    
    @abstractmethod
    async def detect(self, metrics: Dict[str, float]) -> Tuple[bool, str]:
        """
        Detect if current system state is anomalous.
        Returns (is_anomaly, reason).
        """
        pass
