"""
统一监控服务模块

合并以下服务:
- MetricsService (metrics_service.py)
- PerformanceMonitor (performance_monitor.py)
- MonitoringDashboardService (monitoring_dashboard_service.py)
- SystemHealthMonitor (system_health_monitor.py)
- ServiceHealthChecker (service_health_checker.py)
- AutoscalingService (autoscaling_service.py)
- AdvancedAutoscalingService (advanced_autoscaling_service.py)

使用示例:
```python
from src.services.monitoring import MonitoringService

monitor = MonitoringService()
metrics = monitor.collect_metrics()
health = monitor.check_health()
```
"""

import time
import psutil
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass


# ============== Enums ==============

class MetricCategory(str, Enum):
    """指标类别"""
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK = "disk"
    CUSTOM = "custom"


class MetricUnit(str, Enum):
    """指标单位"""
    PERCENT = "percent"
    BYTES = "bytes"
    COUNT = "count"
    MS = "ms"


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ScalingDecision(str, Enum):
    """扩缩容决策"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"


# ============== Data Classes ==============

@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: float
    unit: MetricUnit
    category: MetricCategory
    timestamp: float


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    service: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: float


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    source: str
    message: str
    timestamp: float
    metadata: Dict[str, Any]


# ============== Main Class ==============

class MonitoringService:
    """
    统一监控服务
    
    提供:
    - 指标收集 (Metrics)
    - 性能监控 (Performance)
    - 健康检查 (Health)
    - 告警 (Alerts)
    - 自动扩缩容 (Autoscaling)
    """
    
    def __init__(self):
        self._metrics_history: List[MetricValue] = []
        self._alerts: List[Alert] = []
        self._max_history = 1000
        self._max_alerts = 100
    
    # ============== Metrics ==============
    
    def collect_metrics(self) -> List[MetricValue]:
        """收集系统指标"""
        metrics = []
        timestamp = time.time()
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=0.1)
        metrics.append(MetricValue(
            name="cpu_percent",
            value=cpu_percent,
            unit=MetricUnit.PERCENT,
            category=MetricCategory.CPU,
            timestamp=timestamp
        ))
        
        # Memory
        memory = psutil.virtual_memory()
        metrics.append(MetricValue(
            name="memory_percent",
            value=memory.percent,
            unit=MetricUnit.PERCENT,
            category=MetricCategory.MEMORY,
            timestamp=timestamp
        ))
        metrics.append(MetricValue(
            name="memory_used",
            value=memory.used,
            unit=MetricUnit.BYTES,
            category=MetricCategory.MEMORY,
            timestamp=timestamp
        ))
        
        # Disk
        disk = psutil.disk_usage('/')
        metrics.append(MetricValue(
            name="disk_percent",
            value=disk.percent,
            unit=MetricUnit.PERCENT,
            category=MetricCategory.DISK,
            timestamp=timestamp
        ))
        
        # Network
        net_io = psutil.net_io_counters()
        metrics.append(MetricValue(
            name="network_bytes_sent",
            value=net_io.bytes_sent,
            unit=MetricUnit.BYTES,
            category=MetricCategory.NETWORK,
            timestamp=timestamp
        ))
        metrics.append(MetricValue(
            name="network_bytes_recv",
            value=net_io.bytes_recv,
            unit=MetricUnit.BYTES,
            category=MetricCategory.NETWORK,
            timestamp=timestamp
        ))
        
        # Store history
        self._metrics_history.extend(metrics)
        if len(self._metrics_history) > self._max_history:
            self._metrics_history = self._metrics_history[-self._max_history:]
        
        return metrics
    
    def get_metric_summary(self, category: Optional[MetricCategory] = None) -> Dict[str, Any]:
        """获取指标摘要"""
        metrics = self._metrics_history
        
        if category:
            metrics = [m for m in metrics if m.category == category]
        
        if not metrics:
            return {"count": 0}
        
        # Group by name
        by_name: Dict[str, List[float]] = {}
        for m in metrics:
            if m.name not in by_name:
                by_name[m.name] = []
            by_name[m.name].append(m.value)
        
        # Calculate stats
        summary = {"count": len(metrics)}
        for name, values in by_name.items():
            summary[name] = {
                "current": values[-1],
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
        
        return summary
    
    # ============== Health ==============
    
    def check_health(self) -> HealthCheckResult:
        """检查系统健康状态"""
        metrics = self.collect_metrics()
        
        # Calculate health score
        cpu = next((m.value for m in metrics if m.name == "cpu_percent"), 0)
        memory = next((m.value for m in metrics if m.name == "memory_percent"), 0)
        disk = next((m.value for m in metrics if m.name == "disk_percent"), 0)
        
        # Determine status
        if cpu > 90 or memory > 90 or disk > 95:
            status = HealthStatus.CRITICAL
            message = "Critical: One or more resources at capacity"
        elif cpu > 70 or memory > 70 or disk > 85:
            status = HealthStatus.WARNING
            message = "Warning: Resources running high"
        elif cpu > 50 or memory > 50:
            status = HealthStatus.WARNING
            message = "Notice: Resources moderately used"
        else:
            status = HealthStatus.HEALTHY
            message = "System healthy"
        
        return HealthCheckResult(
            service="system",
            status=status,
            message=message,
            details={"cpu": cpu, "memory": memory, "disk": disk},
            timestamp=time.time()
        )
    
    def check_service_health(self, service_name: str) -> HealthCheckResult:
        """检查服务健康状态"""
        # Simplified - in production would check actual service
        return HealthCheckResult(
            service=service_name,
            status=HealthStatus.HEALTHY,
            message=f"Service {service_name} is running",
            details={},
            timestamp=time.time()
        )
    
    # ============== Alerts ==============
    
    def check_and_alert(self) -> List[Alert]:
        """检查并生成告警"""
        alerts = []
        health = self.check_health()
        
        if health.status == HealthStatus.CRITICAL:
            alerts.append(Alert(
                level=AlertLevel.CRITICAL,
                source="monitoring",
                message=health.message,
                timestamp=time.time(),
                metadata=health.details
            ))
        elif health.status == HealthStatus.WARNING:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                source="monitoring",
                message=health.message,
                timestamp=time.time(),
                metadata=health.details
            ))
        
        # Store alerts
        self._alerts.extend(alerts)
        if len(self._alerts) > self._max_alerts:
            self._alerts = self._alerts[-self._max_alerts:]
        
        return alerts
    
    def get_alerts(
        self, 
        level: Optional[AlertLevel] = None,
        limit: int = 50
    ) -> List[Alert]:
        """获取告警列表"""
        alerts = self._alerts
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        return alerts[-limit:]
    
    # ============== Autoscaling ==============
    
    def should_scale(self) -> ScalingDecision:
        """判断是否需要扩缩容"""
        metrics = self.collect_metrics()
        
        cpu = next((m.value for m in metrics if m.name == "cpu_percent"), 0)
        memory = next((m.value for m in metrics if m.name == "memory_percent"), 0)
        
        # Average resource usage
        avg_usage = (cpu + memory) / 2
        
        if avg_usage > 80:
            return ScalingDecision.SCALE_UP
        elif avg_usage < 30:
            return ScalingDecision.SCALE_DOWN
        else:
            return ScalingDecision.MAINTAIN
    
    # ============== Dashboard ==============
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表盘数据"""
        return {
            "health": self.check_health().__dict__,
            "metrics": self.get_metric_summary(),
            "alerts": len(self._alerts),
            "scaling": self.should_scale().value,
            "timestamp": time.time(),
        }


# ============== Factory ==============

def get_monitoring_service() -> MonitoringService:
    """获取监控服务实例"""
    return MonitoringService()
