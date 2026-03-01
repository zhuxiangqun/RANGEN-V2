#!/usr/bin/env python3
"""
端口诊断工具 - 快速检查端口状态
"""

import socket
import subprocess
import sys

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

def check_port_processes(port):
    """检查端口的进程占用"""
    processes = []

    # 使用 lsof
    success, stdout, stderr = run_command(f"lsof -i :{port}")
    if success and stdout:
        lines = stdout.strip().split('\n')
        if len(lines) > 1:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    process_name = parts[0] if len(parts) > 0 else "unknown"
                    processes.append((pid, process_name))

    return processes

def test_port_binding(port):
    """测试端口绑定能力"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            s.listen(1)
            return True
    except OSError:
        return False

def diagnose_port(port):
    """诊断单个端口"""
    print(f"\n🔍 诊断端口 {port}:")

    # 检查进程占用
    processes = check_port_processes(port)
    if processes:
        print(f"  ❌ 被进程占用:")
        for pid, name in processes:
            print(f"     - PID: {pid}, 进程: {name}")
        return False
    else:
        print("  ✅ 无进程占用")

    # 测试绑定能力
    if test_port_binding(port):
        print("  ✅ 可以绑定")
        return True
    else:
        print("  ❌ 无法绑定")
        return False

def main():
    print("🔧 RANGEN 端口诊断工具")
    print("=" * 40)

    ports_to_check = [8080, 8081, 9000, 9001]

    if len(sys.argv) > 1:
        try:
            ports_to_check = [int(arg) for arg in sys.argv[1:]]
        except ValueError:
            print("❌ 无效的端口号")
            sys.exit(1)

    all_good = True
    for port in ports_to_check:
        if not diagnose_port(port):
            all_good = False

    print(f"\n📊 诊断结果: {'✅ 所有端口正常' if all_good else '❌ 发现问题'}")

    if not all_good:
        print("\n💡 建议解决方案:")
        print("1. python scripts/force_cleanup_ports.py  # 强制清理")
        print("2. python scripts/smart_server_launcher.py  # 智能启动")
        print("3. ./scripts/quick_start_server.sh  # 快速启动")

if __name__ == "__main__":
    main()
