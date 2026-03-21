#!/usr/bin/env python3
"""
API 接入层

提供 REST API 端点
"""

import warnings

# 尝试从 routes 导入平台路由
try:
    from src.access.api.routes import platform
    __all__ = ["platform"]
except ImportError:
    warnings.warn("API routes not available", ImportWarning)
    __all__ = []
