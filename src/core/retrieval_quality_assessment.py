"""
检索质量评估框架

提供全面的检索质量评估体系，确保性能优化后质量不下降
包括离线评估、在线A/B测试、监控预警等完整解决方案
"""

import asyncio
import logging
import time
import json
import statistics
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import math

from .ab_testing_framework import get_ab_testing_framework, Variant, ExperimentResult
from .performance_benchmark import get_performance_benchmark, BenchmarkConfig

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """检索质量指标"""
    PRECISION = "precision"           # 精确率
    RECALL = "recall"                # 召回率
    F1_SCORE = "f1_score"            # F1分数
    MRR = "mrr"                      # 平均倒数排名
    NDCG = "ndcg"                    # 归一化折损累计收益
    RESPONSE_TIME = "response_time"   # 响应时间
    SUCCESS_RATE = "success_rate"     # 成功率
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    retrieved_docs: List[Dict[str, Any]]
    relevant_docs: Set[str] = field(default_factory=set)  # 相关文档ID集合
    response_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class QualityAssessment:
    """质量评估结果"""
    metric_name: str
    value: float
    baseline_value: Optional[float] = None
    improvement: Optional[float] = None
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    sample_size: int = 0
    statistical_significance: bool = False
    assessment_time: float = field(default_factory=time.time)


@dataclass
class RetrievalQualityReport:
    """检索质量报告"""
    experiment_name: str
    baseline_version: str
    test_version: str
    assessment_time: float
    metrics: Dict[str, QualityAssessment] = field(default_factory=dict)
    overall_quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    passed_thresholds: bool = True


