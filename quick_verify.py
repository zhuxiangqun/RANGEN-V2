#!/usr/bin/env python3
"""
快速验证修复效果
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

async def verify():
    try:
        from src.agents.rag_agent import RAGExpert
        rag_expert = RAGExpert()
        lightweight = getattr(rag_expert, '_lightweight_mode', False)
        print(f"✅ RAGExpert初始化成功，轻量级模式: {lightweight}")
        return not lightweight
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False

import asyncio
success = asyncio.run(verify())
print(f"结果: {'✅ 通过' if success else '❌ 失败'}")
