#!/usr/bin/env python3
"""
端口管理工具 - 自动检测和解决端口冲突
"""

import os
import subprocess
import sys
import socket
import time
from pathlib import Path

def run_command(cmd, capture_output=True):
    """运行系统命令"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        else:
            result = subprocess.run(cmd, shell=True)
            return result.returncode == 0, "", ""
    except Exception as e:
        return False, "", str(e)

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0  # 0表示连接成功，端口被占用
    except:
        sock.close()
        return False

def find_process_on_port(port):
    """查找占用指定端口的进程"""
    success, stdout, stderr = run_command(f"lsof -i :{port}")
    if success and stdout:
        lines = stdout.strip().split('\n')
        if len(lines) > 1:  # 第一行是标题
            process_info = lines[1].split()
            if len(process_info) >= 2:
                pid = process_info[1]
                process_name = process_info[0] if len(process_info) > 0 else "unknown"
                return pid, process_name
    return None, None

def kill_process(pid):
    """杀死指定PID的进程"""
    print(f"🔪 正在终止进程 PID: {pid}...")
    success, stdout, stderr = run_command(f"kill -9 {pid}")
    if success:
        print(f"✅ 进程 {pid} 已终止")
        time.sleep(1)  # 等待进程完全退出
        return True
    else:
        print(f"❌ 无法终止进程 {pid}: {stderr}")
        return False

def find_free_ports(start_port, count):
    """查找连续的可用端口"""
    free_ports = []
    port = start_port

    while len(free_ports) < count:
        if not check_port(port):
            free_ports.append(port)
        port += 1

    return free_ports

def cleanup_conflicting_ports(target_ports):
    """清理冲突的端口"""
    print("🔍 检查端口占用情况...")
    conflicts_found = False

    for port in target_ports:
        if check_port(port):
            conflicts_found = True
            pid, process_name = find_process_on_port(port)
            if pid:
                print(f"❌ 端口 {port} 被进程占用: {process_name} (PID: {pid})")
                # 询问用户是否终止进程
                response = input(f"   终止进程 {process_name} (PID: {pid})? (y/N): ").lower().strip()
                if response in ['y', 'yes']:
                    kill_process(pid)
                else:
                    print(f"   ⏭️  跳过端口 {port}")
            else:
                print(f"❌ 端口 {port} 被占用，但无法识别进程")
        else:
            print(f"✅ 端口 {port} 可用")

    return not conflicts_found

def suggest_alternative_ports(base_port):
    """建议替代端口"""
    print(f"\n💡 建议的替代端口组合:")

    # 查找可用端口
    free_ports = find_free_ports(base_port, 2)
    if len(free_ports) >= 2:
        api_port, viz_port = free_ports[0], free_ports[1]
        print(f"   推荐: --port {api_port}")
        print(f"   API服务器: http://localhost:{api_port}")
        print(f"   可视化服务器: http://localhost:{viz_port}")
        print(f"   配置管理: http://localhost:{viz_port}/config")

    # 其他选项
    alternatives = [
        (9000, 9001),
        (8080, 8081),
        (3000, 3001),
        (5000, 5001),
        (7000, 7001),
    ]

    print("\n   其他选项:")
    for api, viz in alternatives:
        if not check_port(api) and not check_port(viz):
            print(f"   --port {api} (API: {api}, 可视化: {viz})")

def main():
    print("🚀 端口管理工具")
    print("=" * 50)

    if len(sys.argv) > 1:
        try:
            base_port = int(sys.argv[1])
        except ValueError:
            print("❌ 无效的端口号")
            sys.exit(1)
    else:
        base_port = 8082

    target_ports = [base_port, base_port + 1]
    print(f"🎯 目标端口: {target_ports[0]} (API), {target_ports[1]} (可视化)")

    # 检查和清理冲突
    if cleanup_conflicting_ports(target_ports):
        print("\n✅ 所有端口都可用！")
        print("🚀 现在可以启动服务器:")
        print(f"   python scripts/start_unified_server.py --port {base_port}")
    else:
        print("\n⚠️  存在端口冲突")
        suggest_alternative_ports(base_port)

        # 询问是否自动查找并使用可用端口
        response = input("\n🔍 是否自动查找可用端口并启动服务器? (y/N): ").lower().strip()
        if response in ['y', 'yes']:
            free_ports = find_free_ports(base_port, 2)
            if len(free_ports) >= 2:
                api_port = free_ports[0]
                print(f"🚀 启动服务器: python scripts/start_unified_server.py --port {api_port}")
                os.system(f"python scripts/start_unified_server.py --port {api_port}")
            else:
                print("❌ 未找到足够的连续可用端口")

if __name__ == "__main__":
    main()
