"""
WebSocket服务模块
处理实时WebSocket通信，包括工作流执行状态更新和编排事件广播
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set

from src.visualization.servers.base_server import BaseServer

# 导入相关依赖
try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    WebSocket = None
    WebSocketDisconnect = None
    HTMLResponse = None

logger = logging.getLogger(__name__)


class WebSocketServer(BaseServer):
    """
    WebSocket服务

    处理实时WebSocket通信：
    - 工作流执行状态实时更新
    - 编排事件广播
    - 连接管理和消息路由
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 tracker=None):
        """
        初始化WebSocket服务器

        Args:
            config: 服务器配置
            tracker: 执行跟踪器实例
        """
        super().__init__("websocket_server", config)

        self.tracker = tracker
        self.app: Optional[FastAPI] = None

        # WebSocket连接管理
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.connection_lock = asyncio.Lock()

        # 如果FastAPI不可用，记录警告
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI不可用，WebSocket服务将被禁用")

    async def start(self) -> None:
        """启动WebSocket服务器"""
        if not FASTAPI_AVAILABLE:
            self.logger.error("FastAPI不可用，无法启动WebSocket服务器")
            return

        try:
            # 创建FastAPI应用
            self.app = FastAPI(
                title="RANGEN WebSocket Server",
                description="RANGEN 系统的WebSocket实时通信服务",
                version="1.0.0"
            )

            # 注册路由
            await self._register_routes()

            self.logger.info("✅ WebSocket服务器路由注册完成")
            await super().start()

        except Exception as e:
            await self._handle_startup_error(e)

    async def stop(self) -> None:
        """停止WebSocket服务器"""
        # 关闭所有WebSocket连接
        await self._close_all_connections()

        if self.app:
            self.app = None

        await super().stop()

    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        checks = {}

        # 检查FastAPI可用性
        checks["fastapi"] = {
            "status": "pass" if FASTAPI_AVAILABLE else "fail",
            "message": "FastAPI可用" if FASTAPI_AVAILABLE else "FastAPI不可用"
        }

        # 检查活动连接
        total_connections = sum(len(conns) for conns in self.active_connections.values())
        checks["websocket_connections"] = {
            "status": "pass",
            "message": f"活动WebSocket连接: {total_connections}",
            "details": {
                "total_connections": total_connections,
                "execution_ids": list(self.active_connections.keys())
            }
        }

        # 检查跟踪器
        if self.tracker:
            checks["tracker"] = {
                "status": "pass",
                "message": "执行跟踪器可用"
            }
        else:
            checks["tracker"] = {
                "status": "warn",
                "message": "执行跟踪器未配置"
            }

        # 确定整体状态
        failed_checks = [k for k, v in checks.items() if v["status"] == "fail"]
        if failed_checks:
            status = "unhealthy"
        else:
            status = "healthy"

        return {
            "status": status,
            "checks": checks,
            "uptime": self.uptime,
            "timestamp": asyncio.get_event_loop().time()
        }

    def get_routes(self) -> List[str]:
        """获取WebSocket路由列表"""
        if not self.app:
            return []

        routes = []
        for route in self.app.routes:
            if hasattr(route, 'path'):
                routes.append(f"WS: {route.path}")
        return routes

    async def _register_routes(self) -> None:
        """注册WebSocket路由"""
        if not self.app:
            return

        @self.app.get("/", response_class=HTMLResponse)
        async def websocket_home():
            """WebSocket服务状态页面"""
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>RANGEN WebSocket 服务</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        max-width: 800px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    .header {{
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 30px;
                        text-align: center;
                        position: relative;
                    }}
                    .nav-button {{
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
                    }}
                    .nav-button:hover {{
                        background: rgba(255, 255, 255, 0.3);
                        border-color: rgba(255, 255, 255, 0.5);
                    }}
                    .content {{
                        padding: 30px;
                    }}
                    .ws-info {{
                        text-align: center;
                        margin-bottom: 40px;
                    }}
                    .ws-name {{
                        font-size: 2.5em;
                        font-weight: bold;
                        margin-bottom: 10px;
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }}
                    .ws-description {{
                        color: #888;
                        font-size: 1.1em;
                        margin-bottom: 30px;
                    }}
                    .status-card {{
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        margin-bottom: 20px;
                        border-left: 4px solid #667eea;
                    }}
                    .status-title {{
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 10px;
                    }}
                    .status-value {{
                        color: #666;
                        font-family: monospace;
                    }}
                    .endpoint-card {{
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        border-left: 4px solid #28a745;
                        margin-bottom: 20px;
                    }}
                    .endpoint-url {{
                        font-family: monospace;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 8px;
                        background: #e9ecef;
                        padding: 8px;
                        border-radius: 4px;
                    }}
                    .endpoint-desc {{
                        color: #666;
                        font-size: 14px;
                    }}
                    .code-example {{
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 4px;
                        padding: 15px;
                        margin: 15px 0;
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        white-space: pre-wrap;
                    }}
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
                                活动连接: {len(self.active_connections)}<br>
                                执行ID列表: {list(self.active_connections.keys())}
                            </div>
                        </div>

                        <div class="endpoint-card">
                            <div class="endpoint-url">ws://localhost:8080/ws/{{execution_id}}</div>
                            <div class="endpoint-desc">连接到特定执行ID的WebSocket端点</div>
                        </div>

                        <div class="status-card">
                            <div class="status-title">💡 使用说明</div>
                            <div class="endpoint-desc">
                                WebSocket服务提供实时通信功能，支持工作流执行状态的实时推送。<br>
                                通过连接到相应的执行ID端点，可以实时接收工作流状态更新。
                            </div>
                        </div>

                        <div class="status-card">
                            <div class="status-title">🔧 连接示例</div>
                            <div class="code-example">// JavaScript 连接示例
