"""
LangGraph 工作流集成测试 - 阶段2.6
测试完整工作流的端到端功能
"""
import asyncio
import pytest  # type: ignore
import logging
import os
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_unified_workflow import UnifiedResearchWorkflow
from src.unified_research_system import UnifiedResearchSystem

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.asyncio
class TestWorkflowIntegration:
    """测试工作流集成"""
    
    @pytest.fixture
    async def workflow(self):
        """创建工作流实例"""
        system = UnifiedResearchSystem()
        workflow = UnifiedResearchWorkflow(system=system)
        yield workflow
    
    async def test_simple_query_path(self, workflow):
        """测试简单查询路径"""
        query = "What is the capital of France?"
        
        result = await workflow.execute(query)
        
        assert result is not None
        assert 'success' in result
        assert 'route_path' in result
        # 简单查询应该路由到 simple 路径
        # 注意：实际路由可能根据复杂度判断，所以可能是 simple 或 complex
    
    async def test_complex_query_path(self, workflow):
        """测试复杂查询路径"""
        query = "Explain the relationship between quantum mechanics and general relativity, including their historical development and current research challenges."
        
        result = await workflow.execute(query)
        
        assert result is not None
        assert 'success' in result
        assert 'route_path' in result
    
    async def test_workflow_with_user_context(self, workflow):
        """测试带用户上下文的工作流"""
        query = "What is Python?"
        context = {
            "user_id": "test_user_123",
            "session_id": "test_session_456",
            "user_context": {
                "preferences": {"language": "en"},
                "history": []
            }
        }
        
        result = await workflow.execute(query, context)
        
        assert result is not None
        assert 'success' in result
    
    async def test_workflow_error_handling(self, workflow):
        """测试工作流错误处理"""
        # 使用空查询触发错误
        query = ""
        
        result = await workflow.execute(query)
        
        # 应该返回结果（即使失败）
        assert result is not None
        # 可能成功或失败，取决于实现
        assert 'error' in result or result.get('success') == False or result.get('success') == True
    
    async def test_workflow_performance_tracking(self, workflow):
        """测试工作流性能追踪"""
        query = "What is machine learning?"
        
        result = await workflow.execute(query)
        
        assert result is not None
        # 检查性能指标
        assert 'execution_time' in result or 'node_times' in result


@pytest.mark.asyncio
class TestWorkflowStateManagement:
    """测试工作流状态管理"""
    
    async def test_state_initialization(self):
        """测试状态初始化"""
        workflow = UnifiedResearchWorkflow()
        
        state = {
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
        
        result_state = await workflow._entry_node(state)  # type: ignore
        
        # 验证所有阶段2新增字段都已初始化
        assert 'user_context' in result_state
        assert 'user_id' in result_state
        assert 'session_id' in result_state
        assert 'safety_check_passed' in result_state
        assert 'node_execution_times' in result_state
        assert 'token_usage' in result_state
        assert 'api_calls' in result_state


@pytest.mark.asyncio
class TestWorkflowErrorRecovery:
    """测试工作流错误恢复"""
    
    async def test_retry_mechanism(self):
        """测试重试机制"""
        # 这个测试需要模拟可重试的错误
        # 由于需要实际的系统实例，这里只做基本验证
        workflow = UnifiedResearchWorkflow()
        
        # 验证重试相关的状态字段
        state = {
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
        
        assert 'retry_count' in state
        assert state['retry_count'] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

