#!/usr/bin/env python3
"""
Task Planner - 精确任务规划器

借鉴 Superpowers writing-plans skill 的任务规划方法:

规划原则:
1. Bite-sized tasks: 每个任务 2-5 分钟工作量
2. File structure mapping: 定义文件职责
3. Scope check: 多子系统拆分为独立计划
4. 每步验证通过后再进行下一步

规划格式:
```
### Task N: [Component Name]
**Files:** Create/Modify/Test paths

- [ ] Step 1: 写失败的测试
- [ ] Step 2: 运行测试 (确认失败)
- [ ] Step 3: 写最小实现
- [ ] Step 4: 运行测试 (确认通过)
- [ ] Step 5: 提交
```
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"          # 待处理
    IN_PROGRESS = "in_progress"  # 进行中
    BLOCKED = "blocked"          # 被阻塞
    COMPLETED = "completed"      # 完成
    FAILED = "failed"           # 失败
    SKIPPED = "skipped"         # 跳过


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TaskStep:
    """任务步骤"""
    step_id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    verification: str = ""  # 验证命令或方法
    expected_result: str = ""
    actual_result: str = ""
    duration: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "status": self.status.value,
            "verification": self.verification,
            "expected_result": self.expected_result,
            "actual_result": self.actual_result,
            "duration": self.duration,
            "error": self.error
        }


@dataclass
class Task:
    """任务"""
    task_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    files: List[str] = field(default_factory=list)  # Create/Modify/Test 文件
    steps: List[TaskStep] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务 ID
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_completion_percentage(self) -> float:
        """获取完成百分比"""
        if not self.steps:
            return 0.0
        
        completed = sum(1 for s in self.steps if s.status == TaskStatus.COMPLETED)
        return (completed / len(self.steps)) * 100
    
    def is_ready_to_start(self, completed_tasks: List[str]) -> bool:
        """检查任务是否可以开始（依赖已满足）"""
        return all(dep in completed_tasks for dep in self.dependencies)
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "priority": self.priority.value,
            "files": self.files,
            "steps": [s.to_dict() for s in self.steps],
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completion_percentage": self.get_completion_percentage(),
            "metadata": self.metadata
        }


@dataclass
class Plan:
    """计划"""
    plan_id: str
    title: str
    goal: str  # 一句话目标
    architecture: str = ""  # 2-3 句架构描述
    tech_stack: List[str] = field(default_factory=list)
    tasks: List[Task] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def get_completion_percentage(self) -> float:
        """获取完成百分比"""
        if not self.tasks:
            return 0.0
        
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        return (completed / len(self.tasks)) * 100
    
    def get_next_ready_task(self) -> Optional[Task]:
        """获取下一个可执行的任务"""
        completed_ids = [t.task_id for t in self.tasks if t.status == TaskStatus.COMPLETED]
        
        for task in sorted(self.tasks, key=lambda t: t.priority.value):
            if task.status == TaskStatus.PENDING and task.is_ready_to_start(completed_ids):
                return task
        
        return None
    
    def to_dict(self) -> Dict:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "goal": self.goal,
            "architecture": self.architecture,
            "tech_stack": self.tech_stack,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completion_percentage": self.get_completion_percentage()
        }
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"# {self.title}",
            "",
            f"**Goal:** {self.goal}",
            "",
        ]
        
        if self.architecture:
            lines.append(f"**Architecture:** {self.architecture}")
            lines.append("")
        
        if self.tech_stack:
            lines.append(f"**Tech Stack:** {', '.join(self.tech_stack)}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        for i, task in enumerate(self.tasks, 1):
            lines.append(f"### Task {i}: {task.title}")
            lines.append("")
            
            if task.files:
                lines.append(f"**Files:** {', '.join(task.files)}")
                lines.append("")
            
            if task.description:
                lines.append(task.description)
                lines.append("")
            
            for step in task.steps:
                checkbox = "[x]" if step.status == TaskStatus.COMPLETED else "[ ]"
                lines.append(f"- {checkbox} {step.description}")
            
            lines.append("")
        
        return "\n".join(lines)


class TaskPlanner:
    """
    任务规划器
    
    核心功能:
    1. 从高层目标生成精确任务计划
    2. 将任务拆分为 bite-sized 步骤 (2-5 分钟)
    3. 跟踪任务依赖关系
    4. 支持按优先级排序
    5. 提供进度可视化
    """
    
    def __init__(self):
        self._plans: Dict[str, Plan] = {}
        self._current_plan_id: Optional[str] = None
        
        logger.info("TaskPlanner 初始化")
    
    def create_plan(
        self,
        goal: str,
        title: str = "",
        architecture: str = "",
        tech_stack: List[str] = None
    ) -> Plan:
        """创建新计划"""
        plan_id = f"plan_{int(datetime.now().timestamp())}"
        
        plan = Plan(
            plan_id=plan_id,
            title=title or goal[:50],
            goal=goal,
            architecture=architecture,
            tech_stack=tech_stack or []
        )
        
        self._plans[plan_id] = plan
        self._current_plan_id = plan_id
        
        logger.info(f"创建计划: {plan_id} - {plan.title}")
        return plan
    
    def add_task(
        self,
        plan_id: str,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        files: List[str] = None,
        dependencies: List[str] = None,
        steps: List[Dict] = None
    ) -> Task:
        """添加任务到计划"""
        if plan_id not in self._plans:
            raise ValueError(f"计划不存在: {plan_id}")
        
        plan = self._plans[plan_id]
        
        task_id = f"{plan_id}_task_{len(plan.tasks) + 1}"
        
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            files=files or [],
            dependencies=dependencies or []
        )
        
        # 添加步骤
        if steps:
            for i, step_data in enumerate(steps, 1):
                step = TaskStep(
                    step_id=f"{task_id}_step_{i}",
                    description=step_data.get("description", ""),
                    verification=step_data.get("verification", ""),
                    expected_result=step_data.get("expected_result", "")
                )
                task.steps.append(step)
        
        plan.tasks.append(task)
        
        logger.info(f"添加任务: {task_id} - {title}")
        return task
    
    def create_tdd_task(
        self,
        plan_id: str,
        title: str,
        production_file: str,
        test_file: str,
        description: str = ""
    ) -> Task:
        """
        创建 TDD 任务（带标准 RED-GREEN-REFACTOR 步骤）
        
        标准步骤:
        1. 写失败的测试
        2. 运行测试 (确认失败)
        3. 写最小实现
        4. 运行测试 (确认通过)
        5. 提交
        """
        task = self.add_task(
            plan_id=plan_id,
            title=title,
            description=description,
            files=[test_file, production_file],
            steps=[
                {
                    "description": "Step 1: 写失败的测试",
                    "verification": f"python -m pytest {test_file} --tb=short",
                    "expected_result": "测试失败 (RED)"
                },
                {
                    "description": "Step 2: 运行测试确认失败",
                    "verification": f"python -m pytest {test_file} -v",
                    "expected_result": "FAILED"
                },
                {
                    "description": "Step 3: 写最小实现代码",
                    "verification": "python -c 'import ast; ast.parse(open(' + repr(production_file) + ').read())'",
                    "expected_result": "无语法错误"
                },
                {
                    "description": "Step 4: 运行测试确认通过",
                    "verification": f"python -m pytest {test_file} -v",
                    "expected_result": "PASSED (GREEN)"
                },
                {
                    "description": "Step 5: 提交代码",
                    "verification": "git commit -m 'feat: implement ...'",
                    "expected_result": "提交成功"
                }
            ]
        )
        
        return task
    
    def start_task(self, task_id: str) -> bool:
        """开始任务"""
        for plan in self._plans.values():
            for task in plan.tasks:
                if task.task_id == task_id:
                    if task.status != TaskStatus.PENDING:
                        logger.warning(f"任务 {task_id} 不是待处理状态")
                        return False
                    
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = datetime.now()
                    
                    logger.info(f"开始任务: {task_id}")
                    return True
        
        logger.error(f"任务不存在: {task_id}")
        return False
    
    def complete_step(self, task_id: str, step_id: str, actual_result: str = "") -> bool:
        """完成步骤"""
        for plan in self._plans.values():
            for task in plan.tasks:
                if task.task_id == task_id:
                    for step in task.steps:
                        if step.step_id == step_id:
                            step.status = TaskStatus.COMPLETED
                            step.actual_result = actual_result
                            
                            logger.info(f"完成步骤: {step_id}")
                            return True
        
        logger.error(f"步骤不存在: {step_id}")
        return False
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        for plan in self._plans.values():
            for task in plan.tasks:
                if task.task_id == task_id:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    
                    # 检查是否所有任务都完成
                    if all(t.status == TaskStatus.COMPLETED for t in plan.tasks):
                        plan.completed_at = datetime.now()
                        logger.info(f"计划完成: {plan.plan_id}")
                    
                    logger.info(f"完成任务: {task_id}")
                    return True
        
        logger.error(f"任务不存在: {task_id}")
        return False
    
    def fail_task(self, task_id: str, reason: str) -> bool:
        """标记任务失败"""
        for plan in self._plans.values():
            for task in plan.tasks:
                if task.task_id == task_id:
                    task.status = TaskStatus.FAILED
                    task.metadata["failure_reason"] = reason
                    
                    logger.error(f"任务失败: {task_id} - {reason}")
                    return True
        
        logger.error(f"任务不存在: {task_id}")
        return False
    
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        """获取计划"""
        return self._plans.get(plan_id)
    
    def get_current_plan(self) -> Optional[Plan]:
        """获取当前计划"""
        if self._current_plan_id:
            return self._plans.get(self._current_plan_id)
        return None
    
    def get_next_task(self) -> Optional[Task]:
        """获取下一个可执行的任务"""
        plan = self.get_current_plan()
        if plan:
            return plan.get_next_ready_task()
        return None
    
    def get_progress_summary(self) -> Dict:
        """获取进度摘要"""
        summary = {
            "total_plans": len(self._plans),
            "total_tasks": 0,
            "completed_tasks": 0,
            "in_progress_tasks": 0,
            "pending_tasks": 0,
            "plans_completion": {}
        }
        
        for plan_id, plan in self._plans.items():
            summary["total_tasks"] += len(plan.tasks)
            summary["plans_completion"][plan_id] = {
                "title": plan.title,
                "completion": plan.get_completion_percentage()
            }
            
            for task in plan.tasks:
                if task.status == TaskStatus.COMPLETED:
                    summary["completed_tasks"] += 1
                elif task.status == TaskStatus.IN_PROGRESS:
                    summary["in_progress_tasks"] += 1
                elif task.status == TaskStatus.PENDING:
                    summary["pending_tasks"] += 1
        
        return summary
    
    def export_to_json(self, plan_id: str) -> str:
        """导出计划为 JSON"""
        plan = self.get_plan(plan_id)
        if plan:
            return json.dumps(plan.to_dict(), indent=2, ensure_ascii=False)
        return "{}"
    
    def export_to_markdown(self, plan_id: str) -> str:
        """导出计划为 Markdown"""
        plan = self.get_plan(plan_id)
        if plan:
            return plan.to_markdown()
        return ""


# 全局单例
_planner: Optional[TaskPlanner] = None


def get_planner() -> TaskPlanner:
    """获取全局任务规划器"""
    global _planner
    if _planner is None:
        _planner = TaskPlanner()
    return _planner
