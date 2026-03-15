"""
缓存管理器模块

从 UnifiedResearchSystem 拆分出来的缓存功能
"""

import hashlib
import time
from typing import Dict, Any, Optional
from datetime import datetime


class CacheManager:
    """
    缓存管理器
    
    提供多种缓存策略:
    - 查询缓存
    - 知识库缓存
    - 推理结果缓存
    """
    
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache
        
        # 缓存存储
        self._query_cache: Dict[str, Dict[str, Any]] = {}
        self._knowledge_cache: Dict[str, Dict[str, Any]] = {}
        self._reasoning_cache: Dict[str, Dict[str, Any]] = {}
        
        # 缓存统计
        self._cache_stats = {
            "query_hits": 0,
            "query_misses": 0,
            "knowledge_hits": 0,
            "knowledge_misses": 0,
            "reasoning_hits": 0,
            "reasoning_misses": 0,
        }
        
        # 缓存过期时间 (秒)
        self._cache_ttl = {
            "query": 3600,      # 1小时
            "knowledge": 7200,  # 2小时
            "reasoning": 1800,  # 30分钟
        }
    
    def _get_cache_key(
        self, 
        query: str, 
        context: Dict[str, Any], 
        query_type: Optional[str] = None
    ) -> str:
        """生成缓存键"""
        cache_components = {
            "query": query,
            "query_type": query_type or "default",
        }
        
        # 添加上下文中的关键字段
        if context:
            if "user_id" in context:
                cache_components["user_id"] = context["user_id"]
            if "session_id" in context:
                cache_components["session_id"] = context["session_id"]
        
        # 生成哈希键
        cache_string = str(sorted(cache_components.items()))
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _check_cache(
        self, 
        cache_key: str, 
        cache_type: str
    ) -> Optional[Any]:
        """检查缓存"""
        if not self.enable_cache:
            return None
        
        cache_store = self._get_cache_store(cache_type)
        if not cache_store:
            return None
        
        cached = cache_store.get(cache_key)
        if cached is None:
            return None
        
        # 检查是否过期
        timestamp = cached.get("timestamp", 0)
        ttl = self._cache_ttl.get(cache_type, 3600)
        
        if time.time() - timestamp > ttl:
            # 缓存过期，删除
            del cache_store[cache_key]
            return None
        
        # 缓存命中
        self._cache_stats[f"{cache_type}_hits"] += 1
        return cached.get("data")
    
    def _set_cache(
        self, 
        cache_key: str, 
        data: Any, 
        cache_type: str
    ) -> None:
        """设置缓存"""
        if not self.enable_cache:
            return
        
        cache_store = self._get_cache_store(cache_type)
        if not cache_store:
            return
        
        cache_store[cache_key] = {
            "data": data,
            "timestamp": time.time(),
        }
    
    def _get_cache_store(self, cache_type: str) -> Optional[Dict[str, Any]]:
        """获取缓存存储"""
        cache_stores = {
            "query": self._query_cache,
            "knowledge": self._knowledge_cache,
            "reasoning": self._reasoning_cache,
        }
        return cache_stores.get(cache_type)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_queries = self._cache_stats["query_hits"] + self._cache_stats["query_misses"]
        total_knowledge = self._cache_stats["knowledge_hits"] + self._cache_stats["knowledge_misses"]
        total_reasoning = self._cache_stats["reasoning_hits"] + self._cache_stats["reasoning_misses"]
        
        return {
            "query": {
                "hits": self._cache_stats["query_hits"],
                "misses": self._cache_stats["query_misses"],
                "hit_rate": self._cache_stats["query_hits"] / total_queries if total_queries > 0 else 0,
                "cache_size": len(self._query_cache),
            },
            "knowledge": {
                "hits": self._cache_stats["knowledge_hits"],
                "misses": self._cache_stats["knowledge_misses"],
                "hit_rate": self._cache_stats["knowledge_hits"] / total_knowledge if total_knowledge > 0 else 0,
                "cache_size": len(self._knowledge_cache),
            },
            "reasoning": {
                "hits": self._cache_stats["reasoning_hits"],
                "misses": self._cache_stats["reasoning_misses"],
                "hit_rate": self._cache_stats["reasoning_hits"] / total_reasoning if total_reasoning > 0 else 0,
                "cache_size": len(self._reasoning_cache),
            },
        }
    
    def clear_cache(self, cache_type: Optional[str] = None) -> None:
        """清空缓存"""
        if cache_type:
            cache_store = self._get_cache_store(cache_type)
            if cache_store:
                cache_store.clear()
        else:
            self._query_cache.clear()
            self._knowledge_cache.clear()
            self._reasoning_cache.clear()
