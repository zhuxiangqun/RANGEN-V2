#!/usr/bin/env python3
"""
预测性配置管理器 - 阶段5: 实现预测性配置管理
基于时间序列分析和机器学习预测未来配置需求
"""

import time
import logging
import threading
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import math
import json

logger = logging.getLogger(__name__)

class TimeSeriesAnalyzer:
    """时间序列分析器"""
    
    def __init__(self, window_size: int = get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))):
        self.window_size = window_size
        self.time_series_data = defaultdict(lambda: deque(maxlen=window_size))
        self.patterns = {}
        self.seasonal_patterns = {}
        
    def add_data_point(self, metric_name: str, value: Any, timestamp: Optional[datetime] = None):
        """添加数据点"""
        
        if timestamp is None:
            timestamp = datetime.now()
        
        data_point = {
            'timestamp': timestamp,
            'value': value
        }
        
        self.time_series_data[metric_name].append(data_point)
    
    def get_recent_trend(self, metric_name: str, periods: int = get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))) -> str:
        """获取近期趋势"""
        
        data = list(self.time_series_data[metric_name])[-periods:]
        if len(data) < 3:
            return 'stable'
        
        values = [d['value'] for d in data]
        
        # 计算趋势
        if isinstance(values[0], (int, float)):
            # 数值型数据：计算斜率
            x = list(range(len(values)))
            slope = self._calculate_slope(x, values)
            
            if slope > 0.1:
                return 'increasing'
            elif slope < -0.1:
                return 'decreasing'
            else:
                return 'stable'
        else:
            # 类别型数据：计算变化频率
            changes = sum(1 for i in range(1, len(values)) if values[i] != values[i-1])
            change_rate = changes / (len(values) - 1)
            
            if change_rate > get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")):
                return 'volatile'
            elif change_rate > 0.2:
                return 'moderate'
            else:
                return 'stable'
    
    def _calculate_slope(self, x: List[float], y: List[float]) -> float:
        """计算线性回归斜率"""
        
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope
    
    def predict_next_value(self, metric_name: str, method: str = 'linear') -> Any:
        """预测下一个值"""
        
        data = list(self.time_series_data[metric_name])[-20:]  # 使用最近20个数据点
        if len(data) < 3:
            return None
        
        values = [d['value'] for d in data]
        
        if not all(isinstance(v, (int, float)) for v in values):
            # 非数值型数据，使用众数预测
            try:
                return statistics.mode(values)
            except:
                return values[-1]
        
        if method == 'linear':
            # 线性回归预测
            x = list(range(len(values)))
            slope = self._calculate_slope(x, values)
            intercept = sum(values) / len(values) - slope * (len(values) - 1) / 2
            return slope * len(values) + intercept
            
        elif method == 'moving_average':
            # 移动平均预测
            window_size = min(5, len(values))
            return sum(values[-window_size:]) / window_size
            
        elif method == 'exponential_smoothing':
            # 指数平滑预测
            alpha = get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold"))
            if len(values) < 2:
                return values[-1]
            
            smoothed = values[0]
            for value in values[1:]:
                smoothed = alpha * value + (1 - alpha) * smoothed
            
            return smoothed
        
        return values[-1]  # 默认返回最后一个值
    
    def detect_seasonal_pattern(self, metric_name: str, period: int = 24) -> Dict[str, Any]:
        """检测季节性模式"""
        
        data = list(self.time_series_data[metric_name])[-period * 3:]  # 使用3个周期的数据
        if len(data) < period * 2:
            return {}
        
        values = [d['value'] for d in data]
        
        if not all(isinstance(v, (int, float)) for v in values):
            return {}
        
        # 计算自相关
        autocorr = []
        for lag in range(1, period + 1):
            if len(values) > lag:
                corr = self._calculate_correlation(values[:-lag], values[lag:])
                autocorr.append((lag, corr))
        
        # 找到最强的自相关
        if autocorr:
            best_lag, best_corr = max(autocorr, key=lambda x: x[1])
            if best_corr > get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")):  # 自相关阈值
                return {
                    'period': best_lag,
                    'correlation': best_corr,
                    'pattern_type': 'seasonal'
                }
        
        return {}
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """计算皮尔逊相关系数"""
        
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        mean_x = sum(x) / len(x)
        mean_y = sum(y) / len(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denominator = math.sqrt(
            sum((xi - mean_x) ** 2 for xi in x) * 
            sum((yi - mean_y) ** 2 for yi in y)
        )
        
        return numerator / denominator if denominator != 0 else 0
    
    def get_time_series_stats(self, metric_name: str) -> Dict[str, Any]:
        """获取时间序列统计信息"""
        
        data = list(self.time_series_data[metric_name])
        if not data:
            return {}
        
        values = [d['value'] for d in data]
        
        stats = {
            'count': len(data),
            'trend': self.get_recent_trend(metric_name),
            'seasonal_pattern': self.detect_seasonal_pattern(metric_name)
        }
        
        if all(isinstance(v, (int, float)) for v in values):
            stats.update({
                'mean': statistics.mean(values),
                'median': statistics.median(values),
                'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                'min': min(values),
                'max': max(values),
                'range': max(values) - min(values)
            })
        
        return stats

class PredictiveModel:
    """预测模型"""
    
    def __init__(self):
        self.models = {}
        self.training_data = defaultdict(list)
        self.model_accuracy = {}
    
    def train_model(self, feature_name: str, target_name: str, 
                   training_periods: int = 50):
        """训练预测模型"""
        
        # 收集训练数据
        features = []
        targets = []
        
        # 这里简化实现，实际应该使用更复杂的机器学习算法
        feature_data = list(self.training_data[feature_name])[-training_periods:]
        target_data = list(self.training_data[target_name])[-training_periods:]
        
        if len(feature_data) != len(target_data) or len(feature_data) < get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
            return False
        
        # 简单的线性回归模型
        feature_values = [d['value'] for d in feature_data]
        target_values = [d['value'] for d in target_data]
        
        if not all(isinstance(v, (int, float)) for v in feature_values + target_values):
            return False
        
        # 计算线性回归参数
        slope, intercept = self._simple_linear_regression(feature_values, target_values)
        
        self.models[f"{feature_name}_to_{target_name}"] = {
            'slope': slope,
            'intercept': intercept,
            'feature_name': feature_name,
            'target_name': target_name,
            'trained_at': datetime.now(),
            'training_samples': len(feature_values)
        }
        
        # 计算模型准确性
        predictions = [slope * x + intercept for x in feature_values]
        mse = sum((p - t) ** 2 for p, t in zip(predictions, target_values)) / len(predictions)
        rmse = math.sqrt(mse)
        mean_target = sum(target_values) / len(target_values)
        accuracy = 1 - (rmse / mean_target) if mean_target != 0 else 0
        
        self.model_accuracy[f"{feature_name}_to_{target_name}"] = {
            'accuracy': max(0, accuracy),
            'rmse': rmse,
            'mean_target': mean_target
        }
        
        logger.info(f"✅ 训练预测模型: {feature_name} → {target_name}, 准确性: {accuracy:.3f}")
        return True
    
    def _simple_linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        """简单线性回归"""
        
        if len(x) != len(y) or len(x) < 2:
            return 0, sum(y) / len(y) if y else 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0, sum_y / n
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept
    
    def predict(self, feature_name: str, feature_value: float, target_name: str) -> Optional[float]:
        """使用训练好的模型进行预测"""
        
        model_key = f"{feature_name}_to_{target_name}"
        if model_key not in self.models:
            return None
        
        model = self.models[model_key]
        prediction = model['slope'] * feature_value + model['intercept']
        
        return prediction
    
    def add_training_sample(self, feature_name: str, feature_value: Any, 
                           target_name: str, target_value: Any):
        """添加训练样本"""
        
        feature_sample = {
            'timestamp': datetime.now(),
            'value': feature_value
        }
        
        target_sample = {
            'timestamp': datetime.now(),
            'value': target_value
        }
        
        self.training_data[feature_name].append(feature_sample)
        self.training_data[target_name].append(target_sample)
        
        # 保持训练数据在合理范围内
        max_samples = 1000
        if len(self.training_data[feature_name]) > max_samples:
            self.training_data[feature_name] = self.training_data[feature_name][-max_samples:]
        if len(self.training_data[target_name]) > max_samples:
            self.training_data[target_name] = self.training_data[target_name][-max_samples:]
    
    def get_model_stats(self) -> Dict[str, Any]:
        """获取模型统计信息"""
        return {
            'total_models': len(self.models),
            'model_accuracies': self.model_accuracy,
            'training_data_sizes': {k: len(v) for k, v in self.training_data.items()},
            'avg_accuracy': (
                sum(acc['accuracy'] for acc in self.model_accuracy.values()) / 
                len(self.model_accuracy) if self.model_accuracy else 0
            )
        }

class PredictiveConfigManager:
    """预测性配置管理器"""
    
    def __init__(self):
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.predictive_model = PredictiveModel()
        self.prediction_history = []
        self.monitoring_thread = threading.Thread(target=self._continuous_monitoring)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # 配置预测规则
        self.prediction_rules = self._load_prediction_rules()
    
    def _load_prediction_rules(self) -> Dict[str, Any]:
        """加载预测规则"""
        return {
            'cpu_based_timeout': {
                'feature': 'cpu_usage',
                'target': 'timeout',
                'prediction_window': 5,  # 预测5分钟后的CPU使用率
                'adjustment_factor': 0.1
            },
            'memory_based_cache': {
                'feature': 'memory_usage', 
                'target': 'cache_size',
                'prediction_window': get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                'adjustment_factor': 0.05
            },
            'load_based_workers': {
                'feature': 'system_load',
                'target': 'max_workers',
                'prediction_window': 3,
                'adjustment_factor': 0.2
            },
            'traffic_based_connections': {
                'feature': 'network_connections',
                'target': 'max_connections',
                'prediction_window': 2,
                'adjustment_factor': 0.15
            }
        }
    
    def predict_future_config(self, current_config: Dict[str, Any], 
                            current_context: Dict[str, Any], 
                            prediction_horizon: int = 5) -> Dict[str, Any]:
        """预测未来配置需求"""
        
        predicted_config = current_config.copy()
        predictions = {}
        
        # 1. 时间序列预测
        time_series_predictions = self._predict_from_time_series(prediction_horizon)
        predictions.update(time_series_predictions)
        
        # 2. 机器学习模型预测
        ml_predictions = self._predict_from_models(current_context)
        predictions.update(ml_predictions)
        
        # 3. 应用预测规则调整配置
        for rule_name, rule in self.prediction_rules.items():
            feature_name = rule['feature']
            target_name = rule['target']
            
            if feature_name in predictions:
                predicted_feature = predictions[feature_name]
                current_target = current_config.get(target_name)
                
                if current_target is not None and isinstance(current_target, (int, float)):
                    # 计算调整量
                    adjustment = (predicted_feature - current_context.get(feature_name, predicted_feature)) * rule['adjustment_factor']
                    new_value = current_target + adjustment
                    
                    # 应用合理范围限制
                    new_value = self._apply_reasonable_limits(target_name, new_value)
                    
                    predicted_config[target_name] = new_value
                    
                    logger.info(f"🔮 预测调整 {target_name}: {current_target} → {new_value} "
                              f"(基于 {feature_name} 预测: {predicted_feature})")
        
        # 记录预测历史
        self.prediction_history.append({
            'timestamp': datetime.now(),
            'current_config': current_config,
            'current_context': current_context,
            'predicted_config': predicted_config,
            'predictions': predictions,
            'horizon': prediction_horizon
        })
        
        # 保持历史记录在合理范围内
        if len(self.prediction_history) > 500:
            self.prediction_history = self.prediction_history[-300:]
        
        return predicted_config
    
    def _predict_from_time_series(self, horizon: int) -> Dict[str, Any]:
        """基于时间序列的预测"""
        
        predictions = {}
        key_metrics = ['cpu_usage', 'memory_usage', 'system_load', 'network_connections']
        
        for metric in key_metrics:
            predicted_value = self.time_series_analyzer.predict_next_value(metric, 'exponential_smoothing')
            if predicted_value is not None:
                predictions[metric] = predicted_value
        
        return predictions
    
    def _predict_from_models(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """基于机器学习模型的预测"""
        
        predictions = {}
        
        # 尝试使用训练好的模型进行预测
        for feature_name, feature_value in context.items():
            if isinstance(feature_value, (int, float)):
                for target_name in ['timeout', 'max_workers', 'cache_size', 'max_connections']:
                    prediction = self.predictive_model.predict(feature_name, feature_value, target_name)
                    if prediction is not None:
                        predictions[f"{feature_name}_to_{target_name}"] = prediction
        
        return predictions
    
    def _apply_reasonable_limits(self, config_name: str, value: float) -> float:
        """应用合理范围限制"""
        
        limits = {
            'timeout': (5, 300),
            'max_workers': (1, 50),
            'cache_size': (get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")), 10000),
            'max_connections': (1, 1000)
        }
        
        if config_name in limits:
            min_val, max_val = limits[config_name]
            return max(min_val, min(max_val, value))
        
        return value
    
    def record_system_metrics(self, metrics: Dict[str, Any]):
        """记录系统指标"""
        
        timestamp = datetime.now()
        
        for metric_name, value in metrics.items():
            self.time_series_analyzer.add_data_point(metric_name, value, timestamp)
            
            # 为机器学习模型添加训练样本
            if metric_name in ['cpu_usage', 'memory_usage']:
                # 添加一些相关的配置作为目标变量
                for config_name in ['timeout', 'max_workers', 'cache_size']:
                    # 这里简化，实际应该从当前配置中获取
                    mock_config_value = 30 if config_name == 'timeout' else 8
                    self.predictive_model.add_training_sample(
                        metric_name, value, config_name, mock_config_value)
    
    def _continuous_monitoring(self):
        """持续监控和学习"""
        while True:
            try:
                # 模拟收集系统指标（实际应该从系统监控中获取）
                mock_metrics = {
                    'cpu_usage': 50 + 20 * math.sin(time.time() / 3600),  # 模拟CPU使用率波动
                    'memory_usage': 60 + 15 * math.cos(time.time() / 3600),
                    'system_load': 1.5 + get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) * math.sin(time.time() / 1800),
                    'network_connections': get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit")) + 50 * math.sin(time.time() / 7200)
                }
                
                self.record_system_metrics(mock_metrics)
                
                # 定期训练模型
                if int(time.time()) % 300 == 0:  # 每5分钟训练一次
                    self._train_prediction_models()
                
                time.sleep(60)  # 每分钟监控一次
                
            except Exception as e:
                logger.error(f"持续监控异常: {e}")
                time.sleep(60)
    
    def _train_prediction_models(self):
        """训练预测模型"""
        
        try:
            # 训练一些关键的预测模型
            training_pairs = [
                ('cpu_usage', 'timeout'),
                ('memory_usage', 'cache_size'),
                ('system_load', 'max_workers'),
                ('network_connections', 'max_connections')
            ]
            
            for feature, target in training_pairs:
                self.predictive_model.train_model(feature, target)
                
        except Exception as e:
            logger.error(f"模型训练异常: {e}")
    
    def get_prediction_accuracy(self) -> Dict[str, Any]:
        """获取预测准确性统计"""
        
        if not self.prediction_history:
            return {}
        
        recent_predictions = self.prediction_history[-50:]  # 最近50个预测
        
        accuracies = []
        config_improvements = []
        
        for pred in recent_predictions:
            # 这里简化准确性计算，实际应该比较预测值与实际值
            if 'actual_config' in pred:  # 假设稍后会添加实际配置数据
                accuracy = get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))  # 模拟准确性
                accuracies.append(accuracy)
                
                # 计算配置改进
                if 'improvement_score' in pred:
                    config_improvements.append(pred['improvement_score'])
        
        return {
            'total_predictions': len(self.prediction_history),
            'recent_predictions': len(recent_predictions),
            'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0,
            'avg_improvement': sum(config_improvements) / len(config_improvements) if config_improvements else 0,
            'model_stats': self.predictive_model.get_model_stats(),
            'time_series_stats': {
                metric: self.time_series_analyzer.get_time_series_stats(metric)
                for metric in ['cpu_usage', 'memory_usage', 'system_load']
            }
        }
    
    def get_predictive_config_stats(self) -> Dict[str, Any]:
        """获取预测性配置统计"""
        return {
            'prediction_history_size': len(self.prediction_history),
            'active_monitoring': self.monitoring_thread.is_alive(),
            'prediction_rules_count': len(self.prediction_rules),
            'accuracy_stats': self.get_prediction_accuracy()
        }

# 全局预测性配置管理器实例
_predictive_config_manager = None

def get_predictive_config_manager() -> PredictiveConfigManager:
    """获取预测性配置管理器实例"""
    global _predictive_config_manager
    if _predictive_config_manager is None:
        _predictive_config_manager = PredictiveConfigManager()
    return _predictive_config_manager

def predict_future_configuration(current_config: Dict[str, Any], 
                               current_context: Dict[str, Any], 
                               horizon: int = 5) -> Dict[str, Any]:
    """预测未来配置需求"""
    return get_predictive_config_manager().predict_future_config(current_config, current_context, horizon)

def record_system_metrics(metrics: Dict[str, Any]):
    """记录系统指标"""
    get_predictive_config_manager().record_system_metrics(metrics)

def get_prediction_stats() -> Dict[str, Any]:
    """获取预测统计"""
    return get_predictive_config_manager().get_predictive_config_stats()
