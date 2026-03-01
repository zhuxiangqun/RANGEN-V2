#!/usr/bin/env python3
"""
检索性能优化脚本

按照分析结果实施检索性能优化，并验证质量不下降
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from src.core.retrieval_quality_assessment import (
    get_retrieval_quality_assessor,
    run_comprehensive_quality_assessment,
    RetrievalResult
)
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OptimizationStep:
    """优化步骤配置"""
    name: str
    description: str
    parameter_changes: Dict[str, Any]
    expected_impact: str
    risk_level: str  # "low", "medium", "high"


class RetrievalOptimizer:
    """检索性能优化器"""

    def __init__(self):
        self.assessor = get_retrieval_quality_assessor()
        self.baseline_params = {
            'top_k': 10,
            'similarity_threshold': 0.5,
            'use_rerank': True,
            'use_graph': True,
            'use_llamaindex': True
        }

    def get_optimization_plan(self) -> List[OptimizationStep]:
        """获取优化计划"""
        return [
            OptimizationStep(
                name="reduce_top_k",
                description="减少检索结果数量从10到5",
                parameter_changes={'top_k': 5},
                expected_impact="减少计算量，预计响应时间减少30-40%",
                risk_level="low"
            ),
            OptimizationStep(
                name="increase_similarity_threshold",
                description="提高相似度阈值从0.5到0.6",
                parameter_changes={'similarity_threshold': 0.6},
                expected_impact="提高检索精确率，减少无关结果",
                risk_level="low"
            ),
            OptimizationStep(
                name="disable_rerank",
                description="禁用重排序功能",
                parameter_changes={'use_rerank': False},
                expected_impact="减少LLM调用，预计响应时间减少20-30%",
                risk_level="medium"
            ),
            OptimizationStep(
                name="disable_graph_search",
                description="禁用知识图谱查询",
                parameter_changes={'use_graph': False},
                expected_impact="减少图数据库查询，预计响应时间减少15-25%",
                risk_level="medium"
            ),
            OptimizationStep(
                name="final_threshold_tune",
                description="进一步提高相似度阈值到0.7",
                parameter_changes={'similarity_threshold': 0.7},
                expected_impact="进一步提高精确率，减少处理文档数量",
                risk_level="medium"
            )
        ]

    async def create_retrieval_function(self, params: Dict[str, Any]):
        """创建具有指定参数的检索函数"""
        async def retrieval_func(query: str) -> RetrievalResult:
            service = KnowledgeRetrievalService()

            # 应用参数
            for param_name, param_value in params.items():
                if hasattr(service, param_name):
                    setattr(service, param_name, param_value)

            # 执行检索
            result = await service.execute(query)

            return RetrievalResult(
                query=query,
                retrieved_docs=result.data.get('sources', []) if result.data else [],
                response_time=result.processing_time,
                success=result.success,
                error_message=result.error
            )

        return retrieval_func

    async def evaluate_optimization_step(
        self,
        step: OptimizationStep,
        current_params: Dict[str, Any],
        test_queries: List[str],
        ground_truth: Dict[str, str]
    ) -> Dict[str, Any]:
        """评估单个优化步骤"""
        print(f"\n🔬 评估优化步骤: {step.name}")
        print(f"   描述: {step.description}")
        print(f"   风险等级: {step.risk_level}")
        print(f"   预期影响: {step.expected_impact}")

        # 创建新的参数配置
        new_params = current_params.copy()
        new_params.update(step.parameter_changes)

        print(f"   参数变化: {step.parameter_changes}")
        print(f"   新配置: {new_params}")

        # 创建检索函数
        baseline_func = await self.create_retrieval_function(current_params)
        test_func = await self.create_retrieval_function(new_params)

        # 执行评估
        try:
            report = await self.assessor.perform_offline_assessment(
                baseline_version=f"before_{step.name}",
                test_version=f"after_{step.name}",
                test_queries=test_queries,
                baseline_retrieval=baseline_func,
                test_retrieval=test_func,
                ground_truth=ground_truth
            )

            # 输出结果
            print("   📊 评估结果:")
            print(".1f")
            if report.passed_thresholds:
                print("   ✅ 质量阈值: 通过")
            else:
                print("   ❌ 质量阈值: 未通过")
            # 检查关键指标
            response_time_metric = report.metrics.get('response_time')
            if response_time_metric and response_time_metric.improvement:
                if response_time_metric.improvement > 0.5:  # 减少超过0.5秒
                    print(".1f")
                elif response_time_metric.improvement < -0.5:  # 增加超过0.5秒
                    print(".1f")
            else:
                print(".1f")
            # 检查质量指标
            precision_metric = report.metrics.get('precision')
            recall_metric = report.metrics.get('recall')
            f1_metric = report.metrics.get('f1_score')

            quality_degraded = False
            if precision_metric and precision_metric.improvement and precision_metric.improvement < -0.05:
                print(".1%")
                quality_degraded = True
            if recall_metric and recall_metric.improvement and recall_metric.improvement < -0.05:
                print(".1%")
                quality_degraded = True
            if f1_metric and f1_metric.improvement and f1_metric.improvement < -0.05:
                print(".1%")
                quality_degraded = True

            return {
                'step': step.name,
                'success': report.passed_thresholds and not quality_degraded,
                'report': report,
                'new_params': new_params,
                'quality_degraded': quality_degraded
            }

        except Exception as e:
            logger.error(f"评估步骤 {step.name} 失败: {e}")
            return {
                'step': step.name,
                'success': False,
                'error': str(e),
                'new_params': new_params
            }

    async def run_optimization_pipeline(
        self,
        test_queries: List[str],
        ground_truth: Dict[str, str]
    ) -> Dict[str, Any]:
        """运行完整的优化流程"""
        print("🚀 开始检索性能优化流程")
        print("=" * 60)

        current_params = self.baseline_params.copy()
        optimization_history = []
        successful_steps = []

        optimization_plan = self.get_optimization_plan()

        for i, step in enumerate(optimization_plan, 1):
            print(f"\n📍 步骤 {i}/{len(optimization_plan)}: {step.name}")
            print("-" * 50)

            result = await self.evaluate_optimization_step(
                step, current_params, test_queries, ground_truth
            )

            optimization_history.append(result)

            if result['success']:
                print(f"✅ 步骤 {step.name} 评估通过，应用优化")
                current_params = result['new_params']
                successful_steps.append(step.name)
            else:
                print(f"❌ 步骤 {step.name} 评估失败")
                if 'error' in result:
                    print(f"   错误: {result['error']}")
                break

        # 生成最终报告
        final_report = {
            'optimization_completed': len(successful_steps) == len(optimization_plan),
            'successful_steps': successful_steps,
            'final_parameters': current_params,
            'baseline_parameters': self.baseline_params,
            'optimization_history': optimization_history,
            'performance_improvement': self._calculate_performance_improvement(optimization_history),
            'recommendations': self._generate_final_recommendations(optimization_history)
        }

        return final_report

    def _calculate_performance_improvement(self, history: List[Dict]) -> Dict[str, float]:
        """计算性能改进"""
        successful_reports = [h for h in history if h.get('success') and 'report' in h]

        if not successful_reports:
            return {}

        total_response_time_improvement = 0
        total_precision_change = 0
        total_recall_change = 0
        total_f1_change = 0

        for result in successful_reports:
            report = result['report']
            metrics = report.metrics

            if 'response_time' in metrics and metrics['response_time'].improvement:
                total_response_time_improvement += metrics['response_time'].improvement

            if 'precision' in metrics and metrics['precision'].improvement:
                total_precision_change += metrics['precision'].improvement

            if 'recall' in metrics and metrics['recall'].improvement:
                total_recall_change += metrics['recall'].improvement

            if 'f1_score' in metrics and metrics['f1_score'].improvement:
                total_f1_change += metrics['f1_score'].improvement

        return {
            'response_time_improvement': total_response_time_improvement,
            'precision_change': total_precision_change,
            'recall_change': total_recall_change,
            'f1_change': total_f1_change
        }

    def _generate_final_recommendations(self, history: List[Dict]) -> List[str]:
        """生成最终建议"""
        recommendations = []

        successful_steps = [h['step'] for h in history if h.get('success')]
        failed_steps = [h['step'] for h in history if not h.get('success')]

        if successful_steps:
            recommendations.append(f"✅ 成功应用优化步骤: {', '.join(successful_steps)}")

        if failed_steps:
            recommendations.append(f"⚠️ 未能应用优化步骤: {', '.join(failed_steps)}")

        # 基于历史结果生成建议
        performance_improvement = self._calculate_performance_improvement(history)

        if performance_improvement.get('response_time_improvement', 0) > 1.0:
            recommendations.append(".1f")
        elif performance_improvement.get('response_time_improvement', 0) < 0:
            recommendations.append(".1f")
        # 质量变化建议
        if abs(performance_improvement.get('precision_change', 0)) > 0.05:
            if performance_improvement['precision_change'] > 0:
                recommendations.append(".1%")
            else:
                recommendations.append(".1%")
        return recommendations


def load_test_data():
    """加载测试数据"""
    # 这里应该加载真实的测试数据
    # 为了演示，使用示例数据
    test_queries = [
        "什么是人工智能？",
        "机器学习和深度学习的区别",
        "Python编程语言的特点",
        "数据库管理系统有哪些类型",
        "云计算的基本概念"
    ]

    ground_truth = {
        "什么是人工智能？": {"doc_ai_001", "doc_ai_002"},
        "机器学习和深度学习的区别": {"doc_ml_003", "doc_dl_001"},
        "Python编程语言的特点": {"doc_python_001", "doc_python_002"},
        "数据库管理系统有哪些类型": {"doc_db_001", "doc_db_002"},
        "云计算的基本概念": {"doc_cloud_001", "doc_cloud_002"}
    }

    return test_queries, ground_truth


async def main():
    """主函数"""
    print("🔧 检索性能优化工具")
    print("=" * 60)

    try:
        # 初始化优化器
        optimizer = RetrievalOptimizer()

        # 加载测试数据
        print("1. 加载测试数据...")
        test_queries, ground_truth = load_test_data()
        print(f"   ✅ 加载 {len(test_queries)} 个测试查询")

        # 运行优化流程
        print("\n2. 执行优化流程...")
        print("   这可能需要几分钟时间，请耐心等待...")

        final_report = await optimizer.run_optimization_pipeline(
            test_queries=test_queries,
            ground_truth=ground_truth
        )

        # 输出最终结果
        print("\n" + "=" * 60)
        print("📊 优化结果总结")
        print("=" * 60)

        if final_report['optimization_completed']:
            print("🎉 优化流程完成！所有步骤都成功应用")
        else:
            print("⚠️ 优化流程部分完成，某些步骤未能通过质量评估")

        print(f"\n成功应用的优化步骤: {len(final_report['successful_steps'])}")
        for step in final_report['successful_steps']:
            print(f"   ✅ {step}")

        # 显示参数变化
        print("\n📋 参数配置变化:")
        print("   基线配置:")
        for k, v in final_report['baseline_parameters'].items():
            print(f"      {k}: {v}")

        print("   优化后配置:")
        for k, v in final_report['final_parameters'].items():
            print(f"      {k}: {v}")

        # 显示性能改进
        perf = final_report['performance_improvement']
        print("\n📈 性能改进统计:")
        if 'response_time_improvement' in perf:
            print(".1f")
        if 'precision_change' in perf:
            print(".1%")
            if perf['precision_change'] > 0:
                print("      (精确率提升)")
            else:
                print("      (精确率下降)")

        if 'recall_change' in perf:
            print(".1%")
            if perf['recall_change'] > 0:
                print("      (召回率提升)")
            else:
                print("      (召回率下降)")

        if 'f1_change' in perf:
            print(".1%")
            if perf['f1_change'] > 0:
                print("      (F1分数提升)")
            else:
                print("      (F1分数下降)")

        # 显示建议
        if final_report['recommendations']:
            print("\n💡 建议:")
            for rec in final_report['recommendations']:
                print(f"   • {rec}")

        # 保存详细报告
        report_file = f"retrieval_optimization_report_{int(asyncio.get_event_loop().time())}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            # 转换为可序列化的格式
            serializable_report = {
                k: v for k, v in final_report.items()
                if k not in ['optimization_history']  # 跳过包含复杂对象的字段
            }
            json.dump(serializable_report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存到: {report_file}")

        # 部署建议
        print("\n" + "=" * 60)
        print("🚀 部署建议")
        print("=" * 60)

        if final_report['optimization_completed']:
            print("✅ 推荐操作:")
            print("   1. 在测试环境验证优化配置")
            print("   2. 小流量灰度发布")
            print("   3. 监控生产环境质量指标")
            print("   4. 确认无质量下降后全量发布")
        else:
            print("⚠️ 建议操作:")
            print("   1. 重新评估失败的优化步骤")
            print("   2. 调整参数阈值或优化策略")
            print("   3. 考虑更保守的优化方案")

        print("\n🔄 回滚计划:")
        print("   如发现质量问题，可通过以下方式回滚:")
        print("   1. 恢复到基线参数配置")
        print("   2. 使用版本控制系统回退代码")
        print("   3. 重新运行评估脚本验证")

    except Exception as e:
        logger.error(f"优化过程出错: {e}", exc_info=True)
        print(f"\n❌ 优化失败: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
