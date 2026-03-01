#!/usr/bin/env python3
"""
自适应并发管理器 - 根据资源使用情况动态调整并发数
平衡性能与稳定性
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .resource_monitor import ResourceMonitor, ResourceThresholds


@dataclass
class ConcurrencyConfig:
    """并发配置"""
    min_concurrent: int = 1      # 最小并发数
    max_concurrent: int = 5      # 最大并发数
    initial_concurrent: int = 3  # 初始并发数
    adjustment_step: int = 1     # 每次调整的步长
    check_interval: float = 5.0  # 检查间隔（秒）
    min_adjustment_interval: float = 10.0  # 最小调整间隔（秒）


class AdaptiveConcurrencyManager:
    """自适应并发管理器 - 根据资源使用情况动态调整并发数"""
    
    def __init__(
        self,
        config: Optional[ConcurrencyConfig] = None,
        resource_monitor: Optional[ResourceMonitor] = None
    ):
        """初始化自适应并发管理器"""
        self.logger = logging.getLogger(__name__)
        self.config = config or ConcurrencyConfig()
        self.resource_monitor = resource_monitor or ResourceMonitor()
        
        # 当前并发数
        self.current_concurrent = self.config.initial_concurrent
        self._semaphore = asyncio.Semaphore(self.current_concurrent)
        
        # 调整历史
        self.adjustment_history = []
        self.last_adjustment_time = 0
        
        # 性能指标
        self.performance_metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_wait_time': 0.0,
            'average_execution_time': 0.0,
        }
        
        # 资源使用历史（用于趋势分析）
        self.resource_history = []
        self.max_history_size = 20
        
    async def execute_with_adaptive_concurrency(
        self,
        tasks: list,
        task_name: str = "task"
    ) -> list:
        """使用自适应并发执行任务列表"""
        self.logger.info(
            f"🚀 开始执行 {len(tasks)} 个{task_name}，"
            f"初始并发数: {self.current_concurrent}"
        )
        
        # 启动资源监控和自适应调整
        adjustment_task = asyncio.create_task(self._adaptive_adjustment_loop())
        
        try:
            # 执行任务
            results = []
            for i, task in enumerate(tasks, 1):
                # 等待信号量（控制并发）
                await self._semaphore.acquire()
                
                # 创建任务
                task_wrapper = asyncio.create_task(
                    self._execute_with_metrics(task, i, len(tasks), task_name)
                )
                
                # 添加完成回调
                task_wrapper.add_done_callback(
                    lambda t, s=self._semaphore: s.release()
                )
                
                results.append(task_wrapper)
            
            # 等待所有任务完成
            completed_results = await asyncio.gather(*results, return_exceptions=True)
            
            # 计算性能指标
            self._update_performance_metrics()
            
            return completed_results
            
        finally:
            # 停止自适应调整
            adjustment_task.cancel()
            try:
                await adjustment_task
            except asyncio.CancelledError:
                pass
    
    async def _execute_with_metrics(
        self,
        task,
        task_index: int,
        total_tasks: int,
        task_name: str
    ):
        """执行任务并记录指标"""
        start_time = time.time()
        wait_time = time.time() - start_time
        
        try:
            self.performance_metrics['total_tasks'] += 1
            result = await task
            
            execution_time = time.time() - start_time
            self.performance_metrics['completed_tasks'] += 1
            
            self.logger.debug(
                f"✅ {task_name} {task_index}/{total_tasks} 完成，"
                f"等待时间: {wait_time:.2f}s，执行时间: {execution_time:.2f}s"
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.performance_metrics['failed_tasks'] += 1
            
            self.logger.warning(
                f"❌ {task_name} {task_index}/{total_tasks} 失败: {e}，"
                f"执行时间: {execution_time:.2f}s"
            )
            raise
    
    async def _adaptive_adjustment_loop(self):
        """自适应调整循环"""
        while True:
            try:
                await asyncio.sleep(self.config.check_interval)
                
                # 检查是否可以调整（距离上次调整的时间间隔）
                current_time = time.time()
                if current_time - self.last_adjustment_time < self.config.min_adjustment_interval:
                    continue
                
                # 获取资源状态
                resource_status = self.resource_monitor.get_resource_status()
                if resource_status.get("status") != "ok":
                    continue
                
                # 记录资源使用历史
                self.resource_history.append({
                    'timestamp': current_time,
                    'memory_percent': resource_status['memory']['system_percent'],
                    'memory_mb': resource_status['memory']['process_rss_mb'],
                    'cpu_percent': resource_status['cpu']['process_percent'],
                    'fds': resource_status['file_descriptors']['count'],
                    'concurrent': self.current_concurrent
                })
                
                # 限制历史记录大小
                if len(self.resource_history) > self.max_history_size:
                    self.resource_history = self.resource_history[-self.max_history_size:]
                
                # 根据资源使用情况调整并发数
                new_concurrent = self._calculate_optimal_concurrency(resource_status)
                
                if new_concurrent != self.current_concurrent:
                    await self._adjust_concurrency(new_concurrent, resource_status)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"自适应调整循环出错: {e}")
                await asyncio.sleep(self.config.check_interval)
    
    def _calculate_optimal_concurrency(
        self,
        resource_status: Dict[str, Any]
    ) -> int:
        """根据资源使用情况计算最优并发数"""
        memory = resource_status['memory']
        cpu = resource_status['cpu']
        fds = resource_status['file_descriptors']
        
        # 获取资源使用率
        memory_percent = memory['system_percent']
        memory_mb = memory['process_rss_mb']
        cpu_percent = cpu['process_percent']
        fd_count = fds['count'] if fds['count'] > 0 else 0
        
        # 计算资源压力分数（0-1，越高压力越大）
        memory_pressure = min(memory_percent / 80.0, 1.0)  # 80%为阈值
        memory_mb_pressure = min(memory_mb / 4000.0, 1.0) if memory_mb > 0 else 0  # 4GB为阈值
        fd_pressure = min(fd_count / 500.0, 1.0) if fd_count > 0 else 0  # 500为阈值
        
        # 综合压力（取最大值）
        overall_pressure = max(memory_pressure, memory_mb_pressure, fd_pressure)
        
        # 根据压力调整并发数
        if overall_pressure > 0.8:  # 高压力：降低并发
            new_concurrent = max(
                self.config.min_concurrent,
                self.current_concurrent - self.config.adjustment_step
            )
            reason = f"资源压力高 ({overall_pressure:.2f})，降低并发"
        elif overall_pressure > 0.6:  # 中等压力：保持或略微降低
            new_concurrent = max(
                self.config.min_concurrent,
                self.current_concurrent - 1
            )
            reason = f"资源压力中等 ({overall_pressure:.2f})，略微降低并发"
        elif overall_pressure < 0.3:  # 低压力：提高并发
            new_concurrent = min(
                self.config.max_concurrent,
                self.current_concurrent + self.config.adjustment_step
            )
            reason = f"资源压力低 ({overall_pressure:.2f})，提高并发"
        else:  # 正常压力：保持当前并发
            new_concurrent = self.current_concurrent
            reason = f"资源压力正常 ({overall_pressure:.2f})，保持并发"
        
        return new_concurrent
    
    async def _adjust_concurrency(
        self,
        new_concurrent: int,
        resource_status: Dict[str, Any]
    ):
        """调整并发数"""
        if new_concurrent == self.current_concurrent:
            return
        
        old_concurrent = self.current_concurrent
        
        # 更新信号量
        # 注意：asyncio.Semaphore不支持直接修改值，需要创建新的
        # 这里我们使用一个技巧：等待所有当前任务完成，然后创建新的信号量
        # 但实际上，由于信号量是共享的，我们需要更仔细地处理
        
        # 简单方案：记录新的并发数，下次创建任务时使用
        # 但这样不够精确，更好的方案是使用BoundedSemaphore或者自定义实现
        
        # 临时方案：记录调整，实际调整在下次任务创建时生效
        self.current_concurrent = new_concurrent
        
        # 创建新的信号量（注意：这不会影响正在运行的任务）
        # 更好的实现是使用一个包装器来动态控制并发
        self._semaphore = asyncio.Semaphore(new_concurrent)
        
        self.last_adjustment_time = time.time()
        
        self.adjustment_history.append({
            'timestamp': self.last_adjustment_time,
            'old_concurrent': old_concurrent,
            'new_concurrent': new_concurrent,
            'resource_status': resource_status
        })
        
        self.logger.info(
            f"🔄 并发数调整: {old_concurrent} -> {new_concurrent} "
            f"(内存: {resource_status['memory']['system_percent']:.1f}%, "
            f"进程内存: {resource_status['memory']['process_rss_mb']:.1f}MB, "
            f"文件描述符: {resource_status['file_descriptors']['count']})"
        )
    
    def _update_performance_metrics(self):
        """更新性能指标"""
        total = self.performance_metrics['total_tasks']
        if total > 0:
            success_rate = self.performance_metrics['completed_tasks'] / total
            self.logger.info(
                f"📊 性能指标: 总任务={total}, "
                f"成功率={success_rate:.2%}, "
                f"当前并发数={self.current_concurrent}"
            )
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            'current_concurrent': self.current_concurrent,
            'config': {
                'min_concurrent': self.config.min_concurrent,
                'max_concurrent': self.config.max_concurrent,
            },
            'performance': self.performance_metrics.copy(),
            'adjustment_count': len(self.adjustment_history),
            'last_adjustment': self.adjustment_history[-1] if self.adjustment_history else None
        }

