#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能监控器
提供系统性能监控和指标收集功能
"""

import time
import psutil
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import json

from src.utils.unified_centers import get_unified_center

# 初始化日志
logger = logging.getLogger(__name__)

class PerformanceLevel(Enum):
    """性能等级"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    level: PerformanceLevel
    description: str = ""

@dataclass
class PerformanceTrend:
    """性能趋势"""
    metric_name: str
    trend_direction: str  # "improving", "stable", "declining", "volatile"
    trend_strength: float  # 0.0-1.0
    change_percentage: float
    time_period: str
    data_points: List[float]
    prediction: Optional[float] = None
    confidence: float = 0.0

@dataclass
class TrendAnalysis:
    """趋势分析结果"""
    timestamp: datetime
    overall_trend: str
    trend_score: float  # 0.0-1.0
    metric_trends: List[PerformanceTrend]
    recommendations: List[str]
    alerts: List[str] = field(default_factory=list)

@dataclass
class PerformanceReport:
    """性能报告"""
    timestamp: datetime
    overall_score: float
    level: PerformanceLevel
    metrics: List[PerformanceMetric]
    recommendations: List[str] = field(default_factory=list)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化性能监控器"""
        self.config = config or {}
        self.metrics_history: List[PerformanceMetric] = []
        self.timers: Dict[str, float] = {}
        self.trend_data: Dict[str, deque] = {}  # 存储趋势数据
        self.trend_window_size = 50  # 趋势分析窗口大小
        
        # 从配置系统获取设置
        smart_config = get_unified_center('get_smart_config')
        if smart_config and hasattr(smart_config, 'get_config'):
            self.collection_interval = smart_config.get_config('performance_collection_interval', self.config, 30)
            self.performance_thresholds = smart_config.get_config('performance_thresholds', self.config, {
                'cpu_usage': {'excellent': 20, 'good': 40, 'fair': 60, 'poor': 80},
                'memory_usage': {'excellent': 30, 'good': 50, 'fair': 70, 'poor': 85},
                'response_time': {'excellent': 0.1, 'good': 0.5, 'fair': 1.0, 'poor': 2.0}
            })
        else:
            self.collection_interval = 30
            self.performance_thresholds = {
                'cpu_usage': {'excellent': 20, 'good': 40, 'fair': 60, 'poor': 80},
                'memory_usage': {'excellent': 30, 'good': 50, 'fair': 70, 'poor': 85},
                'response_time': {'excellent': 0.1, 'good': 0.5, 'fair': 1.0, 'poor': 2.0}
            }
        
        logger.info("性能监控器初始化完成")
    
    def start_timer(self, name: str) -> None:
        """开始计时"""
        self.timers[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时"""
        if name not in self.timers:
            logger.warning(f"计时器 {name} 未找到")
            return 0.0
        
        elapsed = time.time() - self.timers[name]
        del self.timers[name]
        return elapsed
    
    def collect_system_metrics(self) -> List[PerformanceMetric]:
        """收集系统性能指标"""
        metrics = []
        current_time = datetime.now()
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_level = self._get_performance_level('cpu_usage', cpu_percent)
            metrics.append(PerformanceMetric(
                name="cpu_usage",
                value=cpu_percent,
                unit="%",
                timestamp=current_time,
                level=cpu_level,
                description="CPU使用率"
            ))
            
            # 内存使用率
            memory = psutil.virtual_memory()
            memory_level = self._get_performance_level('memory_usage', memory.percent)
            metrics.append(PerformanceMetric(
                name="memory_usage",
                value=memory.percent,
                unit="%",
                timestamp=current_time,
                level=memory_level,
                description="内存使用率"
            ))
            
            # 磁盘I/O
            disk_io = psutil.disk_io_counters()
            if disk_io:
                metrics.append(PerformanceMetric(
                    name="disk_read_bytes",
                    value=disk_io.read_bytes,
                    unit="bytes",
                    timestamp=current_time,
                    level=PerformanceLevel.GOOD,
                    description="磁盘读取字节数"
                ))
                
                metrics.append(PerformanceMetric(
                    name="disk_write_bytes",
                    value=disk_io.write_bytes,
                    unit="bytes",
                    timestamp=current_time,
                    level=PerformanceLevel.GOOD,
                    description="磁盘写入字节数"
                ))
            
            # 网络I/O
            network_io = psutil.net_io_counters()
            if network_io:
                metrics.append(PerformanceMetric(
                    name="network_sent_bytes",
                    value=network_io.bytes_sent,
                    unit="bytes",
                    timestamp=current_time,
                    level=PerformanceLevel.GOOD,
                    description="网络发送字节数"
                ))
                
                metrics.append(PerformanceMetric(
                    name="network_recv_bytes",
                    value=network_io.bytes_recv,
                    unit="bytes",
                    timestamp=current_time,
                    level=PerformanceLevel.GOOD,
                    description="网络接收字节数"
                ))
            
        except Exception as e:
            logger.error(f"收集系统性能指标失败: {e}")
        
        # 保存到历史记录
        self.metrics_history.extend(metrics)
        
        # 更新趋势数据
        self._update_trend_data(metrics)
        
        # 限制历史记录大小
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def _get_performance_level(self, metric_name: str, value: float) -> PerformanceLevel:
        """获取性能等级"""
        if metric_name not in self.performance_thresholds:
            return PerformanceLevel.GOOD
        
        thresholds = self.performance_thresholds[metric_name]
        
        if value <= thresholds.get('excellent', 0):
            return PerformanceLevel.EXCELLENT
        elif value <= thresholds.get('good', 0):
            return PerformanceLevel.GOOD
        elif value <= thresholds.get('fair', 0):
            return PerformanceLevel.FAIR
        elif value <= thresholds.get('poor', 0):
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL
    
    def generate_performance_report(self) -> PerformanceReport:
        """生成性能报告"""
        current_time = datetime.now()
        metrics = self.collect_system_metrics()
        
        # 计算总体性能分数
        if not metrics:
            return PerformanceReport(
                timestamp=current_time,
                overall_score=0.0,
                level=PerformanceLevel.CRITICAL,
                metrics=[],
                recommendations=["无法收集性能指标"]
            )
        
        # 计算平均分数
        total_score = 0.0
        level_scores = {
            PerformanceLevel.EXCELLENT: 100,
            PerformanceLevel.GOOD: 80,
            PerformanceLevel.FAIR: 60,
            PerformanceLevel.POOR: 40,
            PerformanceLevel.CRITICAL: 20
        }
        
        for metric in metrics:
            total_score += level_scores.get(metric.level, 0)
        
        overall_score = total_score / len(metrics)
        
        # 确定总体性能等级
        if overall_score >= 90:
            overall_level = PerformanceLevel.EXCELLENT
        elif overall_score >= 70:
            overall_level = PerformanceLevel.GOOD
        elif overall_score >= 50:
            overall_level = PerformanceLevel.FAIR
        elif overall_score >= 30:
            overall_level = PerformanceLevel.POOR
        else:
            overall_level = PerformanceLevel.CRITICAL
        
        # 生成建议
        recommendations = self._generate_recommendations(metrics, overall_level)
        
        return PerformanceReport(
            timestamp=current_time,
            overall_score=overall_score,
            level=overall_level,
            metrics=metrics,
            recommendations=recommendations
        )
    
    def _generate_recommendations(self, metrics: List[PerformanceMetric], level: PerformanceLevel) -> List[str]:
        """生成性能优化建议"""
        recommendations = []
        
        for metric in metrics:
            if metric.level == PerformanceLevel.CRITICAL:
                if metric.name == "cpu_usage":
                    recommendations.append("CPU使用率过高，建议优化算法或增加CPU资源")
                elif metric.name == "memory_usage":
                    recommendations.append("内存使用率过高，建议优化内存使用或增加内存")
                elif "response_time" in metric.name:
                    recommendations.append("响应时间过长，建议优化代码性能")
            elif metric.level == PerformanceLevel.POOR:
                if metric.name == "cpu_usage":
                    recommendations.append("CPU使用率较高，建议监控并考虑优化")
                elif metric.name == "memory_usage":
                    recommendations.append("内存使用率较高，建议检查内存泄漏")
        
        if level == PerformanceLevel.CRITICAL:
            recommendations.append("系统性能严重不足，建议立即进行性能优化")
        elif level == PerformanceLevel.POOR:
            recommendations.append("系统性能较差，建议进行性能调优")
        elif level == PerformanceLevel.FAIR:
            recommendations.append("系统性能一般，建议持续监控")
        elif level == PerformanceLevel.EXCELLENT:
            recommendations.append("系统性能优秀，继续保持")
        
        return recommendations
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp.timestamp() >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "没有可用的性能指标数据"}
        
        # 按指标名称分组
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.name not in metrics_by_name:
                metrics_by_name[metric.name] = []
            metrics_by_name[metric.name].append(metric.value)
        
        # 计算统计信息
        summary = {}
        for name, values in metrics_by_name.items():
            summary[name] = {
                "count": len(values),
                "average": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1] if values else 0
            }
        
        return summary
    
    def export_metrics(self) -> Dict[str, Any]:
        """导出指标数据"""
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics_count": len(self.metrics_history),
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "level": m.level.value,
                    "timestamp": m.timestamp.isoformat(),
                    "description": m.description
                }
                for m in self.metrics_history[-100:]  # 最近100个指标
            ]
        }

    def _update_trend_data(self, metrics: List[PerformanceMetric]) -> None:
        """更新趋势数据"""
        for metric in metrics:
            if metric.name not in self.trend_data:
                self.trend_data[metric.name] = deque(maxlen=self.trend_window_size)
            
            self.trend_data[metric.name].append(metric.value)
    
    def analyze_trends(self, time_period: str = "1h") -> TrendAnalysis:
        """分析性能趋势"""
        current_time = datetime.now()
        metric_trends = []
        overall_trend_score = 0.0
        recommendations = []
        alerts = []
        
        for metric_name, data_points in self.trend_data.items():
            if len(data_points) < 3:  # 需要至少3个数据点
                continue
            
            trend = self._calculate_trend(metric_name, list(data_points), time_period)
            metric_trends.append(trend)
            
            # 计算趋势分数
            trend_score = self._get_trend_score(trend)
            overall_trend_score += trend_score
            
            # 生成建议和告警
            if trend.trend_direction == "declining":
                alerts.append(f"指标 {metric_name} 性能下降 {trend.change_percentage:.1f}%")
                recommendations.append(f"建议优化 {metric_name} 相关配置")
            elif trend.trend_direction == "volatile":
                alerts.append(f"指标 {metric_name} 性能波动较大")
                recommendations.append(f"建议检查 {metric_name} 的稳定性")
        
        # 计算总体趋势
        if metric_trends:
            overall_trend_score /= len(metric_trends)
        
        if overall_trend_score >= 0.7:
            overall_trend = "improving"
        elif overall_trend_score >= 0.4:
            overall_trend = "stable"
        else:
            overall_trend = "declining"
        
        return TrendAnalysis(
            timestamp=current_time,
            overall_trend=overall_trend,
            trend_score=overall_trend_score,
            metric_trends=metric_trends,
            recommendations=recommendations,
            alerts=alerts
        )
    
    def _calculate_trend(self, metric_name: str, data_points: List[float], time_period: str) -> PerformanceTrend:
        """计算单个指标的趋势"""
        if len(data_points) < 2:
            return PerformanceTrend(
                metric_name=metric_name,
                trend_direction="stable",
                trend_strength=0.0,
                change_percentage=0.0,
                time_period=time_period,
                data_points=data_points
            )
        
        # 计算线性回归斜率
        n = len(data_points)
        x = list(range(n))
        y = data_points
        
        # 简单线性回归
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        # 计算变化百分比
        first_value = data_points[0]
        last_value = data_points[-1]
        change_percentage = ((last_value - first_value) / first_value) * 100 if first_value != 0 else 0
        
        # 确定趋势方向
        if abs(slope) < 0.01:  # 斜率很小
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "improving" if self._is_positive_trend(metric_name) else "declining"
        else:
            trend_direction = "declining" if self._is_positive_trend(metric_name) else "improving"
        
        # 计算趋势强度
        trend_strength = min(abs(slope) * 10, 1.0)  # 标准化到0-1
        
        # 计算预测值（简单线性外推）
        prediction = None
        confidence = 0.0
        if len(data_points) >= 5:
            prediction = last_value + slope
            confidence = min(trend_strength * 0.8, 0.8)  # 最大80%置信度
        
        return PerformanceTrend(
            metric_name=metric_name,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            change_percentage=change_percentage,
            time_period=time_period,
            data_points=data_points,
            prediction=prediction,
            confidence=confidence
        )
    
    def _is_positive_trend(self, metric_name: str) -> bool:
        """判断指标值增加是否为正面趋势"""
        # 对于某些指标，值增加是负面的（如CPU使用率、内存使用率）
        negative_metrics = {'cpu_usage', 'memory_usage', 'disk_usage', 'response_time', 'error_rate'}
        return metric_name not in negative_metrics
    
    def _get_trend_score(self, trend: PerformanceTrend) -> float:
        """计算趋势分数"""
        if trend.trend_direction == "improving":
            return 0.8 + trend.trend_strength * 0.2
        elif trend.trend_direction == "stable":
            return 0.5 + trend.trend_strength * 0.3
        elif trend.trend_direction == "declining":
            return 0.2 - trend.trend_strength * 0.2
        else:  # volatile
            return 0.3
    
    def get_trend_summary(self) -> Dict[str, Any]:
        """获取趋势摘要"""
        trend_analysis = self.analyze_trends()
        
        return {
            "timestamp": trend_analysis.timestamp.isoformat(),
            "overall_trend": trend_analysis.overall_trend,
            "trend_score": trend_analysis.trend_score,
            "metric_count": len(trend_analysis.metric_trends),
            "alerts_count": len(trend_analysis.alerts),
            "recommendations_count": len(trend_analysis.recommendations),
            "top_concerns": [
                {
                    "metric": trend.metric_name,
                    "trend": trend.trend_direction,
                    "change": trend.change_percentage
                }
                for trend in trend_analysis.metric_trends
                if trend.trend_direction in ["declining", "volatile"]
            ][:3]  # 只显示前3个关注点
        }

def get_performance_monitor(config: Optional[Dict[str, Any]] = None) -> PerformanceMonitor:
    """获取性能监控器实例"""
    return PerformanceMonitor(config)

# 便捷函数
def record_metric(name: str, value: float, unit: str = "", description: str = "") -> None:
    """记录指标"""
    monitor = get_performance_monitor()
    metric = PerformanceMetric(
        name=name,
        value=value,
        unit=unit,
        timestamp=datetime.now(),
        level=PerformanceLevel.GOOD,
        description=description
    )
    monitor.metrics_history.append(metric)

def start_timer(name: str) -> None:
    """开始计时"""
    monitor = get_performance_monitor()
    monitor.start_timer(name)

def end_timer(name: str) -> float:
    """结束计时"""
    monitor = get_performance_monitor()
    return monitor.end_timer(name)