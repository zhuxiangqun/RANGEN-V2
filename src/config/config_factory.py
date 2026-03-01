#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置工厂模块
提供统一的配置创建和管理功能
"""

import os
import logging
import time
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class ConfigFactory(ABC):
    """配置工厂基类"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def create_config(self, config_type: str) -> Dict[str, Any]:
        """创建配置"""
        pass
    
    def _create_database_config(self) -> Dict[str, Any]:
        """创建数据库配置"""
        return {
            "host": "localhost",
            "port": 5432,
            "database": "rangen_db",
            "username": "rangen_user",
            "password": "rangen_pass"
        }
    
    def _create_api_config(self) -> Dict[str, Any]:
        """创建API配置"""
        return {
            "base_url": "http://localhost:8000",
            "timeout": 30,
            "retry_count": 3
        }
    
    def _create_cache_config(self) -> Dict[str, Any]:
        """创建缓存配置"""
        return {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "ttl": 3600
        }
    
    def _create_logging_config(self) -> Dict[str, Any]:
        """创建日志配置"""
        return {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "rangen.log"
        }


class DatabaseConfigFactory(ConfigFactory):
    """数据库配置工厂"""
    
    def create_config(self, config_type: str) -> Dict[str, Any]:
        """创建数据库配置"""
        try:
            if config_type == "postgresql":
                return {
                    "host": os.getenv("POSTGRES_HOST", "localhost"),
                    "port": int(os.getenv("POSTGRES_PORT", "5432")),
                    "database": os.getenv("POSTGRES_DB", "rangen_db"),
                    "username": os.getenv("POSTGRES_USER", "rangen_user"),
                    "password": os.getenv("POSTGRES_PASSWORD", "rangen_pass"),
                    "pool_size": int(os.getenv("DB_POOL_SIZE", "10")),
                    "max_connections": int(os.getenv("DB_MAX_CONNECTIONS", "20")),
                }
            elif config_type == "mysql":
                return {
                    "host": os.getenv("MYSQL_HOST", "localhost"),
                    "port": int(os.getenv("MYSQL_PORT", "3306")),
                    "database": os.getenv("MYSQL_DB", "rangen_db"),
                    "username": os.getenv("MYSQL_USER", "rangen_user"),
                    "password": os.getenv("MYSQL_PASSWORD", "rangen_pass"),
                    "charset": "utf8mb4",
                    "pool_size": int(os.getenv("DB_POOL_SIZE", "10"))
                }
            elif config_type == "sqlite":
                return {
                    "database": os.getenv("SQLITE_DB", "rangen.db"),
                    "timeout": int(os.getenv("SQLITE_TIMEOUT", "30")),
                    "check_same_thread": False
                }
            else:
                self.logger.warning(f"不支持的数据库类型: {config_type}")
                return {}
                
        except Exception as e:
            self.logger.error(f"创建数据库配置失败: {e}")
            return {}


class APIConfigFactory(ConfigFactory):
    """API配置工厂"""
    
    def create_config(self, config_type: str) -> Dict[str, Any]:
        """创建API配置"""
        try:
            if config_type == "fastapi":
                return {
                    "host": os.getenv("API_HOST", "0.0.0.0"),
                    "port": int(os.getenv("API_PORT", "8000")),
                    "debug": os.getenv("API_DEBUG", "false").lower() == "true",
                    "reload": os.getenv("API_RELOAD", "false").lower() == "true",
                    "workers": int(os.getenv("API_WORKERS", "1")),
                    "timeout": int(os.getenv("API_TIMEOUT", "30"))
                }
            elif config_type == "flask":
                return {
                    "host": os.getenv("API_HOST", "0.0.0.0"),
                    "port": int(os.getenv("API_PORT", "8000")),
                    "debug": os.getenv("API_DEBUG", "false").lower() == "true",
                    "threaded": True,
                    "timeout": int(os.getenv("API_TIMEOUT", "30"))
                }
            else:
                self.logger.warning(f"不支持的API类型: {config_type}")
                return {}
                
        except Exception as e:
            self.logger.error(f"创建API配置失败: {e}")
            return {}


