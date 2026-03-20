#!/usr/bin/env python3
"""
RANGEN 环境诊断脚本
检查Python环境、依赖包和系统配置
"""

import sys
import os
import platform
import subprocess

def check_python_version():
    """检查Python版本"""
    print("🐍 Python 环境检查")
    print("=" * 40)
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"平台: {platform.platform()}")

    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python版本兼容 (需要 3.8+)")
    else:
        print(f"❌ Python版本过低 (需要 3.8+, 当前 {version.major}.{version.minor})")
    print()

def check_dependencies():
    """检查依赖包"""
    print("📦 依赖包检查")
    print("=" * 40)

    dependencies = {
        'fastapi': 'Web框架',
        'uvicorn': 'ASGI服务器',
        'python-dotenv': '环境变量管理',
        'langgraph': '工作流引擎',
        'httpx': 'HTTP客户端'
    }

    # 特殊处理的包（可能有权限问题）
    special_deps = {
        'torch': '机器学习框架',
        'transformers': 'AI模型库'
    }

    all_good = True
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package}: 已安装 ({description})")
        except ImportError:
            print(f"❌ {package}: 未安装 ({description})")
            all_good = False

    # 检查特殊包
    for package, description in special_deps.items():
        try:
            __import__(package)
            print(f"✅ {package}: 已安装 ({description})")
        except ImportError:
            print(f"❌ {package}: 未安装 ({description})")
        except Exception as e:
            print(f"⚠️  {package}: 安装但有问题 ({description}) - {str(e)[:50]}...")

    if all_good:
        print("\n🎉 所有核心依赖都已安装！")
    else:
        print("\n⚠️  缺少必要依赖，请运行:")
        print("   pip install -r requirements.txt")
    print()

def check_files():
    """检查项目文件"""
    print("📁 项目文件检查")
    print("=" * 40)

    required_files = [
        'scripts/start_unified_server.py',
        'src/visualization/browser_server.py',
        'requirements.txt'
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}: 存在")
        else:
            print(f"❌ {file_path}: 不存在")

    # 检查可执行权限
    script_path = 'start_server.sh'
    if os.path.exists(script_path):
        if os.access(script_path, os.X_OK):
            print(f"✅ {script_path}: 可执行")
        else:
            print(f"⚠️  {script_path}: 存在但不可执行")
            print(f"   运行: chmod +x {script_path}")
    print()

def check_network():
    """检查网络和端口"""
    print("🌐 网络和端口检查")
    print("=" * 40)

    # 检查端口占用
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', 8080))
        sock.close()

        if result == 0:
            print("⚠️  端口8080: 已被占用")
        else:
            print("✅ 端口8080: 可用")
    except Exception as e:
        print(f"❌ 端口检查失败: {e}")

    print()

def check_environment_variables():
    """检查环境变量"""
    print("🔧 环境变量检查")
    print("=" * 40)

    env_vars = ['DEEPSEEK_API_KEY', 'VISUALIZATION_PORT']

    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var == 'DEEPSEEK_API_KEY':
                print(f"✅ {var}: 已设置 (长度: {len(value)})")
            else:
                print(f"✅ {var}: {value}")
        else:
            if var == 'DEEPSEEK_API_KEY':
                print(f"⚠️  {var}: 未设置 (可选，用于AI功能)")
            else:
                print(f"ℹ️  {var}: 未设置 (使用默认值)")

    # 检查.env文件
    if os.path.exists('.env'):
        print("✅ .env文件: 存在")
    else:
        print("ℹ️  .env文件: 不存在 (可选)")
    print()

def main():
    """主函数"""
    print("🔍 RANGEN 环境诊断")
    print("=" * 50)
    print()

    check_python_version()
    check_dependencies()
    check_files()
    check_network()
    check_environment_variables()

    print("📋 诊断完成！")
    print("=" * 50)
    print()
    print("🚀 下一步:")
    print("1. 安装缺失的依赖: pip install -r requirements.txt")
    print("2. 启动服务器: ./start_server.sh")
    print("3. 访问: http://localhost:8080/visualization/")

if __name__ == "__main__":
    main()
