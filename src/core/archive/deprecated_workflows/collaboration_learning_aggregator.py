"""
协作学习聚合器 (Collaboration Learning Aggregator)

聚合多智能体协作模式的学习，实现：
- 协作模式识别和分析
- 性能关联分析
- 学习洞察合成
- 知识在智能体间的分布
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics
import json
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class CollaborationPattern(Enum):
    """协作模式"""
    SEQUENTIAL = "sequential"      # 顺序协作
    PARALLEL = "parallel"          # 并行协作
    HIERARCHICAL = "hierarchical"  # 层次协作
    PEER_TO_PEER = "peer_to_peer"  # 对等协作
    MASTER_SLAVE = "master_slave"  # 主从协作
    NEGOTIATION_BASED = "negotiation"  # 协商协作


class LearningOutcome(Enum):
    """学习结果"""
    PATTERN_RECOGNITION = "pattern_recognition"  # 模式识别
    PERFORMANCE_OPTIMIZATION = "performance_optimization"  # 性能优化
    RESOURCE_ALLOCATION = "resource_allocation"  # 资源分配
    CONFLICT_RESOLUTION = "conflict_resolution"  # 冲突解决
    ADAPTATION_STRATEGY = "adaptation_strategy"  # 适应策略


@dataclass
class CollaborationSession:
    """协作会话"""
    session_id: str
    participants: List[str]
    start_time: datetime
    end_time: Optional[datetime] = None
    collaboration_type: CollaborationPattern
    tasks: List[Dict[str, Any]] = field(default_factory=list)
    interactions: List[Dict[str, Any]] = field(default_factory=list)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """会话持续时间（秒）"""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def add_interaction(self, from_agent: str, to_agent: str,
                       interaction_type: str, content: Dict[str, Any]):
        """添加交互记录"""
        interaction = {
            'from_agent': from_agent,
            'to_agent': to_agent,
            'type': interaction_type,
            'content': content,
            'timestamp': datetime.now()
        }
        self.interactions.append(interaction)


@dataclass
class PerformanceOutcome:
    """性能结果"""
    session_id: str
    overall_success: bool
    performance_metrics: Dict[str, float]
    agent_contributions: Dict[str, Dict[str, Any]]
    bottlenecks_identified: List[Dict[str, Any]]
    improvement_opportunities: List[Dict[str, Any]]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningInsights:
    """学习洞察"""
    insights_id: str
    generated_at: datetime
    collaboration_patterns: List[Dict[str, Any]]
    performance_correlations: List[Dict[str, Any]]
    recommended_strategies: List[Dict[str, Any]]
    confidence_scores: Dict[str, float]
    actionable_recommendations: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternRecognizer:
    """模式识别器"""

    def __init__(self):
        self.pattern_templates: Dict[CollaborationPattern, Dict[str, Any]] = {
            CollaborationPattern.SEQUENTIAL: {
                'interaction_pattern': 'linear',
                'communication_density': 'low',
                'decision_making': 'centralized'
            },
            CollaborationPattern.PARALLEL: {
                'interaction_pattern': 'mesh',
                'communication_density': 'high',
                'decision_making': 'distributed'
            },
            CollaborationPattern.HIERARCHICAL: {
                'interaction_pattern': 'tree',
                'communication_density': 'medium',
                'decision_making': 'hierarchical'
            }
        }

    async def identify_patterns(self, collaboration_sessions: List[CollaborationSession]
                               ) -> List[Dict[str, Any]]:
        """识别协作模式"""
        patterns = []

        for session in collaboration_sessions:
            pattern_analysis = await self._analyze_session_pattern(session)
            if pattern_analysis:
                patterns.append(pattern_analysis)

        # 聚合相似模式
        aggregated_patterns = self._aggregate_similar_patterns(patterns)

        return aggregated_patterns

    async def _analyze_session_pattern(self, session: CollaborationSession) -> Optional[Dict[str, Any]]:
        """分析单个会话的模式"""
        if not session.interactions:
            return None

        # 分析交互模式
        interaction_analysis = self._analyze_interactions(session.interactions)

        # 确定协作模式
        collaboration_pattern = self._classify_collaboration_pattern(interaction_analysis)

        # 计算模式特征
        pattern_features = {
            'session_id': session.session_id,
            'pattern_type': collaboration_pattern.value,
            'participant_count': len(session.participants),
            'interaction_count': len(session.interactions),
            'duration': session.duration,
            'interaction_density': interaction_analysis['density'],
            'communication_patterns': interaction_analysis['patterns'],
            'bottlenecks': self._identify_bottlenecks(session),
            'success_indicators': self._calculate_success_indicators(session)
        }

        return pattern_features

    def _analyze_interactions(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析交互模式"""
        if not interactions:
            return {'density': 0, 'patterns': []}

        # 计算交互密度
        total_interactions = len(interactions)
        unique_participants = set()
        interaction_types = Counter()

        for interaction in interactions:
            unique_participants.add(interaction['from_agent'])
            unique_participants.add(interaction['to_agent'])
            interaction_types[interaction['type']] += 1

        participant_count = len(unique_participants)
        density = total_interactions / max(participant_count * (participant_count - 1), 1)

        # 识别通信模式
        patterns = []
        if interaction_types['task_assignment'] > total_interactions * 0.3:
            patterns.append('coordinated')
        if interaction_types['resource_request'] > total_interactions * 0.2:
            patterns.append('resource_sharing')
        if interaction_types['conflict_resolution'] > total_interactions * 0.1:
            patterns.append('conflict_prone')

        return {
            'density': density,
            'patterns': patterns,
            'interaction_types': dict(interaction_types)
        }

    def _classify_collaboration_pattern(self, interaction_analysis: Dict[str, Any]) -> CollaborationPattern:
        """分类协作模式"""
        density = interaction_analysis['density']
        patterns = interaction_analysis['patterns']

        if density < 0.3:
            return CollaborationPattern.SEQUENTIAL
        elif density > 0.7 and 'coordinated' in patterns:
            return CollaborationPattern.PARALLEL
        elif 'conflict_prone' in patterns:
            return CollaborationPattern.NEGOTIATION_BASED
        else:
            return CollaborationPattern.HIERARCHICAL

    def _identify_bottlenecks(self, session: CollaborationSession) -> List[Dict[str, Any]]:
        """识别瓶颈"""
        bottlenecks = []

        # 分析交互延迟
        if session.interactions:
            timestamps = [inter['timestamp'] for inter in session.interactions]
            if len(timestamps) > 1:
                delays = []
                for i in range(1, len(timestamps)):
                    delay = (timestamps[i] - timestamps[i-1]).total_seconds()
                    delays.append(delay)

                avg_delay = statistics.mean(delays)
                max_delay = max(delays)

                if max_delay > avg_delay * 2:
                    bottlenecks.append({
                        'type': 'communication_delay',
                        'severity': 'high',
                        'description': f'通信延迟峰值: {max_delay:.2f}秒'
                    })

        return bottlenecks

    def _calculate_success_indicators(self, session: CollaborationSession) -> Dict[str, Any]:
        """计算成功指标"""
        indicators = {
            'task_completion_rate': 0.0,
            'communication_efficiency': 0.0,
            'conflict_resolution_rate': 0.0
        }

        # 计算任务完成率
        if session.tasks:
            completed_tasks = sum(1 for task in session.tasks if task.get('completed', False))
            indicators['task_completion_rate'] = completed_tasks / len(session.tasks)

        # 计算通信效率
        if session.interactions and session.duration:
            interaction_rate = len(session.interactions) / session.duration
            indicators['communication_efficiency'] = min(interaction_rate / 10.0, 1.0)  # 归一化

        return indicators

    def _aggregate_similar_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """聚合相似模式"""
        if not patterns:
            return []

        # 按模式类型分组
        pattern_groups = defaultdict(list)
        for pattern in patterns:
            pattern_groups[pattern['pattern_type']].append(pattern)

        # 为每个组创建聚合模式
        aggregated = []
        for pattern_type, group_patterns in pattern_groups.items():
            if len(group_patterns) >= 2:  # 至少需要2个模式才能聚合
                aggregated_pattern = {
                    'pattern_type': pattern_type,
                    'frequency': len(group_patterns),
                    'avg_participants': statistics.mean(p['participant_count'] for p in group_patterns),
                    'avg_duration': statistics.mean(p['duration'] for p in group_patterns if p['duration']),
                    'common_characteristics': self._find_common_characteristics(group_patterns),
                    'performance_indicators': self._aggregate_performance_indicators(group_patterns)
                }
                aggregated.append(aggregated_pattern)

        return aggregated

    def _find_common_characteristics(self, patterns: List[Dict[str, Any]]) -> List[str]:
        """寻找共同特征"""
        characteristics = []

        # 检查共同的通信模式
        communication_patterns = []
        for pattern in patterns:
            communication_patterns.extend(pattern.get('communication_patterns', []))

        pattern_counts = Counter(communication_patterns)
        common_patterns = [pattern for pattern, count in pattern_counts.items()
                          if count >= len(patterns) * 0.6]  # 60%以上出现

        if common_patterns:
            characteristics.extend(common_patterns)

        return characteristics

    def _aggregate_performance_indicators(self, patterns: List[Dict[str, Any]]) -> Dict[str, float]:
        """聚合性能指标"""
        indicators = defaultdict(list)

        for pattern in patterns:
            success_indicators = pattern.get('success_indicators', {})
            for key, value in success_indicators.items():
                indicators[key].append(value)

        aggregated = {}
        for key, values in indicators.items():
            if values:
                aggregated[key] = statistics.mean(values)

        return aggregated


