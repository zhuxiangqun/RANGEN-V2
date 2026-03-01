#!/usr/bin/env python3
"""
内存管理模块 - 增强版
支持智能监控、优化和异常检测
"""

import gc
import sys
import os
import logging
import psutil
from typing import Dict, Any, Optional, List
from collections import deque
import threading
import time


class MemoryManager:
    """内存管理器 - 增强版，支持智能监控和优化"""
    
    def __init__(self, max_memory_mb: int = 1000):
        """初始化内存管理器"""
        self.max_memory_mb = max_memory_mb
        self.memory_usage = deque(maxlen=int(os.getenv("DEFAULT_TIMEOUT", "100")))
        self.lock = threading.Lock()
        self.monitoring = False
        self.monitor_thread = None
        self.cleanup_callbacks = []
        self.memory_overflow_count = 0
        
        # 增强功能
        self.memory_trends = deque(maxlen=50)  # 内存趋势分析
        self.optimization_history = []  # 优化历史记录
        self.anomaly_detection = []  # 异常检测结果
        self.auto_optimization = True  # 自动优化开关
        self.optimization_threshold = 0.8  # 优化阈值（80%）
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"增强内存管理器初始化完成，最大内存限制: {max_memory_mb}MB")

    def start_monitoring(self):
        """开始内存监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_memory, daemon=True)
        self.monitor_thread.start()
        self.logger.info("内存监控已启动")

    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        self.logger.info("内存监控已停止")

    def _monitor_memory(self):
        """监控内存使用情况"""
        while self.monitoring:
            try:
                memory_info = self.get_memory_info()
                with self.lock:
                    self.memory_usage.append(memory_info)
                
                # 检查内存使用是否超过限制
                if memory_info['used_mb'] > self.max_memory_mb:
                    self._handle_memory_overflow(memory_info)
                
                # 清理旧的内存使用记录
                self._cleanup_old_records()
                
                # 执行智能优化
                if self.auto_optimization:
                    self.intelligent_optimization()
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.logger.error(f"内存监控出错: {e}")
                time.sleep(5)  # 出错时等待5秒再继续
    
    def _handle_memory_overflow(self, memory_info: Dict[str, Any]):
        """处理内存溢出"""
        try:
            self.logger.warning(f"内存使用超过限制: {memory_info['used_mb']:.2f}MB > {self.max_memory_mb}MB")
            
            # 触发垃圾回收
            gc.collect()
            
            # 记录内存溢出事件
            self.memory_overflow_count += 1
            
            # 如果内存仍然过高，记录警告
            current_memory = self.get_memory_info()
            if current_memory['used_mb'] > self.max_memory_mb * 0.9:
                self.logger.error("内存使用仍然过高，建议检查内存泄漏")
                
        except Exception as e:
            self.logger.error(f"处理内存溢出失败: {e}")
    
    def _cleanup_old_records(self):
        """清理旧的内存使用记录"""
        try:
            # 只保留最近1000条记录
            max_records = 1000
            if len(self.memory_usage) > max_records:
                with self.lock:
                    if self.memory_usage:
                        # 使用列表推导式来保留最近的记录
                        if len(self.memory_usage) > max_records:
                            self.memory_usage = [self.memory_usage[i] for i in range(len(self.memory_usage) - max_records, len(self.memory_usage))]
        except Exception as e:
            self.logger.warning(f"清理旧记录失败: {e}")

    def get_memory_info(self) -> Dict[str, Any]:
        """获取内存使用信息"""
        try:
            # 获取当前进程内存使用情况
            process = psutil.Process()
            memory_info = process.memory_info()
            used_mb = memory_info.rss / (1024 * 1024)
            
            return {
                'used_mb': used_mb,
                'max_mb': self.max_memory_mb,
                'percent': (used_mb / self.max_memory_mb) * 100,
                'timestamp': time.time()
            }
        except Exception as e:
            self.logger.error(f"获取内存信息失败: {e}")
            return {
                'used_mb': 0,
                'max_mb': self.max_memory_mb,
                'percent': 0,
                'timestamp': time.time()
            }

    def cleanup_memory(self):
        """清理内存"""
        try:
            # 执行垃圾回收
            collected = gc.collect()
            self.logger.info(f"垃圾回收完成，回收对象数: {collected}")
            
            # 执行清理回调
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"清理回调执行失败: {e}")
            
        except Exception as e:
            self.logger.error(f"内存清理失败: {e}")

    def add_cleanup_callback(self, callback):
        """添加清理回调"""
        self.cleanup_callbacks.append(callback)

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计信息"""
        with self.lock:
            return {
                'total_records': len(self.memory_usage),
                'max_memory_mb': self.max_memory_mb,
                'current_usage_mb': self.memory_usage[-1]['used_mb'] if self.memory_usage else 0,
                'monitoring_active': self.monitoring,
                'overflow_count': self.memory_overflow_count
            }

    def analyze_memory_trends(self) -> Dict[str, Any]:
        """分析内存趋势"""
        try:
            if len(self.memory_usage) < 5:
                return {"message": "数据不足，无法分析趋势"}
            
            recent_usage = list(self.memory_usage)[-10:]
            usage_percentages = [usage['percent'] for usage in recent_usage]
            
            # 计算趋势
            trend_analysis = {
                'current_usage': usage_percentages[-1] if usage_percentages else 0,
                'average_usage': sum(usage_percentages) / len(usage_percentages),
                'max_usage': max(usage_percentages),
                'min_usage': min(usage_percentages),
                'trend_direction': 'stable',
                'volatility': 0.0
            }
            
            # 计算趋势方向
            if len(usage_percentages) >= 3:
                recent_avg = sum(usage_percentages[-3:]) / 3
                earlier_avg = sum(usage_percentages[-6:-3]) / 3 if len(usage_percentages) >= 6 else recent_avg
                
                if recent_avg > earlier_avg * 1.05:
                    trend_analysis['trend_direction'] = 'increasing'
                elif recent_avg < earlier_avg * 0.95:
                    trend_analysis['trend_direction'] = 'decreasing'
            
            # 计算波动性
            if len(usage_percentages) > 1:
                variance = sum((x - trend_analysis['average_usage']) ** 2 for x in usage_percentages) / len(usage_percentages)
                trend_analysis['volatility'] = variance ** 0.5
            
            # 记录趋势数据
            self.memory_trends.append({
                'timestamp': time.time(),
                'analysis': trend_analysis
            })
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"内存趋势分析失败: {e}")
            return {"error": str(e)}
    
    def detect_memory_anomalies(self) -> List[Dict[str, Any]]:
        """检测内存异常"""
        try:
            anomalies = []
            
            if len(self.memory_usage) < 5:
                return anomalies
            
            recent_usage = list(self.memory_usage)[-10:]
            usage_percentages = [usage['percent'] for usage in recent_usage]
            
            # 检测突然增长
            if len(usage_percentages) >= 3:
                current = usage_percentages[-1]
                previous = usage_percentages[-2]
                
                if current > previous * 1.5:  # 增长超过50%
                    anomalies.append({
                        'type': 'sudden_increase',
                        'severity': 'high',
                        'current': current,
                        'previous': previous,
                        'increase_percent': ((current - previous) / previous) * 100,
                        'timestamp': time.time(),
                        'message': f"内存使用突然增长: {previous:.1f}% -> {current:.1f}%"
                    })
            
            # 检测持续高使用率
            high_usage_count = sum(1 for usage in usage_percentages if usage > 90)
            if high_usage_count >= 3:
                anomalies.append({
                    'type': 'persistent_high_usage',
                    'severity': 'critical',
                    'count': high_usage_count,
                    'timestamp': time.time(),
                    'message': f"连续{high_usage_count}次检测到内存使用率超过90%"
                })
            
            # 检测内存泄漏模式
            if len(usage_percentages) >= 10:
                # 检查是否有持续增长趋势
                growth_count = 0
                for i in range(1, len(usage_percentages)):
                    if usage_percentages[i] > usage_percentages[i-1]:
                        growth_count += 1
                
                if growth_count >= 7:  # 10次中有7次增长
                    anomalies.append({
                        'type': 'potential_memory_leak',
                        'severity': 'medium',
                        'growth_count': growth_count,
                        'timestamp': time.time(),
                        'message': f"检测到潜在内存泄漏，{growth_count}/10次检测显示增长"
                    })
            
            # 记录异常
            self.anomaly_detection.extend(anomalies)
            
            # 保持异常记录在合理范围内
            if len(self.anomaly_detection) > 100:
                self.anomaly_detection = self.anomaly_detection[-50:]
            
            return anomalies
            
        except Exception as e:
            self.logger.error(f"内存异常检测失败: {e}")
            return []
    
    def intelligent_optimization(self) -> Dict[str, Any]:
        """智能内存优化"""
        try:
            if not self.auto_optimization:
                return {"message": "自动优化已禁用"}
            
            current_usage = self.get_memory_info()
            usage_percent = current_usage['percent'] / 100
            
            optimization_result = {
                'triggered': False,
                'actions_taken': [],
                'memory_freed_mb': 0,
                'optimization_level': 'none'
            }
            
            # 根据使用率决定优化策略
            if usage_percent > self.optimization_threshold:
                optimization_result['triggered'] = True
                optimization_result['optimization_level'] = 'aggressive'
                
                # 执行垃圾回收
                collected = gc.collect()
                optimization_result['actions_taken'].append(f"垃圾回收: 回收了{collected}个对象")
                
                # 清理内存使用记录
                with self.lock:
                    old_size = len(self.memory_usage)
                    self.memory_usage.clear()
                    optimization_result['actions_taken'].append(f"清理内存记录: 清理了{old_size}条记录")
                
                # 执行清理回调
                for callback in self.cleanup_callbacks:
                    try:
                        callback()
                        optimization_result['actions_taken'].append("执行清理回调")
                    except Exception as e:
                        self.logger.warning(f"清理回调执行失败: {e}")
                
                # 记录优化历史
                self.optimization_history.append({
                    'timestamp': time.time(),
                    'trigger_usage': usage_percent,
                    'actions': optimization_result['actions_taken'],
                    'level': optimization_result['optimization_level']
                })
                
                # 保持历史记录在合理范围内
                if len(self.optimization_history) > 50:
                    self.optimization_history = self.optimization_history[-25:]
                
                self.logger.info(f"智能内存优化完成: {optimization_result}")
            
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"智能内存优化失败: {e}")
            return {"error": str(e)}
    
    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        try:
            recommendations = []
            
            # 基于趋势分析提供建议
            trend_analysis = self.analyze_memory_trends()
            
            if trend_analysis.get('trend_direction') == 'increasing':
                recommendations.append({
                    'type': 'trend',
                    'priority': 'medium',
                    'message': '内存使用呈上升趋势',
                    'suggestion': '考虑优化内存使用或增加内存限制'
                })
            
            if trend_analysis.get('volatility', 0) > 10:
                recommendations.append({
                    'type': 'volatility',
                    'priority': 'low',
                    'message': '内存使用波动较大',
                    'suggestion': '检查是否有内存分配/释放不均衡的情况'
                })
            
            # 基于异常检测提供建议
            recent_anomalies = [a for a in self.anomaly_detection if time.time() - a['timestamp'] < 3600]  # 最近1小时
            
            if any(a['type'] == 'potential_memory_leak' for a in recent_anomalies):
                recommendations.append({
                    'type': 'memory_leak',
                    'priority': 'high',
                    'message': '检测到潜在内存泄漏',
                    'suggestion': '检查代码中是否有未释放的资源或循环引用'
                })
            
            if any(a['type'] == 'persistent_high_usage' for a in recent_anomalies):
                recommendations.append({
                    'type': 'high_usage',
                    'priority': 'critical',
                    'message': '内存使用率持续过高',
                    'suggestion': '立即检查内存使用情况，考虑增加内存或优化代码'
                })
            
            # 基于优化历史提供建议
            if len(self.optimization_history) > 5:
                recent_optimizations = self.optimization_history[-5:]
                frequent_optimization = len([o for o in recent_optimizations if o['level'] == 'aggressive']) >= 3
                
                if frequent_optimization:
                    recommendations.append({
                        'type': 'frequent_optimization',
                        'priority': 'medium',
                        'message': '频繁触发内存优化',
                        'suggestion': '考虑调整优化阈值或优化内存使用模式'
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"获取优化建议失败: {e}")
            return []
    
    def get_memory_analytics(self) -> Dict[str, Any]:
        """获取内存分析报告"""
        try:
            current_info = self.get_memory_info()
            trend_analysis = self.analyze_memory_trends()
            recent_anomalies = [a for a in self.anomaly_detection if time.time() - a['timestamp'] < 3600]
            recommendations = self.get_optimization_recommendations()
            
            return {
                'current_status': current_info,
                'trend_analysis': trend_analysis,
                'recent_anomalies': recent_anomalies,
                'optimization_recommendations': recommendations,
                'optimization_history_count': len(self.optimization_history),
                'anomaly_detection_count': len(self.anomaly_detection),
                'auto_optimization_enabled': self.auto_optimization,
                'optimization_threshold': self.optimization_threshold
            }
            
        except Exception as e:
            self.logger.error(f"获取内存分析报告失败: {e}")
            return {"error": str(e)}
    
    def cleanup(self):
        """清理资源"""
        try:
            self.stop_monitoring()
            self.cleanup_callbacks.clear()
            with self.lock:
                self.memory_usage.clear()
                self.memory_trends.clear()
            self.optimization_history.clear()
            self.anomaly_detection.clear()
            self.logger.info("增强内存管理器清理完成")
        except Exception as e:
            self.logger.error(f"内存管理器清理失败: {e}")


# 创建全局实例
memory_manager = MemoryManager()


def get_memory_manager() -> MemoryManager:
    """获取内存管理器实例"""
    return memory_manager