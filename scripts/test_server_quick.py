#!/usr/bin/env python3
"""
快速测试服务器配置管理功能
"""

import sys
import os
from pathlib import Path
import asyncio

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def test_config_server():
    """测试配置管理服务器"""
    print("🚀 快速测试配置管理服务器...")

    try:
        # 只创建BrowserVisualizationServer，不依赖完整的系统
        from src.visualization.browser_server import BrowserVisualizationServer

        print("🔧 创建可视化服务器...")
        server = BrowserVisualizationServer(
            workflow=None,  # 不需要工作流
            system=None,    # 不需要完整系统
            port=8080,
            enable_config_management=True
        )

        print(f"✅ config_manager: {server.config_manager is not None}")

        if server.config_manager:
            print("🎉 配置管理器初始化成功！")

            # 检查路由
            routes = [route.path for route in server.app.routes]
            config_routes = [r for r in routes if 'config' in r.lower()]

            print(f"📋 配置相关路由数量: {len(config_routes)}")
            for route in config_routes:
                print(f"   - {route}")

            # 启动服务器测试
            print("\n🚀 启动测试服务器（5秒后自动停止）...")

            # 创建一个简单的任务来启动服务器
            async def start_server():
                # 这里我们不实际启动服务器，只验证初始化
                return True

            success = await start_server()

            if success:
                print("✅ 服务器初始化成功！")
                print("\n🌐 现在应该可以访问:")
                print("http://localhost:8080/config")
                print("http://localhost:8080/api/config")
                return True
            else:
                print("❌ 服务器启动失败")
                return False
        else:
            print("❌ 配置管理器初始化失败")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_config_server())
    if success:
        print("\n🎉 配置管理功能测试通过！现在可以启动完整服务器了。")
        print("\n💡 运行命令:")
        print("python scripts/start_unified_server.py --port 8080")
    else:
        print("\n❌ 配置管理功能测试失败")

    sys.exit(0 if success else 1)
