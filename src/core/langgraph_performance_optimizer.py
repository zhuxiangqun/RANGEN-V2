"""
性能优化模块 - 阶段5.1
实现节点并行化、缓存机制优化、LLM调用优化等功能
"""
import logging
import time
import asyncio
import hashlib
from typing import Dict, Any, Optional, List, Callable, Awaitable
from functools import wraps
from collections import OrderedDict

logger = logging.getLogger(__name__)


class WorkflowCache:
    """工作流缓存管理器 - 优化查询结果、推理步骤、Agent思考的缓存"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒）
        """
        self.max_size = max_size
        self.ttl = ttl
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def _generate_key(self, cache_type: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 标准化参数
        key_parts = [cache_type]
        for arg in args:
            if isinstance(arg, (str, int, float, bool)):
                key_parts.append(str(arg))
            elif isinstance(arg, dict):
                # 对字典进行排序以确保一致性
                key_parts.append(hashlib.md5(str(sorted(arg.items())).encode()).hexdigest())
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        
        return hashlib.md5("|".join(key_parts).encode()).hexdigest()
    
    def get(self, cache_type: str, *args, **kwargs) -> Optional[Any]:
        """获取缓存
        
        Args:
            cache_type: 缓存类型（'query_result', 'reasoning_steps', 'agent_thought'等）
            *args, **kwargs: 用于生成缓存键的参数
        
        Returns:
            缓存的值，如果不存在或过期返回None
        """
        cache_key = self._generate_key(cache_type, *args, **kwargs)
        
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            # 检查是否过期
            if time.time() - entry['timestamp'] < self.ttl:
                # 更新访问顺序（LRU）
                self._cache.move_to_end(cache_key)
                self._cache_stats['hits'] += 1
                return entry['value']
            else:
                # 过期，删除
                del self._cache[cache_key]
                self._cache_stats['evictions'] += 1
        
        self._cache_stats['misses'] += 1
        return None
    
    def set(self, cache_type: str, value: Any, *args, **kwargs) -> None:
        """设置缓存
        
        Args:
            cache_type: 缓存类型
            value: 要缓存的值
            *args, **kwargs: 用于生成缓存键的参数
        """
        cache_key = self._generate_key(cache_type, *args, **kwargs)
        
        # 如果缓存已满，删除最旧的条目（LRU）
        if len(self._cache) >= self.max_size and cache_key not in self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._cache_stats['evictions'] += 1
        
        # 设置缓存
        self._cache[cache_key] = {
            'value': value,
            'timestamp': time.time()
        }
        # 更新访问顺序
        self._cache.move_to_end(cache_key)
    
    def clear(self, cache_type: Optional[str] = None) -> None:
        """清空缓存
        
        Args:
            cache_type: 如果指定，只清空该类型的缓存；否则清空所有缓存
        """
        if cache_type is None:
            self._cache.clear()
        else:
            # 只清空指定类型的缓存
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(cache_type)]
            for key in keys_to_remove:
                del self._cache[key]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_requests = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = self._cache_stats['hits'] / total_requests if total_requests > 0 else 0.0
        
        return {
            **self._cache_stats,
            'total_requests': total_requests,
            'hit_rate': hit_rate,
            'current_size': len(self._cache),
            'max_size': self.max_size
        }


