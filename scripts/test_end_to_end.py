"""
End-to-End Test for RANGEN Architecture
"""
import asyncio
import sys
import os
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from src.core.context_manager import ContextManager
from src.core.configurable_router import ConfigurableRouter, RouteTarget
from src.core.execution_coordinator import ExecutionCoordinator
from src.agents.tools.tool_registry import ToolRegistry
from src.agents.tools.retrieval_tool import RetrievalTool
from src.interfaces.agent import IAgent, AgentConfig, AgentResult, ExecutionStatus
from src.services.logging_service import get_logger

logger = get_logger("e2e_test")

# Mock KMS for testing without vector DB dependency
class MockKMS:
    def retrieve_knowledge(self, query, top_k=5, **kwargs):
        logger.info(f"[MockKMS] Retrieving for: {query}")
        return [
            {"id": "1", "content": f"Quantum computers use qubits. Shor's algorithm can factor large integers efficiently, threatening RSA.", "score": 0.95},
            {"id": "2", "content": f"Post-quantum cryptography is being developed to resist quantum attacks.", "score": 0.85}
        ]

# Mock LLM Integration
class MockLLMIntegration:
    def __init__(self, config=None):
        self.call_count = 0
        
    def _call_llm(self, prompt, **kwargs):
        self.call_count += 1
        logger.info(f"[MockLLM] Call #{self.call_count} Prompt length: {len(prompt)}")
        
        # Simple state machine for the test case
        if "knowledge_retrieval" in prompt and self.call_count == 1:
            return "Thought: I need to search for the impact of quantum computing on cryptography.\nAction: knowledge_retrieval\nAction Input: impact of quantum computing on cryptography"
        
        if "Observation:" in prompt:
             return "Thought: The search results mention Shor's algorithm and threats to RSA. I can now answer.\nFinal Answer: Quantum computing threatens current encryption methods like RSA because algorithms like Shor's can factor large numbers efficiently. However, post-quantum cryptography is being developed as a defense."
             
        return "Final Answer: I am not sure."

async def main():
    logger.info("Starting End-to-End Test (Full Coordinator Flow)...")
    
    # 1. Initialize Core Services
    context_manager = ContextManager(session_id="test_session_001")
    router = ConfigurableRouter(default_route=RouteTarget.REACT)
    
    # 2. Setup Tool Registry & Tools
    registry = ToolRegistry()
    
    # Use Mock KMS
    retrieval_tool = RetrievalTool()
    retrieval_tool._kms = MockKMS() # Inject Mock
    registry.register_tool(retrieval_tool)
    
    # 3. Initialize Coordinator
    # Note: We need to patch LLMIntegration inside ReasoningAgent which is created inside ExecutionCoordinator
    
    with patch('src.agents.reasoning_agent.LLMIntegration', side_effect=MockLLMIntegration):
        coordinator = ExecutionCoordinator(router, context_manager, registry)
        
        task = "Explain the impact of quantum computing on cryptography"
        logger.info(f"Task: {task}")
        
        # Execute via Coordinator
        result = await coordinator.run_task(task)
        
        logger.info("-" * 50)
        logger.info("Coordinator Result:")
        logger.info(result)
        logger.info("-" * 50)
        
        # Verification
        final_answer = result.get("final_answer", "")
        if "Quantum computing" in final_answer:
            logger.info("✅ Full System Test Passed!")
        else:
            logger.error("❌ Full System Test Failed")

if __name__ == "__main__":
    asyncio.run(main())
