
import sys
import os
import json
import logging
from typing import Dict, Any, Optional

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoning.step_generator import StepGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("TestComplexQuery")

# Mock LLM Integration
class MockLLMIntegration:
    def __init__(self):
        self.call_count = 0
        
    def call_llm(self, prompt: str, response_format: Optional[Dict] = None, temperature: float = 0.1) -> str:
        self.call_count += 1
        print(f"\n📝 [Mock LLM] Prompt received (Call #{self.call_count}):")
        print("-" * 20 + " PROMPT START " + "-" * 20)
        # Print the prompt to verify content
        print(prompt)
        print("-" * 20 + " PROMPT END " + "-" * 20)
        
        # Simulate response based on the query in the prompt
        # We'll simulate a valid response for the complex query
        
        response = {
            "reasoning": {
                "thought_process": "User wants to find the name of their future wife based on a complex riddle. The riddle involves: 1. 15th First Lady's mother's first name. 2. 2nd assassinated President's mother's maiden name. I need to break this down into retrieval steps.",
                "risk_factors": ["Ambiguity of 'future wife'", "Historical data accuracy"],
                "uncertainty_level": "Medium"
            },
            "steps": [
                {
                    "type": "information_retrieval",
                    "description": "Identify the 15th First Lady of the United States",
                    "sub_query": "Who was the 15th First Lady of the United States?"
                },
                {
                    "type": "information_retrieval",
                    "description": "Find the name of the mother of the 15th First Lady",
                    "sub_query": "Who was the mother of [step 1 result]?"
                },
                {
                    "type": "information_retrieval",
                    "description": "Identify the second assassinated President of the United States",
                    "sub_query": "Who was the second assassinated President of the US?"
                },
                {
                    "type": "information_retrieval",
                    "description": "Find the maiden name of the mother of the second assassinated President",
                    "sub_query": "What was the maiden name of the mother of [step 3 result]?"
                },
                {
                    "type": "answer_synthesis",
                    "description": "Combine the first name from step 2 and surname from step 4 to determine the future wife's name",
                }
            ]
        }
        
        return json.dumps(response)

def test_complex_query():
    query = "If my future wife has the same first name as the 15th first lady of the United States' mother and her surname is the same as the second assassinated president's mother's maiden name, what is my future wife's name?"
    
    print(f"\n🔍 Testing Complex Query: {query}\n")
    print("-" * 50)
    
    # Initialize with Mock LLM
    mock_llm = MockLLMIntegration()
    generator = StepGenerator(llm_integration=mock_llm)
    
    try:
        # Generate steps
        result = generator.generate_steps_with_retry(query)
        
        print("\n✅ Generation Successful!")
        
        if isinstance(result, list):
             print("\n📋 Generated Steps:")
             for i, step in enumerate(result, 1):
                print(f"\nStep {i}:")
                print(f"  Type: {step.get('type')}")
                print(f"  Description: {step.get('description')}")
                print(f"  Sub-query: {step.get('sub_query', 'N/A')}")
        else:
             print(f"\n⚠️ Unexpected result: {result}")
            
    except Exception as e:
        print(f"\n❌ Generation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complex_query()
