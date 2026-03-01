"""
WhatsApp Channel Adapter

WhatsApp 渠道实现 (使用 Baileys 库)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.services.logging_service import get_logger

logger = get_logger(__name__)

# WhatsApp Baileys (需要安装)
# pip install baileys
try:
    from baileys import WhatsApp
    WHATSAPP_AVAILABLE = True
except ImportError:
    WHATSAPP_AVAILABLE = False

from src.gateway.channels.channel_adapter import (
    ChannelAdapter, Message as GatewayMessage, User, MessageType
)


class WhatsAppAdapter(ChannelAdapter):
    """
    WhatsApp 渠道适配器
    
    使用 Baelees 库连接 WhatsApp
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        super().__init__("whatsapp", config)
        
        self.client = None
        self.auth_dir = config.get("auth_dir", "data/whatsapp_auth")
    
    async def connect(self) -> bool:
        """连接 WhatsApp"""
        if not WHATSAPP_AVAILABLE:
            logger.error("baileys not installed. Run: pip install baileys")
            return False
        
        try:
            import os
            os.makedirs(self.auth_dir, exist_ok=True)
            
            self.client = WhatsApp(
                auth_dir=self.auth_dir,
                phone_number=self.config.get("phone_number", "")
            )
            
            await self.client.connect()
            
            logger.info("WhatsApp connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to WhatsApp: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            await self.client.disconnect()
            self.client = None
    
    async def send(
        self,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
        **kwargs
    ) -> bool:
        """发送消息"""
        if not self.client:
            return False
        
        try:
            await self.client.send_message(
                chat_id=chat_id,
                message=text
            )
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send WhatsApp message: {e}")
            return False
    
    async def send_interactive(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict],
        **kwargs
    ) -> bool:
        """发送交互式消息 (Buttons)"""
        if not self.client:
            return False
        
        try:
            # 构建按钮消息
            from baileys.types import InteractiveMessage
            
            button_entries = []
            for btn in buttons:
                button_entries.append({
                    "buttonId": btn.get("id", ""),
                    "buttonText": {"displayText": btn.get("text", "")}
                })
            
            interactive = InteractiveMessage(
                body={"text": text},
                action={"buttons": button_entries}
            )
            
            await self.client.send_message(
                chat_id=chat_id,
                message=interactive
            )
            
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send interactive message: {e}")
            return False
    
    async def send_typing(self, chat_id: str, typing: bool = True):
        """发送 typing 状态"""
        if not self.client:
            return
        
        try:
            if typing:
                await self.client.send_typing(chat_id)
        except Exception as e:
            logger.error(f"Failed to send typing: {e}")
    
    async def _listen(self):
        """监听消息"""
        # Baileys 使用事件监听
        if not self.client:
            return
        
        @self.client.on("message")
        async def on_message(msg):
            await self._handle_message({
                "message": msg,
                "key": msg.key,
                "chat": msg.key.remote_jid
            })
        
        # 保持运行
        while self._running:
            await asyncio.sleep(1)
    
    def _parse_message(self, raw_message: Dict[str, Any]) -> Optional[GatewayMessage]:
        """解析 WhatsApp 消息"""
        try:
            msg = raw_message.get("message", {})
            key = raw_message.get("key", {})
            
            # 获取消息内容
            content = ""
            msg_type = MessageType.TEXT
            
            if msg.get("conversation"):
                content = msg.get("conversation")
            elif msg.get("extendedTextMessage"):
                content = msg.get("extendedTextMessage", {}).get("text", "")
            elif msg.get("imageMessage"):
                content = "[Image]"
                msg_type = MessageType.IMAGE
            elif msg.get("documentMessage"):
                content = "[Document]"
                msg_type = MessageType.FILE
            
            if not content:
                return None
            
            # 获取用户信息
            user_id = key.get("remote_jid", "")
            user = User(
                id=user_id,
                name=user_id.split("@")[0] if "@" in user_id else user_id
            )
            
            return GatewayMessage(
                channel=self.channel_id,
                type=msg_type,
                content=content,
                user=user,
                timestamp=datetime.now(),
                metadata={"key": key}
            )
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None


def create_whatsapp_adapter(auth_dir: str = "data/whatsapp_auth") -> WhatsAppAdapter:
    """创建 WhatsApp 适配器"""
    config = {
        "auth_dir": auth_dir
    }
    return WhatsAppAdapter(config)
