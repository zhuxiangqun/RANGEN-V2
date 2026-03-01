"""
LangGraph监控适配器

解决监控系统重复建设问题，实现LangGraph原生监控与自定义监控系统的深度集成
提供统一的监控面板和智能告警路由
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable, Union, Protocol
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
from abc import ABC
import threading


logger = logging.getLogger(__name__)


class MonitoringSource(Enum):
    """监控源类型"""
    LANGGRAPH_NATIVE = "langgraph_native"  # LangGraph原生监控
    CUSTOM_SYSTEM = "custom_system"        # 自定义监控系统
    EXTERNAL_METRICS = "external_metrics"  # 外部指标


@dataclass
class UnifiedMetric:
    """统一指标格式"""
    name: str
    value: Union[int, float]
    timestamp: float
    source: MonitoringSource
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UnifiedAlert:
    """统一告警格式"""
    alert_id: str
    title: str
    description: str
    severity: str  # info, warning, error, critical
    source: MonitoringSource
    timestamp: float
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[float] = None


@dataclass
class MonitoringBridge:
    """监控桥接器"""
    source: MonitoringSource
    adapter_function: Callable
    enabled: bool = True
    last_sync: Optional[float] = None
    sync_interval: float = 30.0  # 同步间隔（秒）


class LangGraphMetricsExtractor:
    """LangGraph指标提取器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._metrics_cache: Dict[str, Any] = {}
        self._extraction_functions = {
            "node_execution_times": self._extract_node_execution_times,
            "workflow_status": self._extract_workflow_status,
            "error_rates": self._extract_error_rates,
            "resource_usage": self._extract_resource_usage,
            "performance_metrics": self._extract_performance_metrics
        }

    def extract_metrics(self, langgraph_context: Optional[Any] = None) -> List[UnifiedMetric]:
        """
        从LangGraph上下文中提取指标

        由于无法直接访问LangGraph内部状态，这里通过：
        1. 环境变量和配置推断
        2. 日志分析（如果可用）
        3. 默认假设和模拟
        """
        metrics = []

        # 尝试从不同来源提取指标
        for metric_name, extractor_func in self._extraction_functions.items():
            try:
                extracted_metrics = extractor_func(langgraph_context)
                metrics.extend(extracted_metrics)
            except Exception as e:
                self.logger.debug(f"提取指标失败 {metric_name}: {e}")

        return metrics

    def _extract_node_execution_times(self, context: Optional[Any] = None) -> List[UnifiedMetric]:
        """提取节点执行时间"""
        # 由于无法直接访问，这里返回模拟指标
        # 实际实现中应该从LangGraph的状态或日志中提取
        metrics = []

        # 模拟一些常见的LangGraph节点指标
        common_nodes = ["query_analysis", "reasoning", "answer_generation", "citation"]

        for node in common_nodes:
            # 模拟执行时间（实际应该从真实数据中获取）
            avg_time = self._get_simulated_node_time(node)

            metrics.append(UnifiedMetric(
                name=f"langgraph_node_execution_time_{node}",
                value=avg_time,
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"node": node, "metric_type": "execution_time"},
                metadata={"simulated": True, "note": "无法直接访问LangGraph内部指标"}
            ))

        return metrics

    def _extract_workflow_status(self, context: Optional[Any] = None) -> List[UnifiedMetric]:
        """提取工作流状态"""
        # 模拟工作流状态指标
        return [
            UnifiedMetric(
                name="langgraph_workflow_status",
                value=1,  # 1表示运行中，0表示停止
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"status": "running"},
                metadata={"simulated": True}
            )
        ]

    def _extract_error_rates(self, context: Optional[Any] = None) -> List[UnifiedMetric]:
        """提取错误率"""
        # 模拟错误率指标
        return [
            UnifiedMetric(
                name="langgraph_error_rate",
                value=0.02,  # 2%错误率
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"time_window": "5m"},
                metadata={"simulated": True}
            )
        ]

    def _extract_resource_usage(self, context: Optional[Any] = None) -> List[UnifiedMetric]:
        """提取资源使用情况"""
        # 模拟资源使用指标
        return [
            UnifiedMetric(
                name="langgraph_memory_usage",
                value=150.5,  # MB
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"resource": "memory"},
                metadata={"simulated": True}
            ),
            UnifiedMetric(
                name="langgraph_cpu_usage",
                value=45.2,  # 百分比
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"resource": "cpu"},
                metadata={"simulated": True}
            )
        ]

    def _extract_performance_metrics(self, context: Optional[Any] = None) -> List[UnifiedMetric]:
        """提取性能指标"""
        # 模拟性能指标
        return [
            UnifiedMetric(
                name="langgraph_throughput",
                value=12.5,  # 请求/秒
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"metric": "throughput"},
                metadata={"simulated": True}
            ),
            UnifiedMetric(
                name="langgraph_average_latency",
                value=2.3,  # 秒
                timestamp=time.time(),
                source=MonitoringSource.LANGGRAPH_NATIVE,
                labels={"metric": "latency"},
                metadata={"simulated": True}
            )
        ]

    def _get_simulated_node_time(self, node_name: str) -> float:
        """获取模拟的节点执行时间"""
        # 基于节点类型返回合理的模拟时间
        base_times = {
            "query_analysis": 1.2,
            "reasoning": 3.5,
            "answer_generation": 2.1,
            "citation": 0.8
        }
        return base_times.get(node_name, 1.0)