class CollaborationAnalyzer:
    """协作分析器"""

    def __init__(self):
        self.correlation_threshold = 0.7

    async def analyze_pattern_performance(self, collaboration_patterns: List[Dict[str, Any]],
                                        performance_outcomes: List[PerformanceOutcome]
                                        ) -> List[Dict[str, Any]]:
        """分析模式与性能的关联"""
        correlations = []

        for pattern in collaboration_patterns:
            pattern_correlations = await self._analyze_single_pattern_performance(
                pattern, performance_outcomes
            )
            correlations.extend(pattern_correlations)

        return correlations

    async def _analyze_single_pattern_performance(self, pattern: Dict[str, Any],
                                                performance_outcomes: List[PerformanceOutcome]
                                                ) -> List[Dict[str, Any]]:
        """分析单个模式的性能关联"""
        correlations = []

        # 找到相关的性能结果
        relevant_sessions = [
            outcome for outcome in performance_outcomes
            if outcome.session_id in [p.get('session_id') for p in [pattern]]
        ]

        if len(relevant_sessions) < 3:  # 需要足够的样本
            return correlations

        # 分析性能指标与模式特征的关联
        performance_metrics = ['overall_success', 'task_completion_rate', 'communication_efficiency']

        for metric in performance_metrics:
            correlation = self._calculate_pattern_metric_correlation(
                pattern, relevant_sessions, metric
            )

            if abs(correlation) > self.correlation_threshold:
                correlation_info = {
                    'pattern_type': pattern['pattern_type'],
                    'performance_metric': metric,
                    'correlation_coefficient': correlation,
                    'correlation_strength': self._interpret_correlation_strength(correlation),
                    'sample_size': len(relevant_sessions),
                    'insights': self._generate_correlation_insights(pattern, metric, correlation)
                }
                correlations.append(correlation_info)

        return correlations

    def _calculate_pattern_metric_correlation(self, pattern: Dict[str, Any],
                                            outcomes: List[PerformanceOutcome],
                                            metric: str) -> float:
        """计算模式与指标的相关性"""
        # 简化实现：基于模式的频率和性能的关联
        pattern_frequency = pattern.get('frequency', 1)
        avg_performance = statistics.mean(
            getattr(outcome, metric, 0.5) if hasattr(outcome, metric)
            else outcome.performance_metrics.get(metric, 0.5)
            for outcome in outcomes
        )

        # 简单的相关性计算（实际应该使用更复杂的统计方法）
        correlation = (pattern_frequency / 10.0) * avg_performance - 0.5
        return max(-1.0, min(1.0, correlation))  # 限制在[-1, 1]范围内

    def _interpret_correlation_strength(self, correlation: float) -> str:
        """解释相关性强度"""
        abs_corr = abs(correlation)
        if abs_corr > 0.8:
            return 'strong'
        elif abs_corr > 0.6:
            return 'moderate'
        elif abs_corr > 0.3:
            return 'weak'
        else:
            return 'very_weak'

    def _generate_correlation_insights(self, pattern: Dict[str, Any],
                                     metric: str, correlation: float) -> List[str]:
        """生成相关性洞察"""
        insights = []

        pattern_type = pattern['pattern_type']
        strength = self._interpret_correlation_strength(correlation)

        if correlation > 0:
            if metric == 'overall_success':
                insights.append(f"{pattern_type}模式与整体成功率呈{strength}正相关")
            elif metric == 'task_completion_rate':
                insights.append(f"{pattern_type}模式有助于提高任务完成率")
            elif metric == 'communication_efficiency':
                insights.append(f"{pattern_type}模式提升了通信效率")
        else:
            insights.append(f"{pattern_type}模式可能不适合{metric}优化")

        return insights


