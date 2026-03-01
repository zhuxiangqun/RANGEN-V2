"""
Channel Adapter - 消息渠道适配器基类

定义消息渠道的统一接口
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """消息类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    LOCATION = "location"
    BUTTON = "button"
    INTERACTIVE = "interactive"


@dataclass
class User:
    """用户信息"""
    id: str
    name: str = ""
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    language: str = "en"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Message:
    """消息"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    channel: str = ""
    type: MessageType = MessageType.TEXT
    content: str = ""
    user: User = field(default_factory=User)
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 可选字段
    reply_to: str = ""  # 回复的消息ID
    attachments: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "type": self.type.value,
            "content": self.content,
            "user": {
                "id": self.user.id,
                "name": self.user.name,
                "username": self.user.username
            },
            "timestamp": self.timestamp.isoformat(),
            "reply_to": self.reply_to,
            "attachments": self.attachments,
            "metadata": self.metadata
        }


class ChannelAdapter(ABC):
    """
    消息渠道适配器基类
    
    所有渠道适配器需要实现此接口
    """
    
    def __init__(self, channel_id: str, config: Optional[Dict] = None):
        self.channel_id = channel_id
        self.config = config or {}
        self.gateway = None  # 将在注册时设置
        self._running = False
        
        # 统计
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }
    
    def set_gateway(self, gateway):
        """设置 Gateway 引用"""
        self.gateway = gateway
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        连接渠道
        
        Returns:
            bool: 连接是否成功
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass
    
    @abstractmethod
    async def send(
        self,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
        **kwargs
    ) -> bool:
        """
        发送消息
        
        Args:
            chat_id: 聊天ID
            text: 消息内容
            reply_to: 回复的消息ID
            **kwargs: 其他参数
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    async def send_interactive(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict],
        **kwargs
    ) -> bool:
        """
        发送交互式消息（如按钮）
        
        Args:
            chat_id: 聊天ID
            text: 消息内容
            buttons: 按钮列表 [{"id": "btn1", "text": "Option 1"}, ...]
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    async def send_typing(self, chat_id: str, typing: bool = True):
        """
        发送 typing 状态
        
        Args:
            chat_id: 聊天ID
            typing: 是否显示 typing 状态
        """
        pass
    
    async def start_listening(self):
        """开始监听消息"""
        if self._running:
            return
        
        self._running = True
        asyncio.create_task(self._listen())
        logger.info(f"Channel {self.channel_id} started listening")
    
    async def stop_listening(self):
        """停止监听消息"""
        self._running = False
        logger.info(f"Channel {self.channel_id} stopped listening")
    
    @abstractmethod
    async def _listen(self):
        """
        监听循环
        
        子类需要实现具体的监听逻辑
        当收到消息时，调用 self._handle_message()
        """
        pass
    
    async def _handle_message(self, raw_message: Dict[str, Any]):
        """
        处理收到的原始消息
        
        Args:
            raw_message: 原始消息数据
        """
        try:
            # 1. 解析消息
            message = self._parse_message(raw_message)
            
            if not message:
                return
            
            # 2. 统计
            self.stats["messages_received"] += 1
            
            # 3. 转发给 Gateway
            if self.gateway:
                await self.gateway.handle_message(message)
            else:
                logger.warning(f"Gateway not set for channel {self.channel_id}")
                
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Error handling message: {e}")
    
    @abstractmethod
    def _parse_message(self, raw_message: Dict[str, Any]) -> Optional[Message]:
        """
        解析原始消息为 Message 对象
        
        Args:
            raw_message: 原始消息数据
            
        Returns:
            Message: 解析后的消息，None 表示跳过
        """
        pass
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "channel_id": self.channel_id,
            "running": self._running,
            **self.stats
        }


# ==================== 便捷基类 ====================

class PollingChannelAdapter(ChannelAdapter):
    """基于轮询的渠道适配器基类"""
    
    def __init__(self, channel_id: str, config: Optional[Dict] = None):
        super().__init__(channel_id, config)
        self.poll_interval = 1.0  # 轮询间隔（秒）
    
    async def _listen(self):
        """基于轮询的监听"""
        while self._running:
            try:
                messages = await self._fetch_messages()
                for msg in messages:
                    await self._handle_message(msg)
            except Exception as e:
                logger.error(f"Error in polling: {e}")
            
            await asyncio.sleep(self.poll_interval)
    
    @abstractmethod
    async def _fetch_messages(self) -> List[Dict]:
        """获取新消息"""
        pass


class WebhookChannelAdapter(ChannelAdapter):
    """基于 Webhook 的渠道适配器基类"""
    
    def __init__(self, channel_id: str, config: Optional[Dict] = None):
        super().__init__(channel_id, config)
        self._webhook_server = None
    
    async def _listen(self):
        """Webhook 模式不需要主动监听"""
        # Webhook 由外部调用 _handle_message
        while self._running:
            await asyncio.sleep(1)
    
    @abstractmethod
    async def setup_webhook(self, webhook_url: str) -> bool:
        """设置 Webhook"""
        pass
