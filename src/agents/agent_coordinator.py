#!/usr/bin/env python3
"""
AgentCoordinator - 智能体协调器 (L5高级认知)
系统大脑，负责智能任务分配、资源调度、多Agent协作

优化特性：
- 智能任务分配算法：基于Agent能力和负载的任务匹配
- 资源调度与负载均衡：实时监控和动态调整
- 冲突检测与解决：预测性冲突避免和智能解决
"""

import time
import logging
import asyncio
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import heapq

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager
from src.utils.logging_helper import get_module_logger, ModuleType

logger = logging.getLogger(__name__)


class FailureAwareRouter:
    """失败感知路由器 - 避开最近失败的Agent"""

    def __init__(self):
        self.failure_history: Dict[str, List[Tuple[float, str]]] = {}  # agent_id -> [(timestamp, error_type), ...]
        self.failure_penalty_window = 300  # 5分钟惩罚窗口
        self.max_failure_rate = 0.3  # 30%失败率阈值
        self.min_samples_for_penalty = 5  # 最少样本数才考虑惩罚

    def record_failure(self, agent_id: str, error_type: str = "general"):
        """记录Agent失败"""
        if agent_id not in self.failure_history:
            self.failure_history[agent_id] = []

        self.failure_history[agent_id].append((time.time(), error_type))

        # 清理过期记录（超过1小时的）
        cutoff_time = time.time() - 3600
        self.failure_history[agent_id] = [
            (ts, err) for ts, err in self.failure_history[agent_id]
            if ts > cutoff_time
        ]

    def should_penalty_agent(self, agent_id: str) -> bool:
        """判断Agent是否应该被惩罚（临时降低优先级）"""
        recent_failures = self._get_recent_failures(agent_id)

        if len(recent_failures) < self.min_samples_for_penalty:
            return False  # 样本不足，不惩罚

        # 计算失败率
        failure_count = len([f for f in recent_failures if f[1] != 'success'])
        failure_rate = failure_count / len(recent_failures)

        return failure_rate > self.max_failure_rate

    def get_failure_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取Agent的失败统计"""
        recent_failures = self._get_recent_failures(agent_id)
        total_requests = len(recent_failures)

        if total_requests == 0:
            return {"failure_rate": 0.0, "total_requests": 0, "is_penalty": False}

        failure_count = len([f for f in recent_failures if f[1] != 'success'])
        failure_rate = failure_count / total_requests

        return {
            "failure_rate": failure_rate,
            "total_requests": total_requests,
            "is_penalty": self.should_penalty_agent(agent_id)
        }

    def _get_recent_failures(self, agent_id: str) -> List[Tuple[float, str]]:
        """获取最近的失败记录"""
        if agent_id not in self.failure_history:
            return []

        cutoff_time = time.time() - self.failure_penalty_window
        return [
            (ts, err_type) for ts, err_type in self.failure_history[agent_id]
            if ts > cutoff_time
        ]


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"
    BUSY = "busy"
    OVERLOADED = "overloaded"
    ERROR = "error"


@dataclass
class Task:
    """任务定义"""
    id: str
    description: str
    requirements: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: Set[str] = field(default_factory=set)
    estimated_complexity: float = 1.0  # 1.0-5.0
    deadline: Optional[float] = None
    submitted_time: float = field(default_factory=time.time)


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    capabilities: Set[str]
    current_load: float = 0.0  # 0.0-1.0
    status: AgentStatus = AgentStatus.IDLE
    performance_score: float = 1.0
    specialization_score: Dict[str, float] = field(default_factory=dict)
    last_active: float = field(default_factory=time.time)


class AgentCoordinator(ExpertAgent):
    """AgentCoordinator - 智能体协调器 (L5高级认知)

    核心职责：
    1. 智能任务分解与分配
    2. 多Agent协作编排
    3. 资源调度与负载均衡
    4. 系统级决策制定
    5. 冲突检测与解决

    优化特性：
    - 智能任务分配算法：基于多维度匹配的任务分配
    - 实时负载均衡：动态资源调度和过载保护
    - 冲突预测解决：基于依赖图的冲突检测和解决
    
    遵循三大原则:
    1. Superpowers: TDDEnforcer, TaskPlanner, TwoStageReviewer
    2. Claude HUD: AgentHUD 实时状态追踪
    3. Open SWE: MiddlewareChain 团队协作
    """
    
    def __init__(self):
        """初始化AgentCoordinator"""
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        self.agent_config = {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        }

        self.thresholds = {
            'performance_warning_threshold': self.threshold_manager.get_dynamic_threshold('performance', default_value=5.0),
            'error_rate_threshold': self.threshold_manager.get_dynamic_threshold('error_rate', default_value=0.1),
            'memory_usage_threshold': self.threshold_manager.get_dynamic_threshold('memory', default_value=80.0)
        }

        super().__init__(
            agent_id="agent_coordinator",
            domain_expertise="多智能体协调与调度",
            capability_level=0.95,
            collaboration_style="authoritative"
        )

        self.module_logger = get_module_logger(ModuleType.AGENT, "AgentCoordinator")

        # === OpenClaw: Superpowers 方法论工具集成 ===
        self._init_openclaw_tools()

        # 🚀 新增：核心数据结构
        self._agents: Dict[str, AgentInfo] = {}  # Agent注册表
        self._tasks: Dict[str, Task] = {}  # 任务队列
        self._task_assignments: Dict[str, str] = {}  # 任务分配映射
        self._execution_graph: Dict[str, Set[str]] = {}  # 任务依赖图

        # 🚀 新增：调度和监控
        self._scheduler = ThreadPoolExecutor(max_workers=8, thread_name_prefix="coordinator_scheduler")
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        self._load_balance_interval = 30
        self._conflict_check_interval = 15

        # 🚀 新增：性能统计
        self._stats = {
            'tasks_processed': 0,
            'tasks_failed': 0,
            'avg_response_time': 0.0,
            'load_balance_operations': 0,
            'conflicts_resolved': 0
        }

        # 🚀 新增：失败感知路由系统
        self.failure_aware_router = FailureAwareRouter()

        # 启动监控线程
        self._start_monitoring()
    
    def _init_openclaw_tools(self):
        """初始化 OpenClaw 方法论工具 (Superpowers 原则)"""
        # TDD Enforcer - 铁律检查
        try:
            from src.agents.tdd_enforcer import get_enforcer
            self.tdd_enforcer = get_enforcer()
            logger.debug("TDDEnforcer 集成成功")
        except ImportError:
            logger.warning("TDDEnforcer 不可用")
            self.tdd_enforcer = None
        
        # Two Stage Reviewer - 代码审查
        try:
            from src.agents.two_stage_reviewer import TwoStageReviewer
            self.code_reviewer = TwoStageReviewer()
            logger.debug("TwoStageReviewer 集成成功")
        except ImportError:
            logger.warning("TwoStageReviewer 不可用")
            self.code_reviewer = None
        
        # Requirement Discovery - 需求发现
        try:
            from src.agents.requirement_discovery import RequirementDiscoveryAgent
            self.requirement_discoverer = RequirementDiscoveryAgent()
            logger.debug("RequirementDiscoveryAgent 集成成功")
        except ImportError:
            logger.warning("RequirementDiscoveryAgent 不可用")
            self.requirement_discoverer = None
        
        # Task Planner - 任务规划
        try:
            from src.agents.task_planner import get_planner
            self.task_planner = get_planner()
            logger.debug("TaskPlanner 集成成功")
        except ImportError:
            logger.warning("TaskPlanner 不可用")
            self.task_planner = None
    
    def check_tdd_compliance(self, file_path: str) -> Tuple[bool, str]:
        """检查 TDD 合规性 (Superpowers 铁律)"""
        if self.tdd_enforcer:
            return self.tdd_enforcer.check_can_write_production(file_path)
        return True, "TDDEnforcer 未启用"
    
    def review_code(self, code: str, spec: str = "") -> Dict[str, Any]:
        """审查代码 (两阶段审查)"""
        if self.code_reviewer:
            return self.code_reviewer.run_review(code, spec).to_dict()
        return {"status": "skip", "reason": "Reviewer 未启用"}
    
    def discover_requirements(self, problem: str) -> Dict[str, Any]:
        """发现需求"""
        if self.requirement_discoverer:
            result = self.requirement_discoverer.discover_requirements(problem)
            return self.requirement_discoverer.export_to_dict()
        return {"error": "Discoverer 未启用"}

    def _get_service(self):
        """AgentCoordinator不直接使用单一Service"""
        return None

    def _get_failure_routing_stats(self) -> Dict[str, Any]:
        """获取失败感知路由统计"""
        agent_stats = {}
        for agent_id in self._agents.keys():
            agent_stats[agent_id] = self.failure_aware_router.get_failure_stats(agent_id)

        return {
            "agent_failure_stats": agent_stats,
            "penalty_window_seconds": self.failure_aware_router.failure_penalty_window,
            "max_failure_rate_threshold": self.failure_aware_router.max_failure_rate,
            "min_samples_required": self.failure_aware_router.min_samples_for_penalty
        }

    # 🚀 新增：Agent管理方法
    def register_agent(self, agent_id: str, capabilities: List[str],
                      specialization_scores: Optional[Dict[str, float]] = None):
        """注册Agent到协调器"""
        agent_info = AgentInfo(
            agent_id=agent_id,
            capabilities=set(capabilities),
            specialization_score=specialization_scores or {}
        )
        self._agents[agent_id] = agent_info
        self.module_logger.info(f"✅ Agent已注册: {agent_id}, 能力: {capabilities}")

    def update_agent_status(self, agent_id: str, status: AgentStatus, load: float = 0.0):
        """更新Agent状态"""
        if agent_id in self._agents:
            self._agents[agent_id].status = status
            self._agents[agent_id].current_load = load
            self._agents[agent_id].last_active = time.time()
            self.module_logger.debug(f"📊 Agent状态更新: {agent_id} -> {status.value} (负载: {load:.2f})")

    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self._agents:
            del self._agents[agent_id]
            # 清理相关任务分配
            self._cleanup_agent_tasks(agent_id)
            self.module_logger.info(f"❌ Agent已注销: {agent_id}")

    # 🚀 新增：智能任务分配算法
    async def submit_task(self, task: Task) -> str:
        """提交任务到协调器"""
        task_id = f"task_{int(time.time() * 1000)}_{task.id}"
        self._tasks[task_id] = task
        self._execution_graph[task_id] = set()

        # 建立依赖关系
        for dep_id in task.dependencies:
            if dep_id in self._tasks:
                self._execution_graph[dep_id].add(task_id)

        self.module_logger.info(f"📋 任务已提交: {task_id} - {task.description[:50]}...")

        # 尝试立即分配任务
        await self._try_assign_task(task_id)

        return task_id

    async def _try_assign_task(self, task_id: str) -> bool:
        """尝试分配任务"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        # 检查依赖是否已完成
        if not self._are_dependencies_met(task_id):
            self.module_logger.debug(f"⏳ 任务依赖未满足，等待中: {task_id}")
            return False

        # 智能选择最佳Agent
        best_agent = await self._select_best_agent(task)
        if not best_agent:
            self.module_logger.warning(f"⚠️ 无可用Agent处理任务: {task_id}")
            return False

        # 分配任务
        self._task_assignments[task_id] = best_agent
        self.update_agent_status(best_agent, AgentStatus.BUSY,
                               self._agents[best_agent].current_load + task.estimated_complexity * 0.1)

        self.module_logger.info(f"✅ 任务已分配: {task_id} -> {best_agent}")
        return True

    def report_task_result(self, task_id: str, agent_id: str, success: bool, error_type: str = "general"):
        """报告任务执行结果（用于失败感知路由）"""
        if success:
            # 记录成功
            self.failure_aware_router.record_failure(agent_id, "success")
        else:
            # 记录失败
            self.failure_aware_router.record_failure(agent_id, error_type)
            self.module_logger.debug(f"📊 记录Agent失败: {agent_id}, 类型: {error_type}")

        # 更新统计
        if success:
            self._stats['tasks_processed'] += 1
        else:
            self._stats['tasks_failed'] += 1

    async def _select_best_agent(self, task: Task) -> Optional[str]:
        """智能选择最佳Agent（集成失败感知路由）"""
        candidates = []

        for agent_id, agent_info in self._agents.items():
            if agent_info.status in [AgentStatus.IDLE, AgentStatus.BUSY]:
                # 🚀 新增：失败感知路由 - 检查是否应该惩罚此Agent
                if self.failure_aware_router.should_penalty_agent(agent_id):
                    self.module_logger.debug(f"🚫 Agent {agent_id} 被失败感知路由惩罚，跳过")
                    continue

                # 计算匹配分数
                match_score = self._calculate_match_score(task, agent_info)
                load_penalty = agent_info.current_load * 0.3  # 负载惩罚
                final_score = match_score - load_penalty

                candidates.append((final_score, agent_id))

        if not candidates:
            # 如果所有候选人都被惩罚了，选择失败率最低的Agent
            self.module_logger.warning("⚠️ 所有候选Agent都被惩罚，使用失败率最低的Agent")
            return self._select_least_failed_agent(task)

        # 选择分数最高的Agent
        candidates.sort(reverse=True)
        best_agent = candidates[0][1]

        self.module_logger.debug(f"🎯 任务分配选择: {best_agent} (分数: {candidates[0][0]:.2f})")
        return best_agent

    def _select_least_failed_agent(self, task: Task) -> Optional[str]:
        """选择失败率最低的Agent（兜底策略）"""
        candidates = []

        for agent_id, agent_info in self._agents.items():
            if agent_info.status in [AgentStatus.IDLE, AgentStatus.BUSY]:
                failure_stats = self.failure_aware_router.get_failure_stats(agent_id)
                failure_rate = failure_stats['failure_rate']

                # 计算匹配分数（正常分数 - 失败率惩罚）
                match_score = self._calculate_match_score(task, agent_info)
                failure_penalty = failure_rate * 2.0  # 失败率惩罚权重
                final_score = match_score - failure_penalty

                candidates.append((final_score, agent_id))

        if not candidates:
            return None

        candidates.sort(reverse=True)
        best_agent = candidates[0][1]

        self.module_logger.info(f"🛡️ 兜底策略选择Agent: {best_agent} (失败率兜底)")
        return best_agent

    def _calculate_match_score(self, task: Task, agent: AgentInfo) -> float:
        """计算任务与Agent的匹配分数"""
        score = 0.0

        # 1. 能力匹配 (权重: 0.4)
        required_caps = set(task.requirements.get('capabilities', []))
        agent_caps = agent.capabilities
        cap_match = len(required_caps & agent_caps) / len(required_caps) if required_caps else 1.0
        score += cap_match * 0.4

        # 2. 专业化匹配 (权重: 0.3)
        domain = task.requirements.get('domain', '')
        specialization = agent.specialization_score.get(domain, 0.5)
        score += specialization * 0.3

        # 3. 性能分数 (权重: 0.2)
        score += agent.performance_score * 0.2

        # 4. 优先级加成 (权重: 0.1)
        priority_bonus = (task.priority.value - 1) * 0.1
        score += priority_bonus

        return min(score, 1.0)  # 最高分数为1.0

    def _are_dependencies_met(self, task_id: str) -> bool:
        """检查任务依赖是否满足"""
        task = self._tasks.get(task_id)
        if not task:
            return False

        for dep_id in task.dependencies:
            if dep_id not in self._task_assignments:
                return False  # 依赖任务未分配

            # 检查依赖任务是否已完成（这里需要外部状态更新）
            # 简化实现：假设已分配的任务都会完成
            pass

        return True

    # 🚀 新增：负载均衡和冲突解决
    async def _load_balance_check(self):
        """负载均衡检查"""
        while self._running:
            try:
                await asyncio.sleep(self._load_balance_interval)

                overloaded_agents = [
                    agent_id for agent_id, agent in self._agents.items()
                    if agent.current_load > 0.8
                ]

                if overloaded_agents:
                    self.module_logger.info(f"⚖️ 检测到过载Agent: {overloaded_agents}")
                    await self._perform_load_balancing(overloaded_agents)
                    self._stats['load_balance_operations'] += 1

            except Exception as e:
                self.module_logger.error(f"负载均衡检查失败: {e}")

    async def _perform_load_balancing(self, overloaded_agents: List[str]):
        """执行负载均衡"""
        for agent_id in overloaded_agents:
            # 查找负载较低的Agent
            underloaded_agents = [
                aid for aid, agent in self._agents.items()
                if agent.current_load < 0.5 and agent.status != AgentStatus.ERROR
            ]

            if not underloaded_agents:
                continue

            # 尝试迁移任务（简化实现）
            # 实际实现需要更复杂的任务迁移逻辑
            self.module_logger.info(f"🔄 尝试负载均衡: {agent_id} -> {underloaded_agents[0]}")

    async def _conflict_detection_check(self):
        """冲突检测检查"""
        while self._running:
            try:
                await asyncio.sleep(self._conflict_check_interval)

                conflicts = self._detect_conflicts()
                if conflicts:
                    self.module_logger.warning(f"⚠️ 检测到任务冲突: {len(conflicts)} 个")
                    await self._resolve_conflicts(conflicts)
                    self._stats['conflicts_resolved'] += len(conflicts)

            except Exception as e:
                self.module_logger.error(f"冲突检测失败: {e}")

    def _detect_conflicts(self) -> List[Tuple[str, str]]:
        """检测任务冲突"""
        conflicts = []

        # 检查资源冲突（简化实现）
        agent_tasks = {}
        for task_id, agent_id in self._task_assignments.items():
            if agent_id not in agent_tasks:
                agent_tasks[agent_id] = []
            agent_tasks[agent_id].append(task_id)

        # 检查单个Agent的任务负载冲突
        for agent_id, tasks in agent_tasks.items():
            if len(tasks) > 5:  # 单个Agent同时处理的任务上限
                # 标记为冲突（简化逻辑）
                for i in range(1, len(tasks)):
                    conflicts.append((tasks[0], tasks[i]))

        return conflicts

    async def _resolve_conflicts(self, conflicts: List[Tuple[str, str]]):
        """解决任务冲突"""
        for task1_id, task2_id in conflicts:
            # 重新分配优先级较低的任务
            task1 = self._tasks.get(task1_id)
            task2 = self._tasks.get(task2_id)

            if not task1 or not task2:
                continue

            # 选择优先级较低的任务重新分配
            lower_priority_task = task1 if task1.priority.value <= task2.priority.value else task2

            # 从当前分配中移除
            if lower_priority_task.id in self._task_assignments:
                old_agent = self._task_assignments[lower_priority_task.id]
                del self._task_assignments[lower_priority_task.id]

                # 降低原Agent负载
                if old_agent in self._agents:
                    self._agents[old_agent].current_load = max(0,
                        self._agents[old_agent].current_load - lower_priority_task.estimated_complexity * 0.1)

                # 尝试重新分配
                await self._try_assign_task(lower_priority_task.id)

                self.module_logger.info(f"🔧 冲突解决: 重新分配任务 {lower_priority_task.id}")

    # 🚀 新增：监控和统计
    def _start_monitoring(self):
        """启动监控线程"""
        self._running = True
        self._monitor_thread = threading.Thread(target=self._run_monitoring_loop, daemon=True)
        self._monitor_thread.start()
        self.module_logger.info("📊 监控线程已启动")

    def _run_monitoring_loop(self):
        """运行监控循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._monitoring_loop())
        except Exception as e:
            self.module_logger.error(f"监控循环异常: {e}")
        finally:
            loop.close()

    async def _monitoring_loop(self):
        """监控循环"""
        await asyncio.gather(
            self._load_balance_check(),
            self._conflict_detection_check()
        )

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'active_agents': len([a for a in self._agents.values() if a.status != AgentStatus.ERROR]),
            'pending_tasks': len(self._tasks) - len(self._task_assignments),
            'current_load_avg': sum(a.current_load for a in self._agents.values()) / len(self._agents) if self._agents else 0
        }

    # 🚀 新增：任务状态管理
    def mark_task_completed(self, task_id: str, success: bool = True):
        """标记任务完成"""
        if task_id in self._task_assignments:
            agent_id = self._task_assignments[task_id]

            # 更新Agent负载
            if agent_id in self._agents:
                task = self._tasks.get(task_id)
                if task:
                    load_reduction = task.estimated_complexity * 0.1
                    self._agents[agent_id].current_load = max(0,
                        self._agents[agent_id].current_load - load_reduction)

                    # 更新性能分数
                    if success:
                        self._agents[agent_id].performance_score = min(1.0,
                            self._agents[agent_id].performance_score + 0.01)
                    else:
                        self._agents[agent_id].performance_score = max(0.5,
                            self._agents[agent_id].performance_score - 0.05)

            # 清理任务
            if success:
                self._stats['tasks_processed'] += 1
            else:
                self._stats['tasks_failed'] += 1

            del self._task_assignments[task_id]

            # 尝试分配等待中的任务
            pending_tasks = [tid for tid in self._tasks.keys() if tid not in self._task_assignments]
            for pending_task in pending_tasks:
                asyncio.create_task(self._try_assign_task(pending_task))

            self.module_logger.info(f"✅ 任务完成: {task_id} ({'成功' if success else '失败'})")

    def _cleanup_agent_tasks(self, agent_id: str):
        """清理Agent相关的任务"""
        # 将分配给该Agent的任务重新分配
        affected_tasks = [tid for tid, aid in self._task_assignments.items() if aid == agent_id]

        for task_id in affected_tasks:
            if task_id in self._task_assignments:
                del self._task_assignments[task_id]
                # 异步重新分配（简化实现）
                asyncio.create_task(self._try_assign_task(task_id))

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行协调任务

        Args:
            context: 协调请求上下文
                - action: 协调动作 ("register_agent", "submit_task", "get_stats"等)
                - agent_id: Agent ID (注册时需要)
                - capabilities: Agent能力列表 (注册时需要)
                - task: 任务对象 (提交任务时需要)

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        action = context.get("action", "")

        try:
            if action == "register_agent":
                agent_id = context.get("agent_id", "")
                capabilities = context.get("capabilities", [])
                specialization_scores = context.get("specialization_scores")

                self.register_agent(agent_id, capabilities, specialization_scores)
                result_data = {"status": "registered", "agent_id": agent_id}

            elif action == "submit_task":
                task_data = context.get("task", {})
                task = Task(**task_data)
                task_id = await self.submit_task(task)
                result_data = {"status": "submitted", "task_id": task_id}

            elif action == "get_stats":
                result_data = self.get_stats()

            elif action == "get_failure_routing_stats":
                result_data = self._get_failure_routing_stats()

            elif action == "update_agent_status":
                agent_id = context.get("agent_id", "")
                status_str = context.get("status", "idle")
                load = context.get("load", 0.0)

                try:
                    status = AgentStatus(status_str)
                    self.update_agent_status(agent_id, status, load)
                    result_data = {"status": "updated", "agent_id": agent_id}
                except ValueError:
                    result_data = {"error": f"无效状态: {status_str}"}

            else:
                result_data = {"error": f"不支持的动作: {action}"}

            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.9,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.module_logger.error(f"协调执行失败: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )

    def shutdown(self):
        """关闭协调器"""
        self._running = False
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)

        self._scheduler.shutdown(wait=True)
        self.module_logger.info("🛑 AgentCoordinator已关闭")
