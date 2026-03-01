"""
Standard ReAct Workflow Definition
"""
from typing import TypedDict, Annotated, Literal, Union, Dict, Any, List
import operator
from langgraph.graph import StateGraph, END
from src.services.logging_service import get_logger
from src.core.llm_integration import LLMIntegration
from src.interfaces.tool import ITool
from src.prompts.reasoning.react import REACT_SYSTEM_PROMPT, REACT_USER_PROMPT
from src.prompts.reasoning.dialectical import DIALECTICAL_SYSTEM_PROMPT, DIALECTICAL_USER_PROMPT
from src.services.prompt_engineering.orchestrator import PromptOrchestrator

logger = get_logger(__name__)

class ReActState(TypedDict):
    """
    State schema for ReAct (Reasoning + Acting) workflow.
    """
    query: str
    context: Dict[str, Any]
    
    # Trace of the reasoning process
    messages: Annotated[list, operator.add]
    agent_scratchpad: str # Accumulates Thought/Action/Obs
    
    # Current step details
    current_thought: str
    next_action: str
    action_input: Dict[str, Any]
    observation: str
    
    # Control flags
    iteration_count: int
    max_iterations: int
    final_answer: str
    error: str
    
    # DDL / Challenge Mode
    challenge_triggered: bool
    challenge_result: str

