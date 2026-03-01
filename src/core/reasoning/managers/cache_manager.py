"""
LLM缓存管理器
管理LLM响应的缓存，支持多种缓存策略和内容验证
"""
import logging
import hashlib
import time
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheEntry:
    """缓存条目"""

    def __init__(self, key: str, value: Any, ttl_seconds: int = 3600):
        self.key = key
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.last_accessed = datetime.now()

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        return datetime.now() - self.created_at > timedelta(seconds=self.ttl_seconds)

    def access(self):
        """记录访问"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'key': self.key,
            'value': self.value,
            'created_at': self.created_at.isoformat(),
            'ttl_seconds': self.ttl_seconds,
            'access_count': self.access_count,
            'last_accessed': self.last_accessed.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """从字典创建"""
        entry = cls(
            key=data['key'],
            value=data['value'],
            ttl_seconds=data['ttl_seconds']
        )
        entry.created_at = datetime.fromisoformat(data['created_at'])
        entry.access_count = data.get('access_count', 0)
        entry.last_accessed = datetime.fromisoformat(data.get('last_accessed', data['created_at']))
        return entry


class LLMCacheManager:
    """LLM缓存管理器"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl

        # 缓存统计
        self.stats = {
            'total_entries': 0,
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_cleanups': 0
        }

        # 内容验证器
        self.content_validators = []

        logger.info(f"✅ LLM缓存管理器初始化完成，最大容量: {max_size}")

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        self._cleanup_expired()

        if key in self.cache:
            entry = self.cache[key]

            # 验证内容是否仍然有效
            if self._validate_content(entry.value, key):
                entry.access()
                self.stats['hits'] += 1
                return entry.value
            else:
                # 内容无效，移除缓存
                del self.cache[key]
                self.stats['misses'] += 1
                logger.debug(f"缓存内容无效，已移除: {key}")
                return None
        else:
            self.stats['misses'] += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            # 验证内容
            if not self._validate_content(value, key):
                logger.debug(f"内容验证失败，不缓存: {key}")
                return False

            # 检查容量限制
            if len(self.cache) >= self.max_size:
                self._evict_entries()

            # 创建缓存条目
            ttl = ttl_seconds or self.default_ttl
            entry = CacheEntry(key, value, ttl)
            self.cache[key] = entry
            self.stats['total_entries'] = len(self.cache)

            logger.debug(f"✅ 缓存已设置: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存条目"""
        if key in self.cache:
            del self.cache[key]
            self.stats['total_entries'] = len(self.cache)
            return True
        return False

    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.stats['total_entries'] = 0
        logger.info("✅ 缓存已清空")

    def cleanup_expired(self) -> int:
        """清理过期条目"""
        return self._cleanup_expired()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        stats = self.stats.copy()
        total_requests = stats['hits'] + stats['misses']
        if total_requests > 0:
            stats['hit_rate'] = stats['hits'] / total_requests * 100
        else:
            stats['hit_rate'] = 0.0

        stats['current_size'] = len(self.cache)
        stats['max_size'] = self.max_size
        stats['utilization_rate'] = len(self.cache) / self.max_size * 100

        return stats

    def add_content_validator(self, validator_func):
        """添加内容验证器"""
        self.content_validators.append(validator_func)
        logger.info(f"✅ 内容验证器已添加，现在有{len(self.content_validators)}个验证器")

    def remove_content_validator(self, validator_func):
        """移除内容验证器"""
        if validator_func in self.content_validators:
            self.content_validators.remove(validator_func)
            logger.info(f"✅ 内容验证器已移除")

    def _validate_content(self, content: Any, key: str) -> bool:
        """验证缓存内容是否仍然有效"""
        if not self.content_validators:
            return True  # 没有验证器，默认有效

        try:
            for validator in self.content_validators:
                if not validator(content, key):
                    return False
            return True
        except Exception as e:
            logger.warning(f"内容验证失败 {key}: {e}")
            return False

    def _cleanup_expired(self) -> int:
        """清理过期条目"""
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.stats['expired_cleanups'] += len(expired_keys)
            self.stats['total_entries'] = len(self.cache)
            logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")

        return len(expired_keys)

    def _evict_entries(self, count: int = 1):
        """驱逐缓存条目（使用LRU策略）"""
        # 按最后访问时间排序
        entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed
        )

        # 驱逐最少使用的条目
        for i in range(min(count, len(entries))):
            key, _ = entries[i]
            del self.cache[key]
            self.stats['evictions'] += 1

        self.stats['total_entries'] = len(self.cache)
        logger.debug(f"驱逐了 {count} 个缓存条目")

    def get_popular_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最热门的缓存键"""
        entries = [
            {
                'key': key,
                'access_count': entry.access_count,
                'last_accessed': entry.last_accessed.isoformat(),
                'age_seconds': (datetime.now() - entry.created_at).total_seconds()
            }
            for key, entry in self.cache.items()
        ]

        # 按访问次数排序
        return sorted(entries, key=lambda x: x['access_count'], reverse=True)[:limit]

    def preload_cache(self, data: Dict[str, Any]):
        """预加载缓存数据"""
        loaded_count = 0
        for key, entry_data in data.items():
            try:
                entry = CacheEntry.from_dict(entry_data)
                if not entry.is_expired:
                    self.cache[key] = entry
                    loaded_count += 1
            except Exception as e:
                logger.warning(f"加载缓存条目失败 {key}: {e}")

        self.stats['total_entries'] = len(self.cache)
        logger.info(f"✅ 已预加载 {loaded_count} 个缓存条目")

    def export_cache(self) -> Dict[str, Any]:
        """导出缓存数据"""
        return {
            'entries': {
                key: entry.to_dict() for key, entry in self.cache.items()
            },
            'stats': self.get_stats(),
            'exported_at': datetime.now().isoformat()
        }

    def set_max_size(self, max_size: int):
        """设置最大缓存容量"""
        self.max_size = max_size
        # 如果当前大小超过新限制，立即驱逐
        while len(self.cache) > self.max_size:
            self._evict_entries()
        logger.info(f"✅ 最大缓存容量已设置为: {max_size}")

    def set_default_ttl(self, ttl_seconds: int):
        """设置默认TTL"""
        self.default_ttl = ttl_seconds
        logger.info(f"✅ 默认TTL已设置为: {ttl_seconds}秒")

    # 内置内容验证器
    def add_default_validators(self):
        """添加默认的内容验证器"""
        # 验证响应不为空
        def not_empty_validator(content, key):
            return content is not None and str(content).strip() != ""

        # 验证响应不包含错误信息
        def no_error_validator(content, key):
            content_str = str(content).lower()
            error_indicators = ['error', 'failed', 'exception', 'sorry']
            return not any(indicator in content_str for indicator in error_indicators)

        self.add_content_validator(not_empty_validator)
        self.add_content_validator(no_error_validator)

        logger.info("✅ 默认内容验证器已添加")
