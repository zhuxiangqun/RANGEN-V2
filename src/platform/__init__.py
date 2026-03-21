"""
RANGEN AI 基盘平台核心模块

纯新增模块，不影响现有系统。
通过环境变量 RANGEN_PLATFORM_ENABLED 控制是否启用。

默认状态: RANGEN_PLATFORM_ENABLED=false (平台功能禁用，现有系统完全不受影响)
启用平台: RANGEN_PLATFORM_ENABLED=true
"""

__version__ = "1.0.0"

from src.platform.app.registry import AppRegistry, App, AppStatus, get_app_registry
from src.platform.quota.manager import QuotaManager, QuotaLimit, QuotaUsage, get_quota_manager
from src.platform.namespace.manager import NamespaceManager, Namespace, get_namespace_manager

__all__ = [
    # App Management
    "AppRegistry",
    "App",
    "AppStatus",
    "get_app_registry",
    # Quota Management
    "QuotaManager",
    "QuotaLimit",
    "QuotaUsage",
    "get_quota_manager",
    # Namespace Management
    "NamespaceManager",
    "Namespace",
    "get_namespace_manager",
]
