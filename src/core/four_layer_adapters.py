#!/usr/bin/env python3
"""
四层架构适配器 - 将现有组件适配到四层架构协议
"""

import logging
from typing import Dict, List, Any, Optional, cast
import asyncio

from .four_layer_manager import (
    InteractionLayerProtocol, GatewayLayerProtocol, 
    AgentLayerProtocol, ToolLayerProtocol
)
from .gateway import RANGENGateway
from .hierarchical_tool_system import HierarchicalToolSystem
from ..agents.professional_teams.professional_team_entrepreneur import ProfessionalTeamEntrepreneur
from ..agents.professional_teams.engineering_agent import EngineeringAgent
from ..agents.professional_teams.design_agent import DesignAgent
from ..agents.professional_teams.marketing_agent import MarketingAgent
from ..agents.professional_teams.testing_agent import TestingAgent

logger = logging.getLogger(__name__)


class GatewayLayerAdapter(GatewayLayerProtocol):
    """网关层适配器 - 适配RANGENGateway"""
    
    def __init__(self, gateway: RANGENGateway):
        self.gateway = gateway
    
    async def route_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """路由消息到适当的目标层"""
        # 使用现有gateway的路由逻辑
        routed_message = await self.gateway._route_message(message)
        return {
            "routing_info": {
                "target_layer": routed_message.get("target_layer", "agent"),
                "target_component": routed_message.get("target_component"),
                "priority": routed_message.get("priority", "normal")
            }
        }
    
    async def perform_safety_check(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """执行安全检查"""
        # 使用现有gateway的安全检查逻辑
        safety_result = await self.gateway._perform_safety_check(message)
        return {
            "safe": safety_result.get("safe", True),
            "reasons": safety_result.get("reasons", []),
            "risk_level": safety_result.get("risk_level", "low")
        }
    
    async def assemble_agents(self, task: Dict[str, Any]) -> List[str]:
        """组装Agent团队"""
        # 使用现有gateway的Agent组装逻辑
        assembly_context = await self.gateway._assemble_agents(task)
        agent_ids = assembly_context.get("agent_ids", [])
        return agent_ids


class AgentLayerAdapter(AgentLayerProtocol):
    """Agent层适配器 - 适配专业Agent团队"""
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}
        self.teams: Dict[str, List[str]] = {}
        self.entrepreneur: Optional[ProfessionalTeamEntrepreneur] = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """初始化专业Agent"""
        # 创建企业家协调员
        self.entrepreneur = ProfessionalTeamEntrepreneur.create_simplified(
            agent_id="entrepreneur_001",
            business_domain="技术创业",
            initial_capital=1000000.0
        )
        
        # 创建专业Agent
        engineering_agent = EngineeringAgent(
            agent_id="engineering_001",
            specialization="全栈开发"
        )
        
        design_agent = DesignAgent(
            agent_id="design_001",
            specialization="UI/UX设计"
        )
        
        marketing_agent = MarketingAgent(
            agent_id="marketing_001",
            specialization="数字营销"
        )
        
        testing_agent = TestingAgent(
            agent_id="testing_001",
            specialization="软件测试"
        )
        
        # 注册Agent
        self.agents[engineering_agent.agent_id] = engineering_agent
        self.agents[design_agent.agent_id] = design_agent
        self.agents[marketing_agent.agent_id] = marketing_agent
        self.agents[testing_agent.agent_id] = testing_agent
        
        # 向企业家注册Agent
        self.entrepreneur.register_agent(engineering_agent)
        self.entrepreneur.register_agent(design_agent)
        self.entrepreneur.register_agent(marketing_agent)
        self.entrepreneur.register_agent(testing_agent)
        
        logger.info(f"Agent层适配器初始化完成，注册了{len(self.agents)}个专业Agent")
    
    async def execute_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        if agent_id not in self.agents:
            # 如果没有特定Agent，尝试使用企业家协调员
            if self.entrepreneur:
                return await self.entrepreneur.execute_task(task)
            else:
                raise ValueError(f"未知Agent ID: {agent_id}")
        
        agent = self.agents[agent_id]
        return await agent.execute_task(task)
    
    async def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """获取Agent能力"""
        if agent_id not in self.agents:
            if self.entrepreneur and agent_id == self.entrepreneur.agent_id:
                return self.entrepreneur.get_capabilities()
            else:
                return []
        
        agent = self.agents[agent_id]
        # 假设Agent有capabilities属性
        if hasattr(agent, 'capabilities'):
            return agent.capabilities
        elif hasattr(agent, 'config') and hasattr(agent.config, 'capabilities'):
            return agent.config.capabilities
        else:
            return []
    
    async def form_team(self, agent_ids: List[str], team_purpose: str) -> str:
        """组建团队"""
        if not self.entrepreneur:
            raise RuntimeError("企业家协调员未初始化")
        
        # 验证Agent IDs
        valid_agent_ids = []
        for agent_id in agent_ids:
            if agent_id in self.agents:
                valid_agent_ids.append(agent_id)
            elif agent_id == self.entrepreneur.agent_id:
                valid_agent_ids.append(agent_id)
        
        if not valid_agent_ids:
            raise ValueError("没有有效的Agent ID")
        
        # 创建团队ID
        team_id = f"team_{hash(tuple(sorted(valid_agent_ids)) + (team_purpose,))}"
        
        # 企业家组建团队
        team = await self.entrepreneur.form_team(valid_agent_ids, team_purpose)
        self.teams[team_id] = valid_agent_ids
        
        logger.info(f"组建团队 {team_id}，目的: {team_purpose}，成员: {valid_agent_ids}")
        return team_id


