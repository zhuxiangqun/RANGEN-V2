#!/usr/bin/env python3
"""
异步依赖容器 - 提供异步依赖注入和生命周期管理
"""

import asyncio
import logging
import time
import weakref
from typing import Dict, List, Any, Optional, Union, Tuple, Type, Callable, TypeVar
from dataclasses import dataclass
from enum import Enum
import inspect

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ServiceLifetime(Enum):
    """服务生命周期枚举"""
    SINGLETON = "singleton"
    SCOPED = "scoped"
    TRANSIENT = "transient"


@dataclass
class ServiceRegistration:
    """服务注册信息"""
    service_type: Type
    implementation_type: Optional[Type] = None
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type] = None
    is_async: bool = False


class AsyncDependencyContainer:
    """异步依赖容器"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
        self._services: Dict[Type, ServiceRegistration] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._container_lock = asyncio.Lock()
        self._scope_id = 0
    
    def register_singleton(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None, 
                          factory: Optional[Callable] = None) -> None:
        """注册单例服务"""
        self._register_service(service_type, implementation_type, factory, ServiceLifetime.SINGLETON)
    
    def register_scoped(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None, 
                       factory: Optional[Callable] = None) -> None:
        """注册作用域服务"""
        self._register_service(service_type, implementation_type, factory, ServiceLifetime.SCOPED)
    
    def register_transient(self, service_type: Type[T], implementation_type: Optional[Type[T]] = None, 
                          factory: Optional[Callable] = None) -> None:
        """注册瞬态服务"""
        self._register_service(service_type, implementation_type, factory, ServiceLifetime.TRANSIENT)
    
    def _register_service(self, service_type: Type, implementation_type: Optional[Type], 
                         factory: Optional[Callable], lifetime: ServiceLifetime) -> None:
        """注册服务"""
        try:
            dependencies = self._get_dependencies(implementation_type or service_type)
            is_async = self._is_async_constructor(implementation_type or service_type)
            
            registration = ServiceRegistration(
                service_type=service_type,
                implementation_type=implementation_type,
                factory=factory,
                lifetime=lifetime,
                dependencies=dependencies,
                is_async=is_async
            )
            
            self._services[service_type] = registration
            logger.info(f"✅ 服务 {service_type.__name__} 注册成功 ({lifetime.value})")
            
        except Exception as e:
            logger.error(f"❌ 服务 {service_type.__name__} 注册失败: {e}")
            raise
    
    def _get_dependencies(self, service_type: Type) -> List[Type]:
        """获取服务依赖"""
        try:
            if not service_type:
                return []
            
            # 获取构造函数参数
            sig = inspect.signature(service_type.__init__)
            dependencies = []
            
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)
            
            return dependencies
            
        except Exception as e:
            logger.warning(f"获取依赖失败: {e}")
            return []
    
    def _is_async_constructor(self, service_type: Type) -> bool:
        """检查构造函数是否为异步"""
        try:
            if not service_type:
                return False
            
            # 检查是否有异步构造函数
            if hasattr(service_type, '__ainit__'):
                return True
            
            # 检查是否有异步工厂方法
            if hasattr(service_type, 'create_async'):
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"检查异步构造函数失败: {e}")
            return False
    
    async def get_service(self, service_type: Type[T]) -> T:
        """获取服务实例"""
        async with self._container_lock:
            if service_type not in self._services:
                raise ValueError(f"服务 {service_type.__name__} 未注册")
            
            registration = self._services[service_type]
            
            # 根据生命周期返回实例
            if registration.lifetime == ServiceLifetime.SINGLETON:
                return await self._get_singleton_instance(service_type, registration)
            elif registration.lifetime == ServiceLifetime.SCOPED:
                return await self._get_scoped_instance(service_type, registration)
            else:  # TRANSIENT
                return await self._create_instance(service_type, registration)
    
    async def _get_singleton_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """获取单例实例"""
        if service_type in self._singleton_instances:
            return self._singleton_instances[service_type]
        
        instance = await self._create_instance(service_type, registration)
        self._singleton_instances[service_type] = instance
        return instance
    
    async def _get_scoped_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """获取作用域实例"""
        if service_type in self._scoped_instances:
            return self._scoped_instances[service_type]
        
        instance = await self._create_instance(service_type, registration)
        self._scoped_instances[service_type] = instance
        return instance
    
    async def _create_instance(self, service_type: Type, registration: ServiceRegistration) -> Any:
        """创建服务实例"""
        try:
            # 解析依赖
            dependencies = await self._resolve_dependencies(registration.dependencies)
            
            # 创建实例
            if registration.factory:
                if registration.is_async:
                    instance = await registration.factory(*dependencies)
                else:
                    instance = registration.factory(*dependencies)
            elif registration.implementation_type:
                if registration.is_async:
                    instance = await registration.implementation_type(*dependencies)
                else:
                    instance = registration.implementation_type(*dependencies)
            else:
                if registration.is_async:
                    instance = await service_type(*dependencies)
                else:
                    instance = service_type(*dependencies)
            
            # 如果实例有异步初始化方法，调用它
            if hasattr(instance, 'initialize') and asyncio.iscoroutinefunction(instance.initialize):
                await instance.initialize()
            
            logger.info(f"✅ 服务 {service_type.__name__} 实例创建成功")
            return instance
            
        except Exception as e:
            logger.error(f"❌ 服务 {service_type.__name__} 实例创建失败: {e}")
            raise
    
    async def _resolve_dependencies(self, dependencies: List[Type]) -> List[Any]:
        """解析依赖"""
        resolved_deps = []
        
        for dep_type in dependencies:
            try:
                dep_instance = await self.get_service(dep_type)
                resolved_deps.append(dep_instance)
            except Exception as e:
                logger.error(f"❌ 依赖 {dep_type.__name__} 解析失败: {e}")
                raise
        
        return resolved_deps
    
    async def create_scope(self) -> 'AsyncDependencyScope':
        """创建作用域"""
        self._scope_id += 1
        return AsyncDependencyScope(self, self._scope_id)
    
    async def dispose_singletons(self) -> None:
        """释放单例实例"""
        try:
            for service_type, instance in self._singleton_instances.items():
                if hasattr(instance, 'dispose') and asyncio.iscoroutinefunction(instance.dispose):
                    await instance.dispose()
                elif hasattr(instance, 'cleanup') and asyncio.iscoroutinefunction(instance.cleanup):
                    await instance.cleanup()
            
            self._singleton_instances.clear()
            logger.info("✅ 单例实例释放完成")
            
        except Exception as e:
            logger.error(f"❌ 释放单例实例失败: {e}")
    
    async def dispose_scoped(self) -> None:
        """释放作用域实例"""
        try:
            for service_type, instance in self._scoped_instances.items():
                if hasattr(instance, 'dispose') and asyncio.iscoroutinefunction(instance.dispose):
                    await instance.dispose()
                elif hasattr(instance, 'cleanup') and asyncio.iscoroutinefunction(instance.cleanup):
                    await instance.cleanup()
            
            self._scoped_instances.clear()
            logger.info("✅ 作用域实例释放完成")
            
        except Exception as e:
            logger.error(f"❌ 释放作用域实例失败: {e}")
    
    def get_registered_services(self) -> Dict[str, Dict[str, Any]]:
        """获取已注册的服务"""
        result = {}
        for service_type, registration in self._services.items():
            result[service_type.__name__] = {
                "service_type": service_type.__name__,
                "implementation_type": registration.implementation_type.__name__ if registration.implementation_type else None,
                "lifetime": registration.lifetime.value,
                "dependencies": [dep.__name__ for dep in registration.dependencies] if registration.dependencies else [],
                "is_async": registration.is_async,
                "has_factory": registration.factory is not None
            }
        return result
    
    def get_container_status(self) -> Dict[str, Any]:
        """获取容器状态"""
        return {
            "initialized": self.initialized,
            "registered_services": len(self._services),
            "singleton_instances": len(self._singleton_instances),
            "scoped_instances": len(self._scoped_instances),
            "current_scope_id": self._scope_id,
            "timestamp": time.time()
        }
    
    async def shutdown(self) -> None:
        """关闭容器"""
        try:
            logger.info("🔄 关闭异步依赖容器...")
            
            await self.dispose_scoped()
            await self.dispose_singletons()
            
            self._services.clear()
            self._scope_id = 0
            
            logger.info("✅ 异步依赖容器关闭完成")
            
        except Exception as e:
            logger.error(f"❌ 关闭异步依赖容器失败: {e}")


class AsyncDependencyScope:
    """异步依赖作用域"""
    
    def __init__(self, container: AsyncDependencyContainer, scope_id: int):
        self.container = container
        self.scope_id = scope_id
        self.scoped_instances: Dict[Type, Any] = {}
        self._disposed = False
    
    async def get_service(self, service_type: Type[T]) -> T:
        """获取作用域内的服务实例"""
        if self._disposed:
            raise RuntimeError("作用域已释放")
        
        if service_type in self.scoped_instances:
            return self.scoped_instances[service_type]
        
        # 从容器获取服务
        instance = await self.container.get_service(service_type)
        
        # 如果是作用域服务，缓存到当前作用域
        if service_type in self.container._services:
            registration = self.container._services[service_type]
            if registration.lifetime == ServiceLifetime.SCOPED:
                self.scoped_instances[service_type] = instance
        
        return instance
    
    async def dispose(self) -> None:
        """释放作用域"""
        if self._disposed:
            return
        
        try:
            for service_type, instance in self.scoped_instances.items():
                if hasattr(instance, 'dispose') and asyncio.iscoroutinefunction(instance.dispose):
                    await instance.dispose()
                elif hasattr(instance, 'cleanup') and asyncio.iscoroutinefunction(instance.cleanup):
                    await instance.cleanup()
            
            self.scoped_instances.clear()
            self._disposed = True
            
            logger.info(f"✅ 作用域 {self.scope_id} 释放完成")
            
        except Exception as e:
            logger.error(f"❌ 释放作用域 {self.scope_id} 失败: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.create_task(self.dispose())


# 便捷函数
def get_async_dependency_container() -> AsyncDependencyContainer:
    """获取异步依赖容器实例"""
    return AsyncDependencyContainer()


# 装饰器
def injectable(lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
    """可注入装饰器"""
    def decorator(cls):
        cls._injectable_lifetime = lifetime
        return cls
    return decorator


def singleton(cls):
    """单例装饰器"""
    return injectable(ServiceLifetime.SINGLETON)(cls)


def scoped(cls):
    """作用域装饰器"""
    return injectable(ServiceLifetime.SCOPED)(cls)


def transient(cls):
    """瞬态装饰器"""
    return injectable(ServiceLifetime.TRANSIENT)(cls)
