
import unittest
from unittest.mock import MagicMock, patch

import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoning.step_generator import StepGenerator

class TestLiveRelevanceValidation(unittest.TestCase):
    def setUp(self):
        self.step_generator = StepGenerator()
        
    def test_relevance_validation_rejects_irrelevant_steps(self):
        fake_steps = [
            {
                "step_id": "1",
                "type": "information_retrieval",
                "description": "Calculate the height of the Eiffel Tower",
                "sub_query": "height of Eiffel Tower",
            },
            {
                "step_id": "2",
                "type": "information_retrieval",
                "description": "Find the capital of France",
                "sub_query": "capital of France",
            },
        ]

        mock_relevance_validator = MagicMock(
            return_value={
                "is_relevant": False,
                "reason": "mocked as irrelevant",
                "irrelevant_steps": [
                    {
                        "step_id": "1",
                        "description": "Calculate the height of the Eiffel Tower",
                    }
                ],
            }
        )

        self.step_generator.cache_manager = None
        self.step_generator._call_llm_with_cache = MagicMock(return_value="DUMMY_RESPONSE")
        self.step_generator._parse_llm_response = MagicMock(return_value=fake_steps)
        self.step_generator._validate_steps = MagicMock(
            return_value={"is_valid": True, "reason": "ok", "quality_score": 0.9}
        )
        self.step_generator._validate_reasoning_relevance = mock_relevance_validator
        self.step_generator.llm_integration = MagicMock()

        query = "How to use python pandas dataframe?"
        context = {}

        self.step_generator._generate_fallback_steps = MagicMock(return_value=[{"step_id": "fallback"}])
        result = self.step_generator.execute_reasoning_steps_with_prompts(query, context)

        self.step_generator._call_llm_with_cache.assert_called()
        mock_relevance_validator.assert_called()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertEqual(result[0].get("step_id"), "fallback")


if __name__ == '__main__':
    unittest.main()
