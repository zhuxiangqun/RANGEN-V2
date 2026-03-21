#!/usr/bin/env python3
"""
编排层模块 (Orchestration Layer)

AI基盘架构的核心编排模块，负责：
- 任务分解与智能路由
- 多Agent协调
- 执行计划管理
- 反馈循环机制
"""

import warnings

# 发出弃用警告（如果从旧路径导入）
warnings.filterwarnings("once", category=DeprecationWarning)

# ============================================================================
# 核心服务
# ============================================================================

try:
    from .services import (
        CoreService,
        Component,
        ServiceManager,
        get_core_logger
    )
except ImportError:
    from ..services import (
        CoreService,
        Component,
        ServiceManager,
        get_core_logger
    )

# ============================================================================
# 性能监控 (从 services 导入)
# ============================================================================

try:
    from src.services.performance_monitor import (
        PerformanceMonitor,
        PerformanceMetric,
        PerformanceLevel,
        PerformanceTrend,
        get_performance_monitor
    )
except ImportError:
    # 尝试从 monitoring.tools 导入
    try:
        from src.monitoring.tools.performance_monitor import (
            PerformanceMonitor,
            PerformanceMetric,
            PerformanceLevel,
            PerformanceTrend,
            get_performance_monitor
        )
    except ImportError:
        warnings.warn("Performance monitor not available", ImportWarning)
        PerformanceMonitor = None
        PerformanceMetric = None
        PerformanceLevel = None
        PerformanceTrend = None
        get_performance_monitor = None

# ============================================================================
# 编排器
# ============================================================================

try:
    from .intelligent_orchestrator import IntelligentOrchestrator
except ImportError:
    pass

# ============================================================================
# 任务管理
# ============================================================================

try:
    from .task_decomposition import TaskDecomposer
except ImportError:
    pass

# ============================================================================
# 导出列表
# ============================================================================

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
    'get_performance_monitor',
]

# ============================================================================
# 版本信息
# ============================================================================

__version__ = "2.0.0"
__layer__ = "orchestration"
