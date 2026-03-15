#!/usr/bin/env python3
"""测试通过项目的MCP客户端连接到本地MCP服务器"""
import asyncio
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.gateway.mcp import get_mcp_registry


async def test_mcp_connection():
    print("=== 添加MCP服务器 ===")
    registry = get_mcp_registry()
    
    server_cmd = "/opt/anaconda3/bin/python src/agents/tools/standalone_mcp_server.py"
    
    try:
        conn_id = await registry.add_server(
            name="local-standalone",
            server_url=server_cmd,
            transport="stdio"
        )
        print(f"✓ 服务器添加成功: {conn_id}")
        
        # 获取工具列表
        print("\n=== 获取工具列表 ===")
        tools = registry.get_tools(conn_id)
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # 测试调用工具
        print("\n=== 测试调用 calculator ===")
        result = await registry.call_tool(conn_id, "calculator", {"expression": "100/5+20"})
        print(f"Result: {result}")
        
        print("\n=== 测试调用 echo ===")
        result = await registry.call_tool(conn_id, "echo", {"message": "Hello from MCP Client!"})
        print(f"Result: {result}")
        
        # 断开连接
        print("\n=== 断开连接 ===")
        await registry.remove_server(conn_id)
        print("✓ 已断开连接")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mcp_connection())
