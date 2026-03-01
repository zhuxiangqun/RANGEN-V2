#!/usr/bin/env python3
"""
应急回滚系统管理脚本
提供回滚计划创建、执行和监控功能
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.rollback.emergency_rollback_system import (
    get_rollback_system,
    create_rollback_plan,
    execute_emergency_rollback,
    RollbackStrategy,
    RollbackTrigger
)


def print_header():
    """打印头部信息"""
    print("\n" + "="*80)
    print("🛟 应急回滚系统管理")
    print("="*80)


def print_available_strategies():
    """打印可用策略"""
    print("\n📋 回滚策略说明")
    print("-" * 50)

    strategies = [
        ("immediate", "立即回滚", "直接将所有受影响Agent恢复到100%旧版本，风险高但速度快"),
        ("gradual", "渐进回滚", "逐步降低新Agent比例，风险较低但耗时较长"),
        ("selective", "选择性回滚", "只回滚出现问题的Agent，其他Agent保持不变"),
        ("phased", "分阶段回滚", "按优先级分批回滚，平衡风险和速度")
    ]

    for name, desc, details in strategies:
        print(f"• {name}: {desc}")
        print(f"    {details}")


def print_available_triggers():
    """打印可用触发条件"""
    print("\n🚨 触发条件说明")
    print("-" * 50)

    triggers = [
        ("manual", "手动触发", "管理员手动发起回滚"),
        ("performance_degradation", "性能下降", "系统性能下降超过阈值"),
        ("error_rate_spike", "错误率激增", "错误率突然上升"),
        ("system_crash", "系统崩溃", "系统频繁崩溃或无法启动"),
        ("business_impact", "业务影响", "对业务造成严重影响")
    ]

    for name, desc, details in triggers:
        print(f"• {name}: {desc}")
        print(f"    {details}")


async def create_new_plan():
    """创建新回滚计划"""
    print("\n📝 创建回滚计划")
    print("-" * 40)

    # 选择策略
    while True:
        strategy = input("选择回滚策略 (immediate/gradual/selective/phased): ").strip()
        if strategy in ['immediate', 'gradual', 'selective', 'phased']:
            break
        print("❌ 无效策略，请重新选择")

    # 选择触发条件
    while True:
        trigger = input("选择触发条件 (manual/performance_degradation/error_rate_spike/system_crash/business_impact): ").strip()
        if trigger in ['manual', 'performance_degradation', 'error_rate_spike', 'system_crash', 'business_impact']:
            break
        print("❌ 无效触发条件，请重新选择")

    # 输入受影响的Agent
    agents_input = input("输入受影响的Agent (用逗号分隔，留空使用默认全部): ").strip()
    if agents_input:
        affected_agents = [agent.strip() for agent in agents_input.split(',') if agent.strip()]
    else:
        affected_agents = [
            'ChiefAgentWrapper', 'AnswerGenerationAgentWrapper',
            'LearningSystemWrapper', 'StrategicChiefAgentWrapper',
            'PromptEngineeringAgentWrapper', 'ContextEngineeringAgentWrapper',
            'OptimizedKnowledgeRetrievalAgentWrapper'
        ]

    print(f"\n确认计划:")
    print(f"  策略: {strategy}")
    print(f"  触发: {trigger}")
    print(f"  Agent: {', '.join(affected_agents)}")

    confirm = input("\n确认创建? (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # 创建计划
    plan = await create_rollback_plan(strategy, trigger, affected_agents)

    if plan:
        print("✅ 回滚计划创建成功！")
        print(f"  计划ID: {plan.plan_id}")
        print(f"  风险等级: {plan.risk_level}")
        print(f"  预计耗时: {plan.estimated_duration}")
        print(f"  回滚步骤: {len(plan.rollback_steps)}")
    else:
        print("❌ 计划创建失败")


async def execute_plan():
    """执行回滚计划"""
    print("\n⚡ 执行回滚")
    print("-" * 40)

    # 显示可用计划
    system = get_rollback_system()
    available_plans = system.get_available_rollback_plans()

    if not available_plans:
        print("❌ 没有可用的回滚计划")
        return

    print("可用计划:")
    for plan_id, info in available_plans.items():
        print(f"  • {plan_id}: {info['strategy']}策略, 影响{len(info['affected_agents'])}个Agent, 风险{info['risk_level']}")

    plan_id = input("\n输入要执行的计划ID: ").strip()

    if plan_id not in available_plans:
        print("❌ 无效计划ID")
        return

    plan_info = available_plans[plan_id]
    print(f"\n将执行计划: {plan_id}")
    print(f"  策略: {plan_info['strategy']}")
    print(f"  风险: {plan_info['risk_level']}")
    print(".0f")
    print(f"  影响Agent: {len(plan_info['affected_agents'])}")

    confirm = input("\n⚠️  确认执行回滚? 这可能影响系统运行 (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # 执行回滚
    print("\n开始执行回滚...")
    execution = await execute_emergency_rollback("manual", plan_info['affected_agents'])

    if execution:
        print("✅ 回滚执行完成！")
        print(f"  执行ID: {execution.execution_id}")
        print(f"  状态: {execution.status}")
        print(f"  开始时间: {execution.started_at}")
        print(f"  完成时间: {execution.completed_at}")

        if execution.issues_encountered:
            print("⚠️  遇到问题:")
            for issue in execution.issues_encountered:
                print(f"    • {issue}")

        # 显示验证结果
        if execution.verification_results:
            verification = execution.verification_results
            if verification.get('overall_success'):
                print("✅ 验证通过")
            else:
                print("❌ 验证失败")
                if 'issues' in verification:
                    for issue in verification['issues']:
                        print(f"    • {issue}")
    else:
        print("❌ 回滚执行失败")


async def view_plans_and_history():
    """查看计划和历史"""
    print("\n📚 计划和执行历史")
    print("-" * 50)

    system = get_rollback_system()

    # 显示计划
    plans = system.get_available_rollback_plans()
    if plans:
        print("📋 可用回滚计划:")
        for plan_id, info in plans.items():
            print(f"  • {plan_id}")
            print(f"    策略: {info['strategy']}, 风险: {info['risk_level']}")
            print(f"    影响Agent: {len(info['affected_agents'])}")
    else:
        print("📋 暂无回滚计划")

    # 显示执行历史
    history = system.get_execution_history()
    if history:
        print("\n🕐 最近执行记录:")
        for exec_info in history[:5]:  # 显示最近5条
            status_emoji = "✅" if exec_info['status'] == 'completed' else "❌" if exec_info['status'] == 'failed' else "⏳"
            print(f"  {status_emoji} {exec_info['execution_id']} ({exec_info['status']})")
            print(f"    计划: {exec_info['plan_id']}")
            print(f"    时间: {exec_info['started_at'].strftime('%m-%d %H:%M')}")
            if exec_info['issues']:
                print(f"    问题: {len(exec_info['issues'])}个")
    else:
        print("🕐 暂无执行记录")


async def emergency_rollback():
    """应急回滚"""
    print("\n🚨 应急回滚")
    print("-" * 40)
    print("⚠️  这将立即创建并执行应急回滚计划")
    print("   适用于系统出现严重问题的情况")

    # 选择触发原因
    triggers = {
        '1': ('performance_degradation', '性能严重下降'),
        '2': ('error_rate_spike', '错误率激增'),
        '3': ('system_crash', '系统频繁崩溃'),
        '4': ('business_impact', '严重影响业务')
    }

    print("\n选择触发原因:")
    for key, (trigger, desc) in triggers.items():
        print(f"  {key}. {desc}")

    while True:
        choice = input("\n选择 (1-4): ").strip()
        if choice in triggers:
            trigger, desc = triggers[choice]
            break
        print("❌ 无效选择")

    print(f"\n将执行应急回滚: {desc}")

    # 输入问题Agent (可选)
    agents_input = input("输入问题Agent (留空回滚所有Agent): ").strip()
    if agents_input:
        problematic_agents = [agent.strip() for agent in agents_input.split(',') if agent.strip()]
    else:
        problematic_agents = None

    confirm = input(f"\n🔴 确认执行应急回滚? 这将{'回滚所有Agent' if not problematic_agents else f'回滚{len(problematic_agents)}个Agent'} (y/N): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return

    # 执行应急回滚
    print("\n开始应急回滚...")
    execution = await execute_emergency_rollback(trigger, problematic_agents)

    if execution:
        print("✅ 应急回滚完成！")
        print(f"  执行ID: {execution.execution_id}")
        print(f"  状态: {execution.status}")

        if execution.status == 'completed':
            print("🎉 系统已恢复到安全状态")
        else:
            print("⚠️  回滚执行遇到问题，请检查系统状态")

        if execution.issues_encountered:
            print("📋 详细信息:")
            for issue in execution.issues_encountered:
                print(f"  • {issue}")
    else:
        print("❌ 应急回滚失败，请手动处理")


def print_menu():
    """打印菜单"""
    print("\n🎮 操作菜单")
    print("-" * 50)
    print("1. 查看策略和触发条件说明")
    print("2. 创建回滚计划")
    print("3. 执行回滚计划")
    print("4. 查看计划和执行历史")
    print("5. 应急回滚 (紧急情况使用)")
    print("0. 退出")
    print("-" * 50)


async def main():
    """主函数"""
    print_header()

    while True:
        print_menu()

        try:
            choice = input("请选择操作 (0-5): ").strip()

            if choice == "0":
                print("\n👋 再见！")
                break
            elif choice == "1":
                print_available_strategies()
                print_available_triggers()
            elif choice == "2":
                await create_new_plan()
            elif choice == "3":
                await execute_plan()
            elif choice == "4":
                await view_plans_and_history()
            elif choice == "5":
                await emergency_rollback()
            else:
                print("❌ 无效选择，请重新输入")

            input("\n按回车键继续...")

        except (KeyboardInterrupt, EOFError):
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 操作异常: {e}")
            input("\n按回车键继续...")


if __name__ == "__main__":
    asyncio.run(main())
