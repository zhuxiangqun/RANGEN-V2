"""
Gateway FastAPI Integration

将 Gateway 集成到 FastAPI 应用中
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import BaseModel

from src.services.logging_service import get_logger
from src.gateway import Gateway, GatewayConfig, get_gateway
from src.gateway.channels.channel_adapter import Message, User, MessageType

logger = get_logger(__name__)


# ==================== API Models ====================

class ChatRequest(BaseModel):
    """聊天请求"""
    query: str
    user_id: str
    channel: str = "api"
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str
    session_id: str
    status: str
    metadata: Dict[str, Any] = {}


class GatewayStatusResponse(BaseModel):
    """Gateway 状态响应"""
    status: str
    channels: list
    active_sessions: int
    kill_switch_active: bool


class ChannelRegisterRequest(BaseModel):
    """渠道注册请求"""
    channel_type: str  # telegram, slack, whatsapp, webchat
    config: Dict[str, Any] = {}


# ==================== FastAPI Gateway ====================

class GatewayFastAPI:
    """
    FastAPI Gateway 集成
    
    提供 REST API 访问 Gateway
    """
    
    def __init__(self, app: FastAPI, config: Optional[GatewayConfig] = None):
        self.app = app
        self.config = config or GatewayConfig()
        self.gateway: Optional[Gateway] = None
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册路由"""
        
        @self.app.on_event("startup")
        async def startup():
            """启动时初始化 Gateway"""
            logger.info("Initializing Gateway...")
            self.gateway = Gateway(self.config)
            await self.gateway.start()
            logger.info("Gateway initialized")
        
        @self.app.on_event("shutdown")
        async def shutdown():
            """关闭时停止 Gateway"""
            if self.gateway:
                await self.gateway.stop()
        
        # ==================== Chat Endpoints ====================
        
        @self.app.post("/gateway/chat", response_model=ChatResponse)
        async def chat(request: ChatRequest):
            """聊天接口"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            try:
                # 创建消息
                message = Message(
                    channel=request.channel,
                    type=MessageType.TEXT,
                    content=request.query,
                    user=User(id=request.user_id)
                )
                
                # 处理消息
                await self.gateway.handle_message(message)
                
                # 获取会话
                session = await self.gateway._get_or_create_session(message)
                
                return ChatResponse(
                    answer="Message processed",  # 实际响应由渠道返回
                    session_id=session["session_id"],
                    status="completed",
                    metadata={"channel": request.channel}
                )
                
            except Exception as e:
                logger.error(f"Chat error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # ==================== Status Endpoints ====================
        
        @self.app.get("/gateway/status", response_model=GatewayStatusResponse)
        async def get_status():
            """获取 Gateway 状态"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            status = self.gateway.get_status()
            return GatewayStatusResponse(**status)
        
        @self.app.post("/gateway/kill-switch")
        async def activate_kill_switch(reason: str = ""):
            """激活 Kill Switch"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            await self.gateway.activate_kill_switch(reason)
            return {"status": "ok", "message": "Kill switch activated"}
        
        @self.app.delete("/gateway/kill-switch")
        async def deactivate_kill_switch():
            """停用 Kill Switch"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            await self.gateway.deactivate_kill_switch()
            return {"status": "ok", "message": "Kill switch deactivated"}
        
        # ==================== Channel Endpoints ====================
        
        @self.app.post("/gateway/channels")
        async def register_channel(request: ChannelRegisterRequest):
            """注册渠道"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            try:
                adapter = await self._create_channel_adapter(
                    request.channel_type,
                    request.config
                )
                
                await self.gateway.register_channel(request.channel_id, adapter)
                await adapter.connect()
                
                return {
                    "status": "ok",
                    "channel": request.channel_id,
                    "type": request.channel_type
                }
                
            except Exception as e:
                logger.error(f"Channel registration error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/gateway/channels")
        async def list_channels():
            """列出所有渠道"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            return {
                "channels": self.gateway.list_channels()
            }
        
        @self.app.delete("/gateway/channels/{channel_id}")
        async def unregister_channel(channel_id: str):
            """注销渠道"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            await self.gateway.unregister_channel(channel_id)
            return {"status": "ok", "channel": channel_id}
        
        # ==================== Session Endpoints ====================
        
        @self.app.get("/gateway/sessions/{session_id}")
        async def get_session(session_id: str):
            """获取会话"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            session = await self.gateway.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            return session
        
        @self.app.delete("/gateway/sessions/{session_id}")
        async def delete_session(session_id: str):
            """删除会话"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            await self.gateway.delete_session(session_id)
            return {"status": "ok", "session_id": session_id}
        
        # ==================== Webhook Endpoints ====================
        
        @self.app.post("/gateway/webhooks/telegram")
        async def telegram_webhook(request: Request):
            """Telegram Webhook"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            # 获取 Telegram 更新
            data = await request.json()
            
            # 获取 Telegram 适配器
            adapter = self.gateway.get_channel("telegram")
            if not adapter:
                raise HTTPException(status_code=404, detail="Telegram channel not registered")
            
            # 处理更新
            await adapter.handle_update(data)
            
            return {"status": "ok"}
        
        @self.app.post("/gateway/webhooks/slack")
        async def slack_webhook(request: Request):
            """Slack Webhook / Events"""
            if not self.gateway:
                raise HTTPException(status_code=503, detail="Gateway not initialized")
            
            # 获取 Slack 事件
            data = await request.json()
            
            # 获取 Slack 适配器
            adapter = self.gateway.get_channel("slack")
            if not adapter:
                raise HTTPException(status_code=404, detail="Slack channel not registered")
            
            # 处理事件
            await adapter.handle_event(data)
            
            return {"status": "ok"}
    
    async def _create_channel_adapter(self, channel_type: str, config: Dict) -> Any:
        """创建渠道适配器"""
        
        if channel_type == "telegram":
            from src.gateway.channels.telegram import TelegramAdapter
            return TelegramAdapter(config)
        
        elif channel_type == "slack":
            from src.gateway.channels.slack import SlackAdapter
            return SlackAdapter(config)
        
        elif channel_type == "whatsapp":
            from src.gateway.channels.whatsapp import WhatsAppAdapter
            return WhatsAppAdapter(config)
        
        elif channel_type == "webchat":
            from src.gateway.channels.webchat import WebChatAdapter
            return WebChatAdapter(config)
        
        else:
            raise ValueError(f"Unknown channel type: {channel_type}")


# ==================== 便捷函数 ====================

def create_gateway_app(config: Optional[GatewayConfig] = None) -> FastAPI:
    """创建带有 Gateway 的 FastAPI 应用"""
    app = FastAPI(
        title="RANGEN Gateway API",
        description="RANGEN Personal Assistant Gateway API",
        version="1.0.0"
    )
    
    gateway_integration = GatewayFastAPI(app, config)
    
    return app


# ==================== 示例启动 ====================

if __name__ == "__main__":
    import uvicorn
    
    app = create_gateway_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
