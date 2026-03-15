"""
统一服务管理器
协调和管理所有子服务模块，提供了统一的外部接口
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any, List, Optional

from src.visualization.servers.base_server import BaseServer
from src.visualization.servers.api_server import APIServer
from src.visualization.servers.visualization_server import VisualizationServer
from src.visualization.servers.config_server import ConfigServer
from src.visualization.servers.websocket_server import WebSocketServer

# 导入相关依赖
try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    CORSMiddleware = None
    uvicorn = None

logger = logging.getLogger(__name__)


class UnifiedServerManager(BaseServer):
    """
    统一服务管理器

    协调和管理所有子服务模块：
    - 初始化和配置所有子服务
    - 管理服务生命周期
    - 提供统一的外部接口
    - 处理服务间的依赖和通信
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 workflow_system=None,
                 tracker=None,
                 config_manager=None):
        """
        初始化统一服务管理器

        Args:
            config: 全局配置
            workflow_system: 工作流系统实例
            tracker: 执行跟踪器实例
            config_manager: 配置管理器实例
        """
        super().__init__("unified_server_manager", config)

        self.workflow_system = workflow_system
        self.tracker = tracker
        self.config_manager = config_manager

        # 子服务实例
        self.services: Dict[str, BaseServer] = {}
        self.main_app: Optional[FastAPI] = None
        self._uvicorn_server = None  # 🚀 保存 uvicorn Server 实例，用于优雅关闭

        # 服务配置
        self.service_configs = self._parse_service_configs(config)

        # 初始化子服务
        self._initialize_services()

    def _parse_service_configs(self, config: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """解析服务配置"""
        default_configs = {
            "api_server": {
                "enabled": True,
                "port": 8080,
                "host": "0.0.0.0"
            },
            "visualization_server": {
                "enabled": True,
                "port": 8081,
                "host": "0.0.0.0"
            },
            "config_server": {
                "enabled": True,
                "port": 8082,
                "host": "0.0.0.0"
            },
            "websocket_server": {
                "enabled": True,
                "port": 8083,
                "host": "0.0.0.0"
            }
        }

        if config and "services" in config:
            # 合并用户配置
            for service_name, service_config in config["services"].items():
                if service_name in default_configs:
                    default_configs[service_name].update(service_config)

        return default_configs

    def _initialize_services(self) -> None:
        """初始化所有子服务"""
        # API服务
        if self.service_configs["api_server"]["enabled"]:
            self.services["api"] = APIServer(
                config=self.service_configs["api_server"],
                workflow_system=self.workflow_system,
                tracker=self.tracker
            )

        # 可视化服务
        if self.service_configs["visualization_server"]["enabled"]:
            self.services["visualization"] = VisualizationServer(
                config=self.service_configs["visualization_server"],
                workflow_system=self.workflow_system
            )

        # 配置服务
        if self.service_configs["config_server"]["enabled"]:
            self.services["config"] = ConfigServer(
                config=self.service_configs["config_server"],
                config_manager=self.config_manager
            )

        # WebSocket服务
        if self.service_configs["websocket_server"]["enabled"]:
            self.services["websocket"] = WebSocketServer(
                config=self.service_configs["websocket_server"],
                tracker=self.tracker
            )

    async def start(self) -> None:
        """启动统一服务管理器"""
        self.logger.info(f"🔍 调试: FASTAPI_AVAILABLE = {FASTAPI_AVAILABLE}")
        self.logger.info(f"🔍 调试: FastAPI = {FastAPI}")
        self.logger.info(f"🔍 调试: uvicorn = {uvicorn}")

        if not FASTAPI_AVAILABLE:
            self.logger.error("FastAPI不可用，无法启动统一服务管理器")
            return

        try:
            # 创建主FastAPI应用
            self.main_app = FastAPI(
                title="RANGEN Unified Server",
                description="RANGEN 统一服务器 - 集成多种服务",
                version="1.0.0",
                lifespan=self._lifespan
            )

            # 添加中间件
            self._add_middlewares()

            # 启动子服务（先启动服务，确保app已创建）
            await self._start_services()

            # 挂载子服务（先挂载，让FastAPI的mount机制处理路径）
            await self._mount_services()

            # 添加基础路由（在挂载之后，重定向路由使用较低优先级）
            self._add_base_routes()

            # 启动主服务器
            config = uvicorn.Config(
                self.main_app,
                host=self.get_config("host", "0.0.0.0"),
                port=self.get_config("port", 8080),
                log_level="info"
            )
            self._uvicorn_server = uvicorn.Server(config)

            self.logger.info("✅ 统一服务器启动完成")
            self.logger.info(f"📊 已启动 {len(self.services)} 个子服务")
            await super().start()

            # 运行服务器
            await self._uvicorn_server.serve()

        except Exception as e:
            await self._handle_startup_error(e)

    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """应用生命周期管理"""
        # 启动
        yield
        # 关闭
        await self._stop_services()

    def _add_middlewares(self) -> None:
        """添加中间件"""
        if not self.main_app:
            return

        # CORS中间件
        self.main_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _add_base_routes(self) -> None:
        """添加基础路由"""
        self.logger.info("🔍 调试: _add_base_routes 方法被调用")
        if not self.main_app:
            self.logger.warning("🔍 调试: main_app 未初始化，跳过路由添加")
            return

        # 注意：FastAPI的mount机制会自动处理路径
        # 访问 /service_name 或 /service_name/ 都会正确路由到子应用的 / 路由
        # 不需要手动重定向，避免重定向循环

        @self.main_app.get("/")
        async def root():
            """服务器信息页面"""
            html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RANGEN 统一服务器</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 40px;
            max-width: 800px;
            width: 90%;
            text-align: center;
        }
        .logo {
            font-size: 3em;
            font-weight: bold;
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 20px;
        }
        .subtitle {
            color: #666;
            font-size: 1.2em;
            margin-bottom: 40px;
        }
        .services {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        .service-card {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 25px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border: 2px solid transparent;
        }
        .service-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
            border-color: #667eea;
        }
        .service-icon {
            font-size: 2em;
            margin-bottom: 15px;
        }
        .service-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .service-desc {
            color: #666;
            margin-bottom: 15px;
        }
        .service-link {
            display: inline-block;
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: 500;
            transition: transform 0.2s ease;
        }
        .service-link:hover {
            transform: scale(1.05);
        }
        .footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
        }
        .footer a {
            color: #667eea;
            text-decoration: none;
            margin: 0 10px;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">RANGEN</div>
        <div class="subtitle">统一服务器 - 集成多种服务</div>

        <div class="services">
            <div class="service-card">
                <div class="service-icon">📊</div>
                <div class="service-title">工作流可视化</div>
                <div class="service-desc">LangGraph工作流的实时可视化和监控</div>
                <a href="/visualization" class="service-link">访问可视化</a>
            </div>

            <div class="service-card">
                <div class="service-icon">🔌</div>
                <div class="service-title">REST API</div>
                <div class="service-desc">完整的REST API接口，支持工作流执行和状态查询</div>
                <a href="/api" class="service-link">查看API</a>
            </div>

            <div class="service-card">
                <div class="service-icon">⚙️</div>
                <div class="service-title">配置管理</div>
                <div class="service-desc">系统配置的Web界面管理</div>
                <a href="/config" class="service-link">配置管理</a>
            </div>

            <div class="service-card">
                <div class="service-icon">🔄</div>
                <div class="service-title">实时通信</div>
                <div class="service-desc">WebSocket实时通信和工作流状态推送</div>
                <a href="/ws" class="service-link">查看状态</a>
            </div>
        </div>

        <div class="footer">
            <div style="margin-bottom: 15px;">
                <a href="/health">健康检查</a> |
                <a href="/docs">API文档</a> |
                <a href="https://github.com" target="_blank">GitHub</a>
            </div>
            <div style="font-size: 0.9em; color: #999;">
                RANGEN Unified Server v1.0.0 | 基于LangGraph的工作流引擎
            </div>
        </div>
    </div>
</body>
</html>"""
            return HTMLResponse(content=html_content)

        @self.main_app.get("/.well-known/appspecific/com.chrome.devtools.json")
        async def chrome_devtools_config():
            """Chrome DevTools 配置"""
            return {
                "name": "RANGEN Unified Server",
                "type": "server",
                "url": "http://localhost:8080",
                "webSocketDebuggerUrl": "ws://localhost:8080/ws/debug"
            }

        @self.main_app.get("/health")
        async def health():
            """健康检查"""
            return await self.health_check()
        
        @self.main_app.get("/ws")
        async def websocket_info():
            """WebSocket端点信息页面"""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>RANGEN WebSocket 服务</title>
                <style>
                    body {
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }
                    .container {
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }
                    .header {
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        position: relative;
                    }
                    .nav-button {
                        position: absolute;
                        top: 20px;
                        left: 20px;
                        background: rgba(255, 255, 255, 0.2);
                        color: white;
                        border: 1px solid rgba(255, 255, 255, 0.3);
                        padding: 8px 16px;
                        border-radius: 6px;
                        text-decoration: none;
                        font-size: 14px;
                        transition: all 0.3s ease;
                    }
                    .nav-button:hover {
                        background: rgba(255, 255, 255, 0.3);
                        border-color: rgba(255, 255, 255, 0.5);
                    }
                    .content {
                        padding: 30px;
                    }
                    .ws-info {
                        text-align: center;
                        margin-bottom: 40px;
                    }
                    .ws-name {
                        font-size: 2.5em;
                        font-weight: bold;
                        margin-bottom: 10px;
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }
                    .ws-description {
                        color: #888;
                        font-size: 1.1em;
                        margin-bottom: 30px;
                    }
                    .status-card {
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 20px;
                        border-left: 4px solid #667eea;
                    }
                    .status-title {
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 10px;
                    }
                    .status-value {
                        color: #666;
                        font-family: monospace;
                    }
                    .endpoint-card {
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        border-left: 4px solid #28a745;
                        margin-bottom: 20px;
                    }
                    .endpoint-url {
                        font-family: monospace;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 8px;
                        background: #e9ecef;
                        padding: 8px;
                        border-radius: 4px;
                    }
                    .endpoint-desc {
                        color: #666;
                        font-size: 14px;
                    }
                    .code-example {
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 15px 0;
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        white-space: pre-wrap;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <a href="/" class="nav-button">← 返回首页</a>
                        <div class="ws-info">
                            <div class="ws-name">🔄 WebSocket 服务</div>
                            <div class="ws-description">实时通信和工作流状态推送</div>
                        </div>
                    </div>
                    <div class="content">
                        <div class="status-card">
                            <div class="status-title">📊 服务状态</div>
                            <div class="status-value">
                                WebSocket服务已启用<br>
                                端点路径: /ws/&#123;execution_id&#125;
                            </div>
                        </div>

                        <div class="endpoint-card">
                            <div class="endpoint-url">ws://localhost:8080/ws/&#123;execution_id&#125;</div>
                            <div class="endpoint-desc">连接到特定执行ID的WebSocket端点</div>
                        </div>

                        <div class="status-card">
                            <div class="status-title">💡 使用说明</div>
                            <div class="endpoint-desc">
                                WebSocket服务提供实时通信功能，支持工作流执行状态的实时推送。<br>
                                通过连接到相应的执行ID端点，可以实时接收工作流状态更新。<br>
                                <strong>注意</strong>: 必须提供有效的execution_id参数，不能直接连接到/ws路径。
                            </div>
                        </div>

                        <div class="status-card">
                            <div class="status-title">🔧 连接示例</div>
                            <div class="code-example">// JavaScript 连接示例
// 注意：必须提供执行ID
const executionId = 'your-execution-id-here';
const ws = new WebSocket('ws://localhost:8080/ws/' + executionId);

ws.onopen = function(event) {
    console.log('WebSocket 连接已建立');
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onclose = function(event) {
    console.log('WebSocket 连接已关闭');
};</div>
                        </div>

                        <div class="status-card">
                            <div class="status-title">⚠️ 常见错误</div>
                            <div class="endpoint-desc">
                                <strong>404 错误</strong>: 如果直接连接到 /ws（没有execution_id），会出现404错误。<br>
                                <strong>解决方案</strong>: 确保提供有效的execution_id参数。
                            </div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        # 🚀 新增：在主应用上直接注册 WebSocket 路由，方便前端连接
        self.logger.info(f"🔍 调试: 检查WebSocket服务，self.services.keys() = {list(self.services.keys())}")
        self.logger.info(f"🔍 调试: 'websocket' in self.services = {'websocket' in self.services}")
        if "websocket" in self.services:
            websocket_server = self.services["websocket"]
            self.logger.info(f"🔍 调试: WebSocket服务找到: {websocket_server}")
            
            # 直接在主应用上注册 WebSocket 路由
            from fastapi import WebSocket, WebSocketDisconnect
            
            @self.main_app.websocket("/ws/{execution_id}")
            async def websocket_endpoint(websocket: WebSocket, execution_id: str):
                """WebSocket 端点 - 代理到 WebSocket 服务器"""
                await websocket.accept()
                
                # 调用 WebSocket 服务器的连接处理逻辑
                if hasattr(websocket_server, '_add_connection'):
                    await websocket_server._add_connection(execution_id, websocket)
                
                try:
                    # 发送欢迎消息
                    await websocket.send_json({
                        "type": "welcome",
                        "execution_id": execution_id,
                        "message": "WebSocket连接已建立",
                        "timestamp": asyncio.get_event_loop().time()
                    })
                    
                    # 保持连接并处理消息
                    while True:
                        try:
                            # 接收消息（可选，用于双向通信）
                            data = await asyncio.wait_for(
                                websocket.receive_text(),
                                timeout=30.0  # 30秒超时
                            )
                            
                            # 处理客户端消息
                            if hasattr(websocket_server, '_handle_client_message'):
                                await websocket_server._handle_client_message(execution_id, websocket, data)
                            
                        except asyncio.TimeoutError:
                            # 发送心跳消息
                            await websocket.send_json({
                                "type": "heartbeat",
                                "execution_id": execution_id,
                                "timestamp": asyncio.get_event_loop().time()
                            })
                
                except WebSocketDisconnect:
                    self.logger.info(f"WebSocket连接断开: execution_id={execution_id}")
                except Exception as e:
                    self.logger.error(f"WebSocket处理错误: execution_id={execution_id}, error={e}")
                    try:
                        await websocket.send_json({
                            "type": "error",
                            "execution_id": execution_id,
                            "message": f"处理错误: {str(e)}",
                            "timestamp": asyncio.get_event_loop().time()
                        })
                    except:
                        pass  # 发送错误消息失败，忽略
                finally:
                    # 移除连接
                    if hasattr(websocket_server, '_remove_connection'):
                        await websocket_server._remove_connection(execution_id, websocket)
            
            self.logger.info("✅ 已在主应用上注册 WebSocket 路由: /ws/{execution_id}")

    async def _mount_services(self) -> None:
        """挂载子服务到主应用"""
        if not self.main_app:
            return

        for service_name, service in self.services.items():
            if hasattr(service, 'get_app') and service.get_app():
                service_app = service.get_app()
                mount_path = f"/{service_name}"

                # 使用mount挂载子应用
                # FastAPI的mount会自动处理路径匹配
                # 访问 /service_name 或 /service_name/ 都会路由到子应用的 /
                self.main_app.mount(mount_path, service_app)
                
                self.logger.info(f"✅ 已挂载服务: {service_name} -> {mount_path}")

    async def _start_services(self) -> None:
        """启动所有子服务"""
        start_tasks = []
        for service_name, service in self.services.items():
            start_tasks.append(self._start_service(service_name, service))

        if start_tasks:
            await asyncio.gather(*start_tasks, return_exceptions=True)
        
        # 🚀 新增：设置服务器间引用
        if "visualization" in self.services and "websocket" in self.services:
            visualization_server = self.services["visualization"]
            websocket_server = self.services["websocket"]

            # 设置WebSocket服务器引用到VisualizationServer
            if hasattr(visualization_server, 'set_websocket_server'):
                visualization_server.set_websocket_server(websocket_server)
                self.logger.info("✅ WebSocket服务器引用已设置到VisualizationServer")

            # 🚀 新增：设置VisualizationServer引用到APIServer
            if "api" in self.services:
                api_server = self.services["api"]
                if hasattr(api_server, 'set_visualization_server'):
                    api_server.set_visualization_server(visualization_server)
                    self.logger.info("✅ VisualizationServer引用已设置到APIServer")

    async def _start_service(self, service_name: str, service: BaseServer) -> None:
        """启动单个服务"""
        try:
            await service.start()
            self.logger.info(f"✅ 子服务启动成功: {service_name}")
        except Exception as e:
            self.logger.error(f"❌ 子服务启动失败: {service_name} - {e}")

    async def stop(self) -> None:
        """停止统一服务管理器"""
        # 🚀 修复：设置 uvicorn Server 的 should_exit 标志，让它优雅退出
        if self._uvicorn_server:
            self._uvicorn_server.should_exit = True
            self.logger.info("🛑 已设置 uvicorn Server 退出标志")
        
        await self._stop_services()
        await super().stop()

    async def _stop_services(self) -> None:
        """停止所有子服务"""
        stop_tasks = []
        for service_name, service in self.services.items():
            stop_tasks.append(self._stop_service(service_name, service))

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def _stop_service(self, service_name: str, service: BaseServer) -> None:
        """停止单个服务"""
        try:
            await service.stop()
            self.logger.info(f"🛑 子服务已停止: {service_name}")
        except Exception as e:
            self.logger.error(f"❌ 停止子服务失败: {service_name} - {e}")

    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        checks = {}

        # 检查主应用
        checks["main_app"] = {
            "status": "pass" if self.main_app else "fail",
            "message": "主应用已初始化" if self.main_app else "主应用未初始化"
        }

        # 检查各子服务
        service_checks = {}
        for service_name, service in self.services.items():
            try:
                service_health = await service.health_check()
                service_checks[service_name] = service_health
            except Exception as e:
                service_checks[service_name] = {
                    "status": "error",
                    "error": str(e)
                }

        checks["services"] = {
            "status": "pass" if all(s.get("status") == "healthy" for s in service_checks.values()) else "degraded",
            "message": f"子服务状态检查完成",
            "details": service_checks
        }

        # 确定整体状态
        failed_checks = [k for k, v in checks.items() if v["status"] in ["fail", "error"]]
        if failed_checks:
            status = "unhealthy"
        elif any(v["status"] == "degraded" for v in checks.values()):
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "checks": checks,
            "uptime": self.uptime,
            "timestamp": asyncio.get_event_loop().time()
        }

    def get_routes(self) -> List[str]:
        """获取所有路由列表"""
        routes = []
        for service_name, service in self.services.items():
            service_routes = service.get_routes()
            routes.extend([f"{service_name.upper()}: {route}" for route in service_routes])

        # 添加主应用路由
        if self.main_app:
            for route in self.main_app.routes:
                if hasattr(route, 'path'):
                    routes.append(f"MAIN: {route.path}")

        return routes

    def get_service(self, service_name: str) -> Optional[BaseServer]:
        """获取指定的子服务实例"""
        return self.services.get(service_name)

    def get_service_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务配置"""
        return self.service_configs.copy()

    def update_service_config(self, service_name: str, config: Dict[str, Any]) -> None:
        """更新服务配置"""
        if service_name in self.service_configs:
            self.service_configs[service_name].update(config)
            self.logger.info(f"🔧 服务配置已更新: {service_name}")

            # 如果服务正在运行，通知服务更新配置
            if service_name in self.services:
                service = self.services[service_name]
                service.update_config(config)

    async def broadcast_to_websocket(self, execution_id: str, data: Dict[str, Any]) -> None:
        """广播消息到WebSocket服务"""
        websocket_service = self.get_service("websocket")
        if websocket_service and hasattr(websocket_service, 'broadcast_update'):
            await websocket_service.broadcast_update(execution_id, data)

    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有服务状态"""
        status = {}
        for service_name, service in self.services.items():
            status[service_name] = {
                "running": service.is_running,
                "uptime": service.uptime,
                "config": self.service_configs.get(service_name, {})
            }
        return status

    def get_app(self) -> Optional[FastAPI]:
        """获取主FastAPI应用实例"""
        return self.main_app
