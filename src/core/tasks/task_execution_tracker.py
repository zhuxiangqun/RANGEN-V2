#!/usr/bin/env python3
"""
Task Execution Tracker - 任务执行追踪器
追踪任务执行进度，支持暂停、恢复、检查点
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import uuid


class ExecutionStatus(Enum):
    """执行状态"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Checkpoint:
    """检查点"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    state: Dict[str, Any] = field(default_factory=dict)
    completed_tasks: List[str] = field(default_factory=list)
    current_task_id: Optional[str] = None


@dataclass
class TaskProgress:
    """任务进度"""
    task_id: str
    task_name: str
    status: ExecutionStatus = ExecutionStatus.NOT_STARTED
    progress: float = 0.0  # 0-100
    message: str = ""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    result: Any = None
    error: Optional[str] = None


class TaskExecutionTracker:
    """
    任务执行追踪器
    
    功能：
    1. 追踪每个子任务的进度
    2. 支持检查点创建和恢复
    3. 支持任务暂停和继续
    4. 提供执行统计和分析
    """
    
    def __init__(self):
        self.execution_id: str = str(uuid.uuid4())[:8]
        self.status: ExecutionStatus = ExecutionStatus.NOT_STARTED
        self.progress: Dict[str, TaskProgress] = {}
        self.checkpoints: List[Checkpoint] = []
        self.start_time: Optional[str] = None
        self.end_time: Optional[str] = None
        self.listeners: List[Callable] = []
    
    def start_execution(self):
        """开始执行"""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now().isoformat()
        self._notify_listeners("start", {"execution_id": self.execution_id})
    
    def register_task(self, task_id: str, task_name: str):
        """注册任务"""
        self.progress[task_id] = TaskProgress(
            task_id=task_id,
            task_name=task_name
        )
    
    def update_progress(
        self, 
        task_id: str, 
        progress: float, 
        message: str = "",
        status: Optional[ExecutionStatus] = None
    ):
        """更新进度"""
        if task_id in self.progress:
            self.progress[task_id].progress = progress
            if message:
                self.progress[task_id].message = message
            if status:
                self.progress[task_id].status = status
            
            self._notify_listeners("progress", {
                "task_id": task_id,
                "progress": progress,
                "message": message
            })
    
    def complete_task(
        self, 
        task_id: str, 
        result: Any = None, 
        error: Optional[str] = None
    ):
        """完成任务"""
        if task_id in self.progress:
            self.progress[task_id].status = ExecutionStatus.COMPLETED
            self.progress[task_id].progress = 100.0
            self.progress[task_id].result = result
            self.progress[task_id].end_time = datetime.now().isoformat()
            
            if error:
                self.progress[task_id].error = error
            
            self._notify_listeners("task_complete", {
                "task_id": task_id,
                "result": result
            })
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        if task_id in self.progress:
            self.progress[task_id].status = ExecutionStatus.FAILED
            self.progress[task_id].error = error
            self.progress[task_id].end_time = datetime.now().isoformat()
            
            self._notify_listeners("task_fail", {
                "task_id": task_id,
                "error": error
            })
    
    def create_checkpoint(self, name: str) -> Checkpoint:
        """创建检查点"""
        state = {
            "progress": {
                task_id: {
                    "status": p.status.value,
                    "progress": p.progress,
                    "result": p.result
                }
                for task_id, p in self.progress.items()
            },
            "execution_status": self.status.value
        }
        
        completed = [
            task_id for task_id, p in self.progress.items()
            if p.status == ExecutionStatus.COMPLETED
        ]
        
        current = None
        for task_id, p in self.progress.items():
            if p.status == ExecutionStatus.RUNNING:
                current = task_id
                break
        
        checkpoint = Checkpoint(
            name=name,
            state=state,
            completed_tasks=completed,
            current_task_id=current
        )
        
        self.checkpoints.append(checkpoint)
        self._notify_listeners("checkpoint", {"checkpoint_id": checkpoint.id})
        
        return checkpoint
    
    def restore_from_checkpoint(self, checkpoint_id: str) -> bool:
        """从检查点恢复"""
        checkpoint = self.get_checkpoint(checkpoint_id)
        if not checkpoint:
            return False
        
        # 恢复状态
        for task_id, task_state in checkpoint.state.get("progress", {}).items():
            if task_id in self.progress:
                self.progress[task_id].status = ExecutionStatus(
                    task_state.get("status", "not_started")
                )
                self.progress[task_id].progress = task_state.get("progress", 0.0)
                self.progress[task_id].result = task_state.get("result")
        
        self.status = ExecutionStatus.RUNNING
        self._notify_listeners("restore", {"checkpoint_id": checkpoint_id})
        
        return True
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """获取检查点"""
        for cp in self.checkpoints:
            if cp.id == checkpoint_id:
                return cp
        return None
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """获取最新检查点"""
        return self.checkpoints[-1] if self.checkpoints else None
    
    def pause_execution(self):
        """暂停执行"""
        if self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.PAUSED
            self._notify_listeners("pause", {})
    
    def resume_execution(self):
        """继续执行"""
        if self.status == ExecutionStatus.PAUSED:
            self.status = ExecutionStatus.RUNNING
            self._notify_listeners("resume", {})
    
    def cancel_execution(self):
        """取消执行"""
        self.status = ExecutionStatus.CANCELLED
        self.end_time = datetime.now().isoformat()
        self._notify_listeners("cancel", {})
    
    def complete_execution(self):
        """完成执行"""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = datetime.now().isoformat()
        self._notify_listeners("complete", {})
    
    def get_overall_progress(self) -> float:
        """获取整体进度"""
        if not self.progress:
            return 0.0
        
        total = sum(p.progress for p in self.progress.values())
        return total / len(self.progress)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        completed = sum(
            1 for p in self.progress.values() 
            if p.status == ExecutionStatus.COMPLETED
        )
        failed = sum(
            1 for p in self.progress.values() 
            if p.status == ExecutionStatus.FAILED
        )
        running = sum(
            1 for p in self.progress.values() 
            if p.status == ExecutionStatus.RUNNING
        )
        
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "total_tasks": len(self.progress),
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": running,
            "overall_progress": self.get_overall_progress(),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "checkpoints": len(self.checkpoints)
        }
    
    def add_listener(self, listener: Callable):
        """添加监听器"""
        self.listeners.append(listener)
    
    def _notify_listeners(self, event: str, data: Dict[str, Any]):
        """通知监听器"""
        for listener in self.listeners:
            try:
                listener(event, data)
            except Exception:
                pass


# 便捷函数
def create_tracker() -> TaskExecutionTracker:
    """创建任务追踪器"""
    return TaskExecutionTracker()
