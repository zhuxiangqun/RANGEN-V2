"""
机器学习参数优化器
提供智能的参数优化和动态调整功能
"""

import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import threading

logger = logging.getLogger(__name__)

@dataclass
class OptimizationSample:
    """优化样本数据"""
    parameter_values: Dict[str, Any]
    performance_metrics: Dict[str, float]
    context: Dict[str, Any]
    timestamp: float

@dataclass
class OptimizationResult:
    """优化结果"""
    optimal_parameters: Dict[str, Any]
    expected_performance: Dict[str, float]
    confidence_score: float
    optimization_method: str

class MLParameterOptimizer:
    """机器学习参数优化器"""

    def __init__(self):
        self.samples: List[OptimizationSample] = []
        self.models: Dict[str, LinearRegression] = {}
        self.scalers: Dict[str, StandardScaler] = {}
        self.lock = threading.RLock()
        self.min_samples_for_training = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))

    def add_sample(self, parameter_values: Dict[str, Any],
                   performance_metrics: Dict[str, float],
                   context: Optional[Dict[str, Any]] = None):
        """添加优化样本"""
        with self.lock:
            sample = OptimizationSample(
                parameter_values=parameter_values.copy(),
                performance_metrics=performance_metrics.copy(),
                context=context or {},
                timestamp=time.time()
            )
            self.samples.append(sample)

            # 限制样本数量
            if len(self.samples) > config.DEFAULT_LIMIT0:
                self.samples = self.samples[-config.DEFAULT_LIMIT0:]

            logger.debug(f"添加优化样本，当前样本数: {len(self.samples)}")

    def optimize_parameters(self, target_metric: str = 'accuracy',
                           parameter_keys: Optional[List[str]] = None) -> Optional[OptimizationResult]:
        """优化参数"""
        with self.lock:
            if len(self.samples) < self.min_samples_for_training:
                logger.info(f"样本数不足，需要至少{self.min_samples_for_training}个样本，当前: {len(self.samples)}")
                return None

            # 确定要优化的参数
            if parameter_keys is None:
                # 从样本中推断参数键
                parameter_keys = list(self.samples[config.DEFAULT_ZERO_VALUE].parameter_values.keys())

            # 准备训练数据
            X, y = self._prepare_training_data(target_metric, parameter_keys)

            if X is None or y is None:
                return None

            # 训练模型
            model_key = f"{target_metric}_{'_'.join(parameter_keys)}"
            if model_key not in self.models:
                self.models[model_key] = LinearRegression()
                self.scalers[model_key] = StandardScaler()

            # 标准化数据
            X_scaled = self.scalers[model_key].fit_transform(X)

            # 训练模型
            self.models[model_key].fit(X_scaled, y)

            # 找到最优参数
            optimal_params, expected_performance = self._find_optimal_parameters(
                model_key, parameter_keys, target_metric)

            if optimal_params:
                confidence = self._calculate_confidence_score(model_key, X_scaled, y)

                result = OptimizationResult(
                    optimal_parameters=optimal_params,
                    expected_performance={'accuracy': expected_performance},
                    confidence_score=confidence,
                    optimization_method='linear_regression'
                )

                logger.info(f"参数优化完成，预期性能: {expected_performance:.3f}")
                return result

        return None

    def _prepare_training_data(self, target_metric: str,
                              parameter_keys: List[str]) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """准备训练数据"""
        try:
            # 过滤有目标指标的样本
            valid_samples = [s for s in self.samples if target_metric in s.performance_metrics]

            if len(valid_samples) < self.min_samples_for_training:
                return None, None

            # 提取特征和标签
            X_data = []
            y_data = []

            for sample in valid_samples:
                # 提取参数值作为特征
                features = []
                for key in parameter_keys:
                    value = sample.parameter_values.get(key, config.DEFAULT_ZERO_VALUE)
                    # 转换为数值类型
                    if isinstance(value, (int, float)):
                        features.append(float(value))
                    elif isinstance(value, bool):
                        features.append(config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE if value else config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)
                    elif isinstance(value, str):
                        # 简单的字符串到数字映射
                        features.append(hash(value) % config.DEFAULT_LIMITconfig.DEFAULT_ZERO_VALUE / config.DEFAULT_LIMITconfig.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)
                    else:
                        features.append(config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)

                X_data.append(features)
                y_data.append(sample.performance_metrics[target_metric])

            return np.array(X_data), np.array(y_data)

        except Exception as e:
            logger.error(f"准备训练数据失败: {e}")
            return None, None

    def _find_optimal_parameters(self, model_key: str,
                                parameter_keys: List[str],
                                target_metric: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """找到最优参数"""
        try:
            model = self.models[model_key]
            scaler = self.scalers[model_key]

            # 生成候选参数组合
            candidates = self._generate_parameter_candidates(parameter_keys)

            best_score = -float('inf')
            best_params = None

            for params in candidates:
                # 转换为特征向量
                features = []
                for key in parameter_keys:
                    value = params.get(key, config.DEFAULT_ZERO_VALUE)
                    if isinstance(value, (int, float)):
                        features.append(float(value))
                    elif isinstance(value, bool):
                        features.append(config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE if value else config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)
                    elif isinstance(value, str):
                        features.append(hash(value) % config.DEFAULT_LIMITconfig.DEFAULT_ZERO_VALUE / config.DEFAULT_LIMITconfig.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)
                    else:
                        features.append(config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)

                # 预测性能
                X_pred = np.array([features])
                X_pred_scaled = scaler.transform(X_pred)
                predicted_score = model.predict(X_pred_scaled)[config.DEFAULT_ZERO_VALUE]

                if predicted_score > best_score:
                    best_score = predicted_score
                    best_params = params.copy()

            return best_params, best_score

        except Exception as e:
            logger.error(f"寻找最优参数失败: {e}")
            return None, get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

    def _generate_parameter_candidates(self, parameter_keys: List[str]) -> List[Dict[str, Any]]:
        """生成参数候选组合"""
        # 从历史样本中提取参数范围
        param_ranges = {}

        for key in parameter_keys:
            values = [s.parameter_values.get(key) for s in self.samples
                     if key in s.parameter_values]

            if values:
                # 根据数据类型确定候选值
                unique_values = list(set(values))
                if len(unique_values) <= get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
                    param_ranges[key] = unique_values
                else:
                    # 对于数值类型，生成范围内的值
                    if all(isinstance(v, (int, float)) for v in unique_values):
                        min_val = min(unique_values)
                        max_val = max(unique_values)
                        param_ranges[key] = np.linspace(min_val, max_val, 5).tolist()
                    else:
                        param_ranges[key] = unique_values[:config.DEFAULT_TOP_K]

        # 生成所有组合
        import itertools
        if param_ranges:
            keys = list(param_ranges.keys())
            values = [param_ranges[key] for key in keys]
            combinations = itertools.product(*values)

            candidates = []
            for combo in combinations:
                candidate = dict(zip(keys, combo))
                candidates.append(candidate)

            return candidates[:config.DEFAULT_DISPLAY_LIMIT]  # 限制候选数量

        return []

    def _calculate_confidence_score(self, model_key: str,
                                   X_scaled: np.ndarray,
                                   y: np.ndarray) -> float:
        """计算置信度分数"""
        try:
            model = self.models[model_key]
            predictions = model.predict(X_scaled)

            # 计算R²分数作为置信度
            ss_res = np.sum((y - predictions) ** config.DEFAULT_TWO_VALUE)
            ss_tot = np.sum((y - np.mean(y)) ** 2)

            if ss_tot == 0:
                return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

            r2_score = config.DEFAULT_ONE_VALUE - (ss_res / ss_tot)
            confidence = max(get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), (r2_score + 1) / 2))  # 归一化到[0,1]

            return confidence

        except Exception as e:
            logger.error(f"计算置信度失败: {e}")
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

    def get_optimization_suggestions(self, parameter_key: str) -> List[str]:
        """获取优化建议"""
        suggestions = []

        # 检查样本数量
        if len(self.samples) < self.min_samples_for_training:
            suggestions.append(f"需要更多样本，至少{self.min_samples_for_training}个，当前: {len(self.samples)}")

        # 检查参数变化
        param_values = [s.parameter_values.get(parameter_key) for s in self.samples
                       if parameter_key in s.parameter_values]

        if len(set(param_values)) < 3:
            suggestions.append(f"参数 {parameter_key} 变化不足，建议增加参数值范围")

        # 检查性能指标
        performance_values = [s.performance_metrics.get('accuracy', 0) for s in self.samples]
        if len(performance_values) > 0:
            performance_range = max(performance_values) - min(performance_values)
            if performance_range < config.DEFAULT_LOW_DECIMAL_THRESHOLD:
                suggestions.append("性能指标变化范围较小，建议增加测试场景多样性")

        return suggestions


# 全局实例
_ml_optimizer = None

def get_ml_parameter_optimizer() -> MLParameterOptimizer:
    """获取ML参数优化器实例"""
    global _ml_optimizer
    if _ml_optimizer is None:
        _ml_optimizer = MLParameterOptimizer()
    return _ml_optimizer
