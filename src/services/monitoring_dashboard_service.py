#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控仪表板服务 - 多模型架构的实时监控和告警系统

提供统一的监控仪表板，集成以下监控维度：
1. 模型性能监控：响应时间、成功率、Token使用
2. 成本监控：实时成本跟踪、预算使用情况
3. 系统健康监控：服务可用性、资源使用
4. 路由决策监控：智能路由决策质量
5. 缓存效率监控：缓存命中率、节省效果
6. 实时告警：阈值告警、异常检测

核心功能：
- 统一监控数据聚合和展示
- 实时性能指标可视化
- 多级告警系统（信息、警告、严重）
- 历史数据分析和趋势预测
- 可配置的监控面板
- API接口供前端调用
"""

import time
import json
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import asyncio

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"          # 信息
    WARNING = "warning"    # 警告
    CRITICAL = "critical"  # 严重


class MetricType(str, Enum):
    """指标类型"""
    RESPONSE_TIME = "response_time"          # 响应时间
    SUCCESS_RATE = "success_rate"            # 成功率
    TOKEN_USAGE = "token_usage"              # Token使用
    COST = "cost"                            # 成本
    CACHE_HIT_RATE = "cache_hit_rate"        # 缓存命中率
    CIRCUIT_BREAKER = "circuit_breaker"      # 断路器状态
    FALLBACK_RATE = "fallback_rate"          # 降级率
    MODEL_USAGE = "model_usage"              # 模型使用率


@dataclass
class AlertConfig:
    """告警配置"""
    metric_type: MetricType                  # 指标类型
    threshold: float                         # 阈值
    alert_level: AlertLevel                  # 告警级别
    duration_seconds: int = 60               # 持续时间（秒）
    notification_channels: List[str] = field(default_factory=list)  # 通知渠道
    enabled: bool = True                     # 是否启用
    cooldown_seconds: int = 300              # 冷却时间（秒）


@dataclass
class MetricData:
    """指标数据"""
    metric_type: MetricType                  # 指标类型
    value: float                             # 指标值
    timestamp: float                         # 时间戳
    model_id: Optional[str] = None           # 模型ID（可选）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class Alert:
    """告警"""
    id: str                                  # 告警ID
    metric_type: MetricType                  # 指标类型
    alert_level: AlertLevel                  # 告警级别
    message: str                             # 告警消息
    value: float                             # 触发值
    threshold: float                         # 阈值
    timestamp: float                         # 触发时间
    model_id: Optional[str] = None           # 模型ID（可选）
    acknowledged: bool = False               # 是否已确认
    resolved: bool = False                   # 是否已解决
    resolved_time: Optional[float] = None    # 解决时间
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


@dataclass
class DashboardConfig:
    """仪表板配置"""
    refresh_interval_seconds: int = 5        # 刷新间隔（秒）
    history_duration_hours: int = 24         # 历史数据保留时间（小时）
    max_alerts: int = 1000                   # 最大告警数
    enable_real_time_updates: bool = True    # 启用实时更新
    default_alert_configs: List[AlertConfig] = field(default_factory=list)  # 默认告警配置
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.default_alert_configs:
            self.default_alert_configs = [
                AlertConfig(
                    metric_type=MetricType.RESPONSE_TIME,
                    threshold=5000.0,  # 5秒
                    alert_level=AlertLevel.WARNING,
                    duration_seconds=60
                ),
                AlertConfig(
                    metric_type=MetricType.SUCCESS_RATE,
                    threshold=0.9,  # 90%
                    alert_level=AlertLevel.CRITICAL,
                    duration_seconds=300
                ),
                AlertConfig(
                    metric_type=MetricType.COST,
                    threshold=50.0,  # $50
                    alert_level=AlertLevel.WARNING,
                    duration_seconds=3600
                ),
                AlertConfig(
                    metric_type=MetricType.CACHE_HIT_RATE,
                    threshold=0.3,  # 30%
                    alert_level=AlertLevel.INFO,
                    duration_seconds=1800
                )
            ]


class MonitoringDashboardService:
    """监控仪表板服务"""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.logger = logging.getLogger(__name__)
        
        # 指标数据存储（按时间窗口）
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=10000)
        )
        
        # 当前指标值（最新）
        self.current_metrics: Dict[str, MetricData] = {}
        
        # 告警存储
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=self.config.max_alerts)
        
        # 告警配置
        self.alert_configs: Dict[str, AlertConfig] = {}
        for config in self.config.default_alert_configs:
            config_key = f"{config.metric_type.value}_{config.alert_level.value}"
            self.alert_configs[config_key] = config
        
        # 告警冷却时间跟踪
        self.alert_cooldowns: Dict[str, float] = {}
        
        # 锁
        self.metrics_lock = threading.RLock()
        self.alerts_lock = threading.RLock()
        
        # 统计
        self.stats = {
            "total_metrics_received": 0,
            "total_alerts_triggered": 0,
            "total_alerts_resolved": 0,
            "active_alerts": 0
        }
        
        # 启动后台任务
        self._stop_background_tasks = False
        self._background_tasks = []
        
        self.logger.info("监控仪表板服务初始化完成")
    
    def start(self) -> None:
        """启动监控服务"""
        # 启动后台清理任务
        cleanup_task = threading.Thread(
            target=self._cleanup_old_data,
            daemon=True,
            name="MonitoringCleanup"
        )
        cleanup_task.start()
        self._background_tasks.append(cleanup_task)
        
        # 启动告警检查任务
        alert_check_task = threading.Thread(
            target=self._check_alerts_periodically,
            daemon=True,
            name="AlertChecker"
        )
        alert_check_task.start()
        self._background_tasks.append(alert_check_task)
        
        self.logger.info("监控服务已启动")
    
    def stop(self) -> None:
        """停止监控服务"""
        self._stop_background_tasks = True
        for task in self._background_tasks:
            if task.is_alive():
                task.join(timeout=2)
        
        self.logger.info("监控服务已停止")
    
    def record_metric(self, metric_data: MetricData) -> None:
        """
        记录指标数据
        
        Args:
            metric_data: 指标数据
        """
        with self.metrics_lock:
            # 生成存储键
            storage_key = self._generate_storage_key(metric_data)
            
            # 存储到历史
            self.metrics_history[storage_key].append(metric_data)
            
            # 更新当前指标
            current_key = f"{metric_data.metric_type.value}_{metric_data.model_id or 'global'}"
            self.current_metrics[current_key] = metric_data
            
            # 更新统计
            self.stats["total_metrics_received"] += 1
            
            # 检查告警
            self._check_metric_for_alerts(metric_data)
    
    def record_response_time(
        self, 
        response_time_ms: float, 
        model_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录响应时间
        
        Args:
            response_time_ms: 响应时间（毫秒）
            model_id: 模型ID
            metadata: 元数据
        """
        metric_data = MetricData(
            metric_type=MetricType.RESPONSE_TIME,
            value=response_time_ms,
            timestamp=time.time(),
            model_id=model_id,
            metadata=metadata or {}
        )
        
        self.record_metric(metric_data)
    
    def record_success_rate(
        self, 
        success_rate: float, 
        model_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录成功率
        
        Args:
            success_rate: 成功率（0-1）
            model_id: 模型ID
            metadata: 元数据
        """
        metric_data = MetricData(
            metric_type=MetricType.SUCCESS_RATE,
            value=success_rate,
            timestamp=time.time(),
            model_id=model_id,
            metadata=metadata or {}
        )
        
        self.record_metric(metric_data)
    
    def record_token_usage(
        self, 
        tokens: int, 
        model_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录Token使用
        
        Args:
            tokens: Token数量
            model_id: 模型ID
            metadata: 元数据
        """
        metric_data = MetricData(
            metric_type=MetricType.TOKEN_USAGE,
            value=float(tokens),
            timestamp=time.time(),
            model_id=model_id,
            metadata=metadata or {}
        )
        
        self.record_metric(metric_data)
    
    def record_cost(
        self, 
        cost: float, 
        model_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录成本
        
        Args:
            cost: 成本（美元）
            model_id: 模型ID
            metadata: 元数据
        """
        metric_data = MetricData(
            metric_type=MetricType.COST,
            value=cost,
            timestamp=time.time(),
            model_id=model_id,
            metadata=metadata or {}
        )
        
        self.record_metric(metric_data)
    
    def get_current_metrics(self, filter_model: Optional[str] = None) -> List[MetricData]:
        """
        获取当前指标
        
        Args:
            filter_model: 过滤模型ID
            
        Returns:
            List[MetricData]: 当前指标列表
        """
        with self.metrics_lock:
            result = []
            
            for key, metric in self.current_metrics.items():
                if filter_model and metric.model_id != filter_model:
                    continue
                
                result.append(metric)
            
            return result
    
    def get_metric_history(
        self, 
        metric_type: MetricType,
        model_id: Optional[str] = None,
        time_window_seconds: Optional[int] = None
    ) -> List[MetricData]:
        """
        获取指标历史
        
        Args:
            metric_type: 指标类型
            model_id: 模型ID
            time_window_seconds: 时间窗口（秒）
            
        Returns:
            List[MetricData]: 指标历史列表
        """
        storage_key = self._generate_storage_key_for_query(metric_type, model_id)
        
        with self.metrics_lock:
            history = list(self.metrics_history.get(storage_key, deque()))
            
            if time_window_seconds:
                cutoff_time = time.time() - time_window_seconds
                history = [m for m in history if m.timestamp >= cutoff_time]
            
            return sorted(history, key=lambda x: x.timestamp)
    
    def get_active_alerts(self) -> List[Alert]:
        """
        获取活动告警
        
        Returns:
            List[Alert]: 活动告警列表
        """
        with self.alerts_lock:
            return [
                alert for alert in self.alerts.values() 
                if not alert.resolved
            ]
    
    def get_alert_history(
        self, 
        limit: int = 100,
        resolved_only: bool = False,
        level: Optional[AlertLevel] = None
    ) -> List[Alert]:
        """
        获取告警历史
        
        Args:
            limit: 限制数量
            resolved_only: 仅获取已解决的告警
            level: 告警级别过滤
            
        Returns:
            List[Alert]: 告警历史列表
        """
        with self.alerts_lock:
            alerts = list(self.alert_history)
            
            if resolved_only:
                alerts = [a for a in alerts if a.resolved]
            
            if level:
                alerts = [a for a in alerts if a.alert_level == level]
            
            # 按时间戳降序排序
            alerts.sort(key=lambda x: x.timestamp, reverse=True)
            
            return alerts[:limit]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        确认告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            bool: 是否成功
        """
        with self.alerts_lock:
            if alert_id in self.alerts:
                self.alerts[alert_id].acknowledged = True
                self.logger.info(f"告警已确认: {alert_id}")
                return True
            
            return False
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        解决告警
        
        Args:
            alert_id: 告警ID
            
        Returns:
            bool: 是否成功
        """
        with self.alerts_lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.resolved = True
                alert.resolved_time = time.time()
                self.stats["total_alerts_resolved"] += 1
                self.stats["active_alerts"] = max(0, self.stats["active_alerts"] - 1)
                self.logger.info(f"告警已解决: {alert_id}")
                return True
            
            return False
    
    def add_alert_config(self, config: AlertConfig) -> str:
        """
        添加告警配置
        
        Args:
            config: 告警配置
            
        Returns:
            str: 配置键
        """
        config_key = f"{config.metric_type.value}_{config.alert_level.value}_{len(self.alert_configs)}"
        self.alert_configs[config_key] = config
        self.logger.info(f"添加告警配置: {config_key}")
        return config_key
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        获取仪表板摘要
        
        Returns:
            Dict[str, Any]: 仪表板摘要
        """
        with self.metrics_lock:
            with self.alerts_lock:
                # 计算关键指标
                summary = {
                    "timestamp": time.time(),
                    "stats": self.stats.copy(),
                    "active_alerts_count": len(self.get_active_alerts()),
                    "system_status": "healthy"
                }
                
                # 检查系统状态
                active_alerts = self.get_active_alerts()
                critical_alerts = [a for a in active_alerts if a.alert_level == AlertLevel.CRITICAL]
                
                if critical_alerts:
                    summary["system_status"] = "critical"
                elif active_alerts:
                    summary["system_status"] = "warning"
                
                # 添加模型性能概览
                summary["model_performance"] = self._get_model_performance_summary()
                
                # 添加成本概览
                summary["cost_overview"] = self._get_cost_overview()
                
                return summary
    
    def _generate_storage_key(self, metric_data: MetricData) -> str:
        """生成存储键"""
        model_part = metric_data.model_id or "global"
        return f"{metric_data.metric_type.value}_{model_part}"
    
    def _generate_storage_key_for_query(
        self, 
        metric_type: MetricType, 
        model_id: Optional[str] = None
    ) -> str:
        """生成查询用的存储键"""
        model_part = model_id or "global"
        return f"{metric_type.value}_{model_part}"
    
    def _check_metric_for_alerts(self, metric_data: MetricData) -> None:
        """检查指标是否触发告警"""
        current_time = time.time()
        
        # 检查所有相关告警配置
        for config_key, config in self.alert_configs.items():
            if not config.enabled:
                continue
            
            if config.metric_type != metric_data.metric_type:
                continue
            
            # 检查冷却时间
            cooldown_key = f"{config_key}_{metric_data.model_id or 'global'}"
            last_trigger = self.alert_cooldowns.get(cooldown_key, 0)
            if current_time - last_trigger < config.cooldown_seconds:
                continue
            
            # 检查阈值
            should_trigger = False
            if config.metric_type in [MetricType.RESPONSE_TIME, MetricType.COST, MetricType.TOKEN_USAGE]:
                # 大于阈值触发
                should_trigger = metric_data.value > config.threshold
            elif config.metric_type in [MetricType.SUCCESS_RATE, MetricType.CACHE_HIT_RATE]:
                # 小于阈值触发
                should_trigger = metric_data.value < config.threshold
            
            if should_trigger:
                # 检查持续时间
                history = self.get_metric_history(
                    config.metric_type,
                    metric_data.model_id,
                    config.duration_seconds
                )
                
                # 检查在持续时间内是否一直超过阈值
                all_exceed = all(
                    (h.value > config.threshold if config.metric_type in [MetricType.RESPONSE_TIME, MetricType.COST, MetricType.TOKEN_USAGE]
                     else h.value < config.threshold)
                    for h in history
                )
                
                if all_exceed and len(history) >= 3:  # 至少有3个数据点
                    self._trigger_alert(metric_data, config)
                    self.alert_cooldowns[cooldown_key] = current_time
    
    def _trigger_alert(self, metric_data: MetricData, config: AlertConfig) -> None:
        """触发告警"""
        alert_id = f"alert_{int(time.time())}_{len(self.alerts)}"
        
        # 生成告警消息
        if metric_data.metric_type == MetricType.RESPONSE_TIME:
            message = f"响应时间超过阈值: {metric_data.value:.1f}ms > {config.threshold:.1f}ms"
        elif metric_data.metric_type == MetricType.SUCCESS_RATE:
            message = f"成功率低于阈值: {metric_data.value:.1%} < {config.threshold:.1%}"
        elif metric_data.metric_type == MetricType.COST:
            message = f"成本超过阈值: ${metric_data.value:.2f} > ${config.threshold:.2f}"
        elif metric_data.metric_type == MetricType.CACHE_HIT_RATE:
            message = f"缓存命中率低于阈值: {metric_data.value:.1%} < {config.threshold:.1%}"
        else:
            message = f"指标 {metric_data.metric_type.value} 超过阈值: {metric_data.value} > {config.threshold}"
        
        if metric_data.model_id:
            message = f"[{metric_data.model_id}] {message}"
        
        alert = Alert(
            id=alert_id,
            metric_type=metric_data.metric_type,
            alert_level=config.alert_level,
            message=message,
            value=metric_data.value,
            threshold=config.threshold,
            timestamp=time.time(),
            model_id=metric_data.model_id,
            metadata={
                "duration_seconds": config.duration_seconds,
                "notification_channels": config.notification_channels,
                **metric_data.metadata
            }
        )
        
        # 存储告警
        with self.alerts_lock:
            self.alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # 更新统计
            self.stats["total_alerts_triggered"] += 1
            self.stats["active_alerts"] += 1
        
        # 记录日志
        log_method = {
            AlertLevel.INFO: self.logger.info,
            AlertLevel.WARNING: self.logger.warning,
            AlertLevel.CRITICAL: self.logger.error
        }.get(config.alert_level, self.logger.warning)
        
        log_method(f"触发告警: {message}")
        
        # 发送通知（在实际系统中实现）
        self._send_notification(alert, config)
    
    def _send_notification(self, alert: Alert, config: AlertConfig) -> None:
        """发送通知（占位符实现）"""
        # 在实际系统中，这里应该集成邮件、Slack、Webhook等通知渠道
        # 目前只记录日志
        self.logger.debug(f"发送通知: {alert.message} (渠道: {config.notification_channels})")
    
    def _get_model_performance_summary(self) -> Dict[str, Any]:
        """获取模型性能摘要"""
        summary = {}
        
        # 获取所有模型的最新响应时间和成功率
        current_metrics = self.get_current_metrics()
        
        for metric in current_metrics:
            if metric.model_id and metric.metric_type in [MetricType.RESPONSE_TIME, MetricType.SUCCESS_RATE]:
                if metric.model_id not in summary:
                    summary[metric.model_id] = {}
                
                if metric.metric_type == MetricType.RESPONSE_TIME:
                    summary[metric.model_id]["response_time_ms"] = metric.value
                elif metric.metric_type == MetricType.SUCCESS_RATE:
                    summary[metric.model_id]["success_rate"] = metric.value
        
        return summary
    
    def _get_cost_overview(self) -> Dict[str, Any]:
        """获取成本概览"""
        # 获取最近24小时的成本数据
        cost_history = self.get_metric_history(
            MetricType.COST,
            time_window_seconds=86400  # 24小时
        )
        
        total_cost = sum(m.value for m in cost_history)
        avg_daily_cost = total_cost / max(len(cost_history), 1)
        
        # 按模型分组
        cost_by_model = defaultdict(float)
        for metric in cost_history:
            if metric.model_id:
                cost_by_model[metric.model_id] += metric.value
        
        return {
            "total_cost_24h": total_cost,
            "avg_daily_cost": avg_daily_cost,
            "cost_by_model": dict(cost_by_model)
        }
    
    def _cleanup_old_data(self) -> None:
        """清理旧数据"""
        while not self._stop_background_tasks:
            try:
                time.sleep(3600)  # 每小时清理一次
                
                cutoff_time = time.time() - (self.config.history_duration_hours * 3600)
                
                with self.metrics_lock:
                    # 清理旧指标数据
                    for key in list(self.metrics_history.keys()):
                        history = self.metrics_history[key]
                        # 移除旧数据
                        while history and history[0].timestamp < cutoff_time:
                            history.popleft()
                        
                        # 如果历史为空，移除键
                        if not history:
                            del self.metrics_history[key]
                
                with self.alerts_lock:
                    # 清理已解决的旧告警（保留7天）
                    alert_cutoff = time.time() - (7 * 86400)
                    alerts_to_remove = []
                    
                    for alert_id, alert in self.alerts.items():
                        if alert.resolved and alert.resolved_time and alert.resolved_time < alert_cutoff:
                            alerts_to_remove.append(alert_id)
                    
                    for alert_id in alerts_to_remove:
                        del self.alerts[alert_id]
                
                self.logger.debug("已完成数据清理")
                
            except Exception as e:
                self.logger.error(f"数据清理失败: {e}")
    
    def _check_alerts_periodically(self) -> None:
        """定期检查告警"""
        while not self._stop_background_tasks:
            try:
                time.sleep(30)  # 每30秒检查一次
                
                # 自动解决一些告警（如果指标已恢复正常）
                active_alerts = self.get_active_alerts()
                current_time = time.time()
                
                for alert in active_alerts:
                    # 获取最近指标
                    recent_metrics = self.get_metric_history(
                        alert.metric_type,
                        alert.model_id,
                        time_window_seconds=300  # 5分钟
                    )
                    
                    if not recent_metrics:
                        continue
                    
                    # 检查是否已恢复正常
                    recent_values = [m.value for m in recent_metrics]
                    avg_value = sum(recent_values) / len(recent_values)
                    
                    # 判断是否恢复正常
                    is_normal = False
                    if alert.metric_type in [MetricType.RESPONSE_TIME, MetricType.COST, MetricType.TOKEN_USAGE]:
                        is_normal = avg_value <= alert.threshold * 0.8  # 低于阈值的80%
                    elif alert.metric_type in [MetricType.SUCCESS_RATE, MetricType.CACHE_HIT_RATE]:
                        is_normal = avg_value >= alert.threshold * 1.2  # 高于阈值的120%
                    
                    if is_normal and (current_time - alert.timestamp) > 600:  # 告警存在超过10分钟
                        self.resolve_alert(alert.id)
                        self.logger.info(f"告警自动解决: {alert.id} (指标已恢复正常)")
                
            except Exception as e:
                self.logger.error(f"告警检查失败: {e}")


# 全局实例（单例模式）
_monitoring_dashboard_service = None
_monitoring_lock = threading.RLock()


def get_monitoring_dashboard_service(
    config: Optional[DashboardConfig] = None
) -> MonitoringDashboardService:
    """
    获取监控仪表板服务实例（单例模式）
    
    Args:
        config: 配置对象
        
    Returns:
        MonitoringDashboardService: 服务实例
    """
    global _monitoring_dashboard_service
    
    with _monitoring_lock:
        if _monitoring_dashboard_service is None:
            _monitoring_dashboard_service = MonitoringDashboardService(config)
            _monitoring_dashboard_service.start()
        
        return _monitoring_dashboard_service


__all__ = [
    "AlertLevel",
    "MetricType",
    "AlertConfig",
    "MetricData",
    "Alert",
    "DashboardConfig",
    "MonitoringDashboardService",
    "get_monitoring_dashboard_service",
]