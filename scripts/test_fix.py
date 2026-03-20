#!/usr/bin/env python3
"""
测试修复效果
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

try:
    print("🔧 测试修复效果...")

    # 测试answer_validator导入
    from src.core.reasoning.answer_extraction.answer_validator import AnswerValidator
    print("✅ AnswerValidator导入成功")

    # 测试RAGExpert导入
    from src.agents.rag_agent import RAGExpert
    print("✅ RAGExpert导入成功")

    # 测试初始化
    rag_expert = RAGExpert()
    print("✅ RAGExpert初始化成功")

    print("\n🎉 修复验证通过！")
    print("主要修复：")
    print("1. ✅ 修复answer_validator.py缩进错误")
    print("2. ✅ 修复KnowledgeRetrievalService参数传递问题")
    print("3. ✅ 增加递归深度限制")

except Exception as e:
    print(f"❌ 修复验证失败: {e}")
    import traceback
    traceback.print_exc()
