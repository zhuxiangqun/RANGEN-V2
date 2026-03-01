#!/usr/bin/env python3
"""
异步接口模块 - 定义异步编程的通用接口和抽象基类
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple, Callable, Coroutine, Protocol
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AsyncStatus(Enum):
    """异步状态枚举"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AsyncResult:
    """异步结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    timestamp: float = 0.0
    execution_time: float = 0.0


# Agent Interface
class IAsyncAgent(Protocol):
    """异步智能体接口"""
    
    async def process_async(self, query: str, context: Optional[Dict[str, Any]] = None) -> AsyncResult:
        """异步处理查询"""
        ...
    
    def get_agent_id(self) -> str:
        """获取智能体ID"""
        ...
    
    async def is_enabled_async(self) -> bool:
        """异步检查是否启用"""
        ...


# Service Interface  
class IAsyncService(Protocol):
    """异步服务接口"""
    
    async def initialize(self) -> None:
        """初始化服务"""
        ...
    
    async def process_async(self, data: Any) -> AsyncResult:
        """异步处理数据"""
        ...
    
    async def cleanup(self) -> None:
        """清理资源"""
        ...


class AsyncProcessor(Protocol):
    """异步处理器协议"""
    
    async def process(self, data: Any) -> AsyncResult:
        """处理数据"""
        ...


class AsyncValidator(Protocol):
    """异步验证器协议"""
    
    async def validate(self, data: Any) -> bool:
        """验证数据"""
        ...


class AsyncHandler(Protocol):
    """异步处理器协议"""
    
    async def handle(self, event: Any) -> None:
        """处理事件"""
        ...


class AsyncService(ABC):
    """异步服务基类"""
    
    def __init__(self, name: str = "AsyncService"):
        self.name = name
        self.status = AsyncStatus.IDLE
        self.created_at = time.time()
        self.last_activity = time.time()
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化服务"""
        pass
    
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """处理数据"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass
    
    async def start(self) -> None:
        """启动服务"""
        try:
            self.status = AsyncStatus.RUNNING
            await self.initialize()
            logger.info(f"✅ 服务 {self.name} 启动成功")
        except Exception as e:
            self.status = AsyncStatus.FAILED
            logger.error(f"❌ 服务 {self.name} 启动失败: {e}")
            raise
    
    async def stop(self) -> None:
        """停止服务"""
        try:
            self.status = AsyncStatus.IDLE
            await self.cleanup()
            logger.info(f"✅ 服务 {self.name} 停止成功")
        except Exception as e:
            logger.error(f"❌ 服务 {self.name} 停止失败: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "uptime": time.time() - self.created_at
        }


class AsyncWorker(ABC):
    """异步工作者基类"""
    
    def __init__(self, worker_id: str, max_concurrent: int = 1):
        self.worker_id = worker_id
        self.max_concurrent = max_concurrent
        self.current_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.status = AsyncStatus.IDLE
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    @abstractmethod
    async def work(self, task: Any) -> Any:
        """执行工作任务"""
        pass
    
    async def execute_task(self, task: Any) -> AsyncResult:
        """执行任务"""
        async with self._semaphore:
            self.current_tasks += 1
            self.status = AsyncStatus.RUNNING
            start_time = time.time()
            
            try:
                result = await self.work(task)
                execution_time = time.time() - start_time
                self.completed_tasks += 1
                self.status = AsyncStatus.COMPLETED
                
                return AsyncResult(
                    success=True,
                    data=result,
                    timestamp=time.time(),
                    execution_time=execution_time
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                self.failed_tasks += 1
                self.status = AsyncStatus.FAILED
                
                return AsyncResult(
                    success=False,
                    error=str(e),
                    timestamp=time.time(),
                    execution_time=execution_time
                )
            
            finally:
                self.current_tasks -= 1
                if self.current_tasks == 0:
                    self.status = AsyncStatus.IDLE
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """获取工作者统计信息"""
        return {
            "worker_id": self.worker_id,
            "status": self.status.value,
            "current_tasks": self.current_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "max_concurrent": self.max_concurrent,
            "success_rate": self.completed_tasks / max(1, self.completed_tasks + self.failed_tasks)
        }


class AsyncManager(ABC):
    """异步管理器基类"""
    
    def __init__(self, name: str = "AsyncManager"):
        self.name = name
        self.workers: Dict[str, AsyncWorker] = {}
        self.services: Dict[str, AsyncService] = {}
        self.status = AsyncStatus.IDLE
        self._shutdown_event = asyncio.Event()
    
    @abstractmethod
    async def initialize(self) -> None:
        """初始化管理器"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """关闭管理器"""
        pass
    
    async def add_worker(self, worker: AsyncWorker) -> None:
        """添加工作者"""
        self.workers[worker.worker_id] = worker
        logger.info(f"✅ 工作者 {worker.worker_id} 添加成功")
    
    async def remove_worker(self, worker_id: str) -> None:
        """移除工作者"""
        if worker_id in self.workers:
            del self.workers[worker_id]
            logger.info(f"✅ 工作者 {worker_id} 移除成功")
    
    async def add_service(self, service: AsyncService) -> None:
        """添加服务"""
        self.services[service.name] = service
        await service.start()
        logger.info(f"✅ 服务 {service.name} 添加成功")
    
    async def remove_service(self, service_name: str) -> None:
        """移除服务"""
        if service_name in self.services:
            service = self.services[service_name]
            await service.stop()
            del self.services[service_name]
            logger.info(f"✅ 服务 {service_name} 移除成功")
    
    async def execute_task(self, worker_id: str, task: Any) -> AsyncResult:
        """执行任务"""
        if worker_id not in self.workers:
            raise ValueError(f"工作者 {worker_id} 不存在")
        
        worker = self.workers[worker_id]
        return await worker.execute_task(task)
    
    async def execute_task_any(self, task: Any) -> AsyncResult:
        """使用任意可用工作者执行任务"""
        if not self.workers:
            raise RuntimeError("没有可用的工作者")
        
        # 选择负载最轻的工作者
        available_workers = [w for w in self.workers.values() if w.current_tasks < w.max_concurrent]
        if not available_workers:
            raise RuntimeError("所有工作者都忙碌")
        
        worker = min(available_workers, key=lambda w: w.current_tasks)
        return await worker.execute_task(task)
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        return {
            "name": self.name,
            "status": self.status.value,
            "workers_count": len(self.workers),
            "services_count": len(self.services),
            "workers_stats": {w_id: w.get_worker_stats() for w_id, w in self.workers.items()},
            "services_status": {s_name: s.get_status() for s_name, s in self.services.items()}
        }


class AsyncInterfaces:
    """异步接口管理类"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
        self.managers: Dict[str, AsyncManager] = {}
        self.workers: Dict[str, AsyncWorker] = {}
        self.services: Dict[str, AsyncService] = {}
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        return data is not None
    
    async def register_manager(self, manager: AsyncManager) -> None:
        """注册管理器"""
        self.managers[manager.name] = manager
        await manager.initialize()
        logger.info(f"✅ 管理器 {manager.name} 注册成功")
    
    async def unregister_manager(self, manager_name: str) -> None:
        """注销管理器"""
        if manager_name in self.managers:
            manager = self.managers[manager_name]
            await manager.shutdown()
            del self.managers[manager_name]
            logger.info(f"✅ 管理器 {manager_name} 注销成功")
    
    async def register_worker(self, worker: AsyncWorker) -> None:
        """注册工作者"""
        self.workers[worker.worker_id] = worker
        logger.info(f"✅ 工作者 {worker.worker_id} 注册成功")
    
    async def unregister_worker(self, worker_id: str) -> None:
        """注销工作者"""
        if worker_id in self.workers:
            del self.workers[worker_id]
            logger.info(f"✅ 工作者 {worker_id} 注销成功")
    
    async def register_service(self, service: AsyncService) -> None:
        """注册服务"""
        self.services[service.name] = service
        await service.start()
        logger.info(f"✅ 服务 {service.name} 注册成功")
    
    async def unregister_service(self, service_name: str) -> None:
        """注销服务"""
        if service_name in self.services:
            service = self.services[service_name]
            await service.stop()
            del self.services[service_name]
            logger.info(f"✅ 服务 {service_name} 注销成功")
    
    async def execute_task(self, worker_id: str, task: Any) -> AsyncResult:
        """执行任务"""
        if worker_id not in self.workers:
            raise ValueError(f"工作者 {worker_id} 不存在")
        
        worker = self.workers[worker_id]
        return await worker.execute_task(task)
    
    async def execute_task_any(self, task: Any) -> AsyncResult:
        """使用任意可用工作者执行任务"""
        if not self.workers:
            raise RuntimeError("没有可用的工作者")
        
        available_workers = [w for w in self.workers.values() if w.current_tasks < w.max_concurrent]
        if not available_workers:
            raise RuntimeError("所有工作者都忙碌")
        
        worker = min(available_workers, key=lambda w: w.current_tasks)
        return await worker.execute_task(task)
    
    def get_interfaces_status(self) -> Dict[str, Any]:
        """获取接口状态"""
        return {
            "initialized": self.initialized,
            "managers_count": len(self.managers),
            "workers_count": len(self.workers),
            "services_count": len(self.services),
            "managers_status": {name: mgr.get_manager_status() for name, mgr in self.managers.items()},
            "workers_stats": {w_id: w.get_worker_stats() for w_id, w in self.workers.items()},
            "services_status": {s_name: s.get_status() for s_name, s in self.services.items()},
            "timestamp": time.time()
        }
    
    async def shutdown_all(self) -> None:
        """关闭所有组件"""
        try:
            logger.info("🔄 关闭所有异步接口组件...")
            
            # 关闭所有服务
            for service in self.services.values():
                try:
                    await service.stop()
                except Exception as e:
                    logger.error(f"❌ 关闭服务 {service.name} 失败: {e}")
            
            # 关闭所有管理器
            for manager in self.managers.values():
                try:
                    await manager.shutdown()
                except Exception as e:
                    logger.error(f"❌ 关闭管理器 {manager.name} 失败: {e}")
            
            self.managers.clear()
            self.workers.clear()
            self.services.clear()
            
            logger.info("✅ 所有异步接口组件关闭完成")
            
        except Exception as e:
            logger.error(f"❌ 关闭异步接口组件失败: {e}")


# 便捷函数
def get_async_interfaces() -> AsyncInterfaces:
    """获取异步接口实例"""
    return AsyncInterfaces()


# 装饰器
def async_service(name: str = None):
    """异步服务装饰器"""
    def decorator(cls):
        service_name = name or cls.__name__
        cls._service_name = service_name
        return cls
    return decorator


def async_worker(worker_id: str = None, max_concurrent: int = 1):
    """异步工作者装饰器"""
    def decorator(cls):
        worker_id_name = worker_id or cls.__name__
        cls._worker_id = worker_id_name
        cls._max_concurrent = max_concurrent
        return cls
    return decorator


def async_manager(name: str = None):
    """异步管理器装饰器"""
    def decorator(cls):
        manager_name = name or cls.__name__
        cls._manager_name = manager_name
        return cls
    return decorator
