"""
监控和告警系统

提供全面的系统监控、性能指标收集、异常检测和告警通知功能
"""

import asyncio
import logging
import time
import json
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import statistics


logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"      # 计数器
    GAUGE = "gauge"         # 仪表盘
    HISTOGRAM = "histogram" # 直方图
    SUMMARY = "summary"     # 摘要


@dataclass
class MetricValue:
    """指标值"""
    name: str
    value: Union[int, float]
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    description: str
    condition: str  # 条件表达式，如 "error_rate > 0.1"
    level: AlertLevel
    enabled: bool = True
    cooldown: float = 300  # 冷却时间（秒）
    last_triggered: float = 0


@dataclass
class Alert:
    """告警"""
    rule_name: str
    level: AlertLevel
    message: str
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)


class AlertChannel(ABC):
    """告警通道抽象基类"""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """发送告警"""
        pass

    @property
    @abstractmethod
    def channel_type(self) -> str:
        """通道类型"""
        pass


class LogAlertChannel(AlertChannel):
    """日志告警通道"""

    def __init__(self, logger_name: str = "alerts"):
        self.logger = logging.getLogger(logger_name)

    async def send_alert(self, alert: Alert) -> bool:
        """发送告警到日志"""
        log_method = {
            AlertLevel.INFO: self.logger.info,
            AlertLevel.WARNING: self.logger.warning,
            AlertLevel.ERROR: self.logger.error,
            AlertLevel.CRITICAL: self.logger.critical
        }.get(alert.level, self.logger.info)

        log_method(f"🚨 {alert.level.value.upper()}: {alert.message} | Context: {alert.context}")
        return True

    @property
    def channel_type(self) -> str:
        return "log"


class ConsoleAlertChannel(AlertChannel):
    """控制台告警通道"""

    async def send_alert(self, alert: Alert) -> bool:
        """发送告警到控制台"""
        emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }.get(alert.level, "ℹ️")

        print(f"{emoji} [{alert.level.value.upper()}] {alert.message}")
        if alert.context:
            print(f"   Context: {alert.context}")
        return True

    @property
    def channel_type(self) -> str:
        return "console"


