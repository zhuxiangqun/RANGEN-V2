"""
RANGEN Gateway - 控制平面核心

参考 OpenClaw Gateway 架构设计
用于将 RANGEN 从研究系统改造为 Personal Assistant
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid

from src.services.logging_service import get_logger
from src.gateway.events.event_bus import EventBus, Event, EventType
from src.gateway.agents.agent_runtime import AgentRuntime, AgentConfig
from src.gateway.channels.channel_adapter import ChannelAdapter, Message, User

logger = get_logger(__name__)


class GatewayStatus(Enum):
    """Gateway 运行状态"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class GatewayConfig:
    """Gateway 配置"""
    # Agent 配置
    agent_config_path: str = "config/agent.yaml"
    
    # 记忆配置
    memory_enabled: bool = True
    memory_ttl: int = 86400 * 7  # 7 days
    context_window: int = 10  # 记忆上下文窗口
    
    # Agent 运行时配置
    max_iterations: int = 10
    enable_thinking: bool = True
    model_provider: str = "deepseek"
    model_name: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # 工具配置
    tools_enabled: bool = True
    tool_policy_strict: bool = False
    max_tool_calls: int = 10
    tool_timeout: int = 30
    
    # 速率限制
    rate_limit_enabled: bool = True
    rate_limit_max_per_minute: int = 20
    
    # 超时配置
    request_timeout: int = 300  # 5 minutes
    heartbeat_interval: int = 60  # 1 minute
    
    # 安全配置
    sandbox_enabled: bool = False
    max_tool_calls_per_request: int = 10


