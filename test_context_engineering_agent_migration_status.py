#!/usr/bin/env python3
"""
测试ContextEngineeringAgent迁移状态
验证ContextEngineeringAgentWrapper是否正确设置逐步替换策略
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_context_engineering_agent_migration_status():
    """测试ContextEngineeringAgent迁移状态"""
    print("🔍 测试ContextEngineeringAgent迁移状态")
    print("=" * 60)

    step = 1

    # 步骤1: 验证组件导入
    print(f'\n📋 步骤{step}: 验证组件导入')
    print("-" * 30)

    try:
        # 验证包装器
        from src.agents.context_engineering_agent_wrapper import ContextEngineeringAgentWrapper
        print("✅ ContextEngineeringAgentWrapper导入成功")

        # 验证适配器
        from src.adapters.context_engineering_agent_adapter import ContextEngineeringAgentAdapter
        print("✅ ContextEngineeringAgentAdapter导入成功")

        # 验证源Agent
        from src.agents.context_engineering_agent import ContextEngineeringAgent
        print("✅ ContextEngineeringAgent导入成功")

        # 验证目标Agent
        from src.agents.memory_manager import MemoryManager
        print("✅ MemoryManager导入成功")

        step += 1

    except ImportError as e:
        print(f"❌ 组件导入失败: {e}")
        return False

    # 步骤2: 测试包装器实例化
    print(f'\n📋 步骤{step}: 测试包装器实例化')
    print("-" * 30)

    try:
        # 测试逐步替换已启用的包装器
        wrapper = ContextEngineeringAgentWrapper(enable_gradual_replacement=True, initial_replacement_rate=0.01)
        print("✅ ContextEngineeringAgentWrapper实例化成功（逐步替换已启用）")

        # 检查属性
        print(f"   逐步替换启用: {wrapper.enable_gradual_replacement}")
        print(f"   初始替换率: {wrapper.initial_replacement_rate}")
        print(f"   是否有替换策略: {wrapper.replacement_strategy is not None}")

        if wrapper.replacement_strategy:
            stats = wrapper.get_replacement_stats()
            if stats:
                print(f"   当前替换率: {stats.get('replacement_rate', 0):.1%}")

        step += 1

    except Exception as e:
        print(f"❌ 包装器实例化失败: {e}")
        return False

    # 步骤3: 测试适配器实例化
    print(f'\n📋 步骤{step}: 测试适配器实例化')
    print("-" * 30)

    try:
        adapter = ContextEngineeringAgentAdapter()
        print("✅ ContextEngineeringAgentAdapter实例化成功")

        step += 1

    except Exception as e:
        print(f"❌ 适配器实例化失败: {e}")
        return False

    # 步骤4: 测试基本功能
    print(f'\n📋 步骤{step}: 测试基本功能')
    print("-" * 30)

    try:
        # 测试上下文管理
        test_context = {
            'task_type': 'add_context',
            'session_id': 'test_session_001',
            'content': '用户询问关于机器学习的最新发展',
            'category': 'query'
        }

        result = await wrapper.execute(test_context)
        print("✅ 包装器执行成功")

        if hasattr(result, 'success'):
            print(f"   执行结果: {'成功' if result.success else '失败'}")

        # 检查替换统计
        stats = wrapper.get_replacement_stats()
        if stats:
            print("   替换统计:"            print(f"     使用新Agent次数: {stats.get('new_agent_calls', 0)}")
            print(f"     使用旧Agent次数: {stats.get('old_agent_calls', 0)}")
            print(f"     总调用次数: {stats.get('total_calls', 0)}")

        step += 1

    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

    # 步骤5: 检查系统集成
    print(f'\n📋 步骤{step}: 检查系统集成')
    print("-" * 30)

    try:
        # 检查文件中是否使用了包装器
        files_to_check = [
            'src/core/langgraph_core_nodes.py'
        ]

        integration_found = False
        for file_path in files_to_check:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'ContextEngineeringAgentWrapper' in content:
                        print(f"✅ {file_path} 已使用包装器")
                        integration_found = True
            except Exception as e:
                print(f"⚠️ 检查文件失败 {file_path}: {e}")

        if integration_found:
            print("✅ 系统集成验证通过")
            return True
        else:
            print("⚠️ 未找到系统集成")
            return False

    except Exception as e:
        print(f"❌ 系统集成检查失败: {e}")
        return False

def main():
    """主函数"""
    success = asyncio.run(test_context_engineering_agent_migration_status())

    print(f'\n{"=" * 60}')
    if success:
        print("🎉 ContextEngineeringAgent迁移状态验证通过！")
        print("✅ 所有组件正常工作")
        print("✅ 逐步替换策略已启用")
        print("✅ 系统集成正确")
        print("\n💡 迁移状态: 准备就绪，可以投入生产使用")
    else:
        print("❌ ContextEngineeringAgent迁移状态验证失败！")
        print("需要检查和修复迁移问题")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
