#!/usr/bin/env python3
"""
系统常量配置
管理所有魔法数字和硬编码值
注意：环境变量配置已移至 UnifiedConfigCenter 统一管理
"""

import os
from typing import Dict, Any


class SystemConstants:
    """系统常量配置 - 只保留真正的常量，不包含环境变量配置"""
    
    # 技术规范常量（不会改变）
    VECTOR_DIMENSION = 384
    MODEL_EMBEDDING_DIM = 384
    API_KEY_LENGTH = 64
    PASSWORD_MIN_LENGTH = 8
    DB_MAX_CONNECTIONS = 20
    
    # 性能相关常量
    MODEL_MAX_LENGTH = 256
    CHUNK_SIZE = 1024
    CONNECTION_TIMEOUT = 10
    
    # 算法相关常量
    SIMILARITY_THRESHOLD = 0.6
    ALERT_THRESHOLD = 0.95
    NPROBE = 10
    
    # 网络相关常量
    DEFAULT_PORT = 8000
    DEFAULT_LOG_LEVEL = "INFO"
    
    # 缓存相关常量
    CACHE_TTL_SECONDS = 3600
    
    # 注意：以下配置已移至 UnifiedConfigCenter 统一管理
    # MAX_EVALUATION_ITEMS, BATCH_SIZE, LEARNING_RATE, 
    # MAX_CONCURRENT_QUERIES, REQUEST_TIMEOUT, MAX_CACHE_SIZE 等
    # 请使用 get_env_config() 函数获取这些配置
    
    @classmethod
    def get_all_constants(cls) -> Dict[str, Any]:
        """获取所有常量"""
        constants = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and not callable(getattr(cls, attr_name)):
                constants[attr_name] = getattr(cls, attr_name)
        return constants
    
    @classmethod
    def get_constant(cls, name: str, default: Any = None) -> Any:
        """获取指定常量"""
        return getattr(cls, name, default)


# 创建全局实例
constants = SystemConstants()


def get_constants() -> SystemConstants:
    """获取常量实例"""
    return constants


def get_constant(name: str, default: Any = None) -> Any:
    """获取指定常量值"""
    return constants.get_constant(name, default)
