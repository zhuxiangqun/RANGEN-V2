#!/usr/bin/env python3
"""
Self-Evolving Agent 自进化智能体

整合所有自进化组件的完整智能体实现

核心组件:
- Reflection (反思机制) - 自我批评与改进
- Ralph Loop (持续迭代) - 外部状态感知迭代
- MultiTrajectory Explorer (多轨迹探索) - 多策略路径探索
- Feedback Collector (反馈收集) - 自动反馈收集
- Stop Hook (停止钩子) - 完成条件验证

三定律:
- Endure (生存) - 安全优先，StopHook确保安全退出
- Excel (卓越) - 持续优化，SOP质量分析
- Evolve (进化) - 策略演进，多轨迹探索与反思
"""

import asyncio
import json
import uuid
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

from src.core.reflection import ReflexionAgent, ReflectionResult
from src.core.ralph_loop import RalphLoop, LoopConfig
from src.core.stop_hook import CompletionCriterion, CriterionType
from src.core.multi_trajectory import (
    MultiTrajectoryExplorer, AdaptiveExplorer, ExplorerConfig,
    TrajectoryResult
)
from src.core.feedback_loop_mechanism import (
    FeedbackCollector, FeedbackData, FeedbackType, FeedbackPriority
)

logger = logging.getLogger(__name__)


class EvolutionStage(str, Enum):
    """进化阶段"""
    INITIALIZING = "initializing"       # 初始化
    EXPLORING = "exploring"             # 探索中
    REFLECTING = "reflecting"           # 反思中
    LEARNING = "learning"               # 学习中
    EVOLVING = "evolving"               # 进化中
    STABLE = "stable"                   # 稳定
    DEGRADED = "degraded"               # 退化
    RECOVERING = "recovering"           # 恢复中


class EvolutionStrategy(str, Enum):
    """进化策略"""
    CONSERVATIVE = "conservative"       # 保守 - 小步迭代
    AGGRESSIVE = "aggressive"          # 激进 - 大胆尝试
    ADAPTIVE = "adaptive"               # 自适应 - 根据情况调整
    EXPLORATION_FOCUS = "exploration"  # 探索优先
    EXPLOITATION_FOCUS = "exploitation" # 利用优先


@dataclass
class AgentState:
    """智能体状态"""
    stage: EvolutionStage = EvolutionStage.INITIALIZING
    iteration: int = 0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_confidence: float = 0.0
    current_strategy: EvolutionStrategy = EvolutionStrategy.ADAPTIVE
    last_reflection: Optional[ReflectionResult] = None
    last_trajectory_result: Optional[TrajectoryResult] = None
    active_capabilities: List[str] = field(default_factory=list)
    learned_patterns: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    evolution_history: List[Dict[str, Any]] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "iteration": self.iteration,
            "total_tasks": self.total_tasks,
            "successful_tasks": self.successful_tasks,
            "failed_tasks": self.failed_tasks,
            "success_rate": self.successful_tasks / max(self.total_tasks, 1),
            "avg_confidence": self.avg_confidence,
            "current_strategy": self.current_strategy.value,
            "active_capabilities": self.active_capabilities,
            "learned_patterns": self.learned_patterns,
            "performance_metrics": self.performance_metrics,
            "last_update": self.last_update.isoformat()
        }


@dataclass
class EvolutionConfig:
    """进化配置"""
    # 反思配置
    enable_reflection: bool = True
    reflection_threshold: float = 0.6  # 低于此分数触发反思
    
    # Ralph Loop配置
    enable_ralph_loop: bool = True
    max_iterations: int = 50
    iteration_timeout: int = 300
    
    # 多轨迹探索配置
    enable_multi_trajectory: bool = True
    max_trajectories: int = 5
    enable_cross_pollination: bool = True
    
    # 反馈收集配置
    enable_feedback: bool = True
    feedback_interval: float = 60.0
    
    # 进化配置
    evolution_strategy: EvolutionStrategy = EvolutionStrategy.ADAPTIVE
    min_success_rate: float = 0.7      # 最低成功率
    max_consecutive_failures: int = 3   # 最大连续失败次数
    
    # 安全配置
    safety_mode: bool = True           # 安全模式
    stop_on_safety_violation: bool = True
    
    # 学习配置
    enable_pattern_learning: bool = True
    pattern_storage_path: Optional[str] = None


