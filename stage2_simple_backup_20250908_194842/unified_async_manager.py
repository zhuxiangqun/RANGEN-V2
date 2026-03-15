"""
统一异步管理器
整合所有异步管理功能，提供智能、动态、可扩展的异步管理
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable, Coroutine
from datetime import datetime
import threading
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AsyncComponentManager:
    """异步组件管理器 - 整合组件管理功能"""

    def __init__(self):
        self.components: Dict[str, Any] = {}
        self.component_states: Dict[str, str] = {}
        self.lock = threading.RLock()

    async def register_component(self, name: str, component: Any) -> bool:
        """注册组件"""
        with self.lock:
            self.components[name] = component
            self.component_states[name] = 'registered'
            logger.info(f"组件注册成功: {name}")
            return True

    async def unregister_component(self, name: str) -> bool:
        """注销组件"""
        with self.lock:
            if name in self.components:
                del self.components[name]
                del self.component_states[name]
                logger.info(f"组件注销成功: {name}")
                return True
            return False

    async def get_component(self, name: str) -> Optional[Any]:
        """获取组件"""
        return self.components.get(name)

    async def get_component_state(self, name: str) -> str:
        """获取组件状态"""
        return self.component_states.get(name, 'unknown')

class AsyncAgentManager:
    """异步智能体管理器"""

    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        self.lock = threading.RLock()

    async def register_agent(self, name: str, agent: Any) -> bool:
        """注册智能体"""
        with self.lock:
            self.agents[name] = agent
            logger.info(f"智能体注册成功: {name}")
            return True

    async def unregister_agent(self, name: str) -> bool:
        """注销智能体"""
        with self.lock:
            if name in self.agents:
                del self.agents[name]
                if name in self.agent_tasks:
                    self.agent_tasks[name].cancel()
                    del self.agent_tasks[name]
                logger.info(f"智能体注销成功: {name}")
                return True
            return False

    async def execute_agent(self, name: str, *args, **kwargs) -> Any:
        """执行智能体"""
        agent = self.agents.get(name)
        if not agent:
            raise ValueError(f"智能体不存在: {name}")

        if hasattr(agent, 'execute'):
            return await agent.execute(*args, **kwargs)
        elif hasattr(agent, 'run'):
            return await agent.run(*args, **kwargs)
        else:
            raise AttributeError(f"智能体 {name} 没有可用的执行方法")

class AsyncTaskManager:
    """异步任务管理器"""

    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, Any] = {}
        self.lock = threading.RLock()

    async def submit_task(self, name: str, coro: Coroutine) -> str:
        """提交任务"""
        with self.lock:
            task = asyncio.create_task(coro)
            self.tasks[name] = task
            logger.info(f"任务提交成功: {name}")
            return name

    async def cancel_task(self, name: str) -> bool:
        """取消任务"""
        with self.lock:
            if name in self.tasks:
                self.tasks[name].cancel()
                del self.tasks[name]
                logger.info(f"任务取消成功: {name}")
                return True
            return False

    async def get_task_result(self, name: str) -> Optional[Any]:
        """获取任务结果"""
        if name in self.task_results:
            return self.task_results[name]
        return None

    async def wait_for_task(self, name: str, timeout: Optional[float] = None) -> Any:
        """等待任务完成"""
        if name not in self.tasks:
            raise ValueError(f"任务不存在: {name}")

        try:
            result = await asyncio.wait_for(self.tasks[name], timeout=timeout)
            self.task_results[name] = result
            return result
        except asyncio.TimeoutError:
            logger.warning(f"任务超时: {name}")
            raise

class AsyncResourceManager:
    """异步资源管理器"""

    def __init__(self):
        self.resources: Dict[str, Any] = {}
        self.resource_usage: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.RLock()

    async def allocate_resource(self, name: str, resource: Any) -> bool:
        """分配资源"""
        with self.lock:
            self.resources[name] = resource
            self.resource_usage[name] = {
                'allocated_at': datetime.now(),
                'usage_count': 0,
                'last_used': None
            }
            logger.info(f"资源分配成功: {name}")
            return True

    async def deallocate_resource(self, name: str) -> bool:
        """释放资源"""
        with self.lock:
            if name in self.resources:
                del self.resources[name]
                del self.resource_usage[name]
                logger.info(f"资源释放成功: {name}")
                return True
            return False

    async def get_resource(self, name: str) -> Optional[Any]:
        """获取资源"""
        resource = self.resources.get(name)
        if resource:
            with self.lock:
                self.resource_usage[name]['usage_count'] += 1
                self.resource_usage[name]['last_used'] = datetime.now()
        return resource

class UnifiedAsyncManager:
    """统一异步管理器 - 整合所有异步功能"""

    def __init__(self):
        self.component_manager = AsyncComponentManager()
        self.agent_manager = AsyncAgentManager()
        self.task_manager = AsyncTaskManager()
        self.resource_manager = AsyncResourceManager()

        self.performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_reset': datetime.now()
        }

        logger.info("✅ 统一异步管理器初始化完成")

    async def manage_component(self, operation: str, name: str, component: Any = None) -> bool:
        """统一组件管理"""
        try:
            if operation == 'register':
                return await self.component_manager.register_component(name, component)
            elif operation == 'unregister':
                return await self.component_manager.unregister_component(name)
            else:
                raise ValueError(f"未知的组件操作: {operation}")
        except Exception as e:
            logger.error(f"组件管理操作失败: {operation} {name}, 错误: {e}")
            self._record_operation_failure()
            return False
        finally:
            self._record_operation_success()

    async def manage_agent(self, operation: str, name: str, agent: Any = None, *args, **kwargs) -> Any:
        """统一智能体管理"""
        try:
            if operation == 'register':
                return await self.agent_manager.register_agent(name, agent)
            elif operation == 'unregister':
                return await self.agent_manager.unregister_agent(name)
            elif operation == 'execute':
                return await self.agent_manager.execute_agent(name, *args, **kwargs)
            else:
                raise ValueError(f"未知的智能体操作: {operation}")
        except Exception as e:
            logger.error(f"智能体管理操作失败: {operation} {name}, 错误: {e}")
            self._record_operation_failure()
            raise
        finally:
            self._record_operation_success()

    async def manage_task(self, operation: str, name: str, coro: Coroutine = None,
    timeout: Optional[float] = None) -> Any:
        """统一任务管理"""
        try:
            if operation == 'submit':
                return await self.task_manager.submit_task(name, coro)
            elif operation == 'cancel':
                return await self.task_manager.cancel_task(name)
            elif operation == 'wait':
                return await self.task_manager.wait_for_task(name, timeout)
            elif operation == 'get_result':
                return await self.task_manager.get_task_result(name)
            else:
                raise ValueError(f"未知的任务操作: {operation}")
        except Exception as e:
            logger.error(f"任务管理操作失败: {operation} {name}, 错误: {e}")
            self._record_operation_failure()
            raise
        finally:
            self._record_operation_success()

    async def manage_resource(self, operation: str, name: str, resource: Any = None) -> Any:
        """统一资源管理"""
        try:
            if operation == 'allocate':
                return await self.resource_manager.allocate_resource(name, resource)
            elif operation == 'deallocate':
                return await self.resource_manager.deallocate_resource(name)
            elif operation == 'get':
                return await self.resource_manager.get_resource(name)
            else:
                raise ValueError(f"未知的资源操作: {operation}")
        except Exception as e:
            logger.error(f"资源管理操作失败: {operation} {name}, 错误: {e}")
            self._record_operation_failure()
            return False
        finally:
            self._record_operation_success()

    def _record_operation_success(self):
        """记录操作成功"""
        self.performance_metrics['total_operations'] += 1
        self.performance_metrics['successful_operations'] += 1

    def _record_operation_failure(self):
        """记录操作失败"""
        self.performance_metrics['total_operations'] += 1
        self.performance_metrics['failed_operations'] += 1

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        total = self.performance_metrics['total_operations']
        successful = self.performance_metrics['successful_operations']
        failed = self.performance_metrics['failed_operations']

        success_rate = successful / total if total > 0 else 0

        return {
            'total_operations': total,
            'successful_operations': successful,
            'failed_operations': failed,
            'success_rate': success_rate,
            'last_reset': self.performance_metrics['last_reset'].isoformat()
        }

    def reset_performance_metrics(self):
        """重置性能指标"""
        self.performance_metrics = {
            'total_operations': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_reset': datetime.now()
        }
        logger.info("性能指标已重置")

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            'manager_version': '1.0.0',
            'component_count': len(self.component_manager.components),
            'agent_count': len(self.agent_manager.agents),
            'task_count': len(self.task_manager.tasks),
            'resource_count': len(self.resource_manager.resources),
            'performance_metrics': self.get_performance_metrics()
        }

_unified_async_manager = None

def get_unified_async_manager() -> UnifiedAsyncManager:
    """获取统一异步管理器实例"""
    global _unified_async_manager
    if _unified_async_manager is None:
        _unified_async_manager = UnifiedAsyncManager()
    return _unified_async_manager
