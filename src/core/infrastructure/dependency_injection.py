"""
依赖注入容器
用于降低模块间耦合度，提高系统的可测试性和可维护性
"""

import logging
from typing import Dict, Any, Type, Callable, Optional, Union
from abc import ABC, abstractmethod


class ServiceLifetime:
    """服务生命周期枚举"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class ServiceDescriptor:
    """服务描述符"""
    
    def __init__(self, 
                 service_type: Type,
                 implementation: Union[Type, Callable],
                 lifetime: str = ServiceLifetime.TRANSIENT,
                 factory: Optional[Callable] = None):
        self.service_type = service_type
        self.implementation = implementation
        self.lifetime = lifetime
        self.factory = factory


class DependencyContainer:
    """依赖注入容器"""
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_singleton(self, service_type: Type, implementation: Union[Type, Callable]) -> 'DependencyContainer':
        """注册单例服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type, implementation, ServiceLifetime.SINGLETON
        )
        return self
    
    def register_transient(self, service_type: Type, implementation: Union[Type, Callable]) -> 'DependencyContainer':
        """注册瞬态服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type, implementation, ServiceLifetime.TRANSIENT
        )
        return self
    
    def register_scoped(self, service_type: Type, implementation: Union[Type, Callable]) -> 'DependencyContainer':
        """注册作用域服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type, implementation, ServiceLifetime.SCOPED
        )
        return self
    
    def register_factory(self, service_type: Type, factory: Callable, lifetime: str = ServiceLifetime.TRANSIENT) -> 'DependencyContainer':
        """注册工厂服务"""
        self._services[service_type] = ServiceDescriptor(
            service_type, factory, lifetime, factory
        )
        return self
    
    def get_service(self, service_type: Type) -> Any:
        """获取服务实例"""
        if service_type not in self._services:
            raise ValueError(f"Service {service_type} not registered")
        
        descriptor = self._services[service_type]
        
        # 单例模式
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type not in self._singletons:
                self._singletons[service_type] = self._create_instance(descriptor)
            return self._singletons[service_type]
        
        # 作用域模式
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if service_type not in self._scoped_instances:
                self._scoped_instances[service_type] = self._create_instance(descriptor)
            return self._scoped_instances[service_type]
        
        # 瞬态模式
        else:
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """创建服务实例"""
        try:
            if descriptor.factory:
                return descriptor.factory()
            elif callable(descriptor.implementation):
                return descriptor.implementation()
            else:
                return descriptor.implementation()
        except Exception as e:
            self.logger.error(f"Failed to create instance of {descriptor.service_type}: {e}")
            raise
    
    def clear_scoped_instances(self):
        """清除作用域实例"""
        self._scoped_instances.clear()
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        return service_type in self._services
    
    def get_registered_services(self) -> Dict[Type, ServiceDescriptor]:
        """获取所有已注册的服务"""
        return self._services.copy()


# 全局容器实例
_container: Optional[DependencyContainer] = None


def get_container() -> DependencyContainer:
    """获取全局容器实例"""
    global _container
    if _container is None:
        _container = DependencyContainer()
    return _container


def register_services(container: DependencyContainer) -> None:
    """注册核心服务"""
    # 注册配置服务
    try:
        from ..utils.unified_centers import get_unified_center
        config_center = get_unified_center('get_unified_config_center')
        if config_center:
            container.register_singleton(type(config_center), lambda: config_center)
    except ImportError:
        pass
    
    # 注册日志服务
    container.register_singleton(logging.Logger, lambda: logging.getLogger("RANGEN"))
    
    # 注册其他核心服务
    # 这里可以继续添加其他服务的注册


class ServiceProvider:
    """服务提供者基类"""
    
    def __init__(self, container: DependencyContainer):
        self.container = container
    
    @abstractmethod
    def configure_services(self) -> None:
        """配置服务"""
        pass


class DefaultServiceProvider(ServiceProvider):
    """默认服务提供者"""
    
    def configure_services(self) -> None:
        """配置默认服务"""
        # 配置基础服务
        register_services(self.container)
        
        # 配置业务服务
        self._configure_business_services()
        
        # 配置AI服务
        self._configure_ai_services()
    
    def _configure_business_services(self) -> None:
        """配置业务服务"""
        # 这里可以注册业务相关的服务
        pass
    
    def _configure_ai_services(self) -> None:
        """配置AI服务"""
        # 这里可以注册AI相关的服务
        pass


def create_service_provider() -> ServiceProvider:
    """创建服务提供者"""
    container = get_container()
    provider = DefaultServiceProvider(container)
    provider.configure_services()
    return provider
