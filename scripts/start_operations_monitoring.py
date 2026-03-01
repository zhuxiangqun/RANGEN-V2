#!/usr/bin/env python3
"""
运维监控启动脚本
启动完整的运维监控系统
"""

import sys
import os
import signal
import time
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载环境变量')
except ImportError:
    print('⚠️ python-dotenv未安装')

from src.monitoring.operations_monitoring_system import (
    get_operations_monitor,
    start_operations_monitoring,
    stop_operations_monitoring
)

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n📡 收到信号 {signum}，正在停止监控系统...")
    stop_operations_monitoring()
    sys.exit(0)

def main():
    """主函数"""
    print("🚀 启动RANGEN运维监控系统")
    print("=" * 50)

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 获取监控实例
        monitor = get_operations_monitor()

        # 启动监控
        print("📊 初始化监控系统...")
        start_operations_monitoring()

        print("✅ 运维监控系统已启动")
        print("📈 正在收集系统指标...")
        print("🔔 告警系统已激活")
        print("📧 邮件通知已配置"        print("\n按 Ctrl+C 停止监控\n")

        # 显示初始健康报告
        health_report = monitor.get_system_health_report()
        print("🏥 初始系统健康报告:")
        print(f"   健康评分: {health_report['health_score']:.1f}/100")
        print(f"   系统状态: {health_report['status']}")
        print(f"   活跃告警: {health_report['current_metrics']['active_alerts']} 个")

        # 主循环，定期显示状态
        while True:
            time.sleep(60)  # 每分钟显示一次状态

            try:
                health_report = monitor.get_system_health_report()
                metrics = health_report['current_metrics']['metrics']

                print(f"\n📊 [{time.strftime('%H:%M:%S')}] 系统状态:")
                print(".1f"
                print(".1f"
                print(".1f"
                print(f"   活跃告警: {health_report['current_metrics']['active_alerts']}")

                # 显示活跃告警
                if health_report['active_alerts']:
                    print("   🚨 活跃告警:")
                    for alert in health_report['active_alerts'][:3]:  # 只显示前3个
                        print(f"      {alert['severity'].upper()}: {alert['message']}")

                # 显示维护窗口
                if health_report['maintenance_windows']:
                    print("   📅 活跃维护窗口:")
                    for window in health_report['maintenance_windows']:
                        print(f"      {window['name']}: {window['description']}")

            except Exception as e:
                print(f"⚠️ 获取状态信息失败: {e}")

    except KeyboardInterrupt:
        print("\n👋 用户中断，停止监控系统...")
    except Exception as e:
        print(f"❌ 启动监控系统失败: {e}")
        sys.exit(1)
    finally:
        stop_operations_monitoring()

if __name__ == "__main__":
    main()
