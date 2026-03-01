"""
性能监控节点测试 - 阶段2.6
测试性能监控功能
"""
import pytest
import logging
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_performance_monitor import (
    PerformanceMonitor,
    monitor_performance,
    performance_monitor_node
)
from src.core.langgraph_unified_workflow import ResearchSystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPerformanceMonitor:
    """测试性能监控器"""
    
    def test_record_node_execution_time(self):
        """测试记录节点执行时间"""
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
        
        result_state = PerformanceMonitor.record_node_execution(state, "test_node", 1.5)
        
        assert "test_node" in result_state['node_execution_times']
        assert result_state['node_execution_times']['test_node'] == 1.5
    
    def test_record_token_usage(self):
        """测试记录 token 使用情况"""
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
        
        result_state = PerformanceMonitor.record_token_usage(state, "llm_call", 100, "input")
        
        assert "llm_call_input" in result_state['token_usage']
        assert result_state['token_usage']['llm_call_input'] == 100
    
    def test_record_api_call(self):
        """测试记录 API 调用次数"""
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
        
        result_state = PerformanceMonitor.record_api_call(state, "llm_api", 3)
        
        assert "llm_api" in result_state['api_calls']
        assert result_state['api_calls']['llm_api'] == 3
    
    def test_get_performance_summary(self):
        """测试获取性能摘要"""
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
            "execution_time": 10.5,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {
                "node1": 2.0,
                "node2": 3.0,
                "node3": 1.5
            },
            "token_usage": {
                "llm_input": 100,
                "llm_output": 50
            },
            "api_calls": {
                "llm_api": 5
            },
            "metadata": {},
            "checkpoint_id": None
        }
        
        summary = PerformanceMonitor.get_performance_summary(state)
        
        assert summary['total_execution_time'] == 10.5
        assert len(summary['node_execution_times']) == 3
        assert summary['total_token_usage'] == 150
        assert summary['total_api_calls'] == 5
        assert 'slowest_node' in summary
        assert 'fastest_node' in summary


@pytest.mark.asyncio
class TestPerformanceMonitorNode:
    """测试性能监控节点"""
    
    async def test_performance_monitor_node(self):
        """测试性能监控节点"""
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
            "execution_time": 10.0,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {
                "node1": 2.0,
                "node2": 3.0
            },
            "token_usage": {
                "llm_input": 100
            },
            "api_calls": {
                "llm_api": 2
            },
            "metadata": {},
            "checkpoint_id": None
        }
        
        result_state = await performance_monitor_node(state)
        
        assert 'metadata' in result_state
        assert 'performance_summary' in result_state['metadata']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

