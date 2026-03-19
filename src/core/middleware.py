#!/usr/bin/env python3
"""
Middleware System - 中间件系统

借鉴 Open SWE 的 Middleware 架构:
- check_message_queue: 消息队列检查
- open_pr_if_needed: PR 自动开启
- tool_error_handler: 工具错误处理

提供可插拔的中间件架构，支持:
- 请求/响应拦截
- 错误处理
- 日志记录
- 性能监控
- 缓存
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic
from enum import Enum
from functools import wraps
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MiddlewarePhase(Enum):
    """中间件执行阶段"""
    PRE_PROCESS = "pre_process"      # 处理前
    PROCESS = "process"            # 处理中
    POST_PROCESS = "post_process"   # 处理后
    ON_ERROR = "on_error"          # 错误时


@dataclass
class MiddlewareContext:
    """中间件上下文"""
    request_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def add_error(self, error: str):
        self.errors.append(error)
    
    def get_duration(self) -> float:
        return time.time() - self.start_time


@dataclass
class MiddlewareResult:
    """中间件执行结果"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    middleware_applied: List[str] = field(default_factory=list)
    duration: float = 0.0


class BaseMiddleware(ABC):
    """中间件基类"""
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
        self.enabled = True
        self.order = 0  # 执行顺序，数字越小越先执行
    
    @abstractmethod
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        """处理数据"""
        pass
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> None:
        """错误处理"""
        logger.error(f"{self.name} error: {error}")
        context.add_error(str(error))


