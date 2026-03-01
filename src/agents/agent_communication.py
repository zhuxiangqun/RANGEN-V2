#!/usr/bin/env python3
"""
Agent通信协议
实现Agent间的消息传递和协作
"""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Agent消息"""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str  # request, response, broadcast, notification
    content: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    response_to: Optional[str] = None  # 如果是响应，指向原始消息ID


class AgentCommunicationProtocol:
    """Agent通信协议"""
    
    def __init__(self):
        self.message_queue = asyncio.Queue()
        self.registered_agents: Dict[str, Any] = {}  # agent_id -> agent实例
        self.pending_responses: Dict[str, asyncio.Future] = {}
        self.message_history: List[Message] = []
        self.max_history = 1000
    
    def register_agent(self, agent_id: str, agent: Any) -> bool:
        """注册Agent"""
        try:
            if agent_id in self.registered_agents:
                logger.warning(f"Agent {agent_id} 已注册，将被覆盖")
            
            self.registered_agents[agent_id] = agent
            logger.info(f"✅ Agent注册成功: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Agent注册失败: {agent_id}, 错误={e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent"""
        try:
            if agent_id in self.registered_agents:
                del self.registered_agents[agent_id]
                logger.info(f"✅ Agent注销成功: {agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Agent注销失败: {agent_id}, 错误={e}")
            return False
    
    async def send_message(self, from_agent: str, to_agent: str, 
                          message_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """发送消息"""
        try:
            message_id = str(uuid.uuid4())
            message = Message(
                message_id=message_id,
                from_agent=from_agent,
                to_agent=to_agent,
                message_type=message_type,
                content=content
            )
            
            # 添加到历史
            self.message_history.append(message)
            if len(self.message_history) > self.max_history:
                self.message_history.pop(0)
            
            # 如果目标Agent已注册，直接处理
            if to_agent in self.registered_agents:
                target_agent = self.registered_agents[to_agent]
                response = await self._handle_message(target_agent, message)
                return response
            
            # 否则放入消息队列
            await self.message_queue.put(message)
            
            # 等待响应（如果是request类型）
            if message_type == "request":
                future = asyncio.Future()
                self.pending_responses[message_id] = future
                response = await future
                del self.pending_responses[message_id]
                return response
            
            return {"success": True, "message_id": message_id}
            
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def broadcast(self, from_agent: str, message_type: str, 
                       content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """广播消息"""
        responses = []
        for agent_id in self.registered_agents:
            if agent_id != from_agent:
                response = await self.send_message(from_agent, agent_id, message_type, content)
                responses.append(response)
        return responses
    
    async def _handle_message(self, agent: Any, message: Message) -> Dict[str, Any]:
        """处理消息"""
        try:
            # 如果Agent有handle_message方法，调用它
            if hasattr(agent, 'handle_message'):
                response = await agent.handle_message(message)
                return response
            
            # 否则返回默认响应
            return {
                "success": True,
                "message_id": message.message_id,
                "response": "消息已接收"
            }
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_message_history(self, agent_id: Optional[str] = None) -> List[Message]:
        """获取消息历史"""
        if agent_id:
            return [msg for msg in self.message_history 
                   if msg.from_agent == agent_id or msg.to_agent == agent_id]
        return self.message_history.copy()

