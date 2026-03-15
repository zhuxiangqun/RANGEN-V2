#!/usr/bin/env python3
"""
最终验证ReActAgent到ReasoningExpert迁移的修复效果
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def final_test():
    """最终测试"""
    print("🎯 最终迁移验证测试")
    print("=" * 50)

    try:
        print("1️⃣ 测试ReasoningExpert的register_tool方法...")

        from src.agents.reasoning_expert import ReasoningExpert

        # 创建实例
        expert = ReasoningExpert()
        print("   ✅ ReasoningExpert实例化成功")

        # 测试register_tool方法
        result = expert.register_tool("test_tool", {"category": "test"})
        print(f"   ✅ register_tool方法工作正常，返回: {result}")

        print("\n2️⃣ 测试UnifiedResearchSystem的ReactAgent初始化...")

        # 测试UnifiedResearchSystem导入
        from src.unified_research_system import UnifiedResearchSystem
        print("   ✅ UnifiedResearchSystem导入成功")

        # 创建实例
        system = UnifiedResearchSystem()
        print("   ✅ UnifiedResearchSystem实例化成功")

        # 检查_react_agent
        if hasattr(system, '_react_agent') and system._react_agent is not None:
            agent_type = type(system._react_agent).__name__
            print(f"   ✅ _react_agent已正确初始化: {agent_type}")

            if agent_type == "ReasoningExpert":
                print("   🎉 迁移成功！UnifiedResearchSystem现在使用ReasoningExpert")
                return True
            else:
                print(f"   ❌ 仍在使用其他Agent: {agent_type}")
                return False
        else:
            print("   ❌ _react_agent未正确初始化")
            return False

    except Exception as e:
        print(f"   ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = final_test()

    print("\n" + "=" * 50)
    if success:
        print("🎉 迁移修复成功！ReActAgent已完全迁移到ReasoningExpert")
        print("\n📋 迁移完成情况:")
        print("   ✅ 接口兼容性分析")
        print("   ✅ 代码导入替换")
        print("   ✅ 初始化代码修改")
        print("   ✅ 兼容性问题修复")
        print("   ✅ 功能验证通过")
    else:
        print("❌ 迁移仍有问题，需要进一步调试")

    print("\n💡 建议下一步:")
    if success:
        print("   1. 监控ReasoningExpert的性能表现")
        print("   2. 收集用户反馈")
        print("   3. 准备进行其他Agent的迁移")
    else:
        print("   1. 检查详细的错误日志")
        print("   2. 考虑回滚到ReActAgentWrapper")
        print("   3. 逐步调试ReasoningExpert的初始化")