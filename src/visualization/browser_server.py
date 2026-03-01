"""
浏览器可视化服务器 - 模块化架构版本

提供 LangGraph 工作流的实时可视化功能
使用新的模块化服务器架构
"""
import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入新的模块化服务器架构
try:
    from src.visualization.servers.unified_server_manager import UnifiedServerManager
    from src.config.unified_config_manager import UnifiedConfigManager
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"无法导入新的模块化服务器架构: {e}")
    logger.error("请确保所有服务器模块都已正确创建")
    MODULES_AVAILABLE = False
    UnifiedConfigManager = None


class BrowserVisualizationServer:
    """
    浏览器可视化服务器 - 兼容旧接口

    这个类现在作为新模块化架构的兼容层，
    内部使用 UnifiedServerManager 来管理各个服务模块。
    """

    def __init__(self,
                 workflow=None,
                 system=None,
                 port: int = 8080,
                 enable_config_management: bool = True):
        """
        初始化浏览器可视化服务器

        Args:
            workflow: 工作流实例（可选，用于兼容）
            system: 系统实例（可选，用于兼容）
            port: 服务器端口
            enable_config_management: 是否启用配置管理
        """
        self.workflow = workflow
        self.system = system
        self.port = port
        self.enable_config_management = enable_config_management

        # 初始化新的统一服务器管理器
        self.server_manager = None

        if MODULES_AVAILABLE:
            try:
                # 创建配置
                config = {
                    "host": "127.0.0.1",
                    "port": port,
                    "debug": False,
                    "services": {
                        "api_server": {
                            "enabled": True,
                            "port": port + 1,
                            "host": "127.0.0.1"
                        },
                        "visualization_server": {
                            "enabled": True,
                            "port": port + 2,
                            "host": "127.0.0.1"
                        },
                        "config_server": {
                            "enabled": enable_config_management,
                            "host": "127.0.0.1",
                            "port": port + 3,
                            "host": "0.0.0.0"
                        },
                        "websocket_server": {
                            "enabled": True,
                            "host": "127.0.0.1",
                            "port": port + 4,
                            "host": "0.0.0.0"
                        }
                    }
                }

                # 初始化配置管理器
                config_manager = UnifiedConfigManager() if UnifiedConfigManager else None

                # 初始化服务器管理器
                self.server_manager = UnifiedServerManager(
                    config=config,
                    workflow_system=system,  # 传递系统实例
                    tracker=None,  # 暂时设为None
                    config_manager=config_manager  # 使用配置管理器
                )

                logger.info("✅ 模块化服务器架构初始化成功")

            except Exception as e:
                logger.error(f"❌ 初始化模块化服务器架构失败: {e}", exc_info=True)
                self.server_manager = None
        else:
            logger.error("❌ 模块化服务器架构不可用，将使用降级模式")
            self.server_manager = None

    async def start(self) -> None:
        """
        启动服务器

        使用新的统一服务器管理器来启动所有服务。
        """
        if self.server_manager:
            logger.info(f"🚀 启动统一服务器管理器 (端口: {self.port})")
            await self.server_manager.start()
        else:
            logger.error("❌ 服务器管理器不可用，无法启动服务器")
            raise RuntimeError("服务器管理器初始化失败")

    async def stop(self) -> None:
        """
        停止服务器

        停止所有子服务。
        """
        if self.server_manager:
            logger.info("🛑 停止统一服务器管理器")
            await self.server_manager.stop()
        else:
            logger.warning("服务器管理器不可用")

    async def health_check(self) -> Dict[str, Any]:
        """
        执行健康检查

        返回服务器的整体健康状态。
        """
        if self.server_manager:
            return await self.server_manager.health_check()
        else:
            return {
                "status": "unhealthy",
                "checks": {
                    "server_manager": {
                        "status": "fail",
                        "message": "服务器管理器初始化失败"
                    }
                },
                "uptime": 0,
                "timestamp": asyncio.get_event_loop().time()
            }

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态

        返回所有子服务的状态信息。
        """
        if self.server_manager:
            return self.server_manager.get_service_status()
        else:
            return {"error": "服务器管理器不可用"}

    # 兼容性方法 - 委托给服务器管理器
    def get_app(self):
        """获取主应用实例（兼容性方法）"""
        if self.server_manager:
            return self.server_manager.get_app()
        return None

    # 兼容性属性
    @property
    def tracker(self):
        """获取跟踪器（兼容性属性）"""
        # 这里可以从服务器管理器中获取tracker
        return None

    @property
    def orchestration_tracker(self):
        """获取编排跟踪器（兼容性属性）"""
        # 这里可以从服务器管理器中获取orchestration_tracker
        return None

    # 兼容性方法 - 现在这些方法委托给相应的服务模块
    def execute_workflow(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流（兼容性方法）"""
        # 这里应该委托给API服务器
        logger.warning("execute_workflow方法暂未实现，请使用新的API端点")
        return {"error": "方法暂未实现"}

    def get_workflow_graph(self, expanded_groups: Optional[str] = None) -> Dict[str, Any]:
        """获取工作流图（兼容性方法）"""
        # 这里应该委托给可视化服务器
        logger.warning("get_workflow_graph方法暂未实现，请使用新的API端点")
        return {"error": "方法暂未实现"}

    def _generate_config_dashboard_html(self) -> str:
        """生成配置仪表板HTML（兼容性方法）"""
        # 这里应该委托给配置服务器
        logger.warning("_generate_config_dashboard_html方法暂未实现，请使用新的配置服务器")
        return "<h1>配置管理器不可用</h1><p>请使用新的模块化配置服务器</p>"


