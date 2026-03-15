#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强事件系统 - 受Paperclip回调系统启发的强大事件机制

设计原则：
1. 类型安全：使用类型提示和dataclass定义事件数据
2. 异步优先：原生支持异步事件处理
3. 可观察性：事件历史记录和追踪
4. 过滤机制：基于条件的订阅
5. 错误隔离：事件处理器错误不影响主流程
6. 性能优化：批量处理和事件合并

示例用法：

# 定义事件
@dataclass
class ModelRegisteredEvent:
    model_name: str
    model_type: str
    timestamp: datetime

# 订阅事件
@event_bus.subscribe("model.registered", filter=lambda e: e.model_type == "llm")
async def handle_model_registered(event: ModelRegisteredEvent):
    print(f"模型已注册: {event.model_name}")

# 发布事件
await event_bus.publish("model.registered", ModelRegisteredEvent(
    model_name="deepseek-reasoner",
    model_type="llm",
    timestamp=datetime.now()
))
"""

import asyncio
import logging
import inspect
import time
from typing import Dict, Any, List, Optional, Union, Callable, Type, TypeVar, Generic
from dataclasses import dataclass, field, asdict, is_dataclass
from enum import Enum
from datetime import datetime
import threading
from collections import defaultdict
import hashlib
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class EventPriority(Enum):
    """事件优先级"""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    CRITICAL = 5


class EventError(Exception):
    """事件错误基类"""
    pass


@dataclass
class EventMetadata:
    """事件元数据"""
    event_id: str
    event_type: str
    timestamp: datetime
    source: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    retry_count: int = 0
    processing_time_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['priority'] = self.priority.value
        return data


@dataclass
class BaseEvent:
    """事件基类"""
    metadata: EventMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        data['metadata'] = self.metadata.to_dict()
        return data


# 预定义事件类型
class EventTypes:
    """事件类型常量"""
    # 配置相关
    CONFIG_REGISTERED = "config.registered"
    CONFIG_UPDATED = "config.updated"
    CONFIG_DELETED = "config.deleted"
    CONFIG_LOADED = "config.loaded"
    CONFIG_SAVED = "config.saved"
    
    # 模型相关
    MODEL_REGISTERED = "model.registered"
    MODEL_UNREGISTERED = "model.unregistered"
    MODEL_SELECTED = "model.selected"
    MODEL_REJECTED = "model.rejected"
    
    # 路由相关
    ROUTING_STARTED = "routing.started"
    ROUTING_COMPLETED = "routing.completed"
    ROUTING_FAILED = "routing.failed"
    ROUTING_DECISION = "routing.decision"
    
    # 处理器相关
    PROCESSOR_STARTED = "processor.started"
    PROCESSOR_COMPLETED = "processor.completed"
    PROCESSOR_FAILED = "processor.failed"
    PROCESSOR_SKIPPED = "processor.skipped"
    
    # 存储相关
    STORAGE_SAVED = "storage.saved"
    STORAGE_LOADED = "storage.loaded"
    STORAGE_ERROR = "storage.error"
    
    # 系统相关
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    
    # 性能相关
    PERFORMANCE_METRIC = "performance.metric"
    LATENCY_MEASURED = "latency.measured"
    COST_CALCULATED = "cost.calculated"


# 具体事件定义
@dataclass
class ConfigRegisteredEvent(BaseEvent):
    """配置注册事件"""
    config_type: str  # "llm_model", "routing_strategy", "processor"
    config_name: str
    config_data: Dict[str, Any]
    source_class: Optional[str] = None


@dataclass
class ModelSelectedEvent(BaseEvent):
    """模型选择事件"""
    request_id: str
    model_name: str
    model_provider: str
    selection_reason: str
    cost_estimate: float
    latency_estimate: float
    alternatives: List[str] = field(default_factory=list)


@dataclass
class RoutingDecisionEvent(BaseEvent):
    """路由决策事件"""
    request_id: str
    selected_model: str
    decision_factors: Dict[str, Any]
    processing_time_ms: float
    success: bool
    error_message: Optional[str] = None


@dataclass
class StorageOperationEvent(BaseEvent):
    """存储操作事件"""
    operation: str  # "save", "load", "delete"
    storage_type: str  # "memory", "file", "redis", "database"
    key: str
    success: bool
    duration_ms: float
    error_message: Optional[str] = None


@dataclass
class PerformanceMetricEvent(BaseEvent):
    """性能指标事件"""
    metric_name: str
    metric_value: float
    metric_unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[datetime] = None


class EventFilter:
    """事件过滤器"""
    
    def __init__(self, condition: Optional[Callable[[Any], bool]] = None):
        self.condition = condition
    
    def matches(self, event: Any) -> bool:
        """检查事件是否匹配过滤器"""
        if self.condition is None:
            return True
        
        try:
            return self.condition(event)
        except Exception as e:
            logger.error(f"事件过滤器执行失败: {e}")
            return False
    
    @staticmethod
    def by_type(event_type: str) -> 'EventFilter':
        """按事件类型过滤"""
        return EventFilter(lambda e: e.metadata.event_type == event_type)
    
    @staticmethod
    def by_source(source: str) -> 'EventFilter':
        """按事件源过滤"""
        return EventFilter(lambda e: e.metadata.source == source)
    
    @staticmethod
    def by_priority(min_priority: EventPriority) -> 'EventFilter':
        """按最小优先级过滤"""
        return EventFilter(lambda e: e.metadata.priority.value >= min_priority.value)
    
    @staticmethod
    def combine(*filters: 'EventFilter') -> 'EventFilter':
        """组合多个过滤器"""
        def combined_condition(event):
            return all(f.matches(event) for f in filters)
        return EventFilter(combined_condition)


class EventHandler:
    """事件处理器包装器"""
    
    def __init__(
        self,
        handler: Callable,
        event_type: str,
        filter: Optional[EventFilter] = None,
        priority: int = 0,
        async_execution: bool = True,
        max_retries: int = 0,
        timeout_seconds: Optional[float] = None
    ):
        self.handler = handler
        self.event_type = event_type
        self.filter = filter or EventFilter()
        self.priority = priority  # 处理器优先级（数字越小越优先）
        self.async_execution = async_execution
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # 统计信息
        self.invocation_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_processing_time = 0.0
    
    async def handle(self, event: Any) -> bool:
        """处理事件"""
        start_time = time.time()
        self.invocation_count += 1
        
        # 检查过滤器
        if not self.filter.matches(event):
            return False
        
        try:
            # 设置超时
            if self.timeout_seconds:
                try:
                    if self.async_execution and inspect.iscoroutinefunction(self.handler):
                        result = await asyncio.wait_for(
                            self.handler(event),
                            timeout=self.timeout_seconds
                        )
                    else:
                        # 同步函数在异步上下文中执行
                        result = await asyncio.to_thread(self.handler, event)
                except asyncio.TimeoutError:
                    logger.warning(f"事件处理器超时: {self.handler.__name__}")
                    self.failure_count += 1
                    return False
            else:
                # 无超时
                if self.async_execution and inspect.iscoroutinefunction(self.handler):
                    result = await self.handler(event)
                else:
                    result = await asyncio.to_thread(self.handler, event)
            
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            self.success_count += 1
            
            logger.debug(f"事件处理器执行成功: {self.handler.__name__}, 耗时: {processing_time:.3f}s")
            return True
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.total_processing_time += processing_time
            self.failure_count += 1
            
            logger.error(f"事件处理器执行失败 {self.handler.__name__}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        avg_time = (self.total_processing_time / self.invocation_count 
                   if self.invocation_count > 0 else 0)
        
        return {
            "handler_name": self.handler.__name__,
            "event_type": self.event_type,
            "invocation_count": self.invocation_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (self.success_count / self.invocation_count 
                           if self.invocation_count > 0 else 0),
            "total_processing_time": self.total_processing_time,
            "average_processing_time": avg_time,
            "async_execution": self.async_execution,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
        }


class EventHistory:
    """事件历史记录"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.events: List[Dict[str, Any]] = []
        self._lock = threading.RLock()
    
    def add(self, event: Any, processed: bool = True, error: Optional[str] = None):
        """添加事件到历史记录"""
        with self._lock:
            # 创建历史记录条目
            if hasattr(event, 'to_dict'):
                event_data = event.to_dict()
            elif is_dataclass(event):
                event_data = asdict(event)
            elif isinstance(event, dict):
                event_data = event.copy()
            else:
                event_data = {"event": str(event)}
            
            history_entry = {
                "timestamp": datetime.now().isoformat(),
                "event": event_data,
                "processed": processed,
                "error": error,
            }
            
            self.events.append(history_entry)
            
            # 限制历史记录大小
            if len(self.events) > self.max_size:
                self.events = self.events[-self.max_size:]
    
    def query(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询历史事件"""
        with self._lock:
            results = []
            
            for entry in reversed(self.events):  # 从最新开始
                if limit <= 0:
                    break
                
                # 过滤事件类型
                if event_type:
                    event_data = entry["event"]
                    if isinstance(event_data, dict) and "metadata" in event_data:
                        if event_data["metadata"].get("event_type") != event_type:
                            continue
                
                # 过滤时间范围
                if start_time or end_time:
                    entry_time = datetime.fromisoformat(entry["timestamp"].replace('Z', '+00:00'))
                    
                    if start_time and entry_time < start_time:
                        continue
                    if end_time and entry_time > end_time:
                        continue
                
                results.append(entry)
                limit -= 1
            
            return results
    
    def clear(self):
        """清空历史记录"""
        with self._lock:
            self.events.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            event_types = {}
            for entry in self.events:
                event_data = entry["event"]
                if isinstance(event_data, dict) and "metadata" in event_data:
                    event_type = event_data["metadata"].get("event_type", "unknown")
                    event_types[event_type] = event_types.get(event_type, 0) + 1
            
            return {
                "total_events": len(self.events),
                "event_types": event_types,
                "max_size": self.max_size,
            }


class EventBus:
    """事件总线"""
    
    def __init__(self, enable_history: bool = True, max_history_size: int = 1000):
        self._handlers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history = EventHistory(max_history_size) if enable_history else None
        
        # 统计信息
        self._stats = {
            "events_published": 0,
            "events_processed": 0,
            "handler_errors": 0,
            "start_time": datetime.now().isoformat()
        }
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable,
        filter: Optional[EventFilter] = None,
        priority: int = 0,
        async_execution: bool = True,
        max_retries: int = 0,
        timeout_seconds: Optional[float] = None
    ) -> EventHandler:
        """订阅事件"""
        event_handler = EventHandler(
            handler=handler,
            event_type=event_type,
            filter=filter,
            priority=priority,
            async_execution=async_execution,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        
        with self._lock:
            self._handlers[event_type].append(event_handler)
            # 按优先级排序（数字越小越优先）
            self._handlers[event_type].sort(key=lambda h: h.priority)
            
            logger.info(f"事件处理器已注册: {event_type} -> {handler.__name__}")
        
        return event_handler
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """取消订阅事件"""
        with self._lock:
            if event_type not in self._handlers:
                return False
            
            # 查找并移除处理器
            original_count = len(self._handlers[event_type])
            self._handlers[event_type] = [
                h for h in self._handlers[event_type]
                if h.handler != handler
            ]
            
            removed = len(self._handlers[event_type]) < original_count
            if removed:
                logger.info(f"事件处理器已移除: {event_type} -> {handler.__name__}")
            
            # 如果事件类型没有处理器，删除键
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            
            return removed
    
    async def publish(
        self,
        event_type: str,
        event_data: Any,
        source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        wait_for_processing: bool = False
    ) -> bool:
        """发布事件"""
        # 生成事件ID
        event_id = hashlib.md5(
            f"{event_type}:{datetime.now().isoformat()}:{id(event_data)}".encode()
        ).hexdigest()[:16]
        
        # 创建事件元数据
        metadata = EventMetadata(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(),
            source=source,
            correlation_id=correlation_id,
            priority=priority
        )
        
        # 包装事件数据
        event = event_data
        if not hasattr(event, 'metadata'):
            # 如果事件数据不是BaseEvent子类，创建一个包装器
            if is_dataclass(event_data):
                # 动态创建包装类
                @dataclass
                class WrappedEvent(BaseEvent):
                    data: Any = event_data
                
                event = WrappedEvent(metadata=metadata)
            else:
                # 简单包装
                @dataclass
                class SimpleEvent(BaseEvent):
                    data: Any = field(default_factory=lambda: event_data)
                
                event = SimpleEvent(metadata=metadata)
        else:
            # 更新现有事件的元数据
            event.metadata = metadata
        
        # 记录到历史
        if self._history:
            self._history.add(event, processed=False)
        
        # 更新统计
        with self._lock:
            self._stats["events_published"] += 1
        
        # 获取处理器
        handlers = []
        with self._lock:
            # 获取指定事件类型的处理器
            handlers.extend(self._handlers.get(event_type, []))
            
            # 获取通配符处理器
            if "*" in self._handlers:
                handlers.extend(self._handlers["*"])
        
        if not handlers:
            logger.debug(f"事件无处理器: {event_type}")
            
            # 标记为已处理
            if self._history:
                self._history.add(event, processed=True)
            
            return True
        
        # 执行处理器
        processing_tasks = []
        for handler in handlers:
            if wait_for_processing:
                # 同步等待处理器完成
                success = await handler.handle(event)
                if not success:
                    with self._lock:
                        self._stats["handler_errors"] += 1
            else:
                # 异步执行，不等待
                task = asyncio.create_task(handler.handle(event))
                processing_tasks.append((handler, task))
        
        # 等待异步任务完成（如果需要）
        if processing_tasks and wait_for_processing:
            for handler, task in processing_tasks:
                try:
                    success = await task
                    if not success:
                        with self._lock:
                            self._stats["handler_errors"] += 1
                except Exception as e:
                    logger.error(f"事件处理器任务失败 {handler.handler.__name__}: {e}")
                    with self._lock:
                        self._stats["handler_errors"] += 1
        
        # 更新统计
        with self._lock:
            self._stats["events_processed"] += 1
        
        # 标记为已处理
        if self._history:
            self._history.add(event, processed=True)
        
        logger.debug(f"事件已发布: {event_type} (ID: {event_id})")
        return True
    
    def get_handler_stats(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取处理器统计信息"""
        with self._lock:
            stats = {}
            for event_type, handlers in self._handlers.items():
                stats[event_type] = [h.get_stats() for h in handlers]
            return stats
    
    def get_bus_stats(self) -> Dict[str, Any]:
        """获取事件总线统计信息"""
        with self._lock:
            stats = self._stats.copy()
            stats["handler_count"] = sum(len(handlers) for handlers in self._handlers.values())
            stats["event_types"] = list(self._handlers.keys())
            
            if self._history:
                stats["history"] = self._history.get_stats()
            
            return stats
    
    def clear_handlers(self, event_type: Optional[str] = None):
        """清空处理器"""
        with self._lock:
            if event_type:
                if event_type in self._handlers:
                    del self._handlers[event_type]
                    logger.info(f"已清空事件类型处理器: {event_type}")
            else:
                self._handlers.clear()
                logger.info("已清空所有事件处理器")
    
    def get_history(self) -> Optional[EventHistory]:
        """获取事件历史记录"""
        return self._history


# 全局事件总线实例
_event_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus(enable_history=True, max_history_size=2000)
        logger.info("全局事件总线已初始化")
    return _event_bus


def set_event_bus(event_bus: EventBus):
    """设置全局事件总线实例"""
    global _event_bus
    _event_bus = event_bus


# ============================================================================
# 装饰器接口
# ============================================================================

def event_subscriber(
    event_type: str,
    filter: Optional[EventFilter] = None,
    priority: int = 0,
    async_execution: bool = True,
    max_retries: int = 0,
    timeout_seconds: Optional[float] = None
):
    """事件订阅者装饰器"""
    def decorator(func):
        event_bus = get_event_bus()
        event_bus.subscribe(
            event_type=event_type,
            handler=func,
            filter=filter,
            priority=priority,
            async_execution=async_execution,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        return func
    return decorator


# 常用事件订阅装饰器
def on_config_registered(filter: Optional[EventFilter] = None, **kwargs):
    """配置注册事件装饰器"""
    return event_subscriber(EventTypes.CONFIG_REGISTERED, filter=filter, **kwargs)


def on_model_selected(filter: Optional[EventFilter] = None, **kwargs):
    """模型选择事件装饰器"""
    return event_subscriber(EventTypes.MODEL_SELECTED, filter=filter, **kwargs)


def on_routing_decision(filter: Optional[EventFilter] = None, **kwargs):
    """路由决策事件装饰器"""
    return event_subscriber(EventTypes.ROUTING_DECISION, filter=filter, **kwargs)


def on_storage_operation(filter: Optional[EventFilter] = None, **kwargs):
    """存储操作事件装饰器"""
    return event_subscriber(EventTypes.STORAGE_SAVED, filter=filter, **kwargs)


# ============================================================================
# 与现有系统的集成助手
# ============================================================================

class EventSystemIntegration:
    """事件系统集成助手"""
    
    @staticmethod
    def integrate_with_config_registry(config_registry):
        """与配置注册表集成"""
        event_bus = get_event_bus()
        
        # 监听配置注册事件
        @event_subscriber(EventTypes.CONFIG_REGISTERED)
        async def handle_config_registered(event: ConfigRegisteredEvent):
            # 这里可以添加业务逻辑，如：
            # - 验证配置
            # - 更新缓存
            # - 发送通知
            logger.debug(f"配置已注册: {event.config_type}/{event.config_name}")
        
        # 为现有事件添加适配器
        original_emit = config_registry.emit_event
        
        def enhanced_emit(event_type: str, **kwargs):
            # 调用原始方法
            original_emit(event_type, **kwargs)
            
            # 准备事件数据
            event_data = kwargs.get('event_data')
            
            # 如果提供了event_data且是BaseEvent子类，直接使用
            if event_data is not None and hasattr(event_data, 'metadata'):
                # 已经是事件对象
                pass
            else:
                # 构建事件数据字典
                event_data = {
                    "event_type": event_type,
                    **kwargs
                }
            
            # 异步发布，不等待
            asyncio.create_task(
                event_bus.publish(
                    event_type=f"config.{event_type}",
                    event_data=event_data,
                    source="config_registry"
                )
            )
        
        # 替换方法
        config_registry.emit_event = enhanced_emit
        
        logger.info("事件系统已与配置注册表集成")
    
    @staticmethod
    def integrate_with_processor_chain(processor_chain):
        """与处理器链集成"""
        event_bus = get_event_bus()
        
        # 保存原始execute方法
        original_execute = processor_chain.execute
        
        async def instrumented_execute(context):
            # 发布路由开始事件
            await event_bus.publish(
                EventTypes.ROUTING_STARTED,
                event_data={
                    "request_id": context.get("request_id", "unknown"),
                    "context": context,
                },
                source="processor_chain"
            )
            
            start_time = time.time()
            
            try:
                # 执行原始逻辑
                result = await original_execute(context)
                
                processing_time = time.time() - start_time
                
                # 发布路由完成事件
                await event_bus.publish(
                    EventTypes.ROUTING_COMPLETED,
                    event_data={
                        "request_id": context.get("request_id", "unknown"),
                        "processing_time_ms": processing_time * 1000,
                        "success": True,
                        "result": result,
                    },
                    source="processor_chain"
                )
                
                return result
                
            except Exception as e:
                processing_time = time.time() - start_time
                
                # 发布路由失败事件
                await event_bus.publish(
                    EventTypes.ROUTING_FAILED,
                    event_data={
                        "request_id": context.get("request_id", "unknown"),
                        "processing_time_ms": processing_time * 1000,
                        "error": str(e),
                        "success": False,
                    },
                    source="processor_chain"
                )
                
                raise
        
        # 替换方法
        processor_chain.execute = instrumented_execute
        
        logger.info("事件系统已与处理器链集成")