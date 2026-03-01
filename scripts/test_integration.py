#!/usr/bin/env python3
"""
测试配置管理集成
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_browser_server_integration():
    """测试BrowserVisualizationServer的配置管理集成"""
    print("🧪 测试BrowserVisualizationServer配置管理集成")

    try:
        # 检查必要的导入是否可用
        fastapi_available = True
        try:
            from fastapi import FastAPI
        except ImportError:
            fastapi_available = False

        if not fastapi_available:
            print("⚠️ FastAPI不可用，跳过完整实例化测试")
            # 检查代码结构
            return test_code_structure()

        from src.visualization.browser_server import BrowserVisualizationServer

        # 检查构造函数参数
        import inspect
        sig = inspect.signature(BrowserVisualizationServer.__init__)
        params = list(sig.parameters.keys())

        if 'enable_config_management' not in params:
            print("❌ BrowserVisualizationServer缺少enable_config_management参数")
            return False

        print("✅ BrowserVisualizationServer构造函数参数正确")

        # 检查_initialize_config_manager方法是否存在
        if not hasattr(BrowserVisualizationServer, '_initialize_config_manager'):
            print("❌ 缺少_initialize_config_manager方法")
            return False

        print("✅ _initialize_config_manager方法存在")

        # 检查代码结构
        return test_code_structure()

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_code_structure():
    """测试代码结构"""
    print("🔍 检查代码结构...")

    try:
        # 检查BrowserVisualizationServer是否导入了动态配置系统
        with open('src/visualization/browser_server.py', 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查必要的导入
        imports_check = [
            'from src.core.dynamic_config_system import' in content,
            'DYNAMIC_CONFIG_AVAILABLE' in content,
            'enable_config_management' in content,
            '_initialize_config_manager' in content,
        ]

        if not all(imports_check):
            print("❌ 代码结构检查失败")
            return False

        print("✅ 代码结构检查通过")

        # 检查是否有配置管理路由
        if '/config' not in content or '/api/config' not in content:
            print("❌ 缺少配置管理路由")
            return False

        print("✅ 配置管理路由存在")

        return True

    except Exception as e:
        print(f"❌ 代码结构检查失败: {e}")
        return False

def test_unified_server_structure():
    """测试UnifiedServer的结构"""
    print("\n🧪 测试UnifiedServer结构")

    try:
        from scripts.start_unified_server import UnifiedServer

        # 检查类结构
        server = UnifiedServer(port=8080)

        if not hasattr(server, 'port'):
            print("❌ UnifiedServer缺少port属性")
            return False

        if not hasattr(server, 'visualization_server'):
            print("❌ UnifiedServer缺少visualization_server属性")
            return False

        if hasattr(server, 'config_manager'):
            print("⚠️ UnifiedServer仍有旧的config_manager属性")

        print("✅ UnifiedServer结构正确")
        return True

    except Exception as e:
        print(f"❌ UnifiedServer测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 配置管理集成测试")
    print("=" * 50)

    success = True

    # 测试BrowserVisualizationServer集成
    if not test_browser_server_integration():
        success = False

    # 测试UnifiedServer结构
    if not test_unified_server_structure():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 所有集成测试通过！配置管理已成功集成到可视化服务中。")
        print("\n📋 现在您可以：")
        print("   🌐 启动统一服务器: python scripts/start_unified_server.py --port 8080")
        print("   📊 访问可视化: http://localhost:8080/")
        print("   ⚙️ 访问配置管理: http://localhost:8080/config")
        print("   🔗 访问API: http://localhost:8080/api/*")
    else:
        print("❌ 集成测试失败，请检查代码")

    sys.exit(0 if success else 1)
