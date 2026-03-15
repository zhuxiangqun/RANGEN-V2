#!/usr/bin/env python3
"""
ReasoningExpert优化效果测试脚本

测试内容：
1. 并行推理引擎性能提升
2. 推理结果缓存效果
3. 自适应推理策略选择
4. 复杂度分析准确性
"""

import asyncio
import time
import logging
from src.agents.reasoning_expert import ReasoningExpert, ReasoningComplexity

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_reasoning_expert():
    """测试ReasoningExpert功能"""
    print("=" * 60)
    print("🧠 ReasoningExpert并行推理测试")
    print("=" * 60)

    # 初始化推理专家
    reasoning_expert = ReasoningExpert()

    # 测试查询 - 不同复杂度级别
    test_queries = [
        # 简单推理
        {
            "query": "2 + 2 等于多少？",
            "expected_complexity": ReasoningComplexity.SIMPLE,
            "description": "简单数学计算"
        },
        # 中等推理
        {
            "query": "如果今天是星期三，那么后天是星期几？",
            "expected_complexity": ReasoningComplexity.MODERATE,
            "description": "逻辑推理"
        },
        # 复杂推理
        {
            "query": "为什么天空是蓝色的？请解释光的散射原理。",
            "expected_complexity": ReasoningComplexity.COMPLEX,
            "description": "科学解释推理"
        },
        # 高级推理
        {
            "query": "分析气候变化对全球经济的影响，并提出应对策略。",
            "expected_complexity": ReasoningComplexity.ADVANCED,
            "description": "复杂系统分析"
        },
        # 重复查询测试缓存
        {
            "query": "2 + 2 等于多少？",
            "expected_complexity": ReasoningComplexity.SIMPLE,
            "description": "缓存测试 - 重复查询"
        }
    ]

    results = []

    for i, test_case in enumerate(test_queries, 1):
        print(f"\n🧪 测试案例 {i}: {test_case['description']}")
        print(f"   查询: {test_case['query']}")
        print(f"   期望复杂度: {test_case['expected_complexity'].value}")

        start_time = time.time()
        context = {
            "query": test_case['query'],
            "use_cache": True,
            "max_parallel_paths": 3
        }

        result = await reasoning_expert.execute(context)
        execution_time = time.time() - start_time

        print(f"   ⏱️  执行时间: {execution_time:.2f}秒")
        print(f"   📊 置信度: {result.confidence:.2f}")

        if result.success and result.data:
            reasoning_type = result.metadata.get('reasoning_type', 'unknown')
            complexity = result.metadata.get('complexity', 'unknown')
            parallel_paths = result.metadata.get('parallel_paths', 1)

            print(f"   🎯 推理类型: {reasoning_type}")
            print(f"   📈 检测复杂度: {complexity}")
            print(f"   🔄 并行路径: {parallel_paths}")

            # 复杂度匹配检查
            complexity_matched = complexity == test_case['expected_complexity'].value
            print(f"   ✅ 复杂度匹配: {'是' if complexity_matched else '否'}")

            if result.data.get('reasoning'):
                reasoning_preview = result.data['reasoning'][:100] + "..." if len(result.data['reasoning']) > 100 else result.data['reasoning']
                print(f"   💭 推理过程: {reasoning_preview}")

        else:
            print(f"   ❌ 推理失败: {result.error}")

        results.append({
            'query': test_case['query'],
            'description': test_case['description'],
            'success': result.success,
            'time': execution_time,
            'confidence': result.confidence,
            'reasoning_type': result.metadata.get('reasoning_type', 'unknown') if result.metadata else 'unknown',
            'detected_complexity': result.metadata.get('complexity', 'unknown') if result.metadata else 'unknown',
            'expected_complexity': test_case['expected_complexity'].value,
            'parallel_paths': result.metadata.get('parallel_paths', 1) if result.metadata else 1,
            'complexity_matched': (result.metadata.get('complexity', 'unknown') if result.metadata else 'unknown') == test_case['expected_complexity'].value
        })

    # 输出统计结果
    print("\n" + "=" * 60)
    print("📊 推理性能统计")
    print("=" * 60)

    total_time = sum(r['time'] for r in results)
    avg_time = total_time / len(results)
    success_rate = sum(1 for r in results if r['success']) / len(results) * 100
    avg_confidence = sum(r['confidence'] for r in results if r['success']) / max(len([r for r in results if r['success']]), 1)

    # 复杂度分析准确率
    complexity_matches = sum(1 for r in results if r.get('complexity_matched', False))
    complexity_accuracy = complexity_matches / len(results) * 100

    print(f"总执行时间: {total_time:.2f}秒")
    print(f"平均执行时间: {avg_time:.2f}秒")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均置信度: {avg_confidence:.2f}")
    print(f"复杂度分析准确率: {complexity_accuracy:.1f}%")
    # 并行推理统计
    total_parallel_paths = sum(r.get('parallel_paths', 1) for r in results)
    avg_parallel_paths = total_parallel_paths / len(results)

    # 推理类型分布
    reasoning_types = {}
    for r in results:
        rt = r.get('reasoning_type', 'unknown')
        reasoning_types[rt] = reasoning_types.get(rt, 0) + 1

    print(f"平均并行路径数: {avg_parallel_paths:.1f}")
    print("   推理类型分布:")
    for rt, count in reasoning_types.items():
        print(f"     - {rt}: {count} 次")

    # 获取专家统计
    expert_stats = reasoning_expert.get_stats()
    print("\n🧠 专家内部统计:")
    print(f"   处理任务数: {expert_stats['tasks_processed']}")
    print(f"   缓存命中数: {expert_stats['cache_hits']}")
    print(f"   并行执行数: {expert_stats['parallel_executions']}")
    print(f"   平均推理时间: {expert_stats['avg_reasoning_time']:.2f}秒")
    print(f"   缓存命中率: {expert_stats['cache_hit_rate']:.2f}")
    print(f"   当前缓存大小: {expert_stats['cache_size']}")
    print(f"   活跃任务数: {expert_stats['active_tasks']}")

    # 复杂度分布
    if 'complexity_distribution' in expert_stats:
        print("   复杂度分布:")
        for comp, count in expert_stats['complexity_distribution'].items():
            print(f"     - {comp}: {count} 次")

    print("\n✅ ReasoningExpert测试完成！")

    # 关闭专家
    reasoning_expert.shutdown()

if __name__ == "__main__":
    asyncio.run(test_reasoning_expert())
