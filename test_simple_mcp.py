#!/usr/bin/env python3
"""简单测试内部MCP服务器"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def main():
    print("=" * 60)
    print("测试内部MCP服务器")
    print("=" * 60)
    
    # 测试1: 导入并列出工具
    print("\n[1] 测试 InProcessMCPExecutor...")
    try:
        from src.agents.tools.in_process_mcp import InProcessMCPExecutor
        executor = InProcessMCPExecutor()
        tools = executor.list_tools()
        print(f"    ✅ 工具数量: {len(tools)}")
        for t in tools[:5]:
            print(f"       - {t['name']}")
    except Exception as e:
        print(f"    ❌ 失败: {e}")
    
    # 测试2: 尝试调用
    print("\n[2] 测试工具调用...")
    try:
        result = await executor.execute("calculator", {"expression": "10 + 20"})
        print(f"    结果: {result}")
    except Exception as e:
        print(f"    ❌ 失败: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
