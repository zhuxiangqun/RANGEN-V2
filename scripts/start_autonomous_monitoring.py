#!/usr/bin/env python3
"""
启动自主智能监控系统
"""

import sys
import os
import signal
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n🛑 接收到信号 {signum}，正在停止监控系统...")
    if 'monitor' in globals():
        globals()['monitor'].stop_monitoring()
    sys.exit(0)

def main():
    """主函数"""
    print("🚀 启动自主智能监控系统")
    print("=" * 50)

    try:
        # 导入监控系统
        from scripts.autonomous_monitoring_system import AutonomousMonitoringSystem

        # 创建监控实例
        global monitor
        monitor = AutonomousMonitoringSystem()

        # 注册信号处理器
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # 显示配置信息
        print("📋 监控系统配置:")
        config = monitor.monitoring_config
        print(f"   • 检查间隔: {config['check_interval']}秒")
        print(f"   • 优化间隔: {config['optimization_interval']}秒")
        print(f"   • 性能窗口: {config['performance_window']}秒")
        print(f"   • 自动调整: {'启用' if config['auto_adjustment']['enabled'] else '禁用'}")
        print()

        # 启动监控
        monitor.start_monitoring()

        print("✅ 监控系统已启动")
        print("💡 按 Ctrl+C 停止监控系统")
        print("📊 监控数据将自动保存到报告文件中")
        print()

        # 保持运行并显示状态
        while True:
            try:
                status = monitor.get_status()
                if status['active']:
                    checks = status['total_checks']
                    alerts = status['total_alerts']
                    opts = status['total_optimizations']

                    print(f"\r📊 运行中 - 检查: {checks}, 告警: {alerts}, 优化: {opts}", end="", flush=True)
                    time.sleep(10)  # 每10秒更新一次状态显示
                else:
                    break
            except KeyboardInterrupt:
                break

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保所有依赖都已正确安装")
        return 1

    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