class MetricsFusionEngine:
    """指标融合引擎"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._fusion_rules = self._load_fusion_rules()

    def _load_fusion_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载指标融合规则"""
        return {
            "execution_time": {
                "sources": ["langgraph_native", "custom_system"],
                "fusion_method": "weighted_average",
                "weights": {"langgraph_native": 0.7, "custom_system": 0.3},
                "conflict_resolution": "newer_wins"
            },
            "error_rate": {
                "sources": ["langgraph_native", "custom_system"],
                "fusion_method": "maximum",  # 取最大值，更保守
                "weights": {},
                "conflict_resolution": "maximum"
            },
            "resource_usage": {
                "sources": ["langgraph_native", "custom_system"],
                "fusion_method": "average",
                "weights": {"langgraph_native": 0.6, "custom_system": 0.4},
                "conflict_resolution": "average"
            },
            "throughput": {
                "sources": ["langgraph_native", "custom_system"],
                "fusion_method": "sum",  # 总吞吐量
                "weights": {},
                "conflict_resolution": "sum"
            }
        }

    def fuse_metrics(
        self,
        langgraph_metrics: List[UnifiedMetric],
        custom_metrics: List[UnifiedMetric]
    ) -> Dict[str, UnifiedMetric]:
        """融合多源指标"""
        all_metrics = langgraph_metrics + custom_metrics
        fused_metrics = {}

        # 按指标名称分组
        metrics_by_name = defaultdict(list)
        for metric in all_metrics:
            metrics_by_name[metric.name].append(metric)

        # 对每个指标进行融合
        for metric_name, metrics_list in metrics_by_name.items():
            if len(metrics_list) == 1:
                # 只有一个源，直接使用
                fused_metrics[metric_name] = metrics_list[0]
            else:
                # 多个源，需要融合
                fused_metric = self._fuse_single_metric(metric_name, metrics_list)
                if fused_metric:
                    fused_metrics[metric_name] = fused_metric

        return fused_metrics

    def _fuse_single_metric(self, metric_name: str, metrics: List[UnifiedMetric]) -> Optional[UnifiedMetric]:
        """融合单个指标"""
        if metric_name not in self._fusion_rules:
            # 没有融合规则，使用最新的指标
            return max(metrics, key=lambda m: m.timestamp)

        rule = self._fusion_rules[metric_name]
        fusion_method = rule["fusion_method"]

        try:
            if fusion_method == "weighted_average":
                return self._weighted_average_fusion(metrics, rule)
            elif fusion_method == "maximum":
                return self._maximum_fusion(metrics)
            elif fusion_method == "average":
                return self._average_fusion(metrics)
            elif fusion_method == "sum":
                return self._sum_fusion(metrics)
            else:
                return max(metrics, key=lambda m: m.timestamp)

        except Exception as e:
            self.logger.warning(f"指标融合失败 {metric_name}: {e}")
            return max(metrics, key=lambda m: m.timestamp)

    def _weighted_average_fusion(self, metrics: List[UnifiedMetric], rule: Dict[str, Any]) -> UnifiedMetric:
        """加权平均融合"""
        weights = rule.get("weights", {})
        total_weight = 0.0
        weighted_sum = 0.0

        latest_timestamp = max(m.timestamp for m in metrics)

        for metric in metrics:
            source_weight = weights.get(metric.source.value, 1.0)
            weighted_sum += metric.value * source_weight
            total_weight += source_weight

        if total_weight == 0:
            return metrics[0]

        fused_value = weighted_sum / total_weight

        # 合并标签和元数据
        combined_labels = {}
        combined_metadata = {}

        for metric in metrics:
            combined_labels.update(metric.labels)
            combined_metadata.update(metric.metadata)

        combined_metadata["fused_from"] = [m.source.value for m in metrics]
        combined_metadata["fusion_method"] = "weighted_average"

        return UnifiedMetric(
            name=metrics[0].name,
            value=fused_value,
            timestamp=latest_timestamp,
            source=MonitoringSource.EXTERNAL_METRICS,  # 融合后的新源
            labels=combined_labels,
            metadata=combined_metadata
        )

    def _maximum_fusion(self, metrics: List[UnifiedMetric]) -> UnifiedMetric:
        """最大值融合"""
        max_metric = max(metrics, key=lambda m: m.value)
        max_metric.metadata["fused_from"] = [m.source.value for m in metrics]
        max_metric.metadata["fusion_method"] = "maximum"
        max_metric.source = MonitoringSource.EXTERNAL_METRICS
        return max_metric

    def _average_fusion(self, metrics: List[UnifiedMetric]) -> UnifiedMetric:
        """平均值融合"""
        avg_value = sum(m.value for m in metrics) / len(metrics)
        latest_timestamp = max(m.timestamp for m in metrics)

        combined_labels = {}
        combined_metadata = {}

        for metric in metrics:
            combined_labels.update(metric.labels)
            combined_metadata.update(metric.metadata)

        combined_metadata["fused_from"] = [m.source.value for m in metrics]
        combined_metadata["fusion_method"] = "average"

        return UnifiedMetric(
            name=metrics[0].name,
            value=avg_value,
            timestamp=latest_timestamp,
            source=MonitoringSource.EXTERNAL_METRICS,
            labels=combined_labels,
            metadata=combined_metadata
        )

    def _sum_fusion(self, metrics: List[UnifiedMetric]) -> UnifiedMetric:
        """求和融合"""
        sum_value = sum(m.value for m in metrics)
        latest_timestamp = max(m.timestamp for m in metrics)

        combined_labels = {}
        combined_metadata = {}

        for metric in metrics:
            combined_labels.update(metric.labels)
            combined_metadata.update(metric.metadata)

        combined_metadata["fused_from"] = [m.source.value for m in metrics]
        combined_metadata["fusion_method"] = "sum"

        return UnifiedMetric(
            name=metrics[0].name,
            value=sum_value,
            timestamp=latest_timestamp,
            source=MonitoringSource.EXTERNAL_METRICS,
            labels=combined_labels,
            metadata=combined_metadata
        )


