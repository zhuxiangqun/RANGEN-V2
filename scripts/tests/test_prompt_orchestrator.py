import asyncio
import unittest
from unittest.mock import MagicMock, patch
from src.services.prompt_engineering.orchestrator import PromptOrchestrator
from src.core.neural.factory import NeuralServiceFactory

# Mock Reranker that scores based on simple keyword matching
class SmartMockReranker:
    async def rerank(self, query, documents):
        scores = []
        query_lower = query.lower()
        # Mock Reranker that scores based on simple keyword matching
        # Note: In the real app, we rerank based on the 'query' field of the example.
        for doc in documents:
            score = 0.0
            doc_lower = doc.lower()
            
            # Math Logic
            # Query: "Calculate..." -> Match example: "What is 25 * 48?"
            if ("math" in query_lower or "calculate" in query_lower or "*" in query_lower):
                if ("*" in doc_lower or "what is" in doc_lower and any(c.isdigit() for c in doc_lower)):
                     score = 0.9
            
            # History Logic
            # Query: "Who wrote..." -> Match example: "Who invented..."
            elif ("who" in query_lower or "history" in query_lower):
                if ("who" in doc_lower or "invented" in doc_lower):
                     score = 0.9
            
            # Coding Logic
            elif ("code" in query_lower or "python" in query_lower):
                 if ("python" in doc_lower or "def " in doc_lower):
                     score = 0.9
            
            # Default low score
            if score == 0.0:
                score = 0.1
                
            scores.append((doc, score))
        
        # Sort by score descending
        return sorted(scores, key=lambda x: x[1], reverse=True)

class TestPromptOrchestrator(unittest.TestCase):
    def setUp(self):
        # Reset factory to ensure clean state
        NeuralServiceFactory.reset()
        
    @patch('src.core.neural.factory.NeuralServiceFactory.get_reranker')
    def test_few_shot_selection(self, mock_get_reranker):
        # Setup Mock
        mock_reranker = SmartMockReranker()
        mock_get_reranker.return_value = mock_reranker
        
        # Initialize Orchestrator
        orchestrator = PromptOrchestrator()
        
        # Run Async Test
        async def run_test():
            # Test 1: Math Query
            query_math = "Calculate 100 * 200"
            prompt_math = await orchestrator.construct_prompt("Base Template", query_math)
            
            print(f"\n[Test 1] Query: {query_math}")
            print(f"Result Prompt Snippet: {prompt_math.split('CURRENT TASK')[0][-200:]}...")
            
            # Assert that the math example (25 * 48) was selected
            self.assertIn("25 * 48", prompt_math)
            self.assertNotIn("invented the telephone", prompt_math)
            
            # Test 2: History Query
            query_history = "Who wrote Romeo and Juliet?"
            prompt_history = await orchestrator.construct_prompt("Base Template", query_history)
            
            print(f"\n[Test 2] Query: {query_history}")
            print(f"Result Prompt Snippet: {prompt_history.split('CURRENT TASK')[0][-200:]}...")
            
            # Assert that the history example (telephone) was selected
            self.assertIn("invented the telephone", prompt_history)
            self.assertNotIn("25 * 48", prompt_history)
            
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
