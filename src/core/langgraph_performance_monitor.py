"""
性能监控节点 - 阶段2.3
记录节点执行时间、token使用情况、API调用次数等性能指标
"""
import time
import logging
from typing import Dict, Any, Callable, Awaitable
from functools import wraps

from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """性能监控器 - 记录节点性能指标"""
    
    @staticmethod
    def record_node_execution(
        state: ResearchSystemState,
        node_name: str,
        execution_time: float
    ) -> ResearchSystemState:
        """记录节点执行时间
        
        Args:
            state: 工作流状态
            node_name: 节点名称
            execution_time: 执行时间（秒）
        
        Returns:
            更新后的状态
        """
        if 'node_execution_times' not in state:
            state['node_execution_times'] = {}
        
        state['node_execution_times'][node_name] = execution_time
        
        # 兼容旧字段
        if 'node_times' not in state:
            state['node_times'] = {}
        state['node_times'][node_name] = execution_time
        
        return state
    
    @staticmethod
    def record_token_usage(
        state: ResearchSystemState,
        component: str,
        tokens: int,
        token_type: str = "total"  # "input", "output", "total"
    ) -> ResearchSystemState:
        """记录 token 使用情况
        
        Args:
            state: 工作流状态
            component: 组件名称（如 "llm_call", "embedding"）
            tokens: token 数量
            token_type: token 类型
        
        Returns:
            更新后的状态
        """
        if 'token_usage' not in state:
            state['token_usage'] = {}
        
        key = f"{component}_{token_type}"
        if key not in state['token_usage']:
            state['token_usage'][key] = 0
        
        state['token_usage'][key] += tokens
        
        return state
    
    @staticmethod
    def record_api_call(
        state: ResearchSystemState,
        api_name: str,
        count: int = 1
    ) -> ResearchSystemState:
        """记录 API 调用次数
        
        Args:
            state: 工作流状态
            api_name: API 名称（如 "llm_api", "embedding_api"）
            count: 调用次数
        
        Returns:
            更新后的状态
        """
        if 'api_calls' not in state:
            state['api_calls'] = {}
        
        if api_name not in state['api_calls']:
            state['api_calls'][api_name] = 0
        
        state['api_calls'][api_name] += count
        
        return state
    
    @staticmethod
    def get_performance_summary(state: ResearchSystemState) -> Dict[str, Any]:
        """获取性能摘要
        
        Args:
            state: 工作流状态
        
        Returns:
            性能摘要字典
        """
        summary = {
            'total_execution_time': state.get('execution_time', 0.0),
            'node_execution_times': state.get('node_execution_times', {}),
            'total_token_usage': sum(state.get('token_usage', {}).values()),
            'token_usage_by_component': state.get('token_usage', {}),
            'total_api_calls': sum(state.get('api_calls', {}).values()),
            'api_calls_by_type': state.get('api_calls', {}),
        }
        
        # 计算节点执行时间统计
        node_times = state.get('node_execution_times', {})
        if node_times:
            summary['slowest_node'] = max(node_times.items(), key=lambda x: x[1])
            summary['fastest_node'] = min(node_times.items(), key=lambda x: x[1])
            summary['avg_node_time'] = sum(node_times.values()) / len(node_times)
        
        return summary


def monitor_performance(node_name: str):
    """装饰器：自动监控节点性能
    
    使用示例：
    @monitor_performance("my_node")
    async def my_node(state: ResearchSystemState) -> ResearchSystemState:
        # 节点逻辑
        return state
    """
    def decorator(
        node_func: Callable[[ResearchSystemState], Awaitable[ResearchSystemState]]
    ) -> Callable[[ResearchSystemState], Awaitable[ResearchSystemState]]:
        @wraps(node_func)
        async def wrapper(state: ResearchSystemState) -> ResearchSystemState:
            start_time = time.time()
            
            try:
                # 执行节点
                result_state = await node_func(state)
                
                # 记录执行时间
                execution_time = time.time() - start_time
                PerformanceMonitor.record_node_execution(
                    result_state,
                    node_name,
                    execution_time
                )
                
                logger.debug(f"⏱️ [{node_name}] 执行时间: {execution_time:.3f}秒")
                
                return result_state
            except Exception as e:
                # 即使出错也记录执行时间
                execution_time = time.time() - start_time
                PerformanceMonitor.record_node_execution(
                    state,
                    node_name,
                    execution_time
                )
                raise
        
        return wrapper
    return decorator


async def performance_monitor_node(state: ResearchSystemState) -> ResearchSystemState:
    """性能监控节点 - 汇总性能指标并记录到状态
    
    这个节点可以在工作流中插入，用于汇总和记录性能指标
    """
    monitor = PerformanceMonitor()
    summary = monitor.get_performance_summary(state)
    
    # 将性能摘要保存到元数据
    if 'metadata' not in state:
        state['metadata'] = {}
    
    state['metadata']['performance_summary'] = summary
    
    logger.info(f"📊 [Performance Monitor] 性能摘要:")
    logger.info(f"   总执行时间: {summary['total_execution_time']:.2f}秒")
    logger.info(f"   节点执行时间: {len(summary['node_execution_times'])} 个节点")
    if summary.get('slowest_node'):
        logger.info(f"   最慢节点: {summary['slowest_node'][0]} ({summary['slowest_node'][1]:.2f}秒)")
    logger.info(f"   总 Token 使用: {summary['total_token_usage']}")
    logger.info(f"   总 API 调用: {summary['total_api_calls']}")
    
    return state