class RetrievalQualityAssessor:
    """
    检索质量评估器

    提供完整的检索质量评估功能，包括：
    - 离线质量评估
    - 在线A/B测试
    - 基线对比
    - 质量监控
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.baselines: Dict[str, Dict[str, float]] = {}  # 基线数据
        self.quality_history: List[RetrievalQualityReport] = []
        self.ab_framework = get_ab_testing_framework()
        self.performance_benchmark = get_performance_benchmark()

    def establish_baseline(
        self,
        version: str,
        test_queries: List[str],
        retrieval_function: Callable[[str], RetrievalResult],
        ground_truth: Dict[str, Set[str]]
    ) -> Dict[str, float]:
        """
        建立基线质量指标

        Args:
            version: 版本标识
            test_queries: 测试查询列表
            retrieval_function: 检索函数
            ground_truth:  ground truth数据 {query: relevant_doc_ids}

        Returns:
            各指标的基线值
        """
        self.logger.info(f"📊 建立基线: {version}")

        results = []
        for query in test_queries:
            try:
                result = retrieval_function(query)
                result.relevant_docs = ground_truth.get(query, set())
                results.append(result)
            except Exception as e:
                self.logger.warning(f"查询失败: {query[:50]}... -> {e}")
                continue

        # 计算各指标
        baseline_metrics = self._calculate_quality_metrics(results)

        # 保存基线
        self.baselines[version] = baseline_metrics

        self.logger.info(f"✅ 基线建立完成: {version}")
        for metric, value in baseline_metrics.items():
            self.logger.info(f"   {metric}: {value:.4f}")

        return baseline_metrics

    async def perform_offline_assessment(
        self,
        baseline_version: str,
        test_version: str,
        test_queries: List[str],
        baseline_retrieval: Callable[[str], RetrievalResult],
        test_retrieval: Callable[[str], RetrievalResult],
        ground_truth: Dict[str, Set[str]]
    ) -> RetrievalQualityReport:
        """
        执行离线质量评估

        Args:
            baseline_version: 基线版本
            test_version: 测试版本
            test_queries: 测试查询
            baseline_retrieval: 基线检索函数
            test_retrieval: 测试检索函数
            ground_truth: ground truth

        Returns:
            质量评估报告
        """
        self.logger.info(f"🔬 执行离线评估: {baseline_version} vs {test_version}")

        baseline_results = []
        test_results = []

        # 收集结果
        for query in test_queries:
            try:
                baseline_result = baseline_retrieval(query)
                baseline_result.relevant_docs = ground_truth.get(query, set())
                baseline_results.append(baseline_result)

                test_result = test_retrieval(query)
                test_result.relevant_docs = ground_truth.get(query, set())
                test_results.append(test_result)

            except Exception as e:
                self.logger.warning(f"查询评估失败: {query[:50]}... -> {e}")
                continue

        # 计算质量指标
        baseline_metrics = self._calculate_quality_metrics(baseline_results)
        test_metrics = self._calculate_quality_metrics(test_results)

        # 生成评估报告
        report = self._generate_quality_report(
            f"offline_{baseline_version}_vs_{test_version}",
            baseline_version,
            test_version,
            baseline_metrics,
            test_metrics,
            len(test_queries)
        )

        self.quality_history.append(report)
        return report

    async def perform_online_ab_test(
        self,
        experiment_name: str,
        baseline_retrieval: Callable[[str], RetrievalResult],
        test_retrieval: Callable[[str], RetrievalResult],
        test_queries: List[str],
        ground_truth: Optional[Dict[str, Set[str]]] = None,
        duration_hours: int = 24,
        min_sample_size: int = 1000
    ) -> RetrievalQualityReport:
        """
        执行在线A/B测试

        Args:
            experiment_name: 实验名称
            baseline_retrieval: 基线检索函数
            test_retrieval: 测试检索函数
            test_queries: 测试查询池
            ground_truth: ground truth（可选）
            duration_hours: 测试持续时间（小时）
            min_sample_size: 最小样本量

        Returns:
            A/B测试结果报告
        """
        self.logger.info(f"🅰️🅱️ 执行A/B测试: {experiment_name}")

        # 创建实验变体
        variants = [
            Variant(
                name="baseline",
                description="基线检索实现",
                config={"retrieval_func": baseline_retrieval}
            ),
            Variant(
                name="test",
                description="测试检索实现",
                config={"retrieval_func": test_retrieval}
            )
        ]

        # 创建实验
        experiment = self.ab_framework.create_experiment(
            name=experiment_name,
            description=f"A/B测试: 检索质量对比",
            hypothesis="测试版本在保持性能的同时不降低检索质量",
            variants=variants,
            primary_metric="response_time",  # 主要关注性能
            secondary_metrics=["precision", "recall", "success_rate"],
            min_sample_size=min_sample_size
        )

        # 定义测试函数
        async def test_function(variant_name: str) -> Dict[str, Any]:
            try:
                # 随机选择测试查询
                query = test_queries[int(time.time() * 1000) % len(test_queries)]

                variant = next(v for v in variants if v.name == variant_name)
                retrieval_func = variant.config["retrieval_func"]

                # 执行检索
                start_time = time.time()
                result = await retrieval_func(query)
                response_time = time.time() - start_time

                # 计算质量指标（如果有ground truth）
                quality_metrics = {}
                if ground_truth and query in ground_truth:
                    relevant_docs = ground_truth[query]
                    quality_metrics = self._calculate_single_query_metrics(result, relevant_docs)

                return {
                    "success": result.success,
                    "response_time": response_time,
                    "precision": quality_metrics.get("precision", 0.0),
                    "recall": quality_metrics.get("recall", 0.0),
                    "query": query
                }

            except Exception as e:
                return {
                    "success": False,
                    "response_time": 30.0,  # 超时
                    "precision": 0.0,
                    "recall": 0.0,
                    "error": str(e)
                }

        # 启动实验
        self.ab_framework.start_experiment(experiment_name)

        # 运行实验
        start_time = time.time()
        results_collected = 0

        while (time.time() - start_time < duration_hours * 3600 and
               results_collected < min_sample_size * 2):  # 确保每个变体都有足够样本

            try:
                # 执行测试
                variant = self.ab_framework.assign_traffic(experiment_name)
                if variant:
                    result = await test_function(variant)

                    # 记录指标
                    self.ab_framework.record_metric(
                        experiment_name, variant, "response_time", result["response_time"]
                    )
                    self.ab_framework.record_metric(
                        experiment_name, variant, "success_rate", 1.0 if result["success"] else 0.0
                    )
                    if "precision" in result:
                        self.ab_framework.record_metric(
                            experiment_name, variant, "precision", result["precision"]
                        )
                    if "recall" in result:
                        self.ab_framework.record_metric(
                            experiment_name, variant, "recall", result["recall"]
                        )

                    results_collected += 1

                await asyncio.sleep(1)  # 控制测试频率

            except Exception as e:
                self.logger.error(f"A/B测试执行错误: {e}")
                await asyncio.sleep(5)

        # 分析结果
        analysis = self.ab_framework.analyze_experiment(experiment_name)

        # 生成报告
        report = RetrievalQualityReport(
            experiment_name=experiment_name,
            baseline_version="baseline",
            test_version="test",
            assessment_time=time.time()
        )

        if analysis and analysis.detailed_metrics:
            for variant_name, metrics in analysis.detailed_metrics.items():
                # 主要指标：响应时间
                response_time_assessment = QualityAssessment(
                    metric_name="response_time",
                    value=metrics.average_value,
                    sample_size=metrics.sample_size,
                    confidence_interval=metrics.confidence_interval
                )
                report.metrics[f"{variant_name}_response_time"] = response_time_assessment

                # 成功率
                success_rate = metrics.conversions / metrics.sample_size if metrics.sample_size > 0 else 0.0
                success_assessment = QualityAssessment(
                    metric_name="success_rate",
                    value=success_rate,
                    sample_size=metrics.sample_size
                )
                report.metrics[f"{variant_name}_success_rate"] = success_assessment

        # 生成建议
        report = self._enhance_report_with_recommendations(report, analysis)

        # 结束实验
        self.ab_framework.end_experiment(experiment_name)

        self.quality_history.append(report)
        return report

    def _calculate_quality_metrics(self, results: List[RetrievalResult]) -> Dict[str, float]:
        """计算质量指标"""
        if not results:
            return {}

        metrics = {}

        # 精确率 (Precision)
        precisions = []
        for result in results:
            if result.retrieved_docs:
                relevant_retrieved = sum(1 for doc in result.retrieved_docs
                                       if doc.get('id') in result.relevant_docs)
                precision = relevant_retrieved / len(result.retrieved_docs)
                precisions.append(precision)
        metrics["precision"] = statistics.mean(precisions) if precisions else 0.0

        # 召回率 (Recall)
        recalls = []
        for result in results:
            if result.relevant_docs:
                relevant_retrieved = sum(1 for doc in result.retrieved_docs
                                       if doc.get('id') in result.relevant_docs)
                recall = relevant_retrieved / len(result.relevant_docs)
                recalls.append(recall)
        metrics["recall"] = statistics.mean(recalls) if recalls else 0.0

        # F1分数
        precision = metrics["precision"]
        recall = metrics["recall"]
        metrics["f1_score"] = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        # 平均倒数排名 (MRR)
        mrr_scores = []
        for result in results:
            for i, doc in enumerate(result.retrieved_docs):
                if doc.get('id') in result.relevant_docs:
                    mrr_scores.append(1.0 / (i + 1))
                    break
            else:
                mrr_scores.append(0.0)
        metrics["mrr"] = statistics.mean(mrr_scores) if mrr_scores else 0.0

        # 响应时间
        response_times = [r.response_time for r in results if r.response_time > 0]
        metrics["response_time"] = statistics.mean(response_times) if response_times else 0.0

        # 成功率
        success_count = sum(1 for r in results if r.success)
        metrics["success_rate"] = success_count / len(results) if results else 0.0

        return metrics

    def _calculate_single_query_metrics(self, result: RetrievalResult, relevant_docs: Set[str]) -> Dict[str, float]:
        """计算单个查询的质量指标"""
        metrics = {}

        if not result.retrieved_docs:
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0}

        # 精确率
        relevant_retrieved = sum(1 for doc in result.retrieved_docs
                               if doc.get('id') in relevant_docs)
        precision = relevant_retrieved / len(result.retrieved_docs)
        metrics["precision"] = precision

        # 召回率
        if relevant_docs:
            recall = relevant_retrieved / len(relevant_docs)
        else:
            recall = 0.0
        metrics["recall"] = recall

        # F1分数
        if precision + recall > 0:
            f1_score = 2 * precision * recall / (precision + recall)
        else:
            f1_score = 0.0
        metrics["f1_score"] = f1_score

        return metrics

    def _generate_quality_report(
        self,
        experiment_name: str,
        baseline_version: str,
        test_version: str,
        baseline_metrics: Dict[str, float],
        test_metrics: Dict[str, float],
        sample_size: int
    ) -> RetrievalQualityReport:
        """生成质量评估报告"""
        report = RetrievalQualityReport(
            experiment_name=experiment_name,
            baseline_version=baseline_version,
            test_version=test_version,
            assessment_time=time.time()
        )

        # 计算各项指标的改进情况
        for metric_name in set(baseline_metrics.keys()) | set(test_metrics.keys()):
            baseline_value = baseline_metrics.get(metric_name, 0.0)
            test_value = test_metrics.get(metric_name, 0.0)

            # 计算改进（对于响应时间，降低是改进；对于其他指标，提高是改进）
            if metric_name == "response_time":
                improvement = baseline_value - test_value  # 降低是正改进
            else:
                improvement = test_value - baseline_value  # 提高是正改进

            assessment = QualityAssessment(
                metric_name=metric_name,
                value=test_value,
                baseline_value=baseline_value,
                improvement=improvement,
                sample_size=sample_size,
                statistical_significance=self._check_statistical_significance(
                    baseline_value, test_value, sample_size
                )
            )

            report.metrics[metric_name] = assessment

        # 计算总体质量分数
        report.overall_quality_score = self._calculate_overall_score(report.metrics)

        # 生成建议和警告
        report = self._assess_quality_thresholds(report)

        return report

    def _check_statistical_significance(
        self,
        baseline: float,
        test: float,
        sample_size: int,
        alpha: float = 0.05
    ) -> bool:
        """检查统计显著性（简化版本）"""
        if sample_size < 30:
            return False

        # 计算标准误差（假设）
        std_dev = abs(baseline - test) * 0.5  # 简化的标准差估计
        standard_error = std_dev / math.sqrt(sample_size)

        # 计算z分数
        z_score = abs(test - baseline) / standard_error

        # 95%置信区间对应的z分数约为1.96
        return z_score > 1.96

    def _calculate_overall_score(self, metrics: Dict[str, QualityAssessment]) -> float:
        """计算总体质量分数 (0-100)"""
        if not metrics:
            return 0.0

        score = 0.0
        weights = {
            "precision": 0.25,
            "recall": 0.25,
            "f1_score": 0.2,
            "response_time": 0.15,
            "success_rate": 0.15
        }

        for metric_name, assessment in metrics.items():
            if metric_name in weights:
                weight = weights[metric_name]

                # 标准化分数 (0-1)
                if metric_name == "response_time":
                    # 响应时间: 越低越好，假设理想时间为1秒
                    normalized_score = max(0, 1 - assessment.value / 5.0)
                else:
                    # 其他指标: 越高越好
                    normalized_score = min(1.0, assessment.value)

                score += normalized_score * weight * 100

        return score

    def _assess_quality_thresholds(self, report: RetrievalQualityReport) -> RetrievalQualityReport:
        """评估质量阈值"""
        critical_metrics = ["precision", "recall", "f1_score"]
        performance_metrics = ["response_time", "success_rate"]

        for metric_name, assessment in report.metrics.items():
            # 质量下降检查
            if assessment.improvement is not None:
                if metric_name in critical_metrics and assessment.improvement < -0.05:  # 下降5%以上
                    report.warnings.append(
                        f"⚠️ {metric_name}下降{abs(assessment.improvement):.1%}，可能影响检索质量"
                    )
                    report.passed_thresholds = False

                elif metric_name == "response_time" and assessment.improvement < -1.0:  # 响应时间增加1秒以上
                    report.warnings.append(
                        f"⚠️ 响应时间增加{abs(assessment.improvement):.1f}秒，可能影响用户体验"
                    )

        # 生成建议
        if report.passed_thresholds:
            report.recommendations.append("✅ 所有质量指标均符合要求，可以安全部署")
        else:
            report.recommendations.append("❌ 发现质量下降，建议进一步优化或回滚")

        # 性能提升建议
        response_time_metric = report.metrics.get("response_time")
        if response_time_metric and response_time_metric.improvement and response_time_metric.improvement > 0.5:
            report.recommendations.append(
                f"🚀 响应时间提升{response_time_metric.improvement:.1f}秒，性能优化成功"
            )

        return report

    def _enhance_report_with_recommendations(
        self,
        report: RetrievalQualityReport,
        analysis: Optional[ExperimentResult]
    ) -> RetrievalQualityReport:
        """基于A/B测试结果增强报告"""
        if not analysis:
            return report

        if analysis.winner:
            report.recommendations.append(
                f"🎯 A/B测试结果: {analysis.winner}版本表现更优 (置信度: {analysis.confidence_level:.1%})"
            )

            if analysis.winner == "baseline":
                report.warnings.append("⚠️ 基线版本表现更好，建议重新评估优化方案")
                report.passed_thresholds = False
            else:
                report.recommendations.append("✅ 测试版本表现更好，可以安全部署")

        return report

    def get_quality_history(self, days: int = 7) -> List[RetrievalQualityReport]:
        """获取最近的质量评估历史"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        return [r for r in self.quality_history if r.assessment_time >= cutoff_time]

    def generate_quality_dashboard(self) -> Dict[str, Any]:
        """生成质量仪表板数据"""
        recent_reports = self.get_quality_history(days=7)

        if not recent_reports:
            return {"status": "no_data", "message": "暂无质量评估数据"}

        # 计算趋势
        latest_report = max(recent_reports, key=lambda r: r.assessment_time)

        # 质量趋势（最近7天）
        quality_trend = []
        for report in sorted(recent_reports, key=lambda r: r.assessment_time):
            quality_trend.append({
                "time": datetime.fromtimestamp(report.assessment_time).isoformat(),
                "score": report.overall_quality_score,
                "experiment": report.experiment_name
            })

        return {
            "status": "active",
            "latest_assessment": {
                "time": datetime.fromtimestamp(latest_report.assessment_time).isoformat(),
                "overall_score": latest_report.overall_quality_score,
                "passed_thresholds": latest_report.passed_thresholds,
                "warning_count": len(latest_report.warnings)
            },
            "quality_trend": quality_trend,
            "baseline_versions": list(self.baselines.keys()),
            "recommendations": latest_report.recommendations,
            "warnings": latest_report.warnings
        }


