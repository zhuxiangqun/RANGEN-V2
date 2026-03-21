#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资源监控器
提供系统资源监控和统计功能
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

class ResourceStatus(Enum):
    """资源状态"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used: int
    memory_total: int
    disk_usage_percent: float
    disk_used: int
    disk_total: int
    network_sent: int
    network_recv: int

@dataclass
class ResourceAlert:
    """资源告警"""
    alert_id: str
    resource_type: str
    status: ResourceStatus
    message: str
    threshold: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)

class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化资源监控器"""
        self.config = config or {}
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[ResourceAlert] = []
        self.monitoring_active = False
        
        # 从配置系统获取设置
        smart_config = get_unified_center('get_smart_config')
        if smart_config and hasattr(smart_config, 'get_config'):
            self.collection_interval = smart_config.get_config('resource_collection_interval', self.config, 30)
            self.alert_thresholds = smart_config.get_config('resource_alert_thresholds', self.config, {
                'cpu_percent': 80.0,
                'memory_percent': 85.0,
                'disk_usage_percent': 90.0
            })
        else:
            self.collection_interval = 30
            self.alert_thresholds = {
                'cpu_percent': 80.0,
                'memory_percent': 85.0,
                'disk_usage_percent': 90.0
            }
        
        logger.info("资源监控器初始化完成")
    
    def start_monitoring(self):
        """开始监控"""
        self.monitoring_active = True
        logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.monitoring_active = False
        logger.info("资源监控已停止")
    
    def collect_metrics(self) -> SystemMetrics:
        """收集系统资源指标"""
        try:
            current_time = datetime.now()
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used = memory.used
            memory_total = memory.total
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            disk_used = disk.used
            disk_total = disk.total
            
            # 网络信息
            network = psutil.net_io_counters()
            network_sent = network.bytes_sent
            network_recv = network.bytes_recv
            
            metrics = SystemMetrics(
                timestamp=current_time,
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used=memory_used,
                memory_total=memory_total,
                disk_usage_percent=disk_usage_percent,
                disk_used=disk_used,
                disk_total=disk_total,
                network_sent=network_sent,
                network_recv=network_recv
            )
            
            # 保存到历史记录
            self.metrics_history.append(metrics)
            
            # 限制历史记录大小
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集系统资源指标失败: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used=0,
                memory_total=0,
                disk_usage_percent=0.0,
                disk_used=0,
                disk_total=0,
                network_sent=0,
                network_recv=0
            )
    
    def check_alerts(self) -> List[ResourceAlert]:
        """检查资源告警"""
        new_alerts = []
        
        try:
            metrics = self.collect_metrics()
            
            # 检查CPU告警
            if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                alert = ResourceAlert(
                    alert_id=f"cpu_{int(time.time())}",
                    resource_type="cpu",
                    status=ResourceStatus.CRITICAL if metrics.cpu_percent > 90 else ResourceStatus.WARNING,
                    message=f"CPU使用率过高: {metrics.cpu_percent:.1f}%",
                    threshold=self.alert_thresholds['cpu_percent'],
                    current_value=metrics.cpu_percent
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
            
            # 检查内存告警
            if metrics.memory_percent > self.alert_thresholds['memory_percent']:
                alert = ResourceAlert(
                    alert_id=f"memory_{int(time.time())}",
                    resource_type="memory",
                    status=ResourceStatus.CRITICAL if metrics.memory_percent > 95 else ResourceStatus.WARNING,
                    message=f"内存使用率过高: {metrics.memory_percent:.1f}%",
                    threshold=self.alert_thresholds['memory_percent'],
                    current_value=metrics.memory_percent
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
            
            # 检查磁盘告警
            if metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
                alert = ResourceAlert(
                    alert_id=f"disk_{int(time.time())}",
                    resource_type="disk",
                    status=ResourceStatus.CRITICAL if metrics.disk_usage_percent > 95 else ResourceStatus.WARNING,
                    message=f"磁盘使用率过高: {metrics.disk_usage_percent:.1f}%",
                    threshold=self.alert_thresholds['disk_usage_percent'],
                    current_value=metrics.disk_usage_percent
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
            
        except Exception as e:
            logger.error(f"检查资源告警失败: {e}")
        
        return new_alerts
    
    def get_resource_summary(self, hours: int = 1) -> Dict[str, Any]:
        """获取资源摘要"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_metrics = [
            m for m in self.metrics_history
            if m.timestamp.timestamp() >= cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "没有可用的资源指标数据"}
        
        # 计算平均值
        avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
        avg_disk = sum(m.disk_usage_percent for m in recent_metrics) / len(recent_metrics)
        
        # 计算最大值
        max_cpu = max(m.cpu_percent for m in recent_metrics)
        max_memory = max(m.memory_percent for m in recent_metrics)
        max_disk = max(m.disk_usage_percent for m in recent_metrics)
        
        # 计算网络流量
        total_sent = recent_metrics[-1].network_sent - recent_metrics[0].network_sent
        total_recv = recent_metrics[-1].network_recv - recent_metrics[0].network_recv
        
        return {
            "period_hours": hours,
            "metrics_count": len(recent_metrics),
            "cpu": {
                "average_percent": avg_cpu,
                "max_percent": max_cpu,
                "current_percent": recent_metrics[-1].cpu_percent
            },
            "memory": {
                "average_percent": avg_memory,
                "max_percent": max_memory,
                "current_percent": recent_metrics[-1].memory_percent,
                "current_used_gb": recent_metrics[-1].memory_used / (1024**3),
                "total_gb": recent_metrics[-1].memory_total / (1024**3)
            },
            "disk": {
                "average_percent": avg_disk,
                "max_percent": max_disk,
                "current_percent": recent_metrics[-1].disk_usage_percent,
                "current_used_gb": recent_metrics[-1].disk_used / (1024**3),
                "total_gb": recent_metrics[-1].disk_total / (1024**3)
            },
            "network": {
                "total_sent_mb": total_sent / (1024**2),
                "total_recv_mb": total_recv / (1024**2),
                "current_sent": recent_metrics[-1].network_sent,
                "current_recv": recent_metrics[-1].network_recv
            }
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            metrics = self.collect_metrics()
            alerts = self.check_alerts()
            
            # 计算健康分数
            health_score = 100.0
            
            if metrics.cpu_percent > self.alert_thresholds['cpu_percent']:
                health_score -= (metrics.cpu_percent - self.alert_thresholds['cpu_percent']) * 2
            
            if metrics.memory_percent > self.alert_thresholds['memory_percent']:
                health_score -= (metrics.memory_percent - self.alert_thresholds['memory_percent']) * 2
            
            if metrics.disk_usage_percent > self.alert_thresholds['disk_usage_percent']:
                health_score -= (metrics.disk_usage_percent - self.alert_thresholds['disk_usage_percent']) * 2
            
            health_score = max(0, min(100, health_score))
            
            # 确定健康状态
            if health_score >= 80:
                status = ResourceStatus.NORMAL
            elif health_score >= 60:
                status = ResourceStatus.WARNING
            else:
                status = ResourceStatus.CRITICAL
            
            return {
                "timestamp": datetime.now().isoformat(),
                "health_score": health_score,
                "status": status.value,
                "active_alerts": len([a for a in alerts if a.status in [ResourceStatus.WARNING, ResourceStatus.CRITICAL]]),
                "total_alerts": len(self.alerts),
                "monitoring_active": self.monitoring_active,
                "metrics_count": len(self.metrics_history)
            }
            
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "health_score": 0,
                "status": ResourceStatus.UNKNOWN.value,
                "error": str(e)
            }

def get_resource_monitor(config: Optional[Dict[str, Any]] = None) -> ResourceMonitor:
    """获取资源监控器实例"""
    return ResourceMonitor(config)