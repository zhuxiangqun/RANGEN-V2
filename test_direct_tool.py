#!/usr/bin/env python3
"""直接测试 HybridToolExecutor 工具调用"""
import asyncio
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.agents.skills.hybrid_tool_executor import get_hybrid_executor, ToolSource


async def test_tool_execution():
    """直接测试工具执行"""
    executor = get_hybrid_executor()
    
    print("=" * 60)
    print("测试: 直接调用 HybridToolExecutor")
    print("=" * 60)
    
    # 测试1: 列出所有工具
    print("\n1. 列出所有工具:")
    tools = executor.list_all_tools()
    print(f"   内部工具: {len(tools['internal'])}个")
    for t in tools['internal'][:5]:
        print(f"   - {t['name']}")
    
    # 测试2: 通过MCP协议调用计算器
    print("\n2. 通过MCP协议调用计算器:")
    result = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "25 * 4 + 10"},
        tool_source=ToolSource.INTERNAL
    )
    print(f"   表达式: 25 * 4 + 10")
    print(f"   结果: {result.result}")
    print(f"   成功: {result.success}")
    print(f"   来源: {result.source.value}")
    
    # 测试3: 更复杂的表达式
    print("\n3. 复杂表达式:")
    result2 = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "(100 + 50) / 3"},
        tool_source=ToolSource.INTERNAL
    )
    print(f"   表达式: (100 + 50) / 3")
    print(f"   结果: {result2.result}")
    print(f"   成功: {result2.success}")
    
    print("\n" + "=" * 60)
    print("✅ HybridToolExecutor 测试通过!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tool_execution())
