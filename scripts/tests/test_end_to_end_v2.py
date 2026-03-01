"""
End-to-End Test Script for RANGEN V2
Verifies the integration of Coordinator, Agents, Tools, Monitoring, and Prompting.
"""
import asyncio
import os
import sys
from typing import Dict, Any

# Add project root to path
sys.path.append(os.getcwd())

from src.core.execution_coordinator import ExecutionCoordinator
from src.core.context_manager import ContextManager
from src.core.configurable_router import ConfigurableRouter
from src.agents.tools.tool_registry import ToolRegistry
from src.services.logging_service import get_logger
from src.services.performance_monitor import get_performance_monitor
from src.prompts.prompt_manager import get_prompt_manager

logger = get_logger("e2e_test")

async def run_e2e_test():
    print("="*50)
    print("🚀 Starting RANGEN V2 End-to-End Test")
    print("="*50)

    # 1. Initialize Components
    print("\n[1] Initializing Core Components...")
    try:
        # NOTE: ExecutionCoordinator now initializes its own components
        coordinator = ExecutionCoordinator()
        context_manager = coordinator.context_manager
        print("    - ExecutionCoordinator initialized")
        
        # Monitor
        monitor = get_performance_monitor()
        await monitor.start()
        print("    - PerformanceMonitor started")
        
    except Exception as e:
        print(f"❌ Initialization Failed: {e}")
        return

    # 2. Test Case: Simple Reasoning Task
    # We use a query that might trigger the tool (if configured) or just pure reasoning
    query = "What is the capital of France?" 
    session_id = "test_session_001"
    
    print(f"\n[2] Running Task: '{query}' (Session: {session_id})")
    
    try:
        result = await coordinator.run_task(
            task=query,
            session_id=session_id,
            context={"source": "e2e_test"}
        )
        
        print("\n[3] Execution Result:")
        print(f"    - Final Answer: {result.get('final_answer')}")
        print(f"    - Route: {result.get('route')}")
        print(f"    - Steps: {result.get('steps')}")
        
        if result.get("error"):
            print(f"    ❌ Error: {result.get('error')}")
        else:
            print("    ✅ Task Completed Successfully")
            
    except Exception as e:
        print(f"❌ Task Execution Failed: {e}")

    # 3. Verify Context Persistence
    print("\n[4] Verifying Context Persistence...")
    session = await context_manager.get_session(session_id)
    history = session.get("history", [])
    print(f"    - Session History Length: {len(history)}")
    if len(history) > 0:
        print("    ✅ Context Saved Successfully")
    else:
        print("    ⚠️ Context might not be saved (check Coordinator logic)")

    # 4. Verify Monitoring
    print("\n[5] Verifying Monitoring Metrics...")
    stats = monitor.get_stats()
    print(f"    - Metrics Count: {stats['metrics_count']}")
    print(f"    - Active Alerts: {stats['active_alerts']}")
    
    if stats['metrics_count'] > 0:
        print("    ✅ Metrics Recorded")
    else:
        print("    ⚠️ No Metrics Recorded (check decorators)")

    # Cleanup
    await monitor.stop()
    print("\n" + "="*50)
    print("🏁 Test Finished")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
