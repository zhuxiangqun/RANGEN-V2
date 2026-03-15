#!/usr/bin/env python3
"""
独立MCP服务器 - 不依赖RANGEN内部工具系统

直接实例化工具，不通过ToolRegistry
"""

import sys
import os

# 最先执行 - 抑制所有输出
import io
sys.stdout = io.StringIO()
sys.stderr = io.StringIO()

import asyncio
import json
import ast
import operator
import random
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent


# ===== 工具实现 =====

def safe_evaluate(expression: str) -> float:
    import re
    if not re.match(r'^[\d+\-*/().\s]+$', expression):
        raise ValueError("不安全表达式")
    node = ast.parse(expression, mode='eval')
    
    operators = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
                 ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}
    
    def eval_node(n):
        if isinstance(n, ast.Constant):
            return n.value
        elif isinstance(n, ast.BinOp):
            return operators[type(n.op)](eval_node(n.left), eval_node(n.right))
        elif isinstance(n, ast.UnaryOp):
            return operators[type(n.op)](eval_node(n.operand))
        return float(eval_node(n.body))
    
    return float(eval_node(node.body))


# ===== MCP服务器 =====

app = Server("standalone-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculator",
            description="数学计算器，支持加减乘除幂运算",
            inputSchema={
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "表达式如 2+3*4"}},
                "required": ["expression"]
            }
        ),
        Tool(
            name="echo",
            description="回显消息",
            inputSchema={
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": ["message"]
            }
        ),
        Tool(
            name="get_time",
            description="获取当前时间",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="random_number",
            description="生成随机数",
            inputSchema={
                "type": "object",
                "properties": {
                    "min": {"type": "number", "default": 0},
                    "max": {"type": "number", "default": 100}
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    try:
        if name == "calculator":
            result = safe_evaluate(arguments.get("expression", ""))
            return [TextContent(type="text", text=json.dumps({"success": True, "result": result}))]
        
        elif name == "echo":
            return [TextContent(type="text", text=json.dumps({"success": True, "echoed": arguments.get("message", "")}))]
        
        elif name == "get_time":
            now = datetime.now()
            return [TextContent(type="text", text=json.dumps({"success": True, "datetime": now.isoformat()}))]
        
        elif name == "random_number":
            min_val = arguments.get("min", 0)
            max_val = arguments.get("max", 100)
            return [TextContent(type="text", text=json.dumps({
                "success": True, "number": random.uniform(min_val, max_val)
            }))]
        
        else:
            return [TextContent(type="text", text=json.dumps({"success": False, "error": f"未知工具: {name}"}))]
    
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]


async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            initialization_options=app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
