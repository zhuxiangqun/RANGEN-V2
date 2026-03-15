#!/usr/bin/env python3
"""
进程内 MCP 服务器 - 通过 MCP 协议调用内部工具

设计目标：
- 在同一个 Python 进程内通过 MCP 协议调用工具
- 统一内部工具和外部工具的调用接口
- 为未来暴露给外部 MCP 客户端做准备

使用方式：
    from src.agents.tools.in_process_mcp import InProcessMCPExecutor
    
    executor = InProcessMCPExecutor()
    result = await executor.execute("calculator", {"expression": "25 * 4 + 10"})
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class MCPRequest:
    """MCP 请求"""
    jsonrpc: str = "2.0"
    id: str = ""
    method: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPResponse:
    """MCP 响应"""
    jsonrpc: str = "2.0"
    id: str = ""
    result: Any = None
    error: Optional[Dict[str, Any]] = None


class InProcessMCPServer:
    """
    进程内 MCP 服务器
    
    在同一个 Python 进程内实现 MCP 协议，
    可以通过 MCP 协议调用所有内部工具。
    """
    
    def __init__(self):
        self._tools = None
        self._request_id = 0
    
    def _get_tools(self) -> List[Any]:
        """获取工具列表"""
        if self._tools is None:
            from src.agents.tools.tool_registry import get_tool_registry
            registry = get_tool_registry()
            self._tools = registry.get_all_tools()
        return self._tools
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用工具（符合 MCP 协议）"""
        tools = self._get_tools()
        mcp_tools = []
        
        for tool in tools:
            tool_name = tool.config.name if hasattr(tool, 'config') else getattr(tool, 'tool_name', 'unknown')
            tool_desc = tool.config.description if hasattr(tool, 'config') else getattr(tool, 'description', '')
            
            # 获取参数 schema
            params_schema = {}
            try:
                if hasattr(tool, 'get_parameters_schema'):
                    params_schema = tool.get_parameters_schema() or {}
            except Exception:
                pass
            
            mcp_tools.append({
                "name": tool_name,
                "description": tool_desc or f"{tool_name} tool",
                "inputSchema": params_schema
            })
        
        return mcp_tools
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用工具（符合 MCP 协议）
        
        Args:
            name: 工具名称
            arguments: 工具参数
            
        Returns:
            MCP 格式的响应
        """
        tools = self._get_tools()
        tool = None
        
        # 查找工具
        for t in tools:
            tool_name = t.config.name if hasattr(t, 'config') else getattr(t, 'tool_name', None)
            if tool_name == name:
                tool = t
                break
        
        if tool is None:
            return {
                "success": False,
                "error": f"Tool not found: {name}"
            }
        
        try:
            # 调用工具
            if hasattr(tool, 'acall'):
                result = await tool.acall(**arguments)
            elif hasattr(tool, 'call'):
                result = await tool.call(**arguments)
            else:
                result = tool.call(**arguments)
                if asyncio.iscoroutine(result):
                    result = await result
            
            # 处理结果
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
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_request(self, method: str, params: Dict[str, Any] = None) -> MCPRequest:
        """创建 MCP 请求"""
        self._request_id += 1
        return MCPRequest(
            id=str(self._request_id),
            method=method,
            params=params or {}
        )
    
    async def _handle_request(self, request: MCPRequest) -> MCPResponse:
        """处理 MCP 请求"""
        try:
            if request.method == "tools/list":
                tools = self.list_tools()
                return MCPResponse(
                    id=request.id,
                    result={"tools": tools}
                )
            elif request.method == "tools/call":
                tool_name = request.params.get("name")
                arguments = request.params.get("arguments", {})
                result = await self.call_tool(tool_name, arguments)
                return MCPResponse(
                    id=request.id,
                    result=result
                )
            else:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {request.method}"
                    }
                )
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": str(e)
                }
            )


class InProcessMCPExecutor:
    """
    进程内 MCP 执行器
    
    通过 MCP 协议调用内部工具的统一接口。
    与 HybridToolExecutor 的区别：
    - HybridToolExecutor: 直接调用工具实例
    - InProcessMCPExecutor: 通过 MCP 协议层调用
    
    这样的好处：
    1. 统一的协议接口
    2. 更容易扩展和维护
    3. 可以轻松暴露给外部系统
    """
    
    def __init__(self):
        self._server = None
    
    def _get_server(self) -> InProcessMCPServer:
        """获取 MCP 服务器实例"""
        if self._server is None:
            self._server = InProcessMCPServer()
        return self._server
    
    async def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        tool_source: str = "internal"
    ) -> Dict[str, Any]:
        """
        执行工具（通过 MCP 协议）
        
        Args:
            tool_name: 工具名称
            parameters: 工具参数
            tool_source: 工具来源（internal/mcp）
            
        Returns:
            执行结果
        """
        if tool_source == "internal":
            server = self._get_server()
            return await server.call_tool(tool_name, parameters)
        else:
            # 外部 MCP 工具 - 暂时返回错误
            return {
                "success": False,
                "error": "External MCP not implemented yet. Use HybridToolExecutor for external tools."
            }
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用工具"""
        server = self._get_server()
        return server.list_tools()


# 全局单例
_mcp_executor: Optional[InProcessMCPExecutor] = None


def get_in_process_mcp_executor() -> InProcessMCPExecutor:
    """获取进程内 MCP 执行器单例"""
    global _mcp_executor
    if _mcp_executor is None:
        _mcp_executor = InProcessMCPExecutor()
    return _mcp_executor


# 便捷函数
async def execute_via_mcp(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """通过 MCP 协议执行工具"""
    executor = get_in_process_mcp_executor()
    return await executor.execute(tool_name, parameters)


if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("=" * 60)
        print("测试: 进程内 MCP 执行器")
        print("=" * 60)
        
        executor = get_in_process_mcp_executor()
        
        # 列出工具
        print("\n1. 列出工具:")
        tools = executor.list_tools()
        print(f"   总共 {len(tools)} 个工具")
        for t in tools[:3]:
            print(f"   - {t['name']}: {t['description'][:50]}...")
        
        # 调用工具
        print("\n2. 调用 calculator 工具:")
        result = await executor.execute(
            "calculator",
            {"expression": "25 * 4 + 10"}
        )
        print(f"   结果: {result}")
        
        print("\n" + "=" * 60)
        print("✅ 测试完成!")
        print("=" * 60)
    
    asyncio.run(test())
