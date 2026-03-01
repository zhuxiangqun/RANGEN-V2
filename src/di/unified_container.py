#!/usr/bin/env python3
"""
统一依赖注入容器
整合现有依赖注入系统，提供统一的异步和同步支持
"""

import asyncio
import logging
import threading
from typing import Dict, Any, Type, Callable, Optional, Union, List, TypeVar
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod
import inspect

T = TypeVar('T')

logger = logging.getLogger(__name__)


class ServiceLifetime(Enum):
    """服务生命周期"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """服务描述符"""
    service_type: Type
    implementation: Union[Type, Callable, Any]
    lifetime: ServiceLifetime
    factory: Optional[Callable] = None
    dependencies: List[Type] = None
    is_async: bool = False
    instance: Optional[Any] = None


class IDependencyContainer(ABC):
    """依赖注入容器接口"""
    
    @abstractmethod
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], Callable, Any]) -> 'IDependencyContainer':
        """注册单例服务"""
        pass
    
    @abstractmethod
    def register_transient(self, service_type: Type[T], implementation: Union[Type[T], Callable, Any]) -> 'IDependencyContainer':
        """注册瞬态服务"""
        pass
    
    @abstractmethod
    def register_scoped(self, service_type: Type[T], implementation: Union[Type[T], Callable, Any]) -> 'IDependencyContainer':
        """注册作用域服务"""
        pass
    
    @abstractmethod
    def register_factory(self, service_type: Type[T], factory: Callable, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'IDependencyContainer':
        """注册工厂服务"""
        pass
    
    @abstractmethod
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例（同步）"""
        pass
    
    @abstractmethod
    async def get_service_async(self, service_type: Type[T]) -> T:
        """获取服务实例（异步）"""
        pass
    
    @abstractmethod
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass
    
    @abstractmethod
    def clear_scoped_instances(self) -> None:
        """清除作用域实例"""
        pass


