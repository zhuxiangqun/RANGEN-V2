#!/usr/bin/env python3
"""
简化的配置管理服务器测试
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_server():
    """测试配置管理服务器"""
    print("🧪 测试配置管理服务器...")

    try:
        # 只导入必要的配置模块
        from src.core.dynamic_config_system import DynamicConfigManager

        # 创建配置管理器
        config_manager = DynamicConfigManager()
        print("✅ 配置管理器创建成功")

        # 测试FastAPI服务器
        from fastapi import FastAPI
        from fastapi.responses import HTMLResponse, JSONResponse

        app = FastAPI(title="Config Test Server")

        @app.get("/")
        async def root():
            return {"message": "配置管理服务器运行正常"}

        @app.get("/config", response_class=HTMLResponse)
        async def config_page():
            config = config_manager.get_routing_config()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>配置管理测试</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                    .threshold {{ background: #f0f8ff; }}
                    .keyword {{ background: #fffacd; }}
                    .route-type {{ background: #f0fff0; }}
                </style>
            </head>
            <body>
                <h1>🚀 配置管理测试页面</h1>
                <p>如果您能看到这个页面，说明配置管理系统集成成功！</p>

                <div class="section threshold">
                    <h2>阈值配置</h2>
                    <pre>{config.get('thresholds', {})}</pre>
                </div>

                <div class="section keyword">
                    <h2>关键词配置</h2>
                    <pre>{config.get('keywords', {})}</pre>
                </div>

                <div class="section route-type">
                    <h2>路由类型</h2>
                    <pre>{config.get('route_types', [])}</pre>
                </div>
            </body>
            </html>
            """
            return HTMLResponse(content=html)

        @app.get("/api/config")
        async def get_config():
            return config_manager.get_routing_config()

        print("✅ FastAPI应用创建成功")
        print("🎯 测试路由：")
        print("   - GET /         -> 服务器状态")
        print("   - GET /config   -> 配置管理页面")
        print("   - GET /api/config -> 配置API")

        # 启动服务器进行测试
        import uvicorn
        print("\n🚀 启动测试服务器 (按Ctrl+C停止)...")

        # 使用一个不同的端口进行测试
        uvicorn.run(app, host="127.0.0.1", port=8088, log_level="info")

    except KeyboardInterrupt:
        print("\n✅ 测试服务器已停止")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_config_server()