const ws = new WebSocket('ws://localhost:8080/ws/your-execution-id');

ws.onopen = function(event) {{
    console.log('WebSocket 连接已建立');
}};

ws.onmessage = function(event) {{
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
}};

ws.onclose = function(event) {{
    console.log('WebSocket 连接已关闭');
}};</div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        @self.app.websocket("/ws/{execution_id}")
        async def websocket_endpoint(websocket: WebSocket, execution_id: str):
            """
            WebSocket端点 - 处理执行状态实时更新

            Args:
                websocket: WebSocket连接
                execution_id: 执行ID
            """
            await websocket.accept()

            # 添加到活动连接
            await self._add_connection(execution_id, websocket)

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
                        await self._handle_client_message(execution_id, websocket, data)

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
                await self._remove_connection(execution_id, websocket)

    async def broadcast_update(self, execution_id: str, update_data: Dict[str, Any]) -> None:
        """
        广播执行更新到所有连接的客户端

        Args:
            execution_id: 执行ID
            update_data: 更新数据（可以是 node_update、execution_completed 等）
        """
        if execution_id not in self.active_connections:
            self.logger.warning(f"⚠️ [WebSocket] execution_id={execution_id} 没有活动连接，跳过广播。当前活动连接: {list(self.active_connections.keys())}")
            return
        
        connection_count = len(self.active_connections[execution_id])
        self.logger.info(f"📡 [WebSocket] 准备广播消息: execution_id={execution_id}, 连接数={connection_count}, type={update_data.get('type', 'unknown')}")

        # 🚀 修复：如果 update_data 已经包含 type 字段，直接使用它；否则包装为 execution_update
        if isinstance(update_data, dict) and "type" in update_data:
            # update_data 已经是完整的消息格式（如 {"type": "node_update", "data": {...}}）
            message = update_data.copy()
            message["execution_id"] = execution_id
            if "timestamp" not in message:
                message["timestamp"] = asyncio.get_event_loop().time()
        else:
            # 包装为 execution_update 格式
            message = {
                "type": "execution_update",
                "execution_id": execution_id,
                "data": update_data,
                "timestamp": asyncio.get_event_loop().time()
            }

        # 发送给所有连接的客户端
        disconnected = []
        self.logger.info(f"📡 [WebSocket] 开始向 {len(self.active_connections[execution_id])} 个客户端发送消息")
        for websocket in self.active_connections[execution_id]:
            try:
                self.logger.debug(f"📡 [WebSocket] 发送消息到客户端: {message}")
                await websocket.send_json(message)
                self.logger.debug(f"✅ [WebSocket] 消息发送成功")
            except Exception as e:
                self.logger.warning(f"❌ 发送WebSocket消息失败: {e}")
                disconnected.append(websocket)

        # 移除断开的连接
        for websocket in disconnected:
            await self._remove_connection(execution_id, websocket)

    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """
        广播事件到所有客户端

        Args:
            event_type: 事件类型
            event_data: 事件数据
        """
        message = {
            "type": "event",
            "event_type": event_type,
            "data": event_data,
            "timestamp": asyncio.get_event_loop().time()
        }

        # 发送给所有连接
        disconnected = []
        async with self.connection_lock:
            for execution_id, connections in self.active_connections.items():
                for websocket in connections:
                    try:
                        await websocket.send_json(message)
                    except Exception as e:
                        self.logger.warning(f"广播事件失败: execution_id={execution_id}, error={e}")
                        disconnected.append((execution_id, websocket))

        # 移除断开的连接
        for execution_id, websocket in disconnected:
            await self._remove_connection(execution_id, websocket)

    async def _add_connection(self, execution_id: str, websocket: WebSocket) -> None:
        """添加WebSocket连接"""
        async with self.connection_lock:
            if execution_id not in self.active_connections:
                self.active_connections[execution_id] = set()
            self.active_connections[execution_id].add(websocket)

        self.logger.info(f"WebSocket连接已添加: execution_id={execution_id}, 总连接数={len(self.active_connections[execution_id])}")

    async def _remove_connection(self, execution_id: str, websocket: WebSocket) -> None:
        """移除WebSocket连接"""
        async with self.connection_lock:
            if execution_id in self.active_connections:
                self.active_connections[execution_id].discard(websocket)
                if not self.active_connections[execution_id]:
                    del self.active_connections[execution_id]

        total_connections = sum(len(conns) for conns in self.active_connections.values())
        self.logger.info(f"WebSocket连接已移除: execution_id={execution_id}, 剩余总连接数={total_connections}")

    async def _close_all_connections(self) -> None:
        """关闭所有WebSocket连接"""
        self.logger.info("正在关闭所有WebSocket连接...")

        async with self.connection_lock:
            close_tasks = []
            for execution_id, connections in self.active_connections.items():
                for websocket in connections:
                    close_tasks.append(self._safe_close_websocket(websocket))

            # 并发关闭所有连接
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)

            self.active_connections.clear()

        self.logger.info("所有WebSocket连接已关闭")

    async def _safe_close_websocket(self, websocket: WebSocket) -> None:
        """安全地关闭WebSocket连接"""
        try:
            await websocket.close()
        except Exception as e:
            self.logger.debug(f"关闭WebSocket时出错（可忽略）: {e}")

    async def _handle_client_message(self, execution_id: str, websocket: WebSocket, message: str) -> None:
        """
        处理客户端发送的消息

        Args:
            execution_id: 执行ID
            websocket: WebSocket连接
            message: 客户端消息
        """
        try:
            data = json.loads(message)
            message_type = data.get("type", "unknown")

            if message_type == "ping":
                # 响应ping消息
                await websocket.send_json({
                    "type": "pong",
                    "execution_id": execution_id,
                    "timestamp": asyncio.get_event_loop().time()
                })
            elif message_type == "subscribe":
                # 处理订阅请求
                await websocket.send_json({
                    "type": "subscribed",
                    "execution_id": execution_id,
                    "message": "已订阅执行更新",
                    "timestamp": asyncio.get_event_loop().time()
                })
            elif message_type == "unsubscribe":
                # 处理取消订阅请求
                await websocket.send_json({
                    "type": "unsubscribed",
                    "execution_id": execution_id,
                    "message": "已取消订阅",
                    "timestamp": asyncio.get_event_loop().time()
                })
            else:
                self.logger.warning(f"未知的客户端消息类型: {message_type}")

        except json.JSONDecodeError:
            self.logger.warning(f"无效的JSON消息: {message}")
        except Exception as e:
            self.logger.error(f"处理客户端消息失败: {e}")
            try:
                await websocket.send_json({
                    "type": "error",
                    "execution_id": execution_id,
                    "message": f"处理消息失败: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                })
            except:
                pass

    def get_connection_count(self) -> int:
        """获取总连接数"""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_execution_connections(self) -> Dict[str, int]:
        """获取各执行ID的连接数"""
        return {eid: len(conns) for eid, conns in self.active_connections.items()}

    def get_app(self) -> Optional[FastAPI]:
        """获取FastAPI应用实例"""
        return self.app
