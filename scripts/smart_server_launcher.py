#!/usr/bin/env python3
"""
智能服务器启动器 - 自动解决端口冲突
"""

import os
import subprocess
import sys
import time
import signal
from typing import List, Tuple, Optional

class SmartServerLauncher:
    def __init__(self):
        self.preferred_ports = [9000, 8080, 8082, 3000, 5000, 7000, 4000, 6000]
        self.reserved_sockets = []  # 预占的socket

    def run_command(self, cmd: str, shell: bool = True, capture_output: bool = True, text: bool = True):
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

    def find_processes_on_port(self, port: int) -> List[Tuple[str, str]]:
        """查找占用指定端口的进程"""
        processes = []

        # 使用 lsof
        success, stdout, stderr = self.run_command(f"lsof -i :{port}")
        if success and stdout:
            lines = stdout.strip().split('\n')
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 2:
                        pid = parts[1]
                        process_name = parts[0] if len(parts) > 0 else "unknown"
                        processes.append((pid, process_name))

        # 去重
        unique_processes = []
        seen_pids = set()
        for pid, name in processes:
            if pid not in seen_pids:
                unique_processes.append((pid, name))
                seen_pids.add(pid)

        return unique_processes

    def kill_process_forcefully(self, pid: str) -> bool:
        """强制杀死进程"""
        print(f"🔪 强制终止进程 PID: {pid}...")

        try:
            os.kill(int(pid), signal.SIGTERM)
            time.sleep(1)
        except:
            pass

        # 检查是否还活着
        success, stdout, stderr = self.run_command(f"ps -p {pid}")
        if success:
            print(f"⚠️ 进程 {pid} 仍在运行，强制终止...")
            try:
                os.kill(int(pid), signal.SIGKILL)
                time.sleep(1)
            except:
                pass

            success2, stdout2, stderr2 = self.run_command(f"ps -p {pid}")
            if success2:
                print(f"❌ 无法终止进程 {pid}")
                return False

        print(f"✅ 进程 {pid} 已终止")
        return True

    def cleanup_port(self, port: int) -> bool:
        """清理指定端口"""
        processes = self.find_processes_on_port(port)
        if not processes:
            return True  # 端口本来就空闲

        print(f"❌ 端口 {port} 被以下进程占用:")
        for pid, name in processes:
            print(f"   - PID: {pid}, 进程: {name}")

        # 终止进程
        all_killed = True
        for pid, name in processes:
            if not self.kill_process_forcefully(pid):
                all_killed = False

        # 验证清理结果
        time.sleep(2)
        final_processes = self.find_processes_on_port(port)
        if final_processes:
            print(f"⚠️ 端口 {port} 仍有进程占用:")
            for pid, name in final_processes:
                print(f"   - PID: {pid}, 进程: {name}")
            return False

        print(f"✅ 端口 {port} 已清理完成")
        return all_killed

    def test_port_binding(self, port: int) -> bool:
        """测试是否可以实际绑定端口"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('0.0.0.0', port))
                s.listen(1)
                return True
        except OSError:
            return False

    def reserve_ports(self, base_port: int) -> bool:
        """预占端口对，防止其他进程占用"""
        import socket
        try:
            # 预占两个端口
            sockets = []
            for port in [base_port, base_port + 1]:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind(('0.0.0.0', port))
                sock.listen(1)
                sockets.append(sock)

            self.reserved_sockets = sockets
            print(f"✅ 成功预占端口: {base_port}, {base_port + 1}")
            return True

        except OSError as e:
            print(f"❌ 端口预占失败: {e}")
            # 释放已预占的端口
            for sock in sockets:
                try:
                    sock.close()
                except:
                    pass
            return False

    def release_ports(self):
        """释放预占的端口"""
        for sock in self.reserved_sockets:
            try:
                sock.close()
            except:
                pass
        self.reserved_sockets = []
        print("✅ 已释放预占的端口")

    def find_available_port(self) -> Optional[int]:
        """找到一个可用的端口"""
        print("🔍 搜索可用端口...")

        for port in self.preferred_ports:
            print(f"🎯 测试端口: {port}")

            # 先检查进程占用
            if self.find_processes_on_port(port):
                print("  ❌ 端口被进程占用")
                continue

            # 尝试绑定测试
            if self.test_port_binding(port):
                print("  ✅ 端口可用")
                return port
            else:
                print("  ❌ 端口绑定失败")

        # 如果首选端口都不可用，尝试更高范围的端口
        print("🔄 尝试更高范围的端口...")
        for port in range(9000, 10000):
            if not self.find_processes_on_port(port) and self.test_port_binding(port):
                print(f"  ✅ 找到可用端口: {port}")
                return port

        return None

    def launch_server(self, base_port: Optional[int] = None) -> bool:
        """启动统一服务器"""
        print("🚀 RANGEN 智能统一服务器启动器")
        print("=" * 50)

        try:
            if base_port is None:
                print("🔍 自动查找可用端口...")
                base_port = self.find_available_port()
                if base_port is None:
                    print("❌ 未找到可用端口")
                    return False
            else:
                print(f"🎯 指定端口: {base_port} (统一服务)")
                # 清理指定端口
                if not self.cleanup_port(base_port):
                    print("❌ 无法清理指定端口，寻找替代端口...")
                    alt_port = self.find_available_port()
                    if alt_port is None:
                        print("❌ 未找到可用端口")
                        return False
                    base_port = alt_port

            print(f"✅ 使用端口: {base_port} (统一服务)")
            print()
            print("🚀 启动统一服务器...")
            time.sleep(0.5)  # 给系统一点时间回收端口

        # 启动服务器
        try:
            cmd = f"python scripts/start_unified_server.py --port {base_port}"
            print(f"执行命令: {cmd}")
            result = subprocess.run(cmd, shell=True)

            print()
            print("🎉 启动完成！")
            print(f"   🌐 统一服务: http://localhost:{base_port}")
            print(f"   📊 可视化: http://localhost:{base_port}/")
            print(f"   ⚙️ 配置管理: http://localhost:{base_port}/config")
            print(f"   🔗 API端点: http://localhost:{base_port}/api/*")
            print()
            print("💡 所有功能都在同一个端口上")
            print("💡 按 Ctrl+C 停止服务器")

            return result.returncode == 0

        except KeyboardInterrupt:
            print("\n🛑 用户中断")
            return True
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False

def main():
    launcher = SmartServerLauncher()

    # 解析参数
    base_port = None
    if len(sys.argv) > 1:
        try:
            base_port = int(sys.argv[1])
        except ValueError:
            print("❌ 无效的端口号")
            sys.exit(1)

    success = launcher.launch_server(base_port)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
