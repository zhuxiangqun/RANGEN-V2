#!/usr/bin/env python3
"""
Event-driven Streaming System - 事件驱动流式传输系统

基于OpenClaw架构的真正事件流式传输:
- 不同于LangGraph的字符串解析流式传输
- 使用事件队列 + 发布/订阅模式
- 支持实时增量输出

事件类型:
- agent_thinking: Agent思考中
- agent_reasoning: Agent推理结果
- agent_action: Agent执行动作
- agent_observation: Agent观察结果
- agent_answer: Agent生成答案
- agent_error: Agent错误
- agent_complete: Agent完成
"""

import asyncio
import json
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from contextlib import asynccontextmanager
import uuid

logger = logging.getLogger(__name__)


class EventType(Enum):
    """事件类型"""
    
    # Agent生命周期事件
    AGENT_START = "agent_start"
    AGENT_THINKING = "agent_thinking"
    AGENT_REASONING = "agent_reasoning"
    AGENT_ACTION = "agent_action"
    AGENT_OBSERVATION = "agent_observation"
    AGENT_ANSWER = "agent_answer"
    AGENT_ERROR = "agent_error"
    AGENT_COMPLETE = "agent_complete"
    AGENT_STOP = "agent_stop"
    
    # 工具事件
    TOOL_START = "tool_start"
    TOOL_PROGRESS = "tool_progress"
    TOOL_COMPLETE = "tool_complete"
    TOOL_ERROR = "tool_error"
    
    # 流式事件
    STREAM_TOKEN = "stream_token"
    STREAM_CHUNK = "stream_chunk"
    
    # 系统事件
    SYSTEM_INFO = "system_info"
    SYSTEM_WARNING = "system_warning"


@dataclass
class AgentEvent:
    """Agent事件"""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.AGENT_START
    
    # 会话信息
    session_id: Optional[str] = None
    agent_id: str = ""
    
    # 内容
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    
    # 元数据
    timestamp: datetime = field(default_factory=datetime.now)
    iteration: int = 0
    step: int = 0
    
    # 流式控制
    is_final: bool = False
    is_chunk: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "iteration": self.iteration,
            "step": self.step,
            "is_final": self.is_final,
            "is_chunk": self.is_chunk
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentEvent':
        """从字典创建"""
        event_type = EventType(data.get("event_type", "agent_start"))
        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=event_type,
            session_id=data.get("session_id"),
            agent_id=data.get("agent_id", ""),
            content=data.get("content", ""),
            data=data.get("data", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            iteration=data.get("iteration", 0),
            step=data.get("step", 0),
            is_final=data.get("is_final", False),
            is_chunk=data.get("is_chunk", False)
        )


