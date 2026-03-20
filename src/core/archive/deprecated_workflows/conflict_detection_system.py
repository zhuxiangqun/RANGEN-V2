"""
冲突检测与解决系统 (Conflict Detection and Resolution System)

实现多智能体协作中的冲突识别和自动解决机制：
- 资源冲突检测
- 任务依赖冲突检测
- 时序冲突检测
- 自动冲突解决策略
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import heapq

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """冲突类型"""
    RESOURCE_CONFLICT = "resource_conflict"          # 资源冲突
    TASK_DEPENDENCY_CONFLICT = "task_dependency"     # 任务依赖冲突
    TIMING_CONFLICT = "timing_conflict"              # 时序冲突
    CAPABILITY_CONFLICT = "capability_conflict"      # 能力冲突
    PRIORITY_CONFLICT = "priority_conflict"          # 优先级冲突


class ConflictSeverity(Enum):
    """冲突严重程度"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ResolutionStrategy(Enum):
    """解决策略"""
    NEGOTIATION = "negotiation"           # 协商解决
    REASSIGNMENT = "reassignment"         # 重新分配
    SEQUENTIAL_EXECUTION = "sequential"   # 顺序执行
    PARALLEL_EXECUTION = "parallel"       # 并行执行
    RESOURCE_SHARING = "resource_sharing" # 资源共享
    PRIORITY_OVERRIDE = "priority_override" # 优先级覆盖


@dataclass
class Conflict:
    """冲突描述"""
    conflict_id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_agents: List[str]
    affected_resources: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    resolution_strategy: Optional[ResolutionStrategy] = None
    resolution_status: str = "detected"  # detected, resolving, resolved, failed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'conflict_id': self.conflict_id,
            'conflict_type': self.conflict_type.value,
            'severity': self.severity.value,
            'description': self.description,
            'affected_agents': self.affected_agents,
            'affected_resources': self.affected_resources,
            'timestamp': self.timestamp.isoformat(),
            'resolution_strategy': self.resolution_strategy.value if self.resolution_strategy else None,
            'resolution_status': self.resolution_status,
            'metadata': self.metadata
        }


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    agent_id: str
    task_type: str
    resources_required: List[str]
    estimated_duration: float
    priority: int
    dependencies: List[str]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


@dataclass
class ResourceInfo:
    """资源信息"""
    resource_id: str
    resource_type: str
    capacity: float
    current_usage: float
    allocated_to: List[str]  # 分配给的任务ID列表


