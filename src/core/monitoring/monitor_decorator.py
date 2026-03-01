"""
Graph Monitor Decorator
Provides transparent monitoring for LangGraph nodes.
"""
import time
import functools
import asyncio
from typing import Callable, Any, Dict, Optional
from dataclasses import dataclass
from src.services.performance_monitor import get_performance_monitor
from src.services.logging_service import get_logger

logger = get_logger("graph_monitor")

class GraphMonitor:
    """
    Monitor for LangGraph nodes.
    Integrates with the global PerformanceMonitor service.
    """
    
    def __init__(self):
        self.perf_monitor = get_performance_monitor()
        # Ensure monitor is started
        if not self.perf_monitor._running:
             # In a real app, this might be managed by the app lifecycle
             pass 

    def trace_node(self, node_name: str):
        """Decorator to trace node execution time and success/failure"""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                # Extract state if possible (usually the first arg is 'self', second is 'state')
                # But in LangGraph node methods: method(self, state)
                state = None
                if len(args) > 1 and isinstance(args[1], dict):
                    state = args[1]
                elif len(args) > 0 and isinstance(args[0], dict):
                    state = args[0]
                
                # Try to get session_id or query from state for tagging
                tags = {"node": node_name}
                if state:
                    if "route" in state:
                        tags["route"] = state["route"]
                
                try:
                    logger.debug(f"[{node_name}] Started")
                    result = await func(*args, **kwargs)
                    
                    execution_time = time.time() - start_time
                    
                    # Record metrics
                    self.perf_monitor.record_metric(
                        name=f"node.execution_time",
                        value=execution_time,
                        tags=tags,
                        metadata={"success": True}
                    )
                    
                    logger.debug(f"[{node_name}] Completed in {execution_time:.3f}s")
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # Record error metrics
                    self.perf_monitor.record_metric(
                        name=f"node.execution_time",
                        value=execution_time,
                        tags=tags,
                        metadata={"success": False, "error": str(e)}
                    )
                    
                    self.perf_monitor.record_metric(
                        name=f"node.error",
                        value=1.0,
                        tags=tags,
                        metadata={"error": str(e)}
                    )
                    
                    logger.error(f"[{node_name}] Failed: {e}")
                    raise
                    
            return wrapper
        return decorator

# Global instance
monitor = GraphMonitor()
