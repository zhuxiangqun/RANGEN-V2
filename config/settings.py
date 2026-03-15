#!/usr/bin/env python3
"""
系统配置文件
包含所有配置参数
"""

import os
from typing import Any, Dict, List

class Settings:
    """系统设置"""

    # 基础配置
    PROJECT_NAME = "Deep Research Agent System"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # LLM配置 - 只使用DeepSeek作为外部LLM
    # OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # 已废弃：外部LLM只使用DeepSeek
    # ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")  # 已废弃：外部LLM只使用DeepSeek
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "deepseek-reasoner")

    # 向量数据库配置
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
    VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))

    # 搜索API配置
    SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # 数据库配置
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///research.db")

    # 智能体配置
    AGENT_CONFIG = {
        "lead_researcher": {
            "max_iterations": 5,
            "timeout": 600,
            "temperature": 0.1
        },
        "search_agent": {
            "max_iterations": 3,
            "timeout": 120,
            "temperature": 0.1
        },
        "citation_agent": {
            "max_iterations": 2,
            "timeout": 60,
            "temperature": 0.1
        },
        "analysis_agent": {
            "max_iterations": 3,
            "timeout": 180,
            "temperature": 0.1
        },
        "validation_agent": {
            "max_iterations": 2,
            "timeout": 120,
            "temperature": 0.1
        }
    }

    # 记忆系统配置
    MEMORY_CONFIG = {
        "max_items": 10000,
        "similarity_threshold": 0.6,
        "retrieval_top_k": 5
    }

    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 性能配置
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    TASK_TIMEOUT = int(os.getenv("TASK_TIMEOUT", "300"))

    # 安全配置
    ALLOWED_DOMAINS = [
        # "openai.com",  # 已废弃：外部LLM只使用DeepSeek
        # "anthropic.com",  # 已废弃：外部LLM只使用DeepSeek
        "google.com",
        "microsoft.com",
        "github.com",
        "arxiv.org",
        "researchgate.net"
    ]

    # 评估配置
    EVALUATION_CONFIG = {
        "min_accuracy": get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
        "min_citations": 3,
        "max_execution_time": 300
    }

    @classmethod
    def get_agent_config(cls, agent_name: str) -> Dict[str, Any]:
        """获取智能体配置"""
        return cls.AGENT_CONFIG.get(agent_name, {})

    @classmethod
    def validate_config(cls) -> bool:
        """验证配置"""
        required_keys = [
            # 不再强制要求外部LLM API密钥，允许使用本地模型
        ]

        missing_keys = []
        for key in required_keys:
            if not getattr(cls, key):
                missing_keys.append(key)

        if missing_keys:
            print(f"缺少必要的配置: {missing_keys}")
            return False

        return True

    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "project_name": cls.PROJECT_NAME,
            "version": cls.VERSION,
            "debug": cls.DEBUG,
            "default_model": cls.DEFAULT_MODEL,
            "vector_dimension": cls.VECTOR_DIMENSION,
            "log_level": cls.LOG_LEVEL,
            "max_concurrent_tasks": cls.MAX_CONCURRENT_TASKS,
            "task_timeout": cls.TASK_TIMEOUT
        }

# 创建全局设置实例
settings = Settings()