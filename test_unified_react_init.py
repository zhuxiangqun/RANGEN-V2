#!/usr/bin/env python3
"""
测试UnifiedResearchSystem中ReAct Agent的初始化
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_unified_react_init():
    """测试UnifiedResearchSystem中ReAct Agent的初始化"""
    print("🔍 测试UnifiedResearchSystem中ReAct Agent初始化")
    print("=" * 60)

    try:
        print("1️⃣ 创建简化的UnifiedResearchSystem...")
        # 直接导入并创建实例，避免完整的初始化
        from src.unified_research_system import UnifiedResearchSystem

        # 创建实例但不调用__init__
        system = UnifiedResearchSystem.__new__(UnifiedResearchSystem)

        # 手动设置必要的属性
        system._react_agent = None
        system._use_react_agent = False

        # 设置日志器
        import logging
        system.module_logger = logging.getLogger("UnifiedResearchSystem")

        print("   ✅ UnifiedResearchSystem基础设置完成")

        print("\n2️⃣ 直接调用_initialize_react_agent...")
        try:
            await system._initialize_react_agent()
            print("   ✅ _initialize_react_agent调用成功")

            print("   📊 检查结果...")
            print(f"   📊 _react_agent: {system._react_agent}")
            print(f"   📊 _use_react_agent: {system._use_react_agent}")

            if system._react_agent is not None:
                print("   ✅ ReAct Agent初始化成功！")
                print(f"   📊 Agent类型: {type(system._react_agent).__name__}")
                return True
            else:
                print("   ❌ _react_agent仍然是None")
                return False

        except Exception as e:
            print(f"   ❌ _initialize_react_agent调用失败: {e}")
            import traceback
            print("   📊 详细错误:")
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ 测试准备失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_unified_react_init())
    print("\n" + "=" * 60)
    if success:
        print("🎉 UnifiedResearchSystem中ReAct Agent初始化成功！")
        print("💡 问题可能在完整的UnifiedResearchSystem初始化过程中的其他地方")
    else:
        print("❌ UnifiedResearchSystem中ReAct Agent初始化失败")
        print("🔧 需要修复_initialize_react_agent方法")
