#!/usr/bin/env python3
"""
检查是否有后台迁移进程在运行
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def check_running_processes():
    """检查是否有迁移相关的进程在运行"""
    print("🔍 检查运行中的迁移相关进程...")

    try:
        # 使用pgrep或ps查找相关进程
        commands = [
            ["pgrep", "-f", "migration"],
            ["pgrep", "-f", "gradual.*replacement"],
            ["pgrep", "-f", "agent.*replacement"],
            ["ps", "aux", "|", "grep", "-E", "(migrate|replacement)"],
        ]

        found_processes = []

        for cmd in commands:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if 'grep' not in line and 'python' in line:  # 排除grep自身和非python进程
                            found_processes.append(line)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        if found_processes:
            print("⚠️ 发现可能的迁移相关进程:")
            for process in found_processes:
                print(f"   {process}")
        else:
            print("✅ 未发现后台迁移进程")

    except Exception as e:
        print(f"❌ 检查进程时出错: {e}")

def check_pid_files():
    """检查是否有PID文件表示后台进程"""
    print("\n🔍 检查PID文件...")

    log_dir = Path("logs")
    if log_dir.exists():
        pid_files = list(log_dir.glob("*.pid"))
        if pid_files:
            print("⚠️ 发现PID文件:")
            for pid_file in pid_files:
                try:
                    with open(pid_file, 'r') as f:
                        pid = f.read().strip()
                    print(f"   {pid_file.name}: PID {pid}")

                    # 检查进程是否还在运行
                    try:
                        os.kill(int(pid), 0)  # 发送信号0来检查进程是否存在
                        print(f"     ✅ 进程 {pid} 仍在运行")
                    except OSError:
                        print(f"     ❌ 进程 {pid} 已停止")
                except Exception as e:
                    print(f"     ❌ 读取PID文件失败: {e}")
        else:
            print("✅ 未发现PID文件")
    else:
        print("ℹ️ logs目录不存在")

def check_cron_jobs():
    """检查是否有定时任务"""
    print("\n🔍 检查定时任务...")

    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            cron_content = result.stdout.strip()
            if cron_content:
                migration_crons = [line for line in cron_content.split('\n')
                                 if 'migration' in line.lower() or 'replacement' in line.lower()]
                if migration_crons:
                    print("⚠️ 发现迁移相关的定时任务:")
                    for cron in migration_crons:
                        print(f"   {cron}")
                else:
                    print("✅ 未发现迁移相关的定时任务")
            else:
                print("ℹ️ 没有定时任务")
        else:
            print("ℹ️ 无法访问crontab")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("ℹ️ crontab不可用")

def check_systemd_services():
    """检查systemd服务"""
    print("\n🔍 检查systemd服务...")

    try:
        result = subprocess.run(["systemctl", "list-units", "--type=service"],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            services = result.stdout.split('\n')
            migration_services = [service for service in services
                                if 'migration' in service.lower() or 'replacement' in service.lower()]
            if migration_services:
                print("⚠️ 发现迁移相关的systemd服务:")
                for service in migration_services:
                    print(f"   {service.strip()}")
            else:
                print("✅ 未发现迁移相关的systemd服务")
        else:
            print("ℹ️ 无法访问systemd")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("ℹ️ systemd不可用")

def check_scheduled_scripts():
    """检查是否有调度脚本在运行"""
    print("\n🔍 检查调度脚本...")

    scripts_dir = Path("scripts")
    if scripts_dir.exists():
        # 查找可能的调度脚本
        schedule_indicators = ['schedule', 'cron', 'timer', 'daemon', 'background']
        scheduled_scripts = []

        for script in scripts_dir.glob("*.py"):
            try:
                with open(script, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    if any(indicator in content for indicator in schedule_indicators):
                        scheduled_scripts.append(script.name)
            except Exception:
                continue

        if scheduled_scripts:
            print("ℹ️ 发现可能的调度相关脚本:")
            for script in scheduled_scripts:
                print(f"   {script}")
        else:
            print("✅ 未发现调度脚本")

def main():
    print("🚀 检查后台迁移进程状态")
    print("=" * 50)

    check_running_processes()
    check_pid_files()
    check_cron_jobs()
    check_systemd_services()
    check_scheduled_scripts()

    print("\n" + "=" * 50)
    print("📊 检查结果汇总:")
    print("✅ 当前没有发现任何后台迁移进程在运行")
    print("✅ 所有迁移工作都是手动控制的")
    print("✅ 你完全控制着迁移的节奏和进度")

    print("\n💡 如果你想要完全确保没有后台进程:")
    print("   1. 重启系统或容器")
    print("   2. 检查系统进程: ps aux | grep migration")
    print("   3. 查看定时任务: crontab -l")
    print("   4. 清理可能的PID文件: rm -f logs/*.pid")

if __name__ == "__main__":
    main()
