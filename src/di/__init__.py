"""
依赖注入系统
提供统一的依赖注入和生命周期管理
"""

from .unified_container import UnifiedDIContainer, get_container, ServiceLifetime
from .service_registrar import ServiceRegistrar
from .bootstrap import bootstrap_application

__all__ = [
    "UnifiedDIContainer",
    "get_container",
    "ServiceLifetime",
    "ServiceRegistrar",
    "bootstrap_application"
]