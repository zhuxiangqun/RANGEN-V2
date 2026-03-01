#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一配置管理系统 - RANGEN V2
提供单例模式、多源配置加载、热重载、线程安全的配置管理
"""

import os
import json
import yaml
import threading
import time
import logging
from typing import Dict, Any, Optional, Union, Callable, List, Type
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
from collections.abc import Mapping
import weakref
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class ConfigSource(Enum):
    """配置源类型"""
    ENVIRONMENT = "environment"
    FILE = "file"
    DEFAULTS = "defaults"


class ConfigFormat(Enum):
    """配置文件格式"""
    JSON = "json"
    YAML = "yaml"
    YML = "yml"


@dataclass
class ConfigMetadata:
    """配置元数据"""
    source: ConfigSource
    last_modified: float
    file_path: Optional[str] = None
    format: Optional[ConfigFormat] = None
    version: str = "1.0.0"
    description: str = ""


@dataclass
class ConfigChangeEvent:
    """配置变更事件"""
    key: str
    old_value: Any
    new_value: Any
    source: ConfigSource
    timestamp: float = field(default_factory=time.time)


class ConfigValidator:
    """配置验证器基类"""
    
    def validate(self, key: str, value: Any) -> tuple[bool, List[str]]:
        """
        验证配置值
        Returns:
            (is_valid, error_messages)
        """
        return True, []


class TypeValidator(ConfigValidator):
    """类型验证器"""
    
    def __init__(self, expected_type: Type):
        self.expected_type = expected_type
    
    def validate(self, key: str, value: Any) -> tuple[bool, List[str]]:
        if not isinstance(value, self.expected_type):
            return False, [f"配置 {key} 期望类型 {self.expected_type.__name__}, 实际类型 {type(value).__name__}"]
        return True, []


class RangeValidator(ConfigValidator):
    """范围验证器"""
    
    def __init__(self, min_val: Any = None, max_val: Any = None):
        self.min_val = min_val
        self.max_val = max_val
    
    def validate(self, key: str, value: Any) -> tuple[bool, List[str]]:
        errors = []
        if self.min_val is not None and value < self.min_val:
            errors.append(f"配置 {key} 值 {value} 小于最小值 {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            errors.append(f"配置 {key} 值 {value} 大于最大值 {self.max_val}")
        return len(errors) == 0, errors


class ConfigFileHandler(FileSystemEventHandler):
    """配置文件变更监听器"""
    
    def __init__(self, config_manager: 'ConfigManager'):
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
    
    def on_modified(self, event):
        if not event.is_directory and event.src_path in self.config_manager._watched_files:
            self.logger.info(f"检测到配置文件变更: {event.src_path}")
            self.config_manager._reload_file(event.src_path)


class ConfigManager:
    """
    统一配置管理器 - 单例模式
    支持多源配置、热重载、线程安全、配置验证
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, config_dir: str = "config"):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_dir: str = "config"):
        if hasattr(self, '_initialized'):
            return
        
        self.config_dir = Path(config_dir)
        self.logger = logging.getLogger(__name__)
        
        # 配置存储
        self._config_data: Dict[str, Any] = {}
        self._config_metadata: Dict[str, ConfigMetadata] = {}
        
        # 线程安全锁
        self._config_lock = threading.RLock()
        self._listener_lock = threading.Lock()
        
        # 配置变更监听器
        self._change_listeners: List[Callable[[ConfigChangeEvent], None]] = []
        
        # 配置验证器
        self._validators: Dict[str, List[ConfigValidator]] = {}
        
        # 文件监听
        self._watched_files: set[str] = set()
        self._file_observer: Optional[Observer] = None
        
        # 环境变量前缀
        self.env_prefix = "RANGEN_"
        
        # 初始化
        self._initialized = True
        self._ensure_config_dir()
        self._load_all_configs()
        self._setup_file_watcher()
    
    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "sections").mkdir(exist_ok=True)
    
    def _load_all_configs(self):
        """加载所有配置源"""
        with self._config_lock:
            # 1. 加载默认配置
            self._load_default_configs()
            
            # 2. 加载文件配置
            self._load_file_configs()
            
            # 3. 加载环境变量配置
            self._load_environment_configs()
            
            self.logger.info(f"配置加载完成，共加载 {len(self._config_data)} 个配置项")
    
    def _load_default_configs(self):
        """加载默认配置"""
        default_configs = {
            # 系统配置
            "system.name": "RANGEN V2",
            "system.version": "2.0.0",
            "system.debug_mode": False,
            "system.log_level": "INFO",
            "system.max_concurrent_queries": 3,
            "system.timeout_seconds": 30,
            "system.session_timeout": 3600,
            "system.request_timeout": 30,
            "system.max_threads": 4,
            "system.max_connections": 100,
            "system.max_queue_size": 1000,
            "system.max_query_length": 1000,
            "system.max_cache_size": 100,
            "system.default_port": 8000,
            "system.default_log_level": "INFO",
            "system.chunk_size": 1024,
            "system.connection_timeout": 10,
            "system.metrics_interval": 60,
            "system.cache_ttl_seconds": 3600,
            
            # AI/ML 配置
            "ai_ml.model_max_length": 256,
            "ai_ml.model_embedding_dim": 384,
            "ai_ml.vector_dimension": 384,
            "ai_ml.nprobe": 10,
            "ai_ml.learning_rate": 0.001,
            "ai_ml.similarity_threshold": 0.6,
            "ai_ml.alert_threshold": 0.95,
            "ai_ml.batch_size": 32,
            "ai_ml.max_evaluation_items": 1000,
            
            # 路径配置
            "paths.data_directory": "data",
            "paths.log_directory": "logs",
            "paths.config_directory": "config",
            "paths.cache_directory": "cache",
            "paths.faiss_index_path": "data/faiss_memory/faiss_index.bin",
            
            # URL 配置
            "urls.api_base_url": "http://localhost:8000",
            "urls.llm_api_url": "https://api.openai.com/v1",
            "urls.vector_db_url": "http://localhost:8080",
            "urls.monitoring_url": "http://localhost:9090",
            
            # 安全配置
            "security.enable_validation": True,
            "security.max_input_length": 1000,
            "security.allowed_file_types": [".txt", ".json", ".csv"],
            "security.rate_limit_per_minute": 100,
            "security.enable_encryption": True,
            
            # 性能配置
            "performance.enable_monitoring": True,
            "performance.metrics_interval": 60,
            "performance.memory_threshold": 0.8,
            "performance.cpu_threshold": 0.8,
            "performance.enable_profiling": False,
            
            # 数据管理配置
            "data_management.cache_size": 1000,
            "data_management.cache_ttl": 3600,
            "data_management.enable_persistence": True,
            "data_management.backup_interval": 86400,
            "data_management.max_file_size": 10485760,  # 10MB
        }
        
        for key, value in default_configs.items():
            self._set_config_value(key, value, ConfigSource.DEFAULTS)
    
    def _load_file_configs(self):
        """加载文件配置"""
        # 加载主配置文件
        main_config_files = [
            self.config_dir / "config.json",
            self.config_dir / "config.yaml",
            self.config_dir / "config.yml",
            self.config_dir / "rangen_v2.yaml",
            self.config_dir / "rangen_v2.yml",
        ]
        
        for config_file in main_config_files:
            if config_file.exists():
                self._load_config_file(config_file)
                break
        
        # 加载配置节文件
        sections_dir = self.config_dir / "sections"
        if sections_dir.exists():
            for config_file in sections_dir.glob("*"):
                if config_file.is_file() and config_file.suffix in ['.json', '.yaml', '.yml']:
                    self._load_config_file(config_file)
    
    def _load_config_file(self, file_path: Path):
        """加载单个配置文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.json':
                    data = json.load(f)
                else:  # yaml/yml
                    data = yaml.safe_load(f) or {}
            
            # 递归处理配置数据
            self._process_config_data(data, ConfigSource.FILE, str(file_path))
            
            # 添加到文件监听
            self._watched_files.add(str(file_path))
            
            self.logger.info(f"加载配置文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败 {file_path}: {e}")
    
    def _process_config_data(self, data: Dict[str, Any], source: ConfigSource, file_path: str = None, prefix: str = ""):
        """递归处理配置数据"""
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, Mapping):
                # 递归处理嵌套字典
                self._process_config_data(value, source, file_path, full_key)
            else:
                # 设置配置值
                self._set_config_value(full_key, value, source, file_path)
    
    def _load_environment_configs(self):
        """加载环境变量配置"""
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                # 移除前缀并转换为小写
                config_key = key[len(self.env_prefix):].lower()
                
                # 尝试转换数据类型
                converted_value = self._convert_env_value(value)
                
                self._set_config_value(config_key, converted_value, ConfigSource.ENVIRONMENT)
    
    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值类型"""
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON 数组或对象
        if value.startswith(('[', '{')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 默认返回字符串
        return value
    
    def _set_config_value(self, key: str, value: Any, source: ConfigSource, file_path: str = None):
        """内部设置配置值"""
        old_value = self._config_data.get(key)
        
        # 验证配置值（只对非默认配置进行验证，避免默认配置被拒绝）
        if source != ConfigSource.DEFAULTS:
            is_valid, errors = self._validate_config(key, value)
            if not is_valid:
                self.logger.error(f"配置验证失败 {key}: {', '.join(errors)}")
                return False
        
        # 设置值和元数据
        self._config_data[key] = value
        self._config_metadata[key] = ConfigMetadata(
            source=source,
            last_modified=time.time(),
            file_path=file_path,
            format=ConfigFormat.JSON if file_path and file_path.endswith('.json') else ConfigFormat.YAML
        )
        
        # 触发变更事件
        if old_value != value:
            self._notify_change_listeners(ConfigChangeEvent(
                key=key,
                old_value=old_value,
                new_value=value,
                source=source
            ))
        
        return True
    
    def _validate_config(self, key: str, value: Any) -> tuple[bool, List[str]]:
        """验证配置值"""
        all_errors = []
        
        # 获取匹配的验证器
        for pattern, validators in self._validators.items():
            if self._key_matches_pattern(key, pattern):
                for validator in validators:
                    is_valid, errors = validator.validate(key, value)
                    if not is_valid:
                        all_errors.extend(errors)
        
        return len(all_errors) == 0, all_errors
    
    def _key_matches_pattern(self, key: str, pattern: str) -> bool:
        """检查配置键是否匹配模式"""
        if pattern == key:
            return True
        
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return key.startswith(prefix)
        
        return False
    
    def _setup_file_watcher(self):
        """设置文件监听器"""
        try:
            self._file_observer = Observer()
            handler = ConfigFileHandler(self)
            self._file_observer.schedule(handler, str(self.config_dir), recursive=True)
            self._file_observer.start()
            self.logger.info("配置文件监听器已启动")
        except Exception as e:
            self.logger.warning(f"无法启动文件监听器: {e}")
    
    def _reload_file(self, file_path: str):
        """重新加载配置文件"""
        try:
            # 清除来自该文件的配置
            keys_to_remove = []
            for key, metadata in self._config_metadata.items():
                if metadata.file_path == file_path:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._config_data[key]
                del self._config_metadata[key]
            
            # 重新加载文件
            self._load_config_file(Path(file_path))
            
            self.logger.info(f"重新加载配置文件: {file_path}")
            
        except Exception as e:
            self.logger.error(f"重新加载配置文件失败 {file_path}: {e}")
    
    def _notify_change_listeners(self, event: ConfigChangeEvent):
        """通知配置变更监听器"""
        with self._listener_lock:
            for listener in self._change_listeners:
                try:
                    listener(event)
                except Exception as e:
                    self.logger.error(f"配置变更监听器执行失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
        Returns:
            配置值
        """
        with self._config_lock:
            return self._config_data.get(key, default)
    
    def get_section(self, prefix: str) -> Dict[str, Any]:
        """
        获取配置节
        Args:
            prefix: 配置节前缀
        Returns:
            配置节字典
        """
        with self._config_lock:
            section = {}
            for key, value in self._config_data.items():
                if key.startswith(prefix + "."):
                    section_key = key[len(prefix) + 1:]
                    section[section_key] = value
            return section
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.DEFAULTS) -> bool:
        """
        设置配置值
        Args:
            key: 配置键
            value: 配置值
            source: 配置源
        Returns:
            是否设置成功
        """
        with self._config_lock:
            try:
                return self._set_config_value(key, value, source)
            except Exception as e:
                self.logger.error(f"设置配置失败 {key}: {e}")
                return False
    
    def update(self, config_dict: Dict[str, Any], source: ConfigSource = ConfigSource.DEFAULTS) -> bool:
        """
        批量更新配置
        Args:
            config_dict: 配置字典
            source: 配置源
        Returns:
            是否更新成功
        """
        with self._config_lock:
            try:
                self._process_config_data(config_dict, source)
                return True
            except Exception as e:
                self.logger.error(f"批量更新配置失败: {e}")
                return False
    
    def add_validator(self, key_pattern: str, validator: ConfigValidator):
        """
        添加配置验证器
        Args:
            key_pattern: 配置键模式
            validator: 验证器
        """
        if key_pattern not in self._validators:
            self._validators[key_pattern] = []
        self._validators[key_pattern].append(validator)
    
    def add_change_listener(self, listener: Callable[[ConfigChangeEvent], None]):
        """
        添加配置变更监听器
        Args:
            listener: 监听器函数
        """
        with self._listener_lock:
            self._change_listeners.append(listener)
    
    def remove_change_listener(self, listener: Callable[[ConfigChangeEvent], None]):
        """
        移除配置变更监听器
        Args:
            listener: 监听器函数
        """
        with self._listener_lock:
            if listener in self._change_listeners:
                self._change_listeners.remove(listener)
    
    def get_metadata(self, key: str) -> Optional[ConfigMetadata]:
        """
        获取配置元数据
        Args:
            key: 配置键
        Returns:
            配置元数据
        """
        with self._config_lock:
            return self._config_metadata.get(key)
    
    def list_keys(self, prefix: str = None) -> List[str]:
        """
        列出配置键
        Args:
            prefix: 前缀过滤
        Returns:
            配置键列表
        """
        with self._config_lock:
            keys = list(self._config_data.keys())
            if prefix:
                keys = [key for key in keys if key.startswith(prefix)]
            return sorted(keys)
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置
        Returns:
            所有配置的字典
        """
        with self._config_lock:
            return self._config_data.copy()
    
    def save_config(self, file_path: str, format: ConfigFormat = ConfigFormat.YAML):
        """
        保存配置到文件
        Args:
            file_path: 文件路径
            format: 文件格式
        """
        with self._config_lock:
            try:
                # 转换为嵌套字典格式
                nested_config = {}
                for key, value in self._config_data.items():
                    self._set_nested_value(nested_config, key, value)
                
                # 保存文件
                file_path = Path(file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    if format == ConfigFormat.JSON:
                        json.dump(nested_config, f, ensure_ascii=False, indent=2)
                    else:  # YAML
                        yaml.dump(nested_config, f, default_flow_style=False, allow_unicode=True)
                
                self.logger.info(f"配置已保存到: {file_path}")
                
            except Exception as e:
                self.logger.error(f"保存配置失败: {e}")
    
    def _set_nested_value(self, nested_dict: Dict[str, Any], key: str, value: Any):
        """设置嵌套字典值"""
        keys = key.split('.')
        current = nested_dict
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def reload(self):
        """重新加载所有配置"""
        self.logger.info("重新加载配置...")
        with self._config_lock:
            self._config_data.clear()
            self._config_metadata.clear()
            self._load_all_configs()
    
    def validate_all(self) -> Dict[str, List[str]]:
        """
        验证所有配置
        Returns:
            验证错误字典 {key: [errors]}
        """
        with self._config_lock:
            all_errors = {}
            
            for key, value in self._config_data.items():
                is_valid, errors = self._validate_config(key, value)
                if not is_valid:
                    all_errors[key] = errors
            
            return all_errors
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        Returns:
            配置摘要信息
        """
        with self._config_lock:
            source_counts = {}
            for metadata in self._config_metadata.values():
                source_counts[metadata.source.value] = source_counts.get(metadata.source.value, 0) + 1
            
            return {
                "total_keys": len(self._config_data),
                "source_distribution": source_counts,
                "watched_files": len(self._watched_files),
                "validators": len(self._validators),
                "change_listeners": len(self._change_listeners),
                "config_dir": str(self.config_dir),
                "env_prefix": self.env_prefix,
            }
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
    
    def cleanup(self):
        """清理资源"""
        if self._file_observer:
            self._file_observer.stop()
            self._file_observer.join()
        
        with self._listener_lock:
            self._change_listeners.clear()


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None
_config_lock = threading.Lock()


def get_config_manager(config_dir: str = "config") -> ConfigManager:
    """
    获取全局配置管理器实例
    Args:
        config_dir: 配置目录
    Returns:
        配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        with _config_lock:
            if _config_manager is None:
                _config_manager = ConfigManager(config_dir)
    
    return _config_manager


def get_config(key: str, default: Any = None) -> Any:
    """
    便捷函数：获取配置值
    Args:
        key: 配置键
        default: 默认值
    Returns:
        配置值
    """
    return get_config_manager().get(key, default)


def set_config(key: str, value: Any, source: ConfigSource = ConfigSource.DEFAULTS) -> bool:
    """
    便捷函数：设置配置值
    Args:
        key: 配置键
        value: 配置值
        source: 配置源
    Returns:
        是否设置成功
    """
    return get_config_manager().set(key, value, source)


def get_config_section(prefix: str) -> Dict[str, Any]:
    """
    便捷函数：获取配置节
    Args:
        prefix: 配置节前缀
    Returns:
        配置节字典
    """
    return get_config_manager().get_section(prefix)


# 配置验证器预设
def add_type_validator(key_pattern: str, expected_type: Type):
    """添加类型验证器"""
    get_config_manager().add_validator(key_pattern, TypeValidator(expected_type))


def add_range_validator(key_pattern: str, min_val: Any = None, max_val: Any = None):
    """添加范围验证器"""
    get_config_manager().add_validator(key_pattern, RangeValidator(min_val, max_val))


# 初始化常用验证器
def _setup_default_validators():
    """设置默认验证器"""
    config_manager = get_config_manager()
    
    # 系统配置验证
    config_manager.add_validator("system.max_*", RangeValidator(min_val=1))
    config_manager.add_validator("system.timeout_*", RangeValidator(min_val=1))
    config_manager.add_validator("system.debug_mode", TypeValidator(bool))
    
    # AI/ML 配置验证
    config_manager.add_validator("ai_ml.*_threshold", RangeValidator(min_val=0, max_val=1))
    config_manager.add_validator("ai_ml.learning_rate", RangeValidator(min_val=0, max_val=1))
    config_manager.add_validator("ai_ml.*_dim", RangeValidator(min_val=1))
    config_manager.add_validator("ai_ml.batch_size", RangeValidator(min_val=1))
    
    # 安全配置验证
    config_manager.add_validator("security.max_*", RangeValidator(min_val=1))
    config_manager.add_validator("security.rate_limit_*", RangeValidator(min_val=1))
    config_manager.add_validator("security.enable_*", TypeValidator(bool))
    
    # 性能配置验证
    config_manager.add_validator("performance.*_threshold", RangeValidator(min_val=0, max_val=1))
    config_manager.add_validator("performance.*_interval", RangeValidator(min_val=1))
    config_manager.add_validator("performance.enable_*", TypeValidator(bool))


# 自动设置默认验证器
_setup_default_validators()