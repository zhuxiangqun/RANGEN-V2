#!/usr/bin/env python3
"""
Agent迁移监控仪表板
提供实时监控状态查看和报告生成功能
"""

import asyncio
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.monitoring.agent_migration_monitoring import (
    get_migration_monitor,
    generate_stability_report,
    get_monitoring_summary
)


def print_header():
    """打印头部信息"""
    print("\n" + "="*80)
    print("🎯 Agent迁移稳定性监控仪表板")
    print("="*80)


def print_summary():
    """打印监控摘要"""
    print("\n📊 监控摘要")
    print("-" * 40)

    summary = get_monitoring_summary()

    print(f"监控状态: {'🟢 运行中' if summary['is_running'] else '🔴 已停止'}")
    print(f"监控间隔: {summary['monitoring_interval']}秒")
    print(f"监控Agent: {len(summary['agents_monitored'])}")
    print(f"生成报告: {summary['total_reports']}")

    if summary['agents_monitored']:
        print("Agent列表:")
        for agent in summary['agents_monitored']:
            print(f"  • {agent}")

    if summary['last_metrics_timestamp']:
        print(f"最后更新: {summary['last_metrics_timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")


async def print_current_metrics():
    """打印当前指标"""
    print("\n📈 当前性能指标")
    print("-" * 40)

    monitor = get_migration_monitor()
    current_metrics = monitor.current_metrics

    if not current_metrics:
        print("暂无监控数据")
        return

    # 表头
    print("<20")
    print("-" * 100)

    for agent_name, metrics in current_metrics.items():
        status = "🟢" if metrics.success_rate > 0.9 else "🟡" if metrics.success_rate > 0.8 else "🔴"

        print("<20"
              "<6.1%"
              "<8.2f"
              "<8.1f"
              "<8.2f")


async def print_stability_report():
    """生成并打印稳定性报告"""
    print("\n📋 稳定性报告")
    print("-" * 40)

    print("正在生成稳定性报告...")
    report = await generate_stability_report()

    if not report:
        print("❌ 生成报告失败")
        return

    print("✅ 报告生成成功")
    print(".1f")
    print(f"监控Agent数量: {report.total_agents_monitored}")
    print(f"有问题的Agent: {report.agents_with_issues}")

    # 显示Agent详情
    print("\nAgent稳定性详情:")
    for agent_name, agent_report in report.agent_reports.items():
        status = "🔴" if agent_report['has_issues'] else "🟢"
        score = agent_report['stability_score']
        metrics = agent_report['current_metrics']

        print(f"  {status} {agent_name}:")
        print(".2f")
        print(".1%")
        print(".2f")
        print(".1f")
        if agent_report['recommendations']:
            print(f"    💡 {agent_report['recommendations'][0]}")

    # 显示建议
    if report.recommendations:
        print("\n💡 系统建议:")
        for rec in report.recommendations:
            print(f"  • {rec}")

    # 显示异常
    if report.anomalies:
        print("\n🚨 检测到异常:")
        for anomaly in report.anomalies:
            print(f"  • [{anomaly['severity'].upper()}] {anomaly['description']}")


def print_menu():
    """打印菜单"""
    print("\n🎮 操作菜单")
    print("-" * 40)
    print("1. 查看监控摘要")
    print("2. 查看当前指标")
    print("3. 生成稳定性报告")
    print("4. 查看历史报告")
    print("5. 启动监控 (如果未启动)")
    print("6. 停止监控")
    print("0. 退出")
    print("-" * 40)


async def view_historical_reports():
    """查看历史报告"""
    print("\n📚 历史报告")
    print("-" * 40)

    monitor = get_migration_monitor()
    reports = monitor.reports

    if not reports:
        print("暂无历史报告")
        return

    print(f"共有 {len(reports)} 个报告:")

    for i, report in enumerate(reports[-5:], 1):  # 显示最近5个
        print(f"{i}. {report.report_id}")
        print(".1f")
        print(f"   Agent数量: {report.total_agents_monitored}, 问题: {report.agents_with_issues}")
        print()

    # 让用户选择查看详情
    if reports:
        try:
            choice = input("选择报告编号查看详情 (回车跳过): ").strip()
            if choice and choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(reports[-5:]):
                    selected_report = reports[-5:][idx]
                    print(f"\n详细报告: {selected_report.report_id}")
                    print(json.dumps({
                        'stability_score': selected_report.overall_stability_score,
                        'agents_with_issues': selected_report.agents_with_issues,
                        'recommendations': selected_report.recommendations,
                        'anomalies': [
                            {
                                'type': a['type'],
                                'agent': a['agent'],
                                'description': a['description'],
                                'severity': a['severity']
                            }
                            for a in selected_report.anomalies
                        ]
                    }, ensure_ascii=False, indent=2))
        except (ValueError, EOFError):
            pass


async def start_monitoring_if_needed():
    """如果需要，启动监控"""
    summary = get_monitoring_summary()

    if not summary['is_running']:
        print("监控未启动，正在启动...")
        from src.monitoring.agent_migration_monitoring import start_migration_monitoring
        await start_migration_monitoring()
        print("✅ 监控已启动")
    else:
        print("监控已在运行中")


def stop_monitoring():
    """停止监控"""
    from src.monitoring.agent_migration_monitoring import stop_migration_monitoring
    stop_migration_monitoring()
    print("✅ 监控已停止")


async def main():
    """主函数"""
    print_header()

    while True:
        print_summary()
        print_menu()

        try:
            choice = input("请选择操作 (0-6): ").strip()

            if choice == "0":
                print("\n👋 再见！")
                break
            elif choice == "1":
                # 摘要已在循环开始时显示
                pass
            elif choice == "2":
                await print_current_metrics()
            elif choice == "3":
                await print_stability_report()
            elif choice == "4":
                await view_historical_reports()
            elif choice == "5":
                await start_monitoring_if_needed()
            elif choice == "6":
                stop_monitoring()
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
