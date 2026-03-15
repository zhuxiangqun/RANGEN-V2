#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控优化器 - 实时监控和优化RANGEN系统性能
提供性能监控、自动优化、资源管理和预测分析功能
"""

import asyncio
import logging
import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
import json

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    query_count: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    error_count: int = 0
    active_connections: int = 0

@dataclass
class OptimizationRule:
    """优化规则"""
    name: str
    condition: Callable[[PerformanceMetrics], bool]
    action: Callable[[], None]
    priority: int = 1
    enabled: bool = True

class SystemMonitorOptimizer:
    """系统监控优化器"""
    
    def __init__(self, monitoring_interval: float = 1.0, history_size: int = 1000):
        self.monitoring_interval = monitoring_interval
        self.history_size = history_size
        
        # 性能历史记录
        self.performance_history = deque(maxlen=history_size)
        self.query_history = deque(maxlen=history_size)
        
        # 当前状态
        self.current_metrics = PerformanceMetrics()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # 优化规则
        self.optimization_rules = []
        self._setup_default_rules()
        
        # 性能阈值
        self.thresholds = {
            'cpu_usage_warning': 70.0,
            'cpu_usage_critical': 90.0,
            'memory_usage_warning': 80.0,
            'memory_usage_critical': 95.0,
            'response_time_warning': 1.0,
            'response_time_critical': 5.0,
            'success_rate_warning': 95.0,
            'success_rate_critical': 90.0
        }
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_response_time': 0.0,
            'optimization_actions_taken': 0,
            'start_time': datetime.now()
        }
        
        logger.info("🔧 系统监控优化器初始化完成")
    
    def _setup_default_rules(self):
        """设置默认优化规则"""
        
        # 高CPU使用率优化
        self.add_optimization_rule(
            name="high_cpu_optimization",
            condition=lambda metrics: metrics.cpu_usage > self.thresholds['cpu_usage_critical'],
            action=self._optimize_high_cpu,
            priority=1
        )
        
        # 高内存使用率优化
        self.add_optimization_rule(
            name="high_memory_optimization",
            condition=lambda metrics: metrics.memory_usage > self.thresholds['memory_usage_critical'],
            action=self._optimize_high_memory,
            priority=1
        )
        
        # 响应时间优化
        self.add_optimization_rule(
            name="response_time_optimization",
            condition=lambda metrics: metrics.avg_response_time > self.thresholds['response_time_critical'],
            action=self._optimize_response_time,
            priority=2
        )
        
        # 成功率优化
        self.add_optimization_rule(
            name="success_rate_optimization",
            condition=lambda metrics: metrics.success_rate < self.thresholds['success_rate_critical'],
            action=self._optimize_success_rate,
            priority=1
        )
    
    def add_optimization_rule(self, name: str, condition: Callable[[PerformanceMetrics], bool],
                            action: Callable[[], None], priority: int = 1, enabled: bool = True):
        """添加优化规则"""
        rule = OptimizationRule(name, condition, action, priority, enabled)
        self.optimization_rules.append(rule)
        # 按优先级排序
        self.optimization_rules.sort(key=lambda x: x.priority)
        logger.info(f"✅ 添加优化规则: {name} (优先级: {priority})")
    
    def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("⚠️ 监控已在运行中")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🚀 系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("⏹️ 系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                self._collect_metrics()
                self._check_optimization_rules()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"❌ 监控循环错误: {e}")
                time.sleep(self.monitoring_interval)
    
    def _collect_metrics(self):
        """收集性能指标"""
        try:
            # 系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # 更新当前指标
            self.current_metrics.timestamp = datetime.now()
            self.current_metrics.cpu_usage = cpu_usage
            self.current_metrics.memory_usage = memory_usage
            
            # 计算查询相关指标
            if len(self.query_history) > 0:
                recent_queries = list(self.query_history)[-100:]  # 最近100个查询
                self.current_metrics.query_count = len(recent_queries)
                self.current_metrics.success_rate = sum(1 for q in recent_queries if q.get('success', False)) / len(recent_queries) * 100
                self.current_metrics.avg_response_time = sum(q.get('response_time', 0) for q in recent_queries) / len(recent_queries)
                self.current_metrics.error_count = sum(1 for q in recent_queries if not q.get('success', False))
            
            # 记录到历史
            self.performance_history.append(self.current_metrics)
            
        except Exception as e:
            logger.error(f"❌ 收集指标错误: {e}")
    
    def record_query(self, query_data: Dict[str, Any]):
        """记录查询数据"""
        query_data['timestamp'] = datetime.now()
        self.query_history.append(query_data)
        
        # 更新统计
        self.stats['total_queries'] += 1
        if query_data.get('success', False):
            self.stats['successful_queries'] += 1
        else:
            self.stats['failed_queries'] += 1
        
        self.stats['total_response_time'] += query_data.get('response_time', 0)
    
    def _check_optimization_rules(self):
        """检查优化规则"""
        for rule in self.optimization_rules:
            if not rule.enabled:
                continue
            
            try:
                if rule.condition(self.current_metrics):
                    logger.info(f"🔧 触发优化规则: {rule.name}")
                    rule.action()
                    self.stats['optimization_actions_taken'] += 1
            except Exception as e:
                logger.error(f"❌ 执行优化规则 {rule.name} 错误: {e}")
    
    def _optimize_high_cpu(self):
        """优化高CPU使用率"""
        logger.info("🔧 执行高CPU使用率优化")
        # 这里可以添加具体的优化逻辑
        # 例如：减少并发处理数量、启用缓存等
        pass
    
    def _optimize_high_memory(self):
        """优化高内存使用率"""
        logger.info("🔧 执行高内存使用率优化")
        # 这里可以添加具体的优化逻辑
        # 例如：清理缓存、减少内存占用等
        pass
    
    def _optimize_response_time(self):
        """优化响应时间"""
        logger.info("🔧 执行响应时间优化")
        # 这里可以添加具体的优化逻辑
        # 例如：启用缓存、优化算法等
        pass
    
    def _optimize_success_rate(self):
        """优化成功率"""
        logger.info("🔧 执行成功率优化")
        # 这里可以添加具体的优化逻辑
        # 例如：改进错误处理、优化算法等
        pass
    
    def get_current_status(self) -> Dict[str, Any]:
        """获取当前系统状态"""
        uptime = datetime.now() - self.stats['start_time']
        
        return {
            'monitoring_active': self.is_monitoring,
            'uptime_seconds': uptime.total_seconds(),
            'current_metrics': {
                'cpu_usage': self.current_metrics.cpu_usage,
                'memory_usage': self.current_metrics.memory_usage,
                'query_count': self.current_metrics.query_count,
                'success_rate': self.current_metrics.success_rate,
                'avg_response_time': self.current_metrics.avg_response_time,
                'error_count': self.current_metrics.error_count
            },
            'statistics': self.stats.copy(),
            'thresholds': self.thresholds.copy(),
            'optimization_rules_count': len(self.optimization_rules),
            'performance_history_size': len(self.performance_history),
            'query_history_size': len(self.query_history)
        }
    
    def get_performance_trends(self, hours: int = 1) -> Dict[str, Any]:
        """获取性能趋势"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.performance_history if m.timestamp >= cutoff_time]
        
        if not recent_metrics:
            return {'error': 'No data available for the specified time period'}
        
        # 计算趋势
        cpu_values = [m.cpu_usage for m in recent_metrics]
        memory_values = [m.memory_usage for m in recent_metrics]
        response_times = [m.avg_response_time for m in recent_metrics]
        success_rates = [m.success_rate for m in recent_metrics]
        
        return {
            'time_period_hours': hours,
            'data_points': len(recent_metrics),
            'cpu_trend': {
                'current': cpu_values[-1] if cpu_values else 0,
                'average': sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                'max': max(cpu_values) if cpu_values else 0,
                'min': min(cpu_values) if cpu_values else 0
            },
            'memory_trend': {
                'current': memory_values[-1] if memory_values else 0,
                'average': sum(memory_values) / len(memory_values) if memory_values else 0,
                'max': max(memory_values) if memory_values else 0,
                'min': min(memory_values) if memory_values else 0
            },
            'response_time_trend': {
                'current': response_times[-1] if response_times else 0,
                'average': sum(response_times) / len(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'min': min(response_times) if response_times else 0
            },
            'success_rate_trend': {
                'current': success_rates[-1] if success_rates else 0,
                'average': sum(success_rates) / len(success_rates) if success_rates else 0,
                'max': max(success_rates) if success_rates else 0,
                'min': min(success_rates) if success_rates else 0
            }
        }
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []
        
        # CPU使用率建议
        if self.current_metrics.cpu_usage > self.thresholds['cpu_usage_warning']:
            recommendations.append({
                'type': 'cpu_optimization',
                'priority': 'high' if self.current_metrics.cpu_usage > self.thresholds['cpu_usage_critical'] else 'medium',
                'message': f'CPU使用率过高 ({self.current_metrics.cpu_usage:.1f}%)',
                'suggestions': [
                    '减少并发处理数量',
                    '启用查询缓存',
                    '优化算法复杂度',
                    '考虑负载均衡'
                ]
            })
        
        # 内存使用率建议
        if self.current_metrics.memory_usage > self.thresholds['memory_usage_warning']:
            recommendations.append({
                'type': 'memory_optimization',
                'priority': 'high' if self.current_metrics.memory_usage > self.thresholds['memory_usage_critical'] else 'medium',
                'message': f'内存使用率过高 ({self.current_metrics.memory_usage:.1f}%)',
                'suggestions': [
                    '清理缓存数据',
                    '优化数据结构',
                    '减少内存占用',
                    '考虑内存池管理'
                ]
            })
        
        # 响应时间建议
        if self.current_metrics.avg_response_time > self.thresholds['response_time_warning']:
            recommendations.append({
                'type': 'response_time_optimization',
                'priority': 'high' if self.current_metrics.avg_response_time > self.thresholds['response_time_critical'] else 'medium',
                'message': f'平均响应时间过长 ({self.current_metrics.avg_response_time:.3f}s)',
                'suggestions': [
                    '启用查询缓存',
                    '优化数据库查询',
                    '使用异步处理',
                    '减少不必要的计算'
                ]
            })
        
        # 成功率建议
        if self.current_metrics.success_rate < self.thresholds['success_rate_warning']:
            recommendations.append({
                'type': 'success_rate_optimization',
                'priority': 'high' if self.current_metrics.success_rate < self.thresholds['success_rate_critical'] else 'medium',
                'message': f'成功率过低 ({self.current_metrics.success_rate:.1f}%)',
                'suggestions': [
                    '改进错误处理机制',
                    '增加输入验证',
                    '优化算法逻辑',
                    '增加重试机制'
                ]
            })
        
        return recommendations
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        # 计算平均响应时间
        avg_response_time = 0.0
        if self.stats['total_queries'] > 0:
            avg_response_time = self.stats['total_response_time'] / self.stats['total_queries']
        
        # 计算成功率
        success_rate = 0.0
        if self.stats['total_queries'] > 0:
            success_rate = (self.stats['successful_queries'] / self.stats['total_queries']) * 100
        
        # 计算错误率
        error_rate = 0.0
        if self.stats['total_queries'] > 0:
            error_rate = (self.stats['failed_queries'] / self.stats['total_queries']) * 100
        
        # 获取当前系统资源使用情况
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            memory_percent = memory.percent
        except:
            cpu_percent = 0.0
            memory_mb = 0.0
            memory_percent = 0.0
        
        return {
            'query_stats': {
                'total_queries': self.stats['total_queries'],
                'successful_queries': self.stats['successful_queries'],
                'failed_queries': self.stats['failed_queries']
            },
            'response_times': {
                'average': avg_response_time,
                'min': 0.0,  # 需要从历史记录中计算
                'max': 0.0   # 需要从历史记录中计算
            },
            'throughput': self.stats['total_queries'] / max(1, (datetime.now() - self.stats['start_time']).total_seconds()),
            'memory_usage': {
                'current_mb': memory_mb,
                'peak_mb': memory_mb,  # 简化处理
                'percentage': memory_percent
            },
            'cpu_usage': {
                'current_percent': cpu_percent,
                'peak_percent': cpu_percent  # 简化处理
            },
            'error_rate': error_rate,
            'monitoring_duration': (datetime.now() - self.stats['start_time']).total_seconds(),
            'optimization_rules_count': len(self.optimization_rules),
            'optimization_count': self.stats['optimization_actions_taken']
        }
    
    def export_metrics(self, filepath: str):
        """导出性能指标到文件"""
        try:
            data = {
                'export_time': datetime.now().isoformat(),
                'system_status': self.get_current_status(),
                'performance_trends': self.get_performance_trends(),
                'optimization_recommendations': self.get_optimization_recommendations(),
                'performance_history': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'cpu_usage': m.cpu_usage,
                        'memory_usage': m.memory_usage,
                        'query_count': m.query_count,
                        'success_rate': m.success_rate,
                        'avg_response_time': m.avg_response_time,
                        'error_count': m.error_count
                    }
                    for m in self.performance_history
                ],
                'query_history': [
                    {
                        'timestamp': q['timestamp'].isoformat() if 'timestamp' in q and hasattr(q['timestamp'], 'isoformat') else str(q.get('timestamp', '')),
                        'success': q.get('success', False),
                        'response_time': q.get('response_time', 0),
                        'confidence': q.get('confidence', 0)
                    }
                    for q in self.query_history
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ 性能指标已导出到: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导出指标失败: {e}")
            return False

# 全局监控器实例
_system_monitor = None

def get_system_monitor() -> SystemMonitorOptimizer:
    """获取系统监控器实例"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitorOptimizer()
    return _system_monitor

def start_system_monitoring():
    """启动系统监控"""
    monitor = get_system_monitor()
    monitor.start_monitoring()
    return monitor

def stop_system_monitoring():
    """停止系统监控"""
    monitor = get_system_monitor()
    monitor.stop_monitoring()
