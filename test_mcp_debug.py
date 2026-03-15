#!/usr/bin/env python3
"""简单测试MCP协议 - 带调试"""
import asyncio
import subprocess
import json
import os

async def test():
    # 启动服务器
    proc = subprocess.Popen(
        ['/opt/anaconda3/bin/python', 'src/agents/tools/standalone_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # 读取stderr（服务器启动信息）
    await asyncio.sleep(0.5)
    if proc.stderr:
        stderr_data = proc.stderr.read(1000)
        if stderr_data:
            print(f"STDERR: {stderr_data.decode()}")
    
    # 发送初始化
    init_req = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    proc.stdin.write(json.dumps(init_req).encode() + b'\n')
    proc.stdin.flush()
    
    # 等待响应
    try:
        line = await asyncio.wait_for(asyncio.create_task(asyncio.stream_reader_line(proc.stdout)), timeout=3)
        print(f"Init response: {line}")
    except asyncio.TimeoutError:
        print("Timeout waiting for init response")
        proc.terminate()
        return
    
    proc.terminate()
    print("Server terminated")

asyncio.run(test())