class EventStream:
    """事件流 - 事件驱动流式传输的核心"""
    
    def __init__(self, session_id: Optional[str] = None, buffer_size: int = 100):
        """
        初始化事件流
        
        Args:
            session_id: 会话ID
            buffer_size: 事件缓冲区大小
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.buffer_size = buffer_size
        
        # 事件队列
        self._event_queue: asyncio.Queue = asyncio.Queue(maxsize=buffer_size)
        
        # 订阅者
        self._subscribers: Dict[EventType, Set[Callable]] = defaultdict(set)
        self._global_subscribers: Set[Callable] = set()
        
        # 事件历史
        self._event_history: List[AgentEvent] = []
        self._max_history = 1000
        
        # 流控制
        self._is_streaming = False
        self._is_paused = False
        self._should_stop = False
        
        # 指标
        self._event_count = 0
        self._start_time = time.time()
        
        self.logger = logging.getLogger(f"{__name__}.EventStream")
    
    async def emit(self, event: AgentEvent):
        """
        发布事件
        
        Args:
            event: Agent事件
        """
        if self._should_stop:
            return
        
        # 暂停时暂时存储
        if self._is_paused:
            return
        
        try:
            # 放入队列（不阻塞）
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            # 队列满时，移除最旧的事件
            try:
                self._event_queue.get_nowait()
                self._event_queue.put_nowait(event)
            except asyncio.QueueEmpty:
                pass
        
        # 更新历史
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]
        
        # 更新计数
        self._event_count += 1
        
        # 通知订阅者
        await self._notify_subscribers(event)
    
    async def emit_simple(
        self,
        event_type: EventType,
        content: str = "",
        data: Optional[Dict[str, Any]] = None,
        agent_id: str = "",
        iteration: int = 0,
        step: int = 0,
        is_final: bool = False
    ):
        """简化的事件发布"""
        event = AgentEvent(
            event_type=event_type,
            session_id=self.session_id,
            agent_id=agent_id,
            content=content,
            data=data or {},
            iteration=iteration,
            step=step,
            is_final=is_final
        )
        await self.emit(event)
    
    def subscribe(
        self,
        handler: Callable,
        event_types: Optional[List[EventType]] = None
    ):
        """
        订阅事件
        
        Args:
            handler: 事件处理函数
            event_types: 感兴趣的事件类型列表，None表示全部
        """
        if event_types is None:
            self._global_subscribers.add(handler)
        else:
            for event_type in event_types:
                self._subscribers[event_type].add(handler)
        
        self.logger.debug(f"订阅事件: {handler.__name__}, 类型: {event_types}")
    
    def unsubscribe(
        self,
        handler: Callable,
        event_types: Optional[List[EventType]] = None
    ):
        """
        取消订阅
        
        Args:
            handler: 事件处理函数
            event_types: 取消订阅的事件类型
        """
        if event_types is None:
            self._global_subscribers.discard(handler)
        else:
            for event_type in event_types:
                self._subscribers[event_type].discard(handler)
    
    async def _notify_subscribers(self, event: AgentEvent):
        """通知订阅者"""
        # 全局订阅者
        for handler in list(self._global_subscribers):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"订阅者执行失败: {e}")
        
        # 类型特定订阅者
        for handler in list(self._subscribers.get(event.event_type, [])):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                self.logger.error(f"订阅者执行失败: {e}")
    
    async def events(self) -> AsyncIterator[AgentEvent]:
        """异步迭代事件"""
        self._is_streaming = True
        try:
            while self._is_streaming and not self._should_stop:
                try:
                    # 带超时的获取
                    event = await asyncio.wait_for(
                        self._event_queue.get(),
                        timeout=0.1
                    )
                    yield event
                except asyncio.TimeoutError:
                    # 继续等待
                    continue
                except asyncio.CancelledError:
                    break
        finally:
            self._is_streaming = False
    
    async def get_event(self, timeout: float = 1.0) -> Optional[AgentEvent]:
        """获取单个事件（带超时）"""
        try:
            return await asyncio.wait_for(
                self._event_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None
    
    def pause(self):
        """暂停事件流"""
        self._is_paused = True
        self.logger.debug("事件流已暂停")
    
    def resume(self):
        """恢复事件流"""
        self._is_paused = False
        self.logger.debug("事件流已恢复")
    
    def stop(self):
        """停止事件流"""
        self._should_stop = True
        self._is_streaming = False
        self.logger.debug("事件流已停止")
    
    def clear(self):
        """清空事件队列"""
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        self.logger.debug("事件队列已清空")
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100
    ) -> List[AgentEvent]:
        """获取事件历史"""
        if event_type is None:
            return self._event_history[-limit:]
        return [
            e for e in self._event_history
            if e.event_type == event_type
        ][-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取流指标"""
        elapsed = time.time() - self._start_time
        return {
            "session_id": self.session_id,
            "event_count": self._event_count,
            "queue_size": self._event_queue.qsize(),
            "subscriber_count": len(self._global_subscribers) + sum(
                len(s) for s in self._subscribers.values()
            ),
            "elapsed_time": elapsed,
            "events_per_second": self._event_count / elapsed if elapsed > 0 else 0,
            "is_streaming": self._is_streaming,
            "is_paused": self._is_paused,
            "should_stop": self._should_stop
        }
    
    @asynccontextmanager
    async def stream_context(self, agent_id: str):
        """流上下文管理器"""
        # 发送开始事件
        await self.emit_simple(
            EventType.AGENT_START,
            content="Agent开始执行",
            agent_id=agent_id
        )
        
        try:
            yield self
        finally:
            # 发送完成事件
            await self.emit_simple(
                EventType.AGENT_COMPLETE,
                content="Agent执行完成",
                agent_id=agent_id,
                is_final=True
            )


