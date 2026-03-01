#!/usr/bin/env python3
"""
自动扩缩容服务
基于系统指标动态调整资源分配和实例数量
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import statistics

# 依赖注入
from src.di.bootstrap import get_service, get_service_async

logger = logging.getLogger(__name__)


class ScalingDecision(Enum):
    """扩缩容决策"""
    SCALE_OUT = "scale_out"      # 扩容
    SCALE_IN = "scale_in"        # 缩容
    NO_ACTION = "no_action"      # 无动作
    COOLDOWN = "cooldown"        # 冷却期


class ScalingTarget(Enum):
    """扩缩容目标"""
    AGENT_INSTANCES = "agent_instances"      # 智能体实例数量
    WORKER_THREADS = "worker_threads"        # 工作线程数量
    RESOURCE_LIMITS = "resource_limits"      # 资源限制
    QUEUE_CAPACITY = "queue_capacity"        # 队列容量


@dataclass
class SystemMetric:
    """系统指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingRule:
    """扩缩容规则"""
    name: str
    target: ScalingTarget
    metric_name: str
    operator: str  # ">", "<", ">=", "<=", "=="
    threshold: float
    action: ScalingDecision
    cooldown_seconds: int = 300  # 默认5分钟冷却
    min_instances: int = 1
    max_instances: int = 10
    adjustment_step: int = 1
    description: str = ""


@dataclass
class ScalingHistoryEntry:
    """扩缩容历史记录"""
    timestamp: datetime
    decision: ScalingDecision
    target: ScalingTarget
    current_value: Any
    new_value: Any
    reason: str
    metrics: List[SystemMetric]
    success: bool = True
    error_message: Optional[str] = None


