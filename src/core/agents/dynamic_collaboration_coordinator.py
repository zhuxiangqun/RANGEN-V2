"""
动态协作协调器

基于头条文章启示实现的智能体动态协作系统。
支持自适应任务分配、实时状态同步和冲突检测与解决。
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from datetime import datetime
from collections import defaultdict

from .capability_matrix import CapabilityAssessmentMatrix

logger = logging.getLogger(__name__)


class CollaborationMode(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


@dataclass
class CollaborationTask:
    """协作任务定义"""
    task_id: str
    task_type: str
    required_capabilities: List[str]
    priority: int
    dependencies: List[str]
    estimated_duration: float
    context: Dict[str, Any] = None


@dataclass
class AgentAssignment:
    """智能体分配结果"""
    agent_type: str
    task_id: str
    confidence_score: float
    expected_performance: float
    assigned_at: datetime = None


@dataclass
class CollaborationResult:
    """协作执行结果"""
    collaboration_id: str
    mode: CollaborationMode
    assignments: Dict[str, AgentAssignment]
    execution_time: float
    success_rate: float
    conflicts_resolved: int
    completed_at: datetime = None


class DynamicCollaborationCoordinator:
    """动态协作协调器"""

    def __init__(self):
        self.capability_matrix = CapabilityAssessmentMatrix()
        self.active_collaborations = {}
        self.collaboration_history = []
        self.agent_availability = {}  # agent_type -> available_count
        self.task_queue = asyncio.Queue()
        self.conflict_detector = ConflictDetector()

        # 初始化默认智能体可用性
        self._initialize_agent_availability()

        logger.info("✅ 动态协作协调器初始化完成")

    async def coordinate_task_execution(
        self,
        tasks: List[CollaborationTask],
        available_agents: Dict[str, int]  # agent_type -> count
    ) -> Dict[str, AgentAssignment]:
        """协调任务执行"""
        try:
            collaboration_id = self._generate_collaboration_id()
            logger.info(f"🎯 开始协调协作任务: {collaboration_id}, 任务数量: {len(tasks)}")

            # 更新智能体可用性
            self.agent_availability.update(available_agents)

            # 分析任务依赖关系
            dependency_graph = self._build_dependency_graph(tasks)
            logger.info(f"📊 依赖关系分析完成: {len(dependency_graph)} 个依赖关系")

            # 确定协作模式
            collaboration_mode = self._determine_collaboration_mode(tasks, dependency_graph)
            logger.info(f"🔄 确定协作模式: {collaboration_mode.value}")

            # 动态分配智能体
            assignments = await self._dynamic_agent_assignment(
                tasks, available_agents, collaboration_mode
            )
            logger.info(f"👥 智能体分配完成: {len(assignments)} 个任务已分配")

            # 记录协作信息
            self.active_collaborations[collaboration_id] = {
                'tasks': tasks,
                'assignments': assignments,
                'mode': collaboration_mode,
                'start_time': datetime.now()
            }

            return assignments

        except Exception as e:
            logger.error(f"❌ 任务协调失败: {e}")
            raise

    async def execute_collaboration(self, assignments: Dict[str, AgentAssignment],
                                  collaboration_mode: CollaborationMode) -> CollaborationResult:
        """执行协作"""
        try:
            collaboration_id = self._generate_collaboration_id()
            start_time = datetime.now()

            logger.info(f"🚀 开始执行协作: {collaboration_id}, 模式: {collaboration_mode.value}")

            # 根据协作模式执行
            if collaboration_mode == CollaborationMode.SEQUENTIAL:
                results = await self._execute_sequential(assignments)
            elif collaboration_mode == CollaborationMode.PARALLEL:
                results = await self._execute_parallel(assignments)
            else:  # HYBRID
                results = await self._execute_hybrid(assignments)

            # 计算执行结果
            execution_time = (datetime.now() - start_time).total_seconds()
            success_rate = self._calculate_success_rate(results)
            conflicts_resolved = self._count_conflicts_resolved(results)

            collaboration_result = CollaborationResult(
                collaboration_id=collaboration_id,
                mode=collaboration_mode,
                assignments=assignments,
                execution_time=execution_time,
                success_rate=success_rate,
                conflicts_resolved=conflicts_resolved,
                completed_at=datetime.now()
            )

            # 记录协作历史
            self._record_collaboration_history(collaboration_result)

            logger.info(f"✅ 协作执行完成: 成功率={success_rate:.2%}, 执行时间={execution_time:.2f}s")
            return collaboration_result

        except Exception as e:
            logger.error(f"❌ 协作执行失败: {e}")
            raise

    def _determine_collaboration_mode(
        self,
        tasks: List[CollaborationTask],
        dependency_graph: Dict[str, List[str]]
    ) -> CollaborationMode:
        """确定协作模式"""
        try:
            # 计算独立任务比例
            independent_tasks = self._count_independent_tasks(dependency_graph)
            total_tasks = len(tasks)

            if total_tasks == 0:
                return CollaborationMode.SEQUENTIAL

            independent_ratio = independent_tasks / total_tasks

            # 计算平均任务复杂度
            avg_complexity = sum(task.priority for task in tasks) / total_tasks

            logger.info(f"📈 任务分析: 独立任务比例={independent_ratio:.2%}, 平均复杂度={avg_complexity:.2f}")

            # 决策逻辑
            if independent_ratio > 0.7 and avg_complexity < 3:
                # 大多数任务独立且复杂度不高，适合并行
                return CollaborationMode.PARALLEL
            elif independent_ratio < 0.3 or avg_complexity > 7:
                # 大多数任务有依赖或复杂度很高，适合串行
                return CollaborationMode.SEQUENTIAL
            else:
                # 中等情况，使用混合模式
                return CollaborationMode.HYBRID

        except Exception as e:
            logger.error(f"❌ 确定协作模式失败: {e}")
            return CollaborationMode.SEQUENTIAL  # 默认串行

    async def _dynamic_agent_assignment(
        self,
        tasks: List[CollaborationTask],
        available_agents: Dict[str, int],
        mode: CollaborationMode
    ) -> Dict[str, AgentAssignment]:
        """动态智能体分配"""
        try:
            assignments = {}
            assigned_agents = defaultdict(int)  # agent_type -> assigned_count

            # 按优先级排序任务
            sorted_tasks = sorted(tasks, key=lambda t: t.priority, reverse=True)

            for task in sorted_tasks:
                # 获取任务最优智能体
                optimal_agent = self.capability_matrix.get_optimal_agent_for_task(
                    {
                        'type': task.task_type,
                        'complexity': 'high' if task.priority > 5 else 'medium',
                        'required_skills': task.required_capabilities,
                        'estimated_duration': task.estimated_duration
                    },
                    list(available_agents.keys())
                )

                # 检查智能体可用性
                if optimal_agent and available_agents.get(optimal_agent, 0) > assigned_agents[optimal_agent]:
                    # 分配最优智能体
                    assigned_agents[optimal_agent] += 1
                    assignments[task.task_id] = AgentAssignment(
                        agent_type=optimal_agent,
                        task_id=task.task_id,
                        confidence_score=0.9,
                        expected_performance=0.85,
                        assigned_at=datetime.now()
                    )
                    logger.debug(f"✅ 任务 {task.task_id} 分配给 {optimal_agent}")
                else:
                    # 寻找次优智能体
                    alternative_agent = self._find_alternative_agent(
                        task, available_agents, assigned_agents
                    )
                    if alternative_agent:
                        assigned_agents[alternative_agent] += 1
                        assignments[task.task_id] = AgentAssignment(
                            agent_type=alternative_agent,
                            task_id=task.task_id,
                            confidence_score=0.7,
                            expected_performance=0.75,
                            assigned_at=datetime.now()
                        )
                        logger.debug(f"⚠️ 任务 {task.task_id} 分配给次优智能体 {alternative_agent}")
                    else:
                        logger.warning(f"❌ 无法为任务 {task.task_id} 分配智能体")

            return assignments

        except Exception as e:
            logger.error(f"❌ 动态智能体分配失败: {e}")
            return {}

    async def _execute_sequential(self, assignments: Dict[str, AgentAssignment]) -> Dict[str, Any]:
        """串行执行"""
        results = {}

        for task_id, assignment in assignments.items():
            try:
                logger.info(f"🔄 串行执行任务: {task_id} -> {assignment.agent_type}")

                # 模拟任务执行
                result = await self._execute_single_task(assignment)

                results[task_id] = result

            except Exception as e:
                logger.error(f"❌ 任务执行失败 {task_id}: {e}")
                results[task_id] = {'success': False, 'error': str(e)}

        return results

    async def _execute_parallel(self, assignments: Dict[str, AgentAssignment]) -> Dict[str, Any]:
        """并行执行"""
        try:
            logger.info(f"🔄 并行执行 {len(assignments)} 个任务")

            # 创建并行任务
            tasks = [
                self._execute_single_task(assignment)
                for assignment in assignments.values()
            ]

            # 等待所有任务完成
            task_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 整理结果
            results = {}
            for i, result in enumerate(task_results):
                task_id = list(assignments.keys())[i]
                if isinstance(result, Exception):
                    logger.error(f"❌ 并行任务失败 {task_id}: {result}")
                    results[task_id] = {'success': False, 'error': str(result)}
                else:
                    results[task_id] = result

            return results

        except Exception as e:
            logger.error(f"❌ 并行执行失败: {e}")
            return {}

    async def _execute_hybrid(self, assignments: Dict[str, AgentAssignment]) -> Dict[str, Any]:
        """混合执行"""
        try:
            logger.info("🔄 混合模式执行: 分析任务依赖关系")

            # 分析依赖关系，分为可并行组和串行链
            parallel_groups, sequential_chain = self._analyze_task_dependencies(assignments)

            results = {}

            # 先执行串行链
            for task_id in sequential_chain:
                if task_id in assignments:
                    result = await self._execute_single_task(assignments[task_id])
                    results[task_id] = result

            # 然后并行执行各组
            for group in parallel_groups:
                group_tasks = [
                    self._execute_single_task(assignments[task_id])
                    for task_id in group if task_id in assignments
                ]

                if group_tasks:
                    group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
                    for i, result in enumerate(group_results):
                        task_id = group[i]
                        if isinstance(result, Exception):
                            results[task_id] = {'success': False, 'error': str(result)}
                        else:
                            results[task_id] = result

            return results

        except Exception as e:
            logger.error(f"❌ 混合执行失败: {e}")
            return {}

    async def _execute_single_task(self, assignment: AgentAssignment) -> Dict[str, Any]:
        """执行单个任务"""
        try:
            # 这里应该调用实际的智能体执行方法
            # 暂时模拟执行
            await asyncio.sleep(0.1)  # 模拟执行时间

            # 模拟成功结果
            return {
                'success': True,
                'agent_type': assignment.agent_type,
                'execution_time': 0.1,
                'quality_score': assignment.expected_performance,
                'confidence_score': assignment.confidence_score
            }

        except Exception as e:
            logger.error(f"❌ 单任务执行失败 {assignment.task_id}: {e}")
            return {'success': False, 'error': str(e)}

    def _find_alternative_agent(self, task: CollaborationTask,
                               available_agents: Dict[str, int],
                               assigned_agents: Dict[str, int]) -> str:
        """寻找次优智能体"""
        # 按可用性排序智能体
        available_list = [
            agent for agent, total in available_agents.items()
            if total > assigned_agents.get(agent, 0)
        ]

        if not available_list:
            return None

        # 返回第一个可用的智能体作为次优选择
        return available_list[0]

    def _build_dependency_graph(self, tasks: List[CollaborationTask]) -> Dict[str, List[str]]:
        """构建依赖关系图"""
        graph = defaultdict(list)

        for task in tasks:
            for dep in task.dependencies:
                graph[task.task_id].append(dep)

        return dict(graph)

    def _count_independent_tasks(self, dependency_graph: Dict[str, List[str]]) -> int:
        """计算独立任务数量"""
        # 没有依赖关系的任务是独立的
        dependent_tasks = set()
        for deps in dependency_graph.values():
            dependent_tasks.update(deps)

        total_tasks = len(dependency_graph)
        return total_tasks - len(dependent_tasks)

    def _analyze_task_dependencies(self, assignments: Dict[str, AgentAssignment]) -> tuple:
        """分析任务依赖关系"""
        # 简化的依赖分析
        # 在实际实现中应该基于任务的实际依赖关系

        # 模拟分组：假设所有任务都可以并行
        parallel_groups = [list(assignments.keys())]
        sequential_chain = []

        return parallel_groups, sequential_chain

    def _calculate_success_rate(self, results: Dict[str, Any]) -> float:
        """计算成功率"""
        if not results:
            return 0.0

        successful = sum(1 for result in results.values() if result.get('success', False))
        return successful / len(results)

    def _count_conflicts_resolved(self, results: Dict[str, Any]) -> int:
        """计算解决的冲突数量"""
        # 暂时返回0，实际实现中应该跟踪冲突解决
        return 0

    def _record_collaboration_history(self, result: CollaborationResult) -> None:
        """记录协作历史"""
        self.collaboration_history.append(result)

        # 限制历史记录数量
        if len(self.collaboration_history) > 100:
            self.collaboration_history = self.collaboration_history[-100:]

    def _generate_collaboration_id(self) -> str:
        """生成协作ID"""
        import uuid
        return f"collab_{uuid.uuid4().hex[:8]}"

    def _initialize_agent_availability(self) -> None:
        """初始化智能体可用性"""
        # 默认配置
        self.agent_availability = {
            'EnhancedKnowledgeRetrievalAgent': 3,
            'EnhancedReasoningAgent': 2,
            'EnhancedAnswerGenerationAgent': 2,
            'EnhancedCitationAgent': 1,
            'FactVerificationAgent': 1
        }


class ConflictDetector:
    """冲突检测器"""

    def __init__(self):
        self.conflict_patterns = {
            'resource_conflict': self._detect_resource_conflict,
            'capability_overlap': self._detect_capability_overlap,
            'timing_conflict': self._detect_timing_conflict
        }

    async def detect_conflicts(self, assignments: Dict[str, AgentAssignment]) -> List[Dict[str, Any]]:
        """检测冲突"""
        conflicts = []

        for pattern_name, detector in self.conflict_patterns.items():
            pattern_conflicts = await detector(assignments)
            conflicts.extend(pattern_conflicts)

        return conflicts

    async def _detect_resource_conflict(self, assignments: Dict[str, AgentAssignment]) -> List[Dict[str, Any]]:
        """检测资源冲突"""
        # 简化的资源冲突检测
        agent_usage = defaultdict(int)

        for assignment in assignments.values():
            agent_usage[assignment.agent_type] += 1

        conflicts = []
        for agent_type, usage in agent_usage.items():
            if usage > 2:  # 假设每个智能体最多支持2个并发任务
                conflicts.append({
                    'type': 'resource_conflict',
                    'agent_type': agent_type,
                    'usage': usage,
                    'severity': 'medium'
                })

        return conflicts

    async def _detect_capability_overlap(self, assignments: Dict[str, AgentAssignment]) -> List[Dict[str, Any]]:
        """检测能力重叠冲突"""
        # 检测相同类型的任务是否分配给了相同能力的智能体
        task_types = defaultdict(list)

        for assignment in assignments.values():
            # 这里需要根据任务类型来判断，暂时简化
            task_types[assignment.agent_type].append(assignment.task_id)

        conflicts = []
        for agent_type, tasks in task_types.items():
            if len(tasks) > 1:
                conflicts.append({
                    'type': 'capability_overlap',
                    'agent_type': agent_type,
                    'tasks': tasks,
                    'severity': 'low'
                })

        return conflicts

    async def _detect_timing_conflict(self, assignments: Dict[str, AgentAssignment]) -> List[Dict[str, Any]]:
        """检测时间冲突"""
        # 暂时返回空列表，实际实现中应该检测时间安排冲突
        return []
