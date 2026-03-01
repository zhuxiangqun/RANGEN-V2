#!/usr/bin/env python3
"""
依赖注入引导程序
初始化依赖注入容器并配置所有服务
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from .unified_container import UnifiedDIContainer, get_container
from .service_registrar import ServiceRegistrar, create_service_registrar

logger = logging.getLogger(__name__)


class DIBootstrap:
    """依赖注入引导程序"""
    
    def __init__(self, container: Optional[UnifiedDIContainer] = None):
        self.container = container or get_container()
        self.registrar = create_service_registrar(self.container)
        self.initialized = False
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def initialize(self) -> 'DIBootstrap':
        """初始化引导程序（同步）"""
        if self.initialized:
            self.logger.warning("引导程序已初始化，跳过重复初始化")
            return self
        
        self.logger.info("开始初始化依赖注入引导程序...")
        
        try:
            # 1. 注册核心服务
            self.registrar.register_core_services()
            
            # 2. 验证服务依赖
            self._validate_service_dependencies()
            
            # 3. 标记为已初始化
            self.initialized = True
            
            self.logger.info("依赖注入引导程序初始化完成")
            return self
            
        except Exception as e:
            self.logger.error(f"依赖注入引导程序初始化失败: {e}")
            raise
    
    async def initialize_async(self) -> 'DIBootstrap':
        """初始化引导程序（异步）"""
        if self.initialized:
            self.logger.warning("引导程序已初始化，跳过重复初始化")
            return self
        
        self.logger.info("开始异步初始化依赖注入引导程序...")
        
        try:
            # 1. 注册核心服务
            self.registrar.register_core_services()
            
            # 2. 验证服务依赖（异步）
            await self._validate_service_dependencies_async()
            
            # 3. 预加载关键服务
            await self._preload_critical_services()
            
            # 4. 标记为已初始化
            self.initialized = True
            
            self.logger.info("异步依赖注入引导程序初始化完成")
            return self
            
        except Exception as e:
            self.logger.error(f"异步依赖注入引导程序初始化失败: {e}")
            raise
    
    def _validate_service_dependencies(self) -> None:
        """验证服务依赖关系（同步）"""
        self.logger.info("验证服务依赖关系...")
        
        # 获取所有已注册的服务
        services = self.container.get_registered_services()
        
        for service_type, descriptor in services.items():
            if descriptor.dependencies:
                self.logger.debug(f"检查服务 {service_type.__name__} 的依赖项: {[d.__name__ for d in descriptor.dependencies]}")
                
                # 检查每个依赖是否已注册
                for dep_type in descriptor.dependencies:
                    if not self.container.is_registered(dep_type):
                        self.logger.warning(f"服务 {service_type.__name__} 依赖未注册的服务: {dep_type.__name__}")
        
        self.logger.info("服务依赖关系验证完成")
    
    async def _validate_service_dependencies_async(self) -> None:
        """验证服务依赖关系（异步）"""
        self.logger.info("异步验证服务依赖关系...")
        
        # 获取所有已注册的服务
        services = self.container.get_registered_services()
        
        for service_type, descriptor in services.items():
            if descriptor.dependencies:
                self.logger.debug(f"检查服务 {service_type.__name__} 的依赖项: {[d.__name__ for d in descriptor.dependencies]}")
                
                # 检查每个依赖是否已注册
                for dep_type in descriptor.dependencies:
                    if not self.container.is_registered(dep_type):
                        self.logger.warning(f"服务 {service_type.__name__} 依赖未注册的服务: {dep_type.__name__}")
        
        self.logger.info("异步服务依赖关系验证完成")
    
    async def _preload_critical_services(self) -> None:
        """预加载关键服务（异步）"""
        self.logger.info("预加载关键服务...")
        
        critical_services = [
            # 配置服务
            "ConfigManager",
            "IConfigurationService",
            
            # 日志服务
            "StructuredLogger",
            "ILoggingService",
            
            # 错误处理服务
            "ErrorManager",
        ]
        
        for service_name in critical_services:
            try:
                # 尝试通过名称查找服务类型
                service_type = self._find_service_type_by_name(service_name)
                if service_type:
                    await self.container.get_service_async(service_type)
                    self.logger.debug(f"预加载服务: {service_name}")
            except Exception as e:
                self.logger.warning(f"预加载服务 {service_name} 失败: {e}")
        
        self.logger.info("关键服务预加载完成")
    
    def _find_service_type_by_name(self, service_name: str) -> Optional[type]:
        """通过名称查找服务类型"""
        services = self.container.get_registered_services()
        
        for service_type in services.keys():
            if service_type.__name__ == service_name:
                return service_type
        
        return None
    
    def get_service(self, service_type: type) -> Any:
        """获取服务实例（同步）"""
        if not self.initialized:
            self.logger.warning("引导程序未初始化，尝试自动初始化")
            self.initialize()
        
        return self.container.get_service(service_type)
    
    async def get_service_async(self, service_type: type) -> Any:
        """获取服务实例（异步）"""
        if not self.initialized:
            self.logger.warning("引导程序未初始化，尝试自动异步初始化")
            await self.initialize_async()
        
        return await self.container.get_service_async(service_type)
    
    def get_container(self) -> UnifiedDIContainer:
        """获取容器实例"""
        return self.container
    
    def get_registrar(self) -> ServiceRegistrar:
        """获取服务注册器"""
        return self.registrar
    
    def get_registered_services(self) -> Dict[str, str]:
        """获取已注册的服务列表"""
        services = self.container.get_registered_services()
        return {
            service_type.__name__: descriptor.lifetime.value
            for service_type, descriptor in services.items()
        }


# 全局引导程序实例
_global_bootstrap: Optional[DIBootstrap] = None


def bootstrap_application(container: Optional[UnifiedDIContainer] = None) -> DIBootstrap:
    """引导应用程序（同步）"""
    global _global_bootstrap
    if _global_bootstrap is None:
        _global_bootstrap = DIBootstrap(container)
        _global_bootstrap.initialize()
    return _global_bootstrap


async def bootstrap_application_async(container: Optional[UnifiedDIContainer] = None) -> DIBootstrap:
    """引导应用程序（异步）"""
    global _global_bootstrap
    if _global_bootstrap is None:
        _global_bootstrap = DIBootstrap(container)
        await _global_bootstrap.initialize_async()
    return _global_bootstrap


def get_bootstrap() -> DIBootstrap:
    """获取引导程序实例"""
    global _global_bootstrap
    if _global_bootstrap is None:
        raise RuntimeError("引导程序未初始化，请先调用 bootstrap_application()")
    return _global_bootstrap


def reset_bootstrap() -> None:
    """重置引导程序（主要用于测试）"""
    global _global_bootstrap
    _global_bootstrap = None


# 便捷函数
def get_service(service_type: type) -> Any:
    """便捷函数：获取服务实例（同步）"""
    bootstrap = get_bootstrap()
    return bootstrap.get_service(service_type)


async def get_service_async(service_type: type) -> Any:
    """便捷函数：获取服务实例（异步）"""
    bootstrap = get_bootstrap()
    return await bootstrap.get_service_async(service_type)