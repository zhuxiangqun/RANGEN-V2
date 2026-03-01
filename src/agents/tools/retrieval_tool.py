"""
Standard Retrieval Tool wrapping Knowledge Management System
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.interfaces.tool import ITool, ToolConfig, ToolResult, ToolCategory
from src.services.logging_service import get_logger
from src.core.neural.factory import NeuralServiceFactory

# Import the KnowledgeManagementService
# Note: We assume the KMS is already initialized or will be initialized on first use
try:
    from knowledge_management_system.api.service_interface import get_knowledge_service
except ImportError:
    # Placeholder for testing or if KMS is not yet available
    get_knowledge_service = None

logger = get_logger(__name__)

class RetrievalParameters(BaseModel):
    """Parameters for retrieval tool"""
    query: str = Field(..., description="The search query string")
    top_k: int = Field(5, description="Number of results to return", ge=1, le=20)
    similarity_threshold: float = Field(0.6, description="Minimum similarity score", ge=0.0, le=1.0)
    use_graph: bool = Field(False, description="Whether to use knowledge graph for retrieval")

class RetrievalTool(ITool):
    """
    Tool for retrieving information from the Vector Knowledge Base.
    Wraps the KnowledgeManagementService.
    """
    
    def __init__(self):
        config = ToolConfig(
            name="knowledge_retrieval",
            category=ToolCategory.RETRIEVAL,
            description="Retrieve relevant information from the knowledge base using vector search.",
            version="1.0.0"
        )
        super().__init__(config)
        self._kms = None
        
        # Neural Reranker
        self.reranker = NeuralServiceFactory.get_reranker()
        
        logger.info("RetrievalTool initialized")

    @property
    def kms(self):
        """Lazy load KMS instance"""
        if self._kms is None:
            if get_knowledge_service:
                self._kms = get_knowledge_service()
            else:
                logger.error("KnowledgeManagementService not available")
        return self._kms

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return the JSON schema for tool parameters"""
        return RetrievalParameters.model_json_schema()

    def validate_parameters(self, **kwargs) -> bool:
        """Validate input parameters"""
        try:
            RetrievalParameters(**kwargs)
            return True
        except Exception:
            return False

    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the retrieval.
        
        Args:
            query (str): Search query
            top_k (int): Number of results
            similarity_threshold (float): Threshold
            use_graph (bool): Use graph retrieval
            
        Returns:
            ToolResult with retrieval results
        """
        import time
        start_time = time.time()
        
        try:
            # 1. Validate parameters
            params = RetrievalParameters(**kwargs)
            
            if not self.kms:
                return ToolResult(
                    success=False,
                    output="Knowledge Management System is not available.",
                    execution_time=time.time() - start_time,
                    error="KMS_NOT_FOUND"
                )

            # 2. Call KMS
            # Retrieve slightly more results to allow for reranking
            initial_top_k = params.top_k * 2 
            
            logger.info(f"Retrieving for query: '{params.query}' (initial_top_k={initial_top_k})")
            
            results = self.kms.retrieve_knowledge(
                query=params.query,
                top_k=initial_top_k,
                similarity_threshold=params.similarity_threshold,
                use_graph=params.use_graph
            )
            
            # 3. Neural Reranking
            if results and len(results) > 1:
                logger.info("Applying neural reranking...")
                # Extract content list
                documents = [res.get("content", "") for res in results]
                # Rerank
                reranked_scores = await self.reranker.rerank(params.query, documents)
                # reranked_scores is list of (doc, score) sorted by score
                
                # Re-map scores back to full objects (assuming content is unique enough or map by index)
                # Better approach: map by index if reranker preserves order or returns indices
                # For simplicity here: we rebuild the list based on sorted contents
                
                # Create a map for quick lookup
                res_map = {res.get("content"): res for res in results}
                
                reranked_results = []
                for doc, score in reranked_scores:
                    if doc in res_map:
                        original_res = res_map[doc]
                        # Update score with neural score
                        original_res["score"] = float(score) 
                        reranked_results.append(original_res)
                
                # Slice to requested top_k
                results = reranked_results[:params.top_k]
            
            # 4. Format results
            formatted_results = []
            for res in results:
                formatted_results.append({
                    "id": res.get("id"),
                    "content": res.get("content"),
                    "score": res.get("score"),
                    "metadata": res.get("metadata", {})
                })
            
            execution_time = time.time() - start_time
            
            return ToolResult(
                success=True,
                output=formatted_results,
                execution_time=execution_time,
                metadata={
                    "count": len(formatted_results),
                    "query": params.query
                }
            )
            
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return ToolResult(
                success=False,
                output=str(e),
                execution_time=time.time() - start_time,
                error=str(e)
            )
