#!/usr/bin/env python3
"""
本地MCP服务器 - 演示使用官方MCP SDK

功能:
1. calculator - 数学计算器
2. echo - 回显消息
3. get_time - 获取当前时间
4. random_number - 生成随机数
"""

# ===== 重要：抑制所有stdout输出 =====
import sys
import os
import io

# 将stdout重定向到null设备，防止日志干扰JSON-RPC
sys.stdout = io.StringIO()
# 允许stderr输出（用于调试）

import asyncio
import json
import random
import ast
import operator
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

import asyncio
import json
import random
import ast
import operator
from datetime import datetime
from typing import Any

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
    """安全地计算数学表达式"""
    import re
    
    # 验证表达式只包含安全字符
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


# 创建服务器实例
app = Server("local-tools")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用工具"""
    return [
        Tool(
            name="calculator",
            description="计算数学表达式。支持加减乘除幂运算，如 '2+3*4' 或 '(10+5)/3'",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，如 '2+3*4'"
                    }
                },
                "required": ["expression"]
            }
        ),
        Tool(
            name="echo",
            description="回显消息 - 返回输入的消息",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要回显的消息"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="get_time",
            description="获取当前时间",
            inputSchema={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区，默认为 'local'，可设为 'utc'",
                        "enum": ["local", "utc"]
                    }
                }
            }
        ),
        Tool(
            name="random_number",
            description="生成随机数",
            inputSchema={
                "type": "object",
                "properties": {
                    "min": {
                        "type": "number",
                        "description": "最小值，默认为0"
                    },
                    "max": {
                        "type": "number",
                        "description": "最大值，默认为100"
                    },
                    "count": {
                        "type": "number",
                        "description": "生成数量，默认为1"
                    }
                }
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """调用工具"""
    
    if name == "calculator":
        expression = arguments.get("expression", "")
        try:
            result = safe_evaluate(expression)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": True,
                    "result": result,
                    "expression": expression
                }, ensure_ascii=False)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "success": False,
                    "error": str(e)
                }, ensure_ascii=False)
            )]
    
    elif name == "echo":
        message = arguments.get("message", "")
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "echoed": message
            }, ensure_ascii=False)
        )]
    
    elif name == "get_time":
        timezone = arguments.get("timezone", "local")
        if timezone == "utc":
            now = datetime.utcnow()
        else:
            now = datetime.now()
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "datetime": now.isoformat(),
                "timestamp": now.timestamp(),
                "timezone": timezone
            }, ensure_ascii=False)
        )]
    
    elif name == "random_number":
        min_val = arguments.get("min", 0)
        max_val = arguments.get("max", 100)
        count = arguments.get("count", 1)
        
        # 限制数量
        count = min(count, 100)
        
        numbers = [random.uniform(min_val, max_val) for _ in range(count)]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": True,
                "numbers": numbers if count > 1 else numbers[0],
                "min": min_val,
                "max": max_val,
                "count": count
            }, ensure_ascii=False)
        )]
    
    else:
        return [TextContent(
            type="text",
            text=json.dumps({
                "success": False,
                "error": f"Unknown tool: {name}"
            }, ensure_ascii=False)
        )]


import logging
import sys

# 抑制所有日志输出到stdout（只输出到stderr）
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s - %(message)s',
    stream=sys.stderr
)

# 关闭RANGEN工具初始化日志
for logger_name in ['src.agents.tools.tool_initializer', 'src.agents.tools.tool_registry']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)


async def main():
    """主函数"""
    async with stdio_server() as reader_writer:
        await app.run(
            reader_writer,
            app.create_initialization_options()
        )
    """主函数"""
    async with stdio_server() as reader_writer:
        await app.run(
            reader_writer,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
