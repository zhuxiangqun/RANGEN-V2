"""
Schedule & Reminders - 日程提醒

提供定时任务和提醒功能
"""

import asyncio
import logging
import os
import json
from typing import Optional, Dict, Any, List, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from uuid import uuid4
import uuid

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ReminderStatus(Enum):
    """提醒状态"""
    PENDING = "pending"      # 待执行
    EXECUTING = "executing" # 执行中
    COMPLETED = "completed"  # 已完成
    CANCELLED = "cancelled"  # 已取消
    FAILED = "failed"        # 失败


class RecurrenceType(Enum):
    """重复类型"""
    NONE = "none"           # 不重复
    DAILY = "daily"        # 每天
    WEEKLY = "weekly"       # 每周
    MONTHLY = "monthly"     # 每月
    CUSTOM = "custom"        # 自定义


@dataclass
class Reminder:
    """提醒"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    message: str = ""
    scheduled_time: datetime = field(default_factory=datetime.now)
    recurrence: RecurrenceType = RecurrenceType.NONE
    status: ReminderStatus = ReminderStatus.PENDING
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    user_id: str = ""
    channel: str = ""  # 发送渠道
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 重复参数 (自定义)
    interval_minutes: int = 0  # 自定义间隔 (分钟)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "scheduled_time": self.scheduled_time.isoformat(),
            "recurrence": self.recurrence.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "channel": self.channel
        }


@dataclass
class ScheduledTask:
    """定时任务"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func_name: str = ""  # 要执行的函数名
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    schedule_type: str = "interval"  # interval, cron
    interval_seconds: int = 0
    cron_expr: str = ""
    enabled: bool = True
    
    # 执行统计
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0


