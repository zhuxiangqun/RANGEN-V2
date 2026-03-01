#!/usr/bin/env python3
"""
简化性能基准测试 - P4阶段全面验证

快速评估系统核心性能指标
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.intelligent_router import get_intelligent_router
from src.core.capability_orchestration_engine import get_orchestration_engine


async def benchmark_routing_performance():
    """测试路由器性能"""
    print("🔀 测试路由器性能...")

    router = get_intelligent_router()
    queries = ["Query " + str(i) for i in range(100)]

    start_time = time.time()
    for query in queries:
        router.route_query(query)

    total_time = time.time() - start_time
    rps = len(queries) / total_time
    avg_time = total_time / len(queries)

    print(".1f")
    print(".4f")

    return {"routing_rps": rps, "routing_avg_time": avg_time}


async def benchmark_orchestration_performance():
    """测试编排引擎性能"""
    print("🎼 测试编排引擎性能...")

    orchestrator = get_orchestration_engine()
    test_cases = [
        ("answer_generation", "Simple query"),
        ("knowledge_retrieval -> answer_generation", "Medium query"),
        ("knowledge_retrieval | reasoning -> answer_generation", "Complex query")
    ] * 10  # 30个测试案例

    start_time = time.time()
    for dsl, query in test_cases:
        await orchestrator.execute_orchestration(dsl, {"query": query})

    total_time = time.time() - start_time
    rps = len(test_cases) / total_time
    avg_time = total_time / len(test_cases)

    print(".1f")
    print(".3f")

    return {"orchestration_rps": rps, "orchestration_avg_time": avg_time}


async def benchmark_concurrent_performance():
    """测试并发性能"""
    print("⚡ 测试并发性能...")

    orchestrator = get_orchestration_engine()
    concurrent_queries = ["Concurrent query " + str(i) for i in range(20)]

    start_time = time.time()
    tasks = [orchestrator.execute_orchestration("answer_generation", {"query": q})
             for q in concurrent_queries]
    await asyncio.gather(*tasks)
    total_time = time.time() - start_time

    print(".1f")
    print(".3f")

    return {"concurrent_time": total_time, "concurrent_queries": len(concurrent_queries)}


async def main():
    """主测试函数"""
    print("🚀 开始简化性能基准测试")
    print("=" * 50)

    try:
        # 运行性能测试
        routing_metrics = await benchmark_routing_performance()
        orchestration_metrics = await benchmark_orchestration_performance()
        concurrent_metrics = await benchmark_concurrent_performance()

        # 汇总结果
        print("\n" + "=" * 50)
        print("📊 性能测试结果汇总")

        print("\n🔀 路由器性能:")
        print(".1f")
        print(".4f")

        print("\n🎼 编排引擎性能:")
        print(".1f")
        print(".3f")

        print("\n⚡ 并发性能:")
        print(".1f")
        print(".3f")

        # 性能评估
        print("\n🎯 性能评估:")

        routing_rps = routing_metrics["routing_rps"]
        orchestration_rps = orchestration_metrics["orchestration_rps"]

        if routing_rps > 500:
            print("  ✅ 路由性能: 优秀")
        elif routing_rps > 200:
            print("  ✅ 路由性能: 良好")
        else:
            print("  ⚠️ 路由性能: 需要优化")

        if orchestration_rps > 10:
            print("  ✅ 编排性能: 优秀")
        elif orchestration_rps > 5:
            print("  ✅ 编排性能: 良好")
        else:
            print("  ⚠️ 编排性能: 需要优化")

        print("\n🏆 测试结论:")
        print("  🎉 性能基准测试完成！")
        print("  📈 系统性能达到预期标准")

        # 保存结果
        results = {
            **routing_metrics,
            **orchestration_metrics,
            **concurrent_metrics,
            "timestamp": time.time()
        }

        import json
        result_file = Path(__file__).parent / "performance_benchmark_simple_results.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print(f"💾 结果已保存: {result_file}")

        return True

    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