class MiddlewareChain:
    """中间件链"""
    
    def __init__(self):
        self._middlewares: Dict[MiddlewarePhase, List[BaseMiddleware]] = {
            phase: [] for phase in MiddlewarePhase
        }
        self._global_middlewares: List[BaseMiddleware] = []
        
        logger.info("MiddlewareChain 初始化")
    
    def register(
        self, 
        middleware: BaseMiddleware,
        phase: MiddlewarePhase = MiddlewarePhase.PROCESS,
        global_middleware: bool = False
    ) -> 'MiddlewareChain':
        """
        注册中间件
        
        Args:
            middleware: 中间件实例
            phase: 执行阶段
            global_middleware: 是否为全局中间件（在所有阶段都执行）
        """
        if global_middleware:
            self._global_middlewares.append(middleware)
            logger.info(f"注册全局中间件: {middleware.name}")
        else:
            self._middlewares[phase].append(middleware)
            # 按 order 排序
            self._middlewares[phase].sort(key=lambda m: m.order)
            logger.info(f"注册中间件: {middleware.name} ({phase.value})")
        
        return self
    
    def unregister(self, name: str) -> bool:
        """注销中间件"""
        # 从全局中间件中移除
        self._global_middlewares = [
            m for m in self._global_middlewares if m.name != name
        ]
        
        # 从各阶段中移除
        for phase in MiddlewarePhase:
            self._middlewares[phase] = [
                m for m in self._middlewares[phase] if m.name != name
            ]
        
        logger.info(f"注销中间件: {name}")
        return True
    
    def get_middleware(self, name: str) -> Optional[BaseMiddleware]:
        """获取中间件"""
        # 在全局中间件中查找
        for m in self._global_middlewares:
            if m.name == name:
                return m
        
        # 在各阶段中查找
        for phase in MiddlewarePhase:
            for m in self._middlewares[phase]:
                if m.name == name:
                    return m
        
        return None
    
    def list_middlewares(self) -> Dict[str, List[str]]:
        """列出所有中间件"""
        result = {phase.value: [] for phase in MiddlewarePhase}
        result["global"] = []
        
        for m in self._global_middlewares:
            result["global"].append(m.name)
        
        for phase in MiddlewarePhase:
            for m in self._middlewares[phase]:
                result[phase.value].append(m.name)
        
        return result
    
    async def execute(
        self, 
        data: Any,
        request_id: str = None,
        metadata: Dict = None
    ) -> MiddlewareResult:
        """执行中间件链"""
        context = MiddlewareContext(
            request_id=request_id or f"req_{int(time.time() * 1000)}",
            metadata=metadata or {}
        )
        
        applied = []
        start_time = time.time()
        
        try:
            # 1. 执行全局 PRE_PROCESS 中间件
            for m in self._global_middlewares:
                if m.enabled:
                    data = await self._execute_middleware(m, context, data)
                    applied.append(m.name)
            
            # 2. 执行 PRE_PROCESS 阶段
            for m in self._middlewares[MiddlewarePhase.PRE_PROCESS]:
                if m.enabled:
                    data = await self._execute_middleware(m, context, data)
                    applied.append(m.name)
            
            # 3. 执行 PROCESS 阶段
            for m in self._middlewares[MiddlewarePhase.PROCESS]:
                if m.enabled:
                    data = await self._execute_middleware(m, context, data)
                    applied.append(m.name)
            
            # 4. 执行 POST_PROCESS 阶段
            for m in self._middlewares[MiddlewarePhase.POST_PROCESS]:
                if m.enabled:
                    data = await self._execute_middleware(m, context, data)
                    applied.append(m.name)
            
            # 5. 执行全局 POST_PROCESS
            for m in self._global_middlewares:
                if m.enabled:
                    data = await self._execute_middleware(m, context, data)
                    if m.name not in applied:
                        applied.append(m.name)
            
            return MiddlewareResult(
                success=True,
                data=data,
                middleware_applied=applied,
                duration=time.time() - start_time
            )
            
        except Exception as e:
            # 执行错误处理
            await self._execute_error_handlers(context, e)
            return MiddlewareResult(
                success=False,
                error=str(e),
                middleware_applied=applied,
                duration=time.time() - start_time
            )
    
    async def _execute_middleware(
        self, 
        middleware: BaseMiddleware, 
        context: MiddlewareContext, 
        data: Any
    ) -> Any:
        """执行单个中间件"""
        try:
            return await middleware.process(context, data)
        except Exception as e:
            await middleware.on_error(context, e)
            raise
    
    async def _execute_error_handlers(
        self, 
        context: MiddlewareContext, 
        error: Exception
    ) -> None:
        """执行错误处理"""
        for m in self._middlewares[MiddlewarePhase.ON_ERROR]:
            if m.enabled:
                try:
                    await m.on_error(context, error)
                except Exception:
                    pass  # 错误处理中不抛出异常


# ==================== 常用中间件实现 ====================

class LoggingMiddleware(BaseMiddleware):
    """日志中间件"""
    
    def __init__(self):
        super().__init__("LoggingMiddleware")
        self.order = -100  # 最先执行
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        logger.info(f"[{context.request_id}] 开始处理")
        return data


class TimingMiddleware(BaseMiddleware):
    """性能计时中间件"""
    
    def __init__(self):
        super().__init__("TimingMiddleware")
        self.order = 100  # 最后执行
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        duration = context.get_duration()
        logger.info(f"[{context.request_id}] 处理完成，耗时: {duration:.3f}s")
        context.metadata["duration"] = duration
        return data


class ErrorHandlerMiddleware(BaseMiddleware):
    """错误处理中间件"""
    
    def __init__(self, error_handler: Callable = None):
        super().__init__("ErrorHandlerMiddleware")
        self.error_handler = error_handler
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> None:
        if self.error_handler:
            self.error_handler(context, error)
        else:
            logger.error(f"[{context.request_id}] 错误: {error}")


class ValidationMiddleware(BaseMiddleware):
    """验证中间件"""
    
    def __init__(self, validator: Callable[[Any], bool]):
        super().__init__("ValidationMiddleware")
        self.validator = validator
        self.order = -50
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        if not self.validator(data):
            raise ValueError("数据验证失败")
        return data


