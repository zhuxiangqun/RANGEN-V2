#!/usr/bin/env python3
"""
P1阶段端到端集成测试脚本 (DDL + KMS + Rerank + Self-Correction)
"""

import sys
import os
import asyncio
import logging
import json
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.real_reasoning_engine import RealReasoningEngine
from src.core.ddl.ddl_parameter_service import DDLParameterService, DDLPhase
from src.core.reasoning.retrieval_strategies.quality_assessor import RetrievalQualityAssessor
from src.core.ddl.adaptive_beta import AdaptiveBetaThreshold

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_end_to_end():
    logger.info("🚀 Starting End-to-End P1 Integration Test...")
    
    # 1. Initialize Engine
    logger.info("\n[1] Initializing RealReasoningEngine...")
    engine = RealReasoningEngine()
    
    # Mock LLM & KMS for testing if not available
    if not hasattr(engine, 'llm_integration') or not engine.llm_integration:
        logger.info("⚠️ LLM not available, using Mock LLM")
        engine.llm_integration = MagicMock()
        engine.llm_integration.generate = AsyncMock(return_value='{"relevance": 0.8, "coverage": 0.9, "contradiction": 0.0}')
        
    if not hasattr(engine, 'kms_service') or not engine.kms_service:
        logger.info("⚠️ KMS not available, using Mock KMS")
        engine.kms_service = MagicMock()
        engine.kms_service.query_knowledge = MagicMock(return_value=[
            {"content": "Mock document 1", "score": 0.9},
            {"content": "Mock document 2", "score": 0.8}
        ])
        
    # Ensure components are initialized
    if not engine.ddl_service:
        engine.ddl_service = DDLParameterService()
    if not engine.adaptive_beta:
        engine.adaptive_beta = AdaptiveBetaThreshold()
    if not engine.retrieval_assessor:
        engine.retrieval_assessor = RetrievalQualityAssessor(engine.llm_integration)
        
    # 2. Test Case: Complex Query (Expect CoT Strategy)
    query_complex = "Compare the economic policies of the 15th and 16th US presidents."
    logger.info(f"\n[2] Testing Complex Query: '{query_complex}'")
    
    context = {"use_ddl": True}
    result_complex = await engine.reason(query_complex, context)
    
    logger.info(f"👉 Result Strategy: {result_complex.reasoning_type}")
    logger.info(f"👉 Result Confidence: {result_complex.total_confidence}")
    logger.info(f"👉 Answer Source: {result_complex.answer_source_details}")
    
    # 3. Test Case: Simple Query (Expect Direct Strategy)
    query_simple = "Who is the 15th president?"
    logger.info(f"\n[3] Testing Simple Query: '{query_simple}'")
    
    # Force low beta for test (mocking DDL service response if needed, or rely on actual logic)
    # For this test, we assume DDL will return low beta for simple query
    result_simple = await engine.reason(query_simple, context)
    
    logger.info(f"👉 Result Strategy: {result_simple.reasoning_type}")
    
    # 4. Test Case: Self-Correction (Simulate Contradiction)
    logger.info("\n[4] Testing Self-Correction (Simulating Contradiction)...")
    
    # Mock Assessor to return contradiction
    original_assess = engine.retrieval_assessor.assess_retrieval_quality
    engine.retrieval_assessor.assess_retrieval_quality = AsyncMock(return_value={
        "overall_score": 0.4,
        "relevance_score": 0.9,
        "coverage_score": 0.9,
        "contradiction_score": 0.8, # High contradiction
        "needs_retry": True,
        "reason": "Simulated contradiction"
    })
    
    result_correction = await engine.reason("Contradictory query", context)
    
    logger.info(f"👉 Retry Count: {result_correction.answer_source_details.get('retries')}")
    logger.info(f"👉 Final Beta: {result_correction.answer_source_details.get('beta')}")
    
    # Restore assessor
    engine.retrieval_assessor.assess_retrieval_quality = original_assess
    
    logger.info("\n🎉 End-to-End Test Completed!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
