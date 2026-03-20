#!/usr/bin/env python3
"""
测试 Web 界面修复
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_web_interface():
    """测试Web界面"""
    print("测试 ConfigWebInterface...")

    try:
        from src.core.config_web_interface import ConfigWebInterface

        # 创建一个模拟的配置系统
        class MockConfigSystem:
            def get_routing_config(self):
                return {"thresholds": {"test": 0.5}, "route_types": []}

        config_system = MockConfigSystem()
        web_interface = ConfigWebInterface(config_system, port=8083)

        # 测试创建请求处理器
        handler_class = web_interface._create_request_handler()
        print("✅ 请求处理器创建成功")

        # 测试生成HTML
        html = web_interface._generate_dashboard_html()
        if "动态路由配置管理系统" in html:
            print("✅ HTML生成成功")
        else:
            print("❌ HTML生成失败")
            return False

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_web_interface()
    if success:
        print("\n🎉 Web界面测试通过！")
    else:
        print("\n💥 Web界面测试失败！")
        sys.exit(1)
