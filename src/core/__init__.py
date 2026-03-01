#!/usr/bin/env python3
"""
核心架构模块
"""

from .services import (
    CoreService,
    Component,
    ServiceManager,
    get_core_logger
)

# 性能监控
from ..tools.monitoring.performance_monitor import (
    PerformanceMonitor,
    PerformanceMetric,
    PerformanceLevel,
    PerformanceTrend,
    get_performance_monitor
)

__all__ = [
    # 服务
    'CoreService',
    'Component',
    'ServiceManager',
    'get_core_logger',
    
    # 性能监控
    'PerformanceMonitor',
    'PerformanceMetric',
    'PerformanceLevel',
    'PerformanceTrend',
    'get_performance_monitor'
]
