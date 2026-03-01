#!/usr/bin/env python3
"""
启动浏览器可视化服务器
"""
import asyncio
import os
import sys
import signal
import threading
import time
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
        print(f"✅ 已从 .env 文件加载环境变量: {env_path}")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")
except Exception as e:
    print(f"⚠️  加载 .env 文件失败: {e}")

# 确保启用统一工作流
os.environ.setdefault('ENABLE_UNIFIED_WORKFLOW', 'true')
# 禁用 UnifiedResearchSystem 的自动可视化服务器启动（我们将手动启动）
os.environ.setdefault('ENABLE_BROWSER_VISUALIZATION', 'false')

from src.visualization.browser_server import BrowserVisualizationServer
from src.unified_research_system import create_unified_research_system

# 全局变量用于信号处理
_shutdown_flag = False
_force_exit_flag = False
_server_instance = None
_signal_thread = None


def signal_handler(signum, frame):
    """信号处理器 - 优雅关闭服务器"""
    global _shutdown_flag, _force_exit_flag, _server_instance

    if not _shutdown_flag:
        _shutdown_flag = True
        print(f"\n⚠️ 收到信号 {signum}，正在关闭服务器...")

        # 如果有正在运行的事件循环，尝试优雅关闭
        try:
            loop = asyncio.get_running_loop()
            # 在事件循环中设置shutdown flag，monitor任务会处理关闭
            print("⚠️ 事件循环正在运行，等待优雅关闭...")
        except RuntimeError:
            # 如果没有运行的事件循环，KeyboardInterrupt 会被 asyncio.run() 捕获
            pass
    else:
        _force_exit_flag = True
        print("\n⚠️ 收到第二次停止信号，强制退出...")
        # 强制退出，跳过所有清理
        import os
        os._exit(1)


def keyboard_interrupt_watcher():
    """在单独线程中监听键盘中断 - 沙盒环境友好"""
    global _shutdown_flag, _force_exit_flag

    try:
        while not _shutdown_flag:
            time.sleep(0.1)  # 短暂等待
    except KeyboardInterrupt:
        if not _shutdown_flag:
            _shutdown_flag = True
            print("\n⚠️ 检测到键盘中断，正在关闭服务器...")
        else:
            _force_exit_flag = True
            print("\n⚠️ 收到第二次中断信号，强制退出...")
            import os
            os._exit(1)


