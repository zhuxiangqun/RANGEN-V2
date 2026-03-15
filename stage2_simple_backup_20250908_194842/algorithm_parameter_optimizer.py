"""
算法参数自学习优化系统
基于历史表现和性能指标动态调整算法参数
替代硬编码的算法参数配置
"""

import json
import logging
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import copy

logger = logging.getLogger(__name__)

@dataclass
class AlgorithmParameter:
    """算法参数配置"""
    name: str
    current_value: Any
    default_value: Any
    value_type: str  # 'float', 'int', 'list', 'dict'
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    description: str = ""
    category: str = "general"
    adaptability: float = get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))  # 自适应度 (0-1)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    last_optimized: datetime = field(default_factory=datetime.now)

@dataclass
class PerformanceRecord:
    """性能记录"""
    timestamp: datetime
    parameters_used: Dict[str, Any]
    metrics: Dict[str, float]
    context: Dict[str, Any]

class AlgorithmParameterOptimizer:
    """
    算法参数优化器
    基于性能监控和历史数据动态调整算法参数
    """

    def __init__(self):
        self.parameters: Dict[str, AlgorithmParameter] = {}
        self.performance_history: deque = deque(maxlen=2000)  # 保留最近2000条记录
        self.parameter_versions: List[Dict[str, Any]] = []
        self.learning_enabled = True
        self.auto_optimization_enabled = True

        # 初始化算法参数
        self._initialize_algorithm_parameters()

        # 保存初始版本
        self._save_parameter_version("initial")

        logger.info(f"✅ 算法参数优化器初始化完成，支持 {len(self.parameters)} 个参数")

    def _initialize_algorithm_parameters(self):
        """初始化算法参数"""
        algorithm_params = [
            # 性能阈值参数
            AlgorithmParameter(
                name="performance_improvement_threshold",
                current_value=1.05,
                default_value=1.05,
                value_type="float",
                min_value=1.01,
                max_value=1.2,
                description="性能改进阈值",
                category="performance",
                adaptability=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
            ),
            AlgorithmParameter(
                name="performance_decline_threshold",
                current_value=0.95,
                default_value=0.95,
                value_type="float",
                min_value=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
                max_value=0.99,
                description="性能下降阈值",
                category="performance",
                adaptability=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
            ),

            # 置信度参数
            AlgorithmParameter(
                name="confidence_base_score",
                current_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                default_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                value_type="float",
                min_value=0.1,
                max_value=0.9,
                description="置信度基础分数",
                category="confidence",
                adaptability=0.4
            ),

            # 权重参数
            AlgorithmParameter(
                name="relevance_weight",
                current_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                default_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                value_type="float",
                min_value=0.1,
                max_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                description="相关性权重",
                category="weights",
                adaptability=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
            ),
            AlgorithmParameter(
                name="accuracy_weight",
                current_value=0.4,
                default_value=0.4,
                value_type="float",
                min_value=0.2,
                max_value=0.6,
                description="准确性权重",
                category="weights",
                adaptability=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
            ),
            AlgorithmParameter(
                name="completeness_weight",
                current_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                default_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                value_type="float",
                min_value=0.1,
                max_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                description="完整性权重",
                category="weights",
                adaptability=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
            ),

            # 长度阈值参数
            AlgorithmParameter(
                name="answer_length_thresholds",
                current_value=[get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")), 50, 20, get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))],
                default_value=[get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")), 50, 20, get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))],
                value_type="list",
                description="答案长度阈值 [长,中,短,极短]",
                category="length",
                adaptability=0.2
            ),

            # 时间窗口参数
            AlgorithmParameter(
                name="recent_scores_window",
                current_value=get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                default_value=get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                value_type="int",
                min_value=5,
                max_value=50,
                description="最近分数窗口大小",
                category="window",
                adaptability=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
            ),
            AlgorithmParameter(
                name="older_scores_window",
                current_value=20,
                default_value=20,
                value_type="int",
                min_value=get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                max_value=get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")),
                description="较早分数窗口大小",
                category="window",
                adaptability=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
            ),

            # 因子参数
            AlgorithmParameter(
                name="score_adjustment_factor_up",
                current_value=1.05,
                default_value=1.05,
                value_type="float",
                min_value=1.01,
                max_value=1.2,
                description="分数上调因子",
                category="factors",
                adaptability=0.4
            ),
            AlgorithmParameter(
                name="score_adjustment_factor_down",
                current_value=0.95,
                default_value=0.95,
                value_type="float",
                min_value=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
                max_value=0.99,
                description="分数下调因子",
                category="factors",
                adaptability=0.4
            ),

            # 相似度参数
            AlgorithmParameter(
                name="similarity_boost_factor",
                current_value=0.2,
                default_value=0.2,
                value_type="float",
                min_value=0.1,
                max_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                description="相似度提升因子",
                category="similarity",
                adaptability=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
            ),

            # 时间衰减参数
            AlgorithmParameter(
                name="time_decay_factor",
                current_value=0.9,
                default_value=0.9,
                value_type="float",
                min_value=0.7,
                max_value=0.99,
                description="时间衰减因子",
                category="temporal",
                adaptability=0.2
            ),

            # 句子复杂度参数
            AlgorithmParameter(
                name="sentence_complexity_threshold",
                current_value=0.7,
                default_value=0.7,
                value_type="float",
                min_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                max_value=0.9,
                description="句子复杂度阈值",
                category="complexity",
                adaptability=0.4
            ),

            # 最小词数参数
            AlgorithmParameter(
                name="min_word_count",
                current_value=5,
                default_value=5,
                value_type="int",
                min_value=3,
                max_value=15,
                description="最小词数",
                category="content",
                adaptability=0.2
            ),
        ]

        for param in algorithm_params:
            self.parameters[param.name] = param

    def get_parameter(self, name: str) -> Any:
        """
        获取参数值
        """
        if name in self.parameters:
            return self.parameters[name].current_value
        else:
            logger.warning(f"算法参数 {name} 不存在，使用默认值 None")
            return None

    def record_performance(self, metrics: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
        """
        记录性能指标
        """
        if not self.learning_enabled:
            return

        # 创建性能记录
        record = PerformanceRecord(
            timestamp=datetime.now(),
            parameters_used={name: param.current_value for name, param in self.parameters.items()},
            metrics=metrics,
            context=context or {}
        )

        # 添加到历史记录
        self.performance_history.append(record)

        # 如果启用了自动优化且有足够数据，进行优化
        if self.auto_optimization_enabled and len(self.performance_history) >= 30:
            self._optimize_parameters()

    def _optimize_parameters(self):
        """
        基于性能历史优化参数
        """
        if len(self.performance_history) < 30:
            return

        # 分析性能趋势
        trends = self._analyze_performance_trends()

        # 基于趋势优化不同类别的参数
        self._optimize_performance_parameters(trends)
        self._optimize_weight_parameters(trends)
        self._optimize_window_parameters(trends)
        self._optimize_factor_parameters(trends)

        # 保存优化后的版本
        self._save_parameter_version("auto_optimized")

    def _analyze_performance_trends(self) -> Dict[str, float]:
        """
        分析性能趋势
        """
        if len(self.performance_history) < get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
            return {}

        # 获取最近的性能记录
        recent_records = list(self.performance_history)[-50:]

        trends = {}

        # 计算各项指标的趋势
        metrics_to_analyze = ['accuracy', 'response_time', 'success_rate', 'quality_score']

        for metric in metrics_to_analyze:
            values = [r.metrics.get(metric, get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for r in recent_records if metric in r.metrics]
            if len(values) >= get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
                trend = self._calculate_trend(values)
                trends[f"{metric}_trend"] = trend

        return trends

    def _calculate_trend(self, values: List[float]) -> float:
        """
        计算趋势值
        """
        if len(values) < 5:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

        # 使用线性回归计算趋势
        n = len(values)
        x = list(range(n))
        y = values

        # 计算斜率 (趋势)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_xx = sum(xi * xi for xi in x)

        if n * sum_xx - sum_x * sum_x == 0:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
        return slope

    def _optimize_performance_parameters(self, trends: Dict[str, float]):
        """
        优化性能参数
        """
        accuracy_trend = trends.get('accuracy_trend', 0)

        # 优化性能改进阈值
        if 'performance_improvement_threshold' in self.parameters:
            param = self.parameters['performance_improvement_threshold']
            if accuracy_trend > 0.01:  # 准确率上升
                # 稍微提高阈值
                new_value = param.current_value * 1.01
            elif accuracy_trend < -0.01:  # 准确率下降
                # 降低阈值
                new_value = param.current_value * 0.99

            new_value = max(param.min_value, min(param.max_value, new_value))
            if abs(new_value - param.current_value) > 0.001:
                self._update_parameter_value(param.name, new_value, "performance_trend")

        # 优化性能下降阈值
        if 'performance_decline_threshold' in self.parameters:
            param = self.parameters['performance_decline_threshold']
            if accuracy_trend < -0.02:  # 准确率显著下降
                # 提高阈值以减少误报
                new_value = param.current_value * 1.02
            elif accuracy_trend > 0.02:  # 准确率显著上升
                # 降低阈值以提高敏感度
                new_value = param.current_value * 0.98

            new_value = max(param.min_value, min(param.max_value, new_value))
            if abs(new_value - param.current_value) > 0.001:
                self._update_parameter_value(param.name, new_value, "performance_trend")

    def _optimize_weight_parameters(self, trends: Dict[str, float]):
        """
        优化权重参数
        """
        accuracy_trend = trends.get('accuracy_trend', 0)
        quality_trend = trends.get('quality_score_trend', 0)

        weight_params = ['relevance_weight', 'accuracy_weight', 'completeness_weight']

        for param_name in weight_params:
            if param_name not in self.parameters:
                continue

            param = self.parameters[param_name]

            # 根据准确率趋势调整权重
            if accuracy_trend > 0.01 and 'accuracy' in param_name:
                # 准确率上升，增加准确性权重
                new_value = param.current_value * 1.05
            elif quality_trend > 0.01 and 'completeness' in param_name:
                # 质量上升，增加完整性权重
                new_value = param.current_value * 1.03
            elif accuracy_trend < -0.01:
                # 准确率下降，微调权重
                new_value = param.current_value * 0.98
            else:
                continue

            new_value = max(param.min_value, min(param.max_value, new_value))
            if abs(new_value - param.current_value) > 0.001:
                self._update_parameter_value(param.name, new_value, "weight_optimization")

    def _optimize_window_parameters(self, trends: Dict[str, float]):
        """
        优化窗口参数
        """
        response_time_trend = trends.get('response_time_trend', 0)

        window_params = ['recent_scores_window', 'older_scores_window']

        for param_name in window_params:
            if param_name not in self.parameters:
                continue

            param = self.parameters[param_name]

            # 根据响应时间趋势调整窗口大小
            if response_time_trend > 0.1:  # 响应时间增加
                # 减小窗口以提高响应速度
                new_value = int(param.current_value * 0.9)
            elif response_time_trend < -0.1:  # 响应时间减少
                # 增大窗口以提高准确性
                new_value = int(param.current_value * 1.1)
            else:
                continue

            new_value = max(param.min_value, min(param.max_value, new_value))
            if new_value != param.current_value:
                self._update_parameter_value(param.name, new_value, "window_optimization")

    def _optimize_factor_parameters(self, trends: Dict[str, float]):
        """
        优化因子参数
        """
        success_rate_trend = trends.get('success_rate_trend', 0)

        factor_params = ['score_adjustment_factor_up', 'score_adjustment_factor_down', 'similarity_boost_factor']

        for param_name in factor_params:
            if param_name not in self.parameters:
                continue

            param = self.parameters[param_name]

            # 根据成功率趋势调整因子
            if success_rate_trend > 0.02:
                if 'up' in param_name:
                    # 成功率上升，稍微增加上调因子
                    new_value = param.current_value * 1.01
                elif 'down' in param_name:
                    # 成功率上升，可以稍微减少下调因子
                    new_value = param.current_value * 1.005
            elif success_rate_trend < -0.02:
                if 'up' in param_name:
                    # 成功率下降，减少上调因子
                    new_value = param.current_value * 0.99
                elif 'down' in param_name:
                    # 成功率下降，增加下调因子
                    new_value = param.current_value * 0.995
            else:
                continue

            new_value = max(param.min_value, min(param.max_value, new_value))
            if abs(new_value - param.current_value) > 0.001:
                self._update_parameter_value(param.name, new_value, "factor_optimization")

    def _update_parameter_value(self, param_name: str, new_value: Any, reason: str):
        """
        更新参数值
        """
        if param_name in self.parameters:
            old_value = self.parameters[param_name].current_value

            # 记录参数变更历史
            history_record = {
                'timestamp': datetime.now(),
                'old_value': old_value,
                'new_value': new_value,
                'reason': reason,
                'performance_context': self._get_current_performance_context()
            }

            self.parameters[param_name].performance_history.append(history_record)
            self.parameters[param_name].current_value = new_value
            self.parameters[param_name].last_optimized = datetime.now()

            logger.info(f"🔧 算法参数调整: {param_name} {old_value} → {new_value} ({reason})")

    def _get_current_performance_context(self) -> Dict[str, Any]:
        """
        获取当前性能上下文
        """
        if not self.performance_history:
            return {}

        recent_records = list(self.performance_history)[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]
        context = {}

        metrics = ['accuracy', 'response_time', 'success_rate', 'quality_score']
        for metric in metrics:
            values = [r.metrics.get(metric, get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for r in recent_records if metric in r.metrics]
            if values:
                context[f"{metric}_avg"] = statistics.mean(values)
                context[f"{metric}_trend"] = self._calculate_trend(values)

        return context

    def _save_parameter_version(self, version_name: str):
        """
        保存参数版本
        """
        version = {
            'version_name': version_name,
            'timestamp': datetime.now().isoformat(),
            'parameters': {name: param.current_value for name, param in self.parameters.items()},
            'performance_stats': self._get_current_performance_context()
        }

        self.parameter_versions.append(version)
        logger.info(f"💾 参数版本已保存: {version_name}")

    def get_parameter_recommendations(self) -> Dict[str, Any]:
        """
        获取参数优化建议
        """
        recommendations = {
            'immediate_actions': [],
            'parameter_analysis': {},
            'optimization_suggestions': []
        }

        # 分析每个参数的性能表现
        for param_name, param in self.parameters.items():
            if len(param.performance_history) >= 5:
                analysis = self._analyze_parameter_performance(param)
                recommendations['parameter_analysis'][param_name] = analysis

                # 生成优化建议
                if analysis.get('needs_optimization', False):
                    recommendations['immediate_actions'].append({
                        'parameter': param_name,
                        'action': analysis.get('recommended_action', 'review'),
                        'confidence': analysis.get('confidence', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
                    })

        # 生成全局优化建议
        global_suggestions = self._generate_global_optimization_suggestions()
        recommendations['optimization_suggestions'] = global_suggestions

        return recommendations

    def _analyze_parameter_performance(self, param: AlgorithmParameter) -> Dict[str, Any]:
        """
        分析单个参数的性能表现
        """
        analysis = {
            'current_value': param.current_value,
            'history_length': len(param.performance_history),
            'needs_optimization': False,
            'recommended_action': 'maintain',
            'confidence': get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
        }

        if len(param.performance_history) < 5:
            return analysis

        # 分析参数调整的效果
        recent_history = param.performance_history[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]

        # 计算调整成功率
        successful_adjustments = 0
        total_adjustments = len(recent_history)

        for record in recent_history:
            # 这里可以根据实际的性能指标来判断调整是否成功
            # 简化的判断逻辑
            performance_context = record.get('performance_context', {})
            accuracy_trend = performance_context.get('accuracy_trend', 0)

            if record['reason'] != 'manual' and abs(accuracy_trend) < 0.05:
                successful_adjustments += 1

        success_rate = successful_adjustments / total_adjustments if total_adjustments > 0 else 0

        if success_rate > 0.7:
            analysis['recommended_action'] = 'continue_auto_optimization'
            analysis['confidence'] = success_rate
        elif success_rate < get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")):
            analysis['needs_optimization'] = True
            analysis['recommended_action'] = 'review_manual_optimization'
            analysis['confidence'] = 1 - success_rate

        return analysis

    def _generate_global_optimization_suggestions(self) -> List[str]:
        """
        生成全局优化建议
        """
        suggestions = []

        # 基于整体性能趋势生成建议
        if len(self.performance_history) >= 20:
            trends = self._analyze_performance_trends()

            if trends.get('accuracy_trend', 0) > 0.02:
                suggestions.append("系统准确率呈上升趋势，建议继续当前的优化策略")
            elif trends.get('accuracy_trend', 0) < -0.02:
                suggestions.append("系统准确率呈下降趋势，建议检查参数调整逻辑")

            if trends.get('response_time_trend', 0) > 0.1:
                suggestions.append("系统响应时间增加，建议优化窗口参数或减少计算复杂度")

            if trends.get('success_rate_trend', 0) < -0.05:
                suggestions.append("系统成功率下降，建议调整权重参数和阈值")

        # 基于参数调整历史生成建议
        total_optimizations = sum(len(param.performance_history) for param in self.parameters.values())
        if total_optimizations > 50:
            suggestions.append("系统已进行大量参数优化，建议进行一次全面的参数评估")

        return suggestions

    def export_configuration(self, filepath: str):
        """
        导出当前配置
        """
        config = {
            'export_time': datetime.now().isoformat(),
            'current_parameters': {name: param.current_value for name, param in self.parameters.items()},
            'parameter_versions': self.parameter_versions[-5:],  # 只导出最近5个版本
            'performance_summary': self._get_performance_summary(),
            'optimization_stats': {
                'total_optimizations': sum(len(param.performance_history) for param in self.parameters.values()),
                'learning_enabled': self.learning_enabled,
                'auto_optimization_enabled': self.auto_optimization_enabled
            }
        }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False, default=str)
            logger.info(f"✅ 算法参数配置已导出到: {filepath}")
        except Exception as e:
            logger.error(f"❌ 导出配置失败: {e}")

    def _get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要
        """
        if not self.performance_history:
            return {}

        recent_records = list(self.performance_history)[-50:]
        summary = {}

        metrics = ['accuracy', 'response_time', 'success_rate', 'quality_score']

        for metric in metrics:
            values = [r.metrics.get(metric) for r in recent_records if r.metrics.get(metric) is not None]
            if values:
                summary[f"{metric}_avg"] = statistics.mean(values)
                summary[f"{metric}_std"] = statistics.stdev(values) if len(values) > 1 else 0
                summary[f"{metric}_trend"] = self._calculate_trend(values)

        return summary

    def reset_parameters(self):
        """
        重置所有参数为默认值
        """
        for param in self.parameters.values():
            param.current_value = param.default_value
            param.performance_history.clear()
            param.last_optimized = datetime.now()

        # 保存重置版本
        self._save_parameter_version("reset")

        logger.info("🔄 所有算法参数已重置为默认值")

    def get_parameter_report(self) -> Dict[str, Any]:
        """
        获取参数报告
        """
        report = {
            'parameter_summary': {},
            'optimization_effectiveness': {},
            'performance_correlations': {},
            'recommendations': self.get_parameter_recommendations()
        }

        # 参数摘要
        for name, param in self.parameters.items():
            report['parameter_summary'][name] = {
                'current_value': param.current_value,
                'default_value': param.default_value,
                'category': param.category,
                'adaptability': param.adaptability,
                'optimizations_count': len(param.performance_history),
                'last_optimized': param.last_optimized.isoformat()
            }

        # 优化效果分析
        optimization_effectiveness = {}
        for name, param in self.parameters.items():
            if param.performance_history:
                # 计算优化成功率
                successful_optimizations = sum(1 for record in param.performance_history
                                             if record.get('reason') != 'manual')
                total_optimizations = len(param.performance_history)
                success_rate = successful_optimizations / total_optimizations if total_optimizations > 0 else 0
                optimization_effectiveness[name] = success_rate

        report['optimization_effectiveness'] = optimization_effectiveness

        return report


# 全局算法参数优化器实例
_algorithm_optimizer = None

def get_algorithm_parameter_optimizer() -> AlgorithmParameterOptimizer:
    """获取算法参数优化器实例"""
    global _algorithm_optimizer
    if _algorithm_optimizer is None:
        _algorithm_optimizer = AlgorithmParameterOptimizer()
    return _algorithm_optimizer

# 便捷函数
def get_algorithm_param(name: str) -> Any:
    """获取算法参数值"""
    return get_algorithm_parameter_optimizer().get_parameter(name)

def record_algorithm_performance(metrics: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
    """记录算法性能指标"""
    get_algorithm_parameter_optimizer().record_performance(metrics, context)
