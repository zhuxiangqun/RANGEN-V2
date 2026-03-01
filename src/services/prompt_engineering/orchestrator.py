"""
Prompt Orchestrator
Dynamically constructs prompts based on task context and few-shot examples.
"""
from typing import List, Dict, Optional
import json
import asyncio
from src.services.logging_service import get_logger
from src.core.neural.factory import NeuralServiceFactory

logger = get_logger(__name__)

class PromptOrchestrator:
    """
    Orchestrates prompt construction by combining:
    1. Base Templates
    2. Dynamic Few-Shot Examples (retrieved via Neural Reranker)
    3. Context Summaries
    4. Style/Role Instructions
    """
    
    def __init__(self):
        # Inject Neural Reranker
        self.reranker = NeuralServiceFactory.get_reranker()
        
        # Load examples from a JSON file or define them here
        # In future, load from 'data/prompt_examples.json'
        self._example_store = self._load_initial_examples()
        
    def _load_initial_examples(self) -> List[Dict]:
        """
        Define a rich set of examples for retrieval.
        Structure: {"query": str, "trace": str, "tags": List[str]}
        """
        return [
            {
                "query": "Who invented the telephone?",
                "trace": "Thought: I need to identify the inventor. This is a disputed topic.\nAction: knowledge_retrieval(query='telephone inventor')\nObservation: Alexander Graham Bell is credited, but Antonio Meucci and Elisha Gray also have claims.\nThought: I should mention the controversy.\nFinal Answer: Alexander Graham Bell is widely credited with patenting the first practical telephone, though Antonio Meucci and Elisha Gray also made significant contributions.",
                "tags": ["research", "history", "controversy"]
            },
            {
                "query": "What is 25 * 48?",
                "trace": "Thought: This is a math problem. I can calculate it directly or use python.\nAction: python_repl(code='print(25*48)')\nObservation: 1200\nFinal Answer: 1200",
                "tags": ["calculation", "math"]
            },
            {
                "query": "How do I implement a binary search in Python?",
                "trace": "Thought: The user wants code for binary search. I should provide a clean implementation and explain it.\nAction: knowledge_retrieval(query='binary search python implementation')\nObservation: [Code snippet found]\nThought: I will write the code based on standard algorithm.\nFinal Answer: Here is the Python code for binary search:\n```python\ndef binary_search(arr, target):\n    ...\n```",
                "tags": ["coding", "python", "algorithm"]
            },
             {
                "query": "Analyze the sentiment of this review: 'The movie was okay, but the ending ruined it.'",
                "trace": "Thought: I need to analyze the sentiment. 'Okay' is neutral/positive, but 'ruined it' is strongly negative.\nFinal Answer: The sentiment is mixed but leaning negative due to the strong criticism of the ending.",
                "tags": ["nlp", "sentiment", "analysis"]
            }
        ]
    
    async def _get_few_shot_examples(self, query: str, n: int = 1) -> str:
        """
        Retrieve relevant few-shot examples using Neural Reranker.
        """
        if not self._example_store:
            return ""
            
        try:
            # 1. Extract query texts from examples
            candidate_queries = [ex["query"] for ex in self._example_store]
            
            # 2. Rerank based on similarity to current query
            # This finds examples that are SEMANTICALLY similar to the user's request
            scores = await self.reranker.rerank(query, candidate_queries)
            
            # 3. Select top N
            top_indices = []
            for doc, score in scores[:n]:
                # Find the index of the doc (inefficient for large lists, but fine for <100 examples)
                idx = candidate_queries.index(doc)
                top_indices.append(idx)
                
            selected_examples = [self._example_store[i] for i in top_indices]
            
            # Format
            formatted = "Here are some RELEVANT examples of how to reason for similar tasks:\n\n"
            for i, ex in enumerate(selected_examples, 1):
                formatted += f"Example {i}:\nUser: {ex['query']}\n{ex['trace']}\n\n"
                
            return formatted
            
        except Exception as e:
            logger.warning(f"Few-shot retrieval failed: {e}. Falling back to random/first example.")
            # Fallback: just return the first one
            ex = self._example_store[0]
            return f"Example:\nUser: {ex['query']}\n{ex['trace']}\n"

    async def construct_prompt(self, base_template: str, query: str, context_summary: str = "", task_type: str = "general") -> str:
        """
        Assemble the final prompt.
        """
        # 1. Get Examples (Async now)
        examples = await self._get_few_shot_examples(query)
        
        # 2. Inject Context Summary (if any)
        context_section = ""
        if context_summary:
            context_section = f"\nPREVIOUS CONTEXT SUMMARY:\n{context_summary}\n"
            
        # 3. Assemble
        full_prompt = f"""
{base_template}

{context_section}

{examples}

CURRENT TASK:
User: {query}
"""
        return full_prompt.strip()
