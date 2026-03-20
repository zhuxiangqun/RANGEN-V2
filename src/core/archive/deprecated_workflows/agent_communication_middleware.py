"""
智能体通信中间件 (Agent Communication Middleware)

实现智能体间的动态协作通信机制，支持：
- 消息传递和路由
- 状态广播和同步
- 事件驱动通信
- 协作上下文管理
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Callable, Set, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import weakref
import threading

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型枚举"""
    TASK_ASSIGNMENT = "task_assignment"      # 任务分配
    STATUS_UPDATE = "status_update"          # 状态更新
    COLLABORATION_REQUEST = "collaboration_request"  # 协作请求
    RESOURCE_REQUEST = "resource_request"    # 资源请求
    CONFLICT_NOTIFICATION = "conflict_notification"  # 冲突通知
    LEARNING_UPDATE = "learning_update"      # 学习更新
    SYSTEM_BROADCAST = "system_broadcast"    # 系统广播


class MessagePriority(Enum):
    """消息优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Message:
    """通信消息"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.STATUS_UPDATE
    priority: MessagePriority = MessagePriority.NORMAL
    sender_id: str = ""
    receiver_id: Optional[str] = None  # None表示广播消息
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Time To Live in seconds
    correlation_id: Optional[str] = None  # 用于关联请求和响应
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """检查消息是否过期"""
        if self.ttl is None:
            return False
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'message_id': self.message_id,
            'message_type': self.message_type.value,
            'priority': self.priority.value,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'ttl': self.ttl,
            'correlation_id': self.correlation_id,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        data_copy = data.copy()
        data_copy['message_type'] = MessageType(data_copy['message_type'])
        data_copy['priority'] = MessagePriority(data_copy['priority'])
        data_copy['timestamp'] = datetime.fromisoformat(data_copy['timestamp'])
        return cls(**data_copy)


@dataclass
class AgentState:
    """智能体状态"""
    agent_id: str
    agent_type: str
    status: str = "idle"  # idle, busy, error, offline
    capabilities: List[str] = field(default_factory=list)
    current_tasks: List[str] = field(default_factory=list)
    resource_usage: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'status': self.status,
            'capabilities': self.capabilities,
            'current_tasks': self.current_tasks,
            'resource_usage': self.resource_usage,
            'performance_metrics': self.performance_metrics,
            'last_updated': self.last_updated.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class CollaborationContext:
    """协作上下文"""
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    participants: List[str] = field(default_factory=list)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    task_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def update_shared_state(self, key: str, value: Any, agent_id: str):
        """更新共享状态"""
        self.shared_state[key] = {
            'value': value,
            'updated_by': agent_id,
            'updated_at': datetime.now().isoformat()
        }
        self.last_updated = datetime.now()


class MessageHandler(Protocol):
    """消息处理器协议"""
    async def handle_message(self, message: Message) -> Optional[Message]:
        """处理消息"""
        ...


