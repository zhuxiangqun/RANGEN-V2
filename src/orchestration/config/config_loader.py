#!/usr/bin/env python3
"""
智能配置加载器 - 解决沙箱环境.env文件访问限制

支持多种配置来源：
1. 环境变量 (最高优先级)
2. .env文件 (标准方式)
3. 默认值 (兜底方案)
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SmartConfigLoader:
    """智能配置加载器，自动适应不同环境"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.project_root = Path(__file__).parent.parent.parent
        self._cache = {}

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值，支持多种来源

        优先级：
        1. 环境变量
        2. .env文件
        3. 默认值
        """
        # 检查缓存
        if key in self._cache:
            return self._cache[key]

        # 1. 优先检查环境变量
        env_value = os.getenv(key)
        if env_value is not None:
            logger.debug(f"✅ 从环境变量获取 {key}")
            self._cache[key] = env_value
            return env_value

        # 2. 尝试从.env文件读取
        file_value = self._load_from_env_file(key)
        if file_value is not None:
            logger.debug(f"✅ 从.env文件获取 {key}")
            self._cache[key] = file_value
            return file_value

        # 3. 使用默认值
        logger.debug(f"⚠️ 使用默认值获取 {key}: {default}")
        self._cache[key] = default
        return default

    def _load_from_env_file(self, key: str) -> Optional[str]:
        """从.env文件加载配置，带错误处理"""
        try:
            env_path = self.project_root / self.env_file
            if not env_path.exists():
                logger.debug(f".env文件不存在: {env_path}")
                return None

            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{key}='):
                        value = line.split('=', 1)[1].strip()
                        # 处理引号包围的值
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                        return value

        except Exception as e:
            logger.debug(f"无法从.env文件读取 {key}: {e}")
            return None

        return None

    def load_all_configs(self, keys: list) -> Dict[str, Any]:
        """批量加载多个配置"""
        configs = {}
        for key in keys:
            configs[key] = self.get_config(key)
        return configs

# 全局配置加载器实例
config_loader = SmartConfigLoader()

def get_api_key(key_name: str, default: str = "") -> str:
    """获取API密钥的便捷方法"""
    return config_loader.get_config(key_name, default)

def get_deepseek_api_key() -> str:
    """获取DeepSeek API密钥"""
    return get_api_key("DEEPSEEK_API_KEY", "")

def get_openai_api_key() -> str:
    """获取OpenAI API密钥"""
    return get_api_key("OPENAI_API_KEY", "")

# 便捷函数
def get_config(key: str, default: Any = None) -> Any:
    """全局配置获取函数"""
    return config_loader.get_config(key, default)
