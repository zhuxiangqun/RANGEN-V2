"""
反馈闭环机制 (Feedback Loop Mechanism)

实现系统的持续学习和改进：
- 性能监控和指标收集
- 反馈数据分析和洞察
- 自动优化策略调整
- 学习成果的应用和验证
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""
    PERFORMANCE = "performance"      # 性能反馈
    ACCURACY = "accuracy"           # 准确性反馈
    USER_SATISFACTION = "user_satisfaction"  # 用户满意度反馈
    SYSTEM_HEALTH = "system_health" # 系统健康反馈
    RESOURCE_USAGE = "resource_usage" # 资源使用反馈


class FeedbackPriority(Enum):
    """反馈优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class LearningAction(Enum):
    """学习行动"""
    PARAMETER_ADJUSTMENT = "parameter_adjustment"  # 参数调整
    STRATEGY_SWITCH = "strategy_switch"           # 策略切换
    COMPONENT_RECONFIGURATION = "component_reconfig"  # 组件重配置
    SYSTEM_OPTIMIZATION = "system_optimization"   # 系统优化
    NO_ACTION = "no_action"                       # 无需行动


@dataclass
class FeedbackData:
    """反馈数据"""
    feedback_id: str
    feedback_type: FeedbackType
    source_component: str
    target_component: Optional[str]
    metrics: Dict[str, Any]
    context: Dict[str, Any]
    priority: FeedbackPriority = FeedbackPriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'feedback_id': self.feedback_id,
            'feedback_type': self.feedback_type.value,
            'source_component': self.source_component,
            'target_component': self.target_component,
            'metrics': self.metrics,
            'context': self.context,
            'priority': self.priority.value,
            'timestamp': self.timestamp.isoformat(),
            'tags': list(self.tags)
        }


@dataclass
class LearningInsight:
    """学习洞察"""
    insight_id: str
    component: str
    insight_type: str
    description: str
    confidence_score: float
    supporting_data: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]
    generated_at: datetime = field(default_factory=datetime.now)
    applied: bool = False
    application_result: Optional[Dict[str, Any]] = None


