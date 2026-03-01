#!/usr/bin/env python3
"""
智能自动化系统 - 自动运维、智能调度、自愈能力
基于现有统一中心系统的智能自动化增强
"""

import os
import time
import logging
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import psutil
import gc


class AutomationStatus(Enum):
    """自动化状态"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class AutomationPriority(Enum):
    """自动化优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AutomationTask:
    """自动化任务"""
    task_id: str
    name: str
    description: str
    function: Callable
    schedule: str  # cron表达式或时间间隔
    priority: AutomationPriority
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    avg_duration: float = 0.0
    status: AutomationStatus = AutomationStatus.IDLE
    error_message: Optional[str] = None


@dataclass
class AutomationRule:
    """自动化规则"""
    rule_id: str
    name: str
    condition: Callable
    action: Callable
    priority: AutomationPriority
    enabled: bool = True
    cooldown: int = 300  # 冷却时间(秒)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class IntelligentAutomationSystem:
    """智能自动化系统"""
    
    def __init__(self):
        """初始化智能自动化系统"""
        self.logger = logging.getLogger(__name__)
        self.tasks: Dict[str, AutomationTask] = {}
        self.rules: Dict[str, AutomationRule] = {}
        self.status = AutomationStatus.IDLE
        self.is_running = False
        self.thread_pool = []
        self.metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_rules': 0,
            'triggered_rules': 0,
            'system_uptime': 0.0
        }
        
        # 自愈能力配置
        self.self_healing = {
            'enabled': True,
            'max_retries': 3,
            'retry_delay': 60,  # 秒
            'health_check_interval': 30,  # 秒
            'auto_recovery_threshold': 0.8
        }
        
        # 智能调度配置
        self.scheduling = {
            'max_concurrent_tasks': 5,
            'resource_threshold': 0.8,
            'load_balancing': True,
            'adaptive_scheduling': True
        }
        
        self.start_time = time.time()
        self._initialize_default_tasks()
        self._initialize_default_rules()
        
        self.logger.info("智能自动化系统初始化完成")
    
    def _initialize_default_tasks(self):
        """初始化默认任务"""
        try:
            # 系统健康检查任务
            health_check_task = AutomationTask(
                task_id="health_check",
                name="系统健康检查",
                description="定期检查系统健康状态",
                function=self._health_check_task,
                schedule="*/30 * * * *",  # 每30秒
                priority=AutomationPriority.HIGH
            )
            self.tasks["health_check"] = health_check_task
            
            # 内存清理任务
            memory_cleanup_task = AutomationTask(
                task_id="memory_cleanup",
                name="内存清理",
                description="定期清理内存和垃圾回收",
                function=self._memory_cleanup_task,
                schedule="0 */10 * * * *",  # 每10分钟
                priority=AutomationPriority.NORMAL
            )
            self.tasks["memory_cleanup"] = memory_cleanup_task
            
            # 日志轮转任务
            log_rotation_task = AutomationTask(
                task_id="log_rotation",
                name="日志轮转",
                description="定期轮转和清理日志文件",
                function=self._log_rotation_task,
                schedule="0 0 */6 * * *",  # 每6小时
                priority=AutomationPriority.LOW
            )
            self.tasks["log_rotation"] = log_rotation_task
            
            # 性能优化任务
            performance_optimization_task = AutomationTask(
                task_id="performance_optimization",
                name="性能优化",
                description="定期执行性能优化",
                function=self._performance_optimization_task,
                schedule="0 0 */2 * * *",  # 每2小时
                priority=AutomationPriority.NORMAL
            )
            self.tasks["performance_optimization"] = performance_optimization_task
            
        except Exception as e:
            self.logger.error(f"默认任务初始化失败: {e}")
    
    def _initialize_default_rules(self):
        """初始化默认规则"""
        try:
            # 高CPU使用率规则
            high_cpu_rule = AutomationRule(
                rule_id="high_cpu_usage",
                name="高CPU使用率处理",
                condition=self._check_high_cpu_usage,
                action=self._handle_high_cpu_usage,
                priority=AutomationPriority.HIGH,
                cooldown=300
            )
            self.rules["high_cpu_usage"] = high_cpu_rule
            
            # 高内存使用率规则
            high_memory_rule = AutomationRule(
                rule_id="high_memory_usage",
                name="高内存使用率处理",
                condition=self._check_high_memory_usage,
                action=self._handle_high_memory_usage,
                priority=AutomationPriority.HIGH,
                cooldown=300
            )
            self.rules["high_memory_usage"] = high_memory_rule
            
            # 磁盘空间不足规则
            low_disk_space_rule = AutomationRule(
                rule_id="low_disk_space",
                name="磁盘空间不足处理",
                condition=self._check_low_disk_space,
                action=self._handle_low_disk_space,
                priority=AutomationPriority.CRITICAL,
                cooldown=600
            )
            self.rules["low_disk_space"] = low_disk_space_rule
            
            # 系统错误规则
            system_error_rule = AutomationRule(
                rule_id="system_error",
                name="系统错误处理",
                condition=self._check_system_errors,
                action=self._handle_system_errors,
                priority=AutomationPriority.CRITICAL,
                cooldown=60
            )
            self.rules["system_error"] = system_error_rule
            
        except Exception as e:
            self.logger.error(f"默认规则初始化失败: {e}")
    
    async def start(self):
        """启动自动化系统"""
        try:
            if self.is_running:
                self.logger.warning("自动化系统已在运行")
                return
            
            self.is_running = True
            self.status = AutomationStatus.RUNNING
            
            # 启动任务调度器
            task_scheduler = threading.Thread(target=self._task_scheduler_loop, daemon=True)
            task_scheduler.start()
            self.thread_pool.append(task_scheduler)
            
            # 启动规则监控器
            rule_monitor = threading.Thread(target=self._rule_monitor_loop, daemon=True)
            rule_monitor.start()
            self.thread_pool.append(rule_monitor)
            
            # 启动自愈监控器
            if self.self_healing['enabled']:
                self_healing_monitor = threading.Thread(target=self._self_healing_loop, daemon=True)
                self_healing_monitor.start()
                self.thread_pool.append(self_healing_monitor)
            
            self.logger.info("智能自动化系统启动完成")
            
        except Exception as e:
            self.logger.error(f"自动化系统启动失败: {e}")
            self.status = AutomationStatus.ERROR
    
    async def stop(self):
        """停止自动化系统"""
        try:
            self.is_running = False
            self.status = AutomationStatus.IDLE
            
            # 等待所有线程结束
            for thread in self.thread_pool:
                if thread.is_alive():
                    thread.join(timeout=5)
            
            self.thread_pool.clear()
            self.logger.info("智能自动化系统停止完成")
            
        except Exception as e:
            self.logger.error(f"自动化系统停止失败: {e}")
    
    def _task_scheduler_loop(self):
        """任务调度循环"""
        while self.is_running:
            try:
                current_time = datetime.now()
                
                for task in self.tasks.values():
                    if not task.enabled:
                        continue
                    
                    # 检查是否到了执行时间
                    if self._should_run_task(task, current_time):
                        # 检查资源使用情况
                        if self._can_run_task():
                            # 执行任务
                            threading.Thread(
                                target=self._execute_task,
                                args=(task,),
                                daemon=True
                            ).start()
                        else:
                            self.logger.warning(f"资源不足，延迟执行任务: {task.name}")
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.logger.error(f"任务调度循环出错: {e}")
                time.sleep(5)
    
    def _rule_monitor_loop(self):
        """规则监控循环"""
        while self.is_running:
            try:
                for rule in self.rules.values():
                    if not rule.enabled:
                        continue
                    
                    # 检查冷却时间
                    if self._is_rule_in_cooldown(rule):
                        continue
                    
                    # 检查条件
                    if rule.condition():
                        # 执行动作
                        threading.Thread(
                            target=self._execute_rule,
                            args=(rule,),
                            daemon=True
                        ).start()
                
                time.sleep(5)  # 每5秒检查一次
                
            except Exception as e:
                self.logger.error(f"规则监控循环出错: {e}")
                time.sleep(10)
    
    def _self_healing_loop(self):
        """自愈监控循环"""
        while self.is_running:
            try:
                # 检查系统健康状态
                health_score = self._calculate_health_score()
                
                if health_score < self.self_healing['auto_recovery_threshold']:
                    self.logger.warning(f"系统健康分数过低: {health_score:.2f}")
                    self._trigger_self_healing()
                
                time.sleep(self.self_healing['health_check_interval'])
                
            except Exception as e:
                self.logger.error(f"自愈监控循环出错: {e}")
                time.sleep(30)
    
    def _should_run_task(self, task: AutomationTask, current_time: datetime) -> bool:
        """检查任务是否应该运行"""
        if task.next_run is None:
            # 计算下次运行时间
            task.next_run = self._calculate_next_run_time(task.schedule, current_time)
            return False
        
        return current_time >= task.next_run
    
    def _calculate_next_run_time(self, schedule: str, current_time: datetime) -> datetime:
        """计算下次运行时间"""
        # 简化的调度计算，实际应该使用cron解析器
        if schedule.startswith("*/"):
            interval = int(schedule[2:].split()[0])
            return current_time + timedelta(seconds=interval)
        elif schedule.startswith("0 */"):
            interval = int(schedule[4:].split()[0])
            return current_time + timedelta(minutes=interval)
        else:
            return current_time + timedelta(minutes=1)
    
    def _can_run_task(self) -> bool:
        """检查是否可以运行任务"""
        if not self.scheduling['load_balancing']:
            return True
        
        # 检查当前运行的任务数量
        running_tasks = sum(1 for task in self.tasks.values() 
                          if task.status == AutomationStatus.RUNNING)
        
        if running_tasks >= self.scheduling['max_concurrent_tasks']:
            return False
        
        # 检查资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        if cpu_percent > self.scheduling['resource_threshold'] * 100:
            return False
        
        if memory_percent > self.scheduling['resource_threshold'] * 100:
            return False
        
        return True
    
    def _execute_task(self, task: AutomationTask):
        """执行任务"""
        try:
            task.status = AutomationStatus.RUNNING
            task.last_run = datetime.now()
            start_time = time.time()
            
            self.logger.info(f"开始执行任务: {task.name}")
            
            # 执行任务函数
            if asyncio.iscoroutinefunction(task.function):
                asyncio.run(task.function())
            else:
                task.function()
            
            # 更新任务统计
            execution_time = time.time() - start_time
            task.run_count += 1
            task.success_count += 1
            task.avg_duration = (task.avg_duration * (task.run_count - 1) + execution_time) / task.run_count
            
            # 计算下次运行时间
            task.next_run = self._calculate_next_run_time(task.schedule, datetime.now())
            task.status = AutomationStatus.IDLE
            task.error_message = None
            
            self.metrics['successful_tasks'] += 1
            self.logger.info(f"任务执行成功: {task.name} (耗时: {execution_time:.2f}s)")
            
        except Exception as e:
            task.status = AutomationStatus.ERROR
            task.failure_count += 1
            task.error_message = str(e)
            self.metrics['failed_tasks'] += 1
            self.logger.error(f"任务执行失败: {task.name} - {e}")
    
    def _execute_rule(self, rule: AutomationRule):
        """执行规则"""
        try:
            rule.last_triggered = datetime.now()
            rule.trigger_count += 1
            
            self.logger.info(f"触发规则: {rule.name}")
            
            # 执行规则动作
            if asyncio.iscoroutinefunction(rule.action):
                asyncio.run(rule.action())
            else:
                rule.action()
            
            self.metrics['triggered_rules'] += 1
            self.logger.info(f"规则执行成功: {rule.name}")
            
        except Exception as e:
            self.logger.error(f"规则执行失败: {rule.name} - {e}")
    
    def _is_rule_in_cooldown(self, rule: AutomationRule) -> bool:
        """检查规则是否在冷却期内"""
        if rule.last_triggered is None:
            return False
        
        time_since_last = (datetime.now() - rule.last_triggered).total_seconds()
        return time_since_last < rule.cooldown
    
    def _calculate_health_score(self) -> float:
        """计算系统健康分数"""
        try:
            # 获取系统指标
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            
            # 计算健康分数 (0-1)
            cpu_score = max(0, 1 - cpu_percent / 100)
            memory_score = max(0, 1 - memory_percent / 100)
            disk_score = max(0, 1 - disk_percent / 100)
            
            # 综合健康分数
            health_score = (cpu_score + memory_score + disk_score) / 3
            
            return health_score
            
        except Exception as e:
            self.logger.error(f"健康分数计算失败: {e}")
            return 0.5
    
    def _trigger_self_healing(self):
        """触发自愈机制"""
        try:
            self.logger.info("触发自愈机制")
            
            # 执行自愈任务
            self._memory_cleanup_task()
            self._performance_optimization_task()
            
            # 重启失败的任务
            for task in self.tasks.values():
                if task.status == AutomationStatus.ERROR:
                    task.status = AutomationStatus.IDLE
                    task.error_message = None
            
            self.logger.info("自愈机制执行完成")
            
        except Exception as e:
            self.logger.error(f"自愈机制执行失败: {e}")
    
    # 默认任务实现
    def _health_check_task(self):
        """系统健康检查任务"""
        try:
            health_score = self._calculate_health_score()
            self.logger.info(f"系统健康分数: {health_score:.2f}")
            
            if health_score < 0.5:
                self.logger.warning("系统健康状态不佳")
            
        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
    
    def _memory_cleanup_task(self):
        """内存清理任务"""
        try:
            # 执行垃圾回收
            collected = gc.collect()
            self.logger.info(f"垃圾回收完成，回收了 {collected} 个对象")
            
        except Exception as e:
            self.logger.error(f"内存清理失败: {e}")
    
    def _log_rotation_task(self):
        """日志轮转任务"""
        try:
            # 这里可以实现日志轮转逻辑
            self.logger.info("日志轮转任务执行")
            
        except Exception as e:
            self.logger.error(f"日志轮转失败: {e}")
    
    def _performance_optimization_task(self):
        """性能优化任务"""
        try:
            # 这里可以实现性能优化逻辑
            self.logger.info("性能优化任务执行")
            
        except Exception as e:
            self.logger.error(f"性能优化失败: {e}")
    
    # 默认规则条件检查
    def _check_high_cpu_usage(self) -> bool:
        """检查高CPU使用率"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return cpu_percent > 80
        except:
            return False
    
    def _check_high_memory_usage(self) -> bool:
        """检查高内存使用率"""
        try:
            memory_percent = psutil.virtual_memory().percent
            return memory_percent > 85
        except:
            return False
    
    def _check_low_disk_space(self) -> bool:
        """检查磁盘空间不足"""
        try:
            disk_percent = psutil.disk_usage('/').percent
            return disk_percent > 90
        except:
            return False
    
    def _check_system_errors(self) -> bool:
        """检查系统错误"""
        try:
            # 这里可以检查系统错误日志
            return False
        except:
            return False
    
    # 默认规则动作
    def _handle_high_cpu_usage(self):
        """处理高CPU使用率"""
        self.logger.warning("检测到高CPU使用率，执行优化措施")
        # 这里可以实现具体的优化措施
    
    def _handle_high_memory_usage(self):
        """处理高内存使用率"""
        self.logger.warning("检测到高内存使用率，执行内存清理")
        self._memory_cleanup_task()
    
    def _handle_low_disk_space(self):
        """处理磁盘空间不足"""
        self.logger.warning("检测到磁盘空间不足，执行清理措施")
        # 这里可以实现具体的清理措施
    
    def _handle_system_errors(self):
        """处理系统错误"""
        self.logger.warning("检测到系统错误，执行恢复措施")
        # 这里可以实现具体的恢复措施
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            'status': self.status.value,
            'is_running': self.is_running,
            'uptime': time.time() - self.start_time,
            'tasks': {
                'total': len(self.tasks),
                'enabled': sum(1 for t in self.tasks.values() if t.enabled),
                'running': sum(1 for t in self.tasks.values() if t.status == AutomationStatus.RUNNING),
                'error': sum(1 for t in self.tasks.values() if t.status == AutomationStatus.ERROR)
            },
            'rules': {
                'total': len(self.rules),
                'enabled': sum(1 for r in self.rules.values() if r.enabled),
                'triggered': self.metrics['triggered_rules']
            },
            'metrics': self.metrics,
            'self_healing': self.self_healing,
            'scheduling': self.scheduling
        }


def get_intelligent_automation_system() -> IntelligentAutomationSystem:
    """获取智能自动化系统实例"""
    return IntelligentAutomationSystem()


if __name__ == "__main__":
    # 测试智能自动化系统
    automation = get_intelligent_automation_system()
    
    # 启动系统
    asyncio.run(automation.start())
    
    # 运行一段时间
    time.sleep(60)
    
    # 停止系统
    asyncio.run(automation.stop())
    
    # 获取状态
    status = automation.get_system_status()
    print(f"系统状态: {status}")
