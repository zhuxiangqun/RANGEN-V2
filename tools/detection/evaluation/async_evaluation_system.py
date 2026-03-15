#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步评估系统
提供异步评估功能和性能监控
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.unified_centers import get_unified_center

# 初始化日志
logger = logging.getLogger(__name__)

class EvaluationStatus(Enum):
    """评估状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class EvaluationResult(Enum):
    """评估结果"""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"

@dataclass
class EvaluationTask:
    """评估任务"""
    task_id: str
    name: str
    description: str
    status: EvaluationStatus
    result: Optional[EvaluationResult] = None
    score: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: float = 0.0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EvaluationReport:
    """评估报告"""
    report_id: str
    timestamp: datetime
    total_tasks: int
    completed_tasks: int
    passed_tasks: int
    failed_tasks: int
    overall_score: float
    duration: float
    tasks: List[EvaluationTask] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)

class BaseInterface:
    """统一接口基类"""
    
    def __init__(self) -> None:
        self.initialized = True
    
    def validate_input(self, data: Any) -> bool:
        """验证输入数据"""
        return data is not None
    
    def process_data(self, data: Any) -> Any:
        """处理数据"""
        return data

class AsyncEvaluationSystem(BaseInterface):
    """异步评估系统"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化异步评估系统"""
        super().__init__()
        self.config = config or {}
        self.tasks: Dict[str, EvaluationTask] = {}
        self.reports: List[EvaluationReport] = []
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # 从配置系统获取设置
        smart_config = get_unified_center('get_smart_config')
        if smart_config and hasattr(smart_config, 'get_config'):
            self.max_concurrent_tasks = smart_config.get_config('evaluation_max_concurrent_tasks', self.config, 5)
            self.task_timeout = smart_config.get_config('evaluation_task_timeout', self.config, 300)
            self.retry_attempts = smart_config.get_config('evaluation_retry_attempts', self.config, 3)
        else:
            self.max_concurrent_tasks = 5
            self.task_timeout = 300
            self.retry_attempts = 3
        
        logger.info("异步评估系统初始化完成")
    
    async def create_task(self, name: str, description: str, 
                         evaluator_func: callable, **kwargs) -> str:
        """创建评估任务"""
        task_id = f"task_{int(time.time())}_{len(self.tasks)}"
        
        task = EvaluationTask(
            task_id=task_id,
            name=name,
            description=description,
            status=EvaluationStatus.PENDING,
            metadata=kwargs
        )
        
        self.tasks[task_id] = task
        logger.info(f"创建评估任务: {name} (ID: {task_id})")
        
        return task_id
    
    async def start_task(self, task_id: str) -> bool:
        """启动评估任务"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            logger.warning(f"达到最大并发任务数: {self.max_concurrent_tasks}")
            return False
        
        task = self.tasks[task_id]
        task.status = EvaluationStatus.RUNNING
        task.start_time = datetime.now()
        
        # 创建异步任务
        async_task = asyncio.create_task(
            self._execute_task(task_id)
        )
        self.running_tasks[task_id] = async_task
        
        logger.info(f"启动评估任务: {task.name} (ID: {task_id})")
        return True
    
    async def _execute_task(self, task_id: str) -> None:
        """执行评估任务"""
        task = self.tasks[task_id]
        
        try:
            # 获取评估函数
            evaluator_func = task.metadata.get('evaluator_func')
            if not evaluator_func:
                raise ValueError("评估函数未定义")
            
            # 执行评估
            result = await asyncio.wait_for(
                evaluator_func(**task.metadata),
                timeout=self.task_timeout
            )
            
            # 处理结果
            if isinstance(result, dict):
                task.result = EvaluationResult(result.get('result', 'pass'))
                task.score = result.get('score', 0.0)
                task.metadata.update(result.get('metadata', {}))
            else:
                task.result = EvaluationResult.PASS
                task.score = 1.0 if result else 0.0
            
            task.status = EvaluationStatus.COMPLETED
            
        except asyncio.TimeoutError:
            task.status = EvaluationStatus.FAILED
            task.result = EvaluationResult.FAIL
            task.error_message = f"任务超时 ({self.task_timeout}秒)"
            logger.error(f"任务超时: {task.name} (ID: {task_id})")
            
        except Exception as e:
            task.status = EvaluationStatus.FAILED
            task.result = EvaluationResult.FAIL
            task.error_message = str(e)
            logger.error(f"任务执行失败: {task.name} (ID: {task_id}) - {e}")
        
        finally:
            # 计算持续时间
            task.end_time = datetime.now()
            if task.start_time:
                task.duration = (task.end_time - task.start_time).total_seconds()
            
            # 从运行任务中移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            logger.info(f"任务完成: {task.name} (ID: {task_id}) - 状态: {task.status.value}")
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消评估任务"""
        if task_id not in self.tasks:
            logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        
        if task.status == EvaluationStatus.RUNNING and task_id in self.running_tasks:
            # 取消运行中的任务
            async_task = self.running_tasks[task_id]
            async_task.cancel()
            del self.running_tasks[task_id]
        
        task.status = EvaluationStatus.CANCELLED
        task.end_time = datetime.now()
        if task.start_time:
            task.duration = (task.end_time - task.start_time).total_seconds()
        
        logger.info(f"取消任务: {task.name} (ID: {task_id})")
        return True
    
    async def wait_for_task(self, task_id: str, timeout: Optional[float] = None) -> EvaluationTask:
        """等待任务完成"""
        if task_id not in self.tasks:
            raise ValueError(f"任务不存在: {task_id}")
        
        task = self.tasks[task_id]
        
        if task.status == EvaluationStatus.RUNNING and task_id in self.running_tasks:
            try:
                await asyncio.wait_for(
                    self.running_tasks[task_id],
                    timeout=timeout or self.task_timeout
                )
            except asyncio.TimeoutError:
                logger.warning(f"等待任务超时: {task.name} (ID: {task_id})")
        
        return task
    
    async def wait_for_all_tasks(self, timeout: Optional[float] = None) -> List[EvaluationTask]:
        """等待所有任务完成"""
        if not self.running_tasks:
            return list(self.tasks.values())
        
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.running_tasks.values(), return_exceptions=True),
                timeout=timeout or self.task_timeout
            )
        except asyncio.TimeoutError:
            logger.warning("等待所有任务超时")
        
        return list(self.tasks.values())
    
    def get_task_status(self, task_id: str) -> Optional[EvaluationStatus]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
        
        return self.tasks[task_id].status
    
    def get_task_result(self, task_id: str) -> Optional[EvaluationTask]:
        """获取任务结果"""
        if task_id not in self.tasks:
            return None
        
        return self.tasks[task_id]
    
    def get_all_tasks(self) -> List[EvaluationTask]:
        """获取所有任务"""
        return list(self.tasks.values())
    
    def get_running_tasks(self) -> List[EvaluationTask]:
        """获取运行中的任务"""
        return [
            self.tasks[task_id] for task_id in self.running_tasks.keys()
            if task_id in self.tasks
        ]
    
    async def generate_report(self, report_name: str = None) -> EvaluationReport:
        """生成评估报告"""
        report_id = f"report_{int(time.time())}"
        timestamp = datetime.now()
        
        # 统计任务
        total_tasks = len(self.tasks)
        completed_tasks = len([t for t in self.tasks.values() if t.status == EvaluationStatus.COMPLETED])
        passed_tasks = len([t for t in self.tasks.values() if t.result == EvaluationResult.PASS])
        failed_tasks = len([t for t in self.tasks.values() if t.result == EvaluationResult.FAIL])
        
        # 计算总体分数
        if completed_tasks > 0:
            overall_score = sum(t.score for t in self.tasks.values() if t.status == EvaluationStatus.COMPLETED) / completed_tasks
        else:
            overall_score = 0.0
        
        # 计算总持续时间
        total_duration = sum(t.duration for t in self.tasks.values())
        
        # 生成摘要
        summary = {
            "success_rate": (passed_tasks / completed_tasks * 100) if completed_tasks > 0 else 0,
            "average_score": overall_score,
            "average_duration": (total_duration / completed_tasks) if completed_tasks > 0 else 0,
            "task_distribution": {
                "pending": len([t for t in self.tasks.values() if t.status == EvaluationStatus.PENDING]),
                "running": len([t for t in self.tasks.values() if t.status == EvaluationStatus.RUNNING]),
                "completed": completed_tasks,
                "failed": len([t for t in self.tasks.values() if t.status == EvaluationStatus.FAILED]),
                "cancelled": len([t for t in self.tasks.values() if t.status == EvaluationStatus.CANCELLED])
            }
        }
        
        report = EvaluationReport(
            report_id=report_id,
            timestamp=timestamp,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            passed_tasks=passed_tasks,
            failed_tasks=failed_tasks,
            overall_score=overall_score,
            duration=total_duration,
            tasks=list(self.tasks.values()),
            summary=summary
        )
        
        self.reports.append(report)
        logger.info(f"生成评估报告: {report_name or report_id}")
        
        return report
    
    def get_reports(self) -> List[EvaluationReport]:
        """获取所有报告"""
        return self.reports.copy()
    
    def clear_tasks(self) -> None:
        """清空所有任务"""
        self.tasks.clear()
        self.running_tasks.clear()
        logger.info("清空所有任务")

def get_async_evaluation_system(config: Optional[Dict[str, Any]] = None) -> AsyncEvaluationSystem:
    """获取异步评估系统实例"""
    return AsyncEvaluationSystem(config)