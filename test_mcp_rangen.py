#!/usr/bin/env python3
"""测试MCP服务器 - 列出工具"""
import asyncio
import subprocess
import json
import sys

async def test():
    proc = subprocess.Popen(
        [sys.executable, '-m', 'src.agents.tools.mcp_server'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    async def send(req):
        data = json.dumps(req) + "\n"
        proc.stdin.write(data.encode())
        proc.stdin.flush()
    
    async def recv():
        line = proc.stdout.readline()
        if line:
            return json.loads(line.decode())
        return None
    
    # 初始化
    await send({
        "jsonrpc": "2.0", 
        "id": "1", 
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05", 
            "capabilities": {}, 
            "clientInfo": {"name": "test"}
        }
    })
    resp = await recv()
    print(f"Init: {resp}")
    
    # 列出工具
    await send({"jsonrpc": "2.0", "id": "2", "method": "tools/list"})
    resp = await recv()
    print(f"\n工具列表:")
    if resp and "result" in resp:
        tools = resp["result"].get("tools", [])
        for t in tools:
            print(f"  - {t['name']}: {t['description'][:50]}...")
    
    # 测试调用计算器
    await send({
        "jsonrpc": "2.0", 
        "id": "3", 
        "method": "tools/call",
        "params": {
            "name": "calculator", 
            "arguments": {"expression": "2+3*4"}
        }
    })
    resp = await recv()
    print(f"\nCalculator调用: {resp}")
    
    proc.terminate()
    print("\n✅ 测试完成!")

asyncio.run(test())
