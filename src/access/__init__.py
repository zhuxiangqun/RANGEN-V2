#!/usr/bin/env python3
"""
AI 中台接入层 (Access Layer)

提供 API、UI、SDK 入口
"""

import warnings

# 尝试从新的 access.api 导入
try:
    from src.access.api import platform
    api_router = platform
except ImportError:
    # 向后兼容：从旧的 src.api 导入
    try:
        from src.api import create_app
        api_router = create_app
    except ImportError:
        warnings.warn("API router not available", ImportWarning)
        api_router = None

__all__ = ["api_router", "platform"]
