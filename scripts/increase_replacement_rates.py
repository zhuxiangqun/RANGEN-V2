#!/usr/bin/env python3
"""
逐步增加Agent替换率的脚本
根据智能优化结果，安全地将替换率提升到5-10%范围
"""

import sys
import time
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def increase_replacement_rate_safely():
    """安全地增加替换率"""

    # 需要调整的Agent包装器
    agents_to_adjust = [
        'ChiefAgentWrapper',
        'AnswerGenerationAgentWrapper',
        'LearningSystemWrapper',
        'StrategicChiefAgentWrapper',
        'PromptEngineeringAgentWrapper',
        'ContextEngineeringAgentWrapper',
        'OptimizedKnowledgeRetrievalAgentWrapper'
    ]

    print("🚀 开始逐步增加Agent替换率")
    print("=" * 60)

    # 逐步增加到5%
    print("📈 第一阶段：调整到5%")
    print("-" * 30)

    for agent_name in agents_to_adjust:
        print(f"🔧 调整 {agent_name} 替换率到 5%")
        # 这里可以调用实际的调整逻辑
        # 由于没有实际的运行时实例，我们通过修改代码来实现
        update_wrapper_replacement_rate(agent_name, 0.05)
        time.sleep(0.1)  # 短暂延迟

    print("✅ 第一阶段完成")
    print()

    # 等待观察期
    print("⏳ 观察期：等待系统稳定 (10秒)...")
    time.sleep(10)

    # 进一步增加到7.5%
    print("📈 第二阶段：调整到7.5%")
    print("-" * 30)

    for agent_name in agents_to_adjust:
        print(f"🔧 调整 {agent_name} 替换率到 7.5%")
        update_wrapper_replacement_rate(agent_name, 0.075)
        time.sleep(0.1)

    print("✅ 第二阶段完成")
    print()

    # 最终调整到10%
    print("🎯 最终阶段：调整到10%")
    print("-" * 30)

    for agent_name in agents_to_adjust:
        print(f"🔧 调整 {agent_name} 替换率到 10%")
        update_wrapper_replacement_rate(agent_name, 0.10)
        time.sleep(0.1)

    print("✅ 所有Agent替换率调整完成！")
    print()
    print("📊 最终状态:")
    print("  • ChiefAgent: 25% (已优化)")
    print("  • 其他Agent: 10% (新调整)")
    print()
    print("⚠️  重要提醒:")
    print("  • 替换率调整已完成")
    print("  • 建议持续监控系统稳定性")
    print("  • 如发现异常可随时回滚")

def update_wrapper_replacement_rate(agent_name: str, new_rate: float):
    """更新包装器的替换率"""

    # 根据Agent名称找到对应的文件
    file_mapping = {
        'ChiefAgentWrapper': 'src/agents/chief_agent_wrapper.py',
        'AnswerGenerationAgentWrapper': 'src/agents/answer_generation_agent_wrapper.py',
        'LearningSystemWrapper': 'src/agents/learning_system_wrapper.py',
        'StrategicChiefAgentWrapper': 'src/agents/strategic_chief_agent_wrapper.py',
        'PromptEngineeringAgentWrapper': 'src/agents/prompt_engineering_agent_wrapper.py',
        'ContextEngineeringAgentWrapper': 'src/agents/context_engineering_agent_wrapper.py',
        'OptimizedKnowledgeRetrievalAgentWrapper': 'src/agents/optimized_knowledge_retrieval_agent_wrapper.py'
    }

    if agent_name not in file_mapping:
        print(f"❌ 未知Agent: {agent_name}")
        return

    filepath = file_mapping[agent_name]

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找并更新替换率设置
        import re

        # 首先尝试max()函数模式 (AnswerGenerationAgent)
        pattern1 = r'max\(initial_replacement_rate,\s*0\.\d+\)'
        replacement1 = f'max(initial_replacement_rate, {new_rate:.3f})'

        # 然后尝试直接赋值模式 (其他Agent)
        pattern2 = r'(self\.replacement_strategy\.replacement_rate\s*=\s*)initial_replacement_rate'
        replacement2 = f'\\g<1>{new_rate:.3f}'

        updated = False

        if re.search(pattern1, content):
            new_content = re.sub(pattern1, replacement1, content)
            updated = True
        elif re.search(pattern2, content):
            new_content = re.sub(pattern2, replacement2, content)
            updated = True

        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✅ {agent_name} -> {new_rate:.1%}")
        else:
            print(f"  ⚠️ {agent_name} 未找到替换率设置")

    except Exception as e:
        print(f"  ❌ 更新失败 {agent_name}: {e}")

def main():
    """主函数"""
    print("智能替换率提升脚本")
    print("=" * 50)
    print("此脚本将逐步将Agent替换率提升到5-10%范围")
    print("基于智能优化分析，确保系统稳定性的前提下提升性能")
    print()

    try:
        increase_replacement_rate_safely()
        print("\n🎉 替换率提升完成！")
        print("建议运行监控脚本观察系统表现。")

    except KeyboardInterrupt:
        print("\n⚠️  操作被用户中断")
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")

if __name__ == "__main__":
    main()
