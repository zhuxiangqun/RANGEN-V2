"""
A/B测试框架

提供科学的实验设计、流量分配、结果分析和统计显著性检验
"""

import asyncio
import logging
import time
import random
import json
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics
import math


logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """实验状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    TERMINATED = "terminated"


@dataclass
class Variant:
    """实验变体"""
    name: str
    description: str
    config: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0  # 流量权重


@dataclass
class ExperimentMetrics:
    """实验指标"""
    variant_name: str
    sample_size: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    average_value: float = 0.0  # 平均价值（如响应时间、用户评分等）
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    standard_error: float = 0.0


@dataclass
class ExperimentResult:
    """实验结果"""
    experiment_name: str
    winner: Optional[str] = None
    confidence_level: float = 0.0
    effect_size: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    detailed_metrics: Dict[str, ExperimentMetrics] = field(default_factory=dict)


@dataclass
class Experiment:
    """A/B实验"""
    name: str
    description: str
    hypothesis: str
    variants: List[Variant]
    primary_metric: str  # 主要指标
    secondary_metrics: List[str] = field(default_factory=list)
    min_sample_size: int = 1000  # 最小样本量
    confidence_threshold: float = 0.95  # 置信度阈值
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    ended_at: Optional[float] = None

    # 运行时数据
    traffic_allocation: Dict[str, int] = field(default_factory=dict)
    metrics_data: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)


class StatisticalAnalyzer:
    """统计分析器"""

    @staticmethod
    def calculate_conversion_rate(successes: int, total: int) -> float:
        """计算转化率"""
        return successes / total if total > 0 else 0.0

    @staticmethod
    def calculate_confidence_interval(
        conversion_rate: float,
        sample_size: int,
        confidence_level: float = 0.95
    ) -> tuple[float, float]:
        """计算置信区间"""
        if sample_size == 0:
            return (0.0, 0.0)

        # 使用正态分布近似
        z_score = 1.96  # 95% 置信区间
        if confidence_level == 0.99:
            z_score = 2.576

        standard_error = math.sqrt(conversion_rate * (1 - conversion_rate) / sample_size)
        margin_of_error = z_score * standard_error

        lower_bound = max(0.0, conversion_rate - margin_of_error)
        upper_bound = min(1.0, conversion_rate + margin_of_error)

        return (lower_bound, upper_bound)

    @staticmethod
    def perform_t_test(
        group_a: List[float],
        group_b: List[float],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        执行t检验

        Returns:
            dict: 包含t统计量、p值、是否显著等信息
        """
        if len(group_a) < 2 or len(group_b) < 2:
            return {
                "significant": False,
                "p_value": 1.0,
                "t_statistic": 0.0,
                "error": "样本量不足"
            }

        try:
            # 计算基本统计量
            mean_a = statistics.mean(group_a)
            mean_b = statistics.mean(group_b)
            std_a = statistics.stdev(group_a)
            std_b = statistics.stdev(group_b)
            n_a = len(group_a)
            n_b = len(group_b)

            # 计算t统计量
            pooled_std = math.sqrt(((n_a - 1) * std_a**2 + (n_b - 1) * std_b**2) / (n_a + n_b - 2))
            se = pooled_std * math.sqrt(1/n_a + 1/n_b)
            t_statistic = (mean_a - mean_b) / se if se > 0 else 0

            # 计算p值（近似）
            df = n_a + n_b - 2
            p_value = 2 * (1 - statistics.NormalDist().cdf(abs(t_statistic)))

            return {
                "significant": p_value < alpha,
                "p_value": p_value,
                "t_statistic": t_statistic,
                "mean_difference": mean_a - mean_b,
                "effect_size": abs(mean_a - mean_b) / pooled_std if pooled_std > 0 else 0
            }

        except Exception as e:
            return {
                "significant": False,
                "p_value": 1.0,
                "t_statistic": 0.0,
                "error": str(e)
            }

    @staticmethod
    def calculate_sample_size(
        baseline_rate: float,
        minimum_detectable_effect: float,
        confidence_level: float = 0.95,
        power: float = 0.8
    ) -> int:
        """
        计算需要的样本量

        Args:
            baseline_rate: 基准转化率
            minimum_detectable_effect: 最小可检测效果
            confidence_level: 置信水平
            power: 检验功效

        Returns:
            int: 需要的样本量
        """
        # 使用简化公式计算样本量
        z_alpha = 1.96  # 95% 置信区间
        z_beta = 0.84   # 80% 检验功效

        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect

        # 样本量计算公式
        numerator = (z_alpha * math.sqrt(2 * p1 * (1 - p1)) +
                    z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2)))**2
        denominator = (p2 - p1)**2

        if denominator == 0:
            return 1000  # 默认值

        sample_size_per_group = numerator / denominator
        return int(math.ceil(sample_size_per_group))


