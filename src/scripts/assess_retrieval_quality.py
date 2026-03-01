#!/usr/bin/env python3
"""
检索质量评估脚本

用于验证检索性能优化后质量是否下降
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Any
from pathlib import Path

from src.core.retrieval_quality_assessment import (
    get_retrieval_quality_assessor,
    run_comprehensive_quality_assessment,
    RetrievalResult
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_baseline_retrieval_function(system):
    """创建基线检索函数"""
    async def baseline_retrieval(query: str) -> RetrievalResult:
        """基线检索实现（使用原始参数）"""
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

        # 创建服务实例
        service = KnowledgeRetrievalService()
        await service.initialize_services()

        # 设置原始参数（假设这些是优化前的参数）
        service.top_k = 10
        service.similarity_threshold = 0.5
        service.use_rerank = True
        service.use_graph = True
        service.use_llamaindex = True

        # 执行检索
        result = await service.execute(query)

        return RetrievalResult(
            query=query,
            retrieved_docs=result.data.get('sources', []) if result.data else [],
            response_time=result.processing_time,
            success=result.success,
            error_message=result.error
        )

    return baseline_retrieval


async def create_optimized_retrieval_function(system):
    """创建优化后检索函数"""
    async def optimized_retrieval(query: str) -> RetrievalResult:
        """优化后检索实现（使用优化参数）"""
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

        # 创建服务实例
        service = KnowledgeRetrievalService()
        await service.initialize_services()

        # 设置优化后的参数
        service.top_k = 5  # 从10减少到5
        service.similarity_threshold = 0.7  # 从0.5提高到0.7
        service.use_rerank = False  # 禁用rerank
        service.use_graph = False  # 禁用图检索
        service.use_llamaindex = True  # 保持启用

        # 执行检索
        result = await service.execute(query)

        return RetrievalResult(
            query=query,
            retrieved_docs=result.data.get('sources', []) if result.data else [],
            response_time=result.processing_time,
            success=result.success,
            error_message=result.error
        )

    return optimized_retrieval


def load_test_data():
    """加载测试数据"""
    # 这里应该加载真实的测试查询和ground truth
    # 为了演示，我们创建一些示例数据

    test_queries = [
        "什么是人工智能？",
        "机器学习和深度学习的区别",
        "Python编程语言的特点",
        "数据库管理系统有哪些类型",
        "云计算的基本概念",
        "网络安全的重要性",
        "软件工程的开发模型",
        "大数据技术的发展历程",
        "物联网的应用场景",
        "区块链的工作原理"
    ]

    # 示例ground truth（实际使用时应该有真实的标注数据）
    ground_truth = {
        "什么是人工智能？": {"doc_ai_001", "doc_ai_002", "doc_ml_001"},
        "机器学习和深度学习的区别": {"doc_ml_003", "doc_dl_001", "doc_ai_005"},
        "Python编程语言的特点": {"doc_python_001", "doc_python_002"},
        "数据库管理系统有哪些类型": {"doc_db_001", "doc_db_002", "doc_db_003"},
        "云计算的基本概念": {"doc_cloud_001", "doc_cloud_002"},
        "网络安全的重要性": {"doc_security_001", "doc_security_002"},
        "软件工程的开发模型": {"doc_se_001", "doc_se_002", "doc_se_003"},
        "大数据技术的发展历程": {"doc_bigdata_001", "doc_bigdata_002"},
        "物联网的应用场景": {"doc_iot_001", "doc_iot_002"},
        "区块链的工作原理": {"doc_blockchain_001", "doc_blockchain_002"}
    }

    return test_queries, ground_truth


async def main():
    """主函数"""
    print("=" * 80)
    print("🔍 检索质量评估系统")
    print("=" * 80)

    try:
        # 加载测试数据
        print("1. 加载测试数据...")
        test_queries, ground_truth = load_test_data()
        print(f"   ✅ 加载 {len(test_queries)} 个测试查询")

        # 初始化系统
        print("2. 初始化检索系统...")
        from src.unified_research_system import create_unified_research_system
        system = await create_unified_research_system()
        print("   ✅ 系统初始化完成")

        # 创建检索函数
        print("3. 创建检索函数...")
        baseline_retrieval = await create_baseline_retrieval_function(system)
        optimized_retrieval = await create_optimized_retrieval_function(system)
        print("   ✅ 检索函数创建完成")

        # 执行全面质量评估
        print("4. 执行质量评估...")
        print("   这可能需要几分钟时间，请耐心等待...")

        assessment_name = f"retrieval_optimization_{int(asyncio.get_event_loop().time())}"
        report = await run_comprehensive_quality_assessment(
            baseline_retrieval=baseline_retrieval,
            test_retrieval=optimized_retrieval,
            test_queries=test_queries,
            ground_truth=ground_truth,
            assessment_name=assessment_name
        )

        # 输出结果
        print("\n" + "=" * 80)
        print("📊 评估结果报告")
        print("=" * 80)

        print(f"实验名称: {report.experiment_name}")
        print(f"基线版本: {report.baseline_version}")
        print(f"测试版本: {report.test_version}")
        print(".1f")
        print(f"评估时间: {report.assessment_time}")

        print(f"\n总体质量分数: {report.overall_quality_score:.1f}/100")

        if report.passed_thresholds:
            print("✅ 质量阈值检查: 通过")
        else:
            print("❌ 质量阈值检查: 未通过")

        print("
详细指标:"        print("-" * 40)
        for metric_name, assessment in report.metrics.items():
            status = ""
            if assessment.improvement is not None:
                if assessment.improvement > 0:
                    status = f"📈 +{assessment.improvement:.3f}"
                elif assessment.improvement < 0:
                    status = f"📉 {assessment.improvement:.3f}"
                else:
                    status = "➡️ 0.000"

            print("6.4f"
                  f"置信区间: [{assessment.confidence_interval[0]:.3f}, {assessment.confidence_interval[1]:.3f}]"
                  f"显著性: {'✅' if assessment.statistical_significance else '❌'}")

        if report.warnings:
            print("
⚠️ 警告信息:"            for warning in report.warnings:
                print(f"   • {warning}")

        if report.recommendations:
            print("
💡 建议:"            for rec in report.recommendations:
                print(f"   • {rec}")

        # 保存报告
        report_file = f"retrieval_quality_report_{int(report.assessment_time)}.json"
        report_data = {
            "experiment_name": report.experiment_name,
            "baseline_version": report.baseline_version,
            "test_version": report.test_version,
            "assessment_time": report.assessment_time,
            "overall_quality_score": report.overall_quality_score,
            "passed_thresholds": report.passed_thresholds,
            "metrics": {
                name: {
                    "value": assessment.value,
                    "baseline_value": assessment.baseline_value,
                    "improvement": assessment.improvement,
                    "confidence_interval": assessment.confidence_interval,
                    "sample_size": assessment.sample_size,
                    "statistical_significance": assessment.statistical_significance
                }
                for name, assessment in report.metrics.items()
            },
            "recommendations": report.recommendations,
            "warnings": report.warnings
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存到: {report_file}")

        # 最终结论
        print("\n" + "=" * 80)
        if report.passed_thresholds and report.overall_quality_score >= 80:
            print("🎉 评估结论: 优化成功！可以安全部署优化版本")
            print("   检索质量保持良好，性能得到提升")
        elif report.passed_thresholds:
            print("⚠️ 评估结论: 优化部分成功，但质量分数较低")
            print("   建议进一步优化或重新评估参数")
        else:
            print("❌ 评估结论: 优化失败，质量下降明显")
            print("   建议回滚更改或调整优化策略")
        print("=" * 80)

    except Exception as e:
        logger.error(f"评估过程中出错: {e}", exc_info=True)
        print(f"\n❌ 评估失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
