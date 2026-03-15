"""
自适应参数优化器 - 动态调整算法参数
实现基于性能的参数自动优化
"""
import asyncio
import logging
import time
import random
import json
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
from collections import defaultdict, deque
from enum import Enum

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)
class OptimizationStrategy(Enum):
    """优化策略"""
    BAYESIAN = "bayesian"
    GENETIC = "genetic"
    REINFORCEMENT = "reinforcement"
    GRADIENT = "gradient"
    RANDOM_SEARCH = "random_search"
@dataclass
class ParameterRange:
    """参数范围"""
    min_value: float
    max_value: float
    step_size: float = config.DEFAULT_VERY_LOW_THRESHOLD  # 将在初始化时动态设置，实际值由智能配置决定
    current_value: Optional[float] = None

    def __post_init__(self):
        if self.current_value is None:
            self.current_value = (self.min_value + self.max_value) / 2
@dataclass
class PerformanceMetrics:
    """性能指标"""
    accuracy: float = get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))  # 将在初始化时动态设置，实际值由智能配置决定
    execution_time: float = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE  # 将在初始化时动态设置，实际值由智能配置决定
    success_rate: float = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE  # 将在初始化时动态设置，实际值由智能配置决定
    efficiency: float = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE  # 将在初始化时动态设置，实际值由智能配置决定
    quality_score: float = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE  # 将在初始化时动态设置，实际值由智能配置决定
    timestamp: datetime = field(default_factory=datetime.now)
@dataclass
class OptimizationResult:
    """优化结果"""
    algorithm_name: str
    optimal_parameters: Dict[str, Any]
    performance_metrics: PerformanceMetrics
    optimization_time: float
    iterations: int
    convergence: bool
    improvement: float  # 将在初始化时动态设置，实际值由智能配置决定
    metadata: Dict[str, Any]
