#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一存储抽象层 - 受Paperclip启发的多后端存储系统

设计原则：
1. 统一接口：为不同存储后端提供一致的API
2. 可插拔架构：支持多种存储后端（内存、文件、Redis、数据库等）
3. 类型安全：支持类型提示和序列化/反序列化
4. 异步支持：原生支持异步操作
5. 错误处理：统一的错误处理和重试机制

示例用法：

# 创建存储实例
storage = StorageFactory.create_storage("file", path="data/config.json")

# 存储数据
await storage.save("llm_models", {"deepseek-reasoner": {...}})

# 加载数据
models = await storage.load("llm_models")

# 集成到声明式配置系统
registry = get_config_registry()
registry.set_storage(storage)  # 自动持久化配置
"""

import json
import pickle
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Type, TypeVar, Generic, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
import threading
import hashlib
import inspect

logger = logging.getLogger(__name__)

T = TypeVar('T')
StorageData = Dict[str, Any]


@dataclass
class StorageConfig:
    """存储配置"""
    backend_type: str  # "memory", "file", "redis", "database"
    backend_options: Dict[str, Any] = field(default_factory=dict)
    auto_save: bool = True
    save_interval: float = 30.0  # 自动保存间隔（秒）
    max_retries: int = 3
    retry_delay: float = 1.0
    compression: bool = False
    encryption: bool = False
    encryption_key: Optional[str] = None
    
    def validate(self):
        """验证配置"""
        if self.backend_type not in ["memory", "file", "redis", "database"]:
            raise ValueError(f"不支持的存储后端类型: {self.backend_type}")
        
        if self.encryption and not self.encryption_key:
            raise ValueError("启用加密时需要提供encryption_key")
        
        return True


class StorageError(Exception):
    """存储错误基类"""
    pass


class StorageBackend(ABC):
    """存储后端抽象基类"""
    
    @abstractmethod
    async def save(self, key: str, data: StorageData) -> bool:
        """保存数据"""
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[StorageData]:
        """加载数据"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """删除数据"""
        pass
    
    @abstractmethod
    async def list_keys(self) -> List[str]:
        """列出所有键"""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """清空所有数据"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    async def close(self):
        """关闭连接/资源"""
        pass


