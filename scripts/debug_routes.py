#!/usr/bin/env python3
"""
调试路由注册问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def debug_routes():
    """调试路由注册"""
    print("🔍 调试路由注册问题...")

    try:
        # 模拟BrowserVisualizationServer的初始化过程
        print("1. 检查依赖可用性...")

        try:
            from fastapi import FastAPI
            FASTAPI_AVAILABLE = True
            print("   ✅ FastAPI 可用")
        except ImportError:
            FASTAPI_AVAILABLE = False
            print("   ❌ FastAPI 不可用")
            return False

        if not FASTAPI_AVAILABLE:
            print("❌ FastAPI 未安装，无法继续测试")
            return False

        print("2. 创建配置管理器...")

        try:
            from src.core.dynamic_config_system import DynamicConfigManager
            config_manager = DynamicConfigManager()
            print("   ✅ 配置管理器创建成功")
        except Exception as e:
            print(f"   ❌ 配置管理器创建失败: {e}")
            return False

        print("3. 创建FastAPI应用并注册路由...")

        app = FastAPI(title="调试应用")

        # 模拟BrowserVisualizationServer的路由注册
        if config_manager:
            print("   🔧 注册 /config 路由...")

            @app.get("/config")
            async def serve_config_dashboard():
                """服务配置管理仪表板"""
                return {"message": "配置管理页面", "status": "success"}

            @app.get("/api/config")
            async def get_config():
                """获取当前配置"""
                return config_manager.get_routing_config()

            print("   ✅ 路由注册完成")

        print("4. 检查注册的路由...")

        routes = [route.path for route in app.routes]
        print(f"   📋 总路由数: {len(routes)}")

        config_routes = [r for r in routes if 'config' in r.lower()]
        print(f"   📋 配置相关路由: {len(config_routes)}")

        for route in sorted(routes):
            print(f"      - {route}")

        # 检查关键路由
        required_routes = ['/config', '/api/config']
        missing = []

        for route in required_routes:
            if route in routes:
                print(f"   ✅ {route} 存在")
            else:
                print(f"   ❌ {route} 缺失")
                missing.append(route)

        if missing:
            print(f"   ❌ 缺失路由: {missing}")
            return False

        print("5. 测试路由功能...")

        # 这里无法实际调用路由（需要运行服务器），但可以检查路由对象
        config_route = None
        api_config_route = None

        for route in app.routes:
            if route.path == '/config':
                config_route = route
            elif route.path == '/api/config':
                api_config_route = route

        if config_route:
            print("   ✅ /config 路由对象存在")
            print(f"      - 方法: {config_route.methods}")
            print(f"      - 响应类: {getattr(config_route, 'response_class', 'N/A')}")
        else:
            print("   ❌ /config 路由对象不存在")

        if api_config_route:
            print("   ✅ /api/config 路由对象存在")
            print(f"      - 方法: {api_config_route.methods}")
            print(f"      - 响应类: {getattr(api_config_route, 'response_class', 'N/A')}")
        else:
            print("   ❌ /api/config 路由对象不存在")

        print("\n🎉 路由注册逻辑测试完成！")
        print("如果这个测试通过但服务器仍有问题，可能是以下原因:")
        print("1. 服务器没有正确重启")
        print("2. 端口被其他进程占用")
        print("3. 浏览器缓存问题")
        print("4. 防火墙或网络配置问题")

        return True

    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_routes()
    sys.exit(0 if success else 1)
