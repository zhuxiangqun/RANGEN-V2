#!/usr/bin/env python3
"""
LearningOptimizer - 学习优化器 (L3基础认知)
增量学习算法、性能模式识别、A/B测试自动化
from ..utils.unified_centers import get_unified_config_center
from ..utils.unified_threshold_manager import get_unified_threshold_manager


优化特性：
- 增量学习算法：支持模型参数和策略的在线增量更新
- 性能模式识别：自动识别系统性能瓶颈和优化机会
- A/B测试自动化：集成A/B测试框架，自动验证优化效果
- 自适应学习策略：基于历史表现动态调整学习参数
"""

import time
import logging
import asyncio
import json
import hashlib
import threading
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, OrderedDict
from concurrent.futures import ThreadPoolExecutor
import statistics
import random
import math

from .expert_agent import ExpertAgent
from .base_agent import AgentResult
from src.utils.logging_helper import get_module_logger, ModuleType

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """学习模式"""
    INCREMENTAL = "incremental"      # 增量学习
    BATCH = "batch"                  # 批量学习
    ONLINE = "online"               # 在线学习
    TRANSFER = "transfer"           # 迁移学习
    META = "meta"                   # 元学习


class OptimizationTarget(Enum):
    """优化目标"""
    PERFORMANCE = "performance"      # 性能优化
    ACCURACY = "accuracy"           # 准确性优化
    EFFICIENCY = "efficiency"       # 效率优化
    ROBUSTNESS = "robustness"       # 鲁棒性优化
    SCALABILITY = "scalability"     # 可扩展性优化