class ConflictDetector:
    """冲突检测器"""

    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.resources: Dict[str, ResourceInfo] = {}
        self.agent_schedules: Dict[str, List[TaskInfo]] = {}

    async def detect_conflicts(self, new_task: TaskInfo) -> List[Conflict]:
        """检测新任务可能引起的冲突"""
        conflicts = []

        # 1. 资源冲突检测
        resource_conflicts = await self._detect_resource_conflicts(new_task)
        conflicts.extend(resource_conflicts)

        # 2. 任务依赖冲突检测
        dependency_conflicts = await self._detect_dependency_conflicts(new_task)
        conflicts.extend(dependency_conflicts)

        # 3. 时序冲突检测
        timing_conflicts = await self._detect_timing_conflicts(new_task)
        conflicts.extend(timing_conflicts)

        # 4. 能力冲突检测
        capability_conflicts = await self._detect_capability_conflicts(new_task)
        conflicts.extend(capability_conflicts)

        # 5. 优先级冲突检测
        priority_conflicts = await self._detect_priority_conflicts(new_task)
        conflicts.extend(priority_conflicts)

        return conflicts

    async def _detect_resource_conflicts(self, new_task: TaskInfo) -> List[Conflict]:
        """检测资源冲突"""
        conflicts = []

        for resource_id in new_task.resources_required:
            if resource_id not in self.resources:
                continue

            resource = self.resources[resource_id]
            current_usage = resource.current_usage

            # 检查资源容量
            if current_usage + 1.0 > resource.capacity:  # 假设每个任务占用1.0单位
                conflict = Conflict(
                    conflict_id=f"resource_{resource_id}_{new_task.task_id}",
                    conflict_type=ConflictType.RESOURCE_CONFLICT,
                    severity=ConflictSeverity.HIGH,
                    description=f"资源 {resource_id} 容量不足",
                    affected_agents=[new_task.agent_id],
                    affected_resources=[resource_id],
                    metadata={
                        'current_usage': current_usage,
                        'capacity': resource.capacity,
                        'required': 1.0
                    }
                )
                conflicts.append(conflict)

        return conflicts

    async def _detect_dependency_conflicts(self, new_task: TaskInfo) -> List[Conflict]:
        """检测任务依赖冲突"""
        conflicts = []

        for dep_task_id in new_task.dependencies:
            if dep_task_id not in self.tasks:
                continue

            dep_task = self.tasks[dep_task_id]

            # 检查循环依赖
            if await self._has_circular_dependency(new_task.task_id, dep_task_id):
                conflict = Conflict(
                    conflict_id=f"dependency_{new_task.task_id}_{dep_task_id}",
                    conflict_type=ConflictType.TASK_DEPENDENCY_CONFLICT,
                    severity=ConflictSeverity.CRITICAL,
                    description=f"检测到循环依赖: {new_task.task_id} -> {dep_task_id}",
                    affected_agents=[new_task.agent_id, dep_task.agent_id],
                    affected_resources=[]
                )
                conflicts.append(conflict)

        return conflicts

    async def _detect_timing_conflicts(self, new_task: TaskInfo) -> List[Conflict]:
        """检测时序冲突"""
        conflicts = []

        agent_id = new_task.agent_id
        if agent_id not in self.agent_schedules:
            return conflicts

        agent_tasks = self.agent_schedules[agent_id]

        # 检查时间重叠
        for existing_task in agent_tasks:
            if existing_task.end_time and new_task.start_time:
                if (existing_task.start_time <= new_task.start_time < existing_task.end_time or
                    new_task.start_time <= existing_task.start_time < new_task.end_time):
                    conflict = Conflict(
                        conflict_id=f"timing_{existing_task.task_id}_{new_task.task_id}",
                        conflict_type=ConflictType.TIMING_CONFLICT,
                        severity=ConflictSeverity.MEDIUM,
                        description=f"任务时序重叠: {existing_task.task_id} 与 {new_task.task_id}",
                        affected_agents=[agent_id],
                        affected_resources=[]
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _detect_capability_conflicts(self, new_task: TaskInfo) -> List[Conflict]:
        """检测能力冲突"""
        # 这里需要与智能体能力管理系统集成
        # 暂时返回空列表
        return []

    async def _detect_priority_conflicts(self, new_task: TaskInfo) -> List[Conflict]:
        """检测优先级冲突"""
        conflicts = []

        # 检查是否有更高优先级的任务在等待
        for task in self.tasks.values():
            if (task.priority > new_task.priority and
                task.agent_id == new_task.agent_id):
                conflict = Conflict(
                    conflict_id=f"priority_{task.task_id}_{new_task.task_id}",
                    conflict_type=ConflictType.PRIORITY_CONFLICT,
                    severity=ConflictSeverity.LOW,
                    description=f"优先级冲突: {task.task_id} (优先级 {task.priority}) vs {new_task.task_id} (优先级 {new_task.priority})",
                    affected_agents=[new_task.agent_id],
                    affected_resources=[]
                )
                conflicts.append(conflict)

        return conflicts

    async def _has_circular_dependency(self, task_id: str, dep_task_id: str) -> bool:
        """检查是否存在循环依赖"""
        visited = set()
        stack = [task_id]

        while stack:
            current = stack.pop()
            if current in visited:
                continue

            visited.add(current)

            if current == dep_task_id:
                return True

            # 检查当前任务的依赖
            if current in self.tasks:
                for dep in self.tasks[current].dependencies:
                    stack.append(dep)

        return False

    def update_task_info(self, task: TaskInfo):
        """更新任务信息"""
        self.tasks[task.task_id] = task

        # 更新智能体调度
        if task.agent_id not in self.agent_schedules:
            self.agent_schedules[task.agent_id] = []
        self.agent_schedules[task.agent_id].append(task)

    def update_resource_info(self, resource: ResourceInfo):
        """更新资源信息"""
        self.resources[resource.resource_id] = resource


class ConflictResolver:
    """冲突解决器"""

    def __init__(self, detector: ConflictDetector):
        self.detector = detector
        self.resolution_strategies = {
            ConflictType.RESOURCE_CONFLICT: self._resolve_resource_conflict,
            ConflictType.TASK_DEPENDENCY_CONFLICT: self._resolve_dependency_conflict,
            ConflictType.TIMING_CONFLICT: self._resolve_timing_conflict,
            ConflictType.CAPABILITY_CONFLICT: self._resolve_capability_conflict,
            ConflictType.PRIORITY_CONFLICT: self._resolve_priority_conflict
        }

    async def resolve_conflicts(self, conflicts: List[Conflict]) -> Dict[str, Any]:
        """解决冲突列表"""
        results = {
            'resolved': [],
            'failed': [],
            'pending_negotiation': []
        }

        # 按严重程度排序，先解决严重冲突
        sorted_conflicts = sorted(conflicts, key=lambda c: c.severity.value, reverse=True)

        for conflict in sorted_conflicts:
            try:
                resolution = await self._resolve_single_conflict(conflict)
                if resolution['status'] == 'resolved':
                    results['resolved'].append(resolution)
                elif resolution['status'] == 'negotiation_required':
                    results['pending_negotiation'].append(resolution)
                else:
                    results['failed'].append(resolution)
            except Exception as e:
                logger.error(f"解决冲突 {conflict.conflict_id} 失败: {e}")
                results['failed'].append({
                    'conflict': conflict,
                    'error': str(e)
                })

        return results

    async def _resolve_single_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """解决单个冲突"""
        resolver = self.resolution_strategies.get(conflict.conflict_type)
        if not resolver:
            return {
                'conflict': conflict,
                'status': 'failed',
                'reason': '不支持的冲突类型'
            }

        try:
            resolution = await resolver(conflict)
            conflict.resolution_strategy = resolution.get('strategy')
            conflict.resolution_status = resolution['status']

            return {
                'conflict': conflict,
                'status': resolution['status'],
                'strategy': resolution.get('strategy'),
                'actions': resolution.get('actions', [])
            }
        except Exception as e:
            return {
                'conflict': conflict,
                'status': 'failed',
                'error': str(e)
            }

    async def _resolve_resource_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """解决资源冲突"""
        # 尝试重新分配资源或调整执行顺序
        affected_resource = conflict.affected_resources[0]

        # 检查是否有其他可用资源
        alternative_resources = [
            r for r in self.detector.resources.values()
            if r.resource_type == self.detector.resources[affected_resource].resource_type
            and r.current_usage < r.capacity
        ]

        if alternative_resources:
            return {
                'status': 'resolved',
                'strategy': ResolutionStrategy.REASSIGNMENT,
                'actions': [{
                    'type': 'reassign_resource',
                    'from_resource': affected_resource,
                    'to_resource': alternative_resources[0].resource_id
                }]
            }
        else:
            # 没有替代资源，建议顺序执行
            return {
                'status': 'resolved',
                'strategy': ResolutionStrategy.SEQUENTIAL_EXECUTION,
                'actions': [{
                    'type': 'sequential_execution',
                    'resource': affected_resource
                }]
            }

    async def _resolve_dependency_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """解决依赖冲突"""
        # 循环依赖无法自动解决，需要人工干预
        return {
            'status': 'negotiation_required',
            'strategy': ResolutionStrategy.NEGOTIATION,
            'actions': [{
                'type': 'manual_intervention',
                'reason': '循环依赖需要人工解决'
            }]
        }

    async def _resolve_timing_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """解决时序冲突"""
        # 调整任务执行时间
        return {
            'status': 'resolved',
            'strategy': ResolutionStrategy.SEQUENTIAL_EXECUTION,
            'actions': [{
                'type': 'adjust_timing',
                'description': '调整任务执行顺序避免时序冲突'
            }]
        }

    async def _resolve_capability_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """解决能力冲突"""
        return {
            'status': 'resolved',
            'strategy': ResolutionStrategy.REASSIGNMENT,
            'actions': [{
                'type': 'reassign_agent',
                'description': '将任务分配给具有合适能力的智能体'
            }]
        }

    async def _resolve_priority_conflict(self, conflict: Conflict) -> Dict[str, Any]:
        """解决优先级冲突"""
        # 让高优先级任务先执行
        return {
            'status': 'resolved',
            'strategy': ResolutionStrategy.PRIORITY_OVERRIDE,
            'actions': [{
                'type': 'priority_override',
                'description': '按优先级顺序执行任务'
            }]
        }


class ConflictDetectionSystem:
    """
    冲突检测与解决系统

    提供完整的冲突管理功能：
    - 实时冲突检测
    - 自动冲突解决
    - 协商机制支持
    - 学习和优化
    """

    def __init__(self):
        self.detector = ConflictDetector()
        self.resolver = ConflictResolver(self.detector)
        self.active_conflicts: Dict[str, Conflict] = {}
        self.resolution_history: List[Dict[str, Any]] = []
        self._running = False
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动冲突检测系统"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._continuous_monitoring())
        logger.info("冲突检测与解决系统已启动")

    async def stop(self):
        """停止冲突检测系统"""
        if not self._running:
            return

        self._running = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("冲突检测与解决系统已停止")

    async def check_task_assignment(self, task: TaskInfo) -> Dict[str, Any]:
        """检查任务分配是否有冲突"""
        # 更新系统状态
        self.detector.update_task_info(task)

        # 检测冲突
        conflicts = await self.detector.detect_conflicts(task)

        if not conflicts:
            return {
                'status': 'approved',
                'conflicts': []
            }

        # 尝试解决冲突
        resolution_results = await self.resolver.resolve_conflicts(conflicts)

        # 记录活动冲突
        for conflict in conflicts:
            self.active_conflicts[conflict.conflict_id] = conflict

        # 记录解决历史
        self.resolution_history.append({
            'timestamp': datetime.now(),
            'task_id': task.task_id,
            'conflicts': [c.to_dict() for c in conflicts],
            'resolution': resolution_results
        })

        # 返回结果
        has_blocking_conflicts = any(
            c.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
            for c in conflicts
        )

        return {
            'status': 'conflicts_detected' if has_blocking_conflicts else 'resolved',
            'conflicts': [c.to_dict() for c in conflicts],
            'resolution': resolution_results,
            'requires_negotiation': len(resolution_results.get('pending_negotiation', [])) > 0
        }

    async def negotiate_conflict_resolution(self, conflict_id: str,
                                          proposed_solution: Dict[str, Any]) -> Dict[str, Any]:
        """协商冲突解决"""
        if conflict_id not in self.active_conflicts:
            return {
                'status': 'not_found',
                'message': f'冲突 {conflict_id} 不存在'
            }

        conflict = self.active_conflicts[conflict_id]

        # 评估协商方案
        evaluation = await self._evaluate_negotiation_proposal(conflict, proposed_solution)

        if evaluation['acceptable']:
            # 接受协商方案
            conflict.resolution_status = 'resolved'
            conflict.metadata['negotiation_result'] = proposed_solution

            return {
                'status': 'accepted',
                'conflict': conflict.to_dict(),
                'evaluation': evaluation
            }
        else:
            return {
                'status': 'rejected',
                'conflict': conflict.to_dict(),
                'evaluation': evaluation,
                'counter_proposals': evaluation.get('counter_proposals', [])
            }

    async def _evaluate_negotiation_proposal(self, conflict: Conflict,
                                           proposal: Dict[str, Any]) -> Dict[str, Any]:
        """评估协商方案"""
        # 简单的评估逻辑，可以根据具体需求扩展
        evaluation = {
            'acceptable': False,
            'score': 0.0,
            'reasons': [],
            'counter_proposals': []
        }

        # 检查提案是否解决了冲突
        if proposal.get('resolves_conflict', False):
            evaluation['score'] += 0.7
            evaluation['acceptable'] = True
            evaluation['reasons'].append('提案解决了核心冲突')
        else:
            evaluation['reasons'].append('提案未能完全解决冲突')

        # 检查对系统性能的影响
        performance_impact = proposal.get('performance_impact', 0.0)
        if performance_impact > -0.3:  # 性能影响不超过30%
            evaluation['score'] += 0.3
        else:
            evaluation['reasons'].append('性能影响过大')

        return evaluation

    async def _continuous_monitoring(self):
        """持续监控冲突状态"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次

                # 检查过期冲突
                current_time = datetime.now()
                expired_conflicts = []

                for conflict_id, conflict in self.active_conflicts.items():
                    if conflict.resolution_status == 'detected':
                        age = current_time - conflict.timestamp
                        if age > timedelta(hours=1):  # 1小时未解决的冲突
                            expired_conflicts.append(conflict_id)

                # 清理过期冲突
                for conflict_id in expired_conflicts:
                    conflict = self.active_conflicts[conflict_id]
                    logger.warning(f"冲突 {conflict_id} 超时未解决: {conflict.description}")
                    del self.active_conflicts[conflict_id]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"冲突监控错误: {e}")

    def get_conflict_statistics(self) -> Dict[str, Any]:
        """获取冲突统计信息"""
        total_conflicts = len(self.resolution_history)
        resolved_conflicts = sum(
            1 for h in self.resolution_history
            if h['resolution'].get('resolved', [])
        )
        failed_conflicts = sum(
            1 for h in self.resolution_history
            if h['resolution'].get('failed', [])
        )

        conflict_types = {}
        for history in self.resolution_history:
            for conflict_data in history['conflicts']:
                conflict_type = conflict_data['conflict_type']
                conflict_types[conflict_type] = conflict_types.get(conflict_type, 0) + 1

        return {
            'total_conflicts': total_conflicts,
            'resolved_conflicts': resolved_conflicts,
            'failed_conflicts': failed_conflicts,
            'resolution_rate': resolved_conflicts / total_conflicts if total_conflicts > 0 else 0,
            'conflict_types': conflict_types,
            'active_conflicts': len(self.active_conflicts)
        }


# 全局实例
_conflict_system_instance: Optional[ConflictDetectionSystem] = None

def get_conflict_detection_system() -> ConflictDetectionSystem:
    """获取冲突检测系统实例"""
    global _conflict_system_instance
    if _conflict_system_instance is None:
        _conflict_system_instance = ConflictDetectionSystem()
    return _conflict_system_instance
