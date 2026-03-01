"""
错误处理模块测试 - 阶段5.4
测试错误分类、处理、恢复策略等功能
"""
import pytest  # type: ignore
import time
import logging
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_error_handler import (
    ErrorHandler,
    ErrorType,
    ErrorInfo,
    get_error_handler,
    handle_node_error
)
from src.core.langgraph_unified_workflow import ResearchSystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestErrorHandler:
    """测试错误处理器"""
    
    def test_classify_timeout_error(self):
        """测试超时错误分类"""
        handler = ErrorHandler()
        
        error = TimeoutError("Request timed out")
        error_info = handler.classify_error(error, "test_node")
        
        assert error_info.error_type == ErrorType.TIMEOUT_ERROR
        assert error_info.retryable is True
        assert error_info.recoverable is True
    
    def test_classify_rate_limit_error(self):
        """测试速率限制错误分类"""
        handler = ErrorHandler()
        
        error = Exception("Rate limit exceeded")
        error_info = handler.classify_error(error, "test_node")
        
        assert error_info.error_type == ErrorType.RATE_LIMIT_ERROR
        assert error_info.retryable is True
    
    def test_classify_data_validation_error(self):
        """测试数据验证错误分类"""
        handler = ErrorHandler()
        
        error = ValueError("Invalid data format")
        error_info = handler.classify_error(error, "test_node")
        
        assert error_info.error_type == ErrorType.DATA_VALIDATION_ERROR
        assert error_info.retryable is False
        assert error_info.recoverable is True
    
    def test_get_recovery_strategy(self):
        """测试获取恢复策略"""
        handler = ErrorHandler()
        
        error = TimeoutError("Request timed out")
        error_info = handler.classify_error(error, "test_node")
        strategy = handler.get_recovery_strategy(error_info)
        
        assert strategy['should_retry'] is True
        assert strategy['max_retries'] == 5
        assert strategy['retry_delay'] == 2.0
    
    def test_should_retry(self):
        """测试是否应该重试"""
        handler = ErrorHandler()
        
        error = TimeoutError("Request timed out")
        error_info = handler.classify_error(error, "test_node")
        
        # 应该重试（未达到最大重试次数）
        assert handler.should_retry(error_info, 0) is True
        assert handler.should_retry(error_info, 2) is True
        
        # 不应该重试（达到最大重试次数）
        assert handler.should_retry(error_info, 5) is False
    
    def test_error_statistics(self):
        """测试错误统计"""
        handler = ErrorHandler()
        
        # 记录一些错误
        handler.classify_error(TimeoutError("Timeout 1"), "node1")
        handler.classify_error(TimeoutError("Timeout 2"), "node2")
        handler.classify_error(ValueError("Validation error"), "node3")
        
        stats = handler.get_error_statistics()
        
        assert stats['total_errors'] == 3
        assert stats['retryable_errors'] == 2
        assert ErrorType.TIMEOUT_ERROR.value in stats['error_types']


class TestHandleNodeError:
    """测试节点错误处理"""
    
    def test_handle_node_error(self):
        """测试处理节点错误"""
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
        
        error = TimeoutError("Request timed out")
        result_state = handle_node_error(error, "test_node", state)
        
        assert result_state['error'] is not None
        assert len(result_state['errors']) == 1
        assert result_state['errors'][0]['node'] == "test_node"
        assert result_state['errors'][0]['error_type'] == ErrorType.TIMEOUT_ERROR.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

