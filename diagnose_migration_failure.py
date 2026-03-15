#!/usr/bin/env python3
"""
详细诊断迁移失败原因
"""

import sys
import traceback
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def diagnose_reasoning_expert():
    """诊断ReasoningExpert初始化问题"""
    print("🔍 诊断ReasoningExpert初始化问题")
    print("=" * 50)

    try:
        print("1️⃣ 测试ReasoningExpert直接导入...")
        from src.agents.reasoning_expert import ReasoningExpert
        print("   ✅ ReasoningExpert导入成功")

        print("\n2️⃣ 测试ReasoningExpert实例化...")
        expert = ReasoningExpert()
        print(f"   ✅ ReasoningExpert实例化成功: {type(expert)}")

        print("\n3️⃣ 测试execute方法签名...")
        import inspect
        execute_method = getattr(expert, 'execute', None)
        if execute_method:
            sig = inspect.signature(execute_method)
            print(f"   ✅ execute方法存在，签名: {sig}")
        else:
            print("   ❌ execute方法不存在")

    except Exception as e:
        print(f"   ❌ ReasoningExpert诊断失败: {e}")
        traceback.print_exc()
        return False

    return True

def diagnose_unified_system():
    """诊断UnifiedResearchSystem初始化问题"""
    print("\n🔍 诊断UnifiedResearchSystem初始化问题")
    print("=" * 50)

    try:
        print("1️⃣ 测试UnifiedResearchSystem导入...")
        from src.unified_research_system import UnifiedResearchSystem
        print("   ✅ UnifiedResearchSystem导入成功")

        print("\n2️⃣ 测试UnifiedResearchSystem实例化...")
        print("   🔄 正在实例化（这可能需要一些时间）...")

        # 启用详细日志
        import logging
        logging.basicConfig(level=logging.INFO)

        system = UnifiedResearchSystem()
        print("   ✅ UnifiedResearchSystem实例化成功")

        print("\n3️⃣ 检查_react_agent状态...")
        if hasattr(system, '_react_agent'):
            react_agent = system._react_agent
            print(f"   📊 _react_agent值: {react_agent}")
            print(f"   📊 _react_agent类型: {type(react_agent)}")

            if react_agent is None:
                print("   ❌ _react_agent是None")
                return False
            else:
                print("   ✅ _react_agent不是None")
        else:
            print("   ❌ UnifiedResearchSystem没有_react_agent属性")
            return False

        print("\n4️⃣ 检查_use_react_agent状态...")
        if hasattr(system, '_use_react_agent'):
            use_react = system._use_react_agent
            print(f"   📊 _use_react_agent值: {use_react}")
        else:
            print("   ⚠️ UnifiedResearchSystem没有_use_react_agent属性")

        return True

    except Exception as e:
        print(f"   ❌ UnifiedResearchSystem诊断失败: {e}")
        traceback.print_exc()
        return False

def check_dependencies():
    """检查依赖项"""
    print("\n🔍 检查关键依赖项")
    print("=" * 50)

    dependencies = [
        'src.agents.base_agent',
        'src.agents.expert_agent',
        'src.utils.logging_helper',
        'src.utils.unified_centers',
    ]

    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError as e:
            print(f"   ❌ {dep}: {e}")
        except Exception as e:
            print(f"   ⚠️ {dep}: {e}")

def main():
    """主诊断函数"""
    print("🚀 迁移失败详细诊断")
    print("=" * 60)

    # 1. 检查依赖
    check_dependencies()

    # 2. 诊断ReasoningExpert
    re_success = diagnose_reasoning_expert()

    # 3. 诊断UnifiedResearchSystem
    us_success = diagnose_unified_system()

    print("\n" + "=" * 60)
    print("📊 诊断结果汇总:")

    if re_success and us_success:
        print("✅ 所有诊断通过，迁移应该成功")
    else:
        print("❌ 诊断发现问题:")

        if not re_success:
            print("   - ReasoningExpert初始化失败")

        if not us_success:
            print("   - UnifiedResearchSystem初始化失败")

        print("\n🔧 建议解决方案:")
        print("   1. 检查ReasoningExpert的__init__方法")
        print("   2. 检查UnifiedResearchSystem的_initialize_react_agent方法")
        print("   3. 查看详细的错误日志")
        print("   4. 考虑回滚到ReActAgentWrapper")

if __name__ == "__main__":
    main()
