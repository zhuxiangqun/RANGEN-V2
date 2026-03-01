#!/usr/bin/env python3
"""
Hook监控器模块
实时监控系统事件，生成警报，提供系统健康状态
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
from dataclasses import dataclass, field

from .hook_types import HookEvent, HookEventType, HookVisibilityLevel


class AlertSeverity(Enum):
    """警报严重级别"""
    INFO = "info"  # 信息
    WARNING = "warning"  # 警告
    ERROR = "error"  # 错误
    CRITICAL = "critical"  # 关键


class AlertType(Enum):
    """警报类型"""
    ERROR_FREQUENCY = "error_frequency"  # 错误频率过高
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降
    RESOURCE_USAGE = "resource_usage"  # 资源使用异常
    SYSTEM_STATE_CHANGE = "system_state_change"  # 系统状态变化
    SECURITY_CONCERN = "security_concern"  # 安全担忧
    CONSTITUTION_VIOLATION = "constitution_violation"  # 宪法违反
    EVOLUTION_STALLED = "evolution_stalled"  # 进化停滞
    AGENT_DECISION_TREND = "agent_decision_trend"  # 智能体决策趋势


class SystemHealthStatus(Enum):
    """系统健康状态"""
    HEALTHY = "healthy"  # 健康
    DEGRADED = "degraded"  # 降级
    CRITICAL = "critical"  # 关键
    EVOLVING = "evolving"  # 进化中
    LEARNING = "learning"  # 学习中
    MAINTENANCE = "maintenance"  # 维护中


@dataclass
class HookAlert:
    """Hook警报"""
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    timestamp: str
    message: str
    source_event_id: Optional[str] = None
    affected_components: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


class HookMonitor:
    """Hook监控器"""
    
    def __init__(self, system_name: str = "rangen_system"):
        self.logger = logging.getLogger(__name__)
        self.system_name = system_name
        
        # 事件窗口（用于趋势分析）
        self.event_window: deque[HookEvent] = deque(maxlen=1000)  # 最近1000个事件
        self.event_stats: Dict[str, Any] = defaultdict(int)
        
        # 警报系统
        self.active_alerts: Dict[str, HookAlert] = {}
        self.alert_history: List[HookAlert] = []
        
        # 监控配置
        self.config = self._load_default_config()
        
        # 系统健康状态
        self.system_health = SystemHealthStatus.HEALTHY
        self.health_history: List[Dict[str, Any]] = []
        
        # 性能指标
        self.performance_metrics = {
            "event_processing_latency": deque(maxlen=100),
            "error_rate": deque(maxlen=100),
            "success_rate": deque(maxlen=100),
            "response_time": deque(maxlen=100)
        }
        
        # 组件状态
        self.component_status: Dict[str, Dict[str, Any]] = {}
        
        # 趋势分析器
        self.trend_analyzers = self._initialize_trend_analyzers()
        
        self.logger.info(f"Hook监控器初始化: {system_name}")
    
    def _load_default_config(self) -> Dict[str, Any]:
        """加载默认配置"""
        return {
            "alert_thresholds": {
                "error_frequency": {
                    "window_minutes": 5,
                    "threshold_count": 10,
                    "severity": AlertSeverity.WARNING
                },
                "performance_degradation": {
                    "response_time_increase_percent": 50,
                    "window_minutes": 10,
                    "severity": AlertSeverity.WARNING
                },
                "constitution_violation": {
                    "severity": AlertSeverity.CRITICAL
                },
                "system_state_change": {
                    "to_critical": AlertSeverity.CRITICAL,
                    "to_degraded": AlertSeverity.WARNING
                },
                "evolution_stalled": {
                    "stalled_hours": 24,
                    "severity": AlertSeverity.WARNING
                }
            },
            "health_check_intervals": {
                "error_rate_check_minutes": 5,
                "performance_check_minutes": 10,
                "resource_check_minutes": 15,
                "system_state_check_minutes": 2
            },
            "retention_periods": {
                "event_window_hours": 24,
                "alert_history_days": 30,
                "health_history_days": 7
            },
            "monitoring_enabled": True,
            "real_time_processing": True,
            "alert_notification_channels": ["log", "internal"]
        }
    
    def _initialize_trend_analyzers(self) -> Dict[str, Any]:
        """初始化趋势分析器"""
        return {
            "error_trend": {
                "window_size": 100,
                "threshold": 0.1,  # 10%错误率
                "sensitivity": "medium"
            },
            "performance_trend": {
                "window_size": 50,
                "degradation_threshold": 0.3,  # 30%性能下降
                "sensitivity": "high"
            },
            "decision_pattern": {
                "window_size": 200,
                "pattern_detection_sensitivity": 0.8,
                "anomaly_detection": True
            },
            "resource_usage": {
                "window_size": 100,
                "high_usage_threshold": 0.8,  # 80%使用率
                "trend_analysis": True
            }
        }
    
    async def process_event(self, event: HookEvent):
        """处理事件"""
        if not self.config.get("monitoring_enabled", True):
            return
        
        try:
            # 记录事件到窗口
            self.event_window.append(event)
            
            # 更新事件统计
            event_type = event.event_type.value
            self.event_stats[event_type] += 1
            self.event_stats["total"] += 1
            
            # 实时监控分析
            await self._analyze_event_real_time(event)
            
            # 更新性能指标
            await self._update_performance_metrics(event)
            
            # 定期健康检查
            await self._perform_periodic_health_checks()
            
            # 检测警报条件
            await self._detect_alert_conditions(event)
            
            self.logger.debug(f"处理监控事件: {event.event_id} ({event_type})")
            
        except Exception as e:
            self.logger.error(f"处理监控事件失败: {e}")
    
    async def _analyze_event_real_time(self, event: HookEvent):
        """实时分析事件"""
        event_type = event.event_type
        
        # 错误事件特别处理
        if event_type == HookEventType.ERROR_OCCURRED:
            await self._handle_error_event(event)
        
        # 系统状态变化
        elif event_type == HookEventType.SYSTEM_STATE_CHANGE:
            await self._handle_system_state_change(event)
        
        # 宪法检查结果
        elif event_type == HookEventType.CONSTITUTION_CHECK:
            await self._handle_constitution_check(event)
        
        # 进化计划
        elif event_type == HookEventType.EVOLUTION_PLAN:
            await self._handle_evolution_plan(event)
        
        # 智能体决策趋势
        elif event_type == HookEventType.AGENT_DECISION:
            await self._analyze_agent_decision_pattern(event)
    
    async def _handle_error_event(self, event: HookEvent):
        """处理错误事件"""
        error_type = event.data.get("error_type", "unknown")
        error_message = event.data.get("error_message", "")
        
        # 错误频率分析
        error_key = f"error_{error_type}"
        self.event_stats[error_key] = self.event_stats.get(error_key, 0) + 1
        
        # 检查错误频率阈值
        window_minutes = self.config["alert_thresholds"]["error_frequency"]["window_minutes"]
        threshold_count = self.config["alert_thresholds"]["error_frequency"]["threshold_count"]
        
        # 计算时间窗口内的错误数量
        recent_errors = await self._count_events_in_window(
            HookEventType.ERROR_OCCURRED, 
            window_minutes
        )
        
        if recent_errors >= threshold_count:
            # 生成警报
            alert_message = f"过去{window_minutes}分钟内发生{recent_errors}次错误，超过阈值{threshold_count}"
            await self._create_alert(
                alert_type=AlertType.ERROR_FREQUENCY,
                severity=self.config["alert_thresholds"]["error_frequency"]["severity"],
                message=alert_message,
                source_event_id=event.event_id,
                metadata={
                    "error_type": error_type,
                    "error_count": recent_errors,
                    "threshold": threshold_count,
                    "window_minutes": window_minutes
                }
            )
    
    async def _handle_system_state_change(self, event: HookEvent):
        """处理系统状态变化"""
        data = event.data
        previous_state = data.get("previous_state", "unknown")
        current_state = data.get("current_state", "unknown")
        change_type = data.get("change_type", "unknown")
        
        # 更新系统健康状态
        new_health_status = self._map_system_state_to_health(current_state)
        
        if new_health_status != self.system_health:
            old_health = self.system_health
            self.system_health = new_health_status
            
            # 记录健康历史
            self.health_history.append({
                "timestamp": datetime.now().isoformat(),
                "previous_health": old_health.value,
                "current_health": new_health_status.value,
                "trigger_event_id": event.event_id,
                "change_type": change_type
            })
            
            # 清理旧历史
            self._cleanup_old_health_history()
            
            # 检查是否需要警报
            alert_config = self.config["alert_thresholds"]["system_state_change"]
            
            if current_state == "critical":
                severity = alert_config.get("to_critical", AlertSeverity.CRITICAL)
                alert_message = f"系统状态变为关键: {previous_state} -> {current_state}"
                await self._create_alert(
                    alert_type=AlertType.SYSTEM_STATE_CHANGE,
                    severity=severity,
                    message=alert_message,
                    source_event_id=event.event_id,
                    metadata={
                        "previous_state": previous_state,
                        "current_state": current_state,
                        "change_type": change_type
                    }
                )
            
            elif current_state == "degraded":
                severity = alert_config.get("to_degraded", AlertSeverity.WARNING)
                alert_message = f"系统状态降级: {previous_state} -> {current_state}"
                await self._create_alert(
                    alert_type=AlertType.SYSTEM_STATE_CHANGE,
                    severity=severity,
                    message=alert_message,
                    source_event_id=event.event_id,
                    metadata={
                        "previous_state": previous_state,
                        "current_state": current_state,
                        "change_type": change_type
                    }
                )
    
    async def _handle_constitution_check(self, event: HookEvent):
        """处理宪法检查"""
        data = event.data
        check_result = data.get("check_result", {})
        compliance = check_result.get("compliance", True)
        
        if not compliance:
            # 宪法违反警报
            plan_id = data.get("plan_id", "unknown")
            issues = check_result.get("issues", [])
            
            alert_message = f"宪法检查未通过: 计划 {plan_id} 违反宪法规范"
            await self._create_alert(
                alert_type=AlertType.CONSTITUTION_VIOLATION,
                severity=self.config["alert_thresholds"]["constitution_violation"]["severity"],
                message=alert_message,
                source_event_id=event.event_id,
                metadata={
                    "plan_id": plan_id,
                    "issues": issues[:5],  # 只取前5个问题
                    "compliance": compliance
                }
            )
    
    async def _handle_evolution_plan(self, event: HookEvent):
        """处理进化计划"""
        data = event.data
        status = data.get("status", "proposed")
        plan = data.get("plan", {})
        plan_id = plan.get("id", "unknown")
        
        # 跟踪进化计划状态
        if status == "proposed":
            # 记录计划提出时间
            if "evolution_tracking" not in self.component_status:
                self.component_status["evolution_tracking"] = {}
            
            self.component_status["evolution_tracking"][plan_id] = {
                "proposed_at": datetime.now().isoformat(),
                "status": "proposed",
                "last_update": datetime.now().isoformat()
            }
        
        elif status in ["executing", "completed", "failed"]:
            # 更新计划状态
            if "evolution_tracking" in self.component_status and plan_id in self.component_status["evolution_tracking"]:
                self.component_status["evolution_tracking"][plan_id].update({
                    "status": status,
                    "last_update": datetime.now().isoformat()
                })
        
        # 检查进化停滞
        await self._check_evolution_stall()
    
    async def _analyze_agent_decision_pattern(self, event: HookEvent):
        """分析智能体决策模式"""
        data = event.data
        agent = data.get("agent", "unknown")
        decision = data.get("decision", {})
        
        # 跟踪智能体决策
        agent_key = f"agent_{agent}"
        if agent_key not in self.component_status:
            self.component_status[agent_key] = {
                "decision_count": 0,
                "decision_types": defaultdict(int),
                "recent_decisions": deque(maxlen=20),
                "last_decision_time": None
            }
        
        agent_stats = self.component_status[agent_key]
        agent_stats["decision_count"] += 1
        
        decision_type = decision.get("type", "unknown")
        agent_stats["decision_types"][decision_type] += 1
        
        agent_stats["recent_decisions"].append({
            "timestamp": datetime.now().isoformat(),
            "type": decision_type,
            "event_id": event.event_id
        })
        
        agent_stats["last_decision_time"] = datetime.now().isoformat()
        
        # 检测决策模式异常
        await self._detect_decision_pattern_anomalies(agent, agent_stats)
    
    async def _update_performance_metrics(self, event: HookEvent):
        """更新性能指标"""
        # 简单实现：记录事件处理延迟
        if event.event_type == HookEventType.HAND_EXECUTION:
            data = event.data
            result = data.get("result", {})
            execution_time = result.get("execution_time", 0)
            
            if isinstance(execution_time, (int, float)) and execution_time > 0:
                self.performance_metrics["event_processing_latency"].append(execution_time)
        
        # 更新错误率
        if event.event_type == HookEventType.ERROR_OCCURRED:
            self.performance_metrics["error_rate"].append(1)  # 错误
        elif event.event_type in [HookEventType.HAND_EXECUTION, HookEventType.AGENT_DECISION]:
            # 假设这些事件可能成功或失败
            data = event.data
            result = data.get("result", {})
            success = result.get("success", True)
            self.performance_metrics["success_rate"].append(1 if success else 0)
    
    async def _perform_periodic_health_checks(self):
        """执行定期健康检查"""
        # 简单实现：检查性能指标
        current_time = datetime.now()
        
        # 每5分钟检查一次错误率
        if not hasattr(self, "_last_error_rate_check"):
            self._last_error_rate_check = current_time
        
        if (current_time - self._last_error_rate_check).total_seconds() >= 300:  # 5分钟
            await self._check_error_rate()
            self._last_error_rate_check = current_time
        
        # 每10分钟检查一次性能
        if not hasattr(self, "_last_performance_check"):
            self._last_performance_check = current_time
        
        if (current_time - self._last_performance_check).total_seconds() >= 600:  # 10分钟
            await self._check_performance()
            self._last_performance_check = current_time
    
    async def _check_error_rate(self):
        """检查错误率"""
        error_rate_window = list(self.performance_metrics["error_rate"])
        if not error_rate_window:
            return
        
        error_rate = sum(error_rate_window) / len(error_rate_window)
        
        if error_rate > 0.1:  # 10%错误率
            alert_message = f"系统错误率过高: {error_rate:.1%}"
            await self._create_alert(
                alert_type=AlertType.ERROR_FREQUENCY,
                severity=AlertSeverity.WARNING,
                message=alert_message,
                metadata={
                    "error_rate": error_rate,
                    "window_size": len(error_rate_window),
                    "threshold": 0.1
                }
            )
    
    async def _check_performance(self):
        """检查性能"""
        latency_window = list(self.performance_metrics["event_processing_latency"])
        if len(latency_window) < 10:
            return
        
        avg_latency = sum(latency_window) / len(latency_window)
        
        # 检查性能下降
        config = self.config["alert_thresholds"]["performance_degradation"]
        threshold_percent = config.get("response_time_increase_percent", 50)
        
        # 简单实现：与历史基线比较
        if hasattr(self, "_baseline_latency") and self._baseline_latency > 0:
            increase_percent = ((avg_latency - self._baseline_latency) / self._baseline_latency) * 100
            
            if increase_percent >= threshold_percent:
                alert_message = f"系统性能下降: 延迟增加{increase_percent:.1f}%"
                await self._create_alert(
                    alert_type=AlertType.PERFORMANCE_DEGRADATION,
                    severity=config.get("severity", AlertSeverity.WARNING),
                    message=alert_message,
                    metadata={
                        "current_latency": avg_latency,
                        "baseline_latency": self._baseline_latency,
                        "increase_percent": increase_percent,
                        "threshold_percent": threshold_percent
                    }
                )
        else:
            # 设置基线
            self._baseline_latency = avg_latency
    
    async def _check_evolution_stall(self):
        """检查进化停滞"""
        if "evolution_tracking" not in self.component_status:
            return
        
        evolution_tracking = self.component_status["evolution_tracking"]
        if not evolution_tracking:
            return
        
        config = self.config["alert_thresholds"]["evolution_stalled"]
        stalled_hours = config.get("stalled_hours", 24)
        
        current_time = datetime.now()
        stalled_plans = []
        
        for plan_id, plan_info in evolution_tracking.items():
            if plan_info.get("status") == "proposed":
                proposed_at_str = plan_info.get("proposed_at")
                if proposed_at_str:
                    try:
                        proposed_at = datetime.fromisoformat(proposed_at_str)
                        hours_stalled = (current_time - proposed_at).total_seconds() / 3600
                        
                        if hours_stalled >= stalled_hours:
                            stalled_plans.append({
                                "plan_id": plan_id,
                                "hours_stalled": hours_stalled,
                                "proposed_at": proposed_at_str
                            })
                    except ValueError:
                        continue
        
        if stalled_plans:
            alert_message = f"发现{len(stalled_plans)}个进化计划停滞超过{stalled_hours}小时"
            await self._create_alert(
                alert_type=AlertType.EVOLUTION_STALLED,
                severity=config.get("severity", AlertSeverity.WARNING),
                message=alert_message,
                metadata={
                    "stalled_plans": stalled_plans,
                    "stalled_hours": stalled_hours
                }
            )
    
    async def _detect_decision_pattern_anomalies(self, agent: str, agent_stats: Dict[str, Any]):
        """检测决策模式异常"""
        recent_decisions = list(agent_stats["recent_decisions"])
        if len(recent_decisions) < 10:
            return
        
        # 简单实现：检查决策类型分布
        decision_types = agent_stats["decision_types"]
        total_decisions = agent_stats["decision_count"]
        
        if total_decisions > 20:
            # 计算主要决策类型比例
            main_decision_type = max(decision_types.items(), key=lambda x: x[1]) if decision_types else None
            
            if main_decision_type:
                type_name, count = main_decision_type
                proportion = count / total_decisions
                
                if proportion > 0.8:  # 80%以上为同一种决策类型
                    alert_message = f"智能体 {agent} 决策模式单一: {type_name} 占{proportion:.1%}"
                    await self._create_alert(
                        alert_type=AlertType.AGENT_DECISION_TREND,
                        severity=AlertSeverity.WARNING,
                        message=alert_message,
                        metadata={
                            "agent": agent,
                            "main_decision_type": type_name,
                            "proportion": proportion,
                            "total_decisions": total_decisions
                        }
                    )
    
    async def _detect_alert_conditions(self, event: HookEvent):
        """检测警报条件"""
        # 这里已经由各个处理函数处理了
        pass
    
    async def _create_alert(self, alert_type: AlertType, severity: AlertSeverity, 
                           message: str, source_event_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建警报"""
        alert_id = f"alert_{alert_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        alert = HookAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            message=message,
            source_event_id=source_event_id,
            metadata=metadata or {},
            acknowledged=False,
            resolved=False
        )
        
        # 添加到活跃警报
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # 清理旧警报历史
        self._cleanup_old_alerts()
        
        # 记录日志
        self.logger.warning(f"创建警报: {alert_id} [{severity.value}] {message}")
        
        # 通知（简单实现：日志输出）
        await self._notify_alert(alert)
        
        return alert_id
    
    async def _notify_alert(self, alert: HookAlert):
        """通知警报"""
        channels = self.config.get("alert_notification_channels", ["log"])
        
        for channel in channels:
            if channel == "log":
                # 已经记录日志了
                pass
            elif channel == "internal":
                # 内部通知（可以扩展）
                pass
    
    async def _count_events_in_window(self, event_type: HookEventType, minutes: int) -> int:
        """计算时间窗口内的事件数量"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        count = 0
        
        for event in self.event_window:
            if event.event_type == event_type:
                try:
                    event_time = datetime.fromisoformat(event.timestamp)
                    if event_time >= cutoff_time:
                        count += 1
                except ValueError:
                    continue
        
        return count
    
    def _map_system_state_to_health(self, system_state: str) -> SystemHealthStatus:
        """映射系统状态到健康状态"""
        mapping = {
            "healthy": SystemHealthStatus.HEALTHY,
            "degraded": SystemHealthStatus.DEGRADED,
            "critical": SystemHealthStatus.CRITICAL,
            "evolving": SystemHealthStatus.EVOLVING,
            "learning": SystemHealthStatus.LEARNING,
            "maintenance": SystemHealthStatus.MAINTENANCE
        }
        
        return mapping.get(system_state, SystemHealthStatus.HEALTHY)
    
    def _cleanup_old_alerts(self):
        """清理旧警报"""
        retention_days = self.config["retention_periods"].get("alert_history_days", 30)
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        # 清理警报历史
        self.alert_history = [
            alert for alert in self.alert_history
            if datetime.fromisoformat(alert.timestamp) >= cutoff_time
        ]
        
        # 清理活跃警报（标记为已解决的）
        resolved_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.resolved and datetime.fromisoformat(alert.timestamp) < cutoff_time
        ]
        
        for alert_id in resolved_alerts:
            del self.active_alerts[alert_id]
    
    def _cleanup_old_health_history(self):
        """清理旧健康历史"""
        retention_days = self.config["retention_periods"].get("health_history_days", 7)
        cutoff_time = datetime.now() - timedelta(days=retention_days)
        
        self.health_history = [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) >= cutoff_time
        ]
    
    async def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        # 计算性能指标
        error_rate = 0
        success_rate = 0
        avg_latency = 0
        
        error_rate_window = list(self.performance_metrics["error_rate"])
        if error_rate_window:
            error_rate = sum(error_rate_window) / len(error_rate_window)
        
        success_rate_window = list(self.performance_metrics["success_rate"])
        if success_rate_window:
            success_rate = sum(success_rate_window) / len(success_rate_window)
        
        latency_window = list(self.performance_metrics["event_processing_latency"])
        if latency_window:
            avg_latency = sum(latency_window) / len(latency_window)
        
        # 统计组件状态
        component_count = len(self.component_status)
        healthy_components = sum(
            1 for comp in self.component_status.values()
            if comp.get("status", "unknown") == "healthy"
        )
        
        # 活跃警报统计
        active_alerts_by_severity = defaultdict(int)
        for alert in self.active_alerts.values():
            if not alert.resolved:
                active_alerts_by_severity[alert.severity.value] += 1
        
        health_report = {
            "system_health": self.system_health.value,
            "timestamp": datetime.now().isoformat(),
            "performance_metrics": {
                "error_rate": error_rate,
                "success_rate": success_rate,
                "average_latency_seconds": avg_latency,
                "event_count": self.event_stats.get("total", 0)
            },
            "component_status": {
                "total_components": component_count,
                "healthy_components": healthy_components,
                "unhealthy_components": component_count - healthy_components
            },
            "alert_status": {
                "active_alerts": len([a for a in self.active_alerts.values() if not a.resolved]),
                "by_severity": dict(active_alerts_by_severity),
                "total_alerts_history": len(self.alert_history)
            },
            "health_history_summary": {
                "entries": len(self.health_history),
                "last_change": self.health_history[-1]["timestamp"] if self.health_history else None
            },
            "recommendations": self._generate_health_recommendations()
        }
        
        return health_report
    
    def _generate_health_recommendations(self) -> List[str]:
        """生成健康建议"""
        recommendations = []
        
        # 基于系统健康状态
        if self.system_health == SystemHealthStatus.CRITICAL:
            recommendations.append("系统处于关键状态，需要立即检查")
            recommendations.append("建议查看错误日志和活跃警报")
            recommendations.append("考虑回滚到稳定版本")
        
        elif self.system_health == SystemHealthStatus.DEGRADED:
            recommendations.append("系统性能降级，建议优化资源使用")
            recommendations.append("检查是否有组件故障")
            recommendations.append("监控错误率和响应时间")
        
        elif self.system_health == SystemHealthStatus.EVOLVING:
            recommendations.append("系统正在进化，某些功能可能不可用")
            recommendations.append("监控进化计划执行状态")
            recommendations.append("确保有足够的系统资源")
        
        # 基于警报
        critical_alerts = [a for a in self.active_alerts.values() 
                          if a.severity == AlertSeverity.CRITICAL and not a.resolved]
        
        if critical_alerts:
            recommendations.append(f"有{len(critical_alerts)}个关键警报需要处理")
        
        # 基于性能指标
        error_rate_window = list(self.performance_metrics["error_rate"])
        if error_rate_window and sum(error_rate_window) / len(error_rate_window) > 0.05:
            recommendations.append("错误率较高，建议检查系统配置和依赖")
        
        return recommendations
    
    async def get_alert_count(self) -> Dict[str, int]:
        """获取警报数量"""
        active_alerts = [a for a in self.active_alerts.values() if not a.resolved]
        
        return {
            "total": len(active_alerts),
            "by_severity": {
                "info": len([a for a in active_alerts if a.severity == AlertSeverity.INFO]),
                "warning": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                "error": len([a for a in active_alerts if a.severity == AlertSeverity.ERROR]),
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL])
            }
        }
    
    async def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """确认警报"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.acknowledged = True
            alert.metadata["acknowledged_by"] = user
            alert.metadata["acknowledged_at"] = datetime.now().isoformat()
            
            self.logger.info(f"警报已确认: {alert_id} 由 {user}")
            return True
        
        return False
    
    async def resolve_alert(self, alert_id: str, resolution_note: str = "") -> bool:
        """解决警报"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.metadata["resolved_at"] = datetime.now().isoformat()
            alert.metadata["resolution_note"] = resolution_note
            
            self.logger.info(f"警报已解决: {alert_id}")
            return True
        
        return False
    
    async def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[HookAlert]:
        """获取活跃警报"""
        alerts = [alert for alert in self.active_alerts.values() if not alert.resolved]
        
        if severity:
            alerts = [alert for alert in alerts if alert.severity == severity]
        
        return alerts
    
    async def get_alert_history(self, limit: int = 50) -> List[HookAlert]:
        """获取警报历史"""
        return self.alert_history[-limit:] if self.alert_history else []
    
    def update_config(self, config_updates: Dict[str, Any]):
        """更新配置"""
        self._deep_update(self.config, config_updates)
        self.logger.info("监控配置已更新")
    
    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]):
        """深度更新字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._deep_update(target[key], value)
            else:
                target[key] = value
    
    def __str__(self):
        return f"HookMonitor({self.system_name})"