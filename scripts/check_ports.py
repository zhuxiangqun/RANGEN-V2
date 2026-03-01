#!/usr/bin/env python3
"""
检查端口占用情况并提供解决方案
"""

import socket
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_port(port):
    """检查端口是否被占用"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0  # 0表示端口被占用
    except:
        return False

def find_free_port(start_port, max_attempts=10):
    """查找可用的端口"""
    for port in range(start_port, start_port + max_attempts):
        if not check_port(port):
            return port
    return None

def main():
    """主函数"""
    print("🔍 检查端口占用情况")
    print("=" * 50)

    ports_to_check = [8080, 8081, 8082, 8083, 8084, 8085]
    occupied_ports = []
    free_ports = []

    for port in ports_to_check:
        if check_port(port):
            occupied_ports.append(port)
            print(f"❌ 端口 {port}: 被占用")
        else:
            free_ports.append(port)
            print(f"✅ 端口 {port}: 可用")

    print("\n📊 总结:")
    print(f"  🔴 被占用端口: {occupied_ports}")
    print(f"  🟢 可用端口: {free_ports}")

    if occupied_ports:
        print("\n💡 建议解决方案:")

        if 8080 in occupied_ports:
            print("  1. 如果是之前的服务器仍在运行，建议先停止它:")
            print("     pkill -f 'python.*start_unified_server'")
            print("     pkill -f 'python.*quick_start'")

        if 8081 in occupied_ports:
            print("  2. 使用其他端口启动统一服务器:")
            if free_ports:
                suggested_port = free_ports[0]
                print(f"     python scripts/start_unified_server.py --port {suggested_port}")
                print(f"     # 这将使用端口 {suggested_port} (API) 和 {suggested_port + 1} (可视化)")

        print("  3. 或者手动指定端口:")
        if len(free_ports) >= 2:
            api_port, web_port = free_ports[0], free_ports[1]
            print(f"     python scripts/start_unified_server.py --port {api_port}")
            print("     # 然后访问:")
            print(f"     #   API: http://localhost:{api_port}")
            print(f"     #   Web: http://localhost:{web_port}")

    if not occupied_ports:
        print("\n🎉 所有常用端口都可用！")
        print("   可以正常启动统一服务器:")
        print("   python scripts/start_unified_server.py --port 8080")

if __name__ == '__main__':
    main()
