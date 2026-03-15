#!/usr/bin/env python3
"""
RAGExpert优化效果测试脚本

测试内容：
1. 并行检索性能提升
2. 缓存机制效果
3. 整体响应时间优化
"""

import asyncio
import time
import logging
from src.agents.rag_agent import RAGExpert

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rag_expert_performance():
    """测试RAGExpert性能"""
    print("=" * 60)
    print("🚀 RAGExpert性能优化测试")
    print("=" * 60)

    # 初始化RAGExpert
    rag_expert = RAGExpert()

    # 测试查询
    test_queries = [
        "什么是机器学习？",
        "Python中如何实现多线程？",
        "深度学习和机器学习的区别是什么？",
        "什么是机器学习？",  # 重复查询测试缓存
    ]

    results = []

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 测试查询 {i}: {query}")

        # 测试并行检索
        start_time = time.time()
        context = {
            "query": query,
            "use_cache": True,
            "use_parallel": True,
            "max_results": 5
        }

        result = await rag_expert.execute(context)
        execution_time = time.time() - start_time

        print(f"   ⏱️  执行时间: {execution_time:.2f}秒")
        print(f"   📊 证据数量: {len(result.data.get('evidence', [])) if result.success else 0}")
        print(f"   🎯 置信度: {result.confidence:.2f}")

        if result.success and result.data.get('answer'):
            answer_preview = result.data['answer'][:100] + "..." if len(result.data['answer']) > 100 else result.data['answer']
            print(f"   💡 答案预览: {answer_preview}")

        results.append({
            'query': query,
            'success': result.success,
            'time': execution_time,
            'confidence': result.confidence,
            'evidence_count': len(result.data.get('evidence', [])) if result.success else 0,
            'cached': result.metadata.get('cache_used', False) if hasattr(result, 'metadata') else False
        })

    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 性能统计结果")
    print("=" * 60)

    total_time = sum(r['time'] for r in results)
    avg_time = total_time / len(results)
    success_rate = sum(1 for r in results if r['success']) / len(results) * 100
    cached_queries = sum(1 for r in results if r.get('cached', False))

    print(f"总执行时间: {total_time:.2f}秒")
    print(f"平均执行时间: {avg_time:.2f}秒")
    print(f"成功率: {success_rate:.1f}%")
    print(f"缓存命中次数: {cached_queries}")
    print(f"平均置信度: {avg_confidence:.2f}")
    print(f"平均证据数量: {avg_evidence:.1f}")
    # 分析性能提升
    if cached_queries > 0:
        cached_times = [r['time'] for r in results if r.get('cached', False)]
        non_cached_times = [r['time'] for r in results if not r.get('cached', False)]

        if cached_times and non_cached_times:
            avg_cached = sum(cached_times) / len(cached_times)
            avg_non_cached = sum(non_cached_times) / len(non_cached_times)
            speedup = avg_non_cached / avg_cached if avg_cached > 0 else 0
            print(f"缓存加速比: {speedup:.1f}x")

    print("\n✅ 测试完成！")

if __name__ == "__main__":
    asyncio.run(test_rag_expert_performance())
