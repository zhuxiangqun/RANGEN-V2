"""
RANGEN API Routes

平台层模块，提供统一的API路由入口
"""

from .platform import router as platform_router

__all__ = ["platform_router"]
