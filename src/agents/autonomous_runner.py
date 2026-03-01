"""
自主运行Agent (L7级别)
实现完全自主的运行能力，能够自我规划、自我优化和自我进化
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import uuid
import json
import random

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from .multi_agent_coordinator import MultiAgentCoordinator
from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center, get_unified_intelligent_center

logger = logging.getLogger(__name__)

@dataclass
class AutonomousGoal:
    """自主目标"""
    goal_id: str
    description: str
    priority: int  # 1-10
    deadline: Optional[datetime]
    status: str = "active"  # active, completed, failed, suspended
    progress: float = 0.0  # 0-1
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LearningInsight:
    """学习洞察"""
    insight_id: str
    type: str  # performance, pattern, anomaly, opportunity
    description: str
    confidence: float
    impact: str  # high, medium, low
    actionable: bool = True
    discovered_at: datetime = field(default_factory=datetime.now)
    applied: bool = False
    applied_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EvolutionaryStrategy:
    """进化策略"""
    strategy_id: str
    name: str
    description: str
    type: str  # adaptation, optimization, innovation
    conditions: Dict[str, Any]  # 触发条件
    actions: List[Dict[str, Any]]  # 执行动作
    success_rate: float = 0.0
    last_applied: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

class AutonomousRunner(ExpertAgent):
    """
    自主运行Agent (L7级别)
    实现完全自主的运行能力：
    - 自我规划和目标管理
    - 持续学习和洞察发现
    - 自适应优化和进化
    - 自主决策和问题解决
    """

    def __init__(self):
        super().__init__(
            agent_id="autonomous_runner",
            domain_expertise="自主运行和自我进化",
            capability_level=1.0,  # L7级别
            collaboration_style="autonomous"
        )
        self.module_logger = get_module_logger(ModuleType.AGENT, "AutonomousRunner")
        self.config_center = get_unified_config_center()
        self.intelligent_center = get_unified_intelligent_center()

        # 目标管理系统
        self.active_goals: Dict[str, AutonomousGoal] = {}
        self.completed_goals: deque[AutonomousGoal] = deque(maxlen=500)
        self.goal_templates: Dict[str, Dict[str, Any]] = {}

        # 学习和洞察系统
        self.learning_insights: deque[LearningInsight] = deque(maxlen=1000)
        self.performance_history: deque[Dict[str, Any]] = deque(maxlen=2000)
        self.pattern_recognition: Dict[str, Dict[str, Any]] = {}

        # 进化系统
        self.evolutionary_strategies: Dict[str, EvolutionaryStrategy] = {}
        self.evolution_history: deque[Dict[str, Any]] = deque(maxlen=500)

        # 自适应系统
        self.environment_adaptation: Dict[str, Any] = {}
        self.self_optimization_rules: Dict[str, Dict[str, Any]] = {}

        # 协作协调器引用
        self.multi_agent_coordinator: Optional[MultiAgentCoordinator] = None

        # 配置参数
        self.learning_interval = self.config_center.get_config_value(
            "autonomous_runner", "learning_interval_seconds", 3600
        )
        self.evolution_check_interval = self.config_center.get_config_value(
            "autonomous_runner", "evolution_check_interval_seconds", 7200
        )
        self.goal_review_interval = self.config_center.get_config_value(
            "autonomous_runner", "goal_review_interval_seconds", 1800
        )

        # 运行状态
        self._learning_task: Optional[asyncio.Task] = None
        self._evolution_task: Optional[asyncio.Task] = None
        self._goal_management_task: Optional[asyncio.Task] = None
        self._adaptation_task: Optional[asyncio.Task] = None
        self._running = False

        # 统计信息
        self.total_goals_achieved = 0
        self.learning_insights_discovered = 0
        self.evolutionary_actions_taken = 0
        self.autonomous_decisions_made = 0
        self.system_efficiency_score = 1.0

        # 初始化
        self._initialize_goal_templates()
        self._initialize_evolutionary_strategies()
        self._initialize_adaptation_rules()

    def _initialize_goal_templates(self):
        """初始化目标模板"""
        self.goal_templates = {
            "performance_optimization": {
                "description": "优化系统性能指标",
                "priority": 8,
                "subtasks": [
                    {"type": "analysis", "description": "分析当前性能瓶颈"},
                    {"type": "planning", "description": "制定优化计划"},
                    {"type": "implementation", "description": "实施优化措施"},
                    {"type": "validation", "description": "验证优化效果"}
                ]
            },
            "learning_enhancement": {
                "description": "增强学习和适应能力",
                "priority": 7,
                "subtasks": [
                    {"type": "assessment", "description": "评估当前学习能力"},
                    {"type": "research", "description": "研究改进方法"},
                    {"type": "implementation", "description": "实施学习增强"},
                    {"type": "testing", "description": "测试学习效果"}
                ]
            },
            "system_health_maintenance": {
                "description": "维护系统健康状态",
                "priority": 9,
                "subtasks": [
                    {"type": "monitoring", "description": "监控系统状态"},
                    {"type": "diagnosis", "description": "诊断潜在问题"},
                    {"type": "maintenance", "description": "执行维护任务"},
                    {"type": "verification", "description": "验证系统健康"}
                ]
            },
            "capability_expansion": {
                "description": "扩展系统能力边界",
                "priority": 6,
                "subtasks": [
                    {"type": "exploration", "description": "探索新的能力领域"},
                    {"type": "evaluation", "description": "评估扩展可行性"},
                    {"type": "development", "description": "开发新能力"},
                    {"type": "integration", "description": "整合新能力"}
                ]
            }
        }

    def _initialize_evolutionary_strategies(self):
        """初始化进化策略"""
        strategies = [
            {
                "strategy_id": "performance_adaptation",
                "name": "性能自适应",
                "description": "根据性能指标动态调整系统配置",
                "type": "adaptation",
                "conditions": {
                    "performance_degradation": 0.15,  # 性能下降15%
                    "consecutive_occurrences": 3
                },
                "actions": [
                    {"type": "config_adjustment", "target": "resource_allocation", "method": "increase"},
                    {"type": "load_balancing", "method": "redistribute"},
                    {"type": "caching_optimization", "method": "adaptive"}
                ]
            },
            {
                "strategy_id": "learning_acceleration",
                "name": "学习加速",
                "description": "检测学习机会并加速学习过程",
                "type": "optimization",
                "conditions": {
                    "learning_opportunity_detected": True,
                    "success_rate_below": 0.7
                },
                "actions": [
                    {"type": "algorithm_switch", "target": "learning_method", "method": "adaptive_selection"},
                    {"type": "data_augmentation", "method": "intelligent"},
                    {"type": "feedback_loop", "method": "reinforce"}
                ]
            },
            {
                "strategy_id": "capability_innovation",
                "name": "能力创新",
                "description": "探索和开发新的系统能力",
                "type": "innovation",
                "conditions": {
                    "stagnation_detected": True,
                    "resource_available": True,
                    "risk_assessment": "low"
                },
                "actions": [
                    {"type": "capability_exploration", "method": "systematic"},
                    {"type": "prototype_development", "method": "rapid"},
                    {"type": "capability_integration", "method": "gradual"}
                ]
            }
        ]

        for strategy_data in strategies:
            strategy = EvolutionaryStrategy(**strategy_data)
            self.evolutionary_strategies[strategy.strategy_id] = strategy

    def _initialize_adaptation_rules(self):
        """初始化自适应规则"""
        self.self_optimization_rules = {
            "resource_allocation": {
                "trigger": "high_load_detected",
                "action": "redistribute_resources",
                "threshold": 0.8,
                "cooldown": 300  # 5分钟冷却
            },
            "learning_rate_adjustment": {
                "trigger": "performance_plateau",
                "action": "adjust_learning_parameters",
                "threshold": 0.05,
                "cooldown": 600  # 10分钟冷却
            },
            "capability_activation": {
                "trigger": "task_complexity_increase",
                "action": "activate_advanced_capabilities",
                "threshold": 0.2,
                "cooldown": 1800  # 30分钟冷却
            }
        }

    def set_multi_agent_coordinator(self, coordinator: MultiAgentCoordinator):
        """设置多Agent协调器引用"""
        self.multi_agent_coordinator = coordinator
        self.module_logger.info("✅ 多Agent协调器已设置")

    async def generate_autonomous_goal(self, goal_type: str, context: Dict[str, Any]) -> Optional[str]:
        """生成自主目标"""
        if goal_type not in self.goal_templates:
            self.module_logger.warning(f"⚠️ 未知目标类型: {goal_type}")
            return None

        template = self.goal_templates[goal_type]

        goal_id = f"goal_{uuid.uuid4().hex[:8]}"

        # 基于上下文调整优先级和截止时间
        priority = template["priority"]
        deadline = None

        if context.get("urgent", False):
            priority = min(10, priority + 2)
            deadline = datetime.now() + timedelta(hours=context.get("time_limit_hours", 24))

        goal = AutonomousGoal(
            goal_id=goal_id,
            description=template["description"],
            priority=priority,
            deadline=deadline,
            subtasks=template["subtasks"].copy(),
            metadata=context
        )

        # 设置子任务依赖
        self._setup_goal_dependencies(goal)

        self.active_goals[goal_id] = goal

        self.module_logger.info(f"🎯 自主目标已生成: {goal_id} - {goal.description} (优先级: {priority})")
        return goal_id

    def _setup_goal_dependencies(self, goal: AutonomousGoal):
        """设置目标依赖关系"""
        # 简单的顺序依赖：每个子任务依赖前一个
        for i, subtask in enumerate(goal.subtasks):
            if i > 0:
                prev_subtask_id = goal.subtasks[i-1]["id"] = f"{goal.goal_id}_subtask_{i-1}"
                current_subtask_id = subtask["id"] = f"{goal.goal_id}_subtask_{i}"
                goal.dependencies[current_subtask_id] = {prev_subtask_id}
            else:
                subtask["id"] = f"{goal.goal_id}_subtask_{i}"

    async def _goal_management_loop(self):
        """目标管理循环"""
        while self._running:
            try:
                await self._review_active_goals()
                await self._prioritize_goals()
                await self._execute_goal_actions()

            except Exception as e:
                self.module_logger.error(f"❌ 目标管理循环异常: {e}", exc_info=True)

            await asyncio.sleep(self.goal_review_interval)

    async def _review_active_goals(self):
        """审查活跃目标"""
        current_time = datetime.now()

        for goal_id, goal in list(self.active_goals.items()):
            # 检查截止时间
            if goal.deadline and current_time > goal.deadline:
                self.module_logger.warning(f"⚠️ 目标超时: {goal_id}")
                goal.status = "failed"
                self._complete_goal(goal)
                continue

            # 检查进度
            completed_subtasks = sum(1 for st in goal.subtasks if st.get("completed", False))
            goal.progress = completed_subtasks / len(goal.subtasks) if goal.subtasks else 0

            # 检查是否完成
            if goal.progress >= 1.0:
                goal.status = "completed"
                goal.completed_at = current_time
                self._complete_goal(goal)

    async def _prioritize_goals(self):
        """目标优先级排序"""
        # 基于优先级、截止时间和进度重新排序
        def goal_priority_key(goal: AutonomousGoal) -> Tuple[int, float, float]:
            # 优先级权重
            priority_weight = goal.priority

            # 截止时间权重（越接近截止时间优先级越高）
            deadline_weight = 0
            if goal.deadline:
                time_remaining = (goal.deadline - datetime.now()).total_seconds()
                if time_remaining > 0:
                    deadline_weight = max(0, (86400 - time_remaining) / 86400)  # 24小时内线性增加
                else:
                    deadline_weight = 10  # 已过期，最高优先级

            # 进度权重（进度慢的优先级稍高）
            progress_weight = (1.0 - goal.progress) * 2

            return (-priority_weight, -deadline_weight, -progress_weight)  # 负数因为heapq是最小堆

        # 重新排序活跃目标（这里简化为按优先级排序的字典）
        sorted_goals = sorted(self.active_goals.values(), key=goal_priority_key)
        self.active_goals = {goal.goal_id: goal for goal in sorted_goals}

    async def _execute_goal_actions(self):
        """执行目标动作"""
        # 选择最高优先级的目标执行
        if not self.active_goals:
            return

        highest_priority_goal = next(iter(self.active_goals.values()))

        # 查找下一个要执行的子任务
        for subtask in highest_priority_goal.subtasks:
            if not subtask.get("completed", False):
                # 检查依赖
                dependencies = highest_priority_goal.dependencies.get(subtask["id"], set())
                if dependencies:
                    # 检查依赖是否完成
                    dependent_completed = all(
                        any(st.get("completed", False) for st in highest_priority_goal.subtasks if st["id"] == dep_id)
                        for dep_id in dependencies
                    )
                    if not dependent_completed:
                        continue

                # 执行子任务
                await self._execute_goal_subtask(highest_priority_goal, subtask)
                break  # 一次只执行一个子任务

    async def _execute_goal_subtask(self, goal: AutonomousGoal, subtask: Dict[str, Any]):
        """执行目标子任务"""
        self.module_logger.info(f"▶️ 执行目标子任务: {subtask['id']} - {subtask['description']}")

        try:
            # 使用多Agent协调器执行复杂的子任务
            if self.multi_agent_coordinator:
                context = {
                    "description": subtask["description"],
                    "goal_context": goal.metadata,
                    "subtask_type": subtask["type"],
                    "timeout": 1800  # 30分钟超时
                }

                result = await self.multi_agent_coordinator.execute(context)

                if result.success:
                    subtask["completed"] = True
                    subtask["result"] = result.data
                    subtask["completed_at"] = datetime.now()
                    self.module_logger.info(f"✅ 子任务完成: {subtask['id']}")
                else:
                    self.module_logger.warning(f"⚠️ 子任务失败: {subtask['id']} - {result.error}")
            else:
                # 简单的自执行
                await asyncio.sleep(random.uniform(1, 5))  # 模拟执行时间
                subtask["completed"] = True
                subtask["result"] = {"status": "simulated_completion"}
                subtask["completed_at"] = datetime.now()

        except Exception as e:
            self.module_logger.error(f"❌ 子任务执行异常: {subtask['id']} - {e}")
            subtask["error"] = str(e)

    def _complete_goal(self, goal: AutonomousGoal):
        """完成目标"""
        if goal.status == "completed":
            self.total_goals_achieved += 1

        # 从活跃目标中移除
        if goal.goal_id in self.active_goals:
            del self.active_goals[goal.goal_id]

        # 添加到完成目标列表
        self.completed_goals.append(goal)

        self.module_logger.info(f"🏁 目标完成: {goal.goal_id} - {goal.description} ({goal.status})")

    async def _learning_loop(self):
        """学习循环"""
        while self._running:
            try:
                await self._collect_performance_data()
                await self._analyze_patterns()
                await self._generate_learning_insights()
                await self._apply_learning_insights()

            except Exception as e:
                self.module_logger.error(f"❌ 学习循环异常: {e}", exc_info=True)

            await asyncio.sleep(self.learning_interval)

    async def _collect_performance_data(self):
        """收集性能数据"""
        current_time = datetime.now()

        # 收集系统性能指标
        performance_data = {
            "timestamp": current_time,
            "goals_active": len(self.active_goals),
            "goals_completed": self.total_goals_achieved,
            "learning_insights": len(self.learning_insights),
            "system_efficiency": self.system_efficiency_score,
            "autonomous_decisions": self.autonomous_decisions_made
        }

        # 收集Agent协作统计（如果有协调器）
        if self.multi_agent_coordinator:
            collab_stats = self.multi_agent_coordinator.get_collaboration_stats()
            performance_data.update({
                "collaboration_stats": collab_stats,
                "tasks_processed": collab_stats.get("total_tasks_processed", 0),
                "success_rate": collab_stats.get("success_rate", 0)
            })

        self.performance_history.append(performance_data)

    async def _analyze_patterns(self):
        """分析模式"""
        if len(self.performance_history) < 10:
            return

        recent_data = list(self.performance_history)[-50:]  # 最近50个数据点

        # 分析性能趋势
        efficiency_values = [d.get("system_efficiency", 1.0) for d in recent_data]
        if len(efficiency_values) >= 10:
            recent_avg = sum(efficiency_values[-10:]) / 10
            older_avg = sum(efficiency_values[-20:-10]) / 10 if len(efficiency_values) >= 20 else recent_avg

            if recent_avg < older_avg * 0.95:  # 效率下降5%
                self.pattern_recognition["efficiency_decline"] = {
                    "detected_at": datetime.now(),
                    "severity": "medium",
                    "trend": f"{older_avg:.3f} → {recent_avg:.3f}",
                    "recommendation": "检查系统负载和资源分配"
                }

        # 分析目标完成模式
        goal_completion_rates = []
        for i in range(1, len(recent_data)):
            prev = recent_data[i-1]
            curr = recent_data[i]
            rate = curr.get("goals_completed", 0) - prev.get("goals_completed", 0)
            goal_completion_rates.append(rate)

        if goal_completion_rates:
            avg_completion_rate = sum(goal_completion_rates) / len(goal_completion_rates)
            if avg_completion_rate < 0.5:  # 平均每天完成不到0.5个目标
                self.pattern_recognition["low_goal_completion"] = {
                    "detected_at": datetime.now(),
                    "severity": "high",
                    "rate": avg_completion_rate,
                    "recommendation": "优化目标分配和执行策略"
                }

    async def _generate_learning_insights(self):
        """生成学习洞察"""
        current_time = datetime.now()

        # 基于模式识别生成洞察
        for pattern_name, pattern_data in self.pattern_recognition.items():
            if pattern_name == "efficiency_decline":
                insight = LearningInsight(
                    insight_id=f"insight_{uuid.uuid4().hex[:8]}",
                    type="performance",
                    description=f"检测到系统效率下降趋势: {pattern_data['trend']}",
                    confidence=0.85,
                    impact="high",
                    actionable=True,
                    metadata={
                        "pattern": pattern_name,
                        "recommendation": pattern_data["recommendation"],
                        "severity": pattern_data["severity"]
                    }
                )
                self.learning_insights.append(insight)
                self.learning_insights_discovered += 1

            elif pattern_name == "low_goal_completion":
                insight = LearningInsight(
                    insight_id=f"insight_{uuid.uuid4().hex[:8]}",
                    type="pattern",
                    description=f"目标完成率偏低: {pattern_data['rate']:.2f} 个/周期",
                    confidence=0.75,
                    impact="medium",
                    actionable=True,
                    metadata={
                        "pattern": pattern_name,
                        "recommendation": pattern_data["recommendation"],
                        "current_rate": pattern_data["rate"]
                    }
                )
                self.learning_insights.append(insight)
                self.learning_insights_discovered += 1

        # 清理旧的模式识别结果（保留1小时）
        expired_patterns = []
        for pattern_name, pattern_data in self.pattern_recognition.items():
            if (current_time - pattern_data["detected_at"]).total_seconds() > 3600:
                expired_patterns.append(pattern_name)

        for pattern_name in expired_patterns:
            del self.pattern_recognition[pattern_name]

    async def _apply_learning_insights(self):
        """应用学习洞察"""
        unapplied_insights = [insight for insight in self.learning_insights if not insight.applied and insight.actionable]

        for insight in unapplied_insights:
            try:
                if insight.type == "performance" and "efficiency_decline" in insight.metadata.get("pattern", ""):
                    # 应用性能优化措施
                    await self._apply_performance_optimization(insight)
                    insight.applied = True
                    insight.applied_at = datetime.now()

                elif insight.type == "pattern" and "low_goal_completion" in insight.metadata.get("pattern", ""):
                    # 应用目标优化措施
                    await self._apply_goal_optimization(insight)
                    insight.applied = True
                    insight.applied_at = datetime.now()

            except Exception as e:
                self.module_logger.error(f"❌ 应用学习洞察失败: {insight.insight_id} - {e}")

    async def _apply_performance_optimization(self, insight: LearningInsight):
        """应用性能优化"""
        self.module_logger.info(f"🔧 应用性能优化洞察: {insight.description}")

        # 增加自主决策计数
        self.autonomous_decisions_made += 1

        # 简单的性能优化措施
        if "efficiency" in insight.description.lower():
            # 调整学习间隔（减少学习频率以提高效率）
            old_interval = self.learning_interval
            self.learning_interval = min(old_interval * 1.2, 7200)  # 最多增加到2小时
            self.module_logger.info(f"⚡ 性能优化: 学习间隔从 {old_interval} 调整为 {self.learning_interval}")

    async def _apply_goal_optimization(self, insight: LearningInsight):
        """应用目标优化"""
        self.module_logger.info(f"🎯 应用目标优化洞察: {insight.description}")

        self.autonomous_decisions_made += 1

        # 调整目标优先级策略
        # 这里可以实现更复杂的目标优化逻辑
        self.module_logger.info("⚡ 目标优化: 调整目标分配策略")

    async def _evolution_loop(self):
        """进化循环"""
        while self._running:
            try:
                await self._evaluate_evolutionary_conditions()
                await self._apply_evolutionary_strategies()
                await self._track_evolution_progress()

            except Exception as e:
                self.module_logger.error(f"❌ 进化循环异常: {e}", exc_info=True)

            await asyncio.sleep(self.evolution_check_interval)

    async def _evaluate_evolutionary_conditions(self):
        """评估进化条件"""
        current_time = datetime.now()

        for strategy_id, strategy in self.evolutionary_strategies.items():
            conditions_met = True

            # 检查所有触发条件
            for condition_key, condition_value in strategy.conditions.items():
                if not self._check_evolutionary_condition(condition_key, condition_value):
                    conditions_met = False
                    break

            if conditions_met:
                # 标记策略为可应用
                strategy.last_applied = current_time
                self.module_logger.info(f"🔄 进化条件满足: {strategy.name}")

    def _check_evolutionary_condition(self, condition_key: str, condition_value: Any) -> bool:
        """检查进化条件"""
        if condition_key == "performance_degradation":
            # 检查性能下降
            if len(self.performance_history) < 5:
                return False

            recent_efficiency = [d.get("system_efficiency", 1.0) for d in list(self.performance_history)[-5:]]
            avg_recent = sum(recent_efficiency) / len(recent_efficiency)

            # 检查是否连续下降
            degradation_count = 0
            for i in range(1, len(recent_efficiency)):
                if recent_efficiency[i] < recent_efficiency[i-1]:
                    degradation_count += 1

            return degradation_count >= 3 and (1.0 - avg_recent) >= condition_value

        elif condition_key == "learning_opportunity_detected":
            # 检查学习机会（简化为定期触发）
            return len(self.learning_insights) > 5

        elif condition_key == "stagnation_detected":
            # 检查停滞（目标完成率低且无新洞察）
            recent_goals = sum(d.get("goals_completed", 0) for d in list(self.performance_history)[-10:])
            return recent_goals < 2  # 最近10个周期完成少于2个目标

        return False

    async def _apply_evolutionary_strategies(self):
        """应用进化策略"""
        current_time = datetime.now()

        for strategy_id, strategy in self.evolutionary_strategies.items():
            if strategy.last_applied and (current_time - strategy.last_applied).total_seconds() < 3600:
                # 冷却期内不重复应用
                continue

            if self._check_evolutionary_condition_list(strategy.conditions):
                await self._execute_evolutionary_strategy(strategy)
                self.evolutionary_actions_taken += 1

    def _check_evolutionary_condition_list(self, conditions: Dict[str, Any]) -> bool:
        """检查条件列表"""
        return all(self._check_evolutionary_condition(k, v) for k, v in conditions.items())

    async def _execute_evolutionary_strategy(self, strategy: EvolutionaryStrategy):
        """执行进化策略"""
        self.module_logger.info(f"🔬 执行进化策略: {strategy.name}")

        success_count = 0

        for action in strategy.actions:
            try:
                action_type = action["type"]

                if action_type == "config_adjustment":
                    # 配置调整
                    await self._execute_config_adjustment(action)
                elif action_type == "algorithm_switch":
                    # 算法切换
                    await self._execute_algorithm_switch(action)
                elif action_type == "capability_exploration":
                    # 能力探索
                    await self._execute_capability_exploration(action)

                success_count += 1

            except Exception as e:
                self.module_logger.error(f"❌ 进化动作执行失败: {action_type} - {e}")

        # 更新成功率
        total_actions = len(strategy.actions)
        strategy.success_rate = success_count / total_actions if total_actions > 0 else 0

        self.module_logger.info(f"✅ 进化策略执行完成: {strategy.name} (成功率: {strategy.success_rate:.1%})")

    async def _execute_config_adjustment(self, action: Dict[str, Any]):
        """执行配置调整"""
        target = action.get("target")
        method = action.get("method")

        if target == "resource_allocation" and method == "increase":
            # 增加资源分配
            self.module_logger.info("⚙️ 配置调整: 增加资源分配")

        # 这里可以实现具体的配置调整逻辑

    async def _execute_algorithm_switch(self, action: Dict[str, Any]):
        """执行算法切换"""
        target = action.get("target")
        method = action.get("method")

        if target == "learning_method" and method == "adaptive_selection":
            # 自适应学习方法选择
            self.module_logger.info("🧠 算法切换: 启用自适应学习方法选择")

    async def _execute_capability_exploration(self, action: Dict[str, Any]):
        """执行能力探索"""
        method = action.get("method")

        if method == "systematic":
            # 系统性的能力探索
            self.module_logger.info("🔍 能力探索: 系统性探索新能力")

    async def _track_evolution_progress(self):
        """跟踪进化进度"""
        evolution_data = {
            "timestamp": datetime.now(),
            "evolutionary_actions_taken": self.evolutionary_actions_taken,
            "active_strategies": len([s for s in self.evolutionary_strategies.values() if s.last_applied]),
            "system_efficiency": self.system_efficiency_score,
            "learning_insights_applied": len([i for i in self.learning_insights if i.applied])
        }

        self.evolution_history.append(evolution_data)

    async def _adaptation_loop(self):
        """自适应循环"""
        while self._running:
            try:
                await self._monitor_environment_changes()
                await self._apply_adaptation_rules()
                await self._update_system_efficiency()

            except Exception as e:
                self.module_logger.error(f"❌ 自适应循环异常: {e}", exc_info=True)

            await asyncio.sleep(600)  # 每10分钟自适应一次

    async def _monitor_environment_changes(self):
        """监控环境变化"""
        # 检测负载变化
        if len(self.performance_history) >= 5:
            recent_load = [d.get("goals_active", 0) for d in list(self.performance_history)[-5:]]
            avg_load = sum(recent_load) / len(recent_load)

            self.environment_adaptation["current_load"] = avg_load
            self.environment_adaptation["high_load_detected"] = avg_load > 5  # 阈值

        # 检测性能变化
        if len(self.performance_history) >= 10:
            recent_efficiency = [d.get("system_efficiency", 1.0) for d in list(self.performance_history)[-10:]]
            current_avg = sum(recent_efficiency[-3:]) / 3
            previous_avg = sum(recent_efficiency[-6:-3]) / 3

            self.environment_adaptation["performance_trend"] = current_avg - previous_avg
            self.environment_adaptation["performance_plateau"] = abs(current_avg - previous_avg) < 0.05

    async def _apply_adaptation_rules(self):
        """应用自适应规则"""
        for rule_name, rule in self.self_optimization_rules.items():
            trigger = rule["trigger"]
            threshold = rule["threshold"]
            cooldown = rule["cooldown"]
            action = rule["action"]

            # 检查冷却期
            last_applied = rule.get("last_applied")
            if last_applied and (datetime.now() - last_applied).total_seconds() < cooldown:
                continue

            # 检查触发条件
            if self._check_adaptation_trigger(trigger, threshold):
                await self._execute_adaptation_action(action, rule)
                rule["last_applied"] = datetime.now()
                self.autonomous_decisions_made += 1

    def _check_adaptation_trigger(self, trigger: str, threshold: float) -> bool:
        """检查自适应触发条件"""
        if trigger == "high_load_detected":
            return self.environment_adaptation.get("high_load_detected", False)

        elif trigger == "performance_plateau":
            return self.environment_adaptation.get("performance_plateau", False)

        elif trigger == "task_complexity_increase":
            # 简化为检查活跃目标数量
            return len(self.active_goals) > threshold

        return False

    async def _execute_adaptation_action(self, action: str, rule: Dict[str, Any]):
        """执行自适应动作"""
        self.module_logger.info(f"🔄 执行自适应动作: {action}")

        if action == "redistribute_resources":
            # 重新分配资源
            self.module_logger.info("⚖️ 自适应: 重新分配系统资源")

        elif action == "adjust_learning_parameters":
            # 调整学习参数
            self.module_logger.info("🧠 自适应: 调整学习参数")

        elif action == "activate_advanced_capabilities":
            # 激活高级能力
            self.module_logger.info("🚀 自适应: 激活高级能力")

    async def _update_system_efficiency(self):
        """更新系统效率评分"""
        # 基于多个因素计算效率评分
        efficiency_factors = {
            "goal_completion_rate": min(1.0, self.total_goals_achieved / max(1, self.total_goals_achieved + len(self.active_goals))),
            "learning_effectiveness": min(1.0, len([i for i in self.learning_insights if i.applied]) / max(1, len(self.learning_insights))),
            "adaptation_rate": min(1.0, self.autonomous_decisions_made / max(1, self.total_goals_achieved)),
            "evolution_progress": min(1.0, self.evolutionary_actions_taken / max(1, len(self.evolutionary_strategies)))
        }

        # 加权平均
        weights = {"goal_completion_rate": 0.4, "learning_effectiveness": 0.3, "adaptation_rate": 0.2, "evolution_progress": 0.1}

        self.system_efficiency_score = sum(factor * weights[name] for name, factor in efficiency_factors.items())

    def _get_service(self):
        """AutonomousRunner不直接使用单一Service"""
        return None

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行自主运行任务"""
        task_type = context.get("task_type", "goal_generation")

        try:
            if task_type == "goal_generation":
                goal_type = context.get("goal_type", "performance_optimization")
                goal_id = await self.generate_autonomous_goal(goal_type, context)

                if goal_id:
                    return AgentResult(
                        success=True,
                        data={"goal_id": goal_id, "message": f"自主目标已生成: {goal_id}"},
                        confidence=0.9
                    )
                else:
                    return AgentResult(success=False, error="无法生成自主目标")

            elif task_type == "status_report":
                status = self.get_autonomous_status()
                return AgentResult(success=True, data=status, confidence=1.0)

            elif task_type == "evolution_trigger":
                await self._trigger_manual_evolution()
                return AgentResult(success=True, data={"message": "手动进化已触发"}, confidence=0.8)

            else:
                return AgentResult(success=False, error=f"未知任务类型: {task_type}")

        except Exception as e:
            self.module_logger.error(f"❌ 自主运行执行异常: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    async def _trigger_manual_evolution(self):
        """触发手动进化"""
        self.module_logger.info("🔬 手动触发系统进化")

        # 强制评估进化条件
        await self._evaluate_evolutionary_conditions()

        # 应用所有可用的进化策略
        applied_strategies = 0
        for strategy in self.evolutionary_strategies.values():
            if self._check_evolutionary_condition_list(strategy.conditions):
                await self._execute_evolutionary_strategy(strategy)
                applied_strategies += 1

        self.module_logger.info(f"✅ 手动进化完成: 应用了 {applied_strategies} 个进化策略")

    def get_autonomous_status(self) -> Dict[str, Any]:
        """获取自主运行状态"""
        return {
            "active_goals": len(self.active_goals),
            "completed_goals": len(self.completed_goals),
            "learning_insights": len(self.learning_insights),
            "applied_insights": len([i for i in self.learning_insights if i.applied]),
            "evolutionary_actions": self.evolutionary_actions_taken,
            "autonomous_decisions": self.autonomous_decisions_made,
            "system_efficiency": self.system_efficiency_score,
            "total_goals_achieved": self.total_goals_achieved,
            "pattern_recognition_active": len(self.pattern_recognition) > 0,
            "evolution_strategies_count": len(self.evolutionary_strategies)
        }

    async def start(self):
        """启动自主运行Agent"""
        if self._running:
            return

        self._running = True
        self._goal_management_task = asyncio.create_task(self._goal_management_loop())
        self._learning_task = asyncio.create_task(self._learning_loop())
        self._evolution_task = asyncio.create_task(self._evolution_loop())
        self._adaptation_task = asyncio.create_task(self._adaptation_loop())

        self.module_logger.info("✅ 自主运行Agent已启动")

    async def stop(self):
        """停止自主运行Agent"""
        self._running = False

        for task in [self._goal_management_task, self._learning_task, self._evolution_task, self._adaptation_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.module_logger.info("🛑 自主运行Agent已停止")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "active_goals": len(self.active_goals),
            "learning_insights": len(self.learning_insights),
            "evolution_history": len(self.evolution_history),
            "running": self._running
        }
