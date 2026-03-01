#!/usr/bin/env python3
"""
智能替换率优化器
基于性能指标和系统负载智能调整Agent替换率
"""

import asyncio
import time
import logging
import json
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """优化策略"""
    CONSERVATIVE = "conservative"      # 保守策略 - 缓慢增加替换率
    BALANCED = "balanced"             # 平衡策略 - 适度调整
    AGGRESSIVE = "aggressive"         # 激进策略 - 快速增加替换率
    PERFORMANCE_BASED = "performance_based"  # 基于性能的策略


class AdjustmentDirection(Enum):
    """调整方向"""
    INCREASE = "increase"     # 增加替换率
    DECREASE = "decrease"     # 减少替换率
    HOLD = "hold"            # 保持不变


@dataclass
class ReplacementOptimizationResult:
    """替换率优化结果"""
    agent_name: str
    current_rate: float
    recommended_rate: float
    adjustment_direction: AdjustmentDirection
    confidence_score: float
    reasoning: List[str]
    expected_impact: Dict[str, Any]
    timestamp: datetime


@dataclass
class OptimizationMetrics:
    """优化指标"""
    agent_name: str
    time_window: timedelta

    # 性能指标
    avg_response_time: float
    response_time_trend: str  # 'improving', 'stable', 'degrading'
    success_rate: float
    error_rate_trend: str

    # 系统指标
    cpu_usage: float
    memory_usage: float
    resource_pressure: str  # 'low', 'medium', 'high'

    # 业务指标
    throughput: float
    user_satisfaction_estimate: float  # 基于成功率和响应时间估算

    # 稳定性指标
    performance_variance: float
    error_stability: str  # 'stable', 'fluctuating', 'increasing'


