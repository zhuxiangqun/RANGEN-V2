#!/usr/bin/env python3
"""
工具注册表 - 向后兼容重定向

⚠️  ToolRegistry 已移动到 src.services.tool_registry
    此文件仅用于保持向后兼容。
"""

import warnings
warnings.warn(
    "src.agents.tools.tool_registry 已移动到 src.services.tool_registry",
    DeprecationWarning,
    stacklevel=2
)

from src.services.tool_registry import ToolRegistry, get_tool_registry

__all__ = ['ToolRegistry', 'get_tool_registry']
