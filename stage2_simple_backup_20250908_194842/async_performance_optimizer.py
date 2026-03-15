#!/usr/bin/env pythonconfig.DEFAULT_MAX_RETRIES
"""
异步性能优化器 - 专门优化异步组件的性能
"""
import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

@dataclass
class AsyncTaskMetrics:
    """异步任务指标"""
    task_id: str
    task_name: str
    start_time: float
    end_time: Optional[float] = None
    execution_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None

class AsyncPerformanceOptimizer:
    """异步性能优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_history: deque[AsyncTaskMetrics] = deque(maxlen=config.DEFAULT_LIMIT0)
        self.optimization_callbacks: List[Callable] = []
        
        self.logger.info("✅ 异步性能优化器初始化完成")

    async def optimize_task_execution(self, task_func: Callable, *args, **kwargs) -> Any:
        """优化任务执行"""
        start_time = time.time()
        task_id = f"task_{int(start_time * config.DEFAULT_LIMIT0)}"
        
        metrics = AsyncTaskMetrics(
            task_id=task_id,
            task_name=task_func.__name__,
            start_time=start_time
        )
        
        try:
            # 执行任务
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                # 如果是同步函数，在线程池中执行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, task_func, *args, **kwargs)
            
            # 记录成功
            end_time = time.time()
            metrics.end_time = end_time
            metrics.execution_time = end_time - start_time
            metrics.success = True
            
            self.logger.info(f"✅ 任务 {task_func.__name__} 执行成功，耗时: {metrics.execution_time:.2f}s")
            return result
            
        except Exception as e:
            # 记录失败
            end_time = time.time()
            metrics.end_time = end_time
            metrics.execution_time = end_time - start_time
            metrics.error_message = str(e)
            
            self.logger.error(f"❌ 任务 {task_func.__name__} 执行失败: {e}")
            raise
        finally:
            # 保存指标
            self.task_history.append(metrics)

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.task_history:
            return {}
        
        successful_tasks = [t for t in self.task_history if t.success]
        failed_tasks = [t for t in self.task_history if not t.success]
        
        if successful_tasks:
            # 过滤掉None值
            execution_times = [t.execution_time for t in successful_tasks if t.execution_time is not None]
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)
                max_execution_time = max(execution_times)
                min_execution_time = min(execution_times)
            else:
                avg_execution_time = max_execution_time = min_execution_time = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
        else:
            avg_execution_time = max_execution_time = min_execution_time = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))
        
        return {
            "total_tasks": len(self.task_history),
            "successful_tasks": len(successful_tasks),
            "failed_tasks": len(failed_tasks),
            "success_rate": len(successful_tasks) / len(self.task_history) if self.task_history else get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
            "average_execution_time": avg_execution_time,
            "max_execution_time": max_execution_time,
            "min_execution_time": min_execution_time
        }

# 全局实例
_async_performance_optimizer = None

def get_async_performance_optimizer() -> AsyncPerformanceOptimizer:
    """获取异步性能优化器实例"""
    global _async_performance_optimizer
    if _async_performance_optimizer is None:
        _async_performance_optimizer = AsyncPerformanceOptimizer()
    return _async_performance_optimizer
