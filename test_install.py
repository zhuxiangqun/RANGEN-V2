#!/usr/bin/env python3
"""
测试包安装的脚本
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n🔧 {description}")
    print(f"命令: {cmd}")
    print("-" * 50)

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)

        if result.returncode == 0:
            print("✅ 成功!")
            if result.stdout.strip():
                # 只显示最后几行输出
                lines = result.stdout.strip().split('\n')
                if len(lines) > 10:
                    print("输出 (最后10行):")
                    for line in lines[-10:]:
                        print(f"  {line}")
                else:
                    print("输出:")
                    for line in lines:
                        print(f"  {line}")
        else:
            print("❌ 失败!")
            if result.stderr.strip():
                print("错误信息:")
                for line in result.stderr.strip().split('\n')[-10:]:  # 只显示最后10行错误
                    print(f"  {line}")

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("❌ 超时!")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False

def test_import(package_name):
    """测试包导入"""
    try:
        __import__(package_name)
        print(f"✅ {package_name}: 导入成功")
        return True
    except ImportError as e:
        print(f"❌ {package_name}: 导入失败 - {e}")
        return False

def main():
    print("🚀 RANGEN 依赖安装测试")
    print("=" * 50)

    # 显示当前Python环境
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    print(f"工作目录: {os.getcwd()}")

    # 检查pip
    print("\n📦 检查pip...")
    run_command("which pip3", "查找pip3")
    run_command("pip3 --version", "pip版本")

    # 尝试安装一个简单的包进行测试
    print("\n🧪 测试安装simple包...")
    if run_command("pip3 install requests", "安装requests测试包"):
        if test_import("requests"):
            print("🎉 pip安装工作正常!")
        else:
            print("⚠️ pip安装可能有问题")
    else:
        print("❌ pip安装完全失败")

    # 显示安装建议
    print("\n💡 安装建议:")
    print("1. 使用国内镜像:")
    print("   pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple fastapi uvicorn python-dotenv langgraph")
    print()
    print("2. 如果权限问题:")
    print("   pip3 install --user fastapi uvicorn python-dotenv langgraph")
    print()
    print("3. 强制重新安装:")
    print("   pip3 install --force-reinstall fastapi uvicorn python-dotenv langgraph")
    print()
    print("4. 检查pip指向的Python:")
    print("   pip3 show pip")
    print("   python3 -c \"import sys; print(sys.executable)\"")

if __name__ == "__main__":
    main()
