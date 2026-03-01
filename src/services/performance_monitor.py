"""
Performance Monitoring Service
Provides metrics collection, analysis, and alerting.
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Callable, Tuple, Deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics

from src.services.logging_service import get_logger
from src.services.config_service import ConfigService

logger = get_logger("performance_monitor")

@dataclass
class PerformanceMetric:
    """Data structure for performance metrics"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceAlert:
    """Data structure for performance alerts"""
    alert_id: str
    metric_name: str
    threshold: float
    actual_value: float
    level: str  # info, warning, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)

class PerformanceMonitor:
    """
    Real-time performance monitoring service.
    Collects system metrics and application-specific metrics (latency, errors).
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
            
        self.config_service = ConfigService()
        
        # Configuration
        self.collection_interval = 10 # seconds
        self.metrics_retention_days = 7
        self.alert_thresholds = {
            "response_time": {"warning": 2.0, "critical": 5.0},
            "error_rate": {"warning": 0.05, "critical": 0.15},
            "memory_usage": {"warning": 80.0, "critical": 95.0},
            "cpu_usage": {"warning": 80.0, "critical": 95.0}
        }

        # Storage
        self.metrics: Dict[str, Deque[PerformanceMetric]] = defaultdict(lambda: deque(maxlen=10000))
        self.active_alerts: Dict[str, PerformanceAlert] = {}
        
        # Tasks
        self._running = False
        self._tasks = []
        
        self._initialized = True
        logger.info("PerformanceMonitor initialized")

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record a metric point"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {},
            metadata=metadata or {}
        )
        self.metrics[name].append(metric)
        self._check_thresholds(metric)

    def _check_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds thresholds"""
        if metric.name not in self.alert_thresholds:
            return

        thresholds = self.alert_thresholds[metric.name]
        level = None
        
        if metric.value >= thresholds.get("critical", float('inf')):
            level = "critical"
        elif metric.value >= thresholds.get("warning", float('inf')):
            level = "warning"
            
        if level:
            msg = f"{metric.name} is {level}: {metric.value}"
            logger.warning(f"[Alert] {msg}")
            # Logic to deduplicate or persist alerts could go here

    async def start(self):
        """Start background monitoring tasks"""
        if self._running:
            return
        self._running = True
        self._tasks.append(asyncio.create_task(self._system_metrics_loop()))
        logger.info("Monitoring tasks started")

    async def stop(self):
        """Stop background tasks"""
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks = []
        logger.info("Monitoring tasks stopped")

    async def _system_metrics_loop(self):
        """Collect system-level metrics (CPU, Memory)"""
        while self._running:
            try:
                import psutil
                cpu = psutil.cpu_percent()
                mem = psutil.virtual_memory().percent
                self.record_metric("system.cpu_usage", cpu)
                self.record_metric("system.memory_usage", mem)
            except ImportError:
                logger.warning("psutil not installed, skipping system metrics")
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
            
            await asyncio.sleep(self.collection_interval)

    def get_stats(self) -> Dict[str, Any]:
        """Return summary stats"""
        return {
            "metrics_count": sum(len(q) for q in self.metrics.values()),
            "active_alerts": len(self.active_alerts),
            "status": "running" if self._running else "stopped"
        }

# Global Accessor
def get_performance_monitor() -> PerformanceMonitor:
    return PerformanceMonitor()
