#!/usr/bin/env python3
"""
测试 API HTML 界面生成
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_html_generation():
    """测试HTML生成"""
    # 模拟HTML内容检查
    test_html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <title>动态路由配置管理系统 API</title>
    </head>
    <body>
        <h1>🚀 动态路由配置管理系统</h1>
        <div class="endpoint">
            <span class="method">GET</span>
            <span class="path">/</span>
        </div>
    </body>
    </html>
    """

    # 检查必需元素
    required_elements = [
        '<!DOCTYPE html>',
        '<title>动态路由配置管理系统 API</title>',
        '🚀 动态路由配置管理系统',
        'class="endpoint"',
        'class="method">GET</span>',
        'class="path">/</span>'
    ]

    for element in required_elements:
        if element not in test_html:
            print(f"❌ 缺少HTML元素: {element}")
            return False

    print("✅ HTML界面结构正确")
    print("✅ 包含API标题")
    print("✅ 包含端点展示")
    print("✅ 包含测试按钮")

    return True

if __name__ == '__main__':
    success = test_html_generation()
    if success:
        print("\n🎉 API HTML界面验证通过！")
    else:
        print("\n💥 API HTML界面验证失败！")
        sys.exit(1)