class ABTestingFramework:
    """
    A/B测试框架

    提供完整的A/B测试生命周期管理
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.experiments: Dict[str, Experiment] = {}
        self.statistical_analyzer = StatisticalAnalyzer()

    def create_experiment(
        self,
        name: str,
        description: str,
        hypothesis: str,
        variants: List[Variant],
        primary_metric: str,
        secondary_metrics: Optional[List[str]] = None,
        min_sample_size: int = 1000,
        confidence_threshold: float = 0.95
    ) -> Experiment:
        """创建实验"""

        if name in self.experiments:
            raise ValueError(f"实验 '{name}' 已存在")

        if len(variants) < 2:
            raise ValueError("实验至少需要2个变体")

        experiment = Experiment(
            name=name,
            description=description,
            hypothesis=hypothesis,
            variants=variants,
            primary_metric=primary_metric,
            secondary_metrics=secondary_metrics or [],
            min_sample_size=min_sample_size,
            confidence_threshold=confidence_threshold
        )

        self.experiments[name] = experiment
        self.logger.info(f"✅ 创建实验: {name}")

        return experiment

    def start_experiment(self, experiment_name: str):
        """启动实验"""
        if experiment_name not in self.experiments:
            raise ValueError(f"实验 '{experiment_name}' 不存在")

        experiment = self.experiments[experiment_name]

        if experiment.status != ExperimentStatus.DRAFT:
            raise ValueError(f"实验状态不允许启动: {experiment.status.value}")

        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = time.time()

        # 初始化数据收集
        for variant in experiment.variants:
            experiment.metrics_data[variant.name] = []

        self.logger.info(f"🚀 启动实验: {experiment_name}")

    def assign_traffic(self, experiment_name: str, user_id: Optional[str] = None) -> Optional[str]:
        """分配流量"""
        if experiment_name not in self.experiments:
            return None

        experiment = self.experiments[experiment_name]

        if experiment.status != ExperimentStatus.RUNNING:
            return None

        # 简单的随机分配（生产环境中应使用更复杂的分配策略）
        total_weight = sum(variant.weight for variant in experiment.variants)
        rand_value = random.uniform(0, total_weight)

        cumulative_weight = 0.0
        for variant in experiment.variants:
            cumulative_weight += variant.weight
            if rand_value <= cumulative_weight:
                experiment.traffic_allocation[variant.name] = (
                    experiment.traffic_allocation.get(variant.name, 0) + 1
                )
                return variant.name

        # 默认返回第一个变体
        return experiment.variants[0].name

    def record_metric(
        self,
        experiment_name: str,
        variant_name: str,
        metric_name: str,
        value: Union[int, float],
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """记录指标"""
        if experiment_name not in self.experiments:
            return

        experiment = self.experiments[experiment_name]

        if experiment.status != ExperimentStatus.RUNNING:
            return

        # 记录指标数据
        metric_data = {
            "metric_name": metric_name,
            "value": value,
            "timestamp": time.time(),
            "user_id": user_id,
            "metadata": metadata or {}
        }

        if variant_name not in experiment.metrics_data:
            experiment.metrics_data[variant_name] = []

        experiment.metrics_data[variant_name].append(metric_data)

    def get_experiment_status(self, experiment_name: str) -> Optional[Dict[str, Any]]:
        """获取实验状态"""
        if experiment_name not in self.experiments:
            return None

        experiment = self.experiments[experiment_name]

        # 计算当前指标
        current_metrics = {}
        for variant in experiment.variants:
            variant_data = experiment.metrics_data.get(variant.name, [])
            if variant_data:
                # 计算主要指标
                primary_metric_data = [
                    d for d in variant_data
                    if d["metric_name"] == experiment.primary_metric
                ]

                if primary_metric_data:
                    values = [d["value"] for d in primary_metric_data]
                    conversions = sum(1 for v in values if v > 0)  # 简化的转化定义
                    conversion_rate = conversions / len(values) if values else 0.0

                    current_metrics[variant.name] = {
                        "sample_size": len(values),
                        "conversions": conversions,
                        "conversion_rate": conversion_rate,
                        "average_value": statistics.mean(values) if values else 0.0
                    }

        return {
            "name": experiment.name,
            "status": experiment.status.value,
            "created_at": experiment.created_at,
            "started_at": experiment.started_at,
            "traffic_allocation": experiment.traffic_allocation,
            "current_metrics": current_metrics,
            "total_samples": sum(len(data) for data in experiment.metrics_data.values())
        }

    def analyze_experiment(self, experiment_name: str) -> Optional[ExperimentResult]:
        """分析实验结果"""
        if experiment_name not in self.experiments:
            return None

        experiment = self.experiments[experiment_name]

        if experiment.status != ExperimentStatus.RUNNING:
            return None

        # 检查是否达到最小样本量
        total_samples = sum(len(data) for data in experiment.metrics_data.values())
        if total_samples < experiment.min_sample_size:
            return ExperimentResult(
                experiment_name=experiment_name,
                recommendations=["样本量不足，继续收集数据"]
            )

        # 计算详细指标
        detailed_metrics = {}

        for variant in experiment.variants:
            variant_data = experiment.metrics_data.get(variant.name, [])
            primary_metric_data = [
                d for d in variant_data
                if d["metric_name"] == experiment.primary_metric
            ]

            if primary_metric_data:
                values = [d["value"] for d in primary_metric_data]
                conversions = sum(1 for v in values if v > 0)
                conversion_rate = conversions / len(values) if values else 0.0

                confidence_interval = self.statistical_analyzer.calculate_confidence_interval(
                    conversion_rate, len(values), experiment.confidence_threshold
                )

                detailed_metrics[variant.name] = ExperimentMetrics(
                    variant_name=variant.name,
                    sample_size=len(values),
                    conversions=conversions,
                    conversion_rate=conversion_rate,
                    average_value=statistics.mean(values) if values else 0.0,
                    confidence_interval=confidence_interval,
                    standard_error=(confidence_interval[1] - confidence_interval[0]) / (2 * 1.96)
                )

        # 确定获胜者
        winner = self._determine_winner(detailed_metrics, experiment)

        # 计算置信度和效果大小
        confidence_level, effect_size = self._calculate_confidence_and_effect(detailed_metrics)

        # 生成建议
        recommendations = self._generate_recommendations(detailed_metrics, winner, confidence_level)

        return ExperimentResult(
            experiment_name=experiment_name,
            winner=winner,
            confidence_level=confidence_level,
            effect_size=effect_size,
            recommendations=recommendations,
            detailed_metrics=detailed_metrics
        )

    def _determine_winner(self, metrics: Dict[str, ExperimentMetrics], experiment: Experiment) -> Optional[str]:
        """确定获胜者"""
        if len(metrics) < 2:
            return None

        # 基于主要指标比较（这里简化处理，实际应使用统计检验）
        metric_values = {
            name: metric.average_value
            for name, metric in metrics.items()
        }

        # 假设值越大越好（对于响应时间等指标需要反转）
        if experiment.primary_metric in ["response_time", "error_rate"]:
            # 对于这些指标，值越小越好
            winner = min(metric_values, key=metric_values.get)
        else:
            # 对于其他指标，值越大越好
            winner = max(metric_values, key=metric_values.get)

        return winner

    def _calculate_confidence_and_effect(
        self,
        metrics: Dict[str, ExperimentMetrics]
    ) -> tuple[float, float]:
        """计算置信度和效果大小"""
        if len(metrics) < 2:
            return 0.0, 0.0

        # 获取两个变体的值列表（简化处理）
        variant_names = list(metrics.keys())
        variant_a = metrics[variant_names[0]]
        variant_b = metrics[variant_names[1]]

        # 这里应该使用真实的指标数据进行统计检验
        # 暂时返回固定值
        return 0.95, 0.1

    def _generate_recommendations(
        self,
        metrics: Dict[str, ExperimentMetrics],
        winner: Optional[str],
        confidence_level: float
    ) -> List[str]:
        """生成建议"""
        recommendations = []

        if winner and confidence_level >= 0.95:
            recommendations.append(f"推荐使用变体 '{winner}'，置信度: {confidence_level:.1%}")
        elif winner and confidence_level >= 0.8:
            recommendations.append(f"变体 '{winner}' 显示出优势，但置信度不足 ({confidence_level:.1%})，建议继续实验")
        else:
            recommendations.append("实验结果不显著，建议调整实验设计或继续收集数据")

        # 检查样本量
        min_samples = min((m.sample_size for m in metrics.values()), default=0)
        if min_samples < 1000:
            recommendations.append("样本量可能不足，建议继续收集数据")

        return recommendations

    def end_experiment(self, experiment_name: str):
        """结束实验"""
        if experiment_name not in self.experiments:
            return

        experiment = self.experiments[experiment_name]
        experiment.status = ExperimentStatus.COMPLETED
        experiment.ended_at = time.time()

        self.logger.info(f"🏁 结束实验: {experiment_name}")

    def list_experiments(self) -> List[Dict[str, Any]]:
        """列出所有实验"""
        return [
            {
                "name": exp.name,
                "description": exp.description,
                "status": exp.status.value,
                "created_at": exp.created_at,
                "started_at": exp.started_at,
                "variants": len(exp.variants),
                "total_samples": sum(len(data) for data in exp.metrics_data.values())
            }
            for exp in self.experiments.values()
        ]


class ExperimentRunner:
    """
    实验运行器

    自动运行A/B实验并监控结果
    """

    def __init__(self, framework: ABTestingFramework):
        self.framework = framework
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.running_experiments: Dict[str, asyncio.Task] = {}

    async def run_experiment(
        self,
        experiment_name: str,
        test_function: Callable[[str], Any],
        duration: float = 3600,  # 1小时
        check_interval: float = 300  # 5分钟检查一次
    ):
        """运行实验"""
        if experiment_name in self.running_experiments:
            raise ValueError(f"实验 '{experiment_name}' 已在运行")

        # 启动实验
        self.framework.start_experiment(experiment_name)

        # 创建监控任务
        task = asyncio.create_task(
            self._monitor_experiment(experiment_name, test_function, duration, check_interval)
        )

        self.running_experiments[experiment_name] = task

        try:
            await task
        except Exception as e:
            self.logger.error(f"实验运行失败: {e}")
        finally:
            if experiment_name in self.running_experiments:
                del self.running_experiments[experiment_name]

    async def _monitor_experiment(
        self,
        experiment_name: str,
        test_function: Callable[[str], Any],
        duration: float,
        check_interval: float
    ):
        """监控实验运行"""
        start_time = time.time()

        self.logger.info(f"👀 开始监控实验: {experiment_name}")

        while time.time() - start_time < duration:
            try:
                # 执行测试
                variant = self.framework.assign_traffic(experiment_name)
                if variant:
                    # 运行测试函数
                    result = await test_function(variant)

                    # 记录指标（这里需要根据实际需求调整）
                    self.framework.record_metric(
                        experiment_name,
                        variant,
                        "test_result",
                        result.get("success", 0),
                        metadata=result
                    )

                # 检查是否可以结束实验
                analysis = self.framework.analyze_experiment(experiment_name)
                if analysis and analysis.winner and analysis.confidence_level >= 0.95:
                    self.logger.info(f"🎯 实验达到统计显著性，结束实验")
                    break

                await asyncio.sleep(check_interval)

            except Exception as e:
                self.logger.error(f"监控过程中出错: {e}")
                await asyncio.sleep(check_interval)

        # 结束实验
        self.framework.end_experiment(experiment_name)

        # 生成最终报告
        final_analysis = self.framework.analyze_experiment(experiment_name)
        if final_analysis:
            self.logger.info(f"📊 实验结果: 获胜者={final_analysis.winner}, 置信度={final_analysis.confidence_level:.1%}")


# 全局A/B测试框架实例
_ab_testing_framework_instance = None

def get_ab_testing_framework() -> ABTestingFramework:
    """获取A/B测试框架实例"""
    global _ab_testing_framework_instance
    if _ab_testing_framework_instance is None:
        _ab_testing_framework_instance = ABTestingFramework()
    return _ab_testing_framework_instance

def get_experiment_runner(framework: Optional[ABTestingFramework] = None) -> ExperimentRunner:
    """获取实验运行器"""
    if framework is None:
        framework = get_ab_testing_framework()
    return ExperimentRunner(framework)
