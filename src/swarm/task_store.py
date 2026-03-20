"""
Swarm 任务存储

实现任务管理和依赖跟踪:
- 任务 CRUD
- 依赖管理 (blocked-by)
- 自动解除阻塞
- 状态流转
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict, field


class TaskStatus:
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Task:
    """任务"""
    id: str
    title: str
    description: str = ""
    owner: str = ""  # 负责人
    status: str = TaskStatus.PENDING
    blocked_by: List[str] = field(default_factory=list)  # 依赖的任务ID
    created_at: str = ""
    updated_at: str = ""
    completed_at: str = ""
    result: str = ""  # 执行结果
    priority: int = 0  # 0-10
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)
    
    @property
    def is_blocked(self) -> bool:
        """是否被阻塞"""
        return self.status == TaskStatus.BLOCKED and len(self.blocked_by) > 0


class TaskStore:
    """
    任务存储
    
    存储结构:
    .swarm/
    └── {team}/
        └── tasks/
            └── tasks.json
    
    使用方式:
        store = TaskStore(".swarm")
        store.create_task("test-team", "实现认证", owner="backend")
        store.create_task("test-team", "编写测试", blocked_by=["T1"])
    """
    
    def __init__(self, base_dir: str = ".swarm"):
        self.base_dir = Path(base_dir)
    
    def _get_tasks_file(self, team: str) -> Path:
        """获取任务文件路径"""
        return self.base_dir / team / "tasks" / "tasks.json"
    
    def _ensure_dir(self, team: str) -> Path:
        """确保目录存在"""
        tasks_dir = self.base_dir / team / "tasks"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        return tasks_dir
    
    def _load_tasks(self, team: str) -> Dict[str, Task]:
        """加载任务"""
        tasks_file = self._get_tasks_file(team)
        
        if not tasks_file.exists():
            return {}
        
        with open(tasks_file, encoding="utf-8") as f:
            data = json.load(f)
            return {tid: Task.from_dict(tdata) for tid, tdata in data.items()}
    
    def _save_tasks(self, team: str, tasks: Dict[str, Task]) -> None:
        """保存任务"""
        self._ensure_dir(team)
        tasks_file = self._get_tasks_file(team)
        
        with open(tasks_file, "w", encoding="utf-8") as f:
            data = {tid: task.to_dict() for tid, task in tasks.items()}
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _generate_id(self) -> str:
        """生成任务ID"""
        return f"T{str(uuid.uuid4())[:4].upper()}"
    
    def create_task(
        self,
        team: str,
        title: str,
        description: str = "",
        owner: str = "",
        blocked_by: Optional[List[str]] = None,
        priority: int = 0
    ) -> Task:
        """
        创建任务
        
        Args:
            team: 团队名
            title: 任务标题
            description: 任务描述
            owner: 负责人
            blocked_by: 依赖的任务ID列表
            priority: 优先级 (0-10)
            
        Returns:
            创建的任务
        """
        tasks = self._load_tasks(team)
        
        task_id = self._generate_id()
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            owner=owner,
            status=TaskStatus.PENDING,
            blocked_by=blocked_by or [],
            priority=priority
        )
        
        # 如果有依赖，自动设为 blocked
        if task.blocked_by:
            task.status = TaskStatus.BLOCKED
        
        tasks[task_id] = task
        self._save_tasks(team, tasks)
        
        return task
    
    def get_task(self, team: str, task_id: str) -> Optional[Task]:
        """获取任务"""
        tasks = self._load_tasks(team)
        return tasks.get(task_id)
    
    def list_tasks(
        self,
        team: str,
        status: Optional[str] = None,
        owner: Optional[str] = None
    ) -> List[Task]:
        """
        列出任务
        
        Args:
            team: 团队名
            status: 按状态过滤
            owner: 按负责人过滤
            
        Returns:
            任务列表
        """
        tasks = self._load_tasks(team)
        result = list(tasks.values())
        
        if status:
            result = [t for t in result if t.status == status]
        
        if owner:
            result = [t for t in result if t.owner == owner]
        
        # 按优先级和创建时间排序
        result.sort(key=lambda t: (-t.priority, t.created_at))
        
        return result
    
    def update_status(
        self,
        team: str,
        task_id: str,
        status: str,
        result: str = ""
    ) -> Optional[Task]:
        """
        更新任务状态
        
        Args:
            team: 团队名
            task_id: 任务ID
            status: 新状态
            result: 执行结果
            
        Returns:
            更新后的任务
        """
        tasks = self._load_tasks(team)
        
        if task_id not in tasks:
            return None
        
        task = tasks[task_id]
        task.status = status
        task.updated_at = datetime.now().isoformat()
        
        if result:
            task.result = result
        
        if status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now().isoformat()
            # 自动解除依赖此任务的任务
            self._unblock_dependents(team, task_id)
        
        self._save_tasks(team, tasks)
        return task
    
    def _unblock_dependents(self, team: str, completed_task_id: str) -> List[str]:
        """
        解除依赖完成任务的任务
        
        Args:
            team: 团队名
            completed_task_id: 已完成的任务ID
            
        Returns:
            被解除阻塞的任务ID列表
        """
        tasks = self._load_tasks(team)
        unblocked = []
        
        for task in tasks.values():
            if completed_task_id in task.blocked_by:
                # 移除已完成的依赖
                task.blocked_by.remove(completed_task_id)
                
                # 如果没有其他依赖，解除阻塞
                if not task.blocked_by and task.status == TaskStatus.BLOCKED:
                    task.status = TaskStatus.PENDING
                    unblocked.append(task.id)
                    task.updated_at = datetime.now().isoformat()
        
        if unblocked:
            self._save_tasks(team, tasks)
        
        return unblocked
    
    def add_blocker(self, team: str, task_id: str, blocker_id: str) -> Optional[Task]:
        """
        添加任务依赖
        
        Args:
            team: 团队名
            task_id: 任务ID
            blocker_id: 被依赖的任务ID
            
        Returns:
            更新后的任务
        """
        tasks = self._load_tasks(team)
        
        if task_id not in tasks or blocker_id not in tasks:
            return None
        
        task = tasks[task_id]
        
        if blocker_id not in task.blocked_by:
            task.blocked_by.append(blocker_id)
            # 如果之前不是 blocked，改为 blocked
            if task.status != TaskStatus.BLOCKED and task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.BLOCKED
        
        task.updated_at = datetime.now().isoformat()
        self._save_tasks(team, tasks)
        
        return task
    
    def delete_task(self, team: str, task_id: str) -> bool:
        """删除任务"""
        tasks = self._load_tasks(team)
        
        if task_id not in tasks:
            return False
        
        del tasks[task_id]
        
        # 从其他任务的 blocked_by 中移除
        for task in tasks.values():
            if task_id in task.blocked_by:
                task.blocked_by.remove(task_id)
                if not task.blocked_by and task.status == TaskStatus.BLOCKED:
                    task.status = TaskStatus.PENDING
        
        self._save_tasks(team, tasks)
        return True
    
    def get_stats(self, team: str) -> Dict[str, int]:
        """获取任务统计"""
        tasks = self._load_tasks(team)
        
        stats = {
            "total": len(tasks),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "blocked": 0,
            "failed": 0,
        }
        
        for task in tasks.values():
            stats[task.status] = stats.get(task.status, 0) + 1
        
        return stats
    
    def cleanup(self, team: str) -> None:
        """清理团队任务"""
        import shutil
        tasks_dir = self.base_dir / team / "tasks"
        if tasks_dir.exists():
            shutil.rmtree(tasks_dir)


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    store = TaskStore("/tmp/.swarm-test")
    
    # 清理测试环境
    store.cleanup("test-team")
    
    # 创建任务链: T1 -> T2 -> T3
    t1 = store.create_task("test-team", "设计API", owner="architect", priority=10)
    print(f"创建任务: {t1.id} - {t1.title}")
    
    t2 = store.create_task(
        "test-team",
        "实现后端",
        owner="backend",
        blocked_by=[t1.id],
        priority=8
    )
    print(f"创建任务: {t2.id} - {t2.title} (blocked by {t2.blocked_by})")
    
    t3 = store.create_task(
        "test-team",
        "编写测试",
        owner="tester",
        blocked_by=[t2.id],
        priority=6
    )
    print(f"创建任务: {t3.id} - {t3.title} (blocked by {t3.blocked_by})")
    
    # 列出所有任务
    print("\n当前任务状态:")
    for task in store.list_tasks("test-team"):
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.FAILED: "❌",
        }
        print(f"  {status_icon.get(task.status, '❓')} {task.id} {task.title} ({task.owner})")
    
    # 完成 T1，自动解除 T2, T3 的阻塞
    print(f"\n完成 {t1.id}...")
    store.update_status("test-team", t1.id, TaskStatus.COMPLETED, "API设计完成，输出OpenAPI规范")
    
    # 再次查看状态
    print("\n更新后任务状态:")
    for task in store.list_tasks("test-team"):
        status_icon = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.BLOCKED: "🚫",
            TaskStatus.FAILED: "❌",
        }
        print(f"  {status_icon.get(task.status, '❓')} {task.id} {task.title} ({task.owner})")
    
    # 统计
    print(f"\n任务统计: {store.get_stats('test-team')}")
