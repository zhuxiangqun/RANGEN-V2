#!/usr/bin/env python3
"""
测试ReAct Agent初始化修复
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_react_agent_init():
    """测试ReAct Agent初始化"""
    print("🔍 测试ReAct Agent初始化修复")
    print("=" * 50)

    try:
        # 1. 测试导入
        print("1️⃣ 测试导入...")
        from src.unified_research_system import UnifiedResearchSystem
        print("   ✅ UnifiedResearchSystem导入成功")

        from src.agents.reasoning_expert import ReasoningExpert
        print("   ✅ ReasoningExpert导入成功")

        # 2. 测试直接实例化ReasoningExpert
        print("\n2️⃣ 测试ReasoningExpert实例化...")
        expert = ReasoningExpert()
        print(f"   ✅ ReasoningExpert实例化成功: {type(expert)}")

        # 3. 测试_initialize_react_agent方法
        print("\n3️⃣ 测试_initialize_react_agent方法...")

        # 创建UnifiedResearchSystem实例但不调用__init__
        system = UnifiedResearchSystem.__new__(UnifiedResearchSystem)

        # 设置必要的属性
        system._react_agent = None
        system._use_react_agent = False

        # 导入必要的模块
        import asyncio
        import logging
        system.module_logger = logging.getLogger("UnifiedResearchSystem")

        # 调用方法
        async def test_method():
            await system._initialize_react_agent()
            return system._react_agent, system._use_react_agent

        react_agent, use_react_agent = asyncio.run(test_method())

        print(f"   📊 _react_agent: {react_agent}")
        print(f"   📊 _use_react_agent: {use_react_agent}")

        if react_agent is not None and type(react_agent).__name__ == "ReasoningExpert":
            print("   ✅ _initialize_react_agent方法工作正常")
            return True
        else:
            print("   ❌ _initialize_react_agent方法仍有问题")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_react_agent_init()
    print("\n" + "=" * 50)
    if success:
        print("🎉 ReAct Agent初始化修复测试通过！")
        print("💡 现在可以测试完整的UnifiedResearchSystem初始化")
    else:
        print("❌ ReAct Agent初始化修复测试失败")
        print("🔧 需要进一步检查ReasoningExpert或初始化逻辑")
