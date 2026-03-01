
import sys
import os
import logging
import json
from typing import Dict, Optional

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoning.step_generator import StepGenerator

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Mock LLM that returns HALLUCINATED steps
class MockHallucinatingLLM:
    def __init__(self, mode="neptune"):
        self.mode = mode
        
    def call_llm(self, prompt: str, response_format: Optional[Dict] = None, temperature: float = 0.1) -> str:
        print(f"\n📝 [Mock LLM] Generating hallucinated response (Mode: {self.mode})")
        
        if self.mode == "neptune":
            # Copying the Neptune example
            response = {
                "reasoning": {
                    "thought_process": "User wants to find the rotation period of Neptune.",
                    "risk_factors": [],
                    "uncertainty_level": "Low"
                },
                "steps": [
                    {
                        "type": "information_retrieval",
                        "description": "Identify the planet Neptune and its rotational characteristics",
                        "sub_query": "What is the planet Neptune?"
                    },
                    {
                        "type": "information_retrieval",
                        "description": "Find the rotation period of Neptune",
                        "sub_query": "What is the rotation period of Neptune?"
                    },
                     {
                        "type": "answer_synthesis",
                        "description": "Combine findings"
                    }
                ]
            }
        elif self.mode == "france":
            # Unrelated "France" steps
            response = {
                "reasoning": {
                    "thought_process": "I need to find the capital of France.",
                    "risk_factors": [],
                    "uncertainty_level": "Low"
                },
                "steps": [
                    {
                        "type": "information_retrieval",
                        "description": "Find the capital of France",
                        "sub_query": "What is the capital of France?"
                    },
                    {
                        "type": "answer_synthesis",
                        "description": "The capital is Paris."
                    }
                ]
            }
            
        return json.dumps(response)

def test_python_query():
    # Python query that previously caused "French Capital" hallucinations
    query = "How do I use list comprehension in Python to filter even numbers?"
    
    print(f"\n🔍 Testing Query: {query}")
    
    # Test 1: Neptune Hallucination
    print("\n--- Test 1: Neptune Hallucination ---")
    mock_llm_neptune = MockHallucinatingLLM(mode="neptune")
    generator = StepGenerator(llm_integration=mock_llm_neptune)
    
    try:
        result = generator.generate_steps_with_retry(query, max_attempts=2) # Only 2 attempts to save time
        
        if result is None:
            print("✅ SUCCESS: Neptune hallucination was rejected (returned None).")
        else:
            print("❌ FAILURE: Neptune hallucination was ACCEPTED!")
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 2: France Hallucination
    print("\n--- Test 2: France Hallucination ---")
    mock_llm_france = MockHallucinatingLLM(mode="france")
    generator = StepGenerator(llm_integration=mock_llm_france)
    
    try:
        result = generator.generate_steps_with_retry(query, max_attempts=2)
        
        if result is None:
            print("✅ SUCCESS: France hallucination was rejected (returned None).")
        else:
            print("❌ FAILURE: France hallucination was ACCEPTED!")
            print(result)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_python_query()
