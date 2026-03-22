#!/usr/bin/env python3
"""
测试优化后的路由决策逻辑

验证新的优先级决策树和特征提取是否正确工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.intelligent_router import IntelligentRouter, RouteType

def test_routing_scenarios():
    """测试各种路由场景"""
    router = IntelligentRouter()

    test_cases = [
        # 多智能体场景
        {
            "query": "分析人工智能对医疗行业的冲击，以及政策制定者、企业和个人应该如何应对这一变革？",
            "expected": RouteType.MULTI_AGENT,
            "description": "多问题复杂查询"
        },
        {
            "query": "解释机器学习算法的工作原理，并比较不同算法的时间复杂度。",
            "expected": RouteType.MULTI_AGENT,
            "description": "多任务复杂查询"
        },

        # 推理密集场景
        {
            "query": "为什么重力会随着距离的平方而减弱？请详细解释物理原理。",
            "expected": RouteType.REASONING,
            "description": "解释型推理查询"
        },
        {
            "query": "分析微服务架构的优势和挑战，如何在项目中正确实施？",
            "expected": RouteType.REASONING,
            "description": "分析推理查询"
        },

        # 代码/数学场景
        {
            "query": "写一个Python函数来计算斐波那契数列。",
            "expected": RouteType.COMPLEX,
            "description": "代码编写查询"
        },
        {
            "query": "求解方程 x² + 2x + 1 = 0 的根。",
            "expected": RouteType.COMPLEX,
            "description": "数学计算查询"
        },

        # 比较场景
        {
            "query": "比较不同排序算法的优缺点和适用场景。",
            "expected": RouteType.COMPLEX,
            "description": "比较型查询"
        },

        # 流程场景
        {
            "query": "如何部署一个Django应用程序到生产环境？",
            "expected": RouteType.MEDIUM,
            "description": "流程型查询"
        },

        # 复杂场景
        {
            "query": "详细解释TCP/IP协议的工作原理，包括三次握手和四次挥手的过程。",
            "expected": RouteType.COMPLEX,
            "description": "复杂技术查询"
        },

        # 中等场景
        {
            "query": "什么是容器化技术？Docker和Kubernetes有什么关系？",
            "expected": RouteType.MEDIUM,
            "description": "中等复杂度查询"
        },

        # 简单场景
        {
            "query": "什么是Python？",
            "expected": RouteType.SIMPLE,
            "description": "简单查询"
        },
        {
            "query": "你好",
            "expected": RouteType.SIMPLE,
            "description": "超简单查询"
        }
    ]

    print("🧪 测试优化后的路由决策逻辑")
    print("=" * 60)

    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['description']}")
        print(f"查询: {test_case['query'][:60]}{'...' if len(test_case['query']) > 60 else ''}")

        try:
            # 获取特征用于调试
            features = router.feature_extractor.extract_features(test_case['query'])
            decision = router.route_query(test_case['query'])

            print(f"预期: {test_case['expected'].value}")
            print(f"实际: {decision.route_type.value}")
            print(f"置信度: {decision.confidence:.2f}")
            print(f"推理: {decision.reasoning}")
            print(f"特征: 多查询={features.is_multi_query}({features.num_questions}), 复杂度={features.complexity_score:.2f}, 词数={features.word_count}, 连接词={features.has_connectors}")
            print(f"处理时间: {decision.processing_time:.3f}s")

            is_correct = decision.route_type == test_case['expected']
            status = "✅ 正确" if is_correct else "❌ 错误"
            print(f"结果: {status}")

            results.append({
                'test_id': i,
                'query': test_case['query'][:50],
                'expected': test_case['expected'].value,
                'actual': decision.route_type.value,
                'confidence': decision.confidence,
                'correct': is_correct,
                'processing_time': decision.processing_time
            })

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            results.append({
                'test_id': i,
                'query': test_case['query'][:50],
                'expected': test_case['expected'].value,
                'actual': 'ERROR',
                'confidence': 0.0,
                'correct': False,
                'processing_time': 0.0
            })

    # 统计结果
    print("\n" + "=" * 60)
    print("📊 测试结果统计")

    total_tests = len(results)
    correct_tests = sum(1 for r in results if r['correct'])
    accuracy = correct_tests / total_tests if total_tests > 0 else 0

    print(f"总测试数: {total_tests}")
    print(f"正确预测: {correct_tests}")
    print(f"准确率: {accuracy:.2%}")

    # 按路由类型统计
    route_stats = {}
    for result in results:
        route_type = result['expected']
        if route_type not in route_stats:
            route_stats[route_type] = {'total': 0, 'correct': 0}
        route_stats[route_type]['total'] += 1
        if result['correct']:
            route_stats[route_type]['correct'] += 1

    print("\n📈 按路由类型统计:")
    for route_type, stats in route_stats.items():
        type_accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        print(f"  {route_type}: {stats['correct']}/{stats['total']} ({type_accuracy:.1%})")

    # 性能统计
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    avg_processing_time = sum(r['processing_time'] for r in results) / len(results)

    print("\n⚡ 性能指标:")
    print(f"   平均置信度: {avg_confidence:.2f}")
    print(f"   平均处理时间: {avg_processing_time:.4f}s")
    # 详细分析错误案例
    incorrect_cases = [r for r in results if not r['correct']]
    if incorrect_cases:
        print(f"\n🔍 错误案例分析 ({len(incorrect_cases)}个):")
        for case in incorrect_cases:
            print(f"  测试{case['test_id']}: 预期{case['expected']} -> 实际{case['actual']}")

    return accuracy >= 0.85  # 85%作为通过标准

def test_feature_extraction():
    """测试特征提取功能"""
    print("\n" + "=" * 60)
    print("🔍 测试特征提取功能")

    router = IntelligentRouter()
    test_queries = [
        "什么是机器学习？",
        "解释神经网络的工作原理，并比较CNN和RNN的区别。",
        "写一个Python函数来排序数组。",
        "分析气候变化的影响以及应对策略。"
    ]

    for query in test_queries:
        print(f"\n查询: {query}")
        features = router.feature_extractor.extract_features(query)

        print(f"  多查询: {features.is_multi_query} ({features.num_questions}个问题)")
        print(f"  连接词: {features.has_connectors}")
        print(f"  查询类型: {features.query_type}")
        print(f"  复杂度: {features.complexity_score:.2f}")
        print(f"  词数: {features.word_count}")
        print(f"  句子结构: {features.sentence_structure}")
        print(f"  置信度: {features.confidence:.2f}")

def main():
    """主函数"""
    try:
        print("🚀 开始测试优化后的路由决策逻辑")

        # 测试路由决策
        routing_passed = test_routing_scenarios()

        # 测试特征提取
        test_feature_extraction()

        print("\n" + "=" * 60)
        if routing_passed:
            print("✅ 路由决策测试通过！")
            return 0
        else:
            print("❌ 路由决策测试未达到预期准确率")
            return 1

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
