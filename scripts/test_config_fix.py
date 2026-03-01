#!/usr/bin/env python3
"""
测试配置管理器修复
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_manager_fix():
    """测试配置管理器修复"""
    print("🧪 测试配置管理器修复...")

    try:
        # 测试BrowserVisualizationServer初始化
        from src.visualization.browser_server import BrowserVisualizationServer

        print("🔧 创建BrowserVisualizationServer实例...")
        server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8080,
            enable_config_management=True
        )

        print(f"✅ config_manager状态: {server.config_manager is not None}")

        if server.config_manager:
            print("🎉 配置管理器初始化成功！")
            print("✅ 路由应该已经注册")

            # 检查关键路由
            routes = [route.path for route in server.app.routes]
            config_routes = [r for r in routes if 'config' in r.lower()]

            print(f"📋 找到配置相关路由: {len(config_routes)} 个")
            for route in config_routes:
                print(f"   - {route}")

            if '/config' in routes:
                print("✅ /config 路由已注册")
                return True
            else:
                print("❌ /config 路由未注册")
                return False
        else:
            print("❌ 配置管理器仍然初始化失败")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_config_manager_fix()
    sys.exit(0 if success else 1)
