import sys
import os
import re
from unittest.mock import MagicMock
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.core.reasoning.step_generator import StepGenerator
from src.core.reasoning.prompt_generator import PromptGenerator

def test_complex_query():
    # Setup
    llm_mock = MagicMock()
    
    # Define a realistic response for this query to simulate what a good LLM would do
    # This helps verify the parsing logic
    simulated_response = """
    {
        "reasoning": {
            "thought_process": "This is a complex riddle-like query requiring multiple factual retrievals. I need to break it down into identifying the 15th First Lady, her mother, the 2nd assassinated president, his mother, and her maiden name.",
            "risk_factors": ["Ambiguity in '2nd assassinated president' definition", "Maiden name availability"],
            "uncertainty_level": "Medium"
        },
        "steps": [
            {
                "step": 1,
                "type": "information_retrieval",
                "description": "Identify the 15th First Lady of the United States",
                "sub_query": "Who was the 15th First Lady of the United States?",
                "confidence": 0.95
            },
            {
                "step": 2,
                "type": "information_retrieval",
                "description": "Find the name of the 15th First Lady's mother",
                "sub_query": "Who was the mother of [step 1 result]?",
                "confidence": 0.9
            },
            {
                "step": 3,
                "type": "information_retrieval",
                "description": "Identify the second US President to be assassinated",
                "sub_query": "List of assassinated US presidents in chronological order",
                "confidence": 0.95
            },
            {
                "step": 4,
                "type": "information_retrieval",
                "description": "Find the maiden name of the second assassinated president's mother",
                "sub_query": "What was the maiden name of the mother of [step 3 result]?",
                "confidence": 0.9
            },
            {
                "step": 5,
                "type": "logical_deduction",
                "description": "Synthesize the final answer by combining the first name from step 2 and surname from step 4",
                "sub_query": "Combine [step 2 result first name] and [step 4 result surname]",
                "confidence": 1.0
            }
        ]
    }
    """
    
    # We want to capture the prompt
    captured_prompts = []
    def capture_prompt(prompt, **kwargs):
        captured_prompts.append(prompt)
        return simulated_response
    
    llm_mock.get_response.side_effect = capture_prompt
    llm_mock.call_llm.side_effect = capture_prompt  # Added this
    llm_mock._call_llm.side_effect = capture_prompt
    llm_mock._call_llm_with_cache.side_effect = capture_prompt

    prompt_gen = PromptGenerator()
    generator = StepGenerator(llm_integration=llm_mock, prompt_generator=prompt_gen)
    
    # Ensure parallel classifier is disabled to test main path
    generator.parallel_classifier_enabled = False
    generator.transformer_planner_enabled = False
    
    query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    print(f"Testing Query: {query}")
    
    try:
        steps = generator.generate_reasoning_steps(query)
        
        print(f"\n✅ Generated {len(steps)} Steps:")
        for step in steps:
            print(f"- Step {step.get('step')}: {step.get('description')}")
            print(f"  Sub-query: {step.get('sub_query')}")
            
        print("\n--- Prompt Analysis ---")
        if captured_prompts:
            # Check the last prompt (likely the one used for generation)
            last_prompt = captured_prompts[-1]
            print(f"Prompt Length: {len(last_prompt)}")
            
            # 1. Check Query Type Detection in Prompt
            if "COMPLEX" in last_prompt or "general" in last_prompt:
                 print("✅ Query type treated as General/Complex")
            
            # 2. Check for Multi-hop/Dependency instructions
            # The system prompt should encourage using [step X result]
            if "step" in last_prompt.lower() and "result" in last_prompt.lower():
                 print("✅ Prompt contains dependency instructions (step/result)")
            else:
                 print("⚠️ Prompt might be missing explicit dependency instructions")
                 
            # 3. Check for specific keywords
            if "first lady" in last_prompt.lower():
                print("✅ Original query included in prompt")
                
            # 4. Check for hallucinated Eiffel Tower
            if "Eiffel Tower" in last_prompt and "Python" not in query:
                 print("ℹ️ Standard examples used (Expected for non-coding query)")
            elif "Eiffel Tower" not in last_prompt:
                 print("ℹ️ Standard examples NOT used (Might be dynamic)")
                 
        else:
            print("❌ No prompt captured!")
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complex_query()
