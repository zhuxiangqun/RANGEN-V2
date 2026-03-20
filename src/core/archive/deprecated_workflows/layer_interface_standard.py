#!/usr/bin/env python3
"""
层间接口标准化
Layer Interface Standardization

V3优化：优化四层架构的层间接口标准化，实现清晰的架构分层和层间标准化接口。
"""
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Union, TypedDict
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class LayerType(Enum):
    """层类型"""
    INTERACTION = "interaction"
    GATEWAY = "gateway"
    AGENT = "agent"
    TOOL = "tool"
    SYSTEM = "system"  # 系统层，用于内部通信


class MessageType(Enum):
    """消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class MessagePriority(Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LayerMessageHeader:
    """层间消息头"""
    message_id: str
    message_type: MessageType
    priority: MessagePriority
    timestamp: float
    source_layer: LayerType
    source_component: str
    target_layer: LayerType
    target_component: str
    correlation_id: Optional[str] = None  # 用于关联请求和响应
    session_id: Optional[str] = None
    ttl_seconds: float = 300.0  # 消息生存时间（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "source_layer": self.source_layer.value,
            "source_component": self.source_component,
            "target_layer": self.target_layer.value,
            "target_component": self.target_component,
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "ttl_seconds": self.ttl_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerMessageHeader':
        """从字典创建消息头"""
        return cls(
            message_id=data.get("message_id", str(uuid.uuid4())),
            message_type=MessageType(data.get("message_type", "request")),
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=data.get("timestamp", time.time()),
            source_layer=LayerType(data.get("source_layer", "system")),
            source_component=data.get("source_component", ""),
            target_layer=LayerType(data.get("target_layer", "system")),
            target_component=data.get("target_component", ""),
            correlation_id=data.get("correlation_id"),
            session_id=data.get("session_id"),
            ttl_seconds=data.get("ttl_seconds", 300.0)
        )
    
    def is_expired(self) -> bool:
        """检查消息是否过期"""
        return time.time() - self.timestamp > self.ttl_seconds


@dataclass
class LayerMessage:
    """标准化的层间消息"""
    header: LayerMessageHeader
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后验证"""
        if not self.header.message_id:
            self.header.message_id = str(uuid.uuid4())
        if not self.header.timestamp:
            self.header.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "header": self.header.to_dict(),
            "payload": self.payload,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LayerMessage':
        """从字典创建消息"""
        header_data = data.get("header", {})
        # 如果timestamp是字符串，转换为时间戳
        if "timestamp" in header_data and isinstance(header_data["timestamp"], str):
            try:
                dt = datetime.fromisoformat(header_data["timestamp"].replace('Z', '+00:00'))
                header_data["timestamp"] = dt.timestamp()
            except ValueError:
                header_data["timestamp"] = time.time()
        
        header = LayerMessageHeader.from_dict(header_data)
        return cls(
            header=header,
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {})
        )
    
    def create_response(self, 
                        payload: Dict[str, Any], 
                        status: str = "success",
                        error_message: Optional[str] = None) -> 'LayerMessage':
        """创建响应消息"""
        response_header = LayerMessageHeader(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.RESPONSE,
            priority=self.header.priority,
            timestamp=time.time(),
            source_layer=self.header.target_layer,  # 响应来源是原始目标
            source_component=self.header.target_component,
            target_layer=self.header.source_layer,  # 响应目标是原始来源
            target_component=self.header.source_component,
            correlation_id=self.header.message_id,  # 关联原始请求
            session_id=self.header.session_id,
            ttl_seconds=self.header.ttl_seconds
        )
        
        response_payload = {
            "status": status,
            "original_message_id": self.header.message_id,
            "data": payload
        }
        
        if error_message:
            response_payload["error"] = error_message
        
        return LayerMessage(
            header=response_header,
            payload=response_payload,
            metadata={"response_to": self.header.message_id}
        )


