#!/usr/bin/env python3
"""
Core Interfaces
==============

⚠️ DEPRECATED: Agent 接口请使用 src.interfaces.unified_agent 替代
    - 统一接口: UnifiedAgentConfig, UnifiedAgentResult, IAgent
    - 迁移: from src.interfaces.unified_agent import IAgent

此文件保留 IConfigManager 和 IThresholdManager 接口。
Agent 接口已弃用，请使用 unified_agent.py
"""

import logging
import warnings
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

# 发出弃用警告 (仅当导入 IAgent 时)
_import_warned = False


def _warn_if_needed():
    global _import_warned
    if not _import_warned:
        warnings.warn(
            "src.interfaces.core_interfaces.IAgent is deprecated. "
            "Please use src.interfaces.unified_agent.IAgent instead.\n"
            "Migration: from src.interfaces.unified_agent import IAgent",
            DeprecationWarning,
            stacklevel=3
        )
        _import_warned = True


class CoreInterfaces:
    """CoreInterfaces类"""
    
    def __init__(self) -> None:
        """初始化"""
        self.initialized = True
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data
    
    def validate(self, data: Any) -> bool:
        """验证数据"""
        return data is not None


# Agent Interface (DEPRECATED)
class IAgent:
    """
    ⚠️ DEPRECATED: Agent Interface
    
    请使用 src.interfaces.unified_agent.IAgent
    
    这个接口返回 Dict 而非 UnifiedAgentResult，请迁移到统一接口。
    """
    
    def __init__(self, agent_id: str) -> None:
        """初始化"""
        _warn_if_needed()
        self.agent_id = agent_id
    
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """处理查询"""
        raise NotImplementedError
    
    def is_enabled(self) -> bool:
        """检查是否启用"""
        return True


# Config Manager Interface
class IConfigManager:
    """Config Manager Interface"""
    
    def get_config(self, key: str) -> Any:
        """获取配置"""
        raise NotImplementedError
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        raise NotImplementedError


# Threshold Manager Interface
class IThresholdManager:
    """Threshold Manager Interface"""
    
    def get_threshold(self, name: str) -> float:
        """获取阈值"""
        raise NotImplementedError
    
    def set_threshold(self, name: str, value: float) -> None:
        """设置阈值"""
        raise NotImplementedError


# 便捷函数
def get_core_interfaces() -> CoreInterfaces:
    """获取实例"""
    return CoreInterfaces()
