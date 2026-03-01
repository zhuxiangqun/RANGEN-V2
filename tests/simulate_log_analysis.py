
import sys
import os
import asyncio
import logging
import unittest
from unittest.mock import MagicMock, patch

# Add root directory to path
sys.path.append(os.getcwd())

from src.core.reasoning.step_generator import StepGenerator

# Configure logging to file
log_file = "simulation_debug.log"
if os.path.exists(log_file):
    os.remove(log_file)

file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Root logger
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)

class TestLogAnalysis(unittest.TestCase):
    def setUp(self):
        self.step_generator = StepGenerator()
        # Mock dependencies
        self.step_generator.llm_integration = MagicMock()
        self.step_generator.prompt_generator = MagicMock()
        self.step_generator.prompt_generator.generate_optimized_prompt.return_value = "Mock Prompt Content for Python Pandas"
        
        # Mock config
        self.step_generator.config = MagicMock()
        self.step_generator.config.validation.semantic_similarity_threshold = 0.6
        self.step_generator.config.validation.topic_overlap_threshold = 0.5
        self.step_generator.config.validation.irrelevant_keywords = {'france', 'capital'}

    def test_log_capture_fallback(self):
        """Simulate a fallback scenario and check logs"""
        print("\n🚀 Simulating Fallback Scenario (Timeout/Failure)...")
        
        # Mock LLM returning None to trigger fallback
        self.step_generator.llm_integration.generate_response.return_value = None
        # Mock cache manager if present
        if hasattr(self.step_generator, 'cache_manager'):
             self.step_generator.cache_manager = MagicMock()
             self.step_generator.cache_manager.call_llm_with_cache.return_value = None
        
        # We need to mock _call_llm_with_cache as well just in case
        with patch.object(self.step_generator, '_call_llm_with_cache', return_value=None):
            steps = self.step_generator.execute_reasoning_steps_with_prompts(
                query="python pandas dataframe filtering",
                context={},
                original_query="python pandas dataframe filtering"
            )
            
        print(f"Generated {len(steps)} steps via fallback.")

    def test_log_capture_success(self):
        """Simulate a successful scenario and check logs"""
        print("\n🚀 Simulating Success Scenario...")
        
        mock_response = """
        ```json
        {
            "steps": [
                {
                    "type": "evidence_gathering",
                    "description": "Understand pandas filtering",
                    "sub_query": "How to filter dataframe in pandas?"
                },
                {
                    "type": "coding",
                    "description": "Write filtering code",
                    "sub_query": "Code example for pandas filtering"
                }
            ]
        }
        ```
        """
        
        with patch.object(self.step_generator, '_call_llm_with_cache', return_value=mock_response):
            # Also mock embedding for validation to pass
            with patch.object(self.step_generator, '_get_text_embedding', return_value=[0.1]*768):
                steps = self.step_generator.execute_reasoning_steps_with_prompts(
                    query="python pandas dataframe filtering",
                    context={},
                    original_query="python pandas dataframe filtering"
                )
        
        print(f"Generated {len(steps)} steps via LLM.")

if __name__ == "__main__":
    unittest.main(exit=False)
    
    print("\n" + "="*50)
    print("LOG ANALYSIS REPORT")
    print("="*50)
    if os.path.exists(log_file):
        with open(log_file, 'r') as f:
            content = f.read()
            # Filter for our key logs
            key_logs = [
                "Beginning Step Generation",
                "PROMPT DEBUG",
                "RESPONSE DEBUG",
                "VALIDATION DEBUG",
                "Fallback",
                "Triggering fallback"
            ]
            
            for line in content.split('\n'):
                if any(k in line for k in key_logs) or "ERROR" in line or "WARNING" in line:
                    print(line[:200] + "..." if len(line) > 200 else line)
    else:
        print("Log file not found!")
