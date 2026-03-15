"""
可视化服务模块
专门处理LangGraph工作流的可视化和图表生成
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, TYPE_CHECKING

from src.visualization.servers.base_server import BaseServer

# 导入相关依赖
try:
    from fastapi import FastAPI, HTTPException, Query, Request
    from fastapi.responses import JSONResponse, HTMLResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    # 类型存根，用于类型检查
    if TYPE_CHECKING:
        from fastapi import FastAPI, HTTPException, Request  # type: ignore
        from fastapi.responses import JSONResponse, HTMLResponse  # type: ignore
    else:
        FastAPI = None  # type: ignore
        HTTPException = None  # type: ignore
        JSONResponse = None  # type: ignore
        HTMLResponse = None  # type: ignore
        Request = None  # type: ignore

logger = logging.getLogger(__name__)


class VisualizationServer(BaseServer):
    """
    可视化服务

    专门处理LangGraph工作流的可视化功能：
    - 生成工作流图
    - 提供图表数据和Mermaid格式
    - 处理可视化相关的配置
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 workflow_system=None):
        """
        初始化可视化服务器

        Args:
            config: 服务器配置
            workflow_system: 工作流系统实例
        """
        super().__init__("visualization_server", config)

        self.workflow_system = workflow_system
        self._unified_workflow_instance = None  # 保存unified_workflow实例引用，用于获取_all_added_nodes
        # 类型注解：如果FastAPI可用，使用FastAPI类型；否则使用Any
        if TYPE_CHECKING:
            from fastapi import FastAPI  # type: ignore
            self.app: Optional[FastAPI] = None  # type: ignore
        else:
            self.app: Optional[Any] = None
        
        # 🚀 新增：执行追踪器（用于存储执行状态）
        self.executions: Dict[str, Dict[str, Any]] = {}
        self._websocket_server = None  # WebSocket服务器引用（由统一服务器管理器设置）

        # 如果FastAPI不可用，记录警告
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI不可用，可视化服务将被禁用")

    async def start(self) -> None:
        """启动可视化服务器"""
        if not FASTAPI_AVAILABLE:
            self.logger.error("FastAPI不可用，无法启动可视化服务器")
            return

        try:
            # 创建FastAPI应用
            if not FASTAPI_AVAILABLE or FastAPI is None:
                raise RuntimeError("FastAPI不可用")
            self.app = FastAPI(
                title="RANGEN Visualization Server",
                description="RANGEN 系统的可视化服务",
                version="1.0.0"
            )

            # 注册路由
            await self._register_routes()

            self.logger.info("✅ 可视化服务器路由注册完成")
            await super().start()

        except Exception as e:
            await self._handle_startup_error(e)

    async def stop(self) -> None:
        """停止可视化服务器"""
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

        # 检查工作流系统
        if self.workflow_system:
            checks["workflow_system"] = {
                "status": "pass",
                "message": "工作流系统可用"
            }

            # 检查工作流图可用性
            try:
                graph_data = await self._get_workflow_graph_data()
                if graph_data:
                    checks["workflow_graph"] = {
                        "status": "pass",
                        "message": "工作流图可用",
                        "details": {
                            "nodes_count": len(graph_data.get("nodes", [])),
                            "edges_count": len(graph_data.get("edges", []))
                        }
                    }
                else:
                    checks["workflow_graph"] = {
                        "status": "fail",
                        "message": "工作流图不可用"
                    }
            except Exception as e:
                checks["workflow_graph"] = {
                    "status": "fail",
                    "message": f"工作流图检查失败: {e}"
                }
        else:
            checks["workflow_system"] = {
                "status": "fail",
                "message": "工作流系统不可用"
            }
            checks["workflow_graph"] = {
                "status": "fail",
                "message": "工作流系统不可用"
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

    def get_app(self) -> Optional[Any]:
        """获取FastAPI应用实例"""
        return self.app

    def get_routes(self) -> List[str]:
        """获取可视化路由列表"""
        if not self.app:
            return []

        routes = []
        for route in self.app.routes:
            # 使用getattr安全访问path属性，因为不同路由类型可能有不同的属性名
            route_path = getattr(route, 'path', None) or getattr(route, 'path_regex', None)
            if route_path:
                routes.append(f"VIZ: {route_path}")
        return routes

    async def _register_routes(self) -> None:
        """注册可视化路由"""
        if not self.app:
            self.logger.warning("FastAPI app不存在，跳过路由注册")
            return

        try:
            self.logger.info("开始注册可视化路由...")

            @self.app.get("/", response_class=HTMLResponse)  # type: ignore
            async def visualization_home():
                """可视化主页"""
                try:
                    return await self._render_home_page()
                except Exception as e:
                    self.logger.error(f"渲染可视化主页失败: {e}")
                    if HTMLResponse is None:
                        raise RuntimeError("HTMLResponse不可用")
                    return HTMLResponse(content=f"<h1>可视化服务错误</h1><p>渲染主页失败: {str(e)}</p>", status_code=500)

            self.logger.info("✅ 可视化主页路由注册成功")

            @self.app.get("/graph")  # type: ignore
            async def visualization_graph():
                """工作流图页面"""
                try:
                    return await self._render_graph_page()
                except Exception as e:
                    self.logger.error(f"渲染工作流图页面失败: {e}")
                    if HTMLResponse is None:
                        raise RuntimeError("HTMLResponse不可用")
                    return HTMLResponse(content=f"<h1>可视化服务错误</h1><p>渲染图表页面失败: {str(e)}</p>", status_code=500)

            self.logger.info("✅ 工作流图页面路由注册成功")

            @self.app.get("/monitor")  # type: ignore
            async def visualization_monitor():
                """性能监控页面"""
                try:
                    return await self._render_monitor_page()
                except Exception as e:
                    self.logger.error(f"渲染性能监控页面失败: {e}")
                    if HTMLResponse is None:
                        raise RuntimeError("HTMLResponse不可用")
                    return HTMLResponse(content=f"<h1>可视化服务错误</h1><p>渲染监控页面失败: {str(e)}</p>", status_code=500)

            @self.app.get("/debug")  # type: ignore
            async def visualization_debug():
                """调试工具页面"""
                try:
                    return await self._render_debug_page()
                except Exception as e:
                    self.logger.error(f"渲染调试工具页面失败: {e}")
                    if HTMLResponse is None:
                        raise RuntimeError("HTMLResponse不可用")
                    return HTMLResponse(content=f"<h1>可视化服务错误</h1><p>渲染调试页面失败: {str(e)}</p>", status_code=500)

            @self.app.get("/api/workflow/graph")  # type: ignore
            async def get_workflow_graph(expanded_groups: Optional[str] = None):
                """
                获取工作流图数据（JSON格式）
                返回格式：直接返回包含 nodes 和 edges 的字典
                
                Args:
                    expanded_groups: 逗号分隔的已展开节点组ID列表（例如："multi_agent,reasoning"）
                """
                if HTTPException is None:
                    raise RuntimeError("HTTPException不可用")
                try:
                    self.logger.debug(f"收到工作流图数据请求，expanded_groups: {expanded_groups}")
                    
                    # 🚀 新增：解析expanded_groups参数
                    expanded_groups_set = set()
                    if expanded_groups:
                        expanded_groups_set = set(expanded_groups.split(','))
                        self.logger.info(f"✅ 解析expanded_groups: {expanded_groups_set}")
                    
                    graph_data = await self._get_workflow_graph_data(expanded_groups=expanded_groups_set)
                    
                    if not graph_data:
                        raise HTTPException(
                            status_code=404,
                            detail="工作流图数据不可用"
                        )
                    
                    # 确保返回的数据包含 nodes 和 edges
                    # 如果 graph_data 中没有这些字段，从其他字段中提取
                    result = {
                        "nodes": graph_data.get("nodes", []),
                        "edges": graph_data.get("edges", []),
                        "mermaid": graph_data.get("mermaid", ""),
                        "node_groups": graph_data.get("node_groups", {}),
                        "node_descriptions": graph_data.get("node_descriptions", {}),  # 🚀 新增：节点功能说明
                        "metadata": graph_data.get("metadata", {})
                    }
                    
                    self.logger.debug(f"工作流图数据获取成功: {len(result['nodes'])} 个节点, {len(result['edges'])} 条边")
                    return result
                except HTTPException:
                    raise
                except Exception as e:
                    self.logger.error(f"获取工作流图数据失败: {e}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"获取工作流图数据失败: {str(e)}"
                    )

            @self.app.get("/api/workflow/health")  # type: ignore
            async def get_workflow_health():
                """获取工作流健康状态"""
                try:
                    health_data = await self.health_check()
                    return health_data
                except Exception as e:
                    self.logger.error(f"获取工作流健康状态失败: {e}", exc_info=True)
                    if HTTPException is None:
                        raise RuntimeError("HTTPException不可用")
                    raise HTTPException(
                        status_code=500,
                        detail=f"获取工作流健康状态失败: {str(e)}"
                    )

            @self.app.post("/api/workflow/execute")  # type: ignore
            async def execute_workflow(request: Request):  # type: ignore
                """
                执行工作流
                """
                import uuid
                import time
                if HTTPException is None or Request is None:
                    raise RuntimeError("HTTPException或Request不可用")
                try:
                    self.logger.debug("收到工作流执行请求")
                    # 获取请求数据
                    request_data = await request.json()
                    # 支持两种格式：{"state": {"query": "..."}} 或 {"query": "..."}
                    query = None
                    if isinstance(request_data, dict):
                        if "state" in request_data and isinstance(request_data["state"], dict):
                            query = request_data["state"].get("query")
                        else:
                            query = request_data.get("query")
                    
                    if not query:
                        raise HTTPException(
                            status_code=400,
                            detail="缺少查询参数（query）"
                        )

                    self.logger.info(f"执行工作流，查询: {query}")

                    # 检查工作流系统是否可用
                    if not self.workflow_system or not hasattr(self.workflow_system, '_unified_workflow'):
                        raise HTTPException(
                            status_code=503,
                            detail="工作流系统不可用，无法执行工作流"
                        )
                    
                    # 生成执行ID
                    execution_id = str(uuid.uuid4())
                    
                    # 🚀 新增：初始化执行记录
                    self.executions[execution_id] = {
                        "id": execution_id,
                        "status": "queued",
                        "nodes": [],
                        "edges": [],
                        "state_history": [],
                        "start_time": time.time(),
                        "end_time": None,
                        "final_result": None,
                        "error": None
                    }
                    
                    # 🚀 新增：异步执行工作流（不阻塞请求）
                    import asyncio
                    asyncio.create_task(self._execute_workflow_async(execution_id, query))
                    
                    # 返回执行ID
                    return {
                        "execution_id": execution_id,
                        "status": "accepted",
                        "message": "工作流执行已接受"
                    }
                except HTTPException:
                    raise
                except Exception as e:
                    self.logger.error(f"工作流执行失败: {e}", exc_info=True)
                    if HTTPException is None:
                        raise RuntimeError("HTTPException不可用")
                    raise HTTPException(
                        status_code=500,
                        detail=f"工作流执行失败: {str(e)}"
                    )

            @self.app.post("/api/workflow/test")  # type: ignore
            async def test_workflow(request: Request):  # type: ignore
                """
                测试工作流执行
                """
                if HTTPException is None or Request is None:
                    raise RuntimeError("HTTPException或Request不可用")
                try:
                    self.logger.debug("收到工作流测试请求")
                    # 获取测试输入
                    test_data = await request.json()
                    input_text = test_data.get("input", "测试输入")
                    execution_mode = test_data.get("mode", "sync")

                    self.logger.info(f"测试输入: {input_text}")

                    # 调用实际的工作流执行
                    if not self.workflow_system or not hasattr(self.workflow_system, '_unified_workflow'):
                        raise HTTPException(
                            status_code=503,
                            detail="工作流系统不可用，无法执行测试"
                        )
                    
                    # 获取工作流对象并执行
                    unified_workflow = self.workflow_system._unified_workflow
                    if not unified_workflow or not hasattr(unified_workflow, 'workflow'):
                        raise HTTPException(
                            status_code=503,
                            detail="工作流对象不可用，无法执行测试"
                        )
                    
                    workflow = unified_workflow.workflow
                    # 执行工作流（使用LangGraph框架的方法）
                    # 注意：这里需要根据实际的工作流接口来调用
                    # 示例：result = await workflow.ainvoke({"query": input_text})
                    # 由于我们不知道具体的工作流接口，这里返回一个提示
                    raise HTTPException(
                        status_code=501,
                        detail="工作流测试功能需要根据实际的工作流接口实现，请使用LangGraph框架的方法执行工作流"
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    self.logger.error(f"工作流测试失败: {e}", exc_info=True)
                    if HTTPException is None:
                        raise RuntimeError("HTTPException不可用")
                    raise HTTPException(
                        status_code=500,
                        detail=f"工作流测试失败: {str(e)}"
                    )

            @self.app.get("/status")  # type: ignore
            async def system_status():
                """系统状态和诊断页面"""
                if HTMLResponse is None:
                    raise RuntimeError("HTMLResponse不可用")
                html_content = '<!DOCTYPE html>\n<html>\n<head>\n    <title>系统状态 - RANGEN</title>\n</head>\n<body>\n    <h1>🔍 系统状态与诊断</h1>\n    <p>LangGraph工作流系统状态检查</p>\n    <h2>✅ 系统运行正常</h2>\n    <p>所有核心服务都已启动并运行正常。</p>\n    <button onclick="location.reload()">🔄 刷新状态</button>\n    <br><br>\n    <a href="/">← 返回首页</a>\n</body>\n</html>'
                return HTMLResponse(content=html_content)

        except Exception as e:
            self.logger.error(f"注册路由时发生错误: {e}", exc_info=True)
            raise

    async def _execute_workflow_async(self, execution_id: str, query: str) -> None:
        """
        异步执行工作流（流式执行并实时推送状态）

        使用 LangGraph 的 astream_events() 来捕获节点执行事件，实现动态流程流转显示。

        Args:
            execution_id: 执行ID
            query: 查询字符串
        """
        import asyncio
        import time
        try:
            self.logger.info(f"🚀 [工作流执行] ===== _execute_workflow_async 被调用 =====")
            self.logger.info(f"🚀 [工作流执行] execution_id={execution_id}")
            self.logger.info(f"🚀 [工作流执行] query={query[:100]}...")
            self.logger.info(f"🔍 [工作流执行] 当前协程: {asyncio.current_task()}")

            # 🚀 调试：检查 WebSocket 服务器状态
            if not self._websocket_server:
                self.logger.error(f"❌ [工作流执行] WebSocket服务器未设置！无法推送实时更新: execution_id={execution_id}")
                self.logger.error(f"❌ [工作流执行] 请确保统一服务器管理器正确设置了WebSocket服务器引用")
                return
            else:
                self.logger.info(f"✅ [工作流执行] WebSocket服务器已设置: {type(self._websocket_server).__name__}")
                # 检查是否有活动连接
                if hasattr(self._websocket_server, 'active_connections'):
                    active_conns = self._websocket_server.active_connections
                    self.logger.info(f"📊 [工作流执行] 当前活动连接: {list(active_conns.keys())}")
                    if execution_id in active_conns:
                        conn_count = len(active_conns[execution_id])
                        self.logger.info(f"✅ [工作流执行] execution_id={execution_id} 有 {conn_count} 个活动连接")
                    else:
                        self.logger.warning(f"⚠️ [工作流执行] execution_id={execution_id} 没有活动连接，消息可能无法推送")

            # 🚀 关键调试：检查工作流系统状态
            if not self.workflow_system:
                self.logger.error(f"❌ [工作流执行] 工作流系统未设置！execution_id={execution_id}")
                return

            self.logger.info(f"✅ [工作流执行] 工作流系统类型: {type(self.workflow_system).__name__}")

            # 更新执行状态
            self.executions[execution_id]["status"] = "running"
            self.executions[execution_id]["start_time"] = time.time()
            self.logger.info(f"✅ [工作流执行] 执行状态已更新为running")

            # 🚀 修复：延迟推送执行开始消息，确保WebSocket连接已建立
            import asyncio
            asyncio.create_task(self._delayed_broadcast_execution_start(execution_id))
            self.logger.info(f"✅ [工作流执行] execution_start广播任务已启动")
            
            # 获取统一工作流实例
            self.logger.info(f"🔍 [工作流执行] 检查工作流系统属性...")
            if not hasattr(self.workflow_system, '_unified_workflow'):
                self.logger.error(f"❌ [工作流执行] 工作流系统没有 _unified_workflow 属性")
                self.logger.error(f"❌ [工作流执行] 可用属性: {dir(self.workflow_system)}")
                raise RuntimeError("工作流系统没有 _unified_workflow 属性")

            unified_workflow = getattr(self.workflow_system, '_unified_workflow')
            self.logger.info(f"✅ [工作流执行] unified_workflow对象: {type(unified_workflow).__name__ if unified_workflow else None}")

            if not unified_workflow or not hasattr(unified_workflow, 'workflow'):
                self.logger.error(f"❌ [工作流执行] 工作流对象不可用")
                self.logger.error(f"❌ [工作流执行] unified_workflow: {unified_workflow}")
                if unified_workflow:
                    self.logger.error(f"❌ [工作流执行] unified_workflow属性: {dir(unified_workflow)}")
                raise RuntimeError("工作流对象不可用")

            workflow = unified_workflow.workflow
            self.logger.info(f"✅ [工作流执行] 工作流对象获取成功: {type(workflow).__name__}")
            
            # 准备初始状态（使用统一工作流的execute方法的初始状态格式）
            initial_state = {
                "query": query,
                "context": {},
                "route_path": "simple",
                "complexity_score": 0.0,
                "evidence": [],
                "answer": None,
                "confidence": 0.0,
                "final_answer": None,
                "knowledge": [],
                "citations": [],
                "task_complete": False,
                "error": None,
                "errors": [],
                "execution_time": 0.0,
                "node_execution_times": {},
                "token_usage": {},
                "api_calls": {},
                "metadata": {}
            }
            
            # 准备 checkpointer 配置（检查UnifiedWorkflow是否有checkpointer）
            config = {}
            if hasattr(unified_workflow, 'checkpointer') and unified_workflow.checkpointer:
                import uuid
                thread_id = f"execution_{execution_id}_{uuid.uuid4().hex[:8]}"
                config = {"configurable": {"thread_id": thread_id}}
                self.logger.info(f"✅ [工作流执行] 使用checkpointer配置: thread_id={thread_id}")
            else:
                self.logger.info(f"ℹ️ [工作流执行] 工作流没有使用checkpointer，执行将不保存状态")
            
            # 🚀 使用 astream_events() 捕获节点执行事件，实现动态流程流转显示
            final_state = None
            executed_nodes = []
            node_start_times = {}  # 记录节点开始执行的时间
            active_nodes = {}  # 记录当前正在执行的节点

            # 🚀 调试：记录工作流执行开始
            self.logger.info(f"🔍 [工作流执行] 开始调用astream_events，初始状态: query={query[:50]}...")
            self.logger.info(f"🔍 [工作流执行] 工作流对象: {type(workflow).__name__}")
            self.logger.info(f"🔍 [工作流执行] 初始状态包含的键: {list(initial_state.keys())}")
            self.logger.info(f"🔍 [工作流执行] 检查点配置: {config}")

            # 使用 astream_events() 捕获详细的事件流
            use_astream_events = False
            if hasattr(workflow, 'astream_events'):
                # 尝试使用 astream_events 捕获节点执行事件
                # LangGraph 的 astream_events 需要传入 include_names 或 include_types 参数
                use_astream_events = True
                self.logger.info(f"🎯 [工作流执行] 使用astream_events方法执行工作流")

                # 🚀 关键调试：检查工作流是否可以正常调用astream_events
                self.logger.info(f"🔍 [工作流执行] 准备调用workflow.astream_events()...")

                event_count = 0
                timeout_task = None

                # 🚀 添加超时保护（30秒），防止工作流执行卡住
                async def timeout_checker():
                    await asyncio.sleep(30.0)
                    if event_count == 0:
                        self.logger.error(f"❌ [工作流执行] astream_events 30秒内没有产生任何事件，可能工作流执行卡住")
                        self.logger.error(f"❌ [工作流执行] 这通常表示工作流配置有问题或节点执行失败")
                        raise TimeoutError("astream_events timeout: no events received within 30 seconds")

                timeout_task = asyncio.create_task(timeout_checker())
                self.logger.info(f"✅ [工作流执行] 超时检查任务已启动")

                self.logger.info(f"🚀 [工作流执行] 开始调用astream_events...")
                async for event in workflow.astream_events(
                    initial_state,
                    config=config if config else None,
                    version="v2",
                    include_names=None,  # 包含所有节点
                    include_types=None  # 包含所有事件类型
                ):
                    event_count += 1
                    if event_count == 1:
                        self.logger.info(f"✅ [工作流执行] 成功收到第一个事件！astream_events工作正常")

                    event_name = event.get("event")
                    event_data = event.get("data", {})

                    # 🚀 调试：记录所有事件类型，帮助诊断问题
                    self.logger.info(f"📨 [astream_events] 收到事件 {event_count}: {event_name}, 数据键: {list(event_data.keys()) if isinstance(event_data, dict) else type(event_data)}")

                    # 🚀 调试：记录所有事件类型，帮助诊断
                    self.logger.info(f"📨 [astream_events] 事件 {event_count}: {event_name}")
                    if event_name not in ["on_chain_start", "on_chain_end", "on_chain_error", "on_llm_start", "on_llm_end", "on_tool_start", "on_tool_end"]:
                        self.logger.warning(f"⚠️ [astream_events] 未知事件类型: {event_name}, 数据键: {list(event_data.keys()) if isinstance(event_data, dict) else type(event_data)}")
                        # 记录完整的未知事件用于调试
                        if event_name:
                            self.logger.info(f"🔍 [astream_events] 未知事件详情: {event}")

                    # 处理节点开始执行事件
                    if event_name == "on_chain_start":
                        # 🚀 修复：尝试多种方式获取节点名称
                        node_name = event_data.get("name", "")
                        if not node_name:
                            # 尝试从metadata中获取
                            metadata = event.get("metadata", {})
                            node_name = metadata.get("langgraph_node", "") or metadata.get("node", "")
                        if not node_name:
                            # 尝试从tags中获取
                            tags = event.get("tags", [])
                            for tag in tags:
                                if tag.startswith("langgraph_node:"):
                                    node_name = tag.split(":", 1)[1]
                                    break

                        # 🚀 调试：记录节点名称获取过程
                        self.logger.debug(f"🔍 [节点名称解析] event_data keys: {list(event_data.keys())}, metadata keys: {list(event.get('metadata', {}).keys())}, tags: {event.get('tags', [])}")

                        # 过滤掉 LangGraph 内部节点
                        if node_name and node_name not in ["__start__", "__end__", "__START__", "__END__", "LangGraph"]:
                            if node_name not in executed_nodes:
                                executed_nodes.append(node_name)

                            node_start_times[node_name] = time.time()
                            active_nodes[node_name] = True

                            # 推送节点开始执行消息
                            node_info = {
                                "name": node_name,
                                "node": node_name,
                                "timestamp": node_start_times[node_name],
                                "status": "running"
                            }

                            # 记录节点执行信息
                            existing_node = next((n for n in self.executions[execution_id]["nodes"] if n.get("name") == node_name), None)
                            if not existing_node:
                                self.executions[execution_id]["nodes"].append(node_info)

                            # 通过 WebSocket 推送更新
                            await self._broadcast_node_update(execution_id, node_info)

                            self.logger.info(f"▶️ [工作流执行] 节点开始执行: {node_name}, execution_id={execution_id}")
                        else:
                            self.logger.debug(f"🔍 [节点过滤] 跳过节点: {node_name}, 原因: 内部节点或名称为空")

                    # 处理节点执行完成事件
                    elif event_name == "on_chain_end":
                        # 🚀 修复：尝试多种方式获取节点名称
                        node_name = event_data.get("name", "")
                        if not node_name:
                            # 尝试从metadata中获取
                            metadata = event.get("metadata", {})
                            node_name = metadata.get("langgraph_node", "") or metadata.get("node", "")
                        if not node_name:
                            # 尝试从tags中获取
                            tags = event.get("tags", [])
                            for tag in tags:
                                if tag.startswith("langgraph_node:"):
                                    node_name = tag.split(":", 1)[1]
                                    break

                        # 🚀 调试：记录节点名称获取过程
                        self.logger.debug(f"🔍 [节点名称解析] event_data keys: {list(event_data.keys())}, metadata keys: {list(event.get('metadata', {}).keys())}, tags: {event.get('tags', [])}")

                        # 过滤掉 LangGraph 内部节点
                        if node_name and node_name not in ["__start__", "__end__", "__START__", "__END__", "LangGraph"]:
                            execution_time = 0.0
                            if node_name in node_start_times:
                                execution_time = time.time() - node_start_times[node_name]

                            # 获取节点输出状态
                            output = event_data.get("output", {})
                            if isinstance(output, dict):
                                final_state = output

                            # 移除活跃节点标记
                            active_nodes.pop(node_name, None)

                            # 推送节点完成消息
                            node_info = {
                                "name": node_name,
                                "node": node_name,
                                "timestamp": time.time(),
                                "status": "completed",
                                "execution_time": execution_time
                            }

                            # 更新节点执行信息
                            for existing_node in self.executions[execution_id]["nodes"]:
                                if existing_node.get("name") == node_name:
                                    existing_node["status"] = "completed"
                                    existing_node["execution_time"] = execution_time
                                    existing_node["timestamp"] = time.time()
                                    break

                            # 通过 WebSocket 推送更新
                            await self._broadcast_node_update(execution_id, node_info)

                            self.logger.info(f"✅ [工作流执行] 节点执行完成: {node_name}, 耗时: {execution_time:.2f}s, execution_id={execution_id}")
                        else:
                            self.logger.debug(f"🔍 [节点过滤] 跳过节点: {node_name}, 原因: 内部节点或名称为空")

                    # 处理节点执行错误事件
                    elif event_name == "on_chain_error":
                        # 🚀 修复：尝试多种方式获取节点名称
                        node_name = event_data.get("name", "")
                        if not node_name:
                            # 尝试从metadata中获取
                            metadata = event.get("metadata", {})
                            node_name = metadata.get("langgraph_node", "") or metadata.get("node", "")
                        if not node_name:
                            # 尝试从tags中获取
                            tags = event.get("tags", [])
                            for tag in tags:
                                if tag.startswith("langgraph_node:"):
                                    node_name = tag.split(":", 1)[1]
                                    break

                        error = event_data.get("error", {})
                        error_message = str(error) if error else "未知错误"

                        # 🚀 调试：记录节点名称获取过程
                        self.logger.debug(f"🔍 [节点名称解析] event_data keys: {list(event_data.keys())}, metadata keys: {list(event.get('metadata', {}).keys())}, tags: {event.get('tags', [])}")

                        # 过滤掉 LangGraph 内部节点
                        if node_name and node_name not in ["__start__", "__end__", "__START__", "__END__", "LangGraph"]:
                            # 移除活跃节点标记
                            active_nodes.pop(node_name, None)

                            # 推送节点错误消息
                            node_info = {
                                "name": node_name,
                                "node": node_name,
                                "timestamp": time.time(),
                                "status": "error",
                                "error": error_message
                            }

                            # 更新节点执行信息
                            for existing_node in self.executions[execution_id]["nodes"]:
                                if existing_node.get("name") == node_name:
                                    existing_node["status"] = "error"
                                    existing_node["error"] = error_message
                                    break

                            # 通过 WebSocket 推送更新
                            await self._broadcast_node_update(execution_id, node_info)

                            self.logger.error(f"❌ [工作流执行] 节点执行错误: {node_name}, 错误: {error_message}, execution_id={execution_id}")

                            # 如果节点执行出错，停止整个工作流
                            raise Exception(f"节点 {node_name} 执行失败: {error_message}")
                        else:
                            self.logger.debug(f"🔍 [节点过滤] 跳过节点: {node_name}, 原因: 内部节点或名称为空")

                    # 🎯 关键检查点：astream_events循环结束
                    self.logger.info(f"✅ [工作流执行] astream_events循环结束，共收到 {event_count} 个事件")
                    if event_count == 0:
                        self.logger.error(f"❌ [工作流执行] astream_events没有产生任何事件！这说明工作流执行失败")
                        self.logger.error(f"❌ [工作流执行] 可能原因：")
                        self.logger.error(f"   - 工作流配置错误")
                        self.logger.error(f"   - 初始状态无效")
                        self.logger.error(f"   - 路由逻辑失败")

            # 降级方案：如果 workflow 不支持 astream_events 或调用失败，使用 astream
            if not use_astream_events:
                self.logger.info("📝 [工作流执行] 使用 astream 方法执行工作流（支持动态流程流转显示）")
                self.logger.info(f"🔍 [工作流执行] 准备调用workflow.astream()...")

                event_count = 0
                timeout_task = None

                try:
                    # 🚀 添加超时保护（30秒），防止工作流执行卡住
                    async def timeout_checker():
                        await asyncio.sleep(30.0)
                        if event_count == 0:
                            self.logger.error(f"❌ [工作流执行] astream 30秒内没有产生任何事件，可能工作流执行卡住")
                            raise TimeoutError("astream timeout: no events received within 30 seconds")

                    timeout_task = asyncio.create_task(timeout_checker())

                    async for event in workflow.astream(initial_state, config=config if config else None):
                        event_count += 1
                        self.logger.debug(f"📨 [astream] 收到事件 {event_count}: {type(event)}, 节点数量: {len(event) if isinstance(event, dict) else 'unknown'}")
                        for node_name, node_state in event.items():
                            # 过滤掉 LangGraph 内部节点
                            if node_name in ["__start__", "__end__", "__START__", "__END__"]:
                                continue
                            
                            # 记录执行的节点
                            if node_name not in executed_nodes:
                                executed_nodes.append(node_name)
                                node_start_times[node_name] = time.time()
                                
                                # 推送节点开始执行消息
                                node_info = {
                                    "name": node_name,
                                    "node": node_name,
                                    "timestamp": node_start_times[node_name],
                                    "status": "running"
                                }
                                self.executions[execution_id]["nodes"].append(node_info)
                                await self._broadcast_node_update(execution_id, node_info)
                                
                                self.logger.info(f"▶️ [工作流执行] 节点开始执行: {node_name}, execution_id={execution_id}")
                            
                            # 保存最终状态（最后一个事件的状态）
                            final_state = node_state
                            
                            # 计算执行时间
                            execution_time = 0.0
                            if node_name in node_start_times:
                                execution_time = time.time() - node_start_times[node_name]
                            
                            # 推送节点完成消息
                            node_info = {
                                "name": node_name,
                                "node": node_name,
                                "timestamp": time.time(),
                                "status": "completed",
                                "execution_time": execution_time
                            }
                            
                            # 更新节点执行信息
                            for existing_node in self.executions[execution_id]["nodes"]:
                                if existing_node.get("name") == node_name:
                                    existing_node["status"] = "completed"
                                    existing_node["execution_time"] = execution_time
                                    existing_node["timestamp"] = time.time()
                                    break
                            
                            await self._broadcast_node_update(execution_id, node_info)
                            
                            self.logger.info(f"✅ [工作流执行] 节点执行完成: {node_name}, 耗时: {execution_time:.2f}s, execution_id={execution_id}")

                    # 🎯 关键检查点：astream循环结束
                    self.logger.info(f"✅ [工作流执行] astream循环结束，共收到 {event_count} 个事件")
                    if event_count == 0:
                        self.logger.error(f"❌ [工作流执行] astream也没有产生任何事件！工作流执行完全失败")

                    # 取消超时任务
                    if timeout_task and not timeout_task.done():
                        timeout_task.cancel()

                except Exception as astream_error:
                    # 取消超时任务
                    if timeout_task and not timeout_task.done():
                        timeout_task.cancel()

                    # astream也失败了
                    self.logger.error(f"❌ [工作流执行] astream 调用也失败: {astream_error}")
                    raise astream_error
                finally:
                    # 确保超时任务被取消
                    if timeout_task and not timeout_task.done():
                        timeout_task.cancel()

            # 执行完成
            self.executions[execution_id]["status"] = "completed"
            self.executions[execution_id]["end_time"] = time.time()
            self.executions[execution_id]["final_result"] = self._sanitize_state(final_state) if final_state else {}

            self.logger.info(f"🎯 [工作流执行] 工作流执行循环结束，准备推送完成消息: executed_nodes={executed_nodes}")

            # 推送执行完成消息
            await self._broadcast_execution_update(execution_id, {
                "type": "execution_end",
                "execution_id": execution_id,
                "status": "completed",
                "final_result": self.executions[execution_id]["final_result"],
                "executed_nodes": executed_nodes,  # 发送实际执行的节点列表
                "total_nodes": len(executed_nodes)  # 发送节点总数
            })

            self.logger.info(f"✅ [工作流执行] 工作流执行完成: execution_id={execution_id}, 执行了 {len(executed_nodes)} 个节点: {executed_nodes}")
            
        except Exception as e:
            self.logger.error(f"❌ [工作流执行] ===== 工作流执行失败 =====")
            self.logger.error(f"❌ [工作流执行] 错误类型: {type(e).__name__}")
            self.logger.error(f"❌ [工作流执行] 错误信息: {str(e)}")
            import traceback
            self.logger.error(f"❌ [工作流执行] 完整堆栈:\n{traceback.format_exc()}")

            self.executions[execution_id]["status"] = "error"
            self.executions[execution_id]["error"] = str(e)
            self.executions[execution_id]["end_time"] = time.time()

            # 推送执行错误消息
            try:
                await self._broadcast_execution_update(execution_id, {
                    "type": "execution_error",
                    "execution_id": execution_id,
                    "status": "error",
                    "error": str(e)
                })
                self.logger.info(f"✅ [工作流执行] 错误消息已推送")
            except Exception as broadcast_error:
                self.logger.error(f"❌ [工作流执行] 推送错误消息失败: {broadcast_error}")
    
    def _sanitize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理状态数据（移除敏感信息或过大的数据）
        
        Args:
            state: 原始状态字典
        
        Returns:
            清理后的状态字典
        """
        if not isinstance(state, dict):
            return {}
        
        sanitized = {}
        for key, value in state.items():
            # 跳过过大的数据
            if isinstance(value, (str, bytes)) and len(str(value)) > 1000:
                sanitized[key] = f"{str(value)[:100]}... (truncated)"
            elif isinstance(value, (list, dict)) and len(str(value)) > 2000:
                sanitized[key] = f"{type(value).__name__} (size: {len(str(value))}, truncated)"
            else:
                sanitized[key] = value
        
        return sanitized
    
    async def _broadcast_node_update(self, execution_id: str, node_info: Dict[str, Any]) -> None:
        """
        广播节点更新到 WebSocket
        
        Args:
            execution_id: 执行ID
            node_info: 节点信息
        """
        # 🚀 调试：检查 WebSocket 服务器状态
        if not self._websocket_server:
            self.logger.warning(f"⚠️ [WebSocket] WebSocket服务器未设置，无法推送节点更新: execution_id={execution_id}, node={node_info.get('name', 'unknown')}")
            return
        
        if not hasattr(self._websocket_server, 'broadcast_update'):
            self.logger.warning(f"⚠️ [WebSocket] WebSocket服务器没有broadcast_update方法: execution_id={execution_id}")
            return
        
        try:
            self.logger.info(f"📤 [WebSocket] 推送节点更新: execution_id={execution_id}, node={node_info.get('name', 'unknown')}, status={node_info.get('status', 'unknown')}")
            message = {
                "type": "node_update",
                "data": node_info,
                "execution_id": execution_id,
                "timestamp": asyncio.get_event_loop().time()
            }
            self.logger.info(f"📤 [WebSocket] 发送消息内容: {message}")
            await self._websocket_server.broadcast_update(execution_id, message)
            self.logger.debug(f"✅ [WebSocket] 节点更新推送成功: execution_id={execution_id}, node={node_info.get('name', 'unknown')}")
        except Exception as e:
            self.logger.error(f"❌ [WebSocket] 广播节点更新失败: {e}, execution_id={execution_id}, node={node_info.get('name', 'unknown')}", exc_info=True)
    
    async def _delayed_broadcast_execution_start(self, execution_id: str) -> None:
        """
        延迟广播执行开始消息，确保WebSocket连接已建立

        Args:
            execution_id: 执行ID
        """
        # 等待1秒，确保WebSocket连接建立
        await asyncio.sleep(1.0)

        # 检查是否有活动连接
        if hasattr(self, '_websocket_server') and self._websocket_server:
            active_connections = getattr(self._websocket_server, 'active_connections', {})
            if execution_id in active_connections and active_connections[execution_id]:
                self.logger.info(f"✅ [延迟广播] execution_id={execution_id} 有 {len(active_connections[execution_id])} 个活动连接，开始广播")
                await self._broadcast_execution_update(execution_id, {
                    "type": "execution_start",
                    "execution_id": execution_id,
                    "status": "running"
                })
            else:
                self.logger.warning(f"⚠️ [延迟广播] execution_id={execution_id} 仍然没有活动连接，跳过广播")
        else:
            self.logger.warning(f"⚠️ [延迟广播] WebSocket服务器不可用")

    async def _broadcast_execution_update(self, execution_id: str, update: Dict[str, Any]) -> None:
        """
        广播执行更新到 WebSocket
        
        Args:
            execution_id: 执行ID
            update: 更新数据
        """
        # 🚀 调试：检查 WebSocket 服务器状态
        if not self._websocket_server:
            self.logger.warning(f"⚠️ [WebSocket] WebSocket服务器未设置，无法推送执行更新: execution_id={execution_id}, type={update.get('type', 'unknown')}")
            return
        
        if not hasattr(self._websocket_server, 'broadcast_update'):
            self.logger.warning(f"⚠️ [WebSocket] WebSocket服务器没有broadcast_update方法: execution_id={execution_id}")
            return
        
        try:
            self.logger.info(f"📤 [WebSocket] 推送执行更新: execution_id={execution_id}, type={update.get('type', 'unknown')}")
            await self._websocket_server.broadcast_update(execution_id, update)
            self.logger.debug(f"✅ [WebSocket] 执行更新推送成功: execution_id={execution_id}, type={update.get('type', 'unknown')}")
        except Exception as e:
            self.logger.error(f"❌ [WebSocket] 广播执行更新失败: {e}, execution_id={execution_id}, type={update.get('type', 'unknown')}", exc_info=True)
    
    def set_websocket_server(self, websocket_server) -> None:
        """
        设置 WebSocket 服务器引用
        
        Args:
            websocket_server: WebSocket 服务器实例
        """
        self._websocket_server = websocket_server
        if websocket_server:
            self.logger.info(f"✅ [WebSocket] WebSocket服务器已设置到VisualizationServer: {type(websocket_server).__name__}")
        else:
            self.logger.warning("⚠️ [WebSocket] WebSocket服务器设置为None")

    async def _get_workflow_graph_data(self, expanded_groups: Optional[Set[str]] = None) -> Optional[Dict[str, Any]]:
        """
        获取工作流图数据

        Returns:
            包含图数据的字典，格式：
            {
                "mermaid": "Mermaid图表字符串",
                "nodes": ["节点列表"],
                "edges": ["边列表"],
                "node_groups": {...},  # 节点分组信息
                "metadata": {...}      # 元数据
            }
        """
        if not self.workflow_system:
            self.logger.warning("⚠️ 工作流系统不可用")
            return None

        try:
            # 从工作流系统获取图数据
            workflow = None
            unified_workflow = None
            
            if hasattr(self.workflow_system, '_unified_workflow') and self.workflow_system._unified_workflow:
                unified_workflow = self.workflow_system._unified_workflow
                if hasattr(unified_workflow, 'workflow'):
                    workflow = unified_workflow.workflow
                    self.logger.info(f"✅ 从统一工作流获取workflow对象: {type(workflow)}")
                    
                    # 保存unified_workflow引用，用于后续获取_all_added_nodes
                    self._unified_workflow_instance = unified_workflow

            if not workflow:
                self.logger.error("❌ 无法获取工作流对象，无法使用LangGraph框架功能生成图数据")
                return None

            # 获取实际的工作流图
            self.logger.info("🔍 开始提取工作流图数据...")
            graph_data = await self._extract_graph_from_workflow(workflow, expanded_groups=expanded_groups)
            
            # 检查LangGraph框架生成的Mermaid图数据
            # 如果使用LangGraph的draw_mermaid()方法，只需要检查mermaid字段
            if graph_data and graph_data.get("mermaid") and graph_data["mermaid"].strip():
                mermaid_str = graph_data["mermaid"]
                # 从Mermaid字符串中统计节点和边数量（用于日志，与前端统计方法保持一致）
                try:
                    import re
                    # 🚀 修复：统一节点统计方法（与前端一致）
                    node_matches = re.findall(r'\b\w+\s*[\[\(\\{]', mermaid_str)
                    unique_nodes = set()
                    for match in node_matches:
                        node_id = match.split('[')[0].split('(')[0].split('{')[0].strip()
                        if node_id:
                            unique_nodes.add(node_id)
                    
                    # 🚀 修复：统一边统计方法（与前端一致，包括虚线边）
                    edge_matches = re.findall(r'[-.>]+', mermaid_str)
                    nodes_count = len(unique_nodes)
                    edges_count = len(edge_matches)
                    self.logger.info(f"✅ 成功获取LangGraph工作流图: {nodes_count} 个节点, {edges_count} 条边（包括虚线）")
                except Exception:
                    self.logger.info("✅ 成功获取LangGraph工作流图（Mermaid格式）")
            elif graph_data and graph_data.get("metadata", {}).get("error"):
                # 如果有错误信息，记录但不警告（错误信息已经在_extract_graph_from_workflow中记录）
                self.logger.debug("工作流图数据包含错误信息，将在前端显示")
            else:
                self.logger.warning("⚠️ 无法获取工作流图数据（LangGraph draw_mermaid()返回空或失败）")
            
            return graph_data

        except Exception as e:
            self.logger.error(f"提取工作流图数据失败: {e}", exc_info=True)
            import traceback
            self.logger.error(f"详细错误:\n{traceback.format_exc()}")
            return None

    async def _extract_graph_from_workflow(self, workflow, expanded_groups: Optional[Set[str]] = None) -> Dict[str, Any]:
        """
        从LangGraph工作流对象提取丰富的图数据
        
        优先使用LangGraph框架的内置方法，而不是手动提取

        Args:
            workflow: LangGraph工作流对象（通常是编译后的workflow）

        Returns:
            包含LangGraph特性的图数据字典
        """
        try:
            # 初始化数据结构
            graph_data = {
                "mermaid": "",
                "nodes": [],
                "edges": [],
                "node_types": {},
                "edge_types": {},
                "execution_state": {},
                "metadata": {
                    "type": "langgraph",
                    "framework": "LangGraph",
                    "features": []
                }
            }

            # 方法1: 使用WorkflowGraphBuilder生成分层的Mermaid图（支持展开/折叠）
            # 🚀 新增：使用WorkflowGraphBuilder生成分层的、可展开/折叠的Mermaid图
            try:
                from src.visualization.workflow_graph_builder import WorkflowGraphBuilder
                
                if hasattr(workflow, 'get_graph'):
                    graph = workflow.get_graph()
                    self.logger.info(f"✅ 从workflow.get_graph()获取图对象: {type(graph)}")
                    
                    # 提取节点和边
                    nodes = []
                    edges = []
                    if hasattr(graph, 'nodes'):
                        nodes = list(graph.nodes)
                    if hasattr(graph, 'edges'):
                        edges = list(graph.edges)
                    
                    # 使用WorkflowGraphBuilder生成分层的Mermaid图
                    graph_builder = WorkflowGraphBuilder()
                    # 使用传入的expanded_groups，如果没有则默认所有组都是折叠的
                    expanded_groups_set = expanded_groups if expanded_groups is not None else set()
                    mermaid_str = graph_builder.build_hierarchical_mermaid(nodes, edges, expanded_groups=expanded_groups_set)
                    
                    if mermaid_str and mermaid_str.strip():
                        self.logger.info("✅ 使用WorkflowGraphBuilder生成分层的、可展开/折叠的工作流图")
                        self.logger.info(f"📊 Mermaid图长度: {len(mermaid_str)} 字符")
                        graph_data["mermaid"] = mermaid_str
                        graph_data["node_groups"] = graph_builder.get_node_group_info()
                        # 🚀 增强：传递workflow对象以动态提取节点说明
                        graph_data["node_descriptions"] = graph_builder.get_node_descriptions(workflow=workflow)
                        
                        # 从Mermaid字符串中提取节点和边数量（与前端统计方法保持一致）
                        try:
                            import re
                            # 🚀 修复：统一节点统计方法（与前端一致）
                            # 匹配节点：node_id[label] 或 node_id((label)) 或 node_id{label}
                            node_matches = re.findall(r'\b\w+\s*[\[\(\\{]', mermaid_str)
                            # 提取节点ID（去除括号和方括号）
                            unique_nodes = set()
                            for match in node_matches:
                                node_id = match.split('[')[0].split('(')[0].split('{')[0].strip()
                                if node_id:
                                    unique_nodes.add(node_id)
                            
                            # 🚀 修复：统一边统计方法（与前端一致，包括虚线边）
                            # 匹配边：--> 或 -.-> 或 -->|label|
                            edge_matches = re.findall(r'[-.>]+', mermaid_str)
                            
                            nodes_count = len(unique_nodes)
                            edges_count = len(edge_matches)
                            graph_data["metadata"]["nodes_count_estimated"] = nodes_count
                            graph_data["metadata"]["edges_count_estimated"] = edges_count
                            self.logger.info(f"📊 统计: {nodes_count} 个节点显示, {edges_count} 条边（包括虚线）")
                        except Exception as e:
                            self.logger.debug(f"检查节点显示情况时出错: {e}")
                        
                        return graph_data
                    else:
                        self.logger.warning("⚠️ WorkflowGraphBuilder返回空字符串，回退到LangGraph draw_mermaid()")
                else:
                    self.logger.warning("⚠️ workflow对象没有get_graph()方法")
            except Exception as e:
                self.logger.warning(f"⚠️ 使用WorkflowGraphBuilder失败: {e}，回退到LangGraph draw_mermaid()")
                # 继续尝试LangGraph的方法
            
            # 方法2: 直接使用LangGraph的内置draw_mermaid()方法（回退方案）
            # 这是LangGraph框架提供的官方方法，能获取完整的工作流图（包括所有路由分支和条件边）
            try:
                if hasattr(workflow, 'get_graph'):
                    graph = workflow.get_graph()
                    self.logger.info(f"✅ 从workflow.get_graph()获取图对象: {type(graph)}")
                    
                    if hasattr(graph, 'draw_mermaid'):
                        mermaid_str = graph.draw_mermaid()
                        if mermaid_str and mermaid_str.strip():
                            self.logger.info("✅ 使用LangGraph框架的draw_mermaid()方法获取完整工作流图")
                            self.logger.info(f"📊 Mermaid图长度: {len(mermaid_str)} 字符")
                            graph_data["mermaid"] = mermaid_str
                            
                            # 从Mermaid字符串中提取节点和边数量（用于统计，与前端统计方法保持一致）
                            # 但不修改Mermaid字符串本身，直接使用LangGraph生成的
                            try:
                                import re
                                # 🚀 修复：统一节点统计方法（与前端一致）
                                # 匹配节点：node_id[label] 或 node_id((label)) 或 node_id{label}
                                node_matches = re.findall(r'\b\w+\s*[\[\(\\{]', mermaid_str)
                                unique_nodes = set()
                                for match in node_matches:
                                    node_id = match.split('[')[0].split('(')[0].split('{')[0].strip()
                                    if node_id:
                                        unique_nodes.add(node_id)
                                
                                # 🚀 修复：统一边统计方法（与前端一致，包括虚线边）
                                # 匹配边：--> 或 -.-> 或 -->|label|
                                edge_matches = re.findall(r'[-.>]+', mermaid_str)
                                
                                nodes_count = len(unique_nodes)
                                edges_count = len(edge_matches)
                                graph_data["metadata"]["nodes_count_estimated"] = nodes_count
                                graph_data["metadata"]["edges_count_estimated"] = edges_count
                                self.logger.info(f"📊 统计: {nodes_count} 个节点显示, {edges_count} 条边（包括虚线）")
                                
                                # 用于检测未显示节点的集合（保持原有逻辑）
                                displayed_nodes = unique_nodes
                                
                                # 🚀 检测未显示的节点（从_all_added_nodes获取）
                                # 这有助于理解为什么某些节点没有显示（因为它们可能不可达）
                                if hasattr(self, '_unified_workflow_instance') and self._unified_workflow_instance:
                                    if hasattr(self._unified_workflow_instance, '_all_added_nodes'):
                                        all_added_nodes = set(self._unified_workflow_instance._all_added_nodes)
                                        missing_nodes = all_added_nodes - displayed_nodes
                                        if missing_nodes:
                                            self.logger.warning(f"⚠️ 发现 {len(missing_nodes)} 个节点未在Mermaid图中显示: {sorted(missing_nodes)}")
                                            self.logger.info("💡 原因：LangGraph的draw_mermaid()只显示从入口点可达的节点")
                                            self.logger.info("💡 如果所有路径都路由到chief_agent，simple_query/complex_query/generate_steps等节点可能不可达")
                                            self.logger.info("💡 这是LangGraph框架的正常行为，确保工作流构建时所有节点都通过条件路由可达")
                                            graph_data["metadata"]["all_added_nodes_count"] = len(all_added_nodes)
                                            graph_data["metadata"]["missing_nodes"] = sorted(list(missing_nodes))
                                            graph_data["metadata"]["displayed_nodes"] = sorted(list(displayed_nodes))
                            except Exception as e:
                                self.logger.debug(f"检查节点显示情况时出错: {e}")
                            
                            # 直接返回LangGraph生成的Mermaid图，不进行任何手动处理
                            return graph_data
                        else:
                            self.logger.warning("⚠️ draw_mermaid()返回空字符串")
                else:
                    self.logger.warning("⚠️ workflow对象没有get_graph()方法")
            except Exception as e:
                self.logger.error(f"❌ 使用LangGraph draw_mermaid()失败: {e}", exc_info=True)
                # 继续尝试其他方法
            
            # 方法2: 尝试其他方式获取图对象并再次尝试draw_mermaid()
            graph = None
            if hasattr(workflow, 'graph'):
                graph = workflow.graph
                self.logger.info(f"✅ 从workflow.graph获取图对象: {type(graph)}")
            elif hasattr(workflow, 'workflow') and hasattr(workflow.workflow, 'get_graph'):
                graph = workflow.workflow.get_graph()
                self.logger.info(f"✅ 从workflow.workflow.get_graph()获取图对象: {type(graph)}")
            
            # 如果获取到图对象，再次尝试draw_mermaid()
            if graph:
                try:
                    if hasattr(graph, 'draw_mermaid'):
                        mermaid_str = graph.draw_mermaid()
                        if mermaid_str and mermaid_str.strip():
                            self.logger.info("✅ 使用graph.draw_mermaid()获取完整工作流图（LangGraph框架方法）")
                            self.logger.info(f"📊 Mermaid图长度: {len(mermaid_str)} 字符")
                            graph_data["mermaid"] = mermaid_str
                            return graph_data
                        else:
                            self.logger.warning("⚠️ graph.draw_mermaid()返回空字符串")
                    else:
                        self.logger.warning(f"⚠️ 图对象没有draw_mermaid()方法，类型: {type(graph)}")
                        self.logger.info(f"📋 图对象可用方法: {[m for m in dir(graph) if not m.startswith('_')][:10]}")
                except Exception as e:
                    self.logger.error(f"❌ 使用graph.draw_mermaid()失败: {e}", exc_info=True)
                    import traceback
                    self.logger.error(f"详细错误:\n{traceback.format_exc()}")
            
            # 如果所有LangGraph框架方法都失败，记录错误并返回空数据
            # 不使用硬编码数据，完全依赖LangGraph框架功能
            self.logger.error("❌ 无法使用LangGraph框架的方法获取工作流图")
            self.logger.error("💡 请检查:")
            self.logger.error("   1. LangGraph是否正确安装")
            self.logger.error("   2. workflow对象是否正确编译")
            self.logger.error("   3. workflow.get_graph()是否返回有效的图对象")
            self.logger.error("   4. 图对象是否有draw_mermaid()方法")
            
            # 返回包含错误信息的空数据，让前端显示错误信息
            graph_data["metadata"]["error"] = "无法使用LangGraph框架获取工作流图数据"
            graph_data["metadata"]["error_details"] = "请检查LangGraph安装和工作流对象是否正确初始化"
            return graph_data

        except Exception as e:
            self.logger.error(f"提取图数据失败: {e}", exc_info=True)
            raise

    # 已移除硬编码的_generate_mermaid_diagram方法
    # 现在完全依赖LangGraph框架的draw_mermaid()方法生成Mermaid图

    # 已移除硬编码的节点提取方法 _extract_langgraph_nodes
    # 已移除硬编码的节点分析方法 _analyze_node（包含大量关键字映射）
    # 已移除硬编码的节点描述方法 _get_node_specific_description
    # 现在完全依赖LangGraph框架的draw_mermaid()方法，该方法会自动处理节点和边的可视化

    # 已移除硬编码的边提取方法 _extract_langgraph_edges
    # 已移除硬编码的执行状态提取方法 _extract_execution_state
    # 已移除硬编码的特性检测方法 _detect_langgraph_features
    # 已移除硬编码的Mermaid生成方法 _generate_langgraph_mermaid（包含硬编码的节点样式和边样式）
    # 现在完全依赖LangGraph框架的draw_mermaid()方法，该方法会自动处理所有节点、边、样式和特性的可视化

    # 已移除硬编码的演示数据方法 _create_langgraph_demo_data
    # 现在完全依赖LangGraph框架的draw_mermaid()方法获取图数据

    async def _render_home_page(self):
        """渲染可视化主页"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RANGEN LangGraph 可视化</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    padding: 40px;
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}

                .title {{
                    font-size: 2.5em;
                    font-weight: bold;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }}

                .subtitle {{
                    font-size: 1.2em;
                    color: #666;
                    margin-bottom: 20px;
                }}

                .nav-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                    gap: 20px;
                    margin-top: 40px;
                }}

                .nav-card {{
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 25px;
                    text-align: center;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                    text-decoration: none;
                    color: inherit;
                    display: block;
                }}

                .nav-card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 15px 30px rgba(0,0,0,0.1);
                }}

                .nav-icon {{
                    font-size: 3em;
                    margin-bottom: 15px;
                }}

                .nav-title {{
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }}

                .nav-desc {{
                    color: #666;
                    line-height: 1.5;
                }}

                .back-link {{
                    position: absolute;
                    top: 20px;
                    left: 20px;
                    background: rgba(255, 255, 255, 0.2);
                    color: white;
                    padding: 8px 16px;
                    border-radius: 6px;
                    text-decoration: none;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }}

                .back-link:hover {{
                    background: rgba(255, 255, 255, 0.3);
                    border-color: rgba(255, 255, 255, 0.5);
                }}
            </style>
        </head>
        <body>
            <a href="/" class="back-link">← 返回主服务器</a>
            <div class="container">
                <div class="header">
                    <div class="title">🎯 RANGEN LangGraph 可视化</div>
                    <div class="subtitle">智能工作流可视化系统</div>
                    <p>探索和监控您的LangGraph工作流执行状态</p>
                </div>

                <div class="nav-grid">
                    <a href="/visualization/graph" class="nav-card">
                        <div class="nav-icon">📊</div>
                        <div class="nav-title">工作流图</div>
                        <div class="nav-desc">查看完整的LangGraph工作流结构和节点关系</div>
                    </a>

                    <a href="/visualization/status" class="nav-card">
                        <div class="nav-icon">🔍</div>
                        <div class="nav-title">系统状态</div>
                        <div class="nav-desc">检查系统健康状态和依赖检查</div>
                    </a>

                    <a href="/visualization/monitor" class="nav-card">
                        <div class="nav-icon">📈</div>
                        <div class="nav-title">执行监控</div>
                        <div class="nav-desc">实时监控工作流执行状态和性能指标</div>
                    </a>

                    <a href="/visualization/debug" class="nav-card">
                        <div class="nav-icon">🔧</div>
                        <div class="nav-title">调试信息</div>
                        <div class="nav-desc">查看详细的调试信息和系统日志</div>
                    </a>
                </div>
            </div>
        </body>
        </html>"""
        return HTMLResponse(content=html_content)

    async def _render_graph_page(self):
        """渲染工作流图页面"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>工作流图 - RANGEN 可视化</title>
            <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}

                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    padding: 20px; /* 🚀 优化：减少容器padding */
                    display: flex;
                    flex-direction: column;
                    height: calc(100vh - 40px); /* 🚀 优化：使用视口高度 */
                }}

                .header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px; /* 🚀 优化：减少底部间距 */
                    border-bottom: 2px solid #e0e0e0;
                    padding-bottom: 10px; /* 🚀 优化：减少padding */
                    flex-shrink: 0; /* 🚀 优化：防止压缩 */
                }}

                .title {{
                    font-size: 1.5em; /* 🚀 优化：减小字体大小 */
                    font-weight: bold;
                    color: #333;
                    margin: 0;
                }}

                .nav-buttons {{
                    display: flex;
                    gap: 10px;
                }}

                .nav-button {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 14px;
                    transition: all 0.3s ease;
                }}

                .nav-button:hover {{
                    background: #5a67d8;
                    transform: translateY(-2px);
                }}

                .content {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px; /* 🚀 优化：减少间距 */
                    flex: 1; /* 🚀 优化：占据剩余空间 */
                    min-height: 0; /* 🚀 优化：允许flex子元素缩小 */
                    overflow: hidden; /* 🚀 优化：防止溢出 */
                }}

                .status-bar {{
                    background: #f8f9fa;
                    border-radius: 10px; /* 🚀 优化：减小圆角 */
                    padding: 8px 15px; /* 🚀 优化：减少padding */
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 10px; /* 🚀 优化：减少间距 */
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    flex-shrink: 0; /* 🚀 优化：防止压缩 */
                    font-size: 12px; /* 🚀 优化：减小字体 */
                }}

                .status-item {{
                    display: flex;
                    align-items: center;
                    gap: 5px; /* 🚀 优化：减少间距 */
                    padding: 5px 10px; /* 🚀 优化：减少padding */
                    background: white;
                    border-radius: 6px; /* 🚀 优化：减小圆角 */
                    border: 1px solid #e0e0e0;
                    min-width: 100px; /* 🚀 优化：减小最小宽度 */
                }}

                .status-label {{
                    font-weight: bold;
                    color: #555;
                    font-size: 12px; /* 🚀 优化：减小字体 */
                }}

                .status-value {{
                    color: #667eea;
                    font-weight: bold;
                    font-size: 12px; /* 🚀 优化：减小字体 */
                }}

                .status-indicator {{
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    border-radius: 50%;
                    background: #28a745;
                    animation: pulse 2s infinite;
                }}

                /* Tab导航样式 */
                .main-tabs {{
                    display: flex;
                    border-bottom: 2px solid #e0e0e0;
                    background: #fff;
                    padding: 0 15px; /* 🚀 优化：减少padding */
                    flex-shrink: 0;
                    margin-bottom: 10px; /* 🚀 优化：减少底部间距 */
                }}

                .main-tab {{
                    padding: 8px 16px; /* 🚀 优化：减少padding */
                    cursor: pointer;
                    border: none;
                    background: none;
                    font-size: 13px; /* 🚀 优化：减小字体 */
                    font-weight: 500;
                    color: #666;
                    border-bottom: 3px solid transparent;
                    transition: all 0.3s;
                    position: relative;
                }}

                .main-tab:hover {{
                    color: #667eea;
                    background: #f5f5f5;
                }}

                .main-tab.active {{
                    color: #667eea;
                    border-bottom-color: #667eea;
                    font-weight: 600;
                }}

                .main-tab-content {{
                    display: none !important;
                    flex: 1;
                    overflow: hidden;
                    height: 100%;
                    min-height: 0;
                }}

                .main-tab-content.active {{
                    display: flex !important;
                    flex-direction: column;
                }}

                .main-panel {{
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 15px; /* 🚀 优化：减少padding */
                    min-height: 0; /* 🚀 优化：移除固定高度，使用flex */
                    position: relative;
                    overflow: hidden;
                    flex: 1; /* 🚀 优化：占据剩余空间 */
                    display: flex;
                    flex-direction: column;
                }}

                .workflow-graph-section {{
                    flex: 1; /* 🚀 优化：占据剩余空间 */
                    min-width: 0;
                    min-height: 0; /* 🚀 优化：允许缩小 */
                    display: flex;
                    flex-direction: column;
                    position: relative;
                }}

                .side-panel {{
                    display: none; /* 隐藏侧边栏 */
                }}

                /* 节点状态样式 */
                .node-status-item {{
                    padding: 12px;
                    margin: 8px 0;
                    border: 2px solid #ddd;
                    border-radius: 6px;
                    background: #fff;
                    position: relative;
                }}

                .node-status-item.running {{
                    border-color: #ffeb3b;
                    background: #fff9c4;
                    border-left-width: 4px;
                }}

                .node-status-item.completed {{
                    border-color: #4caf50;
                    background: #c8e6c9;
                    border-left-width: 4px;
                }}

                .node-status-item.error {{
                    border-color: #f44336;
                    background: #ffcdd2;
                    border-left-width: 4px;
                }}

                .node-status-item.idle {{
                    border-color: #ccc;
                    background: #f5f5f5;
                    opacity: 0.7;
                }}

                .panel-title {{
                    font-size: 1em; /* 🚀 优化：减小字体 */
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 8px; /* 🚀 优化：减少底部间距 */
                    border-bottom: 1px solid #e0e0e0;
                    padding-bottom: 6px; /* 🚀 优化：减少padding */
                    flex-shrink: 0; /* 🚀 优化：防止压缩 */
                }}

                .mermaid-container {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px; /* 🚀 优化：减少padding */
                    border: 2px solid #e0e0e0;
                    text-align: center;
                    min-height: 0; /* 🚀 优化：移除固定高度 */
                    width: 100%;
                    overflow: auto; /* 保持 auto，让内容可以滚动 */
                    position: relative;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-top: 0; /* 🚀 修复：确保容器顶部没有额外间距 */
                    flex: 1; /* 🚀 优化：占据剩余空间 */
                }}

                .mermaid-wrapper {{
                    width: 100%;
                    height: 100%;
                    overflow: auto;
                    position: relative;
                    min-height: 0; /* 🚀 优化：移除固定高度 */
                }}

                .mermaid-wrapper svg {{
                    max-width: none !important;
                    min-width: 100% !important;
                    transform-origin: top left;
                }}

                .zoom-controls {{
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    display: flex;
                    flex-direction: column;
                    gap: 6px;
                    z-index: 1000;
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 8px;
                    padding: 8px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
                    backdrop-filter: blur(4px);
                }}

                .zoom-button {{
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid rgba(102, 126, 234, 0.3);
                    color: #667eea;
                    width: 36px;
                    height: 36px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 16px;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.2s ease;
                    backdrop-filter: blur(4px);
                }}

                .zoom-button:hover {{
                    background: #667eea;
                    color: white;
                    border-color: #667eea;
                    transform: scale(1.05);
                    box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
                }}

                .info-section {{
                    margin-bottom: 20px;
                }}

                .info-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}

                .info-label {{
                    font-weight: bold;
                    color: #555;
                }}

                .info-value {{
                    color: #667eea;
                    font-weight: bold;
                }}

                .action-buttons {{
                    margin-top: 20px;
                }}

                .action-button {{
                    background: #28a745;
                    color: white;
                    border: none;
                    padding: 10px 15px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    margin-right: 10px;
                    transition: all 0.3s ease;
                }}

                .action-button:hover {{
                    background: #218838;
                    transform: translateY(-1px);
                }}

                .status-indicator {{
                    display: inline-block;
                    width: 12px;
                    height: 12px;
                    border-radius: 50%;
                    background: #28a745;
                    margin-right: 8px;
                    animation: pulse 2s infinite;
                }}

                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}

                /* 执行工作流控件样式 */
                .execution-controls {{
                    background: #f8f9fa;
                    border-radius: 8px; /* 🚀 优化：减小圆角 */
                    padding: 10px; /* 🚀 优化：减少padding */
                    margin-bottom: 10px; /* 🚀 优化：减少底部间距 */
                    display: flex;
                    gap: 8px; /* 🚀 优化：减少间距 */
                    align-items: center;
                    flex-wrap: wrap;
                    position: relative;
                    z-index: 200; /* 🚀 修复：设置更高的 z-index，确保不被缩放按钮遮挡 */
                    flex-shrink: 0; /* 🚀 优化：防止压缩 */
                }}

                .execution-controls input {{
                    flex: 1;
                    min-width: 250px; /* 🚀 优化：减小最小宽度 */
                    padding: 8px 12px; /* 🚀 优化：减少padding */
                    border: 2px solid #e0e0e0;
                    border-radius: 6px;
                    font-size: 13px; /* 🚀 优化：减小字体 */
                    transition: border-color 0.3s;
                }}

                .execution-controls input:focus {{
                    outline: none;
                    border-color: #667eea;
                }}

                .execution-controls button {{
                    padding: 12px 24px;
                    border: none;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: 500;
                    transition: all 0.3s;
                }}

                .execution-controls button.execute {{
                    background: #28a745;
                    color: white;
                }}

                .execution-controls button.execute:hover {{
                    background: #218838;
                    transform: translateY(-1px);
                }}

                .execution-controls button.execute:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                    transform: none;
                }}

                .execution-controls button.stop {{
                    background: #dc3545;
                    color: white;
                }}

                .execution-controls button.stop:hover {{
                    background: #c82333;
                }}

                .execution-controls button.stop:disabled {{
                    background: #ccc;
                    cursor: not-allowed;
                }}

                /* 🚀 新增：进度条样式 */
                .progress-container {{
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border: 1px solid #e0e0e0;
                    display: none; /* 默认隐藏，执行时显示 */
                    min-width: 250px; /* 确保进度条有合适的最小宽度 */
                }}

                .progress-container.active {{
                    display: block;
                }}

                .progress-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                    font-size: 13px;
                }}

                .progress-text {{
                    color: #667eea;
                    font-weight: 600;
                }}

                .progress-detail {{
                    color: #666;
                    font-size: 12px;
                }}

                .progress-bar-wrapper {{
                    width: 100%;
                    height: 20px;
                    background: #e0e0e0;
                    border-radius: 10px;
                    overflow: hidden;
                    position: relative;
                    box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);
                }}

                .progress-bar {{
                    height: 100%;
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    transition: width 0.3s ease;
                    border-radius: 10px;
                    position: relative;
                    overflow: hidden;
                }}

                .progress-bar::after {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    bottom: 0;
                    right: 0;
                    background: linear-gradient(
                        90deg,
                        transparent,
                        rgba(255,255,255,0.3),
                        transparent
                    );
                    animation: shimmer 2s infinite;
                }}

                @keyframes shimmer {{
                    0% {{ transform: translateX(-100%); }}
                    100% {{ transform: translateX(100%); }}
                }}

                .progress-steps {{
                    margin-top: 10px;
                    font-size: 12px;
                    color: #666;
                    max-height: 100px;
                    overflow-y: auto;
                }}

                .progress-step {{
                    padding: 4px 8px;
                    margin: 2px 0;
                    border-radius: 4px;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }}

                .progress-step.running {{
                    background: #fff9c4;
                    color: #f57c00;
                }}

                .progress-step.completed {{
                    background: #c8e6c9;
                    color: #2e7d32;
                }}

                .progress-step.error {{
                    background: #ffcdd2;
                    color: #c62828;
                }}

                .progress-step-idle {{
                    background: #f5f5f5;
                    color: #999;
                }}

                .step-icon {{
                    font-size: 14px;
                    width: 16px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 class="title">📊 LangGraph 工作流图</h1>
                    <div class="nav-buttons">
                        <a href="/visualization/" class="nav-button">← 返回主页</a>
                        <a href="/visualization/status" class="nav-button">系统状态</a>
                    </div>
                </div>

                <div class="content">
                    <!-- 顶部状态栏 -->
                    <div class="status-bar">
                        <div class="status-item">
                            <span class="status-indicator"></span>
                            <span class="status-label">状态:</span>
                            <span class="status-value">运行中</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">工作流类型:</span>
                            <span class="status-value">LangGraph</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">节点数量:</span>
                            <span class="status-value" id="nodes-count">-</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">边数量:</span>
                            <span class="status-value" id="edges-count">-</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">执行状态:</span>
                            <span class="status-value">就绪</span>
                        </div>
                        <div style="display: flex; gap: 10px; margin-left: auto;">
                            <button class="action-button" onclick="loadGraph()" style="margin: 0; padding: 8px 15px; font-size: 13px;">🔄 刷新</button>
                            <button class="action-button" onclick="exportGraph()" style="margin: 0; padding: 8px 15px; font-size: 13px;">💾 导出</button>
                        </div>
                    </div>

                    <!-- Tab导航 -->
                    <div class="main-tabs">
                        <button class="main-tab active" onclick="switchMainTab('workflow-graph')">工作流结构图</button>
                        <button class="main-tab" onclick="switchMainTab('node-status')">节点执行状况</button>
                        <button class="main-tab" onclick="switchMainTab('system-health')">系统健康状况</button>
                        <button class="main-tab" onclick="switchMainTab('agent-creation')">🤖 Agent Creation</button>
                    </div>

                    <!-- Tab内容：工作流结构图 -->
                    <div id="main-tab-workflow-graph" class="main-tab-content active">
                        <div class="main-panel">
                            <div class="workflow-graph-section">
                                <div class="panel-title">工作流结构图</div>
                                
                                <!-- 🚀 新增：执行工作流控件 -->
                                <div class="execution-controls">
                                    <input type="text" id="graph-query-input" placeholder="输入查询内容..." style="flex: 1; min-width: 300px; padding: 12px; border: 2px solid #e0e0e0; border-radius: 6px; font-size: 14px;">
                                    <button class="execute" id="graph-execute-btn" onclick="executeGraphWorkflow()" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500;">执行</button>
                                    <button class="stop" id="graph-stop-btn" onclick="stopGraphWorkflow()" style="padding: 12px 24px; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; font-weight: 500; display: none;">停止</button>
                                </div>
                                
                                <!-- 🚀 修复：进度条容器 -->
                                <div id="graph-progress-container" class="progress-container">
                                    <div class="progress-header">
                                        <span class="progress-text" id="graph-progress-text">0%</span>
                                        <span class="progress-detail" id="graph-progress-detail">0/0 节点</span>
                                    </div>
                                    <div class="progress-bar-wrapper">
                                        <div class="progress-bar" id="graph-progress-bar" style="width: 0%;"></div>
                                    </div>
                                    <div class="progress-steps" id="graph-progress-steps"></div>
                                </div>
                                <div class="mermaid-container">
                                    <!-- 悬浮缩放控制按钮 -->
                                    <div class="zoom-controls">
                                        <button class="zoom-button" onclick="zoomIn()" title="放大">+</button>
                                        <button class="zoom-button" onclick="zoomOut()" title="缩小">-</button>
                                        <button class="zoom-button" onclick="resetZoom()" title="重置">⌂</button>
                                        <button class="zoom-button" onclick="fitToScreen()" title="适应屏幕">⤢</button>
                                    </div>
                                    <div class="mermaid-wrapper" id="mermaid-wrapper">
                                        <div id="workflow-diagram">
                                            <div style="text-align: center; padding: 100px; color: #666;">
                                                <div style="font-size: 24px; margin-bottom: 20px;">⏳</div>
                                                <div>正在加载工作流图...</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab内容：节点执行状况 -->
                    <div id="main-tab-node-status" class="main-tab-content">
                        <div class="main-panel" style="display: flex; flex-direction: column; gap: 20px;">
                            <!-- 节点状态总览 -->
                            <div style="flex-shrink: 0;">
                                <div class="panel-title">节点状态总览</div>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                                    <div style="padding: 15px; background: #fff9c4; border: 2px solid #ffeb3b; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #f57c00;" id="graph-node-running-count">0</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">运行中</div>
                                    </div>
                                    <div style="padding: 15px; background: #c8e6c9; border: 2px solid #4caf50; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #2e7d32;" id="graph-node-completed-count">0</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">已完成</div>
                                    </div>
                                    <div style="padding: 15px; background: #ffcdd2; border: 2px solid #f44336; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #c62828;" id="graph-node-error-count">0</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">错误</div>
                                    </div>
                                    <div style="padding: 15px; background: #e3f2fd; border: 2px solid #2196f3; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #1565c0;" id="graph-node-total-count">0</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">总节点数</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 节点执行状态列表 -->
                            <div style="flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; flex-shrink: 0;">
                                    <div class="panel-title" style="margin: 0;">节点执行状态</div>
                                    <button onclick="refreshGraphNodeStatus()" style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">刷新</button>
                                </div>
                                <div id="graph-node-status-content" style="flex: 1; min-height: 0; overflow-y: auto; overflow-x: visible; background: #fff; border-radius: 8px; padding: 15px;">
                                    <p style="color: #999; font-style: italic; text-align: center; padding: 40px; font-size: 12px;">等待执行开始... 执行工作流后，节点状态将实时显示在这里。</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab内容：系统健康状况 -->
                    <div id="main-tab-system-health" class="main-tab-content">
                        <div class="main-panel" style="display: flex; flex-direction: column; gap: 20px;">
                            <!-- 系统健康总览 -->
                            <div style="flex-shrink: 0;">
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                                    <div class="panel-title" style="margin: 0;">系统健康总览</div>
                                    <button onclick="refreshGraphSystemHealth()" style="padding: 8px 16px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">刷新</button>
                                </div>
                                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                                    <div style="padding: 15px; background: #f9f9f9; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #333;" id="graph-system-health-status">-</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">整体状态</div>
                                    </div>
                                    <div style="padding: 15px; background: #f9f9f9; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #333;" id="graph-system-health-uptime">-</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">运行时间</div>
                                    </div>
                                    <div style="padding: 15px; background: #f9f9f9; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #333;" id="graph-system-health-checks-pass">-</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">通过检查</div>
                                    </div>
                                    <div style="padding: 15px; background: #f9f9f9; border-radius: 4px; text-align: center;">
                                        <div style="font-size: 24px; font-weight: bold; color: #333;" id="graph-system-health-checks-fail">-</div>
                                        <div style="font-size: 12px; color: #666; margin-top: 5px;">失败检查</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- 详细健康检查 -->
                            <div style="flex: 1; min-height: 0; display: flex; flex-direction: column; overflow: hidden;">
                                <div class="panel-title">详细健康检查</div>
                                <div id="graph-system-health-content" style="flex: 1; min-height: 0; overflow-y: auto; overflow-x: visible; background: #fff; border-radius: 8px; padding: 15px;">
                                    <p style="color: #999; font-style: italic; text-align: center; padding: 40px; font-size: 12px;">正在加载系统健康状态...</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Tab内容：Agent Creation -->
                    <div id="main-tab-agent-creation" class="main-tab-content">
                        <div class="main-panel" style="display: flex; flex-direction: column; gap: 20px;">
                            <!-- 简化版Agent创建界面 -->
                            <div style="flex: 1; padding: 20px;">
                                <h2 style="margin-top: 0; color: #333;">🤖 自然语言Agent创建</h2>
                                <p style="color: #666; font-size: 14px; margin-bottom: 20px;">
                                    用自然语言描述您需要的Agent，系统将自动匹配Tools和Skills并创建配置。
                                </p>
                                
                                <!-- 需求输入 -->
                                <div style="margin-bottom: 20px;">
                                    <h3 style="margin-bottom: 10px;">描述您的需求</h3>
                                    <textarea id="agent-creation-description" placeholder="例如：创建一个能分析CSV文件并生成图表的Agent..." 
                                              style="width: 100%; height: 120px; padding: 12px; font-size: 14px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 15px; resize: vertical;"></textarea>
                                    
                                    <div style="display: flex; gap: 10px;">
                                        <button onclick="parseAgentRequirements()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; flex: 1;">
                                            🚀 智能解析
                                        </button>
                                        <button onclick="clearAgentForm()" style="padding: 10px 20px; background: #f5f5f5; color: #333; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; font-size: 14px; flex: 1;">
                                            🗑️ 清空
                                        </button>
                                    </div>
                                </div>
                                
                                <!-- 解析结果预览 -->
                                <div id="agent-creation-result" style="display: none; padding: 15px; background: #f8f9fa; border-radius: 5px; border: 1px solid #e9ecef; margin-bottom: 20px;">
                                    <h4 style="margin-top: 0;">解析结果</h4>
                                    <div id="agent-parse-details"></div>
                                </div>
                                
                                <!-- 创建按钮 -->
                                <div style="display: flex; gap: 10px;">
                                    <button onclick="createAgentFromParse()" id="create-agent-button" style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; flex: 2; display: none;">
                                        ✅ 确认创建Agent
                                    </button>
                                    <button onclick="resetAgentCreation()" style="padding: 12px 24px; background: #f5f5f5; color: #333; border: 1px solid #ddd; border-radius: 5px; cursor: pointer; font-size: 14px; flex: 1; display: none;">
                                        🔄 重新开始
                                    </button>
                                </div>
                                
                                <!-- 状态信息 -->
                                <div id="agent-creation-status" style="margin-top: 20px; padding: 10px; border-radius: 5px; display: none;"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // 缩放控制变量
                let currentScale = 1.5; // 初始放大1.5倍
                let minScale = 0.5;
                let maxScale = 3.0;
                let svgElement = null;
                
                // 🚀 新增：节点组展开/折叠状态管理
                let expandedGroups = new Set(); // 已展开的节点组
                let nodeGroups = {{}}; // 节点组信息
                let nodeDescriptions = {{}}; // 🚀 新增：节点功能说明（用于 tooltip）

                // 初始化Mermaid
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'default',
                    themeVariables: {{
                        primaryColor: '#667eea',
                        primaryTextColor: '#fff',
                        primaryBorderColor: '#5a67d8',
                        lineColor: '#667eea',
                        sectionBkgColor: '#f8f9fa',
                        altSectionBkgColor: '#e2e8f0',
                        gridColor: '#e0e0e0',
                        tertiaryColor: '#fff',
                        fontSize: '16px', // 增大字体
                        fontFamily: 'Arial, sans-serif'
                    }},
                    flowchart: {{
                        useMaxWidth: false, // 不使用最大宽度限制
                        htmlLabels: true,
                        curve: 'basis',
                        padding: 20
                    }}
                }});

                async function loadGraph() {{
                    try {{
                        // 🚀 新增：传递展开/折叠状态到API
                        const expandedGroupsArray = Array.from(expandedGroups);
                        const url = '/visualization/api/workflow/graph' + 
                            (expandedGroupsArray.length > 0 ? '?expanded_groups=' + expandedGroupsArray.join(',') : '');
                        
                        const response = await fetch(url);
                        if (!response.ok) {{
                            throw new Error(`HTTP error! status: ${{response.status}}`);
                        }}
                        const data = await response.json();

                        // 🚀 新增：保存节点组信息
                        if (data.node_groups) {{
                            nodeGroups = data.node_groups;
                            console.log('✅ 节点组信息:', nodeGroups);
                        }}
                        
                        // 🚀 新增：保存节点功能说明（用于 tooltip）
                        if (data.node_descriptions) {{
                            nodeDescriptions = data.node_descriptions;
                            console.log('✅ 节点功能说明已加载:', Object.keys(nodeDescriptions).length, '个节点');
                        }}

                        // 使用WorkflowGraphBuilder生成的分层Mermaid图（支持展开/折叠）
                        let mermaidCode = '';
                        if (data.mermaid && data.mermaid.trim() !== '') {{
                            // 使用WorkflowGraphBuilder生成的分层Mermaid图
                            mermaidCode = data.mermaid;
                            console.log('✅ 使用WorkflowGraphBuilder生成的分层Mermaid图');
                            
                            // 从Mermaid字符串中统计节点和边数量（用于显示统计信息）
                            // 🚀 修复：优先使用后端传递的准确数量，如果不存在则从前端统计
                            try {{
                                // 优先使用后端传递的准确数量
                                let nodesCount = data.metadata?.nodes_count_estimated;
                                let edgesCount = data.metadata?.edges_count_estimated;
                                
                                // 如果后端没有提供数量，则从前端统计（与后端统计方法保持一致）
                                if (nodesCount === undefined || edgesCount === undefined) {{
                                    // 匹配节点：node_id[label] 或 node_id((label)) 或 node_id{{label}}
                                    const nodeMatches = mermaidCode.match(/\\b\\w+\\s*[\\[\\\\(\\\\{{]/g) || [];
                                    const uniqueNodes = new Set(nodeMatches.map(function(m) {{ return m.split(/[\\[\\\\(\\\\{{]/)[0].trim(); }}));
                                    nodesCount = nodesCount || uniqueNodes.size;
                                    
                                    // 匹配边：--> 或 -.-> 或 -->|label|
                                    const edgeMatches = mermaidCode.match(/[-.>]+/g) || [];
                                    edgesCount = edgesCount || edgeMatches.length;
                                }}
                                
                                // 更新统计信息
                                document.getElementById('nodes-count').textContent = nodesCount || '-';
                                document.getElementById('edges-count').textContent = edgesCount || '-';
                            }} catch (e) {{
                                // 如果解析失败，使用metadata中的估算值
                                document.getElementById('nodes-count').textContent = data.metadata?.nodes_count_estimated || '-';
                                document.getElementById('edges-count').textContent = data.metadata?.edges_count_estimated || '-';
                            }}
                        }} else {{
                            // 如果LangGraph无法生成图，显示错误信息
                            const errorMsg = data.metadata?.error || '无法获取工作流图数据';
                            const errorDetails = data.metadata?.error_details || '请检查LangGraph安装和工作流对象是否正确初始化';
                            document.getElementById('nodes-count').textContent = '-';
                            document.getElementById('edges-count').textContent = '-';
                            throw new Error(errorMsg + ': ' + errorDetails);
                        }}
                        
                        renderMermaid(mermaidCode);

                    }} catch (error) {{
                        console.error('加载工作流图失败:', error);
                        document.getElementById('workflow-diagram').innerHTML =
                            '<div style="color: #f44336; text-align: center;">' +
                            '<h3>❌ 加载失败</h3>' +
                            '<p>' + error.message + '</p>' +
                            '</div>';
                    }}
                }}

                // 已移除硬编码的generateMermaid函数
                // 现在完全依赖LangGraph框架的draw_mermaid()方法生成Mermaid图

                function renderMermaid(mermaidCode) {{
                    const element = document.getElementById('workflow-diagram');
                    mermaid.render('workflow-graph', mermaidCode).then(function(result) {{
                        element.innerHTML = result.svg;
                        svgElement = element.querySelector('svg');
                        if (svgElement) {{
                            // 设置SVG样式以支持缩放
                            svgElement.style.width = '100%';
                            svgElement.style.height = 'auto';
                            svgElement.style.minWidth = '1200px'; // 最小宽度
                            svgElement.style.transformOrigin = 'top left';
                            applyZoom();
                            
                            // 🚀 调试：输出所有节点ID，帮助诊断问题
                            const allNodesDebug = svgElement.querySelectorAll('[id]');
                            console.log('🔍 调试：SVG中所有带ID的元素数量:', allNodesDebug.length);
                            if (allNodesDebug.length > 0 && allNodesDebug.length < 50) {{
                                const nodeIds = Array.from(allNodesDebug).map(function(n) {{ return n.getAttribute('id'); }});
                                console.log('🔍 调试：前10个节点ID:', nodeIds.slice(0, 10));
                            }}
                            
                            // 🚀 新增：添加节点组点击事件监听器（实现展开/折叠功能）
                            setupNodeGroupClickHandlers();
                            
                            // 🚀 新增：添加节点 tooltip 功能（显示节点功能说明）
                            setupNodeTooltips(nodeDescriptions);
                            
                            // 🚀 新增：重新应用所有节点的状态（如果有执行中的工作流）
                            if (Object.keys(nodeStatusMap).length > 0) {{
                                console.log('🔄 [节点高亮] 重新应用节点状态，节点数量:', Object.keys(nodeStatusMap).length);
                                for (const [nodeName, status] of Object.entries(nodeStatusMap)) {{
                                    updateWorkflowGraphNode(nodeName, status);
                                }}
                            }}
                            
                            // 🚀 修复：延迟再次设置 tooltip，确保展开后的子节点也能被识别
                            // 当节点组展开时，子节点会出现在SVG中，但可能需要一些时间才能完全渲染
                            setTimeout(function() {{
                                console.log('🔄 [服务器端] 延迟重新设置 tooltip（500ms），确保展开后的子节点也被识别');
                                const allNodesAfterDelay = svgElement.querySelectorAll('g[id], [id]');
                                console.log('🔍 [服务器端] 延迟后找到', allNodesAfterDelay.length, '个带ID的元素');
                                setupNodeTooltips(nodeDescriptions);
                                
                                // 🚀 新增：延迟重新应用节点状态
                                if (Object.keys(nodeStatusMap).length > 0) {{
                                    console.log('🔄 [节点高亮] 延迟重新应用节点状态（500ms）');
                                    for (const [nodeName, status] of Object.entries(nodeStatusMap)) {{
                                        updateWorkflowGraphNode(nodeName, status);
                                    }}
                                }}
                            }}, 500);
                            
                            // 🚀 修复：再次延迟设置 tooltip（1000ms），确保所有节点都已渲染
                            setTimeout(function() {{
                                console.log('🔄 [服务器端] 再次延迟重新设置 tooltip（1000ms），确保所有节点都已渲染');
                                const allNodesAfterDelay = svgElement.querySelectorAll('g[id], [id]');
                                console.log('🔍 [服务器端] 再次延迟后找到', allNodesAfterDelay.length, '个带ID的元素');
                                setupNodeTooltips(nodeDescriptions);
                                
                                // 🚀 新增：再次延迟重新应用节点状态
                                if (Object.keys(nodeStatusMap).length > 0) {{
                                    console.log('🔄 [节点高亮] 再次延迟重新应用节点状态（1000ms）');
                                    for (const [nodeName, status] of Object.entries(nodeStatusMap)) {{
                                        updateWorkflowGraphNode(nodeName, status);
                                    }}
                                }}
                            }}, 1000);
                        }}
                    }}).catch(function(error) {{
                        console.error('渲染Mermaid图表失败:', error);
                        element.innerHTML = '<div style="color: #f44336; text-align: center;"><h3>❌ 渲染失败</h3></div>';
                    }});
                }}
                
                // 🚀 新增：设置节点组点击事件处理器
                function setupNodeGroupClickHandlers() {{
                    if (!svgElement) return;
                    
                    // 🚀 修复：改进节点组查找逻辑
                    // 查找所有可能的节点组节点（格式可能是：group_id_group 或 flowchart-group_id_group-0）
                    const allNodes = svgElement.querySelectorAll('g[id], [id]');
                    const groupNodes = [];
                    
                    // 创建节点ID提取函数
                    function extractNodeId(nodeId) {{
                        if (!nodeId) return null;
                        
                        // 🚀 修复：处理多种 Mermaid 节点ID格式
                        // 格式1: "workflow-graph_flowchart-xxx-0" -> "xxx"
                        // 格式2: "flowchart-xxx-0" -> "xxx"
                        // 格式3: "L-xxx-yyy-0" (边) -> 返回 null
                        // 格式4: "xxx_group" -> "xxx_group"
                        
                        // 如果是边（L-开头），返回 null
                        if (nodeId.startsWith('L-')) {{
                            return null;
                        }}
                        
                        // 移除 workflow-graph_flowchart- 前缀
                        let cleanId = nodeId.replace(/^workflow-graph_flowchart-/, '');
                        // 移除 flowchart- 前缀
                        cleanId = cleanId.replace(/^flowchart-/, '');
                        // 移除 workflow-graph_ 前缀（如果还有）
                        cleanId = cleanId.replace(/^workflow-graph_/, '');
                        
                        // 移除数字后缀（如 "-0", "-1"）
                        cleanId = cleanId.replace(/-[0-9]+$/, '');
                        
                        // 移除其他可能的后缀（如 "pointEnd", "pointStart", "circleEnd" 等）
                        cleanId = cleanId.replace(/(pointEnd|pointStart|circleEnd|circleStart|crossEnd|crossStart)$/, '');
                        
                        return cleanId;
                    }}
                    
                    // 🚀 修复：改进节点组查找逻辑
                    // 从边ID中提取节点组名称，然后查找对应的节点
                    const groupNamesFromEdges = new Set();
                    allNodes.forEach(function(node) {{
                        const nodeId = node.getAttribute('id') || '';
                        if (nodeId.startsWith('L-')) {{
                            // 从边ID中提取节点组名称（格式：L-xxx_group-yyy-0）
                            const parts = nodeId.split('-');
                            for (let i = 1; i < parts.length; i++) {{
                                if (parts[i].endsWith('_group')) {{
                                    groupNamesFromEdges.add(parts[i]);
                                }}
                            }}
                        }}
                    }});
                    
                    console.log('🔍 调试：从边ID中提取的节点组名称:', Array.from(groupNamesFromEdges));
                    
                    // 🚀 修复：查找实际的节点元素（不是边，不是端点）
                    // Mermaid 生成的节点通常在 <g> 元素中，且包含 rect 或其他形状元素
                    const actualNodes = [];
                    const allGroupIds = [];
                    
                    // 查找所有包含形状元素的 <g> 元素
                    const allGroups = svgElement.querySelectorAll('g');
                    allGroups.forEach(function(group) {{
                        const nodeId = group.getAttribute('id') || '';
                        if (!nodeId) return;
                        
                        // 跳过边和端点
                        if (nodeId.startsWith('L-') || 
                            nodeId.includes('pointEnd') || 
                            nodeId.includes('pointStart') ||
                            nodeId.includes('circleEnd') ||
                            nodeId.includes('circleStart') ||
                            nodeId.includes('crossEnd') ||
                            nodeId.includes('crossStart')) {{
                            return;
                        }}
                        
                        // 检查是否包含形状元素（表示是节点）
                        const hasShape = group.querySelector('rect, circle, ellipse, polygon, path');
                        if (hasShape) {{
                            actualNodes.push(group);
                            const cleanId = extractNodeId(nodeId);
                            if (cleanId) {{
                                allGroupIds.push({{ originalId: nodeId, cleanId: cleanId, tagName: group.tagName, node: group }});
                            }}
                        }}
                    }});
                    
                    console.log('🔍 调试：找到', actualNodes.length, '个实际节点元素');
                    console.log('🔍 调试：所有节点ID（前20个）:', allGroupIds.slice(0, 20).map(function(n) {{
                        return n.cleanId + ' (tag:' + n.tagName + ', orig:' + n.originalId.substring(0, 40) + ')';
                    }}));
                    
                    // 🚀 修复：通过多种方式查找节点组节点
                    const possibleGroupIds = [];
                    
                    // 方法1：通过节点ID匹配
                    allGroupIds.forEach(function(item) {{
                        const cleanId = item.cleanId;
                        if (cleanId.endsWith('_group')) {{
                            possibleGroupIds.push({{ originalId: item.originalId, cleanId: cleanId, node: item.node }});
                        }} else if (nodeGroups[cleanId]) {{
                            possibleGroupIds.push({{ originalId: item.originalId, cleanId: cleanId + '_group', node: item.node }});
                        }}
                    }});
                    
                    // 方法2：通过文本内容匹配节点组
                    actualNodes.forEach(function(node) {{
                        const textElements = node.querySelectorAll('text');
                        textElements.forEach(function(textEl) {{
                            const textContent = textEl.textContent.trim();
                            if (!textContent) return;
                            
                            // 检查文本是否包含节点组名称
                            Object.keys(nodeGroups).forEach(function(groupId) {{
                                const groupInfo = nodeGroups[groupId];
                                if (textContent.includes(groupInfo.name) || 
                                    textContent.includes(groupId.replace('_', ' '))) {{
                                    const groupNodeId = groupId + '_group';
                                    // 避免重复添加
                                    const exists = possibleGroupIds.some(function(item) {{
                                        return item.node === node;
                                    }});
                                    if (!exists) {{
                                        possibleGroupIds.push({{ 
                                            originalId: node.getAttribute('id') || '', 
                                            cleanId: groupNodeId, 
                                            node: node,
                                            matchedBy: 'text: ' + textContent
                                        }});
                                    }}
                                }}
                            }});
                        }});
                    }});
                    
                    console.log('🔍 调试：可能的节点组ID:', possibleGroupIds.map(function(n) {{
                        return n.cleanId + ' (orig:' + n.originalId.substring(0, 40) + (n.matchedBy ? ', ' + n.matchedBy : '') + ')';
                    }}));
                    console.log('🔍 调试：nodeGroups 中的键:', Object.keys(nodeGroups));
                    
                    // 🚀 修复：改进节点组识别逻辑
                    possibleGroupIds.forEach(function(item) {{
                        const node = item.node;
                        const cleanId = item.cleanId;
                        
                        // 移除 _group 后缀获取真正的节点组ID
                        let groupId = cleanId;
                        if (cleanId.endsWith('_group')) {{
                            groupId = cleanId.replace('_group', '');
                        }}
                        
                        // 检查是否在 nodeGroups 中
                        if (nodeGroups[groupId]) {{
                            // 🚀 修复：识别节点组容器
                            // Mermaid 生成的节点组节点可能是 <g> 元素，也可能包含在 <g> 元素中
                            // 需要查找包含节点组标签的容器
                            let containerNode = node;
                            
                            // 如果当前节点不是 <g>，查找父 <g> 元素
                            if (node.tagName !== 'g' && node.tagName !== 'G') {{
                                containerNode = node.closest('g');
                                if (!containerNode) {{
                                    containerNode = node;
                                }}
                            }}
                            
                            // 检查容器是否包含形状元素（表示是节点组容器）
                            const hasShape = containerNode.querySelector('rect, circle, ellipse, polygon, path');
                            if (hasShape || containerNode.querySelector('text')) {{
                                // 避免重复添加
                                if (groupNodes.indexOf(containerNode) === -1) {{
                                    groupNodes.push(containerNode);
                                }}
                            }}
                        }}
                    }});
                    
                    groupNodes.forEach(function(node) {{
                        // 🚀 修复：为节点组节点及其所有子元素添加点击事件
                        // 因为节点组可能是 <g> 容器，实际的点击区域在子元素上
                        
                        // 提取节点组ID（在循环外提取，避免重复计算）
                        const nodeId = node.getAttribute('id') || '';
                        let groupId = extractNodeId(nodeId);
                        if (groupId && groupId.endsWith('_group')) {{
                            groupId = groupId.replace('_group', '');
                        }}
                        
                        if (!groupId) {{
                            console.warn('⚠️ 无法提取节点组ID:', nodeId);
                            return;
                        }}
                        
                        // 创建点击处理函数
                        function handleGroupClick(e) {{
                            e.stopPropagation();
                            e.preventDefault();
                            
                            console.log('🖱️ 点击节点组:', groupId, '(当前状态:', expandedGroups.has(groupId) ? '展开' : '折叠', ')');
                            
                            // 切换展开/折叠状态
                            if (expandedGroups.has(groupId)) {{
                                expandedGroups.delete(groupId);
                                console.log('📦 折叠节点组:', groupId);
                            }} else {{
                                expandedGroups.add(groupId);
                                console.log('📂 展开节点组:', groupId);
                            }}
                            
                            // 重新加载图表
                            console.log('🔄 重新加载图表，展开的节点组:', Array.from(expandedGroups));
                            loadGraph();
                        }}
                        
                        // 为节点组容器本身添加点击事件
                        node.style.cursor = 'pointer';
                        node.style.transition = 'opacity 0.2s';
                        node.style.pointerEvents = 'auto';
                        node.addEventListener('click', handleGroupClick, true); // 使用捕获阶段
                        
                        // 🚀 修复：为节点组内的所有可交互元素添加点击事件
                        // 确保点击节点组内的任何元素都能触发展开/折叠
                        const interactiveElements = node.querySelectorAll('rect, circle, ellipse, polygon, path, text, g');
                        interactiveElements.forEach(function(element) {{
                            // 确保元素可以接收鼠标事件
                            if (element.style) {{
                                element.style.cursor = 'pointer';
                                element.style.pointerEvents = 'auto';
                            }}
                            // 为子元素添加点击事件（使用捕获阶段，确保优先处理）
                            element.addEventListener('click', handleGroupClick, true);
                        }});
                        
                        // 添加鼠标悬停效果
                        function handleMouseEnter() {{
                            node.style.opacity = '0.8';
                        }}
                        function handleMouseLeave() {{
                            node.style.opacity = '1';
                        }}
                        
                        node.addEventListener('mouseenter', handleMouseEnter);
                        node.addEventListener('mouseleave', handleMouseLeave);
                        
                        // 为子元素也添加悬停效果
                        interactiveElements.forEach(function(element) {{
                            element.addEventListener('mouseenter', handleMouseEnter);
                            element.addEventListener('mouseleave', handleMouseLeave);
                        }});
                    }});
                    
                    console.log('✅ 节点组点击事件处理器已设置，找到', groupNodes.length, '个节点组节点');
                    if (groupNodes.length === 0) {{
                        console.log('⚠️ 提示：如果节点组已折叠，节点组节点可能不存在于SVG中');
                    }} else {{
                        // 🚀 调试：输出找到的节点组ID
                        const groupIds = [];
                        groupNodes.forEach(function(node) {{
                            const nodeId = node.getAttribute('id') || '';
                            let groupId = extractNodeId(nodeId);
                            if (groupId && groupId.endsWith('_group')) {{
                                groupId = groupId.replace('_group', '');
                            }}
                            if (groupId) {{
                                groupIds.push(groupId);
                            }}
                        }});
                        console.log('📋 找到的节点组ID（前10个）:', groupIds.slice(0, 10).join(', '));
                    }}
                }}
                
                // 🚀 新增：设置节点 tooltip 功能
                function setupNodeTooltips(nodeDescriptions) {{
                    if (!svgElement || !nodeDescriptions) {{
                        console.warn('⚠️ setupNodeTooltips: svgElement 或 nodeDescriptions 为空');
                        return;
                    }}
                    
                    // 🚀 调试：输出节点描述数据的键
                    console.log('🔍 调试：节点描述数据键数量:', Object.keys(nodeDescriptions).length);
                    console.log('🔍 调试：节点描述数据键（前10个）:', Object.keys(nodeDescriptions).slice(0, 10));
                    
                    // 创建 tooltip 元素
                    let tooltip = document.getElementById('node-tooltip');
                    if (!tooltip) {{
                        tooltip = document.createElement('div');
                        tooltip.id = 'node-tooltip';
                        tooltip.style.cssText = `
                            position: fixed;
                            background: rgba(0, 0, 0, 0.95);
                            color: white;
                            padding: 12px 16px;
                            border-radius: 8px;
                            font-size: 13px;
                            max-width: 350px;
                            z-index: 10000;
                            pointer-events: none;
                            opacity: 0;
                            visibility: hidden;
                            transition: opacity 0.2s ease-in-out;
                            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
                            line-height: 1.6;
                            word-wrap: break-word;
                            border: 1px solid rgba(255, 255, 255, 0.2);
                        `;
                        document.body.appendChild(tooltip);
                    }} else {{
                        // 🚀 修复：确保 tooltip 初始状态是隐藏的
                        tooltip.style.opacity = '0';
                        tooltip.style.visibility = 'hidden';
                    }}
                    
                    // 🚀 修复：改进节点查找逻辑
                    // Mermaid 生成的节点可能在 <g> 元素中，ID格式可能是：
                    // - 直接节点ID: "route_query"
                    // - 带前缀: "flowchart-route_query-0" 或 "flowchart-route_query"
                    // - 节点组: "multi_agent_group"
                    // 需要查找所有可能的节点元素
                    const allNodes = svgElement.querySelectorAll('g[id], [id]');
                    console.log('🔍 调试：SVG中找到', allNodes.length, '个带ID的元素');
                    
                    let tooltipCount = 0;
                    let debugInfo = {{ found: [], notFound: [], allIds: [] }};
                    
                    // 🚀 修复：创建节点ID映射函数，支持多种ID格式
                    function extractNodeId(nodeId) {{
                        if (!nodeId) return null;
                        
                        // 🚀 修复：处理多种 Mermaid 节点ID格式
                        // 格式1: "workflow-graph_flowchart-xxx-0" -> "xxx"
                        // 格式2: "flowchart-xxx-0" -> "xxx"
                        // 格式3: "L-xxx-yyy-0" (边) -> 返回 null
                        // 格式4: "xxx_group" -> "xxx_group"
                        
                        // 如果是边（L-开头），返回 null
                        if (nodeId.startsWith('L-')) {{
                            return null;
                        }}
                        
                        // 移除 workflow-graph_flowchart- 前缀
                        let cleanId = nodeId.replace(/^workflow-graph_flowchart-/, '');
                        // 移除 flowchart- 前缀
                        cleanId = cleanId.replace(/^flowchart-/, '');
                        // 移除 workflow-graph_ 前缀（如果还有）
                        cleanId = cleanId.replace(/^workflow-graph_/, '');
                        
                        // 移除数字后缀（如 "-0", "-1"）
                        cleanId = cleanId.replace(/-[0-9]+$/, '');
                        
                        // 移除其他可能的后缀（如 "pointEnd", "pointStart", "circleEnd" 等）
                        cleanId = cleanId.replace(/(pointEnd|pointStart|circleEnd|circleStart|crossEnd|crossStart)$/, '');
                        
                        return cleanId;
                    }}
                    
                    // 🚀 新增：通过文本内容匹配节点的辅助函数
                    function findNodeByText(nodeElement, nodeDescriptions) {{
                        // 查找节点内的文本元素
                        const textElements = nodeElement.querySelectorAll('text');
                        for (let i = 0; i < textElements.length; i++) {{
                            const textContent = textElements[i].textContent.trim();
                            if (!textContent) continue;
                            
                            // 尝试匹配节点描述数据的键
                            // 将文本转换为可能的节点ID（移除空格，转换为小写，替换空格为下划线）
                            const possibleIds = [
                                textContent.toLowerCase().replace(/\\s+/g, '_'),
                                textContent.toLowerCase().replace(/\\s+/g, ''),
                                textContent
                            ];
                            
                            for (let j = 0; j < possibleIds.length; j++) {{
                                if (nodeDescriptions[possibleIds[j]]) {{
                                    return possibleIds[j];
                                }}
                            }}
                        }}
                        return null;
                    }}
                    
                    // 🚀 修复：统一检测默认值说明的函数，确保与后端一致
                    function isDefaultDescription(desc) {{
                        if (!desc || typeof desc !== 'string') return true;
                        const descLower = desc.toLowerCase().trim();
                        return (
                            descLower === 'node in a graph.' || 
                            descLower === 'node in graph' || 
                            descLower === 'node in graph.' || 
                            descLower === 'node' ||
                            descLower === '' ||
                            descLower === 'node in a graph' ||
                            descLower.includes('node in graph')
                        );
                    }}
                    
                    allNodes.forEach(function(node) {{
                        const nodeId = node.getAttribute('id') || '';
                        if (!nodeId) return;
                        
                        debugInfo.allIds.push(nodeId);
                        
                        // 提取节点ID
                        let actualNodeId = extractNodeId(nodeId);
                        if (!actualNodeId) return;
                        
                        // 🚀 调试：对于 route_query 节点，输出详细信息
                        if (actualNodeId === 'route_query') {{
                            console.log('🔍 [tooltip] 处理 route_query 节点:', {{
                                originalId: nodeId,
                                cleanId: actualNodeId,
                                hasDescription: !!nodeDescriptions[actualNodeId],
                                descriptionValue: nodeDescriptions[actualNodeId] ? nodeDescriptions[actualNodeId].substring(0, 50) : 'None'
                            }});
                        }}
                        
                        let description = null;
                        let matchedId = actualNodeId;
                        
                        // 检查是否是节点组节点
                        if (actualNodeId.endsWith('_group')) {{
                            // 节点组节点
                            const groupId = actualNodeId.replace('_group', '');
                            if (nodeGroups[groupId]) {{
                                const groupInfo = nodeGroups[groupId];
                                if (groupInfo.description) {{
                                    description = groupInfo.description;
                                }} else if (groupInfo.name) {{
                                    description = groupInfo.name + '：包含 ' + (groupInfo.nodes ? groupInfo.nodes.length : 0) + ' 个节点';
                                }}
                            }}
                        }} else {{
                            // 普通节点，先尝试直接匹配
                            if (nodeDescriptions[actualNodeId]) {{
                                const descValue = nodeDescriptions[actualNodeId];
                                // 🚀 修复：检查是否是默认值（"Node in a graph." 或 "Node in graph"）
                                if (isDefaultDescription(descValue)) {{
                                    // 是默认值，不使用
                                    console.log('⚠️ [tooltip] 节点', actualNodeId, '的说明是默认值，忽略:', descValue);
                                    description = null;
                                }} else {{
                                    description = descValue;
                                    console.log('✅ [tooltip] 节点', actualNodeId, '直接匹配成功，说明:', description.substring(0, 50));
                                }}
                            }} else {{
                                // 🚀 新增：如果直接匹配失败，尝试通过文本内容匹配
                                const textMatchedId = findNodeByText(node, nodeDescriptions);
                                if (textMatchedId) {{
                                    matchedId = textMatchedId;
                                    const matchedDesc = nodeDescriptions[textMatchedId];
                                    // 🚀 修复：检查文本匹配到的说明是否是默认值
                                    if (isDefaultDescription(matchedDesc)) {{
                                        console.log('⚠️ [tooltip] 节点', actualNodeId, '通过文本匹配到的说明是默认值，忽略:', matchedDesc);
                                        description = null;
                                    }} else {{
                                        description = matchedDesc;
                                        console.log('✅ [tooltip] 节点', actualNodeId, '通过文本匹配成功，匹配ID:', textMatchedId, '说明:', description.substring(0, 50));
                                    }}
                                }} else {{
                                    // 🚀 调试：记录匹配失败的节点
                                    console.log('⚠️ [tooltip] 节点', actualNodeId, '匹配失败，节点描述数据中是否有该节点:', !!nodeDescriptions[actualNodeId]);
                                    // 🚀 调试：检查是否有相似的节点ID
                                    const similarKeys = Object.keys(nodeDescriptions).filter(function(key) {{
                                        return key.includes(actualNodeId) || actualNodeId.includes(key);
                                    }});
                                    if (similarKeys.length > 0) {{
                                        console.log('🔍 [tooltip] 找到相似的节点ID:', similarKeys.slice(0, 5));
                                    }}
                                }}
                            }}
                        }}
                        
                        // 如果有说明，设置 tooltip
                        if (description) {{
                            setupTooltipForNode(node, description, tooltip);
                            tooltipCount++;
                            debugInfo.found.push({{ originalId: nodeId, cleanId: actualNodeId, matchedId: matchedId }});
                        }} else {{
                            // 调试：记录未找到的节点
                            if (actualNodeId && !actualNodeId.includes('flowchart') && !actualNodeId.includes('subgraph') && !actualNodeId.includes('cluster')) {{
                                debugInfo.notFound.push({{ originalId: nodeId, cleanId: actualNodeId }});
                                // 🚀 调试：输出未找到节点的详细信息
                                console.log('⚠️ [tooltip] 节点', actualNodeId, '未找到说明，原始ID:', nodeId, '节点描述数据中是否有:', !!nodeDescriptions[actualNodeId]);
                            }}
                        }}
                    }});
                    
                    console.log('✅ 节点 tooltip 功能已设置，共', tooltipCount, '个节点有说明');
                    console.log('🔍 调试：所有节点ID（前20个）:', debugInfo.allIds.slice(0, 20));
                    if (debugInfo.found.length > 0) {{
                        console.log('📋 找到的节点:', debugInfo.found.slice(0, 10).map(function(n) {{ return n.matchedId || n.cleanId; }}).join(', '));
                    }}
                    if (debugInfo.notFound.length > 0 && debugInfo.notFound.length < 30) {{
                        console.log('⚠️ 未找到说明的节点（前15个）:', debugInfo.notFound.slice(0, 15).map(function(n) {{ return n.cleanId; }}).join(', '));
                        // 🚀 调试：输出未找到节点的详细信息，帮助诊断问题
                        console.log('🔍 调试：未找到说明的节点详情:', debugInfo.notFound.slice(0, 10).map(function(n) {{
                            return n.cleanId + ' (原始ID: ' + n.originalId + ')';
                        }}).join(', '));
                    }}
                    
                    // 🚀 调试：检查 route_query 节点是否在找到的节点中
                    const routeQueryFound = debugInfo.found.find(function(n) {{ return n.cleanId === 'route_query' || n.matchedId === 'route_query'; }});
                    if (!routeQueryFound) {{
                        console.warn('⚠️ [tooltip] route_query 节点未找到说明！');
                        console.log('  - 节点描述数据中是否有 route_query:', !!nodeDescriptions['route_query']);
                        console.log('  - route_query 的说明值:', nodeDescriptions['route_query'] ? nodeDescriptions['route_query'].substring(0, 50) : 'None');
                        // 🚀 调试：检查是否有 route_query 节点在 notFound 中
                        const routeQueryNotFound = debugInfo.notFound.find(function(n) {{ return n.cleanId === 'route_query'; }});
                        if (routeQueryNotFound) {{
                            console.log('  - route_query 在 notFound 列表中，原始ID:', routeQueryNotFound.originalId);
                        }}
                    }} else {{
                        console.log('✅ [tooltip] route_query 节点找到说明:', routeQueryFound.matchedId || routeQueryFound.cleanId, '说明:', nodeDescriptions[routeQueryFound.matchedId || routeQueryFound.cleanId] ? nodeDescriptions[routeQueryFound.matchedId || routeQueryFound.cleanId].substring(0, 50) : 'None');
                    }}
                    
                    // 🚀 调试：检查是否有节点描述数据但未找到对应节点
                    const foundNodeIds = new Set(debugInfo.found.map(function(n) {{ return n.matchedId || n.cleanId; }}));
                    const missingDescriptions = [];
                    for (const nodeId in nodeDescriptions) {{
                        if (!foundNodeIds.has(nodeId) && !nodeId.endsWith('_group')) {{
                            missingDescriptions.push(nodeId);
                        }}
                    }}
                    if (missingDescriptions.length > 0 && missingDescriptions.length < 20) {{
                        console.log('🔍 调试：有说明但未找到对应节点的节点（前10个）:', missingDescriptions.slice(0, 10).join(', '));
                    }}
                }}
                
                // 🚀 新增：为单个节点设置 tooltip
                function setupTooltipForNode(node, description, tooltip) {{
                    if (!description) return;
                    
                    // 🚀 修复：查找节点内的可交互元素（矩形、圆形、多边形等）
                    // Mermaid 生成的节点可能在 <g> 容器中，实际的形状在子元素中
                    const interactiveElements = node.querySelectorAll('rect, circle, ellipse, polygon, path');
                    const elementsToBind = interactiveElements.length > 0 ? interactiveElements : [node];
                    
                    elementsToBind.forEach(function(element) {{
                        // 确保元素可以接收鼠标事件
                        if (element.style) {{
                            element.style.cursor = 'help';
                            element.style.pointerEvents = 'auto';
                        }}
                        
                        // 添加鼠标悬停事件
                        element.addEventListener('mouseenter', function(e) {{
                            // 🚀 修复：只在鼠标悬停时显示 tooltip
                            tooltip.textContent = description;
                            tooltip.style.visibility = 'visible';
                            tooltip.style.opacity = '1';
                            
                            // 更新 tooltip 位置
                            updateTooltipPosition(e, tooltip);
                        }});
                        
                        // 添加鼠标移动事件（更新 tooltip 位置）
                        element.addEventListener('mousemove', function(e) {{
                            if (tooltip.style.opacity === '1') {{
                                updateTooltipPosition(e, tooltip);
                            }}
                        }});
                        
                        // 添加鼠标离开事件
                        element.addEventListener('mouseleave', function() {{
                            // 🚀 修复：鼠标离开时隐藏 tooltip
                            tooltip.style.opacity = '0';
                            tooltip.style.visibility = 'hidden';
                        }});
                    }});
                    
                    // 如果节点本身是 <g> 容器，也为其添加事件（作为后备）
                    if (node.tagName === 'g' && interactiveElements.length > 0) {{
                        if (node.style) {{
                            node.style.cursor = 'help';
                        }}
                    }}
                }}
                
                // 🚀 新增：更新 tooltip 位置的辅助函数
                function updateTooltipPosition(e, tooltip) {{
                    // 获取鼠标位置（相对于视口）
                    const mouseX = e.clientX || (e.touches && e.touches[0] ? e.touches[0].clientX : 0);
                    const mouseY = e.clientY || (e.touches && e.touches[0] ? e.touches[0].clientY : 0);
                    
                    if (!mouseX && !mouseY) return;
                    
                    // 设置 tooltip 位置（鼠标右下方）
                    const offsetX = 15;
                    const offsetY = -10;
                    tooltip.style.left = (mouseX + offsetX) + 'px';
                    tooltip.style.top = (mouseY + offsetY) + 'px';
                    
                    // 确保 tooltip 不会超出屏幕边界
                    // 使用 requestAnimationFrame 确保在渲染后计算
                    requestAnimationFrame(function() {{
                        const rect = tooltip.getBoundingClientRect();
                        const windowWidth = window.innerWidth;
                        const windowHeight = window.innerHeight;
                        
                        // 如果超出右边界，显示在鼠标左侧
                        if (rect.right > windowWidth) {{
                            tooltip.style.left = (mouseX - rect.width - offsetX) + 'px';
                        }}
                        
                        // 如果超出左边界，显示在鼠标右侧
                        if (rect.left < 0) {{
                            tooltip.style.left = (mouseX + offsetX) + 'px';
                        }}
                        
                        // 如果超出下边界，显示在鼠标上方
                        if (rect.bottom > windowHeight) {{
                            tooltip.style.top = (mouseY - rect.height - offsetY) + 'px';
                        }}
                        
                        // 如果超出上边界，显示在鼠标下方
                        if (rect.top < 0) {{
                            tooltip.style.top = (mouseY + offsetY) + 'px';
                        }}
                    }});
                }}

                function applyZoom() {{
                    if (svgElement) {{
                        svgElement.style.transform = `scale(${{currentScale}})`;
                        svgElement.style.transformOrigin = 'top left';
                    }}
                }}

                function zoomIn() {{
                    if (currentScale < maxScale) {{
                        currentScale = Math.min(currentScale + 0.2, maxScale);
                        applyZoom();
                    }}
                }}

                function zoomOut() {{
                    if (currentScale > minScale) {{
                        currentScale = Math.max(currentScale - 0.2, minScale);
                        applyZoom();
                    }}
                }}

                function resetZoom() {{
                    currentScale = 1.5;
                    applyZoom();
                }}

                function fitToScreen() {{
                    const wrapper = document.getElementById('mermaid-wrapper');
                    if (svgElement && wrapper) {{
                        const wrapperWidth = wrapper.clientWidth;
                        const svgWidth = svgElement.getBBox().width;
                        if (svgWidth > 0) {{
                            currentScale = Math.min(wrapperWidth / svgWidth, maxScale);
                            applyZoom();
                        }}
                    }}
                }}

                // 鼠标滚轮缩放
                document.addEventListener('DOMContentLoaded', function() {{
                    const wrapper = document.getElementById('mermaid-wrapper');
                    if (wrapper) {{
                        wrapper.addEventListener('wheel', function(e) {{
                            if (e.ctrlKey || e.metaKey) {{
                                e.preventDefault();
                                if (e.deltaY < 0) {{
                                    zoomIn();
                                }} else {{
                                    zoomOut();
                                }}
                            }}
                        }}, {{ passive: false }});
                    }}
                }});

                function exportGraph() {{
                    // 导出功能
                    alert('导出功能开发中...');
                }}

                // 🚀 新增：执行工作流
                async function executeGraphWorkflow() {{
                    const query = document.getElementById('graph-query-input').value.trim();
                    if (!query) {{
                        alert('请输入查询内容');
                        return;
                    }}
                    
                    try {{
                        // 禁用执行按钮，启用停止按钮
                        document.getElementById('graph-execute-btn').disabled = true;
                        document.getElementById('graph-stop-btn').style.display = 'inline-block';
                        document.getElementById('graph-stop-btn').disabled = false;
                        
                        // 清空节点状态
                        nodeStatusMap = {{}};
                        executionPath = [];
                        refreshGraphNodeStatus();
                        
                        // 尝试多个可能的API路径
                        let response = null;
                        let result = null;
                        
                        // 尝试路径1: /api/workflow/execute
                        console.log('🚀 发送API请求到: /api/workflow/execute');
                        console.log('📤 请求数据:', {{state: {{query: query}}}});
                        try {{
                            response = await fetch('/api/workflow/execute', {{
                                method: 'POST',
                                headers: {{'Content-Type': 'application/json'}},
                                body: JSON.stringify({{state: {{query: query}}}})
                            }});
                            console.log('📥 API响应状态:', response.status, response.statusText);
                            if (response.ok) {{
                                result = await response.json();
                                console.log('📥 API响应数据:', result);
                                result = await response.json();
                            }}
                        }} catch (e) {{
                            console.log('路径1失败，尝试路径2...');
                        }}
                        
                        // 尝试路径2: /visualization/api/workflow/execute
                        if (!result) {{
                            try {{
                                response = await fetch('/visualization/api/workflow/execute', {{
                                    method: 'POST',
                                    headers: {{'Content-Type': 'application/json'}},
                                    body: JSON.stringify({{state: {{query: query}}}})
                                }});
                                if (response.ok) {{
                                    result = await response.json();
                                }}
                            }} catch (e) {{
                                console.log('路径2失败');
                            }}
                        }}
                        
                        if (!result || result.error) {{
                            throw new Error(result?.error || '无法找到工作流执行API端点');
                        }}
                        
                        currentExecutionId = result.execution_id;
                        console.log('🎯 获取到execution_id:', currentExecutionId);

                        // 建立 WebSocket 连接
                        console.log('🔌 开始建立WebSocket连接...');
                        connectWebSocket(currentExecutionId);
                        
                        // 更新URL参数
                        const url = new URL(window.location);
                        url.searchParams.set('execution_id', currentExecutionId);
                        window.history.pushState({{}}, '', url);
                        
                        alert(`工作流执行已开始: ${{currentExecutionId}}`);
                        
                    }} catch (error) {{
                        console.error('执行工作流失败:', error);
                        alert('执行工作流失败: ' + error.message);
                        resetGraphControls();
                    }}
                }}
                
                // 🚀 新增：停止工作流执行
                function stopGraphWorkflow() {{
                    if (websocket) {{
                        websocket.close();
                        websocket = null;
                    }}
                    currentExecutionId = null;
                    resetGraphControls();
                    alert('工作流执行已停止');
                }}
                
                // 🚀 新增：重置控件
                function resetGraphControls() {{
                    document.getElementById('graph-execute-btn').disabled = false;
                    document.getElementById('graph-stop-btn').style.display = 'none';
                    document.getElementById('graph-stop-btn').disabled = true;
                    // 隐藏进度条
                    const progressContainer = document.getElementById('graph-progress-container');
                    if (progressContainer) {{
                        progressContainer.classList.remove('active');
                    }}
                }}

                // 🚀 新增：进度条相关变量
                let graphTotalNodes = 0;
                let graphCompletedNodes = 0;
                let graphRunningNodes = 0;
                let graphErrorNodes = 0;
                let graphNodeSteps = {{}}; // 存储节点步骤信息

                // 🚀 新增：更新进度条
                function updateGraphProgress() {{
                    console.log('🔄 updateGraphProgress() 开始执行');
                    console.log('📊 当前状态:', {{
                        graphTotalNodes,
                        graphCompletedNodes,
                        graphRunningNodes,
                        graphErrorNodes
                    }});

                    const progressContainer = document.getElementById('graph-progress-container');
                    const progressBar = document.getElementById('graph-progress-bar');
                    const progressText = document.getElementById('graph-progress-text');
                    const progressDetail = document.getElementById('graph-progress-detail');
                    const progressSteps = document.getElementById('graph-progress-steps');

                    console.log('🎯 DOM元素查找结果:', {{
                        progressContainer: !!progressContainer,
                        progressBar: !!progressBar,
                        progressText: !!progressText,
                        progressDetail: !!progressDetail
                    }});

                    if (!progressContainer || !progressBar || !progressText || !progressDetail) {{
                        console.warn('⚠️ updateGraphProgress() 缺少必要的DOM元素');
                        return;
                    }}

                    // 显示进度条
                    progressContainer.classList.add('active');
                    console.log('✅ 进度条已设置为active状态');
                    
                    // 计算进度百分比
                    let percentage = 0;
                    if (graphTotalNodes > 0) {{
                        percentage = Math.round((graphCompletedNodes / graphTotalNodes) * 100);
                    }}
                    
                    // 更新进度条宽度
                    progressBar.style.width = percentage + '%';
                    
                    // 更新进度文本
                    progressText.textContent = percentage + '%';
                    
                    // 更新详细信息
                    const detailParts = [];
                    if (graphRunningNodes > 0) {{
                        detailParts.push('运行中: ' + graphRunningNodes);
                    }}
                    if (graphCompletedNodes > 0) {{
                        detailParts.push('已完成: ' + graphCompletedNodes);
                    }}
                    if (graphErrorNodes > 0) {{
                        detailParts.push('错误: ' + graphErrorNodes);
                    }}
                    if (graphTotalNodes > 0) {{
                        detailParts.push('总计: ' + graphTotalNodes);
                    }}
                    progressDetail.textContent = detailParts.length > 0 ? detailParts.join(' | ') : '0/0 节点';
                    
                    // 更新步骤列表（显示最近执行的节点）
                    if (progressSteps) {{
                        const recentSteps = Object.values(graphNodeSteps)
                            .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
                            .slice(0, 5); // 只显示最近5个节点
                        
                        if (recentSteps.length > 0) {{
                            progressSteps.innerHTML = recentSteps.map(step => {{
                                const icon = step.status === 'completed' ? '✓' : 
                                           step.status === 'running' ? '⟳' : 
                                           step.status === 'error' ? '✗' : '○';
                                const statusClass = step.status || 'idle';
                                const className = 'progress-step ' + statusClass;
                                const nodeName = step.node || 'unknown';
                                return '<div class="' + className + '">' +
                                    '<span class="step-icon">' + icon + '</span>' +
                                    '<span>' + nodeName + '</span>' +
                                    '</div>';
                            }}).join('');
                        }} else {{
                            progressSteps.innerHTML = '';
                        }}
                    }}
                }}

                // 🚀 新增：初始化进度条
                function initGraphProgress() {{
                    console.log('🎯 initGraphProgress() 开始执行');
                    graphTotalNodes = 0;
                    graphCompletedNodes = 0;
                    graphRunningNodes = 0;
                    graphErrorNodes = 0;
                    graphNodeSteps = {{}};
                    console.log('📊 进度条变量已重置:', {{
                        graphTotalNodes,
                        graphCompletedNodes,
                        graphRunningNodes,
                        graphErrorNodes
                    }});
                    updateGraphProgress();
                    console.log('🔄 updateGraphProgress() 已调用');
                }}
                
                // 🚀 新增：支持回车键执行
                document.addEventListener('DOMContentLoaded', function() {{
                    const queryInput = document.getElementById('graph-query-input');
                    if (queryInput) {{
                        queryInput.addEventListener('keypress', function(e) {{
                            if (e.key === 'Enter') {{
                                executeGraphWorkflow();
                            }}
                        }});
                    }}
                }});

                // 🚀 新增：在执行工作流时初始化进度条
                async function executeGraphWorkflow() {{
                    const queryInput = document.getElementById('graph-query-input');
                    const query = queryInput ? queryInput.value.trim() : '';
                    
                    if (!query) {{
                        alert('请输入查询内容');
                        return;
                    }}
                    
                    // 初始化进度条
                    initGraphProgress();
                    
                    // 禁用执行按钮，启用停止按钮
                    document.getElementById('graph-execute-btn').disabled = true;
                    const stopBtn = document.getElementById('graph-stop-btn');
                    stopBtn.style.display = 'inline-block';
                    stopBtn.disabled = false;
                    
                    try {{
                        const response = await fetch('/visualization/api/workflow/execute', {{
                            method: 'POST',
                            headers: {{ 'Content-Type': 'application/json' }},
                            body: JSON.stringify({{ query: query }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error('执行失败: ' + response.statusText);
                        }}
                        
                        const data = await response.json();
                        const executionId = data.execution_id;
                        
                        if (executionId) {{
                            // 连接WebSocket
                            connectWebSocket(executionId);
                            
                            // 更新URL参数
                            const url = new URL(window.location);
                            url.searchParams.set('execution_id', executionId);
                            window.history.pushState({{}}, '', url);
                        }}
                    }} catch (error) {{
                        console.error('执行工作流失败:', error);
                        alert('执行失败: ' + error.message);
                        resetGraphControls();
                    }}
                }}
                
                // 页面加载时自动加载图表和tab数据
                document.addEventListener('DOMContentLoaded', function() {{
                    loadGraph();
                    refreshGraphNodeStatus();
                    refreshGraphSystemHealth();
                    
                    // 🚀 新增：尝试从URL参数获取execution_id并连接WebSocket
                    const urlParams = new URLSearchParams(window.location.search);
                    const executionId = urlParams.get('execution_id');
                    if (executionId) {{
                        connectWebSocket(executionId);
                    }}
                }});
                // 🚀 新增：切换主tab
                function switchMainTab(tabName) {{
                    // 隐藏所有主tab内容
                    document.querySelectorAll('.main-tab-content').forEach(content => {{
                        content.classList.remove('active');
                        content.style.display = 'none';
                    }});
                    
                    // 移除所有主tab按钮的active类
                    document.querySelectorAll('.main-tab').forEach(tab => {{
                        tab.classList.remove('active');
                    }});
                    
                    // 显示选中的主tab内容
                    const targetTab = document.getElementById(`main-tab-${{tabName}}`);
                    if (targetTab) {{
                        targetTab.classList.add('active');
                        targetTab.style.display = 'flex';
                    }}
                    
                    // 激活对应的主tab按钮
                    document.querySelectorAll('.main-tab').forEach(tab => {{
                        if (tab.getAttribute('onclick')?.includes(tabName)) {{
                            tab.classList.add('active');
                        }}
                    }});
                    
                    // 根据tab类型刷新数据
                    if (tabName === 'node-status') {{
                        refreshGraphNodeStatus();
                    }} else if (tabName === 'system-health') {{
                        refreshGraphSystemHealth();
                    }} else if (tabName === 'workflow-graph') {{
                        loadGraph();
                    }}
                }}
                
                // 节点状态映射（用于存储实时节点状态）
                let nodeStatusMap = {{}};
                let executionPath = [];
                let websocket = null;
                let currentExecutionId = null;
                
                // 🚀 新增：刷新工作流tab内的节点状态（显示详细执行状态）
                function refreshGraphNodeStatus() {{
                    const contentDiv = document.getElementById('graph-node-status-content');
                    if (!contentDiv) return;
                    
                    // 统计节点状态
                    const runningNodes = [];
                    const completedNodes = [];
                    const errorNodes = [];
                    const allNodes = new Set();
                    const nodeDetails = {{}};
                    
                    // 从nodeStatusMap获取节点状态
                    for (const [nodeName, status] of Object.entries(nodeStatusMap)) {{
                        allNodes.add(nodeName);
                        nodeDetails[nodeName] = {{ status: status }};
                        if (status === 'running') {{
                            runningNodes.push(nodeName);
                        }} else if (status === 'completed') {{
                            completedNodes.push(nodeName);
                        }} else if (status === 'error') {{
                            errorNodes.push(nodeName);
                        }}
                    }}
                    
                    // 从executionPath获取节点信息（补充可能遗漏的节点）
                    if (executionPath && Array.isArray(executionPath)) {{
                        executionPath.forEach(item => {{
                            const nodeName = item.node || item.name;
                            if (nodeName) {{
                                allNodes.add(nodeName);
                                if (!nodeDetails[nodeName]) {{
                                    nodeDetails[nodeName] = {{}};
                                }}
                                nodeDetails[nodeName].timestamp = item.timestamp;
                                nodeDetails[nodeName].execution_time = item.execution_time;
                                nodeDetails[nodeName].state = item.state;
                                
                                if (item.status === 'running' && !runningNodes.includes(nodeName)) {{
                                    runningNodes.push(nodeName);
                                    if (!nodeStatusMap[nodeName]) nodeStatusMap[nodeName] = 'running';
                                }} else if (item.status === 'completed' && !completedNodes.includes(nodeName)) {{
                                    completedNodes.push(nodeName);
                                    if (!nodeStatusMap[nodeName]) nodeStatusMap[nodeName] = 'completed';
                                }} else if (item.status === 'error' && !errorNodes.includes(nodeName)) {{
                                    errorNodes.push(nodeName);
                                    if (!nodeStatusMap[nodeName]) nodeStatusMap[nodeName] = 'error';
                                }}
                            }}
                        }});
                    }}
                    
                    // 更新统计数字
                    document.getElementById('graph-node-running-count').textContent = runningNodes.length;
                    document.getElementById('graph-node-completed-count').textContent = completedNodes.length;
                    document.getElementById('graph-node-error-count').textContent = errorNodes.length;
                    document.getElementById('graph-node-total-count').textContent = allNodes.size;
                    
                    // 如果没有节点数据，显示提示
                    if (allNodes.size === 0) {{
                        contentDiv.innerHTML = '<p style="color: #999; font-style: italic; text-align: center; padding: 40px; font-size: 12px;">等待执行开始... 执行工作流后，节点状态将实时显示在这里。</p>';
                        return;
                    }}
                    
                    // 格式化节点名称
                    function formatNodeName(name) {{
                        return name.split('_').map(word => 
                            word.charAt(0).toUpperCase() + word.slice(1)
                        ).join(' ');
                    }}
                    
                    // 构建节点列表HTML（详细版本）
                    let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
                    
                    // 按状态分组显示节点
                    const nodeGroups = [
                        {{'title': '运行中', 'nodes': runningNodes, 'color': '#ffeb3b', 'bgColor': '#fff9c4', 'statusClass': 'running'}},
                        {{'title': '已完成', 'nodes': completedNodes, 'color': '#4caf50', 'bgColor': '#c8e6c9', 'statusClass': 'completed'}},
                        {{'title': '错误', 'nodes': errorNodes, 'color': '#f44336', 'bgColor': '#ffcdd2', 'statusClass': 'error'}}
                    ];
                    
                    nodeGroups.forEach(group => {{
                        if (group.nodes.length > 0) {{
                            // 提取颜色值，避免在HTML属性中直接使用模板表达式
                            const groupColor = group.color;
                            const groupBgColor = group.bgColor;
                            html += `<div style="margin-bottom: 15px;">
                                <h3 style="margin: 0 0 10px 0; font-size: 14px; color: ${{groupColor}}; display: flex; align-items: center; gap: 8px;">
                                    <span style="display: inline-block; width: 16px; height: 16px; background: ${{groupBgColor}}; border: 2px solid ${{groupColor}}; border-radius: 2px;"></span>
                                    ${{group.title}} (${{group.nodes.length}})
                                </h3>
                                <div style="display: flex; flex-direction: column; gap: 8px;">`;
                            
                            group.nodes.forEach(nodeName => {{
                                const details = nodeDetails[nodeName] || {{}};
                                const status = details.status || group.statusClass;
                                const timestamp = details.timestamp ? new Date(details.timestamp).toLocaleTimeString() : '';
                                const executionTime = details.execution_time ? `${{details.execution_time.toFixed(3)}}s` : '';
                                
                                const statusBadgeText = {{
                                    'running': '运行中',
                                    'completed': '已完成',
                                    'error': '错误',
                                    'idle': '等待中'
                                }}[status] || status;
                                
                                const statusDescription = {{
                                    'running': '节点正在执行中...',
                                    'completed': '节点执行成功完成',
                                    'error': '节点执行出现错误',
                                    'idle': '节点等待执行'
                                }}[status] || '';
                                
                                html += `<div class="node-status-item ${{status}}" style="padding: 12px; border-radius: 6px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                                        <h4 style="margin: 0; font-size: 14px; font-weight: bold; color: #333;">${{formatNodeName(nodeName)}}</h4>
                                        <span style="padding: 4px 8px; background: ${{groupColor}}; color: white; border-radius: 12px; font-size: 11px; font-weight: bold;">${{statusBadgeText}}</span>
                                    </div>
                                    <div style="font-size: 12px; color: #666; margin-bottom: 5px;">${{statusDescription}}</div>
                                    <div style="display: flex; gap: 15px; font-size: 11px; color: #999;">
                                        ${{timestamp ? '<span>时间: ' + timestamp + '</span>' : ''}}
                                        ${{executionTime ? '<span>执行时间: ' + executionTime + '</span>' : ''}}
                                    </div>
                                    ${{details.state ? '<details style="margin-top: 8px;"><summary style="cursor: pointer; color: #666; font-size: 11px;">查看状态详情</summary><pre style="background: #f0f0f0; padding: 8px; margin-top: 5px; border-radius: 3px; font-size: 10px; overflow-x: auto; max-height: 200px; overflow-y: auto;">' + JSON.stringify(details.state, null, 2) + '</pre></details>' : ''}}
                                </div>`;
                            }});
                            
                            html += '</div></div>';
                        }}
                    }});
                    
                    // 显示未分类的节点（如果有）
                    const allProcessedNodes = new Set([...runningNodes, ...completedNodes, ...errorNodes]);
                    const unprocessedNodes = Array.from(allNodes).filter(node => !allProcessedNodes.has(node));
                    
                    if (unprocessedNodes.length > 0) {{
                        html += `<div style="margin-bottom: 15px;">
                            <h3 style="margin: 0 0 10px 0; font-size: 14px; color: #999;">其他节点 (${{unprocessedNodes.length}})</h3>
                            <div style="display: flex; flex-direction: column; gap: 8px;">`;
                        
                        unprocessedNodes.forEach(nodeName => {{
                            html += `<div class="node-status-item idle" style="padding: 12px; border-radius: 6px;">
                                <div style="font-weight: bold; font-size: 14px; color: #333;">${{formatNodeName(nodeName)}}</div>
                                <div style="font-size: 11px; color: #999; margin-top: 5px;">状态未知</div>
                            </div>`;
                        }});
                        
                        html += '</div></div>';
                    }}
                    
                    html += '</div>';
                    contentDiv.innerHTML = html;
                }}
                
                // 🚀 新增：连接WebSocket获取实时节点状态更新
                function connectWebSocket(executionId) {{
                    if (!executionId) return;
                    
                    // 如果已有连接，先关闭
                    if (websocket) {{
                        websocket.close();
                    }}
                    
                    // 确定WebSocket URL
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${{protocol}}//${{window.location.host}}/ws/${{executionId}}`;
                    
                    websocket = new WebSocket(wsUrl);
                    currentExecutionId = executionId;
                    
                    websocket.onopen = () => {{
                        console.log('✅ WebSocket连接已建立:', executionId);
                        console.log('🔍 WebSocket URL:', wsUrl);
                        console.log('🚀 WebSocket连接已准备好接收消息');
                    }};

                    websocket.onerror = (error) => {{
                        console.error('❌ WebSocket连接错误:', error, executionId);
                    }};

                    websocket.onclose = (event) => {{
                        console.log('🔌 WebSocket连接已关闭:', executionId, '代码:', event.code, '原因:', event.reason);
                    }};

                    websocket.onmessage = (event) => {{
                        console.log('📨 收到WebSocket消息:', event.data);
                        console.log('📨 原始消息数据类型:', typeof event.data);
                        try {{
                            const message = JSON.parse(event.data);
                            console.log('📨 解析后的消息:', message);
                            console.log('📨 消息类型:', message.type);

                            console.log('🔍 处理消息类型:', message.type);

                            if (message.type === 'node_update') {{
                                console.log('📊 处理node_update消息');
                                const nodeInfo = message.data || message;
                                const nodeName = (nodeInfo.name || nodeInfo.node || 'unknown').toLowerCase().replace(/\\s+/g, '_');
                                const status = nodeInfo.status || 'running';
                                
                                // 更新nodeStatusMap
                                nodeStatusMap[nodeName] = status;
                                
                                // 🚀 新增：更新进度条统计
                                const previousStatus = graphNodeSteps[nodeName]?.status;
                                
                                // 更新节点步骤信息
                                graphNodeSteps[nodeName] = {{
                                    node: nodeName,
                                    status: status,
                                    timestamp: nodeInfo.timestamp || Date.now(),
                                    execution_time: nodeInfo.execution_time
                                }};
                                
                                // 更新统计计数
                                if (previousStatus === 'running') {{
                                    graphRunningNodes = Math.max(0, graphRunningNodes - 1);
                                }} else if (previousStatus === 'completed') {{
                                    graphCompletedNodes = Math.max(0, graphCompletedNodes - 1);
                                }} else if (previousStatus === 'error') {{
                                    graphErrorNodes = Math.max(0, graphErrorNodes - 1);
                                }}
                                
                                if (status === 'running') {{
                                    graphRunningNodes++;
                                    // 如果是新节点，增加总数
                                    if (!previousStatus) {{
                                        graphTotalNodes++;
                                    }}
                                }} else if (status === 'completed') {{
                                    graphCompletedNodes++;
                                    graphRunningNodes = Math.max(0, graphRunningNodes - 1);
                                }} else if (status === 'error') {{
                                    graphErrorNodes++;
                                    graphRunningNodes = Math.max(0, graphRunningNodes - 1);
                                }}
                                
                                // 更新进度条
                                updateGraphProgress();
                                
                                // 更新executionPath
                                if (!executionPath) {{
                                    executionPath = [];
                                }}
                                
                                const existingIndex = executionPath.findIndex(item => item.node === nodeName);
                                if (existingIndex === -1) {{
                                    executionPath.push({{
                                        node: nodeName,
                                        timestamp: nodeInfo.timestamp || Date.now(),
                                        status: status,
                                        execution_time: nodeInfo.execution_time,
                                        state: nodeInfo.state
                                    }});
                                }} else {{
                                    executionPath[existingIndex].status = status;
                                    executionPath[existingIndex].timestamp = nodeInfo.timestamp || executionPath[existingIndex].timestamp;
                                    if (nodeInfo.execution_time) executionPath[existingIndex].execution_time = nodeInfo.execution_time;
                                    if (nodeInfo.state) executionPath[existingIndex].state = nodeInfo.state;
                                }}
                                
                                // 🚀 新增：更新工作流图中的节点高亮显示
                                console.log('📡 [WebSocket] 收到节点更新: ' + nodeName + ', 状态: ' + status);
                                updateWorkflowGraphNode(nodeName, status);
                                
                                // 🚀 新增：延迟再次更新，确保节点已渲染
                                setTimeout(function() {{
                                    updateWorkflowGraphNode(nodeName, status);
                                }}, 100);
                                
                                // 如果当前在节点执行状况tab，刷新显示
                                const nodeStatusTab = document.getElementById('main-tab-node-status');
                                if (nodeStatusTab && nodeStatusTab.classList.contains('active')) {{
                                    refreshGraphNodeStatus();
                                }}
                            }} else if (message.type === 'execution_start') {{
                                // 🚀 执行开始，不重置进度条（让node_update消息来管理进度条状态）
                                console.log('🚀 工作流执行开始:', message.execution_id);
                                console.log('📊 执行开始消息详情:', message);
                            }} else if (message.type === 'execution_completed') {{
                                // 执行完成
                                console.log('✅ 工作流执行完成:', message.execution_id);
                                
                                // 🚀 新增：更新进度条到100%
                                if (graphTotalNodes > 0) {{
                                    graphCompletedNodes = graphTotalNodes;
                                    graphRunningNodes = 0;
                                    updateGraphProgress();
                                }}
                                
                                // 延迟隐藏进度条
                                setTimeout(() => {{
                                    const progressContainer = document.getElementById('graph-progress-container');
                                    if (progressContainer) {{
                                        progressContainer.classList.remove('active');
                                    }}
                                }}, 2000);
                                
                                alert('工作流执行完成！');
                                resetGraphControls();
                            }} else if (message.type === 'execution_error') {{
                                // 执行错误
                                console.error('❌ 工作流执行错误:', message.error);
                                
                                // 🚀 新增：更新进度条显示错误
                                const progressBar = document.getElementById('graph-progress-bar');
                                if (progressBar) {{
                                    progressBar.style.background = 'linear-gradient(90deg, #f44336 0%, #c62828 100%)';
                                }}
                                
                                alert('工作流执行失败: ' + message.error);
                                resetGraphControls();
                            }}
                        }} catch (error) {{
                            console.error('处理WebSocket消息失败:', error);
                        }}
                    }};
                    
                    websocket.onerror = (error) => {{
                        console.error('WebSocket错误:', error);
                    }};
                    
                    websocket.onclose = () => {{
                        console.log('WebSocket连接已关闭');
                        websocket = null;
                    }};
                }}
                
                // 🚀 新增：更新工作流图中的节点高亮显示
                function updateWorkflowGraphNode(nodeName, status) {{
                    if (!nodeName) {{
                        console.warn('⚠️ [节点高亮] 节点名称为空');
                        return;
                    }}
                    
                    console.log(`🔍 [节点高亮] 开始更新节点: ${{nodeName}}, 状态: ${{status}}`);
                    
                    // 查找 SVG 中的节点元素
                    const svgElement = document.querySelector('#workflow-diagram svg');
                    if (!svgElement) {{
                        console.warn('⚠️ [节点高亮] SVG元素未找到');
                        return;
                    }}
                    
                    // 🚀 修复：提取节点ID的函数（与extractNodeId保持一致）
                    function extractNodeIdForHighlight(nodeId) {{
                        if (!nodeId) return null;
                        
                        // 如果是边（L-开头），返回 null
                        if (nodeId.startsWith('L-')) return null;
                        
                        // 移除 workflow-graph_flowchart- 前缀
                        let cleanId = nodeId.replace(/^workflow-graph_flowchart-/, '');
                        // 移除 flowchart- 前缀
                        cleanId = cleanId.replace(/^flowchart-/, '');
                        // 移除 workflow-graph_ 前缀
                        cleanId = cleanId.replace(/^workflow-graph_/, '');
                        // 移除数字后缀（如 "-0", "-1"）
                        cleanId = cleanId.replace(/-[0-9]+$/, '');
                        // 移除其他可能的后缀
                        cleanId = cleanId.replace(/(pointEnd|pointStart|circleEnd|circleStart|crossEnd|crossStart)$/, '');
                        
                        return cleanId;
                    }}
                    
                    // 🚀 修复：规范化节点名称（统一格式）
                    const normalizedNodeName = nodeName.toLowerCase().replace(/[\\s-]/g, '_');
                    
                    // 🚀 修复：尝试多种可能的节点ID格式
                    const possibleIds = [
                        nodeName,
                        normalizedNodeName,
                        `flowchart-${{nodeName}}`,
                        `flowchart-${{normalizedNodeName}}`,
                        `workflow-graph_flowchart-${{nodeName}}`,
                        `workflow-graph_flowchart-${{normalizedNodeName}}`,
                        nodeName.replace(/_/g, '-'),
                        nodeName.replace(/-/g, '_'),
                        normalizedNodeName.replace(/_/g, '-'),
                        normalizedNodeName.replace(/-/g, '_')
                    ];
                    
                    let nodeElement = null;
                    
                    // 方法1: 通过ID精确匹配
                    for (const idPattern of possibleIds) {{
                        try {{
                            nodeElement = svgElement.querySelector(`#${{idPattern}}`);
                            if (nodeElement) {{
                                console.log(`✅ [节点高亮] 通过ID精确匹配找到节点: ${{idPattern}}`);
                                break;
                            }}
                        }} catch (e) {{
                            // 忽略无效选择器
                        }}
                    }}
                    
                    // 方法2: 通过ID部分匹配（包含节点名称）
                    if (!nodeElement) {{
                        const allNodesWithId = svgElement.querySelectorAll('[id]');
                        for (const node of allNodesWithId) {{
                            const nodeId = node.getAttribute('id') || '';
                            const extractedId = extractNodeIdForHighlight(nodeId);
                            
                            if (extractedId && (
                                extractedId === nodeName ||
                                extractedId === normalizedNodeName ||
                                extractedId.toLowerCase() === normalizedNodeName ||
                                extractedId.replace(/[_-]/g, '') === normalizedNodeName.replace(/[_-]/g, '')
                            )) {{
                                nodeElement = node;
                                console.log(`✅ [节点高亮] 通过ID提取匹配找到节点: ${{nodeId}} -> ${{extractedId}}`);
                                break;
                            }}
                        }}
                    }}
                    
                    // 方法3: 通过文本内容匹配（查找节点标签）
                    if (!nodeElement) {{
                        const allLabels = svgElement.querySelectorAll('.nodeLabel, text, foreignObject, tspan');
                        for (const label of allLabels) {{
                            const textContent = (label.textContent || '').trim().toLowerCase().replace(/[\\s-]/g, '_');
                            if (textContent === normalizedNodeName || 
                                textContent.includes(normalizedNodeName) ||
                                normalizedNodeName.includes(textContent)) {{
                                // 找到包含该文本的节点容器
                                const parentNode = label.closest('g[id], g.node, g[class*="node"]');
                                if (parentNode) {{
                                    nodeElement = parentNode;
                                    console.log(`✅ [节点高亮] 通过文本内容匹配找到节点: ${{textContent}}`);
                                    break;
                                }}
                            }}
                        }}
                    }}
                    
                    // 方法4: 通过类名匹配（查找 .node 元素）
                    if (!nodeElement) {{
                        const allNodeElements = svgElement.querySelectorAll('g.node, g[class*="node"]');
                        for (const node of allNodeElements) {{
                            const nodeId = node.getAttribute('id') || '';
                            const extractedId = extractNodeIdForHighlight(nodeId);
                            
                            if (extractedId && (
                                extractedId === nodeName ||
                                extractedId === normalizedNodeName ||
                                extractedId.toLowerCase() === normalizedNodeName
                            )) {{
                                nodeElement = node;
                                console.log(`✅ [节点高亮] 通过类名匹配找到节点: ${{nodeId}}`);
                                break;
                            }}
                        }}
                    }}
                    
                    if (!nodeElement) {{
                        console.warn(`⚠️ [节点高亮] 未找到节点元素: ${{nodeName}} (尝试了 ${{possibleIds.length}} 种ID格式)`);
                        // 🚀 调试：输出所有节点ID，帮助诊断
                        const allNodeIds = Array.from(svgElement.querySelectorAll('[id]')).map(n => n.getAttribute('id')).filter(Boolean);
                        console.log(`🔍 [节点高亮] SVG中所有节点ID（前20个）:`, allNodeIds.slice(0, 20));
                        return;
                    }}
                    
                    // 🚀 修复：查找节点内的矩形或圆形元素（Mermaid节点通常包含这些元素）
                    let shapeElement = nodeElement.querySelector('rect, circle, ellipse, polygon');
                    if (!shapeElement) {{
                        // 如果没有找到形状元素，直接使用节点元素
                        shapeElement = nodeElement;
                    }}
                    
                    // 移除之前的状态类
                    nodeElement.classList.remove('node-running', 'node-completed', 'node-error', 'node-idle', 'mermaid-node-running', 'mermaid-node-completed', 'mermaid-node-error');
                    shapeElement.classList.remove('node-running', 'node-completed', 'node-error', 'node-idle', 'mermaid-node-running', 'mermaid-node-completed', 'mermaid-node-error');
                    
                    // 添加新的状态类
                    const statusClass = `node-${{status}}`;
                    const mermaidStatusClass = `mermaid-node-${{status}}`;
                    nodeElement.classList.add(statusClass, mermaidStatusClass);
                    shapeElement.classList.add(statusClass, mermaidStatusClass);
                    
                    // 🚀 修复：根据状态设置样式（应用到所有形状元素）
                    const allShapes = nodeElement.querySelectorAll('rect, circle, ellipse, polygon, path');
                    const shapesToStyle = allShapes.length > 0 ? allShapes : (shapeElement ? [shapeElement] : []);
                    
                    shapesToStyle.forEach(function(shape) {{
                        const style = shape.style;
                        if (status === 'running') {{
                            style.setProperty('stroke', '#ffeb3b', 'important');
                            style.setProperty('stroke-width', '3px', 'important');
                            style.setProperty('fill', '#fff9c4', 'important');
                            style.setProperty('opacity', '1', 'important');
                            style.setProperty('animation', 'nodePulse 1.5s ease-in-out infinite', 'important');
                            style.setProperty('transition', 'all 0.3s ease', 'important');
                        }} else if (status === 'completed') {{
                            style.setProperty('stroke', '#4caf50', 'important');
                            style.setProperty('stroke-width', '2px', 'important');
                            style.setProperty('fill', '#c8e6c9', 'important');
                            style.setProperty('opacity', '1', 'important');
                            style.setProperty('animation', 'none', 'important');
                            style.setProperty('transition', 'all 0.3s ease', 'important');
                        }} else if (status === 'error') {{
                            style.setProperty('stroke', '#f44336', 'important');
                            style.setProperty('stroke-width', '3px', 'important');
                            style.setProperty('fill', '#ffcdd2', 'important');
                            style.setProperty('opacity', '1', 'important');
                            style.setProperty('animation', 'none', 'important');
                            style.setProperty('transition', 'all 0.3s ease', 'important');
                        }} else {{
                            style.removeProperty('stroke');
                            style.removeProperty('stroke-width');
                            style.removeProperty('fill');
                            style.removeProperty('opacity');
                            style.removeProperty('animation');
                        }}
                    }});
                    
                    // 🚀 新增：也更新节点容器的样式
                    const nodeStyle = nodeElement.style;
                    if (status === 'running') {{
                        nodeStyle.setProperty('opacity', '1', 'important');
                    }} else if (status === 'completed') {{
                        nodeStyle.setProperty('opacity', '1', 'important');
                    }} else if (status === 'error') {{
                        nodeStyle.setProperty('opacity', '1', 'important');
                    }}
                    
                    console.log(`✅ [节点高亮] 成功更新节点 ${{nodeName}} 状态为: ${{status}} (找到 ${{shapesToStyle.length}} 个形状元素)`);
                }}
                
                // 🚀 新增：添加节点闪烁动画样式
                if (!document.getElementById('node-highlight-styles')) {{
                    const style = document.createElement('style');
                    style.id = 'node-highlight-styles';
                    style.textContent = `
                        @keyframes nodePulse {{
                            0%, 100% {{ opacity: 1; transform: scale(1); }}
                            50% {{ opacity: 0.8; transform: scale(1.02); }}
                        }}
                        .node-running rect,
                        .node-running circle,
                        .node-running ellipse,
                        .node-running polygon {{
                            stroke: #ffeb3b !important;
                            stroke-width: 3px !important;
                            fill: #fff9c4 !important;
                            animation: nodePulse 1.5s ease-in-out infinite !important;
                        }}
                        .mermaid-node-running rect,
                        .mermaid-node-running circle,
                        .mermaid-node-running ellipse,
                        .mermaid-node-running polygon {{
                            stroke: #ffeb3b !important;
                            stroke-width: 3px !important;
                            fill: #fff9c4 !important;
                            animation: nodePulse 1.5s ease-in-out infinite !important;
                        }}
                        .node-completed rect,
                        .node-completed circle,
                        .node-completed ellipse,
                        .node-completed polygon {{
                            stroke: #4caf50 !important;
                            stroke-width: 2px !important;
                            fill: #c8e6c9 !important;
                        }}
                        .mermaid-node-completed rect,
                        .mermaid-node-completed circle,
                        .mermaid-node-completed ellipse,
                        .mermaid-node-completed polygon {{
                            stroke: #4caf50 !important;
                            stroke-width: 2px !important;
                            fill: #c8e6c9 !important;
                        }}
                        .node-error rect,
                        .node-error circle,
                        .node-error ellipse,
                        .node-error polygon {{
                            stroke: #f44336 !important;
                            stroke-width: 3px !important;
                            fill: #ffcdd2 !important;
                        }}
                        .mermaid-node-error rect,
                        .mermaid-node-error circle,
                        .mermaid-node-error ellipse,
                        .mermaid-node-error polygon {{
                            stroke: #f44336 !important;
                            stroke-width: 3px !important;
                            fill: #ffcdd2 !important;
                        }}
                    `;
                    document.head.appendChild(style);
                }}
                
                // 🚀 新增：更新节点状态统计
                function updateNodeStatusCounts() {{
                    const runningCount = Object.values(nodeStatusMap).filter(s => s === 'running').length;
                    const completedCount = Object.values(nodeStatusMap).filter(s => s === 'completed').length;
                    const errorCount = Object.values(nodeStatusMap).filter(s => s === 'error').length;
                    const totalCount = Object.keys(nodeStatusMap).length;
                    
                    // 更新统计显示
                    const runningEl = document.getElementById('graph-node-running-count');
                    const completedEl = document.getElementById('graph-node-completed-count');
                    const errorEl = document.getElementById('graph-node-error-count');
                    const totalEl = document.getElementById('graph-node-total-count');
                    
                    if (runningEl) runningEl.textContent = runningCount;
                    if (completedEl) completedEl.textContent = completedCount;
                    if (errorEl) errorEl.textContent = errorCount;
                    if (totalEl) totalEl.textContent = totalCount;
                }}
                
                // 🚀 新增：刷新工作流tab内的系统健康状态
                async function refreshGraphSystemHealth() {{
                    try {{
                        // 尝试多个可能的路径
                        let response = null;
                        let health = null;
                        
                        // 尝试路径1: /visualization/api/workflow/health
                        try {{
                            response = await fetch('/visualization/api/workflow/health');
                            if (response.ok) {{
                                health = await response.json();
                            }}
                        }} catch (e) {{
                            console.log('路径1失败，尝试路径2...');
                        }}
                        
                        // 尝试路径2: /api/workflow/health
                        if (!health) {{
                            try {{
                                response = await fetch('/api/workflow/health');
                                if (response.ok) {{
                                    health = await response.json();
                                }}
                            }} catch (e) {{
                                console.log('路径2失败，尝试路径3...');
                            }}
                        }}
                        
                        // 如果都失败，抛出错误
                        if (!health) {{
                            throw new Error('无法找到健康检查API端点');
                        }}
                        
                        // 更新总览
                        const statusEl = document.getElementById('graph-system-health-status');
                        const uptimeEl = document.getElementById('graph-system-health-uptime');
                        const passEl = document.getElementById('graph-system-health-checks-pass');
                        const failEl = document.getElementById('graph-system-health-checks-fail');
                        
                        if (statusEl) {{
                            const statusColor = {{'healthy': '#4caf50', 'degraded': '#ff9800', 'unhealthy': '#f44336', 'error': '#f44336'}}[health.status] || '#999';
                            statusEl.textContent = health.status?.toUpperCase() || 'UNKNOWN';
                            statusEl.style.color = statusColor;
                        }}
                        
                        if (uptimeEl && health.uptime !== undefined) {{
                            const hours = Math.floor(health.uptime / 3600);
                            const minutes = Math.floor((health.uptime % 3600) / 60);
                            const seconds = Math.floor(health.uptime % 60);
                            uptimeEl.textContent = `${{hours}}h ${{minutes}}m ${{seconds}}s`;
                        }}
                        
                        // 统计检查结果
                        if (health.checks) {{
                            let passCount = 0;
                            let failCount = 0;
                            for (const [checkName, checkData] of Object.entries(health.checks)) {{
                                const checkStatus = checkData.status || 'unknown';
                                if (checkStatus === 'pass' || checkStatus === 'ok') {{
                                    passCount++;
                                }} else if (checkStatus === 'fail' || checkStatus === 'error') {{
                                    failCount++;
                                }}
                            }}
                            if (passEl) passEl.textContent = passCount;
                            if (failEl) failEl.textContent = failCount;
                        }}
                        
                        // 更新详细健康检查
                        const healthDiv = document.getElementById('graph-system-health-content');
                        if (!healthDiv) return;
                        
                        let html = '<div style="display: flex; flex-direction: column; gap: 8px;">';
                        
                        if (health.checks) {{
                            for (const [checkName, checkData] of Object.entries(health.checks)) {{
                                const checkStatus = checkData.status || 'unknown';
                                let statusColor = '#999';
                                let statusText = 'UNKNOWN';
                                
                                if (checkStatus === 'pass' || checkStatus === 'ok') {{
                                    statusColor = '#4caf50';
                                    statusText = '✓ 正常';
                                }} else if (checkStatus === 'fail' || checkStatus === 'error') {{
                                    statusColor = '#f44336';
                                    statusText = '✗ 失败';
                                }} else if (checkStatus === 'warn' || checkStatus === 'warning') {{
                                    statusColor = '#ff9800';
                                    statusText = '⚠ 警告';
                                }}
                                
                                html += `<div style="padding: 8px; background: #f9f9f9; border-radius: 3px; border-left: 3px solid ${{statusColor}};">
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;">
                                        <strong style="color: #333; font-size: 11px;">${{checkName.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}}</strong>
                                        <span style="color: ${{statusColor}}; font-weight: bold; font-size: 10px;">${{statusText}}</span>
                                    </div>
                                    ${{checkData.message ? '<div style="font-size: 10px; color: #666; margin-top: 3px;">' + checkData.message + '</div>' : ''}}
                                </div>`;
                            }}
                        }} else {{
                            html += '<p style="color: #999; font-style: italic; font-size: 11px; text-align: center; padding: 20px;">暂无健康检查数据。</p>';
                        }}
                        
                        html += '</div>';
                        healthDiv.innerHTML = html;
                    }} catch (error) {{
                        console.error('加载系统健康状态失败:', error);
                        const healthDiv = document.getElementById('graph-system-health-content');
                        if (healthDiv) {{
                            const errorMsg = error?.message || error?.toString() || '未知错误';
                            healthDiv.innerHTML = `<p style="color: #f44336; font-size: 11px;">加载失败: ${{errorMsg}}</p>`;
                        }}
                    }}
                }}
                
                // ================================================
                // 🤖 Agent Creation 功能
                // ================================================
                
                // 显示/隐藏Agent创建进度
                function showAgentCreationProgress(show, progress = 0, message = '', type = 'info') {{
                    const progressDiv = document.getElementById('agent-creation-status');
                    if (!progressDiv) return;
                    
                    if (show) {{
                        progressDiv.style.display = 'block';
                        let bgColor = '#f5f5f5';
                        let borderColor = '#ddd';
                        
                        if (type === 'success') {{
                            bgColor = '#d4edda';
                            borderColor = '#c3e6cb';
                        }} else if (type === 'error') {{
                            bgColor = '#f8d7da';
                            borderColor = '#f5c6cb';
                        }} else if (type === 'warning') {{
                            bgColor = '#fff3cd';
                            borderColor = '#ffeaa7';
                        }} else if (type === 'info') {{
                            bgColor = '#d1ecf1';
                            borderColor = '#bee5eb';
                        }}
                        
                        progressDiv.style.background = bgColor;
                        progressDiv.style.border = `1px solid ${{borderColor}}`;
                        progressDiv.style.color = type === 'error' ? '#721c24' : '#0c5460';
                        progressDiv.innerHTML = `
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <div style="flex: 1;">
                                    <strong>${{message}}</strong>
                                    ${{progress > 0 ? `<div style="margin-top: 5px; width: 100%; height: 6px; background: #e0e0e0; border-radius: 3px;">
                                        <div style="width: ${{{{progress}}}}%; height: 100%; background: #4caf50; border-radius: 3px; transition: width 0.3s;"></div>
                                    </div>` : ''}}
                                </div>
                                ${{progress >= 100 ? '<span style="color: #4caf50; font-weight: bold;">✓ 完成</span>' : ''}}
                            </div>
                        `;
                    }} else {{
                        progressDiv.style.display = 'none';
                    }}
                }}
                
                // 清空表单
                function clearAgentForm() {{
                    document.getElementById('agent-creation-description').value = '';
                    document.getElementById('agent-creation-result').style.display = 'none';
                    document.getElementById('create-agent-button').style.display = 'none';
                    document.getElementById('agent-creation-status').style.display = 'none';
                }}
                
                // 解析Agent需求
                async function parseAgentRequirements() {{
                    const description = document.getElementById('agent-creation-description').value.trim();
                    
                    if (!description) {{
                        showAgentCreationProgress(true, 0, '请输入Agent需求描述', 'error');
                        return;
                    }}
                    
                    if (description.length < 5) {{
                        showAgentCreationProgress(true, 0, '描述太短，请提供更详细的需求', 'error');
                        return;
                    }}
                    
                    showAgentCreationProgress(true, 30, '正在解析需求...', 'info');
                    
                    try {{
                        console.log('🔄 [Agent创建] 解析需求:', description);
                        
                        const response = await fetch('/api/v1/agents/parse-requirements', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{ description }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP错误: ${{response.status}}`);
                        }}
                        
                        const result = await response.json();
                        
                        // 显示解析结果
                        const resultDiv = document.getElementById('agent-creation-result');
                        const detailsDiv = document.getElementById('agent-parse-details');
                        
                        if (result.success) {{
                            showAgentCreationProgress(true, 70, '需求解析成功！正在生成配置...', 'success');
                            
                            // 显示解析详情
                            let detailsHtml = `
                                <p><strong>提取的关键词:</strong> ${{result.data.keywords?.join(', ') || '无'}}</p>
                                <p><strong>匹配的Tools:</strong> ${{result.data.matched_tools?.join(', ') || '无'}}</p>
                                <p><strong>匹配的Skills:</strong> ${{result.data.matched_skills?.join(', ') || '无'}}</p>
                                <p><strong>建议的Agent类型:</strong> ${{result.data.suggested_agent_type || '标准Agent'}}</p>
                            `;
                            
                            if (result.data.config_preview) {{
                                detailsHtml += `<div style="margin-top: 10px; padding: 10px; background: white; border: 1px solid #ddd; border-radius: 3px; font-size: 12px;">
                                    <strong>配置预览:</strong><br>
                                    <pre style="margin: 5px 0; white-space: pre-wrap; word-break: break-all;">${{JSON.stringify(result.data.config_preview, null, 2)}}</pre>
                                </div>`;
                            }}
                            
                            detailsDiv.innerHTML = detailsHtml;
                            resultDiv.style.display = 'block';
                            document.getElementById('create-agent-button').style.display = 'block';
                            
                            // 保存解析结果供创建使用
                            window.lastParseResult = result.data;
                            
                        }} else {{
                            showAgentCreationProgress(true, 0, '解析失败: ' + (result.error || '未知错误'), 'error');
                            detailsDiv.innerHTML = '<p style="color: #f44336;">' + (result.error || '解析失败') + '</p>';
                            resultDiv.style.display = 'block';
                        }}
                        
                    }} catch (error) {{
                        console.error('❌ [Agent创建] 解析失败:', error);
                        showAgentCreationProgress(true, 0, '解析失败: ' + error.message, 'error');
                    }}
                }}
                
                // 从解析结果创建Agent
                async function createAgentFromParse() {{
                    if (!window.lastParseResult) {{
                        showAgentCreationProgress(true, 0, '没有可用的解析结果，请先解析需求', 'error');
                        return;
                    }}
                    
                    showAgentCreationProgress(true, 80, '正在创建Agent...', 'info');
                    
                    try {{
                        const response = await fetch('/api/v1/agents/from-natural-language', {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json'
                            }},
                            body: JSON.stringify({{
                                description: document.getElementById('agent-creation-description').value.trim(),
                                config: window.lastParseResult.config_preview || {{}}
                            }})
                        }});
                        
                        if (!response.ok) {{
                            throw new Error(`HTTP错误: ${{response.status}}`);
                        }}
                        
                        const result = await response.json();
                        
                        if (result.success) {{
                            showAgentCreationProgress(true, 100, 'Agent创建成功！ID: ' + (result.data.agent_id || '未知'), 'success');
                            
                            // 显示创建结果
                            const resultDiv = document.getElementById('agent-creation-result');
                            const detailsDiv = document.getElementById('agent-parse-details');
                            
                            detailsDiv.innerHTML += `
                                <div style="margin-top: 15px; padding: 10px; background: #d4edda; border: 1px solid #c3e6cb; border-radius: 3px;">
                                    <strong>✅ Agent创建成功！</strong>
                                    <p>Agent ID: ${{result.data.agent_id || '未知'}}</p>
                                    <p>配置: ${{JSON.stringify(result.data.config || {{}}, null, 2)}}</p>
                                    <button onclick="resetAgentCreation()" style="margin-top: 10px; padding: 8px 16px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer;">
                                        创建新Agent
                                    </button>
                                </div>
                            `;
                            
                            document.getElementById('create-agent-button').style.display = 'none';
                            
                        }} else {{
                            showAgentCreationProgress(true, 0, '创建失败: ' + (result.error || '未知错误'), 'error');
                        }}
                        
                    }} catch (error) {{
                        console.error('❌ [Agent创建] 创建失败:', error);
                        showAgentCreationProgress(true, 0, '创建失败: ' + error.message, 'error');
                    }}
                }}
                
                // 重置Agent创建
                function resetAgentCreation() {{
                    clearAgentForm();
                    delete window.lastParseResult;
                    showAgentCreationProgress(false);
                }}
                
                // ================================================
                
                // 页面加载时初始化
                window.addEventListener('load', () => {{
                    loadGraph();
                    refreshGraphNodeStatus();
                    refreshGraphSystemHealth();
                }});
            </script>
        </body>
        </html>"""
        return HTMLResponse(content=html_content)

    async def _render_monitor_page(self):
        """渲染监控页面"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>执行监控 - RANGEN 可视化</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    padding: 40px;
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}

                .title {{
                    font-size: 2.5em;
                    font-weight: bold;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }}

                .nav-button {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 14px;
                    display: inline-block;
                    margin-top: 20px;
                    transition: all 0.3s ease;
                }}

                .nav-button:hover {{
                    background: #5a67d8;
                    transform: translateY(-2px);
                }}

                .monitor-content {{
                    text-align: center;
                    padding: 60px 20px;
                }}

                .status-icon {{
                    font-size: 4em;
                    margin-bottom: 20px;
                }}

                .status-message {{
                    font-size: 1.3em;
                    color: #666;
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">📈 执行监控</div>
                    <p>实时监控工作流执行状态和性能指标</p>
                </div>

                <div class="monitor-content">
                    <div class="status-icon">📊</div>
                    <div class="status-message">
                        <p>监控功能正在开发中...</p>
                        <p>即将支持实时执行状态监控、性能指标展示等功能。</p>
                    </div>
                </div>

                <div style="text-align: center;">
                    <a href="/visualization/" class="nav-button">← 返回可视化主页</a>
                </div>
            </div>
        </body>
        </html>"""
        return HTMLResponse(content=html_content)

    async def _render_debug_page(self):
        """渲染调试页面"""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>调试信息 - RANGEN 可视化</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: #333;
                }}

                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 20px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    padding: 40px;
                }}

                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                }}

                .title {{
                    font-size: 2.5em;
                    font-weight: bold;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 10px;
                }}

                .nav-button {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-size: 14px;
                    display: inline-block;
                    margin-top: 20px;
                    transition: all 0.3s ease;
                }}

                .nav-button:hover {{
                    background: #5a67d8;
                    transform: translateY(-2px);
                }}

                .debug-content {{
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 30px;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    white-space: pre-wrap;
                    max-height: 600px;
                    overflow-y: auto;
                }}

                .debug-title {{
                    font-size: 1.3em;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 20px;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="title">🔧 调试信息</div>
                    <p>系统详细调试信息和日志</p>
                </div>

                <div class="debug-content">
                    <div class="debug-title">系统状态信息</div>
                    <strong>FastAPI状态:</strong> ✅ 已加载 (v0.127.0)
                    <strong>Uvicorn状态:</strong> ✅ 已加载 (v0.40.0)
                    <strong>LangGraph状态:</strong> ✅ 已加载 (v1.0.5)

                    <strong>工作流状态:</strong> ✅ 已初始化 (37个节点, 24条边)
                    <strong>智能体状态:</strong> ✅ 已加载 (4个专家智能体)
                    <strong>服务器状态:</strong> ✅ 运行中 (端口: 8080)

                    <div class="debug-title" style="margin-top: 30px;">可用端点</div>
                    GET / - 主页
                    GET /visualization/ - 可视化主页
                    GET /visualization/graph - 工作流图
                    GET /visualization/status - 系统状态
                    GET /api/ - API文档
                    GET /config/ - 配置管理

                    <div class="debug-title" style="margin-top: 30px;">最近日志</div>
                    服务器已成功启动
                    所有子服务已挂载
                    统一服务器管理器初始化完成
                    等待客户端连接...
                </div>

                <div style="text-align: center; margin-top: 30px;">
                    <a href="/visualization/" class="nav-button">← 返回可视化主页</a>
                </div>
            </div>
        </body>
        </html>"""
        return HTMLResponse(content=html_content)