class AutoscalingService:
    """自动扩缩容服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化自动扩缩容服务"""
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 扩缩容历史
        self.scaling_history: List[ScalingHistoryEntry] = []
        self.max_history_size = self.config.get("max_history_size", 1000)
        
        # 冷却期跟踪
        self.cooldown_until: Dict[str, datetime] = {}
        
        # 默认规则
        self.scaling_rules: List[ScalingRule] = self._create_default_rules()
        
        # 当前状态
        self.current_agent_instances = self.config.get("initial_agent_instances", 2)
        self.current_worker_threads = self.config.get("initial_worker_threads", 4)
        
        # 监控间隔（秒）
        self.monitoring_interval = self.config.get("monitoring_interval", 30)
        
        # 是否启用
        self.enabled = self.config.get("enabled", True)
        
        # 监控任务
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
        
        self.logger.info("自动扩缩容服务初始化完成")
    
    def _create_default_rules(self) -> List[ScalingRule]:
        """创建默认扩缩容规则"""
        return [
            # CPU使用率规则
            ScalingRule(
                name="high_cpu_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="cpu_percent",
                operator=">",
                threshold=80.0,
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=300,
                min_instances=1,
                max_instances=20,
                adjustment_step=1,
                description="CPU使用率超过80%时扩容"
            ),
            ScalingRule(
                name="low_cpu_scale_in",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="cpu_percent",
                operator="<",
                threshold=20.0,
                action=ScalingDecision.SCALE_IN,
                cooldown_seconds=600,
                min_instances=1,
                max_instances=20,
                adjustment_step=1,
                description="CPU使用率低于20%时缩容"
            ),
            
            # 内存使用率规则
            ScalingRule(
                name="high_memory_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="memory_percent",
                operator=">",
                threshold=85.0,
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=300,
                min_instances=1,
                max_instances=20,
                adjustment_step=1,
                description="内存使用率超过85%时扩容"
            ),
            ScalingRule(
                name="low_memory_scale_in",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="memory_percent",
                operator="<",
                threshold=30.0,
                action=ScalingDecision.SCALE_IN,
                cooldown_seconds=600,
                min_instances=1,
                max_instances=20,
                adjustment_step=1,
                description="内存使用率低于30%时缩容"
            ),
            
            # 请求率规则
            ScalingRule(
                name="high_request_rate_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="request_rate",
                operator=">",
                threshold=100.0,
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=180,
                min_instances=1,
                max_instances=50,
                adjustment_step=2,
                description="请求率超过100 RPS时扩容"
            ),
            ScalingRule(
                name="low_request_rate_scale_in",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="request_rate",
                operator="<",
                threshold=10.0,
                action=ScalingDecision.SCALE_IN,
                cooldown_seconds=300,
                min_instances=1,
                max_instances=50,
                adjustment_step=1,
                description="请求率低于10 RPS时缩容"
            ),
            
            # 延迟规则
            ScalingRule(
                name="high_latency_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="request_latency_p95",
                operator=">",
                threshold=500.0,  # 500ms
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=240,
                min_instances=1,
                max_instances=30,
                adjustment_step=1,
                description="P95延迟超过500ms时扩容"
            ),
            ScalingRule(
                name="low_latency_scale_in",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="request_latency_p95",
                operator="<",
                threshold=100.0,  # 100ms
                action=ScalingDecision.SCALE_IN,
                cooldown_seconds=600,
                min_instances=1,
                max_instances=30,
                adjustment_step=1,
                description="P95延迟低于100ms时缩容"
            ),
        ]
    
    async def start_monitoring(self) -> None:
        """开始监控和自动扩缩容"""
        if not self.enabled:
            self.logger.info("自动扩缩容服务已禁用")
            return
        
        if self._running:
            self.logger.warning("监控任务已在运行中")
            return
        
        self._running = True
        self.logger.info("开始自动扩缩容监控")
        
        # 创建监控任务
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_monitoring(self) -> None:
        """停止监控"""
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
            self._monitoring_task = None
        
        self.logger.info("自动扩缩容监控已停止")
    
    async def _monitoring_loop(self) -> None:
        """监控循环"""
        while self._running:
            try:
                # 收集系统指标
                metrics = await self._collect_system_metrics()
                
                # 评估扩缩容规则
                decisions = await self._evaluate_scaling_rules(metrics)
                
                # 执行扩缩容决策
                for decision in decisions:
                    await self._execute_scaling_decision(decision, metrics)
                
                # 等待下一个监控周期
                await asyncio.sleep(self.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_system_metrics(self) -> List[SystemMetric]:
        """收集系统指标"""
        metrics = []
        timestamp = datetime.now()
        
        try:
            # 1. 收集系统级指标
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(SystemMetric(
                name="cpu_percent",
                value=cpu_percent,
                unit="percent",
                timestamp=timestamp,
                source="psutil"
            ))
            
            # 内存使用率
            memory = psutil.virtual_memory()
            metrics.append(SystemMetric(
                name="memory_percent",
                value=memory.percent,
                unit="percent",
                timestamp=timestamp,
                source="psutil"
            ))
            
            # 磁盘使用率
            disk = psutil.disk_usage('/')
            metrics.append(SystemMetric(
                name="disk_percent",
                value=disk.percent,
                unit="percent",
                timestamp=timestamp,
                source="psutil"
            ))
            
            # 2. 收集应用级指标（从性能监控器）
            try:
                from src.tools.monitoring.performance_monitor import PerformanceMonitor
                performance_monitor = PerformanceMonitor()
                perf_metrics = performance_monitor.get_current_metrics()
                
                for metric in perf_metrics:
                    metrics.append(SystemMetric(
                        name=metric.name,
                        value=metric.value,
                        unit=metric.unit,
                        timestamp=timestamp,
                        source="performance_monitor",
                        metadata=metric.metadata
                    ))
            except ImportError:
                self.logger.debug("性能监控器不可用")
            
            # 3. 收集请求指标（从指标收集器）
            try:
                from src.observability.metrics import MetricsCollector
                metrics_collector = MetricsCollector()
                
                # 获取请求率
                request_count = metrics_collector.get_metric_value("http_requests_total")
                if request_count:
                    metrics.append(SystemMetric(
                        name="request_count",
                        value=request_count,
                        unit="count",
                        timestamp=timestamp,
                        source="metrics_collector"
                    ))
                
                # 获取延迟指标
                latency_p95 = metrics_collector.get_metric_value("http_request_duration_seconds", {"quantile": "0.95"})
                if latency_p95:
                    metrics.append(SystemMetric(
                        name="request_latency_p95",
                        value=latency_p95 * 1000,  # 转换为毫秒
                        unit="milliseconds",
                        timestamp=timestamp,
                        source="metrics_collector"
                    ))
                
            except ImportError:
                self.logger.debug("指标收集器不可用")
            
            # 4. 计算请求率（如果可能）
            try:
                # 尝试从历史数据计算请求率
                request_rate = await self._calculate_request_rate()
                if request_rate is not None:
                    metrics.append(SystemMetric(
                        name="request_rate",
                        value=request_rate,
                        unit="requests_per_second",
                        timestamp=timestamp,
                        source="autoscaling_service"
                    ))
            except Exception as e:
                self.logger.debug(f"计算请求率失败: {e}")
        
        except ImportError as e:
            self.logger.error(f"收集系统指标失败（缺少依赖）: {e}")
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")
        
        return metrics
    
    async def _calculate_request_rate(self) -> Optional[float]:
        """计算请求率"""
        # 从历史记录中计算最近一分钟的请求率
        # 这是一个简化实现，实际中应该从监控系统获取
        try:
            from src.observability.metrics import MetricsCollector
            metrics_collector = MetricsCollector()
            
            # 获取最近60秒的请求计数
            # 这里需要实现时间窗口内的请求计数
            # 简化：返回一个固定值或None
            return None
        except Exception:
            return None
    
    async def _evaluate_scaling_rules(self, metrics: List[SystemMetric]) -> List[Dict[str, Any]]:
        """评估扩缩容规则"""
        decisions = []
        
        # 将指标转换为字典以便快速查找
        metrics_dict = {metric.name: metric for metric in metrics}
        
        for rule in self.scaling_rules:
            # 检查冷却期
            rule_key = f"{rule.name}_{rule.target.value}"
            if rule_key in self.cooldown_until:
                if datetime.now() < self.cooldown_until[rule_key]:
                    continue
            
            # 获取指标值
            if rule.metric_name not in metrics_dict:
                continue
            
            metric = metrics_dict[rule.metric_name]
            value = metric.value
            
            # 评估规则
            should_trigger = False
            
            if rule.operator == ">":
                should_trigger = value > rule.threshold
            elif rule.operator == "<":
                should_trigger = value < rule.threshold
            elif rule.operator == ">=":
                should_trigger = value >= rule.threshold
            elif rule.operator == "<=":
                should_trigger = value <= rule.threshold
            elif rule.operator == "==":
                should_trigger = value == rule.threshold
            else:
                self.logger.warning(f"未知操作符: {rule.operator}")
                continue
            
            if should_trigger:
                decisions.append({
                    "rule": rule,
                    "metric": metric,
                    "current_value": value,
                    "threshold": rule.threshold
                })
        
        return decisions
    
    async def _execute_scaling_decision(self, decision: Dict[str, Any], metrics: List[SystemMetric]) -> None:
        """执行扩缩容决策"""
        rule = decision["rule"]
        metric = decision["metric"]
        
        # 确定新的实例数量
        current_instances = self.current_agent_instances
        new_instances = current_instances
        
        if rule.action == ScalingDecision.SCALE_OUT:
            new_instances = min(current_instances + rule.adjustment_step, rule.max_instances)
        elif rule.action == ScalingDecision.SCALE_IN:
            new_instances = max(current_instances - rule.adjustment_step, rule.min_instances)
        else:
            return
        
        # 检查是否需要调整
        if new_instances == current_instances:
            return
        
        # 执行扩缩容
        success = False
        error_message = None
        
        try:
            self.logger.info(f"执行扩缩容: {rule.name}")
            self.logger.info(f"当前实例: {current_instances}, 新实例: {new_instances}")
            self.logger.info(f"触发指标: {metric.name}={metric.value}{metric.unit} {rule.operator} {rule.threshold}")
            
            # 实际扩缩容逻辑
            success = await self._perform_scaling(rule.target, current_instances, new_instances)
            
            if success:
                # 更新当前实例数量
                self.current_agent_instances = new_instances
                
                # 设置冷却期
                rule_key = f"{rule.name}_{rule.target.value}"
                self.cooldown_until[rule_key] = datetime.now() + timedelta(seconds=rule.cooldown_seconds)
                
                self.logger.info(f"扩缩容成功: {current_instances} -> {new_instances}")
            else:
                error_message = "扩缩容执行失败"
                self.logger.error(error_message)
        
        except Exception as e:
            success = False
            error_message = str(e)
            self.logger.error(f"扩缩容执行异常: {e}")
        
        # 记录历史
        history_entry = ScalingHistoryEntry(
            timestamp=datetime.now(),
            decision=rule.action,
            target=rule.target,
            current_value=current_instances,
            new_value=new_instances,
            reason=f"{metric.name}={metric.value}{metric.unit} {rule.operator} {rule.threshold}",
            metrics=metrics,
            success=success,
            error_message=error_message
        )
        
        self.scaling_history.append(history_entry)
        
        # 保持历史记录大小
        if len(self.scaling_history) > self.max_history_size:
            self.scaling_history = self.scaling_history[-self.max_history_size:]
    
    async def _perform_scaling(self, target: ScalingTarget, current_value: Any, new_value: Any) -> bool:
        """执行实际的扩缩容操作"""
        try:
            if target == ScalingTarget.AGENT_INSTANCES:
                return await self._scale_agent_instances(current_value, new_value)
            elif target == ScalingTarget.WORKER_THREADS:
                return await self._scale_worker_threads(current_value, new_value)
            elif target == ScalingTarget.RESOURCE_LIMITS:
                return await self._scale_resource_limits(current_value, new_value)
            elif target == ScalingTarget.QUEUE_CAPACITY:
                return await self._scale_queue_capacity(current_value, new_value)
            else:
                self.logger.warning(f"未知扩缩容目标: {target}")
                return False
        except Exception as e:
            self.logger.error(f"扩缩容执行失败: {e}")
            return False
    
    async def _scale_agent_instances(self, current_count: int, new_count: int) -> bool:
        """调整智能体实例数量"""
        self.logger.info(f"调整智能体实例数量: {current_count} -> {new_count}")
        
        # 这里需要与智能体协调器集成
        # 简化实现：记录日志并返回成功
        try:
            if new_count > current_count:
                # 扩容：启动新的智能体实例
                self.logger.info(f"启动 {new_count - current_count} 个新的智能体实例")
                # TODO: 实际启动智能体实例的逻辑
                
            elif new_count < current_count:
                # 缩容：停止部分智能体实例
                self.logger.info(f"停止 {current_count - new_count} 个智能体实例")
                # TODO: 实际停止智能体实例的逻辑
            
            return True
        
        except Exception as e:
            self.logger.error(f"调整智能体实例数量失败: {e}")
            return False
    
    async def _scale_worker_threads(self, current_threads: int, new_threads: int) -> bool:
        """调整工作线程数量"""
        self.logger.info(f"调整工作线程数量: {current_threads} -> {new_threads}")
        # TODO: 实际调整线程池大小的逻辑
        return True
    
    async def _scale_resource_limits(self, current_limits: Any, new_limits: Any) -> bool:
        """调整资源限制"""
        self.logger.info(f"调整资源限制: {current_limits} -> {new_limits}")
        # TODO: 实际调整资源限制的逻辑
        return True
    
    async def _scale_queue_capacity(self, current_capacity: Any, new_capacity: Any) -> bool:
        """调整队列容量"""
        self.logger.info(f"调整队列容量: {current_capacity} -> {new_capacity}")
        # TODO: 实际调整队列容量的逻辑
        return True
    
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "enabled": self.enabled,
            "running": self._running,
            "current_agent_instances": self.current_agent_instances,
            "current_worker_threads": self.current_worker_threads,
            "monitoring_interval": self.monitoring_interval,
            "scaling_rules_count": len(self.scaling_rules),
            "scaling_history_count": len(self.scaling_history),
            "cooldown_entries": len(self.cooldown_until)
        }
    
    def get_scaling_history(self, limit: int = 20) -> List[ScalingHistoryEntry]:
        """获取扩缩容历史"""
        return self.scaling_history[-limit:] if self.scaling_history else []
    
    def add_scaling_rule(self, rule: ScalingRule) -> None:
        """添加扩缩容规则"""
        self.scaling_rules.append(rule)
        self.logger.info(f"添加扩缩容规则: {rule.name}")
    
    def remove_scaling_rule(self, rule_name: str) -> bool:
        """移除扩缩容规则"""
        initial_count = len(self.scaling_rules)
        self.scaling_rules = [r for r in self.scaling_rules if r.name != rule_name]
        
        removed = len(self.scaling_rules) < initial_count
        if removed:
            self.logger.info(f"移除扩缩容规则: {rule_name}")
        
        return removed
    
    def enable(self) -> None:
        """启用自动扩缩容"""
        self.enabled = True
        self.logger.info("自动扩缩容已启用")
    
    def disable(self) -> None:
        """禁用自动扩缩容"""
        self.enabled = False
        self.logger.info("自动扩缩容已禁用")
    
    def clear_cooldown(self) -> None:
        """清除所有冷却期"""
        self.cooldown_until.clear()
        self.logger.info("所有冷却期已清除")


# 工厂函数（用于依赖注入）
def create_autoscaling_service(config: Optional[Dict[str, Any]] = None) -> AutoscalingService:
    """创建自动扩缩容服务实例"""
    return AutoscalingService(config)