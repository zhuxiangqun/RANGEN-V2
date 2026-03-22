#!/usr/bin/env python3
"""
测试路由注册过程
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_route_registration():
    """测试路由注册"""
    try:
        print("🔍 测试路由注册过程...")

        # 检查FastAPI是否可用
        try:
            from fastapi import FastAPI
            print("✅ FastAPI 可用")
        except ImportError:
            print("❌ FastAPI 不可用")
            return

        # 创建服务器实例
        from src.visualization.browser_server import BrowserVisualizationServer

        print("🚀 创建服务器实例...")
        server = BrowserVisualizationServer(port=8080, enable_config_management=True)

        print("🔧 注册路由...")
        server._register_routes()

        # 检查路由
        routes = [route.path for route in server.app.routes]
        print(f"📋 总路由数: {len(routes)}")

        key_routes = ['/api/workflow/graph', '/api/test', '/api/config', '/']
        print("\n🔍 关键路由检查:")
        for route in key_routes:
            if route in routes:
                print(f"  ✅ {route}")
            else:
                print(f"  ❌ {route}")

        print("\n📋 所有路由:")
        for route in sorted(routes):
            print(f"  - {route}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_route_registration()
