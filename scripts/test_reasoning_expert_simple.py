#!/usr/bin/env python3
"""
超级简单的ReasoningExpert测试
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_simple():
    """超级简单的测试"""
    print("🔍 超级简单ReasoningExpert测试")
    print("=" * 40)

    try:
        print("1️⃣ 导入...")
        from src.agents.reasoning_expert import ReasoningExpert
        print("   ✅ 导入成功")

        print("\n2️⃣ 实例化...")
        expert = ReasoningExpert()
        print("   ✅ 实例化成功")
        print(f"   📊 类型: {type(expert)}")
        print(f"   📊 类名: {type(expert).__name__}")

        print("\n3️⃣ 检查方法...")
        methods = ['execute', 'register_tool']
        for method in methods:
            has_method = hasattr(expert, method)
            print(f"   📊 has {method}: {has_method}")

        print("\n" + "=" * 40)
        print("🎉 超级简单测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    if success:
        print("💡 ReasoningExpert本身工作正常，问题在集成层面")
    else:
        print("💡 ReasoningExpert本身就有问题")
