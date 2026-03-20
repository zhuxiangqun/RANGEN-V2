#!/usr/bin/env python3
"""
直接测试ReAct Agent初始化方法
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def test_react_agent_direct():
    """直接测试ReAct Agent初始化"""
    print("🔍 直接测试ReAct Agent初始化方法")
    print("=" * 50)

    try:
        # 创建一个简化的系统实例
        from src.unified_research_system import UnifiedResearchSystem

        # 创建实例但不调用__init__的复杂逻辑
        system = UnifiedResearchSystem.__new__(UnifiedResearchSystem)

        # 设置必要的属性
        system._react_agent = None
        system._use_react_agent = False

        # 设置日志器
        import logging
        system.module_logger = logging.getLogger("UnifiedResearchSystem")

        print("1️⃣ 测试直接调用_initialize_react_agent...")

        # 直接调用初始化方法
        await system._initialize_react_agent()

        print("2️⃣ 检查结果...")

        if hasattr(system, '_react_agent') and system._react_agent is not None:
            agent_type = type(system._react_agent).__name__
            print(f"   📊 Agent类型: {agent_type}")
            print(f"   📊 Agent实例: {system._react_agent}")
            print(f"   📊 _use_react_agent: {system._use_react_agent}")

            if agent_type == "ReasoningExpert":
                print("   ✅ ReAct Agent初始化成功！")
                return True
            else:
                print(f"   ❌ 错误：期望ReasoningExpert，实际得到{agent_type}")
                return False
        else:
            print("   ❌ 初始化失败：_react_agent为None")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_react_agent_direct())
    print("\n" + "=" * 50)
    if success:
        print("🎉 ReAct Agent初始化测试通过！")
        print("💡 UnifiedResearchSystem的_initialize_react_agent方法工作正常")
    else:
        print("❌ ReAct Agent初始化测试失败")
        print("🔧 需要进一步检查ReasoningExpert或初始化逻辑")