class CacheConfigFactory(ConfigFactory):
    """缓存配置工厂"""
    
    def create_config(self, config_type: str) -> Dict[str, Any]:
        """创建缓存配置"""
        try:
            if config_type == "redis":
                return {
                    "host": os.getenv("REDIS_HOST", "localhost"),
                    "port": int(os.getenv("REDIS_PORT", "6379")),
                    "password": os.getenv("REDIS_PASSWORD", ""),
                    "db": int(os.getenv("REDIS_DB", "0")),
                    "timeout": int(os.getenv("REDIS_TIMEOUT", "5")),
                    "max_connections": int(os.getenv("REDIS_MAX_CONNECTIONS", "100")),
                }
            elif config_type == "memory":
                return {
                "max_size": int(os.getenv("MEMORY_CACHE_SIZE", "1000")),
                "ttl": int(os.getenv("MEMORY_CACHE_TTL", "3600")),
                    "cleanup_interval": int(os.getenv("MEMORY_CACHE_CLEANUP", "300"))
                }
            else:
                self.logger.warning(f"不支持的缓存类型: {config_type}")
                return {}
                
        except Exception as e:
            self.logger.error(f"创建缓存配置失败: {e}")
            return {}


class LoggingConfigFactory(ConfigFactory):
    """日志配置工厂"""
    
    def create_config(self, config_type: str) -> Dict[str, Any]:
        """创建日志配置"""
        try:
            if config_type == "file":
                return {
                    "level": os.getenv("LOG_LEVEL", "INFO"),
                    "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                    "filename": os.getenv("LOG_FILE", os.getenv("RANGEN_LOG_PATH", "rangen.log")),
                    "max_bytes": int(os.getenv("LOG_MAX_BYTES", "10485760")),  # 10MB
                    "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
                }
            elif config_type == "console":
                return {
                    "level": os.getenv("LOG_LEVEL", "INFO"),
                    "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                    "stream": "stdout"
                }
            else:
                self.logger.warning(f"不支持的日志类型: {config_type}")
                return {}
                
        except Exception as e:
            self.logger.error(f"创建日志配置失败: {e}")
            return {}


