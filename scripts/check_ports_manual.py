#!/usr/bin/env python3
"""
手动检查端口占用的脚本
"""

import socket
import sys

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

def main():
    print("🔍 检查端口占用情况:")
    print("=" * 50)

    ports_to_check = [8080, 8081, 8082, 8083, 8084, 8085, 9000, 9001]
    occupied_ports = []

    for port in ports_to_check:
        is_occupied = check_port(port)
        status = "❌ 被占用" if is_occupied else "✅ 可用"
        print("15")
        if is_occupied:
            occupied_ports.append(port)

    print("\n📋 总结:")
    if occupied_ports:
        print(f"🔴 被占用端口: {occupied_ports}")
        print("🟢 可用端口: [port for port in ports_to_check if port not in occupied_ports]")
        print("\n💡 建议解决方案:")
        print("1. 停止占用进程:")
        for port in occupied_ports:
            print(f"   lsof -i :{port}  # 查看占用进程")
            print(f"   kill -9 <PID>    # 杀死进程")
        print("\n2. 使用其他端口启动:")
        available_ports = [port for port in ports_to_check if port not in occupied_ports]
        if available_ports:
            port = available_ports[0]
            print(f"   python scripts/start_unified_server.py --port {port}")
            print(f"   # 这将使用端口 {port} (API) 和 {port+1} (可视化)")
    else:
        print("🎉 所有常用端口都可用！")
        print("   可以正常启动: python scripts/start_unified_server.py --port 8080")

if __name__ == "__main__":
    main()
