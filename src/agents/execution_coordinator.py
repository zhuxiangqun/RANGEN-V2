"""
执行协调层：ExecutionCoordinator

专注于"怎么协调执行"的执行协调组件。
根据战略决策和战术优化参数，协调多任务的执行，管理依赖关系和并发控制。
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, deque
from dataclasses import dataclass, field

from src.core.layered_architecture_types import (
    StrategicPlan, ExecutionParams, TaskDefinition, TaskResult,
    ExecutionResult, TaskType, ExecutionStrategy
)

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """执行上下文"""
    task_id: str
    task: TaskDefinition
    params: ExecutionParams
    start_time: float = 0.0
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 1


@dataclass
class ExecutionState:
    """执行状态"""
    pending_tasks: Set[str] = field(default_factory=set)
    running_tasks: Set[str] = field(default_factory=set)
    completed_tasks: Set[str] = field(default_factory=set)
    failed_tasks: Set[str] = field(default_factory=set)
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    execution_start_time: float = 0.0


class ExecutionCoordinator:
    """
    执行协调层：专注于怎么协调执行

    职责：
    - 根据战略计划和战术参数协调任务执行
    - 管理任务依赖关系和执行顺序
    - 监控执行进度和错误处理
    - 结果聚合和质量评估
    - 支持并行和串行执行模式
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 任务执行器注册表
        self._task_executors = {}

        # 进度监控
        self._progress_callbacks = []

        # 并发控制
        self._semaphore = None

    def register_executor(self, task_type: str, executor: Any):
        """注册任务执行器"""
        self._task_executors[task_type] = executor
        self.logger.info(f"✅ [ExecutionCoordinator] 注册执行器: {task_type}")

    def add_progress_callback(self, callback: callable):
        """添加进度回调"""
        self._progress_callbacks.append(callback)

    async def coordinate_execution(
        self,
        strategic_plan: StrategicPlan,
        tactical_params: ExecutionParams
    ) -> ExecutionResult:
        """
        协调任务执行

        Args:
            strategic_plan: 战略决策结果
            tactical_params: 战术优化参数

        Returns:
            ExecutionResult: 执行协调结果
        """
        self.logger.info("🎯 [ExecutionCoordinator] 开始执行协调")

        execution_start_time = time.time()

        try:
            # 1. 初始化执行状态
            execution_state = self._initialize_execution_state(strategic_plan)

            # 2. 构建执行上下文
            execution_contexts = self._build_execution_contexts(strategic_plan, tactical_params)

            # 3. 根据执行策略选择协调方式
            if strategic_plan.execution_strategy == ExecutionStrategy.PARALLEL:
                result = await self._execute_parallel(
                    strategic_plan, tactical_params, execution_contexts, execution_state
                )
            elif strategic_plan.execution_strategy == ExecutionStrategy.SERIAL:
                result = await self._execute_serial(
                    strategic_plan, tactical_params, execution_contexts, execution_state
                )
            else:  # MIXED
                result = await self._execute_mixed(
                    strategic_plan, tactical_params, execution_contexts, execution_state
                )

            # 4. 结果聚合和质量评估
            final_result = await self._aggregate_results(result, strategic_plan, execution_start_time)

            execution_time = time.time() - execution_start_time
            self.logger.info(f"✅ [ExecutionCoordinator] 执行协调完成，耗时{execution_time:.2f}s")

            return final_result

        except Exception as e:
            self.logger.error(f"❌ [ExecutionCoordinator] 执行协调失败: {e}", exc_info=True)
            # 返回错误结果
            return ExecutionResult(
                final_answer="",
                task_results={},
                execution_metrics={
                    "total_time": time.time() - execution_start_time,
                    "error": str(e)
                },
                quality_score=0.0,
                errors=[str(e)]
            )

    def _initialize_execution_state(self, strategic_plan: StrategicPlan) -> ExecutionState:
        """初始化执行状态"""
        state = ExecutionState()
        state.pending_tasks = {task.task_id for task in strategic_plan.tasks}
        state.execution_start_time = time.time()
        return state

    def _build_execution_contexts(
        self,
        strategic_plan: StrategicPlan,
        tactical_params: ExecutionParams
    ) -> Dict[str, ExecutionContext]:
        """构建执行上下文"""
        contexts = {}

        for task in strategic_plan.tasks:
            context = ExecutionContext(
                task_id=task.task_id,
                task=task,
                params=tactical_params,
                timeout=tactical_params.timeouts.get(task.task_id, 30.0),
                max_retries=tactical_params.retry_strategy.get(task.task_id, 1)
            )
            contexts[task.task_id] = context

        return contexts

    async def _execute_parallel(
        self,
        strategic_plan: StrategicPlan,
        tactical_params: ExecutionParams,
        contexts: Dict[str, ExecutionContext],
        state: ExecutionState
    ) -> Dict[str, TaskResult]:
        """并行执行协调"""

        self.logger.info("🔄 [ExecutionCoordinator] 使用并行执行策略")

        # 初始化并发控制
        max_concurrency = self._calculate_max_concurrency(tactical_params)
        self._semaphore = asyncio.Semaphore(max_concurrency)

        # 执行任务（考虑依赖关系）
        results = await self._execute_with_dependencies_parallel(
            strategic_plan, contexts, state
        )

        return results

    async def _execute_serial(
        self,
        strategic_plan: StrategicPlan,
        tactical_params: ExecutionParams,
        contexts: Dict[str, ExecutionContext],
        state: ExecutionState
    ) -> Dict[str, TaskResult]:
        """串行执行协调"""

        self.logger.info("📋 [ExecutionCoordinator] 使用串行执行策略")

        results = {}

        # 拓扑排序确保依赖关系
        execution_order = self._topological_sort(strategic_plan.task_dependencies)

        for task_id in execution_order:
            if task_id not in contexts:
                continue

            context = contexts[task_id]
            result = await self._execute_task_with_retry(context, state)
            results[task_id] = result

            # 报告进度
            await self._report_progress(state)

        return results

    async def _execute_mixed(
        self,
        strategic_plan: StrategicPlan,
        tactical_params: ExecutionParams,
        contexts: Dict[str, ExecutionContext],
        state: ExecutionState
    ) -> Dict[str, TaskResult]:
        """混合执行协调（并行+串行结合）"""

        self.logger.info("🔀 [ExecutionCoordinator] 使用混合执行策略")

        results = {}

        # 分批执行，考虑依赖关系
        execution_batches = self._create_execution_batches(
            list(strategic_plan.task_dependencies.keys()),
            strategic_plan.task_dependencies
        )

        for batch in execution_batches:
            self.logger.debug(f"执行批次: {batch}")

            if len(batch) == 1:
                # 单任务串行执行
                task_id = batch[0]
                if task_id in contexts:
                    context = contexts[task_id]
                    result = await self._execute_task_with_retry(context, state)
                    results[task_id] = result
            else:
                # 多任务并行执行
                batch_contexts = [contexts[task_id] for task_id in batch if task_id in contexts]
                batch_results = await self._execute_batch_parallel(batch_contexts, state)
                results.update(batch_results)

            # 报告进度
            await self._report_progress(state)

        return results

    async def _execute_with_dependencies_parallel(
        self,
        strategic_plan: StrategicPlan,
        contexts: Dict[str, ExecutionContext],
        state: ExecutionState
    ) -> Dict[str, TaskResult]:
        """考虑依赖关系的并行执行"""

        results = {}
        completed = set()

        while len(completed) < len(contexts):
            # 找出可以并行执行的任务（依赖已满足）
            ready_tasks = []
            for task_id, context in contexts.items():
                if task_id in completed:
                    continue

                dependencies = strategic_plan.task_dependencies.get(task_id, [])
                if all(dep in completed for dep in dependencies):
                    ready_tasks.append(context)

            if not ready_tasks:
                # 没有就绪任务，可能存在循环依赖
                self.logger.error("⚠️ [ExecutionCoordinator] 检测到可能的循环依赖")
                break

            # 并行执行就绪任务
            batch_results = await self._execute_batch_parallel(ready_tasks, state)
            results.update(batch_results)

            # 更新完成任务集合
            for task_id, result in batch_results.items():
                if result.success:
                    completed.add(task_id)

        return results

    async def _execute_batch_parallel(
        self,
        contexts: List[ExecutionContext],
        state: ExecutionState
    ) -> Dict[str, TaskResult]:
        """并行执行一批任务"""

        async def execute_with_semaphore(context: ExecutionContext) -> TaskResult:
            async with self._semaphore:
                return await self._execute_task_with_retry(context, state)

        # 创建并行任务
        tasks = [execute_with_semaphore(context) for context in contexts]

        # 等待所有任务完成
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        results = {}
        for i, result in enumerate(batch_results):
            context = contexts[i]
            if isinstance(result, Exception):
                # 任务执行异常
                task_result = TaskResult(
                    task_id=context.task_id,
                    task_type=context.task.task_type,
                    success=False,
                    error=str(result)
                )
            else:
                task_result = result
            results[context.task_id] = task_result

        return results

    async def _execute_task_with_retry(
        self,
        context: ExecutionContext,
        state: ExecutionState
    ) -> TaskResult:
        """执行任务（支持重试）"""

        last_error = None

        for attempt in range(context.max_retries + 1):
            try:
                context.retry_count = attempt
                result = await self._execute_single_task(context)

                if result.success:
                    return result
                else:
                    last_error = result.error or "Unknown error"

            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"⚠️ [ExecutionCoordinator] 任务{context.task_id}执行失败(尝试{attempt+1}): {e}")

            # 重试前等待
            if attempt < context.max_retries:
                await asyncio.sleep(0.1 * (attempt + 1))  # 递增等待

        # 所有重试都失败
        return TaskResult(
            task_id=context.task_id,
            task_type=context.task.task_type,
            success=False,
            error=f"执行失败，经过{context.max_retries + 1}次尝试: {last_error}"
        )

    async def _execute_single_task(self, context: ExecutionContext) -> TaskResult:
        """执行单个任务"""

        task_id = context.task_id
        task = context.task

        # 获取执行器
        executor = self._task_executors.get(task.task_type.value)
        if not executor:
            raise ValueError(f"未找到任务类型{task.task_type.value}的执行器")

        context.start_time = time.time()

        try:
            # 构建任务输入
            task_input = self._build_task_input(task, context.params)

            # 执行任务（带超时控制）
            result = await asyncio.wait_for(
                executor.execute(task_input),
                timeout=context.timeout
            )

            execution_time = time.time() - context.start_time

            # 创建任务结果
            task_result = TaskResult(
                task_id=task_id,
                task_type=task.task_type,
                success=True,
                result=result,
                execution_time=execution_time,
                quality_score=getattr(result, 'quality_score', 0.8),
                metadata={
                    "execution_time": execution_time,
                    "retry_count": context.retry_count
                }
            )

            return task_result

        except asyncio.TimeoutError:
            execution_time = time.time() - context.start_time
            return TaskResult(
                task_id=task_id,
                task_type=task.task_type,
                success=False,
                error=f"执行超时({context.timeout}s)",
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - context.start_time
            return TaskResult(
                task_id=task_id,
                task_type=task.task_type,
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    def _build_task_input(self, task: TaskDefinition, params: ExecutionParams) -> Dict[str, Any]:
        """构建任务输入"""
        return {
            "task_id": task.task_id,
            "task_type": task.task_type.value,
            "description": task.description,
            "query": task.metadata.get("query", ""),
            "timeout": params.timeouts.get(task.task_id, 30.0),
            "resource_allocation": params.resource_allocation.get(task.task_id, 1),
            "batch_size": params.batch_sizes.get(task.task_id, 1),
            "concurrency_limit": params.concurrency_limits.get(task.task_id, 1),
            **task.metadata
        }

    def _topological_sort(self, dependencies: Dict[str, List[str]]) -> List[str]:
        """拓扑排序（处理依赖关系）"""

        # 构建图
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        all_tasks = set(dependencies.keys())
        for deps in dependencies.values():
            all_tasks.update(deps)

        for task in all_tasks:
            in_degree[task] = 0

        for task, deps in dependencies.items():
            graph[task] = deps
            for dep in deps:
                in_degree[dep] += 1

        # 拓扑排序
        queue = deque([task for task in all_tasks if in_degree[task] == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # 减少依赖当前任务的任务的入度
            for task in all_tasks:
                if current in graph.get(task, []):
                    in_degree[task] -= 1
                    if in_degree[task] == 0:
                        queue.append(task)

        # 检查是否存在循环依赖
        if len(result) != len(all_tasks):
            self.logger.warning("⚠️ [ExecutionCoordinator] 检测到循环依赖，使用原始顺序")
            return list(all_tasks)

        return result

    def _create_execution_batches(
        self,
        tasks: List[str],
        dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """创建执行批次（考虑依赖关系）"""

        batches = []
        remaining = set(tasks)
        processed = set()

        while remaining:
            # 找出当前批次（没有未处理依赖的任务）
            current_batch = []
            for task in remaining:
                task_deps = dependencies.get(task, [])
                if all(dep in processed for dep in task_deps):
                    current_batch.append(task)

            if not current_batch:
                # 无法找到可执行任务，可能存在问题
                self.logger.warning("⚠️ [ExecutionCoordinator] 无法创建更多批次，可能存在循环依赖")
                batches.append(list(remaining))
                break

            batches.append(current_batch)
            processed.update(current_batch)
            remaining -= set(current_batch)

        return batches

    def _calculate_max_concurrency(self, tactical_params: ExecutionParams) -> int:
        """计算最大并发数"""
        # 基于资源分配和并发限制计算
        total_resources = sum(tactical_params.resource_allocation.values())
        max_concurrency_limit = max(tactical_params.concurrency_limits.values())

        # 保守估计：不超过总资源数的2倍，且不超过最大并发限制
        return min(total_resources * 2, max_concurrency_limit, 10)  # 最大10个并发

    async def _report_progress(self, state: ExecutionState):
        """报告执行进度"""
        total_tasks = len(state.pending_tasks) + len(state.running_tasks) + len(state.completed_tasks) + len(state.failed_tasks)
        completed_count = len(state.completed_tasks)
        failed_count = len(state.failed_tasks)

        progress = {
            "total_tasks": total_tasks,
            "completed": completed_count,
            "failed": failed_count,
            "running": len(state.running_tasks),
            "pending": len(state.pending_tasks),
            "progress_percentage": (completed_count / total_tasks) * 100 if total_tasks > 0 else 0
        }

        # 调用进度回调
        for callback in self._progress_callbacks:
            try:
                await callback(progress)
            except Exception as e:
                self.logger.debug(f"进度回调失败: {e}")

    async def _aggregate_results(
        self,
        task_results: Dict[str, TaskResult],
        strategic_plan: StrategicPlan,
        execution_start_time: float
    ) -> ExecutionResult:
        """聚合执行结果"""

        # 提取最终答案（通常来自答案生成任务）
        final_answer = ""
        for task_result in task_results.values():
            if task_result.task_type == TaskType.ANSWER_GENERATION and task_result.success:
                final_answer = task_result.result or ""
                break

        # 计算执行指标
        execution_metrics = self._calculate_execution_metrics(task_results, execution_start_time)

        # 计算质量评分
        quality_score = self._calculate_quality_score(task_results, strategic_plan)

        # 收集错误信息
        errors = []
        warnings = []

        for task_result in task_results.values():
            if not task_result.success:
                errors.append(f"{task_result.task_id}: {task_result.error}")
            elif task_result.quality_score < 0.7:
                warnings.append(f"{task_result.task_id}: 质量评分低({task_result.quality_score:.2f})")

        return ExecutionResult(
            final_answer=final_answer,
            task_results=task_results,
            execution_metrics=execution_metrics,
            quality_score=quality_score,
            errors=errors,
            warnings=warnings
        )

    def _calculate_execution_metrics(
        self,
        task_results: Dict[str, TaskResult],
        execution_start_time: float
    ) -> Dict[str, Any]:
        """计算执行指标"""

        total_time = time.time() - execution_start_time
        successful_tasks = sum(1 for r in task_results.values() if r.success)
        failed_tasks = len(task_results) - successful_tasks

        task_times = [r.execution_time for r in task_results.values() if r.execution_time > 0]

        return {
            "total_execution_time": total_time,
            "successful_tasks": successful_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": successful_tasks / len(task_results) if task_results else 0,
            "average_task_time": sum(task_times) / len(task_times) if task_times else 0,
            "max_task_time": max(task_times) if task_times else 0,
            "min_task_time": min(task_times) if task_times else 0
        }

    def _calculate_quality_score(
        self,
        task_results: Dict[str, TaskResult],
        strategic_plan: StrategicPlan
    ) -> float:
        """计算整体质量评分"""

        if not task_results:
            return 0.0

        # 基于任务权重计算加权平均质量评分
        total_weight = 0
        weighted_score = 0

        for task_result in task_results.values():
            task_id = task_result.task_id
            weight = strategic_plan.priority_weights.get(task_id, 1.0)

            # 成功任务使用质量评分，失败任务为0
            score = task_result.quality_score if task_result.success else 0.0

            weighted_score += score * weight
            total_weight += weight

        return weighted_score / total_weight if total_weight > 0 else 0.0