def create_react_workflow(llm: LLMIntegration, tools: List[ITool]) -> StateGraph:
    """
    Create a standard ReAct workflow graph with real LLM and Tools.
    
    Args:
        llm: Initialized LLM integration instance
        tools: List of available tools
    """
    workflow = StateGraph(ReActState)
    
    # Prepare tool info for prompt
    tool_descriptions = "\n".join([f"{t.config.name}: {t.config.description}" for t in tools])
    tool_names = ", ".join([t.config.name for t in tools])
    tool_map = {t.config.name: t for t in tools}

    # Prompt Orchestrator
    prompt_orchestrator = PromptOrchestrator()

    # --- Nodes ---
    
    async def think_node(state: ReActState) -> Dict[str, Any]:
        """
        Agent generates a thought and decides next action using LLM.
        """
        query = state["query"]
        scratchpad = state.get("agent_scratchpad", "")
        context = state.get("context", {})
        iteration = state.get("iteration_count", 0) + 1
        
        # Check if we are in a "Challenge Loop" (re-thinking after challenge)
        challenge_result = state.get("challenge_result")
        if challenge_result:
            scratchpad += f"\n\n[DIALECTICAL REVIEW]: {challenge_result}\n\n[Agent]: Considering the critique above, I will now revise my thinking."
        
        # 1. Construct Prompt via Orchestrator
        # Extract complexity from context for dynamic few-shot selection
        task_type = "general"
        if context.get("complexity") == "high":
            # Simple heuristic mapping for now
            # In future, Neural Router should pass specific task type
            task_type = "research" 
            
        # Get Context Summary from session context (if available)
        context_summary = context.get("summary", "")

        base_system_msg = REACT_SYSTEM_PROMPT.format(
            tool_descriptions=tool_descriptions,
            tool_names=tool_names
        )
        
        # Use Orchestrator to assemble the full prompt with examples and summary
        full_system_msg = await prompt_orchestrator.construct_prompt(
            base_template=base_system_msg,
            query=query,
            context_summary=context_summary,
            task_type=task_type
        )
        
        user_msg = REACT_USER_PROMPT.format(
            query=query,
            context=str(context),
            agent_scratchpad=scratchpad
        )
        
        # 2. Call LLM
        # Note: We use _call_llm directly. In future, use generate() if available.
        # Assuming LLM supports system/user messages via simple string concatenation or structured input
        # Here we simplify for text-based models
        full_prompt = f"{full_system_msg}\n\n{user_msg}"
        
        try:
            response = llm._call_llm(full_prompt) # Using internal method for now
            if not response:
                return {"error": "Empty LLM response", "iteration_count": iteration}
                
            # 3. Parse Response
            # Simple parser for Thought/Action/Action Input
            import re
            
            # Check for Final Answer
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[-1].strip()
                
                # IMPORTANT: If this is the FIRST final answer and we haven't challenged yet,
                # AND the context suggests complexity (e.g. via tags or just default for now),
                # we might want to trigger a challenge instead of returning immediately.
                # For now, we rely on the graph edge logic to decide.
                
                return {
                    "final_answer": final_answer,
                    "iteration_count": iteration,
                    "agent_scratchpad": scratchpad + f"\n{response}"
                }
            
            # Parse Action
            action_match = re.search(r"Action: (.*?)\n", response)
            input_match = re.search(r"Action Input: (.*?)(?:\n|$)", response)
            
            if action_match and input_match:
                action = action_match.group(1).strip()
                action_input = input_match.group(1).strip()
                return {
                    "current_thought": response,
                    "next_action": action,
                    "action_input": action_input, # Keep as string for now, tool needs to parse if JSON
                    "iteration_count": iteration,
                    "agent_scratchpad": scratchpad + f"\n{response}"
                }
            
            # Fallback if no action parsed but no final answer (could be just thought)
            return {
                "current_thought": response,
                "next_action": "continue", # Or fail
                "iteration_count": iteration,
                "agent_scratchpad": scratchpad + f"\n{response}"
            }
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return {"error": str(e), "iteration_count": iteration}

    async def challenge_node(state: ReActState) -> Dict[str, Any]:
        """
        [DDL β≈2] Dialectical Challenge Node.
        Acts as a Devil's Advocate to critique the proposed Final Answer.
        """
        query = state["query"]
        trace = state.get("agent_scratchpad", "")
        answer = state.get("final_answer", "")
        
        logger.info("Triggering Dialectical Challenge (β≈2)...")
        
        system_msg = DIALECTICAL_SYSTEM_PROMPT.format(
            query=query,
            reasoning=trace,
            conclusion=answer
        )
        user_msg = DIALECTICAL_USER_PROMPT.format(
            query=query,
            trace=trace,
            answer=answer
        )
        
        full_prompt = f"{system_msg}\n\n{user_msg}"
        
        try:
            critique = llm._call_llm(full_prompt)
            
            # Simple heuristic parsing of the verdict
            # Real impl would use structured output
            verdict = "VALID"
            if "NEEDS_REFINEMENT" in critique:
                verdict = "NEEDS_REFINEMENT"
            elif "INVALID" in critique:
                verdict = "INVALID"
                
            logger.info(f"Challenge Verdict: {verdict}")
            
            if verdict == "VALID":
                # Pass through, clear challenge flag so we exit
                return {"challenge_triggered": True, "challenge_result": "VALID"}
            else:
                # Force re-think
                # We clear final_answer to loop back to 'think'
                # We append critique to scratchpad in 'think' node (via state update here or next)
                return {
                    "challenge_triggered": True, 
                    "challenge_result": critique,
                    "final_answer": None, # Clear answer to force re-generation
                    "next_action": "continue" # Loop back
                }
                
        except Exception as e:
            logger.error(f"Challenge failed: {e}")
            return {"challenge_triggered": True, "challenge_result": "Error in challenge"}

    async def act_node(state: ReActState) -> Dict[str, Any]:
        """
        Execute the decided action (Tool execution).
        """
        action = state.get("next_action")
        action_input_str = state.get("action_input")
        scratchpad = state.get("agent_scratchpad", "")
        
        if action not in tool_map:
            obs = f"Error: Tool '{action}' not found. Available tools: {tool_names}"
        else:
            tool = tool_map[action]
            try:
                # Simple input parsing: assume single string arg for now
                # Real implementation should parse JSON or map args
                # For RetrievalTool, input is 'query'
                if tool.config.name == "knowledge_retrieval":
                     # Handle potential JSON input or raw string
                     # For now assume raw string is the query
                     result = await tool.execute(query=action_input_str)
                else:
                    # Generic fallback
                    result = await tool.execute(input=action_input_str)
                
                obs = str(result.output)
            except Exception as e:
                obs = f"Error executing tool: {e}"
        
        return {
            "observation": obs,
            "agent_scratchpad": scratchpad + f"\nObservation: {obs}\n"
        }

    # --- Graph Construction ---
    
    workflow.add_node("think", think_node)
    workflow.add_node("act", act_node)
    workflow.add_node("challenge", challenge_node)

    # --- Edges ---
    
    def decide_next(state: ReActState) -> Literal["act", "think", "challenge", "end"]:
        # Safety checks
        if state.get("error"):
            return "end"
        if state.get("iteration_count", 0) >= state.get("max_iterations", 5):
            return "end"
            
        # Logic for Challenge Mode
        final_answer = state.get("final_answer")
        challenge_triggered = state.get("challenge_triggered")
        challenge_result = state.get("challenge_result")
        
        if final_answer:
            # Logic for Dynamic Challenge (DDL β≈2)
            # We trigger challenge if:
            # 1. Complexity is HIGH (from Neural Router tags)
            # 2. Or Iteration Count > 1 (implies difficulty)
            # 3. Or Random sample (for exploration, skipped here)
            
            complexity = state.get("context", {}).get("complexity", "medium")
            iteration = state.get("iteration_count", 0)
            
            # Decide if we need dialectical reasoning
            should_challenge = False
            
            if not challenge_triggered:
                if complexity == "high":
                    should_challenge = True
                elif complexity == "medium" and iteration > 1:
                    # If it took multiple steps, it's worth checking
                    should_challenge = True
                # For "simple" queries, we skip challenge to save latency/cost
            
            if should_challenge:
                logger.info(f"Dynamic Challenge Triggered (Complexity: {complexity}, Iteration: {iteration})")
                return "challenge"
            
            # If we challenged and it was VALID (or we gave up), end
            if challenge_result == "VALID":
                return "end"
            
            # If we challenged and failed (invalid/refine), we loop back to 'think'
            # The 'challenge_node' already cleared 'final_answer' in that case
            # so we wouldn't be in this 'if final_answer' block theoretically,
            # but just in case:
            if not final_answer: 
                return "think"
                
            return "end" # Should not reach here if logic holds

        if state.get("next_action") == "continue":
             return "think" 
        if state.get("next_action"):
            return "act"
            
        return "end"

    workflow.set_entry_point("think")
    
    workflow.add_conditional_edges(
        "think",
        decide_next,
        {
            "act": "act",
            "think": "think",
            "challenge": "challenge",
            "end": END
        }
    )
    
    workflow.add_edge("act", "think")
    workflow.add_conditional_edges(
        "challenge",
        decide_next, # Reuse logic: if answer cleared -> think, if valid -> end
        {
            "think": "think",
            "end": END
        }
    )

    return workflow.compile()
