
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.reasoning.step_generator import StepGenerator

class TestFallbackSemanticValidation(unittest.TestCase):
    def setUp(self):
        self.step_generator = StepGenerator()
        # Mock logger to avoid clutter
        self.step_generator.logger = MagicMock()

    @patch('src.core.reasoning.step_generator.get_semantic_understanding_pipeline')
    def test_coding_fallback_semantic_validation_high_similarity(self, mock_get_pipeline):
        # Setup mock pipeline
        mock_pipeline = MagicMock()
        mock_get_pipeline.return_value = mock_pipeline
        mock_pipeline.are_models_available.return_value = True
        
        # Mock embeddings and cosine similarity
        mock_pipeline.understand_query.return_value = {"embedding": [1.0, 0.0]}
        mock_pipeline._sentence_transformer_util.cos_sim.return_value.item.return_value = 0.9 # High similarity
        
        # Call _generate_fallback_steps
        query = "python pandas dataframe"
        steps = self.step_generator._generate_fallback_steps(query, query_type="coding")
        
        # Verify
        self.assertTrue(len(steps) > 0)
        self.assertEqual(steps[0]["type"], "evidence_gathering")
        # Check that description was NOT modified (no "related to" added)
        self.assertNotIn("related to 'python pandas dataframe'", steps[0]["description"])
        
        # Verify semantic check was performed
        mock_pipeline.understand_query.assert_called()
        self.step_generator.logger.info.assert_any_call(f"🔍 [Fallback] 编程步骤语义相似度: 0.9000")

    @patch('src.core.reasoning.step_generator.get_semantic_understanding_pipeline')
    def test_coding_fallback_semantic_validation_low_similarity(self, mock_get_pipeline):
        # Setup mock pipeline
        mock_pipeline = MagicMock()
        mock_get_pipeline.return_value = mock_pipeline
        mock_pipeline.are_models_available.return_value = True
        
        # Mock embeddings and cosine similarity
        mock_pipeline.understand_query.return_value = {"embedding": [1.0, 0.0]}
        mock_pipeline._sentence_transformer_util.cos_sim.return_value.item.return_value = 0.1 # Low similarity
        
        # Call _generate_fallback_steps
        query = "python pandas dataframe"
        steps = self.step_generator._generate_fallback_steps(query, query_type="coding")
        
        # Verify
        self.assertTrue(len(steps) > 0)
        # Check that description WAS modified
        self.assertIn("related to 'python pandas dataframe'", steps[0]["description"])
        
        # Verify warning log
        self.step_generator.logger.warning.assert_any_call("⚠️ [Fallback] 编程步骤可能不相关 (相似度 0.1000 < 0.2)，尝试修正")

if __name__ == '__main__':
    unittest.main()