class StreamingFormatter:
    """流式格式化器 - 将事件转换为不同格式"""
    
    @staticmethod
    def to_sse(event: AgentEvent) -> str:
        """转换为Server-Sent Events格式"""
        data = event.to_dict()
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
    
    @staticmethod
    def to_token_stream(event: AgentEvent) -> List[str]:
        """转换为token流"""
        if not event.content:
            return []
        return list(event.content)
    
    @staticmethod
    def to_markdown(event: AgentEvent) -> str:
        """转换为Markdown格式"""
        type_emoji = {
            EventType.AGENT_START: "🚀",
            EventType.AGENT_THINKING: "💭",
            EventType.AGENT_REASONING: "🧠",
            EventType.AGENT_ACTION: "🎬",
            EventType.AGENT_OBSERVATION: "👁️",
            EventType.AGENT_ANSWER: "📝",
            EventType.AGENT_ERROR: "❌",
            EventType.AGENT_COMPLETE: "✅",
            EventType.TOOL_START: "🔧",
            EventType.TOOL_COMPLETE: "✨"
        }
        
        emoji = type_emoji.get(event.event_type, "📌")
        
        if event.event_type == EventType.AGENT_THINKING:
            return f"{emoji} *Thinking: {event.content}*"
        elif event.event_type == EventType.AGENT_ACTION:
            tool = event.data.get("tool_name", "unknown")
            return f"{emoji} *Action: Using {tool}*"
        elif event.event_type == EventType.AGENT_ANSWER:
            return f"{emoji} *Answer:*\n\n{event.content}"
        else:
            return f"{emoji} {event.content}"


class EventStreamManager:
    """事件流管理器 - 管理多个会话的事件流"""
    
    def __init__(self):
        self._streams: Dict[str, EventStream] = {}
        self._default_stream: Optional[EventStream] = None
        self.logger = logging.getLogger(__name__)
    
    def create_stream(
        self,
        session_id: Optional[str] = None,
        buffer_size: int = 100
    ) -> EventStream:
        """
        创建新的事件流
        
        Args:
            session_id: 会话ID
            buffer_size: 缓冲区大小
            
        Returns:
            EventStream实例
        """
        stream = EventStream(session_id=session_id, buffer_size=buffer_size)
        self._streams[stream.session_id] = stream
        
        if self._default_stream is None:
            self._default_stream = stream
        
        self.logger.info(f"创建事件流: {stream.session_id}")
        return stream
    
    def get_stream(self, session_id: str) -> Optional[EventStream]:
        """获取事件流"""
        return self._streams.get(session_id)
    
    def get_or_create_stream(self, session_id: str) -> EventStream:
        """获取或创建事件流"""
        if session_id not in self._streams:
            return self.create_stream(session_id)
        return self._streams[session_id]
    
    def get_default_stream(self) -> EventStream:
        """获取默认事件流"""
        if self._default_stream is None:
            self._default_stream = self.create_stream()
        return self._default_stream
    
    def remove_stream(self, session_id: str):
        """移除事件流"""
        if session_id in self._streams:
            self._streams[session_id].stop()
            del self._streams[session_id]
            self.logger.info(f"移除事件流: {session_id}")
    
    def list_streams(self) -> List[str]:
        """列出所有事件流"""
        return list(self._streams.keys())
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有流的指标"""
        return {
            session_id: stream.get_metrics()
            for session_id, stream in self._streams.items()
        }


# 全局事件流管理器
_event_stream_manager: Optional[EventStreamManager] = None


def get_event_stream_manager() -> EventStreamManager:
    """获取全局事件流管理器"""
    global _event_stream_manager
    if _event_stream_manager is None:
        _event_stream_manager = EventStreamManager()
    return _event_stream_manager


def create_event_stream(
    session_id: Optional[str] = None,
    buffer_size: int = 100
) -> EventStream:
    """创建事件流的便捷函数"""
    return get_event_stream_manager().create_stream(session_id, buffer_size)


def get_event_stream(session_id: str) -> Optional[EventStream]:
    """获取事件流的便捷函数"""
    return get_event_stream_manager().get_stream(session_id)