@dataclass
class FeedbackAnalysis:
    """反馈分析结果"""
    analysis_id: str
    time_window: Tuple[datetime, datetime]
    component: str
    feedback_summary: Dict[str, Any]
    trend_analysis: Dict[str, Any]
    anomaly_detection: List[Dict[str, Any]]
    insights_generated: List[LearningInsight]
    recommendations: List[Dict[str, Any]]
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class FeedbackCollector:
    """反馈收集器"""

    def __init__(self, max_feedback_history: int = 10000):
        self.feedback_history: deque = deque(maxlen=max_feedback_history)
        self.active_collectors: Dict[str, Callable] = {}
        self.collection_intervals: Dict[str, float] = {}
        self._running = False
        self._collection_tasks: Dict[str, asyncio.Task] = {}

    async def start_collection(self):
        """启动反馈收集"""
        if self._running:
            return

        self._running = True

        # 启动所有收集器
        for collector_name, collector_func in self.active_collectors.items():
            interval = self.collection_intervals.get(collector_name, 60.0)  # 默认60秒
            task = asyncio.create_task(self._run_collector(collector_name, collector_func, interval))
            self._collection_tasks[collector_name] = task

        logger.info(f"反馈收集器已启动，{len(self.active_collectors)}个收集器正在运行")

    async def stop_collection(self):
        """停止反馈收集"""
        if not self._running:
            return

        self._running = False

        # 取消所有收集任务
        for task in self._collection_tasks.values():
            task.cancel()

        # 等待任务完成
        await asyncio.gather(*self._collection_tasks.values(), return_exceptions=True)

        logger.info("反馈收集器已停止")

    def register_collector(self, name: str, collector_func: Callable,
                          interval: float = 60.0):
        """注册反馈收集器"""
        self.active_collectors[name] = collector_func
        self.collection_intervals[name] = interval
        logger.info(f"注册反馈收集器: {name}, 间隔: {interval}秒")

    async def collect_feedback(self, feedback: FeedbackData):
        """收集反馈数据"""
        self.feedback_history.append(feedback)

        # 添加到组件特定的历史记录（用于分析）
        logger.debug(f"收集反馈: {feedback.feedback_type.value} from {feedback.source_component}")

    def get_recent_feedback(self, component: Optional[str] = None,
                           feedback_type: Optional[FeedbackType] = None,
                           hours: int = 24) -> List[FeedbackData]:
        """获取最近的反馈数据"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_feedback = [
            f for f in self.feedback_history
            if f.timestamp > cutoff_time
        ]

        if component:
            recent_feedback = [f for f in recent_feedback if f.source_component == component]

        if feedback_type:
            recent_feedback = [f for f in recent_feedback if f.feedback_type == feedback_type]

        return recent_feedback

    async def _run_collector(self, name: str, collector_func: Callable, interval: float):
        """运行收集器"""
        while self._running:
            try:
                feedback_data = await collector_func()
                if feedback_data:
                    if isinstance(feedback_data, list):
                        for feedback in feedback_data:
                            await self.collect_feedback(feedback)
                    else:
                        await self.collect_feedback(feedback_data)

            except Exception as e:
                logger.error(f"收集器 {name} 出错: {e}")

            await asyncio.sleep(interval)


class FeedbackAnalyzer:
    """反馈分析器"""

    def __init__(self):
        self.analysis_history: List[FeedbackAnalysis] = []
        self.baseline_metrics: Dict[str, Dict[str, float]] = {}
        self.anomaly_thresholds: Dict[str, Dict[str, float]] = {}

    async def analyze_feedback(self, component: str,
                              time_window_hours: int = 24) -> FeedbackAnalysis:
        """分析反馈数据"""
        # 获取时间窗口内的反馈
        feedback_data = self.get_recent_feedback(component, time_window_hours)

        if not feedback_data:
            return self._create_empty_analysis(component, time_window_hours)

        # 执行各种分析
        summary = await self._summarize_feedback(feedback_data)
        trends = await self._analyze_trends(feedback_data)
        anomalies = await self._detect_anomalies(feedback_data, component)
        insights = await self._generate_insights(feedback_data, component)
        recommendations = await self._generate_recommendations(insights, component)

        analysis = FeedbackAnalysis(
            analysis_id=f"analysis_{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            time_window=(datetime.now() - timedelta(hours=time_window_hours), datetime.now()),
            component=component,
            feedback_summary=summary,
            trend_analysis=trends,
            anomaly_detection=anomalies,
            insights_generated=insights,
            recommendations=recommendations
        )

        self.analysis_history.append(analysis)
        return analysis

    def get_recent_feedback(self, component: str, hours: int) -> List[FeedbackData]:
        """获取最近反馈数据（需要注入反馈收集器）"""
        # 这里需要与FeedbackCollector集成
        # 暂时返回空列表，实际使用时需要注入collector
        return []

    async def _summarize_feedback(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """汇总反馈数据"""
        if not feedback_data:
            return {}

        # 按类型分组
        type_counts = defaultdict(int)
        metric_aggregates = defaultdict(list)

        for feedback in feedback_data:
            type_counts[feedback.feedback_type.value] += 1

            # 聚合指标
            for metric_name, metric_value in feedback.metrics.items():
                if isinstance(metric_value, (int, float)):
                    metric_aggregates[metric_name].append(metric_value)

        # 计算统计信息
        summary = {
            'total_feedback': len(feedback_data),
            'feedback_types': dict(type_counts),
            'time_span': {
                'start': min(f.timestamp for f in feedback_data),
                'end': max(f.timestamp for f in feedback_data)
            }
        }

        # 添加指标统计
        for metric_name, values in metric_aggregates.items():
            if values:
                summary[f'{metric_name}_stats'] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0
                }

        return summary

    async def _analyze_trends(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """分析趋势"""
        if len(feedback_data) < 2:
            return {'insufficient_data': True}

        # 按时间排序
        sorted_feedback = sorted(feedback_data, key=lambda f: f.timestamp)

        # 计算时间序列趋势
        trends = {}

        # 对于数值型指标，计算趋势
        metric_series = defaultdict(list)
        for feedback in sorted_feedback:
            for metric_name, metric_value in feedback.metrics.items():
                if isinstance(metric_value, (int, float)):
                    metric_series[metric_name].append((feedback.timestamp, metric_value))

        for metric_name, series in metric_series.items():
            if len(series) >= 3:
                # 简单线性趋势分析
                x_values = [(t - series[0][0]).total_seconds() for t, _ in series]
                y_values = [v for _, v in series]

                # 计算趋势斜率（简化版）
                if len(x_values) > 1:
                    slope = (y_values[-1] - y_values[0]) / (x_values[-1] - x_values[0])
                    trends[metric_name] = {
                        'slope': slope,
                        'direction': 'improving' if slope > 0 else 'degrading' if slope < 0 else 'stable',
                        'magnitude': abs(slope)
                    }

        return trends

    async def _detect_anomalies(self, feedback_data: List[FeedbackData],
                               component: str) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []

        if component not in self.baseline_metrics:
            # 建立基线
            await self._establish_baseline(component, feedback_data)
            return anomalies

        baseline = self.baseline_metrics[component]
        thresholds = self.anomaly_thresholds.get(component, {})

        for feedback in feedback_data:
            for metric_name, metric_value in feedback.metrics.items():
                if isinstance(metric_value, (int, float)) and metric_name in baseline:
                    expected_mean = baseline[metric_name]
                    threshold = thresholds.get(metric_name, expected_mean * 0.5)  # 默认50%阈值

                    deviation = abs(metric_value - expected_mean)
                    if deviation > threshold:
                        anomaly = {
                            'feedback_id': feedback.feedback_id,
                            'metric': metric_name,
                            'expected_value': expected_mean,
                            'actual_value': metric_value,
                            'deviation': deviation,
                            'severity': 'high' if deviation > threshold * 2 else 'medium',
                            'timestamp': feedback.timestamp
                        }
                        anomalies.append(anomaly)

        return anomalies

    async def _establish_baseline(self, component: str, feedback_data: List[FeedbackData]):
        """建立基线"""
        metric_values = defaultdict(list)

        for feedback in feedback_data[-100:]:  # 使用最近100个反馈建立基线
            for metric_name, metric_value in feedback.metrics.items():
                if isinstance(metric_value, (int, float)):
                    metric_values[metric_name].append(metric_value)

        baseline = {}
        thresholds = {}

        for metric_name, values in metric_values.items():
            if len(values) >= 10:  # 需要足够的样本
                mean_val = statistics.mean(values)
                std_dev = statistics.stdev(values) if len(values) > 1 else 0

                baseline[metric_name] = mean_val
                thresholds[metric_name] = std_dev * 2  # 2倍标准差作为异常阈值

        self.baseline_metrics[component] = baseline
        self.anomaly_thresholds[component] = thresholds

    async def _generate_insights(self, feedback_data: List[FeedbackData],
                               component: str) -> List[LearningInsight]:
        """生成学习洞察"""
        insights = []

        # 分析模式和趋势
        summary = await self._summarize_feedback(feedback_data)
        trends = await self._analyze_trends(feedback_data)

        # 生成洞察
        insight_id = f"insight_{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 性能洞察
        if 'performance' in trends:
            perf_trend = trends['performance']
            if perf_trend['direction'] == 'degrading':
                insight = LearningInsight(
                    insight_id=f"{insight_id}_perf_degrade",
                    component=component,
                    insight_type="performance_degradation",
                    description=f"检测到性能下降趋势，下降率: {perf_trend['slope']:.4f}",
                    confidence_score=0.8,
                    supporting_data={'trend': perf_trend},
                    recommended_actions=[{
                        'action': LearningAction.PARAMETER_ADJUSTMENT.value,
                        'description': '调整性能相关参数',
                        'parameters': ['timeout', 'batch_size']
                    }]
                )
                insights.append(insight)

        # 使用模式洞察
        usage_patterns = self._analyze_usage_patterns(feedback_data)
        if usage_patterns.get('bottleneck_detected', False):
            insight = LearningInsight(
                insight_id=f"{insight_id}_bottleneck",
                component=component,
                insight_type="resource_bottleneck",
                description="检测到资源瓶颈模式",
                confidence_score=0.75,
                supporting_data=usage_patterns,
                recommended_actions=[{
                    'action': LearningAction.SYSTEM_OPTIMIZATION.value,
                    'description': '优化资源分配策略',
                    'target': 'resource_manager'
                }]
            )
            insights.append(insight)

        return insights

    async def _generate_recommendations(self, insights: List[LearningInsight],
                                      component: str) -> List[Dict[str, Any]]:
        """生成推荐行动"""
        recommendations = []

        for insight in insights:
            for action in insight.recommended_actions:
                recommendation = {
                    'insight_id': insight.insight_id,
                    'component': component,
                    'action_type': action['action'],
                    'description': action['description'],
                    'priority': 'high' if insight.confidence_score > 0.8 else 'medium',
                    'expected_impact': insight.confidence_score * 0.7,  # 简化计算
                    'implementation_complexity': 'low' if action['action'] == LearningAction.PARAMETER_ADJUSTMENT.value else 'medium'
                }

                if 'parameters' in action:
                    recommendation['affected_parameters'] = action['parameters']
                if 'target' in action:
                    recommendation['target_component'] = action['target']

                recommendations.append(recommendation)

        return recommendations

    def _analyze_usage_patterns(self, feedback_data: List[FeedbackData]) -> Dict[str, Any]:
        """分析使用模式"""
        patterns = {
            'bottleneck_detected': False,
            'peak_usage_times': [],
            'resource_pressure': 0.0
        }

        # 简化的模式分析
        resource_usage = []
        for feedback in feedback_data:
            if feedback.feedback_type == FeedbackType.RESOURCE_USAGE:
                usage = feedback.metrics.get('cpu_usage', 0) + feedback.metrics.get('memory_usage', 0)
                resource_usage.append(usage)

        if resource_usage:
            avg_usage = statistics.mean(resource_usage)
            max_usage = max(resource_usage)

            if max_usage > avg_usage * 1.5:  # 峰值明显高于平均值
                patterns['bottleneck_detected'] = True
                patterns['resource_pressure'] = (max_usage - avg_usage) / avg_usage

        return patterns


class LearningApplier:
    """学习应用器"""

    def __init__(self):
        self.applied_insights: Dict[str, LearningInsight] = {}
        self.application_results: List[Dict[str, Any]] = []

    async def apply_insight(self, insight: LearningInsight) -> Dict[str, Any]:
        """应用学习洞察"""
        application_id = f"apply_{insight.insight_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 记录应用尝试
        application_record = {
            'application_id': application_id,
            'insight_id': insight.insight_id,
            'component': insight.component,
            'applied_at': datetime.now(),
            'actions_taken': []
        }

        try:
            # 执行推荐行动
            for action in insight.recommended_actions:
                action_result = await self._execute_action(action, insight.component)
                application_record['actions_taken'].append(action_result)

            # 标记洞察为已应用
            insight.applied = True
            insight.application_result = application_record

            self.applied_insights[insight.insight_id] = insight

            application_record['status'] = 'success'

        except Exception as e:
            logger.error(f"应用洞察失败 {insight.insight_id}: {e}")
            application_record['status'] = 'failed'
            application_record['error'] = str(e)

        self.application_results.append(application_record)
        return application_record

    async def _execute_action(self, action: Dict[str, Any], component: str) -> Dict[str, Any]:
        """执行具体行动"""
        action_type = action.get('action')

        if action_type == LearningAction.PARAMETER_ADJUSTMENT.value:
            return await self._adjust_parameters(component, action)
        elif action_type == LearningAction.STRATEGY_SWITCH.value:
            return await self._switch_strategy(component, action)
        elif action_type == LearningAction.SYSTEM_OPTIMIZATION.value:
            return await self._optimize_system(component, action)
        else:
            return {
                'action': action_type,
                'status': 'unknown_action_type',
                'component': component
            }

    async def _adjust_parameters(self, component: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """调整参数"""
        parameters = action.get('parameters', [])

        # 这里应该调用实际的参数调整逻辑
        # 暂时返回模拟结果
        return {
            'action': 'parameter_adjustment',
            'component': component,
            'parameters_adjusted': parameters,
            'status': 'simulated_success'
        }

    async def _switch_strategy(self, component: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """切换策略"""
        # 这里应该调用实际的策略切换逻辑
        return {
            'action': 'strategy_switch',
            'component': component,
            'status': 'simulated_success'
        }

    async def _optimize_system(self, component: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """系统优化"""
        # 这里应该调用实际的系统优化逻辑
        return {
            'action': 'system_optimization',
            'component': component,
            'status': 'simulated_success'
        }

    def get_application_statistics(self) -> Dict[str, Any]:
        """获取应用统计"""
        total_applications = len(self.application_results)
        successful_applications = len([r for r in self.application_results if r['status'] == 'success'])

        return {
            'total_applications': total_applications,
            'successful_applications': successful_applications,
            'success_rate': successful_applications / total_applications if total_applications > 0 else 0,
            'applied_insights': len(self.applied_insights)
        }


class FeedbackLoopMechanism:
    """
    反馈闭环机制

    实现完整的反馈收集、分析、学习和应用循环：
    - 自动反馈收集
    - 智能反馈分析
    - 学习洞察生成
    - 自动优化应用
    - 效果验证和改进
    """

    def __init__(self):
        self.feedback_collector = FeedbackCollector()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.learning_applier = LearningApplier()

        self.learning_loop_active = False
        self.analysis_interval = 3600  # 1小时分析一次
        self.learning_interval = 7200  # 2小时学习一次

        self.monitored_components: Set[str] = set()

    async def start_feedback_loop(self):
        """启动反馈闭环"""
        if self.learning_loop_active:
            return

        self.learning_loop_active = True

        # 启动反馈收集
        await self.feedback_collector.start_collection()

        # 启动学习循环
        asyncio.create_task(self._learning_loop())

        logger.info("反馈闭环机制已启动")

    async def stop_feedback_loop(self):
        """停止反馈闭环"""
        if not self.learning_loop_active:
            return

        self.learning_loop_active = False

        # 停止反馈收集
        await self.feedback_collector.stop_collection()

        logger.info("反馈闭环机制已停止")

    def register_component_monitoring(self, component: str,
                                    feedback_collectors: Optional[List[Tuple[str, Callable, float]]] = None):
        """注册组件监控"""
        self.monitored_components.add(component)

        # 注册反馈收集器
        if feedback_collectors:
            for collector_name, collector_func, interval in feedback_collectors:
                self.feedback_collector.register_collector(
                    f"{component}_{collector_name}",
                    collector_func,
                    interval
                )

        logger.info(f"注册组件监控: {component}")

    async def submit_feedback(self, feedback: FeedbackData):
        """提交反馈数据"""
        await self.feedback_collector.collect_feedback(feedback)

    async def trigger_analysis(self, component: Optional[str] = None,
                              time_window_hours: int = 24) -> List[FeedbackAnalysis]:
        """触发反馈分析"""
        analyses = []

        components_to_analyze = [component] if component else list(self.monitored_components)

        for comp in components_to_analyze:
            try:
                analysis = await self.feedback_analyzer.analyze_feedback(comp, time_window_hours)
                analyses.append(analysis)

                # 自动应用高置信度洞察
                await self._auto_apply_insights(analysis)

            except Exception as e:
                logger.error(f"分析组件 {comp} 失败: {e}")

        return analyses

    async def _auto_apply_insights(self, analysis: FeedbackAnalysis):
        """自动应用洞察"""
        for insight in analysis.insights_generated:
            if insight.confidence_score > 0.8:  # 高置信度自动应用
                try:
                    application_result = await self.learning_applier.apply_insight(insight)
                    logger.info(f"自动应用洞察 {insight.insight_id}: {application_result['status']}")
                except Exception as e:
                    logger.error(f"自动应用洞察失败 {insight.insight_id}: {e}")

    async def _learning_loop(self):
        """学习循环"""
        while self.learning_loop_active:
            try:
                # 定期分析
                await asyncio.sleep(self.analysis_interval)
                analyses = await self.trigger_analysis()

                if analyses:
                    logger.info(f"完成反馈分析，共生成 {sum(len(a.insights_generated) for a in analyses)} 个洞察")

                # 定期学习应用
                await asyncio.sleep(self.learning_interval - self.analysis_interval)

                # 验证学习效果
                await self._validate_learning_effectiveness()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"学习循环错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试

    async def _validate_learning_effectiveness(self):
        """验证学习效果"""
        # 获取最近的应用结果
        recent_applications = [
            r for r in self.learning_applier.application_results
            if (datetime.now() - r['applied_at']) < timedelta(hours=24)
        ]

        if recent_applications:
            success_rate = len([r for r in recent_applications if r['status'] == 'success']) / len(recent_applications)

            if success_rate > 0.8:
                logger.info(f"成功率: {success_rate:.2f}")
            elif success_rate < 0.5:
                logger.warning(f"成功率: {success_rate:.2f}")
    def get_feedback_loop_status(self) -> Dict[str, Any]:
        """获取反馈闭环状态"""
        return {
            'active': self.learning_loop_active,
            'monitored_components': len(self.monitored_components),
            'feedback_collector_status': {
                'active_collectors': len(self.feedback_collector.active_collectors),
                'feedback_history_size': len(self.feedback_collector.feedback_history)
            },
            'analyzer_status': {
                'analyses_performed': len(self.feedback_analyzer.analysis_history),
                'baseline_components': len(self.feedback_analyzer.baseline_metrics)
            },
            'applier_status': self.learning_applier.get_application_statistics(),
            'configuration': {
                'analysis_interval': self.analysis_interval,
                'learning_interval': self.learning_interval
            }
        }

    def get_recent_insights(self, component: Optional[str] = None,
                           hours: int = 24) -> List[LearningInsight]:
        """获取最近的学习洞察"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        insights = []
        for analysis in self.feedback_analyzer.analysis_history:
            if analysis.analysis_timestamp > cutoff_time:
                if component is None or analysis.component == component:
                    insights.extend(analysis.insights_generated)

        return insights

    def get_recent_recommendations(self, component: Optional[str] = None,
                                  hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的推荐行动"""
        insights = self.get_recent_insights(component, hours)

        recommendations = []
        for insight in insights:
            for action in insight.recommended_actions:
                recommendations.append({
                    'insight_id': insight.insight_id,
                    'component': insight.component,
                    'action': action,
                    'confidence': insight.confidence_score,
                    'generated_at': insight.generated_at
                })

        return recommendations


# 全局实例
_feedback_loop_instance: Optional[FeedbackLoopMechanism] = None

def get_feedback_loop_mechanism() -> FeedbackLoopMechanism:
    """获取反馈闭环机制实例"""
    global _feedback_loop_instance
    if _feedback_loop_instance is None:
        _feedback_loop_instance = FeedbackLoopMechanism()
    return _feedback_loop_instance
