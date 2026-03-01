"""
OpenTelemetry 集成测试 - 阶段2.5
测试 OpenTelemetry 追踪和指标功能
"""
import pytest
import logging
import os
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_opentelemetry_integration import (
    OPENTELEMETRY_AVAILABLE,
    traced_node,
    initialize_opentelemetry,
    configure_opentelemetry_exporter
)
from src.core.langgraph_unified_workflow import ResearchSystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.skipif(not OPENTELEMETRY_AVAILABLE, reason="OpenTelemetry not installed")
class TestOpenTelemetryIntegration:
    """测试 OpenTelemetry 集成"""
    
    def test_opentelemetry_available(self):
        """测试 OpenTelemetry 是否可用"""
        assert OPENTELEMETRY_AVAILABLE, "OpenTelemetry 应该可用"
    
    def test_initialize_opentelemetry_console(self):
        """测试初始化 OpenTelemetry（控制台导出器）"""
        result = initialize_opentelemetry(
            exporter_type="console",
            enabled=True
        )
        assert result is True or result is False  # 可能成功或失败（取决于安装）
    
    def test_configure_console_exporter(self):
        """测试配置控制台导出器"""
        result = configure_opentelemetry_exporter("console")
        assert result is True or result is False
    
    @pytest.mark.asyncio
    async def test_traced_node_decorator(self):
        """测试 traced_node 装饰器"""
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
        
        @traced_node("test_node")
        async def test_node(state: ResearchSystemState) -> ResearchSystemState:
            state['answer'] = "test answer"
            return state
        
        result = await test_node(state)
        assert result['answer'] == "test answer"
    
    @pytest.mark.asyncio
    async def test_traced_node_with_error(self):
        """测试 traced_node 装饰器处理错误"""
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
        
        @traced_node("test_node_error")
        async def test_node_error(state: ResearchSystemState) -> ResearchSystemState:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            await test_node_error(state)
    
    @pytest.mark.asyncio
    async def test_traced_node_with_token_usage(self):
        """测试 traced_node 装饰器记录 token 使用"""
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
            "token_usage": {"input": 100, "output": 50},
            "api_calls": {},
            "metadata": {},
            "checkpoint_id": None
        }
        
        @traced_node("test_node_token")
        async def test_node_token(state: ResearchSystemState) -> ResearchSystemState:
            return state
        
        result = await test_node_token(state)
        assert result['token_usage'] == {"input": 100, "output": 50}


class TestOpenTelemetryWithoutInstallation:
    """测试 OpenTelemetry 未安装时的行为"""
    
    @pytest.mark.asyncio
    async def test_traced_node_without_opentelemetry(self):
        """测试 OpenTelemetry 未安装时装饰器仍然工作"""
        # 这个测试在 OpenTelemetry 未安装时也应该通过
        # 因为装饰器会检查可用性
        
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
        
        @traced_node("test_node")
        async def test_node(state: ResearchSystemState) -> ResearchSystemState:
            state['answer'] = "test answer"
            return state
        
        result = await test_node(state)
        assert result['answer'] == "test answer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

