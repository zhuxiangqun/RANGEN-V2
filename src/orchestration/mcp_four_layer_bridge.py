#!/usr/bin/env python3
"""
MCP四层架构桥接器 - 将MCP工具集成到四层架构中
"""

import logging
from typing import Dict, List, Any, Optional, cast
import asyncio

from .four_layer_manager import LayerComponent, get_four_layer_manager
from ..utils.mcp_protocol import MCPMessageType, MCPPriority
from ..services.mcp_server_manager import MCPServerManager

logger = logging.getLogger(__name__)


class MCPToolBridge:
    """MCP工具桥接器 - 将MCP工具暴露给四层架构"""
    
    def __init__(self, mcp_server_manager: Optional[MCPServerManager] = None):
        self.mcp_server_manager = mcp_server_manager or MCPServerManager()
        self.mcp_tools: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化MCP工具桥接器"""
        if self._initialized:
            return True
        
        try:
            # 获取所有MCP服务器
            servers = self.mcp_server_manager.get_all_servers()
            logger.info(f"发现{len(servers)}个MCP服务器")
            
            # 从每个服务器发现工具
            for server in servers:
                try:
                    tools = await self.discover_mcp_tools(server["id"])
                    self.mcp_tools.update({tool["id"]: tool for tool in tools})
                    logger.info(f"从服务器{server['id']}发现{len(tools)}个工具")
                except Exception as e:
                    logger.error(f"从服务器{server['id']}发现工具失败: {e}")
            
            self._initialized = True
            logger.info(f"MCP工具桥接器初始化完成，共发现{len(self.mcp_tools)}个工具")
            return True
            
        except Exception as e:
            logger.error(f"MCP工具桥接器初始化失败: {e}")
            return False
    
    async def discover_mcp_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """发现MCP服务器上的工具"""
        try:
            # 通过MCP服务器管理器获取工具列表
            tools = await self.mcp_server_manager.discover_tools(server_id)
            
            formatted_tools = []
            for tool in tools:
                formatted_tool = {
                    "id": f"mcp_{server_id}_{tool.get('name', 'unknown')}",
                    "name": tool.get("name", "未知工具"),
                    "description": tool.get("description", ""),
                    "capabilities": tool.get("capabilities", []),
                    "category": "mcp",
                    "metadata": {
                        "server_id": server_id,
                        "mcp_protocol_version": tool.get("protocol_version", "1.0"),
                        "tool_definition": tool
                    }
                }
                formatted_tools.append(formatted_tool)
            
            return formatted_tools
            
        except Exception as e:
            logger.error(f"发现MCP服务器{server_id}的工具失败: {e}")
            return []
    
    async def execute_mcp_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行MCP工具"""
        try:
            # 解析工具ID获取服务器ID和工具名称
            parts = tool_id.split("_")
            if len(parts) < 3:
                raise ValueError(f"无效的MCP工具ID格式: {tool_id}")
            
            server_id = parts[1]
            tool_name = "_".join(parts[2:])
            
            # 通过MCP服务器管理器执行工具
            result = await self.mcp_server_manager.execute_tool(server_id, tool_name, params)
            
            return {
                "success": True,
                "output": result.get("output"),
                "error": result.get("error"),
                "execution_metrics": {
                    "server_id": server_id,
                    "tool_name": tool_name,
                    "execution_time": result.get("execution_time", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"执行MCP工具{tool_id}失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_metrics": {}
            }
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """获取所有MCP工具"""
        return list(self.mcp_tools.values())
    
    def get_tool_by_capability(self, capability: str) -> List[Dict[str, Any]]:
        """根据能力获取MCP工具"""
        return [
            tool for tool in self.mcp_tools.values()
            if capability in tool.get("capabilities", [])
        ]


async def integrate_mcp_with_four_layer() -> Dict[str, Any]:
    """将MCP集成到四层架构中"""
    manager = get_four_layer_manager()
    bridge = MCPToolBridge()
    
    # 初始化桥接器
    success = await bridge.initialize()
    if not success:
        return {
            "success": False,
            "error": "MCP工具桥接器初始化失败",
            "tools_registered": 0
        }
    
    # 注册MCP工具到四层管理器
    tools_registered = 0
    for tool in bridge.get_all_tools():
        component = LayerComponent(
            component_id=tool["id"],
            component_type="tool",
            capabilities=tool["capabilities"],
            endpoint=f"mcp://{tool['metadata']['server_id']}/{tool['name']}",
            metadata={
                **tool["metadata"],
                "source": "mcp",
                "bridge_version": "1.0"
            }
        )
        
        if manager.register_component(component):
            tools_registered += 1
            logger.debug(f"注册MCP工具组件: {tool['id']}")
        else:
            logger.warning(f"注册MCP工具组件失败: {tool['id']}")
    
    # 创建MCP工具层适配器（扩展现有工具层）
    class MCPEnhancedToolLayer:
        """MCP增强的工具层"""
        
        def __init__(self, bridge: MCPToolBridge, base_tool_layer):
            self.bridge = bridge
            self.base_tool_layer = base_tool_layer
        
        async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
            """执行工具（支持MCP工具和基础工具）"""
            # 检查是否是MCP工具
            if tool_id.startswith("mcp_"):
                return await self.bridge.execute_mcp_tool(tool_id, params)
            else:
                # 委托给基础工具层
                return await self.base_tool_layer.execute_tool(tool_id, params)
        
        async def discover_tools(self, capability_filter: Optional[str] = None) -> List[Dict[str, Any]]:
            """发现工具（合并MCP工具和基础工具）"""
            base_tools = await self.base_tool_layer.discover_tools(capability_filter)
            mcp_tools = self.bridge.get_tool_by_capability(capability_filter) if capability_filter else self.bridge.get_all_tools()
            
            # 合并工具列表
            combined_tools = base_tools + [
                {
                    "tool_id": tool["id"],
                    "name": tool["name"],
                    "description": tool["description"],
                    "capabilities": tool["capabilities"],
                    "category": "mcp",
                    "metadata": tool["metadata"]
                }
                for tool in mcp_tools
            ]
            
            return combined_tools
        
        async def register_tool(self, tool_definition: Dict[str, Any]) -> str:
            """注册新工具"""
            # 默认委托给基础工具层
            return await self.base_tool_layer.register_tool(tool_definition)
    
    # 获取当前工具层实现
    current_tool_layer = manager.tool_layer
    if current_tool_layer:
        # 创建增强工具层
        enhanced_tool_layer = MCPEnhancedToolLayer(bridge, current_tool_layer)
        # 更新工具层实现
        manager.set_layer_implementation("tool", enhanced_tool_layer)
        logger.info("MCP增强工具层已设置")
    else:
        logger.warning("当前未设置工具层实现，无法集成MCP增强")
    
    logger.info(f"MCP集成完成，注册了{tools_registered}个工具到四层架构")
    
    return {
        "success": True,
        "tools_registered": tools_registered,
        "total_mcp_tools": len(bridge.get_all_tools()),
        "layer_updated": current_tool_layer is not None
    }


def register_mcp_components() -> List[LayerComponent]:
    """注册MCP组件到四层架构"""
    manager = get_four_layer_manager()
    
    # 创建MCP服务器组件
    mcp_server_component = LayerComponent(
        component_id="mcp_server_manager_001",
        component_type="tool",
        capabilities=["mcp_tool_discovery", "mcp_tool_execution", "mcp_server_management"],
        endpoint="internal://mcp-server-manager",
        metadata={
            "type": "MCPServerManager",
            "version": "1.0",
            "protocol": "MCP"
        }
    )
    
    # 创建MCP客户端组件
    mcp_client_component = LayerComponent(
        component_id="mcp_client_001",
        component_type="tool",
        capabilities=["mcp_communication", "protocol_handling", "message_routing"],
        endpoint="internal://mcp-client",
        metadata={
            "type": "MCPClient",
            "version": "1.0",
            "protocol": "MCP"
        }
    )
    
    components = [mcp_server_component, mcp_client_component]
    
    for component in components:
        if manager.register_component(component):
            logger.info(f"注册MCP组件: {component.component_id}")
        else:
            logger.warning(f"注册MCP组件失败: {component.component_id}")
    
    return components


async def test_mcp_integration() -> Dict[str, Any]:
    """测试MCP集成"""
    try:
        # 集成MCP到四层架构
        integration_result = await integrate_mcp_with_four_layer()
        
        if not integration_result["success"]:
            return integration_result
        
        # 注册MCP组件
        components = register_mcp_components()
        
        # 获取四层管理器状态
        manager = get_four_layer_manager()
        layer_status = manager.get_layer_status()
        
        return {
            "success": True,
            "integration_result": integration_result,
            "components_registered": len(components),
            "layer_status": layer_status,
            "tool_layer_enhanced": integration_result["layer_updated"]
        }
        
    except Exception as e:
        logger.error(f"MCP集成测试失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "integration_result": None
        }