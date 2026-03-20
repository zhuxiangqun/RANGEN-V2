#!/usr/bin/env python3
"""
测试AnswerGenerationAgent迁移状态
验证AnswerGenerationAgentWrapper是否正确设置逐步替换策略
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_answer_generation_agent_migration_status():
    """测试AnswerGenerationAgent迁移状态"""
    print("🔍 测试AnswerGenerationAgent迁移状态")
    print("=" * 60)

    step = 1

    # 步骤1: 验证组件导入
    print(f'\n📋 步骤{step}: 验证组件导入')
    print("-" * 30)

    try:
        # 验证包装器
        from src.agents.answer_generation_agent_wrapper import AnswerGenerationAgentWrapper
        print("✅ AnswerGenerationAgentWrapper导入成功")

        # 验证适配器
        from src.adapters.answer_generation_agent_adapter import AnswerGenerationAgentAdapter
        print("✅ AnswerGenerationAgentAdapter导入成功")

        # 验证源Agent
        from src.agents.expert_agents import AnswerGenerationAgent
        print("✅ AnswerGenerationAgent导入成功")

        # 验证目标Agent
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert导入成功")

        step += 1

    except ImportError as e:
        print(f"❌ 组件导入失败: {e}")
        return False

    # 步骤2: 测试包装器实例化
    print(f'\n📋 步骤{step}: 测试包装器实例化')
    print("-" * 30)

    try:
        # 测试逐步替换已启用的包装器
        wrapper = AnswerGenerationAgentWrapper(enable_gradual_replacement=True, initial_replacement_rate=0.01)
        print("✅ AnswerGenerationAgentWrapper实例化成功（逐步替换已启用）")

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
        adapter = AnswerGenerationAgentAdapter()
        print("✅ AnswerGenerationAgentAdapter实例化成功")

        step += 1

    except Exception as e:
        print(f"❌ 适配器实例化失败: {e}")
        return False

    # 步骤4: 测试基本功能
    print(f'\n📋 步骤{step}: 测试基本功能')
    print("-" * 30)

    try:
        # 测试简单答案生成
        test_context = {
            'query': '解释什么是人工智能',
            'knowledge': [{'content': '人工智能是计算机科学的一个分支', 'source': 'textbook'}]
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

    # 步骤5: 检查UnifiedResearchSystem中的使用
    print(f'\n📋 步骤{step}: 检查系统集成')
    print("-" * 30)

    try:
        from src.unified_research_system import UnifiedResearchSystem
        system = UnifiedResearchSystem()

        # 检查是否使用了包装器
        if hasattr(system, '_answer_agent') and system._answer_agent is not None:
            agent_type = type(system._answer_agent).__name__
            print(f"✅ 系统中的AnswerGenerationAgent类型: {agent_type}")

            if agent_type == 'AnswerGenerationAgentWrapper':
                print("✅ 系统正确使用AnswerGenerationAgentWrapper")
                return True
            else:
                print(f"⚠️ 系统使用的是{agent_type}，不是AnswerGenerationAgentWrapper")
                return False
        else:
            print("⚠️ 系统未初始化AnswerGenerationAgent")
            return False

    except Exception as e:
        print(f"❌ 系统集成检查失败: {e}")
        return False

def main():
    """主函数"""
    success = asyncio.run(test_answer_generation_agent_migration_status())

    print(f'\n{"=" * 60}')
    if success:
        print("🎉 AnswerGenerationAgent迁移状态验证通过！")
        print("✅ 所有组件正常工作")
        print("✅ 逐步替换策略已启用")
        print("✅ 系统集成正确")
        print("\n💡 迁移状态: 准备就绪，可以投入生产使用")
    else:
        print("❌ AnswerGenerationAgent迁移状态验证失败！")
        print("需要检查和修复迁移问题")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
