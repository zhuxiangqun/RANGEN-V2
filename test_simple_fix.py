#!/usr/bin/env python3
"""
简单测试修复效果
"""

import sys
import os
from pathlib import Path

# 修复1: 增加递归深度限制
sys.setrecursionlimit(2000)

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 确保移除轻量级模式
if 'USE_LIGHTWEIGHT_RAG' in os.environ:
    del os.environ['USE_LIGHTWEIGHT_RAG']
os.environ['USE_NEW_AGENTS'] = 'true'

async def test_imports():
    """测试导入是否正常"""
    try:
        print("🔧 测试导入...")

        # 测试answer_validator导入
        from src.core.reasoning.answer_extraction.answer_validator import AnswerValidator
        print("✅ AnswerValidator导入成功")

        # 测试RAGExpert导入
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert导入成功")

        # 测试KnowledgeRetrievalService导入
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        print("✅ KnowledgeRetrievalService导入成功")

        print("\n🎉 所有导入测试通过！")
        return True

    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

import asyncio
success = asyncio.run(test_imports())
print(f"结果: {'✅ 通过' if success else '❌ 失败'}")
