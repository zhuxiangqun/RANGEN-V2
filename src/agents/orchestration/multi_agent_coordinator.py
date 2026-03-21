"""
多Agent协作协调器 (L6级别)
提供高级的多Agent协作能力，支持任务分解、协作规划和智能调度
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

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center, get_unified_intelligent_center

logger = logging.getLogger(__name__)

@dataclass
class CollaborationTask:
    """协作任务"""
    task_id: str
    description: str
    complexity: str  # simple, moderate, complex, advanced
    subtasks: List[Dict[str, Any]] = field(default_factory=list)
    assigned_agents: Dict[str, str] = field(default_factory=dict)  # subtask_id -> agent_id
    dependencies: Dict[str, Set[str]] = field(default_factory=dict)  # subtask_id -> set of prerequisite subtask_ids
    status: str = "pending"  # pending, in_progress, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentCapability:
    """Agent能力描述"""
    agent_id: str
    capabilities: Set[str]
    expertise_level: Dict[str, float]  # capability -> level (0-1)
    availability: float  # 0-1, 当前可用性
    current_load: int
    max_concurrent_tasks: int
    performance_history: deque = field(default_factory=lambda: deque(maxlen=100))

@dataclass
class CollaborationPlan:
    """协作计划"""
    plan_id: str
    task: CollaborationTask
    execution_order: List[str]  # subtask_ids in execution order
    agent_assignments: Dict[str, str]  # subtask_id -> agent_id
    estimated_duration: float
    risk_assessment: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

class MultiAgentCoordinator(ExpertAgent):
    """
    多Agent协作协调器 (L6级别)
    实现高级的多Agent协作能力，包括：
    - 智能任务分解和规划
    - 动态Agent调度和负载均衡
    - 协作流程优化和冲突解决
    - 实时协作监控和调整
    """

    def __init__(self):
        super().__init__(
            agent_id="multi_agent_coordinator",
            domain_expertise="多Agent协作和任务编排",
            capability_level=0.95,  # L6级别
            collaboration_style="orchestrator"
        )
        self.module_logger = get_module_logger(ModuleType.AGENT, "MultiAgentCoordinator")
        self.config_center = get_unified_config_center()
        self.intelligent_center = get_unified_intelligent_center()

        # 协作任务管理
        self.active_tasks: Dict[str, CollaborationTask] = {}
        self.completed_tasks: deque[CollaborationTask] = deque(maxlen=1000)
        self.task_queue: asyncio.Queue[CollaborationTask] = asyncio.Queue()

        # Agent能力注册表
        self.agent_capabilities: Dict[str, AgentCapability] = {}
        self.agent_instances: Dict[str, ExpertAgent] = {}

        # 协作计划缓存
        self.collaboration_plans: Dict[str, CollaborationPlan] = {}

        # 性能监控
        self.task_execution_times: deque[float] = deque(maxlen=1000)
        self.collaboration_efficiency: deque[float] = deque(maxlen=100)

        # 配置参数
        self.max_concurrent_tasks = self.config_center.get_config_value(
            "multi_agent_coordinator", "max_concurrent_tasks", 10
        )
        self.task_timeout = self.config_center.get_config_value(
            "multi_agent_coordinator", "task_timeout_seconds", 3600
        )
        self.load_balancing_threshold = self.config_center.get_config_value(
            "multi_agent_coordinator", "load_balancing_threshold", 0.8
        )

        # 任务管理
        self._task_processor_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
        self._running = False

        # 协作统计
        self.total_tasks_processed = 0
        self.successful_collaborations = 0
        self.average_task_duration = 0.0
        self.collaboration_conflicts_resolved = 0

    def register_agent(self, agent: ExpertAgent, capabilities: Set[str],
                      expertise_levels: Dict[str, float], max_concurrent: int = 3):
        """注册Agent及其能力"""
        agent_id = agent.agent_id

        capability = AgentCapability(
            agent_id=agent_id,
            capabilities=capabilities,
            expertise_level=expertise_levels,
            availability=1.0,
            current_load=0,
            max_concurrent_tasks=max_concurrent
        )

        self.agent_capabilities[agent_id] = capability
        self.agent_instances[agent_id] = agent

        self.module_logger.info(f"✅ Agent已注册: {agent_id}, 能力: {capabilities}")

    async def submit_collaboration_task(self, description: str, context: Dict[str, Any]) -> str:
        """提交协作任务"""
        task_id = f"collab_{uuid.uuid4().hex[:8]}"

        # 分析任务复杂度
        complexity = await self._analyze_task_complexity(description, context)

        # 创建协作任务
        task = CollaborationTask(
            task_id=task_id,
            description=description,
            complexity=complexity,
            metadata=context
        )

        self.active_tasks[task_id] = task
        await self.task_queue.put(task)

        self.module_logger.info(f"📋 协作任务已提交: {task_id} - {description[:50]}... (复杂度: {complexity})")
        return task_id

    async def _analyze_task_complexity(self, description: str, context: Dict[str, Any]) -> str:
        """分析任务复杂度"""
        # 基于描述长度、关键词和上下文分析复杂度
        description_length = len(description)
        complexity_keywords = ['复杂', '高级', '多步骤', '协作', '优化', '分析', '设计']

        keyword_count = sum(1 for keyword in complexity_keywords if keyword in description.lower())

        if description_length > 500 or keyword_count >= 3 or context.get('complexity') == 'advanced':
            return 'advanced'
        elif description_length > 200 or keyword_count >= 2 or context.get('complexity') == 'complex':
            return 'complex'
        elif description_length > 100 or keyword_count >= 1 or context.get('complexity') == 'moderate':
            return 'moderate'
        else:
            return 'simple'

    async def _task_processor_loop(self):
        """任务处理循环"""
        while self._running:
            try:
                # 检查并发限制
                if len(self.active_tasks) >= self.max_concurrent_tasks:
                    await asyncio.sleep(1)
                    continue

                # 获取任务
                task = await self.task_queue.get()

                # 异步处理任务
                asyncio.create_task(self._process_collaboration_task(task))

            except Exception as e:
                self.module_logger.error(f"❌ 任务处理循环异常: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _process_collaboration_task(self, task: CollaborationTask):
        """处理协作任务"""
        start_time = time.time()
        task.status = "in_progress"

        try:
            self.module_logger.info(f"🚀 开始处理协作任务: {task.task_id}")

            # 步骤1: 任务分解
            await self._decompose_task(task)

            # 步骤2: 生成协作计划
            plan = await self._generate_collaboration_plan(task)

            # 步骤3: 执行协作计划
            success = await self._execute_collaboration_plan(task, plan)

            # 步骤4: 整合结果
            final_result = await self._integrate_results(task)

            task.status = "completed" if success else "failed"
            task.completed_at = datetime.now()
            task.results = final_result

            duration = time.time() - start_time
            self.task_execution_times.append(duration)
            self.total_tasks_processed += 1

            if success:
                self.successful_collaborations += 1
                self.module_logger.info(f"✅ 协作任务完成: {task.task_id} (耗时: {duration:.2f}秒)")
            else:
                self.module_logger.error(f"❌ 协作任务失败: {task.task_id}")

        except Exception as e:
            task.status = "failed"
            task.completed_at = datetime.now()
            self.module_logger.error(f"❌ 协作任务异常: {task.task_id} - {e}", exc_info=True)

        finally:
            # 清理任务
            if task.task_id in self.active_tasks:
                completed_task = self.active_tasks.pop(task.task_id)
                self.completed_tasks.append(completed_task)

    async def _decompose_task(self, task: CollaborationTask):
        """任务分解"""
        self.module_logger.info(f"🔍 分解任务: {task.task_id}")

        # 基于复杂度确定分解策略
        if task.complexity == 'simple':
            # 简单任务：1-2个子任务
            task.subtasks = [
                {
                    "id": f"{task.task_id}_main",
                    "description": task.description,
                    "type": "main",
                    "estimated_effort": 1
                }
            ]
        elif task.complexity == 'moderate':
            # 中等任务：2-3个子任务
            task.subtasks = [
                {
                    "id": f"{task.task_id}_analysis",
                    "description": f"分析任务需求: {task.description}",
                    "type": "analysis",
                    "estimated_effort": 1
                },
                {
                    "id": f"{task.task_id}_execution",
                    "description": f"执行主要任务: {task.description}",
                    "type": "execution",
                    "estimated_effort": 2
                }
            ]
        elif task.complexity == 'complex':
            # 复杂任务：3-5个子任务
            task.subtasks = [
                {
                    "id": f"{task.task_id}_planning",
                    "description": f"制定执行计划: {task.description}",
                    "type": "planning",
                    "estimated_effort": 1
                },
                {
                    "id": f"{task.task_id}_analysis",
                    "description": f"深入分析任务: {task.description}",
                    "type": "analysis",
                    "estimated_effort": 2
                },
                {
                    "id": f"{task.task_id}_execution",
                    "description": f"执行任务: {task.description}",
                    "type": "execution",
                    "estimated_effort": 3
                },
                {
                    "id": f"{task.task_id}_review",
                    "description": f"审查和优化结果: {task.description}",
                    "type": "review",
                    "estimated_effort": 1
                }
            ]
        else:  # advanced
            # 高级任务：4-6个子任务
            task.subtasks = [
                {
                    "id": f"{task.task_id}_research",
                    "description": f"研究和信息收集: {task.description}",
                    "type": "research",
                    "estimated_effort": 2
                },
                {
                    "id": f"{task.task_id}_design",
                    "description": f"设计解决方案: {task.description}",
                    "type": "design",
                    "estimated_effort": 2
                },
                {
                    "id": f"{task.task_id}_implementation",
                    "description": f"实施解决方案: {task.description}",
                    "type": "implementation",
                    "estimated_effort": 4
                },
                {
                    "id": f"{task.task_id}_testing",
                    "description": f"测试和验证: {task.description}",
                    "type": "testing",
                    "estimated_effort": 2
                },
                {
                    "id": f"{task.task_id}_optimization",
                    "description": f"优化和改进: {task.description}",
                    "type": "optimization",
                    "estimated_effort": 2
                }
            ]

        # 设置依赖关系
        self._setup_task_dependencies(task)

        self.module_logger.info(f"✅ 任务分解完成: {len(task.subtasks)} 个子任务")

    def _setup_task_dependencies(self, task: CollaborationTask):
        """设置任务依赖关系"""
        if task.complexity == 'simple':
            # 简单任务无依赖
            pass
        elif task.complexity == 'moderate':
            # analysis -> execution
            task.dependencies[task.subtasks[1]["id"]] = {task.subtasks[0]["id"]}
        elif task.complexity == 'complex':
            # planning -> analysis -> execution -> review
            task.dependencies[task.subtasks[1]["id"]] = {task.subtasks[0]["id"]}
            task.dependencies[task.subtasks[2]["id"]] = {task.subtasks[1]["id"]}
            task.dependencies[task.subtasks[3]["id"]] = {task.subtasks[2]["id"]}
        else:  # advanced
            # research -> design -> implementation -> testing -> optimization
            task.dependencies[task.subtasks[1]["id"]] = {task.subtasks[0]["id"]}
            task.dependencies[task.subtasks[2]["id"]] = {task.subtasks[1]["id"]}
            task.dependencies[task.subtasks[3]["id"]] = {task.subtasks[2]["id"]}
            task.dependencies[task.subtasks[4]["id"]] = {task.subtasks[3]["id"]}

    async def _generate_collaboration_plan(self, task: CollaborationTask) -> CollaborationPlan:
        """生成协作计划"""
        self.module_logger.info(f"📋 生成协作计划: {task.task_id}")

        plan_id = f"plan_{task.task_id}"

        # 确定执行顺序（基于依赖关系）
        execution_order = self._calculate_execution_order(task)

        # 分配Agent
        agent_assignments = await self._assign_agents_to_subtasks(task, execution_order)

        # 估算总时长
        estimated_duration = sum(subtask["estimated_effort"] for subtask in task.subtasks) * 60  # 假设每effort单位1分钟

        # 风险评估
        risk_assessment = await self._assess_collaboration_risks(task, agent_assignments)

        plan = CollaborationPlan(
            plan_id=plan_id,
            task=task,
            execution_order=execution_order,
            agent_assignments=agent_assignments,
            estimated_duration=estimated_duration,
            risk_assessment=risk_assessment
        )

        self.collaboration_plans[plan_id] = plan
        self.module_logger.info(f"✅ 协作计划生成完成: {plan_id}")
        return plan

    def _calculate_execution_order(self, task: CollaborationTask) -> List[str]:
        """计算任务执行顺序"""
        # 简单的拓扑排序
        subtask_ids = [st["id"] for st in task.subtasks]
        result = []
        visited = set()
        visiting = set()

        def visit(subtask_id: str):
            if subtask_id in visiting:
                return  # 循环依赖，跳过
            if subtask_id in visited:
                return

            visiting.add(subtask_id)

            # 访问依赖
            for dep_id in task.dependencies.get(subtask_id, set()):
                visit(dep_id)

            visiting.remove(subtask_id)
            visited.add(subtask_id)
            result.append(subtask_id)

        # 访问所有子任务
        for subtask_id in subtask_ids:
            if subtask_id not in visited:
                visit(subtask_id)

        return result

    async def _assign_agents_to_subtasks(self, task: CollaborationTask, execution_order: List[str]) -> Dict[str, str]:
        """为子任务分配Agent"""
        assignments = {}

        for subtask_id in execution_order:
            subtask = next(st for st in task.subtasks if st["id"] == subtask_id)
            subtask_type = subtask["type"]

            # 基于子任务类型选择最佳Agent
            best_agent = await self._select_best_agent_for_subtask(subtask_type, subtask)

            if best_agent:
                assignments[subtask_id] = best_agent
                task.assigned_agents[subtask_id] = best_agent

                # 更新Agent负载
                if best_agent in self.agent_capabilities:
                    self.agent_capabilities[best_agent].current_load += 1

        return assignments

    async def _select_best_agent_for_subtask(self, subtask_type: str, subtask: Dict[str, Any]) -> Optional[str]:
        """为子任务选择最佳Agent"""
        candidates = []

        for agent_id, capability in self.agent_capabilities.items():
            if capability.current_load >= capability.max_concurrent_tasks:
                continue  # Agent已满载

            # 计算匹配度
            relevance_score = 0

            # 类型匹配
            if subtask_type in capability.capabilities:
                relevance_score += 0.4

            # 能力水平
            expertise = capability.expertise_level.get(subtask_type, 0)
            relevance_score += expertise * 0.4

            # 可用性
            relevance_score += capability.availability * 0.2

            if relevance_score > 0:
                candidates.append((agent_id, relevance_score))

        if not candidates:
            return None

        # 选择匹配度最高的
        best_agent = max(candidates, key=lambda x: x[1])[0]
        return best_agent

    async def _assess_collaboration_risks(self, task: CollaborationTask, assignments: Dict[str, str]) -> Dict[str, Any]:
        """评估协作风险"""
        risks = {
            "high_load_agents": [],
            "single_point_failures": [],
            "dependency_conflicts": 0,
            "resource_contention": False,
            "overall_risk_level": "low"
        }

        # 检查高负载Agent
        for agent_id, capability in self.agent_capabilities.items():
            load_ratio = capability.current_load / capability.max_concurrent_tasks
            if load_ratio > self.load_balancing_threshold:
                risks["high_load_agents"].append(agent_id)

        # 检查单点故障
        agent_usage = defaultdict(int)
        for agent_id in assignments.values():
            agent_usage[agent_id] += 1

        for agent_id, usage in agent_usage.items():
            if usage >= len(task.subtasks) * 0.7:  # 一个Agent负责70%以上的任务
                risks["single_point_failures"].append(agent_id)

        # 计算整体风险等级
        risk_score = len(risks["high_load_agents"]) * 0.3 + len(risks["single_point_failures"]) * 0.4

        if risk_score > 0.7:
            risks["overall_risk_level"] = "high"
        elif risk_score > 0.3:
            risks["overall_risk_level"] = "medium"

        return risks

    async def _execute_collaboration_plan(self, task: CollaborationTask, plan: CollaborationPlan) -> bool:
        """执行协作计划"""
        self.module_logger.info(f"▶️ 开始执行协作计划: {plan.plan_id}")

        results = {}
        completed_subtasks = set()

        for subtask_id in plan.execution_order:
            # 检查依赖是否满足
            dependencies = task.dependencies.get(subtask_id, set())
            if not dependencies.issubset(completed_subtasks):
                self.module_logger.warning(f"⚠️ 跳过子任务 {subtask_id}，依赖未满足")
                continue

            # 执行子任务
            success = await self._execute_subtask(task, subtask_id, plan.agent_assignments.get(subtask_id))
            results[subtask_id] = success

            if success:
                completed_subtasks.add(subtask_id)
            else:
                self.module_logger.error(f"❌ 子任务执行失败: {subtask_id}")
                return False

        task.results = results
        self.module_logger.info(f"✅ 协作计划执行完成: {plan.plan_id}")
        return True

    async def _execute_subtask(self, task: CollaborationTask, subtask_id: str, agent_id: Optional[str]) -> bool:
        """执行单个子任务"""
        if not agent_id or agent_id not in self.agent_instances:
            self.module_logger.error(f"❌ 无法执行子任务 {subtask_id}，Agent {agent_id} 不可用")
            return False

        agent = self.agent_instances[agent_id]
        subtask = next(st for st in task.subtasks if st["id"] == subtask_id)

        try:
            # 准备上下文
            context = {
                "subtask_id": subtask_id,
                "subtask_type": subtask["type"],
                "description": subtask["description"],
                "parent_task": task.description,
                "complexity": task.complexity,
                **task.metadata
            }

            # 执行任务
            result = await agent.execute(context)

            # 记录结果
            subtask["result"] = result.data if result.success else None
            subtask["success"] = result.success
            subtask["error"] = result.error
            subtask["processing_time"] = result.processing_time

            # 更新Agent性能历史
            if agent_id in self.agent_capabilities:
                capability = self.agent_capabilities[agent_id]
                capability.performance_history.append({
                    "timestamp": datetime.now(),
                    "success": result.success,
                    "processing_time": result.processing_time,
                    "subtask_type": subtask["type"]
                })

            return result.success

        except Exception as e:
            self.module_logger.error(f"❌ 子任务执行异常: {subtask_id} - {e}", exc_info=True)
            return False

        finally:
            # 减少Agent负载
            if agent_id in self.agent_capabilities:
                self.agent_capabilities[agent_id].current_load = max(0, self.agent_capabilities[agent_id].current_load - 1)

    async def _integrate_results(self, task: CollaborationTask) -> Dict[str, Any]:
        """整合所有子任务结果"""
        integrated_result = {
            "task_id": task.task_id,
            "description": task.description,
            "complexity": task.complexity,
            "subtask_results": {},
            "summary": "",
            "confidence": 0.0
        }

        successful_subtasks = 0
        total_subtasks = len(task.subtasks)

        for subtask in task.subtasks:
            subtask_id = subtask["id"]
            integrated_result["subtask_results"][subtask_id] = {
                "type": subtask["type"],
                "description": subtask["description"],
                "success": subtask.get("success", False),
                "result": subtask.get("result"),
                "processing_time": subtask.get("processing_time", 0)
            }

            if subtask.get("success", False):
                successful_subtasks += 1

        # 生成摘要
        success_rate = successful_subtasks / total_subtasks if total_subtasks > 0 else 0
        integrated_result["summary"] = f"协作任务完成，成功率: {success_rate:.1%} ({successful_subtasks}/{total_subtasks})"
        integrated_result["confidence"] = success_rate

        return integrated_result

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await self._update_agent_availability()
                await self._monitor_collaboration_health()
                await self._cleanup_expired_tasks()

            except Exception as e:
                self.module_logger.error(f"❌ 监控循环异常: {e}", exc_info=True)

            await asyncio.sleep(60)  # 每分钟监控一次

    async def _update_agent_availability(self):
        """更新Agent可用性"""
        for agent_id, capability in self.agent_capabilities.items():
            # 基于负载计算可用性
            load_ratio = capability.current_load / capability.max_concurrent_tasks
            capability.availability = max(0, 1.0 - load_ratio)

    async def _monitor_collaboration_health(self):
        """监控协作健康状况"""
        # 计算协作效率
        if self.task_execution_times:
            recent_times = list(self.task_execution_times)[-10:]  # 最近10个任务
            avg_time = sum(recent_times) / len(recent_times)
            self.collaboration_efficiency.append(1.0 / (1.0 + avg_time / 3600))  # 归一化效率指标

        # 检查长时间运行的任务
        current_time = datetime.now()
        for task in self.active_tasks.values():
            if (current_time - task.created_at).total_seconds() > self.task_timeout:
                self.module_logger.warning(f"⚠️ 任务超时: {task.task_id}")
                task.status = "failed"

    async def _cleanup_expired_tasks(self):
        """清理过期任务"""
        current_time = datetime.now()
        expired_tasks = []

        for task_id, task in self.active_tasks.items():
            if task.status in ["completed", "failed"]:
                # 保留已完成的任务一段时间
                if task.completed_at and (current_time - task.completed_at).total_seconds() > 3600:  # 1小时
                    expired_tasks.append(task_id)

        for task_id in expired_tasks:
            completed_task = self.active_tasks.pop(task_id)
            self.completed_tasks.append(completed_task)

    async def _optimization_loop(self):
        """优化循环"""
        while self._running:
            try:
                await self._optimize_agent_assignments()
                await self._update_performance_models()

            except Exception as e:
                self.module_logger.error(f"❌ 优化循环异常: {e}", exc_info=True)

            await asyncio.sleep(300)  # 每5分钟优化一次

    async def _optimize_agent_assignments(self):
        """优化Agent分配策略"""
        # 基于历史性能数据调整分配策略
        for agent_id, capability in self.agent_capabilities.items():
            if capability.performance_history:
                recent_performance = list(capability.performance_history)[-20:]  # 最近20次执行

                success_rate = sum(1 for p in recent_performance if p["success"]) / len(recent_performance)
                avg_time = sum(p["processing_time"] for p in recent_performance) / len(recent_performance)

                # 调整能力水平评估
                for subtask_type in capability.expertise_level:
                    type_performance = [p for p in recent_performance if p["subtask_type"] == subtask_type]
                    if type_performance:
                        type_success_rate = sum(1 for p in type_performance if p["success"]) / len(type_performance)
                        # 根据成功率微调能力水平
                        adjustment = (type_success_rate - 0.5) * 0.1  # 微调幅度
                        capability.expertise_level[subtask_type] = max(0, min(1, capability.expertise_level[subtask_type] + adjustment))

    async def _update_performance_models(self):
        """更新性能模型"""
        # 更新平均任务持续时间
        if self.task_execution_times:
            self.average_task_duration = sum(self.task_execution_times) / len(self.task_execution_times)

    def _get_service(self):
        """MultiAgentCoordinator不直接使用单一Service"""
        return None

    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """执行多Agent协作任务"""
        description = context.get("description", "")
        if not description:
            return AgentResult(success=False, error="任务描述不能为空")

        try:
            task_id = await self.submit_collaboration_task(description, context)

            # 等待任务完成（简单的轮询，生产环境可以使用事件驱动）
            timeout = context.get("timeout", 3600)  # 默认1小时超时
            start_wait = time.time()

            while time.time() - start_wait < timeout:
                if task_id not in self.active_tasks:
                    # 任务已完成，查找结果
                    completed_task = None
                    for task in self.completed_tasks:
                        if task.task_id == task_id:
                            completed_task = task
                            break

                    if completed_task and completed_task.status == "completed":
                        return AgentResult(
                            success=True,
                            data=completed_task.results,
                            confidence=completed_task.results.get("confidence", 0.8)
                        )
                    else:
                        return AgentResult(success=False, error="任务执行失败")

                await asyncio.sleep(1)

            # 超时
            return AgentResult(success=False, error=f"任务执行超时 ({timeout}秒)")

        except Exception as e:
            self.module_logger.error(f"❌ 多Agent协作执行异常: {e}", exc_info=True)
            return AgentResult(success=False, error=str(e))

    async def start(self):
        """启动协调器"""
        if self._running:
            return

        self._running = True
        self._task_processor_task = asyncio.create_task(self._task_processor_loop())
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self._optimization_task = asyncio.create_task(self._optimization_loop())

        self.module_logger.info("✅ 多Agent协作协调器已启动")

    async def stop(self):
        """停止协调器"""
        self._running = False

        for task in [self._task_processor_task, self._monitor_task, self._optimization_task]:
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.module_logger.info("🛑 多Agent协作协调器已停止")

    def get_collaboration_stats(self) -> Dict[str, Any]:
        """获取协作统计信息"""
        return {
            "total_tasks_processed": self.total_tasks_processed,
            "successful_collaborations": self.successful_collaborations,
            "success_rate": self.successful_collaborations / self.total_tasks_processed if self.total_tasks_processed > 0 else 0,
            "average_task_duration": self.average_task_duration,
            "active_tasks": len(self.active_tasks),
            "registered_agents": len(self.agent_capabilities),
            "collaboration_conflicts_resolved": self.collaboration_conflicts_resolved,
            "current_efficiency": list(self.collaboration_efficiency)[-1] if self.collaboration_efficiency else 0
        }

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "status": "healthy",
            "active_tasks": len(self.active_tasks),
            "registered_agents": len(self.agent_capabilities),
            "completed_tasks": len(self.completed_tasks),
            "running": self._running
        }
