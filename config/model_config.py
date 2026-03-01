"""
模型配置模块
提供统一的模型配置管理
"""

import os
from typing import Dict, Any, Optional


def get_embedding_config() -> Dict[str, Any]:
    """获取嵌入模型配置"""
    return {
        "model_name": "all-MiniLM-L6-v2",  # 移除sentence-transformers/前缀
        "dimension": 384,
        "device": os.getenv("DEVICE", "cpu"),
        "cache_folder": os.getenv("MODEL_CACHE_DIR", "models/cache"),
        "max_seq_length": 512,
        "normalize_embeddings": True,
        "trust_remote_code": False,
        "revision": "main"
    }


def get_llm_config() -> Dict[str, Any]:
    """获取大语言模型配置"""
    return {
        "model_name": "gpt-2",
        "device": os.getenv("DEVICE", "cpu"),
        "cache_folder": os.getenv("MODEL_CACHE_DIR", "models/cache"),
        "max_length": 1024,
        "temperature": 0.7,
        "do_sample": True,
        "pad_token_id": 50256
    }


def get_reranker_config() -> Dict[str, Any]:
    """获取重排模型配置"""
    return {
        "model_name": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "device": os.getenv("DEVICE", "cpu"),
        "cache_folder": os.getenv("MODEL_CACHE_DIR", "models/cache"),
        "max_seq_length": 512
    }


def get_model_config(model_type: str = "embedding") -> Dict[str, Any]:
    """获取指定类型的模型配置"""
    config_map = {
        "embedding": get_embedding_config,
        "llm": get_llm_config,
        "reranker": get_reranker_config
    }

    if model_type in config_map:
        return config_map[model_type]()

    return get_embedding_config()


def get_performance_config() -> Dict[str, Any]:
    """获取性能优化配置"""
    return {
        "batch_size": int(os.getenv("BATCH_SIZE", "32")),
        "num_workers": int(os.getenv("NUM_WORKERS", "4")),
        "prefetch_factor": int(os.getenv("PREFETCH_FACTOR", "2")),
        "persistent_workers": True,
        "pin_memory": True if os.getenv("DEVICE", "cpu") == "cuda" else False,
        "timeout": int(os.getenv("TIMEOUT", "30")),
        "retry_count": int(os.getenv("RETRY_COUNT", "3"))
    }


def get_cache_config() -> Dict[str, Any]:
    """获取缓存配置"""
    return {
        "max_cache_size": int(os.getenv("MAX_CACHE_SIZE", "1000")),
        "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
        "enable_memory_cache": os.getenv("ENABLE_MEMORY_CACHE", "true").lower() == "true",
        "enable_disk_cache": os.getenv("ENABLE_DISK_CACHE", "true").lower() == "true",
        "cache_dir": os.getenv("CACHE_DIR", "cache")
    }
