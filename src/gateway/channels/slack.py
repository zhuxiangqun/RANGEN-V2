"""
Slack Channel Adapter

Slack 渠道实现
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

from src.services.logging_service import get_logger

logger = get_logger(__name__)

# Slack SDK (需要安装)
# pip install slack-sdk
try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    from slack_sdk.models import blocks, messages
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False

from src.gateway.channels.channel_adapter import (
    ChannelAdapter, Message as GatewayMessage, User, MessageType, WebhookChannelAdapter
)


class SlackAdapter(ChannelAdapter):
    """
    Slack 渠道适配器
    
    支持 Bot 模式和 Webhook 模式
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        super().__init__("slack", config)
        
        self.bot_token = config.get("bot_token", os.getenv("SLACK_BOT_TOKEN"))
        self.signing_secret = config.get("signing_secret", os.getenv("SLACK_SIGNING_SECRET"))
        self.client: Optional[WebClient] = None
        
        # Webhook URL (用于收到消息)
        self.webhook_url = config.get("webhook_url")
    
    async def connect(self) -> bool:
        """连接 Slack"""
        if not SLACK_AVAILABLE:
            logger.error("slack-sdk not installed. Run: pip install slack-sdk")
            return False
        
        if not self.bot_token:
            logger.error("Slack bot token not configured")
            return False
        
        try:
            self.client = WebClient(token=self.bot_token)
            
            # 验证 token
            auth_test = self.client.auth_test()
            logger.info(f"Slack connected: {auth_test['user']}")
            
            return True
            
        except SlackApiError as e:
            logger.error(f"Failed to connect to Slack: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
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
            # chat_id 在 Slack 中是 channel ID
            message_kwargs = {
                "channel": chat_id,
                "text": text
            }
            
            # 如果是回复
            if reply_to:
                message_kwargs["thread_ts"] = reply_to
            
            response = self.client.chat_postMessage(**message_kwargs)
            
            self.stats["messages_sent"] += 1
            return True
            
        except SlackApiError as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    async def send_interactive(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict],
        **kwargs
    ) -> bool:
        """发送交互式消息 (使用 Block Kit)"""
        if not self.client:
            return False
        
        try:
            # 构建 Block Kit 消息
            blocks_list = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": btn.get("text", "")
                            },
                            "value": btn.get("id", ""),
                            "action_id": btn.get("id", "")
                        }
                        for btn in buttons
                    ]
                }
            ]
            
            message_kwargs = {
                "channel": chat_id,
                "blocks": blocks_list
            }
            
            if reply_to := kwargs.get("reply_to"):
                message_kwargs["thread_ts"] = reply_to
            
            self.client.chat_postMessage(**message_kwargs)
            
            self.stats["messages_sent"] += 1
            return True
            
        except SlackApiError as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send interactive message: {e}")
            return False
    
    async def send_typing(self, chat_id: str, typing: bool = True):
        """发送 typing 状态"""
        if not self.client:
            return
        
        try:
            if typing:
                self.client.chat_postEphemeral(
                    channel=chat_id,
                    user=chat_id,  # 这会显示给当前用户
                    text="🤔"
                )
        except SlackApiError as e:
            logger.error(f"Failed to send typing: {e}")
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """设置 Webhook (用于 Slack Events)"""
        self.webhook_url = webhook_url
        # Slack Events 需要通过 Slack App 配置
        # 这里只是保存配置
        logger.info(f"Webhook URL configured: {webhook_url}")
        return True
    
    async def _listen(self):
        """监听 Slack Events (Webhooks 模式)"""
        # Slack Events API 使用 Webhook
        # 实际监听由外部服务处理
        # 这里提供一个处理入口
        while self._running:
            await asyncio.sleep(1)
    
    def _parse_message(self, raw_message: Dict[str, Any]) -> Optional[GatewayMessage]:
        """解析 Slack 消息"""
        try:
            event = raw_message.get("event", {})
            
            # 忽略消息类型
            if event.get("subtype") == "bot_message":
                return None
            
            # 获取消息内容
            content = event.get("text", "")
            if not content:
                return None
            
            # 确定消息类型
            msg_type = MessageType.TEXT
            if event.get("files"):
                msg_type = MessageType.FILE
            
            # 获取用户信息
            user_id = event.get("user", "")
            
            # 获取用户信息
            user_name = user_id
            if self.client and user_id:
                try:
                    user_info = self.client.users_info(user=user_id)
                    user_name = user_info["user"]["real_name"] or user_id
                except:
                    pass
            
            user = User(
                id=user_id,
                name=user_name
            )
            
            return GatewayMessage(
                channel=self.channel_id,
                type=msg_type,
                content=content,
                user=user,
                timestamp=datetime.now(),
                metadata={
                    "channel": event.get("channel"),
                    "ts": event.get("ts")
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing Slack message: {e}")
            return None
    
    async def handle_event(self, event: Dict) -> bool:
        """
        处理 Slack Event
        
        供外部调用 (如 Flask/FastAPI endpoint)
        """
        # URL 验证挑战
        if event.get("type") == "url_verification":
            return True
        
        # 处理事件
        if "event" in event:
            message = self._parse_message(event)
            if message:
                await self._handle_message(event)
                return True
        
        return False


def create_slack_adapter(bot_token: str = None, signing_secret: str = None) -> SlackAdapter:
    """创建 Slack 适配器"""
    config = {}
    if bot_token:
        config["bot_token"] = bot_token
    if signing_secret:
        config["signing_secret"] = signing_secret
    return SlackAdapter(config)
