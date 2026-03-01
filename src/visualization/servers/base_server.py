"""
基础服务器抽象类
定义所有服务器模块的通用接口和基础功能
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class BaseServer(ABC):
    """
    基础服务器抽象类

    所有服务器模块都应该继承此类，实现统一的生命周期管理和接口。
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化基础服务器

        Args:
            name: 服务器名称，用于标识和日志记录
            config: 服务器配置字典
        """
        self.name = name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{name}")
        self._running = False
        self._startup_time = None

    @property
    def is_running(self) -> bool:
        """检查服务器是否正在运行"""
        return self._running

    @property
    def uptime(self) -> Optional[float]:
        """获取服务器运行时间（秒）"""
        if self._startup_time:
            return asyncio.get_event_loop().time() - self._startup_time
        return None

    @abstractmethod
    async def start(self) -> None:
        """
        启动服务器

        子类必须实现此方法来启动具体的服务器功能。
        启动过程中应该设置 self._running = True 和 self._startup_time。
        """
        self._running = True
        self._startup_time = asyncio.get_event_loop().time()
        self.logger.info(f"✅ {self.name} 服务器启动成功")

    @abstractmethod
    async def stop(self) -> None:
        """
        停止服务器

        子类必须实现此方法来停止具体的服务器功能。
        停止过程中应该设置 self._running = False。
        """
        self._running = False
        self.logger.info(f"🛑 {self.name} 服务器已停止")

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查

        Returns:
            包含健康状态信息的字典，格式：
            {
                "status": "healthy|unhealthy|degraded",
                "checks": {
                    "check_name": {
                        "status": "pass|fail|warn",
                        "message": "检查结果描述",
                        "details": {...}  # 可选的详细信息
                    }
                },
                "uptime": 运行时间秒数,
                "timestamp": 检查时间戳
            }
        """
        return {
            "status": "unknown",
            "checks": {},
            "uptime": self.uptime,
            "timestamp": asyncio.get_event_loop().time()
        }

    @abstractmethod
    def get_routes(self) -> List[str]:
        """
        获取服务器提供的路由列表

        Returns:
            路由路径字符串列表，用于服务发现和文档生成
        """
        return []

    async def restart(self) -> None:
        """
        重启服务器

        先停止再启动服务器。
        """
        self.logger.info(f"🔄 重启 {self.name} 服务器...")
        await self.stop()
        await asyncio.sleep(0.1)  # 短暂延迟确保清理完成
        await self.start()
        self.logger.info(f"✅ {self.name} 服务器重启完成")

    def get_config(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值或默认值
        """
        return self.config.get(key, default)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """
        更新服务器配置

        Args:
            updates: 要更新的配置字典
        """
        self.config.update(updates)
        self.logger.info(f"🔧 {self.name} 配置已更新: {list(updates.keys())}")

    async def _handle_startup_error(self, error: Exception) -> None:
        """
        处理启动错误

        Args:
            error: 启动过程中发生的异常
        """
        self._running = False
        self.logger.error(f"❌ {self.name} 启动失败: {error}", exc_info=True)

        # 可以在这里添加错误恢复逻辑
        # 例如：重试启动、发送告警等

    async def _handle_shutdown_error(self, error: Exception) -> None:
        """
        处理关闭错误

        Args:
            error: 关闭过程中发生的异常
        """
        self.logger.error(f"❌ {self.name} 关闭失败: {error}", exc_info=True)

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.stop()
