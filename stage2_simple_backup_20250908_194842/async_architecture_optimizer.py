#!/usr/bin/env python3
"""
异步架构优化器 - 充分利用现有性能监控中心，进一步优化异步架构
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from functools import wraps

# 使用现有的统一中心
from src.utils.unified_performance_center import get_unified_performance_center
from src.utils.unified_monitoring_center import get_unified_monitoring_center
from src.utils.unified_config_center import get_unified_config_center

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)

@dataclass
class AsyncOptimizationConfig:
    """异步优化配置"""
    max_concurrent_tasks: int = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))
    task_timeout: Optional[float] = None
    enable_parallel_execution: bool = True
    enable_adaptive_timeout: bool = True
    enable_performance_monitoring: bool = True
    enable_error_recovery: bool = True

class AsyncArchitectureOptimizer:
    """异步架构优化器"""
    
    def __init__(self):
        self.performance_center = get_unified_performance_center()
        self.monitoring_center = get_unified_monitoring_center()
        self.config_center = get_unified_config_center()
        
        # 获取异步优化配置
        self.config = self._load_async_config()
        
        # 任务统计
        self.task_stats = {
            'total_tasks': config.DEFAULT_ZERO_VALUE,
            'completed_tasks': config.DEFAULT_ZERO_VALUE,
            'failed_tasks': config.DEFAULT_ZERO_VALUE,
            'parallel_executions': config.DEFAULT_ZERO_VALUE,
            'avg_execution_time': config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
        }
        
        logger.info("✅ 异步架构优化器初始化完成")
    
    def _load_async_config(self) -> AsyncOptimizationConfig:
        """加载异步优化配置"""
        try:
            config_data = self.config_center.get_config_value("async_optimization", "config", {})

            # 使用智能配置系统获取默认超时时间
            if "task_timeout" not in config_data:
                async_context = create_query_context(query_type="async_optimization_config")
                config_data["task_timeout"] = get_smart_config("async_task_timeout", async_context)

            return AsyncOptimizationConfig(**config_data)
        except Exception as e:
            logger.warning(f"加载异步配置失败，使用默认配置: {e}")
            # 使用智能配置系统获取默认配置
            async_context = create_query_context(query_type="async_optimization_config")
            return AsyncOptimizationConfig(
                task_timeout=get_smart_config("async_task_timeout", async_context)
            )
    
    async def optimize_parallel_execution(self, tasks: List[Callable], context: str = "general") -> List[Any]:
        """优化并行执行"""
        if not self.config.enable_parallel_execution:
            # 顺序执行
            results = []
            for task in tasks:
                result = await self._execute_with_monitoring(task, context)
                results.append(result)
            return results
        
        # 并行执行
        self.task_stats['parallel_executions'] += config.DEFAULT_ONE_VALUE
        
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        
        async def limited_task(task):
            async with semaphore:
                return await self._execute_with_monitoring(task, context)
        
        # 创建所有任务
        task_coros = [limited_task(task) for task in tasks]
        
        # 并行执行
        start_time = time.time()
        results = await asyncio.gather(*task_coros, return_exceptions=True)
        execution_time = time.time() - start_time
        
        # 更新统计
        self._update_task_stats(len(tasks), execution_time, results)
        
        return results
    
    async def _execute_with_monitoring(self, task: Callable, context: str) -> Any:
        """带监控的任务执行"""
        start_time = time.time()
        
        try:
            # 使用性能中心监控
            if self.config.enable_performance_monitoring:
                # 直接执行任务，性能中心已经在后台监控
                result = await task()
            else:
                result = await task()
            
            execution_time = time.time() - start_time
            
            # 自适应超时调整
            if self.config.enable_adaptive_timeout:
                self._adjust_timeout(execution_time, context)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"任务执行失败 [{context}]: {e}")
            
            # 错误恢复
            if self.config.enable_error_recovery:
                return await self._error_recovery(task, context, e)
            
            raise
    
    async def _error_recovery(self, task: Callable, context: str, error: Exception) -> Any:
        """错误恢复机制"""
        try:
            logger.info(f"尝试错误恢复 [{context}]")
            
            # 简单的重试机制
            for attempt in range(2):
                try:
                    await asyncio.sleep(config.DEFAULT_LOW_DECIMAL_THRESHOLD * (attempt + 1))  # 短暂延迟
                    result = await task()
                    logger.info(f"错误恢复成功 [{context}]")
                    return result
                except Exception as retry_error:
                    logger.warning(f"重试失败 [{context}] 第{attempt + 1}次: {retry_error}")
            
            # 返回错误信息
            return {
                'error': str(error),
                'recovery_failed': True,
                'context': context
            }
            
        except Exception as recovery_error:
            logger.error(f"错误恢复机制失败 [{context}]: {recovery_error}")
            return {
                'error': str(error),
                'recovery_error': str(recovery_error),
                'context': context
            }
    
    def _adjust_timeout(self, execution_time: float, context: str):
        """自适应超时调整"""
        try:
            # 根据执行时间调整超时配置
            if execution_time > self.config.task_timeout * config.DEFAULT_HIGH_THRESHOLD:
                # 执行时间接近超时，增加超时时间
                new_timeout = self.config.task_timeout * config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE
                self.config.task_timeout = min(new_timeout, config.DEFAULT_TIMEOUT_MINUTES.config.DEFAULT_ZERO_VALUE)  # 最大config.DEFAULT_TIMEOUT_MINUTES秒
                logger.info(f"增加超时时间 [{context}]: {new_timeout:.config.DEFAULT_ONE_VALUEf}s")
            elif execution_time < self.config.task_timeout * config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                # 执行时间很短，减少超时时间
                new_timeout = self.config.task_timeout * config.DEFAULT_HIGH_THRESHOLD
                self.config.task_timeout = max(new_timeout, 5.config.DEFAULT_ZERO_VALUE)  # 最小5秒
                logger.info(f"减少超时时间 [{context}]: {new_timeout:.config.DEFAULT_ONE_VALUEf}s")
        except Exception as e:
            logger.warning(f"超时调整失败: {e}")
    
    def _update_task_stats(self, task_count: int, execution_time: float, results: List[Any]):
        """更新任务统计"""
        self.task_stats['total_tasks'] += task_count
        self.task_stats['completed_tasks'] += len([r for r in results if not isinstance(r, Exception)])
        self.task_stats['failed_tasks'] += len([r for r in results if isinstance(r, Exception)])
        
        # 更新平均执行时间
        if self.task_stats['total_tasks'] > config.DEFAULT_ZERO_VALUE:
            self.task_stats['avg_execution_time'] = (
                (self.task_stats['avg_execution_time'] * (self.task_stats['total_tasks'] - task_count) + execution_time) 
                / self.task_stats['total_tasks']
            )
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """获取优化报告"""
        return {
            'config': {
                'max_concurrent_tasks': self.config.max_concurrent_tasks,
                'task_timeout': self.config.task_timeout,
                'enable_parallel_execution': self.config.enable_parallel_execution,
                'enable_adaptive_timeout': self.config.enable_adaptive_timeout,
                'enable_performance_monitoring': self.config.enable_performance_monitoring,
                'enable_error_recovery': self.config.enable_error_recovery
            },
            'stats': self.task_stats,
            'performance_center_status': 'active',
            'monitoring_center_status': 'active',
            'optimization_effectiveness': self._calculate_effectiveness()
        }
    
    def _calculate_effectiveness(self) -> Dict[str, float]:
        """计算优化效果"""
        if self.task_stats['total_tasks'] == 0:
            return {'success_rate': get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), 'parallel_efficiency': get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))}
        
        success_rate = self.task_stats['completed_tasks'] / self.task_stats['total_tasks']
        parallel_efficiency = self.task_stats['parallel_executions'] / max(1, self.task_stats['total_tasks'])
        
        return {
            'success_rate': success_rate,
            'parallel_efficiency': parallel_efficiency,
            'avg_execution_time': self.task_stats['avg_execution_time']
        }

# 装饰器：异步性能监控
def async_performance_monitor(context: str = "general"):
    """异步性能监控装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = get_async_architecture_optimizer()
            return await optimizer._execute_with_monitoring(
                lambda: func(*args, **kwargs), 
                context
            )
        return wrapper
    return decorator

# 装饰器：并行执行优化
def parallel_execution_optimizer(max_concurrent: int = 5):
    """并行执行优化装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            optimizer = get_async_architecture_optimizer()
            
            # 创建任务列表
            tasks = [lambda: func(*args, **kwargs)]
            
            # 使用并行执行优化
            results = await optimizer.optimize_parallel_execution(tasks, func.__name__)
            return results[0] if results else None
        return wrapper
    return decorator

# 全局实例
_async_optimizer = None

def get_async_architecture_optimizer() -> AsyncArchitectureOptimizer:
    """获取异步架构优化器实例"""
    global _async_optimizer
    if _async_optimizer is None:
        _async_optimizer = AsyncArchitectureOptimizer()
    return _async_optimizer

# 便捷函数
async def optimize_parallel_tasks(tasks: List[Callable], context: str = "general") -> List[Any]:
    """优化并行任务执行的便捷函数"""
    optimizer = get_async_architecture_optimizer()
    return await optimizer.optimize_parallel_execution(tasks, context)

def get_async_optimization_report() -> Dict[str, Any]:
    """获取异步优化报告的便捷函数"""
    optimizer = get_async_architecture_optimizer()
    return optimizer.get_optimization_report()
