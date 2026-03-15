#!/usr/bin/env python3
"""
环境变量工作区 - 在沙箱环境中绕过.env文件访问限制

使用方法：
1. 在沙箱环境运行：
   python diagnostics/env_workaround.py

2. 在生产环境运行：
   python diagnostics/env_workaround.py --production
"""

import os
import sys
import argparse
from pathlib import Path

def setup_sandbox_environment():
    """为沙箱环境设置环境变量"""
    print("🔧 设置沙箱环境变量...")

    # 检查是否已经有环境变量
    if os.getenv('DEEPSEEK_API_KEY'):
        print("✅ DEEPSEEK_API_KEY已设置")
        return

    # 在沙箱环境中，我们可以提示用户输入或使用默认值
    print("⚠️  沙箱环境无法访问.env文件")
    print("请手动设置环境变量，或使用默认配置")

    # 设置默认值用于测试
    os.environ['DEEPSEEK_API_KEY'] = 'sandbox_test_key'
    os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'
    os.environ['JINA_API_KEY'] = ''

    print("✅ 已设置沙箱环境变量")

def setup_production_environment():
    """为生产环境设置环境变量"""
    print("🏭 设置生产环境变量...")

    try:
        # 在生产环境中，尝试正常加载.env文件
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 成功加载.env文件")
    except Exception as e:
        print(f"⚠️  加载.env文件失败: {e}")
        print("请确保.env文件存在且包含必要的配置")

def test_environment():
    """测试环境变量是否正确设置"""
    print("\n🧪 测试环境配置:")

    required_vars = ['DEEPSEEK_API_KEY']
    optional_vars = ['USE_LIGHTWEIGHT_RAG', 'JINA_API_KEY']

    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: 设置 (长度: {len(value)})")
        else:
            print(f"❌ {var}: 未设置")

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"ℹ️  {var}: {value}")
        else:
            print(f"ℹ️  {var}: 未设置")

def main():
    parser = argparse.ArgumentParser(description='环境变量设置工具')
    parser.add_argument('--production', action='store_true',
                       help='使用生产环境配置')
    parser.add_argument('--test', action='store_true',
                       help='测试环境变量配置')

    args = parser.parse_args()

    if args.test:
        test_environment()
        return

    if args.production:
        setup_production_environment()
    else:
        setup_sandbox_environment()

    test_environment()

if __name__ == "__main__":
    main()
