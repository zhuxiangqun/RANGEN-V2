#!/usr/bin/env python3
"""
测试服务器路由注册
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_route_registration():
    """测试路由注册"""
    print("🧪 测试服务器路由注册...")

    try:
        # 检查FastAPI是否可用
        try:
            from fastapi import FastAPI
            FASTAPI_AVAILABLE = True
            print("✅ FastAPI可用")
        except ImportError:
            print("❌ FastAPI不可用")
            return False

        # 检查动态配置系统
        try:
            from src.core.dynamic_config_system import DynamicConfigManager
            DYNAMIC_CONFIG_AVAILABLE = True
            print("✅ 动态配置系统可用")
        except ImportError as e:
            print(f"❌ 动态配置系统不可用: {e}")
            DYNAMIC_CONFIG_AVAILABLE = False

        if not DYNAMIC_CONFIG_AVAILABLE:
            print("⚠️ 由于动态配置系统不可用，将跳过配置管理路由测试")
            return test_basic_routes()

        # 创建BrowserVisualizationServer实例
        print("🔧 创建BrowserVisualizationServer实例...")
        from src.visualization.browser_server import BrowserVisualizationServer

        server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8080,
            enable_config_management=True
        )

        print(f"🔍 config_manager状态: {server.config_manager is not None}")

        if server.config_manager:
            print("✅ 配置管理器已初始化")
        else:
            print("❌ 配置管理器初始化失败")
            return False

        # 检查路由列表
        routes = [route.path for route in server.app.routes]
        print(f"📋 总路由数量: {len(routes)}")

        # 检查关键路由
        key_routes = ['/', '/config', '/api/config']
        found_routes = []

        for route in key_routes:
            if route in routes:
                found_routes.append(route)
                print(f"✅ 路由 {route} 已注册")
            else:
                print(f"❌ 路由 {route} 未注册")

        if len(found_routes) == len(key_routes):
            print("🎉 所有关键路由都已正确注册！")
            return True
        else:
            print(f"⚠️ 只有 {len(found_routes)}/{len(key_routes)} 个关键路由已注册")
            return False

    except Exception as e:
        print(f"❌ 路由注册测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_routes():
    """测试基本路由（不依赖配置管理器）"""
    print("🧪 测试基本路由注册...")

    try:
        from fastapi import FastAPI
        from src.visualization.browser_server import BrowserVisualizationServer

        server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8080,
            enable_config_management=False  # 禁用配置管理器
        )

        routes = [route.path for route in server.app.routes]
        print(f"📋 基本路由数量: {len(routes)}")

        # 检查基本路由
        basic_routes = ['/']
        for route in basic_routes:
            if route in routes:
                print(f"✅ 基本路由 {route} 已注册")
            else:
                print(f"❌ 基本路由 {route} 未注册")

        return True

    except Exception as e:
        print(f"❌ 基本路由测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 服务器路由注册测试")
    print("=" * 50)

    success = test_route_registration()

    print("\n" + "=" * 50)
    if success:
        print("🎉 路由注册测试通过！")
        print("\n💡 现在可以启动服务器：")
        print("python scripts/start_unified_server.py --port 8080")
        print("\n🔍 然后测试访问：")
        print("curl http://localhost:8080/")
        print("curl http://localhost:8080/config")
        print("curl http://localhost:8080/api/config")
    else:
        print("❌ 路由注册测试失败")
        print("\n🔧 可能的解决方案：")
        print("1. 检查FastAPI是否正确安装：pip install fastapi uvicorn")
        print("2. 检查动态配置系统是否可用")
        print("3. 查看详细错误信息")

    sys.exit(0 if success else 1)
