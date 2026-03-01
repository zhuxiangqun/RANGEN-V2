#!/usr/bin/env python3
"""
启动统一架构监控系统
监控8个核心Agent的运行状态和性能指标
"""

import sys
import os
import time
import argparse
from pathlib import Path
from datetime import datetime

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from src.monitoring.unified_architecture_monitor import get_unified_architecture_monitor


def print_header():
    """打印头部信息"""
    print("\n" + "="*80)
    print("🎯 统一架构监控系统")
    print("="*80)
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"监控对象: 8个核心Agent")
    print("="*80)


def print_status_summary(monitor):
    """打印状态摘要"""
    status = monitor.get_current_status()
    summary = monitor.get_health_summary()

    print(f"\n📊 当前状态摘要")
    print("-" * 40)
    print(f"监控状态: {'🟢 运行中' if status['monitoring_active'] else '🔴 已停止'}")
    print(f"监控间隔: {status['monitoring_interval']}秒")
    print(f"Agent总数: {summary['total_agents']}")
    print(f"健康Agent: {summary['healthy_agents']}")
    print(f"异常Agent: {summary['unhealthy_agents']}")
    print(f"健康率: {summary['health_percentage']:.1f}%")
    print(f"活跃告警: {len(status['active_alerts'])}个")

    # 显示系统指标
    system = status['system_metrics']
    print(f"\n🖥️  系统指标")
    print("-" * 40)
    print(f"CPU使用率: {system.get('cpu_percent', 0):.1f}%")
    print(f"内存使用率: {system.get('memory_percent', 0):.1f}%")
    print(f"磁盘使用率: {system.get('disk_percent', 0):.1f}%")


def print_agent_health_details(monitor):
    """打印Agent健康详情"""
    status = monitor.get_current_status()

    print(f"\n🤖 Agent健康详情")
    print("-" * 40)

    for agent_name, health in status['agent_health'].items():
        status_icon = "🟢" if health['status'] == 'healthy' else "🔴"
        response_time = f"{health['response_time']:.2f}s" if health['response_time'] else "N/A"
        error_info = f" (错误: {health['error_count']})" if health['error_count'] > 0 else ""

        print(f"{status_icon} {agent_name}: {health['status']} | 响应时间: {response_time}{error_info}")

        if health['last_error']:
            print(f"    最后错误: {health['last_error'][:100]}...")


def print_active_alerts(monitor):
    """打印活跃告警"""
    status = monitor.get_current_status()
    alerts = status['active_alerts']

    if not alerts:
        print(f"\n⚠️  活跃告警")
        print("-" * 40)
        print("✅ 暂无活跃告警")
        return

    print(f"\n🚨 活跃告警 ({len(alerts)}个)")
    print("-" * 40)

    for alert in alerts:
        severity_icon = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🔵'
        }.get(alert['severity'], '⚪')

        print(f"{severity_icon} [{alert['type']}] {alert['message']}")
        if 'agent' in alert:
            print(f"    影响Agent: {alert['agent']}")


def interactive_monitoring(monitor, duration_minutes=None):
    """交互式监控"""
    print("\n开始监控... (按 Ctrl+C 停止)")

    start_time = time.time()
    check_count = 0

    try:
        while True:
            check_count += 1
            print(f"\n--- 检查 #{check_count} ---")

            print_status_summary(monitor)
            print_agent_health_details(monitor)
            print_active_alerts(monitor)

            # 检查是否达到指定持续时间
            if duration_minutes and (time.time() - start_time) >= (duration_minutes * 60):
                print(f"\n⏰ 已达到指定监控时长 ({duration_minutes} 分钟)")
                break

            print(f"\n等待下次检查... ({monitor.monitoring_interval}秒)")
            time.sleep(monitor.monitoring_interval)

    except KeyboardInterrupt:
        print("\n\n⚠️  收到中断信号，正在停止监控...")


def export_monitoring_report(monitor, filepath=None):
    """导出监控报告"""
    if not filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"reports/unified_architecture_monitoring_report_{timestamp}.json"

    # 确保reports目录存在
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    monitor.export_monitoring_data(filepath)
    print(f"✅ 监控报告已导出: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="统一架构监控系统")
    parser.add_argument("--duration", type=int, help="监控持续时间(分钟)，不指定则持续运行")
    parser.add_argument("--interval", type=int, default=30, help="监控间隔(秒)，默认30秒")
    parser.add_argument("--export", type=str, help="导出监控报告的文件路径")
    parser.add_argument("--once", action="store_true", help="只执行一次检查后退出")

    args = parser.parse_args()

    print_header()

    # 获取监控实例
    monitor = get_unified_architecture_monitor()
    monitor.monitoring_interval = args.interval

    # 启动监控
    monitor.start_monitoring()

    try:
        if args.once:
            # 只执行一次检查
            time.sleep(2)  # 等待第一次数据收集完成
            print_status_summary(monitor)
            print_agent_health_details(monitor)
            print_active_alerts(monitor)

        elif args.export:
            # 运行一段时间后导出报告
            duration = args.duration or 5  # 默认5分钟
            print(f"开始监控 {duration} 分钟后导出报告...")
            time.sleep(duration * 60)
            export_monitoring_report(monitor, args.export)

        else:
            # 交互式监控
            interactive_monitoring(monitor, args.duration)

        # 导出最终报告（如果没有指定导出路径）
        if not args.export and not args.once:
            export_monitoring_report(monitor)

    except Exception as e:
        print(f"❌ 监控过程中发生错误: {e}")
    finally:
        monitor.stop_monitoring()
        print("\n👋 统一架构监控系统已关闭")


if __name__ == "__main__":
    main()
