#!/usr/bin/env python3
"""测试统一MCP调用架构"""
import asyncio
import sys
sys.path.insert(0, '/Users/apple/workdata/person/zy/RANGEN-main(syu-python)')

from src.agents.skills.hybrid_tool_executor import get_hybrid_executor, ToolSource


async def test_unified_mcp():
    """测试统一MCP调用"""
    executor = get_hybrid_executor()
    
    print("=" * 60)
    print("测试 1: 列出所有工具")
    print("=" * 60)
    all_tools = executor.list_all_tools()
    
    print(f"\n内部工具 ({len(all_tools['internal'])}个):")
    for t in all_tools['internal']:
        print(f"  - {t['name']}: {t['description'][:40]}...")
    
    print(f"\n外部MCP工具 ({len(all_tools['mcp'])}个):")
    if all_tools['mcp']:
        for t in all_tools['mcp']:
            print(f"  - {t['name']} [{t.get('server', 'unknown')}]: {t['description'][:30]}...")
    else:
        print("  (无)")
    
    print("\n" + "=" * 60)
    print("测试 2: 通过MCP协议调用内部计算器工具")
    print("=" * 60)
    
    # 通过MCP协议调用内部工具
    result = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "10 + 20 * 3"},
        tool_source=ToolSource.INTERNAL
    )
    
    print(f"\n调用: calculator(expression='10 + 20 * 3')")
    print(f"结果: {result.result}")
    print(f"来源: {result.source.value}")
    print(f"成功: {result.success}")
    print(f"耗时: {result.execution_time:.4f}s")
    
    print("\n" + "=" * 60)
    print("测试 3: 复杂表达式")
    print("=" * 60)
    
    result2 = await executor.execute(
        tool_name="calculator",
        parameters={"expression": "(100 + 50) / 3"},
        tool_source=ToolSource.INTERNAL
    )
    
    print(f"\n调用: calculator(expression='(100 + 50) / 3')")
    print(f"结果: {result2.result}")
    print(f"成功: {result2.success}")
    
    print("\n" + "=" * 60)
    print("测试 4: 测试不存在的工具")
    print("=" * 60)
    
    result3 = await executor.execute(
        tool_name="nonexistent_tool",
        parameters={},
        tool_source=ToolSource.INTERNAL
    )
    
    print(f"\n调用: nonexistent_tool()")
    print(f"成功: {result3.success}")
    print(f"错误: {result3.error}")
    
    print("\n✅ 统一MCP调用测试完成!")


if __name__ == "__main__":
    asyncio.run(test_unified_mcp())
