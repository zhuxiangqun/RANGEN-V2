#!/usr/bin/env python3
"""
调试配置管理器初始化
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_manager_initialization():
    """测试配置管理器初始化"""
    print("🔍 测试配置管理器初始化...")

    try:
        # 导入必要的模块
        print("📦 导入模块...")

        # 测试动态配置系统导入
        try:
            from src.core.dynamic_config_system import (
                DynamicConfigManager, ConfigStore, FileConfigStore,
                ConfigValidator, ConfigMonitor
            )
            print("✅ 动态配置系统导入成功")
        except ImportError as e:
            print(f"❌ 动态配置系统导入失败: {e}")
            return False

        # 测试高级功能导入
        try:
            from src.core.advanced_config_features import AdvancedConfigSystem
            print("✅ 高级配置功能导入成功")
        except ImportError as e:
            print(f"⚠️ 高级配置功能导入失败（可选）: {e}")

        # 初始化配置管理器
        print("🔧 初始化配置管理器...")
        config_manager = DynamicConfigManager()
        print("✅ 配置管理器初始化成功")

        # 检查路由类型注册表
        if hasattr(config_manager, 'route_type_registry'):
            route_types = config_manager.route_type_registry.get_all_route_types()
            print(f"✅ 路由类型注册表正常，包含 {len(route_types)} 个路由类型")
            for rt in list(route_types)[:3]:  # 只显示前3个
                print(f"   - {rt.name}: {rt.description}")
        else:
            print("❌ 路由类型注册表不存在")
            return False

        # 测试配置获取
        try:
            config = config_manager.get_routing_config()
            print(f"✅ 配置获取成功，包含 {len(config)} 个配置项")
        except Exception as e:
            print(f"❌ 配置获取失败: {e}")
            return False

        print("🎉 配置管理器测试通过！")
        return True

    except Exception as e:
        print(f"❌ 配置管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_browser_server_config():
    """测试BrowserVisualizationServer的配置集成"""
    print("\n🔍 测试BrowserVisualizationServer配置集成...")

    try:
        # 检查代码结构
        with open('src/visualization/browser_server.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查必要的导入
        required_imports = [
            'from src.core.dynamic_config_system import',
            'DYNAMIC_CONFIG_AVAILABLE',
            '_initialize_config_manager',
            'enable_config_management'
        ]

        for imp in required_imports:
            if imp not in content:
                print(f"❌ 缺少导入或定义: {imp}")
                return False

        print("✅ BrowserVisualizationServer代码结构正确")

        # 检查构造函数参数
        if 'enable_config_management' not in content:
            print("❌ 构造函数缺少enable_config_management参数")
            return False

        print("✅ 构造函数参数正确")

        # 检查路由注册
        if '/config' not in content or '/api/config' not in content:
            print("❌ 缺少配置管理路由")
            return False

        print("✅ 配置管理路由存在")

        print("🎉 BrowserVisualizationServer测试通过！")
        return True

    except Exception as e:
        print(f"❌ BrowserVisualizationServer测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🐛 配置管理器调试工具")
    print("=" * 50)

    success = True

    # 测试配置管理器
    if not test_config_manager_initialization():
        success = False

    # 测试BrowserVisualizationServer集成
    if not test_browser_server_config():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 所有调试测试通过！配置管理器应该能正常工作。")
        print("\n💡 如果仍然遇到问题，请检查：")
        print("1. 服务器是否正在运行")
        print("2. 端口是否正确")
        print("3. 浏览器缓存是否清除")
        print("4. 查看服务器日志中的错误信息")
    else:
        print("❌ 调试发现问题，请修复后重试")

    print("\n🔧 快速测试命令：")
    print("python scripts/start_unified_server.py --port 8080")
    print("curl http://localhost:8080/config")

    sys.exit(0 if success else 1)
