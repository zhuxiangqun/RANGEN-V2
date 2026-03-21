
from typing import Dict, List, Any
import time
import asyncio
from .base_strategy import BaseRetrievalStrategy, RetrievalResult

class CoTRetrievalStrategy(BaseRetrievalStrategy):
    """
    Chain-of-Thought Retrieval Strategy (Beta > 1.4)
    
    Complex retrieval that involves:
    1. Analyzing the query to identify missing information.
    2. Generating sub-queries.
    3. Multi-path retrieval.
    4. Reasoning about the results.
    """
    
    def __init__(self, llm_service, knowledge_service, config: Dict = None):
        super().__init__("cot", config)
        self.llm = llm_service
        self.kms = knowledge_service
        
    async def execute(self, query: str, context: Dict) -> RetrievalResult:
        start_time = time.time()
        
        # Step 1: Analyze and Plan (Decompose)
        # For P1, we implement a simplified version: Generate sub-queries directly
        sub_queries = await self._generate_sub_queries(query)
        
        # Step 2: Parallel Retrieval
        all_results = []
        if sub_queries:
            tasks = [self._single_retrieve(q) for q in sub_queries]
            results_list = await asyncio.gather(*tasks)
            for res in results_list:
                all_results.extend(res)
        else:
            # Fallback if no sub-queries
            all_results = await self._single_retrieve(query)
            
        # Step 3: Deduplicate and Merge
        merged_results = self._merge_results(all_results)
        
        # Step 4: (Optional) Relation Reasoning - "No-Graph" Optimization
        # This aligns with Section 4.14.2 Document Relation Reasoner
        # For now, we just return the merged results, but we add metadata indicating CoT was used
        
        execution_time = time.time() - start_time
        
        return RetrievalResult(
            documents=merged_results[:self.config.get("top_k", 10)], # Return top results
            strategy_name=self.name,
            execution_time=execution_time,
            metadata={
                "original_query": query,
                "sub_queries": sub_queries,
                "beta": context.get("beta", 0.0)
            }
        )
    
    async def _generate_sub_queries(self, query: str) -> List[str]:
        """Generate sub-queries using LLM"""
        prompt = (
            f"Analyze the following complex query and break it down into 2-3 simple, distinct search queries "
            f"that would help answer it comprehensively.\n"
            f"Query: {query}\n"
            f"Output only the sub-queries, one per line."
        )
        
        try:
            response = await self.llm.generate(prompt, temperature=0.5, max_tokens=100)
            # Parse lines
            queries = [line.strip().strip('- ') for line in response.split('\n') if line.strip()]
            return queries[:3] # Limit to 3
        except Exception as e:
            # Fallback
            return [query]

    async def _single_retrieve(self, query: str) -> List[Dict]:
        """Helper for single retrieval"""
        # Similar to DirectStrategy logic
        if hasattr(self.kms, 'search_vector'):
            return await self.kms.search_vector(query, top_k=5)
        else:
            return self.kms.query_knowledge(query, top_k=5)
            
    def _merge_results(self, results: List[Dict]) -> List[Dict]:
        """Simple deduplication based on content or ID"""
        seen = set()
        merged = []
        for doc in results:
            # Assuming doc has 'id' or we use 'content' hash
            # P0 KMS returns dict with 'content', 'source', 'score'
            content = doc.get('content', '')
            if content and content not in seen:
                seen.add(content)
                merged.append(doc)
        
        # Sort by score if available
        merged.sort(key=lambda x: x.get('score', 0), reverse=True)
        return merged
