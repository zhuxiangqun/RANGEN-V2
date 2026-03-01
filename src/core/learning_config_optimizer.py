"""
学习型配置优化器 (Learning Configuration Optimizer)

基于机器学习和强化学习实现智能配置优化：
- 多维度配置参数学习
- 性能预测和优化
- 上下文感知配置调整
- 持续学习和改进
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import statistics
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class OptimizationTarget(Enum):
    """优化目标"""
    PERFORMANCE = "performance"      # 性能优化
    ACCURACY = "accuracy"           # 准确性优化
    EFFICIENCY = "efficiency"       # 效率优化
    STABILITY = "stability"         # 稳定性优化
    COST = "cost"                   # 成本优化


class LearningAlgorithm(Enum):
    """学习算法"""
    LINEAR_REGRESSION = "linear_regression"    # 线性回归
    RANDOM_FOREST = "random_forest"           # 随机森林
    GRADIENT_BOOSTING = "gradient_boosting"   # 梯度提升
    NEURAL_NETWORK = "neural_network"         # 神经网络
    REINFORCEMENT_LEARNING = "reinforcement"  # 强化学习


@dataclass
class ConfigurationParameter:
    """配置参数"""
    name: str
    value_type: str  # int, float, bool, enum
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enum_values: Optional[List[Any]] = None
    default_value: Any = None
    description: str = ""

    def validate_value(self, value: Any) -> bool:
        """验证参数值"""
        if self.value_type == "int":
            if not isinstance(value, int):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.value_type == "float":
            if not isinstance(value, (int, float)):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.value_type == "bool":
            if not isinstance(value, bool):
                return False
        elif self.value_type == "enum":
            if self.enum_values and value not in self.enum_values:
                return False

        return True


@dataclass
class ConfigurationProfile:
    """配置档案"""
    profile_id: str
    component_name: str
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    context_features: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    average_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'profile_id': self.profile_id,
            'component_name': self.component_name,
            'parameters': self.parameters,
            'performance_metrics': self.performance_metrics,
            'context_features': self.context_features,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count,
            'average_score': self.average_score
        }


@dataclass
class OptimizationResult:
    """优化结果"""
    target_component: str
    original_config: Dict[str, Any]
    optimized_config: Dict[str, Any]
    expected_improvement: Dict[str, float]
    confidence_level: float
    optimization_method: str
    reasoning: str
    applied_at: Optional[datetime] = None


@dataclass
class PerformanceFeedback:
    """性能反馈"""
    component_name: str
    configuration: Dict[str, Any]
    context: Dict[str, Any]
    performance_metrics: Dict[str, float]
    user_satisfaction: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    feedback_source: str = "system"  # system, user, benchmark


class ContextAnalyzer:
    """上下文分析器"""

    def __init__(self):
        self.context_patterns: Dict[str, Dict[str, Any]] = {}
        self.feature_importance: Dict[str, float] = {}

    def analyze_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析上下文特征"""
        features = {}

        # 任务特征
        if 'task_type' in context:
            features['task_complexity'] = self._assess_task_complexity(context)
            features['task_urgency'] = context.get('priority', 1) / 5.0  # 归一化

        # 系统状态特征
        if 'system_load' in context:
            features['system_load'] = context['system_load']

        # 用户特征
        if 'user_history' in context:
            features['user_experience'] = self._analyze_user_experience(context['user_history'])

        # 时间特征
        current_hour = datetime.now().hour
        features['time_of_day'] = current_hour / 24.0
        features['is_business_hours'] = 1.0 if 9 <= current_hour <= 17 else 0.0

        return features

    def _assess_task_complexity(self, context: Dict[str, Any]) -> float:
        """评估任务复杂度"""
        task_type = context.get('task_type', '')
        complexity_keywords = {
            'simple': 0.2,
            'analysis': 0.6,
            'complex': 0.8,
            'reasoning': 0.7,
            'generation': 0.5
        }

        for keyword, score in complexity_keywords.items():
            if keyword in task_type.lower():
                return score

        return 0.5  # 默认中等复杂度

    def _analyze_user_experience(self, user_history: List[Dict[str, Any]]) -> float:
        """分析用户经验水平"""
        if not user_history:
            return 0.5

        # 基于历史交互次数和成功率评估经验
        total_interactions = len(user_history)
        success_rate = sum(1 for h in user_history if h.get('success', False)) / total_interactions

        experience_score = min(total_interactions / 100.0, 1.0) * 0.6 + success_rate * 0.4
        return experience_score