async def main():
    """主函数（异步）"""
    global _server_instance

    print("=" * 80)
    print("🌐 LangGraph Workflow Visualizer")
    print("=" * 80)
    print()

    # 获取端口配置
    port = int(os.getenv('VISUALIZATION_PORT', '8080'))

    server = None
    system = None

    try:
        print("1. 初始化 UnifiedResearchSystem...")
        # 初始化系统（这会自动初始化工作流）
        system = await create_unified_research_system()
        print("   ✅ 系统初始化完成")

        # 检查工作流状态
        if hasattr(system, '_unified_workflow') and system._unified_workflow:
            if hasattr(system._unified_workflow, 'workflow') and system._unified_workflow.workflow:
                print("   ✅ 统一工作流已初始化")
            else:
                print("   ⚠️  统一工作流对象存在，但 workflow 图为 None")
                print("   💡 可能原因: 工作流构建或编译失败")
        else:
            print("   ⚠️  统一工作流未初始化")
            print("   🔍 诊断信息:")

            # 检查环境变量（os 已在文件顶部导入）
            enable_workflow = os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true').lower() == 'true'
            print(f"      - ENABLE_UNIFIED_WORKFLOW: {os.getenv('ENABLE_UNIFIED_WORKFLOW', 'true')} (解析为: {enable_workflow})")

            # 检查 LangGraph 是否可用
            try:
                from src.core.langgraph_unified_workflow import LANGGRAPH_AVAILABLE
                print(f"      - LangGraph 可用: {LANGGRAPH_AVAILABLE}")
                if not LANGGRAPH_AVAILABLE:
                    print("      💡 安装 LangGraph: pip install langgraph")
            except Exception as e:
                print(f"      - LangGraph 检查失败: {e}")

            # 检查详细处理节点模块
            try:
                from src.core.langgraph_detailed_processing_nodes import DetailedProcessingNodes
                print("      - 详细处理节点模块: ✅ 可用")
            except Exception as e:
                print(f"      - 详细处理节点模块: ❌ 不可用 ({e})")

            # 检查核心功能节点模块
            try:
                from src.core.langgraph_core_nodes import CoreNodes
                print("      - 核心功能节点模块: ✅ 可用")
            except Exception as e:
                print(f"      - 核心功能节点模块: ❌ 不可用 ({e})")

            print("   💡 提示:")
            print("      1. 确保 ENABLE_UNIFIED_WORKFLOW=true")
            print("      2. 确保 LangGraph 已安装: pip install langgraph")
            print("      3. 查看系统初始化日志，查找 '❌ [初始化] 统一工作流初始化失败' 错误")
            print("      4. 运行诊断脚本: python3 scripts/diagnose_workflow.py")

        print()

        print("2. 启动可视化服务器...")
        print(f"   端口: {port}")
        print(f"   访问地址: http://localhost:{port}")
        print()
        print("提示:")
        print("- 在浏览器中打开上述地址即可查看可视化界面")
        print("- 按 Ctrl+C 停止服务器（支持沙盒环境）")
        print("- 如果 Ctrl+C 不响应，请连续按两次 Ctrl+C 强制退出")
        print()

        # 创建并启动服务器，传入系统实例
        server = BrowserVisualizationServer(
            workflow=None,  # 让服务器从系统获取工作流
            system=system,  # 传入系统实例
            port=port
        )

        _server_instance = server

        # 创建服务器启动任务
        server_task = asyncio.create_task(server.start())

        # 创建监控任务，定期检查shutdown flag
        async def monitor_shutdown():
            while not _shutdown_flag:
                await asyncio.sleep(0.1)  # 每100ms检查一次

            print("\n🔄 收到关闭信号，正在停止服务器...")
            try:
                # 取消服务器任务
                if not server_task.done():
                    server_task.cancel()
                    try:
                        await server_task
                    except asyncio.CancelledError:
                        pass

                # 停止服务器
                if hasattr(server, 'stop'):
                    await server.stop()

                print("✅ 服务器已停止")

            except Exception as e:
                print(f"⚠️ 停止服务器时出错: {e}")
                # 强制退出
                import os
                os._exit(1)

        monitor_task = asyncio.create_task(monitor_shutdown())

        # 等待服务器任务完成（或被取消）
        try:
            await server_task
        except asyncio.CancelledError:
            # 服务器被取消，这是正常的关闭流程
            pass

        # 等待监控任务完成
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass

    except KeyboardInterrupt:
        print("\n⚠️ 收到停止信号，正在关闭服务器...")
        raise
    except asyncio.CancelledError:
        print("\n⚠️ 服务器任务被取消")
        raise
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # 清理资源
        if server and hasattr(server, 'stop'):
            try:
                await server.stop()
            except Exception:
                pass
        if system and hasattr(system, 'shutdown'):
            try:
                await system.shutdown()
            except Exception:
                pass
        print("🧹 资源清理完成")


if __name__ == "__main__":
    # 🚀 修复：启动键盘中断监听线程（沙盒环境友好）
    _signal_thread = threading.Thread(target=keyboard_interrupt_watcher, daemon=True)
    _signal_thread.start()

    # 设置信号处理器（作为备用）
    try:
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    except (OSError, ValueError) as e:
        print(f"⚠️ 信号处理器设置失败（沙盒环境限制）: {e}")
        print("🔄 将使用线程监听键盘中断")

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

