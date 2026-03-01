#!/usr/bin/env python3
"""
统一错误处理系统

提供错误分类、日志记录、通知功能和错误恢复机制的单例错误管理器。

特性:
- 错误分类和严重程度管理
- 结构化日志记录
- 错误恢复和重试机制
- 错误通知和报告
- 线程安全
- 性能监控
"""
import asyncio
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union
from dataclasses import dataclass, field
from pathlib import Path

from src.services.logging_service import get_logger


class ErrorLevel(Enum):
    """错误严重程度"""
    LOW = 1          # 可忽略的错误
    MEDIUM = 2       # 需要关注
    HIGH = 3         # 需要立即处理
    CRITICAL = 4     # 系统级错误


class ErrorCategory(Enum):
    """错误分类"""
    VALIDATION = "validation"           # 验证错误
    NETWORK = "network"                # 网络错误
    DATABASE = "database"              # 数据库错误
    LLM_API = "llm_api"               # LLM API错误
    PARSING = "parsing"                # 解析错误
    SYSTEM = "system"                  # 系统错误
    BUSINESS = "business"              # 业务逻辑错误
    CONFIGURATION = "configuration"    # 配置错误
    TIMEOUT = "timeout"               # 超时错误
    UNKNOWN = "unknown"                # 未知错误


@dataclass
class ErrorEvent:
    """错误事件数据结构"""
    error_id: str
    category: ErrorCategory
    level: ErrorLevel
    message: str
    exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    module: str = ""
    function: str = ""
    line_number: Optional[int] = None
    stack_trace: Optional[str] = None
    recovery_attempts: int = 0
    resolved: bool = False
    resolution_strategy: Optional[str] = None


@dataclass
class ErrorStats:
    """错误统计信息"""
    total_errors: int = 0
    errors_by_category: Dict[ErrorCategory, int] = field(default_factory=lambda: defaultdict(int))
    errors_by_level: Dict[ErrorLevel, int] = field(default_factory=lambda: defaultdict(int))
    recent_errors: deque = field(default_factory=lambda: deque(maxlen=1000))
    error_rate: float = 0.0
    last_reset_time: datetime = field(default_factory=datetime.now)


