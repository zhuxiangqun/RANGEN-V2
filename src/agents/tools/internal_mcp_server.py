#!/usr/bin/env python3
"""
内部MCP服务器 - 将RANGEN内部工具暴露为MCP服务

设计目标：
- 将所有内部工具通过MCP协议暴露
- 外部MCP客户端可直接调用
- 统一工具调用接口

使用方式：
    # STDIO模式（用于Claude Desktop等）
    python -m src.agents.tools.internal_mcp_server

    # HTTP模式
    python -m src.agents.tools.internal_mcp_server --http --port 8080
"""

# ===== 必须最先执行 =====
import sys
import os
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

import argparse
import asyncio
import json
import logging
from typing import Any, Optional

# 配置日志
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().addHandler(logging.NullHandler())

from mcp.server import Server
from mcp.types import Tool, TextContent


def create_internal_mcp_server() -> Server:
    """创建内部MCP服务器"""
    app = Server("rangen-internal-tools")
    tools_cache = None
    
    def get_tools():
        """懒加载工具"""
        nonlocal tools_cache
        if tools_cache is None:
            from src.agents.tools.tool_registry import get_tool_registry
            registry = get_tool_registry()
            tools_cache = registry.get_all_tools()
        return tools_cache
    
    @app.list_tools()
    async def list_tools() -> list[Tool]:
        """列出所有可用工具"""
        tools = get_tools()
        
        mcp_tools = []
        for tool in tools:
            # 获取工具元数据
            tool_name = tool.config.name if hasattr(tool, 'config') else getattr(tool, 'tool_name', 'unknown')
            tool_desc = tool.config.description if hasattr(tool, 'config') else getattr(tool, 'description', '')
            
            # 获取参数schema
            params_schema = {}
            try:
                if hasattr(tool, 'get_parameters_schema'):
                    params_schema = tool.get_parameters_schema() or {}
            except Exception:
                pass
            
            mcp_tools.append(Tool(
                name=tool_name,
                description=tool_desc or f"{tool_name} tool",
                inputSchema=params_schema
            ))
        
        return mcp_tools
    
    @app.call_tool()
    async def call_tool(name: str, arguments: Any) -> list[TextContent]:
        """调用工具"""
        try:
            tools = get_tools()
            tool = None
            
            # 查找工具
            for t in tools:
                tool_name = t.config.name if hasattr(t, 'config') else getattr(t, 'tool_name', None)
                if tool_name == name:
                    tool = t
                    break
            
            if tool is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({"success": False, "error": f"Tool not found: {name}"}, ensure_ascii=False)
                )]
            
            # 调用工具
            try:
                if hasattr(tool, 'acall'):
                    result = await tool.acall(**arguments)
                elif hasattr(tool, 'call'):
                    result = await tool.call(**arguments)
                else:
                    result = tool.call(**arguments)
                    if asyncio.iscoroutine(result):
                        result = await result
            except TypeError:
                # 尝试无参数调用
                if hasattr(tool, 'acall'):
                    result = await tool.acall()
                else:
                    result = tool.call()
                    if asyncio.iscoroutine(result):
                        result = await result
            
            # 处理结果
            if hasattr(result, 'success'):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": result.success,
                        "data": result.data if hasattr(result, 'data') else str(result),
                        "error": getattr(result, 'error', None)
                    }, ensure_ascii=False, default=str)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"success": True, "data": str(result)}, ensure_ascii=False)
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)
            )]
    
    return app


async def run_stdio():
    """运行STDIO服务器"""
    from mcp.server.stdio import stdio_server
    app = create_internal_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            initialization_options=app.create_initialization_options()
        )


async def run_http(host: str = "0.0.0.0", port: int = 8080):
    """运行HTTP服务器"""
    from mcp.server.streamable_http import StreamableHTTPServer
    app = create_internal_mcp_server()
    server = StreamableHTTPServer(app=app, host=host, port=port)
    await server.run()


async def main():
    parser = argparse.ArgumentParser(description="RANGEN Internal MCP Server")
    parser.add_argument("--http", action="store_true", help="Use HTTP transport")
    parser.add_argument("--port", type=int, default=8080, help="HTTP port")
    parser.add_argument("--host", default="0.0.0.0", help="HTTP host")
    args = parser.parse_args()
    
    if args.http:
        await run_http(args.host, args.port)
    else:
        await run_stdio()


if __name__ == "__main__":
    asyncio.run(main())
