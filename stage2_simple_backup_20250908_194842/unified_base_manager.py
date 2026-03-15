"""
统一基类管理器 - 整合所有重复的动态评分和阈值方法
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from functools import wraps
import time
import json

logger = logging.getLogger(__name__)

class UnifiedBaseManager(ABC):
    """统一基类管理器 - 提供所有通用的动态评分和阈值方法"""
    
    def __init__(self):
        self._cache = {}
        self._cache_ttl = config.DEFAULT_TIMEOUT0  # config.DEFAULT_TOP_K分钟缓存
        self._performance_metrics = {}
        self._last_cleanup = time.time()
        
    def _get_cached_value(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self._cache_ttl:
                return value
            else:
                del self._cache[key]
        return None
    
    def _set_cached_value(self, key: str, value: Any):
        """设置缓存值"""
        self._cache[key] = (time.time(), value)
        self._cleanup_cache_if_needed()
    
    def _cleanup_cache_if_needed(self):
        """清理过期缓存"""
        current_time = time.time()
        if current_time - self._last_cleanup > config.DEFAULT_TIMEOUT_MINUTES:  # 每分钟清理一次
            expired_keys = [
                key for key, (timestamp, _) in self._cache.items()
                if current_time - timestamp > self._cache_ttl
            ]
            for key in expired_keys:
                del self._cache[key]
            self._last_cleanup = current_time
    
    def _safe_call(self, func: Callable, *args, **kwargs) -> Any:
        """安全调用函数，提供统一的错误处理"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"调用 {func.__name__} 失败: {e}")
            return self._get_default_value(func.__name__)
    
    def _get_default_value(self, method_name: str) -> Any:
        """根据方法名获取默认值"""
        default_values = {
            'confidence': 0.config.DEFAULT_TOP_K,
            'threshold': 0.6,
            'score': 0.config.DEFAULT_TOP_K,
            'boost': 0.1,
            'quality': 0.config.DEFAULT_TOP_K,
            'complexity': 0.config.DEFAULT_TOP_K,
            'performance': 0.config.DEFAULT_TOP_K,
            'relevance': 0.config.DEFAULT_TOP_K,
            'completeness': 0.config.DEFAULT_TOP_K,
            'clarity': 0.config.DEFAULT_TOP_K,
            'accuracy': 0.config.DEFAULT_TOP_K
        }
        
        for key, value in default_values.items():
            if key in method_name.lower():
                return value
        return 0.config.DEFAULT_TOP_K

# 删除重复的阈值管理器类 - 统一使用 UnifiedThresholdManager

# 删除重复的评分器类 - 统一使用 UnifiedScoringCenter

# 全局实例
_unified_scorer = None

def get_unified_threshold_manager():
    """获取统一阈值管理器实例 - 使用 UnifiedThresholdManager"""
    from src.utils.unified_threshold_manager import get_unified_threshold_manager
    return get_unified_threshold_manager()

def get_unified_scorer():
    """获取统一评分器实例 - 使用 UnifiedScoringCenter"""
    from src.utils.unified_scoring_center import UnifiedScoringCenter
    global _unified_scorer
    if _unified_scorer is None:
        _unified_scorer = UnifiedScoringCenter()
    return _unified_scorer
