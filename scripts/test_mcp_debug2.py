#!/usr/bin/env python3
"""测试MCP服务器 - 调试版本"""
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
    
    # 读取响应
    import select
    await asyncio.sleep(0.5)
    
    # 先读取stderr
    if select.select([proc.stderr], [], [], 0)[0]:
        err = proc.stderr.read(500)
        if err:
            print(f"STDERR: {err.decode()[:200]}")
    
    # 读取stdout
    line = proc.stdout.readline()
    print(f"First line: {line[:100] if line else 'empty'}")
    
    # 尝试解析
    try:
        resp = json.loads(line.decode())
        print(f"Init: {resp}")
    except:
        # 可能有多行
        print(f"Raw: {line}")
        # 读取所有可用行
        while select.select([proc.stdout], [], [], 0.1)[0]:
            extra = proc.stdout.readline()
            print(f"Extra: {extra[:100]}")
    
    proc.terminate()

asyncio.run(test())
