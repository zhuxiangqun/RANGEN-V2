"""
服务注册中心
提供服务的注册、发现和管理功能，进一步降低系统耦合度
"""

import logging
import threading
from typing import Dict, Any, Type, Optional, Callable, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum


class ServiceLifetime(Enum):
    """服务生命周期"""
    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


@dataclass
class ServiceDescriptor:
    """服务描述符"""
    service_type: Type
    implementation: Any
    lifetime: ServiceLifetime
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    dependencies: List[Type] = None


class IServiceRegistry(ABC):
    """服务注册中心接口"""
    
    @abstractmethod
    def register_singleton(self, service_type: Type, implementation: Any) -> 'IServiceRegistry':
        """注册单例服务"""
        pass
    
    @abstractmethod
    def register_transient(self, service_type: Type, implementation: Type) -> 'IServiceRegistry':
        """注册瞬态服务"""
        pass
    
    @abstractmethod
    def register_scoped(self, service_type: Type, implementation: Type) -> 'IServiceRegistry':
        """注册作用域服务"""
        pass
    
    @abstractmethod
    def register_factory(self, service_type: Type, factory: Callable, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'IServiceRegistry':
        """注册工厂服务"""
        pass
    
    @abstractmethod
    def get_service(self, service_type: Type) -> Any:
        """获取服务实例"""
        pass
    
    @abstractmethod
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        pass
    
    @abstractmethod
    def unregister(self, service_type: Type) -> bool:
        """注销服务"""
        pass


class ServiceRegistry(IServiceRegistry):
    """服务注册中心实现"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def register_singleton(self, service_type: Type, implementation: Any) -> 'IServiceRegistry':
        """注册单例服务"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.SINGLETON,
                instance=implementation
            )
            self.logger.info(f"注册单例服务: {service_type.__name__}")
        return self
    
    def register_transient(self, service_type: Type, implementation: Type) -> 'IServiceRegistry':
        """注册瞬态服务"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.TRANSIENT
            )
            self.logger.info(f"注册瞬态服务: {service_type.__name__}")
        return self
    
    def register_scoped(self, service_type: Type, implementation: Type) -> 'IServiceRegistry':
        """注册作用域服务"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=implementation,
                lifetime=ServiceLifetime.SCOPED
            )
            self.logger.info(f"注册作用域服务: {service_type.__name__}")
        return self
    
    def register_factory(self, service_type: Type, factory: Callable, lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> 'IServiceRegistry':
        """注册工厂服务"""
        with self._lock:
            self._services[service_type] = ServiceDescriptor(
                service_type=service_type,
                implementation=factory,
                lifetime=lifetime,
                factory=factory
            )
            self.logger.info(f"注册工厂服务: {service_type.__name__} (生命周期: {lifetime.value})")
        return self
    
    def get_service(self, service_type: Type) -> Any:
        """获取服务实例"""
        with self._lock:
            if service_type not in self._services:
                raise ValueError(f"服务 {service_type.__name__} 未注册")
            
            descriptor = self._services[service_type]
            
            if descriptor.lifetime == ServiceLifetime.SINGLETON:
                return descriptor.instance
            
            elif descriptor.lifetime == ServiceLifetime.TRANSIENT:
                if descriptor.factory:
                    return descriptor.factory()
                return descriptor.implementation()
            
            elif descriptor.lifetime == ServiceLifetime.SCOPED:
                if service_type not in self._scoped_instances:
                    if descriptor.factory:
                        self._scoped_instances[service_type] = descriptor.factory()
                    else:
                        self._scoped_instances[service_type] = descriptor.implementation()
                return self._scoped_instances[service_type]
            
            return None
    
    def is_registered(self, service_type: Type) -> bool:
        """检查服务是否已注册"""
        with self._lock:
            return service_type in self._services
    
    def unregister(self, service_type: Type) -> bool:
        """注销服务"""
        with self._lock:
            if service_type in self._services:
                del self._services[service_type]
                if service_type in self._scoped_instances:
                    del self._scoped_instances[service_type]
                self.logger.info(f"注销服务: {service_type.__name__}")
                return True
            return False
    
    def clear_scoped_instances(self):
        """清除作用域实例"""
        with self._lock:
            self._scoped_instances.clear()
            self.logger.info("清除所有作用域实例")
    
    def get_registered_services(self) -> List[Type]:
        """获取已注册的服务类型"""
        with self._lock:
            return list(self._services.keys())
    
    def get_service_info(self, service_type: Type) -> Optional[Dict[str, Any]]:
        """获取服务信息"""
        with self._lock:
            if service_type not in self._services:
                return None
            
            descriptor = self._services[service_type]
            return {
                'service_type': service_type.__name__,
                'lifetime': descriptor.lifetime.value,
                'has_factory': descriptor.factory is not None,
                'has_instance': descriptor.instance is not None,
                'dependencies': descriptor.dependencies or []
            }


class ServiceLocator:
    """服务定位器"""
    
    def __init__(self, registry: IServiceRegistry):
        self._registry = registry
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_service(self, service_type: Type) -> Any:
        """获取服务"""
        try:
            return self._registry.get_service(service_type)
        except Exception as e:
            self.logger.error(f"获取服务失败 {service_type.__name__}: {e}")
            raise
    
    def try_get_service(self, service_type: Type) -> Optional[Any]:
        """尝试获取服务"""
        try:
            return self._registry.get_service(service_type)
        except Exception as e:
            self.logger.warning(f"获取服务失败 {service_type.__name__}: {e}")
            return None
    
    def is_service_available(self, service_type: Type) -> bool:
        """检查服务是否可用"""
        return self._registry.is_registered(service_type)


# 全局服务注册中心
_global_registry: Optional[ServiceRegistry] = None
_registry_lock = threading.Lock()


def get_global_registry() -> ServiceRegistry:
    """获取全局服务注册中心"""
    global _global_registry
    if _global_registry is None:
        with _registry_lock:
            if _global_registry is None:
                _global_registry = ServiceRegistry()
    return _global_registry


def get_service_locator() -> ServiceLocator:
    """获取服务定位器"""
    return ServiceLocator(get_global_registry())


def register_core_services():
    """注册核心服务"""
    registry = get_global_registry()
    
    try:
        # 注册配置服务
        from ..utils.unified_centers import get_unified_center
        config_center = get_unified_center('get_unified_config_center')
        if config_center:
            registry.register_singleton(type(config_center), config_center)
    except ImportError:
        pass
    
    # 注册日志服务
    registry.register_singleton(logging.Logger, logging.getLogger("RANGEN"))
    
    # 注册ML/RL协同引擎
    try:
        from ..ai.ml_rl_synergy_engine import MLRLSynergyEngine
        registry.register_singleton(MLRLSynergyEngine, MLRLSynergyEngine())
    except ImportError:
        pass
    
    # 注册多步推理引擎
    try:
        from ..ai.multi_step_reasoning_engine import MultiStepReasoningEngine
        registry.register_singleton(MultiStepReasoningEngine, MultiStepReasoningEngine())
    except ImportError:
        pass
    
    registry.logger.info("核心服务注册完成")


# 装饰器：自动注入服务
def inject_service(service_type: Type):
    """服务注入装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            locator = get_service_locator()
            service = locator.get_service(service_type)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator


# 装饰器：可选服务注入
def inject_optional_service(service_type: Type):
    """可选服务注入装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            locator = get_service_locator()
            service = locator.try_get_service(service_type)
            return func(service, *args, **kwargs)
        return wrapper
    return decorator
