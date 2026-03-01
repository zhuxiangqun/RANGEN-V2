#!/usr/bin/env python3
"""
Multi-Trajectory Explorer 多轨迹探索器

让Agent能够生成和评估多条解决路径，实现跨轨迹知识共享

核心功能:
- 多策略并行探索
- 轨迹质量评估与排序
- 轨迹交叉授粉 (Cross-Pollination)
- 自适应策略选择
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict
import logging
import random

logger = logging.getLogger(__name__)


class TrajectoryStrategy(str, Enum):
    """轨迹探索策略"""
    DEPTH_FIRST = "depth_first"       # 深度优先 - 深入探索单一路径
    BREADTH_FIRST = "breadth_first"    # 广度优先 - 先探索所有分支
    MONTE_CARLO = "monte_carlo"        # 蒙特卡洛 - 随机采样
    BEST_FIRST = "best_first"         # 最佳优先 - 每次选择最优
    HYBRID = "hybrid"                  # 混合策略


class TrajectoryState(str, Enum):
    """轨迹状态"""
    PENDING = "pending"           # 待执行
    RUNNING = "running"           # 执行中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"            # 失败
    PRUNED = "pruned"            # 被剪枝
    FROZEN = "frozen"            # 冻结(等待资源)


class SolutionQuality(str, Enum):
    """解决方案质量等级"""
    EXCELLENT = "excellent"       # 优秀 - 完全满足需求
    GOOD = "good"                # 良好 - 基本满足
    ACCEPTABLE = "acceptable"    # 可接受 - 需要改进
    POOR = "poor"                # 较差 - 不满足需求
    FAILED = "failed"            # 失败 - 无法解决


@dataclass
class TrajectoryStep:
    """轨迹中的单步"""
    step_id: str
    action: str
    reasoning: str
    inputs: Dict[str, Any]
    outputs: Any
    state_after: Dict[str, Any]
    execution_time: float = 0.0
    success: bool = True
    error: Optional[str] = None


@dataclass
class Trajectory:
    """解决路径"""
    trajectory_id: str
    task: str
    strategy: TrajectoryStrategy
    steps: List[TrajectoryStep] = field(default_factory=list)
    state: TrajectoryState = TrajectoryState.PENDING
    quality: Optional[SolutionQuality] = None
    score: float = 0.0
    total_time: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_trajectory_id: Optional[str] = None  # 用于轨迹授粉
    cross_pollinated_from: List[str] = field(default_factory=list)  # 交叉授粉来源
    
    def add_step(self, step: TrajectoryStep) -> None:
        """添加步骤"""
        self.steps.append(step)
        self.total_time += step.execution_time
        
    def get_action_sequence(self) -> List[str]:
        """获取动作序列"""
        return [step.action for step in self.steps]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trajectory_id": self.trajectory_id,
            "task": self.task,
            "strategy": self.strategy.value,
            "steps": [
                {
                    "step_id": s.step_id,
                    "action": s.action,
                    "reasoning": s.reasoning,
                    "success": s.success
                }
                for s in self.steps
            ],
            "state": self.state.value,
            "quality": self.quality.value if self.quality else None,
            "score": self.score,
            "total_time": self.total_time,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "metadata": self.metadata,
            "cross_pollinated_from": self.cross_pollinated_from
        }


@dataclass
class TrajectoryResult:
    """轨迹探索结果"""
    trajectories: List[Trajectory]
    best_trajectory: Optional[Trajectory]
    cross_pollination_insights: Dict[str, Any]
    exploration_summary: Dict[str, Any]
    execution_stats: Dict[str, Any]


@dataclass
class ExplorerConfig:
    """探索器配置"""
    max_trajectories: int = 5              # 最大轨迹数
    max_steps_per_trajectory: int = 10     # 每条轨迹最大步数
    timeout_per_step: int = 60             # 单步超时(秒)
    enable_cross_pollination: bool = True  # 启用交叉授粉
    cross_pollination_threshold: float = 0.3  # 授粉阈值
    pruning_enabled: bool = True           # 启用剪枝
    quality_threshold: float = 0.5         # 质量阈值
    parallel_execution: bool = True        # 并行执行
    diversity_weight: float = 0.3           # 多样性权重


class TrajectoryQualityScorer:
    """轨迹质量评分器"""
    
    @staticmethod
    def calculate_quality(
        trajectory: Trajectory,
        expected_outcome: Any,
        context: Dict[str, Any]
    ) -> tuple[SolutionQuality, float]:
        """计算轨迹质量
        
        评估维度:
        - 成功率 (success_rate)
        - 效率 (efficiency) 
        - 鲁棒性 (robustness)
        - 创新性 (innovation)
        """
        if not trajectory.steps:
            return SolutionQuality.FAILED, 0.0
            
        # 1. 成功率评分
        successful_steps = sum(1 for s in trajectory.steps if s.success)
        success_rate = successful_steps / len(trajectory.steps)
        
        # 2. 效率评分 (用时越少越高)
        expected_time = context.get("expected_time", 100)
        efficiency = min(1.0, expected_time / max(trajectory.total_time, 0.1))
        
        # 3. 鲁棒性 (错误恢复能力)
        errors = [s for s in trajectory.steps if s.error]
        recovery_rate = 0.0
        if errors:
            # 检查错误后是否有恢复
            for i, step in enumerate(trajectory.steps):
                if step.error and i + 1 < len(trajectory.steps):
                    if trajectory.steps[i + 1].success:
                        recovery_rate += 1
            recovery_rate = recovery_rate / len(errors)
        robustness = 1.0 - (len(errors) / len(trajectory.steps)) + (recovery_rate * 0.3)
        
        # 4. 创新性 (基于动作多样性)
        unique_actions = len(set(trajectory.get_action_sequence()))
        action_diversity = unique_actions / len(trajectory.steps)
        
        # 综合评分
        weights = {"success": 0.4, "efficiency": 0.2, "robustness": 0.25, "innovation": 0.15}
        score = (
            success_rate * weights["success"] +
            efficiency * weights["efficiency"] +
            robustness * weights["robustness"] +
            action_diversity * weights["innovation"]
        )
        
        # 质量等级判定
        if score >= 0.85:
            quality = SolutionQuality.EXCELLENT
        elif score >= 0.7:
            quality = SolutionQuality.GOOD
        elif score >= 0.5:
            quality = SolutionQuality.ACCEPTABLE
        elif score > 0:
            quality = SolutionQuality.POOR
        else:
            quality = SolutionQuality.FAILED
            
        return quality, round(score, 3)


class CrossPollinator:
    """轨迹交叉授粉器
    
    核心思想: 从多条轨迹中提取成功模式，组合成新策略
    """
    
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self.insight_history: List[Dict[str, Any]] = []
        
    def find_patterns(self, trajectories: List[Trajectory]) -> Dict[str, Any]:
        """发现跨轨迹的成功模式"""
        if len(trajectories) < 2:
            return {}
            
        # 收集所有成功的动作序列
        successful_sequences = []
        for traj in trajectories:
            if traj.quality in [SolutionQuality.EXCELLENT, SolutionQuality.GOOD]:
                successful_sequences.append({
                    "actions": traj.get_action_sequence(),
                    "score": traj.score,
                    "trajectory_id": traj.trajectory_id
                })
                
        if not successful_sequences:
            return {}
            
        # 找出共同的成功动作
        action_frequency = defaultdict(int)
        for seq in successful_sequences:
            for action in seq["actions"]:
                action_frequency[action] += 1
                
        # 筛选高频成功动作
        min_freq = max(2, len(successful_sequences) * self.threshold)
        common_successful_actions = [
            action for action, freq in action_frequency.items()
            if freq >= min_freq
        ]
        
        # 找出最佳轨迹的成功模式
        best_trajectory = max(trajectories, key=lambda t: t.score)
        
        return {
            "common_successful_actions": common_successful_actions,
            "best_sequence": best_trajectory.get_action_sequence(),
            "best_trajectory_id": best_trajectory.trajectory_id,
            "action_frequency": dict(action_frequency),
            "total_successful_trajectories": len(successful_sequences)
        }
    
    def create_hybrid_strategy(
        self,
        patterns: Dict[str, Any],
        task: str
    ) -> List[str]:
        """基于模式创建混合策略"""
        if not patterns:
            return []
            
        hybrid = []
        best_sequence = patterns.get("best_sequence", [])
        common_actions = patterns.get("common_successful_actions", [])
        
        # 优先使用经过验证的动作
        for action in best_sequence[:3]:  # 取前3个
            if action in common_actions:
                hybrid.append(f"{action}_verified")
            else:
                hybrid.append(action)
                
        # 添加一些探索性动作
        if len(hybrid) < 5:
            hybrid.append("explore_alternative")
            
        return hybrid
    
    def record_insight(self, insight: Dict[str, Any]) -> None:
        """记录授粉洞察"""
        self.insight_history.append({
            **insight,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_insights_summary(self) -> List[Dict[str, Any]]:
        """获取洞察历史摘要"""
        return self.insight_history[-10:]  # 最近10条


class TrajectoryPruner:
    """轨迹剪枝器
    
    早期剪枝低质量轨迹，节省计算资源
    """
    
    def __init__(self, quality_threshold: float = 0.5):
        self.quality_threshold = quality_threshold
        self.pruning_history: List[Dict[str, Any]] = []
        
    def should_prune(
        self,
        trajectory: Trajectory,
        current_best_score: float
    ) -> tuple[bool, str]:
        """判断是否应该剪枝"""
        
        # 1. 检查失败率
        if trajectory.steps:
            failed_steps = sum(1 for s in trajectory.steps if not s.success)
            failure_rate = failed_steps / len(trajectory.steps)
            
            if failure_rate > 0.7:
                return True, f"high_failure_rate:{failure_rate:.2f}"
                
        # 2. 检查是否明显低于最佳
        if current_best_score > 0:
            score_gap = current_best_score - trajectory.score
            if score_gap > 0.4:
                return True, f"score_gap:{score_gap:.2f}"
                
        # 3. 检查是否重复无效动作
        if len(trajectory.steps) >= 3:
            recent_actions = trajectory.get_action_sequence()[-3:]
            if len(set(recent_actions)) == 1:
                return True, "repeated_actions"
                
        return False, ""
        
    def prune(
        self,
        trajectories: List[Trajectory],
        active_trajectories: Set[str]
    ) -> List[Trajectory]:
        """执行剪枝"""
        if not trajectories:
            return []
            
        # 找出当前最佳分数
        completed = [t for t in trajectories if t.state == TrajectoryState.COMPLETED]
        current_best = max((t.score for t in completed), default=0.0)
        
        pruned = []
        for traj_id in active_trajectories:
            traj = next((t for t in trajectories if t.trajectory_id == traj_id), None)
            if traj:
                should_prune, reason = self.should_prune(traj, current_best)
                if should_prune:
                    traj.state = TrajectoryState.PRUNED
                    pruned.append(traj)
                    self.pruning_history.append({
                        "trajectory_id": traj_id,
                        "reason": reason,
                        "score": traj.score,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Pruned trajectory {traj_id}: {reason}")
                    
        return pruned


class MultiTrajectoryExplorer:
    """多轨迹探索器
    
    核心功能:
    - 多种策略并行探索解决方案空间
    - 实时评估和排序轨迹
    - 跨轨迹知识共享
    - 自适应策略调整
    """
    
    def __init__(
        self,
        config: Optional[ExplorerConfig] = None,
        llm_provider=None
    ):
        self.config = config or ExplorerConfig()
        self.llm_provider = llm_provider
        
        # 核心组件
        self.scorer = TrajectoryQualityScorer()
        self.cross_pollinator = CrossPollinator(
            threshold=self.config.cross_pollination_threshold
        )
        self.pruner = TrajectoryPruner(
            quality_threshold=self.config.quality_threshold
        )
        
        # 轨迹管理
        self.trajectories: Dict[str, Trajectory] = {}
        self.active_trajectories: Set[str] = set()
        self.completed_trajectories: List[Trajectory] = []
        
        # 策略执行器
        self._executor: Optional[Callable] = None
        
        logger.info(f"MultiTrajectoryExplorer initialized with {len(TrajectoryStrategy)} strategies")
        
    def set_executor(self, executor: Callable) -> None:
        """设置策略执行器
        
        executor(task, strategy, context) -> (success, result, error)
        """
        self._executor = executor
        
    async def explore(
        self,
        task: str,
        initial_context: Dict[str, Any],
        expected_outcome: Any = None
    ) -> TrajectoryResult:
        """执行多轨迹探索
        
        Args:
            task: 任务描述
            initial_context: 初始上下文
            expected_outcome: 期望结果(用于评估)
            
        Returns:
            TrajectoryResult: 包含所有轨迹和最佳结果
        """
        start_time = datetime.now()
        
        # 1. 初始化轨迹
        self._initialize_trajectories(task, initial_context)
        
        # 2. 执行探索循环
        while self.active_trajectories:
            # 检查是否达到最大轨迹数
            if len(self.completed_trajectories) >= self.config.max_trajectories:
                logger.info("Max trajectories reached")
                break
                
            # 执行一批轨迹
            await self._execute_active_trajectories(initial_context)
            
            # 3. 交叉授粉
            if self.config.enable_cross_pollination:
                await self._cross_pollinate(initial_context)
                
            # 4. 剪枝
            if self.config.pruning_enabled:
                self._prune_trajectories()
                
        # 5. 评估所有轨迹
        self._evaluate_all_trajectories(expected_outcome, initial_context)
        
        # 6. 构建结果
        result = self._build_result(start_time)
        
        logger.info(
            f"Exploration complete: {len(self.completed_trajectories)} trajectories, "
            f"best score: {result.best_trajectory.score if result.best_trajectory else 0}"
        )
        
        return result
    
    def _initialize_trajectories(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> None:
        """初始化多条轨迹"""
        strategies = self._select_strategies()
        
        for strategy in strategies:
            traj = Trajectory(
                trajectory_id=str(uuid.uuid4())[:8],
                task=task,
                strategy=strategy,
                metadata={
                    "context_snapshot": context.copy(),
                    "initialization_time": datetime.now().isoformat()
                }
            )
            self.trajectories[traj.trajectory_id] = traj
            self.active_trajectories.add(traj.trajectory_id)
            
        logger.info(f"Initialized {len(strategies)} trajectories with strategies: {[s.value for s in strategies]}")
    
    def _select_strategies(self) -> List[TrajectoryStrategy]:
        """选择要使用的策略组合"""
        all_strategies = list(TrajectoryStrategy)
        
        # 根据配置选择策略数量
        num_strategies = min(self.config.max_trajectories, len(all_strategies))
        
        # 始终包含最佳优先和混合策略
        selected = [TrajectoryStrategy.BEST_FIRST, TrajectoryStrategy.HYBRID]
        
        # 随机选择其他策略
        remaining = [s for s in all_strategies if s not in selected]
        selected.extend(random.sample(remaining, min(num_strategies - 2, len(remaining))))
        
        return selected[:num_strategies]
    
    async def _execute_active_trajectories(
        self,
        context: Dict[str, Any]
    ) -> None:
        """执行所有活跃轨迹"""
        if not self._executor:
            logger.warning("No executor set, using mock execution")
            await self._mock_execute_all(context)
            return
            
        tasks = []
        for traj_id in list(self.active_trajectories):
            traj = self.trajectories[traj_id]
            if traj.state == TrajectoryState.PENDING:
                traj.state = TrajectoryState.RUNNING
                if self.config.parallel_execution:
                    tasks.append(self._execute_trajectory(traj, context))
                else:
                    await self._execute_trajectory(traj, context)
                    
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_trajectory(
        self,
        trajectory: Trajectory,
        context: Dict[str, Any]
    ) -> None:
        """执行单条轨迹"""
        max_steps = self.config.max_steps_per_trajectory
        step_timeout = self.config.timeout_per_step
        
        try:
            for step_num in range(max_steps):
                # 检查轨迹状态
                if trajectory.state != TrajectoryState.RUNNING:
                    break
                    
                # 生成下一步
                action, reasoning = await self._generate_next_action(
                    trajectory, context
                )
                
                if not action:
                    logger.info(f"Trajectory {trajectory.trajectory_id}: no more actions")
                    break
                    
                # 执行动作
                try:
                    success, result, error = await asyncio.wait_for(
                        asyncio.to_thread(self._executor, action, trajectory, context),
                        timeout=step_timeout
                    )
                except asyncio.TimeoutError:
                    success, result, error = False, None, "timeout"
                    
                # 记录步骤
                step = TrajectoryStep(
                    step_id=f"{trajectory.trajectory_id}_step_{step_num}",
                    action=action,
                    reasoning=reasoning,
                    inputs={"context": context.copy()},
                    outputs=result,
                    state_after=context.copy(),
                    success=success,
                    error=error
                )
                trajectory.add_step(step)
                
                # 如果失败，可以选择停止或继续
                if not success and trajectory.metadata.get("stop_on_error", False):
                    break
                    
            # 标记完成
            trajectory.state = TrajectoryState.COMPLETED
            trajectory.completed_at = datetime.now()
            self.completed_trajectories.append(trajectory)
            self.active_trajectories.discard(trajectory.trajectory_id)
            
        except Exception as e:
            logger.error(f"Trajectory {trajectory.trajectory_id} failed: {e}")
            trajectory.state = TrajectoryState.FAILED
    
    async def _generate_next_action(
        self,
        trajectory: Trajectory,
        context: Dict[str, Any]
    ) -> tuple[Optional[str], str]:
        """生成下一步动作"""
        if self.llm_provider:
            # 使用LLM生成
            prompt = self._build_action_prompt(trajectory, context)
            try:
                response = await self.llm_provider.generate(prompt)
                # 解析响应
                return self._parse_action_response(response)
            except Exception as e:
                logger.warning(f"LLM generation failed: {e}")
                
        # 回退到策略选择
        return self._strategy_based_action(trajectory, context)
    
    def _build_action_prompt(
        self,
        trajectory: Trajectory,
        context: Dict[str, Any]
    ) -> str:
        """构建动作生成提示"""
        history = "\n".join([
            f"  Step {i+1}: {s.action} - {'✓' if s.success else '✗'}"
            for i, s in enumerate(trajectory.steps[-3:])
        ])
        
        return f"""
