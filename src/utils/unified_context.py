#!/usr/bin/env python3
"""
统一上下文管理器
提供动态上下文管理和刷新功能
"""

import os
import logging
import threading
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum


class ContextType(Enum):
    """上下文类型"""
    USER_SESSION = "user_session"
    RESEARCH_CONTEXT = "research_context"
    SYSTEM_STATE = "system_state"
    CACHE_DATA = "cache_data"
    DYNAMIC_DATA = "dynamic_data"


class ContextPriority(Enum):
    """上下文优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ContextMetadata:
    """上下文元数据"""
    context_type: ContextType
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    refresh_interval: Optional[int] = None
    dependencies: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)
    priority: ContextPriority = ContextPriority.MEDIUM


@dataclass
class Context:
    """上下文数据"""
    id: str
    data: Any
    metadata: ContextMetadata
    ttl: Optional[int] = None


class UnifiedContextManager:
    """统一上下文管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.contexts: Dict[str, Context] = {}
        self.dynamic_contexts: Dict[str, Context] = {}
        self.context_dependencies: Dict[str, Set[str]] = defaultdict(set)
        self.management_stats: Dict[str, Any] = {
            "total_contexts": 0,
            "active_contexts": 0,
            "refresh_count": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
        
        # 配置参数
        self.max_contexts = int(os.getenv("MAX_CONTEXTS", "1000"))
        self.default_ttl = int(os.getenv("DEFAULT_TTL", "3600"))
        self.refresh_interval = int(os.getenv("REFRESH_INTERVAL", "60"))
        
        # 线程安全
        self.lock = threading.RLock()
        
        # 启动动态刷新线程
        self._start_refresh_worker()
        
        self.logger.info("统一上下文管理器初始化完成")
    
    def _start_refresh_worker(self):
        """启动刷新工作线程"""
        def refresh_worker():
            while True:
                try:
                    time.sleep(self.refresh_interval)
                    self._refresh_dynamic_contexts()
                except Exception as e:
                    self.logger.error(f"刷新工作线程错误: {e}")
        
        refresh_thread = threading.Thread(target=refresh_worker, daemon=True)
        refresh_thread.start()
        self.logger.info("动态上下文刷新线程已启动")
    
    def add_context(self, context_id: str, data: Any, context_type: ContextType, 
                   ttl: Optional[int] = None, refresh_interval: Optional[int] = None,
                   dependencies: Optional[List[str]] = None, 
                   triggers: Optional[List[str]] = None,
                   priority: ContextPriority = ContextPriority.MEDIUM) -> bool:
        """添加上下文"""
        try:
            with self.lock:
                # 检查上下文数量限制
                if len(self.contexts) >= self.max_contexts:
                    self._cleanup_expired_contexts()
                
                if len(self.contexts) >= self.max_contexts:
                    self.logger.warning(f"上下文数量已达上限: {self.max_contexts}")
                    return False
                
                # 创建上下文
                metadata = ContextMetadata(
                    context_type=context_type,
                    created_at=datetime.now(),
                    last_accessed=datetime.now(),
                    refresh_interval=refresh_interval,
                    dependencies=dependencies or [],
                    triggers=triggers or [],
                    priority=priority
                )
                
                context = Context(
                    id=context_id,
                    data=data,
                    metadata=metadata,
                    ttl=ttl or self.default_ttl
                )
                
                # 存储上下文
                if refresh_interval:
                    self.dynamic_contexts[context_id] = context
                else:
                    self.contexts[context_id] = context
                
                # 更新依赖关系
                for dep in metadata.dependencies:
                    self.context_dependencies[dep].add(context_id)
                
                # 更新统计
                self.management_stats["total_contexts"] += 1
                self.management_stats["active_contexts"] += 1
                
                self.logger.info(f"添加上下文: {context_id} (类型: {context_type.value})")
                return True
                
        except Exception as e:
            self.logger.error(f"添加上下文失败: {e}")
            return False
    
    def get_context(self, context_id: str) -> Optional[Any]:
        """获取上下文数据"""
        try:
            with self.lock:
                # 检查普通上下文
                if context_id in self.contexts:
                    context = self.contexts[context_id]
                    context.metadata.last_accessed = datetime.now()
                    context.metadata.access_count += 1
                    self.management_stats["cache_hits"] += 1
                    return context.data
                
                # 检查动态上下文
                if context_id in self.dynamic_contexts:
                    context = self.dynamic_contexts[context_id]
                    context.metadata.last_accessed = datetime.now()
                    context.metadata.access_count += 1
                    self.management_stats["cache_hits"] += 1
                    return context.data
                
                self.management_stats["cache_misses"] += 1
                return None
                
        except Exception as e:
            self.logger.error(f"获取上下文失败: {e}")
            return None
    
    def update_context(self, context_id: str, data: Any) -> bool:
        """更新上下文数据"""
        try:
            with self.lock:
                # 更新普通上下文
                if context_id in self.contexts:
                    self.contexts[context_id].data = data
                    self.contexts[context_id].metadata.last_accessed = datetime.now()
                    return True
                
                # 更新动态上下文
                if context_id in self.dynamic_contexts:
                    self.dynamic_contexts[context_id].data = data
                    self.dynamic_contexts[context_id].metadata.last_accessed = datetime.now()
                    return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"更新上下文失败: {e}")
            return False
    
    def remove_context(self, context_id: str) -> bool:
        """移除上下文"""
        try:
            with self.lock:
                removed = False
                
                # 移除普通上下文
                if context_id in self.contexts:
                    del self.contexts[context_id]
                    removed = True
                
                # 移除动态上下文
                if context_id in self.dynamic_contexts:
                    del self.dynamic_contexts[context_id]
                    removed = True
                
                # 清理依赖关系
                if context_id in self.context_dependencies:
                    del self.context_dependencies[context_id]
                
                # 更新统计
                if removed:
                    self.management_stats["active_contexts"] -= 1
                
                return removed
                
        except Exception as e:
            self.logger.error(f"移除上下文失败: {e}")
            return False
    
    def _refresh_dynamic_contexts(self):
        """刷新动态上下文"""
        try:
            with self.lock:
                current_time = datetime.now()
                refreshed_count = 0
                
                for context_id, context in list(self.dynamic_contexts.items()):
                    metadata = context.metadata
                    
                    # 检查是否需要刷新
                    if metadata.refresh_interval:
                        time_since_last_refresh = (
                            current_time - metadata.last_accessed
                        ).total_seconds()
                        
                        if time_since_last_refresh >= metadata.refresh_interval:
                            # 执行刷新逻辑
                            if self._execute_refresh_logic(context):
                                refreshed_count += 1
                                self.management_stats["refresh_count"] += 1
                
                if refreshed_count > 0:
                    self.logger.info(f"刷新了 {refreshed_count} 个动态上下文")
                    
        except Exception as e:
            self.logger.error(f"刷新动态上下文失败: {e}")
    
    def _execute_refresh_logic(self, context: Context) -> bool:
        """执行刷新逻辑"""
        try:
            # 这里可以实现具体的刷新逻辑
            # 例如：重新计算数据、从外部源获取最新数据等
            context.metadata.last_accessed = datetime.now()
            return True
        except Exception as e:
            self.logger.error(f"执行刷新逻辑失败: {e}")
            return False
    
    def _cleanup_expired_contexts(self):
        """清理过期上下文"""
        try:
            with self.lock:
                current_time = datetime.now()
                expired_contexts = []
                
                # 检查普通上下文
                for context_id, context in self.contexts.items():
                    if context.ttl:
                        time_since_creation = (
                            current_time - context.metadata.created_at
                        ).total_seconds()
                        
                        if time_since_creation >= context.ttl:
                            expired_contexts.append(context_id)
                
                # 检查动态上下文
                for context_id, context in self.dynamic_contexts.items():
                    if context.ttl:
                        time_since_creation = (
                            current_time - context.metadata.created_at
                        ).total_seconds()
                        
                        if time_since_creation >= context.ttl:
                            expired_contexts.append(context_id)
                
                # 移除过期上下文
                for context_id in expired_contexts:
                    self.remove_context(context_id)
                
                if expired_contexts:
                    self.logger.info(f"清理了 {len(expired_contexts)} 个过期上下文")
                    
        except Exception as e:
            self.logger.error(f"清理过期上下文失败: {e}")
    
    def get_context_stats(self) -> Dict[str, Any]:
        """获取上下文统计信息"""
        try:
            with self.lock:
                stats = self.management_stats.copy()
                stats.update({
                    "context_count": len(self.contexts),
                    "dynamic_context_count": len(self.dynamic_contexts),
                    "dependency_count": len(self.context_dependencies),
                    "memory_usage": self._calculate_memory_usage()
                })
                return stats
                
        except Exception as e:
            self.logger.error(f"获取上下文统计失败: {e}")
            return {}
    
    def _calculate_memory_usage(self) -> int:
        """计算内存使用量（估算）"""
        try:
            total_size = 0
            for context in self.contexts.values():
                total_size += len(str(context.data))
            for context in self.dynamic_contexts.values():
                total_size += len(str(context.data))
            return total_size
        except Exception:
            return 0
    
    def clear_all_contexts(self):
        """清空所有上下文"""
        try:
            with self.lock:
                self.contexts.clear()
                self.dynamic_contexts.clear()
                self.context_dependencies.clear()
                self.management_stats["active_contexts"] = 0
                self.logger.info("已清空所有上下文")
        except Exception as e:
            self.logger.error(f"清空上下文失败: {e}")
    
    def search_contexts(self, query: str, context_type: Optional[ContextType] = None) -> List[str]:
        """搜索上下文"""
        try:
            results = []
            query_lower = query.lower()
            
            with self.lock:
                # 搜索普通上下文
                for context_id, context in self.contexts.items():
                    if context_type and context.metadata.context_type != context_type:
                        continue
                    
                    if (query_lower in context_id.lower() or 
                        query_lower in str(context.data).lower()):
                        results.append(context_id)
                
                # 搜索动态上下文
                for context_id, context in self.dynamic_contexts.items():
                    if context_type and context.metadata.context_type != context_type:
                        continue
                    
                    if (query_lower in context_id.lower() or 
                        query_lower in str(context.data).lower()):
                        results.append(context_id)
            
            return results
            
        except Exception as e:
            self.logger.error(f"搜索上下文失败: {e}")
            return []


