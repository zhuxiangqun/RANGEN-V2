"""
系统健康监控服务
提供系统整体健康状态监控、性能指标收集和告警机制
"""

import asyncio
import time
import threading
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque

from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center, get_unified_intelligent_center

logger = logging.getLogger(__name__)

@dataclass
class HealthMetric:
    """健康指标数据结构"""
    name: str
    value: float
    timestamp: datetime
    unit: str = ""
    status: str = "healthy"  # healthy, warning, critical
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthAlert:
    """健康告警数据结构"""
    alert_id: str
    metric_name: str
    level: str  # info, warning, critical
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

class SystemHealthMonitor:
    """
    系统健康监控服务
    监控系统整体健康状态，包括CPU、内存、磁盘、网络等指标
    以及各个服务的运行状态
    """

    def __init__(self):
        self.module_logger = get_module_logger(ModuleType.SERVICE, "SystemHealthMonitor")
        self.config_center = get_unified_config_center()
        self.intelligent_center = get_unified_intelligent_center()

        # 配置参数
        self.monitoring_interval = self.config_center.get_config_value(
            "system_health_monitor", "monitoring_interval_seconds", 30
        )
        self.alert_thresholds = self.config_center.get_config_value(
            "system_health_monitor", "alert_thresholds", {
                "cpu_percent": {"warning": 80.0, "critical": 95.0},
                "memory_percent": {"warning": 85.0, "critical": 95.0},
                "disk_percent": {"warning": 90.0, "critical": 98.0},
                "network_errors": {"warning": 10, "critical": 50}
            }
        )
        self.metrics_history_size = self.config_center.get_config_value(
            "system_health_monitor", "metrics_history_size", 1000
        )

        # 数据存储
        self.metrics_history: Dict[str, deque] = {}
        self.active_alerts: Dict[str, HealthAlert] = {}
        self.service_status: Dict[str, Dict[str, Any]] = {}

        # 监控任务
        self._monitoring_task: Optional[asyncio.Task] = None
        self._alert_processing_task: Optional[asyncio.Task] = None
        self._running = False

        # 告警回调
        self.alert_callbacks: List[Callable[[HealthAlert], None]] = []

        # 初始化
        self._initialize_monitoring()

    def _initialize_monitoring(self):
        """初始化监控指标"""
        metric_names = [
            "cpu_percent", "memory_percent", "memory_used_mb", "disk_percent",
            "disk_used_gb", "network_bytes_sent", "network_bytes_recv",
            "system_load_1m", "system_load_5m", "system_load_15m",
            "process_count", "thread_count", "open_files"
        ]

        for metric_name in metric_names:
            self.metrics_history[metric_name] = deque(maxlen=self.metrics_history_size)

        self.module_logger.info("✅ 系统健康监控初始化完成")

    def register_service(self, service_name: str, service_instance: Any):
        """注册服务进行监控"""
        self.service_status[service_name] = {
            "instance": service_instance,
            "status": "unknown",
            "last_check": None,
            "response_time": None,
            "error_count": 0,
            "health_score": 0.0
        }
        self.module_logger.info(f"✅ 服务已注册监控: {service_name}")

    def add_alert_callback(self, callback: Callable[[HealthAlert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)

    async def start_monitoring(self):
        """启动监控"""
        if self._running:
            return

        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        self._alert_processing_task = asyncio.create_task(self._alert_processing_loop())

        self.module_logger.info("✅ 系统健康监控已启动")

    async def stop_monitoring(self):
        """停止监控"""
        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self._alert_processing_task:
            self._alert_processing_task.cancel()
            try:
                await self._alert_processing_task
            except asyncio.CancelledError:
                pass

        self.module_logger.info("🛑 系统健康监控已停止")

    async def _monitoring_loop(self):
        """监控主循环"""
        while self._running:
            try:
                await self._collect_system_metrics()
                await self._check_service_health()
                await self._analyze_health_trends()

            except Exception as e:
                self.module_logger.error(f"❌ 监控循环异常: {e}", exc_info=True)

            await asyncio.sleep(self.monitoring_interval)

    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            self._add_metric("cpu_percent", cpu_percent, "%")

            # 内存指标
            memory = psutil.virtual_memory()
            self._add_metric("memory_percent", memory.percent, "%")
            self._add_metric("memory_used_mb", memory.used / 1024 / 1024, "MB")

            # 磁盘指标
            disk = psutil.disk_usage('/')
            self._add_metric("disk_percent", disk.percent, "%")
            self._add_metric("disk_used_gb", disk.used / 1024 / 1024 / 1024, "GB")

            # 网络指标
            network = psutil.net_io_counters()
            self._add_metric("network_bytes_sent", network.bytes_sent, "bytes")
            self._add_metric("network_bytes_recv", network.bytes_recv, "bytes")

            # 系统负载
            load = psutil.getloadavg()
            self._add_metric("system_load_1m", load[0])
            self._add_metric("system_load_5m", load[1])
            self._add_metric("system_load_15m", load[2])

            # 进程指标
            process_count = len(psutil.pids())
            self._add_metric("process_count", process_count)
            self._add_metric("thread_count", threading.active_count())

        except Exception as e:
            self.module_logger.error(f"❌ 收集系统指标失败: {e}")

    async def _check_service_health(self):
        """检查服务健康状态"""
        for service_name, service_info in self.service_status.items():
            try:
                service_instance = service_info["instance"]
                start_time = time.time()

                # 简单的健康检查 - 尝试调用健康检查方法
                if hasattr(service_instance, 'health_check'):
                    health_result = await service_instance.health_check()
                    response_time = time.time() - start_time

                    service_info.update({
                        "status": health_result.get("status", "unknown"),
                        "last_check": datetime.now(),
                        "response_time": response_time,
                        "health_score": health_result.get("score", 0.0)
                    })

                    # 检查响应时间告警
                    if response_time > 5.0:  # 超过5秒
                        await self._trigger_alert(
                            f"{service_name}_response_time",
                            "warning",
                            f"服务 {service_name} 响应时间过长: {response_time:.2f}秒"
                        )

                elif hasattr(service_instance, 'is_running'):
                    # 简单的运行状态检查
                    is_running = service_instance.is_running()
                    service_info.update({
                        "status": "healthy" if is_running else "unhealthy",
                        "last_check": datetime.now(),
                        "response_time": None,
                        "health_score": 1.0 if is_running else 0.0
                    })

                else:
                    # 无法检查，标记为未知
                    service_info.update({
                        "status": "unknown",
                        "last_check": datetime.now(),
                        "response_time": None,
                        "health_score": 0.5
                    })

            except Exception as e:
                service_info["error_count"] += 1
                service_info.update({
                    "status": "error",
                    "last_check": datetime.now(),
                    "response_time": None,
                    "health_score": 0.0
                })

                # 错误计数告警
                if service_info["error_count"] > 5:
                    await self._trigger_alert(
                        f"{service_name}_errors",
                        "critical",
                        f"服务 {service_name} 连续错误次数: {service_info['error_count']}"
                    )

    async def _analyze_health_trends(self):
        """分析健康趋势"""
        try:
            # 检查CPU使用率趋势
            cpu_metrics = list(self.metrics_history["cpu_percent"])
            if len(cpu_metrics) >= 10:
                recent_avg = sum(m.value for m in cpu_metrics[-5:]) / 5
                older_avg = sum(m.value for m in cpu_metrics[-10:-5]) / 5

                if recent_avg > older_avg + 20:  # CPU使用率快速上升
                    await self._trigger_alert(
                        "cpu_trend",
                        "warning",
                        f"CPU使用率快速上升: {older_avg:.1f}% → {recent_avg:.1f}%"
                    )

            # 检查内存使用率趋势
            memory_metrics = list(self.metrics_history["memory_percent"])
            if len(memory_metrics) >= 10:
                recent_avg = sum(m.value for m in memory_metrics[-5:]) / 5
                if recent_avg > 90:  # 内存使用率过高
                    await self._trigger_alert(
                        "memory_usage_high",
                        "warning",
                        f"内存使用率过高: {recent_avg:.1f}%"
                    )

        except Exception as e:
            self.module_logger.error(f"❌ 健康趋势分析失败: {e}")

    def _add_metric(self, name: str, value: float, unit: str = ""):
        """添加指标到历史记录"""
        metric = HealthMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            unit=unit
        )

        # 确定状态
        if name in self.alert_thresholds:
            thresholds = self.alert_thresholds[name]
            if value >= thresholds.get("critical", float('inf')):
                metric.status = "critical"
            elif value >= thresholds.get("warning", float('inf')):
                metric.status = "warning"

        self.metrics_history[name].append(metric)

        # 如果状态异常，触发告警
        if metric.status != "healthy":
            asyncio.create_task(self._trigger_alert(
                name,
                metric.status,
                f"{name} 超出阈值: {value}{unit}"
            ))

    async def _trigger_alert(self, metric_name: str, level: str, message: str):
        """触发告警"""
        alert_id = f"{metric_name}_{int(time.time())}"

        alert = HealthAlert(
            alert_id=alert_id,
            metric_name=metric_name,
            level=level,
            message=message,
            timestamp=datetime.now()
        )

        self.active_alerts[alert_id] = alert

        # 调用回调函数
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                self.module_logger.error(f"❌ 告警回调失败: {e}")

        self.module_logger.warning(f"🚨 健康告警 [{level.upper()}]: {message}")

    async def _alert_processing_loop(self):
        """告警处理循环 - 定期清理已解决的告警"""
        while self._running:
            try:
                current_time = datetime.now()
                to_remove = []

                for alert_id, alert in self.active_alerts.items():
                    # 简单的时间过期逻辑（实际可以更复杂）
                    if not alert.resolved and (current_time - alert.timestamp) > timedelta(hours=1):
                        alert.resolved = True
                        alert.resolved_at = current_time
                        to_remove.append(alert_id)

                for alert_id in to_remove:
                    del self.active_alerts[alert_id]

            except Exception as e:
                self.module_logger.error(f"❌ 告警处理异常: {e}")

            await asyncio.sleep(300)  # 每5分钟清理一次

    def get_health_report(self) -> Dict[str, Any]:
        """获取健康报告"""
        report = {
            "timestamp": datetime.now(),
            "system_status": "healthy",
            "metrics": {},
            "services": {},
            "active_alerts": list(self.active_alerts.values())
        }

        # 系统指标摘要
        for metric_name, history in self.metrics_history.items():
            if history:
                latest = history[-1]
                report["metrics"][metric_name] = {
                    "current": latest.value,
                    "unit": latest.unit,
                    "status": latest.status,
                    "timestamp": latest.timestamp
                }

                # 如果有关键指标异常，整个系统状态设为异常
                if latest.status == "critical":
                    report["system_status"] = "critical"
                elif latest.status == "warning" and report["system_status"] == "healthy":
                    report["system_status"] = "warning"

        # 服务状态
        for service_name, service_info in self.service_status.items():
            report["services"][service_name] = {
                "status": service_info["status"],
                "health_score": service_info["health_score"],
                "last_check": service_info["last_check"],
                "response_time": service_info["response_time"],
                "error_count": service_info["error_count"]
            }

            # 如果服务异常，整个系统状态设为异常
            if service_info["status"] in ["error", "unhealthy"]:
                report["system_status"] = "critical"
            elif service_info["status"] == "warning" and report["system_status"] == "healthy":
                report["system_status"] = "warning"

        return report

    def get_metrics_history(self, metric_name: str, hours: int = 1) -> List[HealthMetric]:
        """获取指标历史数据"""
        if metric_name not in self.metrics_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics_history[metric_name] if m.timestamp >= cutoff_time]

    async def health_check(self) -> Dict[str, Any]:
        """健康检查接口"""
        return {
            "status": "healthy" if not self.active_alerts else "warning",
            "timestamp": datetime.now(),
            "active_alerts_count": len(self.active_alerts),
            "monitored_services_count": len(self.service_status),
            "monitoring_active": self._running
        }
