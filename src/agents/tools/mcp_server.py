#!/usr/bin/env python3
"""
MCP服务器 - 将RANGEN内部工具暴露为MCP服务
"""

# ===== 必须最先执行 =====
import sys
import os
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')

# 延迟导入
import argparse
import asyncio
import json
import logging
from typing import Any, Optional

# 配置日志
logging.basicConfig(level=logging.CRITICAL)
null_handler = logging.NullHandler()
logging.getLogger().addHandler(null_handler)

from mcp.server import Server
from mcp.types import Tool, TextContent


def get_registry():
    """懒加载工具注册表"""
    from src.agents.tools.tool_registry import get_tool_registry
    return get_tool_registry()


def create_mcp_server() -> Server:
    """创建MCP服务器"""
    app = Server("rangen-tools")
    registry = None
    
    @app.list_tools()
    async def list_tools() -> list[Tool]:
        nonlocal registry
        if registry is None:
            registry = get_registry()
        
        tools = registry.get_all_tools()
        
        mcp_tools = []
        for tool in tools:
            tool_name = tool.config.name if hasattr(tool, 'config') else getattr(tool, 'tool_name', 'unknown')
            tool_desc = tool.config.description if hasattr(tool, 'config') else getattr(tool, 'description', '')
            
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
        nonlocal registry
        try:
            if registry is None:
                registry = get_registry()
            
            tool = registry.get_tool(name)
            
            if tool is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({"success": False, "error": f"Tool not found: {name}"}, ensure_ascii=False)
                )]
            
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
                if hasattr(tool, 'acall'):
                    result = await tool.acall()
                elif hasattr(tool, 'call'):
                    result = await tool.call()
                else:
                    result = tool.call()
                    if asyncio.iscoroutine(result):
                        result = await result
            
            if hasattr(result, 'success'):
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": result.success,
                        "data": result.data if hasattr(result, 'data') else str(result),
                        "error": result.error if hasattr(result, 'error') else None
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
    from mcp.server.stdio import stdio_server
    app = create_mcp_server()
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            initialization_options=app.create_initialization_options()
        )


async def run_http(host: str = "0.0.0.0", port: int = 8080):
    from mcp.server.streamable_http import StreamableHTTPServer
    app = create_mcp_server()
    server = StreamableHTTPServer(app=app, host=host, port=port)
    await server.run()


async def main():
    parser = argparse.ArgumentParser(description="RANGEN MCP Server")
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
