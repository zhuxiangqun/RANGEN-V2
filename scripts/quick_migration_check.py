#!/usr/bin/env python3
"""
快速验证ReActAgent迁移的简化脚本
可以复制到Python解释器中运行
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def quick_check():
    """快速检查迁移状态"""
    print("🔍 快速迁移验证")
    print("=" * 40)

    try:
        # 1. 测试导入
        print("1️⃣ 测试导入...")
        from src.unified_research_system import UnifiedResearchSystem
        from src.agents.reasoning_expert import ReasoningExpert
        print("   ✅ 导入成功")

        # 2. 测试实例化
        print("\n2️⃣ 测试实例化和初始化...")
        system = UnifiedResearchSystem()

        # UnifiedResearchSystem需要先调用initialize()方法
        print("   🔄 正在初始化系统...")
        try:
            import asyncio
            asyncio.run(system.initialize())
            print("   ✅ 系统初始化成功")
        except Exception as e:
            print(f"   ❌ 系统初始化失败: {e}")
            return False

        if hasattr(system, '_react_agent') and system._react_agent is not None:
            agent_type = type(system._react_agent).__name__
            print(f"   📊 Agent类型: {agent_type}")

            if agent_type == "ReasoningExpert":
                print("   ✅ 迁移成功！")
                return True
            else:
                print(f"   ❌ 仍在使用: {agent_type}")
                return False
        else:
            print("   ❌ 未找到有效的Agent实例")
            return False

    except Exception as e:
        print(f"   ❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_check()
    if success:
        print("\n🎉 迁移验证通过！")
    else:
        print("\n❌ 迁移验证失败！")
