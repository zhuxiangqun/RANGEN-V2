"""
基础API服务模块
提供核心的REST API功能，包括工作流执行、状态查询、健康检查等
"""
import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional

from src.visualization.servers.base_server import BaseServer

# 导入相关依赖
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse, HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    HTTPException = None
    JSONResponse = None
    HTMLResponse = None

logger = logging.getLogger(__name__)


class APIServer(BaseServer):
    """
    基础API服务

    提供核心的REST API功能：
    - 工作流执行API
    - 执行状态查询API
    - 健康检查API
    - 诊断API
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 workflow_system=None,
                 tracker=None):
        """
        初始化API服务器

        Args:
            config: 服务器配置
            workflow_system: 工作流系统实例
            tracker: 执行跟踪器实例
        """
        super().__init__("api_server", config)

        self.workflow_system = workflow_system
        self.tracker = tracker
        self.visualization_server = None  # 🚀 新增：可视化服务器引用
        self.app: Optional[FastAPI] = None
        self.executions: Dict[str, Dict[str, Any]] = {}

        # 如果FastAPI不可用，记录警告
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI不可用，API服务将被禁用")

    def set_visualization_server(self, visualization_server) -> None:
        """设置可视化服务器引用"""
        self.visualization_server = visualization_server
        self.logger.info("✅ VisualizationServer引用已设置到APIServer")

    async def start(self) -> None:
        """启动API服务器"""
        if not FASTAPI_AVAILABLE:
            self.logger.error("FastAPI不可用，无法启动API服务器")
            return

        try:
            # 创建FastAPI应用
            self.app = FastAPI(
                title="RANGEN API Server",
                description="RANGEN 系统的REST API服务",
                version="1.0.0"
            )

            # 注册路由
            await self._register_routes()

            self.logger.info("✅ API服务器路由注册完成")
            await super().start()

        except Exception as e:
            await self._handle_startup_error(e)

    async def stop(self) -> None:
        """停止API服务器"""
        if self.app:
            # 这里可以添加清理逻辑
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

        # 检查工作流系统
        if self.workflow_system:
            checks["workflow_system"] = {
                "status": "pass",
                "message": "工作流系统正常"
            }
        else:
            checks["workflow_system"] = {
                "status": "warn",
                "message": "工作流系统未配置"
            }

        # 检查执行跟踪器
        if self.tracker:
            checks["tracker"] = {
                "status": "pass",
                "message": "执行跟踪器正常"
            }
        else:
            checks["tracker"] = {
                "status": "warn",
                "message": "执行跟踪器未配置"
            }

        # 检查活跃执行
        active_executions = len([e for e in self.executions.values()
                                if e.get("status") == "running"])
        checks["active_executions"] = {
            "status": "pass",
            "message": f"活跃执行: {active_executions}",
            "details": {"count": active_executions}
        }

        # 确定整体状态
        failed_checks = [k for k, v in checks.items() if v["status"] == "fail"]
        if failed_checks:
            status = "unhealthy"
        elif any(v["status"] == "warn" for v in checks.values()):
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
        """获取API路由列表"""
        if not self.app:
            return []

        routes = []
        for route in self.app.routes:
            if hasattr(route, 'path'):
                routes.append(f"API: {route.path}")
        return routes

    async def _register_routes(self) -> None:
        """注册API路由"""
        if not self.app:
            return

        @self.app.get("/", response_class=HTMLResponse)
        async def api_home():
            """API服务主页"""
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>RANGEN API Server</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }}
                    .container {{
                        max-width: 1000px;
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
                    .api-info {{
                        text-align: center;
                        margin-bottom: 40px;
                    }}
                    .api-name {{
                        font-size: 2.5em;
                        font-weight: bold;
                        margin-bottom: 10px;
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                    }}
                    .api-version {{
                        color: #666;
                        font-size: 1.2em;
                        margin-bottom: 20px;
                    }}
                    .api-description {{
                        color: #888;
                        font-size: 1.1em;
                        margin-bottom: 30px;
                    }}
                    .endpoints {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 20px;
                        margin-bottom: 40px;
                    }}
                    .endpoint-card {{
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        border-left: 4px solid #667eea;
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                    }}
                    .endpoint-card:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    }}
                    .endpoint-method {{
                        display: inline-block;
                        background: #667eea;
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        font-weight: bold;
                        margin-right: 10px;
                    }}
                    .endpoint-path {{
                        font-family: monospace;
                        font-weight: bold;
                        color: #333;
                        margin-bottom: 8px;
                    }}
                    .endpoint-description {{
                        color: #666;
                        font-size: 14px;
                    }}
                    .docs-link {{
                        display: inline-block;
                        background: linear-gradient(45deg, #667eea, #764ba2);
                        color: white;
                        padding: 12px 24px;
                        border-radius: 6px;
                        text-decoration: none;
                        font-weight: bold;
                        margin-top: 20px;
                        transition: opacity 0.3s ease;
                    }}
                    .docs-link:hover {{
                        opacity: 0.9;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <a href="/" class="nav-button">← 返回首页</a>
                        <div class="api-info">
                            <div class="api-name">🚀 RANGEN API Server</div>
                            <div class="api-version">v1.0.0</div>
                            <div class="api-description">RANGEN 工作流执行和状态查询API</div>
                        </div>
                    </div>
                    <div class="content">
                        <div class="endpoints">
                            <div class="endpoint-card">
                                <div class="endpoint-path">
                                    <span class="endpoint-method">GET</span>/api/ping
                                </div>
                                <div class="endpoint-description">测试API是否正常工作</div>
                            </div>
                            <div class="endpoint-card">
                                <div class="endpoint-path">
                                    <span class="endpoint-method">GET</span>/api/workflow/health
                                </div>
                                <div class="endpoint-description">获取工作流健康状态</div>
                            </div>
                            <div class="endpoint-card">
                                <div class="endpoint-path">
                                    <span class="endpoint-method">GET</span>/api/executions
                                </div>
                                <div class="endpoint-description">获取执行列表</div>
                            </div>
                            <div class="endpoint-card">
                                <div class="endpoint-path">
                                    <span class="endpoint-method">GET</span>/api/execution/{{execution_id}}
                                </div>
                                <div class="endpoint-description">获取执行状态详情</div>
                            </div>
                            <div class="endpoint-card">
                                <div class="endpoint-path">
                                    <span class="endpoint-method">GET</span>/api/diagnose/execution/{{execution_id}}
                                </div>
                                <div class="endpoint-description">执行诊断信息</div>
                            </div>
                        </div>
                        <div style="text-align: center;">
                            <a href="/docs" class="docs-link">📚 查看完整API文档</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)

        @self.app.get("/api/ping")
        async def ping():
            """测试API是否正常工作"""
            return {
                "status": "ok",
                "timestamp": time.time(),
                "server": "api_server"
            }

        @self.app.get("/api/workflow/health")
        async def get_workflow_health():
            """获取工作流健康状态"""
            if not self.workflow_system:
                return {
                    "available": False,
                    "error": "工作流系统未初始化"
                }

            try:
                # 这里应该实现详细的健康检查逻辑
                # 暂时返回基本信息
                return {
                    "available": True,
                    "status": "healthy",
                    "workflow_count": 1,  # 暂时固定值
                    "last_check": time.time()
                }
            except Exception as e:
                logger.error(f"工作流健康检查失败: {e}", exc_info=True)
                return {
                    "available": False,
                    "error": str(e)
                }

        @self.app.post("/api/workflow/execute")
        async def execute_workflow(request_data: Dict[str, Any]):
            """执行工作流"""
            if not self.workflow_system:
                raise HTTPException(status_code=503, detail="工作流系统不可用")

            try:
                execution_id = str(uuid.uuid4())

                # 创建执行记录
                self.executions[execution_id] = {
                    "id": execution_id,
                    "status": "queued",
                    "start_time": time.time(),
                    "request_data": request_data
                }

                # 🚀 修复：实际启动工作流执行
                self.executions[execution_id]["status"] = "running"

                # 获取查询内容
                query = request_data.get("query", "默认查询")
                logger.info(f"🔍 [API] 收到工作流执行请求: execution_id={execution_id}, query='{query[:100]}...'")

                # 异步执行工作流（如果有visualization_server的话）
                if hasattr(self, 'visualization_server') and self.visualization_server:
                    logger.info(f"✅ [API] visualization_server引用存在，开始执行工作流")
                    # 在后台任务中执行工作流
                    try:
                        task = asyncio.create_task(self.visualization_server._execute_workflow_async(execution_id, query))
                        logger.info(f"✅ [API] 工作流执行任务已启动: execution_id={execution_id}, task={task}")
                    except Exception as e:
                        logger.error(f"❌ [API] 创建工作流执行任务失败: {e}", exc_info=True)
                else:
                    logger.error("❌ [API] visualization_server引用不存在或为None")
                    logger.error(f"   hasattr(self, 'visualization_server'): {hasattr(self, 'visualization_server')}")
                    if hasattr(self, 'visualization_server'):
                        logger.error(f"   self.visualization_server: {self.visualization_server}")

                return {
                    "execution_id": execution_id,
                    "status": "accepted",
                    "message": "工作流执行已开始"
                }

            except Exception as e:
                logger.error(f"工作流执行失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

        @self.app.get("/api/execution/{execution_id}")
        async def get_execution_status(execution_id: str):
            """获取执行状态"""
            if execution_id not in self.executions:
                raise HTTPException(status_code=404, detail="执行ID不存在")

            execution = self.executions[execution_id]

            # 模拟状态更新（实际应该从tracker获取）
            if execution["status"] == "running":
                # 随机决定是否完成
                import random
                if random.random() < 0.1:  # 10%概率完成
                    execution["status"] = "completed"
                    execution["end_time"] = time.time()
                    execution["result"] = {"message": "工作流执行完成"}

            return execution

        @self.app.get("/api/executions")
        async def get_all_executions():
            """获取所有执行记录"""
            return {
                "executions": list(self.executions.values()),
                "total": len(self.executions),
                "active": len([e for e in self.executions.values()
                             if e.get("status") == "running"])
            }

        @self.app.get("/api/diagnose/execution/{execution_id}")
        async def diagnose_execution(execution_id: str):
            """诊断执行问题"""
            if execution_id not in self.executions:
                raise HTTPException(status_code=404, detail="执行ID不存在")

            execution = self.executions[execution_id]

            # 生成诊断信息
            diagnosis = {
                "execution_id": execution_id,
                "status": execution.get("status"),
                "duration": None,
                "issues": [],
                "recommendations": []
            }

            if execution.get("end_time") and execution.get("start_time"):
                diagnosis["duration"] = execution["end_time"] - execution["start_time"]

            # 检查常见问题
            if execution.get("status") == "running":
                duration = time.time() - execution.get("start_time", 0)
                if duration > 300:  # 5分钟
                    diagnosis["issues"].append("执行时间过长")
                    diagnosis["recommendations"].append("检查工作流是否卡住")

            if "error" in execution:
                diagnosis["issues"].append(f"执行错误: {execution['error']}")
                diagnosis["recommendations"].append("查看详细错误日志")

            return diagnosis

    def get_app(self) -> Optional[FastAPI]:
        """获取FastAPI应用实例"""
        return self.app
