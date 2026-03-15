#!/usr/bin/env python3
"""
移动监控支持模块 - 提供移动设备友好的系统监控接口
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 动态处理导入路径
import sys
import os

# 将项目根目录添加到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 现在可以使用绝对导入
from src.core.four_layer_manager import get_four_layer_manager
from src.core.mcp_four_layer_bridge import test_mcp_integration
from src.core.four_layer_adapters import create_default_four_layer_setup
from src.core.v3_compliance_checker import V3ComplianceChecker, check_v3_compliance

logger = logging.getLogger(__name__)


class MobileMonitoringSystem:
    """移动监控系统"""
    
    def __init__(self, api_prefix: str = "/mobile-monitoring"):
        self.app = FastAPI(title="RANGEN移动监控", version="1.0")
        self.router = APIRouter(prefix=api_prefix)
        self.setup_cors()
        self.setup_routes()
        self.app.include_router(self.router)
        
        # 四层架构管理器
        self.layer_manager = get_four_layer_manager()
        
        logger.info("移动监控系统初始化完成")
    
    def setup_cors(self):
        """设置CORS以支持移动设备访问"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 生产环境中应限制
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routes(self):
        """设置API路由"""
        
        @self.router.get("/health", summary="健康检查")
        async def health_check():
            """系统健康检查"""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "mobile_monitoring",
                "version": "1.0"
            }
        
        @self.router.get("/layer-status", summary="四层架构状态")
        async def get_layer_status():
            """获取四层架构状态"""
            try:
                status = self.layer_manager.get_layer_status()
                health = await self.layer_manager.health_check()
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "layer_status": status,
                    "health_check": health
                }
            except Exception as e:
                logger.error(f"获取层状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/v3-compliance", summary="V3理念遵从性检查")
        async def get_v3_compliance():
            """获取V3理念遵从性报告"""
            try:
                # 创建V3遵从性检查器
                checker = V3ComplianceChecker()
                report = checker.check_all_principles()
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "compliance_report": report
                }
            except Exception as e:
                logger.error(f"V3遵从性检查失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/agent-status", summary="Agent状态")
        async def get_agent_status():
            """获取所有Agent状态"""
            try:
                # 这里可以扩展为获取实际Agent状态
                agent_status = {
                    "total_agents": 0,
                    "active_agents": 0,
                    "agents": []
                }
                
                # 从四层管理器获取Agent组件
                status = self.layer_manager.get_layer_status()
                agent_components = status.get("agent_layer", {}).get("components", [])
                
                agent_status["total_agents"] = len(agent_components)
                agent_status["active_agents"] = len(agent_components)  # 假设都活跃
                agent_status["agents"] = [
                    {
                        "id": agent_id,
                        "status": "active",
                        "last_heartbeat": datetime.now().isoformat()
                    }
                    for agent_id in agent_components
                ]
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "agent_status": agent_status
                }
            except Exception as e:
                logger.error(f"获取Agent状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/gateway-metrics", summary="网关指标")
        async def get_gateway_metrics():
            """获取网关性能指标"""
            try:
                # 模拟网关指标
                metrics = {
                    "requests_processed": 1000,
                    "average_response_time_ms": 150.5,
                    "error_rate_percent": 0.5,
                    "active_sessions": 25,
                    "queue_size": 0
                }
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "metrics": metrics
                }
            except Exception as e:
                logger.error(f"获取网关指标失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/mcp-integration-status", summary="MCP集成状态")
        async def get_mcp_integration_status():
            """获取MCP集成状态"""
            try:
                result = await test_mcp_integration()
                
                return {
                    "success": True,
                    "timestamp": datetime.now().isoformat(),
                    "mcp_integration": result
                }
            except Exception as e:
                logger.error(f"获取MCP集成状态失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/system-summary", summary="系统摘要")
        async def get_system_summary():
            """获取系统摘要（移动设备优化）"""
            try:
                # 收集各种状态
                layer_status = self.layer_manager.get_layer_status()
                layer_health = await self.layer_manager.health_check()
                
                summary = {
                    "system_name": "RANGEN V2",
                    "version": "2.0.0",
                    "timestamp": datetime.now().isoformat(),
                    "overall_status": layer_health.get("overall", "unknown"),
                    "layers": {
                        "interaction": layer_status.get("interaction_layer", {}).get("implemented", False),
                        "gateway": layer_status.get("gateway_layer", {}).get("implemented", False),
                        "agent": layer_status.get("agent_layer", {}).get("implemented", False),
                        "tool": layer_status.get("tool_layer", {}).get("implemented", False)
                    },
                    "component_counts": {
                        "total_components": sum(
                            layer.get("component_count", 0)
                            for layer in layer_status.values()
                            if isinstance(layer, dict)
                        ),
                        "by_layer": {
                            "interaction": layer_status.get("interaction_layer", {}).get("component_count", 0),
                            "gateway": layer_status.get("gateway_layer", {}).get("component_count", 0),
                            "agent": layer_status.get("agent_layer", {}).get("component_count", 0),
                            "tool": layer_status.get("tool_layer", {}).get("component_count", 0)
                        }
                    }
                }
                
                return {
                    "success": True,
                    "summary": summary
                }
            except Exception as e:
                logger.error(f"获取系统摘要失败: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.router.get("/mobile-dashboard", response_class=HTMLResponse, summary="移动监控仪表盘")
        async def mobile_dashboard():
            """移动设备优化的监控仪表盘"""
            html_content = """
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>RANGEN移动监控仪表盘</title>
                <style>
                    * { box-sizing: border-box; margin: 0; padding: 0; }
                    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; 
                           background: #f5f5f5; color: #333; line-height: 1.6; padding: 20px; }
                    .container { max-width: 800px; margin: 0 auto; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .header h1 { color: #2c3e50; margin-bottom: 5px; }
                    .header p { color: #7f8c8d; }
                    .status-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 30px; }
                    .card { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .card h3 { margin-bottom: 15px; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px; }
                    .status-item { display: flex; justify-content: space-between; margin-bottom: 10px; }
                    .status-label { font-weight: 500; }
                    .status-value { font-weight: 600; }
                    .status-healthy { color: #27ae60; }
                    .status-warning { color: #f39c12; }
                    .status-error { color: #e74c3c; }
                    .refresh-btn { display: block; width: 100%; padding: 15px; background: #3498db; color: white; 
                                   border: none; border-radius: 5px; font-size: 16px; cursor: pointer; margin-top: 20px; }
                    .refresh-btn:hover { background: #2980b9; }
                    .footer { text-align: center; margin-top: 30px; color: #7f8c8d; font-size: 14px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📱 RANGEN移动监控</h1>
                        <p>实时系统状态监控</p>
                    </div>
                    
                    <div id="status-cards" class="status-cards">
                        <!-- 状态卡片将通过JavaScript动态加载 -->
                    </div>
                    
                    <button class="refresh-btn" onclick="loadDashboard()">🔄 刷新状态</button>
                    
                    <div class="footer">
                        <p>RANGEN V2 移动监控系统 &copy; 2024</p>
                        <p>最后更新: <span id="last-update">正在加载...</span></p>
                    </div>
                </div>
                
                <script>
                    async function loadDashboard() {
                        try {
                            // 加载系统摘要
                            const summaryResp = await fetch('/mobile-monitoring/system-summary');
                            const summary = await summaryResp.json();
                            
                            // 加载层状态
                            const layerResp = await fetch('/mobile-monitoring/layer-status');
                            const layerStatus = await layerResp.json();
                            
                            // 加载Agent状态
                            const agentResp = await fetch('/mobile-monitoring/agent-status');
                            const agentStatus = await agentResp.json();
                            
                            // 加载网关指标
                            const gatewayResp = await fetch('/mobile-monitoring/gateway-metrics');
                            const gatewayMetrics = await gatewayResp.json();
                            
                            // 构建HTML
                            let html = `
                                <div class="card">
                                    <h3>系统概览</h3>
                                    <div class="status-item">
                                        <span class="status-label">系统名称</span>
                                        <span class="status-value">${summary.summary.system_name}</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">版本</span>
                                        <span class="status-value">${summary.summary.version}</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">总体状态</span>
                                        <span class="status-value status-healthy">${summary.summary.overall_status}</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">总组件数</span>
                                        <span class="status-value">${summary.summary.component_counts.total_components}</span>
                                    </div>
                                </div>
                                
                                <div class="card">
                                    <h3>四层架构</h3>
                                    <div class="status-item">
                                        <span class="status-label">交互层</span>
                                        <span class="status-value ${summary.summary.layers.interaction ? 'status-healthy' : 'status-error'}">
                                            ${summary.summary.layers.interaction ? '✅ 已实现' : '❌ 未实现'}
                                        </span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">网关层</span>
                                        <span class="status-value ${summary.summary.layers.gateway ? 'status-healthy' : 'status-error'}">
                                            ${summary.summary.layers.gateway ? '✅ 已实现' : '❌ 未实现'}
                                        </span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">Agent层</span>
                                        <span class="status-value ${summary.summary.layers.agent ? 'status-healthy' : 'status-error'}">
                                            ${summary.summary.layers.agent ? '✅ 已实现' : '❌ 未实现'}
                                        </span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">工具层</span>
                                        <span class="status-value ${summary.summary.layers.tool ? 'status-healthy' : 'status-error'}">
                                            ${summary.summary.layers.tool ? '✅ 已实现' : '❌ 未实现'}
                                        </span>
                                    </div>
                                </div>
                                
                                <div class="card">
                                    <h3>Agent状态</h3>
                                    <div class="status-item">
                                        <span class="status-label">总Agent数</span>
                                        <span class="status-value">${agentStatus.agent_status.total_agents}</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">活跃Agent</span>
                                        <span class="status-value">${agentStatus.agent_status.active_agents}</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">最后心跳</span>
                                        <span class="status-value">刚刚</span>
                                    </div>
                                </div>
                                
                                <div class="card">
                                    <h3>网关性能</h3>
                                    <div class="status-item">
                                        <span class="status-label">处理请求数</span>
                                        <span class="status-value">${gatewayMetrics.metrics.requests_processed}</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">平均响应时间</span>
                                        <span class="status-value">${gatewayMetrics.metrics.average_response_time_ms}ms</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">错误率</span>
                                        <span class="status-value">${gatewayMetrics.metrics.error_rate_percent}%</span>
                                    </div>
                                    <div class="status-item">
                                        <span class="status-label">活跃会话</span>
                                        <span class="status-value">${gatewayMetrics.metrics.active_sessions}</span>
                                    </div>
                                </div>
                            `;
                            
                            document.getElementById('status-cards').innerHTML = html;
                            document.getElementById('last-update').textContent = new Date().toLocaleString('zh-CN');
                            
                        } catch (error) {
                            document.getElementById('status-cards').innerHTML = `
                                <div class="card">
                                    <h3>错误</h3>
                                    <p>加载监控数据失败: ${error.message}</p>
                                </div>
                            `;
                        }
                    }
                    
                    // 页面加载时自动刷新
                    document.addEventListener('DOMContentLoaded', loadDashboard);
                    // 每30秒自动刷新
                    setInterval(loadDashboard, 30000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
    
    async def start(self, host: str = "0.0.0.0", port: int = 8080):
        """启动移动监控服务器"""
        logger.info(f"启动移动监控服务器: {host}:{port}")
        
        # 确保四层架构已初始化
        try:
            setup_result = create_default_four_layer_setup()
            logger.info(f"四层架构默认设置完成: {setup_result.get('manager')}")
        except Exception as e:
            logger.warning(f"四层架构默认设置失败: {e}")
        
        config = uvicorn.Config(
            app=self.app,
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
        
        server = uvicorn.Server(config)
        await server.serve()
    
    def get_app(self) -> FastAPI:
        """获取FastAPI应用实例"""
        return self.app


# 全局移动监控实例
_mobile_monitoring_instance = None

def get_mobile_monitoring() -> MobileMonitoringSystem:
    """获取移动监控系统实例"""
    global _mobile_monitoring_instance
    if _mobile_monitoring_instance is None:
        _mobile_monitoring_instance = MobileMonitoringSystem()
    return _mobile_monitoring_instance


async def start_mobile_monitoring_server(host: str = "0.0.0.0", port: int = 8080):
    """启动移动监控服务器（独立运行）"""
    monitoring = get_mobile_monitoring()
    await monitoring.start(host, port)


if __name__ == "__main__":
    # 直接运行此文件将启动移动监控服务器
    import asyncio
    # 使用8081端口避免与主服务器冲突
    asyncio.run(start_mobile_monitoring_server(port=8081))