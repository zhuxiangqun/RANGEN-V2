#!/usr/bin/env python3
"""
强制清理端口冲突的工具
"""

import os
import subprocess
import sys
import time
import signal

def run_command(cmd, shell=True, capture_output=True, text=True):
    """运行系统命令"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, capture_output=capture_output, text=text)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=shell)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def find_processes_on_port(port):
    """查找占用指定端口的所有进程"""
    # 使用 lsof 查找进程
    success, stdout, stderr = run_command(f"lsof -i :{port}")
    processes = []

    if success and stdout:
        lines = stdout.strip().split('\n')
        if len(lines) > 1:  # 第一行是标题
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    process_name = parts[0] if len(parts) > 0 else "unknown"
                    processes.append((pid, process_name))

    # 也使用 netstat 确认
    success2, stdout2, stderr2 = run_command(f"netstat -tlnp | grep :{port}")
    if success2 and stdout2:
        for line in stdout2.strip().split('\n'):
            if f":{port} " in line:
                parts = line.split()
                if len(parts) >= 6:
                    pid_program = parts[6]
                    if '/' in pid_program:
                        pid, program = pid_program.split('/', 1)
                        processes.append((pid, program))

    # 去重
    unique_processes = []
    seen_pids = set()
    for pid, name in processes:
        if pid not in seen_pids:
            unique_processes.append((pid, name))
            seen_pids.add(pid)

    return unique_processes

def kill_process_forcefully(pid):
    """强制杀死进程"""
    print(f"🔪 强制终止进程 PID: {pid}...")

    # 首先尝试正常终止
    try:
        os.kill(int(pid), signal.SIGTERM)
        time.sleep(1)
    except:
        pass

    # 检查是否还活着
    success, stdout, stderr = run_command(f"ps -p {pid}")
    if success:
        print(f"⚠️ 进程 {pid} 仍在运行，尝试强制终止...")
        # 强制终止
        try:
            os.kill(int(pid), signal.SIGKILL)
            time.sleep(1)
        except:
            pass

        # 最后检查
        success2, stdout2, stderr2 = run_command(f"ps -p {pid}")
        if success2:
            print(f"❌ 无法终止进程 {pid}")
            return False
        else:
            print(f"✅ 进程 {pid} 已终止")
            return True
    else:
        print(f"✅ 进程 {pid} 已终止")
        return True

def cleanup_ports(ports):
    """清理指定端口"""
    print("🔧 强制清理端口冲突...")
    print("=" * 50)

    all_cleaned = True

    for port in ports:
        print(f"\n🔍 检查端口 {port}:")

        processes = find_processes_on_port(port)
        if processes:
            print(f"❌ 端口 {port} 被以下进程占用:")
            for pid, name in processes:
                print(f"   - PID: {pid}, 进程: {name}")

            # 终止所有相关进程
            for pid, name in processes:
                if kill_process_forcefully(pid):
                    print(f"   ✅ 清理完成: {name} (PID: {pid})")
                else:
                    print(f"   ❌ 清理失败: {name} (PID: {pid})")
                    all_cleaned = False

            # 再次检查端口
            time.sleep(2)
            final_processes = find_processes_on_port(port)
            if final_processes:
                print(f"⚠️ 端口 {port} 仍有进程占用:")
                for pid, name in final_processes:
                    print(f"   - PID: {pid}, 进程: {name}")
                all_cleaned = False
            else:
                print(f"✅ 端口 {port} 已清理完成")
        else:
            print(f"✅ 端口 {port} 未被占用")

    return all_cleaned

def main():
    print("💪 强制端口清理工具")
    print("=" * 50)

    # 默认清理常用端口
    default_ports = [8080, 8081, 8082, 8083, 9000, 9001]

    if len(sys.argv) > 1:
        try:
            ports = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            print("❌ 无效的端口号")
            sys.exit(1)
    else:
        ports = default_ports
        print(f"🎯 将清理默认端口: {ports}")
        response = input("是否继续？(Y/n): ").lower().strip()
        if response in ['n', 'no']:
            print("❌ 操作已取消")
            sys.exit(0)

    if cleanup_ports(ports):
        print("\n✅ 所有端口清理完成！")
        print("\n🚀 现在可以启动服务器:")
        available_port = min(ports) if ports else 8080
        print(f"   python scripts/start_unified_server.py --port {available_port}")
        print(f"   # 或使用快速启动脚本:")
        print(f"   ./scripts/quick_start_server.sh {available_port}")
    else:
        print("\n⚠️ 某些端口清理失败")
        print("💡 建议:")
        print("1. 手动检查和终止进程: ps aux | grep python")
        print("2. 使用其他端口启动")
        print("3. 重启系统（最后手段）")

if __name__ == "__main__":
    main()