class PerformancePredictor:
    """性能预测器"""

    def __init__(self):
        self.prediction_models: Dict[str, Any] = {}  # 简单的模型存储
        self.historical_data: Dict[str, List[Tuple[Dict[str, Any], Dict[str, float]]]] = defaultdict(list)

    def train_model(self, component_name: str, training_data: List[Tuple[Dict[str, Any], Dict[str, float]]]):
        """训练预测模型"""
        self.historical_data[component_name].extend(training_data)

        # 简单的线性模型训练（实际应该使用更复杂的ML算法）
        if len(training_data) >= 10:
            self._train_simple_linear_model(component_name)

    def predict_performance(self, component_name: str, config: Dict[str, Any],
                          context: Dict[str, Any]) -> Dict[str, float]:
        """预测性能"""
        if component_name not in self.prediction_models:
            return self._get_default_predictions(component_name)

        model = self.prediction_models[component_name]

        # 简单的预测逻辑（实际应该使用训练好的模型）
        base_predictions = self._get_base_predictions(component_name)

        # 根据配置调整预测
        config_adjustments = self._calculate_config_adjustments(config, component_name)
        context_adjustments = self._calculate_context_adjustments(context, component_name)

        predictions = {}
        for metric, base_value in base_predictions.items():
            adjustment = config_adjustments.get(metric, 0) + context_adjustments.get(metric, 0)
            predictions[metric] = max(0.0, min(1.0, base_value + adjustment))

        return predictions

    def _train_simple_linear_model(self, component_name: str):
        """训练简单的线性模型"""
        # 这里应该实现实际的ML训练逻辑
        # 暂时只是存储模型占位符
        self.prediction_models[component_name] = {
            'trained_at': datetime.now(),
            'data_points': len(self.historical_data[component_name])
        }

    def _get_default_predictions(self, component_name: str) -> Dict[str, float]:
        """获取默认预测"""
        defaults = {
            'response_time': 0.5,
            'accuracy': 0.7,
            'efficiency': 0.6,
            'stability': 0.8
        }
        return defaults

    def _get_base_predictions(self, component_name: str) -> Dict[str, float]:
        """获取基础预测"""
        # 基于组件类型返回不同的基础预测
        if 'reasoning' in component_name.lower():
            return {'response_time': 0.7, 'accuracy': 0.8, 'efficiency': 0.5, 'stability': 0.9}
        elif 'knowledge' in component_name.lower():
            return {'response_time': 0.4, 'accuracy': 0.9, 'efficiency': 0.8, 'stability': 0.9}
        elif 'generation' in component_name.lower():
            return {'response_time': 0.6, 'accuracy': 0.7, 'efficiency': 0.6, 'stability': 0.8}
        else:
            return self._get_default_predictions(component_name)

    def _calculate_config_adjustments(self, config: Dict[str, Any], component_name: str) -> Dict[str, float]:
        """计算配置调整"""
        adjustments = {}

        # 基于配置参数调整预测
        if 'timeout' in config:
            timeout = config['timeout']
            if timeout < 30:
                adjustments['response_time'] = -0.2  # 更快的响应
                adjustments['accuracy'] = -0.1     # 可能牺牲准确性
            elif timeout > 120:
                adjustments['response_time'] = 0.2  # 更慢的响应
                adjustments['accuracy'] = 0.1       # 更高的准确性

        if 'parallel_execution' in config and config['parallel_execution']:
            adjustments['efficiency'] = 0.2
            adjustments['response_time'] = -0.1

        return adjustments

    def _calculate_context_adjustments(self, context: Dict[str, Any], component_name: str) -> Dict[str, float]:
        """计算上下文调整"""
        adjustments = {}

        # 基于上下文调整预测
        if context.get('system_load', 0) > 0.8:
            adjustments['response_time'] = 0.3
            adjustments['efficiency'] = -0.2

        if context.get('task_complexity', 0.5) > 0.7:
            adjustments['response_time'] = 0.2
            adjustments['accuracy'] = 0.1

        return adjustments


