"""
Neural Service Factory
Implements the Factory Pattern for creating and managing neural models.
Handles lazy loading and dependency injection.
"""
from typing import Dict, Any, Optional, List, Tuple
from src.interfaces.neural import IIntentClassifier, IReranker, IAnomalyDetector
from src.services.logging_service import get_logger

logger = get_logger(__name__)

# --- Concrete Implementations (Mock/Rule-based for now, Real DL later) ---

class RuleBasedIntentClassifier(IIntentClassifier):
    """Fallback classifier using simple heuristics"""
    async def classify(self, query: str) -> Dict[str, float]:
        query = query.lower()
        if any(w in query for w in ["search", "find", "who", "what", "where"]):
            return {"research": 0.8, "chat": 0.2}
        if any(w in query for w in ["calculate", "solve", "math"]):
            return {"calculation": 0.9, "chat": 0.1}
        return {"chat": 0.7, "research": 0.3}

class MockReranker(IReranker):
    """Fallback reranker that does nothing (identity)"""
    async def rerank(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        # Assign dummy scores
        return [(doc, 1.0 - (i * 0.1)) for i, doc in enumerate(documents)]

# --- Factory ---

from src.core.neural.models import ZeroShotIntentClassifier, CrossEncoderReranker
from src.core.utils.smart_model_manager import get_model_manager

class NeuralServiceFactory:
    """
    Factory for creating neural services.
    Manages lifecycle and configuration using SmartModelManager.
    """
    
    _instances: Dict[str, Any] = {}
    
    @classmethod
    def get_intent_classifier(cls, config: Optional[Dict] = None) -> IIntentClassifier:
        """Get or create an Intent Classifier"""
        # 🚀 Use SmartModelManager for lifecycle management
        manager = get_model_manager()
        
        def loader():
            logger.info("Initializing Intent Classifier (Lazy Load)...")
            return ZeroShotIntentClassifier()
            
        # Get from manager (handles caching & eviction)
        # Note: We wrap it in a proxy or just use it directly if it's stateless enough
        # Here we assume the model instance is the service itself
        classifier = manager.get_model("intent_classifier", loader)
        
        if classifier:
            return classifier
        else:
            logger.warning("Failed to load Intent Classifier, falling back to RuleBased")
            return RuleBasedIntentClassifier()

    @classmethod
    def get_reranker(cls, config: Optional[Dict] = None) -> IReranker:
        """Get or create a Reranker"""
        # 🚀 Use SmartModelManager for lifecycle management
        manager = get_model_manager()
        
        def loader():
            logger.info("Initializing Reranker (Lazy Load)...")
            return CrossEncoderReranker()
            
        reranker = manager.get_model("reranker", loader)
        
        if reranker:
            return reranker
        else:
            logger.warning("Failed to load Reranker, falling back to Mock")
            return MockReranker()

    @classmethod
    def reset(cls):
        """Clear all instances (for testing)"""
        # Also clear smart manager
        # Note: SmartModelManager doesn't have a public clear method yet, but we can simulate it
        # For now just clear local cache if any
        cls._instances = {}