class Gateway:
    """
    RANGEN Gateway - 控制平面
    
    核心职责:
    - 连接管理 (多渠道)
    - 授权认证
    - 任务分发路由
    - 广播推送
    - Kill Switch 紧急停止
    """
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        
        # 状态管理
        self.status: GatewayStatus = GatewayStatus.STOPPED
        self._shutdown_event = asyncio.Event()
        
        # 核心组件
        self.event_bus = EventBus()
        self.agent_runtime: Optional[AgentRuntime] = None
        
        # 连接管理
        self.channels: Dict[str, ChannelAdapter] = {}
        self.active_connections: Dict[str, Dict] = {}  # connection_id -> metadata
        
        # 用户会话管理
        self.sessions: Dict[str, Dict] = {}  # session_id -> session data
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        
        # Kill Switch
        self.kill_switch_active: bool = False
        
        # 速率限制
        self.rate_limiter: Dict[str, List[datetime]] = {}
        
        # 回调函数
        self.message_handlers: List[Callable[[Message], Awaitable[None]]] = []
        
        logger.info("Gateway instance created")
    
    # ==================== 生命周期管理 ====================
    
    async def start(self):
        """启动 Gateway"""
        if self.status != GatewayStatus.STOPPED:
            logger.warning(f"Cannot start gateway from status: {self.status}")
            return
        
        self.status = GatewayStatus.STARTING
        logger.info("Starting RANGEN Gateway...")
        
        try:
            # 1. 初始化事件总线
            await self.event_bus.start()
            
            # 2. 初始化 Agent 运行时
            # 将 GatewayConfig 转换为 AgentConfig
            agent_config = AgentConfig(
                model_provider=self.config.model_provider,
                model_name=self.config.model_name,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                max_tool_calls=self.config.max_tool_calls,
                tool_timeout=self.config.tool_timeout,
                max_iterations=self.config.max_iterations,
                enable_thinking=self.config.enable_thinking,
                memory_enabled=self.config.memory_enabled,
                context_window=self.config.context_window
            )
            self.agent_runtime = AgentRuntime(config=agent_config)
            await self.agent_runtime.start()
            
            # 3. 注册默认事件处理器
            self._register_event_handlers()
            
            # 4. 启动心跳
            asyncio.create_task(self._heartbeat_loop())
            
            self.status = GatewayStatus.RUNNING
            logger.info("RANGEN Gateway started successfully")
            
        except Exception as e:
            self.status = GatewayStatus.ERROR
            logger.error(f"Failed to start gateway: {e}")
            raise
    
    async def stop(self):
        """停止 Gateway"""
        if self.status != GatewayStatus.RUNNING:
            logger.warning(f"Cannot stop gateway from status: {self.status}")
            return
        
        self.status = GatewayStatus.STOPPING
        logger.info("Stopping RANGEN Gateway...")
        
        try:
            # 1. 激活 Kill Switch
            self.kill_switch_active = True
            
            # 2. 停止所有渠道
            for channel in self.channels.values():
                await channel.disconnect()
            
            # 3. 停止 Agent 运行时
            if self.agent_runtime:
                await self.agent_runtime.stop()
            
            # 4. 停止事件总线
            await self.event_bus.stop()
            
            self.status = GatewayStatus.STOPPED
            logger.info("RANGEN Gateway stopped")
            
        except Exception as e:
            logger.error(f"Error stopping gateway: {e}")
            self.status = GatewayStatus.ERROR
            raise
    
    # ==================== 渠道管理 ====================
    
    async def register_channel(self, channel_id: str, adapter: ChannelAdapter):
        """注册消息渠道"""
        if channel_id in self.channels:
            logger.warning(f"Channel {channel_id} already registered, replacing")
        
        self.channels[channel_id] = adapter
        adapter.set_gateway(self)
        
        logger.info(f"Channel registered: {channel_id}")
        
        # 发送事件
        await self.event_bus.emit(Event(
            type=EventType.CHANNEL_REGISTERED,
            data={"channel_id": channel_id, "adapter_type": type(adapter).__name__}
        ))
    
    async def unregister_channel(self, channel_id: str):
        """注销消息渠道"""
        if channel_id not in self.channels:
            logger.warning(f"Channel {channel_id} not registered")
            return
        
        channel = self.channels.pop(channel_id)
        await channel.disconnect()
        
        logger.info(f"Channel unregistered: {channel_id}")
        
        await self.event_bus.emit(Event(
            type=EventType.CHANNEL_UNREGISTERED,
            data={"channel_id": channel_id}
        ))
    
    def get_channel(self, channel_id: str) -> Optional[ChannelAdapter]:
        """获取渠道"""
        return self.channels.get(channel_id)
    
    def list_channels(self) -> List[str]:
        """列出所有渠道"""
        return list(self.channels.keys())
    
    # ==================== 消息处理 ====================
    
    async def handle_message(self, message: Message):
        """处理收到的消息"""
        # 1. Kill Switch 检查
        if self.kill_switch_active:
            await self._send_error(message, "Gateway is temporarily unavailable")
            return
        
        # 2. 速率限制检查
        if not await self._check_rate_limit(message.user):
            await self._send_error(message, "Rate limit exceeded")
            return
        
        # 3. 验证消息
        if not await self._validate_message(message):
            await self._send_error(message, "Invalid message")
            return
        
        # 4. 获取或创建会话
        session = await self._get_or_create_session(message)
        
        # 5. 发送消息事件
        await self.event_bus.emit(Event(
            type=EventType.MESSAGE_RECEIVED,
            data={
                "message": message.to_dict(),
                "session_id": session["session_id"],
                "channel": message.channel
            }
        ))
        
        # 6. 交给 Agent 处理
        try:
            response = await self.agent_runtime.process(
                user_input=message.content,
                user_id=message.user.id,
                session_id=session["session_id"],
                channel=message.channel,
                context={
                    "message_type": str(message.type),
                    "timestamp": message.timestamp.isoformat()
                }
            )
            
            # 7. 发送响应
            await self._send_response(message, response.content)
            
            # 8. 发送完成事件
            await self.event_bus.emit(Event(
                type=EventType.MESSAGE_PROCESSED,
                data={
                    "message_id": message.id,
                    "session_id": session["session_id"],
                    "response_length": len(response.content)
                }
            ))
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error(message, f"Error: {str(e)}")
    
    # ==================== 会话管理 ====================
    
    async def _get_or_create_session(self, message: Message) -> Dict:
        """获取或创建会话"""
        # 尝试通过用户ID查找现有会话
        if message.user.id in self.user_sessions:
            session_id = self.user_sessions[message.user.id]
            if session_id in self.sessions:
                return self.sessions[session_id]
        
        # 创建新会话
        session_id = str(uuid.uuid4())
        session = {
            "session_id": session_id,
            "user_id": message.user.id,
            "channel": message.channel,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "message_count": 0,
            "context": {}
        }
        
        self.sessions[session_id] = session
        self.user_sessions[message.user.id] = session_id
        
        logger.debug(f"Created new session: {session_id} for user {message.user.id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """获取会话"""
        return self.sessions.get(session_id)
    
    async def delete_session(self, session_id: str):
        """删除会话"""
        if session_id in self.sessions:
            session = self.sessions.pop(session_id)
            user_id = session.get("user_id")
            if user_id and user_id in self.user_sessions:
                del self.user_sessions[user_id]
    
    # ==================== 速率限制 ====================
    
    async def _check_rate_limit(self, user: User) -> bool:
        """检查速率限制"""
        if not self.config.rate_limit_enabled:
            return True
        
        now = datetime.now()
        user_key = user.id
        
        # 获取或初始化用户速率记录
        if user_key not in self.rate_limiter:
            self.rate_limiter[user_key] = []
        
        # 清理过期的记录
        self.rate_limiter[user_key] = [
            t for t in self.rate_limiter[user_key]
            if (now - t).total_seconds() < 60
        ]
        
        # 检查是否超过限制
        if len(self.rate_limiter[user_key]) >= self.config.rate_limit_max_per_minute:
            return False
        
        # 添加新记录
        self.rate_limiter[user_key].append(now)
        return True
    
    # ==================== 消息验证 ====================
    
    async def _validate_message(self, message: Message) -> bool:
        """验证消息"""
        if not message.content or not message.content.strip():
            return False
        
        if len(message.content) > 10000:  # 10KB 限制
            return False
        
        return True
    
    # ==================== 响应发送 ====================
    
    async def _send_response(self, message: Message, response: str):
        """发送响应"""
        channel = self.get_channel(message.channel)
        if not channel:
            logger.error(f"Channel not found: {message.channel}")
            return
        
        await channel.send(
            chat_id=message.user.id,
            text=response,
            reply_to=message.id
        )
    
    async def _send_error(self, message: Message, error: str):
        """发送错误消息"""
        channel = self.get_channel(message.channel)
        if not channel:
            return
        
        await channel.send(
            chat_id=message.user.id,
            text=f"❌ {error}"
        )
    
    # ==================== Kill Switch ====================
    
    async def activate_kill_switch(self, reason: str = ""):
        """激活 Kill Switch"""
        self.kill_switch_active = True
        logger.warning(f"Kill Switch activated. Reason: {reason}")
        
        await self.event_bus.emit(Event(
            type=EventType.KILL_SWITCH_ACTIVATED,
            data={"reason": reason}
        ))
    
    async def deactivate_kill_switch(self):
        """停用 Kill Switch"""
        self.kill_switch_active = False
        logger.info("Kill Switch deactivated")
        
        await self.event_bus.emit(Event(
            type=EventType.KILL_SWITCH_DEACTIVATED,
            data={}
        ))
    
    # ==================== 心跳 ====================
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.status == GatewayStatus.RUNNING:
            try:
                # 发送心跳事件
                await self.event_bus.emit(Event(
                    type=EventType.HEARTBEAT,
                    data={
                        "status": self.status.value,
                        "active_connections": len(self.active_connections),
                        "sessions": len(self.sessions),
                        "channels": list(self.channels.keys())
                    }
                ))
                
            except Exception as e:
                logger.error(f"Error in heartbeat: {e}")
            
            await asyncio.sleep(self.config.heartbeat_interval)
    
    # ==================== 事件处理 ====================
    
    def _register_event_handlers(self):
        """注册事件处理器"""
        # 可以添加更多自定义处理器
        pass
    
    # ==================== 工具方法 ====================
    
    def get_status(self) -> Dict:
        """获取 Gateway 状态"""
        return {
            "status": self.status.value,
            "kill_switch_active": self.kill_switch_active,
            "channels": list(self.channels.keys()),
            "active_sessions": len(self.sessions),
            "active_connections": len(self.active_connections)
        }


# ==================== 全局 Gateway 实例 ====================

_gateway_instance: Optional[Gateway] = None


def get_gateway() -> Gateway:
    """获取全局 Gateway 实例"""
    global _gateway_instance
    if _gateway_instance is None:
        _gateway_instance = Gateway()
    return _gateway_instance


async def initialize_gateway(config: Optional[GatewayConfig] = None) -> Gateway:
    """初始化 Gateway"""
    global _gateway_instance
    _gateway_instance = Gateway(config)
    await _gateway_instance.start()
    return _gateway_instance
