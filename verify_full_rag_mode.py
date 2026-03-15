#!/usr/bin/env python3
"""
验证完整RAG模式是否启用
"""

import os
import sys
from pathlib import Path

def verify_rag_mode():
    """验证RAG模式状态"""

    print("🔍 验证RAG模式状态")
    print("=" * 50)

    # 检查环境变量
    lightweight_env = os.getenv('USE_LIGHTWEIGHT_RAG')
    print(f"环境变量 USE_LIGHTWEIGHT_RAG: '{lightweight_env}'")

    # 检查.env文件
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
            lightweight_lines = [line for line in content.split('\n') if 'USE_LIGHTWEIGHT_RAG' in line]
            if lightweight_lines:
                print(f"⚠️ .env文件中仍存在配置:")
                for line in lightweight_lines:
                    print(f"   {line}")
            else:
                print("✅ .env文件中未找到USE_LIGHTWEIGHT_RAG配置")

    # 模拟RAGExpert的检查逻辑
    lightweight_mode = os.getenv('USE_LIGHTWEIGHT_RAG', 'false').lower() == 'true'
    print(f"RAGExpert轻量级模式状态: {lightweight_mode}")

    if lightweight_mode:
        print("❌ 仍处于轻量级模式，完整RAG功能未启用")
        print("\n🔧 修复步骤:")
        print("1. 编辑.env文件，移除或注释掉: USE_LIGHTWEIGHT_RAG=true")
        print("2. 或者设置为: USE_LIGHTWEIGHT_RAG=false")
        print("3. 重启Python进程")
        return False
    else:
        print("✅ 轻量级模式已禁用，完整RAG功能已启用")
        print("\n🎯 现在可以测试完整RAG功能，包括:")
        print("   - 实际知识检索")
        print("   - 推理引擎调用")
        print("   - 答案生成和验证")
        return True

if __name__ == "__main__":
    success = verify_rag_mode()
    if success:
        print("\n🚀 可以运行完整RAG测试了！")
    else:
        print("\n⚠️ 请先修复环境变量配置")