class AgentCommunicationMiddleware:
    """
    智能体通信中间件

    提供智能体间的通信基础设施，支持：
    - 点对点消息传递
    - 广播通信
    - 状态同步
    - 事件驱动处理
    - 协作上下文管理
    """

    def __init__(self):
        self._message_handlers: Dict[str, List[MessageHandler]] = {}
        self._agent_states: Dict[str, AgentState] = {}
        self._collaboration_contexts: Dict[str, CollaborationContext] = {}
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processing_task: Optional[asyncio.Task] = None

        # 线程安全
        self._lock = asyncio.Lock()

        # 状态同步间隔
        self._state_sync_interval = 30  # 秒
        self._last_state_sync = datetime.now()

        logger.info("智能体通信中间件已初始化")

    async def start(self):
        """启动通信中间件"""
        async with self._lock:
            if self._running:
                return

            self._running = True
            self._processing_task = asyncio.create_task(self._message_processing_loop())

            # 启动定期状态同步
            asyncio.create_task(self._periodic_state_sync())

            logger.info("智能体通信中间件已启动")

    async def stop(self):
        """停止通信中间件"""
        async with self._lock:
            if not self._running:
                return

            self._running = False
            if self._processing_task:
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass

            logger.info("智能体通信中间件已停止")

    async def register_agent(self, agent_state: AgentState) -> bool:
        """注册智能体"""
        async with self._lock:
            self._agent_states[agent_state.agent_id] = agent_state

            # 广播新智能体加入消息
            welcome_message = Message(
                message_type=MessageType.SYSTEM_BROADCAST,
                sender_id="middleware",
                payload={
                    'event': 'agent_joined',
                    'agent_id': agent_state.agent_id,
                    'agent_type': agent_state.agent_type,
                    'capabilities': agent_state.capabilities
                }
            )
            await self._broadcast_message(welcome_message)

            logger.info(f"智能体 {agent_state.agent_id} 已注册")
            return True

    async def unregister_agent(self, agent_id: str):
        """注销智能体"""
        async with self._lock:
            if agent_id in self._agent_states:
                del self._agent_states[agent_id]

                # 广播智能体离开消息
                goodbye_message = Message(
                    message_type=MessageType.SYSTEM_BROADCAST,
                    sender_id="middleware",
                    payload={
                        'event': 'agent_left',
                        'agent_id': agent_id
                    }
                )
                await self._broadcast_message(goodbye_message)

                logger.info(f"智能体 {agent_id} 已注销")

    def register_message_handler(self, agent_id: str, handler: MessageHandler):
        """注册消息处理器"""
        if agent_id not in self._message_handlers:
            self._message_handlers[agent_id] = []
        self._message_handlers[agent_id].append(handler)
        logger.debug(f"为智能体 {agent_id} 注册了消息处理器")

    def unregister_message_handler(self, agent_id: str, handler: MessageHandler):
        """注销消息处理器"""
        if agent_id in self._message_handlers:
            try:
                self._message_handlers[agent_id].remove(handler)
            except ValueError:
                pass  # 处理器不存在

    async def send_message(self, message: Message) -> bool:
        """发送消息"""
        if not self._running:
            logger.warning("通信中间件未运行，无法发送消息")
            return False

        # 设置发送者ID（如果未设置）
        if not message.sender_id:
            logger.warning("消息缺少发送者ID")
            return False

        # 放入消息队列
        await self._message_queue.put(message)
        logger.debug(f"消息 {message.message_id} 已放入队列")
        return True

    async def broadcast_status_update(self, agent_id: str, status_update: Dict[str, Any]):
        """广播状态更新"""
        message = Message(
            message_type=MessageType.STATUS_UPDATE,
            sender_id=agent_id,
            payload=status_update
        )
        await self.send_message(message)

    async def request_collaboration(self, requester_id: str, target_agents: List[str],
                                  collaboration_context: Dict[str, Any]) -> str:
        """请求协作"""
        context_id = str(uuid.uuid4())

        message = Message(
            message_type=MessageType.COLLABORATION_REQUEST,
            sender_id=requester_id,
            payload={
                'context_id': context_id,
                'collaboration_context': collaboration_context,
                'target_agents': target_agents
            }
        )

        # 创建协作上下文
        collab_context = CollaborationContext(
            context_id=context_id,
            session_id=f"collab_{context_id}",
            participants=[requester_id] + target_agents
        )
        self._collaboration_contexts[context_id] = collab_context

        await self.send_message(message)
        return context_id

    async def update_collaboration_context(self, context_id: str, agent_id: str,
                                         updates: Dict[str, Any]):
        """更新协作上下文"""
        if context_id not in self._collaboration_contexts:
            logger.warning(f"协作上下文 {context_id} 不存在")
            return

        context = self._collaboration_contexts[context_id]
        for key, value in updates.items():
            context.update_shared_state(key, value, agent_id)

        # 广播上下文更新
        message = Message(
            message_type=MessageType.LEARNING_UPDATE,
            sender_id=agent_id,
            payload={
                'context_id': context_id,
                'updates': updates
            }
        )
        await self.send_message(message)

    async def get_agent_states(self) -> Dict[str, AgentState]:
        """获取所有智能体状态"""
        async with self._lock:
            return self._agent_states.copy()

    async def get_collaboration_context(self, context_id: str) -> Optional[CollaborationContext]:
        """获取协作上下文"""
        return self._collaboration_contexts.get(context_id)

    async def _message_processing_loop(self):
        """消息处理循环"""
        logger.info("消息处理循环已启动")

        while self._running:
            try:
                # 获取消息（带超时）
                message = await asyncio.wait_for(self._message_queue.get(), timeout=1.0)

                # 处理消息
                await self._process_message(message)

                # 标记任务完成
                self._message_queue.task_done()

            except asyncio.TimeoutError:
                # 超时继续循环
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"消息处理错误: {e}", exc_info=True)

        logger.info("消息处理循环已停止")

    async def _process_message(self, message: Message):
        """处理单个消息"""
        # 检查消息是否过期
        if message.is_expired():
            logger.debug(f"消息 {message.message_id} 已过期，跳过处理")
            return

        logger.debug(f"处理消息: {message.message_type.value} from {message.sender_id}")

        # 根据接收者路由消息
        if message.receiver_id:
            # 点对点消息
            await self._deliver_point_to_point(message)
        else:
            # 广播消息
            await self._broadcast_message(message)

    async def _deliver_point_to_point(self, message: Message):
        """点对点消息投递"""
        receiver_id = message.receiver_id

        if receiver_id not in self._message_handlers:
            logger.warning(f"智能体 {receiver_id} 没有注册消息处理器")
            return

        # 调用所有处理器
        for handler in self._message_handlers[receiver_id]:
            try:
                response = await handler.handle_message(message)
                if response and message.correlation_id:
                    # 如果有响应且是请求-响应模式，发送响应
                    response.correlation_id = message.correlation_id
                    await self.send_message(response)
            except Exception as e:
                logger.error(f"消息处理器错误 (智能体 {receiver_id}): {e}")

    async def _broadcast_message(self, message: Message):
        """广播消息"""
        # 向所有注册的智能体广播
        for agent_id, handlers in self._message_handlers.items():
            if agent_id == message.sender_id:
                continue  # 不给自己广播

            for handler in handlers:
                try:
                    await handler.handle_message(message)
                except Exception as e:
                    logger.error(f"广播消息处理错误 (智能体 {agent_id}): {e}")

    async def _periodic_state_sync(self):
        """定期状态同步"""
        while self._running:
            try:
                await asyncio.sleep(self._state_sync_interval)
                await self._sync_agent_states()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"状态同步错误: {e}")

    async def _sync_agent_states(self):
        """同步智能体状态"""
        async with self._lock:
            # 检查离线的智能体
            current_time = datetime.now()
            offline_agents = []

            for agent_id, state in self._agent_states.items():
                time_since_update = current_time - state.last_updated
                if time_since_update > timedelta(seconds=self._state_sync_interval * 3):
                    # 3倍间隔未更新，认为离线
                    state.status = "offline"
                    offline_agents.append(agent_id)

            if offline_agents:
                logger.info(f"检测到离线智能体: {offline_agents}")

                # 广播离线状态
                for agent_id in offline_agents:
                    offline_message = Message(
                        message_type=MessageType.STATUS_UPDATE,
                        sender_id="middleware",
                        payload={
                            'agent_id': agent_id,
                            'status': 'offline',
                            'timestamp': current_time.isoformat()
                        }
                    )
                    await self._broadcast_message(offline_message)


# 全局中间件实例
_middleware_instance: Optional[AgentCommunicationMiddleware] = None
_middleware_lock = threading.Lock()

def get_communication_middleware() -> AgentCommunicationMiddleware:
    """获取通信中间件实例（单例模式）"""
    global _middleware_instance

    if _middleware_instance is None:
        with _middleware_lock:
            if _middleware_instance is None:
                _middleware_instance = AgentCommunicationMiddleware()

    return _middleware_instance