class IntelligentReplacementOptimizer:
    """智能替换率优化器"""

    def __init__(self, strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
        """
        初始化优化器

        Args:
            strategy: 优化策略
        """
        self.strategy = strategy
        self.optimization_history: Dict[str, List[ReplacementOptimizationResult]] = {}
        self.current_adjustments: Dict[str, float] = {}

        # 配置参数
        self.config = self._load_config()

        # 数据存储
        self.data_dir = Path("data/replacement_optimization")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"智能替换率优化器初始化完成，策略: {strategy.value}")

    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        return {
            'conservative': {
                'max_adjustment_per_step': 0.02,  # 每次最多调整2%
                'min_confidence_threshold': 0.8,   # 最小置信度
                'monitoring_window_hours': 24,    # 监控窗口
                'stability_required_hours': 6      # 需要稳定观察时间
            },
            'balanced': {
                'max_adjustment_per_step': 0.05,  # 每次最多调整5%
                'min_confidence_threshold': 0.7,
                'monitoring_window_hours': 12,
                'stability_required_hours': 3
            },
            'aggressive': {
                'max_adjustment_per_step': 0.10,  # 每次最多调整10%
                'min_confidence_threshold': 0.6,
                'monitoring_window_hours': 6,
                'stability_required_hours': 1
            },
            'performance_based': {
                'max_adjustment_per_step': 0.08,
                'min_confidence_threshold': 0.75,
                'monitoring_window_hours': 8,
                'stability_required_hours': 2
            }
        }.get(self.strategy.value, {})

    async def optimize_replacement_rate(self, agent_name: str,
                                      current_metrics: Dict[str, Any]) -> ReplacementOptimizationResult:
        """
        优化单个Agent的替换率

        Args:
            agent_name: Agent名称
            current_metrics: 当前性能指标

        Returns:
            优化结果
        """
        try:
            # 收集历史数据
            historical_data = await self._collect_historical_data(agent_name)

            # 计算优化指标
            optimization_metrics = self._calculate_optimization_metrics(
                agent_name, current_metrics, historical_data
            )

            # 分析当前状态
            current_rate = current_metrics.get('replacement_rate', 0.01)

            # 生成优化建议
            recommended_rate, direction, confidence, reasoning = await self._generate_optimization_recommendation(
                agent_name, current_rate, optimization_metrics, historical_data
            )

            # 预测影响
            expected_impact = self._predict_impact(
                agent_name, current_rate, recommended_rate, optimization_metrics
            )

            result = ReplacementOptimizationResult(
                agent_name=agent_name,
                current_rate=current_rate,
                recommended_rate=recommended_rate,
                adjustment_direction=direction,
                confidence_score=confidence,
                reasoning=reasoning,
                expected_impact=expected_impact,
                timestamp=datetime.now()
            )

            # 保存优化历史
            if agent_name not in self.optimization_history:
                self.optimization_history[agent_name] = []
            self.optimization_history[agent_name].append(result)

            # 保存到文件
            self._save_optimization_result(result)

            logger.info(f"✅ {agent_name}替换率优化完成: {result.current_rate:.1%} → {result.recommended_rate:.1%}")
            return result

        except Exception as e:
            logger.error(f"优化{agent_name}替换率异常: {e}", exc_info=True)
            # 返回保守的建议
            return ReplacementOptimizationResult(
                agent_name=agent_name,
                current_rate=current_metrics.get('replacement_rate', 0.01),
                recommended_rate=current_metrics.get('replacement_rate', 0.01),
                adjustment_direction=AdjustmentDirection.HOLD,
                confidence_score=0.5,
                reasoning=["优化过程出现异常，建议保持当前替换率"],
                expected_impact={"risk": "unknown", "benefit": "maintain_stability"},
                timestamp=datetime.now()
            )

    async def _collect_historical_data(self, agent_name: str) -> List[Dict[str, Any]]:
        """收集历史数据"""
        # 这里应该从监控系统中获取历史数据
        # 现在返回模拟数据
        return [
            {'timestamp': datetime.now() - timedelta(hours=i),
             'replacement_rate': 0.01 + (i * 0.005),
             'avg_response_time': 2.5 - (i * 0.1),
             'success_rate': 0.90 + (i * 0.005),
             'error_rate': 0.10 - (i * 0.005)}
            for i in range(10)
        ]

    def _calculate_optimization_metrics(self, agent_name: str,
                                      current_metrics: Dict[str, Any],
                                      historical_data: List[Dict[str, Any]]) -> OptimizationMetrics:
        """计算优化指标"""
        try:
            # 计算响应时间趋势
            response_times = [d.get('avg_response_time', 2.5) for d in historical_data[-5:]]
            if len(response_times) >= 2:
                trend_slope = statistics.linear_regression(range(len(response_times)), response_times)[0]
                response_time_trend = 'improving' if trend_slope < -0.01 else 'degrading' if trend_slope > 0.01 else 'stable'
            else:
                response_time_trend = 'stable'

            # 计算错误率趋势
            error_rates = [d.get('error_rate', 0.05) for d in historical_data[-5:]]
            if len(error_rates) >= 2:
                error_trend_slope = statistics.linear_regression(range(len(error_rates)), error_rates)[0]
                error_rate_trend = 'improving' if error_trend_slope < -0.001 else 'increasing' if error_trend_slope > 0.001 else 'stable'
            else:
                error_rate_trend = 'stable'

            # 计算性能方差
            performance_variance = statistics.variance(response_times) if len(response_times) > 1 else 0

            # 确定资源压力
            cpu_usage = current_metrics.get('cpu_usage', 50)
            memory_usage = current_metrics.get('memory_usage', 60)
            avg_resource_usage = (cpu_usage + memory_usage) / 2

            if avg_resource_usage < 60:
                resource_pressure = 'low'
            elif avg_resource_usage < 80:
                resource_pressure = 'medium'
            else:
                resource_pressure = 'high'

            # 计算吞吐量（模拟）
            throughput = 1000 / current_metrics.get('avg_response_time', 2.5)  # 请求/分钟

            # 估算用户满意度
            response_time_score = max(0, 1 - (current_metrics.get('avg_response_time', 2.5) - 1.5) / 2)  # 1.5s为基准
            success_rate_score = current_metrics.get('success_rate', 0.95)
            user_satisfaction_estimate = (response_time_score + success_rate_score) / 2

            return OptimizationMetrics(
                agent_name=agent_name,
                time_window=timedelta(hours=1),
                avg_response_time=current_metrics.get('avg_response_time', 2.5),
                response_time_trend=response_time_trend,
                success_rate=current_metrics.get('success_rate', 0.95),
                error_rate_trend=error_rate_trend,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                resource_pressure=resource_pressure,
                throughput=throughput,
                user_satisfaction_estimate=user_satisfaction_estimate,
                performance_variance=performance_variance,
                error_stability='stable' if error_rate_trend == 'stable' else 'fluctuating'
            )

        except Exception as e:
            logger.error(f"计算优化指标异常: {e}")
            # 返回默认指标
            return OptimizationMetrics(
                agent_name=agent_name,
                time_window=timedelta(hours=1),
                avg_response_time=2.5,
                response_time_trend='stable',
                success_rate=0.95,
                error_rate_trend='stable',
                cpu_usage=50,
                memory_usage=60,
                resource_pressure='medium',
                throughput=400,
                user_satisfaction_estimate=0.8,
                performance_variance=0.1,
                error_stability='stable'
            )

    async def _generate_optimization_recommendation(self, agent_name: str,
                                                   current_rate: float,
                                                   metrics: OptimizationMetrics,
                                                   historical_data: List[Dict[str, Any]]) -> Tuple[float, AdjustmentDirection, float, List[str]]:
        """生成优化建议"""
        reasoning = []
        confidence = 0.8

        # 基于策略的参数
        max_adjustment = self.config.get('max_adjustment_per_step', 0.05)
        min_confidence = self.config.get('min_confidence_threshold', 0.7)

        # 分析当前性能
        performance_score = self._calculate_performance_score(metrics)
        stability_score = self._calculate_stability_score(metrics, historical_data)

        # 决策逻辑
        if performance_score >= 0.8 and stability_score >= 0.8:
            # 性能和稳定性都很好，可以增加替换率
            if current_rate < 0.5:  # 如果替换率不高
                adjustment = min(max_adjustment, 0.1 - current_rate)  # 向10%靠拢
                recommended_rate = min(1.0, current_rate + adjustment)
                direction = AdjustmentDirection.INCREASE
                reasoning.append("性能和稳定性表现优秀，建议增加替换率")
                confidence = 0.9
            else:
                recommended_rate = current_rate
                direction = AdjustmentDirection.HOLD
                reasoning.append("替换率已较高，建议保持当前水平")
                confidence = 0.7

        elif performance_score >= 0.6 and stability_score >= 0.6:
            # 性能和稳定性中等，可以小幅调整
            if metrics.response_time_trend == 'improving':
                adjustment = max_adjustment * 0.5
                recommended_rate = min(1.0, current_rate + adjustment)
                direction = AdjustmentDirection.INCREASE
                reasoning.append("性能呈改善趋势，可以适度增加替换率")
            elif metrics.response_time_trend == 'degrading':
                adjustment = max_adjustment * 0.3
                recommended_rate = max(0.01, current_rate - adjustment)
                direction = AdjustmentDirection.DECREASE
                reasoning.append("性能呈下降趋势，建议减少替换率")
            else:
                recommended_rate = current_rate
                direction = AdjustmentDirection.HOLD
                reasoning.append("性能稳定，建议保持当前替换率")

        else:
            # 性能或稳定性较差，应该减少替换率或保持谨慎
            if current_rate > 0.05:
                adjustment = max_adjustment * 0.5
                recommended_rate = max(0.01, current_rate - adjustment)
                direction = AdjustmentDirection.DECREASE
                reasoning.append("性能或稳定性不佳，建议减少替换率以确保系统稳定")
                confidence = 0.6
            else:
                recommended_rate = current_rate
                direction = AdjustmentDirection.HOLD
                reasoning.append("替换率已很低，建议保持并观察性能改善")

        # 考虑资源压力
        if metrics.resource_pressure == 'high':
            if direction == AdjustmentDirection.INCREASE:
                recommended_rate = current_rate  # 取消增加
                direction = AdjustmentDirection.HOLD
                reasoning.append("系统资源压力较大，暂不增加替换率")
                confidence *= 0.9

        # 应用策略特定的调整
        if self.strategy == OptimizationStrategy.CONSERVATIVE:
            if direction == AdjustmentDirection.INCREASE:
                recommended_rate = current_rate + (recommended_rate - current_rate) * 0.5
            reasoning.append("采用保守策略，调整幅度较小")

        # 确保置信度不低于阈值
        confidence = max(confidence, min_confidence)

        return recommended_rate, direction, confidence, reasoning

    def _calculate_performance_score(self, metrics: OptimizationMetrics) -> float:
        """计算性能评分"""
        # 基于多个指标计算综合性能评分
        response_time_score = max(0, 1 - (metrics.avg_response_time - 1.5) / 2)  # 1.5s为基准
        success_rate_score = metrics.success_rate
        throughput_score = min(1.0, metrics.throughput / 1000)  # 1000为基准

        # 加权平均
        weights = [0.4, 0.4, 0.2]
        scores = [response_time_score, success_rate_score, throughput_score]

        return sum(w * s for w, s in zip(weights, scores))

    def _calculate_stability_score(self, metrics: OptimizationMetrics,
                                 historical_data: List[Dict[str, Any]]) -> float:
        """计算稳定性评分"""
        # 基于方差和趋势计算稳定性
        variance_score = max(0, 1 - metrics.performance_variance * 10)  # 方差评分

        # 趋势稳定性
        trend_stability = 1.0
        if metrics.response_time_trend == 'degrading':
            trend_stability *= 0.7
        if metrics.error_rate_trend == 'increasing':
            trend_stability *= 0.8

        # 资源稳定性
        resource_stability = 1.0
        if metrics.resource_pressure == 'high':
            resource_stability *= 0.9

        return (variance_score + trend_stability + resource_stability) / 3

    def _predict_impact(self, agent_name: str, current_rate: float,
                       recommended_rate: float, metrics: OptimizationMetrics) -> Dict[str, Any]:
        """预测调整的影响"""
        rate_change = recommended_rate - current_rate

        # 估算性能影响
        expected_response_time_change = rate_change * 0.5  # 每1%替换率变化约影响0.5秒响应时间
        expected_success_rate_change = rate_change * 0.02  # 每1%替换率变化约影响2%成功率

        # 风险评估
        if abs(rate_change) > 0.1:
            risk_level = 'high'
        elif abs(rate_change) > 0.05:
            risk_level = 'medium'
        else:
            risk_level = 'low'

        # 预期收益
        if rate_change > 0:
            benefit = 'potential_performance_improvement'
        elif rate_change < 0:
            benefit = 'stability_improvement'
        else:
            benefit = 'maintain_stability'

        return {
            'response_time_change_seconds': expected_response_time_change,
            'success_rate_change_percent': expected_success_rate_change * 100,
            'risk_level': risk_level,
            'expected_benefit': benefit,
            'rollback_time_estimate': '5-15分钟' if risk_level == 'low' else '15-30分钟'
        }

    def _save_optimization_result(self, result: ReplacementOptimizationResult):
        """保存优化结果"""
        try:
            filename = f"optimization_{result.agent_name}_{result.timestamp.strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.data_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'agent_name': result.agent_name,
                    'current_rate': result.current_rate,
                    'recommended_rate': result.recommended_rate,
                    'adjustment_direction': result.adjustment_direction.value,
                    'confidence_score': result.confidence_score,
                    'reasoning': result.reasoning,
                    'expected_impact': result.expected_impact,
                    'timestamp': result.timestamp.isoformat()
                }, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"保存优化结果异常: {e}")

    async def apply_optimization_recommendation(self, agent_name: str,
                                               result: ReplacementOptimizationResult) -> bool:
        """
        应用优化建议

        Args:
            agent_name: Agent名称
            result: 优化结果

        Returns:
            是否成功应用
        """
        try:
            # 这里应该实际调整Agent包装器的替换率
            # 由于无法直接访问包装器实例，这里记录调整意图

            if result.adjustment_direction != AdjustmentDirection.HOLD:
                self.current_adjustments[agent_name] = result.recommended_rate
                logger.info(f"✅ 已记录{agent_name}替换率调整: {result.current_rate:.1%} → {result.recommended_rate:.1%}")

                # 在实际系统中，这里应该调用包装器的设置方法
                # await self._update_agent_replacement_rate(agent_name, result.recommended_rate)

            return True

        except Exception as e:
            logger.error(f"应用优化建议异常: {e}")
            return False

    def get_optimization_summary(self) -> Dict[str, Any]:
        """获取优化摘要"""
        return {
            'strategy': self.strategy.value,
            'agents_optimized': list(self.optimization_history.keys()),
            'total_optimizations': sum(len(history) for history in self.optimization_history.values()),
            'current_adjustments': self.current_adjustments,
            'data_directory': str(self.data_dir)
        }