class ToolLayerAdapter(ToolLayerProtocol):
    """工具层适配器 - 适配HierarchicalToolSystem"""
    
    def __init__(self, tool_system: HierarchicalToolSystem):
        self.tool_system = tool_system
    
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        # 使用现有工具系统的执行逻辑
        result = await self.tool_system.execute_tool(tool_id, params)
        return {
            "success": result.get("success", False),
            "output": result.get("output"),
            "error": result.get("error"),
            "execution_metrics": result.get("metrics", {})
        }
    
    async def discover_tools(self, capability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """发现可用工具"""
        # 使用现有工具系统的发现逻辑
        tools = await self.tool_system.discover_tools(capability_filter)
        return [
            {
                "tool_id": tool.get("id"),
                "name": tool.get("name"),
                "description": tool.get("description"),
                "capabilities": tool.get("capabilities", []),
                "category": tool.get("category")
            }
            for tool in tools
        ]
    
    async def register_tool(self, tool_definition: Dict[str, Any]) -> str:
        """注册新工具"""
        # 使用现有工具系统的注册逻辑
        tool_id = await self.tool_system.register_tool(tool_definition)
        return tool_id


class InteractionLayerAdapter(InteractionLayerProtocol):
    """交互层适配器 - 适配现有API和UI"""
    
    def __init__(self, api_endpoint: str = "http://localhost:8000"):
        self.api_endpoint = api_endpoint
        # 这里可以集成FastAPI或Streamlit
        logger.info(f"交互层适配器初始化，API端点: {api_endpoint}")
    
    async def handle_user_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入"""
        # 模拟处理用户输入，实际应调用现有API
        processed_input = {
            **input_data,
            "processed_timestamp": asyncio.get_event_loop().time(),
            "input_type": input_data.get("type", "text"),
            "language": input_data.get("language", "zh-CN")
        }
        
        # 简单的输入验证
        if "content" not in input_data:
            processed_input["validation_error"] = "缺少content字段"
        
        logger.info(f"交互层处理用户输入: {input_data.get('request_id', 'unknown')}")
        
        return {
            "processed_input": processed_input,
            "validation_passed": "validation_error" not in processed_input
        }
    
    async def deliver_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """交付响应给用户"""
        # 模拟交付响应，实际应调用现有UI或API
        delivery_status = "success"
        delivery_message = "响应已交付"
        
        # 检查响应格式
        if "answer" not in response and "error" not in response:
            delivery_status = "warning"
            delivery_message = "响应缺少answer或error字段"
        
        logger.info(f"交互层交付响应: {response.get('request_id', 'unknown')}")
        
        return {
            "status": delivery_status,
            "message": delivery_message,
            "delivery_timestamp": asyncio.get_event_loop().time(),
            "response_format": "json"
        }


def create_default_four_layer_setup() -> Dict[str, Any]:
    """创建默认的四层架构设置"""
    from .four_layer_manager import get_four_layer_manager, LayerComponent
    
    manager = get_four_layer_manager()
    
    # 创建网关层组件
    gateway = RANGENGateway()
    gateway_adapter = GatewayLayerAdapter(gateway)
    manager.set_layer_implementation("gateway", gateway_adapter)
    
    # 注册网关组件
    gateway_component = LayerComponent(
        component_id="rangengateway_001",
        component_type="gateway",
        capabilities=["message_routing", "safety_check", "agent_assembly"],
        endpoint="internal://gateway",
        metadata={"version": "1.0", "type": "RANGENGateway"}
    )
    manager.register_component(gateway_component)
    
    # 创建Agent层组件
    agent_adapter = AgentLayerAdapter()
    manager.set_layer_implementation("agent", agent_adapter)
    
    # 注册Agent组件
    for agent_id in agent_adapter.agents.keys():
        agent_component = LayerComponent(
            component_id=agent_id,
            component_type="agent",
            capabilities=agent_adapter.agents[agent_id].config.capabilities if (hasattr(agent_adapter.agents[agent_id], 'config') and hasattr(agent_adapter.agents[agent_id].config, 'capabilities')) else [],
            endpoint=f"internal://agent/{agent_id}",
            metadata={"role": agent_adapter.agents[agent_id].role_name}
        )
        manager.register_component(agent_component)
    
    # 注册企业家组件
    if agent_adapter.entrepreneur:
        entrepreneur_component = LayerComponent(
            component_id=agent_adapter.entrepreneur.agent_id,
            component_type="agent",
            capabilities=["team_coordination", "business_decision", "resource_allocation"],
            endpoint="internal://agent/entrepreneur",
            metadata={"role": "Entrepreneur Coordinator"}
        )
        manager.register_component(entrepreneur_component)
    
    # 创建工具层组件
    tool_system = HierarchicalToolSystem()
    tool_adapter = ToolLayerAdapter(tool_system)
    manager.set_layer_implementation("tool", tool_adapter)
    
    # 注册工具组件
    tool_component = LayerComponent(
        component_id="hierarchical_tool_system_001",
        component_type="tool",
        capabilities=["tool_execution", "tool_discovery", "tool_registration"],
        endpoint="internal://tool-system",
        metadata={"type": "HierarchicalToolSystem"}
    )
    manager.register_component(tool_component)
    
    # 创建交互层组件
    interaction_adapter = InteractionLayerAdapter()
    manager.set_layer_implementation("interaction", interaction_adapter)
    
    # 注册交互组件
    interaction_component = LayerComponent(
        component_id="interaction_adapter_001",
        component_type="interaction",
        capabilities=["user_input_processing", "response_delivery"],
        endpoint="http://localhost:8000",
        metadata={"type": "API/UI Adapter"}
    )
    manager.register_component(interaction_component)
    
    logger.info("默认四层架构设置完成")
    
    return {
        "manager": manager,
        "gateway": gateway,
        "agent_adapter": agent_adapter,
        "tool_adapter": tool_adapter,
        "interaction_adapter": interaction_adapter
    }