"""
标准日志服务（向后兼容）
使用新的结构化日志系统，提供JSON格式日志和追踪上下文支持
"""
import os
import logging
import sys
from typing import Optional, Union

# 尝试导入结构化日志系统
try:
    from src.observability.structured_logging import (
        get_structured_logger,
        LogLevel,
        StructuredLogger
    )
    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError as e:
    STRUCTURED_LOGGING_AVAILABLE = False
    StructuredLogger = None  # type fallback

# 配置：是否使用结构化日志
USE_STRUCTURED_LOGGING = os.getenv("USE_STRUCTURED_LOGGING", "true").lower() == "true"


def get_logger(name: str, level: int = logging.INFO) -> Union[logging.Logger, StructuredLogger]:
    """
    获取配置的日志记录器实例（向后兼容）
    
    参数:
        name: 日志记录器名称
        level: 日志级别（logging.DEBUG, logging.INFO等）
    
    返回:
        日志记录器实例
    """
    # 如果结构化日志可用且启用，使用结构化日志
    if STRUCTURED_LOGGING_AVAILABLE and USE_STRUCTURED_LOGGING:
        # 将logging级别转换为LogLevel枚举
        level_map = {
            logging.DEBUG: LogLevel.DEBUG,
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARNING,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.CRITICAL,
        }
        
        log_level = level_map.get(level, LogLevel.INFO)
        return get_structured_logger(name, level=log_level)
    
    # 否则使用传统日志（保持向后兼容）
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(level)
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        
        # 如果启用了文件日志（环境变量配置）
        if os.getenv("LOG_ENABLE_FILE", "false").lower() == "true":
            try:
                from logging.handlers import RotatingFileHandler
                
                log_file = os.getenv("LOG_FILE_PATH", "logs/app.log")
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                
                file_handler = RotatingFileHandler(
                    filename=log_file,
                    maxBytes=int(os.getenv("LOG_MAX_FILE_SIZE_MB", "100")) * 1024 * 1024,
                    backupCount=int(os.getenv("LOG_BACKUP_COUNT", "5")),
                    encoding='utf-8'
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                print(f"配置文件日志失败: {e}")
    
    return logger


# 便捷函数（保持向后兼容）
def setup_logging(level: int = logging.INFO):
    """设置全局日志配置（向后兼容）"""
    # 结构化日志系统会自动初始化
    # 这里只处理传统日志的额外配置
    if not (STRUCTURED_LOGGING_AVAILABLE and USE_STRUCTURED_LOGGING):
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        
        # 如果根日志记录器没有处理器，添加一个
        if not root_logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            
            root_logger.addHandler(console_handler)


# 初始化日志系统
setup_logging()
