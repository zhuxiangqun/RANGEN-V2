#!/usr/bin/env python3
"""
LangGraph Workflow Error Handling Utilities

提取的错误处理和重试机制
"""
import asyncio
import logging
from typing import Any, Callable, Optional, Tuple

logger = logging.getLogger(__name__)


class ErrorCategory:
    """错误分类"""
    RETRYABLE = "retryable"  # 可重试错误
    FATAL = "fatal"  # 致命错误
    TEMPORARY = "temporary"  # 临时错误
    PERMANENT = "permanent"  # 永久错误


def classify_error(error: Exception) -> str:
    """分类错误"""
    error_str = str(error).lower()
    
    if isinstance(error, (TimeoutError, ConnectionError)):
        return ErrorCategory.TEMPORARY
    
    retryable_keywords = ['timeout', 'connection', 'network', 'temporary', 'unavailable', 'rate limit']
    if any(keyword in error_str for keyword in retryable_keywords):
        return ErrorCategory.RETRYABLE
    
    fatal_keywords = ['config', 'invalid', 'missing', 'not found', 'permission', 'authentication']
    if any(keyword in error_str for keyword in fatal_keywords):
        return ErrorCategory.FATAL
    
    return ErrorCategory.RETRYABLE


def should_retry_error(error: Exception, retry_count: int, max_retries: int = 3) -> bool:
    """判断是否应该重试错误"""
    if retry_count >= max_retries:
        return False
    
    error_category = classify_error(error)
    
    if error_category in [ErrorCategory.RETRYABLE, ErrorCategory.TEMPORARY]:
        return True
    
    return False


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """重试机制，带指数退避"""
    delay = initial_delay
    
    for attempt in range(max_retries):
        try:
            return await func()
        except exceptions as e:
            if attempt == max_retries - 1:
                logger.error(f"重试次数用尽: {e}")
                raise
            
            if not should_retry_error(e, attempt, max_retries):
                raise
            
            logger.warning(f"重试 {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(min(delay, max_delay))
            delay *= backoff_factor


def handle_node_error(
    error: Exception,
    node_name: str,
    state: dict
) -> dict:
    """处理节点错误"""
    error_category = classify_error(error)
    
    return {
        "node_name": node_name,
        "error": str(error),
        "error_category": error_category,
        "should_retry": should_retry_error(error, 0),
        "state_snapshot": state.copy() if state else {}
    }


def record_node_time(state: dict, node_name: str, execution_time: float) -> dict:
    """记录节点执行时间"""
    if 'node_timings' not in state:
        state['node_timings'] = {}
    
    if node_name not in state['node_timings']:
        state['node_timings'][node_name] = []
    
    state['node_timings'][node_name].append({
        'time': execution_time,
        'timestamp': __import__('time').time()
    })
    
    return state
