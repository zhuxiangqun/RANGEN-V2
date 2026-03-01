
from typing import Dict, List, Any
import time
from .base_strategy import BaseRetrievalStrategy, RetrievalResult

class DirectRetrievalStrategy(BaseRetrievalStrategy):
    """
    Direct Retrieval Strategy (Beta < 0.5)
    
    Simple, fast retrieval based on the original query. 
    Suitable for factual questions or when low latency is required.
    """
    
    def __init__(self, knowledge_service, config: Dict = None):
        super().__init__("direct", config)
        self.kms = knowledge_service
        
    async def execute(self, query: str, context: Dict) -> RetrievalResult:
        start_time = time.time()
        
        # Simple retrieval using the KMS service
        # Note: In a real scenario, we might want to apply filters from context
        top_k = self.config.get("top_k", 5)
        
        # Using the atomic search interface if available, otherwise standard query
        if hasattr(self.kms, 'search_vector'):
            search_results = await self.kms.search_vector(query, top_k=top_k)
        else:
            # Fallback to standard interface
            # Assuming query_knowledge is synchronous or handles async internally if designed that way
            # But based on P0, we might need to be careful. 
            # In P0 test, we used kms.query_knowledge which returned a list.
            search_results = self.kms.query_knowledge(
                query=query,
                top_k=top_k
            )
            
        execution_time = time.time() - start_time
        
        return RetrievalResult(
            documents=search_results,
            strategy_name=self.name,
            execution_time=execution_time,
            metadata={
                "original_query": query,
                "beta": context.get("beta", 0.0)
            }
        )
