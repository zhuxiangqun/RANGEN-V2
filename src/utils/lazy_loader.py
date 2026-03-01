#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
延迟加载器
提供延迟加载功能
"""

from typing import Any, Callable, Optional, Dict
import threading
import time

class LazyLoader:
    """延迟加载器"""
    
    def __init__(self, loader_func: Callable, *args, **kwargs):
        self.loader_func = loader_func
        self.args = args
        self.kwargs = kwargs
        self._value = None
        self._loaded = False
        self._lock = threading.RLock()
    
    def get(self) -> Any:
        """获取值，如果未加载则加载"""
        with self._lock:
            if not self._loaded:
                self._value = self.loader_func(*self.args, **self.kwargs)
                self._loaded = True
            return self._value
    
    def is_loaded(self) -> bool:
        """检查是否已加载"""
        return self._loaded
    
    def reset(self):
        """重置加载器"""
        with self._lock:
            self._value = None
            self._loaded = False

class LazyManager:
    """延迟管理器"""
    
    def __init__(self):
        self.loaders: Dict[str, LazyLoader] = {}
        self.lock = threading.RLock()
    
    def register_loader(self, name: str, loader_func: Callable, *args, **kwargs) -> LazyLoader:
        """注册延迟加载器"""
        with self.lock:
            loader = LazyLoader(loader_func, *args, **kwargs)
            self.loaders[name] = loader
            return loader
    
    def get_loader(self, name: str) -> Optional[LazyLoader]:
        """获取延迟加载器"""
        with self.lock:
            return self.loaders.get(name)
    
    def get_value(self, name: str) -> Any:
        """获取值"""
        loader = self.get_loader(name)
        if loader:
            return loader.get()
        return None
    
    def is_loaded(self, name: str) -> bool:
        """检查是否已加载"""
        loader = self.get_loader(name)
        if loader:
            return loader.is_loaded()
        return False
    
    def reset_loader(self, name: str):
        """重置加载器"""
        loader = self.get_loader(name)
        if loader:
            loader.reset()

# 全局管理器实例
_lazy_manager = None

def get_lazy_manager() -> LazyManager:
    """获取延迟管理器实例"""
    global _lazy_manager
    if _lazy_manager is None:
        _lazy_manager = LazyManager()
    return _lazy_manager

# 版本信息
__version__ = "1.0"
__author__ = "RANGEN Team"