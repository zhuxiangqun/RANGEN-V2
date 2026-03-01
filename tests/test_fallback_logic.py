
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.core.real_reasoning_engine import RealReasoningEngine

@pytest.mark.asyncio
async def test_fallback_logic_when_evidence_fails():
    # Setup
    engine = RealReasoningEngine()
    engine.evidence_processor = MagicMock()
    engine.evidence_processor.gather_evidence = AsyncMock(return_value=[])  # Return empty evidence
    
    engine.llm_integration = MagicMock()
    engine.llm_integration.generate_response = MagicMock(return_value="James Fenimore Cooper")
    
    engine.fast_llm_integration = MagicMock()
    engine.fast_llm_integration.analyze_query_complexity = AsyncMock(return_value={"is_simple": False, "beta": 1.0})
    
    # Mock operators to return None (so it falls through to evidence gathering)
    with patch('src.core.real_reasoning_engine.ExtractionOperator') as MockExtOp:
        MockExtOp.return_value.execute = AsyncMock(return_value=MagicMock(success=False))
        
        # Define a simple plan
        initial_plan = [
            {
                "id": "step_1",
                "step_id": "step_1",
                "description": "Identify the author",
                "sub_query": "Who wrote 'The Last of the Mohicans'?",
                "type": "evidence_gathering",
                "dependencies": []
            }
        ]
        
        # Execute
        result = await engine._execute_deep_reasoning_loop(
            query="Who wrote 'The Last of the Mohicans'?",
            initial_plan=initial_plan,
            context={}
        )
        
        # Verify
        # 1. Check if gather_evidence was called
        engine.evidence_processor.gather_evidence.assert_called()
        
        # 2. Check if LLM fallback was called
        engine.llm_integration.generate_response.assert_called()
        args, _ = engine.llm_integration.generate_response.call_args
        assert "Answer the following question directly" in args[0]
        
        # 3. Check if result contains the fallback answer
        step_1_result = result.reasoning_steps[0]['result']
        assert "James Fenimore Cooper" in step_1_result
        
        print("✅ Fallback logic verified: LLM used when evidence gathering failed.")

if __name__ == "__main__":
    asyncio.run(test_fallback_logic_when_evidence_fails())
