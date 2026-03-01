"""
状态管理优化模块测试 - 阶段5.4
测试状态更新优化功能
"""
import pytest  # type: ignore
import logging
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_state_optimizer import (
    StateOptimizer,
    get_state_optimizer,
    optimize_node_state_update
)
from src.core.langgraph_unified_workflow import ResearchSystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStateOptimizer:
    """测试状态优化器"""
    
    def test_should_update_field(self):
        """测试是否应该更新字段"""
        optimizer = StateOptimizer()
        
        # 相同值不应该更新
        assert optimizer.should_update_field('answer', 'test', 'test') is False
        
        # 不同值应该更新
        assert optimizer.should_update_field('answer', 'old', 'new') is True
        
        # 只读字段不应该更新
        assert optimizer.should_update_field('query', 'old', 'new') is False
    
    def test_optimize_state_update(self):
        """测试优化状态更新"""
        optimizer = StateOptimizer()
        
        old_state: ResearchSystemState = {
            "query": "test query",
            "answer": "old answer",
            "confidence": 0.5,
            "context": {},
            "evidence": [],
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
            "route_path": "simple",
            "complexity_score": 0.0,
            "final_answer": None
        }
        
        new_state = old_state.copy()
        new_state['answer'] = 'new answer'  # 改变
        new_state['confidence'] = 0.5  # 相同（不应该更新）
        new_state['query'] = 'modified query'  # 只读字段（不应该更新）
        
        optimized = optimizer.optimize_state_update(old_state, new_state, "test_node")
        
        # answer应该更新
        assert optimized['answer'] == 'new answer'
        # query不应该被更新（只读字段）
        assert optimized['query'] == 'test query'
    
    def test_deep_compare(self):
        """测试深度比较"""
        optimizer = StateOptimizer()
        
        old_state = {
            'evidence': [{'id': 1, 'content': 'test'}],
            'context': {'key': 'value'}
        }
        
        new_state = {
            'evidence': [{'id': 1, 'content': 'test'}],  # 相同
            'context': {'key': 'value'}  # 相同
        }
        
        # 深度比较应该返回True（相等）
        assert optimizer._deep_equal(old_state['evidence'], new_state['evidence']) is True
        assert optimizer._deep_equal(old_state['context'], new_state['context']) is True
    
    def test_update_statistics(self):
        """测试更新统计"""
        optimizer = StateOptimizer()
        
        old_state = {'answer': 'old'}
        new_state1 = {'answer': 'new1'}
        new_state2 = {'answer': 'new2'}
        
        optimizer.optimize_state_update(old_state, new_state1, "node1")
        optimizer.optimize_state_update(old_state, new_state2, "node2")
        
        stats = optimizer.get_update_statistics()
        
        assert stats['total_updates'] == 2
        assert 'answer' in stats['field_update_counts']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

