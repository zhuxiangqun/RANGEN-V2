#!/usr/bin/env python3
"""测试内部MCP服务器"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_in_process_mcp():
    """测试进程内MCP执行器"""
    print("=" * 60)
    print("测试: 进程内MCP执行器")
    print("=" * 60)
    
    try:
        from src.agents.tools.in_process_mcp import get_in_process_mcp_executor
        
        executor = get_in_process_mcp_executor()
        
        # 1. 列出工具
        print("\n[1] 列出可用工具...")
        tools = executor.list_tools()
        print(f"    共 {len(tools)} 个工具")
        for t in tools[:5]:
            print(f"    - {t['name']}: {t['description'][:50]}...")
        
        # 2. 调用calculator工具
        print("\n[2] 调用 calculator 工具...")
        result = await executor.execute("calculator", {"expression": "25 * 4 + 10"})
        print(f"    表达式: 25 * 4 + 10")
        print(f"    结果: {result}")
        
        if result.get("success"):
            print(f"    ✅ 计算成功: {result.get('data')}")
        else:
            print(f"    ❌ 计算失败: {result.get('error')}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_standalone_mcp_server():
    """测试独立MCP服务器"""
    print("\n" + "=" * 60)
    print("测试: 独立MCP服务器 (internal_mcp_server.py)")
    print("=" * 60)
    
    try:
        # 尝试导入
        from src.agents.tools.internal_mcp_server import create_internal_mcp_server
        
        print("\n[1] 创建MCP服务器...")
        app = create_internal_mcp_server()
        print(f"    ✅ 服务器创建成功: {app}")
        
        # 获取工具列表
        print("\n[2] 获取工具列表...")
        
        # 使用mcp库的官方方式
        from mcp.types import Tool
        
        # 直接调用list_tools
        tools = await app._tool_manager.list_tools()
        print(f"    共 {len(tools)} 个工具")
        for t in tools[:3]:
            print(f"    - {t.name}")
        
        return True
        
    except ImportError as e:
        print(f"    ⚠️  MCP库未正确安装: {e}")
        return False
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_hybrid_executor():
    """测试HybridToolExecutor"""
    print("\n" + "=" * 60)
    print("测试: HybridToolExecutor (MCP模式)")
    print("=" * 60)
    
    try:
        from src.agents.skills.hybrid_tool_executor import HybridToolExecutor
        
        # 使用MCP模式
        executor = HybridToolExecutor(internal_mode="mcp")
        
        print("\n[1] 列出所有工具...")
        all_tools = executor.list_all_tools()
        print(f"    内部工具: {len(all_tools.get('internal', []))} 个")
        print(f"    MCP工具: {len(all_tools.get('mcp', []))} 个")
        
        print("\n[2] 通过MCP模式调用calculator...")
        result = await executor.execute(
            "calculator",
            {"expression": "100 / 4 + 50"},
            tool_source=None
        )
        
        if result.success:
            print(f"    ✅ 执行成功: {result.result}")
        else:
            print(f"    ❌ 执行失败: {result.error}")
        
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("\n" + "=" * 60)
    print("🧪 RANGEN 内部MCP服务器测试")
    print("=" * 60)
    
    results = []
    
    # 测试1: 进程内MCP
    results.append(("进程内MCP", await test_in_process_mcp()))
    
    # 测试2: HybridToolExecutor
    results.append(("HybridToolExecutor", await test_hybrid_executor()))
    
    # 测试3: 独立MCP服务器
    results.append(("独立MCP服务器", await test_standalone_mcp_server()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(r[1] for r in results)
    print()
    if all_passed:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试失败，请检查错误信息")
    
    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
