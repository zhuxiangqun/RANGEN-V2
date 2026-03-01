#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强内存清理器
提供内存清理功能
"""

import gc
import sys
import threading
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

# 初始化日志
logger = logging.getLogger(__name__)

@dataclass
class MemoryCleanupContext:
    """内存清理上下文"""
    cleanup_type: str
    target_objects: Optional[List[Any]] = None
    force_gc: bool = True
    metadata: Optional[Dict[str, Any]] = None

class EnhancedMemoryCleaner:
    """内存清理器"""
    
    def __init__(self):
        self.cleanup_history: List[MemoryCleanupContext] = []
        self._lock = threading.RLock()
    
    def cleanup_memory(self, context: MemoryCleanupContext) -> bool:
        """清理内存"""
        try:
            with self._lock:
                # 记录清理历史
                self.cleanup_history.append(context)
                
                # 执行垃圾回收
                if context.force_gc:
                    collected = gc.collect()
                    logger.info(f"Garbage collection collected {collected} objects")
                
                # 清理特定对象
                if context.target_objects:
                    for obj in context.target_objects:
                        if hasattr(obj, '__del__'):
                            try:
                                del obj
                            except Exception as e:
                                logger.warning(f"Error deleting object: {e}")
                
                # 清理系统缓存
                if hasattr(sys, '_clear_type_cache'):
                    sys._clear_type_cache()
                
                logger.info(f"Memory cleanup completed for type: {context.cleanup_type}")
                return True
                
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
            return False
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            
            return {
                'rss': memory_info.rss,  # 常驻内存
                'vms': memory_info.vms,  # 虚拟内存
                'percent': process.memory_percent(),
                'available': psutil.virtual_memory().available
            }
        except ImportError:
            # 如果没有psutil，使用基本方法
            return {
                'rss': 0,
                'vms': 0,
                'percent': 0,
                'available': 0
            }
    
    def get_cleanup_history(self) -> List[MemoryCleanupContext]:
        """获取清理历史"""
        with self._lock:
            return self.cleanup_history.copy()
    
    def clear_history(self):
        """清空清理历史"""
        with self._lock:
            self.cleanup_history.clear()

# 全局清理器实例
_memory_cleaner = None

def get_memory_cleaner() -> EnhancedMemoryCleaner:
    """获取内存清理器实例"""
    global _memory_cleaner
    if _memory_cleaner is None:
        _memory_cleaner = EnhancedMemoryCleaner()
    return _memory_cleaner

# 版本信息
__version__ = "1.0"
__author__ = "RANGEN Team"