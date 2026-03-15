#!/usr/bin/env python3
"""
独立本地MCP服务器 - 不依赖RANGEN

功能：
1. calculator - 数学计算器
2. echo - 回显消息
3. get_time - 获取当前时间
4. random_number - 生成随机数
"""

import asyncio
import json
import random
import ast
import operator
import sys
import os
from datetime import datetime
from typing import Any

# 重定向stdout到/dev/null以抑制所有输出
sys.stdout = open(os.devnull, 'w')

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# 安全运算符
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_evaluate(expression: str) -> float:
    import re
    if not re.match(r'^[\d+\-*/().\s]+$', expression):
        raise ValueError(f"不安全的表达式: {expression}")
    node = ast.parse(expression, mode='eval')
    
    def _eval_node(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"不支持的常量类型: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](left, right)
            raise ValueError(f"不支持的运算符: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = _eval_node(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return SAFE_OPERATORS[op_type](operand)
            raise ValueError(f"不支持的一元运算符: {op_type}")
        else:
            raise ValueError(f"不支持的语法节点: {type(node)}")
    
    return float(_eval_node(node.body))


app = Server("local-tools-standalone")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="calculator",
            description="计算数学表达式。支持加减乘除幂运算",
            inputSchema={
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "数学表达式"}},
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
    if name == "calculator":
        try:
            result = safe_evaluate(arguments.get("expression", ""))
            return [TextContent(type="text", text=json.dumps({"success": True, "result": result}))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}))]
    
    elif name == "echo":
        return [TextContent(type="text", text=json.dumps({"success": True, "echoed": arguments.get("message", "")}))]
    
    elif name == "get_time":
        now = datetime.now()
        return [TextContent(type="text", text=json.dumps({"success": True, "datetime": now.isoformat()}))]
    
    elif name == "random_number":
        min_val = arguments.get("min", 0)
        max_val = arguments.get("max", 100)
        return [TextContent(type="text", text=json.dumps({
            "success": True, 
            "number": random.uniform(min_val, max_val)
        }))]
    
    else:
        return [TextContent(type="text", text=json.dumps({"success": False, "error": f"Unknown: {name}"}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            initialization_options=app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