class ErrorManager:
    """
    统一错误管理器 - 单例模式
    
    提供错误处理、分类、日志记录、恢复和统计功能
    """
    
    _instance: Optional['ErrorManager'] = None
    _lock: threading.Lock = threading.Lock()
    
    def __new__(cls) -> 'ErrorManager':
        """单例实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化错误管理器"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._lock = threading.RLock()
        self._error_history: List[ErrorEvent] = []
        self._stats = ErrorStats()
        self._recovery_strategies: Dict[ErrorCategory, List[Callable]] = defaultdict(list)
        self._notification_handlers: List[Callable[[ErrorEvent], None]] = []
        self._error_callbacks: Dict[ErrorCategory, List[Callable]] = defaultdict(list)
        
        # 配置日志
        self.logger = get_logger(__name__)
        
        # 注册默认恢复策略
        self._register_default_recovery_strategies()
        
        # 性能监控
        self._performance_metrics: Dict[str, List[float]] = defaultdict(list)
        
        self.logger.info("ErrorManager 初始化完成")
    
    def _register_default_recovery_strategies(self):
        """注册默认的错误恢复策略"""
        
        # 网络错误恢复策略
        self.register_recovery_strategy(ErrorCategory.NETWORK, self._retry_with_backoff)
        self.register_recovery_strategy(ErrorCategory.NETWORK, self._switch_endpoint)
        
        # LLM API错误恢复策略
        self.register_recovery_strategy(ErrorCategory.LLM_API, self._retry_with_exponential_backoff)
        self.register_recovery_strategy(ErrorCategory.LLM_API, self._switch_model_provider)
        
        # 数据库错误恢复策略
        self.register_recovery_strategy(ErrorCategory.DATABASE, self._retry_connection)
        self.register_recovery_strategy(ErrorCategory.DATABASE, self._use_cache_fallback)
        
        # 解析错误恢复策略
        self.register_recovery_strategy(ErrorCategory.PARSING, self._robust_parsing)
        self.register_recovery_strategy(ErrorCategory.PARSING, self._skip_invalid_data)
        
        # 超时错误恢复策略
        self.register_recovery_strategy(ErrorCategory.TIMEOUT, self._increase_timeout)
        self.register_recovery_strategy(ErrorCategory.TIMEOUT, self._reduce_complexity)
    
    def handle_error(
        self,
        error: Union[Exception, str],
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        level: ErrorLevel = ErrorLevel.MEDIUM,
        context: Optional[Dict[str, Any]] = None,
        module: str = "",
        function: str = "",
        line_number: Optional[int] = None
    ) -> ErrorEvent:
        """
        处理错误事件
        
        Args:
            error: 异常对象或错误消息
            category: 错误分类
            level: 错误严重程度
            context: 错误上下文信息
            module: 模块名
            function: 函数名
            line_number: 行号
            
        Returns:
            ErrorEvent: 创建的错误事件
        """
        with self._lock:
            # 创建错误事件
            error_event = self._create_error_event(
                error, category, level, context, module, function, line_number
            )
            
            # 更新统计信息
            self._update_stats(error_event)
            
            # 记录日志
            self._log_error(error_event)
            
            # 执行错误回调
            self._execute_error_callbacks(error_event)
            
            # 发送通知（如果是高级别错误）
            if level in [ErrorLevel.HIGH, ErrorLevel.CRITICAL]:
                self._send_notifications(error_event)
            
            return error_event
    
    def _create_error_event(
        self,
        error: Union[Exception, str],
        category: ErrorCategory,
        level: ErrorLevel,
        context: Optional[Dict[str, Any]],
        module: str,
        function: str,
        line_number: Optional[int]
    ) -> ErrorEvent:
        """创建错误事件对象"""
        import traceback
        import uuid
        
        error_id = str(uuid.uuid4())[:8]
        
        if isinstance(error, Exception):
            message = str(error)
            exception = error
            stack_trace = traceback.format_exc()
        else:
            message = error
            exception = None
            stack_trace = None
        
        return ErrorEvent(
            error_id=error_id,
            category=category,
            level=level,
            message=message,
            exception=exception,
            context=context or {},
            timestamp=datetime.now(),
            module=module,
            function=function,
            line_number=line_number,
            stack_trace=stack_trace
        )
    
    def _update_stats(self, error_event: ErrorEvent):
        """更新错误统计信息"""
        self._stats.total_errors += 1
        self._stats.errors_by_category[error_event.category] += 1
        self._stats.errors_by_level[error_event.level] += 1
        self._stats.recent_errors.append(error_event)
        
        # 计算错误率（每分钟）
        now = datetime.now()
        time_diff = (now - self._stats.last_reset_time).total_seconds() / 60
        if time_diff > 0:
            self._stats.error_rate = self._stats.total_errors / time_diff
    
    def _log_error(self, error_event: ErrorEvent):
        """记录错误日志"""
        log_message = (
            f"[{error_event.error_id}] "
            f"{error_event.category.value.upper()} - "
            f"{error_event.level.name}: {error_event.message}"
        )
        
        if error_event.module:
            log_message += f" | Module: {error_event.module}"
        if error_event.function:
            log_message += f" | Function: {error_event.function}"
        if error_event.context:
            log_message += f" | Context: {error_event.context}"
        
        # 根据错误级别选择日志级别
        if error_event.level == ErrorLevel.CRITICAL:
            self.logger.critical(log_message)
        elif error_event.level == ErrorLevel.HIGH:
            self.logger.error(log_message)
        elif error_event.level == ErrorLevel.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # 记录堆栈跟踪
        if error_event.stack_trace:
            self.logger.debug(f"Stack trace for {error_event.error_id}:\n{error_event.stack_trace}")
    
    def _execute_error_callbacks(self, error_event: ErrorEvent):
        """执行错误回调函数"""
        try:
            for callback in self._error_callbacks[error_event.category]:
                callback(error_event)
        except Exception as e:
            self.logger.error(f"Error executing callback: {e}")
    
    def _send_notifications(self, error_event: ErrorEvent):
        """发送错误通知"""
        try:
            for handler in self._notification_handlers:
                handler(error_event)
        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
    
    def try_recover(
        self,
        error_event: ErrorEvent,
        operation: Callable,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        尝试从错误中恢复
        
        Args:
            error_event: 错误事件
            operation: 要重试的操作
            *args, **kwargs: 操作参数
            
        Returns:
            Tuple[bool, Any]: (是否成功, 结果或错误)
        """
        strategies = self._recovery_strategies[error_event.category]
        
        for strategy in strategies:
            try:
                result = strategy(error_event, operation, *args, **kwargs)
                if result is not None:
                    error_event.resolved = True
                    error_event.resolution_strategy = strategy.__name__
                    self.logger.info(f"Error {error_event.error_id} resolved using {strategy.__name__}")
                    return True, result
            except Exception as e:
                self.logger.warning(f"Recovery strategy {strategy.__name__} failed: {e}")
                error_event.recovery_attempts += 1
        
        return False, None
    
    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """注册错误恢复策略"""
        with self._lock:
            self._recovery_strategies[category].append(strategy)
            self.logger.debug(f"Registered recovery strategy for {category.value}: {strategy.__name__}")
    
    def register_notification_handler(self, handler: Callable[[ErrorEvent], None]):
        """注册错误通知处理器"""
        with self._lock:
            self._notification_handlers.append(handler)
            self.logger.debug(f"Registered notification handler: {handler.__name__}")
    
    def register_error_callback(self, category: ErrorCategory, callback: Callable[[ErrorEvent], None]):
        """注册错误回调函数"""
        with self._lock:
            self._error_callbacks[category].append(callback)
            self.logger.debug(f"Registered error callback for {category.value}: {callback.__name__}")
    
    # 默认恢复策略实现
    def _retry_with_backoff(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """使用退避重试"""
        max_retries = 3
        base_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.debug(f"Retry attempt {attempt + 1} failed: {e}")
    
    def _retry_with_exponential_backoff(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """使用指数退避重试（适用于API调用）"""
        max_retries = 5
        base_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                delay = base_delay * (2 ** attempt) + (attempt * 0.1)
                time.sleep(delay)
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                self.logger.debug(f"Exponential backoff attempt {attempt + 1} failed: {e}")
    
    def _switch_endpoint(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """切换端点"""
        # 这里可以实现端点切换逻辑
        # 暂时直接重试
        return operation(*args, **kwargs)
    
    def _switch_model_provider(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """切换模型提供商"""
        # 这里可以实现模型切换逻辑
        # 暂时直接重试
        return operation(*args, **kwargs)
    
    def _retry_connection(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """重试数据库连接"""
        return self._retry_with_backoff(error_event, operation, *args, **kwargs)
    
    def _use_cache_fallback(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """使用缓存回退"""
        # 这里可以实现缓存回退逻辑
        return None
    
    def _robust_parsing(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """健壮解析"""
        try:
            return operation(*args, **kwargs)
        except:
            # 尝试更宽松的解析方式
            # 这里可以实现具体的解析逻辑
            return None
    
    def _skip_invalid_data(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """跳过无效数据"""
        return None
    
    def _increase_timeout(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """增加超时时间"""
        # 这里可以实现超时时间调整
        return operation(*args, **kwargs)
    
    def _reduce_complexity(self, error_event: ErrorEvent, operation: Callable, *args, **kwargs) -> Any:
        """降低复杂度"""
        # 这里可以实现复杂度降低逻辑
        return operation(*args, **kwargs)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        with self._lock:
            return {
                'total_errors': self._stats.total_errors,
                'error_rate': self._stats.error_rate,
                'errors_by_category': {
                    cat.name: count 
                    for cat, count in self._stats.errors_by_category.items()
                },
                'errors_by_level': {
                    level.name: count 
                    for level, count in self._stats.errors_by_level.items()
                },
                'recent_errors_count': len(self._stats.recent_errors),
                'last_reset_time': self._stats.last_reset_time.isoformat()
            }
    
    def get_recent_errors(self, limit: int = 50) -> List[ErrorEvent]:
        """获取最近的错误"""
        with self._lock:
            return list(self._stats.recent_errors)[-limit:]
    
    def clear_error_history(self):
        """清除错误历史"""
        with self._lock:
            self._error_history.clear()
            self._stats = ErrorStats()
            self.logger.info("Error history cleared")
    
    def export_error_report(self, file_path: Optional[str] = None) -> str:
        """导出错误报告"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"error_report_{timestamp}.json"
        
        import json
        
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'statistics': self.get_error_statistics(),
            'recent_errors': [
                {
                    'error_id': err.error_id,
                    'category': err.category.value,
                    'level': err.level.name,
                    'message': err.message,
                    'timestamp': err.timestamp.isoformat(),
                    'module': err.module,
                    'function': err.function,
                    'context': err.context,
                    'resolved': err.resolved,
                    'recovery_attempts': err.recovery_attempts
                }
                for err in self.get_recent_errors(100)
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Error report exported to {file_path}")
        return file_path


# 便捷装饰器
def error_boundary(
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    level: ErrorLevel = ErrorLevel.MEDIUM,
    context: Optional[Dict[str, Any]] = None,
    reraise: bool = True
):
    """
    错误边界装饰器
    
    自动捕获函数中的异常并交由ErrorManager处理
    
    Args:
        category: 错误分类
        level: 错误级别
        context: 错误上下文
        reraise: 是否重新抛出异常
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                manager = ErrorManager()
                
                # 获取调用信息
                import inspect
                frame = inspect.currentframe().f_back
                module = frame.f_globals.get('__name__', '')
                function = func.__name__
                line_number = frame.f_lineno if frame else None
                
                error_event = manager.handle_error(
                    error=e,
                    category=category,
                    level=level,
                    context=context,
                    module=module,
                    function=function,
                    line_number=line_number
                )
                
                # 尝试恢复
                success, result = manager.try_recover(
                    error_event, func, *args, **kwargs
                )
                
                if success:
                    return result
                
                if reraise:
                    raise
                
                return None
        return wrapper
    return decorator


# 全局错误管理器实例
def get_error_manager() -> ErrorManager:
    """获取全局错误管理器实例"""
    return ErrorManager()


# 便捷函数
def handle_error(
    error: Union[Exception, str],
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    level: ErrorLevel = ErrorLevel.MEDIUM,
    **kwargs
) -> ErrorEvent:
    """便捷的错误处理函数"""
    return get_error_manager().handle_error(error, category, level, **kwargs)


# 保持向后兼容的函数
def safe_execute(default_return: Any = None, log_error: bool = True):
    """
    安全执行装饰器（向后兼容）
    捕获所有异常并返回默认值
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                manager = get_error_manager()
                manager.handle_error(
                    error=e,
                    category=ErrorCategory.UNKNOWN,
                    level=ErrorLevel.LOW,
                    context={'default_return': default_return},
                    function=func.__name__
                )
                return default_return
        return wrapper
    return decorator


def safe_attribute_access(obj: Any, attr: str, default: Any = None) -> Any:
    """安全访问对象属性（向后兼容）"""
    try:
        return getattr(obj, attr, default)
    except Exception as e:
        manager = get_error_manager()
        manager.handle_error(
            error=e,
            category=ErrorCategory.UNKNOWN,
            level=ErrorLevel.LOW,
            context={'attribute': attr, 'default': default},
            function='safe_attribute_access'
        )
        return default


def safe_type_comparison(value1: Any, value2: Any, operator: str = '>') -> bool:
    """安全的类型比较（向后兼容）"""
    try:
        # 确保两个值都是可比较的类型
        if isinstance(value1, (list, tuple)):
            value1 = len(value1)
        if isinstance(value2, (list, tuple)):
            value2 = len(value2)
        
        if operator == '>':
            return value1 > value2
        elif operator == '<':
            return value1 < value2
        elif operator == '==':
            return value1 == value2
        elif operator == '>=':
            return value1 >= value2
        elif operator == '<=':
            return value1 <= value2
        else:
            return False
    except Exception as e:
        manager = get_error_manager()
        manager.handle_error(
            error=e,
            category=ErrorCategory.UNKNOWN,
            level=ErrorLevel.LOW,
            context={'value1': value1, 'value2': value2, 'operator': operator},
            function='safe_type_comparison'
        )
        return False
