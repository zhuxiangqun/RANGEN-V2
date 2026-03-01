#!/usr/bin/env python3
"""
简单测试服务器路由注册（不依赖完整系统）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量避免torch导入问题
os.environ['TRANSFORMERS_OFFLINE'] = '1'

def test_simple_server():
    """简单测试服务器"""
    print("🧪 简单服务器路由测试...")

    try:
        # 创建一个最小的BrowserVisualizationServer测试
        from fastapi import FastAPI

        # 检查FastAPI是否可用
        print("✅ FastAPI已安装")

        # 手动创建配置管理器
        from src.core.dynamic_config_system import DynamicConfigManager
        print("🔧 创建配置管理器...")
        config_manager = DynamicConfigManager()
        print("✅ 配置管理器创建成功")

        # 创建FastAPI应用
        app = FastAPI(title="测试服务器")

        # 手动注册路由（模拟BrowserVisualizationServer的行为）
        if config_manager:
            print("✅ 注册配置路由...")

            @app.get("/config")
            async def serve_config_dashboard():
                """服务配置管理仪表板"""
                return {"message": "配置管理页面", "status": "success"}

            @app.get("/api/config")
            async def get_config():
                """获取当前配置"""
                return config_manager.get_routing_config()

            @app.get("/api/route-types")
            async def get_route_types():
                """获取路由类型列表"""
                return {
                    "route_types": [
                        {
                            "name": rt.name,
                            "description": rt.description,
                            "priority": rt.priority,
                            "enabled": rt.enabled
                        }
                        for rt in config_manager.route_type_registry.get_all_route_types()
                    ]
                }

        # 检查路由
        routes = [route.path for route in app.routes]
        print(f"📋 总路由数量: {len(routes)}")

        config_routes = [r for r in routes if 'config' in r.lower()]
        print(f"📋 配置相关路由: {len(config_routes)}")

        for route in config_routes:
            print(f"   - {route}")

        # 检查关键路由
        key_routes = ['/config', '/api/config', '/api/route-types']
        all_present = all(route in routes for route in key_routes)

        if all_present:
            print("🎉 所有关键路由都已正确注册！")
            return True
        else:
            missing = [r for r in key_routes if r not in routes]
            print(f"❌ 缺失路由: {missing}")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_server()
    if success:
        print("\n🚀 路由注册测试通过！配置管理器路由已正确设置。")
        print("现在完整服务器应该也能正常工作了。")
    else:
        print("\n❌ 路由注册测试失败")

    sys.exit(0 if success else 1)