class MemoryStorageBackend(StorageBackend):
    """内存存储后端"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._data: Dict[str, StorageData] = {}
        self._lock = threading.RLock()
        self._config = config or {}
        self._stats = {
            "saves": 0,
            "loads": 0,
            "deletes": 0,
            "total_keys": 0,
            "created_at": datetime.now().isoformat()
        }
    
    async def save(self, key: str, data: StorageData) -> bool:
        with self._lock:
            self._data[key] = data
            self._stats["saves"] += 1
            self._stats["total_keys"] = len(self._data)
            logger.debug(f"内存存储保存: {key}")
            return True
    
    async def load(self, key: str) -> Optional[StorageData]:
        with self._lock:
            data = self._data.get(key)
            if data:
                self._stats["loads"] += 1
                logger.debug(f"内存存储加载: {key}")
            return data
    
    async def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._stats["deletes"] += 1
                self._stats["total_keys"] = len(self._data)
                logger.debug(f"内存存储删除: {key}")
                return True
            return False
    
    async def list_keys(self) -> List[str]:
        with self._lock:
            return list(self._data.keys())
    
    async def exists(self, key: str) -> bool:
        with self._lock:
            return key in self._data
    
    async def clear(self) -> bool:
        with self._lock:
            self._data.clear()
            self._stats["total_keys"] = 0
            logger.debug("内存存储已清空")
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return self._stats.copy()
    
    async def close(self):
        """内存存储无需关闭"""
        pass


class FileStorageBackend(StorageBackend):
    """文件存储后端"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        self.storage_dir = Path(config.get("storage_dir", "data/storage"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.file_extension = config.get("file_extension", ".json")
        self.encoding = config.get("encoding", "utf-8")
        self.pretty_print = config.get("pretty_print", True)
        self._lock = threading.RLock()
        self._stats = {
            "saves": 0,
            "loads": 0,
            "deletes": 0,
            "total_keys": 0,
            "total_size_bytes": 0,
            "created_at": datetime.now().isoformat()
        }
        self._update_stats()
    
    def _get_filepath(self, key: str) -> Path:
        """获取文件路径"""
        # 对键进行哈希以避免文件名问题
        key_hash = hashlib.md5(key.encode()).hexdigest()[:16]
        return self.storage_dir / f"{key_hash}{self.file_extension}"
    
    def _update_stats(self):
        """更新统计信息"""
        with self._lock:
            total_size = 0
            key_count = 0
            
            for file_path in self.storage_dir.glob(f"*{self.file_extension}"):
                if file_path.is_file():
                    key_count += 1
                    total_size += file_path.stat().st_size
            
            self._stats["total_keys"] = key_count
            self._stats["total_size_bytes"] = total_size
    
    async def save(self, key: str, data: StorageData) -> bool:
        filepath = self._get_filepath(key)
        
        try:
            # 序列化数据
            if self.file_extension == ".json":
                content = json.dumps(data, ensure_ascii=False, indent=2 if self.pretty_print else None)
            elif self.file_extension == ".pkl":
                content = pickle.dumps(data)
            else:
                # 默认为JSON
                content = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 写入文件
            with open(filepath, 'w' if self.file_extension == ".json" else 'wb', encoding=self.encoding if self.file_extension == ".json" else None) as f:
                f.write(content)
            
            with self._lock:
                self._stats["saves"] += 1
                self._update_stats()
            
            logger.debug(f"文件存储保存: {key} -> {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"文件存储保存失败 {key}: {e}")
            return False
    
    async def load(self, key: str) -> Optional[StorageData]:
        filepath = self._get_filepath(key)
        
        if not filepath.exists():
            return None
        
        try:
            # 读取文件
            mode = 'r' if self.file_extension == ".json" else 'rb'
            with open(filepath, mode, encoding=self.encoding if self.file_extension == ".json" else None) as f:
                content = f.read()
            
            # 反序列化数据
            if self.file_extension == ".json":
                data = json.loads(content)
            elif self.file_extension == ".pkl":
                data = pickle.loads(content)
            else:
                # 尝试JSON
                try:
                    data = json.loads(content)
                except:
                    # 尝试pickle
                    try:
                        data = pickle.loads(content.encode() if isinstance(content, str) else content)
                    except:
                        logger.error(f"无法解析文件内容: {filepath}")
                        return None
            
            with self._lock:
                self._stats["loads"] += 1
            
            logger.debug(f"文件存储加载: {key} <- {filepath}")
            return data
            
        except Exception as e:
            logger.error(f"文件存储加载失败 {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        filepath = self._get_filepath(key)
        
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            
            with self._lock:
                self._stats["deletes"] += 1
                self._update_stats()
            
            logger.debug(f"文件存储删除: {key} -> {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"文件存储删除失败 {key}: {e}")
            return False
    
    async def list_keys(self) -> List[str]:
        """注意：由于使用哈希文件名，无法恢复原始键名"""
        # 文件存储后端不支持列出原始键名
        # 可以维护一个索引文件，但为了简单起见返回空列表
        return []
    
    async def exists(self, key: str) -> bool:
        filepath = self._get_filepath(key)
        return filepath.exists()
    
    async def clear(self) -> bool:
        try:
            for file_path in self.storage_dir.glob(f"*{self.file_extension}"):
                if file_path.is_file():
                    file_path.unlink()
            
            with self._lock:
                self._update_stats()
            
            logger.debug("文件存储已清空")
            return True
            
        except Exception as e:
            logger.error(f"文件存储清空失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return self._stats.copy()
    
    async def close(self):
        """文件存储无需关闭"""
        pass


class RedisStorageBackend(StorageBackend):
    """Redis存储后端（存根实现）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._connected = False
        self._redis_client = None
        self._lock = threading.RLock()
        self._stats = {
            "saves": 0,
            "loads": 0,
            "deletes": 0,
            "total_keys": 0,
            "connected": False,
            "created_at": datetime.now().isoformat()
        }
    
    async def _ensure_connected(self):
        """确保Redis连接"""
        if self._connected and self._redis_client:
            return True
        
        try:
            import redis.asyncio as redis
            
            host = self._config.get("host", "localhost")
            port = self._config.get("port", 6379)
            db = self._config.get("db", 0)
            password = self._config.get("password")
            ssl = self._config.get("ssl", False)
            
            self._redis_client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                ssl=ssl,
                decode_responses=False  # 保持字节数据
            )
            
            # 测试连接
            await self._redis_client.ping()
            self._connected = True
            self._stats["connected"] = True
            
            logger.info(f"Redis存储已连接: {host}:{port}/{db}")
            return True
            
        except ImportError:
            logger.error("未安装redis库: pip install redis")
            return False
        except Exception as e:
            logger.error(f"Redis连接失败: {e}")
            return False
    
    async def save(self, key: str, data: StorageData) -> bool:
        if not await self._ensure_connected():
            return False
        
        try:
            # 序列化数据
            serialized = pickle.dumps(data)
            
            # 保存到Redis
            await self._redis_client.set(key, serialized)
            
            with self._lock:
                self._stats["saves"] += 1
                # 更新总键数（近似值）
                total_keys = await self._redis_client.dbsize()
                self._stats["total_keys"] = total_keys
            
            logger.debug(f"Redis存储保存: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Redis存储保存失败 {key}: {e}")
            return False
    
    async def load(self, key: str) -> Optional[StorageData]:
        if not await self._ensure_connected():
            return None
        
        try:
            # 从Redis加载
            serialized = await self._redis_client.get(key)
            
            if serialized is None:
                return None
            
            # 反序列化数据
            data = pickle.loads(serialized)
            
            with self._lock:
                self._stats["loads"] += 1
            
            logger.debug(f"Redis存储加载: {key}")
            return data
            
        except Exception as e:
            logger.error(f"Redis存储加载失败 {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        if not await self._ensure_connected():
            return False
        
        try:
            result = await self._redis_client.delete(key)
            deleted = result > 0
            
            if deleted:
                with self._lock:
                    self._stats["deletes"] += 1
                    total_keys = await self._redis_client.dbsize()
                    self._stats["total_keys"] = total_keys
                
                logger.debug(f"Redis存储删除: {key}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Redis存储删除失败 {key}: {e}")
            return False
    
    async def list_keys(self) -> List[str]:
        if not await self._ensure_connected():
            return []
        
        try:
            # 注意：在生产环境中，SCAN比KEYS更安全
            keys = []
            async for key in self._redis_client.scan_iter("*"):
                if isinstance(key, bytes):
                    keys.append(key.decode('utf-8'))
                else:
                    keys.append(key)
            
            return keys
            
        except Exception as e:
            logger.error(f"Redis存储列出键失败: {e}")
            return []
    
    async def exists(self, key: str) -> bool:
        if not await self._ensure_connected():
            return False
        
        try:
            exists = await self._redis_client.exists(key)
            return exists > 0
            
        except Exception as e:
            logger.error(f"Redis存储检查存在失败 {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        if not await self._ensure_connected():
            return False
        
        try:
            await self._redis_client.flushdb()
            
            with self._lock:
                self._stats["total_keys"] = 0
            
            logger.debug("Redis存储已清空")
            return True
            
        except Exception as e:
            logger.error(f"Redis存储清空失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return self._stats.copy()
    
    async def close(self):
        if self._redis_client:
            await self._redis_client.close()
            self._connected = False
            self._stats["connected"] = False
            logger.debug("Redis存储已关闭")


class DatabaseStorageBackend(StorageBackend):
    """数据库存储后端（存根实现）"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        self._connected = False
        self._engine = None
        self._session = None
        self._lock = threading.RLock()
        self._stats = {
            "saves": 0,
            "loads": 0,
            "deletes": 0,
            "total_keys": 0,
            "connected": False,
            "created_at": datetime.now().isoformat()
        }
    
    async def _ensure_connected(self):
        """确保数据库连接"""
        if self._connected:
            return True
        
        try:
            # 这里简化实现，实际需要SQLAlchemy等
            logger.warning("DatabaseStorageBackend为存根实现，需要完整SQLAlchemy集成")
            self._connected = True
            self._stats["connected"] = True
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    async def save(self, key: str, data: StorageData) -> bool:
        logger.warning("DatabaseStorageBackend.save为存根实现")
        return False
    
    async def load(self, key: str) -> Optional[StorageData]:
        logger.warning("DatabaseStorageBackend.load为存根实现")
        return None
    
    async def delete(self, key: str) -> bool:
        logger.warning("DatabaseStorageBackend.delete为存根实现")
        return False
    
    async def list_keys(self) -> List[str]:
        logger.warning("DatabaseStorageBackend.list_keys为存根实现")
        return []
    
    async def exists(self, key: str) -> bool:
        logger.warning("DatabaseStorageBackend.exists为存根实现")
        return False
    
    async def clear(self) -> bool:
        logger.warning("DatabaseStorageBackend.clear为存根实现")
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return self._stats.copy()
    
    async def close(self):
        self._connected = False
        self._stats["connected"] = False
        logger.debug("数据库存储已关闭")


class Storage:
    """统一存储接口"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._backend: Optional[StorageBackend] = None
        self._auto_save_task: Optional[asyncio.Task] = None
        self._dirty_keys: Set[str] = set()
        self._cache: Dict[str, StorageData] = {}
        self._lock = threading.RLock()
        self._init_backend()
    
    def _init_backend(self):
        """初始化存储后端"""
        backend_type = self.config.backend_type
        
        if backend_type == "memory":
            self._backend = MemoryStorageBackend(self.config.backend_options)
        elif backend_type == "file":
            self._backend = FileStorageBackend(self.config.backend_options)
        elif backend_type == "redis":
            self._backend = RedisStorageBackend(self.config.backend_options)
        elif backend_type == "database":
            self._backend = DatabaseStorageBackend(self.config.backend_options)
        else:
            raise ValueError(f"不支持的存储后端类型: {backend_type}")
        
        logger.info(f"存储后端已初始化: {backend_type}")
        
        # 启动自动保存任务
        if self.config.auto_save:
            self._start_auto_save()
    
    def _start_auto_save(self):
        """启动自动保存任务"""
        async def auto_save_loop():
            while True:
                await asyncio.sleep(self.config.save_interval)
                await self._flush_dirty_keys()
        
        self._auto_save_task = asyncio.create_task(auto_save_loop())
        logger.debug(f"自动保存任务已启动，间隔: {self.config.save_interval}秒")
    
    async def _flush_dirty_keys(self):
        """刷新脏键到存储后端"""
        if not self._dirty_keys:
            return
        
        with self._lock:
            dirty_keys = list(self._dirty_keys)
            self._dirty_keys.clear()
        
        for key in dirty_keys:
            if key in self._cache:
                try:
                    success = await self._backend.save(key, self._cache[key])
                    if not success:
                        # 保存失败，重新标记为脏键
                        with self._lock:
                            self._dirty_keys.add(key)
                except Exception as e:
                    logger.error(f"自动保存失败 {key}: {e}")
                    with self._lock:
                        self._dirty_keys.add(key)
    
    async def save(self, key: str, data: StorageData, immediate: bool = False) -> bool:
        """保存数据"""
        with self._lock:
            self._cache[key] = data
            
            if immediate:
                # 立即保存
                try:
                    success = await self._backend.save(key, data)
                    if success:
                        logger.debug(f"立即保存成功: {key}")
                    return success
                except Exception as e:
                    logger.error(f"立即保存失败 {key}: {e}")
                    self._dirty_keys.add(key)
                    return False
            else:
                # 标记为脏键，稍后自动保存
                self._dirty_keys.add(key)
                logger.debug(f"标记为脏键: {key}")
                return True
    
    async def load(self, key: str, use_cache: bool = True) -> Optional[StorageData]:
        """加载数据"""
        # 首先检查缓存
        if use_cache and key in self._cache:
            logger.debug(f"从缓存加载: {key}")
            return self._cache[key]
        
        # 从后端加载
        try:
            data = await self._backend.load(key)
            if data is not None:
                with self._lock:
                    self._cache[key] = data
                logger.debug(f"从后端加载: {key}")
            return data
        except Exception as e:
            logger.error(f"加载失败 {key}: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """删除数据"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
            if key in self._dirty_keys:
                self._dirty_keys.remove(key)
        
        try:
            success = await self._backend.delete(key)
            if success:
                logger.debug(f"删除成功: {key}")
            return success
        except Exception as e:
            logger.error(f"删除失败 {key}: {e}")
            return False
    
    async def list_keys(self) -> List[str]:
        """列出所有键"""
        try:
            return await self._backend.list_keys()
        except Exception as e:
            logger.error(f"列出键失败: {e}")
            return []
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        with self._lock:
            if key in self._cache:
                return True
        
        try:
            return await self._backend.exists(key)
        except Exception as e:
            logger.error(f"检查存在失败 {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """清空所有数据"""
        with self._lock:
            self._cache.clear()
            self._dirty_keys.clear()
        
        try:
            success = await self._backend.clear()
            if success:
                logger.debug("存储已清空")
            return success
        except Exception as e:
            logger.error(f"清空失败: {e}")
            return False
    
    async def flush(self) -> bool:
        """强制刷新所有脏键到存储后端"""
        success = True
        with self._lock:
            dirty_keys = list(self._dirty_keys)
        
        for key in dirty_keys:
            if key in self._cache:
                try:
                    key_success = await self._backend.save(key, self._cache[key])
                    if not key_success:
                        success = False
                    else:
                        with self._lock:
                            self._dirty_keys.remove(key)
                except Exception as e:
                    logger.error(f"刷新失败 {key}: {e}")
                    success = False
        
        logger.debug(f"刷新完成，成功: {success}")
        return success
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        backend_stats = self._backend.get_stats() if self._backend else {}
        
        with self._lock:
            stats = {
                "config": asdict(self.config),
                "cache_size": len(self._cache),
                "dirty_keys": len(self._dirty_keys),
                "backend_type": self.config.backend_type,
                "auto_save_enabled": self.config.auto_save,
                "auto_save_interval": self.config.save_interval,
            }
            stats.update(backend_stats)
        
        return stats
    
    async def close(self):
        """关闭存储"""
        # 刷新所有脏键
        await self.flush()
        
        # 停止自动保存任务
        if self._auto_save_task:
            self._auto_save_task.cancel()
            try:
                await self._auto_save_task
            except asyncio.CancelledError:
                pass
            self._auto_save_task = None
        
        # 关闭后端
        if self._backend:
            await self._backend.close()
        
        logger.info("存储已关闭")


class StorageFactory:
    """存储工厂"""
    
    @staticmethod
    def create_storage(config: Union[StorageConfig, Dict[str, Any]]) -> Storage:
        """创建存储实例"""
        if isinstance(config, dict):
            config = StorageConfig(**config)
        
        config.validate()
        return Storage(config)
    
    @staticmethod
    def create_memory_storage(**kwargs) -> Storage:
        """创建内存存储"""
        config = StorageConfig(
            backend_type="memory",
            backend_options=kwargs
        )
        return StorageFactory.create_storage(config)
    
    @staticmethod
    def create_file_storage(
        storage_dir: str = "data/storage",
        file_extension: str = ".json",
        **kwargs
    ) -> Storage:
        """创建文件存储"""
        backend_options = {
            "storage_dir": storage_dir,
            "file_extension": file_extension,
            **kwargs
        }
        
        config = StorageConfig(
            backend_type="file",
            backend_options=backend_options
        )
        return StorageFactory.create_storage(config)
    
    @staticmethod
    def create_redis_storage(
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        ssl: bool = False,
        **kwargs
    ) -> Storage:
        """创建Redis存储"""
        backend_options = {
            "host": host,
            "port": port,
            "db": db,
            "password": password,
            "ssl": ssl,
            **kwargs
        }
        
        config = StorageConfig(
            backend_type="redis",
            backend_options=backend_options
        )
        return StorageFactory.create_storage(config)
    
    @staticmethod
    def get_default_storage() -> Storage:
        """获取默认存储（文件存储）"""
        return StorageFactory.create_file_storage()


# 全局默认存储实例
_default_storage: Optional[Storage] = None


def get_default_storage() -> Storage:
    """获取全局默认存储实例"""
    global _default_storage
    if _default_storage is None:
        _default_storage = StorageFactory.get_default_storage()
    return _default_storage


def set_default_storage(storage: Storage):
    """设置全局默认存储实例"""
    global _default_storage
    _default_storage = storage


async def close_default_storage():
    """关闭全局默认存储实例"""
    global _default_storage
    if _default_storage:
        await _default_storage.close()
        _default_storage = None


# ============================================================================
# 存储适配器（兼容现有ConfigStore）
# ============================================================================

class StorageConfigStoreAdapter:
    """存储适配器，使Storage兼容现有的ConfigStore接口"""
    
    def __init__(self, storage: Storage, namespace: str = "config"):
        self.storage = storage
        self.namespace = namespace
        self._full_key = f"{namespace}:store"
    
    def save_config(self, config: Dict[str, Any]) -> str:
        """保存配置"""
        # 同步版本（简化）
        import asyncio
        version_id = f"v{hash(json.dumps(config, sort_keys=True)) % 1000000:06d}"
        
        config_data = {
            "config": config,
            "version_id": version_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 同步保存
        success = asyncio.run(self.storage.save(self._full_key, config_data, immediate=True))
        return version_id if success else ""
    
    async def save_config_async(self, config: Dict[str, Any]) -> str:
        """异步保存配置"""
        version_id = f"v{hash(json.dumps(config, sort_keys=True)) % 1000000:06d}"
        
        config_data = {
            "config": config,
            "version_id": version_id,
            "timestamp": datetime.now().isoformat()
        }
        
        success = await self.storage.save(self._full_key, config_data, immediate=True)
        return version_id if success else ""
    
    def load_config(self) -> Optional[Dict[str, Any]]:
        """加载配置"""
        import asyncio
        data = asyncio.run(self.storage.load(self._full_key, use_cache=True))
        return data.get("config") if data else None
    
    async def load_config_async(self) -> Optional[Dict[str, Any]]:
        """异步加载配置"""
        data = await self.storage.load(self._full_key, use_cache=True)
        return data.get("config") if data else None
    
    def get_config_versions(self) -> List[str]:
        """获取配置版本（简化实现）"""
        # 实际实现需要存储多个版本
        data = self.load_config()
        if data:
            return ["latest"]
        return []
    
    def rollback_to_version(self, version: str) -> Optional[Dict[str, Any]]:
        """回滚到指定版本（简化实现）"""
        # 实际实现需要存储多个版本
        if version == "latest":
            return self.load_config()
        return None