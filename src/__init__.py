#!/usr/bin/env python3
"""
RANGEN AI 中台系统
RANGEN AI Platform - Enterprise AI Foundation Platform

AI基盘架构分层:
- Layer 1: 接入层 (Access) - API、UI、SDK
- Layer 2: 网关层 (Gateway) - 统一入口
- Layer 3: 编排层 (Orchestration) - 任务分解、智能路由
- Layer 4: 执行层 (Execution) - Agent执行、工作流
- Layer 5: 服务层 (Services) - LLM、知识、工具
- Layer 6: 平台层 (Platform) - 应用管理、配额、计量
- Layer 7: 基础设施层 (Infra) - 数据库、缓存、存储
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import warnings

# 版本信息
__version__ = "2.0.0"
__author__ = "RANGEN AI Team"

# ============================================================================
# 模块导入 - 简化版，使用延迟导入
# ============================================================================

# 接入层
try:
    from src import access
    api_router = getattr(access, 'api_router', None)
except ImportError:
    api_router = None

# Agent 层
try:
    from src import agents
except ImportError:
    agents = None

# 服务层
try:
    from src import services
except ImportError:
    services = None

# 编排层
try:
    from src import orchestration
except ImportError:
    orchestration = None

# 平台层
try:
    from src import platform
except ImportError:
    platform = None

# 网关层
try:
    from src import gateway
except ImportError:
    gateway = None

# ============================================================================
# 导出列表
# ============================================================================

__all__ = [
    "__version__",
    "api_router",
    "agents",
    "services",
    "orchestration",
    "platform",
    "gateway",
]
