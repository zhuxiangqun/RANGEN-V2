"""
系统级自适应优化器 (System-Level Adaptive Optimizer)

实现基于反馈的系统级持续优化：
- 系统状态监控
- 反馈数据收集和分析
- 优化机会识别
- 优化策略制定和实施
- 效果验证和持续改进
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


class OptimizationScope(Enum):
    """优化范围"""
    LOCAL = "local"              # 局部优化
    COMPONENT = "component"      # 组件级优化
    SUBSYSTEM = "subsystem"      # 子系统优化
    GLOBAL = "global"           # 全局系统优化


class OptimizationTrigger(Enum):
    """优化触发器"""
    SCHEDULED = "scheduled"      # 定时触发
    THRESHOLD = "threshold"      # 阈值触发
    EVENT = "event"            # 事件触发
    MANUAL = "manual"          # 手动触发


class OptimizationPhase(Enum):
    """优化阶段"""
    MONITORING = "monitoring"         # 监控阶段
    ANALYSIS = "analysis"            # 分析阶段
    PLANNING = "planning"            # 规划阶段
    IMPLEMENTATION = "implementation" # 实施阶段
    VALIDATION = "validation"        # 验证阶段
    LEARNING = "learning"           # 学习阶段


@dataclass
class SystemState:
    """系统状态"""
    timestamp: datetime
    components: Dict[str, Dict[str, Any]]  # component_id -> state
    global_metrics: Dict[str, float]
    performance_indicators: Dict[str, float]
    resource_utilization: Dict[str, float]
    anomaly_flags: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'components': self.components,
            'global_metrics': self.global_metrics,
            'performance_indicators': self.performance_indicators,
            'resource_utilization': self.resource_utilization,
            'anomaly_flags': self.anomaly_flags
        }


@dataclass
class FeedbackData:
    """反馈数据"""
    source: str
    metric_type: str
    value: Any
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"  # info, warning, error, critical


@dataclass
class OptimizationOpportunity:
    """优化机会"""
    opportunity_id: str
    scope: OptimizationScope
    target_components: List[str]
    problem_description: str
    potential_impact: Dict[str, float]
    confidence_score: float
    recommended_actions: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    identified_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'opportunity_id': self.opportunity_id,
            'scope': self.scope.value,
            'target_components': self.target_components,
            'problem_description': self.problem_description,
            'potential_impact': self.potential_impact,
            'confidence_score': self.confidence_score,
            'recommended_actions': self.recommended_actions,
            'risk_assessment': self.risk_assessment,
            'identified_at': self.identified_at.isoformat()
        }


@dataclass
class OptimizationStrategy:
    """优化策略"""
    strategy_id: str
    name: str
    description: str
    scope: OptimizationScope
    target_objectives: Dict[str, float]
    implementation_plan: List[Dict[str, Any]]
    expected_outcomes: Dict[str, Any]
    risk_mitigation: List[str]
    created_at: datetime = field(default_factory=datetime.now)
    estimated_effort: str = "medium"  # low, medium, high


@dataclass
class OptimizationResult:
    """优化结果"""
    optimization_id: str
    strategy_applied: OptimizationStrategy
    implementation_start: datetime
    implementation_end: Optional[datetime] = None
    actual_outcomes: Dict[str, Any] = field(default_factory=dict)
    success_metrics: Dict[str, float] = field(default_factory=dict)
    issues_encountered: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    status: str = "in_progress"  # in_progress, completed, failed, rolled_back


class SystemMonitor:
    """系统监控器"""

    def __init__(self, monitoring_window: int = 3600):  # 1小时窗口
        self.monitoring_window = monitoring_window
        self.system_states: deque = deque(maxlen=1000)
        self.metric_baselines: Dict[str, Dict[str, float]] = {}
        self.anomaly_detectors: Dict[str, Callable] = {}

    async def get_current_state(self) -> SystemState:
        """获取当前系统状态"""
        # 这里应该从各个监控源收集状态信息
        # 暂时生成模拟状态
        components = await self._collect_component_states()
        global_metrics = await self._collect_global_metrics()
        performance_indicators = await self._calculate_performance_indicators(components)
        resource_utilization = await self._collect_resource_utilization()
        anomalies = await self._detect_anomalies(components, global_metrics)

        state = SystemState(
            timestamp=datetime.now(),
            components=components,
            global_metrics=global_metrics,
            performance_indicators=performance_indicators,
            resource_utilization=resource_utilization,
            anomaly_flags=anomalies
        )

        self.system_states.append(state)
        return state

    async def _collect_component_states(self) -> Dict[str, Dict[str, Any]]:
        """收集组件状态"""
        # 模拟组件状态收集
        components = {
            'knowledge_retrieval': {
                'status': 'active',
                'response_time': 0.8,
                'error_rate': 0.02,
                'throughput': 150
            },
            'reasoning_engine': {
                'status': 'active',
                'response_time': 2.1,
                'error_rate': 0.05,
                'throughput': 75
            },
            'answer_generator': {
                'status': 'active',
                'response_time': 1.2,
                'error_rate': 0.01,
                'throughput': 120
            }
        }
        return components

    async def _collect_global_metrics(self) -> Dict[str, float]:
        """收集全局指标"""
        # 模拟全局指标收集
        return {
            'total_requests': 345.0,
            'average_response_time': 1.7,
            'system_load': 0.65,
            'memory_usage': 0.72,
            'error_rate': 0.025
        }

    async def _calculate_performance_indicators(self, components: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """计算性能指标"""
        indicators = {}

        # 计算整体响应时间
        response_times = [comp.get('response_time', 0) for comp in components.values()]
        if response_times:
            indicators['avg_response_time'] = statistics.mean(response_times)

        # 计算整体错误率
        error_rates = [comp.get('error_rate', 0) for comp in components.values()]
        if error_rates:
            indicators['avg_error_rate'] = statistics.mean(error_rates)

        # 计算整体吞吐量
        throughputs = [comp.get('throughput', 0) for comp in components.values()]
        if throughputs:
            indicators['total_throughput'] = sum(throughputs)

        return indicators

    async def _collect_resource_utilization(self) -> Dict[str, float]:
        """收集资源利用率"""
        # 模拟资源利用率收集
        return {
            'cpu_usage': 0.68,
            'memory_usage': 0.72,
            'disk_io': 0.45,
            'network_io': 0.38
        }

    async def _detect_anomalies(self, components: Dict[str, Dict[str, Any]],
                               global_metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """检测异常"""
        anomalies = []

        # 检查响应时间异常
        for comp_name, comp_state in components.items():
            response_time = comp_state.get('response_time', 0)
            baseline = self.metric_baselines.get(f"{comp_name}.response_time", response_time * 0.8)

            if response_time > baseline * 1.5:  # 响应时间超过基线50%
                anomalies.append({
                    'component': comp_name,
                    'metric': 'response_time',
                    'current_value': response_time,
                    'baseline': baseline,
                    'severity': 'high',
                    'description': f'{comp_name}响应时间异常升高'
                })

        # 检查错误率异常
        for comp_name, comp_state in components.items():
            error_rate = comp_state.get('error_rate', 0)
            baseline = self.metric_baselines.get(f"{comp_name}.error_rate", 0.05)

            if error_rate > baseline * 2:  # 错误率超过基线2倍
                anomalies.append({
                    'component': comp_name,
                    'metric': 'error_rate',
                    'current_value': error_rate,
                    'baseline': baseline,
                    'severity': 'critical',
                    'description': f'{comp_name}错误率异常升高'
                })

        return anomalies

    def update_baselines(self, state: SystemState):
        """更新基线"""
        # 使用最近的状态更新基线
        if len(self.system_states) >= 10:  # 需要足够的样本
            recent_states = list(self.system_states)[-10:]

            for comp_name in state.components.keys():
                for metric_name in ['response_time', 'error_rate', 'throughput']:
                    metric_key = f"{comp_name}.{metric_name}"
                    values = []

                    for s in recent_states:
                        comp_state = s.components.get(comp_name, {})
                        value = comp_state.get(metric_name)
                        if value is not None:
                            values.append(value)

                    if values:
                        self.metric_baselines[metric_key] = statistics.mean(values)


class FeedbackAnalyzer:
    """反馈分析器"""

    def __init__(self, analysis_window: int = 3600):  # 1小时分析窗口
        self.analysis_window = analysis_window
        self.feedback_buffer: deque = deque(maxlen=10000)
        self.analysis_patterns: Dict[str, Dict[str, Any]] = {}

    async def collect_feedback(self) -> List[FeedbackData]:
        """收集反馈数据"""
        # 这里应该从各种来源收集反馈
        # 暂时生成模拟反馈
        feedbacks = [
            FeedbackData(
                source="user_interaction",
                metric_type="satisfaction_score",
                value=4.2,
                timestamp=datetime.now(),
                context={"query_type": "complex"}
            ),
            FeedbackData(
                source="system_monitor",
                metric_type="response_time",
                value=1.8,
                timestamp=datetime.now(),
                context={"component": "reasoning_engine"}
            )
        ]

        self.feedback_buffer.extend(feedbacks)
        return feedbacks

    async def analyze_feedback_trends(self) -> Dict[str, Any]:
        """分析反馈趋势"""
        cutoff_time = datetime.now() - timedelta(seconds=self.analysis_window)

        recent_feedback = [
            f for f in self.feedback_buffer
            if f.timestamp > cutoff_time
        ]

        if not recent_feedback:
            return {'insufficient_data': True}

        # 按类型分组分析
        trends = {}

        feedback_by_type = defaultdict(list)
        for feedback in recent_feedback:
            feedback_by_type[feedback.metric_type].append(feedback)

        for metric_type, feedbacks in feedback_by_type.items():
            values = [f.value for f in feedbacks if isinstance(f.value, (int, float))]

            if len(values) >= 3:
                trend_analysis = self._analyze_metric_trend(values, feedbacks)
                trends[metric_type] = trend_analysis

        return trends

    def _analyze_metric_trend(self, values: List[float], feedbacks: List[FeedbackData]) -> Dict[str, Any]:
        """分析指标趋势"""
        if len(values) < 3:
            return {'insufficient_data': True}

        # 计算趋势
        recent_avg = statistics.mean(values[-10:])  # 最近10个值
        earlier_avg = statistics.mean(values[:-10]) if len(values) > 10 else statistics.mean(values)

        trend_direction = "stable"
        if recent_avg > earlier_avg * 1.1:
            trend_direction = "improving"
        elif recent_avg < earlier_avg * 0.9:
            trend_direction = "degrading"

        # 计算波动性
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        volatility = std_dev / statistics.mean(values) if statistics.mean(values) > 0 else 0

        return {
            'trend_direction': trend_direction,
            'recent_average': recent_avg,
            'earlier_average': earlier_avg,
            'change_percentage': (recent_avg - earlier_avg) / earlier_avg if earlier_avg > 0 else 0,
            'volatility': volatility,
            'sample_count': len(values)
        }


class OptimizationEngine:
    """优化引擎"""

    def __init__(self):
        self.optimization_templates: Dict[str, OptimizationStrategy] = {}
        self.active_optimizations: Dict[str, OptimizationResult] = {}

    def develop_strategy(self, opportunities: List[OptimizationOpportunity]) -> Optional[OptimizationStrategy]:
        """制定优化策略"""
        if not opportunities:
            return None

        # 按优先级排序机会
        sorted_opportunities = sorted(opportunities, key=lambda o: o.confidence_score, reverse=True)

        # 为最高优先级的机会制定策略
        primary_opportunity = sorted_opportunities[0]

        strategy = await self._create_optimization_strategy(primary_opportunity)

        return strategy

    async def _create_optimization_strategy(self, opportunity: OptimizationOpportunity) -> OptimizationStrategy:
        """创建优化策略"""
        strategy_id = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 根据机会类型创建相应的策略
        if "performance" in opportunity.problem_description.lower():
            strategy = self._create_performance_optimization_strategy(opportunity)
        elif "resource" in opportunity.problem_description.lower():
            strategy = self._create_resource_optimization_strategy(opportunity)
        elif "error" in opportunity.problem_description.lower():
            strategy = self._create_error_reduction_strategy(opportunity)
        else:
            strategy = self._create_general_optimization_strategy(opportunity)

        return strategy

    def _create_performance_optimization_strategy(self, opportunity: OptimizationOpportunity) -> OptimizationStrategy:
        """创建性能优化策略"""
        return OptimizationStrategy(
            strategy_id=f"perf_opt_{datetime.now().strftime('%H%M%S')}",
            name="性能优化策略",
            description=f"针对{opportunity.target_components}的性能优化",
            scope=opportunity.scope,
            target_objectives={
                'response_time_reduction': 0.2,  # 减少20%响应时间
                'throughput_increase': 0.15     # 增加15%吞吐量
            },
            implementation_plan=[
                {
                    'phase': 'analysis',
                    'actions': ['识别性能瓶颈', '分析资源利用率']
                },
                {
                    'phase': 'optimization',
                    'actions': ['调整缓存策略', '优化算法参数', '增加并发度']
                },
                {
                    'phase': 'validation',
                    'actions': ['性能测试', '负载测试']
                }
            ],
            expected_outcomes={
                'performance_gain': 0.25,
                'resource_efficiency': 0.1
            },
            risk_mitigation=[
                '实施渐进式优化',
                '准备回滚方案',
                '监控关键指标'
            ],
            estimated_effort='medium'
        )

    def _create_resource_optimization_strategy(self, opportunity: OptimizationOpportunity) -> OptimizationStrategy:
        """创建资源优化策略"""
        return OptimizationStrategy(
            strategy_id=f"resource_opt_{datetime.now().strftime('%H%M%S')}",
            name="资源优化策略",
            description=f"针对{opportunity.target_components}的资源优化",
            scope=opportunity.scope,
            target_objectives={
                'resource_utilization': 0.9,   # 提高到90%利用率
                'cost_reduction': 0.15        # 减少15%成本
            },
            implementation_plan=[
                {
                    'phase': 'assessment',
                    'actions': ['资源使用分析', '成本效益评估']
                },
                {
                    'phase': 'optimization',
                    'actions': ['资源重新分配', '负载均衡调整']
                }
            ],
            expected_outcomes={
                'resource_efficiency': 0.2,
                'cost_savings': 0.15
            },
            risk_mitigation=[
                '确保服务可用性',
                '实施容量规划'
            ],
            estimated_effort='low'
        )

    def _create_error_reduction_strategy(self, opportunity: OptimizationOpportunity) -> OptimizationStrategy:
        """创建错误减少策略"""
        return OptimizationStrategy(
            strategy_id=f"error_opt_{datetime.now().strftime('%H%M%S')}",
            name="错误减少策略",
            description=f"针对{opportunity.target_components}的错误减少",
            scope=opportunity.scope,
            target_objectives={
                'error_rate_reduction': 0.5,  # 减少50%错误率
                'reliability_improvement': 0.3  # 提高30%可靠性
            },
            implementation_plan=[
                {
                    'phase': 'diagnosis',
                    'actions': ['错误根因分析', '故障模式识别']
                },
                {
                    'phase': 'remediation',
                    'actions': ['修复已知问题', '增加错误处理', '改进监控']
                }
            ],
            expected_outcomes={
                'error_rate_reduction': 0.4,
                'system_stability': 0.25
            },
            risk_mitigation=[
                '测试修复效果',
                '避免过度修复'
            ],
            estimated_effort='high'
        )

    def _create_general_optimization_strategy(self, opportunity: OptimizationOpportunity) -> OptimizationStrategy:
        """创建通用优化策略"""
        return OptimizationStrategy(
            strategy_id=f"general_opt_{datetime.now().strftime('%H%M%S')}",
            name="通用优化策略",
            description=f"针对{opportunity.problem_description}的优化",
            scope=opportunity.scope,
            target_objectives={
                'general_improvement': 0.2
            },
            implementation_plan=[
                {
                    'phase': 'assessment',
                    'actions': ['问题评估', '影响分析']
                },
                {
                    'phase': 'implementation',
                    'actions': ['应用优化措施', '监控效果']
                }
            ],
            expected_outcomes={
                'overall_improvement': 0.15
            },
            risk_mitigation=[
                '最小化变更范围',
                '准备回滚计划'
            ],
            estimated_effort='medium'
        )


class ChangeManager:
    """变更管理器"""

    def __init__(self):
        self.pending_changes: Dict[str, Dict[str, Any]] = {}
        self.change_history: List[Dict[str, Any]] = []
        self.rollback_plans: Dict[str, Dict[str, Any]] = {}

    async def plan_changes(self, strategy: OptimizationStrategy) -> Dict[str, Any]:
        """规划变更"""
        change_plan = {
            'change_id': f"change_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'strategy_id': strategy.strategy_id,
            'planned_changes': strategy.implementation_plan,
            'rollback_plan': self._create_rollback_plan(strategy),
            'validation_criteria': self._create_validation_criteria(strategy),
            'created_at': datetime.now()
        }

        self.pending_changes[change_plan['change_id']] = change_plan
        return change_plan

    async def implement_changes(self, change_plan: Dict[str, Any]) -> Dict[str, Any]:
        """实施变更"""
        change_id = change_plan['change_id']

        implementation_result = {
            'change_id': change_id,
            'status': 'in_progress',
            'phases_completed': [],
            'issues_encountered': [],
            'start_time': datetime.now()
        }

        try:
            # 按阶段实施变更
            for phase in change_plan['planned_changes']:
                phase_name = phase['phase']
                actions = phase['actions']

                logger.info(f"实施变更阶段: {phase_name}")

                # 模拟实施动作
                for action in actions:
                    try:
                        await self._execute_action(action, phase_name)
                        implementation_result['phases_completed'].append(f"{phase_name}:{action}")
                    except Exception as e:
                        issue = f"阶段 {phase_name} 动作 {action} 失败: {e}"
                        implementation_result['issues_encountered'].append(issue)
                        logger.error(issue)

                # 阶段间验证
                validation_result = await self._validate_phase_completion(phase_name)
                if not validation_result['success']:
                    implementation_result['issues_encountered'].extend(validation_result['issues'])

            implementation_result['status'] = 'completed' if not implementation_result['issues_encountered'] else 'completed_with_issues'
            implementation_result['end_time'] = datetime.now()

        except Exception as e:
            implementation_result['status'] = 'failed'
            implementation_result['error'] = str(e)
            implementation_result['end_time'] = datetime.now()

        # 移动到历史记录
        self.change_history.append(implementation_result)
        if change_id in self.pending_changes:
            del self.pending_changes[change_id]

        return implementation_result

    async def _execute_action(self, action: str, phase: str):
        """执行具体动作"""
        # 这里应该实现实际的变更执行逻辑
        # 暂时模拟执行
        await asyncio.sleep(0.1)  # 模拟执行时间

        logger.debug(f"执行动作: {phase} -> {action}")

    async def _validate_phase_completion(self, phase: str) -> Dict[str, Any]:
        """验证阶段完成"""
        # 这里应该实现实际的验证逻辑
        # 暂时返回成功
        return {
            'success': True,
            'issues': []
        }

    def _create_rollback_plan(self, strategy: OptimizationStrategy) -> Dict[str, Any]:
        """创建回滚计划"""
        return {
            'rollback_actions': [
                '恢复原始配置',
                '重启受影响的服务',
                '验证系统稳定性'
            ],
            'rollback_triggers': [
                '性能下降超过20%',
                '错误率上升超过50%',
                '系统不可用'
            ],
            'estimated_rollback_time': '15分钟'
        }

    def _create_validation_criteria(self, strategy: OptimizationStrategy) -> Dict[str, Any]:
        """创建验证标准"""
        return {
            'performance_criteria': {
                'response_time': {'max': 2.0, 'unit': 'seconds'},
                'error_rate': {'max': 0.05, 'unit': 'percentage'}
            },
            'stability_criteria': {
                'uptime': {'min': 0.99, 'unit': 'percentage'},
                'resource_usage': {'max': 0.9, 'unit': 'percentage'}
            },
            'validation_period': '30分钟'
        }


class SystemLevelAdaptiveOptimizer:
    """
    系统级自适应优化器

    实现基于反馈的系统级持续优化：
    - 系统状态监控
    - 反馈数据收集和分析
    - 优化机会识别
    - 优化策略制定和实施
    - 效果验证和持续改进
    """

    def __init__(self):
        self.system_monitor = SystemMonitor()
        self.feedback_analyzer = FeedbackAnalyzer()
        self.optimization_engine = OptimizationEngine()
        self.change_manager = ChangeManager()

        self.optimization_interval = 3600  # 1小时优化一次
        self._running = False
        self._optimization_task: Optional[asyncio.Task] = None

    async def start_adaptive_optimization(self):
        """启动自适应优化"""
        if self._running:
            return

        self._running = True
        self._optimization_task = asyncio.create_task(self._adaptive_optimization_loop())

        logger.info("系统级自适应优化器已启动")

    async def stop_adaptive_optimization(self):
        """停止自适应优化"""
        if not self._running:
            return

        self._running = False
        if self._optimization_task:
            self._optimization_task.cancel()
            try:
                await self._optimization_task
            except asyncio.CancelledError:
                pass

        logger.info("系统级自适应优化器已停止")

    async def optimize_system_adaptively(self) -> OptimizationResult:
        """自适应系统优化"""
        logger.info("开始系统自适应优化循环")

        while self._running:
            try:
                # 1. 系统状态监控
                current_state = await self.system_monitor.get_current_state()
                logger.debug("系统状态监控完成")

                # 更新监控器基线
                self.system_monitor.update_baselines(current_state)

                # 2. 反馈数据收集
                feedback_data = await self.feedback_analyzer.collect_feedback()
                logger.debug(f"收集到 {len(feedback_data)} 条反馈数据")

                # 3. 优化机会识别
                optimization_opportunities = await self._identify_optimization_opportunities(
                    current_state, feedback_data
                )
                logger.debug(f"识别出 {len(optimization_opportunities)} 个优化机会")

                # 4. 优化策略制定
                if optimization_opportunities:
                    optimization_strategy = self.optimization_engine.develop_strategy(optimization_opportunities)
                    if optimization_strategy:
                        logger.info(f"制定优化策略: {optimization_strategy.name}")

                        # 5. 优化实施
                        change_plan = await self.change_manager.plan_changes(optimization_strategy)
                        implementation_result = await self.change_manager.implement_changes(change_plan)

                        # 6. 效果验证
                        validation_result = await self._validate_optimization_effect(implementation_result)

                        # 7. 学习和改进
                        await self._learn_from_optimization_cycle(
                            current_state, feedback_data, implementation_result, validation_result
                        )

                        # 创建优化结果
                        result = OptimizationResult(
                            optimization_id=f"opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                            strategy_applied=optimization_strategy,
                            implementation_start=change_plan['created_at'],
                            implementation_end=datetime.now(),
                            actual_outcomes=validation_result,
                            success_metrics=self._calculate_success_metrics(validation_result),
                            status='completed' if validation_result.get('overall_success', False) else 'failed'
                        )

                        return result

                # 等待下一个优化周期
                await asyncio.sleep(self.optimization_interval)

            except Exception as e:
                logger.error(f"自适应优化循环错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试

        return OptimizationResult(
            optimization_id="optimization_stopped",
            strategy_applied=OptimizationStrategy(
                strategy_id="stopped",
                name="优化已停止",
                description="自适应优化已被停止",
                scope=OptimizationScope.GLOBAL,
                target_objectives={},
                implementation_plan=[],
                expected_outcomes={},
                risk_mitigation=[]
            ),
            implementation_start=datetime.now(),
            status='stopped'
        )

    async def _identify_optimization_opportunities(self, state: SystemState,
                                                 feedback: List[FeedbackData]) -> List[OptimizationOpportunity]:
        """识别优化机会"""
        opportunities = []

        # 分析系统状态寻找问题
        opportunities.extend(await self._analyze_system_state_opportunities(state))

        # 分析反馈数据寻找问题
        opportunities.extend(await self._analyze_feedback_opportunities(feedback))

        # 按置信度排序
        opportunities.sort(key=lambda o: o.confidence_score, reverse=True)

        return opportunities

    async def _analyze_system_state_opportunities(self, state: SystemState) -> List[OptimizationOpportunity]:
        """分析系统状态优化机会"""
        opportunities = []

        # 检查性能问题
        if state.performance_indicators.get('avg_response_time', 0) > 2.0:
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"perf_{datetime.now().strftime('%H%M%S')}",
                scope=OptimizationScope.GLOBAL,
                target_components=list(state.components.keys()),
                problem_description="系统响应时间过长",
                potential_impact={'response_time_reduction': 0.3, 'user_satisfaction': 0.2},
                confidence_score=0.8,
                recommended_actions=[
                    {'action': 'optimize_caching', 'description': '优化缓存策略'},
                    {'action': 'adjust_concurrency', 'description': '调整并发配置'}
                ],
                risk_assessment={'level': 'medium', 'description': '可能影响系统稳定性'}
            ))

        # 检查资源利用问题
        high_utilization = [
            comp for comp, metrics in state.resource_utilization.items()
            if metrics > 0.9
        ]
        if high_utilization:
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"resource_{datetime.now().strftime('%H%M%S')}",
                scope=OptimizationScope.SUBSYSTEM,
                target_components=high_utilization,
                problem_description="资源利用率过高",
                potential_impact={'resource_efficiency': 0.25, 'system_stability': 0.15},
                confidence_score=0.7,
                recommended_actions=[
                    {'action': 'scale_resources', 'description': '扩展资源'},
                    {'action': 'optimize_allocation', 'description': '优化资源分配'}
                ],
                risk_assessment={'level': 'low', 'description': '资源优化通常安全'}
            ))

        # 检查异常情况
        if state.anomaly_flags:
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"anomaly_{datetime.now().strftime('%H%M%S')}",
                scope=OptimizationScope.COMPONENT,
                target_components=[a['component'] for a in state.anomaly_flags],
                problem_description="检测到系统异常",
                potential_impact={'system_stability': 0.3, 'error_reduction': 0.4},
                confidence_score=0.9,
                recommended_actions=[
                    {'action': 'investigate_anomalies', 'description': '调查异常原因'},
                    {'action': 'implement_fixes', 'description': '实施修复措施'}
                ],
                risk_assessment={'level': 'high', 'description': '异常修复可能引入新问题'}
            ))

        return opportunities

    async def _analyze_feedback_opportunities(self, feedback: List[FeedbackData]) -> List[OptimizationOpportunity]:
        """分析反馈优化机会"""
        opportunities = []

        # 分析反馈趋势
        trends = await self.feedback_analyzer.analyze_feedback_trends()

        # 检查用户满意度趋势
        satisfaction_trend = trends.get('satisfaction_score')
        if satisfaction_trend and satisfaction_trend.get('trend_direction') == 'degrading':
            opportunities.append(OptimizationOpportunity(
                opportunity_id=f"satisfaction_{datetime.now().strftime('%H%M%S')}",
                scope=OptimizationScope.GLOBAL,
                target_components=[],  # 影响所有组件
                problem_description="用户满意度下降",
                potential_impact={'user_satisfaction': 0.25, 'engagement': 0.2},
                confidence_score=0.75,
                recommended_actions=[
                    {'action': 'improve_response_quality', 'description': '提升响应质量'},
                    {'action': 'optimize_user_experience', 'description': '优化用户体验'}
                ],
                risk_assessment={'level': 'medium', 'description': '用户体验优化通常正面影响'}
            ))

        return opportunities

    async def _validate_optimization_effect(self, implementation_result: Dict[str, Any]) -> Dict[str, Any]:
        """验证优化效果"""
        # 这里应该实现实际的验证逻辑
        # 暂时基于实施结果模拟验证

        success = len(implementation_result.get('issues_encountered', [])) == 0
        phases_completed = len(implementation_result.get('phases_completed', []))

        validation_result = {
            'overall_success': success,
            'phases_validated': phases_completed,
            'performance_improvement': 0.15 if success else -0.05,
            'stability_assessment': 'stable' if success else 'degraded',
            'validation_timestamp': datetime.now()
        }

        return validation_result

    async def _learn_from_optimization_cycle(self, state: SystemState, feedback: List[FeedbackData],
                                           implementation: Dict[str, Any], validation: Dict[str, Any]):
        """从优化周期中学习"""
        # 更新系统监控器的基线
        self.system_monitor.update_baselines(state)

        # 分析成功和失败的模式
        success = validation.get('overall_success', False)

        if success:
            logger.info("优化周期成功，强化成功策略")
            # 这里可以实现学习逻辑，比如增加成功策略的权重
        else:
            logger.info("优化周期失败，分析失败原因")
            issues = implementation.get('issues_encountered', [])
            if issues:
                logger.warning(f"遇到问题: {issues}")
            # 这里可以实现失败模式的学习，避免重复失败

    def _calculate_success_metrics(self, validation_result: Dict[str, Any]) -> Dict[str, float]:
        """计算成功指标"""
        metrics = {}

        if validation_result.get('overall_success'):
            metrics['success_rate'] = 1.0
            metrics['performance_gain'] = validation_result.get('performance_improvement', 0)
        else:
            metrics['success_rate'] = 0.0
            metrics['performance_gain'] = validation_result.get('performance_improvement', 0)

        return metrics

    def get_optimizer_status(self) -> Dict[str, Any]:
        """获取优化器状态"""
        return {
            'running': self._running,
            'optimization_interval': self.optimization_interval,
            'pending_changes': len(self.change_manager.pending_changes),
            'completed_changes': len(self.change_manager.change_history),
            'system_states_monitored': len(self.system_monitor.system_states),
            'feedback_collected': len(self.feedback_analyzer.feedback_buffer)
        }


# 全局实例
_system_adaptive_optimizer_instance: Optional[SystemLevelAdaptiveOptimizer] = None

def get_system_adaptive_optimizer() -> SystemLevelAdaptiveOptimizer:
    """获取系统级自适应优化器实例"""
    global _system_adaptive_optimizer_instance
    if _system_adaptive_optimizer_instance is None:
        _system_adaptive_optimizer_instance = SystemLevelAdaptiveOptimizer()
    return _system_adaptive_optimizer_instance