class ParallelExecutor:
    """并行执行器 - 识别并并行执行可并行执行的节点"""
    
    def __init__(self):
        """初始化并行执行器"""
        self.logger = logging.getLogger(__name__)
    
    def identify_parallel_nodes(self, nodes: List[Dict[str, Any]]) -> List[List[str]]:
        """识别可并行执行的节点组
        
        Args:
            nodes: 节点列表，每个节点包含 'name', 'dependencies' 等信息
        
        Returns:
            可并行执行的节点组列表
        """
        # 构建依赖图
        dependency_graph = {}
        for node in nodes:
            node_name = node.get('name')
            dependencies = node.get('dependencies', [])
            dependency_graph[node_name] = dependencies
        
        # 拓扑排序，识别可并行执行的节点
        parallel_groups = []
        remaining_nodes = set(dependency_graph.keys())
        completed_nodes = set()
        
        while remaining_nodes:
            # 找到所有没有未完成依赖的节点
            ready_nodes = [
                node for node in remaining_nodes
                if all(dep in completed_nodes for dep in dependency_graph.get(node, []))
            ]
            
            if not ready_nodes:
                # 有循环依赖或错误，返回剩余节点作为单个组
                parallel_groups.append(list(remaining_nodes))
                break
            
            # 这些节点可以并行执行
            parallel_groups.append(ready_nodes)
            completed_nodes.update(ready_nodes)
            remaining_nodes -= set(ready_nodes)
        
        return parallel_groups
    
    async def execute_parallel(
        self,
        tasks: List[Callable[[], Awaitable[Any]]],
        max_concurrent: int = 5
    ) -> List[Any]:
        """并行执行任务
        
        Args:
            tasks: 任务列表
            max_concurrent: 最大并发数
        
        Returns:
            任务执行结果列表
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_with_semaphore(task):
            async with semaphore:
                return await task()
        
        results = await asyncio.gather(*[execute_with_semaphore(task) for task in tasks])
        return results


class LLMCallOptimizer:
    """LLM调用优化器 - 实现批量、去重、缓存优化"""
    
    def __init__(self, cache: Optional[WorkflowCache] = None):
        """初始化LLM调用优化器
        
        Args:
            cache: 缓存管理器（可选）
        """
        self.cache = cache or WorkflowCache()
        self.pending_calls: List[Dict[str, Any]] = []
        self.batch_size = 5
        self.batch_timeout = 0.1  # 100ms
    
    async def call_with_optimization(
        self,
        llm_func: Callable[[str], Awaitable[str]],
        prompt: str,
        cache_key: Optional[str] = None
    ) -> str:
        """优化的LLM调用（支持缓存和去重）
        
        Args:
            llm_func: LLM调用函数
            prompt: 提示词
            cache_key: 缓存键（可选，如果不提供则自动生成）
        
        Returns:
            LLM响应
        """
        # 生成缓存键
        if cache_key is None:
            cache_key = hashlib.md5(prompt.encode()).hexdigest()
        
        # 检查缓存
        cached_result = self.cache.get('llm_call', prompt)
        if cached_result is not None:
            logger.debug(f"✅ LLM调用缓存命中: {prompt[:50]}...")
            return cached_result
        
        # 检查是否有相同的待处理调用（去重）
        for pending in self.pending_calls:
            if pending['prompt'] == prompt:
                # 等待相同的调用完成
                logger.debug(f"🔄 LLM调用去重: 等待相同调用完成")
                return await pending['future']
        
        # 创建新的调用
        future = asyncio.create_task(llm_func(prompt))
        self.pending_calls.append({
            'prompt': prompt,
            'future': future,
            'cache_key': cache_key
        })
        
        try:
            result = await future
            # 缓存结果
            self.cache.set('llm_call', result, prompt)
            return result
        finally:
            # 从待处理列表中移除
            self.pending_calls = [p for p in self.pending_calls if p['prompt'] != prompt]
    
    async def batch_call(
        self,
        llm_func: Callable[[List[str]], Awaitable[List[str]]],
        prompts: List[str]
    ) -> List[str]:
        """批量LLM调用
        
        Args:
            llm_func: 支持批量调用的LLM函数
            prompts: 提示词列表
        
        Returns:
            LLM响应列表
        """
        # 检查缓存
        results = []
        uncached_prompts = []
        uncached_indices = []
        
        for i, prompt in enumerate(prompts):
            cached_result = self.cache.get('llm_call', prompt)
            if cached_result is not None:
                results.append((i, cached_result))
            else:
                uncached_prompts.append(prompt)
                uncached_indices.append(i)
        
        # 批量调用未缓存的提示词
        if uncached_prompts:
            batch_results = await llm_func(uncached_prompts)
            for idx, result, prompt in zip(uncached_indices, batch_results, uncached_prompts):
                results.append((idx, result))
                # 缓存结果（修复：使用正确的 prompt 作为 key）
                self.cache.set('llm_call', prompt, result)
        
        # 按原始顺序排序
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]


# 全局缓存实例
_workflow_cache = None
_parallel_executor = None
_llm_optimizer = None


def get_workflow_cache() -> WorkflowCache:
    """获取全局工作流缓存实例"""
    global _workflow_cache
    if _workflow_cache is None:
        _workflow_cache = WorkflowCache()
    return _workflow_cache


def get_parallel_executor() -> ParallelExecutor:
    """获取全局并行执行器实例"""
    global _parallel_executor
    if _parallel_executor is None:
        _parallel_executor = ParallelExecutor()
    return _parallel_executor


def get_llm_optimizer() -> LLMCallOptimizer:
    """获取全局LLM调用优化器实例"""
    global _llm_optimizer
    if _llm_optimizer is None:
        _llm_optimizer = LLMCallOptimizer(cache=get_workflow_cache())
    return _llm_optimizer


def cached_node(cache_type: str):
    """节点缓存装饰器
    
    使用示例:
    @cached_node('query_result')
    async def my_node(state):
        # 节点逻辑
        return state
    """
    def decorator(node_func: Callable[[Any], Awaitable[Any]]) -> Callable[[Any], Awaitable[Any]]:
        @wraps(node_func)
        async def wrapper(state: Any) -> Any:
            cache = get_workflow_cache()
            
            # 生成缓存键（基于查询和状态）
            query = state.get('query', '') if isinstance(state, dict) else ''
            cache_key = f"{cache_type}:{query}"
            
            # 检查缓存
            cached_result = cache.get(cache_type, query)
            if cached_result is not None:
                logger.info(f"✅ [Cache] {cache_type} 缓存命中: {query[:50]}...")
                # 合并缓存结果到状态
                if isinstance(state, dict) and isinstance(cached_result, dict):
                    state.update(cached_result)
                return state
            
            # 执行节点
            result = await node_func(state)
            
            # 缓存结果
            if isinstance(result, dict):
                cache.set(cache_type, result, query)
            
            return result
        
        return wrapper
    return decorator

