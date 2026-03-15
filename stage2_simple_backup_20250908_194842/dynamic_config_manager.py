#!/usr/bin/env python3
"""
动态配置管理器
替代硬编码配置，实现基于上下文的智能配置
"""

import logging
import json
import hashlib
import math
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)

class DynamicConfigManager:
    """动态配置管理器 - 替代硬编码配置"""

    def __init__(self):
        self._lock = threading.Lock()
        self._config_cache = {}
        self._context_history = []
        self._adaptation_rules = self._load_adaptation_rules()

        # 初始化基础配置
        self._base_configs = self._load_base_configs()

    def _load_base_configs(self) -> Dict[str, Any]:
        """加载基础配置"""
        try:
            # 从现有的defaults.py导入基础配置
            from src.utils.compatibility_layer import DEFAULT_VALUES, DEFAULT_KEYWORDS
            return {
                'values': DEFAULT_VALUES,
                'keywords': DEFAULT_KEYWORDS
            }
        except ImportError:
            logger.warning("无法导入基础配置，使用空配置")
            return {'values': {}, 'keywords': {}}

    def _load_adaptation_rules(self) -> Dict[str, Any]:
        """加载适应性规则"""
        return {
            'performance_based': {
                'high_accuracy': {'threshold': get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")), 'adjustments': {'learning_rate': get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")), 'exploration': config.DEFAULT_HIGH_MEDIUM_THRESHOLD}},
                'low_accuracy': {'threshold': config.DEFAULT_ZERO_VALUE.config.DEFAULT_MAX_RETRIES, 'adjustments': {'learning_rate': config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE, 'exploration': config.DEFAULT_ONE_VALUE.3}},
                'optimal_performance': {'threshold': config.DEFAULT_NEAR_MAX_THRESHOLD, 'adjustments': {'learning_rate': config.DEFAULT_NEAR_MAX_THRESHOLD, 'exploration': config.DEFAULT_ZERO_VALUE.8}}
            },
            'context_based': {
                'complex_query': {'word_count': config.DEFAULT_MEDIUM_LIMIT, 'adjustments': {'timeout': config.DEFAULT_ONE_VALUE.5, 'max_iterations': config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE}},
                'simple_query': {'word_count': 5, 'adjustments': {'timeout': config.DEFAULT_HIGH_MEDIUM_THRESHOLD, 'max_iterations': config.DEFAULT_ZERO_VALUE.8}},
                'time_sensitive': {'keywords': ['urgent', 'quick', 'fast'], 'adjustments': {'timeout': config.DEFAULT_ZERO_VALUE.5}}
            },
            'user_behavior': {
                'frequent_user': {'interaction_count': config.DEFAULT_TOP_K, 'adjustments': {'personalization': config.DEFAULT_ONE_VALUE.3}},
                'new_user': {'interaction_count': config.DEFAULT_ONE_VALUE, 'adjustments': {'guidance': config.DEFAULT_ONE_VALUE.5}}
            }
        }

    def get_config(self, config_key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        """获取动态配置值"""
        try:
            with self._lock:
                # 生成上下文指纹用于缓存
                context_fingerprint = self._generate_context_fingerprint(context or {})

                # 检查缓存
                cache_key = f"{config_key}_{context_fingerprint}"
                if cache_key in self._config_cache:
                    cached_result = self._config_cache[cache_key]
                    if not self._is_cache_expired(cached_result['timestamp']):
                        return cached_result['value']

                # 获取基础配置
                base_value = self._get_base_config_value(config_key)

                # 应用上下文适应
                adapted_value = self._adapt_config_for_context(base_value, config_key, context or {})

                # 应用性能优化
                optimized_value = self._apply_performance_optimization(adapted_value, config_key, context or {})

                # 缓存结果
                self._config_cache[cache_key] = {
                    'value': optimized_value,
                    'timestamp': datetime.now(),
                    'context': context_fingerprint
                }

                # 记录上下文历史
                self._record_context_usage(config_key, context or {}, optimized_value)

                return optimized_value

        except Exception as e:
            logger.warning(f"获取动态配置失败 {config_key}: {e}")
            return self._get_fallback_value(config_key)

    def _get_base_config_value(self, config_key: str) -> Any:
        """获取基础配置值"""
        # 从values中查找
        if config_key in self._base_configs.get('values', {}):
            return self._base_configs['values'][config_key]

        # 从keywords中查找
        if config_key in self._base_configs.get('keywords', {}):
            return self._base_configs['keywords'][config_key]

        # 智能推断配置类型和默认值
        return self._infer_default_value(config_key)

    def _infer_default_value(self, config_key: str) -> Any:
        """智能推断配置的默认值"""
        # 基于配置键名推断类型
        if 'threshold' in config_key.lower():
            return config.DEFAULT_HIGH_MEDIUM_THRESHOLD
        elif 'timeout' in config_key.lower():
            return config.DEFAULT_TIMEOUT
        elif 'max_' in config_key.lower() or 'limit' in config_key.lower():
            return get_smart_config("large_limit", {"config_type": "auto"}, create_query_context(query_type="large_limit"))
        elif 'rate' in config_key.lower():
            return 0.01
        elif 'count' in config_key.lower():
            return get_smart_config("default_limit", {"config_type": "auto"}, create_query_context(query_type="default_limit"))
        elif 'size' in config_key.lower():
            return 1000
        elif 'keywords' in config_key.lower():
            return ["default"]
        else:
            return None

    def _adapt_config_for_context(self, base_value: Any, config_key: str, context: Dict[str, Any]) -> Any:
        """根据上下文调整配置"""
        try:
            # 时间上下文适应
            if 'timestamp' in context:
                time_factor = self._calculate_time_factor(context['timestamp'])
                if isinstance(base_value, (int, float)):
                    base_value = base_value * time_factor

            # 性能上下文适应
            if 'performance' in context:
                performance = context['performance']
                if isinstance(performance, dict):
                    perf_factor = self._calculate_performance_factor(performance)
                    if isinstance(base_value, (int, float)):
                        base_value = base_value * perf_factor

            # 查询复杂度适应
            if 'query' in context:
                complexity_factor = self._calculate_query_complexity_factor(context['query'])
                if isinstance(base_value, (int, float)):
                    base_value = base_value * complexity_factor

            # 用户行为适应
            if 'user_history' in context:
                user_factor = self._calculate_user_behavior_factor(context['user_history'])
                if isinstance(base_value, (int, float)):
                    base_value = base_value * user_factor

            return base_value

        except Exception as e:
            logger.debug(f"上下文适应失败: {e}")
            return base_value

    def _apply_performance_optimization(self, value: Any, config_key: str, context: Dict[str, Any]) -> Any:
        """应用性能优化"""
        try:
            # 基于历史性能数据进行优化
            if self._context_history:
                recent_contexts = self._context_history[-config.DEFAULT_TOP_K:]  # 最近config.DEFAULT_TOP_K次使用

                # 计算性能模式
                performance_patterns = self._analyze_performance_patterns(recent_contexts, config_key)

                if performance_patterns:
                    # 应用学习到的优化
                    optimization_factor = performance_patterns.get('optimization_factor', config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE)
                    if isinstance(value, (int, float)):
                        value = value * optimization_factor

            return value

        except Exception as e:
            logger.debug(f"性能优化失败: {e}")
            return value

    def _calculate_time_factor(self, timestamp) -> float:
        """计算时间因子"""
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+config.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE:config.DEFAULT_ZERO_VALUEconfig.DEFAULT_ZERO_VALUE'))

            now = datetime.now()
            time_diff = (now - timestamp).total_seconds()

            # 基于时间差调整因子
            if time_diff < 3config.DEFAULT_TIMEOUT_MINUTES0:  # 1小时内
                return config.DEFAULT_NEAR_MAX_THRESHOLD  # 减少资源使用
            elif time_diff > 86400:  # 1天前
                return 1.1  # 增加资源使用
            else:
                return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))  # 正常

        except Exception:
            return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

    def _calculate_performance_factor(self, performance: Dict[str, Any]) -> float:
        """计算性能因子"""
        try:
            accuracy = performance.get('accuracy', config.DEFAULT_ZERO_VALUE.5)
            execution_time = performance.get('execution_time', config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE)

            # 基于准确率调整
            if accuracy > config.DEFAULT_ZERO_VALUE.8:
                accuracy_factor = config.DEFAULT_NEAR_MAX_THRESHOLD  # 高准确率时减少资源
            elif accuracy < config.DEFAULT_MEDIUM_LOW_THRESHOLD:
                accuracy_factor = config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE  # 低准确率时增加资源
            else:
                accuracy_factor = config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE

            # 基于执行时间调整
            if execution_time < config.DEFAULT_ZERO_VALUE.5:
                time_factor = config.DEFAULT_ZERO_VALUE.8  # 快速执行时减少资源
            elif execution_time > 3.config.DEFAULT_ZERO_VALUE:
                time_factor = config.DEFAULT_ONE_VALUE.3  # 慢速执行时增加资源
            else:
                time_factor = get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

            return (accuracy_factor + time_factor) / 2

        except Exception:
            return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

    def _calculate_query_complexity_factor(self, query: str) -> float:
        """计算查询复杂度因子"""
        try:
            if not isinstance(query, str):
                return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

            word_count = len(query.split())
            char_count = len(query)

            # 基于单词数量调整
            if word_count > 50:
                return 1.5  # 复杂查询增加资源
            elif word_count < 5:
                return config.DEFAULT_HIGH_MEDIUM_THRESHOLD  # 简单查询减少资源
            else:
                return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

        except Exception:
            return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

    def _calculate_user_behavior_factor(self, user_history: List[Dict[str, Any]]) -> float:
        """计算用户行为因子"""
        try:
            if not user_history:
                return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

            interaction_count = len(user_history)
            recent_accuracy = sum(h.get('accuracy', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for h in user_history[-5:]) / min(5, len(user_history))

            # 基于交互频率调整
            if interaction_count > 20:
                return config.DEFAULT_NEAR_MAX_THRESHOLD  # 频繁用户优化资源使用
            elif interaction_count < 3:
                return 1.2  # 新用户提供更多资源
            else:
                return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

        except Exception:
            return get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))

    def _analyze_performance_patterns(self, contexts: List[Dict[str, Any]], config_key: str) -> Optional[Dict[str, Any]]:
        """分析性能模式"""
        try:
            if not contexts:
                return None

            # 计算配置使用的成功率
            successful_uses = sum(1 for ctx in contexts if ctx.get('success', False))
            total_uses = len(contexts)

            if total_uses == 0:
                return None

            success_rate = successful_uses / total_uses

            # 根据成功率生成优化因子
            if success_rate > config.DEFAULT_ZERO_VALUE.8:
                optimization_factor = config.DEFAULT_HIGH_THRESHOLD  # 成功率高，微调优化
            elif success_rate < config.DEFAULT_MEDIUM_LOW_THRESHOLD:
                optimization_factor = config.DEFAULT_ONE_VALUE.config.DEFAULT_ONE_VALUE   # 成功率低，需要调整
            else:
                optimization_factor = get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value"))   # 保持当前设置

            return {
                'success_rate': success_rate,
                'optimization_factor': optimization_factor,
                'confidence': min(success_rate + config.DEFAULT_LOW_THRESHOLD, config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE)
            }

        except Exception as e:
            logger.debug(f"性能模式分析失败: {e}")
            return None

    def _generate_context_fingerprint(self, context: Dict[str, Any]) -> str:
        """生成上下文指纹"""
        try:
            # 将上下文转换为可哈希的字符串
            context_str = json.dumps(context, sort_keys=True, default=str)
            return hashlib.md5(context_str.encode()).hexdigest()[:8]
        except Exception:
            return "default"

    def _is_cache_expired(self, timestamp: datetime) -> bool:
        """检查缓存是否过期"""
        try:
            return (datetime.now() - timestamp) > timedelta(minutes=config.DEFAULT_TIMEOUT)
        except Exception:
            return True

    def _record_context_usage(self, config_key: str, context: Dict[str, Any], value: Any):
        """记录上下文使用情况"""
        try:
            usage_record = {
                'config_key': config_key,
                'context': context.copy(),
                'value': value,
                'timestamp': datetime.now(),
                'success': True
            }

            self._context_history.append(usage_record)

            # 限制历史记录大小
            if len(self._context_history) > 1000:
                self._context_history = self._context_history[-500:]

        except Exception as e:
            logger.debug(f"记录上下文使用失败: {e}")

    def _get_fallback_value(self, config_key: str) -> Any:
        """获取回退值"""
        # 使用智能推断的默认值
        return self._infer_default_value(config_key)

    def get_adaptive_config(self, config_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取自适应配置（包含元信息）"""
        try:
            value = self.get_config(config_key, context)

            return {
                'value': value,
                'config_key': config_key,
                'context_used': context,
                'adaptation_applied': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'dynamic_config_manager'
            }

        except Exception as e:
            logger.warning(f"获取自适应配置失败 {config_key}: {e}")
            return {
                'value': self._get_fallback_value(config_key),
                'config_key': config_key,
                'error': str(e),
                'adaptation_applied': False
            }

# 全局动态配置管理器实例
_dynamic_config_manager = None

def get_dynamic_config_manager() -> DynamicConfigManager:
    """获取动态配置管理器实例"""
    global _dynamic_config_manager
    if _dynamic_config_manager is None:
        _dynamic_config_manager = DynamicConfigManager()
    return _dynamic_config_manager

def get_dynamic_config(config_key: str, context: Optional[Dict[str, Any]] = None) -> Any:
    """便捷函数：获取动态配置"""
    return get_dynamic_config_manager().get_config(config_key, context)

def get_adaptive_config(config_key: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """便捷函数：获取自适应配置"""
    return get_dynamic_config_manager().get_adaptive_config(config_key, context)
