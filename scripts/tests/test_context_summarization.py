"""
Test script for Context Summarization logic.
Mocks Neural Reranker and LLM to verify the flow.
"""
import sys
import os
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.core.context_manager import ContextManager, SessionContext
from src.core.neural.factory import NeuralServiceFactory
from src.core.llm_integration import LLMIntegration

async def test_smart_forgetting_with_summary():
    print("🚀 Starting Context Summarization Test")
    
    # 1. Mock Components
    print("[1] Mocking Neural Components...")
    
    # Mock Reranker to force low score (simulate topic switch)
    mock_reranker = AsyncMock()
    # return [(doc, score)]
    mock_reranker.rerank.return_value = [("doc", 0.1)] 
    
    # Mock LLM for Summarizer
    mock_llm = MagicMock(spec=LLMIntegration)
    mock_llm._call_llm.return_value = "Summary: User previously asked about Python, and Agent provided code."
    
    # Inject Mocks
    NeuralServiceFactory._reranker_instance = mock_reranker
    
    # 2. Initialize Context Manager
    print("[2] Initializing Context Manager...")
    cm = ContextManager()
    
    # We need to manually inject the mock summarizer into the session
    # because ContextManager creates SessionContext internally
    session = await cm.get_session("test_session_summary")
    
    # Patch the session's summarizer
    from src.services.context_engineering.summarizer import ContextSummarizer
    session.summarizer = ContextSummarizer(mock_llm)
    
    # 3. Simulate Conversation History (Topic A)
    print("[3] Simulating History (Topic A: Python Coding)...")
    await session.add_message("user", "How do I write a loop in Python?")
    await session.add_message("assistant", "You can use a for loop: for i in range(10): print(i)")
    await session.add_message("user", "What about while loops?")
    await session.add_message("assistant", "While loops run as long as a condition is true.")
    
    print(f"    - Current History Length: {len(session.get('history'))}")
    
    # 4. Trigger Topic Switch (Topic B)
    print("[4] Triggering Topic Switch (Topic B: Cooking)...")
    # This should trigger Smart Forgetting because we mocked reranker to return 0.1 < 0.2
    await session.add_message("user", "How do I bake a cake?", smart_forget=True)
    
    # 5. Verify Results
    print("[5] Verifying Results...")
    
    history = session.get("history")
    summary = session.get("summary")
    
    print(f"    - New History Length: {len(history)}")
    print(f"    - Summary in Context: {summary}")
    
    if len(history) == 2 and history[1]["content"] == "How do I bake a cake?":
        print("    ✅ History Truncated Successfully")
    else:
        print(f"    ❌ History Truncation Failed (Len: {len(history)})")
        
    if summary == "Summary: User previously asked about Python, and Agent provided code.":
        print("    ✅ Summary Generated Successfully")
    else:
        print(f"    ❌ Summary Generation Failed: {summary}")

if __name__ == "__main__":
    asyncio.run(test_smart_forgetting_with_summary())
