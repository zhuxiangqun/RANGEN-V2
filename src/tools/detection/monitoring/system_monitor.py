#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统监控器
提供系统性能监控和指标收集功能
"""

import time
import psutil
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.utils.unified_centers import get_unified_center

# 初始化日志
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """系统健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class MetricDataPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    metric_name: str
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class SystemHealthStatus:
    """系统健康状态"""
    status: HealthStatus
    score: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class AlertInfo:
    """告警信息"""
    alert_id: str
    severity: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化系统监控器"""
        self.config = config or {}
        self.metrics_history: List[MetricDataPoint] = []
        self.alerts: List[AlertInfo] = []
        self.monitoring_active = False
        
        # 从配置系统获取设置
        smart_config = get_unified_center('get_smart_config')
        if smart_config and hasattr(smart_config, 'get_config'):
            self.collection_interval = smart_config.get_config('monitor_collection_interval', self.config, 60)
            self.alert_thresholds = smart_config.get_config('monitor_alert_thresholds', self.config, {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'disk_usage': 90.0
            })
        else:
            self.collection_interval = 60
            self.alert_thresholds = {
                'cpu_usage': 80.0,
                'memory_usage': 85.0,
                'disk_usage': 90.0
            }
        
        logger.info("系统监控器初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring_active = True
        logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        logger.info("系统监控已停止")
    
    def collect_metrics(self) -> List[MetricDataPoint]:
        """收集系统指标"""
        metrics = []
        current_time = datetime.now()
        
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(MetricDataPoint(
                timestamp=current_time,
                value=cpu_percent,
                metric_name="cpu_usage",
                tags={"type": "system"}
            ))
            
            # 内存使用率
            memory = psutil.virtual_memory()
            metrics.append(MetricDataPoint(
                timestamp=current_time,
                value=memory.percent,
                metric_name="memory_usage",
                tags={"type": "system"}
            ))
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            metrics.append(MetricDataPoint(
                timestamp=current_time,
                value=disk_percent,
                metric_name="disk_usage",
                tags={"type": "system"}
            ))
            
            # 网络I/O
            network = psutil.net_io_counters()
            metrics.append(MetricDataPoint(
                timestamp=current_time,
                value=network.bytes_sent,
                metric_name="network_bytes_sent",
                tags={"type": "network"}
            ))
            
            metrics.append(MetricDataPoint(
                timestamp=current_time,
                value=network.bytes_recv,
                metric_name="network_bytes_recv",
                tags={"type": "network"}
            ))
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
        
        # 保存到历史记录
        self.metrics_history.extend(metrics)
        
        # 限制历史记录大小
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def check_health(self) -> SystemHealthStatus:
        """检查系统健康状态"""
        try:
            metrics = self.collect_metrics()
            
            # 计算健康分数
            health_score = 100.0
            status = HealthStatus.HEALTHY
            message = "系统运行正常"
            
            for metric in metrics:
                if metric.metric_name in self.alert_thresholds:
                    threshold = self.alert_thresholds[metric.metric_name]
                    if metric.value > threshold:
                        health_score -= (metric.value - threshold) * 2
                        
                        if metric.value > threshold * 1.2:
                            status = HealthStatus.CRITICAL
                            message = f"{metric.metric_name} 使用率过高: {metric.value:.1f}%"
                        elif status == HealthStatus.HEALTHY:
                            status = HealthStatus.WARNING
                            message = f"{metric.metric_name} 使用率较高: {metric.value:.1f}%"
            
            # 确保分数在0-100范围内
            health_score = max(0, min(100, health_score))
            
            return SystemHealthStatus(
                status=status,
                score=health_score,
                message=message
            )
            
        except Exception as e:
            logger.error(f"检查系统健康状态失败: {e}")
            return SystemHealthStatus(
                status=HealthStatus.UNKNOWN,
                score=0.0,
                message=f"健康检查失败: {str(e)}"
            )
    
    def check_alerts(self) -> List[AlertInfo]:
        """检查告警"""
        new_alerts = []
        
        try:
            health_status = self.check_health()
            
            if health_status.status == HealthStatus.CRITICAL:
                alert = AlertInfo(
                    alert_id=f"critical_{int(time.time())}",
                    severity="critical",
                    message=health_status.message
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
            
            elif health_status.status == HealthStatus.WARNING:
                alert = AlertInfo(
                    alert_id=f"warning_{int(time.time())}",
                    severity="warning",
                    message=health_status.message
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
            
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
        
        return new_alerts
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取指标摘要"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp.timestamp() >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "没有可用的指标数据"}
        
        # 按指标类型分组
        metrics_by_name = {}
        for metric in recent_metrics:
            if metric.metric_name not in metrics_by_name:
                metrics_by_name[metric.metric_name] = []
            metrics_by_name[metric.metric_name].append(metric.value)
        
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
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        health_status = self.check_health()
        metrics_summary = self.get_metrics_summary()
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health_status": {
                "status": health_status.status.value,
                "score": health_status.score,
                "message": health_status.message
            },
            "metrics_summary": metrics_summary,
            "alerts": {
                "active_count": len(active_alerts),
                "total_count": len(self.alerts),
                "recent_alerts": [alert.__dict__ for alert in active_alerts[-5:]]
            },
            "monitoring_status": {
                "active": self.monitoring_active,
                "collection_interval": self.collection_interval,
                "metrics_count": len(self.metrics_history)
            }
        }

def get_system_monitor(config: Optional[Dict[str, Any]] = None) -> SystemMonitor:
    """获取系统监控器实例"""
    return SystemMonitor(config)