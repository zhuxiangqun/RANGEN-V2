#!/usr/bin/env python3
"""
服务注册器
配置所有核心服务及其依赖关系
"""

import logging
from typing import Dict, Any, Type, Callable
from .unified_container import UnifiedDIContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class ServiceRegistrar:
    """服务注册器"""
    
    def __init__(self, container: UnifiedDIContainer):
        self.container = container
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def register_core_services(self) -> 'ServiceRegistrar':
        """注册核心服务"""
        self.logger.info("开始注册核心服务...")
        
        # 配置服务
        self._register_config_services()
        
        # 日志服务
        self._register_logging_services()
        
        # 认证服务
        self._register_auth_services()
        
        # 可观测性服务
        self._register_observability_services()
        
        # 核心业务服务
        self._register_core_business_services()
        
        # 智能体服务
        self._register_agent_services()
        
        # 工具服务
        self._register_tool_services()
        
        # 自动扩缩容服务
        self._register_autoscaling_services()
        
        # 安全检测服务
        self._register_security_detection_services()
        
        self.logger.info("核心服务注册完成")
        return self
    
    def _register_config_services(self) -> None:
        """注册配置服务"""
        try:
            # 统一配置中心
            from src.utils.unified_centers import get_unified_config_center
            config_center = get_unified_config_center()
            self.container.register_singleton(type(config_center), config_center)
            self.logger.info("注册统一配置中心")
        except ImportError as e:
            self.logger.warning(f"统一配置中心导入失败: {e}")
        
        try:
            # 统一配置管理器
            from src.config.unified_config_system import ConfigManager
            self.container.register_singleton(ConfigManager, ConfigManager)
            self.logger.info("注册统一配置管理器")
        except ImportError as e:
            self.logger.warning(f"统一配置管理器导入失败: {e}")
        
        try:
            # 配置服务接口
            from src.core.interfaces import IConfigurationService
            from src.core.service_adapters import ConfigurationServiceAdapter
            self.container.register_singleton(IConfigurationService, ConfigurationServiceAdapter)
            self.logger.info("注册配置服务适配器")
        except ImportError as e:
            self.logger.warning(f"配置服务适配器导入失败: {e}")
    
    def _register_logging_services(self) -> None:
        """注册日志服务"""
        # 基础日志器
        import logging
        self.container.register_singleton(logging.Logger, lambda: logging.getLogger("RANGEN"))
        
        try:
            # 结构化日志服务
            from src.observability.structured_logging import StructuredLogger, StructuredLoggingConfig
            self.container.register_singleton(StructuredLoggingConfig, StructuredLoggingConfig)
            self.container.register_singleton(StructuredLogger, StructuredLogger("RANGEN"))
            self.logger.info("注册结构化日志服务")
        except ImportError as e:
            self.logger.warning(f"结构化日志服务导入失败: {e}")
        
        try:
            # 日志服务接口
            from src.core.interfaces import ILoggingService
            from src.core.service_adapters import LoggingServiceAdapter
            self.container.register_singleton(ILoggingService, LoggingServiceAdapter)
            self.logger.info("注册日志服务适配器")
        except ImportError as e:
            self.logger.warning(f"日志服务适配器导入失败: {e}")
    
    def _register_auth_services(self) -> None:
        """注册认证服务"""
        try:
            # 认证服务
            from src.api.auth_service import AuthService
            self.container.register_singleton(AuthService, AuthService)
            self.logger.info("注册认证服务")
        except ImportError as e:
            self.logger.warning(f"认证服务导入失败: {e}")
        
        try:
            # 审计日志服务
            from src.services.audit_log_service import AuditLogService
            self.container.register_singleton(AuditLogService, AuditLogService)
            self.logger.info("注册审计日志服务")
        except ImportError as e:
            self.logger.warning(f"审计日志服务导入失败: {e}")
    
    def _register_observability_services(self) -> None:
        """注册可观测性服务"""
        try:
            # OpenTelemetry追踪
            from src.observability.tracing import OpenTelemetryConfig
            self.container.register_singleton(OpenTelemetryConfig, OpenTelemetryConfig)
            self.logger.info("注册OpenTelemetry追踪配置")
        except ImportError as e:
            self.logger.warning(f"OpenTelemetry追踪导入失败: {e}")
        
        try:
            # 性能监控
            from src.observability.metrics import MetricsCollector, OpenTelemetryMetrics
            self.container.register_singleton(MetricsCollector, MetricsCollector)
            self.container.register_singleton(OpenTelemetryMetrics, OpenTelemetryMetrics)
            self.logger.info("注册性能监控服务")
        except ImportError as e:
            self.logger.warning(f"性能监控服务导入失败: {e}")
    
    def _register_core_business_services(self) -> None:
        """注册核心业务服务"""
        try:
            # 上下文管理器
            from src.core.context_manager import ContextManager
            self.container.register_singleton(ContextManager, ContextManager)
            self.logger.info("注册上下文管理器")
        except ImportError as e:
            self.logger.warning(f"上下文管理器导入失败: {e}")
        
        try:
            # 执行协调器
            from src.core.execution_coordinator import ExecutionCoordinator
            self.container.register_singleton(ExecutionCoordinator, ExecutionCoordinator)
            self.logger.info("注册执行协调器")
        except ImportError as e:
            self.logger.warning(f"执行协调器导入失败: {e}")
        
        try:
            # 知识检索服务
            from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
            self.container.register_singleton(KnowledgeRetrievalService, KnowledgeRetrievalService)
            self.logger.info("注册知识检索服务")
        except ImportError as e:
            self.logger.warning(f"知识检索服务导入失败: {e}")
        
        try:
            # 错误处理服务
            from src.utils.error_handler import ErrorManager
            self.container.register_singleton(ErrorManager, ErrorManager)
            self.logger.info("注册错误处理服务")
        except ImportError as e:
            self.logger.warning(f"错误处理服务导入失败: {e}")
    
    def _register_agent_services(self) -> None:
        """注册智能体服务"""
        try:
            # 智能体构建器
            from src.agents.agent_builder import AgentBuilder
            self.container.register_singleton(AgentBuilder, AgentBuilder)
            self.logger.info("注册智能体构建器")
        except ImportError as e:
            self.logger.warning(f"智能体构建器导入失败: {e}")
        
        try:
            # 智能体协调器
            from src.agents.agent_coordinator import AgentCoordinator
            self.container.register_singleton(AgentCoordinator, AgentCoordinator)
            self.logger.info("注册智能体协调器")
        except ImportError as e:
            self.logger.warning(f"智能体协调器导入失败: {e}")
        
        try:
            # 基础智能体
            from src.agents.base_agent import BaseAgent
            # 注册为工厂，因为BaseAgent通常是基类，具体实现由子类提供
            self.container.register_factory(BaseAgent, lambda: None)
            self.logger.info("注册基础智能体工厂")
        except ImportError as e:
            self.logger.warning(f"基础智能体导入失败: {e}")
    
    def _register_tool_services(self) -> None:
        """注册工具服务"""
        try:
            # 工具注册表
            from src.agents.tools.tool_registry import ToolRegistry
            self.container.register_singleton(ToolRegistry, ToolRegistry)
            self.logger.info("注册工具注册表")
        except ImportError as e:
            self.logger.warning(f"工具注册表导入失败: {e}")
        
        try:
            # 基础工具
            from src.agents.tools.base_tool import BaseTool
            # 注册为工厂
            self.container.register_factory(BaseTool, lambda: None)
            self.logger.info("注册基础工具工厂")
        except ImportError as e:
            self.logger.warning(f"基础工具导入失败: {e}")
    
    def _register_autoscaling_services(self) -> None:
        """注册自动扩缩容服务"""
        try:
            # 首先尝试注册高级自动扩缩容服务
            from src.services.advanced_autoscaling_service import AdvancedAutoscalingService, create_advanced_autoscaling_service
            self.container.register_singleton(AdvancedAutoscalingService, create_advanced_autoscaling_service())
            # 同时注册基础服务接口以保持兼容性
            from src.services.autoscaling_service import AutoscalingService
            self.container.register_singleton(AutoscalingService, create_advanced_autoscaling_service())
            self.logger.info("注册高级自动扩缩容服务")
        except ImportError as e:
            self.logger.warning(f"高级自动扩缩容服务导入失败，回退到基础版本: {e}")
            try:
                # 回退到基础自动扩缩容服务
                from src.services.autoscaling_service import AutoscalingService, create_autoscaling_service
                self.container.register_singleton(AutoscalingService, create_autoscaling_service())
                self.logger.info("注册基础自动扩缩容服务")
            except ImportError as e2:
                self.logger.warning(f"自动扩缩容服务导入失败: {e2}")
    
    def _register_security_detection_services(self) -> None:
        """注册安全检测服务"""
        try:
            # 首先尝试注册高级安全检测服务
            from src.services.advanced_security_detection_service import AdvancedSecurityDetectionService, create_advanced_security_detection_service
            self.container.register_singleton(AdvancedSecurityDetectionService, create_advanced_security_detection_service())
            # 同时注册基础服务接口以保持兼容性
            from src.services.security_detection_service import SecurityDetectionService
            self.container.register_singleton(SecurityDetectionService, create_advanced_security_detection_service())
            self.logger.info("注册高级安全检测服务")
        except ImportError as e:
            self.logger.warning(f"高级安全检测服务导入失败，回退到基础版本: {e}")
            try:
                # 回退到基础安全检测服务
                from src.services.security_detection_service import SecurityDetectionService, create_security_detection_service
                self.container.register_singleton(SecurityDetectionService, create_security_detection_service())
                self.logger.info("注册基础安全检测服务")
            except ImportError as e2:
                self.logger.warning(f"安全检测服务导入失败: {e2}")
    
    def register_custom_service(self, 
                               service_type: Type, 
                               implementation: Any, 
                               lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> 'ServiceRegistrar':
        """注册自定义服务"""
        if lifetime == ServiceLifetime.SINGLETON:
            self.container.register_singleton(service_type, implementation)
        elif lifetime == ServiceLifetime.TRANSIENT:
            self.container.register_transient(service_type, implementation)
        elif lifetime == ServiceLifetime.SCOPED:
            self.container.register_scoped(service_type, implementation)
        
        self.logger.info(f"注册自定义服务: {service_type.__name__} (生命周期: {lifetime.value})")
        return self


def create_service_registrar(container: UnifiedDIContainer = None) -> ServiceRegistrar:
    """创建服务注册器"""
    if container is None:
        from .unified_container import get_container
        container = get_container()
    
    registrar = ServiceRegistrar(container)
    return registrar