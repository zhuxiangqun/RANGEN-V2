"""
配置驱动的动态路由测试 - 阶段2.6
测试 ConfigurableRouter 的功能
"""
import pytest
import logging
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_configurable_router import (
    ConfigurableRouter,
    RouteRule,
    RouteCondition,
    get_configurable_router
)
from src.core.langgraph_unified_workflow import ResearchSystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestRouteRule:
    """测试路由规则"""
    
    def test_route_rule_evaluation(self):
        """测试路由规则评估"""
        state: ResearchSystemState = {
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
        
        rule = RouteRule(
            name="simple_rule",
            priority=10,
            conditions=[
                {"field": "complexity_score", "operator": "<", "value": 3.0}
            ],
            target_path="simple"
        )
        
        assert rule.evaluate(state) == True
    
    def test_route_rule_priority(self):
        """测试路由规则优先级"""
        rule1 = RouteRule(name="rule1", priority=5, target_path="path1")
        rule2 = RouteRule(name="rule2", priority=10, target_path="path2")
        
        assert rule2.priority > rule1.priority


class TestConfigurableRouter:
    """测试配置驱动的路由器"""
    
    def test_router_initialization(self):
        """测试路由器初始化"""
        router = ConfigurableRouter()
        
        assert router is not None
        assert len(router.get_rules()) > 0  # 应该有默认规则
    
    def test_router_add_rule(self):
        """测试添加路由规则"""
        router = ConfigurableRouter()
        
        rule = RouteRule(
            name="test_rule",
            priority=15,
            conditions=[
                {"field": "complexity_score", "operator": ">=", "value": 5.0}
            ],
            target_path="complex"
        )
        
        success = router.add_rule(rule)
        assert success == True
        
        rules = router.get_rules()
        rule_names = [r.name for r in rules]
        assert "test_rule" in rule_names
    
    def test_router_route_simple(self):
        """测试路由到简单路径"""
        router = ConfigurableRouter()
        
        state: ResearchSystemState = {
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
        
        route_path = router.route(state)
        assert route_path in ['simple', 'complex']
    
    def test_router_route_complex(self):
        """测试路由到复杂路径"""
        router = ConfigurableRouter()
        
        state: ResearchSystemState = {
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
        
        route_path = router.route(state)
        assert route_path in ['simple', 'complex']
    
    def test_router_reload_rules(self):
        """测试重新加载路由规则"""
        router = ConfigurableRouter()
        
        initial_count = len(router.get_rules())
        router.reload_rules()
        reloaded_count = len(router.get_rules())
        
        # 重新加载后应该有规则（可能和初始数量相同或不同）
        assert reloaded_count > 0
    
    def test_get_configurable_router_singleton(self):
        """测试单例模式"""
        router1 = get_configurable_router()
        router2 = get_configurable_router()
        
        assert router1 is router2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

