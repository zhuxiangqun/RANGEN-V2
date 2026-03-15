"""
战略决策层：StrategicChiefAgent

专注于"决定做什么"的纯战略决策组件。
负责任务分解、执行策略规划、依赖关系分析和优先级分配。
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.core.layered_architecture_types import (
    StrategicPlan, TaskDefinition, ExecutionStrategy, TaskType,
    QueryAnalysis, SystemState
)

logger = logging.getLogger(__name__)


class StrategicChiefAgent:
    """
    战略决策层：专注于决定做什么

    职责：
    - 基于查询分析进行任务分解
    - 规划执行策略（并行/串行/混合）
    - 分析任务依赖关系
    - 分配任务优先级和资源需求
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._task_templates = self._load_task_templates()

    async def decide_strategy(
        self,
        query_analysis: QueryAnalysis,
        system_state: Optional[SystemState] = None
    ) -> StrategicPlan:
        """
        纯战略决策：任务分解和执行规划

        Args:
            query_analysis: 查询分析结果
            system_state: 系统状态（可选）

        Returns:
            StrategicPlan: 完整的战略决策结果
        """
        self.logger.info("🎯 [StrategicChiefAgent] 开始战略决策分析")

        try:
            # 1. 任务分解
            tasks = await self._decompose_tasks(query_analysis)
            self.logger.info(f"📋 [StrategicChiefAgent] 任务分解完成，共{len(tasks)}个任务")

            # 2. 执行策略规划
            execution_strategy = await self._plan_execution_strategy(
                tasks, query_analysis, system_state
            )
            self.logger.info(f"🎯 [StrategicChiefAgent] 执行策略规划完成：{execution_strategy.value}")

            # 3. 依赖关系分析
            task_dependencies = self._analyze_dependencies(tasks, query_analysis)
            self.logger.info(f"🔗 [StrategicChiefAgent] 依赖关系分析完成")

            # 4. 优先级分配
            priority_weights = self._assign_priorities(tasks, query_analysis, system_state)
            self.logger.info(f"⭐ [StrategicChiefAgent] 优先级分配完成")

            # 5. 资源需求评估
            resource_requirements = self._assess_resource_requirements(tasks, query_analysis)
            self.logger.info(f"💎 [StrategicChiefAgent] 资源需求评估完成")

            # 6. 质量和时间约束
            quality_requirements = self._define_quality_requirements(query_analysis)
            timeline_constraints = self._define_timeline_constraints(tasks, query_analysis)

            strategic_plan = StrategicPlan(
                tasks=tasks,
                execution_strategy=execution_strategy,
                task_dependencies=task_dependencies,
                priority_weights=priority_weights,
                resource_requirements=resource_requirements,
                quality_requirements=quality_requirements,
                timeline_constraints=timeline_constraints
            )

            self.logger.info("✅ [StrategicChiefAgent] 战略决策完成")
            return strategic_plan

        except Exception as e:
            self.logger.error(f"❌ [StrategicChiefAgent] 战略决策失败: {e}", exc_info=True)
            # 返回一个基本的fallback计划
            return self._create_fallback_plan(query_analysis)

    async def _decompose_tasks(self, query_analysis: QueryAnalysis) -> List[TaskDefinition]:
        """任务分解：将查询分解为具体的可执行任务"""

        tasks = []
        task_counter = 0

        # 基于查询类型和复杂度进行任务分解
        query_type = query_analysis.query_type
        complexity_score = query_analysis.complexity_score

        # 基础任务：知识检索（几乎所有查询都需要）
        knowledge_task = TaskDefinition(
            task_id=f"knowledge_retrieval_{task_counter}",
            task_type=TaskType.KNOWLEDGE_RETRIEVAL,
            description="检索相关知识和证据",
            priority=0.9,
            estimated_complexity=min(complexity_score, 3.0),
            metadata={"query": query_analysis.query}
        )
        tasks.append(knowledge_task)
        task_counter += 1

        # 根据查询类型添加特定任务
        if query_type in ["reasoning", "analysis"]:
            # 需要推理的任务
            reasoning_task = TaskDefinition(
                task_id=f"reasoning_{task_counter}",
                task_type=TaskType.REASONING,
                description="基于证据进行推理分析",
                dependencies=["knowledge_retrieval_0"],
                priority=0.8,
                estimated_complexity=complexity_score,
                metadata={"reasoning_requirements": query_analysis.reasoning_requirements}
            )
            tasks.append(reasoning_task)
            task_counter += 1

        elif query_type == "factual":
            # 事实型查询，简化推理
            analysis_task = TaskDefinition(
                task_id=f"analysis_{task_counter}",
                task_type=TaskType.ANALYSIS,
                description="分析检索到的信息",
                dependencies=["knowledge_retrieval_0"],
                priority=0.7,
                estimated_complexity=complexity_score * 0.7
            )
            tasks.append(analysis_task)
            task_counter += 1

        # 答案生成任务（所有查询都需要）
        answer_task = TaskDefinition(
            task_id=f"answer_generation_{task_counter}",
            task_type=TaskType.ANSWER_GENERATION,
            description="生成最终答案",
            dependencies=[t.task_id for t in tasks[:-1]],  # 依赖前面的所有任务
            priority=1.0,
            estimated_complexity=complexity_score * 0.5
        )
        tasks.append(answer_task)
        task_counter += 1

        # 引用生成任务
        citation_task = TaskDefinition(
            task_id=f"citation_{task_counter}",
            task_type=TaskType.CITATION,
            description="生成答案引用和来源",
            dependencies=["answer_generation_" + str(task_counter - 1)],
            priority=0.6,
            estimated_complexity=1.0
        )
        tasks.append(citation_task)

        self.logger.debug(f"任务分解结果: {[f'{t.task_type.value}({t.task_id})' for t in tasks]}")
        return tasks

    async def _plan_execution_strategy(
        self,
        tasks: List[TaskDefinition],
        query_analysis: QueryAnalysis,
        system_state: Optional[SystemState] = None
    ) -> ExecutionStrategy:
        """执行策略规划：决定并行/串行/混合执行"""

        complexity_score = query_analysis.complexity_score
        task_count = len(tasks)

        # 高复杂度查询倾向于并行执行
        if complexity_score > 4.0:
            # 检查系统状态，如果负载不高，可以并行
            if system_state and system_state.current_load.get('cpu', 0) < 70:
                return ExecutionStrategy.PARALLEL
            else:
                return ExecutionStrategy.MIXED

        # 中等复杂度，混合执行
        elif complexity_score > 2.0:
            return ExecutionStrategy.MIXED

        # 简单查询，串行执行（减少资源消耗）
        else:
            return ExecutionStrategy.SERIAL

    def _analyze_dependencies(
        self,
        tasks: List[TaskDefinition],
        query_analysis: QueryAnalysis
    ) -> Dict[str, List[str]]:
        """分析任务依赖关系"""

        dependencies = {}

        # 基于任务类型建立依赖关系
        task_dict = {task.task_id: task for task in tasks}

        for task in tasks:
            deps = []

            # 推理任务依赖知识检索
            if task.task_type == TaskType.REASONING:
                knowledge_tasks = [t.task_id for t in tasks
                                 if t.task_type == TaskType.KNOWLEDGE_RETRIEVAL]
                deps.extend(knowledge_tasks)

            # 分析任务依赖知识检索
            elif task.task_type == TaskType.ANALYSIS:
                knowledge_tasks = [t.task_id for t in tasks
                                 if t.task_type == TaskType.KNOWLEDGE_RETRIEVAL]
                deps.extend(knowledge_tasks)

            # 答案生成依赖大部分任务
            elif task.task_type == TaskType.ANSWER_GENERATION:
                # 依赖除citation外的所有任务
                other_tasks = [t.task_id for t in tasks
                             if t.task_type != TaskType.CITATION and t.task_id != task.task_id]
                deps.extend(other_tasks)

            # 引用生成依赖答案生成
            elif task.task_type == TaskType.CITATION:
                answer_tasks = [t.task_id for t in tasks
                              if t.task_type == TaskType.ANSWER_GENERATION]
                deps.extend(answer_tasks)

            dependencies[task.task_id] = deps

        return dependencies

    def _assign_priorities(
        self,
        tasks: List[TaskDefinition],
        query_analysis: QueryAnalysis,
        system_state: Optional[SystemState] = None
    ) -> Dict[str, float]:
        """分配任务优先级"""

        priorities = {}

        # 基于任务类型设置基础优先级
        type_priorities = {
            TaskType.ANSWER_GENERATION: 1.0,  # 答案生成最高优先级
            TaskType.KNOWLEDGE_RETRIEVAL: 0.9,  # 知识检索很重要
            TaskType.REASONING: 0.8,  # 推理中等优先级
            TaskType.ANALYSIS: 0.7,   # 分析较低优先级
            TaskType.CITATION: 0.6,   # 引用生成最低优先级
            TaskType.MEMORY: 0.5      # 记忆任务最低
        }

        for task in tasks:
            base_priority = type_priorities.get(task.task_type, 0.5)

            # 根据复杂度调整优先级
            complexity_factor = min(task.estimated_complexity / 5.0, 1.0)

            # 根据依赖关系调整（被依赖的任务优先级更高）
            dependency_boost = len(task.dependencies) * 0.1

            final_priority = min(base_priority + complexity_factor * 0.2 + dependency_boost, 1.0)
            priorities[task.task_id] = final_priority

        return priorities

    def _assess_resource_requirements(
        self,
        tasks: List[TaskDefinition],
        query_analysis: QueryAnalysis
    ) -> Dict[str, Any]:
        """评估资源需求"""

        total_complexity = sum(task.estimated_complexity for task in tasks)
        max_complexity = max(task.estimated_complexity for task in tasks)

        return {
            "estimated_complexity": total_complexity,
            "max_task_complexity": max_complexity,
            "task_count": len(tasks),
            "resource_hints": {
                "cpu_intensive": any(t.task_type == TaskType.REASONING for t in tasks),
                "memory_intensive": total_complexity > 10,
                "io_intensive": any(t.task_type == TaskType.KNOWLEDGE_RETRIEVAL for t in tasks)
            }
        }

    def _define_quality_requirements(self, query_analysis: QueryAnalysis) -> Dict[str, Any]:
        """定义质量要求"""

        complexity_score = query_analysis.complexity_score

        if complexity_score > 4.0:
            return {
                "min_quality_score": 0.9,
                "require_evidence_validation": True,
                "require_reasoning_transparency": True,
                "require_citation_accuracy": True
            }
        elif complexity_score > 2.0:
            return {
                "min_quality_score": 0.8,
                "require_evidence_validation": True,
                "require_reasoning_transparency": False,
                "require_citation_accuracy": True
            }
        else:
            return {
                "min_quality_score": 0.7,
                "require_evidence_validation": False,
                "require_reasoning_transparency": False,
                "require_citation_accuracy": True
            }

    def _define_timeline_constraints(
        self,
        tasks: List[TaskDefinition],
        query_analysis: QueryAnalysis
    ) -> Dict[str, Any]:
        """定义时间约束"""

        total_complexity = sum(task.estimated_complexity for task in tasks)

        # 估算总执行时间（复杂度分数 * 基础时间因子）
        estimated_total_time = total_complexity * 10  # 假设复杂度1需要10秒

        return {
            "estimated_total_time": estimated_total_time,
            "max_execution_time": estimated_total_time * 2,  # 允许2倍时间
            "critical_path_time": estimated_total_time * 0.7,  # 关键路径时间
            "time_sensitivity": "medium" if total_complexity < 5 else "high"
        }

    def _load_task_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载任务模板"""
        # 这里可以从配置文件或数据库加载任务模板
        return {
            "knowledge_retrieval": {
                "estimated_time": 15,
                "resource_requirements": {"cpu": 0.3, "memory": 0.4}
            },
            "reasoning": {
                "estimated_time": 30,
                "resource_requirements": {"cpu": 0.8, "memory": 0.6}
            },
            "answer_generation": {
                "estimated_time": 10,
                "resource_requirements": {"cpu": 0.5, "memory": 0.3}
            },
            "citation": {
                "estimated_time": 5,
                "resource_requirements": {"cpu": 0.2, "memory": 0.2}
            }
        }

    def _create_fallback_plan(self, query_analysis: QueryAnalysis) -> StrategicPlan:
        """创建fallback战略计划（当决策失败时使用）"""

        self.logger.warning("⚠️ [StrategicChiefAgent] 使用fallback战略计划")

        # 创建最基本的任务序列
        tasks = [
            TaskDefinition(
                task_id="knowledge_retrieval_fallback",
                task_type=TaskType.KNOWLEDGE_RETRIEVAL,
                description="基础知识检索",
                priority=0.9
            ),
            TaskDefinition(
                task_id="answer_generation_fallback",
                task_type=TaskType.ANSWER_GENERATION,
                description="基础答案生成",
                dependencies=["knowledge_retrieval_fallback"],
                priority=1.0
            )
        ]

        return StrategicPlan(
            tasks=tasks,
            execution_strategy=ExecutionStrategy.SERIAL,
            task_dependencies={"answer_generation_fallback": ["knowledge_retrieval_fallback"]},
            priority_weights={
                "knowledge_retrieval_fallback": 0.9,
                "answer_generation_fallback": 1.0
            }
        )
