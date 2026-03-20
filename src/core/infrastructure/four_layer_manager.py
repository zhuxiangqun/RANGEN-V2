#!/usr/bin/env python3
"""
四层架构管理器 - 基于OpenClaw四层架构分析

实现交互层、网关层、Agent层、工具层的统一管理和协调。
"""

import logging
from typing import Dict, List, Any, Optional, Protocol, runtime_checkable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class LayerComponent:
    """层组件描述"""
    component_id: str
    component_type: str  # "interaction", "gateway", "agent", "tool"
    capabilities: List[str]
    endpoint: Optional[str] = None  # API端点或通信地址
    metadata: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class InteractionLayerProtocol(Protocol):
    """交互层协议"""
    async def handle_user_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户输入"""
        ...

    async def deliver_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """交付响应给用户"""
        ...


@runtime_checkable
class GatewayLayerProtocol(Protocol):
    """网关层协议"""
    async def route_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """路由消息到适当的目标层"""
        ...

    async def perform_safety_check(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """执行安全检查"""
        ...

    async def assemble_agents(self, task: Dict[str, Any]) -> List[str]:
        """组装Agent团队"""
        ...


@runtime_checkable
class AgentLayerProtocol(Protocol):
    """Agent层协议"""
    async def execute_task(self, agent_id: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行任务"""
        ...

    async def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """获取Agent能力"""
        ...

    async def form_team(self, agent_ids: List[str], team_purpose: str) -> str:
        """组建团队"""
        ...


