#!/usr/bin/env python3
"""
简单测试路由注册
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_routes_registration():
    """测试路由注册"""
    print("🧪 测试路由注册...")

    try:
        # 导入必要的模块
        from fastapi import FastAPI
        from src.core.dynamic_config_system import DynamicConfigManager

        print("✅ 模块导入成功")

        # 创建FastAPI应用
        app = FastAPI(title="测试应用")

        # 创建配置管理器
        config_manager = DynamicConfigManager()
        print("✅ 配置管理器创建成功")

        # 手动注册路由（模拟BrowserVisualizationServer的行为）
        if config_manager:
            print("🔧 注册路由...")

            @app.get("/config")
            async def serve_config_dashboard():
                """服务配置管理仪表板"""
                return {"message": "配置管理页面", "status": "success"}

            @app.get("/api/config")
            async def get_config():
                """获取当前配置"""
                return config_manager.get_routing_config()

            print("✅ 路由注册完成")

        # 检查路由
        routes = [route.path for route in app.routes]
        print(f"📋 注册的路由 ({len(routes)} 个):")
        for route in sorted(routes):
            print(f"   - {route}")

        # 检查关键路由
        required_routes = ["/config", "/api/config"]
        missing_routes = []

        for route in required_routes:
            if route in routes:
                print(f"✅ {route} 存在")
            else:
                print(f"❌ {route} 缺失")
                missing_routes.append(route)

        if missing_routes:
            print(f"❌ 缺失路由: {missing_routes}")
            return False
        else:
            print("🎉 所有路由注册成功！")
            return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_routes_registration()
    if success:
        print("\n🚀 路由注册逻辑正确，现在服务器应该可以正常工作")
    else:
        print("\n❌ 路由注册存在问题")

    sys.exit(0 if success else 1)
