"""
战术优化层：TacticalOptimizer

专注于"怎么做最好"的纯战术优化组件。
基于战略决策进行执行参数优化，包括ML预测超时时间、RL优化并行策略等。
"""

import logging
from typing import Dict, List, Any, Optional
import time

from src.core.layered_architecture_types import (
    StrategicPlan, ExecutionParams, TaskDefinition, TaskType,
    QueryAnalysis, SystemState
)

logger = logging.getLogger(__name__)


class TacticalOptimizer:
    """
    战术优化层：专注于怎么做最好

    职责：
    - 基于战略决策优化执行参数
    - ML预测最优超时时间和资源配置
    - RL优化并行执行策略
    - 动态调整重试和批处理策略
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 初始化优化器（延迟加载）
        self._ml_optimizer = None
        self._rl_optimizer = None

        # 默认配置
        self._default_configs = {
            'timeouts': {
                TaskType.KNOWLEDGE_RETRIEVAL: 30.0,
                TaskType.REASONING: 120.0,
                TaskType.ANSWER_GENERATION: 60.0,
                TaskType.CITATION: 15.0,
                TaskType.ANALYSIS: 45.0,
                TaskType.MEMORY: 10.0
            },
            'parallelism': {
                TaskType.KNOWLEDGE_RETRIEVAL: True,   # 知识检索可以并行
                TaskType.REASONING: False,            # 推理通常串行
                TaskType.ANSWER_GENERATION: False,    # 答案生成串行
                TaskType.CITATION: True,              # 引用可以并行
                TaskType.ANALYSIS: False,             # 分析串行
                TaskType.MEMORY: True                 # 记忆操作可以并行
            },
            'resource_allocation': {
                TaskType.KNOWLEDGE_RETRIEVAL: 2,      # 中等资源
                TaskType.REASONING: 4,                # 高资源
                TaskType.ANSWER_GENERATION: 3,        # 中高资源
                TaskType.CITATION: 1,                 # 低资源
                TaskType.ANALYSIS: 2,                 # 中等资源
                TaskType.MEMORY: 1                    # 低资源
            },
            'retry_strategy': {
                TaskType.KNOWLEDGE_RETRIEVAL: 2,      # 允许2次重试
                TaskType.REASONING: 1,                # 允许1次重试
                TaskType.ANSWER_GENERATION: 1,        # 允许1次重试
                TaskType.CITATION: 3,                 # 允许3次重试
                TaskType.ANALYSIS: 1,                 # 允许1次重试
                TaskType.MEMORY: 2                    # 允许2次重试
            }
        }

    async def optimize_execution(
        self,
        strategic_plan: StrategicPlan,
        query_features: Dict[str, Any],
        system_state: Optional[SystemState] = None
    ) -> ExecutionParams:
        """
        基于战略决策进行战术优化

        Args:
            strategic_plan: 战略决策结果
            query_features: 查询特征信息
            system_state: 系统状态（可选）

        Returns:
            ExecutionParams: 优化的执行参数
        """
        self.logger.info("🎯 [TacticalOptimizer] 开始战术优化")

        start_time = time.time()

        try:
            # 1. 初始化优化器
            await self._ensure_optimizers_loaded()

            # 2. 超时时间优化
            timeouts = await self._optimize_timeouts(strategic_plan, query_features, system_state)
            self.logger.info(f"⏱️ [TacticalOptimizer] 超时优化完成: {len(timeouts)}个任务")

            # 3. 并行策略优化
            parallelism = await self._optimize_parallelism(strategic_plan, query_features, system_state)
            self.logger.info(f"🔄 [TacticalOptimizer] 并行优化完成: {sum(parallelism.values())}个并行任务")

            # 4. 资源分配优化
            resource_allocation = self._optimize_resource_allocation(strategic_plan, system_state)
            self.logger.info(f"💎 [TacticalOptimizer] 资源分配完成: 总资源{sum(resource_allocation.values())}")

            # 5. 重试策略优化
            retry_strategy = self._optimize_retry_strategy(strategic_plan, query_features)
            self.logger.info(f"🔄 [TacticalOptimizer] 重试策略完成")

            # 6. 批处理和并发限制优化
            batch_sizes, concurrency_limits = self._optimize_batch_and_concurrency(strategic_plan)

            execution_params = ExecutionParams(
                timeouts=timeouts,
                parallelism=parallelism,
                resource_allocation=resource_allocation,
                retry_strategy=retry_strategy,
                batch_sizes=batch_sizes,
                concurrency_limits=concurrency_limits
            )

            execution_time = time.time() - start_time
            self.logger.info(f"✅ [TacticalOptimizer] 战术优化完成，耗时{execution_time:.2f}s")

            return execution_params

        except Exception as e:
            self.logger.error(f"❌ [TacticalOptimizer] 战术优化失败: {e}", exc_info=True)
            # 返回默认参数
            return self._create_default_params(strategic_plan)

    async def _ensure_optimizers_loaded(self):
        """确保ML和RL优化器已加载"""
        try:
            # 尝试加载ML优化器
            if self._ml_optimizer is None:
                try:
                    from src.utils.ml_scheduling_optimizer import MLSchedulingOptimizer
                    self._ml_optimizer = MLSchedulingOptimizer()
                    self.logger.info("✅ [TacticalOptimizer] ML优化器加载成功")
                except ImportError:
                    self.logger.warning("⚠️ [TacticalOptimizer] ML优化器不可用，使用规则优化")
                    self._ml_optimizer = None

            # 尝试加载RL优化器
            if self._rl_optimizer is None:
                try:
                    from src.utils.rl_scheduling_optimizer import RLSchedulingOptimizer
                    self._rl_optimizer = RLSchedulingOptimizer()
                    self.logger.info("✅ [TacticalOptimizer] RL优化器加载成功")
                except ImportError:
                    self.logger.warning("⚠️ [TacticalOptimizer] RL优化器不可用，使用规则优化")
                    self._rl_optimizer = None

        except Exception as e:
            self.logger.warning(f"⚠️ [TacticalOptimizer] 优化器加载失败: {e}")

    async def _optimize_timeouts(
        self,
        strategic_plan: StrategicPlan,
        query_features: Dict[str, Any],
        system_state: Optional[SystemState] = None
    ) -> Dict[str, float]:
        """优化超时时间"""

        timeouts = {}

        for task in strategic_plan.tasks:
            task_id = task.task_id
            task_type = task.task_type

            # 基础超时时间
            base_timeout = self._default_configs['timeouts'].get(task_type, 30.0)

            # 复杂度调整因子
            complexity_factor = min(task.estimated_complexity / 3.0, 3.0)  # 最高3倍

            # 系统负载调整
            load_factor = 1.0
            if system_state and system_state.current_load.get('cpu', 0) > 80:
                load_factor = 1.5  # 高负载时增加超时时间

            # ML预测调整
            ml_adjustment = 1.0
            if self._ml_optimizer:
                try:
                    ml_prediction = await self._ml_optimizer.predict_timeout(
                        task_type=task_type.value,
                        complexity=task.estimated_complexity,
                        query_features=query_features
                    )
                    if ml_prediction and ml_prediction > 0:
                        ml_adjustment = ml_prediction / base_timeout
                        ml_adjustment = max(0.5, min(ml_adjustment, 3.0))  # 限制在0.5-3倍
                except Exception as e:
                    self.logger.debug(f"ML超时预测失败: {e}")

            # 计算最终超时时间
            final_timeout = base_timeout * complexity_factor * load_factor * ml_adjustment
            timeouts[task_id] = min(final_timeout, 600.0)  # 最大10分钟

        return timeouts

    async def _optimize_parallelism(
        self,
        strategic_plan: StrategicPlan,
        query_features: Dict[str, Any],
        system_state: Optional[SystemState] = None
    ) -> Dict[str, bool]:
        """优化并行执行策略"""

        parallelism = {}

        # 检查系统资源是否支持并行
        system_supports_parallel = True
        if system_state:
            cpu_load = system_state.current_load.get('cpu', 0)
            memory_load = system_state.current_load.get('memory', 0)
            if cpu_load > 80 or memory_load > 85:
                system_supports_parallel = False
                self.logger.info("⚠️ [TacticalOptimizer] 系统负载高，限制并行执行")

        for task in strategic_plan.tasks:
            task_id = task.task_id
            task_type = task.task_type

            # 基础并行策略
            base_parallel = self._default_configs['parallelism'].get(task_type, False)

            # 依赖关系检查：有依赖的任务不能并行
            has_dependencies = len(task.dependencies) > 0
            if has_dependencies:
                can_parallel = False
            else:
                can_parallel = base_parallel and system_supports_parallel

            # RL决策调整
            if self._rl_optimizer and can_parallel:
                try:
                    rl_decision = await self._rl_optimizer.decide_parallelism(
                        task_type=task_type.value,
                        complexity=task.estimated_complexity,
                        dependency_count=len(task.dependencies),
                        system_load=system_state.current_load if system_state else {}
                    )
                    can_parallel = rl_decision.get('parallel', can_parallel)
                except Exception as e:
                    self.logger.debug(f"RL并行决策失败: {e}")

            parallelism[task_id] = can_parallel

        return parallelism

    def _optimize_resource_allocation(
        self,
        strategic_plan: StrategicPlan,
        system_state: Optional[SystemState] = None
    ) -> Dict[str, int]:
        """优化资源分配"""

        allocation = {}

        # 计算总可用资源
        available_resources = 8  # 默认8个CPU核心
        if system_state and system_state.available_resources.get('cpu'):
            available_resources = system_state.available_resources['cpu']

        # 计算资源需求
        total_demand = 0
        task_demands = {}

        for task in strategic_plan.tasks:
            task_type = task.task_type
            base_allocation = self._default_configs['resource_allocation'].get(task_type, 1)

            # 复杂度调整
            complexity_adjustment = min(task.estimated_complexity / 2.0, 2.0)
            demand = int(base_allocation * complexity_adjustment)

            task_demands[task.task_id] = demand
            total_demand += demand

        # 如果总需求超过可用资源，按比例分配
        if total_demand > available_resources:
            scale_factor = available_resources / total_demand
            for task_id, demand in task_demands.items():
                allocation[task_id] = max(1, int(demand * scale_factor))
        else:
            allocation = task_demands

        return allocation

    def _optimize_retry_strategy(
        self,
        strategic_plan: StrategicPlan,
        query_features: Dict[str, Any]
    ) -> Dict[str, int]:
        """优化重试策略"""

        retry_strategy = {}

        for task in strategic_plan.tasks:
            task_type = task.task_type
            base_retry = self._default_configs['retry_strategy'].get(task_type, 1)

            # 根据任务重要性和复杂度调整重试次数
            importance_factor = strategic_plan.priority_weights.get(task.task_id, 0.5)
            complexity_factor = min(task.estimated_complexity / 3.0, 2.0)

            # 重要且复杂的任务允许更多重试
            adjusted_retry = int(base_retry * (importance_factor + complexity_factor) / 2)
            retry_strategy[task.task_id] = min(adjusted_retry, 5)  # 最多5次重试

        return retry_strategy

    def _optimize_batch_and_concurrency(self, strategic_plan: StrategicPlan) -> tuple:
        """优化批处理大小和并发限制"""

        batch_sizes = {}
        concurrency_limits = {}

        # 分析任务类型分布
        task_types = [task.task_type for task in strategic_plan.tasks]
        type_counts = {}
        for task_type in task_types:
            type_counts[task_type] = type_counts.get(task_type, 0) + 1

        for task in strategic_plan.tasks:
            task_id = task.task_id
            task_type = task.task_type

            # 批处理大小（主要用于IO密集型任务）
            if task_type == TaskType.KNOWLEDGE_RETRIEVAL:
                batch_sizes[task_id] = min(type_counts.get(task_type, 1) * 2, 10)
            elif task_type == TaskType.CITATION:
                batch_sizes[task_id] = min(type_counts.get(task_type, 1) * 3, 15)
            else:
                batch_sizes[task_id] = 1

            # 并发限制
            if task_type == TaskType.REASONING:
                concurrency_limits[task_id] = 1  # 推理任务串行
            elif task_type == TaskType.ANSWER_GENERATION:
                concurrency_limits[task_id] = 1  # 答案生成串行
            else:
                concurrency_limits[task_id] = min(type_counts.get(task_type, 1), 5)

        return batch_sizes, concurrency_limits

    def _create_default_params(self, strategic_plan: StrategicPlan) -> ExecutionParams:
        """创建默认执行参数（优化失败时的fallback）"""

        self.logger.warning("⚠️ [TacticalOptimizer] 使用默认执行参数")

        timeouts = {}
        parallelism = {}
        resource_allocation = {}
        retry_strategy = {}

        for task in strategic_plan.tasks:
            task_id = task.task_id
            task_type = task.task_type

            timeouts[task_id] = self._default_configs['timeouts'].get(task_type, 30.0)
            parallelism[task_id] = self._default_configs['parallelism'].get(task_type, False)
            resource_allocation[task_id] = self._default_configs['resource_allocation'].get(task_type, 1)
            retry_strategy[task_id] = self._default_configs['retry_strategy'].get(task_type, 1)

        return ExecutionParams(
            timeouts=timeouts,
            parallelism=parallelism,
            resource_allocation=resource_allocation,
            retry_strategy=retry_strategy,
            batch_sizes={task.task_id: 1 for task in strategic_plan.tasks},
            concurrency_limits={task.task_id: 1 for task in strategic_plan.tasks}
        )