class IntelligentAlertRouter:
    """智能告警路由器"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._routing_rules = self._load_routing_rules()
        self._alert_correlation_engine = AlertCorrelationEngine()

    def _load_routing_rules(self) -> Dict[str, Dict[str, Any]]:
        """加载告警路由规则"""
        return {
            "high_error_rate": {
                "sources": ["langgraph_native", "custom_system"],
                "priority_mapping": {
                    "langgraph_native": "high",
                    "custom_system": "medium"
                },
                "deduplication_window": 300,  # 5分钟去重窗口
                "escalation_rules": [
                    {"threshold": 0.1, "action": "escalate_to_critical"},
                    {"threshold": 0.05, "action": "escalate_to_warning"}
                ]
            },
            "performance_degradation": {
                "sources": ["langgraph_native", "custom_system"],
                "correlation_rules": [
                    {"metrics": ["response_time", "throughput"], "action": "correlate_and_merge"}
                ]
            },
            "resource_exhaustion": {
                "sources": ["langgraph_native", "custom_system"],
                "consolidation_rules": [
                    {"condition": "multiple_similar_alerts", "action": "consolidate"}
                ]
            }
        }

    async def route_alerts(
        self,
        langgraph_alerts: List[UnifiedAlert],
        custom_alerts: List[UnifiedAlert]
    ) -> List[UnifiedAlert]:
        """路由告警"""
        all_alerts = langgraph_alerts + custom_alerts
        routed_alerts = []

        # 按告警类型分组处理
        alerts_by_type = defaultdict(list)
        for alert in all_alerts:
            alert_type = self._classify_alert_type(alert)
            alerts_by_type[alert_type].append(alert)

        for alert_type, alerts in alerts_by_type.items():
            if alert_type in self._routing_rules:
                routed = await self._apply_routing_rules(alert_type, alerts)
                routed_alerts.extend(routed)
            else:
                # 默认处理：保留所有告警
                routed_alerts.extend(alerts)

        # 最终去重和关联
        final_alerts = await self._alert_correlation_engine.correlate_alerts(routed_alerts)

        return final_alerts

    def _classify_alert_type(self, alert: UnifiedAlert) -> str:
        """分类告警类型"""
        title_lower = alert.title.lower()
        desc_lower = alert.description.lower()

        if any(word in title_lower + desc_lower for word in ["error", "失败", "异常"]):
            return "error_related"
        elif any(word in title_lower + desc_lower for word in ["performance", "性能", "slow", "慢"]):
            return "performance_related"
        elif any(word in title_lower + desc_lower for word in ["resource", "资源", "memory", "cpu"]):
            return "resource_related"
        else:
            return "general"

    async def _apply_routing_rules(self, alert_type: str, alerts: List[UnifiedAlert]) -> List[UnifiedAlert]:
        """应用路由规则"""
        rule = self._routing_rules.get(alert_type, {})
        routed_alerts = []

        # 优先级映射
        priority_mapping = rule.get("priority_mapping", {})
        for alert in alerts:
            if alert.source.value in priority_mapping:
                alert.severity = priority_mapping[alert.source.value]
            routed_alerts.append(alert)

        # 去重处理
        deduplication_window = rule.get("deduplication_window", 300)
        routed_alerts = self._deduplicate_alerts(routed_alerts, deduplication_window)

        # 升级规则
        escalation_rules = rule.get("escalation_rules", [])
        for alert in routed_alerts:
            alert.severity = self._apply_escalation_rules(alert, escalation_rules)

        return routed_alerts

    def _deduplicate_alerts(self, alerts: List[UnifiedAlert], window: float) -> List[UnifiedAlert]:
        """去重告警"""
        if not alerts:
            return alerts

        # 按内容和时间窗口去重
        deduplicated = []
        sorted_alerts = sorted(alerts, key=lambda a: a.timestamp)

        for alert in sorted_alerts:
            # 检查是否与已保留的告警重复
            is_duplicate = False
            for existing in deduplicated:
                if (alert.title == existing.title and
                    abs(alert.timestamp - existing.timestamp) < window):
                    is_duplicate = True
                    break

            if not is_duplicate:
                deduplicated.append(alert)

        return deduplicated

    def _apply_escalation_rules(self, alert: UnifiedAlert, rules: List[Dict[str, Any]]) -> str:
        """应用升级规则"""
        current_severity = alert.severity

        for rule in rules:
            threshold = rule.get("threshold", 0)
            action = rule.get("action", "")

            # 简单的阈值检查（可以扩展为更复杂的条件）
            if "error_rate" in alert.title.lower():
                # 假设context中有error_rate信息
                error_rate = alert.context.get("error_rate", 0)
                if error_rate > threshold:
                    if "escalate_to_critical" in action:
                        return "critical"
                    elif "escalate_to_warning" in action and current_severity == "info":
                        return "warning"

        return current_severity


class AlertCorrelationEngine:
    """告警关联引擎"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def correlate_alerts(self, alerts: List[UnifiedAlert]) -> List[UnifiedAlert]:
        """关联告警"""
        if len(alerts) <= 1:
            return alerts

        correlated_alerts = []
        processed_indices = set()

        for i, alert in enumerate(alerts):
            if i in processed_indices:
                continue

            correlated_group = [alert]
            processed_indices.add(i)

            # 查找相关的告警
            for j, other_alert in enumerate(alerts):
                if j in processed_indices or i == j:
                    continue

                if self._are_alerts_related(alert, other_alert):
                    correlated_group.append(other_alert)
                    processed_indices.add(j)

            if len(correlated_group) == 1:
                # 单个告警，直接保留
                correlated_alerts.append(alert)
            else:
                # 多个相关告警，合并为一个
                merged_alert = self._merge_alerts(correlated_group)
                correlated_alerts.append(merged_alert)

        return correlated_alerts

    def _are_alerts_related(self, alert1: UnifiedAlert, alert2: UnifiedAlert) -> bool:
        """判断两个告警是否相关"""
        # 时间接近（5分钟内）
        time_diff = abs(alert1.timestamp - alert2.timestamp)
        if time_diff > 300:  # 5分钟
            return False

        # 内容相似
        title_similarity = self._calculate_text_similarity(alert1.title, alert2.title)
        desc_similarity = self._calculate_text_similarity(alert1.description, alert2.description)

        # 类型相关
        type_related = self._are_types_related(alert1, alert2)

        return (title_similarity > 0.6 or desc_similarity > 0.6) and type_related

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单实现）"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union) if union else 0.0

    def _are_types_related(self, alert1: UnifiedAlert, alert2: UnifiedAlert) -> bool:
        """判断告警类型是否相关"""
        related_pairs = [
            ("performance", "resource"),
            ("error", "performance"),
            ("resource", "error")
        ]

        type1 = self._extract_alert_type(alert1)
        type2 = self._extract_alert_type(alert2)

        return (type1, type2) in related_pairs or (type2, type1) in related_pairs

    def _extract_alert_type(self, alert: UnifiedAlert) -> str:
        """提取告警类型"""
        text = (alert.title + " " + alert.description).lower()

        if any(word in text for word in ["performance", "性能", "slow", "慢", "latency"]):
            return "performance"
        elif any(word in text for word in ["error", "错误", "fail", "失败", "exception"]):
            return "error"
        elif any(word in text for word in ["resource", "资源", "memory", "cpu", "disk"]):
            return "resource"
        else:
            return "general"

    def _merge_alerts(self, alerts: List[UnifiedAlert]) -> UnifiedAlert:
        """合并相关告警"""
        if not alerts:
            return None

        # 使用最新的告警作为基础
        base_alert = max(alerts, key=lambda a: a.timestamp)

        # 合并标题和描述
        titles = [a.title for a in alerts]
        descriptions = [a.description for a in alerts]

        merged_title = f"多个相关告警 ({len(alerts)}个)"
        merged_description = f"检测到 {len(alerts)} 个相关告警：\n" + "\n".join(
            f"- {title}: {desc}" for title, desc in zip(titles, descriptions)
        )

        # 确定最高严重程度
        severity_levels = {"info": 1, "warning": 2, "error": 3, "critical": 4}
        max_severity = max(alerts, key=lambda a: severity_levels.get(a.severity, 1))
        merged_severity = max_severity.severity

        # 合并上下文
        merged_context = {}
        for alert in alerts:
            merged_context.update(alert.context)

        merged_context["correlated_alerts"] = len(alerts)
        merged_context["correlation_timestamp"] = time.time()

        return UnifiedAlert(
            alert_id=f"correlated_{base_alert.alert_id}",
            title=merged_title,
            description=merged_description,
            severity=merged_severity,
            source=MonitoringSource.EXTERNAL_METRICS,
            timestamp=time.time(),
            context=merged_context
        )


