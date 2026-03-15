"""
显式缓存服务 - 短期记忆层
Explicit Cache Service - Short-term Memory Layer

基于Context Engineering文章建议：
- 缓存过期策略：TTL（缓存有效期）别超过5分钟
- 隐私保护：含个人信息的数据，绝对不能缓存
- 效果：生产系统用"KV缓存"，直接让成本降10倍

核心功能：
1. KV缓存管理 - 重复问题秒回
2. TTL过期控制 - 防止旧信息误导
3. 隐私保护 - 敏感数据不缓存
4. 命中率统计 - 缓存效果分析
"""

import logging
import time
import hashlib
import json
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import OrderedDict
from threading import Lock
import threading

logger = logging.getLogger(__name__)


class CacheLevel(str, Enum):
    """缓存级别"""
    MEMORY = "memory"       # 内存缓存
    DISK = "disk"          # 磁盘缓存
    DISTRIBUTED = "distributed"  # 分布式缓存(Redis)


class PrivacyLevel(str, Enum):
    """隐私级别"""
    PUBLIC = "public"       # 公开数据
    INTERNAL = "internal"  # 内部数据
    SENSITIVE = "sensitive"  # 敏感数据
    PERSONAL = "personal"   # 个人数据 - 绝对不能缓存


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    access_count: int = 0
    last_accessed: float = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class CacheStats:
    """缓存统计"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    total_size: int = 0


class ExplicitCacheService:
    """
    显式缓存服务
    
    遵循文章建议：
    - 缓存过期策略：TTL别超过5分钟（300秒）
    - 隐私保护：含个人信息的数据，绝对不能缓存
    - 效果：重复问题响应速度提升8倍+
    """
    
    # 默认配置
    DEFAULT_TTL_SECONDS = 300  # 5分钟 - 文章建议值
    DEFAULT_MAX_SIZE = 1000     # 最大缓存条目数
    DEFAULT_CHECK_INTERVAL = 60  # 过期检查间隔
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # TTL配置（文章建议：不超过5分钟）
        self.ttl_seconds = self.config.get('ttl_seconds', self.DEFAULT_TTL_SECONDS)
        
        # 最大缓存大小
        self.max_size = self.config.get('max_size', self.DEFAULT_MAX_SIZE)
        
        # 缓存存储
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = Lock()
        
        # 统计
        self.stats = CacheStats()
        
        # 隐私关键词（这些数据不能缓存）
        self.privacy_keywords = [
            'password', 'pwd', 'secret', 'token', 'api_key',
            'credit_card', 'card_number', 'ssn', 'social_security',
            'phone', 'mobile', 'email', 'address', 'name',
            'id_card', 'passport', 'bank_account'
        ]
        
        # 缓存级别
        self.cache_level = self.config.get('cache_level', CacheLevel.MEMORY)
        
        # 过期检查线程
        self._cleanup_thread: Optional[threading.Thread] = None
        self._running = False
        
        logger.info(
            f"显式缓存服务初始化: TTL={self.ttl_seconds}秒, "
            f"最大条目={self.max_size}"
        )
    
    def start(self) -> None:
        """启动缓存服务"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True
        )
        self._cleanup_thread.start()
        
        logger.info("显式缓存服务已 def stop(self)启动")
    
    -> None:
        """停止缓存服务"""
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)
        
        logger.info("显式缓存服务已停止")
    
    def _cleanup_loop(self) -> None:
        """过期清理循环"""
        while self._running:
            try:
                time.sleep(self.DEFAULT_CHECK_INTERVAL)
                self._evict_expired()
            except Exception as e:
                logger.error(f"缓存清理错误: {e}")
    
    def _evict_expired(self) -> int:
        """清理过期条目"""
        now = time.time()
        evicted = 0
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if now >= entry.expires_at
            ]
            
            for key in expired_keys:
                del self._cache[key]
                evicted += 1
                self.stats.evictions += 1
        
        if evicted > 0:
            logger.debug(f"清理过期缓存条目: {evicted}")
        
        return evicted
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值
        
        遵循文章建议：
        - 缓存过期策略：防止旧信息误导
        """
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self.stats.misses += 1
                return None
            
            # 检查是否过期
            if time.time() >= entry.expires_at:
                del self._cache[key]
                self.stats.misses += 1
                self.stats.evictions += 1
                return None
            
            # 更新访问统计
            entry.access_count += 1
            entry.last_accessed = time.time()
            
            # 移动到末尾（LRU）
            self._cache.move_to_end(key)
            
            self.stats.hits += 1
            
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        privacy_level: PrivacyLevel = PrivacyLevel.INTERNAL,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        设置缓存值
        
        遵循文章建议：
        - 隐私保护：含个人信息的数据，绝对不能缓存
        """
        # 隐私检查
        if not self._check_privacy(key, value, privacy_level):
            logger.warning(f"隐私检查阻止缓存: {key}")
            return False
        
        # 使用默认TTL或自定义
        effective_ttl = ttl if ttl is not None else self.ttl_seconds
        
        now = time.time()
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=now,
            expires_at=now + effective_ttl,
            metadata=metadata or {}
        )
        
        with self._lock:
            # 如果已存在，更新
            if key in self._cache:
                del self._cache[key]
            
            # 检查是否需要驱逐
            while len(self._cache) >= self.max_size:
                # LRU驱逐：移除最老的
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self.stats.evictions += 1
            
            # 添加新条目
            self._cache[key] = entry
        
        logger.debug(f"缓存设置: {key}, TTL={effective_ttl}秒")
        return True
    
    def _check_privacy(
        self,
        key: str,
        value: Any,
        privacy_level: PrivacyLevel
    ) -> bool:
        """隐私检查"""
        # 个人数据绝对不能缓存
        if privacy_level == PrivacyLevel.PERSONAL:
            return False
        
        # 敏感数据需要明确允许
        if privacy_level == PrivacyLevel.SENSITIVE:
            return False
        
        # 检查关键词
        key_lower = key.lower()
        value_str = str(value).lower() if value else ""
        
        for keyword in self.privacy_keywords:
            if keyword in key_lower or keyword in value_str:
                logger.warning(f"检测到敏感关键词: {keyword}")
                return False
        
        return True
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False
    
    def clear(self) -> int:
        """清空缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            
            self.stats = CacheStats()  # 重置统计
            
            logger.info(f"缓存已清空: {count}条目")
            return count
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self.stats.hits + self.stats.misses
        hit_rate = self.stats.hits / total if total > 0 else 0
        
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'hit_rate': hit_rate,
            'evictions': self.stats.evictions,
            'size': len(self._cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'uptime_seconds': time.time()
        }
    
    def get_keys(self, pattern: Optional[str] = None) -> List[str]:
        """获取缓存键列表"""
        with self._lock:
            keys = list(self._cache.keys())
        
        if pattern:
            import re
            regex = re.compile(pattern)
            keys = [k for k in keys if regex.match(k)]
        
        return keys
    
    def get_entry_info(self, key: str) -> Optional[Dict]:
        """获取缓存条目信息"""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                return None
            
            now = time.time()
            remaining_ttl = max(0, entry.expires_at - now)
            
            return {
                'key': entry.key,
                'created_at': entry.created_at,
                'expires_at': entry.expires_at,
                'remaining_ttl': remaining_ttl,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed,
                'metadata': entry.metadata
            }


class QueryCacheService(ExplicitCacheService):
    """
    查询缓存服务 - 专门用于缓存重复查询
    
    遵循文章建议：
    - 重复问题的响应速度提升8倍+
    - TTL别超过5分钟
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 查询专用配置
        self.normalize_query = self.config.get('normalize_query', True)
        
        logger.info("查询缓存服务初始化完成")
    
    def _normalize_key(self, query: str) -> str:
        """规范化查询键"""
        if not self.normalize_query:
            return query
        
        # 规范化处理：小写、去除多余空格、排序
        normalized = ' '.join(query.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def cache_query(
        self,
        query: str,
        result: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """缓存查询结果"""
        key = self._normalize_key(query)
        
        return self.set(
            key=key,
            value={
                'query': query,
                'result': result,
                'cached_at': time.time()
            },
            ttl=ttl,
            privacy_level=PrivacyLevel.INTERNAL,
            metadata={'type': 'query'}
        )
    
    def get_cached_result(self, query: str) -> Optional[Any]:
        """获取缓存的查询结果"""
        key = self._normalize_key(query)
        
        cached = self.get(key)
        if cached:
            logger.info(f"查询缓存命中: {query[:50]}...")
            return cached.get('result')
        
        return None
    
    def cache_result(
        self,
        key: str,
        result: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """通用结果缓存"""
        return self.set(
            key=key,
            value=result,
            ttl=ttl,
            privacy_level=PrivacyLevel.INTERNAL,
            metadata={'type': 'result'}
        )


# 全局实例
_query_cache: Optional[QueryCacheService] = None
_explicit_cache: Optional[ExplicitCacheService] = None


def get_query_cache(config: Optional[Dict[str, Any]] = None) -> QueryCacheService:
    """获取查询缓存服务实例"""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCacheService(config)
        _query_cache.start()
    return _query_cache


def get_explicit_cache(config: Optional[Dict[str, Any]] = None) -> ExplicitCacheService:
    """获取显式缓存服务实例"""
    global _explicit_cache
    if _explicit_cache is None:
        _explicit_cache = ExplicitCacheService(config)
        _explicit_cache.start()
    return _explicit_cache


def create_query_cache(config: Optional[Dict[str, Any]] = None) -> QueryCacheService:
    """创建查询缓存服务实例"""
    service = QueryCacheService(config)
    service.start()
    return service
