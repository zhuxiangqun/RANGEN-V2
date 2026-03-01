#!/usr/bin/env python3
"""
修复端口冲突的脚本
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    """运行系统命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)

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
    success, stdout, stderr = run_command(f"kill -9 {pid}")
    return success

def main():
    print("🔧 端口冲突修复工具")
    print("=" * 50)

    # 检查问题端口
    problem_ports = [8082, 8083]
    fixed_ports = []

    for port in problem_ports:
        print(f"\n🔍 检查端口 {port}:")
        pid, process_name = find_process_on_port(port)

        if pid:
            print(f"   ❌ 端口 {port} 被进程占用: {process_name} (PID: {pid})")

            # 询问是否杀死进程
            response = input(f"   是否杀死进程 {process_name} (PID: {pid})? (y/N): ").lower().strip()
            if response in ['y', 'yes']:
                if kill_process(pid):
                    print(f"   ✅ 已杀死进程 {process_name} (PID: {pid})")
                    fixed_ports.append(port)
                else:
                    print(f"   ❌ 无法杀死进程 {process_name} (PID: {pid})")
            else:
                print(f"   ⏭️  跳过端口 {port}")
        else:
            print(f"   ✅ 端口 {port} 可用")
            fixed_ports.append(port)

    print("
📋 修复结果:"    if fixed_ports:
        print(f"✅ 已修复端口: {fixed_ports}")
        available_port = min(fixed_ports) if fixed_ports else 8082
        print("
🚀 启动建议:"        print(f"   python scripts/start_unified_server.py --port {available_port}")
        print("   # 这将使用以下端口:"
        print(f"   #   API服务器: http://localhost:{available_port}")
        print(f"   #   可视化服务器: http://localhost:{available_port + 1}")
        print(f"   #   配置管理: http://localhost:{available_port + 1}/config"
    else:
        print("❌ 未能修复任何端口冲突")
        print("\n💡 手动解决方案:")
        print("1. 查找占用进程: ps aux | grep python")
        print("2. 杀死相关进程: kill -9 <PID>")
        print("3. 或使用其他端口: python scripts/start_unified_server.py --port 9000")

if __name__ == "__main__":
    main()
