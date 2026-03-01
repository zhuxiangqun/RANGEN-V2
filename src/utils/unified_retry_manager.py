#!/usr/bin/env python3
"""
统一重试管理器 - Unified Retry Manager
统一处理核心系统中的所有重试逻辑
"""
import logging
import time
import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(Enum):
    """重试策略"""
    FIXED = "fixed"  # 固定延迟
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性增长


class UnifiedRetryManager:
    """统一重试管理器 - 统一处理所有重试逻辑"""
    
    _instance: Optional['UnifiedRetryManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化统一重试管理器"""
        if self._initialized:
            return
        
        self.logger = logging.getLogger(__name__)
        self._initialized = True
        
        # 从配置中心加载重试配置
        self._load_retry_config()
    
    def _load_retry_config(self):
        """从配置中心加载重试配置"""
        try:
            from src.utils.unified_centers import get_unified_config_center
            from src.utils.unified_rule_manager import get_unified_rule_manager
            
            config_center = get_unified_config_center()
            rule_manager = get_unified_rule_manager()
            
            # 从rules.yaml读取重试配置
            if rule_manager:
                # 🚀 修复：get_threshold方法不接受default参数，需要手动处理默认值
                max_attempts_val = rule_manager.get_threshold('retry.default_max_attempts', context={})
                self.max_attempts = int(max_attempts_val) if max_attempts_val != 0.5 else 2  # 0.5是默认值，表示未找到配置
                
                ssl_max_attempts_val = rule_manager.get_threshold('retry.ssl_max_attempts', context={})
                self.ssl_max_attempts = int(ssl_max_attempts_val) if ssl_max_attempts_val != 0.5 else 4
                
                absolute_max_attempts_val = rule_manager.get_threshold('retry.max_attempts', context={})
                self.absolute_max_attempts = int(absolute_max_attempts_val) if absolute_max_attempts_val != 0.5 else 5
                
                base_delay_val = rule_manager.get_threshold('retry.delay.base', context={})
                self.base_delay = float(base_delay_val) if base_delay_val != 0.5 else 1.0
                
                max_delay_val = rule_manager.get_threshold('retry.delay.max', context={})
                self.max_delay = float(max_delay_val) if max_delay_val != 0.5 else 30.0
                
                exponential_backoff_val = rule_manager.get_threshold('retry.delay.exponential_backoff', context={})
                self.exponential_backoff = bool(exponential_backoff_val) if exponential_backoff_val != 0.5 else True
            else:
                # Fallback: 使用默认值
                self.max_attempts = 2
                self.ssl_max_attempts = 4
                self.absolute_max_attempts = 5
                self.base_delay = 1.0
                self.max_delay = 30.0
                self.exponential_backoff = True
                
        except Exception as e:
            self.logger.warning(f"⚠️ 加载重试配置失败: {e}，使用默认值")
            # Fallback: 使用默认值
            self.max_attempts = 2
            self.ssl_max_attempts = 4
            self.absolute_max_attempts = 5
            self.base_delay = 1.0
            self.max_delay = 30.0
            self.exponential_backoff = True
    
    def get_max_attempts(self, retry_type: str = "default") -> int:
        """获取最大重试次数
        
        Args:
            retry_type: 重试类型（default, ssl, absolute）
            
        Returns:
            最大重试次数
        """
        if retry_type == "ssl":
            return int(self.ssl_max_attempts)
        elif retry_type == "absolute":
            return int(self.absolute_max_attempts)
        else:
            return int(self.max_attempts)
    
    def calculate_delay(self, attempt: int, strategy: RetryStrategy = RetryStrategy.EXPONENTIAL) -> float:
        """计算重试延迟
        
        Args:
            attempt: 当前尝试次数（从0开始）
            strategy: 重试策略
            
        Returns:
            延迟时间（秒）
        """
        if strategy == RetryStrategy.EXPONENTIAL and self.exponential_backoff:
            # 指数退避: base_delay * (2 ^ attempt)
            delay = self.base_delay * (2 ** attempt)
        elif strategy == RetryStrategy.LINEAR:
            # 线性增长: base_delay * (attempt + 1)
            delay = self.base_delay * (attempt + 1)
        else:
            # 固定延迟
            delay = self.base_delay
        
        # 限制最大延迟
        return min(float(delay), float(self.max_delay))
    
    def retry(
        self,
        func: Callable[[], T],
        max_attempts: Optional[int] = None,
        retry_type: str = "default",
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        should_retry: Optional[Callable[[Exception], bool]] = None
    ) -> T:
        """同步重试执行
        
        Args:
            func: 要执行的函数
            max_attempts: 最大尝试次数（如果为None，使用配置的默认值）
            retry_type: 重试类型（default, ssl, absolute）
            strategy: 重试策略
            on_retry: 重试回调函数（attempt, error）
            should_retry: 判断是否应该重试的函数（error） -> bool
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次尝试的异常
        """
        if max_attempts is None:
            max_attempts = self.get_max_attempts(retry_type)
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                last_exception = e
                
                # 检查是否应该重试
                if should_retry and not should_retry(e):
                    raise e
                
                # 如果是最后一次尝试，不再重试
                if attempt >= max_attempts - 1:
                    break
                
                # 计算延迟
                delay = self.calculate_delay(attempt, strategy)
                
                # 调用重试回调
                if on_retry:
                    try:
                        on_retry(attempt, e)
                    except Exception:
                        pass
                
                # 等待后重试
                self.logger.debug(f"重试 {attempt + 1}/{max_attempts}，延迟 {delay:.2f}秒: {e}")
                time.sleep(delay)
        
        # 所有尝试都失败，抛出最后一次异常
        raise last_exception
    
    async def retry_async(
        self,
        func: Callable[[], T],
        max_attempts: Optional[int] = None,
        retry_type: str = "default",
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        should_retry: Optional[Callable[[Exception], bool]] = None
    ) -> T:
        """异步重试执行
        
        Args:
            func: 要执行的异步函数
            max_attempts: 最大尝试次数（如果为None，使用配置的默认值）
            retry_type: 重试类型（default, ssl, absolute）
            strategy: 重试策略
            on_retry: 重试回调函数（attempt, error）
            should_retry: 判断是否应该重试的函数（error） -> bool
            
        Returns:
            函数执行结果
            
        Raises:
            最后一次尝试的异常
        """
        if max_attempts is None:
            max_attempts = self.get_max_attempts(retry_type)
        
        last_exception = None
        
        for attempt in range(max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func()
                else:
                    return func()
            except Exception as e:
                last_exception = e
                
                # 检查是否应该重试
                if should_retry and not should_retry(e):
                    raise e
                
                # 如果是最后一次尝试，不再重试
                if attempt >= max_attempts - 1:
                    break
                
                # 计算延迟
                delay = self.calculate_delay(attempt, strategy)
                
                # 调用重试回调
                if on_retry:
                    try:
                        if asyncio.iscoroutinefunction(on_retry):
                            await on_retry(attempt, e)
                        else:
                            on_retry(attempt, e)
                    except Exception:
                        pass
                
                # 等待后重试
                self.logger.debug(f"重试 {attempt + 1}/{max_attempts}，延迟 {delay:.2f}秒: {e}")
                await asyncio.sleep(delay)
        
        # 所有尝试都失败，抛出最后一次异常
        raise last_exception


def get_unified_retry_manager() -> UnifiedRetryManager:
    """获取统一重试管理器实例（单例）"""
    if UnifiedRetryManager._instance is None:
        UnifiedRetryManager._instance = UnifiedRetryManager()
    return UnifiedRetryManager._instance