class AdaptiveParameterOptimizer:
    """自适应参数优化器"""

    def __init__(self):
        self.parameter_ranges = {}
        self.performance_metrics = defaultdict(deque)
        self.optimization_history = []

        try:
            from src.utils.unified_intelligent_center import get_unified_intelligent_center
            learning_system = get_unified_intelligent_center()

            if learning_system:
                learning_params = learning_system.get_learned_keywords("optimization_params")
                if learning_params and isinstance(learning_params, dict):
                    from common_helpers import safe_float

                    self.learning_rate = safe_float(learning_params.get("learning_rate"), config.DEFAULT_LOW_DECIMAL_THRESHOLD)
                    # 使用智能配置系统获取默认阈值参数
                    adaptive_context = create_query_context(query_type="adaptive_parameter_optimizer_config")
                    self.adaptation_threshold = safe_float(learning_params.get("adaptation_threshold"), get_smart_config("adaptation_threshold", adaptive_context))
                    self.max_iterations = int(safe_float(learning_params.get("max_iterations"), config.DEFAULT_LIMIT))
                    self.convergence_threshold = safe_float(learning_params.get("convergence_threshold"), get_smart_config("convergence_threshold", adaptive_context))
                else:
                    self._set_minimal_default_params()
            else:
                self._set_minimal_default_params()
        except ImportError:
            logger.warning("无法导入智能学习系统，使用默认配置")
            self._set_minimal_default_params()
        except Exception as e:
            logger.warning(f"智能学习系统初始化失败: {e}，使用默认配置")
            self._set_minimal_default_params()

        self.optimization_strategies = {
            OptimizationStrategy.BAYESIAN: self._bayesian_optimization,
            OptimizationStrategy.GENETIC: self._genetic_optimization,
            OptimizationStrategy.REINFORCEMENT: self._reinforcement_optimization,
            OptimizationStrategy.GRADIENT: self._gradient_optimization,
            OptimizationStrategy.RANDOM_SEARCH: self._random_search_optimization
        }

        logger.info("自适应参数优化器初始化完成")

    def _get_parameter_from_unified_config(self, param_name: str, default_value: Any = None) -> Any:
        """从统一配置管理中心获取参数值"""
        try:
            # 使用统一依赖管理器获取配置
            from src.utils.unified_dependency_manager import get_dependency
            config_manager = get_dependency('unified_config_center')
            
            if config_manager and hasattr(config_manager, 'get_parameter'):
                value = config_manager.get_parameter(param_name, None)
                if value is not None:
                    return value
        except Exception as e:
            logger.warning(f"获取参数失败 {param_name}: {e}")

        return default_value

    def _set_minimal_default_params(self):
        """设置最小化的默认参数"""
        self.learning_rate = self._get_intelligent_optimization_param("learning_rate")
        self.adaptation_threshold = self._get_intelligent_optimization_param("adaptation_threshold")
        self.max_iterations = self._get_intelligent_optimization_param("max_iterations")
        self.convergence_threshold = self._get_intelligent_optimization_param("convergence_threshold")

    async def optimize_parameters(
        self,
        algorithm_name: str,
        performance_metrics: Dict[str, float],
        strategy: OptimizationStrategy = OptimizationStrategy.BAYESIAN
    ) -> OptimizationResult:
        """动态参数优化"""
        start_time = time.time()

        try:
            performance_analysis = await self._analyze_performance(performance_metrics)

            optimization_func = self.optimization_strategies.get(strategy, self._bayesian_optimization)

            optimal_params, iterations, convergence = await optimization_func(
                algorithm_name, performance_analysis
            )

            validated_params = await self._validate_parameters(optimal_params, algorithm_name)

            final_metrics = await self._apply_and_monitor_parameters(validated_params, algorithm_name)

            improvement = await self._calculate_improvement(performance_metrics, final_metrics)

            optimization_time = time.time() - start_time
            result = OptimizationResult(
                algorithm_name=algorithm_name,
                optimal_parameters=validated_params,
                performance_metrics=final_metrics,
                optimization_time=optimization_time,
                iterations=iterations,
                convergence=convergence,
                improvement=improvement,
                metadata={"strategy": strategy.value, "timestamp": datetime.now()}
            )

            self.optimization_history.append(result)

            logger.info("参数优化完成: {algorithm_name}, 改进: {improvement:.3f}")

            return result

        except Exception as e:
            logger.error("【异常处理】参数优化失败: {e}")
            return OptimizationResult(
                algorithm_name=algorithm_name,
                optimal_parameters={},
                performance_metrics=PerformanceMetrics(),
                optimization_time=time.time() - start_time,
                iterations=config.DEFAULT_ZERO_VALUE,
                convergence=False,
                improvement=config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE,
                metadata={"error": str(e), "fallback_used": True}
            )

    async def _analyze_performance(self, performance_metrics: Dict[str, float]) -> Dict[str, Any]:
        """分析性能指标"""
        analysis = {
            "trend": "stable",
            "bottlenecks": [],
            "optimization_opportunities": [],
            "recommendations": []
        }

        if len(self.performance_metrics) > 5:
            recent_metrics = list(self.performance_metrics.values())[-5:]
            accuracy_trend = []
            for metrics_deque in recent_metrics:
                if metrics_deque:
                    latest_metric = metrics_deque[-config.DEFAULT_ONE_VALUE] if hasattr(metrics_deque, '__getitem__') else None
                    if latest_metric and hasattr(latest_metric, 'accuracy'):
                        accuracy_trend.append(latest_metric.accuracy)

            if len(accuracy_trend) >= 2:
                if accuracy_trend[-1] > accuracy_trend[0]:
                    analysis["trend"] = "improving"
                elif accuracy_trend[-config.DEFAULT_ONE_VALUE] < accuracy_trend[config.DEFAULT_ZERO_VALUE]:
                    analysis["trend"] = "declining"

        min_length = self._get_dynamic_min_length()
        if performance_metrics.get("execution_time", config.DEFAULT_ZERO_VALUE) > min_length:
            analysis["bottlenecks"].append("execution_time")

        accuracy_threshold = self._get_intelligent_optimization_param("accuracy_bottleneck_threshold")
        if performance_metrics.get("accuracy", config.DEFAULT_ZERO_VALUE) < accuracy_threshold:
            analysis["bottlenecks"].append("accuracy")

        success_rate_threshold = self._get_intelligent_optimization_param("success_rate_bottleneck_threshold")
        if performance_metrics.get("success_rate", config.DEFAULT_ZERO_VALUE) < success_rate_threshold:
            analysis["bottlenecks"].append("success_rate")

        accuracy_optimization_threshold = self._get_intelligent_optimization_param("accuracy_optimization_threshold")
        if performance_metrics.get("accuracy", config.DEFAULT_ZERO_VALUE) < accuracy_optimization_threshold:
            analysis["optimization_opportunities"].append("accuracy_optimization")

        execution_time_threshold = self._get_intelligent_optimization_param("execution_time_threshold")
        if performance_metrics.get("execution_time", config.DEFAULT_ZERO_VALUE) > execution_time_threshold:
            analysis["optimization_opportunities"].append("speed_optimization")

        return analysis

    def _get_dynamic_min_length(self) -> int:
        """获取动态最小长度"""
        from src.utils.unified_intelligent_center import get_unified_intelligent_center
        learning_system = get_unified_intelligent_center()

        if learning_system:
            length_params = learning_system.get_learned_keywords("min_length_params")
            if length_params and isinstance(length_params, dict):
                def safe_int(value, default):
                    if isinstance(value, (int, float)):
                        return int(value)
                    elif isinstance(value, set):
                        return len(value)
                    else:
                        return default

                return safe_int(length_params.get("min_length"), config.DEFAULT_TOP_K)
            else:
                return self._get_dynamic_limit("default")  # 使用动态配置值
        else:
            return self._get_dynamic_limit("default")  # 使用动态配置值

    def _get_dynamic_limit(self, context: str) -> int:
        """获取动态限制值"""
        try:
            if context == "default":
                return get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
            elif context == "high":
                return 200
            elif context == "low":
                return 50
            else:
                return get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
        except Exception as e:
            logger.warning("获取动态限制值失败: {e}")
            return get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))

    def _get_intelligent_optimization_param(self, param_name: str) -> Any:
        """获取智能优化参数"""
        try:
            # 尝试使用统一依赖管理器获取配置
            from src.utils.unified_dependency_manager import get_dependency
            config_manager = get_dependency('unified_config_center')
            
            if config_manager and hasattr(config_manager, 'get_parameter'):
                param_value = config_manager.get_parameter(f"adaptive_optimization_{param_name}", None)
                if param_value is not None:
                    return param_value
            
            # 如果配置管理器不可用，使用默认值
            return self._get_default_optimization_param(param_name)
            
        except Exception as e:
            logger.warning(f"获取智能优化参数失败: {e}，使用默认值")
            return self._get_default_optimization_param(param_name)

    def _get_default_optimization_param(self, param_name: str) -> Any:
        """获取默认优化参数（回退值）"""
        default_params = {
            "learning_rate": config.DEFAULT_LOW_DECIMAL_THRESHOLD,
            "adaptation_threshold": config.DEFAULT_LOW_THRESHOLD,
            "max_iterations": config.DEFAULT_LIMIT,
            "convergence_threshold": config.DEFAULT_MINIMUM_THRESHOLD,
            "accuracy_bottleneck_threshold": config.DEFAULT_HIGH_MEDIUM_THRESHOLD,
            "success_rate_bottleneck_threshold": config.DEFAULT_HIGH_THRESHOLD,
            "accuracy_optimization_threshold": config.DEFAULT_NEAR_MAX_THRESHOLD,
            "execution_time_threshold": 5.0
        }
        return default_params.get(param_name, get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))

    def _get_current_optimization_context(self) -> Dict[str, Any]:
        """获取当前优化上下文"""
        return {
            "processor_type": "adaptive_parameter_optimizer",
            "current_algorithm": "general"
        }

    async def _bayesian_optimization(
        self, algorithm_name: str, performance_analysis: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int, bool]:
        """贝叶斯优化"""
        logger.info("使用贝叶斯优化算法: {algorithm_name}")

        param_ranges = self._get_parameter_ranges(algorithm_name)
        if not param_ranges:
            return {}, 0, False

        best_params = {}
        best_score = -float('inf')
        iterations = config.DEFAULT_ZERO_VALUE
        convergence = False

        for i in range(self.max_iterations):
            candidate_params = await self._generate_bayesian_candidates(
                param_ranges, best_params, best_score
            )

            score = await self._evaluate_parameters(candidate_params, algorithm_name)

            if score > best_score:
                best_params = candidate_params.copy()
                best_score = score

                if i > self._get_dynamic_min_length() and abs(score - best_score) < self.convergence_threshold:
                    convergence = True
                    break

            iterations = i + 1

        return best_params, iterations, convergence

    async def _genetic_optimization(
        self, algorithm_name: str, performance_analysis: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int, bool]:
        """遗传算法优化"""
        logger.info("使用遗传算法优化: {algorithm_name}")

        param_ranges = self._get_parameter_ranges(algorithm_name)
        if not param_ranges:
            return {}, 0, False

        population_size = 20
        population = await self._initialize_population(param_ranges, population_size)

        best_params = {}
        best_score = -float('inf')
        generations = config.DEFAULT_ZERO_VALUE
        convergence = False

        for generation in range(self.max_iterations // config.DEFAULT_TOP_K):  # 每代10次评估
            fitness_scores = []
            for individual in population:
                score = await self._evaluate_parameters(individual, algorithm_name)
                fitness_scores.append(score)

                if score > best_score:
                    best_params = individual.copy()
                    best_score = score

            selected = await self._genetic_selection(population, fitness_scores)

            offspring = await self._genetic_crossover(selected)

            mutated = await self._genetic_mutation(offspring, param_ranges)

            population = mutated

            generations = generation + config.DEFAULT_ONE_VALUE

            if generation > config.DEFAULT_SMALL_LIMIT and max(fitness_scores) - min(fitness_scores) < self.convergence_threshold:
                convergence = True
                break

        return best_params, generations, convergence

    async def _reinforcement_optimization(
        self, algorithm_name: str, performance_analysis: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int, bool]:
        """强化学习优化"""
        logger.info("使用强化学习优化: {algorithm_name}")

        param_ranges = self._get_parameter_ranges(algorithm_name)
        if not param_ranges:
            return {}, 0, False

        q_table = defaultdict(lambda: defaultdict(float))

        epsilon = config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE
        epsilon_decay = config.DEFAULT_NEAR_ONE5
        best_params = {}
        best_score = -float('inf')
        iterations = config.DEFAULT_ZERO_VALUE
        convergence = False

        for i in range(self.max_iterations):
            if random.random() < epsilon:
                current_params = await self._random_parameters(param_ranges)
            else:
                current_params = await self._select_best_action(dict(q_table), param_ranges)

            reward = await self._evaluate_parameters(current_params, algorithm_name)

            state = self._encode_state(current_params)
            q_table[state][str(current_params)] = reward

            if reward > best_score:
                best_params = current_params.copy()
                best_score = reward

            epsilon *= epsilon_decay

            iterations = i + config.DEFAULT_ONE_VALUE

            if i > config.DEFAULT_MEDIUM_LIMIT and epsilon < config.DEFAULT_LOW_DECIMAL_THRESHOLD:
                convergence = True
                break

        return best_params, iterations, convergence

    async def _gradient_optimization(
        self, algorithm_name: str, performance_analysis: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int, bool]:
        """梯度优化"""
        logger.info("使用梯度优化: {algorithm_name}")

        param_ranges = self._get_parameter_ranges(algorithm_name)
        if not param_ranges:
            return {}, 0, False

        current_params = {name: range_obj.current_value or get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")) for name, range_obj in param_ranges.items()}
        learning_rate = self.learning_rate

        best_params = current_params.copy()
        best_score = await self._evaluate_parameters(current_params, algorithm_name)
        iterations = config.DEFAULT_ZERO_VALUE
        convergence = False

        for i in range(self.max_iterations):
            gradients = {}

            for param_name, param_range in param_ranges.items():
                current_value = current_params[param_name] or config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE

                forward_params = current_params.copy()
                forward_params[param_name] = current_value + param_range.step_size
                forward_score = await self._evaluate_parameters(forward_params, algorithm_name)

                backward_params = current_params.copy()
                backward_params[param_name] = current_value - param_range.step_size
                backward_score = await self._evaluate_parameters(backward_params, algorithm_name)

                gradient = (forward_score - backward_score) / (config.DEFAULT_TWO_VALUE * param_range.step_size)
                gradients[param_name] = gradient

            for param_name, gradient in gradients.items():
                param_range = param_ranges[param_name]
                current_value = current_params[param_name] or config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
                new_value = current_value - learning_rate * gradient
                new_value = max(param_range.min_value, min(param_range.max_value, new_value))
                current_params[param_name] = new_value

            current_score = await self._evaluate_parameters(current_params, algorithm_name)

            if current_score > best_score:
                best_params = current_params.copy()
                best_score = current_score

            iterations = i + config.DEFAULT_ONE_VALUE

            if i > self._get_dynamic_min_length() and abs(current_score - best_score) < self.convergence_threshold:
                convergence = True
                break

        return best_params, iterations, convergence

    async def _random_search_optimization(
        self, algorithm_name: str, performance_analysis: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int, bool]:
        """随机搜索优化"""
        logger.info("使用随机搜索优化: {algorithm_name}")

        param_ranges = self._get_parameter_ranges(algorithm_name)
        if not param_ranges:
            return {}, 0, False

        best_params = {}
        best_score = -float('inf')
        iterations = 0

        for i in range(self.max_iterations):
            random_params = await self._random_parameters(param_ranges)

            score = await self._evaluate_parameters(random_params, algorithm_name)

            if score > best_score:
                best_params = random_params.copy()
                best_score = score

            iterations = i + 1

        return best_params, iterations, True

    def _get_parameter_ranges(self, algorithm_name: str) -> Dict[str, ParameterRange]:
        """获取参数范围"""
        default_ranges = {
            "knowledge_retrieval": {
                "max_iterations": ParameterRange(5, config.DEFAULT_DISPLAY_LIMIT, config.DEFAULT_ONE_VALUE),
                "min_relevance": ParameterRange(config.DEFAULT_VERY_LOW_THRESHOLD, config.DEFAULT_ZERO_VALUE.config.DEFAULT_TWO_VALUE, config.DEFAULT_VERY_LOW_THRESHOLD),
                "top_k": ParameterRange(config.DEFAULT_TOP_K, config.DEFAULT_TEXT_LIMIT, 5)
            },
            "reasoning": {
                "max_steps": ParameterRange(5, config.DEFAULT_MEDIUM_LIMIT, config.DEFAULT_ONE_VALUE),
                "confidence_threshold": ParameterRange(config.DEFAULT_LOW_DECIMAL_THRESHOLD, config.DEFAULT_NEAR_MAX_THRESHOLD, config.DEFAULT_LOW_THRESHOLD),
                "temperature": ParameterRange(config.DEFAULT_LOW_DECIMAL_THRESHOLD, config.DEFAULT_NEAR_MAX_THRESHOLD, config.DEFAULT_LOW_DECIMAL_THRESHOLD)
            },
            "analysis": {
                "max_insights": ParameterRange(5, config.DEFAULT_MEDIUM_LIMIT, config.DEFAULT_ONE_VALUE),
                "min_confidence": ParameterRange(config.DEFAULT_ZERO_VALUE.config.DEFAULT_MAX_RETRIES, config.DEFAULT_HIGH_THRESHOLD, config.DEFAULT_LOW_THRESHOLD),
                "depth_limit": ParameterRange(config.DEFAULT_MAX_RETRIES, config.DEFAULT_TOP_K, config.DEFAULT_ONE_VALUE)
            },
            "citation": {
                "max_sources": ParameterRange(5, config.DEFAULT_MEDIUM_LIMIT, config.DEFAULT_ONE_VALUE),
                "min_reliability": ParameterRange(config.DEFAULT_MEDIUM_LOW_THRESHOLD, config.DEFAULT_NEAR_MAX_THRESHOLD, config.DEFAULT_LOW_THRESHOLD),
                "format_weight": ParameterRange(config.DEFAULT_LOW_DECIMAL_THRESHOLD, config.DEFAULT_ZERO_VALUE.5, config.DEFAULT_LOW_THRESHOLD)
            }
        }

        return default_ranges.get(algorithm_name, {})

    async def _generate_bayesian_candidates(
        self, param_ranges: Dict[str, ParameterRange],
        best_params: Dict[str, Any], best_score: float
    ) -> Dict[str, Any]:
        """生成贝叶斯优化候选参数"""
        candidates = {}

        for param_name, param_range in param_ranges.items():
            if param_name in best_params:
                current_value = best_params[param_name]
                noise = random.gauss(config.DEFAULT_ZERO_VALUE, param_range.step_size * config.DEFAULT_TWO_VALUE)
                candidate_value = current_value + noise
            else:
                candidate_value = random.uniform(param_range.min_value, param_range.max_value)

            candidate_value = max(param_range.min_value, min(param_range.max_value, candidate_value))
            candidates[param_name] = candidate_value

        return candidates

    async def _evaluate_parameters(self, parameters: Dict[str, Any], algorithm_name: str) -> float:
        """评估参数性能"""

        score = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE

        if "max_iterations" in parameters:
            score += min(parameters["max_iterations"] / config.DEFAULT_DISPLAY_LIMIT.config.DEFAULT_ZERO_VALUE, config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE) * config.DEFAULT_LOW_MEDIUM_THRESHOLD

        if "min_relevance" in parameters:
            score += (config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE - parameters["min_relevance"]) * config.DEFAULT_ZERO_VALUE.config.DEFAULT_TWO_VALUE

        if "confidence_threshold" in parameters:
            score += parameters["confidence_threshold"] * config.DEFAULT_LOW_MEDIUM_THRESHOLD

        score += random.gauss(0, config.DEFAULT_LOW_DECIMAL_THRESHOLD)

        return max(get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), score))

    async def _validate_parameters(self, parameters: Dict[str, Any], algorithm_name: str) -> Dict[str, Any]:
        """验证参数有效性"""
        validated_params = {}
        param_ranges = self._get_parameter_ranges(algorithm_name)

        for param_name, value in parameters.items():
            if param_name in param_ranges:
                param_range = param_ranges[param_name]
                validated_value = max(param_range.min_value, min(param_range.max_value, value))
                validated_params[param_name] = validated_value
            else:
                validated_params[param_name] = value

        return validated_params

    async def _apply_and_monitor_parameters(self, parameters: Dict[str, Any],
    algorithm_name: str) -> PerformanceMetrics:  # noqa: E501
        """应用参数并监控效果"""

        metrics = PerformanceMetrics(
            accuracy=self._get_intelligent_performance_score("accuracy"),
            execution_time=self._get_intelligent_performance_score("execution_time"),
            success_rate=self._get_intelligent_performance_score("success_rate"),
            efficiency=self._get_intelligent_performance_score("efficiency"),
            quality_score=self._get_intelligent_performance_score("quality_score")
        )

        self.performance_metrics[algorithm_name].append(metrics)

        return metrics

    async def _calculate_improvement(
        self, original_metrics: Dict[str, float], new_metrics: PerformanceMetrics
    ) -> float:
        """计算改进程度"""
        improvement = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE

        if "accuracy" in original_metrics:
            accuracy_improvement = new_metrics.accuracy - original_metrics["accuracy"]
            improvement += accuracy_improvement * config.DEFAULT_MEDIUM_LOW_THRESHOLD

        if "execution_time" in original_metrics:
            time_improvement = original_metrics["execution_time"] - new_metrics.execution_time
            improvement += time_improvement * config.DEFAULT_LOW_MEDIUM_THRESHOLD

        if "success_rate" in original_metrics:
            success_improvement = new_metrics.success_rate - original_metrics["success_rate"]
            improvement += success_improvement * config.DEFAULT_LOW_MEDIUM_THRESHOLD

        return improvement

    async def _initialize_population(
        self, param_ranges: Dict[str, ParameterRange], population_size: int
    ) -> List[Dict[str, Any]]:
        """初始化遗传算法种群"""
        population = []

        for _ in range(population_size):
            individual = await self._random_parameters(param_ranges)
            population.append(individual)

        return population

    async def _random_parameters(self, param_ranges: Dict[str, ParameterRange]) -> Dict[str, Any]:
        """生成随机参数"""
        params = {}

        for param_name, param_range in param_ranges.items():
            value = random.uniform(param_range.min_value, param_range.max_value)
            params[param_name] = value

        return params

    async def _genetic_selection(
        self, population: List[Dict[str, Any]], fitness_scores: List[float]
    ) -> List[Dict[str, Any]]:
        """遗传算法选择"""
        total_fitness = sum(max(0, score) for score in fitness_scores)
        if total_fitness == 0:
            return population

        selected = []
        for _ in range(len(population)):
            r = random.uniform(0, total_fitness)
            cumulative = 0
            for i, score in enumerate(fitness_scores):
                cumulative += max(config.DEFAULT_ZERO_VALUE, score)
                if cumulative >= r:
                    selected.append(population[i])
                    break

        return selected

    async def _genetic_crossover(self, selected: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """遗传算法交叉"""
        offspring = []

        for i in range(0, len(selected), 2):
            if i + config.DEFAULT_ONE_VALUE < len(selected):
                parent1 = selected[i]
                parent2 = selected[i + 1]

                crossover_point = random.randint(1, len(parent1) - 1)
                child1 = {**parent1}
                child2 = {**parent2}

                keys = list(parent1.keys())
                for j in range(crossover_point, len(keys)):
                    key = keys[j]
                    child1[key], child2[key] = child2[key], child1[key]

                offspring.extend([childconfig.DEFAULT_ONE_VALUE, childconfig.DEFAULT_TWO_VALUE])
            else:
                offspring.append(selected[i])

        return offspring

    async def _genetic_mutation(
        self, offspring: List[Dict[str, Any]], param_ranges: Dict[str, ParameterRange]
    ) -> List[Dict[str, Any]]:
        """遗传算法变异"""
        mutation_rate = config.DEFAULT_LOW_DECIMAL_THRESHOLD

        for individual in offspring:
            for param_name, param_range in param_ranges.items():
                if random.random() < mutation_rate:
                    mutation = random.gauss(config.DEFAULT_ZERO_VALUE, param_range.step_size * config.DEFAULT_TWO_VALUE)
                    individual[param_name] += mutation
                    individual[param_name] = max(param_range.min_value, min(param_range.max_value,
    individual[param_name]))  # noqa: E501

        return offspring

    def _encode_state(self, parameters: Dict[str, Any]) -> str:
        """编码状态"""
        return json.dumps(parameters, sort_keys=True)

    async def _select_best_action(self, q_table: Dict[str, Dict[str, float]], param_ranges: Dict[str,
    ParameterRange]) -> Dict[str, Any]:  # noqa: E501
        """选择最佳动作"""
        return await self._random_parameters(param_ranges)

    def get_optimization_history(self, algorithm_name: Optional[str] = None) -> List[OptimizationResult]:
        """获取优化历史"""
        if algorithm_name:
            return [result for result in self.optimization_history if result.algorithm_name == algorithm_name]
        return self.optimization_history

    def get_best_parameters(self, algorithm_name: str) -> Dict[str, Any]:
        """获取最佳参数"""
        history = self.get_optimization_history(algorithm_name)
        if not history:
            return {}

        best_result = max(history, key=lambda x: x.improvement)
        return best_result.optimal_parameters
    def _get_intelligent_performance_score(self, score_type: str) -> float:
        """使用统一智能中心获取性能评分"""
        try:
            from src.utils.unified_intelligent_center import get_unified_intelligent_center
            intelligent_center = get_unified_intelligent_center()
            
            # 使用统一智能中心进行性能分析
            analysis = intelligent_center.perform_universal_intelligent_extraction(score_type, "performance_analysis")
            if analysis and 'performance_score' in analysis:
                return analysis['performance_score']
            
            # 回退到历史数据分析
            if hasattr(self, 'optimization_history') and self.optimization_history:
                recent_performance = self.optimization_history[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]
                
                if score_type == "accuracy":
                    scores = [p.improvement for p in recent_performance if hasattr(p, 'improvement')]
                elif score_type == "execution_time":
                    scores = [p.execution_time for p in recent_performance if hasattr(p, 'execution_time')]
                elif score_type == "success_rate":
                    scores = [get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")) if p.improvement > config.DEFAULT_ZERO_VALUE else get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")) for p in recent_performance if hasattr(p, 'improvement')]
                elif score_type == "efficiency":
                    scores = [p.improvement / max(p.execution_time, get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))) for p in recent_performance if hasattr(p, 'execution_time') and hasattr(p, 'improvement')]
                elif score_type == "quality_score":
                    scores = [p.improvement for p in recent_performance if hasattr(p, 'improvement')]
                else:
                    return config.DEFAULT_THREE_QUARTER_THRESHOLD
                
                if scores:
                    return sum(scores) / len(scores)
            
            # 最终回退值
            default_scores = {
                "accuracy": config.DEFAULT_THREE_QUARTER_THRESHOLD,
                "execution_time": 5.config.DEFAULT_ZERO_VALUE,
                "success_rate": config.DEFAULT_HIGH_CONFIDENCE_THRESHOLD,
                "efficiency": config.DEFAULT_THREE_QUARTER_THRESHOLD,
                "quality_score": config.DEFAULT_HIGH_THRESHOLD
            }
            return default_scores.get(score_type, config.DEFAULT_THREE_QUARTER_THRESHOLD)
        except Exception:
            return config.DEFAULT_THREE_QUARTER_THRESHOLD

adaptive_parameter_optimizer = AdaptiveParameterOptimizer()

def get_adaptive_parameter_optimizer() -> AdaptiveParameterOptimizer:
    """获取自适应参数优化器实例"""
    return adaptive_parameter_optimizer
