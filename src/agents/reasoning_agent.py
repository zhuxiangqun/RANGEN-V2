"""
Specialist Reasoning Agent Implementation
"""
from typing import Dict, Any, Optional
import time
import os
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.core.workflows.react_workflow import create_react_workflow
from src.services.logging_service import get_logger
from src.core.llm_integration import LLMIntegration
from src.agents.tools.tool_registry import ToolRegistry

logger = get_logger(__name__)

class ReasoningAgent(IAgent):
    """
    Agent responsible for complex reasoning tasks.
    Uses ReAct or CoT workflows to break down problems and use tools.
    """
    
    def __init__(self, tool_registry: ToolRegistry, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                name="reasoning_agent",
                description="Performs multi-step reasoning and problem solving",
                version="2.0.0"
            )
        super().__init__(config)
        
        self.tool_registry = tool_registry
        
        # Initialize LLM Integration
        # Assuming config.metadata might hold LLM settings, or use env vars
        llm_config = {
            "llm_provider": os.getenv("LLM_PROVIDER", "deepseek"),
            "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
            "model": os.getenv("REASONING_MODEL", "deepseek-reasoner"),
            "base_url": os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        }
        self.llm = LLMIntegration(llm_config)
        
        # Initialize the workflow graph with LLM and Tools
        tools = self.tool_registry.get_all_tools()
        self.workflow = create_react_workflow(self.llm, tools)
        
        logger.info(f"ReasoningAgent initialized: {self.config.name}")

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate that query exists"""
        if "query" not in inputs or not inputs["query"]:
            logger.error("Input validation failed: 'query' is missing")
            return False
        return True

    async def execute(self, inputs: Dict[str, Any], context: Optional[Dict] = None) -> AgentResult:
        """
        Execute the reasoning workflow.
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

            # 2. Prepare State
            initial_state = {
                "query": inputs["query"],
                "context": context or {},
                "messages": [],
                "agent_scratchpad": "",
                "iteration_count": 0,
                "max_iterations": self.config.metadata.get("max_iterations", 5),
                "final_answer": "",
                "error": ""
            }
            
            # 3. Run Workflow
            logger.info(f"Starting reasoning for: {inputs['query']}")
            result_state = await self.workflow.ainvoke(initial_state)
            
            execution_time = time.time() - start_time
            
            # 4. Process Result
            if result_state.get("error"):
                return AgentResult(
                    agent_name=self.config.name,
                    status=ExecutionStatus.FAILED,
                    output=None,
                    execution_time=execution_time,
                    error=result_state["error"]
                )
                
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.COMPLETED,
                output={
                    "answer": result_state.get("final_answer"),
                    "steps": result_state.get("iteration_count"),
                    "trace": result_state.get("agent_scratchpad")
                },
                execution_time=execution_time,
                metadata={"workflow": "react"}
            )
            
        except Exception as e:
            logger.error(f"ReasoningAgent execution failed: {e}")
            return AgentResult(
                agent_name=self.config.name,
                status=ExecutionStatus.FAILED,
                output=None,
                execution_time=time.time() - start_time,
                error=str(e)
            )
