"""
Telegram Channel Adapter

Telegram Bot 渠道实现
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Telegram Bot API (需要安装 python-telegram-bot)
# pip install python-telegram-bot
try:
    from telegram import Update, Bot, ChatPermissions
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

from src.gateway.channels.channel_adapter import (
    ChannelAdapter, Message, User, MessageType, WebhookChannelAdapter
)

logger = logging.getLogger(__name__)


class TelegramAdapter(WebhookChannelAdapter):
    """
    Telegram 渠道适配器
    
    使用 Webhook 模式
    """
    
    def __init__(self, config: Optional[Dict] = None):
        config = config or {}
        super().__init__("telegram", config)
        
        self.bot_token = config.get("bot_token", "")
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # 消息处理回调
        self._update_callback: Optional[callable] = None
    
    async def connect(self) -> bool:
        """连接 Telegram Bot"""
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot not installed")
            return False
        
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            self.bot = Bot(token=self.bot_token)
            
            # 获取 bot 信息
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram bot: {bot_info.name}")
            
            # 启动 Webhook 模式
            webhook_url = self.config.get("webhook_url")
            if webhook_url:
                await self.setup_webhook(webhook_url)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Telegram: {e}")
            return False
    
    async def disconnect(self):
        """断开连接"""
        if self.bot:
            # 删除 webhook
            try:
                await self.bot.delete_webhook()
            except:
                pass
            
            self.bot = None
        
        if self.application:
            await self.application.stop()
            self.application = None
    
    async def setup_webhook(self, webhook_url: str) -> bool:
        """设置 Webhook"""
        if not self.bot:
            return False
        
        try:
            await self.bot.set_webhook(webhook_url)
            logger.info(f"Webhook set to: {webhook_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False
    
    async def send(
        self,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
        **kwargs
    ) -> bool:
        """发送消息"""
        if not self.bot:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_to,
                **kwargs
            )
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def send_interactive(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict],
        **kwargs
    ) -> bool:
        """发送交互式消息（Inline Buttons）"""
        if not self.bot:
            return False
        
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            keyboard = [
                [InlineKeyboardButton(btn["text"], callback_data=btn["id"])]
                for btn in buttons
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=reply_markup,
                **kwargs
            )
            
            self.stats["messages_sent"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send interactive message: {e}")
            return False
    
    async def send_typing(self, chat_id: str, typing: bool = True):
        """发送 typing 状态"""
        if not self.bot:
            return
        
        try:
            if typing:
                await self.bot.send_chat_action(chat_id, "typing")
            else:
                # 没有 "stop typing" 的 action，直接发送任意内容
                pass
        except Exception as e:
            logger.error(f"Failed to send typing: {e}")
    
    async def _listen(self):
        """Webhooks 模式不需要主动监听"""
        # Webhook 由 Telegram 服务器调用
        # 这个方法仅用于保持接口一致
        while self._running:
            await asyncio.sleep(1)
    
    def _parse_message(self, raw_message: Dict[str, Any]) -> Optional[Message]:
        """解析 Telegram Update 为 Message"""
        try:
            if "message" in raw_message:
                update = Update.de_json(raw_message, self.bot)
                msg = update.message
            elif "edited_message" in raw_message:
                return None  # 忽略编辑的消息
            elif "callback_query" in raw_message:
                # 处理按钮回调
                query = raw_message["callback_query"]
                return Message(
                    channel=self.channel_id,
                    type=MessageType.INTERACTIVE,
                    content=query.get("data", ""),
                    user=User(
                        id=str(query["from"]["id"]),
                        name=query["from"].get("first_name", ""),
                        username=query["from"].get("username", "")
                    ),
                    metadata={"callback_id": query.get("id")}
                )
            else:
                return None
            
            # 解析文本消息
            content = msg.text or ""
            if not content:
                return None
            
            # 解析用户
            user = User(
                id=str(msg.from_user.id),
                name=msg.from_user.first_name or "",
                username=msg.from_user.username or "",
                last_name=msg.from_user.last_name or ""
            )
            
            return Message(
                channel=self.channel_id,
                type=MessageType.TEXT,
                content=content,
                user=user,
                timestamp=msg.date or datetime.now(),
                reply_to=str(msg.message_id) if msg.reply_to_message else ""
            )
            
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None
    
    async def handle_update(self, update: Dict) -> bool:
        """
        处理 Telegram Webhook 更新
        
        供外部调用（如 FastAPI endpoint）
        """
        message = self._parse_message(update)
        
        if message:
            await self._handle_message(update)
            return True
        
        return False


# ==================== 便捷创建函数 ====================

def create_telegram_adapter(bot_token: str, webhook_url: str = "") -> TelegramAdapter:
    """创建 Telegram 适配器"""
    config = {
        "bot_token": bot_token,
        "webhook_url": webhook_url
    }
    return TelegramAdapter(config)
