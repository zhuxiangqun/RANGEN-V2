"""
LangGraph 工作流错误恢复测试 - 阶段2.6
测试错误恢复和重试机制
"""
import asyncio
import pytest
import logging
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_resilient_node import ResilientNode
from src.core.langgraph_unified_workflow import (
    ResearchSystemState,
    ErrorCategory,
    classify_error,
    should_retry_error
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestResilientNode:
    """测试 ResilientNode 包装器"""
    
    async def test_resilient_node_success(self):
        """测试 ResilientNode 成功执行"""
        async def test_node(state: ResearchSystemState) -> ResearchSystemState:
            state['test_result'] = 'success'
            return state
        
        resilient = ResilientNode(test_node, "test_node", max_retries=3)
        
        state: ResearchSystemState = {
            "query": "test",
            "context": {},
            "route_path": "simple",
            "complexity_score": 0.0,
            "evidence": [],
            "answer": None,
            "confidence": 0.0,
            "final_answer": None,
            "knowledge": [],
            "citations": [],
            "task_complete": False,
            "error": None,
            "errors": [],
            "execution_time": 0.0,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {},
            "token_usage": {},
            "api_calls": {},
            "metadata": {},
            "checkpoint_id": None
        }
        
        result = await resilient(state)
        
        assert result['test_result'] == 'success'
        assert result['retry_count'] == 0
    
    async def test_resilient_node_retry(self):
        """测试 ResilientNode 重试机制"""
        attempt_count = 0
        
        async def failing_node(state: ResearchSystemState) -> ResearchSystemState:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Network timeout")
            state['test_result'] = 'success_after_retry'
            return state
        
        resilient = ResilientNode(failing_node, "test_node", max_retries=3, initial_delay=0.1)
        
        state: ResearchSystemState = {
            "query": "test",
            "context": {},
            "route_path": "simple",
            "complexity_score": 0.0,
            "evidence": [],
            "answer": None,
            "confidence": 0.0,
            "final_answer": None,
            "knowledge": [],
            "citations": [],
            "task_complete": False,
            "error": None,
            "errors": [],
            "execution_time": 0.0,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {},
            "token_usage": {},
            "api_calls": {},
            "metadata": {},
            "checkpoint_id": None
        }
        
        result = await resilient(state)
        
        assert result['test_result'] == 'success_after_retry'
        assert attempt_count == 2
    
    async def test_resilient_node_fallback(self):
        """测试 ResilientNode 降级策略"""
        async def failing_node(state: ResearchSystemState) -> ResearchSystemState:
            raise Exception("Permanent error")
        
        async def fallback_node(state: ResearchSystemState) -> ResearchSystemState:
            state['test_result'] = 'fallback_success'
            return state
        
        resilient = ResilientNode(
            failing_node,
            "test_node",
            max_retries=1,
            fallback_node=fallback_node
        )
        
        state: ResearchSystemState = {
            "query": "test",
            "context": {},
            "route_path": "simple",
            "complexity_score": 0.0,
            "evidence": [],
            "answer": None,
            "confidence": 0.0,
            "final_answer": None,
            "knowledge": [],
            "citations": [],
            "task_complete": False,
            "error": None,
            "errors": [],
            "execution_time": 0.0,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {},
            "token_usage": {},
            "api_calls": {},
            "metadata": {},
            "checkpoint_id": None
        }
        
        result = await resilient(state)
        
        assert result['test_result'] == 'fallback_success'


@pytest.mark.asyncio
class TestErrorRecoveryStrategies:
    """测试错误恢复策略"""
    
    async def test_fatal_error_stops_execution(self):
        """测试致命错误停止执行"""
        from src.core.langgraph_unified_workflow import handle_node_error
        
        state: ResearchSystemState = {
            "query": "test",
            "context": {},
            "route_path": "simple",
            "complexity_score": 0.0,
            "evidence": [],
            "answer": None,
            "confidence": 0.0,
            "final_answer": None,
            "knowledge": [],
            "citations": [],
            "task_complete": False,
            "error": None,
            "errors": [],
            "execution_time": 0.0,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {},
            "token_usage": {},
            "api_calls": {},
            "metadata": {},
            "checkpoint_id": None
        }
        
        error = ValueError("Invalid configuration")
        result_state = handle_node_error(state, error, "test_node", 0, 0)
        
        # 致命错误应该标记任务完成
        assert result_state['task_complete'] == True
        assert len(result_state['errors']) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

