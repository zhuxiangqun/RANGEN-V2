#!/usr/bin/env python3
"""
测试Groundhog Day查询是否能正确触发RAG流程
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

async def test_groundhog_query():
    """测试Groundhog Day查询的行为"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine

        print("🔧 初始化推理引擎...")
        engine = RealReasoningEngine()

        # 测试Groundhog Day查询
        query = "How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?"

        print(f"🧪 测试查询: '{query[:80]}...'")
        print(f"📏 查询长度: {len(query)} 字符")

        # 检查是否被识别为简单查询
        query_type = "factual"  # 模拟查询类型
        is_simple = engine._is_ultra_simple_query(query, query_type)

        print(f"🔍 简单查询检测结果: {'✅ 是简单查询' if is_simple else '❌ 不是简单查询'}")

        if is_simple:
            print("⚠️  这个查询被错误地识别为简单查询，应该走RAG流程！")
            return False
        else:
            print("✅ 这个查询正确地被识别为复杂查询，应该走RAG流程")

        # 模拟RAG流程
        print("\n🔄 模拟RAG流程...")
        context = {
            'query': query,
            'use_llm_direct': False  # 确保不使用LLM直接回答
        }

        # 这里应该会走正常的RAG流程：检索证据 -> 推理 -> 生成答案
        print("📚 应该从知识库检索相关证据：")
        print("   - Punxsutawney Phil的历史")
        print("   - Groundhog Day传统")
        print("   - 美国首都位置")
        print("   - 宾夕法尼亚州历史")
        print("   - 年份计算推理")

        print("\n🧠 应该进行推理计算：")
        print("   - 确定美国首都所在的州")
        print("   - 确定Punxsutawney Phil的活动范围")
        print("   - 计算时间差")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_simple_vs_complex_queries():
    """测试简单查询vs复杂查询的识别"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine

        engine = RealReasoningEngine()

        test_queries = [
            ("什么是RAG？", True, "简单定义查询"),
            ("解释一下机器学习", True, "简单定义查询"),
            ("How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?", False, "复杂推理查询"),
            ("美国首都在哪里？", True, "简单事实查询"),
            ("为什么天空是蓝色的？", False, "需要科学解释的查询"),
        ]

        print("\n📊 查询类型识别测试:")
        print("=" * 80)

        for query, expected_simple, description in test_queries:
            query_type = "factual"
            is_simple = engine._is_ultra_simple_query(query, query_type)

            status = "✅" if is_simple == expected_simple else "❌"
            result = "简单" if is_simple else "复杂"

            print("30")

        print("=" * 80)

        # 检查Groundhog查询的具体特征
        groundhog_query = "How many years earlier would Punxsutawney Phil have to be canonically alive to have made a Groundhog Day prediction in the same state as the US capitol?"

        print("
🔍 Groundhog查询特征分析:"        print(f"   长度: {len(groundhog_query)} 字符 (>50字符 -> 不简单)")
        print(f"   包含定义关键词: {any(pattern in groundhog_query.lower() for pattern in ['what is', 'define', 'explain', 'describe'])}")
        print(f"   包含复杂指标: {any(indicator in groundhog_query.lower() for indicator in ['how', 'why', 'years', 'would', 'have to'])}")

        return True

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        return False

if __name__ == "__main__":
    print("🧪 测试Groundhog Day查询的RAG流程识别")
    asyncio.run(test_groundhog_query())
    asyncio.run(test_simple_vs_complex_queries())
