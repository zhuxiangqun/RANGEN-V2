#!/usr/bin/env python3
"""
快速诊断脚本 - 检查RAGExpert的基本问题
"""

import os
import sys
import asyncio
from pathlib import Path

# 设置环境
if 'USE_LIGHTWEIGHT_RAG' in os.environ:
    del os.environ['USE_LIGHTWEIGHT_RAG']
os.environ['USE_NEW_AGENTS'] = 'true'

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def quick_check():
    """快速检查RAGExpert问题"""

    print("🔍 快速诊断RAGExpert问题")
    print("=" * 50)

    try:
        # 1. 检查导入
        print("📦 检查导入...")
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert导入成功")

        # 2. 检查初始化
        print("🏗️ 检查初始化...")
        rag_expert = RAGExpert()
        print("✅ RAGExpert初始化成功")

        # 3. 检查模式
        lightweight = getattr(rag_expert, '_lightweight_mode', None)
        print(f"轻量级模式: {lightweight}")

        if lightweight:
            print("❌ 仍在使用轻量级模式！")
            return False

        # 4. 简单执行测试
        print("🧪 简单执行测试...")
        context = {"query": "Hello"}
        result = await rag_expert.execute(context)

        if result.success:
            print("✅ 执行成功")
            return True
        else:
            print(f"❌ 执行失败: {result.error}")
            return False

    except Exception as e:
        print(f"❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(quick_check())
    print(f"\n结果: {'✅ 通过' if success else '❌ 失败'}")
