#!/usr/bin/env python3
"""
统一服务器启动脚本

启动集成的 LangGraph 工作流可视化和动态配置管理系统
所有功能都在同一个端口上提供服务
"""

import asyncio
import os
import sys
import signal
import threading
import concurrent.futures
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 加载环境变量
try:
    from dotenv import load_dotenv
    env_path = project_root / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=False)
        print("✅ 已从 .env 文件加载环境变量")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except PermissionError as e:
    print(f"⚠️  .env 文件权限错误，跳过加载: {e}")
except Exception as e:
    print(f"⚠️  加载 .env 文件时出错: {e}")

# 设置环境变量
os.environ.setdefault('ENABLE_UNIFIED_WORKFLOW', 'true')
os.environ.setdefault('ENABLE_BROWSER_VISUALIZATION', 'true')

# FIX: UnifiedResearchSystem was refactored, skipping


class UnifiedServer:
    """统一服务器 - 集成可视化和配置管理功能"""

    def __init__(self, port: int = 8080):
        self.port = port
        self.system = None
        self.visualization_server = None
        self._shutdown_event = threading.Event()
        self._shutdown_lock = threading.Lock()
        self._is_shutting_down = False

    async def initialize_systems(self):
        """初始化统一服务器"""
        print("🚀 初始化统一服务器...")

        try:
            # 1. 初始化可视化服务器
            print("   🌐 初始化可视化服务器...")
            try:
                from src.visualization.browser_server import BrowserVisualizationServer
                self.visualization_server = BrowserVisualizationServer(
                    workflow=None,
                    system=None,
                    port=self.port,
                    enable_config_management=True
                )
                print(f"   ✅ 可视化服务器初始化完成 (端口: {self.port})")
            except Exception as e:
                print(f"   ❌ 可视化服务器初始化失败: {e}")
                raise

        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            raise

    async def start_server(self):
        """启动统一服务器"""
        try:
            if self.visualization_server:
                print(f"\n🌐 统一服务器启动成功！")
                print(f"   📊 LangGraph可视化: http://localhost:{self.port}")
                print(f"   ⚙️ 配置管理: http://localhost:{self.port}/config")
                print(f"   🔗 API端点: http://localhost:{self.port}/api/*")
                print(f"   📋 服务器信息: http://localhost:{self.port}/")
                print("\n💡 所有功能都在同一个端口上运行")
                print("💡 按 Ctrl+C 停止服务器\n")

                # 🚀 修复：创建服务器任务和监控任务
                server_task = asyncio.create_task(self.visualization_server.start())
                
                # 监控关闭事件
                async def monitor_shutdown():
                    """监控关闭事件"""
                    while not self._shutdown_event.is_set():
                        await asyncio.sleep(0.1)
                    # 关闭事件已设置，取消服务器任务
                    if not server_task.done():
                        server_task.cancel()
                        try:
                            await server_task
                        except (asyncio.CancelledError, KeyboardInterrupt):
                            pass
                
                monitor_task = asyncio.create_task(monitor_shutdown())
                
                # 等待服务器任务完成（或被取消）
                try:
                    await server_task
                except (asyncio.CancelledError, KeyboardInterrupt):
                    # 服务器被取消，这是正常的关闭流程
                    pass
                except Exception as e:
                    # 服务器启动失败
                    monitor_task.cancel()
                    raise
                finally:
                    # 确保监控任务也被取消
                    if not monitor_task.done():
                        monitor_task.cancel()
                        try:
                            await monitor_task
                        except asyncio.CancelledError:
                            pass
            else:
                print("❌ 服务器初始化失败")
                raise RuntimeError("可视化服务器未初始化")

        except KeyboardInterrupt:
            print("\n⚠️ 收到停止信号，正在关闭服务器...")
            raise
        except asyncio.CancelledError:
            print("\n⚠️ 服务器任务被取消")
            raise
        except Exception as e:
            print(f"❌ 服务器启动失败: {e}")
            raise
    
    async def shutdown(self, timeout: float = 3.0):
        """关闭服务器并清理资源"""
        with self._shutdown_lock:
            if self._is_shutting_down:
                return
            self._is_shutting_down = True
        
        print("\n🔄 正在关闭服务器并清理资源...")
        
        try:
            # 1. 关闭可视化服务器（优先处理，uvicorn会自动处理任务清理）
            # 🚀 修复：不手动取消所有任务，避免递归错误
            # uvicorn 服务器关闭时会自动处理任务清理
            if self.visualization_server:
                try:
                    if hasattr(self.visualization_server, 'stop'):
                        await asyncio.wait_for(
                            self.visualization_server.stop(),
                            timeout=timeout
                        )
                    elif hasattr(self.visualization_server, 'shutdown'):
                        await asyncio.wait_for(
                            self.visualization_server.shutdown(),  # type: ignore
                            timeout=timeout
                        )
                except asyncio.TimeoutError:
                    print("⚠️ 可视化服务器关闭超时，强制关闭")
                except Exception as e:
                    print(f"⚠️ 关闭可视化服务器时出错: {e}")
            
            # 2. 关闭系统
            if self.system:
                try:
                    if hasattr(self.system, 'shutdown'):
                        await asyncio.wait_for(
                            self.system.shutdown(),
                            timeout=timeout
                        )
                except asyncio.TimeoutError:
                    print("⚠️ 系统关闭超时，强制关闭")
                except Exception as e:
                    print(f"⚠️ 关闭系统时出错: {e}")
            
            # 3. 关闭所有 HTTP 连接池
            try:
                # 🚀 修复：只清理 LLMIntegration 实例，避免触发 Torch/CUDA 检查
                import gc
                from src.core.llm_integration import LLMIntegration
                closed_count = 0
                for obj in gc.get_objects():
                    # 只处理 LLMIntegration 实例，避免处理其他对象（如 Torch 对象）
                    if isinstance(obj, LLMIntegration):
                        try:
                            obj.close()
                            closed_count += 1
                        except Exception:
                            pass
                if closed_count > 0:
                    print(f"   ✅ 已关闭 {closed_count} 个 HTTP 连接池")
            except Exception as e:
                # 忽略 Torch/CUDA 相关的错误，这些不影响程序退出
                if "CUDA" not in str(e) and "Torch" not in str(e):
                    print(f"⚠️ 清理HTTP连接池时出错: {e}")
            
            # 4. 强制垃圾回收
            try:
                import gc
                gc.collect()
            except Exception:
                pass
            
            print("✅ 资源清理完成")
            
        except Exception as e:
            print(f"⚠️ 关闭过程中出错: {e}")