class StandardizedInterface:
    """标准化接口基类"""
    
    def __init__(self, layer_type: LayerType, component_id: str):
        self.layer_type = layer_type
        self.component_id = component_id
        self.message_handlers: Dict[str, callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.register_handler("ping", self._handle_ping)
        self.register_handler("health_check", self._handle_health_check)
    
    async def _handle_ping(self, message: LayerMessage) -> LayerMessage:
        """处理ping消息"""
        return message.create_response({"pong": True, "timestamp": time.time()})
    
    async def _handle_health_check(self, message: LayerMessage) -> LayerMessage:
        """处理健康检查消息"""
        return message.create_response({
            "status": "healthy",
            "component_id": self.component_id,
            "layer_type": self.layer_type.value,
            "timestamp": time.time()
        })
    
    def register_handler(self, action: str, handler: callable):
        """注册消息处理器"""
        self.message_handlers[action] = handler
        logger.debug(f"注册消息处理器: {self.component_id} -> {action}")
    
    async def process_message(self, message: LayerMessage) -> LayerMessage:
        """处理消息"""
        # 检查消息是否过期
        if message.header.is_expired():
            logger.warning(f"消息已过期: {message.header.message_id}")
            return message.create_response(
                {}, 
                status="error", 
                error_message="Message expired"
            )
        
        # 检查目标是否匹配
        if (message.header.target_layer != self.layer_type or 
            message.header.target_component != self.component_id):
            logger.warning(f"消息目标不匹配: {message.header.target_component} != {self.component_id}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Target mismatch: expected {self.component_id}"
            )
        
        # 从payload中提取action
        action = message.payload.get("action", "")
        if not action:
            return message.create_response(
                {},
                status="error",
                error_message="No action specified in payload"
            )
        
        # 查找处理器
        handler = self.message_handlers.get(action)
        if not handler:
            return message.create_response(
                {},
                status="error",
                error_message=f"Unknown action: {action}"
            )
        
        try:
            # 执行处理器
            logger.debug(f"处理消息: {self.component_id} -> {action}")
            return await handler(message)
        except Exception as e:
            logger.error(f"消息处理失败 {action}: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Handler execution failed: {str(e)}"
            )
    
    def create_message(self, 
                      target_layer: LayerType,
                      target_component: str,
                      action: str,
                      data: Dict[str, Any],
                      message_type: MessageType = MessageType.REQUEST,
                      priority: MessagePriority = MessagePriority.NORMAL,
                      correlation_id: Optional[str] = None,
                      session_id: Optional[str] = None) -> LayerMessage:
        """创建标准化消息"""
        header = LayerMessageHeader(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            priority=priority,
            timestamp=time.time(),
            source_layer=self.layer_type,
            source_component=self.component_id,
            target_layer=target_layer,
            target_component=target_component,
            correlation_id=correlation_id,
            session_id=session_id
        )
        
        payload = {
            "action": action,
            "data": data,
            "timestamp": time.time()
        }
        
        return LayerMessage(
            header=header,
            payload=payload
        )


class LayerCommunicationBus:
    """层间通信总线"""
    
    def __init__(self):
        self.components: Dict[str, StandardizedInterface] = {}
        self.message_history: List[LayerMessage] = []
        self.max_history_size = 1000
        logger.info("层间通信总线初始化完成")
    
    def register_component(self, component: StandardizedInterface):
        """注册组件"""
        component_key = f"{component.layer_type.value}:{component.component_id}"
        self.components[component_key] = component
        logger.info(f"注册组件: {component_key}")
    
    def unregister_component(self, layer_type: LayerType, component_id: str):
        """注销组件"""
        component_key = f"{layer_type.value}:{component_id}"
        if component_key in self.components:
            del self.components[component_key]
            logger.info(f"注销组件: {component_key}")
    
    async def send_message(self, message: LayerMessage) -> LayerMessage:
        """发送消息并等待响应"""
        # 记录消息
        self.message_history.append(message)
        if len(self.message_history) > self.max_history_size:
            self.message_history = self.message_history[-self.max_history_size:]
        
        # 查找目标组件
        component_key = f"{message.header.target_layer.value}:{message.header.target_component}"
        target_component = self.components.get(component_key)
        
        if not target_component:
            logger.error(f"目标组件不存在: {component_key}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Target component not found: {component_key}"
            )
        
        # 发送消息到目标组件
        try:
            logger.debug(f"发送消息: {message.header.source_component} -> {message.header.target_component}")
            response = await target_component.process_message(message)
            
            # 记录响应
            self.message_history.append(response)
            if len(self.message_history) > self.max_history_size:
                self.message_history = self.message_history[-self.max_history_size:]
            
            return response
        except Exception as e:
            logger.error(f"消息发送失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Message delivery failed: {str(e)}"
            )
    
    async def broadcast_message(self, 
                               source_component: StandardizedInterface,
                               target_layer: LayerType,
                               action: str,
                               data: Dict[str, Any]) -> List[LayerMessage]:
        """广播消息到指定层的所有组件"""
        responses = []
        
        # 查找目标层的所有组件
        target_components = [
            comp for comp in self.components.values() 
            if comp.layer_type == target_layer
        ]
        
        logger.info(f"广播消息到 {target_layer.value} 层的 {len(target_components)} 个组件")
        
        # 发送消息到每个组件
        for target_component in target_components:
            message = source_component.create_message(
                target_layer=target_layer,
                target_component=target_component.component_id,
                action=action,
                data=data,
                message_type=MessageType.NOTIFICATION
            )
            
            try:
                response = await self.send_message(message)
                responses.append(response)
            except Exception as e:
                logger.error(f"广播消息失败到 {target_component.component_id}: {e}")
        
        return responses
    
    def get_component_status(self, layer_type: LayerType = None) -> Dict[str, Any]:
        """获取组件状态"""
        if layer_type:
            components = [
                comp for comp in self.components.values()
                if comp.layer_type == layer_type
            ]
        else:
            components = list(self.components.values())
        
        status = {
            "total_components": len(components),
            "components": {}
        }
        
        for comp in components:
            component_key = f"{comp.layer_type.value}:{comp.component_id}"
            status["components"][component_key] = {
                "layer_type": comp.layer_type.value,
                "component_id": comp.component_id,
                "handler_count": len(comp.message_handlers)
            }
        
        return status
    
    def get_recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近的消息"""
        recent = self.message_history[-limit:] if self.message_history else []
        return [msg.to_dict() for msg in recent]


# 便捷函数
_communication_bus: Optional[LayerCommunicationBus] = None

def get_layer_communication_bus() -> LayerCommunicationBus:
    """获取层间通信总线实例"""
    global _communication_bus
    if _communication_bus is None:
        _communication_bus = LayerCommunicationBus()
    return _communication_bus

def create_standardized_interface(layer_type: LayerType, component_id: str) -> StandardizedInterface:
    """创建标准化接口实例"""
    return StandardizedInterface(layer_type, component_id)


if __name__ == "__main__":
    # 测试代码
    import asyncio
    
    async def test_interface_standardization():
        print("=" * 60)
        print("测试层间接口标准化")
        print("=" * 60)
        
        # 创建通信总线
        bus = LayerCommunicationBus()
        
        # 创建两个测试组件
        interaction_component = create_standardized_interface(
            LayerType.INTERACTION, 
            "web_interface"
        )
        
        gateway_component = create_standardized_interface(
            LayerType.GATEWAY,
            "main_gateway"
        )
        
        # 注册组件
        bus.register_component(interaction_component)
        bus.register_component(gateway_component)
        
        # 发送测试消息
        message = interaction_component.create_message(
            target_layer=LayerType.GATEWAY,
            target_component="main_gateway",
            action="ping",
            data={"test": "data"}
        )
        
        print(f"发送消息: {message.header.source_component} -> {message.header.target_component}")
        response = await bus.send_message(message)
        
        print(f"收到响应: {response.payload.get('status', 'unknown')}")
        print(f"响应数据: {response.payload.get('data', {})}")
        
        # 获取状态
        status = bus.get_component_status()
        print(f"\n组件状态: {status['total_components']} 个组件")
        
        print("=" * 60)
        print("✅ 层间接口标准化测试完成")
        print("=" * 60)
    
    asyncio.run(test_interface_standardization())