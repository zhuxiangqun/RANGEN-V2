#!/usr/bin/env python3
"""
直接测试BrowserVisualizationServer路由注册
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_browser_server():
    """测试BrowserVisualizationServer"""
    print("🧪 测试BrowserVisualizationServer路由注册...")

    try:
        # 直接导入BrowserVisualizationServer，避免加载整个系统
        from src.visualization.browser_server import BrowserVisualizationServer

        print("🔧 创建BrowserVisualizationServer实例...")

        # 创建服务器实例，禁用系统和工作流以避免复杂依赖
        server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8080,
            enable_config_management=True
        )

        print("✅ 服务器实例创建成功")

        # 检查配置管理器
        print(f"📋 config_manager状态: {server.config_manager is not None}")
        print(f"📋 enable_config_management: {server.enable_config_management}")

        # 检查路由
        routes = [route.path for route in server.app.routes]
        print(f"📋 总路由数: {len(routes)}")

        # 显示所有路由
        print("📋 所有路由:")
        for route in sorted(routes):
            print(f"   - {route}")

        # 检查配置相关路由
        config_routes = [r for r in routes if 'config' in r.lower()]
        print(f"📋 配置相关路由 ({len(config_routes)} 个):")
        for route in config_routes:
            print(f"   - {route}")

        # 检查关键路由
        required_routes = ['/config', '/api/config']
        missing = []

        for route in required_routes:
            if route in routes:
                print(f"✅ {route} 存在")
            else:
                print(f"❌ {route} 缺失")
                missing.append(route)

        if missing:
            print(f"❌ 缺失路由: {missing}")
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
    success = test_browser_server()
    if success:
        print("\n🚀 BrowserVisualizationServer路由注册测试通过！")
        print("如果完整服务器仍有问题，可能是系统初始化时的其他问题。")
    else:
        print("\n❌ 路由注册测试失败")

    sys.exit(0 if success else 1)
