"""
Execution Coordinator Implementation using LangGraph
"""
from typing import Dict, Any, TypedDict, Annotated, Literal, Optional
import operator
from langgraph.graph import StateGraph, END
from src.interfaces.coordinator import ICoordinator
from src.interfaces.agent import ExecutionStatus
from src.core.configurable_router import ConfigurableRouter, RouteTarget
from src.core.context_manager import ContextManager
from src.core.neural.factory import NeuralServiceFactory
from src.core.llm_integration import LLMIntegration

from src.services.logging_service import get_logger
from src.agents.reasoning_agent import ReasoningAgent
from src.agents.tools.tool_registry import ToolRegistry
from src.core.monitoring.monitor_decorator import monitor
from src.core.nodes.quality_evaluator import QualityEvaluatorNode

logger = get_logger(__name__)

# Define the state schema for the graph
class AgentState(TypedDict):
    query: str
    context: Dict[str, Any]
    route: str
    steps: Annotated[list, operator.add]
    final_answer: str
    error: str
    quality_score: float
    quality_passed: bool
    quality_feedback: str
    retry_count: int

class ExecutionCoordinator(ICoordinator):
    """
    Orchestrates the execution flow using LangGraph.
    Connects Router -> Agents -> Tools based on the defined workflow.
    """
    
    def __init__(self):
        # Components are initialized internally for simplicity in this MVP
        # In a larger system, use dependency injection container
        self.router = ConfigurableRouter()
        self.llm_service = LLMIntegration(config={}) # Initialize LLM once with empty config (uses env vars)
        
        # Initialize Context Manager with LLM for Summarization
        self.context_manager = ContextManager(llm_service=self.llm_service)
        
        self.tool_registry = ToolRegistry()
        
        # Initialize Agents
        self.reasoning_agent = ReasoningAgent(tool_registry=self.tool_registry)
        self.quality_evaluator = QualityEvaluatorNode()
        
        self.graph = self._build_graph()
        logger.info("ExecutionCoordinator initialized with LangGraph and Agents")

    def _build_graph(self) -> StateGraph:
        """Construct the execution graph"""
        workflow = StateGraph(AgentState)

        # Define Nodes
        workflow.add_node("router", self._route_step)
        workflow.add_node("direct_executor", self._direct_execution_step)
        workflow.add_node("reasoning_engine", self._reasoning_step)
        workflow.add_node("quality_evaluator", self.quality_evaluator.evaluate)
        workflow.add_node("error_handler", self._error_handling_step)

        # Define Edges
        workflow.set_entry_point("router")
        
        workflow.add_conditional_edges(
            "router",
            self._decide_next_node,
            {
                RouteTarget.DIRECT.value: "direct_executor",
                RouteTarget.COT.value: "reasoning_engine",
                RouteTarget.REACT.value: "reasoning_engine",
                "error": "error_handler"
            }
        )

        workflow.add_edge("direct_executor", "quality_evaluator")
        workflow.add_edge("reasoning_engine", "quality_evaluator")
        
        workflow.add_conditional_edges(
            "quality_evaluator",
            self._decide_after_eval,
            {
                "pass": END,
                "retry": "reasoning_engine" # Simple retry logic: back to reasoning
            }
        )
        
        workflow.add_edge("error_handler", END)

        return workflow.compile()

    # --- Node Implementations ---

    @monitor.trace_node("router")
    async def _route_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Determine the route"""
        try:
            route = await self.router.route(state["query"], state.get("context"))
            return {"route": route.value}
        except Exception as e:
            logger.error(f"Routing failed: {e}")
            return {"route": "error", "error": str(e)}

    def _decide_next_node(self, state: AgentState) -> str:
        """Edge: Conditional logic based on route"""
        return state.get("route", "error")

    def _decide_after_eval(self, state: AgentState) -> str:
        """Edge: Decide whether to retry based on quality"""
        # Avoid infinite loops
        retry_count = state.get("retry_count", 0)
        if retry_count >= 1:
            return "pass"
            
        passed = state.get("quality_passed", True)
        if passed:
            return "pass"
        
        # If failed, increment retry count and retry
        state["retry_count"] = retry_count + 1
        return "retry"

    @monitor.trace_node("direct_executor")
    async def _direct_execution_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Direct execution"""
        # For now, we can reuse reasoning agent but maybe with a 'direct' prompt
        # Or just call LLM directly. 
        # To keep it consistent, let's use ReasoningAgent but imply a simpler query
        logger.info("Executing Direct Workflow")
        try:
            result = await self.reasoning_agent.execute({
                "query": state["query"],
                # We could hint to not use tools via context if we wanted
            }, context=state.get("context"))
            
            if result.status == ExecutionStatus.COMPLETED:
                 return {
                    "final_answer": result.output.get("answer", str(result.output)), 
                    "steps": ["direct_execution"]
                }
            else:
                 return {"error": result.error or "Direct execution failed"}
        except Exception as e:
            return {"error": str(e)}

    @monitor.trace_node("reasoning_engine")
    async def _reasoning_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Complex reasoning via ReasoningAgent"""
        logger.info(f"Executing Reasoning Workflow ({state['route']})")
        
        try:
            # Execute Reasoning Agent
            result = await self.reasoning_agent.execute(
                inputs={"query": state["query"]},
                context=state.get("context")
            )
            
            if result.status == ExecutionStatus.COMPLETED:
                output = result.output
                return {
                    "final_answer": output.get("answer", ""),
                    "steps": [f"steps: {output.get('steps', 0)}", output.get("trace", "")]
                }
            else:
                return {
                    "error": result.error or "Reasoning execution failed",
                    "final_answer": "Failed to generate answer."
                }
                
        except Exception as e:
            logger.error(f"Reasoning step failed: {e}")
            return {"error": str(e)}

    @monitor.trace_node("error_handler")
    async def _error_handling_step(self, state: AgentState) -> Dict[str, Any]:
        """Node: Global error handler"""
        return {"final_answer": "I encountered an error while processing your request.", "error": state.get("error", "Unknown error")}

    # --- Public Interface ---

    async def run_task(self, task: str, context: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Entry point for running a task"""
        
        # Resolve Session Context
        session_ctx = {}
        session = None
        if session_id:
            try:
                # IMPORTANT: await the async get_session
                session = await self.context_manager.get_session(session_id)
                
                # Record User Query (with Smart Forgetting)
                await session.add_message("user", task)
                
                session_ctx = session.to_dict()
                # Merge explicit context with session context if needed
                if context:
                    session_ctx.update(context)
            except Exception as e:
                logger.warning(f"Failed to retrieve/update session {session_id}: {e}")
                session_ctx = context or {}
        else:
            session_ctx = context or {}

        initial_state = {
            "query": task,
            "context": session_ctx,
            "steps": [],
            "route": "",
            "final_answer": "",
            "error": ""
        }
        
        try:
            # Execute the graph
            result = await self.graph.ainvoke(initial_state)
            
            # Save context after execution
            if session:
                if result.get("final_answer"):
                     # IMPORTANT: await because add_message is now async (neural check)
                     await session.add_message("assistant", result["final_answer"])
                await session.save()
                
            return result
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            return {"error": str(e), "final_answer": "System Error"}

    async def run_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run a specific workflow (bypass router)"""
        # To be implemented for specialized sub-graphs
        pass
