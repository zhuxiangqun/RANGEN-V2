"""
结构化日志系统
提供JSON格式的结构化日志，便于机器解析和集中日志管理
"""

import os
import json
import logging
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from enum import Enum

from src.observability.tracing import TraceContext


class LogFormat(Enum):
    """日志格式"""
    JSON = "json"
    TEXT = "text"
    CONSOLE = "console"


class LogLevel(Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class StructuredLogger:
    """结构化日志记录器"""
    
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        format: LogFormat = LogFormat.JSON,
        include_trace_context: bool = True
    ):
        self.name = name
        self.level = level
        self.format = format
        self.include_trace_context = include_trace_context
        
        # 创建底层logger
        self._logger = logging.getLogger(name)
        
        # 设置日志级别
        log_level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL,
        }
        self._logger.setLevel(log_level_map[level])
        
        # 移除现有处理器
        self._logger.handlers.clear()
        
        # 添加处理器
        self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        if self.format == LogFormat.JSON:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self._logger.addHandler(handler)
        
        elif self.format == LogFormat.TEXT:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
        
        elif self.format == LogFormat.CONSOLE:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def _get_extra_fields(self, **kwargs) -> Dict[str, Any]:
        """获取额外的日志字段"""
        extra = kwargs.copy()
        
        # 添加追踪上下文
        if self.include_trace_context:
            trace_ctx = TraceContext.get_current_context()
            if trace_ctx:
                extra["trace_id"] = trace_ctx.get("trace_id")
                extra["span_id"] = trace_ctx.get("span_id")
        
        # 添加时间戳
        extra["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # 添加日志记录器名称
        extra["logger"] = self.name
        
        # 添加主机信息
        try:
            import socket
            extra["hostname"] = socket.gethostname()
        except:
            pass
        
        # 添加进程信息
        extra["pid"] = os.getpid()
        
        return extra
    
    def debug(self, message: str, **kwargs):
        """记录调试日志"""
        extra = self._get_extra_fields(**kwargs)
        self._logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """记录信息日志"""
        extra = self._get_extra_fields(**kwargs)
        self._logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        """记录警告日志"""
        extra = self._get_extra_fields(**kwargs)
        self._logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        """记录错误日志"""
        extra = self._get_extra_fields(**kwargs)
        self._logger.error(message, extra=extra)
    
    def critical(self, message: str, **kwargs):
        """记录严重错误日志"""
        extra = self._get_extra_fields(**kwargs)
        self._logger.critical(message, extra=extra)
    
    def exception(self, message: str, exc: Exception = None, **kwargs):
        """记录异常日志"""
        extra = self._get_extra_fields(**kwargs)
        
        # 添加异常信息
        if exc:
            extra["exception_type"] = type(exc).__name__
            extra["exception_message"] = str(exc)
            extra["exception_traceback"] = traceback.format_exc()
        
        self._logger.error(message, extra=extra, exc_info=exc is not None)
    
    def log_with_level(self, level: LogLevel, message: str, **kwargs):
        """按指定级别记录日志"""
        log_methods = {
            LogLevel.DEBUG: self.debug,
            LogLevel.INFO: self.info,
            LogLevel.WARNING: self.warning,
            LogLevel.ERROR: self.error,
            LogLevel.CRITICAL: self.critical,
        }
        
        log_method = log_methods.get(level)
        if log_method:
            log_method(message, **kwargs)
        else:
            self.info(message, **kwargs)


class JSONFormatter(logging.Formatter):
    """JSON格式日志格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        log_entry = {
            "timestamp": getattr(record, "timestamp", datetime.utcnow().isoformat() + "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加额外字段
        for key, value in record.__dict__.items():
            if key not in [
                'args', 'asctime', 'created', 'exc_info', 'exc_text', 
                'filename', 'funcName', 'id', 'levelname', 'levelno', 
                'lineno', 'module', 'msecs', 'message', 'msg', 'name', 
                'pathname', 'process', 'processName', 'relativeCreated', 
                'stack_info', 'thread', 'threadName', 'timestamp'
            ]:
                if not key.startswith('_'):
                    log_entry[key] = value
        
        # 添加异常信息
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


class StructuredLoggingConfig:
    """结构化日志配置"""
    
    def __init__(self):
        self.default_format = LogFormat.JSON
        self.default_level = LogLevel.INFO
        self.enable_console_log = True
        self.enable_file_log = False
        self.log_file_path = "logs/app.log"
        self.max_file_size_mb = 100
        self.backup_count = 5
        
        self._load_config()
    
    def _load_config(self):
        """加载配置"""
        # 从环境变量加载配置
        format_str = os.getenv("LOG_FORMAT", "json").lower()
        if format_str in ["json", "text", "console"]:
            self.default_format = LogFormat(format_str)
        
        level_str = os.getenv("LOG_LEVEL", "info").lower()
        if level_str in ["debug", "info", "warning", "error", "critical"]:
            self.default_level = LogLevel(level_str)
        
        self.enable_console_log = os.getenv("LOG_ENABLE_CONSOLE", "true").lower() == "true"
        self.enable_file_log = os.getenv("LOG_ENABLE_FILE", "false").lower() == "true"
        
        log_file = os.getenv("LOG_FILE_PATH")
        if log_file:
            self.log_file_path = log_file
        
        try:
            self.max_file_size_mb = int(os.getenv("LOG_MAX_FILE_SIZE_MB", "100"))
        except ValueError:
            pass
        
        try:
            self.backup_count = int(os.getenv("LOG_BACKUP_COUNT", "5"))
        except ValueError:
            pass


def get_structured_logger(
    name: str,
    level: Optional[LogLevel] = None,
    format: Optional[LogFormat] = None,
    include_trace_context: bool = True
) -> StructuredLogger:
    """获取结构化日志记录器"""
    config = _get_logging_config()
    
    if level is None:
        level = config.default_level
    
    if format is None:
        format = config.default_format
    
    return StructuredLogger(
        name=name,
        level=level,
        format=format,
        include_trace_context=include_trace_context
    )


def setup_global_logging():
    """设置全局日志配置"""
    config = _get_logging_config()
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # 设置日志级别
    level_map = {
        LogLevel.DEBUG: logging.DEBUG,
        LogLevel.INFO: logging.INFO,
        LogLevel.WARNING: logging.WARNING,
        LogLevel.ERROR: logging.ERROR,
        LogLevel.CRITICAL: logging.CRITICAL,
    }
    root_logger.setLevel(level_map[config.default_level])
    
    # 添加控制台处理器
    if config.enable_console_log:
        console_handler = logging.StreamHandler(sys.stdout)
        
        if config.default_format == LogFormat.JSON:
            console_handler.setFormatter(JSONFormatter())
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
        
        root_logger.addHandler(console_handler)
    
    # 添加文件处理器
    if config.enable_file_log:
        try:
            from logging.handlers import RotatingFileHandler
            
            # 确保日志目录存在
            log_dir = os.path.dirname(config.log_file_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = RotatingFileHandler(
                filename=config.log_file_path,
                maxBytes=config.max_file_size_mb * 1024 * 1024,  # MB转字节
                backupCount=config.backup_count,
                encoding='utf-8'
            )
            
            if config.default_format == LogFormat.JSON:
                file_handler.setFormatter(JSONFormatter())
            else:
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(formatter)
            
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            print(f"配置文件日志失败: {e}")


# 全局配置实例
_logging_config = None

def _get_logging_config() -> StructuredLoggingConfig:
    """获取日志配置实例"""
    global _logging_config
    if _logging_config is None:
        _logging_config = StructuredLoggingConfig()
    return _logging_config


# 便捷日志函数
def log_debug(message: str, logger_name: str = "app", **kwargs):
    """记录调试日志便捷函数"""
    logger = get_structured_logger(logger_name)
    logger.debug(message, **kwargs)


def log_info(message: str, logger_name: str = "app", **kwargs):
    """记录信息日志便捷函数"""
    logger = get_structured_logger(logger_name)
    logger.info(message, **kwargs)


def log_warning(message: str, logger_name: str = "app", **kwargs):
    """记录警告日志便捷函数"""
    logger = get_structured_logger(logger_name)
    logger.warning(message, **kwargs)


def log_error(message: str, logger_name: str = "app", **kwargs):
    """记录错误日志便捷函数"""
    logger = get_structured_logger(logger_name)
    logger.error(message, **kwargs)


def log_critical(message: str, logger_name: str = "app", **kwargs):
    """记录严重错误日志便捷函数"""
    logger = get_structured_logger(logger_name)
    logger.critical(message, **kwargs)


def log_exception(message: str, exc: Exception, logger_name: str = "app", **kwargs):
    """记录异常日志便捷函数"""
    logger = get_structured_logger(logger_name)
    logger.exception(message, exc=exc, **kwargs)


# 请求日志中间件
async def request_logging_middleware(request, call_next):
    """请求日志中间件"""
    import time
    
    start_time = time.time()
    
    # 获取请求信息
    method = request.method
    path = request.url.path
    query = str(request.query_params)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # 记录请求开始
    logger = get_structured_logger("request")
    logger.info(
        "请求开始",
        method=method,
        path=path,
        query=query,
        client_ip=client_ip,
        user_agent=user_agent,
        request_id=request.headers.get("x-request-id")
    )
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求完成
        logger.info(
            "请求完成",
            method=method,
            path=path,
            status_code=response.status_code,
            process_time_ms=round(process_time * 1000, 2),
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request.headers.get("x-request-id")
        )
        
        # 添加处理时间头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
        
    except Exception as e:
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求错误
        logger.error(
            "请求错误",
            method=method,
            path=path,
            process_time_ms=round(process_time * 1000, 2),
            client_ip=client_ip,
            user_agent=user_agent,
            request_id=request.headers.get("x-request-id"),
            error_type=type(e).__name__,
            error_message=str(e)
        )
        
        raise


# 初始化全局日志配置
setup_global_logging()