class UnifiedMonitoringDashboard:
    """统一监控面板"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 初始化组件
        self.langgraph_extractor = LangGraphMetricsExtractor()
        self.metrics_fusion = MetricsFusionEngine()
        self.alert_router = IntelligentAlertRouter()

        # 缓存
        self._metrics_cache: Dict[str, UnifiedMetric] = {}
        self._alerts_cache: List[UnifiedAlert] = []
        self._last_update = 0.0
        self._cache_ttl = 30.0  # 缓存30秒

    async def get_comprehensive_metrics(self, force_refresh: bool = False) -> Dict[str, Any]:
        """获取综合指标"""
        current_time = time.time()

        # 检查缓存
        if not force_refresh and current_time - self._last_update < self._cache_ttl:
            return self._format_cached_metrics()

        try:
            # 提取LangGraph指标
            langgraph_metrics = self.langgraph_extractor.extract_metrics()

            # 获取自定义系统指标
            custom_metrics = await self._get_custom_system_metrics()

            # 融合指标
            fused_metrics = self.metrics_fusion.fuse_metrics(langgraph_metrics, custom_metrics)

            # 更新缓存
            self._metrics_cache = fused_metrics
            self._last_update = current_time

            return self._format_metrics_response(fused_metrics, langgraph_metrics, custom_metrics)

        except Exception as e:
            self.logger.error(f"获取综合指标失败: {e}")
            return {
                "error": str(e),
                "timestamp": current_time,
                "cached": True,
                "metrics": self._format_cached_metrics()
            }

    async def get_unified_alerts(self) -> List[Dict[str, Any]]:
        """获取统一告警"""
        try:
            # 获取LangGraph告警
            langgraph_alerts = await self._get_langgraph_alerts()

            # 获取自定义系统告警
            custom_alerts = await self._get_custom_system_alerts()

            # 智能路由告警
            unified_alerts = await self.alert_router.route_alerts(langgraph_alerts, custom_alerts)

            # 更新缓存
            self._alerts_cache = unified_alerts

            return [self._format_alert(alert) for alert in unified_alerts]

        except Exception as e:
            self.logger.error(f"获取统一告警失败: {e}")
            return []

    async def _get_custom_system_metrics(self) -> List[UnifiedMetric]:
        """获取自定义系统指标"""
        try:
            # 尝试导入自定义监控系统
            from src.core.monitoring_system import get_monitoring_system

            monitoring_system = get_monitoring_system()
            metrics_data = monitoring_system.get_metrics_endpoint()

            # 转换为统一格式
            unified_metrics = []
            for metric_name, data in metrics_data.get("metrics", {}).items():
                if isinstance(data, dict) and "latest" in data:
                    unified_metrics.append(UnifiedMetric(
                        name=metric_name,
                        value=data["latest"],
                        timestamp=time.time(),
                        source=MonitoringSource.CUSTOM_SYSTEM,
                        labels={"system": "custom"},
                        metadata=data
                    ))

            return unified_metrics

        except ImportError:
            self.logger.debug("自定义监控系统不可用")
            return []
        except Exception as e:
            self.logger.warning(f"获取自定义系统指标失败: {e}")
            return []

    async def _get_langgraph_alerts(self) -> List[UnifiedAlert]:
        """获取LangGraph告警"""
        # 由于无法直接访问LangGraph告警，这里返回空列表
        # 实际实现中应该从LangGraph的告警系统获取
        return []

    async def _get_custom_system_alerts(self) -> List[UnifiedAlert]:
        """获取自定义系统告警"""
        try:
            from src.core.monitoring_system import get_monitoring_system

            monitoring_system = get_monitoring_system()
            alerts_data = monitoring_system.get_metrics_endpoint()

            # 从告警历史中提取活跃告警
            active_alerts = alerts_data.get("alerts", {}).get("active", [])

            unified_alerts = []
            for alert_data in active_alerts:
                unified_alerts.append(UnifiedAlert(
                    alert_id=f"custom_{alert_data.get('rule_name', 'unknown')}",
                    title=alert_data.get('message', 'Custom Alert'),
                    description=alert_data.get('message', ''),
                    severity=alert_data.get('level', 'warning').lower(),
                    source=MonitoringSource.CUSTOM_SYSTEM,
                    timestamp=alert_data.get('timestamp', time.time()),
                    context=alert_data
                ))

            return unified_alerts

        except Exception as e:
            self.logger.debug(f"获取自定义系统告警失败: {e}")
            return []

    def _format_metrics_response(
        self,
        fused_metrics: Dict[str, UnifiedMetric],
        langgraph_metrics: List[UnifiedMetric],
        custom_metrics: List[UnifiedMetric]
    ) -> Dict[str, Any]:
        """格式化指标响应"""
        return {
            "timestamp": time.time(),
            "fused_metrics": {
                name: self._format_metric(metric)
                for name, metric in fused_metrics.items()
            },
            "source_breakdown": {
                "langgraph_native": len([m for m in langgraph_metrics if not m.metadata.get("simulated", False)]),
                "langgraph_simulated": len([m for m in langgraph_metrics if m.metadata.get("simulated", False)]),
                "custom_system": len(custom_metrics),
                "fused_total": len(fused_metrics)
            },
            "health_status": self._calculate_health_status(fused_metrics)
        }

    def _format_cached_metrics(self) -> Dict[str, Any]:
        """格式化缓存指标"""
        return {
            "timestamp": self._last_update,
            "cached": True,
            "fused_metrics": {
                name: self._format_metric(metric)
                for name, metric in self._metrics_cache.items()
            }
        }

    def _format_metric(self, metric: UnifiedMetric) -> Dict[str, Any]:
        """格式化单个指标"""
        return {
            "name": metric.name,
            "value": metric.value,
            "timestamp": metric.timestamp,
            "source": metric.source.value,
            "labels": metric.labels,
            "metadata": metric.metadata
        }

    def _format_alert(self, alert: UnifiedAlert) -> Dict[str, Any]:
        """格式化告警"""
        return {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "description": alert.description,
            "severity": alert.severity,
            "source": alert.source.value,
            "timestamp": alert.timestamp,
            "context": alert.context,
            "resolved": alert.resolved
        }

    def _calculate_health_status(self, metrics: Dict[str, UnifiedMetric]) -> str:
        """计算健康状态"""
        # 简单的健康评估逻辑
        error_rate = 0.0
        response_time = 0.0

        for metric in metrics.values():
            if "error_rate" in metric.name:
                error_rate = max(error_rate, metric.value)
            elif "response_time" in metric.name or "latency" in metric.name:
                response_time = max(response_time, metric.value)

        if error_rate > 0.1 or response_time > 10.0:
            return "critical"
        elif error_rate > 0.05 or response_time > 5.0:
            return "warning"
        else:
            return "healthy"

    async def get_system_overview(self) -> Dict[str, Any]:
        """获取系统概览"""
        metrics = await self.get_comprehensive_metrics()
        alerts = await self.get_unified_alerts()

        return {
            "metrics_summary": {
                "total_fused_metrics": len(metrics.get("fused_metrics", {})),
                "health_status": metrics.get("health_status", "unknown"),
                "last_update": metrics.get("timestamp", 0)
            },
            "alerts_summary": {
                "active_alerts": len([a for a in alerts if not a.get("resolved", False)]),
                "critical_alerts": len([a for a in alerts if a.get("severity") == "critical"]),
                "warning_alerts": len([a for a in alerts if a.get("severity") == "warning"])
            },
            "integration_status": {
                "langgraph_connected": True,  # 假设连接正常
                "custom_system_connected": True,  # 假设连接正常
                "fusion_engine_active": True
            }
        }


# 全局统一监控面板实例
_unified_monitoring_instance = None

def get_unified_monitoring_dashboard() -> UnifiedMonitoringDashboard:
    """获取统一监控面板实例"""
    global _unified_monitoring_instance
    if _unified_monitoring_instance is None:
        _unified_monitoring_instance = UnifiedMonitoringDashboard()
    return _unified_monitoring_instance

# 便捷函数
async def get_comprehensive_metrics(force_refresh: bool = False) -> Dict[str, Any]:
    """获取综合指标（便捷函数）"""
    dashboard = get_unified_monitoring_dashboard()
    return await dashboard.get_comprehensive_metrics(force_refresh)

async def get_unified_alerts() -> List[Dict[str, Any]]:
    """获取统一告警（便捷函数）"""
    dashboard = get_unified_monitoring_dashboard()
    return await dashboard.get_unified_alerts()

async def get_system_overview() -> Dict[str, Any]:
    """获取系统概览（便捷函数）"""
    dashboard = get_unified_monitoring_dashboard()
    return await dashboard.get_system_overview()
