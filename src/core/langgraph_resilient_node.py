"""
ResilientNode 包装器 - 阶段2.2
为工作流节点提供统一的错误恢复和重试机制
"""
import asyncio
import logging
import time
from typing import Callable, Optional, Dict, Any, TypeVar, Awaitable
from functools import wraps

from src.core.langgraph_unified_workflow import (
    ResearchSystemState,
    ErrorCategory,
    classify_error,
    should_retry_error,
    handle_node_error
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ResilientNode:
    """ResilientNode 包装器 - 为节点提供错误恢复和重试机制
    
    特性：
    - 自动重试（带指数退避）
    - 错误分类和处理
    - 降级策略（fallback 节点）
    - 错误恢复
    """
    
    def __init__(
        self,
        node_func: Callable[[ResearchSystemState], Awaitable[ResearchSystemState]],
        node_name: str,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0,
        fallback_node: Optional[Callable[[ResearchSystemState], Awaitable[ResearchSystemState]]] = None
    ):
        """
        Args:
            node_func: 节点函数
            node_name: 节点名称
            max_retries: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            backoff_factor: 退避因子
            fallback_node: 降级节点（可选）
        """
        self.node_func = node_func
        self.node_name = node_name
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.fallback_node = fallback_node
    
    async def __call__(self, state: ResearchSystemState) -> ResearchSystemState:
        """执行节点（带重试和错误恢复）"""
        retry_count = state.get('retry_count', 0)
        delay = self.initial_delay
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # 更新重试计数
                state['retry_count'] = retry_count + attempt
                
                # 执行节点
                result_state = await self.node_func(state)
                
                # 执行成功，重置重试计数
                if 'retry_count' in result_state:
                    result_state['retry_count'] = 0
                
                return result_state
                
            except Exception as e:
                last_exception = e
                error_category = classify_error(e)
                
                # 检查是否应该重试
                if attempt < self.max_retries and should_retry_error(e, attempt, self.max_retries):
                    logger.warning(
                        f"⚠️ [{self.node_name}] [{error_category}] "
                        f"重试 {attempt + 1}/{self.max_retries}，延迟 {delay:.2f} 秒: {e}"
                    )
                    
                    # 更新状态中的错误信息
                    state = handle_node_error(state, e, self.node_name, attempt, self.max_retries)
                    
                    # 等待后重试
                    await asyncio.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    # 不再重试
                    logger.error(
                        f"❌ [{self.node_name}] [{error_category}] "
                        f"重试 {attempt} 次后仍然失败: {e}"
                    )
                    break
        
        # 所有重试都失败，尝试降级策略
        if self.fallback_node:
            logger.info(f"🔄 [{self.node_name}] 尝试降级策略...")
            try:
                return await self.fallback_node(state)
            except Exception as fallback_error:
                logger.error(f"❌ [{self.node_name}] 降级策略也失败: {fallback_error}")
                return handle_node_error(state, fallback_error, f"{self.node_name}_fallback", 0, 0)
        
        # 如果没有降级策略或降级也失败，返回错误状态
        if last_exception:
            return handle_node_error(state, last_exception, self.node_name, self.max_retries, self.max_retries)
        
        return state


def resilient_node(
    node_name: str,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    fallback_node: Optional[Callable[[ResearchSystemState], Awaitable[ResearchSystemState]]] = None
):
    """装饰器：将节点函数包装为 ResilientNode
    
    使用示例：
    @resilient_node("my_node", max_retries=3)
    async def my_node(state: ResearchSystemState) -> ResearchSystemState:
        # 节点逻辑
        return state
    """
    def decorator(
        node_func: Callable[[ResearchSystemState], Awaitable[ResearchSystemState]]
    ) -> ResilientNode:
        return ResilientNode(
            node_func=node_func,
            node_name=node_name,
            max_retries=max_retries,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            fallback_node=fallback_node
        )
    return decorator

