#!/usr/bin/env python3
"""
异步工具类 - 提供异步编程的通用工具和辅助函数
"""

import asyncio
import logging
import time
import functools
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Coroutine
from dataclasses import dataclass
from enum import Enum
import weakref

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncTaskInfo:
    """异步任务信息"""
    task_id: str
    name: str
    status: TaskStatus
    created_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class AsyncUtils:
    """异步工具类"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
        self.task_counter = 0
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_info: Dict[str, AsyncTaskInfo] = {}
        self._task_lock = asyncio.Lock()
    
    async def process_data(self, data: Any) -> Any:
        """异步处理数据"""
        try:
            await asyncio.sleep(0.01)  # 真实异步处理
            return data
        except Exception as e:
            logger.error(f"数据处理失败: {e}")
            raise
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        return data is not None
    
    async def create_task(self, name: str, coro: Coroutine, 
                         timeout: Optional[float] = None) -> str:
        """创建异步任务"""
        async with self._task_lock:
            task_id = f"task_{self.task_counter}_{int(time.time())}"
            self.task_counter += 1
            
            # 创建任务信息
            task_info = AsyncTaskInfo(
                task_id=task_id,
                name=name,
                status=TaskStatus.PENDING,
                created_at=time.time()
            )
            self.task_info[task_id] = task_info
            
            # 创建异步任务
            if timeout:
                task = asyncio.create_task(
                    asyncio.wait_for(coro, timeout=timeout)
                )
            else:
                task = asyncio.create_task(coro)
            
            self.active_tasks[task_id] = task
            
            # 添加完成回调
            task.add_done_callback(
                functools.partial(self._task_completed, task_id)
            )
            
            logger.info(f"✅ 任务 {name} (ID: {task_id}) 创建成功")
            return task_id
    
    def _task_completed(self, task_id: str, task: asyncio.Task) -> None:
        """任务完成回调"""
        try:
            task_info = self.task_info.get(task_id)
            if not task_info:
                return
            
            task_info.completed_at = time.time()
            
            if task.cancelled():
                task_info.status = TaskStatus.CANCELLED
                logger.info(f"⚠️ 任务 {task_info.name} (ID: {task_id}) 被取消")
            elif task.exception():
                task_info.status = TaskStatus.FAILED
                task_info.error = str(task.exception())
                logger.error(f"❌ 任务 {task_info.name} (ID: {task_id}) 执行失败: {task_info.error}")
            else:
                task_info.status = TaskStatus.COMPLETED
                task_info.result = task.result()
                logger.info(f"✅ 任务 {task_info.name} (ID: {task_id}) 执行成功")
            
            # 清理活跃任务
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
                
        except Exception as e:
            logger.error(f"任务完成回调失败: {e}")
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """等待任务完成"""
        if task_id not in self.task_info:
            raise ValueError(f"任务 {task_id} 不存在")
        
        task_info = self.task_info[task_id]
        
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            try:
                if timeout:
                    await asyncio.wait_for(task, timeout=timeout)
                else:
                    await task
            except asyncio.TimeoutError:
                logger.error(f"❌ 任务 {task_info.name} (ID: {task_id}) 等待超时")
                raise
            except Exception as e:
                logger.error(f"❌ 任务 {task_info.name} (ID: {task_id}) 等待失败: {e}")
                raise
        
        if task_info.status == TaskStatus.COMPLETED:
            return task_info.result
        elif task_info.status == TaskStatus.FAILED:
            raise RuntimeError(f"任务执行失败: {task_info.error}")
        else:
            raise RuntimeError(f"任务状态异常: {task_info.status}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.active_tasks:
            return False
        
        try:
            task = self.active_tasks[task_id]
            task.cancel()
            logger.info(f"✅ 任务 {task_id} 取消成功")
            return True
        except Exception as e:
            logger.error(f"❌ 任务 {task_id} 取消失败: {e}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.task_info:
            return None
        
        task_info = self.task_info[task_id]
        return {
            "task_id": task_id,
            "name": task_info.name,
            "status": task_info.status.value,
            "created_at": task_info.created_at,
            "started_at": task_info.started_at,
            "completed_at": task_info.completed_at,
            "is_active": task_id in self.active_tasks,
            "error": task_info.error
        }
    
    def get_all_tasks_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务状态"""
        result = {}
        for task_id in self.task_info:
            status = self.get_task_status(task_id)
            if status:
                result[task_id] = status
        return result
    
    async def cleanup_completed_tasks(self, max_age: float = 3600.0) -> int:
        """清理已完成的任务"""
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, task_info in self.task_info.items():
            if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] 
                and task_info.completed_at 
                and (current_time - task_info.completed_at) > max_age):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.task_info[task_id]
        
        logger.info(f"✅ 清理了 {len(tasks_to_remove)} 个已完成任务")
        return len(tasks_to_remove)
    
    async def run_with_retry(self, coro: Coroutine, max_retries: int = 3, 
                           delay: float = 1.0, backoff: float = 2.0) -> Any:
        """带重试的异步执行"""
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return await coro
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = delay * (backoff ** attempt)
                    logger.warning(f"⚠️ 执行失败，{wait_time:.2f}秒后重试 (尝试 {attempt + 1}/{max_retries + 1}): {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ 重试 {max_retries} 次后仍然失败: {e}")
        
        raise last_exception
    
    async def run_parallel(self, coros: List[Coroutine], 
                          max_concurrent: Optional[int] = None) -> List[Any]:
        """并行执行多个协程"""
        try:
            if max_concurrent:
                semaphore = asyncio.Semaphore(max_concurrent)
                
                async def limited_coro(coro):
                    async with semaphore:
                        return await coro
                
                coros = [limited_coro(coro) for coro in coros]
            
            results = await asyncio.gather(*coros, return_exceptions=True)
            
            # 检查是否有异常
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"❌ 并行执行第 {i} 个协程失败: {result}")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ 并行执行失败: {e}")
            raise
    
    async def run_with_timeout(self, coro: Coroutine, timeout: float) -> Any:
        """带超时的异步执行"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            logger.error(f"❌ 执行超时 ({timeout}秒)")
            raise
        except Exception as e:
            logger.error(f"❌ 执行失败: {e}")
            raise
    
    def get_utils_status(self) -> Dict[str, Any]:
        """获取工具类状态"""
        return {
            "initialized": self.initialized,
            "active_tasks": len(self.active_tasks),
            "total_tasks": len(self.task_info),
            "completed_tasks": sum(1 for t in self.task_info.values() 
                                 if t.status == TaskStatus.COMPLETED),
            "failed_tasks": sum(1 for t in self.task_info.values() 
                              if t.status == TaskStatus.FAILED),
            "cancelled_tasks": sum(1 for t in self.task_info.values() 
                                 if t.status == TaskStatus.CANCELLED),
            "timestamp": time.time()
        }
    
    async def shutdown(self) -> None:
        """关闭工具类"""
        try:
            logger.info("🔄 关闭异步工具类...")
            
            # 取消所有活跃任务
            for task_id, task in self.active_tasks.items():
                try:
                    task.cancel()
                    logger.info(f"✅ 任务 {task_id} 已取消")
                except Exception as e:
                    logger.error(f"❌ 任务 {task_id} 取消失败: {e}")
            
            # 等待所有任务完成
            if self.active_tasks:
                await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
            
            self.active_tasks.clear()
            self.task_info.clear()
            
            logger.info("✅ 异步工具类关闭完成")
            
        except Exception as e:
            logger.error(f"❌ 关闭异步工具类失败: {e}")


# 便捷函数
def get_async_utils() -> AsyncUtils:
    """获取异步工具类实例"""
    return AsyncUtils()


# 装饰器
def async_retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """异步重试装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            utils = get_async_utils()
            return await utils.run_with_retry(
                func(*args, **kwargs), 
                max_retries, 
                delay, 
                backoff
            )
        return wrapper
    return decorator


def async_timeout(timeout: float):
    """异步超时装饰器"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            utils = get_async_utils()
            return await utils.run_with_timeout(
                func(*args, **kwargs), 
                timeout
            )
        return wrapper
    return decorator
