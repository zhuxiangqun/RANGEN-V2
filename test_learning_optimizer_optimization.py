#!/usr/bin/env python3
"""
LearningOptimizer优化效果测试脚本

测试内容：
1. 增量学习算法效果
2. 性能模式识别功能
3. A/B测试自动化
4. 自适应优化策略
"""

import asyncio
import time
import logging
from src.agents.learning_optimizer import LearningOptimizer, LearningMode, OptimizationTarget

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_learning_optimizer():
    """测试LearningOptimizer功能"""
    print("=" * 60)
    print("🧠 LearningOptimizer学习优化测试")
    print("=" * 60)

    # 初始化学习优化器
    optimizer = LearningOptimizer()

    # 注册测试学习模型
    print("\n📝 注册测试学习模型...")
    result = await optimizer.execute({
        "action": "register_model",
        "model_name": "RAG检索优化模型",
        "parameters": {
            "learning_rate": 0.01,
            "top_k": 15,
            "similarity_threshold": 0.7,
            "use_rerank": True
        },
        "learning_mode": "incremental"
    })

    if result.success:
        model_id = result.data["model_id"]
        print(f"✅ 学习模型已注册: {model_id}")

        # 测试增量学习
        print("\n🔄 测试增量学习...")
        learning_data = [
            {
                "performance_feedback": {"learning_rate": 0.1, "top_k": -0.05},
                "before_metrics": {"accuracy": 0.85, "response_time": 2.1},
                "after_metrics": {"accuracy": 0.87, "response_time": 2.0}
            },
            {
                "performance_feedback": {"similarity_threshold": 0.08, "use_rerank": 0.02},
                "before_metrics": {"accuracy": 0.87, "response_time": 2.0},
                "after_metrics": {"accuracy": 0.89, "response_time": 1.9}
            },
            {
                "performance_feedback": {"learning_rate": -0.05, "top_k": 0.03},
                "before_metrics": {"accuracy": 0.89, "response_time": 1.9},
                "after_metrics": {"accuracy": 0.88, "response_time": 1.85}
            }
        ]

        learning_result = await optimizer.execute({
            "action": "incremental_learning",
            "model_id": model_id,
            "new_data": learning_data
        })

        if learning_result.success:
            learning_data = learning_result.data
            print(f"   ✅ 增量学习成功: 更新参数={learning_data['updates_applied']}")
            print(f"   📈 平均改进: {learning_data['average_improvement']:.4f}")
            print(f"   ⏱️ 执行时间: {learning_data['execution_time']:.2f}秒")
        else:
            print(f"   ❌ 增量学习失败: {learning_result.error}")

    # 测试性能模式识别
    print("\n🎯 测试性能模式识别...")
    performance_data = [
        {"response_time": 1.8, "throughput": 45.2, "error_rate": 0.02, "memory_usage": 0.75, "timestamp": time.time()},
        {"response_time": 2.1, "throughput": 42.1, "error_rate": 0.03, "memory_usage": 0.78, "timestamp": time.time() + 60},
        {"response_time": 2.5, "throughput": 38.9, "error_rate": 0.05, "memory_usage": 0.82, "timestamp": time.time() + 120},
        {"response_time": 2.8, "throughput": 35.7, "error_rate": 0.07, "memory_usage": 0.85, "timestamp": time.time() + 180},
        {"response_time": 3.2, "throughput": 32.1, "error_rate": 0.09, "memory_usage": 0.88, "timestamp": time.time() + 240},
        {"response_time": 3.5, "throughput": 29.8, "error_rate": 0.11, "memory_usage": 0.91, "timestamp": time.time() + 300},
    ]

    pattern_result = await optimizer.execute({
        "action": "detect_patterns",
        "performance_data": performance_data
    })

    if pattern_result.success:
        patterns = pattern_result.data.get("detected_patterns", [])
        print(f"   ✅ 检测到 {len(patterns)} 个性能模式:")

        for pattern in patterns:
            print(f"     🎯 {pattern['pattern_name']} (置信度: {pattern['confidence']:.2f})")
            if pattern.get('recommendations'):
                print(f"        💡 建议: {pattern['recommendations'][0]}")
    else:
        print(f"   ❌ 模式识别失败: {pattern_result.error}")

    # 测试A/B测试
    print("\n🧪 测试A/B测试自动化...")
    ab_test_variants = {
        "baseline": {"learning_rate": 0.01, "top_k": 15},
        "variant_a": {"learning_rate": 0.02, "top_k": 15},
        "variant_b": {"learning_rate": 0.01, "top_k": 20}
    }

    ab_result = await optimizer.execute({
        "action": "create_ab_test",
        "test_name": "检索参数优化测试",
        "description": "测试不同的学习率和top_k参数组合",
        "variants": ab_test_variants,
        "target_metric": "accuracy",
        "baseline_variant": "baseline"
    })

    if ab_result.success:
        test_id = ab_result.data["test_id"]
        print(f"✅ A/B测试已创建: {test_id}")

        # 运行A/B测试
        run_result = await optimizer.execute({
            "action": "run_ab_test",
            "test_id": test_id,
            "sample_size": 50
        })

        if run_result.success:
            test_data = run_result.data
            print(f"   🏆 测试完成: 获胜变体={test_data['winner']}")
            print(f"   📊 置信度: {test_data['confidence']:.2f}")
            print(f"   ⏱️ 执行时间: {test_data['execution_time']:.2f}秒")
        else:
            print(f"   ❌ A/B测试运行失败: {run_result.error}")

    # 测试自适应优化
    print("\n🔧 测试自适应优化...")
    extended_performance_data = performance_data + [
        {"response_time": 3.8, "throughput": 27.3, "error_rate": 0.13, "memory_usage": 0.94, "overall_performance": 0.72},
        {"response_time": 4.1, "throughput": 25.1, "error_rate": 0.15, "memory_usage": 0.96, "overall_performance": 0.68},
    ]

    adaptive_result = await optimizer.execute({
        "action": "adaptive_optimization",
        "performance_data": extended_performance_data
    })

    if adaptive_result.success:
        adaptive_data = adaptive_result.data
        print(f"   ✅ 自适应优化完成:")
        print(f"     🎯 检测模式数: {adaptive_data['patterns_detected']}")
        print(f"     💡 生成建议数: {adaptive_data['recommendations_generated']}")
        print(f"     🔧 应用优化数: {adaptive_data['optimizations_applied']}")
        print(".3f")

    # 获取统计信息
    print("\n📊 学习优化统计:")
    stats_result = await optimizer.execute({"action": "stats"})

    if stats_result.success:
        stats = stats_result.data
        print(f"   🧠 注册模型数: {stats['registered_models']}")
        print(f"   🎯 活动模式数: {stats['active_patterns']}")
        print(f"   🧪 运行中A/B测试: {stats['running_ab_tests']}")
        print(f"   📈 完成A/B测试数: {stats['ab_tests_completed']}")
        print(f"   💾 缓存大小: {stats['cache_size']}")
        print(f"   📊 当前学习率: {stats['current_learning_rate']:.4f}")
        print(f"   📈 性能历史大小: {stats['performance_history_size']}")

    # 等待优化线程执行
    print("\n⏳ 等待自动优化...")
    await asyncio.sleep(2)

    # 关闭学习优化器
    optimizer.shutdown()

    print("\n✅ LearningOptimizer测试完成！")

if __name__ == "__main__":
    asyncio.run(test_learning_optimizer())
