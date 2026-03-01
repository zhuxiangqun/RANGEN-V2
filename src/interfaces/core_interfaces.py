#!/usr/bin/env python3
"""
Core Interfaces
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


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


# Agent Interface
class IAgent:
    """Agent Interface"""
    
    def __init__(self, agent_id: str) -> None:
        """初始化"""
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