任务: {trajectory.task}

当前策略: {trajectory.strategy.value}

最近步骤:
{history}

请生成下一步动作。输出JSON格式:
{{
    "action": "动作描述",
    "reasoning": "推理过程"
}}
"""
    
    def _parse_action_response(self, response: str) -> tuple[Optional[str], str]:
        """解析动作响应"""
        try:
            data = json.loads(response)
            return data.get("action"), data.get("reasoning", "")
        except (json.JSONDecodeError, KeyError, TypeError):
            return None, ""
    
    def _strategy_based_action(
        self,
        trajectory: Trajectory,
        context: Dict[str, Any]
    ) -> tuple[Optional[str], str]:
        """基于策略选择动作"""
        actions = ["analyze", "search", "implement", "verify", "refine"]
        
        if trajectory.strategy == TrajectoryStrategy.DEPTH_FIRST:
            # 深度优先 - 继续当前方向
            if trajectory.steps:
                return trajectory.steps[-1].action, "continue_depth_first"
                
        elif trajectory.strategy == TrajectoryStrategy.BREADTH_FIRST:
            # 广度优先 - 尝试不同动作
            used = set(trajectory.get_action_sequence())
            for action in actions:
                if action not in used:
                    return action, f"exploring_{action}"
                    
        elif trajectory.strategy == TrajectoryStrategy.MONTE_CARLO:
            # 蒙特卡洛 - 随机选择
            return random.choice(actions), "random_exploration"
            
        elif trajectory.strategy == TrajectoryStrategy.BEST_FIRST:
            # 最佳优先 - 选择最可能成功的
            return "analyze", "highest_expected_value"
            
        elif trajectory.strategy == TrajectoryStrategy.HYBRID:
            # 混合 - 结合多种策略
            if len(trajectory.steps) < 3:
                return "analyze", "initial_analysis"
            else:
                return "refine", "refine_existing"
                
        return None, ""
    
    async def _mock_execute_all(self, context: Dict[str, Any]) -> None:
        """模拟执行所有轨迹(用于测试)"""
        for traj_id in list(self.active_trajectories):
            traj = self.trajectories[traj_id]
            if traj.state == TrajectoryState.PENDING:
                traj.state = TrajectoryState.COMPLETED
                traj.completed_at = datetime.now()
                # 模拟一些步骤
                for i in range(random.randint(3, 6)):
                    step = TrajectoryStep(
                        step_id=f"{traj_id}_step_{i}",
                        action=random.choice(["analyze", "search", "implement"]),
                        reasoning="mock",
                        inputs={},
                        outputs={"mock": True},
                        state_after=context.copy(),
                        success=random.random() > 0.2
                    )
                    traj.add_step(step)
                self.completed_trajectories.append(traj)
                self.active_trajectories.discard(traj_id)
    
    async def _cross_pollinate(
        self,
        context: Dict[str, Any]
    ) -> None:
        """执行交叉授粉"""
        if len(self.completed_trajectories) < 2:
            return
            
        # 发现模式
        patterns = self.cross_pollinator.find_patterns(self.completed_trajectories)
        
        if not patterns:
            return
            
        # 创建混合策略轨迹
        if self.config.max_trajectories > len(self.trajectories):
            hybrid_actions = self.cross_pollinator.create_hybrid_strategy(
                patterns, list(self.trajectories.values())[0].task
            )
            
            if hybrid_actions:
                new_traj = Trajectory(
                    trajectory_id=str(uuid.uuid4())[:8],
                    task=list(self.trajectories.values())[0].task,
                    strategy=TrajectoryStrategy.HYBRID,
                    parent_trajectory_id=patterns.get("best_trajectory_id"),
                    cross_pollinated_from=[
                        t.trajectory_id for t in self.completed_trajectories[-3:]
                    ],
                    metadata={
                        "hybrid_actions": hybrid_actions,
                        "inspiration": patterns.get("best_sequence", [])
                    }
                )
                self.trajectories[new_traj.trajectory_id] = new_traj
                self.active_trajectories.add(new_traj.trajectory_id)
                
                # 记录洞察
                self.cross_pollinator.record_insight({
                    "type": "new_trajectory",
                    "inspired_by": patterns.get("best_trajectory_id"),
                    "actions": hybrid_actions
                })
                
                logger.info(f"Created hybrid trajectory {new_traj.trajectory_id}")
    
    def _prune_trajectories(self) -> None:
        """剪枝低质量轨迹"""
        pruned = self.pruner.prune(
            list(self.trajectories.values()),
            self.active_trajectories
        )
        
        for traj in pruned:
            self.active_trajectories.discard(traj.trajectory_id)
    
    def _evaluate_all_trajectories(
        self,
        expected_outcome: Any,
        context: Dict[str, Any]
    ) -> None:
        """评估所有轨迹"""
        for traj in self.trajectories.values():
            if traj.quality is None:
                quality, score = self.scorer.calculate_quality(
                    traj, expected_outcome, context
                )
                traj.quality = quality
                traj.score = score
                
    def _build_result(self, start_time: datetime) -> TrajectoryResult:
        """构建最终结果"""
        # 找出最佳轨迹
        best = None
        if self.completed_trajectories:
            best = max(self.completed_trajectories, key=lambda t: t.score)
            
        # 探索摘要
        strategy_stats = defaultdict(lambda: {"count": 0, "avg_score": 0, "total_score": 0})
        for traj in self.completed_trajectories:
            stats = strategy_stats[traj.strategy.value]
            stats["count"] += 1
            stats["total_score"] += traj.score
            
        for strategy, stats in strategy_stats.items():
            if stats["count"] > 0:
                stats["avg_score"] = stats["total_score"] / stats["count"]
                
        # 执行统计
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return TrajectoryResult(
            trajectories=list(self.trajectories.values()),
            best_trajectory=best,
            cross_pollination_insights=self.cross_pollinator.get_insights_summary(),
            exploration_summary={
                "total_trajectories": len(self.trajectories),
                "completed": len(self.completed_trajectories),
                "strategy_stats": dict(strategy_stats),
                "cross_pollination_count": sum(
                    len(t.cross_pollinated_from) 
                    for t in self.trajectories.values()
                )
            },
            execution_stats={
                "total_time": execution_time,
                "avg_time_per_trajectory": execution_time / max(len(self.completed_trajectories), 1),
                "timestamp": datetime.now().isoformat()
            }
        )
    
    def get_trajectory(self, trajectory_id: str) -> Optional[Trajectory]:
        """获取指定轨迹"""
        return self.trajectories.get(trajectory_id)
    
    def get_all_trajectories(self) -> List[Trajectory]:
        """获取所有轨迹"""
        return list(self.trajectories.values())
    
    def get_best_trajectories(self, n: int = 3) -> List[Trajectory]:
        """获取最佳N条轨迹"""
        sorted_trajs = sorted(
            self.completed_trajectories,
            key=lambda t: t.score,
            reverse=True
        )
        return sorted_trajs[:n]
    
    def export_results(self, filepath: str) -> None:
        """导出结果到JSON文件"""
        result = {
            "trajectories": [t.to_dict() for t in self.trajectories.values()],
            "exploration_summary": self._build_result(datetime.now()).exploration_summary,
            "export_time": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            
        logger.info(f"Results exported to {filepath}")


class AdaptiveExplorer(MultiTrajectoryExplorer):
    """自适应探索器
    
    根据任务难度和执行情况自动调整策略
    """
    
    def __init__(self, config: Optional[ExplorerConfig] = None, llm_provider=None):
        super().__init__(config, llm_provider)
        self.difficulty_estimator: Optional[Callable] = None
        self.performance_history: List[Dict[str, Any]] = []
        
    def set_difficulty_estimator(self, estimator: Callable) -> None:
        """设置难度估计器"""
        self.difficulty_estimator = estimator
        
    async def explore(
        self,
        task: str,
        initial_context: Dict[str, Any],
        expected_outcome: Any = None
    ) -> TrajectoryResult:
        """自适应探索"""
        
        # 1. 估计任务难度
        difficulty = await self._estimate_difficulty(task, initial_context)
        
        # 2. 根据难度调整配置
        self._adjust_config_for_difficulty(difficulty)
        
        # 3. 执行标准探索
        result = await super().explore(task, initial_context, expected_outcome)
        
        # 4. 记录性能
        self.performance_history.append({
            "task": task,
            "difficulty": difficulty,
            "result": result.exploration_summary,
            "timestamp": datetime.now().isoformat()
        })
        
        return result
    
    async def _estimate_difficulty(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> float:
        """估计任务难度 (0-1)"""
        if self.difficulty_estimator:
            try:
                return await self.difficulty_estimator(task, context)
            except Exception:
                pass
                
        # 默认难度估计
        task_length = len(task)
        context_complexity = len(context)
        
        # 基于长度和上下文复杂度的简单估计
        difficulty = min(1.0, (task_length / 500) * 0.4 + (context_complexity / 20) * 0.6)
        
        return difficulty
    
    def _adjust_config_for_difficulty(self, difficulty: float) -> None:
        """根据难度调整配置"""
        if difficulty > 0.7:
            # 高难度 - 增加轨迹数和探索深度
            self.config.max_trajectories = min(10, self.config.max_trajectories + 3)
            self.config.max_steps_per_trajectory = min(15, self.config.max_steps_per_trajectory + 5)
            self.config.diversity_weight = 0.5  # 更注重多样性
            logger.info(f"High difficulty detected, adjusted config: trajectories={self.config.max_trajectories}")
        elif difficulty < 0.3:
            # 低难度 - 减少探索
            self.config.max_trajectories = max(2, self.config.max_trajectories - 2)
            self.config.max_steps_per_trajectory = max(3, self.config.max_steps_per_trajectory - 3)
            self.config.diversity_weight = 0.1
            logger.info(f"Low difficulty detected, adjusted config: trajectories={self.config.max_trajectories}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_history:
            return {"total_tasks": 0}
            
        difficulties = [p["difficulty"] for p in self.performance_history]
        avg_difficulty = sum(difficulties) / len(difficulties)
        
        return {
            "total_tasks": len(self.performance_history),
            "avg_difficulty": round(avg_difficulty, 3),
            "recent_tasks": self.performance_history[-5:],
            "difficulty_distribution": {
                "easy": sum(1 for d in difficulties if d < 0.3),
                "medium": sum(1 for d in difficulties if 0.3 <= d < 0.7),
                "hard": sum(1 for d in difficulties if d >= 0.7)
            }
        }
