#!/usr/bin/env python3
"""
调试配置路由
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from src.core.dynamic_config_system import DynamicRoutingManager
from src.visualization.browser_server import BrowserVisualizationServer

async def debug_config_routes():
    """调试配置路由"""
    print("🔍 调试配置路由...")

    # 设置测试端口
    os.environ['DYNAMIC_CONFIG_API_PORT'] = '8082'
    os.environ['DYNAMIC_CONFIG_WEB_PORT'] = '8083'

    try:
        # 创建配置管理器
        config_manager = DynamicRoutingManager(enable_advanced_features=False)
        print("✅ 配置管理器创建成功")

        # 创建可视化服务器（不启动，只检查路由）
        viz_server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8083,
            config_manager=config_manager
        )
        print("✅ 可视化服务器创建成功")

        # 检查路由表
        routes = []
        for route in viz_server.app.routes:
            routes.append({
                'path': route.path,
                'methods': getattr(route, 'methods', ['GET']),
                'name': getattr(route, 'name', 'unknown')
            })

        print("\n📋 可视化服务器路由表:")
        for route in routes:
            print(f"  {route['methods']} {route['path']} -> {route['name']}")

        # 检查是否有 /config 路由
        config_routes = [r for r in routes if '/config' in r['path']]
        if config_routes:
            print(f"\n✅ 找到 {len(config_routes)} 个 /config 相关路由:")
            for route in config_routes:
                print(f"  {route['methods']} {route['path']}")
        else:
            print("\n❌ 未找到 /config 路由!")

        # 检查 config_manager 是否可用
        if viz_server.config_manager:
            print("\n✅ config_manager 已正确设置")
            config = viz_server.config_manager.get_routing_config()
            print(f"✅ 配置获取成功: {len(config)} 个配置项")
        else:
            print("\n❌ config_manager 未设置")

        return True

    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(debug_config_routes())
    sys.exit(0 if success else 1)
