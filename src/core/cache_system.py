"""
缓存系统

为文档同步系统提供高效的缓存机制，减少重复计算和I/O操作。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
import pickle
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    data: Any
    timestamp: datetime
    ttl: int  # Time to live in seconds
    access_count: int = 0
    last_accessed: datetime = None
    size_bytes: int = 0

    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl <= 0:
            return False  # 永不过期
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl

    def is_stale(self, max_age_seconds: int = 3600) -> bool:
        """检查是否过时（基于最后访问时间）"""
        if not self.last_accessed:
            return False
        return (datetime.now() - self.last_accessed).total_seconds() > max_age_seconds


@dataclass
class CacheStats:
    """缓存统计信息"""
    total_entries: int = 0
    total_size_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    hit_rate: float = 0.0


class CacheSystem:
    """缓存系统"""

    def __init__(self, max_size_mb: float = 100.0, default_ttl: int = 3600,
                 cache_dir: str = "data/cache"):
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.default_ttl = default_ttl
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 内存缓存
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.stats = CacheStats()

        # 持久化存储
        self.persistence_file = self.cache_dir / "cache_data.pkl"
        self.stats_file = self.cache_dir / "cache_stats.json"

        # 线程锁
        self.lock = threading.Lock()

        # 执行器用于异步I/O
        self.executor = ThreadPoolExecutor(max_workers=2)

        # 加载持久化缓存
        self._load_persistent_cache()

        logger.info(f"缓存系统初始化完成: 最大大小 {max_size_mb}MB, 默认TTL {default_ttl}秒")

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存数据"""
        with self.lock:
            if key in self.memory_cache:
                entry = self.memory_cache[key]

                if entry.is_expired():
                    # 过期删除
                    del self.memory_cache[key]
                    self.stats.eviction_count += 1
                    self.stats.miss_count += 1
                    return default

                # 更新访问信息
                entry.access_count += 1
                entry.last_accessed = datetime.now()
                self.stats.hit_count += 1

                return entry.data
            else:
                self.stats.miss_count += 1
                return default

    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存数据"""
        if ttl is None:
            ttl = self.default_ttl

        # 计算数据大小
        try:
            size_bytes = len(pickle.dumps(data))
        except:
            size_bytes = 1024  # 默认1KB

        entry = CacheEntry(
            key=key,
            data=data,
            timestamp=datetime.now(),
            ttl=ttl,
            size_bytes=size_bytes
        )

        with self.lock:
            # 检查是否超过最大大小
            if self._would_exceed_size(size_bytes):
                self._evict_entries(size_bytes)

            # 设置缓存
            self.memory_cache[key] = entry
            self.stats.total_entries = len(self.memory_cache)
            self._update_total_size()

        return True

    def delete(self, key: str) -> bool:
        """删除缓存数据"""
        with self.lock:
            if key in self.memory_cache:
                del self.memory_cache[key]
                self.stats.total_entries = len(self.memory_cache)
                self._update_total_size()
                return True
        return False

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.memory_cache.clear()
            self.stats = CacheStats()
            logger.info("缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            # 计算命中率
            total_requests = self.stats.hit_count + self.stats.miss_count
            if total_requests > 0:
                self.stats.hit_rate = self.stats.hit_count / total_requests

            return {
                'total_entries': self.stats.total_entries,
                'total_size_mb': self.stats.total_size_bytes / (1024 * 1024),
                'max_size_mb': self.max_size_bytes / (1024 * 1024),
                'hit_count': self.stats.hit_count,
                'miss_count': self.stats.miss_count,
                'eviction_count': self.stats.eviction_count,
                'hit_rate': f"{self.stats.hit_rate:.2%}",
                'utilization': f"{(self.stats.total_size_bytes / self.max_size_bytes * 100):.1f}%"
            }

    async def persist_cache(self) -> None:
        """持久化缓存数据"""
        def _persist():
            try:
                # 保存缓存数据
                cache_data = {}
                for key, entry in self.memory_cache.items():
                    if not entry.is_expired():
                        cache_data[key] = {
                            'data': entry.data,
                            'timestamp': entry.timestamp.isoformat(),
                            'ttl': entry.ttl,
                            'access_count': entry.access_count,
                            'last_accessed': entry.last_accessed.isoformat() if entry.last_accessed else None,
                            'size_bytes': entry.size_bytes
                        }

                with open(self.persistence_file, 'wb') as f:
                    pickle.dump(cache_data, f)

                # 保存统计信息
                stats_data = {
                    'total_entries': self.stats.total_entries,
                    'total_size_bytes': self.stats.total_size_bytes,
                    'hit_count': self.stats.hit_count,
                    'miss_count': self.stats.miss_count,
                    'eviction_count': self.stats.eviction_count,
                    'hit_rate': self.stats.hit_rate,
                    'last_updated': datetime.now().isoformat()
                }

                with open(self.stats_file, 'w', encoding='utf-8') as f:
                    json.dump(stats_data, f, indent=2, ensure_ascii=False)

                logger.debug(f"缓存已持久化: {len(cache_data)} 条目")

            except Exception as e:
                logger.error(f"缓存持久化失败: {e}")

        # 在线程池中执行
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(self.executor, _persist)

    def _load_persistent_cache(self) -> None:
        """加载持久化缓存"""
        try:
            if not self.persistence_file.exists():
                return

            with open(self.persistence_file, 'rb') as f:
                cache_data = pickle.load(f)

            for key, entry_data in cache_data.items():
                try:
                    timestamp = datetime.fromisoformat(entry_data['timestamp'])
                    last_accessed = None
                    if entry_data.get('last_accessed'):
                        last_accessed = datetime.fromisoformat(entry_data['last_accessed'])

                    entry = CacheEntry(
                        key=key,
                        data=entry_data['data'],
                        timestamp=timestamp,
                        ttl=entry_data['ttl'],
                        access_count=entry_data.get('access_count', 0),
                        last_accessed=last_accessed,
                        size_bytes=entry_data.get('size_bytes', 1024)
                    )

                    # 检查是否过期
                    if not entry.is_expired():
                        self.memory_cache[key] = entry

                except Exception as e:
                    logger.warning(f"加载缓存条目失败 {key}: {e}")

            self._update_total_size()
            logger.info(f"已加载持久化缓存: {len(self.memory_cache)} 条目")

        except Exception as e:
            logger.error(f"加载持久化缓存失败: {e}")

    def _would_exceed_size(self, additional_bytes: int) -> bool:
        """检查是否会超过大小限制"""
        return self.stats.total_size_bytes + additional_bytes > self.max_size_bytes

    def _evict_entries(self, required_bytes: int) -> None:
        """驱逐缓存条目"""
        # 简单的LRU驱逐策略
        entries = list(self.memory_cache.items())

        # 按最后访问时间排序（最旧的先驱逐）
        entries.sort(key=lambda x: x[1].last_accessed or x[1].timestamp)

        freed_bytes = 0
        evicted_keys = []

        for key, entry in entries:
            if freed_bytes >= required_bytes:
                break

            freed_bytes += entry.size_bytes
            evicted_keys.append(key)
            self.stats.eviction_count += 1

        # 删除驱逐的条目
        for key in evicted_keys:
            del self.memory_cache[key]

        logger.debug(f"驱逐了 {len(evicted_keys)} 个缓存条目，释放 {freed_bytes} 字节")

    def _update_total_size(self) -> None:
        """更新总大小统计"""
        self.stats.total_size_bytes = sum(
            entry.size_bytes for entry in self.memory_cache.values()
        )

    async def cleanup_expired_entries(self) -> int:
        """清理过期条目"""
        expired_keys = []

        with self.lock:
            for key, entry in self.memory_cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self.memory_cache[key]

            if expired_keys:
                self.stats.total_entries = len(self.memory_cache)
                self._update_total_size()
                logger.info(f"清理了 {len(expired_keys)} 个过期缓存条目")

        return len(expired_keys)

    async def optimize_cache(self) -> Dict[str, Any]:
        """优化缓存"""
        # 清理过期条目
        expired_count = await self.cleanup_expired_entries()

        # 清理低频访问的条目
        stale_count = await self._cleanup_stale_entries()

        # 整理内存碎片（这里可以添加更复杂的优化逻辑）

        return {
            'expired_cleaned': expired_count,
            'stale_cleaned': stale_count,
            'final_entries': len(self.memory_cache),
            'final_size_mb': self.stats.total_size_bytes / (1024 * 1024)
        }

    async def _cleanup_stale_entries(self, max_age_hours: int = 24) -> int:
        """清理陈旧条目"""
        stale_keys = []
        max_age_seconds = max_age_hours * 3600

        with self.lock:
            for key, entry in self.memory_cache.items():
                if entry.is_stale(max_age_seconds):
                    stale_keys.append(key)

            for key in stale_keys:
                del self.memory_cache[key]

            if stale_keys:
                self.stats.total_entries = len(self.memory_cache)
                self._update_total_size()
                logger.debug(f"清理了 {len(stale_keys)} 个陈旧缓存条目")

        return len(stale_keys)


# 全局缓存实例
_cache_instance = None

def get_cache_system() -> CacheSystem:
    """获取缓存系统实例"""
    global _cache_instance
    if _cache_instance is None:
        # 这里可以从配置中读取参数
        _cache_instance = CacheSystem()
    return _cache_instance
