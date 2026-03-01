#!/usr/bin/env python3
"""
运维监控系统
提供全面的系统运维监控、告警管理和自动化运维功能
"""

import asyncio
import time
import threading
import logging
import psutil
import json
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_config_center

logger = logging.getLogger(__name__)

@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    metric_name: str
    condition: str  # '>', '<', '>=', '<=', '==', '!='
    threshold: float
    severity: str  # 'info', 'warning', 'error', 'critical'
    cooldown_minutes: int = 5
    enabled: bool = True
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """告警信息"""
    alert_id: str
    rule_id: str
    rule_name: str
    metric_name: str
    actual_value: float
    threshold: float
    severity: str
    message: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class MaintenanceWindow:
    """维护窗口"""
    window_id: str
    name: str
    start_time: datetime
    end_time: datetime
    description: str
    suppress_alerts: bool = True

class OperationsMonitoringSystem:
    """运维监控系统"""

    def __init__(self):
        self.module_logger = get_module_logger(ModuleType.SERVICE, "OperationsMonitor")

        # 配置
        self._config = get_unified_config_center().get_config()
        self._monitoring_enabled = True
        self._collection_interval = 30  # 30秒
        self._retention_days = 7  # 数据保留7天

        # 数据存储
        self._metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._maintenance_windows: List[MaintenanceWindow] = []

        # 通知配置
        self._email_config = {
            'enabled': False,
            'smtp_server': '',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'from_email': '',
            'to_emails': []
        }

        # 监控线程
        self._monitoring_thread: Optional[threading.Thread] = None
        self._running = False

        # 初始化
        self._initialize_alert_rules()
        self._load_configuration()

    def start_monitoring(self):
        """启动监控"""
        if self._monitoring_enabled and not self._running:
            self._running = True
            self._monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="operations_monitor",
                daemon=True
            )
            self._monitoring_thread.start()
            self.module_logger.info("🚀 运维监控系统已启动")

    def stop_monitoring(self):
        """停止监控"""
        self._running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        self.module_logger.info("🛑 运维监控系统已停止")

    def _monitoring_loop(self):
        """监控主循环"""
        while self._running:
            try:
                # 收集系统指标
                metrics = self._collect_system_metrics()

                # 存储指标
                for metric_name, value in metrics.items():
                    self._store_metric(metric_name, value)

                # 检查告警规则
                self._check_alert_rules(metrics)

                # 清理过期数据
                self._cleanup_expired_data()

                # 等待下一个收集周期
                time.sleep(self._collection_interval)

            except Exception as e:
                self.module_logger.error(f"监控循环异常: {e}", exc_info=True)
                time.sleep(10)  # 出错后等待10秒再试

    def _collect_system_metrics(self) -> Dict[str, float]:
        """收集系统指标"""
        metrics = {}

        try:
            # CPU指标
            metrics['cpu_percent'] = psutil.cpu_percent(interval=1)
            metrics['cpu_count'] = psutil.cpu_count()
            cpu_times = psutil.cpu_times_percent()
            metrics['cpu_user'] = cpu_times.user
            metrics['cpu_system'] = cpu_times.system

            # 内存指标
            memory = psutil.virtual_memory()
            metrics['memory_percent'] = memory.percent
            metrics['memory_used_gb'] = memory.used / (1024**3)
            metrics['memory_available_gb'] = memory.available / (1024**3)

            # 磁盘指标
            disk = psutil.disk_usage('/')
            metrics['disk_percent'] = disk.percent
            metrics['disk_used_gb'] = disk.used / (1024**3)
            metrics['disk_free_gb'] = disk.free / (1024**3)

            # 网络指标
            network = psutil.net_io_counters()
            metrics['network_bytes_sent_mb'] = network.bytes_sent / (1024**2)
            metrics['network_bytes_recv_mb'] = network.bytes_recv / (1024**2)

            # 进程指标
            process = psutil.Process()
            metrics['process_cpu_percent'] = process.cpu_percent()
            metrics['process_memory_mb'] = process.memory_info().rss / (1024**2)
            metrics['process_threads'] = process.num_threads()
            metrics['process_fds'] = process.num_fds() if hasattr(process, 'num_fds') else 0

        except Exception as e:
            self.module_logger.error(f"收集系统指标失败: {e}")

        return metrics

    def _store_metric(self, metric_name: str, value: float):
        """存储指标数据"""
        timestamp = datetime.now()
        metric_data = {
            'timestamp': timestamp,
            'value': value
        }
        self._metrics_history[metric_name].append(metric_data)

    def _initialize_alert_rules(self):
        """初始化告警规则"""
        default_rules = [
            AlertRule(
                rule_id="cpu_high",
                name="CPU使用率过高",
                metric_name="cpu_percent",
                condition=">",
                threshold=80.0,
                severity="warning",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="memory_high",
                name="内存使用率过高",
                metric_name="memory_percent",
                condition=">",
                threshold=85.0,
                severity="warning",
                cooldown_minutes=5
            ),
            AlertRule(
                rule_id="disk_high",
                name="磁盘使用率过高",
                metric_name="disk_percent",
                condition=">",
                threshold=90.0,
                severity="error",
                cooldown_minutes=10
            ),
            AlertRule(
                rule_id="memory_critical",
                name="内存使用率严重过高",
                metric_name="memory_percent",
                condition=">",
                threshold=95.0,
                severity="critical",
                cooldown_minutes=2
            )
        ]

        for rule in default_rules:
            self._alert_rules[rule.rule_id] = rule

    def _check_alert_rules(self, metrics: Dict[str, float]):
        """检查告警规则"""
        current_time = datetime.now()

        # 检查是否在维护窗口
        in_maintenance = self._is_in_maintenance_window(current_time)

        for rule in self._alert_rules.values():
            if not rule.enabled:
                continue

            if rule.metric_name not in metrics:
                continue

            actual_value = metrics[rule.metric_name]

            # 检查是否满足告警条件
            triggered = self._evaluate_condition(actual_value, rule.condition, rule.threshold)

            if triggered:
                # 检查冷却时间
                if rule.last_triggered and (current_time - rule.last_triggered).total_seconds() < rule.cooldown_minutes * 60:
                    continue

                # 创建告警
                alert = Alert(
                    alert_id=f"{rule.rule_id}_{int(current_time.timestamp())}",
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    metric_name=rule.metric_name,
                    actual_value=actual_value,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    message=f"{rule.name}: {actual_value:.2f} {rule.condition} {rule.threshold}",
                    timestamp=current_time
                )

                # 存储活跃告警
                self._active_alerts[alert.alert_id] = alert
                rule.last_triggered = current_time

                # 发送通知（如果不在维护窗口）
                if not in_maintenance:
                    self._send_alert_notification(alert)

                self.module_logger.warning(f"🚨 触发告警: {alert.message}")

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """评估告警条件"""
        if condition == '>':
            return value > threshold
        elif condition == '<':
            return value < threshold
        elif condition == '>=':
            return value >= threshold
        elif condition == '<=':
            return value <= threshold
        elif condition == '==':
            return value == threshold
        elif condition == '!=':
            return value != threshold
        return False

    def _is_in_maintenance_window(self, timestamp: datetime) -> bool:
        """检查是否在维护窗口"""
        for window in self._maintenance_windows:
            if window.start_time <= timestamp <= window.end_time:
                return True
        return False

    def _send_alert_notification(self, alert: Alert):
        """发送告警通知"""
        if not self._email_config['enabled']:
            return

        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self._email_config['from_email']
            msg['To'] = ', '.join(self._email_config['to_emails'])
            msg['Subject'] = f"RANGEN 系统告警 - {alert.severity.upper()}: {alert.rule_name}"

            severity_icons = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '❌',
                'critical': '🚨'
            }

            body = f"""
{severity_icons.get(alert.severity, '⚠️')} RANGEN 系统告警

告警规则: {alert.rule_name}
指标名称: {alert.metric_name}
实际值: {alert.actual_value:.2f}
阈值: {alert.threshold}
严重程度: {alert.severity.upper()}
触发时间: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

消息: {alert.message}

请及时检查系统状态。
"""

            msg.attach(MIMEText(body, 'plain'))

            # 发送邮件
            server = smtplib.SMTP(self._email_config['smtp_server'], self._email_config['smtp_port'])
            server.starttls()
            server.login(self._email_config['username'], self._email_config['password'])
            server.sendmail(self._email_config['from_email'], self._email_config['to_emails'], msg.as_string())
            server.quit()

            self.module_logger.info(f"📧 告警邮件已发送: {alert.alert_id}")

        except Exception as e:
            self.module_logger.error(f"发送告警邮件失败: {e}")

    def _cleanup_expired_data(self):
        """清理过期数据"""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(days=self._retention_days)

        # 清理指标历史
        for metric_name, history in self._metrics_history.items():
            # 移除过期数据
            while history and history[0]['timestamp'] < cutoff_time:
                history.popleft()

        # 清理已解决的告警
        resolved_alerts = [
            alert_id for alert_id, alert in self._active_alerts.items()
            if alert.resolved and (current_time - alert.resolved_at).total_seconds() > 3600  # 1小时后删除
        ]
        for alert_id in resolved_alerts:
            del self._active_alerts[alert_id]

    def _load_configuration(self):
        """加载配置"""
        try:
            # 从配置中心加载监控配置
            monitoring_config = self._config.get('monitoring', {})

            self._monitoring_enabled = monitoring_config.get('enabled', True)
            self._collection_interval = monitoring_config.get('collection_interval', 30)
            self._retention_days = monitoring_config.get('retention_days', 7)

            # 加载邮件配置
            email_config = monitoring_config.get('email', {})
            self._email_config.update({
                'enabled': email_config.get('enabled', False),
                'smtp_server': email_config.get('smtp_server', ''),
                'smtp_port': email_config.get('smtp_port', 587),
                'username': email_config.get('username', ''),
                'password': email_config.get('password', ''),
                'from_email': email_config.get('from_email', ''),
                'to_emails': email_config.get('to_emails', [])
            })

        except Exception as e:
            self.module_logger.error(f"加载监控配置失败: {e}")

    # 公共接口方法

    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        latest_metrics = {}
        for metric_name, history in self._metrics_history.items():
            if history:
                latest_metrics[metric_name] = history[-1]['value']

        return {
            'timestamp': datetime.now(),
            'metrics': latest_metrics,
            'active_alerts': len(self._active_alerts)
        }

    def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """获取指标历史"""
        if metric_name not in self._metrics_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = [
            {'timestamp': item['timestamp'], 'value': item['value']}
            for item in self._metrics_history[metric_name]
            if item['timestamp'] > cutoff_time
        ]

        return history

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [
            {
                'alert_id': alert.alert_id,
                'rule_name': alert.rule_name,
                'severity': alert.severity,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'resolved': alert.resolved
            }
            for alert in self._active_alerts.values()
        ]

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self._active_alerts:
            alert = self._active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now()
            self.module_logger.info(f"✅ 告警已解决: {alert_id}")

    def add_maintenance_window(self, name: str, start_time: datetime, end_time: datetime, description: str):
        """添加维护窗口"""
        window = MaintenanceWindow(
            window_id=f"maintenance_{int(time.time())}",
            name=name,
            start_time=start_time,
            end_time=end_time,
            description=description
        )
        self._maintenance_windows.append(window)
        self.module_logger.info(f"📅 维护窗口已添加: {name} ({start_time} - {end_time})")

    def get_system_health_report(self) -> Dict[str, Any]:
        """获取系统健康报告"""
        current_metrics = self.get_current_metrics()
        active_alerts = self.get_active_alerts()

        # 计算健康评分
        health_score = self._calculate_health_score(current_metrics, active_alerts)

        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'status': self._get_health_status(health_score),
            'current_metrics': current_metrics,
            'active_alerts': active_alerts,
            'maintenance_windows': [
                {
                    'name': w.name,
                    'start_time': w.start_time.isoformat(),
                    'end_time': w.end_time.isoformat(),
                    'description': w.description
                }
                for w in self._maintenance_windows
            ]
        }

    def _calculate_health_score(self, metrics: Dict[str, Any], alerts: List[Dict[str, Any]]) -> float:
        """计算健康评分"""
        base_score = 100.0

        # 基于指标的评分
        metric_weights = {
            'cpu_percent': 0.2,
            'memory_percent': 0.3,
            'disk_percent': 0.2,
            'active_alerts': 0.3
        }

        metric_values = metrics.get('metrics', {})

        # CPU评分
        cpu_percent = metric_values.get('cpu_percent', 0)
        if cpu_percent > 90:
            base_score -= 30 * metric_weights['cpu_percent']
        elif cpu_percent > 70:
            base_score -= 15 * metric_weights['cpu_percent']

        # 内存评分
        memory_percent = metric_values.get('memory_percent', 0)
        if memory_percent > 95:
            base_score -= 40 * metric_weights['memory_percent']
        elif memory_percent > 85:
            base_score -= 20 * metric_weights['memory_percent']

        # 磁盘评分
        disk_percent = metric_values.get('disk_percent', 0)
        if disk_percent > 95:
            base_score -= 50 * metric_weights['disk_percent']
        elif disk_percent > 90:
            base_score -= 25 * metric_weights['disk_percent']

        # 告警评分
        alert_count = len(alerts)
        critical_alerts = sum(1 for alert in alerts if alert['severity'] == 'critical')
        warning_alerts = sum(1 for alert in alerts if alert['severity'] == 'warning')

        base_score -= critical_alerts * 20 * metric_weights['active_alerts']
        base_score -= warning_alerts * 5 * metric_weights['active_alerts']

        return max(0.0, min(100.0, base_score))

    def _get_health_status(self, score: float) -> str:
        """获取健康状态"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 70:
            return "fair"
        elif score >= 60:
            return "poor"
        else:
            return "critical"

# 全局监控实例
_monitoring_instance: Optional[OperationsMonitoringSystem] = None
_monitoring_lock = threading.Lock()

def get_operations_monitor() -> OperationsMonitoringSystem:
    """获取运维监控实例"""
    global _monitoring_instance
    if _monitoring_instance is None:
        with _monitoring_lock:
            if _monitoring_instance is None:
                _monitoring_instance = OperationsMonitoringSystem()
    return _monitoring_instance

def start_operations_monitoring():
    """启动运维监控"""
    monitor = get_operations_monitor()
    monitor.start_monitoring()

def stop_operations_monitoring():
    """停止运维监控"""
    monitor = get_operations_monitor()
    monitor.stop_monitoring()
