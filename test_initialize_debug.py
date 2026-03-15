#!/usr/bin/env python3
"""
调试UnifiedResearchSystem的initialize方法
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_initialize_debug():
    """调试initialize方法"""
    print("🔍 调试UnifiedResearchSystem.initialize()")
    print("=" * 60)

    try:
        print("1️⃣ 导入UnifiedResearchSystem...")
        from src.unified_research_system import UnifiedResearchSystem
        print("   ✅ 导入成功")

        print("\n2️⃣ 创建实例...")
        system = UnifiedResearchSystem()
        print("   ✅ 实例创建成功")

        print(f"   📊 初始状态: _react_agent={system._react_agent}, _use_react_agent={system._use_react_agent}")

        print("\n3️⃣ 调用initialize()...")
        print("   🔄 正在初始化（这可能需要一些时间）...")

        try:
            await system.initialize()
            print("   ✅ initialize()调用完成")

            print(f"   📊 初始化后状态: _react_agent={system._react_agent}, _use_react_agent={system._use_react_agent}")

            if system._react_agent is not None:
                agent_type = type(system._react_agent).__name__
                print(f"   📊 Agent类型: {agent_type}")

                if agent_type == "ReasoningExpert":
                    print("   ✅ 迁移成功！")
                    return True
                else:
                    print(f"   ❌ 仍在使用: {agent_type}")
                    return False
            else:
                print("   ❌ _react_agent仍然是None")
                return False

        except Exception as e:
            print(f"   ❌ initialize()调用失败: {e}")
            import traceback
            print("   📊 详细错误:")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_initialize_debug())
    print("\n" + "=" * 60)
    if success:
        print("🎉 初始化测试成功！ReActAgent迁移完成")
    else:
        print("❌ 初始化测试失败")
        print("💡 可能的问题:")
        print("   - UnifiedResearchSystem.initialize()有异常")
        print("   - _initialize_agents()没有被调用")
        print("   - _initialize_react_agent()抛出了异常")
