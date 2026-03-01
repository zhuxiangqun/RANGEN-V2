#!/usr/bin/env python3
"""
Schema-Driven Configuration Loader - 架构驱动的配置加载器

基于配置架构自动加载和验证配置
"""
import os
from typing import Any, Optional, Dict
from src.config.unified_config_schema import (
    CONFIG_SCHEMA,
    ConfigSchema,
    ConfigCategory,
    get_schema,
    validate_config,
    get_all_schemas
)


class SchemaConfigLoader:
    """基于架构的配置加载器"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._env_prefix = "RANGEN_"
    
    def get(self, key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        获取配置值
        
        优先级:
        1. 环境变量 (RANGEN_RETRIEVAL_SIMILARITY_THRESHOLD)
        2. 上下文参数 (context)
        3. 默认值 (from schema)
        """
        if key in self._cache:
            return self._cache[key]
        
        schema = get_schema(key)
        
        # 1. 尝试从环境变量获取
        env_key = self._get_env_key(key)
        env_value = os.environ.get(env_key)
        if env_value is not None:
            value = self._convert_value(env_value, schema)
            if validate_config(key, value):
                self._cache[key] = value
                return value
        
        # 2. 尝试从上下文获取
        if context and key in context:
            value = context[key]
            if validate_config(key, value):
                self._cache[key] = value
                return value
        
        # 3. 使用默认值
        if schema:
            self._cache[key] = schema.default
            return schema.default
        
        # 4. 无架构配置，返回None
        return None
    
    def _get_env_key(self, key: str) -> str:
        """转换为环境变量名"""
        return f"{self._env_prefix}{key.upper().replace('.', '_')}"
    
    def _convert_value(self, value: str, schema: Optional[ConfigSchema]) -> Any:
        """转换环境变量值"""
        if schema is None:
            return value
        
        # 类型转换
        if schema.value_type == bool:
            return value.lower() in ('true', '1', 'yes')
        elif schema.value_type == int:
            return int(value)
        elif schema.value_type == float:
            return float(value)
        
        return value
    
    def get_with_category(self, category: ConfigCategory) -> Dict[str, Any]:
        """获取指定类别的所有配置"""
        result = {}
        for schema in get_all_schemas(category):
            result[schema.key] = self.get(schema.key)
        return result
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


# 全局配置加载器实例
_config_loader = SchemaConfigLoader()


def get_config(key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """获取配置的便捷函数"""
    return _config_loader.get(key, context)


def get_category_config(category: ConfigCategory) -> Dict[str, Any]:
    """获取指定类别的所有配置"""
    return _config_loader.get_with_category(category)


# 便捷访问器
class ConfigAccessor:
    """配置访问器 - 提供类型安全的配置访问"""
    
    @property
    def retrieval(self) -> 'RetrievalConfig':
        return RetrievalConfig()
    
    @property
    def reasoning(self) -> 'ReasoningConfig':
        return ReasoningConfig()
    
    @property
    def agent(self) -> 'AgentConfig':
        return AgentConfig()
    
    @property
    def performance(self) -> 'PerformanceConfig':
        return PerformanceConfig()


class RetrievalConfig:
    """检索配置访问器"""
    
    @property
    def similarity_threshold(self) -> float:
        return get_config("retrieval.similarity_threshold") or 0.6
    
    @property
    def top_k(self) -> int:
        return get_config("retrieval.top_k") or 10
    
    @property
    def confidence_threshold(self) -> float:
        return get_config("retrieval.confidence_threshold") or 0.5


class ReasoningConfig:
    """推理配置访问器"""
    
    @property
    def max_steps(self) -> int:
        return get_config("reasoning.max_steps") or 100
    
    @property
    def confidence_threshold(self) -> float:
        return get_config("reasoning.confidence_threshold") or 0.5
    
    @property
    def timeout(self) -> float:
        return get_config("reasoning.timeout") or 30.0


class AgentConfig:
    """Agent配置访问器"""
    
    @property
    def max_retries(self) -> int:
        return get_config("agent.max_retries") or 3
    
    @property
    def timeout(self) -> float:
        return get_config("agent.timeout") or 30.0


class PerformanceConfig:
    """性能配置访问器"""
    
    @property
    def max_concurrent(self) -> int:
        return get_config("performance.max_concurrent") or 5
    
    @property
    def cache_ttl(self) -> int:
        return get_config("performance.cache_ttl") or 3600


# 全局访问器
config = ConfigAccessor()
