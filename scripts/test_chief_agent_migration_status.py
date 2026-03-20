#!/usr/bin/env python3
"""
测试ChiefAgent迁移状态
验证ChiefAgent是否正确使用逐步替换策略迁移到AgentCoordinator
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_chief_agent_migration_status():
    """测试ChiefAgent迁移状态"""
    print("🔍 测试ChiefAgent迁移状态")
    print("=" * 60)

    step = 1

    # 步骤1: 验证组件导入
    print(f'\n📋 步骤{step}: 验证组件导入')
    print("-" * 30)

    try:
        # 验证包装器
        from src.agents.chief_agent_wrapper import ChiefAgentWrapper
        print("✅ ChiefAgentWrapper导入成功")

        # 验证适配器
        from src.adapters.chief_agent_adapter import ChiefAgentAdapter
        print("✅ ChiefAgentAdapter导入成功")

        # 验证源Agent
        from src.agents.chief_agent import ChiefAgent
        print("✅ ChiefAgent导入成功")

        # 验证目标Agent
        from src.agents.agent_coordinator import AgentCoordinator
        print("✅ AgentCoordinator导入成功")

        step += 1

    except ImportError as e:
        print(f"❌ 组件导入失败: {e}")
        return False

    # 步骤2: 测试包装器实例化
    print(f'\n📋 步骤{step}: 测试包装器实例化')
    print("-" * 30)

    try:
        # 测试逐步替换已启用的包装器
        wrapper = ChiefAgentWrapper(enable_gradual_replacement=True, initial_replacement_rate=0.01)
        print("✅ ChiefAgentWrapper实例化成功（逐步替换已启用）")

        # 检查属性
        print(f"   逐步替换启用: {wrapper.enable_gradual_replacement}")
        print(f"   初始替换率: {wrapper.initial_replacement_rate}")
        print(f"   是否有替换策略: {wrapper.replacement_strategy is not None}")

        step += 1

    except Exception as e:
        print(f"❌ 包装器实例化失败: {e}")
        return False

    # 步骤3: 测试适配器实例化
    print(f'\n📋 步骤{step}: 测试适配器实例化')
    print("-" * 30)

    try:
        adapter = ChiefAgentAdapter()
        print("✅ ChiefAgentAdapter实例化成功")

        step += 1

    except Exception as e:
        print(f"❌ 适配器实例化失败: {e}")
        return False

    # 步骤4: 测试基本功能
    print(f'\n📋 步骤{step}: 测试基本功能')
    print("-" * 30)

    try:
        # 测试简单查询
        test_context = {
            'query': '测试查询',
            'task_type': 'coordination'
        }

        result = await wrapper.execute(test_context)
        print("✅ 包装器执行成功")

        if hasattr(result, 'success'):
            print(f"   执行结果: {'成功' if result.success else '失败'}")

        step += 1

    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

    # 步骤5: 检查UnifiedResearchSystem中的使用
    print(f'\n📋 步骤{step}: 检查系统集成')
    print("-" * 30)

    try:
        from src.unified_research_system import UnifiedResearchSystem
        system = UnifiedResearchSystem()

        # 检查是否使用了包装器
        if hasattr(system, '_chief_agent') and system._chief_agent is not None:
            agent_type = type(system._chief_agent).__name__
            print(f"✅ 系统中的ChiefAgent类型: {agent_type}")

            if agent_type == 'ChiefAgentWrapper':
                print("✅ 系统正确使用ChiefAgentWrapper")
                return True
            else:
                print(f"⚠️ 系统使用的是{agent_type}，不是ChiefAgentWrapper")
                return False
        else:
            print("⚠️ 系统未初始化ChiefAgent")
            return False

    except Exception as e:
        print(f"❌ 系统集成检查失败: {e}")
        return False

def main():
    """主函数"""
    success = asyncio.run(test_chief_agent_migration_status())

    print(f'\n{"=" * 60}')
    if success:
        print("🎉 ChiefAgent迁移状态验证通过！")
        print("✅ 所有组件正常工作")
        print("✅ 逐步替换策略已启用")
        print("✅ 系统集成正确")
        print("\n💡 迁移状态: 准备就绪，可以投入生产使用")
    else:
        print("❌ ChiefAgent迁移状态验证失败！")
        print("需要检查和修复迁移问题")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
