"""
Event Bus - 事件总线

提供事件驱动的通信机制
参考 OpenClaw 的事件驱动架构
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any, Awaitable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    # 生命周期事件
    GATEWAY_STARTED = "gateway_started"
    GATEWAY_STOPPED = "gateway_stopped"
    
    # 渠道事件
    CHANNEL_REGISTERED = "channel_registered"
    CHANNEL_UNREGISTERED = "channel_unregistered"
    CHANNEL_MESSAGE_SENT = "channel_message_sent"
    CHANNEL_MESSAGE_RECEIVED = "channel_message_received"
    
    # 消息事件
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_PROCESSED = "message_processed"
    MESSAGE_FAILED = "message_failed"
    
    # Agent 事件
    AGENT_STARTED = "agent_started"
    AGENT_THINKING = "agent_thinking"
    AGENT_ACTING = "agent_acting"
    AGENT_OBSERVING = "agent_observing"
    AGENT_COMPLETED = "agent_completed"
    AGENT_ERROR = "agent_error"
    
    # 工具事件
    TOOL_INVOKED = "tool_invoked"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"
    
    # 记忆事件
    MEMORY_LOADED = "memory_loaded"
    MEMORY_SAVED = "memory_saved"
    MEMORY_COMPACTED = "memory_compacted"
    
    # 系统事件
    HEARTBEAT = "heartbeat"
    KILL_SWITCH_ACTIVATED = "kill_switch_activated"
    KILL_SWITCH_DEACTIVATED = "kill_switch_deactivated"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"


@dataclass
class Event:
    """事件数据"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }


EventHandler = Callable[[Event], Awaitable[None]]


class EventBus:
    """
    事件总线
    
    提供发布-订阅模式的事件通信
    """
    
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self._handlers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._running = False
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self._worker_task: Optional[asyncio.Task] = None
        
        # 事件统计
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "events_dropped": 0
        }
    
    async def start(self):
        """启动事件总线"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("EventBus started")
    
    async def stop(self):
        """停止事件总线"""
        if not self._running:
            return
        
        self._running = False
        
        # 等待队列处理完成
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"EventBus stopped. Stats: {self.stats}")
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """订阅事件"""
        self._handlers[event_type].append(handler)
        logger.debug(f"Subscribed handler to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """取消订阅"""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Unsubscribed handler from {event_type.value}")
    
    async def emit(self, event: Event):
        """发布事件"""
        self.stats["events_published"] += 1
        
        try:
            # 尝试将事件放入队列
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            self.stats["events_dropped"] += 1
            logger.warning(f"Event queue full, dropping event: {event.type.value}")
    
    async def emit_sync(self, event: Event):
        """同步发布事件（立即处理）"""
        await self._handle_event(event)
    
    async def _process_events(self):
        """事件处理循环"""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._handle_event(event)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _handle_event(self, event: Event):
        """处理单个事件"""
        handlers = self._handlers.get(event.type, [])
        
        if not handlers:
            return
        
        # 创建任务处理所有处理器
        tasks = []
        for handler in handlers:
            try:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating handler task: {e}")
        
        # 等待所有处理器完成
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.stats["events_processed"] += 1
    
    def get_stats(self) -> Dict:
        """获取事件统计"""
        return {
            **self.stats,
            "queue_size": self._event_queue.qsize(),
            "subscribed_types": [et.value for et in self._handlers.keys()],
            "total_handlers": sum(len(h) for h in self._handlers.values())
        }


# ==================== 便捷函数 ====================

class EventBusMixin:
    """Mixin 类，提供事件总线便捷访问"""
    
    @property
    def event_bus(self) -> EventBus:
        """获取事件总线"""
        # 子类需要实现
        raise NotImplementedError