class ScheduleManager:
    """
    日程提醒管理器
    
    功能:
    - 创建一次性提醒
    - 创建重复提醒
    - 定时执行任务
    - 取消提醒
    - 列出提醒
    """
    
    def __init__(self):
        self.reminders: Dict[str, Reminder] = {}
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        self._callback: Optional[Callable] = None
    
    def set_callback(self, callback: Callable[[Reminder], Awaitable[None]]):
        """
        设置提醒回调
        
        当提醒触发时调用
        """
        self._callback = callback
    
    async def start(self):
        """启动调度器"""
        if self._running:
            return
        
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        logger.info("Schedule manager started")
    
    async def stop(self):
        """停止调度器"""
        self._running = False
        
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Schedule manager stopped")
    
    # ==================== 提醒管理 ====================
    
    async def create_reminder(
        self,
        title: str,
        message: str,
        scheduled_time: datetime,
        user_id: str = "",
        channel: str = "default",
        recurrence: RecurrenceType = RecurrenceType.NONE,
        **metadata
    ) -> Reminder:
        """
        创建提醒
        
        Args:
            title: 标题
            message: 消息内容
            scheduled_time: 提醒时间
            user_id: 用户ID
            channel: 发送渠道
            recurrence: 重复类型
            **metadata: 额外参数
            
        Returns:
            Reminder: 创建的提醒
        """
        reminder = Reminder(
            title=title,
            message=message,
            scheduled_time=scheduled_time,
            user_id=user_id,
            channel=channel,
            recurrence=recurrence,
            metadata=metadata
        )
        
        self.reminders[reminder.id] = reminder
        
        logger.info(f"Created reminder: {reminder.id} at {scheduled_time}")
        
        return reminder
    
    async def create_reminder_in(
        self,
        title: str,
        message: str,
        minutes: int,
        user_id: str = "",
        channel: str = "default"
    ) -> Reminder:
        """创建多久后的提醒"""
        scheduled_time = datetime.now() + timedelta(minutes=minutes)
        return await self.create_reminder(
            title=title,
            message=message,
            scheduled_time=scheduled_time,
            user_id=user_id,
            channel=channel
        )
    
    async def cancel_reminder(self, reminder_id: str) -> str:
        """取消提醒"""
        if reminder_id not in self.reminders:
            return f"Reminder not found: {reminder_id}"
        
        reminder = self.reminders[reminder_id]
        reminder.status = ReminderStatus.CANCELLED
        
        logger.info(f"Cancelled reminder: {reminder_id}")
        
        return f"Cancelled: {reminder.title}"
    
    async def delete_reminder(self, reminder_id: str) -> str:
        """删除提醒"""
        if reminder_id in self.reminders:
            del self.reminders[reminder_id]
            return f"Deleted reminder: {reminder_id}"
        
        return f"Reminder not found: {reminder_id}"
    
    async def get_reminder(self, reminder_id: str) -> Optional[Reminder]:
        """获取提醒"""
        return self.reminders.get(reminder_id)
    
    async def list_reminders(
        self,
        user_id: Optional[str] = None,
        status: Optional[ReminderStatus] = None
    ) -> List[Reminder]:
        """列出提醒"""
        reminders = list(self.reminders.values())
        
        if user_id:
            reminders = [r for r in reminders if r.user_id == user_id]
        
        if status:
            reminders = [r for r in reminders if r.status == status]
        
        # 按时间排序
        reminders.sort(key=lambda r: r.scheduled_time)
        
        return reminders
    
    async def get_pending_reminders(self) -> List[Reminder]:
        """获取待执行的提醒"""
        now = datetime.now()
        
        pending = [
            r for r in self.reminders.values()
            if r.status == ReminderStatus.PENDING
            and r.scheduled_time <= now
        ]
        
        return pending
    
    # ==================== 定时任务 ====================
    
    async def create_task(
        self,
        name: str,
        func_name: str,
        interval_seconds: int = 0,
        **kwargs
    ) -> ScheduledTask:
        """创建定时任务"""
        task = ScheduledTask(
            name=name,
            func_name=func_name,
            interval_seconds=interval_seconds,
            kwargs=kwargs,
            next_run=datetime.now() + timedelta(seconds=interval_seconds)
        )
        
        self.tasks[task.id] = task
        
        logger.info(f"Created task: {task.name} ({task.id})")
        
        return task
    
    async def enable_task(self, task_id: str) -> str:
        """启用任务"""
        if task_id not in self.tasks:
            return f"Task not found: {task_id}"
        
        self.tasks[task_id].enabled = True
        return f"Task enabled: {self.tasks[task_id].name}"
    
    async def disable_task(self, task_id: str) -> str:
        """禁用任务"""
        if task_id not in self.tasks:
            return f"Task not found: {task_id}"
        
        self.tasks[task_id].enabled = False
        return f"Task disabled: {self.tasks[task_id].name}"
    
    # ==================== 内部方法 ====================
    
    async def _run_scheduler(self):
        """调度器循环"""
        while self._running:
            try:
                # 1. 检查提醒
                pending = await self.get_pending_reminders()
                
                for reminder in pending:
                    await self._execute_reminder(reminder)
                
                # 2. 检查定时任务
                now = datetime.now()
                
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    if task.next_run and now >= task.next_run:
                        await self._execute_task(task)
                
                # 等待
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
    
    async def _execute_reminder(self, reminder: Reminder):
        """执行提醒"""
        reminder.status = ReminderStatus.EXECUTING
        
        logger.info(f"Executing reminder: {reminder.title}")
        
        try:
            # 调用回调
            if self._callback:
                await self._callback(reminder)
            
            reminder.status = ReminderStatus.COMPLETED
            
            # 处理重复
            if reminder.recurrence != RecurrenceType.NONE:
                next_time = self._get_next_time(reminder)
                if next_time:
                    # 创建新的提醒
                    new_reminder = Reminder(
                        title=reminder.title,
                        message=reminder.message,
                        scheduled_time=next_time,
                        user_id=reminder.user_id,
                        channel=reminder.channel,
                        recurrence=reminder.recurrence
                    )
                    self.reminders[new_reminder.id] = new_reminder
            else:
                # 删除已完成的非重复提醒
                # await self.delete_reminder(reminder.id)
                pass
            
        except Exception as e:
            reminder.status = ReminderStatus.FAILED
            logger.error(f"Reminder execution error: {e}")
    
    async def _execute_task(self, task: ScheduledTask):
        """执行定时任务"""
        logger.info(f"Executing task: {task.name}")
        
        try:
            # TODO: 根据 func_name 执行实际函数
            # 这里需要注册函数映射
            
            task.last_run = datetime.now()
            task.run_count += 1
            
            if task.interval_seconds > 0:
                task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
    
    def _get_next_time(self, reminder: Reminder) -> Optional[datetime]:
        """计算下次执行时间"""
        now = datetime.now()
        
        if reminder.recurrence == RecurrenceType.DAILY:
            return reminder.scheduled_time + timedelta(days=1)
        elif reminder.recurrence == RecurrenceType.WEEKLY:
            return reminder.scheduled_time + timedelta(weeks=1)
        elif reminder.recurrence == RecurrenceType.MONTHLY:
            # 简单处理: 加30天
            return reminder.scheduled_time + timedelta(days=30)
        
        return None
    
    # ==================== 便捷方法 ====================
    
    async def snooze(self, reminder_id: str, minutes: int = 10) -> str:
        """ snooze 提醒"""
        reminder = await self.get_reminder(reminder_id)
        
        if not reminder:
            return f"Reminder not found: {reminder_id}"
        
        reminder.scheduled_time = datetime.now() + timedelta(minutes=minutes)
        reminder.status = ReminderStatus.PENDING
        
        return f"Snoozed for {minutes} minutes"
    
    async def clear_completed(self) -> str:
        """清除已完成的提醒"""
        completed_ids = [
            r.id for r in self.reminders.values()
            if r.status == ReminderStatus.COMPLETED
        ]
        
        for id in completed_ids:
            del self.reminders[id]
        
        return f"Cleared {len(completed_ids)} completed reminders"


# ==================== 便捷函数 ====================

def create_schedule_manager() -> ScheduleManager:
    """创建日程管理器"""
    return ScheduleManager()
