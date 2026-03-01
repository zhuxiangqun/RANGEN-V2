import sys
import os
import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock, patch

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

# Mock missing dependencies before importing RealReasoningEngine
sys.modules['src.core.operators'] = MagicMock()
mock_state_module = MagicMock()
mock_state_instance = MagicMock()
mock_state_instance.is_solved.return_value = False
mock_state_instance.budget_exhausted.return_value = False
mock_state_module.ReasoningState.return_value = mock_state_instance
sys.modules['src.core.reasoning_state'] = mock_state_module

from src.core.real_reasoning_engine import RealReasoningEngine

async def reproduce():
    print("🚀 Starting reproduction script...")
    
    # Patch initialization methods to avoid real initialization
    with patch.object(RealReasoningEngine, '_initialize_config_center', return_value=MagicMock()), \
         patch.object(RealReasoningEngine, '_initialize_llm_integration', return_value=MagicMock()), \
         patch.object(RealReasoningEngine, '_initialize_fast_llm_integration', return_value=MagicMock()), \
         patch.object(RealReasoningEngine, '_initialize_prompt_engineering', return_value=MagicMock()), \
         patch.object(RealReasoningEngine, '_initialize_context_engineering', return_value=MagicMock()), \
         patch.object(RealReasoningEngine, '_initialize_unified_prompt_manager', return_value=MagicMock()), \
         patch.object(RealReasoningEngine, '_initialize_evidence_preprocessor', return_value=MagicMock()):
        
        engine = RealReasoningEngine()
        
        # Inject mocks for components used in the loop
        engine.subquery_processor = MagicMock()
        # Mock subquery_processor methods
        engine.subquery_processor.validate_and_clean_sub_query.side_effect = lambda q, *args, **kwargs: q
        # enhance_sub_query_with_context should return the replaced string
        def enhance_side_effect(sub_query, dep_value, *args, **kwargs):
            if not dep_value:
                return sub_query
            return sub_query.replace("[step 1 result]", str(dep_value))
        engine.subquery_processor.enhance_sub_query_with_context.side_effect = enhance_side_effect
        
        engine.subquery_processor.validate_replacement_context.return_value = True # Important!
        
        engine.step_generator = MagicMock()
        engine.step_generator.analyze_dependencies.return_value = ([0], {}) # Depends on step 0 (Step 1)
        
        engine.answer_extractor = MagicMock()
        engine.answer_extractor.validator.validate_step_answer_reasonableness.return_value = True
        engine.answer_extractor.extract = AsyncMock(return_value=MagicMock(answer="Final Answer", success=True))
        
        engine.operators = {
            'extraction': MagicMock(),
            'comparison': MagicMock(),
            'synthesis': MagicMock(),
            'tool_use': MagicMock()
        }
        
        engine.learning_manager = MagicMock()
        engine.cache_manager = MagicMock()
        
        # Define the query
        query = "Who wrote the book 'The Last of the Mohicans' and when was he born?"
        
        # Define the plan
        initial_plan = [
            {
                "id": 1,
                "sub_query": "Who wrote the book 'The Last of the Mohicans'?",
                "type": "extraction",
                "description": "Find the author"
            },
            {
                "id": 2,
                "sub_query": "What year was [step 1 result] born?",
                "type": "extraction",
                "description": "Find the birth year"
            }
        ]
        
        # Mock fast_llm_integration methods
        engine.fast_llm_integration = MagicMock()
        engine.fast_llm_integration.analyze_query_complexity = AsyncMock(return_value={"is_simple": False, "beta": 1.0})
        
        # Mock _generate_initial_plan
        engine._generate_initial_plan = AsyncMock(return_value=initial_plan)
        
        # Mock _generate_reasoning_steps (just in case)
        engine._generate_reasoning_steps = AsyncMock(return_value=initial_plan)
        engine._analyze_query_type = AsyncMock(return_value="complex")
        engine._initialize_reasoning_context = AsyncMock(return_value=({}, "session_1"))
        engine._validate_and_decompose_steps = AsyncMock(side_effect=lambda x, y: x)
        engine._reflect_and_improve = AsyncMock(return_value=False)
        engine._calculate_authentic_confidence = AsyncMock(return_value=1.0)
        
        # Setup operator execution results
        # Scenario 1: Step 1 succeeds with an answer
        op_result_success = MagicMock()
        op_result_success.success = True
        op_result_success.data = "James Fenimore Cooper"
        
        # Scenario 2: Step 1 succeeds but NO answer (or empty)
        op_result_empty = MagicMock()
        op_result_empty.success = True
        op_result_empty.data = "" 
        
        # Configure the operator to return success for Step 1
        async def execute_side_effect(inputs, context):
            text = inputs.get('text', '')
            if "Who wrote" in text:
                print(f"Executing Step 1: {text}")
                return op_result_success
            elif "What year" in text:
                print(f"Executing Step 2: {text}")
                if "[step 1 result]" in text:
                    print("❌ Step 2 executed with placeholder! Replacement FAILED.")
                    return MagicMock(success=False, error="Placeholder not replaced")
                else:
                    print(f"✅ Step 2 executed with replaced query: {text}")
                    return MagicMock(success=True, data="1789")
            return MagicMock(success=False)

        engine.operators['extraction'].execute = AsyncMock(side_effect=execute_side_effect)
        
        # Mock evidence processor
        engine.evidence_processor = MagicMock()
        engine.evidence_processor.gather_evidence = AsyncMock(return_value=[])

        print("\n--- Running Scenario: Step 1 returns valid answer ---")
        try:
            # Check for reason method
            if hasattr(engine, 'reason'):
                await engine.reason(query, context={})
            elif hasattr(engine, 'execute'):
                await engine.execute(query, context={})
            else:
                # Try to find the method that iterates over reasoning_steps
                print("Method 'reason' not found. Inspecting available methods...")
                print([m for m in dir(engine) if not m.startswith('__')])
                
        except Exception as e:
            print(f"Execution failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(reproduce())