class LearningSynthesizer:
    """学习合成器"""

    def __init__(self):
        self.synthesis_strategies = {
            'pattern_based': self._synthesize_pattern_based_insights,
            'correlation_based': self._synthesize_correlation_based_insights,
            'performance_driven': self._synthesize_performance_driven_insights
        }

    async def synthesize_insights(self, collaboration_patterns: List[Dict[str, Any]],
                                performance_correlations: List[Dict[str, Any]]) -> LearningInsights:
        """合成学习洞察"""
        insights_id = f"insights_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 使用不同策略合成洞察
        all_insights = []
        confidence_scores = {}

        for strategy_name, strategy_func in self.synthesis_strategies.items():
            strategy_insights = await strategy_func(collaboration_patterns, performance_correlations)
            all_insights.extend(strategy_insights)

            # 为每个洞察分配置信度
            for insight in strategy_insights:
                confidence_scores[insight.get('id', f"{strategy_name}_{len(all_insights)}")] = insight.get('confidence', 0.5)

        # 去重和排序
        unique_insights = self._deduplicate_insights(all_insights)
        sorted_insights = sorted(unique_insights, key=lambda x: x.get('confidence', 0), reverse=True)

        # 生成推荐策略
        recommended_strategies = await self._generate_recommended_strategies(sorted_insights)

        # 生成可操作的推荐
        actionable_recommendations = self._generate_actionable_recommendations(sorted_insights)

        insights = LearningInsights(
            insights_id=insights_id,
            generated_at=datetime.now(),
            collaboration_patterns=collaboration_patterns,
            performance_correlations=performance_correlations,
            recommended_strategies=recommended_strategies,
            confidence_scores=confidence_scores,
            actionable_recommendations=actionable_recommendations,
            metadata={
                'synthesis_strategies_used': list(self.synthesis_strategies.keys()),
                'total_patterns_analyzed': len(collaboration_patterns),
                'total_correlations_found': len(performance_correlations)
            }
        )

        return insights

    async def _synthesize_pattern_based_insights(self, patterns: List[Dict[str, Any]],
                                               correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于模式的洞察合成"""
        insights = []

        # 分析最成功的模式
        successful_patterns = [
            p for p in patterns
            if p.get('performance_indicators', {}).get('task_completion_rate', 0) > 0.8
        ]

        for pattern in successful_patterns:
            insight = {
                'id': f"pattern_success_{pattern['pattern_type']}",
                'type': 'pattern_effectiveness',
                'title': f"{pattern['pattern_type']}模式的高效性",
                'description': f"{pattern['pattern_type']}协作模式展现出高任务完成率 ({pattern.get('performance_indicators', {}).get('task_completion_rate', 0):.2f})",
                'confidence': 0.8,
                'supporting_patterns': [pattern],
                'recommendation': f"优先考虑使用{pattern['pattern_type']}模式处理相似任务"
            }
            insights.append(insight)

        return insights

    async def _synthesize_correlation_based_insights(self, patterns: List[Dict[str, Any]],
                                                   correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于相关性的洞察合成"""
        insights = []

        # 分析强相关性
        strong_correlations = [
            corr for corr in correlations
            if corr.get('correlation_strength') == 'strong'
        ]

        for correlation in strong_correlations:
            insight = {
                'id': f"correlation_{correlation['pattern_type']}_{correlation['performance_metric']}",
                'type': 'correlation_discovery',
                'title': f"{correlation['pattern_type']}与{correlation['performance_metric']}的强相关性",
                'description': f"发现{correlation['pattern_type']}模式与{correlation['performance_metric']}之间存在{abs(correlation['correlation_coefficient']):.2f}的相关性",
                'confidence': 0.9,
                'correlation_data': correlation,
                'recommendation': f"对于需要优化{correlation['performance_metric']}的任务，推荐使用{correlation['pattern_type']}协作模式"
            }
            insights.append(insight)

        return insights

    async def _synthesize_performance_driven_insights(self, patterns: List[Dict[str, Any]],
                                                    correlations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于性能的洞察合成"""
        insights = []

        # 识别性能瓶颈模式
        bottleneck_patterns = [
            p for p in patterns
            if p.get('bottlenecks') and len(p['bottlenecks']) > 0
        ]

        for pattern in bottleneck_patterns:
            bottlenecks = pattern.get('bottlenecks', [])
            insight = {
                'id': f"bottleneck_{pattern['pattern_type']}",
                'type': 'bottleneck_identification',
                'title': f"{pattern['pattern_type']}模式的性能瓶颈",
                'description': f"识别出{pattern['pattern_type']}模式中的{len(bottlenecks)}个性能瓶颈",
                'confidence': 0.7,
                'bottlenecks': bottlenecks,
                'recommendation': f"优化{pattern['pattern_type']}模式的瓶颈点以提升整体性能"
            }
            insights.append(insight)

        return insights

    def _deduplicate_insights(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重洞察"""
        seen_ids = set()
        unique_insights = []

        for insight in insights:
            insight_id = insight.get('id')
            if insight_id and insight_id not in seen_ids:
                seen_ids.add(insight_id)
                unique_insights.append(insight)

        return unique_insights

    async def _generate_recommended_strategies(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成推荐策略"""
        strategies = []

        # 基于洞察生成策略
        pattern_effectiveness = [
            insight for insight in insights
            if insight.get('type') == 'pattern_effectiveness'
        ]

        if pattern_effectiveness:
            # 推荐最有效的模式
            best_pattern = max(pattern_effectiveness, key=lambda x: x.get('confidence', 0))
            strategy = {
                'strategy_type': 'pattern_preference',
                'description': f"优先使用{best_pattern['title'].split('模式')[0]}模式",
                'rationale': best_pattern['description'],
                'expected_benefits': ['提高任务完成率', '优化协作效率'],
                'implementation_complexity': 'low'
            }
            strategies.append(strategy)

        correlation_insights = [
            insight for insight in insights
            if insight.get('type') == 'correlation_discovery'
        ]

        if correlation_insights:
            strategy = {
                'strategy_type': 'correlation_based_selection',
                'description': '基于模式-性能相关性选择协作策略',
                'rationale': f'基于{len(correlation_insights)}个相关性发现',
                'expected_benefits': ['精准的模式选择', '性能优化'],
                'implementation_complexity': 'medium'
            }
            strategies.append(strategy)

        return strategies

    def _generate_actionable_recommendations(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成可操作的推荐"""
        recommendations = []

        for insight in insights:
            recommendation = {
                'insight_id': insight.get('id'),
                'title': insight.get('title', ''),
                'description': insight.get('recommendation', ''),
                'priority': 'high' if insight.get('confidence', 0) > 0.8 else 'medium',
                'expected_impact': insight.get('confidence', 0.5),
                'implementation_steps': self._generate_implementation_steps(insight),
                'success_metrics': self._define_success_metrics(insight)
            }
            recommendations.append(recommendation)

        return recommendations

    def _generate_implementation_steps(self, insight: Dict[str, Any]) -> List[str]:
        """生成实施步骤"""
        insight_type = insight.get('type')

        if insight_type == 'pattern_effectiveness':
            return [
                '识别适用的任务类型',
                '配置协作模式选择器',
                '监控模式性能表现',
                '根据反馈调整模式选择'
            ]
        elif insight_type == 'correlation_discovery':
            return [
                '建立模式-性能映射表',
                '实现自动化模式选择',
                '收集使用数据和反馈',
                '持续优化映射关系'
            ]
        elif insight_type == 'bottleneck_identification':
            return [
                '识别瓶颈根源',
                '设计优化方案',
                '实施渐进式改进',
                '验证优化效果'
            ]
        else:
            return ['评估洞察适用性', '制定实施计划', '逐步实施改进']

    def _define_success_metrics(self, insight: Dict[str, Any]) -> List[str]:
        """定义成功指标"""
        insight_type = insight.get('type')

        if insight_type == 'pattern_effectiveness':
            return ['任务完成率提升>10%', '协作效率提升>15%']
        elif insight_type == 'correlation_discovery':
            return ['模式选择准确率>80%', '性能提升>5%']
        elif insight_type == 'bottleneck_identification':
            return ['瓶颈消除率>70%', '整体性能提升>8%']
        else:
            return ['相关指标的正向变化']


class KnowledgeDistributor:
    """知识分发器"""

    def __init__(self):
        self.distribution_history: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, Dict[str, Any]] = defaultdict(dict)

    async def distribute_learning_knowledge(self, learning_insights: LearningInsights,
                                          collaboration_sessions: List[CollaborationSession]):
        """分发学习知识"""
        distribution_record = {
            'distribution_id': f"dist_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'insights_id': learning_insights.insights_id,
            'distributed_at': datetime.now(),
            'target_agents': set(),
            'knowledge_packets': [],
            'distribution_metrics': {}
        }

        # 识别参与协作的智能体
        participating_agents = set()
        for session in collaboration_sessions:
            participating_agents.update(session.participants)

        # 为每个洞察生成知识包
        knowledge_packets = []
        for insight in learning_insights.actionable_recommendations:
            packet = await self._create_knowledge_packet(insight, participating_agents)
            knowledge_packets.append(packet)

        # 分发知识包
        distribution_results = []
        for packet in knowledge_packets:
            result = await self._distribute_packet(packet, participating_agents)
            distribution_results.append(result)

        # 更新分布记录
        distribution_record['knowledge_packets'] = knowledge_packets
        distribution_record['distribution_results'] = distribution_results
        distribution_record['target_agents'] = participating_agents
        distribution_record['distribution_metrics'] = self._calculate_distribution_metrics(distribution_results)

        self.distribution_history.append(distribution_record)

        # 更新知识库
        await self._update_knowledge_base(learning_insights)

        logger.info(f"学习知识分发完成，影响{len(participating_agents)}个智能体")

    async def _create_knowledge_packet(self, insight: Dict[str, Any],
                                     target_agents: Set[str]) -> Dict[str, Any]:
        """创建知识包"""
        packet = {
            'packet_id': f"packet_{insight['insight_id']}_{datetime.now().strftime('%H%M%S')}",
            'insight_id': insight['insight_id'],
            'title': insight['title'],
            'description': insight['description'],
            'content': {
                'recommendation': insight['description'],
                'implementation_steps': insight.get('implementation_steps', []),
                'success_metrics': insight.get('success_metrics', []),
                'priority': insight.get('priority', 'medium'),
                'expected_impact': insight.get('expected_impact', 0.5)
            },
            'target_agents': list(target_agents),
            'created_at': datetime.now(),
            'valid_until': datetime.now() + timedelta(days=30),  # 30天有效期
            'metadata': {
                'insight_type': 'collaboration_learning',
                'distribution_strategy': 'broadcast'
            }
        }

        return packet

    async def _distribute_packet(self, packet: Dict[str, Any],
                               target_agents: Set[str]) -> Dict[str, Any]:
        """分发知识包"""
        distribution_result = {
            'packet_id': packet['packet_id'],
            'target_count': len(target_agents),
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'delivery_details': []
        }

        # 模拟向每个智能体分发（实际应该通过通信中间件）
        for agent_id in target_agents:
            try:
                # 模拟分发过程
                delivery_detail = {
                    'agent_id': agent_id,
                    'status': 'delivered',
                    'timestamp': datetime.now(),
                    'reception_confirmed': True
                }
                distribution_result['successful_deliveries'] += 1
                distribution_result['delivery_details'].append(delivery_detail)

            except Exception as e:
                delivery_detail = {
                    'agent_id': agent_id,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now()
                }
                distribution_result['failed_deliveries'] += 1
                distribution_result['delivery_details'].append(delivery_detail)

        return distribution_result

    def _calculate_distribution_metrics(self, distribution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算分发指标"""
        total_packets = len(distribution_results)
        total_deliveries = sum(r['successful_deliveries'] for r in distribution_results)
        total_failures = sum(r['failed_deliveries'] for r in distribution_results)
        total_targets = sum(r['target_count'] for r in distribution_results)

        return {
            'total_packets': total_packets,
            'total_deliveries': total_deliveries,
            'total_failures': total_failures,
            'total_targets': total_targets,
            'delivery_success_rate': total_deliveries / total_targets if total_targets > 0 else 0,
            'average_deliveries_per_packet': total_deliveries / total_packets if total_packets > 0 else 0
        }

    async def _update_knowledge_base(self, learning_insights: LearningInsights):
        """更新知识库"""
        # 将洞察存储到知识库中
        for insight in learning_insights.actionable_recommendations:
            insight_key = insight['insight_id']
            self.knowledge_base[insight_key] = {
                'content': insight,
                'last_updated': datetime.now(),
                'usage_count': 0,
                'effectiveness_score': insight.get('expected_impact', 0.5)
            }

        # 清理过期知识
        cutoff_date = datetime.now() - timedelta(days=90)  # 90天过期
        expired_keys = [
            key for key, data in self.knowledge_base.items()
            if data['last_updated'] < cutoff_date
        ]

        for key in expired_keys:
            del self.knowledge_base[key]

        if expired_keys:
            logger.info(f"清理了{len(expired_keys)}个过期的知识条目")

    def get_knowledge_statistics(self) -> Dict[str, Any]:
        """获取知识统计"""
        total_knowledge = len(self.knowledge_base)
        total_distributions = len(self.distribution_history)

        if self.distribution_history:
            latest_distribution = max(self.distribution_history, key=lambda x: x['distributed_at'])
            recent_effectiveness = latest_distribution.get('distribution_metrics', {}).get('delivery_success_rate', 0)
        else:
            recent_effectiveness = 0

        return {
            'total_knowledge_items': total_knowledge,
            'total_distributions': total_distributions,
            'recent_distribution_effectiveness': recent_effectiveness,
            'knowledge_freshness': self._calculate_knowledge_freshness()
        }

    def _calculate_knowledge_freshness(self) -> float:
        """计算知识新鲜度"""
        if not self.knowledge_base:
            return 0.0

        now = datetime.now()
        ages = []

        for data in self.knowledge_base.values():
            age_days = (now - data['last_updated']).days
            # 30天内为新鲜（分数1.0），90天后过期（分数0.0）
            freshness = max(0.0, 1.0 - (age_days - 30) / 60) if age_days > 30 else 1.0
            ages.append(freshness)

        return statistics.mean(ages) if ages else 0.0


class CollaborationLearningAggregator:
    """
    协作学习聚合器

    聚合多智能体协作模式的学习，实现：
    - 协作模式识别和分析
    - 性能关联分析
    - 学习洞察合成
    - 知识在智能体间的分布
    """

    def __init__(self):
        self.pattern_recognizer = PatternRecognizer()
        self.collaboration_analyzer = CollaborationAnalyzer()
        self.learning_synthesizer = LearningSynthesizer()
        self.knowledge_distributor = KnowledgeDistributor()
        self.aggregation_history: List[Dict[str, Any]] = []

    async def aggregate_collaboration_learning(self,
                                             collaboration_sessions: List[CollaborationSession],
                                             performance_outcomes: List[PerformanceOutcome]
                                             ) -> LearningInsights:
        """聚合协作学习"""
        aggregation_start = datetime.now()

        try:
            logger.info(f"开始聚合{len(collaboration_sessions)}个协作会话的学习")

            # 1. 协作模式识别
            collaboration_patterns = await self.pattern_recognizer.identify_patterns(
                collaboration_sessions
            )
            logger.debug(f"识别出{len(collaboration_patterns)}个协作模式")

            # 2. 性能关联分析
            pattern_performance = await self.collaboration_analyzer.analyze_pattern_performance(
                collaboration_patterns, performance_outcomes
            )
            logger.debug(f"发现{len(pattern_performance)}个性能关联")

            # 3. 学习洞察合成
            learning_insights = await self.learning_synthesizer.synthesize_insights(
                collaboration_patterns, pattern_performance
            )
            logger.debug(f"合成了{len(learning_insights.actionable_recommendations)}个可操作推荐")

            # 4. 知识分布
            await self.knowledge_distributor.distribute_learning_knowledge(
                learning_insights, collaboration_sessions
            )

            # 记录聚合历史
            aggregation_record = {
                'aggregation_id': f"agg_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': aggregation_start,
                'duration': (datetime.now() - aggregation_start).total_seconds(),
                'input_sessions': len(collaboration_sessions),
                'input_outcomes': len(performance_outcomes),
                'patterns_identified': len(collaboration_patterns),
                'correlations_found': len(pattern_performance),
                'insights_generated': len(learning_insights.actionable_recommendations),
                'knowledge_distributed': len(learning_insights.actionable_recommendations),
                'insights': learning_insights
            }

            self.aggregation_history.append(aggregation_record)

            logger.info(f"协作学习聚合完成，生成{len(learning_insights.actionable_recommendations)}个洞察")

            return learning_insights

        except Exception as e:
            logger.error(f"协作学习聚合失败: {e}")
            raise

    def get_aggregation_statistics(self) -> Dict[str, Any]:
        """获取聚合统计"""
        if not self.aggregation_history:
            return {'total_aggregations': 0}

        total_aggregations = len(self.aggregation_history)
        total_sessions_processed = sum(h['input_sessions'] for h in self.aggregation_history)
        total_insights_generated = sum(h['insights_generated'] for h in self.aggregation_history)
        avg_processing_time = statistics.mean(h['duration'] for h in self.aggregation_history)

        return {
            'total_aggregations': total_aggregations,
            'total_sessions_processed': total_sessions_processed,
            'total_insights_generated': total_insights_generated,
            'average_processing_time': avg_processing_time,
            'insights_per_session': total_insights_generated / total_sessions_processed if total_sessions_processed > 0 else 0
        }

    def get_recent_insights(self, limit: int = 10) -> List[LearningInsights]:
        """获取最近的洞察"""
        if not self.aggregation_history:
            return []

        recent_aggregations = sorted(
            self.aggregation_history,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]

        return [agg['insights'] for agg in recent_aggregations]

    def export_learning_report(self, time_window_days: int = 7) -> Dict[str, Any]:
        """导出学习报告"""
        cutoff_date = datetime.now() - timedelta(days=time_window_days)

        recent_aggregations = [
            agg for agg in self.aggregation_history
            if agg['timestamp'] > cutoff_date
        ]

        report = {
            'report_period': f"{time_window_days}天",
            'generated_at': datetime.now(),
            'aggregations_count': len(recent_aggregations),
            'total_insights': sum(agg['insights_generated'] for agg in recent_aggregations),
            'total_sessions': sum(agg['input_sessions'] for agg in recent_aggregations),
            'pattern_recognizer_stats': self.pattern_recognizer._aggregate_similar_patterns.__wrapped__.__defaults__ if hasattr(self.pattern_recognizer._aggregate_similar_patterns, '__wrapped__') else {},
            'knowledge_distribution_stats': self.knowledge_distributor.get_knowledge_statistics(),
            'top_insights': []
        }

        # 收集热门洞察
        insight_counts = defaultdict(int)
        for agg in recent_aggregations:
            for insight in agg['insights'].actionable_recommendations:
                insight_counts[insight['title']] += 1

        top_insights = sorted(insight_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        report['top_insights'] = [{'title': title, 'frequency': count} for title, count in top_insights]

        return report


# 全局实例
_collaboration_learning_aggregator_instance: Optional[CollaborationLearningAggregator] = None

def get_collaboration_learning_aggregator() -> CollaborationLearningAggregator:
    """获取协作学习聚合器实例"""
    global _collaboration_learning_aggregator_instance
    if _collaboration_learning_aggregator_instance is None:
        _collaboration_learning_aggregator_instance = CollaborationLearningAggregator()
    return _collaboration_learning_aggregator_instance