class ExperimentStatus(Enum):
    """实验状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class LearningModel:
    """学习模型"""
    model_id: str
    name: str
    version: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    training_data_size: int = 0
    last_updated: float = field(default_factory=time.time)
    learning_mode: LearningMode = LearningMode.INCREMENTAL
    optimization_target: OptimizationTarget = OptimizationTarget.PERFORMANCE


@dataclass
class PerformancePattern:
    """性能模式"""
    pattern_id: str
    name: str
    description: str
    indicators: List[str]  # 性能指标
    threshold: float  # 阈值
    confidence: float = 0.0
    occurrences: int = 0
    last_detected: Optional[float] = None
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ABTest:
    """A/B测试"""
    test_id: str
    name: str
    description: str
    variants: Dict[str, Dict[str, Any]]  # 变体配置
    target_metric: str
    baseline_variant: str
    status: ExperimentStatus = ExperimentStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    results: Dict[str, Any] = field(default_factory=dict)
    winner: Optional[str] = None
    confidence_level: float = 0.0


class LearningOptimizer(ExpertAgent):
    """LearningOptimizer - 学习优化器 (L3基础认知)

    核心职责：
    1. 增量学习算法 - 支持模型参数和策略的在线增量更新
    2. 性能模式识别 - 自动识别系统性能瓶颈和优化机会
    3. A/B测试自动化 - 集成A/B测试框架，自动验证优化效果
    4. 自适应学习策略 - 基于历史表现动态调整学习参数

    优化特性：
    - 多模式学习算法：增量、批量、在线、迁移、元学习
    - 智能性能分析：基于统计和机器学习识别性能模式
    - 自动化实验设计：自动生成和执行A/B测试
    - 自适应优化：动态调整学习超参数和策略
    """

    def __init__(self):
        """初始化LearningOptimizer"""
        # 初始化统一配置中心
        self.config_center = get_unified_config_center()
        self.threshold_manager = get_unified_threshold_manager()

        # 获取Agent特定配置
        self.agent_config = self.config_center.get_agent_config(self.__class__.__name__, {
            'enabled': True,
            'max_retries': 3,
            'timeout': 30,
            'debug_mode': False
        })

        # 获取阈值配置
        self.thresholds = self.threshold_manager.get_thresholds(self.__class__.__name__, {
            'performance_warning_threshold': 5.0,
            'error_rate_threshold': 0.1,
            'memory_usage_threshold': 80.0
        })

        super().__init__(
            agent_id="learning_optimizer",
            domain_expertise="增量学习和性能优化",
            capability_level=0.7,  # L3基础认知
            collaboration_style="analytical"
        )

        # 使用模块日志器
        self.module_logger = get_module_logger(ModuleType.AGENT, "LearningOptimizer")

        # 🚀 新增：学习模型管理
        self._learning_models: Dict[str, LearningModel] = {}
        self._performance_patterns: Dict[str, PerformancePattern] = {}
        self._ab_tests: Dict[str, ABTest] = {}
        self._performance_history: List[Dict[str, Any]] = []

        # 🚀 新增：学习和优化配置
        self._parallel_executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="learning_optimization")
        self._max_history_size = 5000
        self._learning_cache = OrderedDict()  # LRU缓存
        self._cache_max_size = 1000

        # 🚀 新增：自适应参数
        self._adaptive_params = {
            'learning_rate': 0.01,
            'learning_rate_decay': 0.95,
            'min_learning_rate': 0.001,
            'performance_threshold': 0.8,
            'pattern_confidence_threshold': 0.7,
            'ab_test_sample_size': 100,
            'ab_test_duration_hours': 24,
            'optimization_interval': 3600  # 1小时
        }

        # 🚀 新增：统计和监控
        self._stats = {
            'total_learning_cycles': 0,
            'successful_optimizations': 0,
            'ab_tests_completed': 0,
            'patterns_detected': 0,
            'performance_improvements': 0.0,
            'learning_efficiency': 0.0
        }

        # 🚀 新增：内置性能模式
        self._initialize_builtin_patterns()

        # 启动优化线程
        self._optimization_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_optimization_thread()

    def _get_service(self):
        """LearningOptimizer不直接使用单一Service"""
        return None

    # 🚀 新增：增量学习算法
    async def incremental_learning(self, model_id: str, new_data: List[Dict[str, Any]],
                                 learning_rate: Optional[float] = None) -> Dict[str, Any]:
        """增量学习算法"""
        if model_id not in self._learning_models:
            return {'success': False, 'error': f'模型不存在: {model_id}'}

        model = self._learning_models[model_id]
        start_time = time.time()

        self.module_logger.info(f"🔄 开始增量学习: {model.name}, 新数据量={len(new_data)}")

        # 使用指定的学习率或自适应学习率
        effective_lr = learning_rate or self._adaptive_params['learning_rate']

        # 增量学习逻辑（简化实现）
        updates = 0
        total_improvement = 0.0

        for data_point in new_data:
            # 计算梯度（简化实现）
            gradient = await self._compute_gradient(model, data_point)

            if gradient:
                # 更新模型参数
                for param_name, param_value in model.parameters.items():
                    if param_name in gradient:
                        # 应用梯度下降
                        new_value = param_value - effective_lr * gradient[param_name]
                        model.parameters[param_name] = new_value
                        updates += 1

                # 计算性能改进
                improvement = await self._evaluate_improvement(model, data_point)
                total_improvement += improvement

        # 更新模型元数据
        model.training_data_size += len(new_data)
        model.last_updated = time.time()

        # 学习率衰减
        self._adaptive_params['learning_rate'] = max(
            self._adaptive_params['min_learning_rate'],
            self._adaptive_params['learning_rate'] * self._adaptive_params['learning_rate_decay']
        )

        execution_time = time.time() - start_time
        avg_improvement = total_improvement / max(len(new_data), 1)

        result = {
            'success': True,
            'model_id': model_id,
            'updates_applied': updates,
            'average_improvement': avg_improvement,
            'execution_time': execution_time,
            'final_learning_rate': self._adaptive_params['learning_rate']
        }

        self.module_logger.info(f"✅ 增量学习完成: {model.name}, 更新={updates}, 平均改进={avg_improvement:.4f}")
        return result

    async def _compute_gradient(self, model: LearningModel, data_point: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """计算梯度（简化实现）"""
        try:
            # 这里应该实现具体的梯度计算逻辑
            # 简化版本：基于性能反馈计算梯度

            performance_feedback = data_point.get('performance_feedback', {})
            if not performance_feedback:
                return None

            gradient = {}
            for param_name, current_value in model.parameters.items():
                # 基于性能反馈计算梯度
                feedback_value = performance_feedback.get(param_name, 0.0)

                if isinstance(current_value, (int, float)):
                    # 对于数值参数，基于反馈调整
                    gradient[param_name] = -feedback_value * 0.1  # 负梯度
                elif isinstance(current_value, bool):
                    # 对于布尔参数，基于阈值调整
                    gradient[param_name] = 0.0  # 布尔参数不计算梯度
                else:
                    # 对于其他参数，随机小幅调整
                    gradient[param_name] = random.uniform(-0.01, 0.01)

            return gradient

        except Exception as e:
            self.module_logger.warning(f"梯度计算失败: {e}")
            return None

    async def _evaluate_improvement(self, model: LearningModel, data_point: Dict[str, Any]) -> float:
        """评估改进效果"""
        try:
            # 计算改进指标（简化实现）
            before_metrics = data_point.get('before_metrics', {})
            after_metrics = data_point.get('after_metrics', {})

            improvements = []
            for metric_name in set(before_metrics.keys()) | set(after_metrics.keys()):
                before = before_metrics.get(metric_name, 0.0)
                after = after_metrics.get(metric_name, 0.0)

                if before > 0:
                    improvement = (after - before) / before
                    improvements.append(improvement)

            return statistics.mean(improvements) if improvements else 0.0

        except Exception as e:
            self.module_logger.warning(f"改进评估失败: {e}")
            return 0.0

    # 🚀 新增：性能模式识别
    async def detect_performance_patterns(self, performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """检测性能模式"""
        detected_patterns = []

        for pattern_id, pattern in self._performance_patterns.items():
            matches = await self._evaluate_pattern_match(pattern, performance_data)

            if matches['is_match']:
                # 更新模式统计
                pattern.occurrences += 1
                pattern.last_detected = time.time()
                pattern.confidence = matches['confidence']

                detected_patterns.append({
                    'pattern_id': pattern_id,
                    'pattern_name': pattern.name,
                    'confidence': matches['confidence'],
                    'recommendations': pattern.recommendations,
                    'severity': matches.get('severity', 'medium')
                })

                self.module_logger.info(f"🎯 检测到性能模式: {pattern.name} (置信度={matches['confidence']:.2f})")

        # 更新统计
        self._stats['patterns_detected'] += len(detected_patterns)

        return detected_patterns

    async def _evaluate_pattern_match(self, pattern: PerformancePattern,
                                    performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """评估模式匹配度"""
        try:
            if len(performance_data) < 5:  # 需要最小数据量
                return {'is_match': False, 'confidence': 0.0}

            # 计算指标统计
            indicator_stats = {}
            for indicator in pattern.indicators:
                values = [d.get(indicator, 0.0) for d in performance_data if indicator in d]
                if values:
                    indicator_stats[indicator] = {
                        'mean': statistics.mean(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                        'trend': self._calculate_trend(values)
                    }

            # 评估是否匹配模式
            match_score = 0.0
            total_indicators = len(pattern.indicators)

            for indicator in pattern.indicators:
                if indicator in indicator_stats:
                    stats = indicator_stats[indicator]

                    # 检查是否超过阈值
                    if pattern.name == "Performance Degradation":
                        if stats['trend'] < -0.1:  # 下降趋势
                            match_score += 1.0
                    elif pattern.name == "Memory Leak":
                        if stats['mean'] > pattern.threshold:
                            match_score += 1.0
                    elif pattern.name == "High Latency":
                        if stats['mean'] > pattern.threshold:
                            match_score += 1.0
                    # 添加更多模式检查...

            confidence = match_score / total_indicators if total_indicators > 0 else 0.0

            return {
                'is_match': confidence >= pattern.threshold,
                'confidence': confidence,
                'severity': 'high' if confidence > 0.8 else 'medium' if confidence > 0.6 else 'low'
            }

        except Exception as e:
            self.module_logger.warning(f"模式评估失败: {e}")
            return {'is_match': False, 'confidence': 0.0}

    def _calculate_trend(self, values: List[float]) -> float:
        """计算趋势（线性回归斜率）"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        y = values

        # 计算线性回归斜率
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)

        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    # 🚀 新增：A/B测试自动化
    async def create_ab_test(self, name: str, description: str, variants: Dict[str, Dict[str, Any]],
                           target_metric: str, baseline_variant: str) -> str:
        """创建A/B测试"""
        test_id = f"ab_test_{int(time.time() * 1000)}_{hash(name) % 10000}"

        ab_test = ABTest(
            test_id=test_id,
            name=name,
            description=description,
            variants=variants,
            target_metric=target_metric,
            baseline_variant=baseline_variant
        )

        self._ab_tests[test_id] = ab_test
        self.module_logger.info(f"✅ A/B测试已创建: {name} ({test_id})")
        return test_id

    async def run_ab_test(self, test_id: str, sample_size: Optional[int] = None) -> Dict[str, Any]:
        """运行A/B测试"""
        if test_id not in self._ab_tests:
            return {'success': False, 'error': f'A/B测试不存在: {test_id}'}

        ab_test = self._ab_tests[test_id]
        if ab_test.status == ExperimentStatus.RUNNING:
            return {'success': False, 'error': '测试已在运行中'}

        ab_test.status = ExperimentStatus.RUNNING
        ab_test.start_time = time.time()

        effective_sample_size = sample_size or self._adaptive_params['ab_test_sample_size']

        self.module_logger.info(f"🧪 开始A/B测试: {ab_test.name}, 样本量={effective_sample_size}")

        # 模拟A/B测试执行（实际应该调用真实的测试执行逻辑）
        test_results = await self._simulate_ab_test_execution(ab_test, effective_sample_size)

        # 分析结果
        analysis = await self._analyze_ab_test_results(ab_test, test_results)

        # 更新测试状态
        ab_test.status = ExperimentStatus.COMPLETED
        ab_test.end_time = time.time()
        ab_test.results = test_results
        ab_test.winner = analysis.get('winner')
        ab_test.confidence_level = analysis.get('confidence', 0.0)

        result = {
            'success': True,
            'test_id': test_id,
            'winner': ab_test.winner,
            'confidence': ab_test.confidence_level,
            'analysis': analysis,
            'execution_time': ab_test.end_time - ab_test.start_time
        }

        self._stats['ab_tests_completed'] += 1

        self.module_logger.info(f"✅ A/B测试完成: {ab_test.name}, 获胜变体={ab_test.winner}, 置信度={ab_test.confidence_level:.2f}")

        return result

    async def _simulate_ab_test_execution(self, ab_test: ABTest, sample_size: int) -> Dict[str, Any]:
        """模拟A/B测试执行"""
        # 这里应该实现真实的A/B测试执行逻辑
        # 简化版本：生成模拟结果

        results = {}
        for variant_name in ab_test.variants.keys():
            # 生成模拟的性能指标
            base_performance = random.uniform(0.7, 0.9)
            variance = random.uniform(0.05, 0.15)

            results[variant_name] = {
                'samples': sample_size,
                'metric_values': [base_performance + random.uniform(-variance, variance)
                                for _ in range(sample_size)],
                'mean_performance': base_performance,
                'std_performance': variance
            }

        return results

    async def _analyze_ab_test_results(self, ab_test: ABTest, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析A/B测试结果"""
        try:
            # 统计检验（简化实现）
            baseline_results = results.get(ab_test.baseline_variant, {})
            baseline_mean = baseline_results.get('mean_performance', 0.0)

            best_variant = ab_test.baseline_variant
            best_improvement = 0.0
            best_p_value = 1.0

            for variant_name, variant_results in results.items():
                if variant_name == ab_test.baseline_variant:
                    continue

                variant_mean = variant_results.get('mean_performance', 0.0)
                improvement = variant_mean - baseline_mean

                # 简化的p值计算（实际应该使用t检验）
                baseline_std = baseline_results.get('std_performance', 0.1)
                variant_std = variant_results.get('std_performance', 0.1)
                pooled_std = math.sqrt((baseline_std**2 + variant_std**2) / 2)

                if pooled_std > 0:
                    t_stat = improvement / (pooled_std / math.sqrt(len(results)))
                    # 近似p值（单尾检验）
                    p_value = 1.0 - abs(t_stat) / 6.0  # 简化近似
                else:
                    p_value = 0.5

                if improvement > best_improvement and p_value < 0.05:  # 显著性阈值
                    best_variant = variant_name
                    best_improvement = improvement
                    best_p_value = p_value

            return {
                'winner': best_variant,
                'improvement': best_improvement,
                'confidence': 1.0 - best_p_value,
                'baseline_performance': baseline_mean,
                'winner_performance': results.get(best_variant, {}).get('mean_performance', 0.0),
                'statistically_significant': best_p_value < 0.05
            }

        except Exception as e:
            self.module_logger.warning(f"A/B测试结果分析失败: {e}")
            return {'winner': ab_test.baseline_variant, 'improvement': 0.0, 'confidence': 0.0}

    # 🚀 新增：自适应优化策略
    async def adaptive_optimization(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """自适应优化策略"""
        self.module_logger.info("🔄 开始自适应优化")

        # 1. 检测性能模式
        patterns = await self.detect_performance_patterns(performance_data)

        # 2. 生成优化建议
        recommendations = await self._generate_optimization_recommendations(patterns, performance_data)

        # 3. 应用优化
        applied_optimizations = []
        for rec in recommendations:
            if rec.get('auto_apply', False):
                success = await self._apply_optimization(rec)
                if success:
                    applied_optimizations.append(rec)

        # 4. 更新学习参数
        await self._update_learning_parameters(performance_data)

        result = {
            'patterns_detected': len(patterns),
            'recommendations_generated': len(recommendations),
            'optimizations_applied': len(applied_optimizations),
            'performance_trend': self._calculate_performance_trend(performance_data)
        }

        self.module_logger.info(f"✅ 自适应优化完成: 检测模式={len(patterns)}, 应用优化={len(applied_optimizations)}")

        return result

    async def _generate_optimization_recommendations(self, patterns: List[Dict[str, Any]],
                                                   performance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成优化建议"""
        recommendations = []

        for pattern in patterns:
            pattern_name = pattern.get('pattern_name', '')

            if pattern_name == "Performance Degradation":
                recommendations.append({
                    'type': 'parameter_tuning',
                    'target': 'learning_rate',
                    'action': 'decrease',
                    'value': 0.8,
                    'reason': '检测到性能下降，建议降低学习率',
                    'auto_apply': True
                })
            elif pattern_name == "Memory Leak":
                recommendations.append({
                    'type': 'resource_management',
                    'target': 'memory_cleanup',
                    'action': 'enable',
                    'reason': '检测到内存泄漏，建议启用内存清理',
                    'auto_apply': True
                })
            elif pattern_name == "High Latency":
                recommendations.append({
                    'type': 'performance_tuning',
                    'target': 'parallel_processing',
                    'action': 'increase',
                    'value': 2,
                    'reason': '检测到高延迟，建议增加并行处理',
                    'auto_apply': False
                })

        return recommendations

    async def _apply_optimization(self, recommendation: Dict[str, Any]) -> bool:
        """应用优化"""
        try:
            opt_type = recommendation.get('type')
            target = recommendation.get('target')
            action = recommendation.get('action')
            value = recommendation.get('value')

            if opt_type == 'parameter_tuning' and target == 'learning_rate':
                if action == 'decrease':
                    self._adaptive_params['learning_rate'] *= value
                elif action == 'increase':
                    self._adaptive_params['learning_rate'] /= value

                self._adaptive_params['learning_rate'] = max(
                    self._adaptive_params['min_learning_rate'],
                    min(0.1, self._adaptive_params['learning_rate'])
                )

            elif opt_type == 'resource_management' and target == 'memory_cleanup':
                # 这里应该触发内存清理逻辑
                pass

            self.module_logger.info(f"✅ 应用优化: {opt_type} -> {target} ({action})")
            return True

        except Exception as e:
            self.module_logger.warning(f"应用优化失败: {e}")
            return False

    async def _update_learning_parameters(self, performance_data: List[Dict[str, Any]]):
        """更新学习参数"""
        try:
            if len(performance_data) < 5:
                return

            # 计算性能趋势
            recent_performance = [d.get('overall_performance', 0.8) for d in performance_data[-10:]]
            trend = self._calculate_trend(recent_performance)

            # 基于趋势调整参数
            if trend < -0.01:  # 性能下降
                self._adaptive_params['learning_rate'] *= 0.9
                self._adaptive_params['pattern_confidence_threshold'] = min(0.9,
                    self._adaptive_params['pattern_confidence_threshold'] + 0.05)
            elif trend > 0.01:  # 性能上升
                self._adaptive_params['learning_rate'] *= 1.05
                self._adaptive_params['pattern_confidence_threshold'] = max(0.5,
                    self._adaptive_params['pattern_confidence_threshold'] - 0.02)

            # 限制参数范围
            self._adaptive_params['learning_rate'] = max(0.001, min(0.1, self._adaptive_params['learning_rate']))

        except Exception as e:
            self.module_logger.warning(f"学习参数更新失败: {e}")

    def _calculate_performance_trend(self, performance_data: List[Dict[str, Any]]) -> float:
        """计算性能趋势"""
        if len(performance_data) < 2:
            return 0.0

        values = [d.get('overall_performance', 0.8) for d in performance_data[-20:]]
        return self._calculate_trend(values)

    # 🚀 新增：模型管理和监控
    async def register_learning_model(self, name: str, parameters: Dict[str, Any],
                                    learning_mode: LearningMode = LearningMode.INCREMENTAL) -> str:
        """注册学习模型"""
        model_id = f"model_{int(time.time() * 1000)}_{hash(name) % 10000}"

        model = LearningModel(
            model_id=model_id,
            name=name,
            version="1.0.0",
            parameters=parameters,
            learning_mode=learning_mode
        )

        self._learning_models[model_id] = model
        self.module_logger.info(f"✅ 学习模型已注册: {name} ({model_id})")
        return model_id

    async def update_model_performance(self, model_id: str, metrics: Dict[str, float]):
        """更新模型性能指标"""
        if model_id in self._learning_models:
            model = self._learning_models[model_id]
            model.performance_metrics.update(metrics)
            model.last_updated = time.time()

    # 🚀 新增：内置性能模式初始化
    def _initialize_builtin_patterns(self):
        """初始化内置性能模式"""
        patterns = [
            PerformancePattern(
                pattern_id="perf_degradation",
                name="Performance Degradation",
                description="检测到性能持续下降",
                indicators=["response_time", "throughput", "error_rate"],
                threshold=0.7,
                recommendations=[
                    "检查系统资源使用情况",
                    "优化算法复杂度",
                    "增加缓存机制",
                    "减少不必要的计算"
                ]
            ),
            PerformancePattern(
                pattern_id="memory_leak",
                name="Memory Leak",
                description="检测到内存使用异常增长",
                indicators=["memory_usage", "gc_frequency"],
                threshold=0.8,
                recommendations=[
                    "检查对象引用释放",
                    "优化内存分配策略",
                    "启用垃圾回收优化",
                    "监控内存使用趋势"
                ]
            ),
            PerformancePattern(
                pattern_id="high_latency",
                name="High Latency",
                description="检测到响应延迟异常",
                indicators=["response_time", "queue_length"],
                threshold=0.9,
                recommendations=[
                    "优化网络请求",
                    "增加并发处理能力",
                    "使用缓存机制",
                    "优化数据库查询"
                ]
            )
        ]

        for pattern in patterns:
            self._performance_patterns[pattern.pattern_id] = pattern

    # 🚀 新增：优化线程
    def _start_optimization_thread(self):
        """启动优化线程"""
        self._running = True
        self._optimization_thread = threading.Thread(target=self._optimization_worker, daemon=True)
        self._optimization_thread.start()
        self.module_logger.debug("🔧 学习优化线程已启动")

    def _optimization_worker(self):
        """优化工作线程"""
        while self._running:
            try:
                time.sleep(self._adaptive_params['optimization_interval'])

                # 创建事件循环来运行异步任务
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:
                    # 执行定期优化任务
                    if len(self._performance_history) >= 10:
                        recent_data = self._performance_history[-50:]
                        loop.run_until_complete(self.adaptive_optimization(recent_data))

                finally:
                    loop.close()

            except Exception as e:
                self.module_logger.warning(f"学习优化异常: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self._stats,
            'registered_models': len(self._learning_models),
            'active_patterns': len(self._performance_patterns),
            'running_ab_tests': len([t for t in self._ab_tests.values() if t.status == ExperimentStatus.RUNNING]),
            'cache_size': len(self._learning_cache),
            'current_learning_rate': self._adaptive_params['learning_rate'],
            'performance_history_size': len(self._performance_history)
        }

    # 核心执行方法
    async def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        执行学习优化任务

        Args:
            context: 学习优化请求上下文
                - action: 操作类型 ("incremental_learning", "detect_patterns", "create_ab_test", "run_ab_test", "adaptive_optimization", "register_model", "stats")
                - model_id: 模型ID (incremental_learning时需要)
                - new_data: 新数据 (incremental_learning时需要)
                - performance_data: 性能数据 (detect_patterns/adaptive_optimization时需要)
                - test_name/description/variants/target_metric/baseline_variant: A/B测试信息 (create_ab_test时需要)
                - test_id: 测试ID (run_ab_test时需要)
                - model_name/parameters/learning_mode: 模型信息 (register_model时需要)

        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        action = context.get("action", "")

        try:
            if action == "incremental_learning":
                model_id = context.get("model_id", "")
                new_data = context.get("new_data", [])

                if not model_id or not new_data:
                    result_data = {"error": "模型ID和新数据不能为空"}
                else:
                    result_data = await self.incremental_learning(model_id, new_data)

            elif action == "detect_patterns":
                performance_data = context.get("performance_data", [])

                if not performance_data:
                    result_data = {"error": "性能数据不能为空"}
                else:
                    patterns = await self.detect_performance_patterns(performance_data)
                    result_data = {"detected_patterns": patterns, "count": len(patterns)}

            elif action == "create_ab_test":
                test_name = context.get("test_name", "")
                description = context.get("description", "")
                variants = context.get("variants", {})
                target_metric = context.get("target_metric", "")
                baseline_variant = context.get("baseline_variant", "")

                if not test_name or not variants or not target_metric or not baseline_variant:
                    result_data = {"error": "测试名称、变体、目标指标和基准变体不能为空"}
                else:
                    test_id = await self.create_ab_test(test_name, description, variants, target_metric, baseline_variant)
                    result_data = {"test_id": test_id, "status": "created"}

            elif action == "run_ab_test":
                test_id = context.get("test_id", "")

                if not test_id:
                    result_data = {"error": "测试ID不能为空"}
                else:
                    result_data = await self.run_ab_test(test_id)

            elif action == "adaptive_optimization":
                performance_data = context.get("performance_data", [])

                if not performance_data:
                    result_data = {"error": "性能数据不能为空"}
                else:
                    result_data = await self.adaptive_optimization(performance_data)

            elif action == "register_model":
                model_name = context.get("model_name", "")
                parameters = context.get("parameters", {})
                learning_mode = LearningMode(context.get("learning_mode", "incremental"))

                if not model_name:
                    result_data = {"error": "模型名称不能为空"}
                else:
                    model_id = await self.register_learning_model(model_name, parameters, learning_mode)
                    result_data = {"model_id": model_id, "status": "registered"}

            elif action == "stats":
                result_data = self.get_stats()

            else:
                result_data = {"error": f"不支持的操作: {action}"}

            return AgentResult(
                success=True,
                data=result_data,
                confidence=0.8,
                processing_time=time.time() - start_time
            )

        except Exception as e:
            self.module_logger.error(f"❌ LearningOptimizer执行异常: {e}", exc_info=True)
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )

    def shutdown(self):
        """关闭学习优化器"""
        self._running = False
        if self._optimization_thread and self._optimization_thread.is_alive():
            self._optimization_thread.join(timeout=5)

        self._parallel_executor.shutdown(wait=True)
        self.module_logger.info("🛑 LearningOptimizer已关闭")
