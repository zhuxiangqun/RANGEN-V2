#!/usr/bin/env python3
"""
性能分析工具 - 用于分析测试超时原因
记录每个操作的执行时间，帮助定位性能瓶颈
"""
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from collections import defaultdict
from contextlib import contextmanager
from functools import wraps

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """性能分析器 - 记录和分析操作执行时间"""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.operation_counts: Dict[str, int] = defaultdict(int)
        self.operation_total_times: Dict[str, float] = defaultdict(float)
        self.operation_max_times: Dict[str, float] = defaultdict(float)
        self.operation_min_times: Dict[str, float] = defaultdict(lambda: float('inf'))
        self.start_times: Dict[str, float] = {}
        self.nested_level = 0
        self.max_nested_level = 0
        
    def start_operation(self, operation_name: str):
        """开始记录操作时间"""
        self.nested_level += 1
        self.max_nested_level = max(self.max_nested_level, self.nested_level)
        
        full_name = f"{'  ' * (self.nested_level - 1)}{operation_name}"
        self.start_times[full_name] = time.time()
        return full_name
    
    def end_operation(self, operation_name: str):
        """结束记录操作时间"""
        if not self.start_times:
            return
        
        # 找到最内层的操作（最后开始的）
        matching_ops = [op for op in self.start_times.keys() if op.strip() == operation_name.strip()]
        if not matching_ops:
            # 尝试匹配完整路径
            matching_ops = [op for op in self.start_times.keys() if operation_name in op]
        
        if not matching_ops:
            logger.warning(f"⚠️ 未找到开始的操作: {operation_name}")
            return
        
        # 使用最内层的操作（最后添加的）
        full_name = matching_ops[-1]
        
        if full_name not in self.start_times:
            logger.warning(f"⚠️ 操作 {full_name} 未开始")
            return
        
        elapsed = time.time() - self.start_times[full_name]
        
        # 记录统计信息
        self.operation_times[full_name].append(elapsed)
        self.operation_counts[full_name] += 1
        self.operation_total_times[full_name] += elapsed
        self.operation_max_times[full_name] = max(self.operation_max_times[full_name], elapsed)
        self.operation_min_times[full_name] = min(self.operation_min_times[full_name], elapsed)
        
        # 移除开始时间
        del self.start_times[full_name]
        self.nested_level = max(0, self.nested_level - 1)
        
        # 记录耗时（如果超过阈值）
        if elapsed > 5.0:  # 超过5秒的操作
            logger.warning(f"⏱️ [{full_name}] 耗时: {elapsed:.2f}秒")
        elif elapsed > 1.0:  # 超过1秒的操作
            logger.info(f"⏱️ [{full_name}] 耗时: {elapsed:.2f}秒")
        else:
            logger.debug(f"⏱️ [{full_name}] 耗时: {elapsed:.2f}秒")
        
        return elapsed
    
    @contextmanager
    def operation(self, operation_name: str):
        """上下文管理器：自动记录操作时间"""
        full_name = self.start_operation(operation_name)
        try:
            yield full_name
        finally:
            self.end_operation(operation_name)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        summary = {
            "total_operations": sum(self.operation_counts.values()),
            "unique_operations": len(self.operation_counts),
            "max_nested_level": self.max_nested_level,
            "operations": []
        }
        
        # 按总耗时排序
        sorted_ops = sorted(
            self.operation_total_times.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for op_name, total_time in sorted_ops:
            count = self.operation_counts[op_name]
            avg_time = total_time / count if count > 0 else 0
            max_time = self.operation_max_times[op_name]
            min_time = self.operation_min_times[op_name] if self.operation_min_times[op_name] != float('inf') else 0
            
            summary["operations"].append({
                "name": op_name,
                "count": count,
                "total_time": round(total_time, 2),
                "avg_time": round(avg_time, 2),
                "max_time": round(max_time, 2),
                "min_time": round(min_time, 2),
                "percentage": 0  # 将在后面计算
            })
        
        # 计算百分比
        total_time = sum(self.operation_total_times.values())
        if total_time > 0:
            for op in summary["operations"]:
                op["percentage"] = round((op["total_time"] / total_time) * 100, 1)
        
        return summary
    
    def print_summary(self):
        """打印性能摘要"""
        summary = self.get_summary()
        
        logger.info("=" * 80)
        logger.info("📊 性能分析摘要")
        logger.info("=" * 80)
        logger.info(f"总操作数: {summary['total_operations']}")
        logger.info(f"唯一操作数: {summary['unique_operations']}")
        logger.info(f"最大嵌套层级: {summary['max_nested_level']}")
        logger.info("")
        logger.info("操作耗时统计（按总耗时排序）:")
        logger.info("-" * 80)
        logger.info(f"{'操作名称':<50} {'次数':<8} {'总耗时':<10} {'平均耗时':<10} {'最大耗时':<10} {'占比':<8}")
        logger.info("-" * 80)
        
        for op in summary["operations"][:20]:  # 只显示前20个
            logger.info(
                f"{op['name']:<50} "
                f"{op['count']:<8} "
                f"{op['total_time']:<10.2f}秒 "
                f"{op['avg_time']:<10.2f}秒 "
                f"{op['max_time']:<10.2f}秒 "
                f"{op['percentage']:<8.1f}%"
            )
        
        logger.info("=" * 80)
    
    def reset(self):
        """重置分析器"""
        self.operation_times.clear()
        self.operation_counts.clear()
        self.operation_total_times.clear()
        self.operation_max_times.clear()
        self.operation_min_times.clear()
        self.start_times.clear()
        self.nested_level = 0
        self.max_nested_level = 0


# 全局性能分析器实例
_global_analyzer = PerformanceAnalyzer()


def get_analyzer() -> PerformanceAnalyzer:
    """获取全局性能分析器"""
    return _global_analyzer


def reset_analyzer():
    """重置全局性能分析器"""
    _global_analyzer.reset()


def track_performance(operation_name: str):
    """装饰器：自动跟踪函数性能"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            analyzer = get_analyzer()
            with analyzer.operation(operation_name):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            analyzer = get_analyzer()
            with analyzer.operation(operation_name):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