# 便捷函数
def get_retrieval_quality_assessor() -> RetrievalQualityAssessor:
    """获取检索质量评估器实例"""
    return RetrievalQualityAssessor()


async def run_comprehensive_quality_assessment(
    baseline_retrieval: Callable[[str], RetrievalResult],
    test_retrieval: Callable[[str], RetrievalResult],
    test_queries: List[str],
    ground_truth: Dict[str, Set[str]],
    assessment_name: str = "retrieval_optimization"
) -> RetrievalQualityReport:
    """
    运行全面的质量评估流程

    Args:
        baseline_retrieval: 基线检索函数
        test_retrieval: 测试检索函数
        test_queries: 测试查询列表
        ground_truth: ground truth数据
        assessment_name: 评估名称

    Returns:
        完整的质量评估报告
    """
    assessor = get_retrieval_quality_assessor()

    # 1. 建立基线
    baseline_metrics = assessor.establish_baseline(
        "baseline",
        test_queries,
        baseline_retrieval,
        ground_truth
    )

    # 2. 执行离线评估
    offline_report = await assessor.perform_offline_assessment(
        "baseline",
        "optimized",
        test_queries,
        baseline_retrieval,
        test_retrieval,
        ground_truth
    )

    # 3. 如果离线评估通过，执行在线A/B测试
    if offline_report.passed_thresholds:
        ab_report = await assessor.perform_online_ab_test(
            f"{assessment_name}_ab_test",
            baseline_retrieval,
            test_retrieval,
            test_queries,
            ground_truth,
            duration_hours=1,  # 简化的测试时长
            min_sample_size=100
        )

        # 合并结果
        combined_report = RetrievalQualityReport(
            experiment_name=f"{assessment_name}_combined",
            baseline_version="baseline",
            test_version="optimized",
            assessment_time=time.time(),
            metrics={**offline_report.metrics, **ab_report.metrics},
            overall_quality_score=(offline_report.overall_quality_score + ab_report.overall_quality_score) / 2,
            recommendations=offline_report.recommendations + ab_report.recommendations,
            warnings=offline_report.warnings + ab_report.warnings,
            passed_thresholds=offline_report.passed_thresholds and ab_report.passed_thresholds
        )

        return combined_report
    else:
        return offline_report
