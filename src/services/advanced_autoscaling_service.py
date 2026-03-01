#!/usr/bin/env python3
"""
高级自动扩缩容服务
提供智能扩缩容规则，包括组合规则、趋势分析、预测性扩缩容和自适应阈值
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import numpy as np
from collections import deque

# 导入基础扩缩容服务
from .autoscaling_service import (
    AutoscalingService, 
    ScalingDecision, 
    ScalingTarget, 
    SystemMetric,
    ScalingRule,
    ScalingHistoryEntry
)

logger = logging.getLogger(__name__)


class RuleConditionType(Enum):
    """规则条件类型"""
    SINGLE_METRIC = "single_metric"          # 单一指标
    MULTI_METRIC = "multi_metric"            # 多个指标组合
    TREND_BASED = "trend_based"              # 趋势分析
    PREDICTIVE = "predictive"                # 预测性
    ADAPTIVE = "adaptive"                    # 自适应阈值


class MetricTrend(Enum):
    """指标趋势"""
    INCREASING = "increasing"        # 上升趋势
    DECREASING = "decreasing"        # 下降趋势
    STABLE = "stable"                # 稳定趋势
    VOLATILE = "volatile"            # 波动趋势


@dataclass
class AdvancedScalingRule(ScalingRule):
    """高级扩缩容规则"""
    condition_type: RuleConditionType = RuleConditionType.SINGLE_METRIC
    required_metrics: List[str] = field(default_factory=list)  # 所需指标列表
    trend_window: int = 10           # 趋势分析窗口大小
    prediction_horizon: int = 5      # 预测时域（分钟）
    adaptive_threshold: bool = False  # 是否使用自适应阈值
    min_threshold: float = 0.0       # 最小阈值
    max_threshold: float = 100.0     # 最大阈值
    learning_rate: float = 0.1       # 自适应学习率
    weight: float = 1.0              # 规则权重
    enabled: bool = True             # 规则是否启用


@dataclass
class MetricTrendAnalysis:
    """指标趋势分析"""
    metric_name: str
    current_value: float
    trend: MetricTrend
    slope: float                     # 趋势斜率
    volatility: float               # 波动性
    forecast: List[float]           # 预测值
    confidence: float               # 预测置信度


@dataclass
class CompoundCondition:
    """复合条件"""
    conditions: List[Dict[str, Any]]  # 条件列表
    operator: str = "AND"           # 条件运算符: AND, OR
    min_satisfied: int = 1          # 最少满足条件数


class AdvancedAutoscalingService(AutoscalingService):
    """高级自动扩缩容服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化高级自动扩缩容服务"""
        super().__init__(config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 指标历史数据
        self.metric_history: Dict[str, deque] = {}
        self.max_history_size = config.get("metric_history_size", 100)
        
        # 趋势分析缓存
        self.trend_cache: Dict[str, MetricTrendAnalysis] = {}
        self.trend_cache_ttl = config.get("trend_cache_ttl", 300)  # 5分钟
        
        # 预测模型
        self.prediction_models: Dict[str, Any] = {}
        
        # 高级规则
        self.advanced_rules: List[AdvancedScalingRule] = self._create_advanced_rules()
        
        # 自适应阈值跟踪
        self.adaptive_thresholds: Dict[str, float] = {}
        
        # 性能统计
        self.performance_stats = {
            "rule_evaluations": 0,
            "predictions_made": 0,
            "trend_analyses": 0,
            "adaptive_adjustments": 0
        }
    
    def _create_advanced_rules(self) -> List[AdvancedScalingRule]:
        """创建高级扩缩容规则"""
        return [
            # 1. 组合规则：CPU和内存同时高负载
            AdvancedScalingRule(
                name="high_cpu_and_memory_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="composite_cpu_memory",
                operator=">",
                threshold=70.0,
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=180,
                min_instances=1,
                max_instances=25,
                adjustment_step=2,
                description="CPU和内存组合负载超过70%时扩容",
                condition_type=RuleConditionType.MULTI_METRIC,
                required_metrics=["cpu_percent", "memory_percent"],
                weight=1.5  # 更高权重
            ),
            
            # 2. 趋势规则：延迟持续上升
            AdvancedScalingRule(
                name="increasing_latency_trend_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="request_latency_p95",
                operator=">",
                threshold=300.0,
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=120,
                min_instances=1,
                max_instances=30,
                adjustment_step=1,
                description="延迟持续上升趋势且超过300ms时扩容",
                condition_type=RuleConditionType.TREND_BASED,
                trend_window=15,
                weight=1.3
            ),
            
            # 3. 预测性规则：基于请求率预测
            AdvancedScalingRule(
                name="predictive_request_rate_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="request_rate_forecast",
                operator=">",
                threshold=120.0,
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=60,
                min_instances=1,
                max_instances=40,
                adjustment_step=3,  # 预测性扩容可以更激进
                description="预测请求率将超过120 RPS时提前扩容",
                condition_type=RuleConditionType.PREDICTIVE,
                prediction_horizon=10,  # 预测未来10分钟
                weight=1.2
            ),
            
            # 4. 自适应规则：根据历史性能自动调整阈值
            AdvancedScalingRule(
                name="adaptive_cpu_threshold_scale_out",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="cpu_percent",
                operator=">",
                threshold=75.0,  # 初始阈值，会自适应调整
                action=ScalingDecision.SCALE_OUT,
                cooldown_seconds=240,
                min_instances=1,
                max_instances=20,
                adjustment_step=1,
                description="自适应CPU阈值扩容",
                condition_type=RuleConditionType.ADAPTIVE,
                adaptive_threshold=True,
                min_threshold=50.0,
                max_threshold=90.0,
                learning_rate=0.05,
                weight=1.0
            ),
            
            # 5. 组合规则：低负载时缩容
            AdvancedScalingRule(
                name="low_composite_load_scale_in",
                target=ScalingTarget.AGENT_INSTANCES,
                metric_name="composite_load",
                operator="<",
                threshold=15.0,
                action=ScalingDecision.SCALE_IN,
                cooldown_seconds=600,
                min_instances=1,
                max_instances=20,
                adjustment_step=1,
                description="组合负载低于15%时缩容",
                condition_type=RuleConditionType.MULTI_METRIC,
                required_metrics=["cpu_percent", "memory_percent", "request_rate"],
                weight=1.0
            ),
        ]
    
    def _update_metric_history(self, metrics: List[SystemMetric]) -> None:
        """更新指标历史数据"""
        timestamp = datetime.now()
        
        for metric in metrics:
            if metric.name not in self.metric_history:
                self.metric_history[metric.name] = deque(maxlen=self.max_history_size)
            
            self.metric_history[metric.name].append({
                "timestamp": timestamp,
                "value": metric.value,
                "unit": metric.unit,
                "source": metric.source
            })
    
    async def _analyze_metric_trend(self, metric_name: str) -> Optional[MetricTrendAnalysis]:
        """分析指标趋势"""
        if metric_name not in self.metric_history:
            return None
        
        history = list(self.metric_history[metric_name])
        if len(history) < 5:
            return None
        
        # 提取时间序列数据
        values = [point["value"] for point in history]
        timestamps = [point["timestamp"] for point in history]
        
        # 计算趋势斜率（线性回归）
        time_indices = np.arange(len(values))
        if len(values) < 2:
            return None
        
        slope, intercept = np.polyfit(time_indices, values, 1)
        
        # 确定趋势类型
        if slope > 0.1:
            trend = MetricTrend.INCREASING
        elif slope < -0.1:
            trend = MetricTrend.DECREASING
        else:
            trend = MetricTrend.STABLE
        
        # 计算波动性（标准差）
        volatility = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 简单预测（使用线性外推）
        forecast_horizon = 5
        forecast = [slope * (len(values) + i) + intercept for i in range(1, forecast_horizon + 1)]
        
        # 计算预测置信度（基于R²）
        y_pred = [slope * i + intercept for i in time_indices]
        ss_res = sum((values[i] - y_pred[i]) ** 2 for i in range(len(values)))
        ss_tot = sum((values[i] - np.mean(values)) ** 2 for i in range(len(values)))
        confidence = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        analysis = MetricTrendAnalysis(
            metric_name=metric_name,
            current_value=values[-1],
            trend=trend,
            slope=slope,
            volatility=volatility,
            forecast=forecast,
            confidence=max(0.0, min(1.0, confidence))  # 限制在0-1之间
        )
        
        self.trend_cache[metric_name] = analysis
        self.performance_stats["trend_analyses"] += 1
        
        return analysis
    
    async def _predict_metric(self, metric_name: str, horizon: int = 5) -> Optional[List[float]]:
        """预测指标未来值"""
        if metric_name not in self.metric_history:
            return None
        
        history = list(self.metric_history[metric_name])
        if len(history) < 10:
            return None
        
        values = [point["value"] for point in history]
        
        try:
            # 使用简单指数平滑进行预测
            alpha = 0.3
            forecasts = []
            last_smooth = values[0]
            
            for value in values[1:]:
                last_smooth = alpha * value + (1 - alpha) * last_smooth
            
            # 生成预测
            for _ in range(horizon):
                forecasts.append(last_smooth)
            
            self.performance_stats["predictions_made"] += 1
            return forecasts
            
        except Exception as e:
            self.logger.warning(f"指标预测失败 {metric_name}: {e}")
            return None
    
    def _calculate_composite_metric(self, metric_names: List[str], weights: Optional[List[float]] = None) -> float:
        """计算组合指标值"""
        if not metric_names:
            return 0.0
        
        if weights is None:
            weights = [1.0 / len(metric_names)] * len(metric_names)
        
        current_values = []
        for metric_name in metric_names:
            if metric_name in self.metric_history and self.metric_history[metric_name]:
                current_values.append(self.metric_history[metric_name][-1]["value"])
            else:
                current_values.append(0.0)
        
        # 加权平均
        composite_value = sum(w * v for w, v in zip(weights, current_values))
        return composite_value
    
    def _adjust_adaptive_threshold(self, rule: AdvancedScalingRule, 
                                  actual_value: float, 
                                  decision_made: bool) -> float:
        """调整自适应阈值"""
        if not rule.adaptive_threshold:
            return rule.threshold
        
        threshold_key = f"{rule.name}_threshold"
        
        if threshold_key not in self.adaptive_thresholds:
            self.adaptive_thresholds[threshold_key] = rule.threshold
        
        current_threshold = self.adaptive_thresholds[threshold_key]
        
        # 根据决策效果调整阈值
        if decision_made:
            # 如果做出了决策，检查是否过于敏感或保守
            if actual_value > current_threshold * 1.2:
                # 阈值可能过低，过于敏感
                adjustment = rule.learning_rate * (actual_value - current_threshold)
                new_threshold = min(rule.max_threshold, current_threshold + adjustment)
            else:
                # 决策合理，微调
                adjustment = rule.learning_rate * 0.1 * (actual_value - current_threshold)
                new_threshold = max(rule.min_threshold, min(rule.max_threshold, 
                                                          current_threshold + adjustment))
        else:
            # 没有决策，检查是否错过了应该决策的情况
            if actual_value > current_threshold * 0.9:
                # 接近阈值，可能需要降低阈值
                adjustment = -rule.learning_rate * 0.05 * current_threshold
                new_threshold = max(rule.min_threshold, current_threshold + adjustment)
            else:
                # 远离阈值，保持稳定
                new_threshold = current_threshold
        
        self.adaptive_thresholds[threshold_key] = new_threshold
        self.performance_stats["adaptive_adjustments"] += 1
        
        self.logger.info(f"自适应阈值调整: {rule.name} {current_threshold:.2f} -> {new_threshold:.2f}")
        return new_threshold
    
    async def _evaluate_advanced_rule(self, rule: AdvancedScalingRule, 
                                     metrics: List[SystemMetric]) -> Tuple[bool, str, float]:
        """评估高级规则"""
        self.performance_stats["rule_evaluations"] += 1
        
        # 更新指标历史
        self._update_metric_history(metrics)
        
        # 检查冷却期
        if self._is_in_cooldown(rule.name):
            return False, "冷却期", 0.0
        
        actual_value = 0.0
        reason = ""
        
        try:
            if rule.condition_type == RuleConditionType.SINGLE_METRIC:
                # 单一指标规则
                metric_value = self._get_metric_value(rule.metric_name, metrics)
                if metric_value is None:
                    return False, f"指标 {rule.metric_name} 不可用", 0.0
                
                actual_value = metric_value
                threshold = rule.threshold
                
                if rule.adaptive_threshold:
                    threshold = self._adjust_adaptive_threshold(rule, metric_value, False)
                
                triggered = self._evaluate_condition(metric_value, rule.operator, threshold)
                reason = f"{rule.metric_name}={metric_value:.2f} {rule.operator} {threshold:.2f}"
            
            elif rule.condition_type == RuleConditionType.MULTI_METRIC:
                # 多指标组合规则
                if not rule.required_metrics:
                    return False, "缺少所需指标", 0.0
                
                composite_value = self._calculate_composite_metric(rule.required_metrics)
                actual_value = composite_value
                threshold = rule.threshold
                
                triggered = self._evaluate_condition(composite_value, rule.operator, threshold)
                reason = f"组合指标={composite_value:.2f} {rule.operator} {threshold:.2f}"
            
            elif rule.condition_type == RuleConditionType.TREND_BASED:
                # 趋势分析规则
                metric_value = self._get_metric_value(rule.metric_name, metrics)
                if metric_value is None:
                    return False, f"指标 {rule.metric_name} 不可用", 0.0
                
                # 分析趋势
                trend_analysis = await self._analyze_metric_trend(rule.metric_name)
                if not trend_analysis:
                    return False, f"趋势分析不可用: {rule.metric_name}", 0.0
                
                # 检查趋势条件
                trend_condition_met = False
                if rule.operator == ">":
                    trend_condition_met = (trend_analysis.trend == MetricTrend.INCREASING and 
                                          trend_analysis.slope > 0.05)
                elif rule.operator == "<":
                    trend_condition_met = (trend_analysis.trend == MetricTrend.DECREASING and 
                                          trend_analysis.slope < -0.05)
                
                # 检查阈值条件
                threshold_condition_met = self._evaluate_condition(metric_value, rule.operator, rule.threshold)
                
                actual_value = metric_value
                triggered = trend_condition_met and threshold_condition_met
                reason = (f"趋势={trend_analysis.trend.value} "
                         f"(斜率={trend_analysis.slope:.3f}), "
                         f"值={metric_value:.2f} {rule.operator} {rule.threshold:.2f}")
            
            elif rule.condition_type == RuleConditionType.PREDICTIVE:
                # 预测性规则
                predictions = await self._predict_metric(rule.metric_name, rule.prediction_horizon)
                if not predictions:
                    return False, f"预测不可用: {rule.metric_name}", 0.0
                
                # 使用预测值的最大值
                predicted_value = max(predictions) if predictions else 0.0
                actual_value = predicted_value
                threshold = rule.threshold
                
                triggered = self._evaluate_condition(predicted_value, rule.operator, threshold)
                reason = f"预测值={predicted_value:.2f} {rule.operator} {threshold:.2f}"
            
            elif rule.condition_type == RuleConditionType.ADAPTIVE:
                # 自适应规则
                metric_value = self._get_metric_value(rule.metric_name, metrics)
                if metric_value is None:
                    return False, f"指标 {rule.metric_name} 不可用", 0.0
                
                actual_value = metric_value
                current_threshold = self._adjust_adaptive_threshold(rule, metric_value, False)
                
                triggered = self._evaluate_condition(metric_value, rule.operator, current_threshold)
                reason = f"{rule.metric_name}={metric_value:.2f} {rule.operator} {current_threshold:.2f} (自适应)"
            
            else:
                return False, f"未知规则类型: {rule.condition_type}", 0.0
            
            return triggered, reason, actual_value
            
        except Exception as e:
            self.logger.error(f"高级规则评估错误 {rule.name}: {e}")
            return False, f"评估错误: {str(e)}", 0.0
    
    def _get_metric_value(self, metric_name: str, metrics: List[SystemMetric]) -> Optional[float]:
        """获取指标值"""
        for metric in metrics:
            if metric.name == metric_name:
                return metric.value
        return None
    
    def _evaluate_condition(self, value: float, operator: str, threshold: float) -> bool:
        """评估条件"""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return abs(value - threshold) < 0.001
        else:
            return False
    
    async def _evaluate_scaling_rules(self, metrics: List[SystemMetric]) -> List[Dict[str, Any]]:
        """评估扩缩容规则（重写父类方法以包含高级规则）"""
        decisions = []
        
        # 首先评估基础规则
        base_decisions = await super()._evaluate_scaling_rules(metrics)
        decisions.extend(base_decisions)
        
        # 评估高级规则
        for rule in self.advanced_rules:
            if not rule.enabled:
                continue
            
            triggered, reason, actual_value = await self._evaluate_advanced_rule(rule, metrics)
            
            if triggered:
                decision = {
                    "rule_name": rule.name,
                    "decision": rule.action,
                    "target": rule.target,
                    "reason": reason,
                    "current_value": actual_value,
                    "threshold": rule.threshold,
                    "adjustment_step": rule.adjustment_step,
                    "weight": rule.weight,
                    "rule_type": "advanced"
                }
                decisions.append(decision)
                
                self.logger.info(f"高级规则触发: {rule.name} - {reason}")
        
        # 按权重排序决策（权重高的优先）
        decisions.sort(key=lambda x: x.get("weight", 1.0), reverse=True)
        
        return decisions
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            "performance_stats": self.performance_stats,
            "metric_history_sizes": {k: len(v) for k, v in self.metric_history.items()},
            "trend_cache_size": len(self.trend_cache),
            "adaptive_thresholds": self.adaptive_thresholds,
            "advanced_rules_enabled": sum(1 for r in self.advanced_rules if r.enabled),
            "total_advanced_rules": len(self.advanced_rules)
        }
    
    async def enable_advanced_rule(self, rule_name: str, enabled: bool = True) -> bool:
        """启用或禁用高级规则"""
        for rule in self.advanced_rules:
            if rule.name == rule_name:
                rule.enabled = enabled
                self.logger.info(f"高级规则 {rule_name} {'启用' if enabled else '禁用'}")
                return True
        return False
    
    async def update_advanced_rule(self, rule_name: str, updates: Dict[str, Any]) -> bool:
        """更新高级规则"""
        for rule in self.advanced_rules:
            if rule.name == rule_name:
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                
                self.logger.info(f"高级规则 {rule_name} 已更新: {updates}")
                return True
        return False


# 创建服务的工厂函数
def create_advanced_autoscaling_service(config: Optional[Dict[str, Any]] = None) -> AdvancedAutoscalingService:
    """创建高级自动扩缩容服务实例"""
    return AdvancedAutoscalingService(config)