@dataclass
class EvolutionResult:
    """进化结果"""
    success: bool
    output: Any
    state: AgentState
    reflections: List[ReflectionResult]
    trajectories: Optional[TrajectoryResult]
    feedback_collected: List[FeedbackData]
    evolution_applied: Dict[str, Any]
    execution_time: float
    error: Optional[str] = None


class SelfEvolvingAgent:
    """自进化智能体
    
    整合所有自进化组件的完整实现
    """
    
    def __init__(
        self,
        config: Optional[EvolutionConfig] = None,
        llm_provider=None
    ):
        self.config = config or EvolutionConfig()
        self.llm_provider = llm_provider
        
        # 初始化状态
        self.state = AgentState()
        
        # 初始化组件
        self._init_reflection()
        self._init_ralph_loop()
        self._init_multi_trajectory()
        self._init_feedback()
        
        # 外部执行器
        self._executor: Optional[Callable] = None
        
        # 统计
        self.consecutive_failures = 0
        self.pattern_library: Dict[str, Any] = {}
        
        # 加载已学习的模式
        if self.config.enable_pattern_learning:
            self._load_patterns()
            
        logger.info("SelfEvolvingAgent initialized with all components")
    
    def _init_reflection(self) -> None:
        """初始化反思组件"""
        if not self.config.enable_reflection:
            self.reflection_agent = None
            return
            
        if self.llm_provider:
            self.reflection_agent = ReflexionAgent(self.llm_provider)
        else:
            self.reflection_agent = ReflexionAgent()
            
        logger.info("Reflection component initialized")
    
    def _init_ralph_loop(self) -> None:
        """初始化Ralph Loop"""
        if not self.config.enable_ralph_loop:
            self.ralph_loop = None
            return
            
        loop_config = LoopConfig(
            max_iterations=self.config.max_iterations,
            iteration_timeout=self.config.iteration_timeout,
            collect_external_state=True
        )
        self.ralph_loop = RalphLoop(loop_config)
        
        # 设置停止钩子
        self._setup_stop_hook()
        
        logger.info("Ralph Loop component initialized")
    
    def _setup_stop_hook(self) -> None:
        """设置停止钩子"""
        if not hasattr(self, 'ralph_loop') or not self.ralph_loop:
            return
            
        # 添加完成条件
        criteria = [
            CompletionCriterion(
                name="task_completed",
                criterion_type=CriterionType.OUTPUT_BASED,
                check_function=lambda ctx: ctx.get("task_completed", False),
                description="任务已完成"
            ),
            CompletionCriterion(
                name="max_iterations",
                criterion_type=CriterionType.COUNT_BASED,
                threshold=self.config.max_iterations,
                description="达到最大迭代次数"
            ),
            CompletionCriterion(
                name="success_rate",
                criterion_type=CriterionType.METRIC_BASED,
                threshold=self.config.min_success_rate,
                metric_name="success_rate",
                description="成功率达标"
            ),
        ]
        
        for criterion in criteria:
            self.ralph_loop.stop_hook.add_criterion(criterion)
            
        # 安全模式
        if self.config.safety_mode:
            self.ralph_loop.stop_hook.enable_safety_mode()
            
        logger.info("Stop hook configured")
    
    def _init_multi_trajectory(self) -> None:
        """初始化多轨迹探索"""
        if not self.config.enable_multi_trajectory:
            self.explorer = None
            return
            
        explorer_config = ExplorerConfig(
            max_trajectories=self.config.max_trajectories,
            enable_cross_pollination=self.config.enable_cross_pollination
        )
        
        if self.llm_provider:
            self.explorer = AdaptiveExplorer(explorer_config, self.llm_provider)
        else:
            self.explorer = MultiTrajectoryExplorer(explorer_config)
            
        logger.info("Multi-Trajectory Explorer initialized")
    
    def _init_feedback(self) -> None:
        """初始化反馈收集"""
        if not self.config.enable_feedback:
            self.feedback_collector = None
            return
            
        self.feedback_collector = FeedbackCollector()
        
        # 注册默认收集器
        self.feedback_collector.register_collector(
            "performance",
            self._collect_performance_feedback,
            interval=self.config.feedback_interval
        )
        
        self.feedback_collector.register_collector(
            "quality",
            self._collect_quality_feedback,
            interval=self.config.feedback_interval * 2
        )
        
        logger.info("Feedback collector initialized")
    
    def set_executor(self, executor: Callable) -> None:
        """设置任务执行器
        
        executor(task, context) -> (success, result, error)
        """
        self._executor = executor
        
        # 同时设置给多轨迹探索器
        if self.explorer:
            self.explorer.set_executor(
                lambda action, trajectory, ctx: executor(action, ctx)
            )
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_ralph_loop: bool = True,
        use_multi_trajectory: bool = True
    ) -> EvolutionResult:
        """执行任务并自动进化
        
        Args:
            task: 任务描述
            context: 执行上下文
            use_ralph_loop: 是否使用Ralph Loop
            use_multi_trajectory: 是否使用多轨迹探索
            
        Returns:
            EvolutionResult: 执行和进化结果
        """
        start_time = datetime.now()
        context = context or {}
        
        self.state.stage = EvolutionStage.EXPLORING
        self.state.total_tasks += 1
        
        reflections: List[ReflectionResult] = []
        feedback_collected: List[FeedbackData] = []
        trajectory_result: Optional[TrajectoryResult] = None
        evolution_applied: Dict[str, Any] = {}
        
        try:
            
            # 2. 执行任务
            output = None
            if use_multi_trajectory and self.explorer:
                # 使用多轨迹探索
                self.state.stage = EvolutionStage.EXPLORING
                trajectory_result = await self.explorer.explore(task, context)
                output = trajectory_result.best_trajectory
                context["trajectory_result"] = trajectory_result
                
            elif use_ralph_loop and self.ralph_loop:
                # 使用Ralph Loop
                self.state.stage = EvolutionStage.EXPLORING
                output = await self._execute_with_ralph_loop(task, context)
                
            else:
                # 简单执行
                output = await self._simple_execute(task, context)
                
            success = output.get("success", True) if isinstance(output, dict) else output is not None
            
            # 3. 收集反馈
            if self.feedback_collector:
                await self.feedback_collector.start_collection()
                feedback = await self._create_feedback(task, output, success, context)
                feedback_collected.append(feedback)
                
            # 4. 反思
            if self.reflection_agent and self.config.enable_reflection:
                self.state.stage = EvolutionStage.REFLECTING
                reflection = await self.reflection_agent.reflect(
                    task, output, context
                )
                reflections.append(reflection)
                self.state.last_reflection = reflection
                
                # 检查是否需要深入反思
                if reflection.confidence < self.config.reflection_threshold:
                    deep_reflection = await self.reflection_agent.reflect_deeply(
                        task, output, context
                    )
                    reflections.append(deep_reflection)
                    
            # 5. 更新状态
            if success:
                self.state.successful_tasks += 1
                self.consecutive_failures = 0
            else:
                self.state.failed_tasks += 1
                self.consecutive_failures += 1
                
            self._update_performance_metrics(success, output)
            
            # 6. 进化
            if self._should_evolve():
                self.state.stage = EvolutionStage.EVOLVING
                evolution_applied = await self._evolve(
                    reflections, trajectory_result, feedback_collected
                )
                
            # 检查是否需要恢复
            if self.consecutive_failures >= self.config.max_consecutive_failures:
                self.state.stage = EvolutionStage.RECOVERING
                await self._recover()
                
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            self.state.failed_tasks += 1
            self.consecutive_failures += 1
            
            # 记录失败反思
            if self.reflection_agent:
                reflection = await self.reflection_agent.reflect(
                    task, {"error": str(e)}, context
                )
                reflections.append(reflection)
                
            return EvolutionResult(
                success=False,
                output=None,
                state=self.state,
                reflections=reflections,
                trajectories=trajectory_result,
                feedback_collected=feedback_collected,
                evolution_applied=evolution_applied,
                execution_time=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )
            
        finally:
            # 停止反馈收集
            if self.feedback_collector:
                await self.feedback_collector.stop_collection()
                
        # 更新迭代
        self.state.iteration += 1
        self.state.last_update = datetime.now()
        
        return EvolutionResult(
            success=success,
            output=output,
            state=self.state,
            reflections=reflections,
            trajectories=trajectory_result,
            feedback_collected=feedback_collected,
            evolution_applied=evolution_applied,
            execution_time=(datetime.now() - start_time).total_seconds()
        )
    
    def _select_strategy(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> EvolutionStrategy:
        """选择执行策略"""
        # 检查模式库
        task_signature = self._get_task_signature(task)
        if task_signature in self.pattern_library:
            pattern = self.pattern_library[task_signature]
            if pattern.get("success_rate", 0) > 0.8:
                return EvolutionStrategy.EXPLOITATION_FOCUS
                
        # 根据当前状态选择
        if self.consecutive_failures > 2:
            return EvolutionStrategy.EXPLORATION_FOCUS
            
        if self.state.avg_confidence > 0.8:
            return EvolutionStrategy.CONSERVATIVE
            
        return self.config.evolution_strategy
    
    async def _execute_with_ralph_loop(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用Ralph Loop执行"""
        if not self.ralph_loop:
            return await self._simple_execute(task, context)
            
        # 设置执行函数
        async def execute_iteration(iteration: int, ctx: Dict) -> Dict:
            success, result, error = await self._execute_task(task, ctx)
            return {
                "iteration": iteration,
                "success": success,
                "result": result,
                "error": error,
                "task_completed": success and result is not None
            }
            
        self.ralph_loop.set_execute_callback(execute_iteration)
        
        # 执行
        results = await self.ralph_loop.run(task, context)
        
        # 返回最佳结果
        best_result = None
        if results:
            successful = [r for r in results if r.completion_status]
            if successful:
                best_result = successful[0].agent_output
                
        return {"result": best_result, "iterations": len(results)}
    
    async def _simple_execute(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """简单执行"""
        success, result, error = await self._execute_task(task, context)
        return {
            "success": success,
            "result": result,
            "error": error
        }
    
    async def _execute_task(
        self,
        task: str,
        context: Dict[str, Any]
    ) -> tuple[bool, Any, Optional[str]]:
        """执行单个任务"""
        if self._executor:
            try:
                return await self._executor(task, context)
            except Exception as e:
                return False, None, str(e)
                
        # 默认模拟执行
        await asyncio.sleep(0.1)
        return True, {"output": f"Completed: {task[:50]}..."}, None
    
    def _should_evolve(self) -> bool:
        """判断是否应该进化"""
        if self.state.total_tasks < 3:
            return False
            
        success_rate = self.state.successful_tasks / self.state.total_tasks
        
        # 成功率下降时进化
        if success_rate < self.config.min_success_rate:
            return True
            
        # 连续失败后进化
        if self.consecutive_failures >= 2:
            return True
            
        # 定期进化
        if self.state.iteration % 10 == 0:
            return True
            
        return False
    
    async def _evolve(
        self,
        reflections: List[ReflectionResult],
        trajectory_result: Optional[TrajectoryResult],
        feedback_collected: List[FeedbackData]
    ) -> Dict[str, Any]:
        """执行进化"""
        evolution_actions = []
        
        # 1. 从反思中学习
        if reflections:
            issues = []
            for ref in reflections:
                issues.extend(ref.issues)
                
            if issues:
                # 生成改进策略
                improvement = await self._generate_improvement(issues)
                evolution_actions.append({
                    "type": "reflection_based",
                    "improvements": improvement
                })
                
        # 2. 从轨迹中学习
        if trajectory_result and trajectory_result.best_trajectory:
            best_traj = trajectory_result.best_trajectory
            pattern = {
                "task_signature": "auto_learned",
                "actions": best_traj.get_action_sequence(),
                "success_rate": best_traj.score
            }
            self._learn_pattern("auto_learned", pattern)
            evolution_actions.append({
                "type": "trajectory_based",
                "pattern": pattern
            })
            
        # 3. 更新策略
        new_strategy = self._adjust_strategy()
        self.state.current_strategy = new_strategy
        evolution_actions.append({
            "type": "strategy_adjustment",
            "new_strategy": new_strategy.value
        })
        
        # 4. 记录进化历史
        self.state.evolution_history.append({
            "timestamp": datetime.now().isoformat(),
            "actions": evolution_actions,
            "success_rate": self.state.successful_tasks / max(self.state.total_tasks, 1)
        })
        
        self.state.stage = EvolutionStage.STABLE
        
        return {"actions": evolution_actions}
    
    async def _generate_improvement(self, issues: List[str]) -> List[str]:
        """生成改进建议"""
        improvements = []
        
        for issue in issues:
            if "timeout" in issue.lower():
                improvements.append("increase_timeout")
            elif "memory" in issue.lower():
                improvements.append("optimize_memory_usage")
            elif "accuracy" in issue.lower():
                improvements.append("enhance_validation")
            else:
                improvements.append("general_improvement")
                
        return improvements
    
    def _adjust_strategy(self) -> EvolutionStrategy:
        """调整进化策略"""
        success_rate = self.state.successful_tasks / max(self.state.total_tasks, 1)
        
        if success_rate < 0.5:
            return EvolutionStrategy.CONSERVATIVE
        elif success_rate < 0.7:
            return EvolutionStrategy.ADAPTIVE
        elif success_rate > 0.9:
            return EvolutionStrategy.AGGRESSIVE
        else:
            return EvolutionStrategy.ADAPTIVE
    
    async def _recover(self) -> None:
        """执行恢复"""
        logger.info("Starting recovery process...")
        
        # 1. 回退到已知有效的策略
        self.state.stage = EvolutionStage.RECOVERING
        
        # 2. 清除最近的失败模式
        if self.pattern_library:
            # 保留成功率达到80%以上的模式
            self.pattern_library = {
                k: v for k, v in self.pattern_library.items()
                if v.get("success_rate", 0) > 0.8
            }
            
        # 3. 重置连续失败计数
        self.consecutive_failures = 0
        
        # 4. 更新状态
        self.state.stage = EvolutionStage.STABLE
        
        logger.info("Recovery complete")
    
    async def _create_feedback(
        self,
        task: str,
        output: Any,
        success: bool,
        context: Dict[str, Any]
    ) -> FeedbackData:
        """创建反馈数据"""
        feedback_type = FeedbackType.PERFORMANCE if success else FeedbackType.ACCURACY
        priority = FeedbackPriority.LOW if success else FeedbackPriority.HIGH
        
        feedback = FeedbackData(
            feedback_id=str(uuid.uuid4()),
            feedback_type=feedback_type,
            source_component="self_evolving_agent",
            target_component="self",
            metrics={
                "success": success,
                "output_type": type(output).__name__,
                "has_output": output is not None
            },
            context={
                "task": task[:100],
                "strategy": self.state.current_strategy.value,
                "iteration": self.state.iteration
            },
            priority=priority
        )
        
        return feedback
    
    async def _collect_performance_feedback(self) -> Dict[str, Any]:
        """收集性能反馈"""
        return {
            "total_tasks": self.state.total_tasks,
            "success_rate": self.state.successful_tasks / max(self.state.total_tasks, 1),
            "avg_confidence": self.state.avg_confidence,
            "iterations": self.state.iteration
        }
    
    async def _collect_quality_feedback(self) -> Dict[str, Any]:
        """收集质量反馈"""
        return {
            "reflections": len(self.state.evolution_history),
            "patterns_learned": len(self.pattern_library),
            "current_stage": self.state.stage.value
        }
    
    def _update_performance_metrics(self, success: bool, output: Any) -> None:
        """更新性能指标"""
        # 计算平均置信度
        if self.state.last_reflection:
            confidences = [self.state.last_reflection.confidence]
            if confidences:
                self.state.avg_confidence = sum(confidences) / len(confidences)
                
        # 更新性能指标
        self.state.performance_metrics = {
            "success_rate": self.state.successful_tasks / max(self.state.total_tasks, 1),
            "avg_confidence": self.state.avg_confidence,
            "consecutive_failures": self.consecutive_failures
        }
    
    def _get_task_signature(self, task: str) -> str:
        """获取任务签名"""
        # 简化处理：使用前50个字符
        return task[:50].lower().strip()
    
    def _learn_pattern(self, signature: str, pattern: Dict[str, Any]) -> None:
        """学习模式"""
        if not self.config.enable_pattern_learning:
            return
            
        if signature not in self.pattern_library:
            self.pattern_library[signature] = pattern
        else:
            # 更新已有模式
            existing = self.pattern_library[signature]
            # 合并成功率
            old_rate = existing.get("success_rate", 0)
            new_rate = pattern.get("success_rate", 0)
            existing["success_rate"] = (old_rate + new_rate) / 2
            
        # 保存到文件
        if self.config.pattern_storage_path:
            self._save_patterns()
            
        logger.info(f"Learned pattern: {signature}")
    
    def _load_patterns(self) -> None:
        """加载模式"""
        if not self.config.pattern_storage_path:
            return
            
        path = Path(self.config.pattern_storage_path)
        if path.exists():
            try:
                with open(path, 'r') as f:
                    self.pattern_library = json.load(f)
                logger.info(f"Loaded {len(self.pattern_library)} patterns")
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")
    
    def _save_patterns(self) -> None:
        """保存模式"""
        if not self.config.pattern_storage_path:
            return
            
        path = Path(self.config.pattern_storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, 'w') as f:
                json.dump(self.pattern_library, f, indent=2)
            logger.info(f"Saved {len(self.pattern_library)} patterns")
        except Exception as e:
            logger.warning(f"Failed to save patterns: {e}")
    
    def get_state(self) -> AgentState:
        """获取当前状态"""
        return self.state
    
    def get_capabilities(self) -> List[str]:
        """获取当前能力列表"""
        capabilities = []
        
        if self.reflection_agent:
            capabilities.append("reflection")
            
        if self.ralph_loop:
            capabilities.append("ralph_loop")
            
        if self.explorer:
            capabilities.append("multi_trajectory")
            
        if self.feedback_collector:
            capabilities.append("feedback_collection")
            
        self.state.active_capabilities = capabilities
        return capabilities
    
    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """获取进化历史"""
        return self.state.evolution_history
    
    def export_state(self, filepath: str) -> None:
        """导出状态到文件"""
        state_data = {
            "agent_state": self.state.to_dict(),
            "capabilities": self.get_capabilities(),
            "patterns": self.pattern_library,
            "evolution_history": self.state.evolution_history,
            "export_time": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2, ensure_ascii=False, default=str)
            
        logger.info(f"State exported to {filepath}")


class SafeSelfEvolvingAgent(SelfEvolvingAgent):
    """安全版本的自进化智能体
    
    增加了额外的安全检查和限制
    """
    
    def __init__(self, config: Optional[EvolutionConfig] = None, llm_provider=None):
        # 强制启用安全模式
        if config:
            config.safety_mode = True
            config.stop_on_safety_violation = True
            
        super().__init__(config, llm_provider)
        
        # 添加安全相关的停止条件
        self._add_safety_criteria()
        
    def _add_safety_criteria(self) -> None:
        """添加安全标准"""
        if not self.ralph_loop:
            return
            
        # 资源使用限制
        self.ralph_loop.stop_hook.add_criterion(
            CompletionCriterion(
                name="resource_limit",
                criterion_type=CriterionType.RESOURCE_BASED,
                threshold=1000,  # 1000MB
                resource_type="memory_mb",
                description="内存使用超限"
            )
        )
        
        # 危险操作检测
        self.ralph_loop.stop_hook.add_criterion(
            CompletionCriterion(
                name="dangerous_operations",
                criterion_type=CriterionType.OUTPUT_BASED,
                check_function=lambda ctx: not ctx.get("contains_dangerous_ops", False),
                description="检测到危险操作"
            )
        )
        
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_ralph_loop: bool = True,
        use_multi_trajectory: bool = True
    ) -> EvolutionResult:
        """安全执行"""
        # 预先检查任务
        if self._is_dangerous_task(task):
            logger.warning(f"Dangerous task detected: {task[:50]}...")
            return EvolutionResult(
                success=False,
                output=None,
                state=self.state,
                reflections=[],
                trajectories=None,
                feedback_collected=[],
                evolution_applied={},
                execution_time=0,
                error="Task flagged as dangerous"
            )
            
        return await super().execute(task, context, use_ralph_loop, use_multi_trajectory)
    
    def _is_dangerous_task(self, task: str) -> bool:
        """检查任务是否危险"""
        dangerous_keywords = [
            "rm -rf", "delete all", "drop table", "format disk",
            "shutdown", "reboot", "kill -9"
        ]
        
        task_lower = task.lower()
        return any(keyword in task_lower for keyword in dangerous_keywords)
