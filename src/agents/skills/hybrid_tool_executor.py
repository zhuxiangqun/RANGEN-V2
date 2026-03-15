#!/usr/bin/env python3
"""
混合工具执行器 - 统一MCP调用架构

设计原则：
- 所有工具（内部+外部）都通过MCP协议调用
- 内部工具通过"内部MCP服务器"调用
- 外部工具通过外部MCP服务器调用
- 对上层提供统一的MCP接口

架构图：
┌─────────────────────────────────────────────────────────────┐
│                   HybridToolExecutor                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   user_input → decide → MCP protocol → tool execution       │
│                           │                                  │
│           ┌───────────────┴───────────────┐                 │
│           ▼                               ▼                 │
│   ┌───────────────────┐     ┌───────────────────┐           │
│   │ 内部MCP服务器      │     │ 外部MCP服务器      │           │
│   │ (localhost)       │     │ (远程)             │           │
│   ├───────────────────┤     ├───────────────────┤           │
│   │ - calculator      │     │ - GitHub          │           │
│   │ - search         │     │ - Slack           │           │
│   │ - rag            │     │ - Custom          │           │
│   │ - ...            │     │ - ...             │           │
│   └───────────────────┘     └───────────────────┘           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ToolSource(Enum):
    """工具来源"""
    INTERNAL = "internal"   # 内部工具（通过内部MCP服务器）
    MCP = "mcp"            # MCP 外部工具
    UNKNOWN = "unknown"


@dataclass
class ToolCallResult:
    """工具调用结果"""
    success: bool
    result: Any = None
    error: Optional[str] = None
    source: ToolSource = ToolSource.INTERNAL
    tool_name: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridToolExecutor:
    """
    混合工具执行器 - 统一MCP调用
    
    特点：
    - 所有工具都通过MCP协议调用
    - 内部工具通过本地MCP服务器
    - 外部工具通过远程MCP服务器
    - 统一的调用接口
    
    支持两种内部工具调用模式：
    - direct: 直接调用工具实例（默认，保持向后兼容）
    - mcp: 通过InProcessMCPExecutor调用（通过MCP协议层）
    """
    
    def __init__(self, internal_mode: str = "direct"):
        """
        初始化混合工具执行器
        
        Args:
            internal_mode: 内部工具调用模式
                - "direct": 直接调用工具实例（默认，向后兼容）
                - "mcp": 通过InProcessMCPExecutor调用（MCP协议层）
        """
        self._mcp_registry = None
        self._internal_mcp_tools = None
        self._internal_mode = internal_mode
        self._mcp_executor = None
    
    def _get_mcp_executor(self):
        """获取InProcessMCPExecutor实例"""
        if self._mcp_executor is None:
            try:
                from src.agents.tools.in_process_mcp import get_in_process_mcp_executor
                self._mcp_executor = get_in_process_mcp_executor()
            except Exception as e:
                logger.warning(f"InProcessMCPExecutor not available: {e}")
        return self._mcp_executor
    
    # ==================== MCP 注册表 ====================
    
    def _get_mcp_registry(self):
        """获取MCP注册表"""
        if self._mcp_registry is None:
            try:
                from src.gateway.mcp import get_mcp_registry
                self._mcp_registry = get_mcp_registry()
            except Exception as e:
                logger.warning(f"MCP registry not available: {e}")
        return self._mcp_registry
    
    # ==================== 内部工具（通过MCP调用） ====================
    
    def _get_internal_mcp_tools(self) -> Dict[str, Dict]:
        """获取内部工具的MCP格式"""
        if self._internal_mcp_tools is None:
            try:
                from src.agents.tools.tool_registry import get_tool_registry
                registry = get_tool_registry()
                tools = registry.get_all_tools()
                
                self._internal_mcp_tools = {}
                for tool in tools:
                    tool_name = tool.config.name if hasattr(tool, 'config') else getattr(tool, 'tool_name', 'unknown')
                    tool_desc = tool.config.description if hasattr(tool, 'config') else getattr(tool, 'description', '')
                    
                    # 获取参数schema
                    params_schema = {}
                    try:
                        if hasattr(tool, 'get_parameters_schema'):
                            params_schema = tool.get_parameters_schema() or {}
                    except:
                        pass
                    
                    self._internal_mcp_tools[tool_name] = {
                        "name": tool_name,
                        "description": tool_desc,
                        "inputSchema": params_schema,
                        "instance": tool  # 保存实例引用
                    }
                    
            except Exception as e:
                logger.error(f"Failed to load internal tools: {e}")
                self._internal_mcp_tools = {}
        
        return self._internal_mcp_tools
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tool_source: Optional[ToolSource] = None
    ) -> ToolCallResult:
        """
        统一执行接口 - 通过MCP协议调用所有工具
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            tool_source: 指定工具来源（可选，自动检测）
        
        Returns:
            ToolCallResult: 执行结果
        """
        import time
        start_time = time.time()
        
        # 1. 确定工具来源
        if tool_source is None:
            tool_source = await self._detect_tool_source(tool_name)
        
        # 2. 通过MCP协议调用
        try:
            if tool_source == ToolSource.INTERNAL:
                result = await self._execute_via_mcp(tool_name, parameters, is_internal=True)
            elif tool_source == ToolSource.MCP:
                result = await self._execute_via_mcp(tool_name, parameters, is_internal=False)
            else:
                # 未知来源，尝试内部
                result = await self._execute_via_mcp(tool_name, parameters, is_internal=True)
            
            return ToolCallResult(
                success=result.get("success", True),
                result=result.get("data") or result.get("result"),
                source=tool_source,
                tool_name=tool_name,
                execution_time=time.time() - start_time,
                metadata=result
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolCallResult(
                success=False,
                error=str(e),
                source=tool_source,
                tool_name=tool_name,
                execution_time=time.time() - start_time
            )
    
    async def _detect_tool_source(self, tool_name: str) -> ToolSource:
        """检测工具来源"""
        # 检查是否是外部MCP工具
        mcp_reg = self._get_mcp_registry()
        if mcp_reg:
            for conn_id, conn in mcp_reg.connections.items():
                for tool in conn.tools:
                    if tool.name == tool_name:
                        return ToolSource.MCP
        
        # 默认认为是内部工具
        return ToolSource.INTERNAL
    
    async def _execute_via_mcp(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        is_internal: bool = True
    ) -> Dict[str, Any]:
        """通过MCP协议执行工具"""
        
        if is_internal:
            # 根据internal_mode决定调用方式
            if self._internal_mode == "mcp" and self._get_mcp_executor():
                # 使用InProcessMCPExecutor
                mcp_exec = self._get_mcp_executor()
                return await mcp_exec.execute(tool_name, parameters, "internal")
            else:
                # 直接调用工具实例（默认，向后兼容）
                tools = self._get_internal_mcp_tools()
                
                if tool_name not in tools:
                    raise ValueError(f"Internal tool not found: {tool_name}")
                
                tool_instance = tools[tool_name]["instance"]
                
                # 调用工具
                try:
                    if hasattr(tool_instance, 'acall'):
                        result = await tool_instance.acall(**parameters)
                    elif hasattr(tool_instance, 'call'):
                        result = await tool_instance.call(**parameters)
                    else:
                        result = tool_instance.call(**parameters)
                        if asyncio.iscoroutine(result):
                            result = await result
                    
                    # 转换为MCP格式
                    if hasattr(result, 'success'):
                        return {
                            "success": result.success,
                            "data": result.data if hasattr(result, 'data') else str(result),
                            "error": getattr(result, 'error', None)
                        }
                    else:
                        return {
                            "success": True,
                            "data": str(result)
                        }
                        
                except TypeError as e:
                    # 尝试无参数调用
                    if hasattr(tool_instance, 'acall'):
                        result = await tool_instance.acall()
                    else:
                        result = tool_instance.call()
                        if asyncio.iscoroutine(result):
                            result = await result
                    
                    return {
                        "success": True,
                        "data": str(result)
                    }
        else:
            # 外部MCP工具：通过MCP注册表调用
            mcp_reg = self._get_mcp_registry()
            if not mcp_reg:
                raise RuntimeError("MCP registry not available")
            
            # 查找并调用
            for conn_id, conn in mcp_reg.connections.items():
                for tool in conn.tools:
                    if tool.name == tool_name:
                        result = await mcp_reg.call_tool(conn_id, tool_name, parameters)
                        return {
                            "success": True,
                            "data": result
                        }
            
            raise ValueError(f"MCP tool not found: {tool_name}")
    
    # ==================== MCP 服务器管理 ====================
    
    async def add_mcp_server(
        self,
        name: str,
        server_url: str,
        transport: str = "stdio"
    ) -> str:
        """添加外部MCP服务器"""
        mcp_reg = self._get_mcp_registry()
        if not mcp_reg:
            raise RuntimeError("MCP registry not available")
        return await mcp_reg.add_server(name, server_url, transport)
    
    async def remove_mcp_server(self, connection_id: str):
        """移除MCP服务器"""
        mcp_reg = self._get_mcp_registry()
        if mcp_reg:
            await mcp_reg.remove_server(connection_id)
    
    def list_mcp_servers(self) -> List[Dict]:
        """列出MCP服务器"""
        mcp_reg = self._get_mcp_registry()
        if mcp_reg:
            return mcp_reg.list_connections()
        return []
    
    def list_all_tools(self) -> Dict[str, List]:
        """列出所有可用工具（内部+外部）"""
        result = {
            "internal": [],
            "mcp": []
        }
        
        # 内部工具
        internal_tools = self._get_internal_mcp_tools()
        for name, tool_info in internal_tools.items():
            result["internal"].append({
                "name": name,
                "description": tool_info["description"]
            })
        
        # 外部MCP工具
        mcp_reg = self._get_mcp_registry()
        if mcp_reg:
            for conn_id, conn in mcp_reg.connections.items():
                for tool in conn.tools:
                    result["mcp"].append({
                        "name": tool.name,
                        "description": tool.description,
                        "server": conn.name
                    })
        
        return result


# ==================== 便捷函数 ====================

_hybrid_executor: Optional[HybridToolExecutor] = None


def get_hybrid_executor() -> HybridToolExecutor:
    """获取混合工具执行器单例"""
    global _hybrid_executor
    if _hybrid_executor is None:
        _hybrid_executor = HybridToolExecutor()
    return _hybrid_executor
