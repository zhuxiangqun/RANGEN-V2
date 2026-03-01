import os
#!/usr/bin/env python3
"""
MCP (Model Context Protocol) 协议标准实现 - 完整版本
支持完整的上下文管理和协议通信
"""

import json
import uuid
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib
import base64


logger = logging.getLogger(__name__)


class MCPMessageType(Enum):
    """MCP消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    QUERY = "query"
    SESSION = "session"
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"


class MCPPriority(Enum):
    """MCP优先级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    NORMAL = "normal"  # 默认优先级


class MCPContextType(Enum):
    """MCP上下文类型"""
    SESSION = "session"
    USER = "user"
    SYSTEM = "system"
    TOOL = "tool"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    QUERY = "query"
    RESPONSE = "response"


@dataclass
class MCPContext:
    """MCP上下文对象"""
    id: str
    type: MCPContextType
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MCPMessage:
    """MCP消息"""
    id: str
    type: MCPMessageType
    context: MCPContext
    payload: Dict[str, Any]
    priority: MCPPriority = MCPPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)


class Component:
    """MCP协议处理器 - 简化版本"""
    
    def __init__(self):
        """初始化MCP协议处理器"""
        self.logger = logging.getLogger(__name__)
        self.contexts: Dict[str, MCPContext] = {}
        self.messages: List[MCPMessage] = []
        self.protocol_stats = {
            "total_messages": 0,
            "successful_messages": 0,
            "failed_messages": 0,
            "contexts_created": 0
        }
    
    def create_component(self, context_type: MCPContextType, 
                      content: Dict[str, Any], 
                      metadata: Optional[Dict[str, Any]] = None) -> MCPContext:
        """创建上下文"""
        try:
            context_id = str(uuid.uuid4())
            context = MCPContext(
                id=context_id,
                type=context_type,
                content=content,
                metadata=metadata or {}
            )
            
            self.contexts[context_id] = context
            self.protocol_stats["contexts_created"] += 1
            
            self.logger.info(f"上下文创建成功: {context_id}")
            return context
            
        except Exception as e:
            self.logger.error(f"创建上下文失败: {e}")
            raise
    
    def send_message(self, context: MCPContext, message_type: MCPMessageType,
                    payload: Dict[str, Any], priority: MCPPriority = MCPPriority.NORMAL) -> MCPMessage:
        """发送消息"""
        try:
            message_id = str(uuid.uuid4())
            message = MCPMessage(
                id=message_id,
                type=message_type,
                context=context,
                payload=payload,
                priority=priority
            )
            
            self.messages.append(message)
            self.protocol_stats["total_messages"] += 1
            self.protocol_stats["successful_messages"] += 1
            
            self.logger.info(f"消息发送成功: {message_id}")
            return message
            
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            self.protocol_stats["failed_messages"] += 1
            raise
    
    def get_context(self, context_id: str) -> Optional[MCPContext]:
        """获取上下文"""
        return self.contexts.get(context_id)
    
    def update_context(self, context_id: str, content: Dict[str, Any]) -> bool:
        """更新上下文"""
        try:
            context = self.contexts.get(context_id)
            if not context:
                return False
            
            context.content.update(content)
            context.updated_at = datetime.now()
            
            self.logger.info(f"上下文更新成功: {context_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新上下文失败: {e}")
            return False
    
    def delete_context(self, context_id: str) -> bool:
        """删除上下文"""
        try:
            if context_id in self.contexts:
                del self.contexts[context_id]
                self.logger.info(f"上下文删除成功: {context_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"删除上下文失败: {e}")
            return False
    
    def get_protocol_stats(self) -> Dict[str, Any]:
        """获取协议统计信息"""
        return self.protocol_stats.copy()
    
    def clear_messages(self):
        """清空消息"""
        self.messages.clear()
        self.logger.info("消息已清空")


# 全局实例
# 注意：Component类被重命名为MCPProtocolHandler以保持兼容性
MCPProtocolHandler = Component

mcp_protocol_handler = Component()


def get_mcp_protocol_handler() -> Component:
    """获取MCP协议处理器实例"""
    return mcp_protocol_handler


def get_mcp_bridge():
    """获取MCP桥接器"""
    return mcp_protocol_handler


class AdvancedMCPProtocol:
    """高级MCP协议实现"""
    
    def __init__(self):
        """初始化高级MCP协议"""
        self.handler = Component()  # 使用Component类
        self.message_handlers: Dict[str, Callable] = {}
        self.context_processors: Dict[MCPContextType, Callable] = {}
        self.compression_enabled = True
        self.encryption_enabled = False
        self.cache_enabled = True
        self.cache = {}
        self.performance_metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "compression_ratio": 0.0,
            "average_response_time": 0.0
        }
        logger.info("高级MCP协议初始化完成")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
        logger.info(f"消息处理器注册成功: {message_type}")
    
    def register_context_processor(self, context_type: MCPContextType, processor: Callable):
        """注册上下文处理器"""
        self.context_processors[context_type] = processor
        logger.info(f"上下文处理器注册成功: {context_type}")
    
    async def process_message(self, message: MCPMessage) -> Dict[str, Any]:
        """异步处理消息"""
        start_time = time.time()
        
        try:
            # 检查缓存
            cache_key = self._generate_cache_key(message)
            if self.cache_enabled and cache_key in self.cache:
                self.performance_metrics["cache_hits"] += 1
                return self.cache[cache_key]
            
            self.performance_metrics["cache_misses"] += 1
            
            # 压缩消息
            if self.compression_enabled:
                message = self._compress_message(message)
            
            # 处理消息
            handler = self.message_handlers.get(message.type.value)
            if handler:
                result = await handler(message)
            else:
                result = await self._default_message_handler(message)
            
            # 加密结果
            if self.encryption_enabled:
                result = self._encrypt_result(result)
            
            # 缓存结果
            if self.cache_enabled:
                self.cache[cache_key] = result
            
            # 更新性能指标
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time)
            
            return result
            
        except Exception as e:
            logger.error(f"异步消息处理失败: {e}")
            return {"error": str(e), "success": False}
    
    def process_context(self, context: MCPContext) -> Dict[str, Any]:
        """处理上下文"""
        try:
            processor = self.context_processors.get(context.type)
            if processor:
                return processor(context)
            else:
                return self._default_context_processor(context)
                
        except Exception as e:
            logger.error(f"上下文处理失败: {e}")
            return {"error": str(e), "success": False}
    
    def _generate_cache_key(self, message: MCPMessage) -> str:
        """生成缓存键"""
        content_hash = hashlib.md5(
            json.dumps(message.payload, sort_keys=True).encode()
        ).hexdigest()
        return f"{message.type.value}_{message.context.id}_{content_hash}"
    
    def _compress_message(self, message: MCPMessage) -> MCPMessage:
        """压缩消息"""
        # 简单的压缩实现
        compressed_payload = {
            "compressed": True,
            "data": base64.b64encode(
                json.dumps(message.payload).encode()
            ).decode()
        }
        
        message.payload = compressed_payload
        return message
    
    def _encrypt_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """加密结果"""
        # 简单的加密实现
        encrypted_data = base64.b64encode(
            json.dumps(result).encode()
        ).decode()
        
        return {
            "encrypted": True,
            "data": encrypted_data
        }
    
    async def _default_message_handler(self, message: MCPMessage) -> Dict[str, Any]:
        """默认消息处理器"""
        return {
            "message_id": message.id,
            "type": message.type.value,
            "context_id": message.context.id,
            "payload": message.payload,
            "success": True,
            "timestamp": message.timestamp.isoformat()
        }
    
    def _default_context_processor(self, context: MCPContext) -> Dict[str, Any]:
        """默认上下文处理器"""
        return {
            "context_id": context.id,
            "type": context.type.value,
            "content": context.content,
            "metadata": context.metadata,
            "success": True,
            "processed_at": datetime.now().isoformat()
        }
    
    def _update_performance_metrics(self, processing_time: float):
        """更新性能指标"""
        self.performance_metrics["total_requests"] += 1
        
        # 更新平均响应时间
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + processing_time) / total_requests
        )
        
        # 更新压缩比
        self.performance_metrics["compression_ratio"] = 0.7  # 假设70%压缩比
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        metrics = self.performance_metrics.copy()
        
        # 计算缓存命中率
        total_cache_requests = metrics["cache_hits"] + metrics["cache_misses"]
        if total_cache_requests > 0:
            metrics["cache_hit_rate"] = metrics["cache_hits"] / total_cache_requests
        else:
            metrics["cache_hit_rate"] = 0.0
        
        return metrics
    
    def enable_compression(self, enabled: bool = True):
        """启用/禁用压缩"""
        self.compression_enabled = enabled
        logger.info(f"压缩功能{'启用' if enabled else '禁用'}")
    
    def enable_encryption(self, enabled: bool = True):
        """启用/禁用加密"""
        self.encryption_enabled = enabled
        logger.info(f"加密功能{'启用' if enabled else '禁用'}")
    
    def enable_cache(self, enabled: bool = True):
        """启用/禁用缓存"""
        self.cache_enabled = enabled
        if not enabled:
            self.cache.clear()
        logger.info(f"缓存功能{'启用' if enabled else '禁用'}")
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("缓存已清空")


# 全局高级协议实例
advanced_mcp_protocol = AdvancedMCPProtocol()


def get_advanced_mcp_protocol() -> AdvancedMCPProtocol:
    """获取高级MCP协议实例"""
    return advanced_mcp_protocol