"""
配置管理器

负责加载、验证和管理生产环境配置
支持YAML配置、环境变量覆盖、配置热重载等功能
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


class ConfigLoader(ABC):
    """配置加载器抽象基类"""

    @abstractmethod
    def load(self, source: str) -> Dict[str, Any]:
        """加载配置"""
        pass

    @abstractmethod
    def supports(self, source: str) -> bool:
        """判断是否支持该配置源"""
        pass


class YAMLConfigLoader(ConfigLoader):
    """YAML配置加载器"""

    def supports(self, source: str) -> bool:
        """支持.yaml和.yml文件"""
        return source.endswith(('.yaml', '.yml'))

    def load(self, source: str) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info(f"✅ YAML配置加载成功: {source}")
                return config or {}
        except FileNotFoundError:
            logger.error(f"❌ 配置文件不存在: {source}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"❌ YAML配置解析失败: {e}")
            return {}
        except Exception as e:
            logger.error(f"❌ 配置加载异常: {e}")
            return {}


class EnvironmentConfigLoader(ConfigLoader):
    """环境变量配置加载器"""

    def supports(self, source: str) -> bool:
        """支持env标识"""
        return source == "env" or source.startswith("env:")

    def load(self, source: str) -> Dict[str, Any]:
        """从环境变量加载配置"""
        config = {}

        # 如果指定了前缀，只加载带前缀的环境变量
        prefix = ""
        if ":" in source:
            prefix = source.split(":", 1)[1]

        for key, value in os.environ.items():
            if prefix and key.startswith(prefix):
                # 移除前缀
                config_key = key[len(prefix):].lstrip("_")
            elif not prefix:
                # 没有前缀，全部加载
                config_key = key
            else:
                continue

            # 尝试转换类型
            config_value = self._convert_value(value)
            self._set_nested_value(config, config_key, config_value)

        logger.info(f"✅ 环境变量配置加载完成，加载了 {len(config)} 个配置项")
        return config

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """转换字符串值为适当的类型"""
        # 布尔值转换
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        if value.lower() in ('false', 'no', '0', 'off'):
            return False

        # 数字转换
        try:
            # 尝试整数
            if '.' not in value:
                return int(value)
            # 尝试浮点数
            return float(value)
        except ValueError:
            pass

        # 字符串原样返回
        return value

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: Any):
        """设置嵌套字典的值"""
        keys = key.split('.')
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value


class ConfigManager:
    """
    配置管理器

    统一管理应用配置，支持多源配置合并、环境变量覆盖、配置验证等
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._config: Dict[str, Any] = {}
        self._loaders: Dict[str, ConfigLoader] = {}
        self._config_sources: List[str] = []

        # 注册内置加载器
        self._register_loader(YAMLConfigLoader())
        self._register_loader(EnvironmentConfigLoader())

    def _register_loader(self, loader: ConfigLoader):
        """注册配置加载器"""
        loader_type = loader.__class__.__name__
        self._loaders[loader_type] = loader

    def load_config(self, sources: Union[str, List[str]], override_env: bool = True):
        """
        加载配置

        Args:
            sources: 配置源列表
            override_env: 是否使用环境变量覆盖
        """
        if isinstance(sources, str):
            sources = [sources]

        self._config_sources = sources

        # 合并所有配置源
        merged_config = {}

        for source in sources:
            config = self._load_from_source(source)
            merged_config = self._deep_merge(merged_config, config)

        # 环境变量覆盖
        if override_env:
            env_config = self._load_from_source("env")
            merged_config = self._deep_merge(merged_config, env_config)

        self._config = merged_config
        self.logger.info(f"✅ 配置加载完成，共 {len(sources)} 个配置源")

        # 验证配置
        self._validate_config()

    def _load_from_source(self, source: str) -> Dict[str, Any]:
        """从配置源加载配置"""
        for loader in self._loaders.values():
            if loader.supports(source):
                return loader.load(source)

        # 如果没有匹配的加载器，尝试作为文件路径
        if Path(source).exists():
            yaml_loader = YAMLConfigLoader()
            return yaml_loader.load(source)

        self.logger.warning(f"⚠️ 不支持的配置源: {source}")
        return {}

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _validate_config(self):
        """验证配置"""
        required_keys = ['system.name', 'system.version', 'workflow.engine']

        for key in required_keys:
            if not self.get(key):
                self.logger.warning(f"⚠️ 缺少必需配置项: {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        支持点分隔的嵌套键，如 "system.name"
        """
        keys = key.split('.')
        value = self._config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        return self.get(section, {})

    def reload_config(self):
        """重新加载配置"""
        if self._config_sources:
            self.load_config(self._config_sources)

    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def export_config(self, format: str = "yaml") -> str:
        """导出配置"""
        if format.lower() == "yaml":
            return yaml.dump(self._config, default_flow_style=False, allow_unicode=True)
        elif format.lower() == "json":
            import json
            return json.dumps(self._config, indent=2, ensure_ascii=False)
        else:
            return str(self._config)


# 全局配置管理器实例
_config_manager_instance = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器实例"""
    global _config_manager_instance
    if _config_manager_instance is None:
        _config_manager_instance = ConfigManager()
    return _config_manager_instance

def init_config(config_sources: Optional[Union[str, List[str]]] = None):
    """
    初始化配置

    Args:
        config_sources: 配置源列表，默认使用生产配置文件
    """
    manager = get_config_manager()

    if config_sources is None:
        # 默认配置源
        config_sources = [
            "config/production_config.yaml",  # 生产配置
            "env"  # 环境变量覆盖
        ]

    try:
        manager.load_config(config_sources)
        logger.info("✅ 配置管理器初始化成功")
    except Exception as e:
        logger.error(f"❌ 配置管理器初始化失败: {e}")
        # 使用空配置继续运行
        manager._config = {}

def get_config(key: str, default: Any = None) -> Any:
    """便捷函数：获取配置值"""
    return get_config_manager().get(key, default)

def set_config(key: str, value: Any):
    """便捷函数：设置配置值"""
    get_config_manager().set(key, value)
