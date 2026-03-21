"""
错误处理增强模块 - 阶段5.2
完善错误分类、处理、恢复策略
"""
import logging
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """错误类型枚举 - 阶段5.2"""
    # 网络相关错误
    NETWORK_ERROR = "network_error"
    TIMEOUT_ERROR = "timeout_error"
    CONNECTION_ERROR = "connection_error"
    
    # API相关错误
    API_ERROR = "api_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    QUOTA_EXCEEDED_ERROR = "quota_exceeded_error"
    
    # 数据相关错误
    DATA_VALIDATION_ERROR = "data_validation_error"
    DATA_FORMAT_ERROR = "data_format_error"
    MISSING_DATA_ERROR = "missing_data_error"
    
    # 配置相关错误
    CONFIG_ERROR = "config_error"
    MISSING_CONFIG_ERROR = "missing_config_error"
    
    # 逻辑错误
    LOGIC_ERROR = "logic_error"
    STATE_ERROR = "state_error"
    
    # 未知错误
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class ErrorInfo:
    """错误信息"""
    error_type: ErrorType
    error_message: str
    error_details: Dict[str, Any]
    timestamp: float
    node_name: Optional[str] = None
    retryable: bool = False
    recoverable: bool = False


class ErrorHandler:
    """错误处理器 - 阶段5.2"""
    
    def __init__(self):
        """初始化错误处理器"""
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorInfo] = []
        self.max_history_size = 1000
    
    def classify_error(self, error: Exception, node_name: Optional[str] = None) -> ErrorInfo:
        """分类错误 - 阶段5.2增强版
        
        Args:
            error: 异常对象
            node_name: 节点名称（可选）
        
        Returns:
            ErrorInfo对象
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__
        
        # 网络相关错误
        if any(keyword in error_str for keyword in ['timeout', 'timed out', 'time out']):
            error_type = ErrorType.TIMEOUT_ERROR
            retryable = True
            recoverable = True
        elif any(keyword in error_str for keyword in ['connection', 'connect', 'network']):
            error_type = ErrorType.CONNECTION_ERROR
            retryable = True
            recoverable = True
        elif 'network' in error_str:
            error_type = ErrorType.NETWORK_ERROR
            retryable = True
            recoverable = True
        
        # API相关错误
        elif 'rate limit' in error_str or 'rate_limit' in error_str:
            error_type = ErrorType.RATE_LIMIT_ERROR
            retryable = True
            recoverable = True
        elif 'quota' in error_str or 'quota exceeded' in error_str:
            error_type = ErrorType.QUOTA_EXCEEDED_ERROR
            retryable = False
            recoverable = False
        elif 'api' in error_str or error_type_name in ['APIError', 'HTTPError']:
            error_type = ErrorType.API_ERROR
            retryable = True
            recoverable = True
        
        # 数据相关错误
        elif 'validation' in error_str or 'invalid' in error_str:
            error_type = ErrorType.DATA_VALIDATION_ERROR
            retryable = False
            recoverable = True
        elif 'format' in error_str or 'malformed' in error_str:
            error_type = ErrorType.DATA_FORMAT_ERROR
            retryable = False
            recoverable = True
        elif 'missing' in error_str or 'not found' in error_str:
            error_type = ErrorType.MISSING_DATA_ERROR
            retryable = False
            recoverable = True
        
        # 配置相关错误
        elif 'config' in error_str or 'configuration' in error_str:
            error_type = ErrorType.CONFIG_ERROR
            retryable = False
            recoverable = True
        elif 'missing config' in error_str:
            error_type = ErrorType.MISSING_CONFIG_ERROR
            retryable = False
            recoverable = True
        
        # 逻辑错误
        elif 'state' in error_str or 'invalid state' in error_str:
            error_type = ErrorType.STATE_ERROR
            retryable = False
            recoverable = True
        elif 'logic' in error_str or 'illegal' in error_str:
            error_type = ErrorType.LOGIC_ERROR
            retryable = False
            recoverable = False
        
        # 未知错误
        else:
            error_type = ErrorType.UNKNOWN_ERROR
            retryable = False
            recoverable = False
        
        error_info = ErrorInfo(
            error_type=error_type,
            error_message=str(error),
            error_details={
                'error_type_name': error_type_name,
                'error_str': error_str,
                'traceback': self._get_traceback(error)
            },
            timestamp=time.time(),
            node_name=node_name,
            retryable=retryable,
            recoverable=recoverable
        )
        
        # 记录错误历史
        self._record_error(error_info)
        
        return error_info
    
    def _get_traceback(self, error: Exception) -> Optional[str]:
        """获取错误堆栈跟踪"""
        import traceback
        try:
            return traceback.format_exc()
        except Exception:
            return None
    
    def _record_error(self, error_info: ErrorInfo) -> None:
        """记录错误历史"""
        self.error_history.append(error_info)
        
        # 限制历史大小
        if len(self.error_history) > self.max_history_size:
            self.error_history = self.error_history[-self.max_history_size:]
    
    def get_recovery_strategy(self, error_info: ErrorInfo) -> Dict[str, Any]:
        """获取错误恢复策略
        
        Args:
            error_info: 错误信息
        
        Returns:
            恢复策略字典
        """
        strategy = {
            'should_retry': error_info.retryable,
            'should_fallback': error_info.recoverable,
            'max_retries': 3,
            'retry_delay': 1.0,
            'fallback_node': None
        }
        
        # 根据错误类型调整策略
        if error_info.error_type == ErrorType.TIMEOUT_ERROR:
            strategy['max_retries'] = 5
            strategy['retry_delay'] = 2.0
        elif error_info.error_type == ErrorType.RATE_LIMIT_ERROR:
            strategy['max_retries'] = 3
            strategy['retry_delay'] = 5.0  # 等待更长时间
        elif error_info.error_type == ErrorType.CONNECTION_ERROR:
            strategy['max_retries'] = 3
            strategy['retry_delay'] = 1.0
        elif error_info.error_type == ErrorType.QUOTA_EXCEEDED_ERROR:
            strategy['should_retry'] = False
            strategy['should_fallback'] = False
        elif error_info.error_type in [ErrorType.DATA_VALIDATION_ERROR, ErrorType.DATA_FORMAT_ERROR]:
            strategy['should_retry'] = False
            strategy['should_fallback'] = True
        
        return strategy
    
    def should_retry(self, error_info: ErrorInfo, retry_count: int) -> bool:
        """判断是否应该重试
        
        Args:
            error_info: 错误信息
            retry_count: 当前重试次数
        
        Returns:
            是否应该重试
        """
        if not error_info.retryable:
            return False
        
        strategy = self.get_recovery_strategy(error_info)
        return retry_count < strategy['max_retries']
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """获取错误统计信息"""
        if not self.error_history:
            return {
                'total_errors': 0,
                'error_types': {},
                'retryable_errors': 0,
                'recoverable_errors': 0
            }
        
        error_types = {}
        retryable_count = 0
        recoverable_count = 0
        
        for error_info in self.error_history:
            error_type = error_info.error_type.value
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            if error_info.retryable:
                retryable_count += 1
            if error_info.recoverable:
                recoverable_count += 1
        
        return {
            'total_errors': len(self.error_history),
            'error_types': error_types,
            'retryable_errors': retryable_count,
            'recoverable_errors': recoverable_count,
            'retryable_rate': retryable_count / len(self.error_history) if self.error_history else 0.0,
            'recoverable_rate': recoverable_count / len(self.error_history) if self.error_history else 0.0
        }


# 全局错误处理器实例
_error_handler = None


def get_error_handler() -> ErrorHandler:
    """获取全局错误处理器实例"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_node_error(
    error: Exception,
    node_name: str,
    state: Dict[str, Any],
    fallback_node: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    """处理节点错误 - 阶段5.2增强版
    
    Args:
        error: 异常对象
        node_name: 节点名称
        state: 状态字典
        fallback_node: 降级节点函数（可选）
    
    Returns:
        更新后的状态字典
    """
    error_handler = get_error_handler()
    error_info = error_handler.classify_error(error, node_name)
    
    # 记录错误
    if 'errors' not in state:
        state['errors'] = []
    
    state['errors'].append({
        'node': node_name,
        'error_type': error_info.error_type.value,
        'error_message': error_info.error_message,
        'error_details': error_info.error_details,
        'timestamp': error_info.timestamp,
        'retryable': error_info.retryable,
        'recoverable': error_info.recoverable
    })
    
    # 设置错误状态
    state['error'] = error_info.error_message
    
    # 如果可恢复且有降级节点，尝试降级
    if error_info.recoverable and fallback_node:
        logger.info(f"🔄 [Error Recovery] 节点 {node_name} 错误，尝试降级节点")
        try:
            import asyncio
            if asyncio.iscoroutinefunction(fallback_node):
                return asyncio.run(fallback_node(state))
            else:
                return fallback_node(state)
        except Exception as fallback_error:
            logger.error(f"❌ [Error Recovery] 降级节点也失败: {fallback_error}")
    
    return state

