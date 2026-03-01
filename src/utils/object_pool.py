#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
对象池管理器
提供对象池的创建和管理功能
"""

from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass
import threading
import time
import logging
from threading import RLock

@dataclass
class ObjectPool:
    """对象池"""
    name: str
    max_size: int
    objects: Optional[List[Any]] = None
    lock: Optional[RLock] = None
    
    def __post_init__(self):
        if self.objects is None:
            self.objects = []
        if self.lock is None:
            self.lock = RLock()
        self.created_count = 0

class ObjectPoolManager:
    """对象池管理器"""
    
    def __init__(self):
        self.pools: Dict[str, ObjectPool] = {}
        self.lock = threading.RLock()
    
    def create_pool(self, name: str, max_size: int = 100) -> ObjectPool:
        """创建对象池"""
        return self.create_component(name, max_size)
    
    def create_component(self, name: str, max_size: int = 100) -> ObjectPool:
        """创建对象池"""
        with self.lock:
            if name in self.pools:
                return self.pools[name]
            
            pool = ObjectPool(
                name=name,
                max_size=max_size
            )
            self.pools[name] = pool
            return pool
    
    def get_pool(self, name: str) -> Optional[ObjectPool]:
        """获取对象池"""
        with self.lock:
            return self.pools.get(name)
    
    def get_object(self, pool_name: str, factory_func=None):
        """从对象池获取对象"""
        try:
            pool = self.get_pool(pool_name)
            if not pool:
                return None
            
            # 尝试从池中获取对象
            if pool.objects:
                return pool.objects.pop()
            
            # 如果池为空且提供了工厂函数，创建新对象
            if factory_func:
                return factory_func()
            
            return None
            
        except Exception as e:
            logger.error(f"获取对象失败: {e}")
            return None
    
    def return_object(self, pool_name: str, obj: Any):
        """将对象返回到对象池"""
        pool = self.get_pool(pool_name)
        if not pool:
            return False
        
        if pool.lock is None:
            pool.lock = RLock()
        with pool.lock:
            if pool.objects is None:
                pool.objects = []
            if len(pool.objects) < pool.max_size:
                pool.objects.append(obj)
                return True
        
        return False

# 全局管理器实例
_pool_manager = None

def get_pool_manager() -> ObjectPoolManager:
    """获取对象池管理器实例"""
    global _pool_manager
    if _pool_manager is None:
        _pool_manager = ObjectPoolManager()
    return _pool_manager

def create_component(name: str = "dict_pool", max_size: int = 100) -> ObjectPool:
    """创建字典对象池"""
    manager = get_pool_manager()
    return manager.create_pool(name, max_size)

def create_list_pool(name: str = "list_pool", max_size: int = 100) -> ObjectPool:
    """创建列表对象池"""
    manager = get_pool_manager()
    return manager.create_pool(name, max_size)
def create_set_pool(name: str = "set_pool", max_size: int = 100) -> ObjectPool:
    """创建集合对象池"""
    manager = get_pool_manager()
    return manager.create_pool(name, max_size)

# 版本信息
__version__ = "1.0"
__author__ = "RANGEN Team"

# 扩展ObjectPoolManager类的方法
def get_pool_status(self, pool_name: str) -> Optional[Dict[str, Any]]:
    """获取对象池状态"""
    try:
        pool = self.get_pool(pool_name)
        if not pool:
            return None
        
        with pool.lock:
            return {
                "name": pool.name,
                "max_size": pool.max_size,
                "current_size": len(pool.objects) if pool.objects else 0,
                "created_count": getattr(pool, 'created_count', 0),
                "utilization_rate": len(pool.objects) / pool.max_size if pool.objects else 0
            }
    except Exception as e:
        logger.error(f"获取对象池状态失败: {e}")
        return None

def get_all_pools_status(self) -> Dict[str, Dict[str, Any]]:
    """获取所有对象池状态"""
    try:
        with self.lock:
            status = {}
            for name, pool in self.pools.items():
                pool_status = self.get_pool_status(name)
                if pool_status:
                    status[name] = pool_status
            return status
    except Exception as e:
        logger.error(f"获取所有对象池状态失败: {e}")
        return {}

def clear_pool(self, pool_name: str) -> bool:
    """清空对象池"""
    try:
        pool = self.get_pool(pool_name)
        if not pool:
            return False
        
        with pool.lock:
            if pool.objects:
                pool.objects.clear()
            pool.created_count = 0
            return True
    except Exception as e:
        logger.error(f"清空对象池失败: {e}")
        return False

def resize_pool(self, pool_name: str, new_size: int) -> bool:
    """调整对象池大小"""
    try:
        pool = self.get_pool(pool_name)
        if not pool:
            return False
        
        with pool.lock:
            old_size = pool.max_size
            pool.max_size = new_size
            
            # 如果新大小小于当前对象数量，移除多余对象
            if pool.objects and len(pool.objects) > new_size:
                pool.objects = pool.objects[:new_size]
            
            logger.info(f"对象池 {pool_name} 大小从 {old_size} 调整为 {new_size}")
            return True
    except Exception as e:
        logger.error(f"调整对象池大小失败: {e}")
        return False

def get_pool_metrics(self, pool_name: str) -> Optional[Dict[str, Any]]:
    """获取对象池指标"""
    try:
        pool = self.get_pool(pool_name)
        if not pool:
            return None
        
        with pool.lock:
            current_size = len(pool.objects) if pool.objects else 0
            created_count = getattr(pool, 'created_count', 0)
            
            return {
                "pool_name": pool_name,
                "max_size": pool.max_size,
                "current_size": current_size,
                "created_count": created_count,
                "utilization_rate": current_size / pool.max_size,
                "creation_rate": created_count / max(time.time() - getattr(pool, 'start_time', time.time()), 1),
                "available_objects": current_size,
                "total_capacity": pool.max_size
            }
    except Exception as e:
        logger.error(f"获取对象池指标失败: {e}")
        return None

def health_check(self) -> Dict[str, Any]:
    """健康检查"""
    try:
        with self.lock:
            total_pools = len(self.pools)
            healthy_pools = 0
            error_pools = 0
            
            for pool in self.pools.values():
                try:
                    with pool.lock:
                        if pool.objects is not None and len(pool.objects) >= 0:
                            healthy_pools += 1
                        else:
                            error_pools += 1
                except Exception:
                    error_pools += 1
            
            return {
                "status": "healthy" if error_pools == 0 else "degraded",
                "total_pools": total_pools,
                "healthy_pools": healthy_pools,
                "error_pools": error_pools,
                "timestamp": time.time()
            }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }

def cleanup_pools(self) -> int:
    """清理对象池"""
    try:
        cleaned_count = 0
        with self.lock:
            for name, pool in list(self.pools.items()):
                try:
                    with pool.lock:
                        if pool.objects:
                            pool.objects.clear()
                        pool.created_count = 0
                        cleaned_count += 1
                except Exception as e:
                    logger.warning(f"清理对象池 {name} 失败: {e}")
        
        return cleaned_count
    except Exception as e:
        logger.error(f"清理对象池失败: {e}")
        return 0

def get_manager_status(self) -> Dict[str, Any]:
    """获取管理器状态"""
    try:
        with self.lock:
            return {
                "total_pools": len(self.pools),
                "pool_names": list(self.pools.keys()),
                "timestamp": time.time()
            }
    except Exception as e:
        logger.error(f"获取管理器状态失败: {e}")
        return {"error": str(e)}

# 将方法添加到类中
ObjectPoolManager.get_pool_status = get_pool_status
ObjectPoolManager.get_all_pools_status = get_all_pools_status
ObjectPoolManager.clear_pool = clear_pool
ObjectPoolManager.resize_pool = resize_pool
ObjectPoolManager.get_pool_metrics = get_pool_metrics
ObjectPoolManager.health_check = health_check
ObjectPoolManager.cleanup_pools = cleanup_pools
ObjectPoolManager.get_manager_status = get_manager_status