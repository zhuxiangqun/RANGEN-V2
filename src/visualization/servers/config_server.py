"""
配置管理服务模块
提供配置管理系统的Web界面和API
"""
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.visualization.servers.base_server import BaseServer

# 导入相关依赖
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    FastAPI = None
    HTTPException = None
    JSONResponse = None
    HTMLResponse = None
    StaticFiles = None

logger = logging.getLogger(__name__)


class ConfigServer(BaseServer):
    """
    配置管理服务

    提供配置管理系统的Web界面和API：
    - 配置管理Web界面
    - 配置数据API
    - 路由类型管理
    - 配置状态监控
    """

    def __init__(self,
                 config: Optional[Dict[str, Any]] = None,
                 config_manager=None):
        """
        初始化配置服务器

        Args:
            config: 服务器配置
            config_manager: 配置管理器实例
        """
        super().__init__("config_server", config)

        self.config_manager = config_manager
        self.app: Optional[FastAPI] = None

        # 如果FastAPI不可用，记录警告
        if not FASTAPI_AVAILABLE:
            self.logger.warning("FastAPI不可用，配置管理服务将被禁用")

    async def start(self) -> None:
        """启动配置服务器"""
        if not FASTAPI_AVAILABLE:
            self.logger.error("FastAPI不可用，无法启动配置服务器")
            return

        try:
            # 创建FastAPI应用
            self.app = FastAPI(
                title="RANGEN Config Server",
                description="RANGEN 系统的配置管理服务",
                version="1.0.0"
            )

            # 注册路由
            await self._register_routes()

            self.logger.info("✅ 配置服务器路由注册完成")
            await super().start()

        except Exception as e:
            await self._handle_startup_error(e)

    async def stop(self) -> None:
        """停止配置服务器"""
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

        # 检查配置管理器
        if self.config_manager:
            checks["config_manager"] = {
                "status": "pass",
                "message": "配置管理器可用"
            }

            # 检查配置数据
            try:
                config_data = self._get_config_data()
                checks["config_data"] = {
                    "status": "pass",
                    "message": "配置数据可用",
                    "details": {
                        "config_count": len(config_data) if isinstance(config_data, dict) else 0
                    }
                }
            except Exception as e:
                checks["config_data"] = {
                    "status": "fail",
                    "message": f"配置数据检查失败: {e}"
                }
        else:
            checks["config_manager"] = {
                "status": "fail",
                "message": "配置管理器不可用"
            }
            checks["config_data"] = {
                "status": "fail",
                "message": "配置管理器不可用"
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
        """获取配置路由列表"""
        if not self.app:
            return []

        routes = []
        for route in self.app.routes:
            if hasattr(route, 'path'):
                routes.append(f"CONFIG: {route.path}")
        return routes

    async def _register_routes(self) -> None:
        """注册配置管理路由"""
        if not self.app:
            return

        @self.app.get("/")
        async def config_home():
            """配置管理主页"""
            try:
                html_content = self._generate_config_dashboard_html()
                return HTMLResponse(content=html_content)
            except Exception as e:
                logger.error(f"生成配置仪表板失败: {e}", exc_info=True)
                return HTMLResponse(
                    content="<h1>配置管理器不可用</h1><p>无法生成配置仪表板</p>",
                    status_code=503
                )

        @self.app.get("/config", response_class=HTMLResponse)
        async def get_config_dashboard():
            """获取配置管理仪表板"""
            try:
                html_content = self._generate_config_dashboard_html()
                return HTMLResponse(content=html_content)
            except Exception as e:
                logger.error(f"生成配置仪表板失败: {e}", exc_info=True)
                return HTMLResponse(
                    content="<h1>配置管理器不可用</h1><p>无法生成配置仪表板</p>",
                    status_code=503
                )

        @self.app.get("/api/config", response_class=JSONResponse)
        async def get_config_data():
            """获取配置数据"""
            try:
                if not self.config_manager:
                    raise HTTPException(status_code=503, detail="配置管理器不可用")

                config_data = self._get_config_data()
                return {
                    "status": "success",
                    "data": config_data,
                    "timestamp": asyncio.get_event_loop().time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取配置数据失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

        @self.app.get("/api/route-types", response_class=JSONResponse)
        async def get_route_types():
            """获取路由类型配置"""
            try:
                if not self.config_manager:
                    raise HTTPException(status_code=503, detail="配置管理器不可用")

                route_types = self._get_route_types()
                return {
                    "status": "success",
                    "data": route_types,
                    "timestamp": asyncio.get_event_loop().time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"获取路由类型失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"获取路由类型失败: {str(e)}")

        @self.app.post("/api/route-types")
        async def update_route_types(request: Request):
            """更新路由类型配置"""
            try:
                if not self.config_manager:
                    raise HTTPException(status_code=503, detail="配置管理器不可用")

                data = await request.json()
                result = self._update_route_types(data)

                return {
                    "status": "success",
                    "message": "路由类型更新成功",
                    "data": result,
                    "timestamp": asyncio.get_event_loop().time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"更新路由类型失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"更新路由类型失败: {str(e)}")

        @self.app.put("/api/config/{section_name}")
        async def update_config_section(section_name: str, request: Request):
            """更新配置节"""
            try:
                if not self.config_manager:
                    raise HTTPException(status_code=503, detail="配置管理器不可用")

                data = await request.json()

                # 更新配置
                for key, value in data.items():
                    success = self.config_manager.set_config(section_name, key, value)
                    if not success:
                        raise HTTPException(status_code=400, detail=f"更新配置项 {key} 失败")

                return {
                    "status": "success",
                    "message": f"配置节 {section_name} 更新成功",
                    "data": data,
                    "timestamp": asyncio.get_event_loop().time()
                }
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"更新配置节失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"更新配置节失败: {str(e)}")

        @self.app.post("/api/config/reload")
        async def reload_config():
            """重新加载配置"""
            try:
                if not self.config_manager:
                    raise HTTPException(status_code=503, detail="配置管理器不可用")

                # 重新加载配置
                self.config_manager._load_configs()

                return {
                    "status": "success",
                    "message": "配置重新加载成功",
                    "timestamp": asyncio.get_event_loop().time()
                }
            except Exception as e:
                logger.error(f"重新加载配置失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"重新加载配置失败: {str(e)}")

        @self.app.get("/api/config/status")
        async def get_config_status():
            """获取配置状态"""
            try:
                status_info = self._get_config_status()
                return {
                    "status": "success",
                    "data": status_info,
                    "timestamp": asyncio.get_event_loop().time()
                }
            except Exception as e:
                logger.error(f"获取配置状态失败: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"获取配置状态失败: {str(e)}")

    def _get_config_data(self) -> Dict[str, Any]:
        """获取配置数据"""
        if not self.config_manager:
            return {}

        try:
            # 使用UnifiedConfigManager获取实际配置数据
            config_data = {}

            # 获取所有配置节
            sections = self.config_manager.list_sections()
            for section_name in sections:
                section_data = self.config_manager.get_section(section_name)
                if section_data:
                    config_data[section_name] = section_data.config

            # 如果没有配置数据，返回一些基本的默认配置
            if not config_data:
                config_data = {
                    "system": {
                        "name": "RANGEN",
                        "version": "1.0.0",
                        "environment": "development"
                    },
                    "services": {
                        "api_server": {"enabled": True, "port": 8080},
                        "visualization_server": {"enabled": True, "port": 8081},
                        "config_server": {"enabled": True, "port": 8082}
                    },
                    "workflow": {
                        "max_concurrent_executions": 5,
                        "timeout_seconds": 300
                    }
                }

            return config_data
        except Exception as e:
            logger.error(f"获取配置数据时出错: {e}")
            return {"error": str(e)}

    def _get_route_types(self) -> Dict[str, Any]:
        """获取路由类型配置"""
        if not self.config_manager:
            return {}

        try:
            # 这里应该从配置管理器获取路由类型
            # 暂时返回模拟数据
            return {
                "simple": {
                    "description": "简单查询",
                    "enabled": True,
                    "priority": 1
                },
                "complex": {
                    "description": "复杂查询",
                    "enabled": True,
                    "priority": 2
                },
                "reasoning": {
                    "description": "推理查询",
                    "enabled": True,
                    "priority": 3
                }
            }
        except Exception as e:
            logger.error(f"获取路由类型时出错: {e}")
            return {"error": str(e)}

    def _update_route_types(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """更新路由类型配置"""
        if not self.config_manager:
            raise HTTPException(status_code=503, detail="配置管理器不可用")

        try:
            # 这里应该更新配置管理器中的路由类型
            # 暂时只是记录日志
            logger.info(f"更新路由类型: {data}")

            # 返回更新结果
            return {
                "updated": True,
                "changes": data
            }
        except Exception as e:
            logger.error(f"更新路由类型时出错: {e}")
            raise

    def _get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        status = {
            "config_manager_available": self.config_manager is not None,
            "config_data_accessible": False,
            "route_types_accessible": False,
            "last_update": None
        }

        if self.config_manager:
            try:
                self._get_config_data()
                status["config_data_accessible"] = True
            except:
                pass

            try:
                self._get_route_types()
                status["route_types_accessible"] = True
            except:
                pass

        status["last_check"] = asyncio.get_event_loop().time()
        return status

    def _generate_config_dashboard_html(self) -> str:
        """生成配置管理仪表板HTML"""
        if not self.config_manager:
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>配置管理 - 不可用</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .error { color: #dc3545; background: #f8d7da; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>配置管理器不可用</h1>
                <div class="error">
                    <p>配置管理系统未初始化或不可用。</p>
                    <p>请检查系统配置和依赖。</p>
                </div>
            </body>
            </html>
            """

        # 生成完整的配置管理界面HTML
        config_data = self._get_config_data()
        route_types = self._get_route_types()

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RANGEN 配置管理</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .container {{
                    max-width: 1200px;
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
                .section {{
                    margin-bottom: 30px;
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    overflow: hidden;
                }}
                .section-header {{
                    background: #f8f9fa;
                    padding: 15px 20px;
                    font-weight: bold;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .section-content {{
                    padding: 20px;
                }}
                .config-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 10px 0;
                    border-bottom: 1px solid #f0f0f0;
                }}
                .config-item:last-child {{
                    border-bottom: none;
                }}
                .config-key {{
                    font-weight: 500;
                    color: #333;
                }}
                .config-value {{
                    color: #666;
                    font-family: monospace;
                }}
                .status {{
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 12px;
                    font-weight: bold;
                }}
                .status.enabled {{
                    background: #d4edda;
                    color: #155724;
                }}
                .status.disabled {{
                    background: #f8d7da;
                    color: #721c24;
                }}
                .json-value {{
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                    max-height: 200px;
                    overflow-y: auto;
                }}
                .config-actions {{
                    display: flex;
                    gap: 8px;
                    align-items: center;
                }}
                .edit-btn, .save-btn, .cancel-btn {{
                    padding: 4px 8px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 12px;
                    transition: all 0.2s ease;
                }}
                .edit-btn {{
                    background: #007bff;
                    color: white;
                }}
                .edit-btn:hover {{
                    background: #0056b3;
                }}
                .save-btn {{
                    background: #28a745;
                    color: white;
                }}
                .save-btn:hover {{
                    background: #218838;
                }}
                .cancel-btn {{
                    background: #6c757d;
                    color: white;
                }}
                .cancel-btn:hover {{
                    background: #545b62;
                }}
                .config-input {{
                    width: 100%;
                    padding: 4px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-size: 14px;
                }}
                .config-textarea {{
                    width: 100%;
                    min-height: 100px;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    resize: vertical;
                }}
                .message {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 12px 20px;
                    border-radius: 6px;
                    color: white;
                    font-weight: bold;
                    z-index: 1000;
                    display: none;
                    animation: slideIn 0.3s ease-out;
                }}
                .message.success {{
                    background: #28a745;
                }}
                .message.error {{
                    background: #dc3545;
                }}
                @keyframes slideIn {{
                    from {{ transform: translateX(100%); opacity: 0; }}
                    to {{ transform: translateX(0); opacity: 1; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <a href="/" class="nav-button">← 返回首页</a>
                    <h1>⚙️ RANGEN 配置管理</h1>
                    <p>系统配置和路由管理界面</p>
                </div>
                <div class="content">
        """

        # 动态生成所有配置节
        if self.config_manager:
            sections = self.config_manager.list_sections()
            for section_name in sections:
                section_data = self.config_manager.get_section(section_name)
                if section_data:
                    section_config = section_data.config
                    section_description = getattr(section_data, 'description', section_name)

                    # 中文标题映射
                    title_mapping = {
                        'reasoning_engine': '推理引擎',
                        'extraction_strategies': '提取策略',
                        'ai_algorithms': 'AI算法',
                        'security': '安全配置',
                        'brain_decision': '大脑决策',
                        'performance': '性能配置',
                        'system': '系统配置',
                        'data_management': '数据管理'
                    }
                    display_title = title_mapping.get(section_name, section_name.replace('_', ' ').title())

                    html += f'''
                    <div class="section">
                        <div class="section-header">{display_title}</div>
                        <div class="section-content">
                    '''

                    # 显示配置项
                    if isinstance(section_config, dict):
                        for key, value in section_config.items():
                            # 格式化值显示
                            if isinstance(value, bool):
                                display_value = "是" if value else "否"
                                status_class = "enabled" if value else "disabled"
                                html += f'''
                            <div class="config-item">
                                <span class="config-key">{key}</span>
                                <div class="config-actions">
                                    <span class="config-value status {status_class}">{display_value}</span>
                                    <button class="edit-btn" onclick="editConfig('{section_name}', '{key}', '{display_value}', 'boolean')">编辑</button>
                                </div>
                            </div>
                                '''
                            elif isinstance(value, (int, float)):
                                html += f'''
                            <div class="config-item">
                                <span class="config-key">{key}</span>
                                <div class="config-actions">
                                    <span class="config-value">{value}</span>
                                    <button class="edit-btn" onclick="editConfig('{section_name}', '{key}', '{value}', 'number')">编辑</button>
                                </div>
                            </div>
                                '''
                            elif isinstance(value, str):
                                html += f'''
                            <div class="config-item">
                                <span class="config-key">{key}</span>
                                <div class="config-actions">
                                    <span class="config-value">{value}</span>
                                    <button class="edit-btn" onclick="editConfig('{section_name}', '{key}', '{value}', 'string')">编辑</button>
                                </div>
                            </div>
                                '''
                            elif isinstance(value, list):
                                display_value = ", ".join(str(item) for item in value[:3])  # 只显示前3个
                                if len(value) > 3:
                                    display_value += f" ... (+{len(value)-3} 更多)"
                                import json
                                json_value = json.dumps(value, ensure_ascii=False)
                                html += f'''
                            <div class="config-item">
                                <span class="config-key">{key}</span>
                                <div class="config-actions">
                                    <span class="config-value">{display_value}</span>
                                    <button class="edit-btn" onclick="editConfig('{section_name}', '{key}', '{json_value}', 'array')">编辑</button>
                                </div>
                            </div>
                                '''
                            elif isinstance(value, dict):
                                # 格式化字典显示
                                import json
                                formatted_json = json.dumps(value, indent=2, ensure_ascii=False)[:200]
                                if len(json.dumps(value, indent=2, ensure_ascii=False)) > 200:
                                    formatted_json += "..."
                                json_value = json.dumps(value, ensure_ascii=False)
                                html += f'''
                            <div class="config-item">
                                <span class="config-key">{key}</span>
                                <div class="config-actions">
                                    <pre class="config-value json-value">{formatted_json}</pre>
                                    <button class="edit-btn" onclick="editConfig('{section_name}', '{key}', '{json_value}', 'object')">编辑</button>
                                </div>
                            </div>
                                '''
                            else:
                                # 处理时间戳
                                if isinstance(value, (int, float)) and key in ['last_updated', 'timestamp', 'created_at', 'updated_at']:
                                    import time
                                    try:
                                        display_value = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value))
                                    except:
                                        display_value = str(value)
                                else:
                                    display_value = str(value)[:100]  # 限制长度
                                    if len(str(value)) > 100:
                                        display_value += "..."
                                html += f'''
                            <div class="config-item">
                                <span class="config-key">{key}</span>
                                <div class="config-actions">
                                    <span class="config-value">{display_value}</span>
                                    <button class="edit-btn" onclick="editConfig('{section_name}', '{key}', '{str(value)}', 'string')">编辑</button>
                                </div>
                            </div>
                                '''
                    else:
                        html += f'''
                            <div class="config-item">
                                <span class="config-key">配置数据</span>
                                <span class="config-value">{str(section_config)[:200]}...</span>
                            </div>
                                '''

                    html += '''
                        </div>
                    </div>
                    '''

        html += '''
                        </div>
                    </div>

                    <div class="section">
                        <div class="section-header">路由类型配置</div>
                        <div class="section-content">
        '''

        # 添加路由类型配置
        for route_type, route_config in route_types.items():
            if isinstance(route_config, dict):
                enabled = route_config.get("enabled", False)
                status_class = "enabled" if enabled else "disabled"
                status_text = "启用" if enabled else "禁用"
                description = route_config.get("description", "")

                html += f'''
                            <div class="config-item">
                                <div>
                                    <span class="config-key">{route_type}</span>
                                    <div style="color: #666; font-size: 14px;">{description}</div>
                                </div>
                                <span class="status {status_class}">{status_text}</span>
                            </div>
                '''

        html += '''
                        </div>
                    </div>
                </div>
                </div>

                <div id="message" class="message"></div>

                <script>
                    let currentEditItem = null;

                    function showMessage(message, type = 'success') {{
                        const msgEl = document.getElementById('message');
                        msgEl.textContent = message;
                        msgEl.className = `message ${{type}}`;
                        msgEl.style.display = 'block';

                        setTimeout(() => {{
                            msgEl.style.display = 'none';
                        }}, 3000);
                    }}

                    function editConfig(sectionName, key, currentValue, valueType) {{
                        if (currentEditItem) {{
                            cancelEdit();
                        }}

                        const configItem = event.target.closest('.config-item');
                        const valueElement = configItem.querySelector('.config-value');
                        const actionsElement = configItem.querySelector('.config-actions');

                        // 保存原始内容
                        const originalHTML = valueElement.outerHTML;

                        // 创建编辑界面
                        let inputHTML = '';
                        switch (valueType) {{
                            case 'boolean':
                                const isTrue = currentValue === 'true';
                                inputHTML = `
                                    <select class="config-input">
                                        <option value="true" ${isTrue ? 'selected' : ''}>是</option>
                                        <option value="false" ${!isTrue ? 'selected' : ''}>否</option>
                                    </select>
                                `;
                                break;
                            case 'number':
                                inputHTML = `<input type="number" class="config-input" value="${currentValue}" />`;
                                break;
                            case 'array':
                            case 'object':
                                inputHTML = `<textarea class="config-textarea">${currentValue}</textarea>`;
                                break;
                            default:
                                inputHTML = `<input type="text" class="config-input" value="${currentValue}" />`;
                        }}

                        // 替换内容为编辑界面
                        valueElement.outerHTML = inputHTML;
                        actionsElement.innerHTML = `
                            <button class="save-btn" onclick="saveConfig('${sectionName}', '${key}', '${valueType}')">保存</button>
                            <button class="cancel-btn" onclick="cancelEdit()">取消</button>
                        `;

                        currentEditItem = {{
                            configItem: configItem,
                            originalHTML: originalHTML,
                            actionsHTML: actionsElement.outerHTML
                        }};
                    }}

                    async function saveConfig(sectionName, key, valueType) {{
                        try {{
                            const configItem = event.target.closest('.config-item');
                            let newValue;

                            switch (valueType) {{
                                case 'boolean':
                                    const select = configItem.querySelector('select');
                                    newValue = select.value === 'true';
                                    break;
                                case 'number':
                                    const input = configItem.querySelector('input[type="number"]');
                                    newValue = parseFloat(input.value);
                                    break;
                                case 'array':
                                case 'object':
                                    const textarea = configItem.querySelector('textarea');
                                    try {{
                                        newValue = JSON.parse(textarea.value);
                                    }} catch (e) {{
                                        showMessage('JSON格式错误', 'error');
                                        return;
                                    }}
                                    break;
                                default:
                                    const textInput = configItem.querySelector('input[type="text"]');
                                    newValue = textInput.value;
                            }}

                            // 发送更新请求
                            const response = await fetch(`/config/api/config/${sectionName}`, {
                                method: 'PUT',
                                headers: {
                                    'Content-Type': 'application/json',
                                },
                                body: JSON.stringify({[key]: newValue})
                            });

                            if (response.ok) {{
                                showMessage('配置更新成功');
                                setTimeout(() => {{
                                    location.reload();
                                }}, 1000);
                            }} else {{
                                const error = await response.json();
                                showMessage('更新失败: ' + (error.detail || '未知错误'), 'error');
                            }}
                        }} catch (error) {{
                            console.error('保存配置失败:', error);
                            showMessage('保存失败，请检查控制台', 'error');
                        }}
                    }}

                    function cancelEdit() {{
                        if (currentEditItem) {{
                            const configItem = currentEditItem.configItem;
                            const valueContainer = configItem.querySelector('.config-actions').previousElementSibling;

                            // 恢复原始内容
                            if (valueContainer) {{
                                valueContainer.outerHTML = currentEditItem.originalHTML;
                            }}

                            // 恢复原始按钮
                            const actionsElement = configItem.querySelector('.config-actions');
                            if (actionsElement) {{
                                actionsElement.outerHTML = currentEditItem.actionsHTML;
                            }}

                            currentEditItem = null;
                        }}
                    }}

                    // 点击其他地方时取消编辑
                    document.addEventListener('click', function(event) {{
                        if (currentEditItem && !event.target.closest('.config-item')) {{
                            cancelEdit();
                        }}
                    }});

                    // ESC键取消编辑
                    document.addEventListener('keydown', function(event) {{
                        if (event.key === 'Escape' && currentEditItem) {{
                            cancelEdit();
                        }}
                    }});
                </script>
            </body>
            </html>
        '''

        return html

    def get_app(self) -> Optional[FastAPI]:
        """获取FastAPI应用实例"""
        return self.app
