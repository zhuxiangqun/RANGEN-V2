"""
学习知识分布机制 (Learning Knowledge Distribution)

实现学习成果在智能体间的智能分布：
- 知识传播策略
- 智能体学习同步
- 知识演化和更新
- 分布式学习协调
- 知识质量保证
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import hashlib
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class DistributionStrategy(Enum):
    """分布策略"""
    BROADCAST = "broadcast"          # 广播所有智能体
    SELECTIVE = "selective"          # 选择性分布
    CASCADE = "cascade"              # 级联分布
    PEER_TO_PEER = "peer_to_peer"    # 对等分布
    HIERARCHICAL = "hierarchical"    # 层次分布


class KnowledgeType(Enum):
    """知识类型"""
    PATTERN_RECOGNITION = "pattern_recognition"    # 模式识别
    PERFORMANCE_OPTIMIZATION = "performance_optimization"  # 性能优化
    BEHAVIOR_ADAPTATION = "behavior_adaptation"    # 行为适应
    STRATEGY_IMPROVEMENT = "strategy_improvement"  # 策略改进
    CONFIGURATION_LEARNING = "configuration_learning"  # 配置学习


class KnowledgeScope(Enum):
    """知识范围"""
    INDIVIDUAL = "individual"        # 个体知识
    GROUP = "group"                  # 组知识
    ORGANIZATIONAL = "organizational" # 组织知识
    DOMAIN = "domain"                # 领域知识


@dataclass
class KnowledgePacket:
    """知识包"""
    packet_id: str
    knowledge_type: KnowledgeType
    scope: KnowledgeScope
    content: Dict[str, Any]
    source_agent: str
    target_agents: List[str]
    confidence_score: float
    validity_period: timedelta
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() - self.created_at > self.validity_period

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'packet_id': self.packet_id,
            'knowledge_type': self.knowledge_type.value,
            'scope': self.scope.value,
            'content': self.content,
            'source_agent': self.source_agent,
            'target_agents': self.target_agents,
            'confidence_score': self.confidence_score,
            'validity_period_days': self.validity_period.days,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class KnowledgeReception:
    """知识接收记录"""
    packet_id: str
    recipient_agent: str
    received_at: datetime
    acceptance_status: str  # accepted, rejected, deferred
    integration_status: str  # pending, integrated, failed
    performance_impact: Optional[Dict[str, float]] = None
    feedback_provided: Optional[Dict[str, Any]] = None


@dataclass
class KnowledgeEvolution:
    """知识演化记录"""
    original_packet_id: str
    evolved_packet_id: str
    evolution_type: str  # refinement, generalization, specialization
    changes_applied: Dict[str, Any]
    evolved_by: str
    evolution_timestamp: datetime
    quality_improvement: float


class KnowledgeRepository:
    """知识仓库"""

    def __init__(self, max_knowledge_items: int = 10000):
        self.knowledge_items: Dict[str, KnowledgePacket] = {}
        self.knowledge_index: Dict[KnowledgeType, Set[str]] = defaultdict(set)
        self.knowledge_receptions: Dict[str, List[KnowledgeReception]] = defaultdict(list)
        self.knowledge_evolutions: List[KnowledgeEvolution] = []
        self._max_items = max_knowledge_items

    async def store_knowledge(self, packet: KnowledgePacket) -> bool:
        """存储知识"""
        self.knowledge_items[packet.packet_id] = packet

        # 更新索引
        self.knowledge_index[packet.knowledge_type].add(packet.packet_id)

        # 清理过期知识
        await self._cleanup_expired_knowledge()

        # 限制知识数量
        if len(self.knowledge_items) > self._max_items:
            await self._evict_old_knowledge()

        logger.debug(f"存储知识包: {packet.packet_id} ({packet.knowledge_type.value})")
        return True

    async def retrieve_knowledge(self, knowledge_type: Optional[KnowledgeType] = None,
                               scope: Optional[KnowledgeScope] = None,
                               min_confidence: float = 0.0) -> List[KnowledgePacket]:
        """检索知识"""
        candidates = []

        if knowledge_type:
            packet_ids = self.knowledge_index.get(knowledge_type, set())
            candidates = [self.knowledge_items[pid] for pid in packet_ids if pid in self.knowledge_items]
        else:
            candidates = list(self.knowledge_items.values())

        # 过滤条件
        filtered = []
        for packet in candidates:
            if packet.is_expired:
                continue
            if scope and packet.scope != scope:
                continue
            if packet.confidence_score < min_confidence:
                continue
            filtered.append(packet)

        # 按置信度排序
        filtered.sort(key=lambda p: p.confidence_score, reverse=True)

        return filtered

    async def update_knowledge_confidence(self, packet_id: str, new_confidence: float,
                                        update_reason: str):
        """更新知识置信度"""
        if packet_id in self.knowledge_items:
            packet = self.knowledge_items[packet_id]
            old_confidence = packet.confidence_score
            packet.confidence_score = new_confidence
            packet.metadata['confidence_updates'] = packet.metadata.get('confidence_updates', [])
            packet.metadata['confidence_updates'].append({
                'old_value': old_confidence,
                'new_value': new_confidence,
                'reason': update_reason,
                'timestamp': datetime.now().isoformat()
            })

            logger.debug(f"更新知识置信度: {packet_id} {old_confidence:.2f} -> {new_confidence:.2f}")

    def record_knowledge_reception(self, reception: KnowledgeReception):
        """记录知识接收"""
        self.knowledge_receptions[reception.packet_id].append(reception)

    def record_knowledge_evolution(self, evolution: KnowledgeEvolution):
        """记录知识演化"""
        self.knowledge_evolutions.append(evolution)

    async def _cleanup_expired_knowledge(self):
        """清理过期知识"""
        expired_ids = [
            packet_id for packet_id, packet in self.knowledge_items.items()
            if packet.is_expired
        ]

        for packet_id in expired_ids:
            del self.knowledge_items[packet_id]

            # 从索引中移除
            for knowledge_type, packet_ids in self.knowledge_index.items():
                packet_ids.discard(packet_id)

        if expired_ids:
            logger.info(f"清理过期知识: {len(expired_ids)} 个项目")

    async def _evict_old_knowledge(self):
        """驱逐旧知识"""
        # 按创建时间排序，保留最新的
        sorted_packets = sorted(
            self.knowledge_items.items(),
            key=lambda x: x[1].created_at,
            reverse=True
        )

        # 保留最新的80%
        keep_count = int(self._max_items * 0.8)
        to_remove = sorted_packets[keep_count:]

        for packet_id, _ in to_remove:
            del self.knowledge_items[packet_id]

            # 从索引中移除
            for knowledge_type, packet_ids in self.knowledge_index.items():
                packet_ids.discard(packet_id)

        logger.info(f"驱逐旧知识: {len(to_remove)} 个项目")

    def get_repository_statistics(self) -> Dict[str, Any]:
        """获取仓库统计"""
        total_packets = len(self.knowledge_items)
        type_distribution = {
            ktype.value: len(packet_ids)
            for ktype, packet_ids in self.knowledge_index.items()
        }

        avg_confidence = 0.0
        if self.knowledge_items:
            avg_confidence = sum(p.confidence_score for p in self.knowledge_items.values()) / total_packets

        total_receptions = sum(len(receptions) for receptions in self.knowledge_receptions.values())

        return {
            'total_packets': total_packets,
            'type_distribution': type_distribution,
            'average_confidence': avg_confidence,
            'total_receptions': total_receptions,
            'evolution_events': len(self.knowledge_evolutions)
        }


class KnowledgeDistributionPlanner:
    """知识分布规划器"""

    def __init__(self):
        self.distribution_strategies: Dict[str, Dict[str, Any]] = {}
        self.agent_profiles: Dict[str, Dict[str, Any]] = {}

    def plan_distribution(self, packet: KnowledgePacket,
                         available_agents: List[str]) -> Dict[str, Any]:
        """规划知识分布"""
        strategy = packet.metadata.get('preferred_distribution_strategy', 'broadcast')

        if strategy == 'broadcast':
            return self._plan_broadcast_distribution(packet, available_agents)
        elif strategy == 'selective':
            return self._plan_selective_distribution(packet, available_agents)
        elif strategy == 'cascade':
            return self._plan_cascade_distribution(packet, available_agents)
        else:
            return self._plan_broadcast_distribution(packet, available_agents)

    def _plan_broadcast_distribution(self, packet: KnowledgePacket,
                                   available_agents: List[str]) -> Dict[str, Any]:
        """规划广播分布"""
        return {
            'strategy': 'broadcast',
            'target_agents': available_agents,
            'priority_order': available_agents,  # 所有智能体同等优先级
            'expected_reach': len(available_agents),
            'estimated_completion_time': len(available_agents) * 0.1  # 每智能体0.1秒
        }

    def _plan_selective_distribution(self, packet: KnowledgePacket,
                                   available_agents: List[str]) -> Dict[str, Any]:
        """规划选择性分布"""
        # 基于智能体特征选择目标
        suitable_agents = []

        for agent_id in available_agents:
            agent_profile = self.agent_profiles.get(agent_id, {})
            suitability_score = self._calculate_agent_suitability(agent_profile, packet)

            if suitability_score > 0.6:  # 适合度阈值
                suitable_agents.append((agent_id, suitability_score))

        # 按适合度排序
        suitable_agents.sort(key=lambda x: x[1], reverse=True)
        target_agents = [agent_id for agent_id, _ in suitable_agents]

        return {
            'strategy': 'selective',
            'target_agents': target_agents,
            'suitability_scores': dict(suitable_agents),
            'expected_reach': len(target_agents),
            'estimated_completion_time': len(target_agents) * 0.1
        }

    def _plan_cascade_distribution(self, packet: KnowledgePacket,
                                 available_agents: List[str]) -> Dict[str, Any]:
        """规划级联分布"""
        # 识别种子智能体（高影响力的智能体）
        seed_agents = self._identify_seed_agents(available_agents)

        # 创建级联层级
        cascade_layers = [seed_agents]

        remaining_agents = [a for a in available_agents if a not in seed_agents]
        layer_size = max(2, len(remaining_agents) // 3)  # 每层智能体数量

        while remaining_agents:
            layer = remaining_agents[:layer_size]
            cascade_layers.append(layer)
            remaining_agents = remaining_agents[layer_size:]

        return {
            'strategy': 'cascade',
            'cascade_layers': cascade_layers,
            'target_agents': available_agents,
            'expected_reach': len(available_agents),
            'estimated_completion_time': len(cascade_layers) * 0.5  # 每层0.5秒
        }

    def _calculate_agent_suitability(self, agent_profile: Dict[str, Any],
                                   packet: KnowledgePacket) -> float:
        """计算智能体适合度"""
        suitability = 0.5  # 基础适合度

        # 基于能力的适合度
        agent_capabilities = set(agent_profile.get('capabilities', []))
        knowledge_requirements = set(packet.content.get('required_capabilities', []))

        if knowledge_requirements:
            capability_match = len(agent_capabilities & knowledge_requirements) / len(knowledge_requirements)
            suitability += capability_match * 0.3

        # 基于经验的适合度
        agent_experience = agent_profile.get('experience_level', 0.5)
        suitability += agent_experience * 0.2

        # 基于当前负载的适合度
        current_load = agent_profile.get('current_load', 0.5)
        load_penalty = current_load * 0.1
        suitability -= load_penalty

        return max(0.0, min(1.0, suitability))

    def _identify_seed_agents(self, available_agents: List[str]) -> List[str]:
        """识别种子智能体"""
        # 选择影响力最大的智能体作为种子
        agent_scores = []

        for agent_id in available_agents:
            profile = self.agent_profiles.get(agent_id, {})
            influence_score = (
                profile.get('connectivity', 0.5) * 0.4 +
                profile.get('expertise_level', 0.5) * 0.4 +
                profile.get('reliability', 0.5) * 0.2
            )
            agent_scores.append((agent_id, influence_score))

        # 选择前20%的智能体作为种子
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        seed_count = max(1, len(agent_scores) // 5)
        seed_agents = [agent_id for agent_id, _ in agent_scores[:seed_count]]

        return seed_agents

    def update_agent_profile(self, agent_id: str, profile: Dict[str, Any]):
        """更新智能体配置"""
        self.agent_profiles[agent_id] = profile


class KnowledgeQualityAssurance:
    """知识质量保证"""

    def __init__(self):
        self.quality_checks: Dict[str, Callable] = {}
        self.quality_history: List[Dict[str, Any]] = []

    def register_quality_check(self, check_name: str, check_function: Callable):
        """注册质量检查"""
        self.quality_checks[check_name] = check_function

    async def assess_knowledge_quality(self, packet: KnowledgePacket) -> Dict[str, Any]:
        """评估知识质量"""
        assessment = {
            'packet_id': packet.packet_id,
            'overall_quality_score': 0.0,
            'quality_checks': {},
            'recommendations': [],
            'assessed_at': datetime.now()
        }

        total_score = 0.0
        check_count = 0

        # 执行所有质量检查
        for check_name, check_func in self.quality_checks.items():
            try:
                check_result = await check_func(packet)
                assessment['quality_checks'][check_name] = check_result

                if 'score' in check_result:
                    total_score += check_result['score']
                    check_count += 1

                if 'recommendations' in check_result:
                    assessment['recommendations'].extend(check_result['recommendations'])

            except Exception as e:
                logger.error(f"质量检查失败 {check_name}: {e}")
                assessment['quality_checks'][check_name] = {
                    'error': str(e),
                    'score': 0.0
                }

        # 计算总体质量分数
        if check_count > 0:
            assessment['overall_quality_score'] = total_score / check_count

        # 记录质量评估历史
        self.quality_history.append(assessment)

        return assessment

    async def _default_consistency_check(self, packet: KnowledgePacket) -> Dict[str, Any]:
        """一致性检查"""
        content = packet.content

        # 检查必需字段
        required_fields = ['description', 'insights']
        missing_fields = [field for field in required_fields if field not in content]

        if missing_fields:
            return {
                'score': 0.3,
                'issues': [f"缺少必需字段: {missing_fields}"],
                'recommendations': ['补充完整的知识内容']
            }

        # 检查内容一致性
        consistency_score = 0.8  # 基础一致性分数

        # 检查置信度与内容质量的匹配
        confidence = packet.confidence_score
        content_quality = len(str(content)) / 1000  # 简化的质量度量

        if abs(confidence - content_quality) > 0.3:
            consistency_score -= 0.2
            issues = ["置信度与内容质量不匹配"]
        else:
            issues = []

        return {
            'score': consistency_score,
            'issues': issues,
            'recommendations': [] if consistency_score > 0.7 else ['提高内容质量以匹配置信度']
        }

    async def _default_relevance_check(self, packet: KnowledgePacket) -> Dict[str, Any]:
        """相关性检查"""
        # 检查知识是否与目标智能体相关
        target_agents = packet.target_agents
        knowledge_scope = packet.scope

        relevance_score = 0.7  # 基础相关性分数

        # 领域知识应该有明确的适用范围
        if knowledge_scope == KnowledgeScope.DOMAIN and not target_agents:
            relevance_score -= 0.3
            issues = ["领域知识缺少明确的适用范围"]
        else:
            issues = []

        return {
            'score': relevance_score,
            'issues': issues,
            'recommendations': [] if relevance_score > 0.6 else ['明确知识的适用范围和目标群体']
        }


class KnowledgeDistributionCoordinator:
    """知识分布协调器"""

    def __init__(self):
        self.repository = KnowledgeRepository()
        self.distribution_planner = KnowledgeDistributionPlanner()
        self.quality_assurance = KnowledgeQualityAssurance()
        self.distribution_tasks: Dict[str, asyncio.Task] = {}
        self.distribution_history: List[Dict[str, Any]] = []

    async def distribute_knowledge(self, packet: KnowledgePacket,
                                 available_agents: List[str]) -> Dict[str, Any]:
        """分布知识"""
        distribution_id = f"dist_{packet.packet_id}_{datetime.now().strftime('%H%M%S')}"

        # 质量评估
        quality_assessment = await self.quality_assurance.assess_knowledge_quality(packet)

        # 如果质量不合格，拒绝分布
        if quality_assessment['overall_quality_score'] < 0.5:
            return {
                'distribution_id': distribution_id,
                'status': 'rejected',
                'reason': 'quality_check_failed',
                'quality_assessment': quality_assessment
            }

        # 规划分布
        distribution_plan = self.distribution_planner.plan_distribution(packet, available_agents)

        # 执行分布
        distribution_result = await self._execute_distribution(packet, distribution_plan)

        # 记录分布历史
        distribution_record = {
            'distribution_id': distribution_id,
            'packet_id': packet.packet_id,
            'plan': distribution_plan,
            'result': distribution_result,
            'quality_assessment': quality_assessment,
            'timestamp': datetime.now()
        }
        self.distribution_history.append(distribution_record)

        return {
            'distribution_id': distribution_id,
            'status': 'completed',
            'plan': distribution_plan,
            'result': distribution_result,
            'quality_assessment': quality_assessment
        }

    async def _execute_distribution(self, packet: KnowledgePacket,
                                  plan: Dict[str, Any]) -> Dict[str, Any]:
        """执行分布"""
        strategy = plan['strategy']
        target_agents = plan['target_agents']

        execution_result = {
            'strategy': strategy,
            'total_targets': len(target_agents),
            'successful_deliveries': 0,
            'failed_deliveries': 0,
            'delivery_details': []
        }

        if strategy == 'broadcast':
            execution_result.update(await self._execute_broadcast_distribution(packet, target_agents))
        elif strategy == 'selective':
            execution_result.update(await self._execute_selective_distribution(packet, target_agents))
        elif strategy == 'cascade':
            execution_result.update(await self._execute_cascade_distribution(packet, plan['cascade_layers']))
        else:
            execution_result.update(await self._execute_broadcast_distribution(packet, target_agents))

        return execution_result

    async def _execute_broadcast_distribution(self, packet: KnowledgePacket,
                                           target_agents: List[str]) -> Dict[str, Any]:
        """执行广播分布"""
        # 并行向所有目标智能体发送知识
        delivery_tasks = []

        for agent_id in target_agents:
            task = asyncio.create_task(self._deliver_knowledge_to_agent(packet, agent_id))
            delivery_tasks.append(task)

        # 等待所有投递完成
        results = await asyncio.gather(*delivery_tasks, return_exceptions=True)

        successful = sum(1 for r in results if not isinstance(r, Exception) and r.get('success', False))
        failed = len(results) - successful

        return {
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'delivery_details': results
        }

    async def _execute_selective_distribution(self, packet: KnowledgePacket,
                                           target_agents: List[str]) -> Dict[str, Any]:
        """执行选择性分布"""
        # 按优先级顺序分布
        successful = 0
        failed = 0
        delivery_details = []

        for agent_id in target_agents:
            result = await self._deliver_knowledge_to_agent(packet, agent_id)
            delivery_details.append(result)

            if result.get('success', False):
                successful += 1
            else:
                failed += 1

        return {
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'delivery_details': delivery_details
        }

    async def _execute_cascade_distribution(self, packet: KnowledgePacket,
                                         cascade_layers: List[List[str]]) -> Dict[str, Any]:
        """执行级联分布"""
        successful = 0
        failed = 0
        delivery_details = []

        # 逐层分布
        for layer in cascade_layers:
            layer_tasks = [
                self._deliver_knowledge_to_agent(packet, agent_id)
                for agent_id in layer
            ]

            layer_results = await asyncio.gather(*layer_tasks, return_exceptions=True)

            for result in layer_results:
                if not isinstance(result, Exception) and result.get('success', False):
                    successful += 1
                else:
                    failed += 1

                delivery_details.append(result)

            # 层间延迟
            await asyncio.sleep(0.1)

        return {
            'successful_deliveries': successful,
            'failed_deliveries': failed,
            'delivery_details': delivery_details,
            'cascade_layers': len(cascade_layers)
        }

    async def _deliver_knowledge_to_agent(self, packet: KnowledgePacket,
                                        agent_id: str) -> Dict[str, Any]:
        """向智能体投递知识"""
        try:
            # 这里应该通过通信中间件发送知识
            # 暂时模拟投递过程
            await asyncio.sleep(0.05)  # 模拟网络延迟

            # 记录接收
            reception = KnowledgeReception(
                packet_id=packet.packet_id,
                recipient_agent=agent_id,
                received_at=datetime.now(),
                acceptance_status='accepted',
                integration_status='pending'
            )

            await self.repository.store_knowledge(packet)
            self.repository.record_knowledge_reception(reception)

            return {
                'agent_id': agent_id,
                'success': True,
                'delivery_time': 0.05,
                'status': 'delivered'
            }

        except Exception as e:
            return {
                'agent_id': agent_id,
                'success': False,
                'error': str(e),
                'status': 'failed'
            }

    def update_agent_profile(self, agent_id: str, profile: Dict[str, Any]):
        """更新智能体配置"""
        self.distribution_planner.update_agent_profile(agent_id, profile)

    def get_distribution_statistics(self) -> Dict[str, Any]:
        """获取分布统计"""
        total_distributions = len(self.distribution_history)

        if not self.distribution_history:
            return {'total_distributions': 0}

        successful_distributions = sum(
            1 for d in self.distribution_history
            if d['result'].get('successful_deliveries', 0) > 0
        )

        total_deliveries = sum(d['result'].get('successful_deliveries', 0) for d in self.distribution_history)
        total_failures = sum(d['result'].get('failed_deliveries', 0) for d in self.distribution_history)

        strategy_usage = defaultdict(int)
        for d in self.distribution_history:
            strategy_usage[d['plan']['strategy']] += 1

        return {
            'total_distributions': total_distributions,
            'successful_distributions': successful_distributions,
            'success_rate': successful_distributions / total_distributions if total_distributions > 0 else 0,
            'total_deliveries': total_deliveries,
            'total_failures': total_failures,
            'delivery_success_rate': total_deliveries / (total_deliveries + total_failures) if (total_deliveries + total_failures) > 0 else 0,
            'strategy_usage': dict(strategy_usage),
            'repository_stats': self.repository.get_repository_statistics()
        }


class LearningKnowledgeDistribution:
    """
    学习知识分布机制

    实现学习成果在智能体间的智能分布：
    - 知识传播策略和协调
    - 智能体学习同步
    - 知识演化和更新
    - 分布式学习协调
    - 知识质量保证
    """

    def __init__(self):
        self.coordinator = KnowledgeDistributionCoordinator()
        self.knowledge_evolution_engine = KnowledgeEvolutionEngine()
        self.learning_sync_manager = LearningSynchronizationManager()

    async def initialize_distribution_system(self):
        """初始化分布系统"""
        # 注册默认质量检查
        await self.coordinator.quality_assurance.register_quality_check(
            'consistency_check',
            self.coordinator.quality_assurance._default_consistency_check
        )
        await self.coordinator.quality_assurance.register_quality_check(
            'relevance_check',
            self.coordinator.quality_assurance._default_relevance_check
        )

        logger.info("学习知识分布系统初始化完成")

    async def distribute_learning_insights(self, insights: List[Dict[str, Any]],
                                         available_agents: List[str]) -> Dict[str, Any]:
        """分布学习洞察"""
        distribution_results = []

        for insight in insights:
            # 创建知识包
            packet = KnowledgePacket(
                packet_id=f"insight_{insight['insight_id']}",
                knowledge_type=KnowledgeType.PATTERN_RECOGNITION,
                scope=KnowledgeScope.ORGANIZATIONAL,
                content=insight,
                source_agent='learning_system',
                target_agents=available_agents,
                confidence_score=insight.get('confidence', 0.8),
                validity_period=timedelta(days=30),
                metadata={
                    'insight_type': insight.get('type'),
                    'distribution_strategy': 'selective'
                }
            )

            # 分布知识
            result = await self.coordinator.distribute_knowledge(packet, available_agents)
            distribution_results.append(result)

        return {
            'total_insights': len(insights),
            'distribution_results': distribution_results,
            'overall_success_rate': self._calculate_overall_success_rate(distribution_results)
        }

    async def synchronize_agent_learning(self, agent_id: str,
                                       learning_state: Dict[str, Any]) -> Dict[str, Any]:
        """同步智能体学习"""
        return await self.learning_sync_manager.synchronize_agent_learning(agent_id, learning_state)

    async def evolve_knowledge(self, packet_id: str, evolution_data: Dict[str, Any],
                             evolved_by: str) -> Optional[KnowledgePacket]:
        """演化知识"""
        return await self.knowledge_evolution_engine.evolve_knowledge(packet_id, evolution_data, evolved_by)

    def update_agent_profile(self, agent_id: str, profile: Dict[str, Any]):
        """更新智能体配置"""
        self.coordinator.update_agent_profile(agent_id, profile)

    def get_distribution_system_status(self) -> Dict[str, Any]:
        """获取分布系统状态"""
        return {
            'coordinator_stats': self.coordinator.get_distribution_statistics(),
            'evolution_stats': self.knowledge_evolution_engine.get_evolution_statistics(),
            'sync_stats': self.learning_sync_manager.get_synchronization_statistics()
        }

    def _calculate_overall_success_rate(self, distribution_results: List[Dict[str, Any]]) -> float:
        """计算总体成功率"""
        if not distribution_results:
            return 0.0

        successful_distributions = sum(
            1 for r in distribution_results
            if r.get('status') == 'completed'
        )

        return successful_distributions / len(distribution_results)


class KnowledgeEvolutionEngine:
    """知识演化引擎"""

    def __init__(self):
        self.evolution_history: List[KnowledgeEvolution] = []
        self.evolution_strategies: Dict[str, Callable] = {}

    async def evolve_knowledge(self, packet_id: str, evolution_data: Dict[str, Any],
                             evolved_by: str) -> Optional[KnowledgePacket]:
        """演化知识"""
        # 这里应该实现知识演化的具体逻辑
        # 暂时返回None
        return None

    def get_evolution_statistics(self) -> Dict[str, Any]:
        """获取演化统计"""
        return {
            'total_evolutions': len(self.evolution_history),
            'evolution_types': {}
        }


class LearningSynchronizationManager:
    """学习同步管理器"""

    def __init__(self):
        self.agent_learning_states: Dict[str, Dict[str, Any]] = {}
        self.sync_history: List[Dict[str, Any]] = []

    async def synchronize_agent_learning(self, agent_id: str,
                                       learning_state: Dict[str, Any]) -> Dict[str, Any]:
        """同步智能体学习"""
        # 这里应该实现学习同步的具体逻辑
        # 暂时返回成功
        return {
            'agent_id': agent_id,
            'status': 'synchronized',
            'synced_at': datetime.now()
        }

    def get_synchronization_statistics(self) -> Dict[str, Any]:
        """获取同步统计"""
        return {
            'total_syncs': len(self.sync_history),
            'active_agents': len(self.agent_learning_states)
        }


# 全局实例
_learning_knowledge_distribution_instance: Optional[LearningKnowledgeDistribution] = None

def get_learning_knowledge_distribution() -> LearningKnowledgeDistribution:
    """获取学习知识分布机制实例"""
    global _learning_knowledge_distribution_instance
    if _learning_knowledge_distribution_instance is None:
        _learning_knowledge_distribution_instance = LearningKnowledgeDistribution()
    return _learning_knowledge_distribution_instance
