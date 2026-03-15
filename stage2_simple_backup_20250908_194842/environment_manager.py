"""
环境管理器
统一管理环境变量和系统配置，避免硬编码的环境依赖
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EnvironmentManager:
    """环境管理器"""

    def __init__(self):
        self.env_vars: Dict[str, Any] = {}
        self.default_values: Dict[str, Any] = {}
        self._load_defaults()

    def _load_defaults(self):
        """加载默认环境配置"""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
        from config.defaults import DEFAULT_NETWORK, DEFAULT_PATHS, DEFAULT_VALUES

        # 网络配置
        for key, value in DEFAULT_NETWORK.items():
            env_key = f"APP_{key.upper()}"
            self.default_values[env_key] = value

        # 路径配置
        for key, value in DEFAULT_PATHS.items():
            env_key = f"APP_{key.upper()}"
            self.default_values[env_key] = value

        # 系统配置
        for key, value in DEFAULT_VALUES.items():
            env_key = f"APP_{key.upper()}"
            self.default_values[env_key] = value

    def get_env(self, key: str, default: Any = None) -> Any:
        """获取环境变量，支持默认值"""
        env_key = f"APP_{key.upper()}"
        value = os.getenv(env_key)

        if value is None:
            # 尝试从默认值获取
            if env_key in self.default_values:
                value = self.default_values[env_key]
            elif default is not None:
                value = default
            else:
                return None

        # 类型转换
        return self._convert_value(value)

    def set_env(self, key: str, value: Any):
        """设置环境变量"""
        env_key = f"APP_{key.upper()}"
        os.environ[env_key] = str(value)
        self.env_vars[env_key] = value

    def get_network_config(self) -> Dict[str, Any]:
        """获取网络配置"""
        return {
            "mirror_urls": self.get_env("mirror_urls", []),
            "huggingface_endpoint": self.get_env("huggingface_endpoint"),
            "api_url": self.get_env("api_url"),
            "retry_attempts": self.get_env("retry_attempts", config.DEFAULT_MAX_RETRIES),
        }

    def get_path_config(self) -> Dict[str, Any]:
        """获取路径配置"""
        return {
            "cache_folder": self.get_env("cache_folder", "./models/cache"),
            "model_dir": self.get_env("model_dir", "./models"),
            "log_dir": self.get_env("log_dir", "./logs"),
            "config_dir": self.get_env("config_dir", "./config"),
        }

    def get_system_config(self) -> Dict[str, Any]:
        """获取系统配置"""
        return {
            "max_workers": self.get_env("max_workers", 4),
            "debug_mode": self.get_env("debug_mode", False),
            "log_level": self.get_env("log_level", "INFO"),
            "timeout": self.get_env("timeout", config.DEFAULT_TIMEOUT),
        }

    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return {
            "primary_model": self.get_env("primary_model", "all-MiniLM-L6-v2"),
            "fallback_model": self.get_env("fallback_model", "paraphrase-MiniLM-L6-v2"),
            "max_seq_length": self.get_env("max_seq_length", config.DEFAULT_TOP_K12),
            "learning_rate": self.get_env("learning_rate", 0.01),
        }

    def _convert_value(self, value: str) -> Any:
        """转换字符串值为合适的数据类型"""
        # 确保是字符串类型
        if not isinstance(value, str):
            return value

        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # 整数
        try:
            if '.' not in value:
                return int(value)
        except ValueError:
            pass

        # 浮点数
        try:
            return float(value)
        except ValueError:
            pass

        # 列表（逗号分隔）
        if ',' in value:
            return [item.strip() for item in value.split(',')]

        # 字符串
        return value

    def load_from_file(self, file_path: str):
        """从文件加载环境配置"""
        if not os.path.exists(file_path):
            logger.warning(f"环境配置文件不存在: {file_path}")
            return

        try:
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for key, value in config.items():
                env_key = f"APP_{key.upper()}"
                os.environ[env_key] = str(value)
                self.env_vars[env_key] = value

            logger.info(f"从文件加载环境配置: {file_path}")

        except Exception as e:
            logger.error(f"加载环境配置文件失败: {e}")

    def save_to_file(self, file_path: str):
        """保存当前环境配置到文件"""
        try:
            config = {}
            for env_key, value in self.env_vars.items():
                if env_key.startswith('APP_'):
                    config_key = env_key[4:].lower()  # 移除APP_前缀
                    config[config_key] = value

            import json
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            logger.info(f"保存环境配置到文件: {file_path}")

        except Exception as e:
            logger.error(f"保存环境配置文件失败: {e}")

    def validate_config(self) -> List[str]:
        """验证环境配置"""
        errors = []

        # 检查必要的配置
        required_configs = [
            "cache_folder",
            "model_dir",
            "timeout",
        ]

        for config in required_configs:
            if self.get_env(config) is None:
                errors.append(f"缺少必要配置: {config}")

        # 检查路径是否存在
        paths_to_check = ["cache_folder", "model_dir", "log_dir"]
        for path_key in paths_to_check:
            path_value = self.get_env(path_key)
            if path_value and not os.path.exists(path_value):
                try:
                    os.makedirs(path_value, exist_ok=True)
                    logger.info(f"创建目录: {path_value}")
                except Exception as e:
                    errors.append(f"无法创建目录 {path_value}: {e}")

        return errors


# 全局环境管理器实例
_env_manager = None

def get_environment_manager() -> EnvironmentManager:
    """获取环境管理器实例"""
    global _env_manager
    if _env_manager is None:
        _env_manager = EnvironmentManager()
    return _env_manager
