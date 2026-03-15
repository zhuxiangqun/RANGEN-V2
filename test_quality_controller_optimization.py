#!/usr/bin/env python3
"""
QualityController优化效果测试脚本

测试内容：
1. 多维度评估算法
2. 自动化验证流程
3. 错误检测与纠正
4. 质量监控与预警
"""

import asyncio
import time
import logging
from src.agents.quality_controller import QualityController, ValidationLevel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_quality_controller():
    """测试QualityController功能"""
    print("=" * 60)
    print("🔍 QualityController质量控制测试")
    print("=" * 60)

    # 初始化质量控制器
    controller = QualityController()

    # 测试内容样例
    test_contents = [
        {
            "content": "Python是一种高级编程语言，由Guido van Rossum在1991年创建。它具有简洁明了的语法，支持面向对象编程。Python在数据科学和机器学习领域非常流行。",
            "content_type": "general",
            "description": "高质量技术介绍"
        },
        {
            "content": "水在100度沸腾。这是一个基本事实。太阳绕地球转是错误的说法。天空有时候是蓝色的，但并不总是这样。",
            "content_type": "general",
            "description": "包含事实错误的内容"
        },
        {
            "content": "这是一个非常简短的回答。没有提供足够的详细信息。用户可能需要更多解释。",
            "content_type": "general",
            "description": "内容不完整的回答"
        },
        {
            "content": "这个问题很复杂，需要详细分析。首先我们要考虑各个方面，然后做出决定。但是我们总是可以找到解决方案，即使有时候看起来很困难。",
            "content_type": "general",
            "description": "逻辑存在矛盾的内容"
        }
    ]

    # 测试多维度评估
    print("\n📊 测试多维度评估...")
    assessment_results = []

    for content_data in test_contents:
        print(f"\n   评估内容: {content_data['description']}")

        start_time = time.time()
        assessment = await controller.assess_quality(
            content_data["content"],
            validation_level=ValidationLevel.COMPREHENSIVE
        )
        execution_time = time.time() - start_time

        print(f"   ✅ 综合评分: {assessment.overall_score:.1f}/100")
        print(f"   ⏱️ 评估耗时: {execution_time:.3f}秒")
        print(f"   🎯 评估维度: {len(assessment.dimension_scores)} 个")
        print(f"   ⚠️  检测问题: {len(assessment.detected_issues)} 个")

        # 显示各维度评分
        for dim, score in assessment.dimension_scores.items():
            status = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
            print(f"     {status} {dim}: {score:.1f}")

        # 显示检测到的问题
        if assessment.detected_issues:
            print("     发现的问题:")
            for issue in assessment.detected_issues[:3]:  # 最多显示3个
                severity = issue.get('severity', 'minor')
                issue_type = issue.get('type', 'unknown')
                desc = issue.get('description', '')[:60]
                print(f"       - [{severity}] {issue_type}: {desc}...")

        # 显示改进建议
        if assessment.recommendations:
            print("     💡 改进建议:")
            for rec in assessment.recommendations[:2]:  # 最多显示2条
                print(f"       - {rec}")

        assessment_results.append({
            'content': content_data['content'],
            'description': content_data['description'],
            'overall_score': assessment.overall_score,
            'dimension_count': len(assessment.dimension_scores),
            'issues_count': len(assessment.detected_issues),
            'time': execution_time
        })

    # 测试自动化验证
    print("\n🔍 测试自动化验证...")
    validation_results = []

    for content_data in test_contents:
        print(f"\n   验证内容: {content_data['description']}")

        start_time = time.time()
        validation = await controller.validate_content(
            content_data["content"],
            content_data["content_type"]
        )
        execution_time = time.time() - start_time

        passed = validation.get('passed', False)
        score = validation.get('overall_score', 0)
        issues = validation.get('issues_count', 0)

        status = "✅ 通过" if passed else "❌ 未通过"
        print(f"   {status}: 评分 {score:.1f}, 问题 {issues} 个")
        print(f"   ⏱️ 验证耗时: {execution_time:.3f}秒")
        # 显示关键问题
        critical_issues = validation.get('critical_issues', [])
        if critical_issues:
            print(f"   🚨 关键问题: {len(critical_issues)} 个")

        validation_results.append({
            'description': content_data['description'],
            'passed': passed,
            'score': score,
            'issues': issues,
            'time': execution_time
        })

    # 测试错误检测与纠正
    print("\n🔧 测试错误检测与纠正...")
    error_content = "水在0度沸腾。这是一个基本事实。天空是方的，地球绕太阳转是错误的。"

    correction_result = await controller.detect_and_correct_errors(error_content)

    print(f"   原始内容: {error_content}")
    print(f"   检测问题: {correction_result['issues_detected']} 个")
    print(f"   应用纠正: {correction_result['corrections_applied']} 个")
    print(f"   评估评分: {correction_result['assessment_score']:.1f}")

    if correction_result.get('corrected_content') != error_content:
        print(f"   纠正后: {correction_result['corrected_content']}")

    # 测试质量监控
    print("\n📈 测试质量监控...")
    # 添加一些历史数据用于监控
    for _ in range(5):
        await controller.assess_quality("这是一个测试内容，用于质量监控。")

    monitoring_result = await controller.monitor_quality_metrics()

    print(f"   📊 监控状态: {monitoring_result.get('status', 'unknown')}")
    print(f"   📈 平均评分: {monitoring_result.get('average_score', 0):.2f}")
    print(f"   ⚠️  错误率: {monitoring_result.get('error_rate', 0):.1%}")
    print(f"   🚨 警报数量: {monitoring_result.get('alert_count', 0)}")

    if monitoring_result.get('alerts'):
        print("   活跃警报:")
        for alert in monitoring_result['alerts'][:3]:  # 最多显示3个
            print(f"     - [{alert['severity']}] {alert['message']}")

    # 获取统计信息
    print("\n📊 质量控制统计:")
    stats_result = await controller.execute({"action": "stats"})

    if stats_result.success:
        stats = stats_result.data
        print(f"   🔍 总评估数: {stats['total_assessments']}")
        print(f"   ✅ 通过评估: {stats['passed_assessments']}")
        print(f"   ❌ 失败评估: {stats['failed_assessments']}")
        print(f"   🔧 自动纠正: {stats['auto_corrections']}")
        print(f"   📋 活跃规则: {stats['active_rules']}")
        print(f"   💾 缓存大小: {stats['cache_size']}")
        print(f"   📊 平均质量: {stats['average_quality_score']:.2f}")
        print(f"   📈 警报数量: {stats['quality_alerts']}")

    # 计算评估统计
    if assessment_results:
        avg_score = sum(r['overall_score'] for r in assessment_results) / len(assessment_results)
        avg_issues = sum(r['issues_count'] for r in assessment_results) / len(assessment_results)
        avg_time = sum(r['time'] for r in assessment_results) / len(assessment_results)

        print("\n🎯 评估性能统计:")
        print(f"   平均评分: {avg_score:.1f}")
        print(f"   平均问题数: {avg_issues:.1f}")
        print(f"   平均耗时: {avg_time:.3f}秒")

    # 计算验证统计
    if validation_results:
        pass_rate = sum(1 for r in validation_results if r['passed']) / len(validation_results) * 100
        print("\n✅ 验证通过率:")
        print(f"   通过率: {pass_rate:.1f}%")
    # 关闭质量控制器
    controller.shutdown()

    print("\n✅ QualityController测试完成！")

if __name__ == "__main__":
    asyncio.run(test_quality_controller())