# 全局优化器实例
_optimizer = None


def get_replacement_optimizer(strategy: OptimizationStrategy = OptimizationStrategy.BALANCED) -> IntelligentReplacementOptimizer:
    """获取全局替换率优化器实例"""
    global _optimizer
    if _optimizer is None:
        _optimizer = IntelligentReplacementOptimizer(strategy)
    return _optimizer


async def optimize_all_agents_replacement_rates() -> Dict[str, List[ReplacementOptimizationResult]]:
    """优化所有Agent的替换率"""
    optimizer = get_replacement_optimizer()

    # 逐步替换的Agent列表
    agents_to_optimize = [
        'ChiefAgentWrapper',
        'AnswerGenerationAgentWrapper',
        'LearningSystemWrapper',
        'StrategicChiefAgentWrapper',
        'PromptEngineeringAgentWrapper',
        'ContextEngineeringAgentWrapper',
        'OptimizedKnowledgeRetrievalAgentWrapper'
    ]

    results = {}

    for agent_name in agents_to_optimize:
        try:
            # 模拟收集当前指标（实际应该从监控系统获取）
            current_metrics = {
                'replacement_rate': 0.01,  # 默认1%
                'avg_response_time': 2.5,
                'success_rate': 0.95,
                'error_rate': 0.05,
                'cpu_usage': 55,
                'memory_usage': 65
            }

            result = await optimizer.optimize_replacement_rate(agent_name, current_metrics)
            results[agent_name] = [result]

            # 应用优化建议
            await optimizer.apply_optimization_recommendation(agent_name, result)

        except Exception as e:
            logger.error(f"优化{agent_name}失败: {e}")
            results[agent_name] = []

    return results
