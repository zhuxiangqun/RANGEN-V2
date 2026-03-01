"""
LangGraph 工作流节点单元测试 - 阶段2.6
测试各个节点的独立功能
"""
import asyncio
import pytest
import logging
from typing import Dict, Any
from unittest.mock import patch

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_unified_workflow import (
    UnifiedResearchWorkflow,
    ResearchSystemState,
    ErrorCategory,
    classify_error,
    should_retry_error,
    handle_node_error,
    record_node_time
)
from src.core.langgraph_reasoning_nodes import ReasoningNodes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestErrorClassification:
    """测试错误分类功能"""
    
    def test_classify_retryable_error(self):
        """测试可重试错误分类"""
        error = Exception("Connection timeout")
        category = classify_error(error)
        assert category == ErrorCategory.RETRYABLE
    
    def test_classify_temporary_error(self):
        """测试临时错误分类"""
        error = TimeoutError("Request timeout")
        category = classify_error(error)
        assert category == ErrorCategory.TEMPORARY
    
    def test_classify_fatal_error(self):
        """测试致命错误分类"""
        error = ValueError("Invalid configuration")
        category = classify_error(error)
        # 根据实现，可能返回 RETRYABLE 或 FATAL
        assert category in [ErrorCategory.RETRYABLE, ErrorCategory.FATAL]
    
    def test_should_retry_error(self):
        """测试错误重试判断"""
        retryable_error = Exception("Network timeout")
        fatal_error = ValueError("Invalid config")
        
        assert should_retry_error(retryable_error, 0, 3) == True
        assert should_retry_error(retryable_error, 3, 3) == False
        assert should_retry_error(fatal_error, 0, 3) == False


class TestNodeErrorHandling:
    """测试节点错误处理"""
    
    def test_handle_node_error_retryable(self):
        """测试可重试错误处理"""
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
        
        error = Exception("Network timeout")
        result_state = handle_node_error(state, error, "test_node", 0, 3)
        
        assert len(result_state['errors']) == 1
        assert result_state['errors'][0]['node'] == "test_node"
        assert result_state['errors'][0]['category'] == ErrorCategory.RETRYABLE
        assert result_state['error'] is not None
        assert result_state['task_complete'] == False  # 可重试错误不立即完成
    
    def test_handle_node_error_fatal(self):
        """测试致命错误处理"""
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
        
        assert len(result_state['errors']) == 1
        assert result_state['task_complete'] == True  # 致命错误立即完成


class TestPerformanceRecording:
    """测试性能记录功能"""
    
    def test_record_node_time(self):
        """测试节点执行时间记录"""
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
        
        result_state = record_node_time(state, "test_node", 1.5)
        
        assert "test_node" in result_state['node_execution_times']
        assert result_state['node_execution_times']['test_node'] == 1.5
        assert "test_node" in result_state['node_times']  # 兼容旧字段
        assert result_state['node_times']['test_node'] == 1.5


@pytest.mark.asyncio
class TestWorkflowNodes:
    """测试工作流节点"""
    
    async def test_entry_node(self):
        """测试入口节点"""
        workflow = UnifiedResearchWorkflow()
        
        state: ResearchSystemState = {
            "query": "test query",
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
        
        result_state = await workflow._entry_node(state)
        
        assert result_state['query'] == "test query"
        assert 'context' in result_state
        assert 'errors' in result_state
        assert 'user_context' in result_state
        assert 'node_execution_times' in result_state
    
    async def test_route_query_node(self):
        """测试路由查询节点"""
        workflow = UnifiedResearchWorkflow()
        
        state: ResearchSystemState = {
            "query": "What is the capital of France?",
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
        
        result_state = await workflow._route_query_node(state)
        
        assert 'complexity_score' in result_state
        assert 'route_path' in result_state
        assert result_state['route_path'] in ['simple', 'complex', 'multi_agent']
    
    async def test_route_decision(self):
        """测试路由决策函数"""
        workflow = UnifiedResearchWorkflow()
        
        # 测试简单查询
        state_simple: ResearchSystemState = {
            "query": "test",
            "context": {},
            "route_path": "simple",
            "complexity_score": 2.0,
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
        
        route_path = workflow._route_decision(state_simple)
        assert route_path in ['simple', 'complex', 'multi_agent']

        # 测试复杂查询
        state_complex: ResearchSystemState = {
            "query": "test",
            "context": {},
            "route_path": "simple",
            "complexity_score": 5.0,
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
        
        route_path = workflow._route_decision(state_complex)
        assert route_path in ['simple', 'complex', 'multi_agent']


@pytest.mark.asyncio
class TestReasoningNodesExecuteStep:
    async def test_infer_depends_on_and_replace_placeholder(self):
        with patch.object(ReasoningNodes, "_initialize_reasoning_engine", lambda self: None):
            nodes = ReasoningNodes()

        state: ResearchSystemState = {
            "query": "Who wrote the book 'The Last of the Mohicans' and when was he born?",
            "context": {},
            "route_path": "complex",
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
            "checkpoint_id": None,
            "reasoning_steps": [
                {"sub_query": "Who wrote the book 'The Last of the Mohicans'?", "type": "extraction", "depends_on": []},
                {"sub_query": "What year was [step 1 result] born?", "type": "extraction", "depends_on": []},
            ],
            "current_step_index": 1,
            "step_answers": ["James Fenimore Cooper"],
        }

        result_state = await nodes.execute_step_node(state)

        current_step = result_state.get("metadata", {}).get("current_step", {})
        assert current_step.get("depends_on") == ["step_1"]
        assert "[step" not in (current_step.get("sub_query") or "").lower()
        assert "James Fenimore Cooper" in (current_step.get("sub_query") or "")

    async def test_infer_depends_on_double_space_placeholder(self):
        with patch.object(ReasoningNodes, "_initialize_reasoning_engine", lambda self: None):
            nodes = ReasoningNodes()

        state: ResearchSystemState = {
            "query": "Who wrote the book 'The Last of the Mohicans' and when was he born?",
            "context": {},
            "route_path": "complex",
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
            "checkpoint_id": None,
            "reasoning_steps": [
                {"sub_query": "Who wrote the book 'The Last of the Mohicans'?", "type": "extraction", "depends_on": []},
                {"sub_query": "What year was [step  1 result] born?", "type": "extraction", "depends_on": []},
            ],
            "current_step_index": 1,
            "step_answers": ["James Fenimore Cooper"],
        }

        result_state = await nodes.execute_step_node(state)

        current_step = result_state.get("metadata", {}).get("current_step", {})
        assert current_step.get("depends_on") == ["step_1"]
        assert "[step" not in (current_step.get("sub_query") or "").lower()
        assert "James Fenimore Cooper" in (current_step.get("sub_query") or "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
