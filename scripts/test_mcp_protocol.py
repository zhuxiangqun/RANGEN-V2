#!/usr/bin/env python3
"""简单测试MCP协议"""
import asyncio
import subprocess
import json

async def test():
    # 启动服务器
    proc = subprocess.Popen(
        ['/opt/anaconda3/bin/python', 'src/agents/tools/standalone_mcp_server.py'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
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
    
    # 读取响应
    line = proc.stdout.readline()
    print(f"Init response: {line}")
    
    # 发送工具列表请求
    list_req = {
        "jsonrpc": "2.0", 
        "id": "2", 
        "method": "tools/list"
    }
    proc.stdin.write(json.dumps(list_req).encode() + b'\n')
    proc.stdin.flush()
    
    line = proc.stdout.readline()
    print(f"List tools response: {line}")
    
    # 发送计算器调用
    call_req = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "tools/call",
        "params": {
            "name": "calculator",
            "arguments": {"expression": "2+3*4"}
        }
    }
    proc.stdin.write(json.dumps(call_req).encode() + b'\n')
    proc.stdin.flush()
    
    line = proc.stdout.readline()
    print(f"Calculator response: {line}")
    
    proc.terminate()

asyncio.run(test())
