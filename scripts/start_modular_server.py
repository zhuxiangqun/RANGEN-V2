#!/usr/bin/env python3
"""
模块化服务器启动脚本
使用新的模块化架构启动RANGEN服务器
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="启动RANGEN模块化服务器")
    parser.add_argument("--port", type=int, default=8080, help="主服务器端口")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务器主机地址")
    parser.add_argument("--config", type=str, help="配置文件路径")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("🚀 启动RANGEN模块化服务器...")
    logger.info(f"📍 服务器地址: {args.host}:{args.port}")

    try:
        # 导入并初始化系统
        logger.info("🔧 初始化系统组件...")

        # 这里应该初始化实际的系统组件
        # 暂时使用模拟对象
        workflow_system = None  # 暂时设为None
        tracker = None
        config_manager = None

        # 导入统一服务管理器
        from src.visualization.servers import UnifiedServerManager

        # 创建配置
        config = {
            "host": args.host,
            "port": args.port,
            "debug": args.debug,
            "services": {
                "api_server": {
                    "enabled": True,
                    "port": args.port + 1,
                    "host": args.host
                },
                "visualization_server": {
                    "enabled": True,
                    "port": args.port + 2,
                    "host": args.host
                },
                "config_server": {
                    "enabled": True,
                    "port": args.port + 3,
                    "host": args.host
                },
                "websocket_server": {
                    "enabled": True,
                    "port": args.port + 4,
                    "host": args.host
                }
            }
        }

        # 创建统一服务管理器
        server_manager = UnifiedServerManager(
            config=config,
            workflow_system=workflow_system,
            tracker=tracker,
            config_manager=config_manager
        )

        # 启动服务器
        logger.info("🌐 启动服务器...")
        asyncio.run(server_manager.start())

    except KeyboardInterrupt:
        logger.info("🛑 收到中断信号，正在关闭服务器...")
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