# 全局变量用于信号处理
_shutdown_flag = False
_force_exit_flag = False
_server_instance = None


def signal_handler(signum, frame):
    """信号处理器 - 优雅关闭服务器"""
    global _shutdown_flag, _force_exit_flag, _server_instance
    
    if not _shutdown_flag:
        _shutdown_flag = True
        print("\n\n⚠️ 收到中断信号 (Ctrl-C)，正在关闭服务器...")
        print("   如果 3 秒内未退出，请再次按 Ctrl-C 强制退出")
        
        # 触发关闭事件
        if _server_instance:
            _server_instance._shutdown_event.set()
        
        # 🚀 修复：通过事件循环发送取消信号到当前任务
        try:
            loop = asyncio.get_running_loop()
            # 取消当前运行的所有任务（除了主任务）
            current_task = asyncio.current_task(loop)
            for task in asyncio.all_tasks(loop):
                if task != current_task and not task.done():
                    task.cancel()
        except RuntimeError:
            # 如果没有运行的事件循环，KeyboardInterrupt 会被 asyncio.run() 捕获
            pass
    else:
        _force_exit_flag = True
        print("\n⚠️ 强制退出...")
        # 强制退出，跳过所有清理
        import os
        os._exit(1)


async def main():
    """主函数"""
    global _server_instance
    
    import argparse

    parser = argparse.ArgumentParser(description='统一服务器启动器')
    parser.add_argument('--port', type=int, default=8080, help='服务器端口（包含可视化和配置管理功能）')

    args = parser.parse_args()

    print("=" * 80)
    print("🚀 统一服务器 - 集成 LangGraph 可视化与配置管理")
    print("=" * 80)
    print()

    server = None

    try:
        server = UnifiedServer(port=args.port)
        _server_instance = server

        # 初始化系统
        await server.initialize_systems()

        # 启动服务器（直接运行，让 KeyboardInterrupt 自然传播）
        try:
            await server.start_server()
        except KeyboardInterrupt:
            print("\n\n⚠️ 收到停止信号，正在关闭服务器...")
            raise  # 重新抛出，让 finally 块处理清理
        except asyncio.CancelledError:
            print("\n⚠️ 服务器任务被取消")
            raise

    except KeyboardInterrupt:
        print("\n\n⚠️ 收到停止信号，正在关闭服务器...")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理资源（快速清理，避免卡住）
        if server:
            try:
                # 🚀 修复：使用更短的超时时间，避免卡住
                await asyncio.wait_for(server.shutdown(timeout=1.5), timeout=2.0)
            except asyncio.TimeoutError:
                print("⚠️ 资源清理超时，强制退出")
            except Exception as e:
                print(f"⚠️ 资源清理时出错: {e}")
        
        # 如果设置了强制退出标志，立即退出
        if _force_exit_flag:
            import os
            os._exit(1)


if __name__ == "__main__":
    # 设置信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, 'SIGTERM'):
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ 程序已退出")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序异常退出: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