class ConfigurationOptimizer:
    """配置优化器"""

    def __init__(self, predictor: PerformancePredictor):
        self.predictor = predictor
        self.optimization_history: List[OptimizationResult] = []
        self.parameter_definitions: Dict[str, Dict[str, ConfigurationParameter]] = {}

    def define_parameters(self, component_name: str, parameters: Dict[str, ConfigurationParameter]):
        """定义组件参数"""
        self.parameter_definitions[component_name] = parameters

    async def optimize_configuration(self, component_name: str,
                                   current_config: Dict[str, Any],
                                   context: Dict[str, Any],
                                   optimization_target: OptimizationTarget = OptimizationTarget.PERFORMANCE
                                   ) -> OptimizationResult:
        """优化配置"""
        # 获取参数定义
        param_defs = self.parameter_definitions.get(component_name, {})

        # 生成候选配置
        candidates = self._generate_candidate_configs(current_config, param_defs)

        # 评估候选配置
        best_config, best_score, reasoning = await self._evaluate_candidates(
            component_name, candidates, context, optimization_target
        )

        # 计算预期改进
        current_predictions = self.predictor.predict_performance(component_name, current_config, context)
        optimized_predictions = self.predictor.predict_performance(component_name, best_config, context)

        expected_improvement = {}
        for metric in current_predictions:
            if metric in optimized_predictions:
                improvement = optimized_predictions[metric] - current_predictions[metric]
                expected_improvement[metric] = improvement

        result = OptimizationResult(
            target_component=component_name,
            original_config=current_config,
            optimized_config=best_config,
            expected_improvement=expected_improvement,
            confidence_level=best_score,
            optimization_method="predictive_optimization",
            reasoning=reasoning
        )

        self.optimization_history.append(result)
        return result

    def _generate_candidate_configs(self, current_config: Dict[str, Any],
                                  param_defs: Dict[str, ConfigurationParameter],
                                  num_candidates: int = 10) -> List[Dict[str, Any]]:
        """生成候选配置"""
        candidates = [current_config.copy()]  # 包含当前配置

        for _ in range(num_candidates - 1):
            candidate = current_config.copy()

            # 随机调整参数
            for param_name, param_def in param_defs.items():
                if random.random() < 0.3:  # 30%概率调整参数
                    candidate[param_name] = self._randomize_parameter_value(param_def)

            candidates.append(candidate)

        return candidates

    def _randomize_parameter_value(self, param_def: ConfigurationParameter) -> Any:
        """随机化参数值"""
        if param_def.value_type == "bool":
            return random.choice([True, False])
        elif param_def.value_type == "int":
            min_val = param_def.min_value or 0
            max_val = param_def.max_value or 100
            return random.randint(int(min_val), int(max_val))
        elif param_def.value_type == "float":
            min_val = param_def.min_value or 0.0
            max_val = param_def.max_value or 1.0
            return random.uniform(min_val, max_val)
        elif param_def.value_type == "enum" and param_def.enum_values:
            return random.choice(param_def.enum_values)
        else:
            return param_def.default_value

    async def _evaluate_candidates(self, component_name: str,
                                 candidates: List[Dict[str, Any]],
                                 context: Dict[str, Any],
                                 target: OptimizationTarget) -> Tuple[Dict[str, Any], float, str]:
        """评估候选配置"""
        best_config = candidates[0]
        best_score = 0.0
        best_reasoning = "默认配置"

        for config in candidates:
            predictions = self.predictor.predict_performance(component_name, config, context)

            # 根据优化目标计算评分
            score = self._calculate_optimization_score(predictions, target)

            if score > best_score:
                best_score = score
                best_config = config
                best_reasoning = self._generate_reasoning(config, predictions, target)

        return best_config, best_score, best_reasoning

    def _calculate_optimization_score(self, predictions: Dict[str, float],
                                    target: OptimizationTarget) -> float:
        """计算优化评分"""
        if target == OptimizationTarget.PERFORMANCE:
            # 性能优化：平衡响应时间和准确性
            return (predictions.get('accuracy', 0.7) * 0.6 +
                   (1 - predictions.get('response_time', 0.5)) * 0.4)
        elif target == OptimizationTarget.ACCURACY:
            return predictions.get('accuracy', 0.7)
        elif target == OptimizationTarget.EFFICIENCY:
            return predictions.get('efficiency', 0.6)
        elif target == OptimizationTarget.STABILITY:
            return predictions.get('stability', 0.8)
        else:
            return statistics.mean(predictions.values())

    def _generate_reasoning(self, config: Dict[str, Any],
                          predictions: Dict[str, float],
                          target: OptimizationTarget) -> str:
        """生成优化推理说明"""
        reasoning_parts = []

        if 'timeout' in config:
            reasoning_parts.append(f"timeout设置为{config['timeout']}秒")

        if 'parallel_execution' in config:
            if config['parallel_execution']:
                reasoning_parts.append("启用并行执行")
            else:
                reasoning_parts.append("使用串行执行")

        if predictions:
            top_metrics = sorted(predictions.items(), key=lambda x: x[1], reverse=True)[:2]
            reasoning_parts.append(f"预期最佳指标: {', '.join(f'{k}={v:.2f}' for k, v in top_metrics)}")

        return "; ".join(reasoning_parts)