# 兼容性函数
def create_visualization_server(workflow=None, system=None, port: int = 8080, enable_config_management: bool = True):
    """
    创建可视化服务器实例（兼容性函数）

    这个函数保持向后兼容，内部使用新的模块化架构。
    """
    return BrowserVisualizationServer(
        workflow=workflow,
        system=system,
        port=port,
        enable_config_management=enable_config_management
    )


# 导出主要的类和函数，保持向后兼容
__all__ = [
    'BrowserVisualizationServer',
    'create_visualization_server',
    'WorkflowTracker'  # 保持兼容性
]


# 导入依赖并创建WorkflowTracker
try:
    from src.visualization.orchestration_tracker import get_orchestration_tracker
    ORCHESTRATION_TRACKER_AVAILABLE = True
except ImportError:
    logger.warning("无法导入orchestration_tracker，使用降级模式")
    ORCHESTRATION_TRACKER_AVAILABLE = False


class WorkflowTracker:
    """兼容性的WorkflowTracker类"""

    def __init__(self):
        self.executions = {}
        if ORCHESTRATION_TRACKER_AVAILABLE:
            self.orchestration_tracker = get_orchestration_tracker()
        else:
            self.orchestration_tracker = None

    async def broadcast_update(self, execution_id: str, data: Dict[str, Any]):
        """广播更新（兼容性方法）"""
        if ORCHESTRATION_TRACKER_AVAILABLE:
            logger.info(f"WorkflowTracker广播更新: {execution_id}")
            # 这里可以委托给WebSocket服务器
            await asyncio.sleep(0)  # 保持async但不阻塞
        else:
            logger.warning("WorkflowTracker不可用，broadcast_update被跳过")
            await asyncio.sleep(0)  # 保持async但不阻塞

    async def track_execution(self, execution_id: str, workflow, initial_state: dict):
        """跟踪执行（兼容性方法）"""
        if ORCHESTRATION_TRACKER_AVAILABLE:
            logger.info(f"WorkflowTracker跟踪执行: {execution_id}")
            # 这里可以委托给相应的服务
            await asyncio.sleep(0)  # 保持async但不阻塞
        else:
            logger.warning("WorkflowTracker不可用，track_execution被跳过")
            await asyncio.sleep(0)  # 保持async但不阻塞