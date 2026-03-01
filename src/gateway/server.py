"""
Gateway Server - 启动脚本

用于启动 RANGEN Gateway 服务
"""

import asyncio
import argparse
import os
import logging
from typing import Optional

from src.gateway import Gateway, GatewayConfig, initialize_gateway
from src.gateway.channels.telegram import create_telegram_adapter
from src.gateway.channels.webchat import create_webchat_adapter
from src.services.logging_service import setup_logging, get_logger

logger = get_logger(__name__)


class GatewayServer:
    """Gateway 服务器"""
    
    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or GatewayConfig()
        self.gateway: Optional[Gateway] = None
    
    async def start(self):
        """启动 Gateway 服务器"""
        logger.info("Starting RANGEN Gateway Server...")
        
        # 1. 初始化 Gateway
        self.gateway = await initialize_gateway(self.config)
        
        # 2. 注册渠道
        await self._register_channels()
        
        # 3. 打印状态
        self._print_status()
        
        logger.info("RANGEN Gateway Server started successfully!")
        
        # 4. 保持运行
        try:
            while True:
                await asyncio.sleep(10)
                status = self.gateway.get_status()
                logger.debug(f"Status: {status}")
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.stop()
    
    async def _register_channels(self):
        """注册渠道"""
        # Telegram
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if telegram_token:
            adapter = create_telegram_adapter(telegram_token)
            await self.gateway.register_channel("telegram", adapter)
            await adapter.connect()
            logger.info("Telegram channel registered")
        
        # WebChat
        webchat_port = int(os.getenv("WEBCHAT_PORT", "8765"))
        adapter = create_webchat_adapter(port=webchat_port)
        await self.gateway.register_channel("webchat", adapter)
        await adapter.connect()
        logger.info(f"WebChat channel started on port {webchat_port}")
    
    def _print_status(self):
        """打印状态"""
        status = self.gateway.get_status()
        print("\n" + "="*50)
        print("RANGEN Gateway Server")
        print("="*50)
        print(f"Status: {status['status']}")
        print(f"Channels: {', '.join(status['channels'])}")
        print(f"Active Sessions: {status['active_sessions']}")
        print("="*50 + "\n")
    
    async def stop(self):
        """停止 Gateway 服务器"""
        if self.gateway:
            await self.gateway.stop()
            logger.info("RANGEN Gateway Server stopped")


async def main():
    """主函数"""
    # 设置日志
    setup_logging(level=logging.INFO)
    
    # 解析参数
    parser = argparse.ArgumentParser(description="RANGEN Gateway Server")
    parser.add_argument("--port", type=int, default=8765, help="WebChat port")
    parser.add_argument("--heartbeat", type=int, default=60, help="Heartbeat interval (seconds)")
    parser.add_argument("--rate-limit", type=int, default=20, help="Rate limit per minute")
    parser.add_argument("--no-rate-limit", action="store_true", help="Disable rate limiting")
    args = parser.parse_args()
    
    # 创建配置
    config = GatewayConfig(
        heartbeat_interval=args.heartbeat,
        rate_limit_enabled=not args.no_rate_limit,
        rate_limit_max_per_minute=args.rate_limit
    )
    
    # 覆盖 WebChat 端口
    config.webchat_port = args.port
    
    # 启动服务器
    server = GatewayServer(config)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
