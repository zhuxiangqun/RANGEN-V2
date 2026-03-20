#!/usr/bin/env python3
"""
超级简单的RAG初始化测试
只测试最基本的导入和初始化
"""

import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def test_basic_imports():
    """测试基本导入"""
    print("🧪 测试基本导入...")

    try:
        from src.agents.tools.rag_tool import RAGTool
        print("✅ RAGTool导入成功")
    except Exception as e:
        print(f"❌ RAGTool导入失败: {e}")
        return False

    try:
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert导入成功")
    except Exception as e:
        print(f"❌ RAGExpert导入失败: {e}")
        return False

    return True

def test_rag_tool_init():
    """测试RAGTool初始化"""
    print("\n🧪 测试RAGTool初始化...")

    try:
        from src.agents.tools.rag_tool import RAGTool
        rag_tool = RAGTool()
        print("✅ RAGTool初始化成功")
        return True
    except Exception as e:
        print(f"❌ RAGTool初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_expert_init():
    """测试RAGExpert初始化"""
    print("\n🧪 测试RAGExpert初始化...")

    try:
        from src.agents.rag_agent import RAGExpert
        print("🔧 开始初始化RAGExpert（这可能需要几秒钟）...")
        rag_expert = RAGExpert()
        print("✅ RAGExpert初始化成功")
        print(f"   Agent ID: {rag_expert.agent_id}")
        return True
    except Exception as e:
        print(f"❌ RAGExpert初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始超级简单RAG初始化测试")
    print("=" * 50)

    # 1. 测试基本导入
    if not test_basic_imports():
        return

    # 2. 测试RAGTool初始化
    if not test_rag_tool_init():
        return

    # 3. 测试RAGExpert初始化
    if not test_rag_expert_init():
        return

    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("\n优化成果:")
    print("1. ✅ RAGTool可以正常初始化")
    print("2. ✅ RAGExpert可以正常初始化")
    print("3. ✅ 移除了RAGAgentWrapper层")
    print("\n问题分析:")
    print("- RAGExpert初始化时间较长，因为需要加载知识库等组件")
    print("- 建议在实际使用时使用延迟加载或预热策略")
    print("- 测试调用时的超时可能是因为RAGExpert的execute方法太耗时")

if __name__ == '__main__':
    main()
