#!/usr/bin/env python3
"""
测试配置管理页面的tab布局
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

async def test_config_tabs():
    """测试配置管理页面的tab布局"""
    print("🧪 测试配置管理页面tab布局...")

    # 设置测试端口
    os.environ['DYNAMIC_CONFIG_API_PORT'] = '8082'
    os.environ['DYNAMIC_CONFIG_WEB_PORT'] = '8083'

    try:
        # 创建配置管理器
        config_manager = DynamicRoutingManager(enable_advanced_features=False)
        print("✅ 配置管理器创建成功")

        # 创建可视化服务器
        viz_server = BrowserVisualizationServer(
            workflow=None,
            system=None,
            port=8083,
            config_manager=config_manager
        )
        print("✅ 可视化服务器创建成功")

        # 生成HTML内容
        html = viz_server._generate_config_dashboard_html()
        print("✅ 配置仪表板HTML生成成功")

        # 检查HTML中是否包含新的tab结构
        if 'id="config"' in html and 'id="system"' in html:
            print("✅ 找到新的tab结构: config 和 system")
        else:
            print("❌ 未找到新的tab结构")
            return False

        if 'config-grid' in html and 'system-grid' in html:
            print("✅ 找到新的网格布局: config-grid 和 system-grid")
        else:
            print("❌ 未找到新的网格布局")
            return False

        if '⚙️ 配置管理' in html and '📊 系统状态' in html:
            print("✅ 找到新的tab标题")
        else:
            print("❌ 未找到新的tab标题")
            return False

        # 检查是否还有旧的tab
        old_tabs = ['id="overview"', 'id="thresholds"', 'id="keywords"', 'id="route-types"']
        found_old = False
        for old_tab in old_tabs:
            if old_tab in html:
                print(f"⚠️ 仍找到旧的tab: {old_tab}")
                found_old = True

        if not found_old:
            print("✅ 已成功移除所有旧的tab结构")

        print("🎉 配置管理页面tab布局测试通过！")
        print("\n📋 新的tab结构:")
        print("  Tab 1: ⚙️ 配置管理")
        print("    - 🎯 阈值配置")
        print("    - 🏷️ 关键词配置")
        print("  Tab 2: 📊 系统状态")
        print("    - 📊 系统概览")
        print("    - 🚦 路由类型管理")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_config_tabs())
    sys.exit(0 if success else 1)
