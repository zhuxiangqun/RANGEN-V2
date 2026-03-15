#!/usr/bin/env python3
"""
调试ReAct Agent初始化过程
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

async def debug_react_agent_init():
    """调试ReAct Agent初始化"""
    print("🔍 调试ReAct Agent初始化过程")
    print("=" * 60)

    try:
        print("1️⃣ 导入UnifiedResearchSystem...")
        from src.unified_research_system import UnifiedResearchSystem
        print("   ✅ 导入成功")

        print("\n2️⃣ 创建UnifiedResearchSystem实例...")
        print("   🔄 正在初始化（这可能需要一些时间）...")

        # 手动调用初始化过程来捕获异常
        print("   📊 步骤2.1: 创建基础实例...")
        system = UnifiedResearchSystem.__new__(UnifiedResearchSystem)
        system._react_agent = None
        system._use_react_agent = False
        system._langgraph_react_agent = None

        # 初始化日志器（可能需要）
        from src.utils.logging_helper import get_module_logger, ModuleType
        system.module_logger = get_module_logger(ModuleType.CORE, "UnifiedResearchSystem")

        print("   📊 步骤2.2: 手动调用_initialize_react_agent...")

        try:
            await system._initialize_react_agent()
            print("   ✅ _initialize_react_agent成功完成")

            print("   📊 检查结果...")
            print(f"   📊 _react_agent: {system._react_agent}")
            print(f"   📊 _use_react_agent: {system._use_react_agent}")
            if system._react_agent:
                print(f"   📊 Agent类型: {type(system._react_agent).__name__}")

        except Exception as e:
            print(f"   ❌ _initialize_react_agent失败: {e}")
            import traceback
            print("   📊 详细错误信息:")
            traceback.print_exc()

            # 检查部分初始化状态
            print("   📊 检查部分状态...")
            print(f"   📊 _react_agent: {system._react_agent}")
            print(f"   📊 _use_react_agent: {system._use_react_agent}")

        print("\n3️⃣ 直接测试ReasoningExpert实例化...")
        try:
            from src.agents.reasoning_expert import ReasoningExpert
            expert = ReasoningExpert()
            print("   ✅ ReasoningExpert直接实例化成功")
            print(f"   📊 类型: {type(expert).__name__}")

            # 测试register_tool方法
            print("   📊 测试register_tool方法...")
            result = expert.register_tool("test", {})
            print(f"   ✅ register_tool返回: {result}")

        except Exception as e:
            print(f"   ❌ ReasoningExpert实例化失败: {e}")
            traceback.print_exc()

    except Exception as e:
        print(f"❌ 调试过程失败: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_react_agent_init())