class MetricsCollector:
    """指标收集器"""

    def __init__(self):
        self._metrics: Dict[str, List[MetricValue]] = {}
        self._max_history_size = 1000  # 每个指标的最大历史记录数

    def record_metric(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        metric_type: MetricType = MetricType.GAUGE
    ):
        """记录指标"""
        if name not in self._metrics:
            self._metrics[name] = []

        metric_value = MetricValue(
            name=name,
            value=value,
            timestamp=time.time(),
            labels=labels or {},
            metric_type=metric_type
        )

        self._metrics[name].append(metric_value)

        # 限制历史记录数量
        if len(self._metrics[name]) > self._max_history_size:
            self._metrics[name] = self._metrics[name][-self._max_history_size:]

    def get_metric(self, name: str, labels: Optional[Dict[str, str]] = None) -> Optional[MetricValue]:
        """获取最新指标值"""
        if name not in self._metrics:
            return None

        metrics = self._metrics[name]

        if labels:
            # 过滤匹配的标签
            filtered = [
                m for m in metrics
                if all(m.labels.get(k) == v for k, v in labels.items())
            ]
            return filtered[-1] if filtered else None

        return metrics[-1] if metrics else None

    def get_metric_history(
        self,
        name: str,
        time_range: Optional[float] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricValue]:
        """获取指标历史"""
        if name not in self._metrics:
            return []

        metrics = self._metrics[name]

        if time_range:
            cutoff_time = time.time() - time_range
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]

        if labels:
            metrics = [
                m for m in metrics
                if all(m.labels.get(k) == v for k, v in labels.items())
            ]

        return metrics

    def get_metric_stats(
        self,
        name: str,
        time_range: Optional[float] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """获取指标统计"""
        history = self.get_metric_history(name, time_range, labels)

        if not history:
            return {}

        values = [m.value for m in history]

        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": statistics.mean(values),
            "median": statistics.median(values),
            "latest": values[-1],
            "time_range": time_range
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        result = {}
        for name in self._metrics.keys():
            result[name] = self.get_metric_stats(name)
        return result

    def clear_metrics(self, name: Optional[str] = None):
        """清除指标"""
        if name:
            self._metrics.pop(name, None)
        else:
            self._metrics.clear()


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._channels: Dict[str, AlertChannel] = {}
        self._alert_history: List[Alert] = []
        self._max_history_size = 1000

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self._rules[rule.name] = rule
        logger.info(f"✅ 添加告警规则: {rule.name}")

    def remove_rule(self, rule_name: str):
        """移除告警规则"""
        if rule_name in self._rules:
            del self._rules[rule_name]
            logger.info(f"✅ 移除告警规则: {rule_name}")

    def add_channel(self, channel: AlertChannel):
        """添加告警通道"""
        self._channels[channel.channel_type] = channel
        logger.info(f"✅ 添加告警通道: {channel.channel_type}")

    def remove_channel(self, channel_type: str):
        """移除告警通道"""
        if channel_type in self._channels:
            del self._channels[channel_type]
            logger.info(f"✅ 移除告警通道: {channel_type}")

    async def evaluate_rules(self, metrics_collector: MetricsCollector):
        """评估告警规则"""
        current_time = time.time()

        for rule in self._rules.values():
            if not rule.enabled:
                continue

            # 检查冷却时间
            if current_time - rule.last_triggered < rule.cooldown:
                continue

            try:
                # 评估条件
                if self._evaluate_condition(rule.condition, metrics_collector):
                    # 触发告警
                    alert = Alert(
                        rule_name=rule.name,
                        level=rule.level,
                        message=f"告警规则 '{rule.name}' 触发: {rule.description}",
                        timestamp=current_time,
                        context={"rule": rule.name, "condition": rule.condition}
                    )

                    # 发送告警
                    await self._send_alert(alert)

                    # 更新最后触发时间
                    rule.last_triggered = current_time

                    # 记录告警历史
                    self._alert_history.append(alert)
                    if len(self._alert_history) > self._max_history_size:
                        self._alert_history = self._alert_history[-self._max_history_size:]

            except Exception as e:
                logger.error(f"❌ 评估告警规则失败 {rule.name}: {e}")

    def _evaluate_condition(self, condition: str, metrics_collector: MetricsCollector) -> bool:
        """评估告警条件"""
        # 简单的条件评估器
        # 支持形如 "error_rate > 0.1" 的条件

        try:
            # 解析条件
            if ">" in condition:
                metric_name, threshold = condition.split(">", 1)
                threshold = float(threshold.strip())
                metric = metrics_collector.get_metric(metric_name.strip())
                return metric is not None and metric.value > threshold

            elif "<" in condition:
                metric_name, threshold = condition.split("<", 1)
                threshold = float(threshold.strip())
                metric = metrics_collector.get_metric(metric_name.strip())
                return metric is not None and metric.value < threshold

            elif ">=" in condition:
                metric_name, threshold = condition.split(">=", 1)
                threshold = float(threshold.strip())
                metric = metrics_collector.get_metric(metric_name.strip())
                return metric is not None and metric.value >= threshold

            elif "<=" in condition:
                metric_name, threshold = condition.split("<=", 1)
                threshold = float(threshold.strip())
                metric = metrics_collector.get_metric(metric_name.strip())
                return metric is not None and metric.value <= threshold

            elif "==" in condition:
                metric_name, value = condition.split("==", 1)
                value = float(value.strip())
                metric = metrics_collector.get_metric(metric_name.strip())
                return metric is not None and metric.value == value

        except Exception as e:
            logger.debug(f"条件评估失败: {condition} - {e}")

        return False

    async def _send_alert(self, alert: Alert):
        """发送告警"""
        success_count = 0

        for channel in self._channels.values():
            try:
                if await channel.send_alert(alert):
                    success_count += 1
            except Exception as e:
                logger.error(f"❌ 发送告警失败 {channel.channel_type}: {e}")

        logger.info(f"✅ 告警发送完成: {success_count}/{len(self._channels)} 个通道成功")

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """获取告警历史"""
        return self._alert_history[-limit:]

    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        # 简单的活跃告警：最近5分钟内的告警
        cutoff_time = time.time() - 300
        return [alert for alert in self._alert_history if alert.timestamp >= cutoff_time]


class MonitoringSystem:
    """
    监控系统

    统一监控入口，提供指标收集、告警管理和健康检查
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()

        # 添加默认告警通道
        self.alert_manager.add_channel(LogAlertChannel())
        self.alert_manager.add_channel(ConsoleAlertChannel())

        # 监控线程
        self._monitoring_thread = None
        self._running = False
        self._monitoring_interval = 30  # 监控间隔（秒）

        # 性能追踪
        self._request_count = 0
        self._error_count = 0
        self._response_times = []

    def start_monitoring(self):
        """启动监控"""
        if self._running:
            return

        self._running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

        self.logger.info("✅ 监控系统启动")

    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

        self.logger.info("✅ 监控系统停止")

    def _monitoring_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 收集系统指标
                self._collect_system_metrics()

                # 评估告警规则
                asyncio.run(self.alert_manager.evaluate_rules(self.metrics_collector))

                # 等待下一个监控周期
                time.sleep(self._monitoring_interval)

            except Exception as e:
                self.logger.error(f"❌ 监控循环异常: {e}")
                time.sleep(5)  # 出错后等待5秒再试

    def _collect_system_metrics(self):
        """收集系统指标"""
        current_time = time.time()

        # 请求相关指标
        self.metrics_collector.record_metric(
            "requests_total",
            self._request_count,
            metric_type=MetricType.COUNTER
        )

        self.metrics_collector.record_metric(
            "errors_total",
            self._error_count,
            metric_type=MetricType.COUNTER
        )

        if self._request_count > 0:
            error_rate = self._error_count / self._request_count
            self.metrics_collector.record_metric("error_rate", error_rate)

        # 响应时间指标
        if self._response_times:
            avg_response_time = statistics.mean(self._response_times[-100:])  # 最近100个请求
            self.metrics_collector.record_metric("avg_response_time", avg_response_time)

            # 清理旧的响应时间数据（保持最近1000个）
            if len(self._response_times) > 1000:
                self._response_times = self._response_times[-1000:]

        # 系统资源指标
        import psutil
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent

            self.metrics_collector.record_metric("cpu_usage", cpu_percent)
            self.metrics_collector.record_metric("memory_usage", memory_percent)
        except ImportError:
            # psutil不可用时跳过
            pass

    def record_request(
        self,
        response_time: float,
        success: bool,
        labels: Optional[Dict[str, str]] = None
    ):
        """记录请求"""
        self._request_count += 1

        if not success:
            self._error_count += 1

        self._response_times.append(response_time)

        # 记录详细指标
        self.metrics_collector.record_metric(
            "request_duration",
            response_time,
            labels=labels,
            metric_type=MetricType.HISTOGRAM
        )

        status = "success" if success else "error"
        self.metrics_collector.record_metric(
            f"requests_by_status_{status}",
            1,
            labels=labels,
            metric_type=MetricType.COUNTER
        )

    def add_alert_rule(
        self,
        name: str,
        description: str,
        condition: str,
        level: AlertLevel,
        cooldown: float = 300
    ):
        """添加告警规则"""
        rule = AlertRule(
            name=name,
            description=description,
            condition=condition,
            level=level,
            cooldown=cooldown
        )
        self.alert_manager.add_rule(rule)

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        metrics = self.metrics_collector.get_all_metrics()

        # 简单的健康检查逻辑
        health_status = "healthy"

        # 检查错误率
        error_rate = metrics.get("error_rate", {}).get("latest", 0)
        if error_rate > 0.1:  # 错误率超过10%
            health_status = "unhealthy"

        # 检查响应时间
        avg_response_time = metrics.get("avg_response_time", {}).get("latest", 0)
        if avg_response_time > 5.0:  # 平均响应时间超过5秒
            health_status = "degraded"

        return {
            "status": health_status,
            "timestamp": time.time(),
            "metrics": metrics,
            "alerts": len(self.alert_manager.get_active_alerts())
        }

    def get_metrics_endpoint(self) -> Dict[str, Any]:
        """获取指标端点数据"""
        return {
            "metrics": self.metrics_collector.get_all_metrics(),
            "alerts": {
                "active": [alert.__dict__ for alert in self.alert_manager.get_active_alerts()],
                "history": [alert.__dict__ for alert in self.alert_manager.get_alert_history(50)]
            },
            "health": self.get_health_status(),
            "timestamp": time.time()
        }

    def export_metrics(self, format: str = "json") -> str:
        """导出指标"""
        data = self.get_metrics_endpoint()

        if format == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            return str(data)


# 全局监控系统实例
_monitoring_system_instance = None

def get_monitoring_system() -> MonitoringSystem:
    """获取监控系统实例"""
    global _monitoring_system_instance
    if _monitoring_system_instance is None:
        _monitoring_system_instance = MonitoringSystem()
    return _monitoring_system_instance

def init_monitoring_system():
    """初始化监控系统"""
    system = get_monitoring_system()

    # 添加默认告警规则
    system.add_alert_rule(
        "high_error_rate",
        "错误率过高",
        "error_rate > 0.1",
        AlertLevel.ERROR,
        cooldown=300
    )

    system.add_alert_rule(
        "slow_response",
        "响应时间过长",
        "avg_response_time > 5.0",
        AlertLevel.WARNING,
        cooldown=60
    )

    system.add_alert_rule(
        "high_cpu_usage",
        "CPU使用率过高",
        "cpu_usage > 80",
        AlertLevel.WARNING,
        cooldown=120
    )

    # 启动监控
    system.start_monitoring()

    logger.info("✅ 监控系统初始化完成")
