"""
配置管理Web界面

提供基于Web的配置管理界面和REST API
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import logging

logger = logging.getLogger(__name__)

class ConfigWebInterface:
    """配置管理Web界面"""

    def __init__(self, config_system, port: int = 8080):
        self.config_system = config_system
        self.port = port
        self.server = None
        self._running = False

    def start(self):
        """启动Web服务器"""
        if self._running:
            return

        self._running = True
        handler_class = self._create_request_handler()
        self.server = HTTPServer(('0.0.0.0', self.port), handler_class)

        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()

        logger.info(f"🌐 配置管理Web界面已启动: http://localhost:{self.port}")

    def stop(self):
        """停止Web服务器"""
        self._running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        logger.info("🛑 配置管理Web界面已停止")

    def _create_request_handler(self):
        """创建请求处理器"""
        config_system = self.config_system
        web_interface = self  # 引用ConfigWebInterface实例

        class ConfigHTTPRequestHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                self.config_system = config_system
                self.web_interface = web_interface  # 引用ConfigWebInterface实例
                super().__init__(*args, **kwargs)

            def do_GET(self):
                """处理GET请求"""
                try:
                    path = self.path.split('?')[0]  # 移除查询参数

                    if path == '/':
                        self._serve_dashboard()
                    elif path == '/api/config':
                        self._serve_config_api()
                    elif path == '/api/metrics':
                        self._serve_metrics_api()
                    elif path == '/api/logs':
                        self._serve_logs_api()
                    elif path.startswith('/api/templates'):
                        self._serve_templates_api()
                    elif path == '/health':
                        self._serve_health_check()
                    else:
                        self._serve_static_file(path)

                except Exception as e:
                    self._send_error(500, f"服务器错误: {str(e)}")

            def do_POST(self):
                """处理POST请求"""
                try:
                    path = self.path

                    if path == '/api/config/thresholds':
                        self._handle_update_thresholds()
                    elif path == '/api/config/keywords':
                        self._handle_update_keywords()
                    elif path == '/api/config/templates':
                        self._handle_apply_template()
                    elif path == '/api/auth/login':
                        self._handle_login()
                    else:
                        self._send_error(404, "接口不存在")

                except Exception as e:
                    self._send_error(500, f"服务器错误: {str(e)}")

            def _serve_dashboard(self):
                """服务仪表板页面"""
                # 通过web_interface调用生成HTML的方法
                html = self.web_interface._generate_dashboard_html()
                self._send_html_response(html)

            def _serve_config_api(self):
                """服务配置API"""
                config_data = self.config_system.get_routing_config()
                self._send_json_response(config_data)

            def _serve_metrics_api(self):
                """服务指标API"""
                if hasattr(self.config_system, 'config_manager') and self.config_system.config_manager:
                    metrics = self.config_system.config_manager.config_monitor.get_config_metrics()
                else:
                    metrics = {"status": "metrics_not_available"}
                self._send_json_response(metrics)

            def _serve_logs_api(self):
                """服务日志API"""
                query_params = parse_qs(urlparse(self.path).query)
                limit = int(query_params.get('limit', ['10'])[0])

                if hasattr(self.config_system, 'config_manager') and self.config_system.config_manager:
                    logs = self.config_system.config_manager.config_monitor.get_change_history(limit)
                else:
                    logs = []

                self._send_json_response({"logs": logs})

            def _serve_templates_api(self):
                """服务模板API"""
                if hasattr(self.config_system, 'config_manager') and self.config_system.config_manager:
                    templates = self.config_system.config_manager.template_manager.list_templates()
                else:
                    templates = []
                self._send_json_response({"templates": templates})

            def _serve_health_check(self):
                """服务健康检查"""
                health_status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "version": "1.0.0"
                }
                self._send_json_response(health_status)

            def _serve_static_file(self, path):
                """服务静态文件"""
                # 简化的静态文件服务
                if path.endswith('.css'):
                    self._send_css_response()
                elif path.endswith('.js'):
                    self._send_js_response()
                else:
                    self._send_error(404, "文件不存在")

            def _handle_update_thresholds(self):
                """处理更新阈值请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                # 验证权限（简化版）
                if not self._check_auth():
                    self._send_error(403, "无权限")
                    return

                try:
                    for key, value in data.items():
                        self.config_system.update_routing_threshold(key, value)

                    self._send_json_response({"status": "success", "message": "阈值已更新"})
                except Exception as e:
                    self._send_error(400, f"更新失败: {str(e)}")

            def _handle_update_keywords(self):
                """处理更新关键词请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                if not self._check_auth():
                    self._send_error(403, "无权限")
                    return

                try:
                    for category, keyword in data.items():
                        self.config_system.add_routing_keyword(category, keyword)

                    self._send_json_response({"status": "success", "message": "关键词已更新"})
                except Exception as e:
                    self._send_error(400, f"更新失败: {str(e)}")

            def _handle_apply_template(self):
                """处理应用模板请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                if not self._check_auth():
                    self._send_error(403, "无权限")
                    return

                template_name = data.get('template_name')
                if not template_name:
                    self._send_error(400, "缺少template_name参数")
                    return

                try:
                    self.config_system.apply_config_template(template_name)
                    self._send_json_response({"status": "success", "message": f"模板 {template_name} 已应用"})
                except Exception as e:
                    self._send_error(400, f"应用模板失败: {str(e)}")

            def _handle_login(self):
                """处理登录请求"""
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))

                username = data.get('username')
                password = data.get('password')

                # 简化的认证逻辑
                if username == 'admin' and password == 'admin':
                    # 生成会话ID
                    import hashlib
                    session_id = hashlib.md5(f"{username}_{datetime.now().isoformat()}".encode()).hexdigest()[:16]

                    if hasattr(self.config_system, 'advanced_system') and self.config_system.advanced_system:
                        self.config_system.advanced_system.access_control.create_session(username)

                    self._send_json_response({
                        "status": "success",
                        "session_id": session_id,
                        "user": username
                    })
                else:
                    self._send_error(401, "认证失败")

            def _check_auth(self) -> bool:
                """检查认证（简化版）"""
                # 检查Authorization头
                auth_header = self.headers.get('Authorization')
                if not auth_header:
                    return False

                # 这里应该验证实际的认证令牌
                return auth_header.startswith('Bearer ')

            def _send_html_response(self, html: str):
                """发送HTML响应"""
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))

            def _send_json_response(self, data: Dict[str, Any]):
                """发送JSON响应"""
                self.send_response(200)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

            def _send_css_response(self):
                """发送CSS响应"""
                css = """
                body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { color: #333; border-bottom: 2px solid #007cba; padding-bottom: 10px; margin-bottom: 20px; }
                .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007cba; }
                .status-healthy { color: #28a745; }
                .status-warning { color: #ffc107; }
                .status-error { color: #dc3545; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #007cba; color: white; }
                .btn { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
                .btn:hover { background: #005a87; }
                """
                self.send_response(200)
                self.send_header('Content-type', 'text/css')
                self.end_headers()
                self.wfile.write(css.encode('utf-8'))

            def _send_js_response(self):
                """发送JavaScript响应"""
                js = """
                // 简化的前端交互脚本
                function updateConfig() {
                    const thresholds = {
                        simple_max_complexity: parseFloat(document.getElementById('simple_max_complexity').value),
                        medium_max_complexity: parseFloat(document.getElementById('medium_max_complexity').value)
                    };

                    fetch('/api/config/thresholds', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer demo-token'
                        },
                        body: JSON.stringify(thresholds)
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('配置已更新: ' + data.message);
                        location.reload();
                    })
                    .catch(error => alert('更新失败: ' + error));
                }

                function applyTemplate(templateName) {
                    fetch('/api/config/templates', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': 'Bearer demo-token'
                        },
                        body: JSON.stringify({template_name: templateName})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('模板已应用: ' + data.message);
                        location.reload();
                    });
                }
                """
                self.send_response(200)
                self.send_header('Content-type', 'application/javascript')
                self.end_headers()
                self.wfile.write(js.encode('utf-8'))

            def _send_error(self, code: int, message: str):
                """发送错误响应"""
                self.send_response(code)
                self.send_header('Content-type', 'application/json; charset=utf-8')
                self.end_headers()
                error_data = {"error": message, "code": code}
                self.wfile.write(json.dumps(error_data, ensure_ascii=False).encode('utf-8'))

            def log_message(self, format, *args):
                """重写日志方法以减少输出"""
                pass

        return ConfigHTTPRequestHandler

    def _run_server(self):
        """运行服务器"""
        try:
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Web服务器运行错误: {e}")

    def _generate_dashboard_html(self) -> str:
        """生成仪表板HTML"""
        return f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>动态路由配置管理系统</title>
            <link rel="stylesheet" href="/style.css">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 动态路由配置管理系统</h1>
                    <p>企业级的配置管理解决方案</p>
                </div>

                <div class="metric">
                    <h3>系统状态</h3>
                    <p>状态: <span class="status-healthy">● 正常运行</span></p>
                    <p>最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="metric">
                    <h3>配置管理</h3>
                    <h4>阈值设置</h4>
                    <label>简单查询最大复杂度: <input type="number" id="simple_max_complexity" step="0.01" value="0.05"></label><br>
                    <label>中等查询最大复杂度: <input type="number" id="medium_max_complexity" step="0.01" value="0.25"></label><br>
                    <button class="btn" onclick="updateConfig()">更新配置</button>

                    <h4>模板应用</h4>
                    <button class="btn" onclick="applyTemplate('conservative')">应用保守模板</button>
                    <button class="btn" onclick="applyTemplate('balanced')">应用平衡模板</button>
                    <button class="btn" onclick="applyTemplate('aggressive')">应用激进模板</button>
                </div>

                <div class="metric">
                    <h3>API接口</h3>
                    <ul>
                        <li><code>GET /api/config</code> - 获取当前配置</li>
                        <li><code>GET /api/metrics</code> - 获取系统指标</li>
                        <li><code>GET /api/logs</code> - 获取变更日志</li>
                        <li><code>POST /api/config/thresholds</code> - 更新阈值</li>
                        <li><code>POST /api/config/templates</code> - 应用模板</li>
                    </ul>
                </div>

                <div class="metric">
                    <h3>系统特性</h3>
                    <ul>
                        <li>✅ 运行时配置更新</li>
                        <li>✅ 配置持久化存储</li>
                        <li>✅ 变更历史追踪</li>
                        <li>✅ 配置验证和健康检查</li>
                        <li>✅ 模板系统支持</li>
                        <li>✅ 多租户配置隔离</li>
                        <li>✅ 热更新和自动刷新</li>
                        <li>✅ 告警和监控系统</li>
                    </ul>
                </div>
            </div>

            <script src="/script.js"></script>
        </body>
        </html>
        """

class ConfigAPIClient:
    """配置管理API客户端"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')

    def get_config(self) -> Dict[str, Any]:
        """获取配置"""
        return self._get("/api/config")

    def update_thresholds(self, thresholds: Dict[str, float], token: str = None) -> Dict[str, Any]:
        """更新阈值"""
        return self._post("/api/config/thresholds", thresholds, token)

    def update_keywords(self, keywords: Dict[str, str], token: str = None) -> Dict[str, Any]:
        """更新关键词"""
        return self._post("/api/config/keywords", keywords, token)

    def apply_template(self, template_name: str, token: str = None) -> Dict[str, Any]:
        """应用模板"""
        return self._post("/api/config/templates", {"template_name": template_name}, token)

    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        return self._get("/api/metrics")

    def get_logs(self, limit: int = 10) -> Dict[str, Any]:
        """获取日志"""
        return self._get(f"/api/logs?limit={limit}")

    def login(self, username: str, password: str) -> Dict[str, Any]:
        """登录"""
        return self._post("/api/auth/login", {"username": username, "password": password})

    def _get(self, endpoint: str) -> Dict[str, Any]:
        """GET请求"""
        import requests
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def _post(self, endpoint: str, data: Dict[str, Any], token: str = None) -> Dict[str, Any]:
        """POST请求"""
        import requests
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'Bearer {token}'

        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=data, headers=headers, timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

