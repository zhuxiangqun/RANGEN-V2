"""
性能优化模块测试 - 阶段5.4
测试缓存、并行执行、LLM调用优化等功能
"""
import pytest  # type: ignore
import asyncio
import time
import logging
from typing import Dict, Any

# 添加项目根目录到路径
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.langgraph_performance_optimizer import (
    WorkflowCache,
    ParallelExecutor,
    LLMCallOptimizer,
    get_workflow_cache,
    get_parallel_executor,
    get_llm_optimizer,
    cached_node
)
from src.core.langgraph_unified_workflow import ResearchSystemState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWorkflowCache:
    """测试工作流缓存"""
    
    def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        cache = WorkflowCache(max_size=100, ttl=3600)
        
        # 设置缓存
        cache.set('query_result', {'answer': 'test answer'}, 'test query')
        
        # 获取缓存
        result = cache.get('query_result', 'test query')
        assert result is not None
        assert result['answer'] == 'test answer'
    
    def test_cache_expiration(self):
        """测试缓存过期"""
        cache = WorkflowCache(max_size=100, ttl=0.1)  # 100ms TTL
        
        # 设置缓存
        cache.set('query_result', {'answer': 'test answer'}, 'test query')
        
        # 立即获取应该成功
        result = cache.get('query_result', 'test query')
        assert result is not None
        
        # 等待过期
        time.sleep(0.2)
        
        # 过期后获取应该返回None
        result = cache.get('query_result', 'test query')
        assert result is None
    
    def test_cache_lru_eviction(self):
        """测试LRU缓存淘汰"""
        cache = WorkflowCache(max_size=3, ttl=3600)
        
        # 设置3个缓存项
        cache.set('query_result', {'answer': '1'}, 'query1')
        cache.set('query_result', {'answer': '2'}, 'query2')
        cache.set('query_result', {'answer': '3'}, 'query3')
        
        # 访问第一个，使其成为最近使用的
        cache.get('query_result', 'query1')
        
        # 添加第4个，应该淘汰query2（最久未使用）
        cache.set('query_result', {'answer': '4'}, 'query4')
        
        # query2应该被淘汰
        assert cache.get('query_result', 'query2') is None
        # query1应该还在
        assert cache.get('query_result', 'query1') is not None
    
    def test_cache_stats(self):
        """测试缓存统计"""
        cache = WorkflowCache(max_size=100, ttl=3600)
        
        # 设置和获取缓存
        cache.set('query_result', {'answer': 'test'}, 'query1')
        cache.get('query_result', 'query1')  # 命中
        cache.get('query_result', 'query2')  # 未命中
        
        stats = cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['hit_rate'] == 0.5


class TestParallelExecutor:
    """测试并行执行器"""
    
    def test_identify_parallel_nodes(self):
        """测试识别可并行执行的节点"""
        executor = ParallelExecutor()
        
        nodes = [
            {'name': 'node1', 'dependencies': []},
            {'name': 'node2', 'dependencies': []},
            {'name': 'node3', 'dependencies': ['node1', 'node2']},
            {'name': 'node4', 'dependencies': ['node3']}
        ]
        
        parallel_groups = executor.identify_parallel_nodes(nodes)
        
        # node1和node2应该可以并行执行
        assert len(parallel_groups) >= 2
        assert 'node1' in parallel_groups[0] or 'node2' in parallel_groups[0]
    
    @pytest.mark.asyncio
    async def test_execute_parallel(self):
        """测试并行执行"""
        executor = ParallelExecutor()
        
        async def task1():
            await asyncio.sleep(0.1)
            return 'result1'
        
        async def task2():
            await asyncio.sleep(0.1)
            return 'result2'
        
        async def task3():
            await asyncio.sleep(0.1)
            return 'result3'
        
        tasks = [task1, task2, task3]
        start_time = time.time()
        results = await executor.execute_parallel(tasks, max_concurrent=3)
        elapsed_time = time.time() - start_time
        
        # 应该并行执行，总时间应该接近0.1秒（而不是0.3秒）
        assert elapsed_time < 0.2
        assert results == ['result1', 'result2', 'result3']


class TestLLMCallOptimizer:
    """测试LLM调用优化器"""
    
    @pytest.mark.asyncio
    async def test_call_with_cache(self):
        """测试带缓存的LLM调用"""
        cache = WorkflowCache()
        optimizer = LLMCallOptimizer(cache=cache)
        
        call_count = 0
        
        async def mock_llm_func(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"Response to: {prompt}"
        
        # 第一次调用
        result1 = await optimizer.call_with_optimization(mock_llm_func, "test prompt")
        assert call_count == 1
        
        # 第二次调用（应该使用缓存）
        result2 = await optimizer.call_with_optimization(mock_llm_func, "test prompt")
        assert call_count == 1  # 不应该再次调用
        assert result1 == result2
    
    @pytest.mark.asyncio
    async def test_call_deduplication(self):
        """测试LLM调用去重"""
        cache = WorkflowCache()
        optimizer = LLMCallOptimizer(cache=cache)
        
        call_count = 0
        
        async def mock_llm_func(prompt: str) -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # 模拟延迟
            return f"Response to: {prompt}"
        
        # 同时发起两个相同的调用
        task1 = optimizer.call_with_optimization(mock_llm_func, "test prompt")
        task2 = optimizer.call_with_optimization(mock_llm_func, "test prompt")
        
        results = await asyncio.gather(task1, task2)
        
        # 应该只调用一次（去重）
        assert call_count == 1
        assert results[0] == results[1]


class TestCachedNodeDecorator:
    """测试缓存节点装饰器"""
    
    @pytest.mark.asyncio
    async def test_cached_node(self):
        """测试缓存节点装饰器"""
        call_count = 0
        
        @cached_node('query_result')
        async def test_node(state: Dict[str, Any]) -> Dict[str, Any]:
            nonlocal call_count
            call_count += 1
            state['answer'] = 'test answer'
            return state
        
        state1: ResearchSystemState = {
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
        
        # 第一次调用
        result1 = await test_node(state1)
        assert call_count == 1
        
        # 第二次调用（应该使用缓存）
        state2 = state1.copy()
        result2 = await test_node(state2)
        assert call_count == 1  # 不应该再次调用


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

