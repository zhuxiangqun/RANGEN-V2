"""
显式缓存服务测试
"""
import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.explicit_cache_service import (
    ExplicitCacheService,
    QueryCacheService,
    CacheLevel,
    PrivacyLevel,
    get_explicit_cache,
    create_query_cache
)


class TestExplicitCacheService:
    """测试显式缓存服务"""

    def setup_method(self):
        """每个测试前设置"""
        self.cache = ExplicitCacheService({
            'ttl_seconds': 5,
            'max_size': 10
        })

    def test_cache_set_and_get(self):
        """测试基本的缓存设置和获取"""
        self.cache.set('key1', 'value1')
        result = self.cache.get('key1')
        assert result == 'value1'

    def test_cache_get_miss(self):
        """测试缓存未命中"""
        result = self.cache.get('nonexistent')
        assert result is None

    def test_cache_expiry(self):
        """测试缓存过期"""
        cache = ExplicitCacheService({'ttl_seconds': 1})
        cache.set('key', 'value')
        
        time.sleep(0.5)
        assert cache.get('key') == 'value'
        
        time.sleep(1)
        assert cache.get('key') is None

    def test_cache_delete(self):
        """测试缓存删除"""
        self.cache.set('key1', 'value1')
        assert self.cache.get('key1') == 'value1'
        
        self.cache.delete('key1')
        assert self.cache.get('key1') is None

    def test_cache_clear(self):
        """测试清空缓存"""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        count = self.cache.clear()
        assert count == 2
        assert self.cache.get('key1') is None
        assert self.cache.get('key2') is None

    def test_cache_stats(self):
        """测试缓存统计"""
        self.cache.set('key1', 'value1')
        self.cache.get('key1')
        self.cache.get('nonexistent')
        
        stats = self.cache.get_stats()
        assert stats['hits'] == 1
        assert stats['misses'] == 1
        assert stats['size'] == 1

    def test_privacy_check_personal(self):
        """测试隐私保护 - 个人数据不能缓存"""
        result = self.cache.set(
            'password', 'secret123',
            privacy_level=PrivacyLevel.PERSONAL
        )
        assert result is False
        assert self.cache.get('password') is None

    def test_privacy_check_keywords(self):
        """测试隐私保护 - 敏感关键词"""
        result = self.cache.set(
            'credit_card', '1234567890',
            privacy_level=PrivacyLevel.INTERNAL
        )
        assert result is False

    def test_max_size_eviction(self):
        """测试容量满时的驱逐"""
        cache = ExplicitCacheService({'max_size': 3})
        
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        
        cache.set('key4', 'value4')
        
        assert cache.get('key1') is None
        assert cache.get('key2') == 'value2'
        assert cache.get('key3') == 'value3'
        assert cache.get('key4') == 'value4'

    def test_lru_order(self):
        """测试LRU顺序"""
        self.cache.set('key1', 'value1')
        self.cache.set('key2', 'value2')
        
        self.cache.get('key1')
        
        self.cache.set('key3', 'value3')
        self.cache.set('key4', 'value4')
        
        assert self.cache.get('key2') is None


class TestQueryCacheService:
    """测试查询缓存服务"""

    def setup_method(self):
        """每个测试前设置"""
        self.cache = QueryCacheService({'ttl_seconds': 5})

    def test_cache_query(self):
        """测试缓存查询"""
        self.cache.cache_query('SELECT * FROM users', [{'id': 1}])
        
        result = self.cache.get_cached_result('SELECT * FROM users')
        assert result is not None
        assert result == [{'id': 1}]

    def test_query_normalization(self):
        """测试查询规范化"""
        self.cache.cache_query('SELECT * FROM users', [{'id': 1}])
        
        result = self.cache.get_cached_result('select * from   users')
        assert result is not None

    def test_cache_result(self):
        """测试通用结果缓存"""
        self.cache.cache_result('result1', {'data': 'value'})
        
        result = self.cache.get('result1')
        assert result == {'data': 'value'}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
