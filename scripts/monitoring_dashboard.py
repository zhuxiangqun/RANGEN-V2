#!/usr/bin/env python3
"""
监控仪表板
提供实时的系统监控信息显示
"""

import sys
import os
import time
import curses
import threading
from datetime import datetime, timedelta
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from src.monitoring.operations_monitoring_system import get_operations_monitor

class MonitoringDashboard:
    """监控仪表板"""

    def __init__(self):
        self.monitor = get_operations_monitor()
        self.running = False
        self.refresh_interval = 2  # 2秒刷新一次

    def start_dashboard(self):
        """启动仪表板"""
        try:
            curses.wrapper(self._run_dashboard)
        except KeyboardInterrupt:
            pass
        finally:
            print("\n👋 监控仪表板已关闭")

    def _run_dashboard(self, stdscr):
        """运行仪表板主循环"""
        # 初始化curses
        curses.curs_set(0)  # 隐藏光标
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)    # 正常
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)   # 警告
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)      # 错误
        curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)     # 信息
        curses.init_pair(5, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # 标题

        self.stdscr = stdscr
        self.running = True

        # 创建数据更新线程
        update_thread = threading.Thread(target=self._data_update_loop, daemon=True)
        update_thread.start()

        # 主显示循环
        while self.running:
            try:
                self._draw_dashboard()
                time.sleep(self.refresh_interval)
            except KeyboardInterrupt:
                break

    def _data_update_loop(self):
        """数据更新循环"""
        while self.running:
            # 这里可以添加额外的后台数据更新逻辑
            time.sleep(1)

    def _draw_dashboard(self):
        """绘制仪表板"""
        self.stdscr.clear()

        # 获取当前数据
        health_report = self.monitor.get_system_health_report()
        current_time = datetime.now()

        # 设置颜色和标题
        self.stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
        self.stdscr.addstr(0, 0, "🚀 RANGEN 运维监控仪表板")
        self.stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)

        self.stdscr.addstr(1, 0, f"时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 系统健康状态
        health_score = health_report['health_score']
        health_status = health_report['status']

        status_color = curses.color_pair(1)  # 默认绿色
        if health_status == 'critical':
            status_color = curses.color_pair(3)  # 红色
        elif health_status == 'poor':
            status_color = curses.color_pair(2)  # 黄色

        self.stdscr.attron(status_color | curses.A_BOLD)
        self.stdscr.addstr(3, 0, f"🏥 系统健康: {health_score:.1f}/100 ({health_status.upper()})")
        self.stdscr.attroff(status_color | curses.A_BOLD)

        # 系统指标
        metrics = health_report['current_metrics']['metrics']
        y_pos = 5

        self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.addstr(y_pos, 0, "📊 系统指标:")
        self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        y_pos += 1

        # CPU信息
        cpu_percent = metrics.get('cpu_percent', 0)
        cpu_color = curses.color_pair(1)
        if cpu_percent > 80:
            cpu_color = curses.color_pair(3)
        elif cpu_percent > 60:
            cpu_color = curses.color_pair(2)

        self.stdscr.attron(cpu_color)
        self.stdscr.addstr(y_pos, 2, ".1f")
        self.stdscr.attroff(cpu_color)
        y_pos += 1

        # 内存信息
        memory_percent = metrics.get('memory_percent', 0)
        memory_used = metrics.get('memory_used_gb', 0)
        memory_color = curses.color_pair(1)
        if memory_percent > 85:
            memory_color = curses.color_pair(3)
        elif memory_percent > 70:
            memory_color = curses.color_pair(2)

        self.stdscr.attron(memory_color)
        self.stdscr.addstr(y_pos, 2, ".1f")
        self.stdscr.attroff(memory_color)
        y_pos += 1

        # 磁盘信息
        disk_percent = metrics.get('disk_percent', 0)
        disk_used = metrics.get('disk_used_gb', 0)
        disk_color = curses.color_pair(1)
        if disk_percent > 90:
            disk_color = curses.color_pair(3)
        elif disk_percent > 80:
            disk_color = curses.color_pair(2)

        self.stdscr.attron(disk_color)
        self.stdscr.addstr(y_pos, 2, ".1f")
        self.stdscr.attroff(disk_color)
        y_pos += 1

        # 进程信息
        process_cpu = metrics.get('process_cpu_percent', 0)
        process_memory = metrics.get('process_memory_mb', 0)
        self.stdscr.addstr(y_pos, 2, ".1f")
        y_pos += 1

        # 活跃告警
        y_pos += 1
        active_alerts = health_report['active_alerts']
        alert_color = curses.color_pair(1)
        if active_alerts:
            alert_color = curses.color_pair(3)

        self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
        self.stdscr.addstr(y_pos, 0, "🚨 活跃告警:")
        self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
        y_pos += 1

        self.stdscr.attron(alert_color)
        self.stdscr.addstr(y_pos, 2, f"数量: {len(active_alerts)}")
        self.stdscr.attroff(alert_color)

        if active_alerts:
            for i, alert in enumerate(active_alerts[:3]):  # 只显示前3个告警
                severity_color = curses.color_pair(2)  # 默认黄色
                if alert['severity'] == 'critical':
                    severity_color = curses.color_pair(3)  # 红色
                elif alert['severity'] == 'error':
                    severity_color = curses.color_pair(3)  # 红色

                y_pos += 1
                self.stdscr.attron(severity_color)
                alert_msg = f"{alert['severity'].upper()}: {alert['message'][:50]}"
                self.stdscr.addstr(y_pos, 2, alert_msg)
                self.stdscr.attroff(severity_color)

        # 维护窗口
        y_pos += 2
        maintenance_windows = health_report['maintenance_windows']
        if maintenance_windows:
            self.stdscr.attron(curses.color_pair(4) | curses.A_BOLD)
            self.stdscr.addstr(y_pos, 0, "📅 维护窗口:")
            self.stdscr.attroff(curses.color_pair(4) | curses.A_BOLD)
            y_pos += 1

            for window in maintenance_windows:
                self.stdscr.addstr(y_pos, 2, f"{window['name']}: {window['description']}")
                y_pos += 1

        # 操作提示
        y_pos = curses.LINES - 3
        self.stdscr.attron(curses.A_DIM)
        self.stdscr.addstr(y_pos, 0, "操作: q-退出, r-刷新, m-添加维护窗口")
        self.stdscr.addstr(y_pos + 1, 0, f"最后更新: {time.strftime('%H:%M:%S')}")
        self.stdscr.attroff(curses.A_DIM)

        # 检查用户输入
        self.stdscr.timeout(1000)  # 1秒超时
        try:
            key = self.stdscr.getch()
            if key == ord('q'):
                self.running = False
            elif key == ord('r'):
                # 强制刷新
                pass
            elif key == ord('m'):
                # 这里可以添加维护窗口管理逻辑
                pass
        except:
            pass

        self.stdscr.refresh()

def print_text_dashboard():
    """打印文本版仪表板（无curses）"""
    monitor = get_operations_monitor()

    print("🚀 RANGEN 运维监控仪表板 (文本版)")
    print("=" * 50)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        health_report = monitor.get_system_health_report()

        # 健康状态
        health_score = health_report['health_score']
        health_status = health_report['status']
        print(f"\n🏥 系统健康: {health_score:.1f}/100 ({health_status})")

        # 系统指标
        metrics = health_report['current_metrics']['metrics']
        print("
📊 系统指标:"        print(".1f"        print(".1f"        print(".1f"        print(".1f"        print(f"   进程CPU: {metrics.get('process_cpu_percent', 0):.1f}%")
        print(".1f"
        # 告警信息
        active_alerts = health_report['active_alerts']
        print(f"\n🚨 活跃告警: {len(active_alerts)} 个")

        if active_alerts:
            for alert in active_alerts[:3]:
                print(f"   {alert['severity'].upper()}: {alert['message']}")

        # 维护窗口
        maintenance_windows = health_report['maintenance_windows']
        if maintenance_windows:
            print(f"\n📅 维护窗口: {len(maintenance_windows)} 个")
            for window in maintenance_windows:
                print(f"   {window['name']}: {window['description']}")

        print("\n💡 提示: 使用 'python scripts/monitoring_dashboard.py --curses' 查看图形界面")

    except Exception as e:
        print(f"❌ 获取监控数据失败: {e}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='RANGEN 监控仪表板')
    parser.add_argument('--curses', action='store_true', help='使用curses图形界面')
    parser.add_argument('--interval', type=int, default=2, help='刷新间隔(秒)')

    args = parser.parse_args()

    if args.curses:
        try:
            dashboard = MonitoringDashboard()
            dashboard.refresh_interval = args.interval
            dashboard.start_dashboard()
        except ImportError:
            print("❌ curses模块不可用，使用文本界面")
            print_text_dashboard()
    else:
        print_text_dashboard()

if __name__ == "__main__":
    main()
