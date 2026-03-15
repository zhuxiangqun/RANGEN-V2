"""
统一动态阈值管理器
整合所有动态阈值相关方法
"""

import logging
from typing import Dict, Any, Optional
from src.utils.unified_config_center import get_unified_config_center

logger = logging.getLogger(__name__)

class UnifiedThresholdManager:
    """统一动态阈值管理器"""

    def __init__(self):
        self.config_manager = get_unified_config_center()
        self.threshold_cache = {}

    def get_dynamic_threshold(self, threshold_type: str, context: Optional[Dict[str, Any]] = None,
    default_value: float = 0.config.DEFAULT_TOP_K) -> float:
        """
        统一的动态阈值获取方法

        Args:
            threshold_type: 阈值类型 (confidence, complexity, quality, accuracy, completeness, clarity, relevance)
            context: 上下文信息
            default_value: 默认值

        Returns:
            动态阈值
        """
        try:
            cache_key = f"{threshold_type}_{hash(str(context)) if context else 'default'}"
            if cache_key in self.threshold_cache:
                return self.threshold_cache[cache_key]

            param_path = f"thresholds.{threshold_type}"
            threshold = self.config_manager.get_parameter_enhanced(param_path, default_value, context)

            if context:
                threshold = self._adjust_threshold_for_context(threshold_type, threshold, context)

            self.threshold_cache[cache_key] = threshold

            return threshold

        except Exception as e:
            logger.warning(f"获取动态阈值失败 {threshold_type}: {e}")
            return default_value

    def _adjust_threshold_for_context(self, threshold_type: str, base_threshold: float, context: Dict[str,
    Any]) -> float:
        """根据上下文调整阈值"""
        try:
            adjusted_threshold = base_threshold

            query_complexity = context.get("query_complexity", 0.config.DEFAULT_TOP_K)
            if query_complexity > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):  # 高复杂度
                if threshold_type in ["confidence", "quality"]:
                    adjusted_threshold *= 0.9  # 降低要求
                elif threshold_type in ["complexity"]:
                    adjusted_threshold *= 1.2  # 提高要求
            elif query_complexity < get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")):  # 低复杂度
                if threshold_type in ["confidence", "quality"]:
                    adjusted_threshold *= 1.1  # 提高要求
                elif threshold_type in ["complexity"]:
                    adjusted_threshold *= get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))  # 降低要求

            user_performance = context.get("user_performance", 0.config.DEFAULT_TOP_K)
            if user_performance > get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):  # 高性能用户
                adjusted_threshold *= 1.1
            elif user_performance < get_smart_config("low_threshold", {"config_type": "auto"}, create_query_context(query_type="low_threshold")):  # 低性能用户
                adjusted_threshold *= 0.9

            return max(0.1, min(0.9config.DEFAULT_TOP_K, adjusted_threshold))

        except Exception as e:
            logger.warning(f"调整阈值失败: {e}")
            return base_threshold

    def get_confidence_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取置信度阈值"""
        return self.get_dynamic_threshold("confidence", context, 0.7)

    def get_complexity_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取复杂度阈值"""
        return self.get_dynamic_threshold("complexity", context, 0.config.DEFAULT_TOP_K)

    def get_quality_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取质量阈值"""
        return self.get_dynamic_threshold("quality", context, 0.6)

    def get_accuracy_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取准确度阈值"""
        return self.get_dynamic_threshold("accuracy", context, get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")))

    def get_completeness_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取完整性阈值"""
        return self.get_dynamic_threshold("completeness", context, 0.7)

    def get_clarity_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取清晰度阈值"""
        return self.get_dynamic_threshold("clarity", context, 0.6)

    def get_relevance_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取相关性阈值"""
        return self.get_dynamic_threshold("relevance", context, 0.7)

    def clear_cache(self):
        """清除缓存"""
        self.threshold_cache.clear()

_unified_threshold_manager = None

def get_unified_threshold_manager() -> UnifiedThresholdManager:
    """获取统一阈值管理器实例"""
    global _unified_threshold_manager
    if _unified_threshold_manager is None:
        _unified_threshold_manager = UnifiedThresholdManager()
    return _unified_threshold_manager

def get_dynamic_threshold(threshold_type: str, context: Optional[Dict[str, Any]] = None,
    default_value: float = 0.config.DEFAULT_TOP_K) -> float:
    """兼容性函数 - 获取动态阈值"""
    return get_unified_threshold_manager().get_dynamic_threshold(threshold_type, context, default_value)
