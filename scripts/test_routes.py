#!/usr/bin/env python3
"""
测试路由注册是否正确
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_routes():
    """测试路由注册"""
    print("🧪 测试路由注册...")

    try:
        # 创建BrowserVisualizationServer
        from src.visualization.browser_server import BrowserVisualizationServer

        print("🔧 创建服务器实例...")
        server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8080,
            enable_config_management=True
        )

        print(f"✅ config_manager: {server.config_manager is not None}")

        # 检查路由
        routes = [route.path for route in server.app.routes]
        print(f"📋 总路由数量: {len(routes)}")

        # 查找配置相关路由
        config_routes = [r for r in routes if 'config' in r.lower()]
        print(f"📋 配置相关路由: {len(config_routes)}")

        for route in config_routes:
            print(f"   - {route}")

        # 检查关键路由
        key_routes = ['/config', '/api/config', '/api/route-types']
        missing_routes = []

        for route in key_routes:
            if route in routes:
                print(f"✅ {route} 路由存在")
            else:
                print(f"❌ {route} 路由缺失")
                missing_routes.append(route)

        if missing_routes:
            print(f"❌ 缺失路由: {missing_routes}")
            return False
        else:
            print("🎉 所有关键路由都已注册！")
            return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_routes()
    if success:
        print("\n🚀 路由注册测试通过！现在应该可以访问 /config 页面了。")
    else:
        print("\n❌ 路由注册测试失败")

    sys.exit(0 if success else 1)
