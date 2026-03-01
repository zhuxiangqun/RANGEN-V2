"""
Quality Evaluator Node
Evaluates the quality of the generated answer and decides whether to accept it or retry.
"""
from typing import Dict, Any
from src.services.logging_service import get_logger
from src.core.monitoring.monitor_decorator import monitor

logger = get_logger(__name__)

class QualityEvaluatorNode:
    """
    Evaluates the quality of the final answer.
    """
    
    def __init__(self):
        # Threshold for acceptance
        self.quality_threshold = 0.7 

    @monitor.trace_node("quality_evaluator")
    async def evaluate(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate the answer quality.
        """
        answer = state.get("final_answer", "")
        query = state.get("query", "")
        
        # 1. Simple Heuristic Check
        # In a real system, this would call an LLM-as-a-Judge
        score = self._heuristic_score(query, answer)
        
        passed = score >= self.quality_threshold
        logger.info(f"Quality Score: {score:.2f} (Passed: {passed})")
        
        return {
            "quality_score": score,
            "quality_passed": passed,
            # If failed, we might want to add feedback to context for the next retry
            "quality_feedback": "Answer too short or lacks detail." if not passed else "Good quality."
        }

    def _heuristic_score(self, query: str, answer: str) -> float:
        """Calculate a heuristic quality score"""
        if not answer:
            return 0.0
            
        score = 0.5 # Base score
        
        # Length check
        if len(answer) > 100:
            score += 0.2
        if len(answer) > 500:
            score += 0.1
            
        # Keyword overlap (very basic relevance check)
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = len(query_words.intersection(answer_words))
        if overlap > 0:
            score += 0.1 * min(overlap, 3)
            
        return min(score, 1.0)
