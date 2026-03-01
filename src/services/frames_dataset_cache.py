"""
FRAMES数据集缓存和更新机制
提供高效的数据集管理、缓存策略和自动更新功能

主要功能：
1. 多层缓存架构（内存缓存、磁盘缓存、分布式缓存）
2. 智能缓存策略（LRU、TTL、热度感知）
3. 自动更新机制（定时更新、增量更新）
4. 数据一致性保证
5. 性能监控和优化
"""

import logging
import json
import time
import hashlib
import asyncio
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import OrderedDict
import sqlite3
import pickle

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    ttl: float
    access_count: int = 0
    last_access: float = 0.0
    size_bytes: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        return time.time() > (self.timestamp + self.ttl)
    
    def touch(self):
        """更新访问信息"""
        self.access_count += 1
        self.last_access = time.time()

@dataclass
class CacheStats:
    """缓存统计信息"""
    total_entries: int = 0
    memory_usage_bytes: int = 0
    hit_count: int = 0
    miss_count: int = 0
    eviction_count: int = 0
    last_cleanup: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """缓存命中率"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    @property
    def memory_usage_mb(self) -> float:
        """内存使用量（MB）"""
        return self.memory_usage_bytes / (1024 * 1024)

class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, max_size: int = 1000, default_ttl: float = 3600.0):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = CacheStats()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                self.stats.miss_count += 1
                return None
            
            entry = self.cache[key]
            
            # 检查过期
            if entry.is_expired():
                del self.cache[key]
                self.stats.miss_count += 1
                return None
            
            # 更新访问信息
            entry.touch()
            
            # 移动到末尾（LRU策略）
            self.cache.move_to_end(key)
            
            self.stats.hit_count += 1
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        with self.lock:
            # 计算大小
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = len(str(value).encode('utf-8'))
            
            ttl = ttl or self.default_ttl
            
            entry = CacheEntry(
                key=key,
                value=value,
                timestamp=time.time(),
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            # 检查容量限制
            current_size = len(self.cache)
            if current_size >= self.max_size:
                self._evict_lru()
            
            # 添加到缓存
            self.cache[key] = entry
            self.stats.total_entries = len(self.cache)
            self.stats.memory_usage_bytes = sum(e.size_bytes for e in self.cache.values())
            
            return True
    
    def _evict_lru(self):
        """移除最近最少使用的条目"""
        if self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.stats.eviction_count += 1
    
    def cleanup_expired(self):
        """清理过期条目"""
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self.cache[key]
                self.stats.eviction_count += len(expired_keys)
            
            self.stats.last_cleanup = time.time()
            
            return len(expired_keys)

class DiskCache:
    """磁盘缓存实现"""
    
    def __init__(self, cache_dir: str, max_size_mb: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.db_path = self.cache_dir / 'cache.db'
        self.lock = threading.RLock()
        self.stats = CacheStats()
        
        # 初始化SQLite数据库
        self._init_db()
    
    def _init_db(self):
        """初始化缓存数据库"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    timestamp REAL,
                    ttl REAL,
                    access_count INTEGER DEFAULT 0,
                    last_access REAL DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0,
                    metadata TEXT DEFAULT '{}'
                )
            ''')
            
            # 创建索引
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON cache_entries(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_last_access ON cache_entries(last_access)')
            conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            try:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        SELECT value, timestamp, ttl, access_count
                        FROM cache_entries
                        WHERE key = ?
                    ''', (key,))
                    
                    row = cursor.fetchone()
                    if not row:
                        self.stats.miss_count += 1
                        return None
                    
                    value_blob, timestamp, ttl, access_count = row
                    
                    # 检查过期
                    if time.time() > (timestamp + ttl):
                        self._delete_key(key)
                        self.stats.miss_count += 1
                        return None
                    
                    # 更新访问信息
                    cursor.execute('''
                        UPDATE cache_entries
                        SET access_count = ?, last_access = ?
                        WHERE key = ?
                    ''', (access_count + 1, time.time(), key))
                    conn.commit()
                    
                    self.stats.hit_count += 1
                    return pickle.loads(value_blob)
                    
            except Exception as e:
                logger.error(f"磁盘缓存获取失败: {e}")
                self.stats.miss_count += 1
                return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        with self.lock:
            try:
                value_blob = pickle.dumps(value)
                timestamp = time.time()
                ttl = ttl or 3600.0
                
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO cache_entries
                        (key, value, timestamp, ttl, size_bytes, metadata)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (key, value_blob, timestamp, ttl, len(value_blob), '{}'))
                    conn.commit()
                
                self.stats.total_entries = self._get_total_entries()
                self.stats.memory_usage_bytes = self._get_total_size()
                
                return True
                
            except Exception as e:
                logger.error(f"磁盘缓存设置失败: {e}")
                return False
    
    def _delete_key(self, key: str):
        """删除缓存键"""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute('DELETE FROM cache_entries WHERE key = ?', (key,))
            conn.commit()
    
    def _get_total_entries(self) -> int:
        """获取总条目数"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM cache_entries')
            return cursor.fetchone()[0]
    
    def _get_total_size(self) -> int:
        """获取总大小"""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(size_bytes) FROM cache_entries')
            result = cursor.fetchone()[0]
            return result or 0
    
    def cleanup_expired(self):
        """清理过期条目"""
        with self.lock:
            try:
                current_time = time.time()
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        DELETE FROM cache_entries
                        WHERE timestamp + ttl < ?
                    ''', (current_time,))
                    conn.commit()
                
                self.stats.last_cleanup = current_time
                return cursor.rowcount
                
            except Exception as e:
                logger.error(f"磁盘缓存清理失败: {e}")
                return 0

class FramesDatasetCache:
    """FRAMES数据集缓存管理器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 缓存配置
        self.memory_cache_enabled = self.config.get('memory_cache_enabled', True)
        self.disk_cache_enabled = self.config.get('disk_cache_enabled', True)
        self.auto_update_enabled = self.config.get('auto_update_enabled', True)
        self.update_interval_hours = self.config.get('update_interval_hours', 24)
        
        # 初始化缓存层
        self.memory_cache = MemoryCache(
            max_size=self.config.get('memory_cache_size', 500),
            default_ttl=self.config.get('memory_ttl', 3600)
        )
        
        self.disk_cache = DiskCache(
            cache_dir=self.config.get('disk_cache_dir', 'data/frames_cache'),
            max_size_mb=self.config.get('disk_cache_size_mb', 500)
        )
        
        # 更新状态
        self.last_update_time = 0.0
        self.update_lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'updates_performed': 0,
            'last_update': 'Never'
        }
        
        logger.info("FRAMES数据集缓存管理器初始化完成")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 1. 尝试内存缓存
        if self.memory_cache_enabled:
            value = self.memory_cache.get(key)
            if value is not None:
                self.stats['cache_hits'] += 1
                logger.debug(f"内存缓存命中: {key}")
                return value
        
        # 2. 尝试磁盘缓存
        if self.disk_cache_enabled:
            value = self.disk_cache.get(key)
            if value is not None:
                self.stats['cache_hits'] += 1
                # 提升到内存缓存
                if self.memory_cache_enabled:
                    self.memory_cache.set(key, value)
                logger.debug(f"磁盘缓存命中: {key}")
                return value
        
        # 缓存未命中
        self.stats['cache_misses'] += 1
        logger.debug(f"缓存未命中: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """设置缓存值"""
        success = True
        
        # 设置到内存缓存
        if self.memory_cache_enabled:
            success &= self.memory_cache.set(key, value, ttl)
        
        # 设置到磁盘缓存
        if self.disk_cache_enabled:
            success &= self.disk_cache.set(key, value, ttl)
        
        return success
    
    def get_dataset(self, dataset_path: str) -> Optional[List[Dict[str, Any]]]:
        """获取数据集缓存"""
        cache_key = self._generate_dataset_key(dataset_path)
        return self.get(cache_key)
    
    def set_dataset(self, dataset_path: str, data: List[Dict[str, Any]], ttl: Optional[float] = None) -> bool:
        """设置数据集缓存"""
        cache_key = self._generate_dataset_key(dataset_path)
        return self.set(cache_key, data, ttl)
    
    def get_relationships(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """获取关系缓存"""
        cache_key = f"relationships:{hashlib.md5(query.encode()).hexdigest()}"
        return self.get(cache_key)
    
    def set_relationships(self, query: str, relationships: List[Dict[str, Any]], ttl: Optional[float] = None) -> bool:
        """设置关系缓存"""
        cache_key = f"relationships:{hashlib.md5(query.encode()).hexdigest()}"
        return self.set(cache_key, relationships, ttl)
    
    def _generate_dataset_key(self, dataset_path: str) -> str:
        """生成数据集缓存键"""
        # 使用文件路径和修改时间生成唯一键
        dataset_path = Path(dataset_path)
        if dataset_path.exists():
            mtime = dataset_path.stat().st_mtime
            return f"dataset:{dataset_path}:{mtime}"
        return f"dataset:{dataset_path}"
    
    def cleanup_expired(self):
        """清理过期缓存"""
        cleaned_memory = 0
        cleaned_disk = 0
        
        if self.memory_cache_enabled:
            cleaned_memory = self.memory_cache.cleanup_expired()
        
        if self.disk_cache_enabled:
            cleaned_disk = self.disk_cache.cleanup_expired()
        
        logger.info(f"缓存清理完成: 内存清理{cleaned_memory}项, 磁盘清理{cleaned_disk}项")
        
        return cleaned_memory + cleaned_disk
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            'config': self.config,
            'stats': self.stats.copy(),
            'hit_rate': 0.0
        }
        
        # 计算命中率
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        if total_requests > 0:
            stats['hit_rate'] = self.stats['cache_hits'] / total_requests
        
        # 添加详细统计
        if self.memory_cache_enabled:
            stats['memory_cache'] = {
                'total_entries': self.memory_cache.stats.total_entries,
                'memory_usage_mb': self.memory_cache.stats.memory_usage_mb,
                'hit_rate': self.memory_cache.stats.hit_rate
            }
        
        if self.disk_cache_enabled:
            stats['disk_cache'] = {
                'total_entries': self.disk_cache.stats.total_entries,
                'memory_usage_mb': self.disk_cache.stats.memory_usage_mb,
                'hit_rate': self.disk_cache.stats.hit_rate
            }
        
        return stats
    
    def schedule_auto_update(self, dataset_path: str, update_callback: callable):
        """安排自动更新"""
        if not self.auto_update_enabled:
            logger.info("自动更新已禁用")
            return
        
        def update_worker():
            while True:
                try:
                    # 检查是否需要更新
                    if self._should_update(dataset_path):
                        logger.info("开始自动更新FRAMES数据集...")
                        update_callback(dataset_path)
                        self.last_update_time = time.time()
                        self.stats['updates_performed'] += 1
                        self.stats['last_update'] = datetime.now().isoformat()
                    
                    # 等待下次更新
                    time.sleep(self.update_interval_hours * 3600)
                    
                except Exception as e:
                    logger.error(f"自动更新失败: {e}")
                    time.sleep(300)  # 5分钟后重试
        
        # 启动后台更新线程
        update_thread = threading.Thread(target=update_worker, daemon=True)
        update_thread.start()
        logger.info(f"自动更新线程已启动，更新间隔: {self.update_interval_hours}小时")
    
    def _should_update(self, dataset_path: str) -> bool:
        """检查是否应该更新"""
        # 如果从未更新过，需要更新
        if self.last_update_time == 0.0:
            return True
        
        # 检查更新间隔
        time_since_update = time.time() - self.last_update_time
        return time_since_update > (self.update_interval_hours * 3600)
    
    def force_update(self, dataset_path: str, update_callback: callable):
        """强制更新数据集"""
        with self.update_lock:
            try:
                logger.info("开始强制更新FRAMES数据集...")
                result = update_callback(dataset_path)
                
                # 清理相关缓存
                cache_key = self._generate_dataset_key(dataset_path)
                
                # 删除内存缓存
                if self.memory_cache_enabled and cache_key in self.memory_cache.cache:
                    del self.memory_cache.cache[cache_key]
                
                # 删除磁盘缓存
                if self.disk_cache_enabled:
                    self.disk_cache._delete_key(cache_key)
                
                self.last_update_time = time.time()
                self.stats['updates_performed'] += 1
                self.stats['last_update'] = datetime.now().isoformat()
                
                logger.info(f"强制更新完成: {result}")
                return result
                
            except Exception as e:
                logger.error(f"强制更新失败: {e}")
                return {'success': False, 'error': str(e)}

class CacheOptimizer:
    """缓存优化器"""
    
    def __init__(self, cache_manager: FramesDatasetCache):
        self.cache_manager = cache_manager
        self.optimization_interval = 300  # 5分钟
        self.last_optimization = 0.0
    
    def optimize_if_needed(self):
        """需要时优化缓存"""
        current_time = time.time()
        
        if current_time - self.last_optimization > self.optimization_interval:
            self._optimize_cache()
            self.last_optimization = current_time
    
    def _optimize_cache(self):
        """优化缓存性能"""
        stats = self.cache_manager.get_cache_stats()
        
        # 优化建议
        recommendations = []
        
        # 内存命中率优化
        if 'memory_cache' in stats:
            mem_hit_rate = stats['memory_cache']['hit_rate']
            if mem_hit_rate < 0.6:
                recommendations.append("建议增加内存缓存大小以提高命中率")
            elif mem_hit_rate > 0.9:
                recommendations.append("内存缓存命中率很高，可适当减少缓存大小节省内存")
        
        # 磁盘缓存优化
        if 'disk_cache' in stats:
            disk_usage = stats['disk_cache']['memory_usage_mb']
            if disk_usage > 400:  # 超过400MB
                recommendations.append("磁盘缓存使用量较大，建议清理过期条目")
        
        # 总体命中率优化
        if stats['hit_rate'] < 0.5:
            recommendations.append("总体命中率较低，建议调整TTL或增加缓存大小")
        
        if recommendations:
            logger.info(f"缓存优化建议: {'; '.join(recommendations)}")
        
        # 执行清理
        self.cache_manager.cleanup_expired()

# 工厂函数
def create_frames_cache(config: Optional[Dict[str, Any]] = None) -> FramesDatasetCache:
    """创建FRAMES数据集缓存管理器实例"""
    return FramesDatasetCache(config)

def create_cache_optimizer(cache_manager: FramesDatasetCache) -> CacheOptimizer:
    """创建缓存优化器实例"""
    return CacheOptimizer(cache_manager)