@runtime_checkable
class ToolLayerProtocol(Protocol):
    """工具层协议"""
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        ...

    async def discover_tools(self, capability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """发现可用工具"""
        ...

    async def register_tool(self, tool_definition: Dict[str, Any]) -> str:
        """注册新工具"""
        ...


class FourLayerManager:
    """四层架构管理器"""
    
    def __init__(self):
        self.interaction_components: Dict[str, LayerComponent] = {}
        self.gateway_components: Dict[str, LayerComponent] = {}
        self.agent_components: Dict[str, LayerComponent] = {}
        self.tool_components: Dict[str, LayerComponent] = {}
        
        # 协议实例
        self.interaction_layer: Optional[InteractionLayerProtocol] = None
        self.gateway_layer: Optional[GatewayLayerProtocol] = None
        self.agent_layer: Optional[AgentLayerProtocol] = None
        self.tool_layer: Optional[ToolLayerProtocol] = None
        
        logger.info("四层架构管理器初始化完成")
    
    def register_component(self, component: LayerComponent) -> bool:
        """注册组件到相应层"""
        if component.component_type == "interaction":
            self.interaction_components[component.component_id] = component
            logger.info(f"注册交互层组件: {component.component_id}")
            return True
        elif component.component_type == "gateway":
            self.gateway_components[component.component_id] = component
            logger.info(f"注册网关层组件: {component.component_id}")
            return True
        elif component.component_type == "agent":
            self.agent_components[component.component_id] = component
            logger.info(f"注册Agent层组件: {component.component_id}")
            return True
        elif component.component_type == "tool":
            self.tool_components[component.component_id] = component
            logger.info(f"注册工具层组件: {component.component_id}")
            return True
        else:
            logger.error(f"未知组件类型: {component.component_type}")
            return False
    
    def set_layer_implementation(self, layer_type: str, implementation: Any) -> bool:
        """设置层协议实现"""
        if layer_type == "interaction":
            if isinstance(implementation, InteractionLayerProtocol):
                self.interaction_layer = implementation
                logger.info("设置交互层实现")
                return True
        elif layer_type == "gateway":
            if isinstance(implementation, GatewayLayerProtocol):
                self.gateway_layer = implementation
                logger.info("设置网关层实现")
                return True
        elif layer_type == "agent":
            if isinstance(implementation, AgentLayerProtocol):
                self.agent_layer = implementation
                logger.info("设置Agent层实现")
                return True
        elif layer_type == "tool":
            if isinstance(implementation, ToolLayerProtocol):
                self.tool_layer = implementation
                logger.info("设置工具层实现")
                return True
        else:
            logger.error(f"未知层类型: {layer_type}")
            return False
        
        logger.warning(f"实现不符合{layer_type}层协议")
        return False
    
    async def process_request(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """处理用户请求（完整四层流程）"""
        logger.info(f"开始处理用户请求: {user_input.get('request_id', 'unknown')}")
        
        # 1. 交互层：接收用户输入
        if self.interaction_layer:
            try:
                interaction_result = await self.interaction_layer.handle_user_input(user_input)
                user_input.update(interaction_result.get("processed_input", {}))
                logger.debug("交互层处理完成")
            except Exception as e:
                logger.error(f"交互层处理失败: {e}")
        else:
            logger.warning("未设置交互层实现，跳过交互层处理")
        
        # 2. 网关层：路由、安全检查、Agent组装
        if self.gateway_layer:
            try:
                # 安全检查
                safety_result = await self.gateway_layer.perform_safety_check(user_input)
                if not safety_result.get("safe", True):
                    return {
                        "success": False,
                        "error": "安全检查未通过",
                        "safety_reasons": safety_result.get("reasons", []),
                        "layer": "gateway"
                    }
                
                # Agent组装
                agent_team = await self.gateway_layer.assemble_agents(user_input)
                user_input["agent_team"] = agent_team
                logger.debug(f"网关层组装Agent团队: {agent_team}")
                
                # 路由决策
                routing_result = await self.gateway_layer.route_message(user_input)
                user_input.update(routing_result.get("routing_info", {}))
                logger.debug("网关层路由完成")
            except Exception as e:
                logger.error(f"网关层处理失败: {e}")
                return {
                    "success": False,
                    "error": f"网关层处理失败: {str(e)}",
                    "layer": "gateway"
                }
        else:
            logger.warning("未设置网关层实现，跳过网关层处理")
        
        # 3. Agent层：任务执行
        if self.agent_layer and "agent_team" in user_input:
            try:
                task_results = []
                for agent_id in user_input["agent_team"]:
                    task_copy = user_input.copy()
                    task_copy["assigned_agent"] = agent_id
                    
                    agent_result = await self.agent_layer.execute_task(agent_id, task_copy)
                    task_results.append({
                        "agent_id": agent_id,
                        "result": agent_result
                    })
                
                user_input["task_results"] = task_results
                logger.debug(f"Agent层执行完成，{len(task_results)}个任务结果")
            except Exception as e:
                logger.error(f"Agent层处理失败: {e}")
                return {
                    "success": False,
                    "error": f"Agent层处理失败: {str(e)}",
                    "layer": "agent"
                }
        else:
            logger.warning("未设置Agent层实现或未分配Agent团队，跳过Agent层处理")
        
        # 4. 工具层：工具执行（如果需要）
        if self.tool_layer and user_input.get("requires_tools", False):
            try:
                tool_results = []
                for tool_request in user_input.get("tool_requests", []):
                    tool_id = tool_request.get("tool_id")
                    params = tool_request.get("params", {})
                    
                    tool_result = await self.tool_layer.execute_tool(tool_id, params)
                    tool_results.append({
                        "tool_id": tool_id,
                        "result": tool_result
                    })
                
                user_input["tool_results"] = tool_results
                logger.debug(f"工具层执行完成，{len(tool_results)}个工具结果")
            except Exception as e:
                logger.error(f"工具层处理失败: {e}")
                # 工具失败不一定导致整体失败，记录但继续
        
        # 5. 网关层：结果整合和返回
        if self.gateway_layer:
            try:
                final_result = await self.gateway_layer.route_message({
                    **user_input,
                    "direction": "response",
                    "source_layer": "agent"
                })
                logger.debug("网关层结果整合完成")
            except Exception as e:
                logger.error(f"网关层结果整合失败: {e}")
                final_result = user_input
        else:
            final_result = user_input
        
        # 6. 交互层：响应交付
        if self.interaction_layer:
            try:
                delivered_response = await self.interaction_layer.deliver_response(final_result)
                final_result["delivery_status"] = delivered_response.get("status", "success")
                logger.debug("交互层响应交付完成")
            except Exception as e:
                logger.error(f"交互层响应交付失败: {e}")
                final_result["delivery_status"] = "failed"
                final_result["delivery_error"] = str(e)
        
        final_result["success"] = True
        final_result["processing_layers"] = [
            "interaction" if self.interaction_layer else None,
            "gateway" if self.gateway_layer else None,
            "agent" if self.agent_layer else None,
            "tool" if self.tool_layer else None
        ]
        
        logger.info(f"请求处理完成: {user_input.get('request_id', 'unknown')}")
        return final_result
    
    def get_layer_status(self) -> Dict[str, Any]:
        """获取各层状态"""
        return {
            "interaction_layer": {
                "implemented": self.interaction_layer is not None,
                "component_count": len(self.interaction_components),
                "components": list(self.interaction_components.keys())
            },
            "gateway_layer": {
                "implemented": self.gateway_layer is not None,
                "component_count": len(self.gateway_components),
                "components": list(self.gateway_components.keys())
            },
            "agent_layer": {
                "implemented": self.agent_layer is not None,
                "component_count": len(self.agent_components),
                "components": list(self.agent_components.keys())
            },
            "tool_layer": {
                "implemented": self.tool_layer is not None,
                "component_count": len(self.tool_components),
                "components": list(self.tool_components.keys())
            }
        }
    
    def find_components_by_capability(self, capability: str) -> List[LayerComponent]:
        """根据能力查找组件"""
        all_components = []
        all_components.extend(self.interaction_components.values())
        all_components.extend(self.gateway_components.values())
        all_components.extend(self.agent_components.values())
        all_components.extend(self.tool_components.values())
        
        return [comp for comp in all_components if capability in comp.capabilities]
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health = {
            "overall": "healthy",
            "layers": {},
            "issues": []
        }
        
        # 检查各层实现是否存在
        if not self.interaction_layer:
            health["layers"]["interaction"] = "not_implemented"
            health["issues"].append("交互层未实现")
        else:
            health["layers"]["interaction"] = "implemented"
        
        if not self.gateway_layer:
            health["layers"]["gateway"] = "not_implemented"
            health["issues"].append("网关层未实现")
        else:
            health["layers"]["gateway"] = "implemented"
        
        if not self.agent_layer:
            health["layers"]["agent"] = "not_implemented"
            health["issues"].append("Agent层未实现")
        else:
            health["layers"]["agent"] = "implemented"
        
        if not self.tool_layer:
            health["layers"]["tool"] = "not_implemented"
            health["issues"].append("工具层未实现")
        else:
            health["layers"]["tool"] = "implemented"
        
        if health["issues"]:
            health["overall"] = "degraded"
        
        return health


# 全局管理器实例
_four_layer_manager_instance = None

def get_four_layer_manager() -> FourLayerManager:
    """获取四层架构管理器实例"""
    global _four_layer_manager_instance
    if _four_layer_manager_instance is None:
        _four_layer_manager_instance = FourLayerManager()
    return _four_layer_manager_instance