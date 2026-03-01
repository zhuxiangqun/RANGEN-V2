"""
WebChat Channel Adapter

WebSocket 实时聊天渠道实现
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from dataclasses import dataclass

from src.gateway.channels.channel_adapter import ChannelAdapter, Message, User, MessageType

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket 连接"""
    connection_id: str
    user_id: str
    websocket: Any
    channel: str
    created_at: datetime


class WebChatAdapter(ChannelAdapter):
    """
    WebChat 渠道适配器
    
    使用 WebSocket 进行实时通信
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__("webchat", config)
        
        # 连接管理
        self._connections: Dict[str, WebSocketConnection] = {}
        self._user_connections: Dict[str, str] = {}  # user_id -> connection_id
        
        # WebSocket 服务器
        self._server = None
        self._server_task: Optional[asyncio.Task] = None
    
    async def connect(self) -> bool:
        """启动 WebSocket 服务器"""
        host = self.config.get("host", "0.0.0.0")
        port = self.config.get("port", 8765)
        
        self._server = await asyncio.start_server(
            self._handle_client,
            host,
            port
        )
        
        addr = self._server.sockets[0].getsockname()
        logger.info(f"WebChat server started on {addr}")
        
        return True
    
    async def disconnect(self):
        """停止 WebSocket 服务器"""
        # 关闭所有连接
        for conn in list(self._connections.values()):
            try:
                await conn.websocket.close()
            except:
                pass
        
        self._connections.clear()
        self._user_connections.clear()
        
        # 关闭服务器
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        logger.info("WebChat server stopped")
    
    async def _handle_client(self, websocket, path):
        """处理客户端连接"""
        connection_id = f"ws_{len(self._connections)}"
        
        try:
            # 等待握手消息（包含 user_id）
            handshake = await asyncio.wait_for(
                websocket.recv(),
                timeout=10
            )
            
            data = json.loads(handshake)
            user_id = data.get("user_id", "anonymous")
            
            # 创建连接
            conn = WebSocketConnection(
                connection_id=connection_id,
                user_id=user_id,
                websocket=websocket,
                channel=self.channel_id,
                created_at=datetime.now()
            )
            
            self._connections[connection_id] = conn
            self._user_connections[user_id] = connection_id
            
            logger.info(f"Client connected: {user_id} ({connection_id})")
            
            # 接收消息循环
            async for raw_message in websocket:
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode()
                
                try:
                    message_data = json.loads(raw_message)
                    
                    # 解析消息
                    message = Message(
                        channel=self.channel_id,
                        type=MessageType.TEXT,
                        content=message_data.get("content", ""),
                        user=User(id=user_id),
                        metadata={"connection_id": connection_id}
                    )
                    
                    # 转发给 Gateway
                    await self._handle_message(message_data)
                    
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from {user_id}")
                    
        except asyncio.TimeoutError:
            logger.warning(f"Client handshake timeout: {path}")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            # 清理连接
            if connection_id in self._connections:
                conn = self._connections.pop(connection_id)
                if conn.user_id in self._user_connections:
                    del self._user_connections[conn.user_id]
                
                logger.info(f"Client disconnected: {conn.user_id}")
    
    async def send(
        self,
        chat_id: str,
        text: str,
        reply_to: Optional[str] = None,
        **kwargs
    ) -> bool:
        """发送消息"""
        connection_id = self._user_connections.get(chat_id)
        
        if not connection_id or connection_id not in self._connections:
            logger.warning(f"Connection not found for user: {chat_id}")
            return False
        
        conn = self._connections[connection_id]
        
        try:
            message = {
                "type": "message",
                "content": text,
                "timestamp": datetime.now().isoformat()
            }
            
            await conn.websocket.send(json.dumps(message))
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
        """发送交互式消息"""
        connection_id = self._user_connections.get(chat_id)
        
        if not connection_id or connection_id not in self._connections:
            return False
        
        conn = self._connections[connection_id]
        
        try:
            message = {
                "type": "interactive",
                "content": text,
                "buttons": buttons,
                "timestamp": datetime.now().isoformat()
            }
            
            await conn.websocket.send(json.dumps(message))
            self.stats["messages_sent"] += 1
            
            return True
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send interactive message: {e}")
            return False
    
    async def send_typing(self, chat_id: str, typing: bool = True):
        """发送 typing 状态"""
        connection_id = self._user_connections.get(chat_id)
        
        if not connection_id or connection_id not in self._connections:
            return
        
        conn = self._connections[connection_id]
        
        try:
            message = {
                "type": "typing",
                "typing": typing
            }
            
            await conn.websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send typing: {e}")
    
    async def _listen(self):
        """WebSocket 模式不需要主动监听"""
        while self._running:
            await asyncio.sleep(1)
    
    def _parse_message(self, raw_message: Dict[str, Any]) -> Optional[Message]:
        """解析消息"""
        # 已经在 _handle_client 中解析
        return None
    
    def get_connection_info(self) -> Dict:
        """获取连接信息"""
        return {
            "total_connections": len(self._connections),
            "unique_users": len(self._user_connections),
            "connections": [
                {
                    "id": c.connection_id,
                    "user_id": c.user_id,
                    "age": (datetime.now() - c.created_at).total_seconds()
                }
                for c in self._connections.values()
            ]
        }


# ==================== 便捷创建函数 ====================

def create_webchat_adapter(host: str = "0.0.0.0", port: int = 8765) -> WebChatAdapter:
    """创建 WebChat 适配器"""
    config = {
        "host": host,
        "port": port
    }
    return WebChatAdapter(config)
