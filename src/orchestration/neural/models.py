"""
Neural Model Implementations
Real DL models using transformers and sentence-transformers.
"""
from typing import Dict, List, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Import DL libraries inside classes or methods to avoid import overhead at startup
from src.interfaces.neural import IIntentClassifier, IReranker
from src.services.logging_service import get_logger

logger = get_logger(__name__)

class ZeroShotIntentClassifier(IIntentClassifier):
    """
    Intent Classifier using BART-Large-MNLI for Zero-Shot Classification.
    Capable of classifying text into arbitrary labels without fine-tuning.
    """
    
    def __init__(self, model_name: str = "facebook/bart-large-mnli", candidate_labels: List[str] = None):
        self.model_name = model_name
        self.candidate_labels = candidate_labels or ["research", "chat", "coding", "calculation"]
        self._pipeline = None
        self._executor = ThreadPoolExecutor(max_workers=1) # Run heavy model in separate thread
        logger.info(f"ZeroShotIntentClassifier configured with {model_name}")

    def _load_model(self):
        """Lazy load the model"""
        if self._pipeline is None:
            from transformers import pipeline
            logger.info("Loading Zero-Shot Classification pipeline (this may take a moment)...")
            self._pipeline = pipeline("zero-shot-classification", model=self.model_name)
            logger.info("Zero-Shot Classification pipeline loaded.")

    async def classify(self, query: str) -> Dict[str, float]:
        """
        Classify query intent.
        """
        loop = asyncio.get_running_loop()
        
        def _predict():
            self._load_model()
            result = self._pipeline(query, self.candidate_labels)
            # Result format: {'sequence': '...', 'labels': ['label1', ...], 'scores': [0.9, ...]}
            return dict(zip(result['labels'], result['scores']))

        try:
            # Offload blocking model inference to thread
            scores = await loop.run_in_executor(self._executor, _predict)
            return scores
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            # Fallback
            return {label: 1.0/len(self.candidate_labels) for label in self.candidate_labels}

class CrossEncoderReranker(IReranker):
    """
    Reranker using Cross-Encoder (MS MARCO).
    Highly accurate relevance scoring.
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name
        self._model = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        logger.info(f"CrossEncoderReranker configured with {model_name}")

    def _load_model(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            logger.info("Loading Cross-Encoder model...")
            self._model = CrossEncoder(self.model_name)
            logger.info("Cross-Encoder model loaded.")

    async def rerank(self, query: str, documents: List[str]) -> List[Tuple[str, float]]:
        """
        Rerank documents.
        """
        if not documents:
            return []
            
        loop = asyncio.get_running_loop()
        
        def _predict():
            self._load_model()
            pairs = [(query, doc) for doc in documents]
            scores = self._model.predict(pairs)
            return scores

        try:
            scores = await loop.run_in_executor(self._executor, _predict)
            
            # Combine docs with scores and sort
            ranked = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
            return ranked
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            # Fallback: return original order with dummy scores
            return [(doc, 0.0) for doc in documents]
