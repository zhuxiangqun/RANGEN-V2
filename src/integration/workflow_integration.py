#!/usr/bin/env python3
"""
工作流集成模块
集成聊天触发和定时任务到系统工作流
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import schedule
import threading

from src.core.unified_workflow_facade import UnifiedWorkflowFacade, WorkflowMode, WorkflowConfig
from src.hook.transparency import HookTransparencySystem
from src.hook.hook_types import HookEventType, HookVisibilityLevel
from src.evolution.engine import EvolutionEngine
from src.hands.registry import HandRegistry
from src.services.logging_service import get_logger


logger = get_logger(__name__)


class TriggerType(Enum):
    """触发类型"""
    CHAT_MESSAGE = "chat_message"  # 聊天消息触发
    SCHEDULED_TASK = "scheduled_task"  # 定时任务触发
    EVENT_DRIVEN = "event_driven"  # 事件驱动触发
    API_CALL = "api_call"  # API调用触发
    MANUAL = "manual"  # 手动触发


class TaskPriority(Enum):
    """任务优先级"""
    LOW = "low"  # 低优先级
    MEDIUM = "medium"  # 中优先级
    HIGH = "high"  # 高优先级
    CRITICAL = "critical"  # 关键优先级


@dataclass
class WorkflowTask:
    """工作流任务"""
    task_id: str
    trigger_type: TriggerType
    query: str
    context: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    scheduled_time: Optional[datetime] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: str = "pending"  # pending, running, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowIntegration:
    """工作流集成管理器"""
    
    def __init__(self, system_name: str = "rangen_system"):
        self.system_name = system_name
        
        # 工作流门面
        self.workflow_facade = UnifiedWorkflowFacade()
        
        # Hook透明化系统
        self.hook_system = HookTransparencySystem(system_name)
        
        # 进化引擎
        self.evolution_engine = EvolutionEngine()  # 使用当前目录
        
        # Hands注册表
        self.hands_registry = HandRegistry()
        
        # 任务管理
        self.tasks: Dict[str, WorkflowTask] = {}
        self.task_queue = asyncio.Queue()
        self.max_concurrent_tasks = 5
        self.active_tasks: Dict[str, asyncio.Task] = {}
        
        # 定时任务调度器
        self.scheduler = schedule.Scheduler()
        self.scheduler_thread = None
        self.scheduler_running = False
        
        # 工作模式
        self.default_workflow_mode = WorkflowMode.STANDARD
        
        # 统计信息
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "active_tasks": 0,
            "scheduled_tasks": 0
        }
        
        logger.info(f"工作流集成管理器初始化: {system_name}")
    
    async def start(self):
        """启动工作流集成管理器"""
        try:
            # 启动Hook透明化系统
            await self.hook_system.recorder.initialize()
            
            # 启动任务处理器
            asyncio.create_task(self._task_processor())
            
            # 启动定时任务调度器
            self._start_scheduler_thread()
            
            # 启动进化引擎
            await self.evolution_engine.start()
            
            # 记录系统启动事件
            await self.hook_system.record_event(
                event_type=HookEventType.SYSTEM_STATE_CHANGE,
                source="workflow_integration",
                data={
                    "previous_state": "stopped",
                    "current_state": "running",
                    "change_type": "startup"
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            logger.info("工作流集成管理器启动完成")
            return True
            
        except Exception as e:
            logger.error(f"启动工作流集成管理器失败: {e}")
            return False
    
    async def stop(self):
        """停止工作流集成管理器"""
        try:
            # 停止所有活跃任务
            for task_id, task in self.active_tasks.items():
                if not task.done():
                    task.cancel()
            
            # 停止定时任务调度器
            self._stop_scheduler_thread()
            
            # 停止进化引擎
            await self.evolution_engine.stop()
            
            # 记录系统停止事件
            await self.hook_system.record_event(
                event_type=HookEventType.SYSTEM_STATE_CHANGE,
                source="workflow_integration",
                data={
                    "previous_state": "running",
                    "current_state": "stopped",
                    "change_type": "shutdown"
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            logger.info("工作流集成管理器停止完成")
            return True
            
        except Exception as e:
            logger.error(f"停止工作流集成管理器失败: {e}")
            return False
    
    async def trigger_chat_message(self, message: str, user_id: str = "anonymous", 
                                  context: Optional[Dict[str, Any]] = None) -> str:
        """触发聊天消息工作流"""
        try:
            # 创建任务
            task_id = f"chat_{uuid.uuid4().hex[:8]}"
            task_context = context or {}
            task_context.update({
                "user_id": user_id,
                "message_type": "chat",
                "timestamp": datetime.now().isoformat()
            })
            
            task = WorkflowTask(
                task_id=task_id,
                trigger_type=TriggerType.CHAT_MESSAGE,
                query=message,
                context=task_context,
                priority=TaskPriority.MEDIUM,
                metadata={
                    "user_id": user_id,
                    "message_length": len(message),
                    "trigger_source": "chat_interface"
                }
            )
            
            # 添加到任务队列
            await self._add_task(task)
            
            # 记录事件
            await self.hook_system.record_event(
                event_type=HookEventType.WORKFLOW_STEP,
                source="chat_trigger",
                data={
                    "task_id": task_id,
                    "message": message[:100] + "..." if len(message) > 100 else message,
                    "user_id": user_id,
                    "task_count": len(self.tasks)
                },
                visibility=HookVisibilityLevel.ENTREPRENEUR
            )
            
            logger.info(f"触发聊天消息工作流: {task_id} (用户: {user_id})")
            return task_id
            
        except Exception as e:
            logger.error(f"触发聊天消息工作流失败: {e}")
            await self.hook_system.record_error(
                error_type="chat_trigger_failed",
                error_message=str(e),
                context={"message": message, "user_id": user_id}
            )
            return ""
    
    async def schedule_task(self, query: str, schedule_time: datetime, 
                           context: Optional[Dict[str, Any]] = None,
                           task_name: Optional[str] = None) -> str:
        """安排定时任务"""
        try:
            # 创建任务
            task_id = f"scheduled_{uuid.uuid4().hex[:8]}"
            task_context = context or {}
            task_context.update({
                "task_type": "scheduled",
                "scheduled_time": schedule_time.isoformat(),
                "task_name": task_name or "unnamed_task"
            })
            
            task = WorkflowTask(
                task_id=task_id,
                trigger_type=TriggerType.SCHEDULED_TASK,
                query=query,
                context=task_context,
                priority=TaskPriority.MEDIUM,
                scheduled_time=schedule_time,
                metadata={
                    "task_name": task_name or "unnamed_task",
                    "schedule_type": "one_time",
                    "original_schedule_time": schedule_time.isoformat()
                }
            )
            
            # 添加到任务字典
            self.tasks[task_id] = task
            self.stats["scheduled_tasks"] += 1
            
            # 安排定时执行
            self._schedule_task_execution(task)
            
            # 记录事件
            await self.hook_system.record_event(
                event_type=HookEventType.WORKFLOW_STEP,
                source="scheduler",
                data={
                    "task_id": task_id,
                    "query": query[:50] + "..." if len(query) > 50 else query,
                    "scheduled_time": schedule_time.isoformat(),
                    "task_name": task_name
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            logger.info(f"安排定时任务: {task_id} (时间: {schedule_time}, 名称: {task_name or '未命名'})")
            return task_id
            
        except Exception as e:
            logger.error(f"安排定时任务失败: {e}")
            await self.hook_system.record_error(
                error_type="schedule_task_failed",
                error_message=str(e),
                context={"query": query, "schedule_time": schedule_time.isoformat()}
            )
            return ""
    
    async def schedule_recurring_task(self, query: str, interval_seconds: int,
                                     context: Optional[Dict[str, Any]] = None,
                                     task_name: Optional[str] = None,
                                     start_immediately: bool = False) -> str:
        """安排重复定时任务"""
        try:
            task_id = f"recurring_{uuid.uuid4().hex[:8]}"
            task_context = context or {}
            task_context.update({
                "task_type": "recurring",
                "interval_seconds": interval_seconds,
                "task_name": task_name or "unnamed_recurring_task"
            })
            
            task = WorkflowTask(
                task_id=task_id,
                trigger_type=TriggerType.SCHEDULED_TASK,
                query=query,
                context=task_context,
                priority=TaskPriority.LOW,
                metadata={
                    "task_name": task_name or "unnamed_recurring_task",
                    "schedule_type": "recurring",
                    "interval_seconds": interval_seconds,
                    "start_immediately": start_immediately
                }
            )
            
            self.tasks[task_id] = task
            self.stats["scheduled_tasks"] += 1
            
            # 安排重复执行
            self._schedule_recurring_task(task, interval_seconds, start_immediately)
            
            # 记录事件
            await self.hook_system.record_event(
                event_type=HookEventType.WORKFLOW_STEP,
                source="scheduler",
                data={
                    "task_id": task_id,
                    "query": query[:50] + "..." if len(query) > 50 else query,
                    "interval_seconds": interval_seconds,
                    "task_name": task_name,
                    "schedule_type": "recurring"
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            logger.info(f"安排重复定时任务: {task_id} (间隔: {interval_seconds}秒, 名称: {task_name or '未命名'})")
            return task_id
            
        except Exception as e:
            logger.error(f"安排重复定时任务失败: {e}")
            await self.hook_system.record_error(
                error_type="schedule_recurring_task_failed",
                error_message=str(e),
                context={"query": query, "interval_seconds": interval_seconds}
            )
            return ""
    
    async def execute_task_immediately(self, query: str, context: Optional[Dict[str, Any]] = None,
                                      priority: TaskPriority = TaskPriority.MEDIUM) -> str:
        """立即执行任务"""
        try:
            task_id = f"immediate_{uuid.uuid4().hex[:8]}"
            task_context = context or {}
            task_context.update({
                "task_type": "immediate",
                "timestamp": datetime.now().isoformat()
            })
            
            task = WorkflowTask(
                task_id=task_id,
                trigger_type=TriggerType.MANUAL,
                query=query,
                context=task_context,
                priority=priority,
                metadata={
                    "execution_type": "immediate",
                    "priority": priority.value
                }
            )
            
            # 立即执行（高优先级直接添加到队列前端）
            await self._add_task(task, high_priority=(priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]))
            
            # 记录事件
            await self.hook_system.record_event(
                event_type=HookEventType.WORKFLOW_STEP,
                source="manual_trigger",
                data={
                    "task_id": task_id,
                    "query": query[:50] + "..." if len(query) > 50 else query,
                    "priority": priority.value,
                    "execution_type": "immediate"
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            logger.info(f"立即执行任务: {task_id} (优先级: {priority.value})")
            return task_id
            
        except Exception as e:
            logger.error(f"立即执行任务失败: {e}")
            await self.hook_system.record_error(
                error_type="immediate_task_failed",
                error_message=str(e),
                context={"query": query, "priority": priority.value}
            )
            return ""
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "trigger_type": task.trigger_type.value,
            "query": task.query,
            "priority": task.priority.value,
            "status": task.status,
            "created_at": task.created_at,
            "scheduled_time": task.scheduled_time.isoformat() if task.scheduled_time else None,
            "result": task.result,
            "error": task.error,
            "metadata": task.metadata
        }
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        # 如果任务正在运行，取消它
        if task_id in self.active_tasks:
            active_task = self.active_tasks[task_id]
            if not active_task.done():
                active_task.cancel()
                await asyncio.sleep(0.1)  # 给取消操作一点时间
        
        # 更新任务状态
        task.status = "cancelled"
        
        # 从调度器移除（如果是定时任务）
        if task.trigger_type == TriggerType.SCHEDULED_TASK:
            self._unschedule_task(task_id)
        
        # 记录事件
        await self.hook_system.record_event(
            event_type=HookEventType.WORKFLOW_STEP,
            source="task_manager",
            data={
                "task_id": task_id,
                "status": "cancelled",
                "trigger_type": task.trigger_type.value
            },
            visibility=HookVisibilityLevel.DEVELOPER
        )
        
        logger.info(f"任务已取消: {task_id}")
        return True
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        active_task_details = []
        for task_id, task in self.tasks.items():
            if task.status == "running":
                active_task_details.append({
                    "task_id": task_id,
                    "query": task.query[:50] + "..." if len(task.query) > 50 else task.query,
                    "trigger_type": task.trigger_type.value,
                    "created_at": task.created_at
                })
        
        return {
            "system_name": self.system_name,
            "timestamp": datetime.now().isoformat(),
            "task_statistics": {
                "total_tasks": self.stats["total_tasks"],
                "completed_tasks": self.stats["completed_tasks"],
                "failed_tasks": self.stats["failed_tasks"],
                "active_tasks": self.stats["active_tasks"],
                "scheduled_tasks": self.stats["scheduled_tasks"],
                "pending_tasks": self.task_queue.qsize()
            },
            "active_tasks": active_task_details,
            "workflow_mode": self.default_workflow_mode.value,
            "scheduler_status": "running" if self.scheduler_running else "stopped",
            "hook_system_status": "enabled",
            "evolution_engine_status": "enabled"
        }
    
    # 私有方法
    async def _add_task(self, task: WorkflowTask, high_priority: bool = False):
        """添加任务到队列"""
        self.tasks[task.task_id] = task
        self.stats["total_tasks"] += 1
        
        if high_priority:
            # 高优先级任务添加到队列前端
            await self.task_queue.put((task.task_id, 0))  # 优先级0（最高）
        else:
            # 普通优先级
            priority_value = {
                TaskPriority.LOW: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.HIGH: 1,
                TaskPriority.CRITICAL: 0
            }.get(task.priority, 2)
            
            await self.task_queue.put((task.task_id, priority_value))
        
        logger.debug(f"任务添加到队列: {task.task_id} (优先级: {task.priority.value})")
    
    async def _task_processor(self):
        """任务处理器"""
        logger.info("任务处理器启动")
        
        while True:
            try:
                # 获取任务（带优先级）
                task_id, priority = await self.task_queue.get()
                
                task = self.tasks.get(task_id)
                if not task:
                    self.task_queue.task_done()
                    continue
                
                # 检查任务是否已取消
                if task.status == "cancelled":
                    self.task_queue.task_done()
                    continue
                
                # 更新任务状态
                task.status = "running"
                self.stats["active_tasks"] += 1
                
                # 创建异步任务
                task_coroutine = self._execute_workflow_task(task)
                task_future = asyncio.create_task(task_coroutine)
                self.active_tasks[task_id] = task_future
                
                # 等待任务完成
                try:
                    await task_future
                except asyncio.CancelledError:
                    logger.info(f"任务被取消: {task_id}")
                    task.status = "cancelled"
                except Exception as e:
                    logger.error(f"任务执行失败: {task_id}, 错误: {e}")
                    task.status = "failed"
                    task.error = str(e)
                    
                    # 记录错误事件
                    await self.hook_system.record_error(
                        error_type="task_execution_failed",
                        error_message=str(e),
                        context={
                            "task_id": task_id,
                            "query": task.query,
                            "trigger_type": task.trigger_type.value
                        }
                    )
                
                # 清理
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
                
                self.stats["active_tasks"] -= 1
                
                # 更新统计
                if task.status == "completed":
                    self.stats["completed_tasks"] += 1
                elif task.status == "failed":
                    self.stats["failed_tasks"] += 1
                
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                logger.info("任务处理器被取消")
                break
            except Exception as e:
                logger.error(f"任务处理器错误: {e}")
                await asyncio.sleep(1)  # 避免错误循环
    
    async def _execute_workflow_task(self, task: WorkflowTask):
        """执行工作流任务"""
        try:
            # 记录任务开始
            await self.hook_system.record_event(
                event_type=HookEventType.WORKFLOW_STEP,
                source="task_executor",
                data={
                    "task_id": task.task_id,
                    "query": task.query,
                    "trigger_type": task.trigger_type.value,
                    "priority": task.priority.value,
                    "status": "started"
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            # 执行工作流
            start_time = time.time()
            result = await self.workflow_facade.execute(
                query=task.query,
                context=task.context,
                mode=self.default_workflow_mode
            )
            execution_time = time.time() - start_time
            
            # 更新任务结果
            task.result = result
            task.status = "completed"
            task.metadata["execution_time"] = execution_time
            task.metadata["completed_at"] = datetime.now().isoformat()
            
            # 记录任务完成
            await self.hook_system.record_event(
                event_type=HookEventType.WORKFLOW_STEP,
                source="task_executor",
                data={
                    "task_id": task.task_id,
                    "execution_time": execution_time,
                    "status": "completed",
                    "result_summary": self._summarize_result(result)
                },
                visibility=HookVisibilityLevel.DEVELOPER
            )
            
            # 如果是聊天消息，记录到企业家可见级别
            if task.trigger_type == TriggerType.CHAT_MESSAGE:
                await self.hook_system.record_event(
                    event_type=HookEventType.AGENT_DECISION,
                    source="workflow_execution",
                    data={
                        "agent": "workflow_integration",
                        "decision": {
                            "type": "chat_response",
                            "query": task.query,
                            "response_summary": self._summarize_result(result),
                            "execution_time": execution_time
                        },
                        "context": task.context
                    },
                    visibility=HookVisibilityLevel.ENTREPRENEUR
                )
            
            logger.info(f"任务执行完成: {task.task_id} (用时: {execution_time:.2f}秒)")
            
        except Exception as e:
            logger.error(f"执行工作流任务失败: {task.task_id}, 错误: {e}")
            raise
    
    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """摘要结果"""
        if not result:
            return {"status": "empty"}
        
        summary = {
            "has_result": True,
            "status": result.get("status", "unknown")
        }
        
        # 提取关键信息
        if "answer" in result:
            answer = result["answer"]
            summary["answer_preview"] = str(answer)[:100] + "..." if len(str(answer)) > 100 else str(answer)
        
        if "evidence" in result:
            evidence = result["evidence"]
            if isinstance(evidence, list):
                summary["evidence_count"] = len(evidence)
        
        if "confidence" in result:
            summary["confidence"] = result["confidence"]
        
        return summary
    
    def _start_scheduler_thread(self):
        """启动定时任务调度器线程"""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            return
        
        self.scheduler_running = True
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_worker,
            daemon=True,
            name="workflow_scheduler"
        )
        self.scheduler_thread.start()
        logger.info("定时任务调度器线程启动")
    
    def _stop_scheduler_thread(self):
        """停止定时任务调度器线程"""
        self.scheduler_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
            logger.info("定时任务调度器线程停止")
    
    def _scheduler_worker(self):
        """定时任务调度器工作线程"""
        logger.info("定时任务调度器工作线程开始运行")
        
        while self.scheduler_running:
            try:
                # 运行待处理的定时任务
                self.scheduler.run_pending()
                time.sleep(1)  # 每秒检查一次
            except Exception as e:
                logger.error(f"定时任务调度器错误: {e}")
                time.sleep(5)  # 错误后等待更长时间
        
        logger.info("定时任务调度器工作线程停止")
    
    def _schedule_task_execution(self, task: WorkflowTask):
        """安排任务执行"""
        if not task.scheduled_time:
            return
        
        # 计算延迟时间（秒）
        now = datetime.now()
        delay_seconds = (task.scheduled_time - now).total_seconds()
        
        if delay_seconds <= 0:
            # 如果已经过了预定时间，立即执行
            asyncio.create_task(self._execute_scheduled_task(task))
            return
        
        # 安排定时执行
        def schedule_wrapper():
            asyncio.create_task(self._execute_scheduled_task(task))
        
        # 使用schedule库安排任务
        self.scheduler.every(delay_seconds).seconds.do(schedule_wrapper)
        
        logger.debug(f"安排任务执行: {task.task_id} (延迟: {delay_seconds:.1f}秒)")
    
    def _schedule_recurring_task(self, task: WorkflowTask, interval_seconds: int, start_immediately: bool = False):
        """安排重复任务执行"""
        def schedule_wrapper():
            asyncio.create_task(self._execute_scheduled_task(task))
        
        # 安排重复执行
        job = self.scheduler.every(interval_seconds).seconds.do(schedule_wrapper)
        
        # 存储job引用以便取消
        task.metadata["schedule_job"] = job
        
        if start_immediately:
            # 立即执行一次
            asyncio.create_task(self._execute_scheduled_task(task))
        
        logger.debug(f"安排重复任务执行: {task.task_id} (间隔: {interval_seconds}秒)")
    
    async def _execute_scheduled_task(self, task: WorkflowTask):
        """执行定时任务"""
        try:
            logger.info(f"执行定时任务: {task.task_id}")
            
            # 添加到任务队列
            await self._add_task(task)
            
        except Exception as e:
            logger.error(f"执行定时任务失败: {task.task_id}, 错误: {e}")
    
    def _unschedule_task(self, task_id: str):
        """取消定时任务调度"""
        task = self.tasks.get(task_id)
        if not task:
            return
        
        # 如果是重复任务，取消调度
        if "schedule_job" in task.metadata:
            job = task.metadata["schedule_job"]
            self.scheduler.cancel_job(job)
            logger.debug(f"取消定时任务调度: {task_id}")
    
    def __str__(self):
        return f"WorkflowIntegration({self.system_name})"


# 全局单例
_workflow_integration_instance: Optional[WorkflowIntegration] = None


def get_workflow_integration(system_name: str = "rangen_system") -> WorkflowIntegration:
    """获取工作流集成管理器单例"""
    global _workflow_integration_instance
    
    if _workflow_integration_instance is None:
        _workflow_integration_instance = WorkflowIntegration(system_name)
    
    return _workflow_integration_instance


async def initialize_workflow_integration(system_name: str = "rangen_system") -> bool:
    """初始化工作流集成管理器"""
    integration = get_workflow_integration(system_name)
    return await integration.start()