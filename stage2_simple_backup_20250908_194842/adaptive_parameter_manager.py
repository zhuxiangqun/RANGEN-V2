"""
自适应参数管理系统
基于性能监控和机器学习动态调整系统参数
替代硬编码的阈值和常量配置
"""

import logging
import time
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class ParameterConfig:
    """参数配置"""
    name: str
    current_value: float
    default_value: float
    min_value: float
    max_value: float
    description: str
    category: str
    last_updated: datetime = field(default_factory=datetime.now)
    performance_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime
    response_time: float
    accuracy: float
    success_rate: float
    resource_usage: float
    parameter_values: Dict[str, float]

class AdaptiveParameterManager:
    """
    自适应参数管理器
    基于性能监控动态调整系统参数
    """

    def __init__(self):
        self.parameters: Dict[str, ParameterConfig] = {}
        self.performance_history: deque = deque(maxlen=1000)  # 保留最近1000条记录
        self.learning_enabled = True
        self.auto_tuning_enabled = True

        # 初始化默认参数配置
        self._initialize_default_parameters()
        self._load_parameter_history()

        logger.info(f"✅ 自适应参数管理器初始化完成，支持 {len(self.parameters)} 个参数")

    def _initialize_default_parameters(self):
        """初始化默认参数配置"""
        default_configs = [
            # 阈值参数
            ParameterConfig(
                name="high_threshold",
                current_value=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
                default_value=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
                min_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                max_value=0.95,
                description="高质量阈值",
                category="threshold"
            ),
            ParameterConfig(
                name="medium_high_threshold",
                current_value=0.7,
                default_value=0.7,
                min_value=0.4,
                max_value=0.9,
                description="中等偏高阈值",
                category="threshold"
            ),
            ParameterConfig(
                name="medium_low_threshold",
                current_value=0.6,
                default_value=0.6,
                min_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                max_value=get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")),
                description="中等偏低阈值",
                category="threshold"
            ),
            ParameterConfig(
                name="low_medium_threshold",
                current_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                default_value=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                min_value=0.2,
                max_value=0.7,
                description="低等偏中阈值",
                category="threshold"
            ),
            ParameterConfig(
                name="low_threshold",
                current_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                default_value=get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")),
                min_value=0.1,
                max_value=0.6,
                description="低质量阈值",
                category="threshold"
            ),

            # 限制参数
            ParameterConfig(
                name="medium_limit",
                current_value=50,
                default_value=50,
                min_value=get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")),
                max_value=200,
                description="中等限制值",
                category="limit"
            ),
            ParameterConfig(
                name="low_decimal_threshold",
                current_value=0.05,
                default_value=0.05,
                min_value=0.01,
                max_value=0.2,
                description="低小数阈值",
                category="threshold"
            ),

            # 因子参数
            ParameterConfig(
                name="improvement_factor",
                current_value=1.05,
                default_value=1.05,
                min_value=1.01,
                max_value=1.2,
                description="改进因子",
                category="factor"
            ),
            ParameterConfig(
                name="decay_factor",
                current_value=0.9,
                default_value=0.9,
                min_value=0.7,
                max_value=0.99,
                description="衰减因子",
                category="factor"
            ),
        ]

        for config in default_configs:
            self.parameters[config.name] = config

    def get_parameter(self, name: str) -> float:
        """
        获取参数值
        如果参数不存在，返回默认值
        """
        if name in self.parameters:
            return self.parameters[name].current_value
        else:
            logger.warning(f"参数 {name} 不存在，使用默认值 get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))")
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))

    def record_performance(self, metrics: Dict[str, Any]):
        """
        记录性能指标
        用于参数优化和学习
        """
        if not self.learning_enabled:
            return

        # 创建性能记录
        record = PerformanceMetrics(
            timestamp=datetime.now(),
            response_time=metrics.get('response_time', get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))),
            accuracy=metrics.get('accuracy', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))),
            success_rate=metrics.get('success_rate', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))),
            resource_usage=metrics.get('resource_usage', get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))),
            parameter_values={name: param.current_value for name, param in self.parameters.items()}
        )

        # 添加到历史记录
        self.performance_history.append(record)

        # 如果启用了自动调优，执行参数优化
        if self.auto_tuning_enabled and len(self.performance_history) >= get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
            self._optimize_parameters()

    def _optimize_parameters(self):
        """
        基于性能历史优化参数
        使用简单的梯度下降算法
        """
        if len(self.performance_history) < get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):
            return

        # 计算最近的性能趋势
        recent_records = list(self.performance_history)[-20:]  # 最近20条记录

        # 计算性能指标的变化趋势
        accuracy_trend = self._calculate_trend([r.accuracy for r in recent_records])
        response_time_trend = self._calculate_trend([r.response_time for r in recent_records])
        success_rate_trend = self._calculate_trend([r.success_rate for r in recent_records])

        # 基于趋势调整参数
        for param_name, param in self.parameters.items():
            if param.category == "threshold":
                self._adjust_threshold_parameter(param, accuracy_trend, success_rate_trend)
            elif param.category == "limit":
                self._adjust_limit_parameter(param, response_time_trend)
            elif param.category == "factor":
                self._adjust_factor_parameter(param, accuracy_trend)

    def _calculate_trend(self, values: List[float]) -> float:
        """
        计算趋势值
        正值表示上升趋势，负值表示下降趋势
        """
        if len(values) < 2:
            return get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value"))

        # 计算最近5个点和之前5个点的平均值
        mid_point = len(values) // 2
        recent_avg = statistics.mean(values[mid_point:])
        earlier_avg = statistics.mean(values[:mid_point])

        return recent_avg - earlier_avg

    def _adjust_threshold_parameter(self, param: ParameterConfig,
                                   accuracy_trend: float,
                                   success_rate_trend: float):
        """
        调整阈值参数
        """
        # 如果准确率和成功率都在下降，降低阈值
        if accuracy_trend < -0.05 and success_rate_trend < -0.05:
            new_value = param.current_value * 0.98  # 降低2%
        # 如果准确率和成功率都在上升，提高阈值
        elif accuracy_trend > 0.05 and success_rate_trend > 0.05:
            new_value = param.current_value * 1.02  # 提高2%
        else:
            return  # 不调整

        # 确保在有效范围内
        new_value = max(param.min_value, min(param.max_value, new_value))

        if abs(new_value - param.current_value) > 0.001:  # 只有显著变化才调整
            self._update_parameter_value(param.name, new_value, "auto_tuning")

    def _adjust_limit_parameter(self, param: ParameterConfig,
                               response_time_trend: float):
        """
        调整限制参数
        """
        # 如果响应时间在增加，降低限制
        if response_time_trend > 0.1:
            new_value = param.current_value * 0.95  # 降低5%
        # 如果响应时间在减少，提高限制
        elif response_time_trend < -0.1:
            new_value = param.current_value * 1.05  # 提高5%
        else:
            return

        new_value = max(param.min_value, min(param.max_value, new_value))
        new_value = int(new_value)  # 限制参数应该是整数

        if new_value != param.current_value:
            self._update_parameter_value(param.name, new_value, "auto_tuning")

    def _adjust_factor_parameter(self, param: ParameterConfig,
                                accuracy_trend: float):
        """
        调整因子参数
        """
        # 如果准确率在下降，调整因子
        if accuracy_trend < -0.03:
            if param.name == "improvement_factor":
                new_value = param.current_value * 0.99
            elif param.name == "decay_factor":
                new_value = param.current_value * 1.01
        elif accuracy_trend > 0.03:
            if param.name == "improvement_factor":
                new_value = param.current_value * 1.01
            elif param.name == "decay_factor":
                new_value = param.current_value * 0.99
        else:
            return

        new_value = max(param.min_value, min(param.max_value, new_value))

        if abs(new_value - param.current_value) > 0.001:
            self._update_parameter_value(param.name, new_value, "auto_tuning")

    def _update_parameter_value(self, param_name: str, new_value: float, reason: str):
        """
        更新参数值
        """
        if param_name in self.parameters:
            old_value = self.parameters[param_name].current_value
            self.parameters[param_name].current_value = new_value
            self.parameters[param_name].last_updated = datetime.now()

            # 记录参数变更历史
            performance_record = {
                'timestamp': datetime.now(),
                'parameter': param_name,
                'old_value': old_value,
                'new_value': new_value,
                'reason': reason
            }
            self.parameters[param_name].performance_history.append(performance_record)

            logger.info(f"🔧 参数调整: {param_name} {old_value:.4f} → {new_value:.4f} ({reason})")

    def get_parameter_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """
        获取参数优化建议
        """
        recommendations = {}

        for param_name, param in self.parameters.items():
            if len(param.performance_history) >= 5:
                # 分析参数调整的历史效果
                recent_history = param.performance_history[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]

                # 计算调整效果
                positive_adjustments = sum(1 for record in recent_history
                                         if record.get('effect', 0) > 0)

                success_rate = positive_adjustments / len(recent_history)

                if success_rate > 0.7:
                    recommendation = "当前参数表现良好，建议保持"
                elif success_rate < get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")):
                    recommendation = "当前参数可能需要调整"
                else:
                    recommendation = "当前参数表现一般，可考虑微调"

                recommendations[param_name] = {
                    'current_value': param.current_value,
                    'recommended_range': f"[{param.min_value}, {param.max_value}]",
                    'success_rate': success_rate,
                    'recommendation': recommendation,
                    'last_updated': param.last_updated.isoformat()
                }

        return recommendations

    def reset_parameters(self):
        """
        重置所有参数为默认值
        """
        for param in self.parameters.values():
            param.current_value = param.default_value
            param.last_updated = datetime.now()
            param.performance_history.clear()

        logger.info("🔄 所有参数已重置为默认值")

    def export_parameters(self, filepath: str):
        """
        导出参数配置到文件
        """
        export_data = {
            'export_time': datetime.now().isoformat(),
            'parameters': {},
            'performance_stats': {
                'total_records': len(self.performance_history),
                'learning_enabled': self.learning_enabled,
                'auto_tuning_enabled': self.auto_tuning_enabled
            }
        }

        for name, param in self.parameters.items():
            export_data['parameters'][name] = {
                'current_value': param.current_value,
                'default_value': param.default_value,
                'min_value': param.min_value,
                'max_value': param.max_value,
                'category': param.category,
                'description': param.description,
                'last_updated': param.last_updated.isoformat(),
                'history_count': len(param.performance_history)
            }

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 参数配置已导出到: {filepath}")
        except Exception as e:
            logger.error(f"❌ 导出参数配置失败: {e}")

    def import_parameters(self, filepath: str):
        """
        从文件导入参数配置
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            imported_count = 0
            for name, param_data in import_data.get('parameters', {}).items():
                if name in self.parameters:
                    self.parameters[name].current_value = param_data['current_value']
                    self.parameters[name].last_updated = datetime.fromisoformat(param_data['last_updated'])
                    imported_count += 1

            logger.info(f"✅ 成功导入 {imported_count} 个参数配置")

        except Exception as e:
            logger.error(f"❌ 导入参数配置失败: {e}")

    def _load_parameter_history(self):
        """
        加载参数历史记录
        """
        history_file = "config/parameter_history.json"
        if os.path.exists(history_file):
            try:
                self.import_parameters(history_file)
                logger.info("✅ 参数历史记录已加载")
            except Exception as e:
                logger.warning(f"⚠️ 加载参数历史失败: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取参数统计信息
        """
        stats = {
            'total_parameters': len(self.parameters),
            'parameter_categories': {},
            'performance_records': len(self.performance_history),
            'learning_enabled': self.learning_enabled,
            'auto_tuning_enabled': self.auto_tuning_enabled,
            'recent_optimizations': 0
        }

        # 统计各类参数
        for param in self.parameters.values():
            category = param.category
            if category not in stats['parameter_categories']:
                stats['parameter_categories'][category] = 0
            stats['parameter_categories'][category] += 1

        # 统计最近的优化次数
        recent_optimizations = sum(1 for param in self.parameters.values()
                                 for record in param.performance_history[-get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit")):]
                                 if record.get('reason') == 'auto_tuning')
        stats['recent_optimizations'] = recent_optimizations

        return stats


# 全局自适应参数管理器实例
_adaptive_manager = None

def get_adaptive_parameter_manager() -> AdaptiveParameterManager:
    """获取自适应参数管理器实例"""
    global _adaptive_manager
    if _adaptive_manager is None:
        _adaptive_manager = AdaptiveParameterManager()
    return _adaptive_manager

# 便捷函数
def get_adaptive_param(name: str) -> float:
    """获取自适应参数值"""
    return get_adaptive_parameter_manager().get_parameter(name)

def record_performance_metrics(metrics: Dict[str, Any]):
    """记录性能指标"""
    get_adaptive_parameter_manager().record_performance(metrics)
