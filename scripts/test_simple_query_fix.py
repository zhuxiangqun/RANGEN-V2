#!/usr/bin/env python3
"""
测试简单查询修复
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载.env文件')
except ImportError:
    print('⚠️ python-dotenv未安装')

async def test_simple_query():
    """测试简单查询是否被正确识别和处理"""
    from src.core.reasoning.engine import RealReasoningEngine

    engine = RealReasoningEngine()

    # 测试简单查询
    test_queries = [
        "什么是RAG？",
        "什么是人工智能？",
        "解释一下机器学习",
        "RAG是什么？"  # 英文查询
    ]

    print("🧪 测试简单查询识别:")
    for query in test_queries:
        query_type = "definition"  # 模拟查询类型
        is_simple = engine._is_ultra_simple_query(query, query_type)
        print(f"  '{query}' -> {'✅ 简单查询' if is_simple else '❌ 复杂查询'}")

    print("\n⚡ 测试简单查询处理:")
    # 测试一个简单查询的完整处理
    try:
        result = await asyncio.wait_for(
            engine.reason(query="什么是RAG？", context={}),
            timeout=15.0
        )
        print("✅ 简单查询处理成功"        print(f"   推理类型: {result.reasoning_type}")
        print(f"   步骤数量: {len(result.reasoning_steps)}")
        print(f"   处理时间: {result.processing_time:.2f}秒")
    except Exception as e:
        print(f"❌ 简单查询处理失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_query())
