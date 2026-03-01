#!/usr/bin/env python3
"""
Test script for RetrievalQualityAssessor
"""

import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.reasoning.retrieval_strategies.quality_assessor import RetrievalQualityAssessor

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock LLM Service
class MockLLMService:
    def __init__(self):
        self.generate = AsyncMock()

async def test_quality_assessor():
    logger.info("🚀 Starting RetrievalQualityAssessor Test...")
    
    llm_service = MockLLMService()
    assessor = RetrievalQualityAssessor(llm_service)
    
    # Case 1: Good Evidence (Beta=0.5)
    logger.info("\n--- Case 1: Good Evidence (Beta=0.5) ---")
    llm_service.generate.return_value = """
    {
        "relevance": 0.9,
        "coverage": 0.8,
        "contradiction": 0.0,
        "reason": "Perfect match."
    }
    """
    evidences = [{"content": "The capital of France is Paris."}]
    result = await assessor.assess_retrieval_quality("Capital of France", evidences, beta=0.5)
    logger.info(f"Result: {result}")
    
    assert result["needs_retry"] == False, "Should not retry for good evidence"
    assert result["overall_score"] > 0.8, "Score should be high"
    
    # Case 2: Bad Evidence (Beta=0.5)
    logger.info("\n--- Case 2: Bad Evidence (Beta=0.5) ---")
    llm_service.generate.return_value = """
    {
        "relevance": 0.2,
        "coverage": 0.1,
        "contradiction": 0.0,
        "reason": "Irrelevant info."
    }
    """
    evidences = [{"content": "Python is a programming language."}]
    result = await assessor.assess_retrieval_quality("Capital of France", evidences, beta=0.5)
    logger.info(f"Result: {result}")
    
    assert result["needs_retry"] == True, "Should retry for bad evidence"
    assert result["overall_score"] < 0.5, "Score should be low"
    
    # Case 3: Contradictory Evidence (Beta=1.5 - High Beta)
    logger.info("\n--- Case 3: Contradictory Evidence (Beta=1.5) ---")
    llm_service.generate.return_value = """
    {
        "relevance": 0.9,
        "coverage": 0.9,
        "contradiction": 0.8,
        "reason": "Contradictory dates found."
    }
    """
    evidences = [
        {"content": "Event happened in 1990."},
        {"content": "Event happened in 1995."}
    ]
    result = await assessor.assess_retrieval_quality("When did the event happen?", evidences, beta=1.5)
    logger.info(f"Result: {result}")
    
    # High beta punishes contradiction
    # Score = 0.9*0.3 + 0.9*0.3 + (1-0.8)*0.4 = 0.27 + 0.27 + 0.08 = 0.62
    # Threshold is 0.7 for Beta > 1.0
    assert result["needs_retry"] == True, "Should retry for contradiction in high beta"
    assert result["contradiction_score"] == 0.8
    
    logger.info("\n🎉 All Tests Passed!")

if __name__ == "__main__":
    asyncio.run(test_quality_assessor())
