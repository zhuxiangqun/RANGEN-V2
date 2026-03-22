#!/usr/bin/env python3
"""
快速系统稳定性检查
检查Agent迁移后的系统稳定性
"""

import sys
import time
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_agent_stability():
    """检查Agent稳定性"""
    print("🔍 开始系统稳定性检查")
    print("=" * 50)

    agents_to_check = [
        'AnswerGenerationAgentWrapper',
        'LearningSystemWrapper',
        'StrategicChiefAgentWrapper',
        'PromptEngineeringAgentWrapper',
        'ContextEngineeringAgentWrapper',
        'OptimizedKnowledgeRetrievalAgentWrapper'
    ]

    stability_results = {}

    for agent_name in agents_to_check:
        print(f"\n🤖 检查 {agent_name}...")
        try:
            # 尝试导入和实例化Agent
            if agent_name == 'AnswerGenerationAgentWrapper':
                from src.agents.answer_generation_agent_wrapper import AnswerGenerationAgentWrapper
                agent = AnswerGenerationAgentWrapper(enable_gradual_replacement=False)  # 禁用逐步替换以简化测试
            elif agent_name == 'LearningSystemWrapper':
                from src.agents.learning_system_wrapper import LearningSystemWrapper
                agent = LearningSystemWrapper(enable_gradual_replacement=False)
            elif agent_name == 'StrategicChiefAgentWrapper':
                from src.agents.strategic_chief_agent_wrapper import StrategicChiefAgentWrapper
                agent = StrategicChiefAgentWrapper(enable_gradual_replacement=False)
            elif agent_name == 'PromptEngineeringAgentWrapper':
                from src.agents.prompt_engineering_agent_wrapper import PromptEngineeringAgentWrapper
                agent = PromptEngineeringAgentWrapper(enable_gradual_replacement=False)
            elif agent_name == 'ContextEngineeringAgentWrapper':
                from src.agents.context_engineering_agent_wrapper import ContextEngineeringAgentWrapper
                agent = ContextEngineeringAgentWrapper(enable_gradual_replacement=False)
            elif agent_name == 'OptimizedKnowledgeRetrievalAgentWrapper':
                from src.agents.optimized_knowledge_retrieval_agent_wrapper import OptimizedKnowledgeRetrievalAgentWrapper
                agent = OptimizedKnowledgeRetrievalAgentWrapper(enable_gradual_replacement=False)

            # 检查初始化是否成功
            print(f"  ✅ {agent_name} 初始化成功")
            stability_results[agent_name] = "✅ 稳定"

        except Exception as e:
            print(f"  ❌ {agent_name} 初始化失败: {str(e)[:100]}")
            stability_results[agent_name] = f"❌ 异常: {str(e)[:50]}"

    print(f"\n📊 稳定性检查结果")
    print("-" * 30)

    stable_count = 0
    total_count = len(agents_to_check)

    for agent_name, status in stability_results.items():
        print(f"{agent_name}: {status}")
        if status.startswith("✅"):
            stable_count += 1

    print(f"\n🎯 总体评估")
    print(f"稳定Agent: {stable_count}/{total_count}")
    stability_rate = stable_count / total_count * 100
    print(".1f")
    if stable_count == total_count:
        print("✅ 系统稳定性良好，所有Agent正常工作")
        return True
    elif stable_count >= total_count * 0.8:
        print("⚠️ 系统稳定性一般，部分Agent存在问题")
        return True
    else:
        print("❌ 系统稳定性差，大多数Agent存在问题")
        return False

def check_replacement_rates():
    """检查替换率设置"""
    print(f"\n🔄 检查Agent替换率设置")
    print("-" * 30)

    wrapper_files = [
        'src/agents/answer_generation_agent_wrapper.py',
        'src/agents/learning_system_wrapper.py',
        'src/agents/strategic_chief_agent_wrapper.py',
        'src/agents/prompt_engineering_agent_wrapper.py',
        'src/agents/context_engineering_agent_wrapper.py',
        'src/agents/optimized_knowledge_retrieval_agent_wrapper.py'
    ]

    for filepath in wrapper_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找替换率设置
            import re
            match = re.search(r'replacement_rate = (0\.\d+)', content)
            if match:
                rate = float(match.group(1))
                agent_name = Path(filepath).stem.replace('_agent_wrapper', '').replace('_', ' ').title()
                print(f"  {agent_name}: {rate:.1%}")        except Exception as e:
            print(f"❌ 检查 {filepath} 失败: {e}")

def main():
    """主函数"""
    print("系统稳定性检查报告")
    print("=" * 60)
    print(f"检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查Agent稳定性
    stability_ok = check_agent_stability()

    # 检查替换率设置
    check_replacement_rates()

    # 生成总结
    print(f"\n{'='*60}")
    print("📋 检查总结")

    if stability_ok:
        print("✅ 系统稳定性检查通过")
        print("💡 建议:")
        print("  • 继续监控系统运行状态")
        print("  • 定期检查Agent性能指标")
        print("  • 关注替换率调整效果")
    else:
        print("❌ 系统稳定性检查失败")
        print("💡 建议:")
        print("  • 检查Agent初始化问题")
        print("  • 验证依赖关系是否正确")
        print("  • 查看详细错误日志")

    print("\n🔍 检查完成")

if __name__ == "__main__":
    main()
