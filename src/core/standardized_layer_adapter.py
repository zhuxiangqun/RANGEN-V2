#!/usr/bin/env python3
"""
标准化层适配器 - 将FourLayerManager协议适配到标准化接口系统

V3优化：为四层架构提供标准化的接口适配器，实现协议方法与标准化消息的转换。
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, cast

from .layer_interface_standard import (
    LayerMessage, LayerMessageHeader, LayerType, MessageType, 
    MessagePriority, StandardizedInterface
)
from .four_layer_manager import (
    InteractionLayerProtocol, GatewayLayerProtocol, 
    AgentLayerProtocol, ToolLayerProtocol
)

logger = logging.getLogger(__name__)


class StandardizedInteractionAdapter(StandardizedInterface):
    """标准化交互层适配器 - 适配InteractionLayerProtocol到标准化接口"""
    
    def __init__(self, protocol_impl: InteractionLayerProtocol, component_id: str = "interaction_adapter"):
        super().__init__(LayerType.INTERACTION, component_id)
        self.protocol_impl = protocol_impl
        self._register_protocol_handlers()
    
    def _register_protocol_handlers(self):
        """注册协议方法的处理器"""
        self.register_handler("handle_user_input", self._handle_user_input)
        self.register_handler("deliver_response", self._deliver_response)
    
    async def _handle_user_input(self, message: LayerMessage) -> LayerMessage:
        """处理用户输入请求"""
        input_data = message.payload.get("data", {})
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.handle_user_input(input_data)
            
            # 创建响应
            return message.create_response({
                "processed_input": result.get("processed_input", {}),
                "validation_passed": result.get("validation_passed", True),
                "protocol_result": result
            })
        except Exception as e:
            logger.error(f"交互层协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _deliver_response(self, message: LayerMessage) -> LayerMessage:
        """交付响应给用户"""
        response_data = message.payload.get("data", {})
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.deliver_response(response_data)
            
            # 创建响应
            return message.create_response({
                "delivery_status": result.get("status", "unknown"),
                "delivery_message": result.get("message", ""),
                "protocol_result": result
            })
        except Exception as e:
            logger.error(f"响应交付协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )


class StandardizedGatewayAdapter(StandardizedInterface):
    """标准化网关层适配器 - 适配GatewayLayerProtocol到标准化接口"""
    
    def __init__(self, protocol_impl: GatewayLayerProtocol, component_id: str = "gateway_adapter"):
        super().__init__(LayerType.GATEWAY, component_id)
        self.protocol_impl = protocol_impl
        self._register_protocol_handlers()
    
    def _register_protocol_handlers(self):
        """注册协议方法的处理器"""
        self.register_handler("route_message", self._route_message)
        self.register_handler("perform_safety_check", self._perform_safety_check)
        self.register_handler("assemble_agents", self._assemble_agents)
    
    async def _route_message(self, message: LayerMessage) -> LayerMessage:
        """路由消息到适当的目标层"""
        routing_data = message.payload.get("data", {})
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.route_message(routing_data)
            
            # 创建响应
            return message.create_response({
                "routing_info": result.get("routing_info", {}),
                "target_layer": result.get("routing_info", {}).get("target_layer"),
                "target_component": result.get("routing_info", {}).get("target_component"),
                "protocol_result": result
            })
        except Exception as e:
            logger.error(f"消息路由协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _perform_safety_check(self, message: LayerMessage) -> LayerMessage:
        """执行安全检查"""
        check_data = message.payload.get("data", {})
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.perform_safety_check(check_data)
            
            # 创建响应
            return message.create_response({
                "safe": result.get("safe", True),
                "reasons": result.get("reasons", []),
                "risk_level": result.get("risk_level", "low"),
                "protocol_result": result
            })
        except Exception as e:
            logger.error(f"安全检查协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _assemble_agents(self, message: LayerMessage) -> LayerMessage:
        """组装Agent团队"""
        task_data = message.payload.get("data", {})
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.assemble_agents(task_data)
            
            # 创建响应 - 注意：协议方法返回List[str]，需要包装
            return message.create_response({
                "agent_team": result,  # 这已经是列表
                "team_size": len(result),
                "protocol_result": {"agent_ids": result}
            })
        except Exception as e:
            logger.error(f"Agent组装协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )


class StandardizedAgentAdapter(StandardizedInterface):
    """标准化Agent层适配器 - 适配AgentLayerProtocol到标准化接口"""
    
    def __init__(self, protocol_impl: AgentLayerProtocol, component_id: str = "agent_adapter"):
        super().__init__(LayerType.AGENT, component_id)
        self.protocol_impl = protocol_impl
        self._register_protocol_handlers()
    
    def _register_protocol_handlers(self):
        """注册协议方法的处理器"""
        self.register_handler("execute_task", self._execute_task)
        self.register_handler("get_agent_capabilities", self._get_agent_capabilities)
        self.register_handler("form_team", self._form_team)
    
    async def _execute_task(self, message: LayerMessage) -> LayerMessage:
        """执行任务"""
        task_data = message.payload.get("data", {})
        agent_id = task_data.get("agent_id", "")
        
        if not agent_id:
            return message.create_response(
                {},
                status="error",
                error_message="Missing agent_id in task data"
            )
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.execute_task(agent_id, task_data)
            
            # 创建响应
            return message.create_response({
                "agent_id": agent_id,
                "task_result": result,
                "execution_status": "completed",
                "protocol_result": result
            })
        except Exception as e:
            logger.error(f"任务执行协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _get_agent_capabilities(self, message: LayerMessage) -> LayerMessage:
        """获取Agent能力"""
        request_data = message.payload.get("data", {})
        agent_id = request_data.get("agent_id", "")
        
        if not agent_id:
            return message.create_response(
                {},
                status="error",
                error_message="Missing agent_id in request data"
            )
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.get_agent_capabilities(agent_id)
            
            # 创建响应
            return message.create_response({
                "agent_id": agent_id,
                "capabilities": result,
                "capability_count": len(result),
                "protocol_result": {"capabilities": result}
            })
        except Exception as e:
            logger.error(f"获取能力协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _form_team(self, message: LayerMessage) -> LayerMessage:
        """组建团队"""
        team_data = message.payload.get("data", {})
        agent_ids = team_data.get("agent_ids", [])
        team_purpose = team_data.get("team_purpose", "")
        
        if not agent_ids or not team_purpose:
            return message.create_response(
                {},
                status="error",
                error_message="Missing agent_ids or team_purpose in team data"
            )
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.form_team(agent_ids, team_purpose)
            
            # 创建响应
            return message.create_response({
                "team_id": result,
                "agent_ids": agent_ids,
                "team_purpose": team_purpose,
                "protocol_result": {"team_id": result}
            })
        except Exception as e:
            logger.error(f"组建团队协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )


class StandardizedToolAdapter(StandardizedInterface):
    """标准化工具层适配器 - 适配ToolLayerProtocol到标准化接口"""
    
    def __init__(self, protocol_impl: ToolLayerProtocol, component_id: str = "tool_adapter"):
        super().__init__(LayerType.TOOL, component_id)
        self.protocol_impl = protocol_impl
        self._register_protocol_handlers()
    
    def _register_protocol_handlers(self):
        """注册协议方法的处理器"""
        self.register_handler("execute_tool", self._execute_tool)
        self.register_handler("discover_tools", self._discover_tools)
        self.register_handler("register_tool", self._register_tool)
    
    async def _execute_tool(self, message: LayerMessage) -> LayerMessage:
        """执行工具"""
        tool_data = message.payload.get("data", {})
        tool_id = tool_data.get("tool_id", "")
        params = tool_data.get("params", {})
        
        if not tool_id:
            return message.create_response(
                {},
                status="error",
                error_message="Missing tool_id in tool data"
            )
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.execute_tool(tool_id, params)
            
            # 创建响应
            return message.create_response({
                "tool_id": tool_id,
                "execution_result": result,
                "success": result.get("success", False),
                "protocol_result": result
            })
        except Exception as e:
            logger.error(f"工具执行协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _discover_tools(self, message: LayerMessage) -> LayerMessage:
        """发现可用工具"""
        request_data = message.payload.get("data", {})
        capability_filter = request_data.get("capability_filter")
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.discover_tools(capability_filter)
            
            # 创建响应
            return message.create_response({
                "tools": result,
                "tool_count": len(result),
                "capability_filter": capability_filter,
                "protocol_result": {"tools": result}
            })
        except Exception as e:
            logger.error(f"工具发现协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )
    
    async def _register_tool(self, message: LayerMessage) -> LayerMessage:
        """注册新工具"""
        tool_data = message.payload.get("data", {})
        tool_definition = tool_data.get("tool_definition", {})
        
        if not tool_definition:
            return message.create_response(
                {},
                status="error",
                error_message="Missing tool_definition in registration data"
            )
        
        try:
            # 调用协议方法
            result = await self.protocol_impl.register_tool(tool_definition)
            
            # 创建响应
            return message.create_response({
                "registered_tool_id": result,
                "tool_definition": tool_definition,
                "registration_status": "success",
                "protocol_result": {"tool_id": result}
            })
        except Exception as e:
            logger.error(f"工具注册协议处理失败: {e}")
            return message.create_response(
                {},
                status="error",
                error_message=f"Protocol execution failed: {str(e)}"
            )


def create_standardized_four_layer_setup(protocol_adapters: Dict[str, Any]) -> Dict[str, Any]:
    """创建标准化的四层架构设置"""
    from .layer_interface_standard import get_layer_communication_bus
    
    bus = get_layer_communication_bus()
    
    # 创建标准化适配器并注册到总线
    standardized_adapters = {}
    
    # 交互层
    if "interaction" in protocol_adapters:
        interaction_adapter = StandardizedInteractionAdapter(
            protocol_adapters["interaction"],
            "standardized_interaction"
        )
        bus.register_component(interaction_adapter)
        standardized_adapters["interaction"] = interaction_adapter
        logger.info("标准化交互层适配器已创建并注册")
    
    # 网关层
    if "gateway" in protocol_adapters:
        gateway_adapter = StandardizedGatewayAdapter(
            protocol_adapters["gateway"],
            "standardized_gateway"
        )
        bus.register_component(gateway_adapter)
        standardized_adapters["gateway"] = gateway_adapter
        logger.info("标准化网关层适配器已创建并注册")
    
    # Agent层
    if "agent" in protocol_adapters:
        agent_adapter = StandardizedAgentAdapter(
            protocol_adapters["agent"],
            "standardized_agent"
        )
        bus.register_component(agent_adapter)
        standardized_adapters["agent"] = agent_adapter
        logger.info("标准化Agent层适配器已创建并注册")
    
    # 工具层
    if "tool" in protocol_adapters:
        tool_adapter = StandardizedToolAdapter(
            protocol_adapters["tool"],
            "standardized_tool"
        )
        bus.register_component(tool_adapter)
        standardized_adapters["tool"] = tool_adapter
        logger.info("标准化工具层适配器已创建并注册")
    
    logger.info("标准化四层架构设置完成")
    
    return {
        "communication_bus": bus,
        "standardized_adapters": standardized_adapters,
        "protocol_adapters": protocol_adapters
    }


async def test_standardized_four_layer_integration():
    """测试标准化四层架构集成"""
    from .four_layer_adapters import (
        InteractionLayerAdapter, GatewayLayerAdapter,
        AgentLayerAdapter, ToolLayerAdapter
    )
    from .gateway import RANGENGateway
    from .hierarchical_tool_system import HierarchicalToolSystem
    
    print("=" * 60)
    print("测试标准化四层架构集成")
    print("=" * 60)
    
    # 创建协议适配器
    protocol_adapters = {
        "interaction": InteractionLayerAdapter(),
        "gateway": GatewayLayerAdapter(RANGENGateway()),
        "agent": AgentLayerAdapter(),
        "tool": ToolLayerAdapter(HierarchicalToolSystem())
    }
    
    # 创建标准化设置
    setup = create_standardized_four_layer_setup(protocol_adapters)
    bus = setup["communication_bus"]
    
    # 发送测试消息 - 交互层 -> 网关层
    interaction_adapter = setup["standardized_adapters"]["interaction"]
    
    # 创建用户输入消息
    user_input_message = interaction_adapter.create_message(
        target_layer=LayerType.GATEWAY,
        target_component="standardized_gateway",
        action="perform_safety_check",
        data={
            "content": "Hello, this is a test message",
            "user_id": "test_user_001",
            "session_id": "test_session_001"
        }
    )
    
    print(f"发送用户输入消息: {user_input_message.header.source_component} -> {user_input_message.header.target_component}")
    print(f"消息ID: {user_input_message.header.message_id}")
    print(f"消息类型: {user_input_message.header.message_type.value}")
    
    # 发送消息
    response = await bus.send_message(user_input_message)
    
    print(f"收到响应: {response.payload.get('status', 'unknown')}")
    print(f"安全检查结果: safe={response.payload.get('data', {}).get('safe', 'unknown')}")
    
    # 获取总线状态
    status = bus.get_component_status()
    print(f"\n总线状态: {status['total_components']} 个组件注册")
    
    for component_key, comp_info in status["components"].items():
        print(f"  - {component_key}: {comp_info['handler_count']} 个处理器")
    
    print("=" * 60)
    print("✅ 标准化四层架构集成测试完成")
    print("=" * 60)
    
    return setup


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_standardized_four_layer_integration())