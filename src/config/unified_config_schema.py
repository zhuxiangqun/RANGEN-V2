#!/usr/bin/env python3
"""
Unified Configuration Schema - 统一配置架构

定义所有可配置参数的类型、默认值和约束
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ConfigCategory(Enum):
    """配置类别"""
    RETRIEVAL = "retrieval"
    REASONING = "reasoning"
    AGENT = "agent"
    PERFORMANCE = "performance"
    SECURITY = "security"


@dataclass
class ConfigSchema:
    """配置项架构"""
    key: str
    category: ConfigCategory
    value_type: type
    default: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    description: str = ""
    env_override: Optional[str] = None


# 配置架构注册表
CONFIG_SCHEMA: Dict[str, ConfigSchema] = {}


def register_config(
    key: str,
    category: ConfigCategory,
    value_type: type,
    default: Any,
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    description: str = "",
    env_override: Optional[str] = None
):
    """注册配置项"""
    schema = ConfigSchema(
        key=key,
        category=category,
        value_type=value_type,
        default=default,
        min_value=min_value,
        max_value=max_value,
        description=description,
        env_override=env_override
    )
    CONFIG_SCHEMA[key] = schema


# ============================================================================
# 检索配置
# ============================================================================
register_config(
    key="retrieval.similarity_threshold",
    category=ConfigCategory.RETRIEVAL,
    value_type=float,
    default=0.6,
    min_value=0.0,
    max_value=1.0,
    description="知识检索相似度阈值",
    env_override="RETRIEVAL_SIMILARITY_THRESHOLD"
)

register_config(
    key="retrieval.top_k",
    category=ConfigCategory.RETRIEVAL,
    value_type=int,
    default=10,
    min_value=1,
    max_value=100,
    description="检索返回结果数量"
)

register_config(
    key="retrieval.confidence_threshold",
    category=ConfigCategory.RETRIEVAL,
    value_type=float,
    default=0.5,
    min_value=0.0,
    max_value=1.0,
    description="检索结果置信度阈值"
)


# ============================================================================
# 推理配置
# ============================================================================
register_config(
    key="reasoning.max_steps",
    category=ConfigCategory.REASONING,
    value_type=int,
    default=100,
    min_value=1,
    max_value=1000,
    description="推理最大步数"
)

register_config(
    key="reasoning.confidence_threshold",
    category=ConfigCategory.REASONING,
    value_type=float,
    default=0.5,
    min_value=0.0,
    max_value=1.0,
    description="推理置信度阈值"
)

register_config(
    key="reasoning.timeout",
    category=ConfigCategory.REASONING,
    value_type=float,
    default=30.0,
    min_value=1.0,
    max_value=300.0,
    description="推理超时时间(秒)"
)


# ============================================================================
# Agent配置
# ============================================================================
register_config(
    key="agent.max_retries",
    category=ConfigCategory.AGENT,
    value_type=int,
    default=3,
    min_value=0,
    max_value=10,
    description="Agent最大重试次数"
)

register_config(
    key="agent.timeout",
    category=ConfigCategory.AGENT,
    value_type=float,
    default=30.0,
    min_value=1.0,
    max_value=300.0,
    description="Agent执行超时时间(秒)"
)


# ============================================================================
# 性能配置
# ============================================================================
register_config(
    key="performance.max_concurrent",
    category=ConfigCategory.PERFORMANCE,
    value_type=int,
    default=5,
    min_value=1,
    max_value=50,
    description="最大并发数"
)

register_config(
    key="performance.cache_ttl",
    category=ConfigCategory.PERFORMANCE,
    value_type=int,
    default=3600,
    min_value=60,
    max_value=86400,
    description="缓存TTL(秒)"
)


def get_schema(key: str) -> Optional[ConfigSchema]:
    """获取配置项架构"""
    return CONFIG_SCHEMA.get(key)


def get_all_schemas(category: Optional[ConfigCategory] = None) -> List[ConfigSchema]:
    """获取所有配置项架构"""
    if category:
        return [s for s in CONFIG_SCHEMA.values() if s.category == category]
    return list(CONFIG_SCHEMA.values())


def validate_config(key: str, value: Any) -> bool:
    """验证配置值"""
    schema = CONFIG_SCHEMA.get(key)
    if not schema:
        return True  # 未注册的配置不做验证
    
    if schema.min_value is not None and value < schema.min_value:
        return False
    if schema.max_value is not None and value > schema.max_value:
        return False
    
    return True
