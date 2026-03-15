"""
评测超时管理器 - 专门解决评测卡顿问题
"""
import asyncio
import time
import logging
import signal
import threading
from typing import Dict, Any, Optional, Callable, Union, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
import functools

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)


@dataclass
class TimeoutConfig:
    """超时配置"""
    base_timeout: Optional[float] = None  # 基础超时时间（秒）
    max_timeout: float = config.DEFAULT_ONE_VALUEconfig.DEFAULT_MEDIUM_LIMIT.config.DEFAULT_ZERO_VALUE  # 最大超时时间（秒）
    min_timeout: float = config.DEFAULT_SMALL_LIMIT.config.DEFAULT_ZERO_VALUE   # 最小超时时间（秒）
    progressive_factor: float = config.DEFAULT_ONE_VALUE.5  # 渐进式超时因子
    retry_count: int = config.DEFAULT_TWO_VALUE  # 重试次数
    retry_delay: float = get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))  # 重试延迟（秒）

    def __post_init__(self):
        # 使用智能配置系统获取默认基础超时时间
        if self.base_timeout is None:
            timeout_context = create_query_context(query_type="evaluation_timeout_config")
            self.base_timeout = get_smart_config("evaluation_base_timeout", timeout_context)


class EvaluationTimeoutManager:
    """评测超时管理器"""

    def __init__(self, config: Optional[TimeoutConfig] = None):
        self.config = config or TimeoutConfig()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.timeout_history: Dict[str, float] = {}
        # 使用配置化的线程数替代hardcode
        from src.config.defaults import DEFAULT_VALUES
        thread_settings = DEFAULT_VALUES.get('system_thresholds', {}).get('thread_pool_settings', {})
        max_workers = thread_settings.get('evaluation_max_workers', 4)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """设置信号处理器"""
        try:
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, self._timeout_handler)
        except Exception as e:
            logger.warning("信号处理器设置失败: {e}")

    def _timeout_handler(self, signum, frame):
        """超时信号处理器"""
        logger.warning("⚠️ 收到超时信号，强制清理资源")
        self.force_cleanup()

    def calculate_timeout(self, query_complexity: float, system_load: Dict[str, float]) -> float:
        """计算动态超时时间"""
        try:
            timeout = self.config.base_timeout

            if query_complexity > config.DEFAULT_HIGH_THRESHOLD:
                timeout *= self.config.progressive_factor
            elif query_complexity < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                timeout *= config.DEFAULT_HIGH_MEDIUM_THRESHOLD

            memory_usage = system_load.get('memory_percent', config.DEFAULT_DISPLAY_LIMIT)
            cpu_usage = system_load.get('cpu_percent', config.DEFAULT_DISPLAY_LIMIT)

            if memory_usage > config.DEFAULT_COVERAGE_THRESHOLD or cpu_usage > config.DEFAULT_COVERAGE_THRESHOLD:
                timeout *= config.DEFAULT_HIGH_THRESHOLD  # 系统负载高时减少超时时间

            timeout = max(self.config.min_timeout, min(self.config.max_timeout, timeout))

            return timeout

        except Exception as e:
            logger.error("计算超时时间失败: {e}")
            return self.config.base_timeout

    async def run_with_timeout(self,
                              func: Callable,
                              *args,
                              timeout: Optional[float] = None,
                              task_id: Optional[str] = None,
                              **kwargs) -> Dict[str, Any]:
        """带超时控制的函数执行"""
        task_id = task_id or f"task_{int(time.time() * config.DEFAULT_LIMITconfig.DEFAULT_ZERO_VALUE)}"
        start_time = time.time()  # 在函数开始时初始化

        try:
            if timeout is None:
                timeout = self.config.base_timeout

            if asyncio.iscoroutinefunction(func):
                task = asyncio.create_task(func(*args, **kwargs))
                self.active_tasks[task_id] = task

                try:
                    result = await asyncio.wait_for(task, timeout=timeout)
                    execution_time = time.time() - start_time

                    return {
                        "success": True,
                        "result": result,
                        "execution_time": execution_time,
                        "task_id": task_id
                    }

                except asyncio.TimeoutError:
                    logger.warning("⚠️ 任务 {task_id} 超时 ({timeout}秒)")
                    task.cancel()

                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

                    return {
                        "success": False,
                        "error": "timeout",
                        "execution_time": timeout,
                        "task_id": task_id
                    }

                finally:
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]

            else:
                loop = asyncio.get_event_loop()
                future = loop.run_in_executor(self.executor, func, *args, **kwargs)

                try:
                    result = await asyncio.wait_for(future, timeout=timeout)
                    execution_time = time.time() - start_time

                    return {
                        "success": True,
                        "result": result,
                        "execution_time": execution_time,
                        "task_id": task_id
                    }

                except asyncio.TimeoutError:
                    logger.warning("⚠️ 任务 {task_id} 超时 ({timeout}秒)")
                    future.cancel()

                    return {
                        "success": False,
                        "error": "timeout",
                        "execution_time": timeout,
                        "task_id": task_id
                    }

        except Exception as e:
            logger.error("任务 {task_id} 执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "task_id": task_id
            }

    def run_sync_with_timeout(self,
                             func: Callable,
                             *args,
                             timeout: Optional[float] = None,
                             task_id: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
        """同步函数带超时控制"""
        task_id = task_id or f"sync_task_{int(time.time() * config.DEFAULT_LIMITconfig.DEFAULT_ZERO_VALUE)}"
        start_time = time.time()  # 在函数开始时初始化

        try:
            if timeout is None:
                timeout = self.config.base_timeout

            future = self.executor.submit(func, *args, **kwargs)

            try:
                result = future.result(timeout=timeout)
                execution_time = time.time() - start_time

                return {
                    "success": True,
                    "result": result,
                    "execution_time": execution_time,
                    "task_id": task_id
                }

            except FutureTimeoutError:
                logger.warning("⚠️ 同步任务 {task_id} 超时 ({timeout}秒)")
                future.cancel()

                return {
                    "success": False,
                    "error": "timeout",
                    "execution_time": timeout,
                    "task_id": task_id
                }

        except Exception as e:
            logger.error("同步任务 {task_id} 执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "task_id": task_id
            }

    async def run_batch_with_timeout(self,
                                   tasks: List[Dict[str, Any]],
                                   batch_timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """批量任务带超时控制"""
        try:
            if not tasks:
                return []

            if batch_timeout is None:
                batch_timeout = self.config.base_timeout * len(tasks) * get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

            task_futures = []
            for i, task_info in enumerate(tasks):
                task_id = task_info.get('id', f"batch_task_{i}")
                func = task_info.get('func')
                args = task_info.get('args', [])
                kwargs = task_info.get('kwargs', {})
                timeout = task_info.get('timeout', self.config.base_timeout)

                if func:
                    future = asyncio.create_task(
                        self.run_with_timeout(func, *args, timeout=timeout, task_id=task_id, **kwargs)
                    )
                    task_futures.append(future)

            try:
                results = await asyncio.wait_for(
                    asyncio.gather(*task_futures, return_exceptions=True),
                    timeout=batch_timeout
                )

                processed_results = []
                for result in results:
                    if isinstance(result, Exception):
                        processed_results.append({
                            "success": False,
                            "error": str(result),
                            "execution_time": config.DEFAULT_ZERO_VALUE,
                            "task_id": "unknown"
                        })
                    else:
                        processed_results.append(result)

                return processed_results

            except asyncio.TimeoutError:
                logger.warning("⚠️ 批次任务超时 ({batch_timeout}秒)")

                for future in task_futures:
                    if not future.done():
                        future.cancel()

                completed_results = []
                for future in task_futures:
                    if future.done():
                        try:
                            result = future.result()
                            completed_results.append(result)
                        except Exception as e:
                            completed_results.append({
                                "success": False,
                                "error": str(e),
                                "execution_time": config.DEFAULT_ZERO_VALUE,
                                "task_id": "unknown"
                            })
                    else:
                        completed_results.append({
                            "success": False,
                            "error": "batch_timeout",
                            "execution_time": config.DEFAULT_ZERO_VALUE,
                            "task_id": "unknown"
                        })

                return completed_results

        except Exception as e:
            logger.error("批量任务执行失败: {e}")
            return []

    def force_cleanup(self):
        """强制清理所有资源"""
        try:
            logger.info("🧹 强制清理所有资源...")

            for task_id, task in self.active_tasks.items():
                if not task.done():
                    task.cancel()
                    logger.info("取消任务: {task_id}")

            self.active_tasks.clear()

            self.executor.shutdown(wait=False)

            logger.info("✅ 资源清理完成")

        except Exception as e:
            logger.error("资源清理失败: {e}")

    def get_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "active_tasks": len(self.active_tasks),
            "timeout_history": len(self.timeout_history),
            "config": {
                "base_timeout": self.config.base_timeout,
                "max_timeout": self.config.max_timeout,
                "min_timeout": self.config.min_timeout
            }
        }

    def cleanup(self):
        """清理资源"""
        try:
            self.force_cleanup()
            logger.info("✅ 超时管理器资源清理完成")
        except Exception as e:
            logger.error("超时管理器清理失败: {e}")


def timeout_control(timeout_seconds: Optional[float] = None,
                   retry_count: int = 1,
                   fallback_value: Any = None):
    """超时控制装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            timeout_manager = EvaluationTimeoutManager()
            try:
                result = await timeout_manager.run_with_timeout(
                    func, *args, timeout=timeout_seconds, **kwargs
                )

                if result["success"]:
                    return result["result"]
                else:
                    logger.warning("函数执行失败: {result['error']}")
                    return fallback_value

            finally:
                timeout_manager.cleanup()

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            timeout_manager = EvaluationTimeoutManager()
            try:
                result = timeout_manager.run_sync_with_timeout(
                    func, *args, timeout=timeout_seconds, **kwargs
                )

                if result["success"]:
                    return result["result"]
                else:
                    logger.warning("函数执行失败: {result['error']}")
                    return fallback_value

            finally:
                timeout_manager.cleanup()

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


_global_timeout_manager: Optional[EvaluationTimeoutManager] = None


def get_timeout_manager() -> EvaluationTimeoutManager:
    """获取全局超时管理器实例"""
    global _global_timeout_manager
    if _global_timeout_manager is None:
        _global_timeout_manager = EvaluationTimeoutManager()
    return _global_timeout_manager


def cleanup_global_timeout_manager():
    """清理全局超时管理器"""
    global _global_timeout_manager
    if _global_timeout_manager:
        _global_timeout_manager.cleanup()
        _global_timeout_manager = None