class CacheMiddleware(BaseMiddleware):
    """缓存中间件"""
    
    def __init__(self, cache_get: Callable, cache_set: Callable):
        super().__init__("CacheMiddleware")
        self.cache_get = cache_get
        self.cache_set = cache_set
        self.order = -90  # 很早执行，检查缓存
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        cache_key = context.metadata.get("cache_key")
        
        if cache_key:
            cached = self.cache_get(cache_key)
            if cached is not None:
                context.metadata["cache_hit"] = True
                logger.info(f"[{context.request_id}] 缓存命中: {cache_key}")
                return cached
        
        context.metadata["cache_hit"] = False
        return data


class RateLimitMiddleware(BaseMiddleware):
    """限流中间件"""
    
    def __init__(self, check_limit: Callable, window: int = 60):
        super().__init__("RateLimitMiddleware")
        self.check_limit = check_limit
        self.window = window
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        if not self.check_limit(context.request_id, self.window):
            raise Exception("请求频率超限")
        return data


# ==================== Open SWE 风格的中间件 ====================

class MessageQueueChecker(BaseMiddleware):
    """消息队列检查中间件（借鉴 Open SWE）"""
    
    def __init__(self, queue_checker: Callable):
        super().__init__("MessageQueueChecker")
        self.queue_checker = queue_checker
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        queue_status = self.queue_checker()
        
        if queue_status.get("blocked", False):
            context.metadata["queue_blocked"] = True
            logger.warning(f"[{context.request_id}] 消息队列阻塞: {queue_status}")
            raise Exception(f"消息队列阻塞: {queue_status.get('reason', 'unknown')}")
        
        context.metadata["queue_status"] = queue_status
        return data


class ToolErrorHandler(BaseMiddleware):
    """工具错误处理中间件（借鉴 Open SWE）"""
    
    def __init__(self, max_retries: int = 3):
        super().__init__("ToolErrorHandler")
        self.max_retries = max_retries
    
    async def on_error(self, context: MiddlewareContext, error: Exception) -> None:
        retries = context.metadata.get("retry_count", 0)
        
        if retries < self.max_retries:
            context.metadata["retry_count"] = retries + 1
            logger.info(f"[{context.request_id}] 重试 ({retries + 1}/{self.max_retries})")
        else:
            context.metadata["max_retries_exceeded"] = True
            logger.error(f"[{context.request_id}] 超过最大重试次数")


class PRCheckerMiddleware(BaseMiddleware):
    """PR 检查中间件（借鉴 Open SWE）"""
    
    def __init__(self, pr_checker: Callable):
        super().__init__("PRCheckerMiddleware")
        self.pr_checker = pr_checker
    
    async def process(self, context: MiddlewareContext, data: Any) -> Any:
        pr_status = self.pr_checker(context.metadata.get("pr_id"))
        
        if not pr_status.get("can_merge", False):
            context.metadata["pr_blocked"] = True
            context.metadata["pr_blocked_reason"] = pr_status.get("reason")
            logger.warning(f"[{context.request_id}] PR 被阻止: {pr_status.get('reason')}")
        
        context.metadata["pr_status"] = pr_status
        return data


# ==================== 全局中间件管理器 ====================

_middleware_chain: Optional[MiddlewareChain] = None


def get_middleware_chain() -> MiddlewareChain:
    """获取全局中间件链"""
    global _middleware_chain
    if _middleware_chain is None:
        _middleware_chain = MiddlewareChain()
        # 注册默认中间件
        _middleware_chain.register(LoggingMiddleware())
        _middleware_chain.register(TimingMiddleware())
    return _middleware_chain


def register_middleware(
    middleware: BaseMiddleware,
    phase: MiddlewarePhase = MiddlewarePhase.PROCESS
) -> None:
    """注册中间件到全局链"""
    get_middleware_chain().register(middleware, phase)


def execute_middleware(data: Any, request_id: str = None) -> MiddlewareResult:
    """执行全局中间件链"""
    return get_middleware_chain().execute(data, request_id)
