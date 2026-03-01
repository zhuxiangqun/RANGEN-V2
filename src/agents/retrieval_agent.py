"""
Specialist Retrieval Agent Implementation
"""
from typing import Dict, Any, Optional
import time
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.agents.tools.tool_registry import ToolRegistry
from src.services.logging_service import get_logger

logger = get_logger(__name__)

class RetrievalAgent(IAgent):
    """
    Agent responsible for information retrieval tasks.
    Focuses on finding relevant documents without complex reasoning loops.
    """
    
    def __init__(self, tool_registry: ToolRegistry, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="retrieval_agent",
                description="Retrieves information from knowledge base",
                version="2.0.0"
            )
        super().__init__(config)
        self.tool_registry = tool_registry
        logger.info(f"RetrievalAgent initialized: {self.config.name}")

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate query and parameters"""
        if "query" not in inputs or not inputs["query"]:
            logger.error("Input validation failed: 'query' is missing")
            return False
        return True

    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """
        Execute the retrieval task.
        """
        start_time = time.time()
        
        try:
            # 1. Validation
            if not self.validate_inputs(inputs):
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.FAILED,
                    output=None,
                    execution_time=0.0,
                    error="Invalid input: 'query' is required"
                )

            query = inputs["query"]
            top_k = inputs.get("top_k", 5)
            
            # 2. Get Retrieval Tool
            retrieval_tool = self.tool_registry.get_tool("knowledge_retrieval")
            if not retrieval_tool:
                raise RuntimeError("Retrieval tool 'knowledge_retrieval' not found in registry")

            # 3. Execute Tool
            logger.info(f"Retrieving knowledge for: {query} (top_k={top_k})")
            tool_result = await retrieval_tool.execute(query=query, top_k=top_k)
            
            execution_time = time.time() - start_time
            
            if not tool_result.success:
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.FAILED,
                    output=None,
                    execution_time=execution_time,
                    error=tool_result.error
                )

            # 4. Format Output
            # For RetrievalAgent, the output is typically the list of documents
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.COMPLETED,
                output={
                    "documents": tool_result.output,
                    "count": len(tool_result.output),
                    "query": query
                },
                execution_time=execution_time,
                metadata={"tool_used": "knowledge_retrieval"}
            )
            
        except Exception as e:
            logger.error(f"RetrievalAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
