#!/usr/bin/env python3
"""
优化的系统配置
"""

# 系统性能配置
PERFORMANCE_CONFIG = {
    "max_execution_time": 30,  # 最大执行时间30秒
    "max_retry_attempts": 3,   # 最大重试次数
    "timeout_threshold": get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),    # 超时阈值
    "memory_limit_mb": 512,     # 内存限制
    "enable_caching": True,     # 启用缓存
    "cache_ttl": 3600,         # 缓存生存时间
}

# 智能体配置
AGENT_CONFIG = {
    "enable_fallback": True,    # 启用备用机制
    "enable_simplified_mode": True,  # 启用简化模式
    "max_knowledge_items": 5,   # 最大知识条目数
    "confidence_threshold": get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")), # 置信度阈值
    "enable_adaptive_learning": True,  # 启用自适应学习
}

# 推理配置
REASONING_CONFIG = {
    "method": "simplified",     # 推理方法
    "max_steps": 5,            # 最大推理步骤
    "enable_validation": True,  # 启用验证
    "enable_optimization": True, # 启用优化
}

# 错误处理配置
ERROR_HANDLING_CONFIG = {
    "enable_graceful_degradation": True,  # 启用优雅降级
    "log_error_details": True,   # 记录错误详情
    "retry_on_failure": True,   # 失败时重试
    "fallback_strategy": "simplified",  # 备用策略
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "enable_file_logging": True,
    "log_file": "logs/system.log",
    "max_log_size_mb": get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
    "backup_count": 5,
}
