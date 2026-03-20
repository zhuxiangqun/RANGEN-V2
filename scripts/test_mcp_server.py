#!/usr/bin/env python3
"""测试本地MCP服务器"""
import asyncio
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.agents.tools.mcp_local_server import list_tools, call_tool


async def test():
    # 测试列出工具
    tools = await list_tools()
    print('=== 可用工具 ===')
    for tool in tools:
        print(f'- {tool.name}: {tool.description}')
    
    # 测试计算器
    print('\n=== 测试 calculator ===')
    result = await call_tool('calculator', {'expression': '2+3*4'})
    print(result[0].text)
    
    # 测试 echo
    print('\n=== 测试 echo ===')
    result = await call_tool('echo', {'message': 'Hello MCP!'})
    print(result[0].text)
    
    # 测试 get_time
    print('\n=== 测试 get_time ===')
    result = await call_tool('get_time', {'timezone': 'local'})
    print(result[0].text)
    
    # 测试 random_number
    print('\n=== 测试 random_number ===')
    result = await call_tool('random_number', {'min': 1, 'max': 10, 'count': 3})
    print(result[0].text)


if __name__ == "__main__":
    asyncio.run(test())
