#!/usr/bin/env python3
"""完整MCP协议测试"""
import asyncio
import subprocess
import json
import sys

async def test():
    proc = subprocess.Popen(
        ['/opt/anaconda3/bin/python', 'src/agents/tools/standalone_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=1
    )
    
    async def send(req):
        data = json.dumps(req) + "\n"
        proc.stdin.write(data.encode())
        proc.stdin.flush()
        print(f"Sent: {req['method']}")
    
    async def recv():
        line = proc.stdout.readline()
        if line:
            return json.loads(line.decode())
        return None
    
    # 初始化
    await send({
        "jsonrpc": "2.0", "id": "1", "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test"}}
    })
    resp = await recv()
    print(f"Init response: {json.dumps(resp, indent=2)[:200]}...")
    
    # 列出工具
    await send({"jsonrpc": "2.0", "id": "2", "method": "tools/list"})
    resp = await recv()
    print(f"Tools: {resp}")
    
    # 调用计算器
    await send({
        "jsonrpc": "2.0", "id": "3", "method": "tools/call",
        "params": {"name": "calculator", "arguments": {"expression": "2+3*4"}}
    })
    resp = await recv()
    print(f"Calculator result: {resp}")
    
    proc.terminate()
    proc.wait()
    print("\n✅ MCP服务器测试成功!")

asyncio.run(test())
