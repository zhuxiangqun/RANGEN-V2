#!/usr/bin/env python3
"""
测试配置管理器核心功能（不依赖FastAPI）
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_config_manager_core():
    """测试配置管理器核心功能"""
    print("🧪 测试配置管理器核心功能...")

    try:
        # 导入配置管理器
        from src.core.dynamic_config_system import DynamicConfigManager
        print("✅ 动态配置系统导入成功")

        # 创建配置管理器
        print("🔧 创建配置管理器...")
        config_manager = DynamicConfigManager()
        print("✅ 配置管理器创建成功")

        # 测试路由类型注册表
        if hasattr(config_manager, 'route_type_registry'):
            route_types = config_manager.route_type_registry.get_all_route_types()
            print(f"✅ 路由类型注册表正常，包含 {len(route_types)} 个类型")

            # 显示前几个路由类型
            for rt in list(route_types)[:3]:
                print(f"   - {rt.name}: {rt.description}")
        else:
            print("❌ 路由类型注册表不存在")
            return False

        # 测试配置获取
        config = config_manager.get_routing_config()
        print(f"✅ 配置获取成功，包含 {len(config)} 个配置项")

        # 检查配置内容
        required_keys = ['thresholds', 'keywords', 'route_types']
        for key in required_keys:
            if key in config:
                print(f"   ✅ {key} 配置存在")
            else:
                print(f"   ❌ {key} 配置缺失")
                return False

        print("🎉 配置管理器核心功能测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_advanced_config_system():
    """测试高级配置系统"""
    print("\n🧪 测试高级配置系统...")

    try:
        from src.core.advanced_config_features import AdvancedConfigSystem
        print("✅ 高级配置功能导入成功")

        # 测试构造函数
        print("🔧 创建高级配置系统...")
        advanced_config = AdvancedConfigSystem()
        print("✅ 高级配置系统创建成功")

        # 检查是否有必要的属性
        if hasattr(advanced_config, 'config_manager'):
            print("✅ 高级配置系统包含config_manager")
        else:
            print("❌ 高级配置系统缺少config_manager")

        if hasattr(advanced_config, 'hot_reload'):
            print("✅ 高级配置系统包含hot_reload")
        else:
            print("⚠️ 高级配置系统缺少hot_reload")

        print("🎉 高级配置系统测试通过！")
        return True

    except Exception as e:
        print(f"❌ 高级配置系统测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🐛 配置管理器核心测试")
    print("=" * 50)

    success = True

    # 测试配置管理器核心
    if not test_config_manager_core():
        success = False

    # 测试高级配置系统
    if not test_advanced_config_system():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 所有核心测试通过！")
        print("\n📋 测试结果：")
        print("✅ 动态配置系统正常")
        print("✅ 配置管理器初始化成功")
        print("✅ 路由类型注册表工作正常")
        print("✅ 高级配置系统可用")
        print("\n🚀 现在应该可以正常启动服务器了")
    else:
        print("❌ 核心测试失败")

    sys.exit(0 if success else 1)
