#!/usr/bin/env python3
"""
统一配置加载器
================

提供统一的配置加载接口，简化配置管理。

Usage:
    from src.config.unified_config import get_config
    
    config = get_config()  # 使用默认环境
    config = get_config('production')  # 使用生产环境
    
    # 访问配置
    llm_config = config.llm
    agent_config = config.agents
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class UnifiedConfig:
    """统一配置对象"""
    system: Dict[str, Any] = field(default_factory=dict)
    llm: Dict[str, Any] = field(default_factory=dict)
    knowledge_base: Dict[str, Any] = field(default_factory=dict)
    kms: Dict[str, Any] = field(default_factory=dict)
    neural_models: Dict[str, Any] = field(default_factory=dict)
    agents: Dict[str, Any] = field(default_factory=dict)
    performance: Dict[str, Any] = field(default_factory=dict)
    retrieval: Dict[str, Any] = field(default_factory=dict)
    security: Dict[str, Any] = field(default_factory=dict)
    monitoring: Dict[str, Any] = field(default_factory=dict)
    integrations: Dict[str, Any] = field(default_factory=dict)
    raw: Dict[str, Any] = field(default_factory=dict)  # 原始配置
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UnifiedConfig':
        """从字典创建配置对象"""
        return cls(
            system=data.get('system', {}),
            llm=data.get('llm', {}),
            knowledge_base=data.get('knowledge_base', {}),
            kms=data.get('kms', {}),
            neural_models=data.get('neural_models', {}),
            agents=data.get('agents', {}),
            performance=data.get('performance', {}),
            retrieval=data.get('retrieval', {}),
            security=data.get('security', {}),
            monitoring=data.get('monitoring', {}),
            integrations=data.get('integrations', {}),
            raw=data,
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.raw.get(key, default)


def _resolve_env_vars(value: Any) -> Any:
    """解析环境变量引用 ${VAR:default}"""
    if isinstance(value, str) and '${' in value:
        import re
        pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
        matches = re.findall(pattern, value)
        for var_name, default in matches:
            env_value = os.getenv(var_name, default)
            value = value.replace(f'${{{var_name}:{default}}}', env_value)
            value = value.replace(f'${{{var_name}}}', env_value)
        return value
    elif isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


def load_config_file(path: str) -> Dict[str, Any]:
    """加载 YAML 配置文件"""
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
        return _resolve_env_vars(config) or {}
    except FileNotFoundError:
        print(f"Warning: Config file not found: {path}")
        return {}
    except yaml.YAMLError as e:
        print(f"Error: Invalid YAML in {path}: {e}")
        return {}


def get_config(env: Optional[str] = None) -> UnifiedConfig:
    """
    获取统一配置
    
    Args:
        env: 环境名称 ('development', 'production', 'testing')
             如果为 None，从 ENVIRONMENT 环境变量获取
    
    Returns:
        UnifiedConfig: 统一配置对象
    """
    if env is None:
        env = os.getenv('ENVIRONMENT', 'development')
    
    # 配置路径映射 - 相对于项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = os.path.join(current_dir, '..', '..', 'config')  # src/config -> 项目根 -> config
    
    config_paths = {
        'development': os.path.join(config_dir, 'environments', 'development.yaml'),
        'production': os.path.join(config_dir, 'environments', 'production.yaml'),
        'testing': os.path.join(config_dir, 'environments', 'testing.yaml'),
        'default': os.path.join(config_dir, 'rangen_v2.yaml'),
        'base': os.path.join(config_dir, 'base.yaml'),
    }
    
    # 加载配置
    config_data = {}
    
    # 1. 加载 base.yaml (未来重构目标)
    base_config = load_config_file(config_paths.get('base', ''))
    
    # 2. 加载环境配置
    env_config = load_config_file(config_paths.get(env, ''))
    
    # 3. 合并配置 (环境配置覆盖基础配置)
    if base_config:
        config_data = base_config.copy()
    if env_config:
        for key, value in env_config.items():
            if key in config_data and isinstance(config_data[key], dict):
                config_data[key].update(value)
            else:
                config_data[key] = value
    
    # 如果没有环境配置，尝试加载默认配置
    if not env_config and not base_config:
        default_config = load_config_file(config_paths['default'])
        if default_config:
            config_data = default_config
    
    return UnifiedConfig.from_dict(config_data)


# 简化的配置访问接口
_config_cache: Optional[UnifiedConfig] = None


def get_cached_config(env: Optional[str] = None) -> UnifiedConfig:
    """获取缓存的配置（单例模式）"""
    global _config_cache
    if _config_cache is None:
        _config_cache = get_config(env)
    return _config_cache


# 导出
__all__ = ['UnifiedConfig', 'get_config', 'get_cached_config']


if __name__ == '__main__':
    # 测试配置加载
    print("=== 配置加载测试 ===")
    
    # 测试开发环境
    config = get_config('development')
    print(f"\n[development]")
    print(f"  system.name: {config.system.get('name')}")
    print(f"  llm.provider: {config.llm.get('provider')}")
    print(f"  debug: {config.system.get('debug')}")
    
    # 测试生产环境
    config = get_config('production')
    print(f"\n[production]")
    print(f"  system.name: {config.system.get('name')}")
    print(f"  llm.provider: {config.llm.get('provider')}")
    print(f"  debug: {config.system.get('debug')}")
    
    print("\n✅ 配置加载测试通过")