# 全局实例
unified_context_manager = UnifiedContextManager()


def get_context_manager() -> UnifiedContextManager:
    """获取统一上下文管理器实例"""
    return unified_context_manager


def create_context(context_id: str, data: Any, context_type: ContextType, 
                  ttl: Optional[int] = None, refresh_interval: Optional[int] = None,
                  dependencies: Optional[List[str]] = None, 
                  triggers: Optional[List[str]] = None,
                  priority: ContextPriority = ContextPriority.MEDIUM) -> bool:
    """创建上下文的便捷函数"""
    return unified_context_manager.add_context(
        context_id, data, context_type, ttl, refresh_interval,
        dependencies, triggers, priority
    )


def get_context(context_id: str) -> Optional[Any]:
    """获取上下文的便捷函数"""
    return unified_context_manager.get_context(context_id)


def update_context(context_id: str, data: Any) -> bool:
    """更新上下文的便捷函数"""
    return unified_context_manager.update_context(context_id, data)


def remove_context(context_id: str) -> bool:
    """移除上下文的便捷函数"""
    return unified_context_manager.remove_context(context_id)


if __name__ == "__main__":
    # 测试代码
    from src.utils.research_logger import log_info, log_warning, log_error, log_debug, UnifiedErrorHandler
    import logging
    logger = logging.getLogger(__name__)
    
    # 创建测试上下文
    create_context("test_user_001", {"api_key": "test_api_key_123"}, ContextType.USER_SESSION)
    
    # 获取上下文
    data = get_context("test_user_001")
    print(f"获取到的数据: {data}")
    
    # 获取统计信息
    stats = unified_context_manager.get_context_stats()
    print(f"上下文统计: {stats}")