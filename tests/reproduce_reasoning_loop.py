
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import MagicMock, AsyncMock

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.real_reasoning_engine import RealReasoningEngine
from src.core.reasoning.models import Evidence

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_reasoning_loop():
    # Initialize engine
    engine = RealReasoningEngine()
    
    # Mock components
    engine.step_generator = MagicMock()
    engine.evidence_processor = AsyncMock()
    engine.llm_integration = MagicMock()
    engine.operators = {
        'extraction': AsyncMock(),
        'comparison': AsyncMock(),
        'synthesis': AsyncMock(),
        'tool_use': AsyncMock()
    }
    # Mock operator execution to fail so it falls back to evidence processor
    for op in engine.operators.values():
        op.execute.return_value = MagicMock(success=False)

    # Mock evidence processor to return evidence for step 1
    async def mock_gather_evidence(sub_query, context, config):
        if "Mohicans" in sub_query:
            return [Evidence(content="James Fenimore Cooper wrote The Last of the Mohicans.", source="mock", confidence=0.9, relevance_score=1.0, evidence_type="text", metadata={})]
        elif "Cooper" in sub_query and "born" in sub_query:
            return [Evidence(content="James Fenimore Cooper was born in 1789.", source="mock", confidence=0.9, relevance_score=1.0, evidence_type="text", metadata={})]
        return []
    
    engine.evidence_processor.gather_evidence = AsyncMock(side_effect=mock_gather_evidence)

    # Mock LLM integration for fallback (not needed if evidence works)
    engine.llm_integration.generate_response.return_value = "Mock Answer"

    # Define the plan
    initial_plan = [
        {
            "type": "extraction",
            "description": "Who wrote the book 'The Last of the Mohicans'?",
            "sub_query": "Who wrote the book 'The Last of the Mohicans'?",
            "confidence": 0.8
        },
        {
            "type": "extraction",
            "description": "Find birth year of author",
            "sub_query": "What year was the author born?",
            "confidence": 0.8
        },
        {
            "type": "synthesis",
            "description": "Synthesize the final answer",
            "sub_query": "Synthesize the final answer",
            "confidence": 0.8
        }
    ]

    # Execute the loop
    logger.info("Starting reasoning loop test...")
    result = await engine._execute_deep_reasoning_loop(
        query="When was the author of The Last of the Mohicans born?",
        initial_plan=initial_plan,
        context={"evidence": []}
    )

    # Verify results
    steps = result.reasoning_steps
    logger.info(f"Total steps executed: {len(steps)}")
    
    step1 = steps[0]
    logger.info(f"Step 1 result: {step1.get('result')}")
    
    step2 = steps[1]
    logger.info(f"Step 2 sub_query (after replacement): {step2.get('sub_query')}")
    
    if "James Fenimore Cooper" in step2.get('sub_query', ''):
        logger.info("✅ Placeholder replacement passed!")
    else:
        logger.error("❌ Placeholder replacement failed!")

if __name__ == "__main__":
    asyncio.run(test_reasoning_loop())