class ConfigImportExportManager:
    """配置导入导出管理器"""

    def __init__(self, config_system):
        self.config_system = config_system

    def export_config(self, format: str = "json", include_history: bool = False) -> str:
        """导出配置"""
        config_data = self.config_system.get_routing_config()

        if include_history and hasattr(self.config_system, 'config_manager'):
            config_data['change_history'] = self.config_system.config_manager.config_monitor.get_change_history(100)

        if format == "json":
            return json.dumps(config_data, ensure_ascii=False, indent=2)
        elif format == "yaml":
            try:
                import yaml
                return yaml.dump(config_data, allow_unicode=True, default_flow_style=False)
            except ImportError:
                return json.dumps(config_data, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def import_config(self, config_data: str, format: str = "json", dry_run: bool = True) -> Dict[str, Any]:
        """导入配置"""
        try:
            if format == "json":
                data = json.loads(config_data)
            elif format == "yaml":
                import yaml
                data = yaml.safe_load(config_data)
            else:
                raise ValueError(f"不支持的格式: {format}")

            # 验证配置
            validation_result = self._validate_import_data(data)

            if not validation_result['valid']:
                return {
                    'success': False,
                    'errors': validation_result['errors']
                }

            if dry_run:
                return {
                    'success': True,
                    'dry_run': True,
                    'changes': validation_result['changes']
                }

            # 执行导入
            self._apply_import_data(data)
            return {
                'success': True,
                'message': '配置导入成功'
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _validate_import_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证导入数据"""
        errors = []
        changes = []

        # 检查必需字段
        required_fields = ['thresholds']
        for field in required_fields:
            if field not in data:
                errors.append(f"缺少必需字段: {field}")

        # 验证阈值
        if 'thresholds' in data:
            current_thresholds = self.config_system.config.thresholds
            for key, value in data['thresholds'].items():
                if key in current_thresholds:
                    current_value = current_thresholds[key]
                    if current_value != value:
                        changes.append({
                            'type': 'threshold_update',
                            'key': key,
                            'old_value': current_value,
                            'new_value': value
                        })

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'changes': changes
        }

    def _apply_import_data(self, data: Dict[str, Any]):
        """应用导入数据"""
        # 更新阈值
        if 'thresholds' in data:
            for key, value in data['thresholds'].items():
                self.config_system.update_routing_threshold(key, value)

        # 更新关键词
        if 'keywords' in data:
            for category, keywords in data['keywords'].items():
                if isinstance(keywords, list):
                    for keyword in keywords:
                        self.config_system.add_routing_keyword(category, keyword)
