"""
自适应任务分配器 (Adaptive Task Allocator)

基于智能体状态、任务特征和历史表现进行智能任务分配：
- 多维度智能体评估
- 任务-智能体匹配优化
- 负载均衡和性能预测
- 动态调整和学习
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import statistics

logger = logging.getLogger(__name__)


class AllocationStrategy(Enum):
    """分配策略"""
    LOAD_BALANCING = "load_balancing"          # 负载均衡
    CAPABILITY_MATCHING = "capability_matching" # 能力匹配
    PERFORMANCE_BASED = "performance_based"    # 基于性能
    COST_OPTIMIZATION = "cost_optimization"    # 成本优化
    HYBRID = "hybrid"                         # 混合策略


@dataclass
class AgentProfile:
    """智能体配置"""
    agent_id: str
    agent_type: str
    capabilities: List[str]
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    current_load: float = 0.0  # 0.0 到 1.0
    specialization_score: Dict[str, float] = field(default_factory=dict)  # 各任务类型的专精度
    reliability_score: float = 0.8  # 可靠性评分
    average_response_time: float = 0.0
    success_rate: float = 0.9
    resource_limits: Dict[str, float] = field(default_factory=dict)
    last_active: datetime = field(default_factory=datetime.now)


@dataclass
class TaskRequirements:
    """任务需求"""
    task_id: str
    task_type: str
    required_capabilities: List[str]
    estimated_complexity: float  # 0.0 到 1.0
    estimated_duration: float  # 预计执行时间（秒）
    priority: int  # 1-10
    deadline: Optional[datetime] = None
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AllocationDecision:
    """分配决策"""
    task_id: str
    selected_agent: str
    strategy_used: AllocationStrategy
    confidence_score: float  # 0.0 到 1.0
    expected_performance: Dict[str, Any]
    alternative_agents: List[Tuple[str, float]]  # (agent_id, score)
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AllocationResult:
    """分配结果"""
    success: bool
    decision: Optional[AllocationDecision] = None
    error_message: Optional[str] = None
    alternatives_tried: int = 0


class AgentEvaluator:
    """智能体评估器"""

    def __init__(self):
        self.performance_weights = {
            'capability_match': 0.3,
            'current_load': 0.2,
            'performance_history': 0.25,
            'reliability': 0.15,
            'specialization': 0.1
        }

    async def evaluate_agent_for_task(self, agent: AgentProfile,
                                    task: TaskRequirements) -> Dict[str, Any]:
        """评估智能体对任务的适合度"""
        scores = {}

        # 1. 能力匹配度
        capability_score = self._calculate_capability_match(agent, task)
        scores['capability_match'] = capability_score

        # 2. 当前负载评估
        load_score = self._calculate_load_score(agent)
        scores['current_load'] = load_score

        # 3. 历史性能评估
        performance_score = self._calculate_performance_score(agent, task.task_type)
        scores['performance_history'] = performance_score

        # 4. 可靠性评估
        reliability_score = agent.reliability_score
        scores['reliability'] = reliability_score

        # 5. 专业化评估
        specialization_score = agent.specialization_score.get(task.task_type, 0.5)
        scores['specialization'] = specialization_score

        # 计算综合评分
        overall_score = sum(
            scores[metric] * weight
            for metric, weight in self.performance_weights.items()
        )

        # 预测性能指标
        expected_performance = self._predict_performance(agent, task, scores)

        return {
            'overall_score': overall_score,
            'component_scores': scores,
            'expected_performance': expected_performance,
            'is_feasible': capability_score > 0.6 and load_score > 0.3  # 基本可行性检查
        }

    def _calculate_capability_match(self, agent: AgentProfile, task: TaskRequirements) -> float:
        """计算能力匹配度"""
        if not task.required_capabilities:
            return 1.0  # 无特殊要求，完全匹配

        matched_capabilities = 0
        for required_cap in task.required_capabilities:
            if required_cap in agent.capabilities:
                matched_capabilities += 1

        return matched_capabilities / len(task.required_capabilities)

    def _calculate_load_score(self, agent: AgentProfile) -> float:
        """计算负载评分（负载越低评分越高）"""
        # 负载为0时得分为1.0，负载为1.0时得分为0.0
        return 1.0 - agent.current_load

    def _calculate_performance_score(self, agent: AgentProfile, task_type: str) -> float:
        """计算历史性能评分"""
        if not agent.performance_history:
            return 0.7  # 默认中等性能

        # 筛选相关任务类型的性能记录
        relevant_history = [
            record for record in agent.performance_history
            if record.get('task_type') == task_type
        ]

        if not relevant_history:
            return 0.6  # 无相关经验，较低评分

        # 计算平均性能评分
        performance_scores = [
            record.get('performance_score', 0.7)
            for record in relevant_history[-10:]  # 最近10次记录
        ]

        return statistics.mean(performance_scores) if performance_scores else 0.6

    def _predict_performance(self, agent: AgentProfile, task: TaskRequirements,
                           component_scores: Dict[str, float]) -> Dict[str, Any]:
        """预测执行性能"""
        # 基于历史数据和当前状态预测
        base_performance = component_scores['performance_history']

        # 考虑负载影响
        load_penalty = agent.current_load * 0.2
        adjusted_performance = base_performance * (1.0 - load_penalty)

        # 考虑任务复杂度
        complexity_factor = 1.0 - (task.estimated_complexity * 0.3)
        final_performance = adjusted_performance * complexity_factor

        # 预测执行时间
        if agent.average_response_time > 0:
            expected_duration = agent.average_response_time * (2.0 - final_performance)
        else:
            expected_duration = task.estimated_duration * (2.0 - final_performance)

        return {
            'expected_performance_score': final_performance,
            'expected_duration': expected_duration,
            'confidence_level': min(component_scores.values())  # 以最低分作为置信度
        }


class AdaptiveTaskAllocator:
    """
    自适应任务分配器

    基于多维度评估进行智能任务分配：
    - 实时智能体状态监控
    - 任务-智能体匹配优化
    - 多策略分配算法
    - 持续学习和改进
    """

    def __init__(self):
        self.agent_evaluator = AgentEvaluator()
        self.agents: Dict[str, AgentProfile] = {}
        self.allocation_history: List[AllocationDecision] = []
        self.strategy_performance: Dict[AllocationStrategy, List[float]] = {
            strategy: [] for strategy in AllocationStrategy
        }

        # 配置参数
        self.max_alternatives_to_try = 3
        self.performance_history_window = 100
        self.learning_rate = 0.1

    async def allocate_task(self, task: TaskRequirements,
                          available_agents: List[str]) -> AllocationResult:
        """分配任务给最适合的智能体"""
        try:
            # 筛选可用的智能体
            available_agent_profiles = [
                self.agents[agent_id] for agent_id in available_agents
                if agent_id in self.agents
            ]

            if not available_agent_profiles:
                return AllocationResult(
                    success=False,
                    error_message="没有可用的智能体"
                )

            # 选择分配策略
            strategy = await self._select_allocation_strategy(task)

            # 执行分配
            decision = await self._execute_allocation(task, available_agent_profiles, strategy)

            if decision:
                # 记录分配历史
                self.allocation_history.append(decision)

                # 更新智能体负载
                self._update_agent_load(decision.selected_agent, task)

                return AllocationResult(success=True, decision=decision)
            else:
                return AllocationResult(
                    success=False,
                    error_message="无法找到合适的智能体分配",
                    alternatives_tried=len(available_agent_profiles)
                )

        except Exception as e:
            logger.error(f"任务分配失败: {e}")
            return AllocationResult(
                success=False,
                error_message=f"分配过程出错: {str(e)}"
            )

    async def _select_allocation_strategy(self, task: TaskRequirements) -> AllocationStrategy:
        """选择分配策略"""
        # 基于任务特征和历史性能选择策略

        if task.priority >= 8:  # 高优先级任务
            return AllocationStrategy.PERFORMANCE_BASED
        elif task.estimated_complexity > 0.7:  # 高复杂度任务
            return AllocationStrategy.CAPABILITY_MATCHING
        elif len(self.allocation_history) < 10:  # 历史数据不足
            return AllocationStrategy.LOAD_BALANCING
        else:
            return AllocationStrategy.HYBRID

    async def _execute_allocation(self, task: TaskRequirements,
                                agent_profiles: List[AgentProfile],
                                strategy: AllocationStrategy) -> Optional[AllocationDecision]:
        """执行分配逻辑"""

        if strategy == AllocationStrategy.LOAD_BALANCING:
            return await self._allocate_by_load_balancing(task, agent_profiles)
        elif strategy == AllocationStrategy.CAPABILITY_MATCHING:
            return await self._allocate_by_capability_matching(task, agent_profiles)
        elif strategy == AllocationStrategy.PERFORMANCE_BASED:
            return await self._allocate_by_performance(task, agent_profiles)
        elif strategy == AllocationStrategy.HYBRID:
            return await self._allocate_by_hybrid_approach(task, agent_profiles)
        else:
            return await self._allocate_by_load_balancing(task, agent_profiles)  # 默认策略

    async def _allocate_by_load_balancing(self, task: TaskRequirements,
                                        agent_profiles: List[AgentProfile]) -> Optional[AllocationDecision]:
        """基于负载均衡的分配"""
        # 选择负载最低的智能体
        sorted_agents = sorted(agent_profiles, key=lambda a: a.current_load)

        for agent in sorted_agents[:self.max_alternatives_to_try]:
            evaluation = await self.agent_evaluator.evaluate_agent_for_task(agent, task)
            if evaluation['is_feasible']:
                return AllocationDecision(
                    task_id=task.task_id,
                    selected_agent=agent.agent_id,
                    strategy_used=AllocationStrategy.LOAD_BALANCING,
                    confidence_score=evaluation['overall_score'],
                    expected_performance=evaluation['expected_performance'],
                    alternative_agents=[
                        (a.agent_id, await self._quick_score_agent(a, task))
                        for a in sorted_agents[1:self.max_alternatives_to_try+1]
                    ],
                    reasoning=f"选择负载最低的智能体: {agent.agent_id} (负载: {agent.current_load:.2f})"
                )

        return None

    async def _allocate_by_capability_matching(self, task: TaskRequirements,
                                            agent_profiles: List[AgentProfile]) -> Optional[AllocationDecision]:
        """基于能力匹配的分配"""
        # 计算每个智能体的能力匹配度
        agent_scores = []
        for agent in agent_profiles:
            evaluation = await self.agent_evaluator.evaluate_agent_for_task(agent, task)
            if evaluation['is_feasible']:
                agent_scores.append((agent, evaluation))

        if not agent_scores:
            return None

        # 选择能力匹配度最高的
        best_agent, best_evaluation = max(agent_scores, key=lambda x: x[1]['overall_score'])

        return AllocationDecision(
            task_id=task.task_id,
            selected_agent=best_agent.agent_id,
            strategy_used=AllocationStrategy.CAPABILITY_MATCHING,
            confidence_score=best_evaluation['overall_score'],
            expected_performance=best_evaluation['expected_performance'],
            alternative_agents=[
                (agent.agent_id, eval_data['overall_score'])
                for agent, eval_data in agent_scores[1:self.max_alternatives_to_try+1]
            ],
            reasoning=f"选择能力匹配度最高的智能体: {best_agent.agent_id}"
        )

    async def _allocate_by_performance(self, task: TaskRequirements,
                                     agent_profiles: List[AgentProfile]) -> Optional[AllocationDecision]:
        """基于性能历史的分配"""
        # 选择历史性能最好的智能体
        agent_scores = []
        for agent in agent_profiles:
            evaluation = await self.agent_evaluator.evaluate_agent_for_task(agent, task)
            if evaluation['is_feasible']:
                # 更重视历史性能
                performance_weighted_score = (
                    evaluation['overall_score'] * 0.7 +
                    evaluation['component_scores']['performance_history'] * 0.3
                )
                agent_scores.append((agent, evaluation, performance_weighted_score))

        if not agent_scores:
            return None

        best_agent, best_evaluation, _ = max(agent_scores, key=lambda x: x[2])

        return AllocationDecision(
            task_id=task.task_id,
            selected_agent=best_agent.agent_id,
            strategy_used=AllocationStrategy.PERFORMANCE_BASED,
            confidence_score=best_evaluation['overall_score'],
            expected_performance=best_evaluation['expected_performance'],
            alternative_agents=[
                (agent.agent_id, score)
                for agent, _, score in agent_scores[1:self.max_alternatives_to_try+1]
            ],
            reasoning=f"选择历史性能最好的智能体: {best_agent.agent_id}"
        )

    async def _allocate_by_hybrid_approach(self, task: TaskRequirements,
                                         agent_profiles: List[AgentProfile]) -> Optional[AllocationDecision]:
        """混合策略分配"""
        # 结合多种因素的综合评估
        candidates = []

        for agent in agent_profiles:
            evaluation = await self.agent_evaluator.evaluate_agent_for_task(agent, task)
            if evaluation['is_feasible']:
                # 综合评分：能力(30%) + 性能(30%) + 负载(20%) + 可靠性(20%)
                hybrid_score = (
                    evaluation['component_scores']['capability_match'] * 0.3 +
                    evaluation['component_scores']['performance_history'] * 0.3 +
                    evaluation['component_scores']['current_load'] * 0.2 +
                    evaluation['component_scores']['reliability'] * 0.2
                )
                candidates.append((agent, evaluation, hybrid_score))

        if not candidates:
            return None

        best_agent, best_evaluation, _ = max(candidates, key=lambda x: x[2])

        return AllocationDecision(
            task_id=task.task_id,
            selected_agent=best_agent.agent_id,
            strategy_used=AllocationStrategy.HYBRID,
            confidence_score=best_evaluation['overall_score'],
            expected_performance=best_evaluation['expected_performance'],
            alternative_agents=[
                (agent.agent_id, score)
                for agent, _, score in candidates[1:self.max_alternatives_to_try+1]
            ],
            reasoning=f"混合策略选择最适合的智能体: {best_agent.agent_id}"
        )

    async def _quick_score_agent(self, agent: AgentProfile, task: TaskRequirements) -> float:
        """快速评估智能体适合度（用于备选方案）"""
        evaluation = await self.agent_evaluator.evaluate_agent_for_task(agent, task)
        return evaluation['overall_score']

    def _update_agent_load(self, agent_id: str, task: TaskRequirements):
        """更新智能体负载"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            # 估算负载增加（基于任务复杂度）
            load_increase = min(task.estimated_complexity * 0.2, 0.3)
            agent.current_load = min(1.0, agent.current_load + load_increase)

    def register_agent(self, agent: AgentProfile):
        """注册智能体"""
        self.agents[agent.agent_id] = agent
        logger.info(f"注册智能体: {agent.agent_id} ({agent.agent_type})")

    def update_agent_status(self, agent_id: str, status_update: Dict[str, Any]):
        """更新智能体状态"""
        if agent_id not in self.agents:
            return

        agent = self.agents[agent_id]

        # 更新负载
        if 'current_load' in status_update:
            agent.current_load = status_update['current_load']

        # 更新性能历史
        if 'performance_record' in status_update:
            agent.performance_history.append(status_update['performance_record'])
            # 保持历史记录在合理范围内
            if len(agent.performance_history) > self.performance_history_window:
                agent.performance_history = agent.performance_history[-self.performance_history_window:]

        # 更新可靠性评分
        if 'task_success' in status_update:
            success = status_update['task_success']
            # 简单的指数移动平均
            agent.success_rate = agent.success_rate * (1 - self.learning_rate) + success * self.learning_rate

        agent.last_active = datetime.now()

    def record_allocation_result(self, decision: AllocationDecision,
                               actual_performance: Dict[str, Any]):
        """记录分配结果用于学习"""
        # 更新策略性能历史
        strategy = decision.strategy_used
        performance_score = actual_performance.get('performance_score', 0.7)
        self.strategy_performance[strategy].append(performance_score)

        # 保持历史记录长度
        if len(self.strategy_performance[strategy]) > 50:
            self.strategy_performance[strategy] = self.strategy_performance[strategy][-50:]

        # 更新智能体的专业化评分
        agent = self.agents.get(decision.selected_agent)
        if agent:
            task_type = decision.task_id.split('_')[0]  # 简单的任务类型提取
            current_score = agent.specialization_score.get(task_type, 0.5)
            # 基于实际性能调整专业化评分
            new_score = current_score * (1 - self.learning_rate) + performance_score * self.learning_rate
            agent.specialization_score[task_type] = new_score

    def get_allocation_statistics(self) -> Dict[str, Any]:
        """获取分配统计信息"""
        total_allocations = len(self.allocation_history)

        if total_allocations == 0:
            return {'total_allocations': 0}

        # 策略使用统计
        strategy_counts = {}
        for decision in self.allocation_history:
            strategy = decision.strategy_used
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        # 平均置信度
        avg_confidence = statistics.mean(d.confidence_score for d in self.allocation_history)

        # 策略性能统计
        strategy_performance_stats = {}
        for strategy, performances in self.strategy_performance.items():
            if performances:
                strategy_performance_stats[strategy.value] = {
                    'avg_performance': statistics.mean(performances),
                    'sample_count': len(performances)
                }

        return {
            'total_allocations': total_allocations,
            'strategy_distribution': {k.value: v for k, v in strategy_counts.items()},
            'average_confidence': avg_confidence,
            'strategy_performance': strategy_performance_stats,
            'registered_agents': len(self.agents)
        }


# 全局实例
_allocator_instance: Optional[AdaptiveTaskAllocator] = None

def get_adaptive_task_allocator() -> AdaptiveTaskAllocator:
    """获取自适应任务分配器实例"""
    global _allocator_instance
    if _allocator_instance is None:
        _allocator_instance = AdaptiveTaskAllocator()
    return _allocator_instance
