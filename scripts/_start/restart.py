#!/usr/bin/env python3
"""
重启统一服务器
"""

import subprocess
import sys
import time
from pathlib import Path

def restart_server():
    """重启服务器"""
    print("🔄 重启统一服务器...")

    try:
        # 终止可能的服务器进程
        print("🛑 终止现有服务器进程...")
        try:
            # 尝试终止端口8080上的进程
            subprocess.run(['pkill', '-f', 'start_unified_server.py'], check=False)
            subprocess.run(['pkill', '-f', 'uvicorn'], check=False)
            time.sleep(2)
        except:
            pass

        # 启动新服务器
        print("🚀 启动新服务器...")
        project_root = Path(__file__).parent.parent
        cmd = [sys.executable, 'scripts/start_unified_server.py', '--port', '8080']

        print(f"执行命令: {' '.join(cmd)}")
        process = subprocess.Popen(
            cmd,
            cwd=str(project_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # 等待服务器启动
        print("⏳ 等待服务器启动...")
        time.sleep(5)

        # 检查进程是否还在运行
        if process.poll() is None:
            print("✅ 服务器启动成功！")
            print("🌐 访问地址:")
            print("   http://localhost:8080")
            print("   http://localhost:8080/config")
            print("   http://localhost:8080/api/config")

            # 保持进程运行
            try:
                print("\n📋 服务器输出:")
                for line in process.stdout:
                    print(line.strip())
                    if "Application startup complete" in line:
                        print("\n🎉 服务器完全启动！现在可以访问 /config 页面了。")
                        break
            except KeyboardInterrupt:
                print("\n🛑 收到中断信号，正在停止服务器...")
                process.terminate()
                process.wait()

        else:
            print("❌ 服务器启动失败")
            # 显示错误输出
            output, _ = process.communicate()
            print("错误输出:")
            print(output)

    except Exception as e:
        print(f"❌ 重启失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    restart_server()
