"""
Gateway Channels 模块
"""

from src.gateway.channels.channel_adapter import (
    ChannelAdapter,
    Message,
    User,
    MessageType,
    PollingChannelAdapter,
    WebhookChannelAdapter
)

# 渠道适配器
from src.gateway.channels.telegram import TelegramAdapter, create_telegram_adapter
from src.gateway.channels.webchat import WebChatAdapter, create_webchat_adapter
from src.gateway.channels.slack import SlackAdapter, create_slack_adapter
from src.gateway.channels.whatsapp import WhatsAppAdapter, create_whatsapp_adapter

__all__ = [
    "ChannelAdapter",
    "Message",
    "User",
    "MessageType",
    "PollingChannelAdapter",
    "WebhookChannelAdapter",
    "TelegramAdapter",
    "create_telegram_adapter",
    "WebChatAdapter",
    "create_webchat_adapter",
    "SlackAdapter",
    "create_slack_adapter",
    "WhatsAppAdapter",
    "create_whatsapp_adapter"
]