class ConfigManager:
    """配置管理器 - 增强版，支持动态配置和硬编码消除"""
    
    def __init__(self):
        self.logger = logging.getLogger("ConfigManager")
        self.factories = {
            "database": DatabaseConfigFactory(),
            "api": APIConfigFactory(),
            "cache": CacheConfigFactory(),
            "logging": LoggingConfigFactory()
        }
        self.configs = {}
        
        # 新增：动态配置支持
        self.dynamic_configs = {}
        self._load_dynamic_configs()
    
    def _load_dynamic_configs(self):
        """加载动态配置，消除硬编码"""
        try:
            # 使用统一配置中心获取环境变量配置
            from src.utils.unified_centers import get_unified_config_center
            config_center = get_unified_config_center()
            
            # 系统配置 - 从统一配置中心获取
            self.dynamic_configs['system'] = {
                'session_timeout': config_center.get_env_config('system', 'SESSION_TIMEOUT', 3600),
                'request_timeout': config_center.get_env_config('system', 'REQUEST_TIMEOUT', 30),
                'max_threads': config_center.get_env_config('system', 'MAX_THREADS', 4),
                'max_connections': config_center.get_env_config('system', 'MAX_CONNECTIONS', 100),
                'max_queue_size': config_center.get_env_config('system', 'MAX_QUEUE_SIZE', 1000),
                'max_query_length': config_center.get_env_config('system', 'MAX_QUERY_LENGTH', 100),
                'max_cache_size': config_center.get_env_config('system', 'MAX_CACHE_SIZE', 100),
                'default_port': config_center.get_env_config('system', 'DEFAULT_PORT', 8000),
                'default_log_level': config_center.get_env_config('system', 'DEFAULT_LOG_LEVEL', 'INFO'),
                'chunk_size': config_center.get_env_config('system', 'CHUNK_SIZE', 1024),
                'connection_timeout': config_center.get_env_config('system', 'CONNECTION_TIMEOUT', 10),
                'metrics_interval': config_center.get_env_config('system', 'METRICS_INTERVAL', 60),
                'cache_ttl_seconds': config_center.get_env_config('system', 'CACHE_TTL_SECONDS', 3600)
            }
            
            # AI/ML配置 - 从统一配置中心获取
            self.dynamic_configs['ai_ml'] = {
                'model_max_length': config_center.get_env_config('ai_ml', 'MODEL_MAX_LENGTH', 256),
                'model_embedding_dim': config_center.get_env_config('ai_ml', 'MODEL_EMBEDDING_DIM', 384),
                'vector_dimension': config_center.get_env_config('ai_ml', 'VECTOR_DIMENSION', 384),
                'nprobe': config_center.get_env_config('ai_ml', 'NPROBE', 10),
                'learning_rate': config_center.get_env_config('ai_ml', 'LEARNING_RATE', 0.001),
                'similarity_threshold': config_center.get_env_config('ai_ml', 'SIMILARITY_THRESHOLD', 0.6),
                'alert_threshold': config_center.get_env_config('ai_ml', 'ALERT_THRESHOLD', 0.95),
                'max_evaluation_items': config_center.get_env_config('system', 'MAX_EVALUATION_ITEMS', 1000),
                'batch_size': config_center.get_env_config('ai_ml', 'BATCH_SIZE', 32)
            }
            
            # 路径配置 - 从统一配置中心获取
            self.dynamic_configs['paths'] = {
                'faiss_index_path': config_center.get_env_config('paths', 'FAISS_INDEX_PATH', 'data/faiss_memory/faiss_index.bin'),
                'data_directory': config_center.get_env_config('paths', 'DATA_DIRECTORY', 'data'),
                'log_directory': config_center.get_env_config('paths', 'LOG_DIRECTORY', 'logs'),
                'config_directory': config_center.get_env_config('paths', 'CONFIG_DIRECTORY', 'config'),
                'cache_directory': config_center.get_env_config('paths', 'CACHE_DIRECTORY', 'cache')
            }
            
            # URL配置 - 从统一配置中心获取
            self.dynamic_configs['urls'] = {
                'api_base_url': config_center.get_env_config('urls', 'API_BASE_URL', 'http://localhost:8000'),
                'llm_api_url': config_center.get_env_config('urls', 'LLM_API_URL', 'https://api.openai.com/v1'),
                'vector_db_url': config_center.get_env_config('urls', 'VECTOR_DB_URL', 'http://localhost:8080'),
                'monitoring_url': config_center.get_env_config('urls', 'MONITORING_URL', 'http://localhost:9090')
            }
            
            self.logger.info("动态配置加载完成（使用统一配置中心）")
        except Exception as e:
            self.logger.error(f"动态配置加载失败: {e}")
    
    def get_dynamic_config(self, category: str, key: str, default: Any = None) -> Any:
        """获取动态配置值"""
        try:
            if category in self.dynamic_configs:
                return self.dynamic_configs[category].get(key, default)
            return default
        except Exception as e:
            self.logger.error(f"获取动态配置失败 {category}.{key}: {e}")
            return default
    
    def set_dynamic_config(self, category: str, key: str, value: Any) -> None:
        """设置动态配置值"""
        try:
            if category not in self.dynamic_configs:
                self.dynamic_configs[category] = {}
            self.dynamic_configs[category][key] = value
            self.logger.debug(f"设置动态配置 {category}.{key} = {value}")
        except Exception as e:
            self.logger.error(f"设置动态配置失败 {category}.{key}: {e}")
    
    def get_all_dynamic_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有动态配置"""
        return self.dynamic_configs.copy()
    
    def get_config(self, factory_type: str, config_type: str) -> Dict[str, Any]:
        """获取配置"""
        try:
            if factory_type not in self.factories:
                self.logger.error(f"不支持的工厂类型: {factory_type}")
                return {}
            
            factory = self.factories[factory_type]
            config = factory.create_config(config_type)
            
            # 缓存配置
            cache_key = f"{factory_type}_{config_type}"
            self.configs[cache_key] = config
            
            self.logger.info(f"获取配置: {factory_type} - {config_type}")
            return config
            
        except Exception as e:
            self.logger.error(f"获取配置失败: {e}")
            return {}
    
    def get_cached_config(self, factory_type: str, config_type: str) -> Optional[Dict[str, Any]]:
        """获取缓存的配置"""
        cache_key = f"{factory_type}_{config_type}"
        return self.configs.get(cache_key)
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self.configs.clear()
        self.logger.info("配置缓存已清除")
    
    def list_available_configs(self) -> Dict[str, list]:
        """列出可用的配置类型"""
        return {
            "database": ["postgresql", "mysql", "sqlite"],
            "api": ["fastapi", "flask"],
            "cache": ["redis", "memory"],
            "logging": ["file", "console"]
        }


# 配置工厂 - 核心配置管理组件
# 提供统一的配置管理和验证功能