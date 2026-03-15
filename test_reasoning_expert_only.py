#!/usr/bin/env python3
"""
单独测试ReasoningExpert实例化
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_reasoning_expert():
    """单独测试ReasoningExpert"""
    print("🔍 单独测试ReasoningExpert实例化")
    print("=" * 50)

    try:
        print("1️⃣ 导入ReasoningExpert...")
        from src.agents.reasoning_expert import ReasoningExpert
        print("   ✅ 导入成功")

        print("\n2️⃣ 实例化ReasoningExpert...")
        expert = ReasoningExpert()
        print("   ✅ 实例化成功")
        print(f"   📊 类型: {type(expert)}")
        print(f"   📊 类名: {type(expert).__name__}")

        print("\n3️⃣ 检查基本属性...")
        print(f"   📊 agent_id: {getattr(expert, 'agent_id', 'N/A')}")
        print(f"   📊 domain_expertise: {getattr(expert, 'domain_expertise', 'N/A')}")

        print("\n4️⃣ 检查方法...")
        has_execute = hasattr(expert, 'execute')
        has_register_tool = hasattr(expert, 'register_tool')
        print(f"   📊 has execute: {has_execute}")
        print(f"   📊 has register_tool: {has_register_tool}")

        if has_register_tool:
            print("\n5️⃣ 测试register_tool方法...")
            result = expert.register_tool("test_tool", {"category": "test"})
            print(f"   ✅ register_tool返回: {result}")

        print("\n6️⃣ 测试execute方法签名...")
        import inspect
        if has_execute:
            sig = inspect.signature(expert.execute)
            print(f"   ✅ execute签名: {sig}")

        print("\n" + "=" * 50)
        print("🎉 ReasoningExpert单独测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_reasoning_expert()
    if not success:
        print("\n💡 问题可能在于ReasoningExpert的初始化或依赖")
    else:
        print("\n💡 ReasoningExpert本身工作正常，问题可能在UnifiedResearchSystem中")