class UnifiedDIContainer(IDependencyContainer):
    """统一依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._container_lock = threading.RLock()
        self._async_lock = asyncio.Lock()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_singleton(self, service_type: Type[T], implementation: Union[Type[T], Callable, Any]) -> 'UnifiedDIContainer':
        """注册单例服务"""
        with self._container_lock:
            dependencies = self._get_dependencies(implementation)
            is_async = self._is_async_constructor(implementation)
            
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.SINGLETON,
                dependencies=dependencies,
                is_async=is_async
            )
            self.logger.info(f"注册单例服务: {service_type.__name__}")
        return self
    
    def register_transient(self, service_type: Type[T], implementation: Union[Type[T], Callable, Any]) -> 'UnifiedDIContainer':
        """注册瞬态服务"""
        with self._container_lock:
            dependencies = self._get_dependencies(implementation)
            is_async = self._is_async_constructor(implementation)
            
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.TRANSIENT,
                dependencies=dependencies,
                is_async=is_async
            )
            self.logger.info(f"注册瞬态服务: {service_type.__name__}")
        return self
    
    def register_scoped(self, service_type: Type[T], implementation: Union[Type[T], Callable, Any]) -> 'UnifiedDIContainer':
        """注册作用域服务"""
        with self._container_lock:
            dependencies = self._get_dependencies(implementation)
            is_async = self._is_async_constructor(implementation)
            
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.SCOPED,
                dependencies=dependencies,
                is_async=is_async
            )
            self.logger.info(f"注册作用域服务: {service_type.__name__}")
        return self
    
    def register_factory(self, service_type: Type[T], factory: Callable, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'UnifiedDIContainer':
        """注册工厂服务"""
        with self._container_lock:
            is_async = asyncio.iscoroutinefunction(factory)
            
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=factory,
                lifetime=lifetime,
                factory=factory,
                dependencies=[],
                is_async=is_async
            )
            self.logger.info(f"注册工厂服务: {service_type.__name__} (生命周期: {lifetime.value})")
        return self
    
    def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例（同步）"""
        if service_type not in self._services:
            raise ValueError(f"服务未注册: {service_type.__name__}")
        
        descriptor = self._services[service_type]
        
        # 单例模式
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type not in self._singleton_instances:
                self._singleton_instances[service_type] = self._create_instance(descriptor)
            return self._singleton_instances[service_type]
        
        # 作用域模式
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type not in self._scoped_instances:
                self._scoped_instances[service_type] = self._create_instance(descriptor)
            return self._scoped_instances[service_type]
        
        # 瞬态模式
        else:
            return self._create_instance(descriptor)
    
    async def get_service_async(self, service_type: Type[T]) -> T:
        """获取服务实例（异步）"""
        if service_type not in self._services:
            raise ValueError(f"服务未注册: {service_type.__name__}")
        
        descriptor = self._services[service_type]
        
        # 单例模式
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            async with self._async_lock:
                if service_type not in self._singleton_instances:
                    self._singleton_instances[service_type] = await self._create_instance_async(descriptor)
                return self._singleton_instances[service_type]
        
        # 作用域模式
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            async with self._async_lock:
                if service_type not in self._scoped_instances:
                    self._scoped_instances[service_type] = await self._create_instance_async(descriptor)
                return self._scoped_instances[service_type]
        
        # 瞬态模式
        else:
            return await self._create_instance_async(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例（同步）"""
        try:
            # 如果有工厂函数，使用工厂
            if descriptor.factory:
                return descriptor.factory()
            
            # 如果是可调用对象，调用它
            elif callable(descriptor.implementation):
                # 检查是否需要依赖注入
                if descriptor.dependencies:
                    dependencies = [self.get_service(dep) for dep in descriptor.dependencies]
                    return descriptor.implementation(*dependencies)
                else:
                    return descriptor.implementation()
            
            # 否则直接返回实例
            else:
                return descriptor.implementation
                
        except Exception as e:
            self.logger.error(f"创建实例失败 {descriptor.service_type.__name__}: {e}")
            raise
    
    async def _create_instance_async(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例（异步）"""
        try:
            # 如果有工厂函数，使用工厂
            if descriptor.factory:
                if descriptor.is_async:
                    return await descriptor.factory()
                else:
                    return descriptor.factory()
            
            # 如果是可调用对象，调用它
            elif callable(descriptor.implementation):
                # 检查是否需要依赖注入
                if descriptor.dependencies:
                    dependencies = []
                    for dep in descriptor.dependencies:
                        if asyncio.iscoroutinefunction(self.get_service):
                            dependencies.append(await self.get_service(dep))
                        else:
                            dependencies.append(self.get_service(dep))
                    
                    if descriptor.is_async:
                        return await descriptor.implementation(*dependencies)
                    else:
                        return descriptor.implementation(*dependencies)
                else:
                    if descriptor.is_async:
                        return await descriptor.implementation()
                    else:
                        return descriptor.implementation()
            
            # 否则直接返回实例
            else:
                return descriptor.implementation
                
        except Exception as e:
            self.logger.error(f"创建异步实例失败 {descriptor.service_type.__name__}: {e}")
            raise
    
    def _get_dependencies(self, implementation: Union[Type, Callable, Any]) -> List[Type]:
        """获取依赖项"""
        dependencies = []
        
        try:
            if isinstance(implementation, type):
                # 检查 __init__ 方法的参数
                init_method = implementation.__init__
                params = inspect.signature(init_method).parameters
                
                for param_name, param in params.items():
                    if param_name == 'self':
                        continue
                    if param.annotation != inspect.Parameter.empty:
                        dependencies.append(param.annotation)
            
            elif callable(implementation):
                # 检查函数的参数
                params = inspect.signature(implementation).parameters
                
                for param_name, param in params.items():
                    if param.annotation != inspect.Parameter.empty:
                        dependencies.append(param.annotation)
        
        except Exception as e:
            self.logger.debug(f"获取依赖项失败: {e}")
        
        return dependencies
    
    def _is_async_constructor(self, implementation: Union[Type, Callable, Any]) -> bool:
        """检查是否为异步构造函数"""
        try:
            if isinstance(implementation, type):
                init_method = implementation.__init__
                return asyncio.iscoroutinefunction(init_method)
            elif callable(implementation):
                return asyncio.iscoroutinefunction(implementation)
            else:
                return False
        except Exception:
            return False
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services
    
    def clear_scoped_instances(self) -> None:
        """清除作用域实例"""
        with self._container_lock:
            self._scoped_instances.clear()
            self.logger.info("作用域实例已清除")
    
    def get_registered_services(self) -> Dict[Type, ServiceDescriptor]:
        """获取所有已注册的服务"""
        return self._services.copy()


# 全局容器实例
_global_container: Optional[UnifiedDIContainer] = None


def get_container() -> UnifiedDIContainer:
    """获取全局容器实例"""
    global _global_container
    if _global_container is None:
        _global_container = UnifiedDIContainer()
    return _global_container


def reset_container() -> None:
    """重置全局容器（主要用于测试）"""
    global _global_container
    _global_container = None