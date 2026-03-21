"""
Circuit Breaker Implementation
用于保护系统免受下游服务故障的影响。
"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "CLOSED"     # 正常状态
    OPEN = "OPEN"         # 熔断状态
    HALF_OPEN = "HALF_OPEN" # 半开状态

class CircuitBreakerOpenError(Exception):
    """当熔断器处于打开状态时抛出的异常"""
    pass

class CircuitBreaker:
    """
    带状态机的熔断器
    
    States:
    - CLOSED: 允许请求。失败计数达到阈值 -> OPEN。
    - OPEN: 拒绝请求 (抛出异常)。冷却时间过后 -> HALF_OPEN。
    - HALF_OPEN: 允许一次试探性请求。成功 -> CLOSED。失败 -> OPEN。
    """
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, name: str = "default"):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = threading.RLock() # 线程安全
        
    @property
    def state(self) -> CircuitState:
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        执行受保护的函数调用
        """
        with self._lock:
            self._check_state_transition()
            
            if self._state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(f"Circuit Breaker '{self.name}' is OPEN")
            
            if self._state == CircuitState.HALF_OPEN:
                # 半开状态：只允许这一个请求通过（由于锁的存在，其他并发请求会看到 OPEN 或等待）
                # 如果我们想严格限制并发，这里逻辑是正确的：
                # 第一个拿到锁的请求执行，如果成功则Close，失败则Open
                pass

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            # 某些异常可能不应该触发熔断（如业务逻辑错误），但这里假设所有异常都是故障
            # 调用者可以通过包装 func 来过滤异常
            self._on_failure()
            raise e

    def _check_state_transition(self):
        """检查是否应该从 OPEN 转换到 HALF_OPEN"""
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed > self.recovery_timeout:
                logger.info(f"Circuit Breaker '{self.name}': Cooling time elapsed ({elapsed:.1f}s > {self.recovery_timeout}s). State -> HALF_OPEN")
                self._state = CircuitState.HALF_OPEN

    def _on_success(self):
        """请求成功时的回调"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit Breaker '{self.name}': Trial request SUCCESS. State -> CLOSED")
                self._state = CircuitState.CLOSED
                self._failure_count = 0
            elif self._state == CircuitState.CLOSED:
                # 正常状态下成功，重置计数器（可选，这里选择重置以实现连续失败才熔断）
                if self._failure_count > 0:
                    self._failure_count = 0

    def _on_failure(self):
        """请求失败时的回调"""
        with self._lock:
            self._last_failure_time = time.time()
            
            if self._state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit Breaker '{self.name}': Trial request FAILED. State -> OPEN")
                self._state = CircuitState.OPEN
                # 保持 OPEN 状态，重置冷却时间
                
            elif self._state == CircuitState.CLOSED:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit Breaker '{self.name}': Failure threshold reached ({self._failure_count}). State -> OPEN")
                    self._state = CircuitState.OPEN
