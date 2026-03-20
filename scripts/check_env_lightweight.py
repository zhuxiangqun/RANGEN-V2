#!/usr/bin/env python3
"""
检查轻量级模式环境变量状态
"""

import os
import sys
from pathlib import Path

def check_lightweight_mode():
    """检查轻量级模式状态"""

    print("🔍 检查轻量级模式环境变量状态")
    print("=" * 50)

    # 检查环境变量
    env_var = os.getenv('USE_LIGHTWEIGHT_RAG')
    print(f"环境变量 USE_LIGHTWEIGHT_RAG: {env_var}")

    # 检查.env文件
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            if 'USE_LIGHTWEIGHT_RAG' in content:
                lines = content.split('\n')
                for line in lines:
                    if 'USE_LIGHTWEIGHT_RAG' in line:
                        print(f".env文件中的配置: {line.strip()}")
            else:
                print(".env文件中未找到USE_LIGHTWEIGHT_RAG配置")
    else:
        print(".env文件不存在")

    # 模拟RAGExpert的检查逻辑
    lightweight_mode = os.getenv('USE_LIGHTWEIGHT_RAG', 'false').lower() == 'true'
    print(f"RAGExpert轻量级模式状态: {lightweight_mode}")

    if lightweight_mode:
        print("⚠️  轻量级模式已启用，系统将返回模拟结果")
        print("💡 要启用完整RAG功能，请移除或注释掉USE_LIGHTWEIGHT_RAG=true")
    else:
        print("✅ 轻量级模式已禁用，将使用完整RAG功能")

if __name__ == "__main__":
    check_lightweight_mode()
