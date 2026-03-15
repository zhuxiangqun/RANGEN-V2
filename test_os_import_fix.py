#!/usr/bin/env python3
"""
测试os导入修复
"""

import os
import sys
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 设置轻量级模式
os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'

def test_rag_expert_import():
    """测试RAGExpert导入"""
    try:
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert导入成功")
        return True
    except Exception as e:
        print(f"❌ RAGExpert导入失败: {e}")
        return False

def test_rag_expert_init():
    """测试RAGExpert初始化"""
    try:
        from src.agents.rag_agent import RAGExpert
        print("🔧 初始化RAGExpert...")
        rag_expert = RAGExpert()
        print("✅ RAGExpert初始化成功")
        print(f"   轻量级模式: {rag_expert._lightweight_mode}")
        return True
    except Exception as e:
        print(f"❌ RAGExpert初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🧪 测试os导入修复")
    print("=" * 30)

    # 1. 测试导入
    if not test_rag_expert_import():
        return

    # 2. 测试初始化
    if not test_rag_expert_init():
        return

    print("\n✅ 所有测试通过！os导入问题已修复")

if __name__ == '__main__':
    main()