class LearningConfigurationOptimizer:
    """
    学习型配置优化器

    基于机器学习和历史数据的智能配置优化系统：
    - 上下文感知配置推荐
    - 性能预测和优化
    - 持续学习改进
    - 多目标优化支持
    """

    def __init__(self):
        self.context_analyzer = ContextAnalyzer()
        self.performance_predictor = PerformancePredictor()
        self.config_optimizer = ConfigurationOptimizer(self.performance_predictor)

        self.configuration_profiles: Dict[str, List[ConfigurationProfile]] = defaultdict(list)
        self.feedback_history: List[PerformanceFeedback] = []

        # 学习参数
        self.learning_rate = 0.1
        self.min_samples_for_learning = 5

    async def optimize_component_config(self, component_name: str,
                                      current_config: Dict[str, Any],
                                      context: Dict[str, Any],
                                      optimization_target: OptimizationTarget = OptimizationTarget.PERFORMANCE
                                      ) -> OptimizationResult:
        """优化组件配置"""
        # 分析上下文
        context_features = self.context_analyzer.analyze_context(context)

        # 查找相似配置档案
        similar_profiles = self._find_similar_profiles(component_name, context_features)

        # 如果有足够的相似档案，使用学习结果
        if len(similar_profiles) >= self.min_samples_for_learning:
            optimized_result = await self._optimize_from_profiles(
                component_name, current_config, similar_profiles, context_features, optimization_target
            )
        else:
            # 否则使用预测优化
            optimized_result = await self.config_optimizer.optimize_configuration(
                component_name, current_config, context_features, optimization_target
            )

        return optimized_result

    async def record_performance_feedback(self, feedback: PerformanceFeedback):
        """记录性能反馈"""
        self.feedback_history.append(feedback)

        # 更新配置档案
        await self._update_configuration_profiles(feedback)

        # 训练预测模型
        await self._train_prediction_models(feedback.component_name)

    async def get_recommended_configurations(self, component_name: str,
                                           context: Dict[str, Any],
                                           limit: int = 5) -> List[ConfigurationProfile]:
        """获取推荐配置"""
        context_features = self.context_analyzer.analyze_context(context)

        # 查找匹配的配置档案
        profiles = self.configuration_profiles.get(component_name, [])

        # 按相似度和性能排序
        scored_profiles = []
        for profile in profiles:
            similarity_score = self._calculate_profile_similarity(profile, context_features)
            performance_score = profile.average_score
            combined_score = similarity_score * 0.6 + performance_score * 0.4
            scored_profiles.append((profile, combined_score))

        # 返回前N个推荐
        scored_profiles.sort(key=lambda x: x[1], reverse=True)
        return [profile for profile, _ in scored_profiles[:limit]]

    def define_component_parameters(self, component_name: str,
                                  parameters: Dict[str, ConfigurationParameter]):
        """定义组件参数"""
        self.config_optimizer.define_parameters(component_name, parameters)

    async def _optimize_from_profiles(self, component_name: str,
                                    current_config: Dict[str, Any],
                                    similar_profiles: List[ConfigurationProfile],
                                    context_features: Dict[str, Any],
                                    target: OptimizationTarget) -> OptimizationResult:
        """基于配置档案优化"""
        # 分析成功配置的共同特征
        successful_configs = [p for p in similar_profiles if p.average_score > 0.7]

        if not successful_configs:
            # 没有成功的配置，回退到预测优化
            return await self.config_optimizer.optimize_configuration(
                component_name, current_config, context_features, target
            )

        # 生成优化配置
        optimized_config = self._synthesize_optimal_config(successful_configs, current_config)

        # 预测性能改进
        current_predictions = self.performance_predictor.predict_performance(
            component_name, current_config, context_features
        )
        optimized_predictions = self.performance_predictor.predict_performance(
            component_name, optimized_config, context_features
        )

        expected_improvement = {}
        for metric in current_predictions:
            if metric in optimized_predictions:
                improvement = optimized_predictions[metric] - current_predictions[metric]
                expected_improvement[metric] = improvement

        return OptimizationResult(
            target_component=component_name,
            original_config=current_config,
            optimized_config=optimized_config,
            expected_improvement=expected_improvement,
            confidence_level=0.8,  # 基于历史数据
            optimization_method="profile_based_optimization",
            reasoning=f"基于{len(successful_configs)}个相似成功配置优化"
        )

    def _find_similar_profiles(self, component_name: str,
                             context_features: Dict[str, Any]) -> List[ConfigurationProfile]:
        """查找相似配置档案"""
        profiles = self.configuration_profiles.get(component_name, [])

        similar_profiles = []
        for profile in profiles:
            similarity = self._calculate_profile_similarity(profile, context_features)
            if similarity > 0.6:  # 相似度阈值
                similar_profiles.append(profile)

        return similar_profiles

    def _calculate_profile_similarity(self, profile: ConfigurationProfile,
                                    context_features: Dict[str, Any]) -> float:
        """计算配置档案相似度"""
        if not profile.context_features:
            return 0.5  # 默认相似度

        # 计算上下文特征相似度
        total_features = len(context_features)
        if total_features == 0:
            return 0.5

        matching_features = 0
        for key, value in context_features.items():
            if key in profile.context_features:
                profile_value = profile.context_features[key]
                # 简单的数值相似度计算
                if isinstance(value, (int, float)) and isinstance(profile_value, (int, float)):
                    diff = abs(value - profile_value)
                    if diff < 0.2:  # 差异小于20%
                        matching_features += 1
                elif value == profile_value:
                    matching_features += 1

        return matching_features / total_features

    def _synthesize_optimal_config(self, successful_profiles: List[ConfigurationProfile],
                                 current_config: Dict[str, Any]) -> Dict[str, Any]:
        """合成最优配置"""
        optimized_config = current_config.copy()

        # 统计各参数的成功值
        param_stats = defaultdict(list)

        for profile in successful_profiles:
            for param_name, param_value in profile.parameters.items():
                param_stats[param_name].append((param_value, profile.average_score))

        # 为每个参数选择最优值
        for param_name, value_score_pairs in param_stats.items():
            if value_score_pairs:
                # 选择得分最高的参数值
                best_value, _ = max(value_score_pairs, key=lambda x: x[1])
                optimized_config[param_name] = best_value

        return optimized_config

    async def _update_configuration_profiles(self, feedback: PerformanceFeedback):
        """更新配置档案"""
        # 查找或创建配置档案
        profile_id = f"{feedback.component_name}_{hash(json.dumps(feedback.configuration, sort_keys=True))}"
        profile = None

        for p in self.configuration_profiles[feedback.component_name]:
            if p.profile_id == profile_id:
                profile = p
                break

        if not profile:
            profile = ConfigurationProfile(
                profile_id=profile_id,
                component_name=feedback.component_name,
                parameters=feedback.configuration.copy(),
                context_features=feedback.context.copy()
            )
            self.configuration_profiles[feedback.component_name].append(profile)

        # 更新档案统计
        profile.usage_count += 1
        profile.performance_metrics.update(feedback.performance_metrics)

        # 更新平均得分（使用指数移动平均）
        new_score = statistics.mean(feedback.performance_metrics.values())
        profile.average_score = (
            profile.average_score * (1 - self.learning_rate) +
            new_score * self.learning_rate
        )

    async def _train_prediction_models(self, component_name: str):
        """训练预测模型"""
        # 收集训练数据
        training_data = []

        for feedback in self.feedback_history[-100:]:  # 使用最近100个反馈
            if feedback.component_name == component_name:
                features = self.context_analyzer.analyze_context(feedback.context)
                targets = feedback.performance_metrics
                training_data.append((features, targets))

        if len(training_data) >= self.min_samples_for_learning:
            self.performance_predictor.train_model(component_name, training_data)

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        total_optimizations = len(self.config_optimizer.optimization_history)
        total_feedbacks = len(self.feedback_history)

        component_stats = {}
        for component, profiles in self.configuration_profiles.items():
            component_stats[component] = {
                'profiles_count': len(profiles),
                'avg_performance': statistics.mean(p.average_score for p in profiles) if profiles else 0
            }

        return {
            'total_optimizations': total_optimizations,
            'total_feedbacks': total_feedbacks,
            'components_optimized': len(component_stats),
            'component_statistics': component_stats
        }


# 全局实例
_optimizer_instance: Optional[LearningConfigurationOptimizer] = None

def get_learning_config_optimizer() -> LearningConfigurationOptimizer:
    """获取学习型配置优化器实例"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = LearningConfigurationOptimizer()
    return _optimizer_instance
