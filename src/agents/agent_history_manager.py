#!/usr/bin/env python3
"""
智能体历史管理器 - 负责历史记录的存储、检索和分析
"""
import time
import threading
import logging
import json
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import deque
from enum import Enum
import pickle
import hashlib


class HistoryType(Enum):
    """历史记录类型"""
    QUERY = "query"
    STRATEGY = "strategy"
    LEARNING = "learning"
    PERFORMANCE = "performance"
    ERROR = "error"
    ACTIVITY = "activity"
    DECISION = "decision"


@dataclass
class HistoryEntry:
    """历史记录条目"""
    entry_id: str
    entry_type: HistoryType
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    importance: float = 1.0  # 重要性评分 0-1
    
    def __post_init__(self):
        if not self.entry_id:
            # 生成唯一ID
            content = f"{self.entry_type.value}_{self.timestamp}_{hash(str(self.data))}"
            self.entry_id = hashlib.md5(content.encode()).hexdigest()[:16]


@dataclass
class HistoryQuery:
    """历史查询条件"""
    entry_types: Optional[List[HistoryType]] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    tags: Optional[List[str]] = None
    importance_min: Optional[float] = None
    importance_max: Optional[float] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    limit: Optional[int] = None
    offset: int = 0
    sort_by: str = "timestamp"  # timestamp, importance, entry_type
    sort_order: str = "desc"   # asc, desc


@dataclass
class HistoryStats:
    """历史统计信息"""
    total_entries: int
    entries_by_type: Dict[str, int]
    entries_by_tag: Dict[str, int]
    oldest_entry: Optional[float]
    newest_entry: Optional[float]
    average_importance: float
    storage_size_bytes: int
    last_cleanup: Optional[float]


class AgentHistoryManager:
    """智能体历史管理器 - 单一职责：历史记录管理"""
    
    def __init__(self, agent_id: str, max_entries: int = 10000,
                 cleanup_threshold: float = 0.8, persistence_enabled: bool = False):
        """
        初始化历史管理器
        
        Args:
            agent_id: 智能体ID
            max_entries: 最大条目数
            cleanup_threshold: 清理阈值（达到最大容量的百分比时触发清理）
            persistence_enabled: 是否启用持久化
        """
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"{__name__}.{agent_id}")
        
        # 存储配置
        self.max_entries = max_entries
        self.cleanup_threshold = cleanup_threshold
        self.persistence_enabled = persistence_enabled
        
        # 历史记录存储
        self._entries: deque = deque(maxlen=max_entries)
        self._entries_by_type: Dict[HistoryType, deque] = {
            entry_type: deque(maxlen=max_entries // 4) for entry_type in HistoryType
        }
        self._entries_by_tag: Dict[str, deque] = {}
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 索引
        self._type_index: Dict[HistoryType, List[str]] = {entry_type: [] for entry_type in HistoryType}
        self._tag_index: Dict[str, List[str]] = {}
        self._time_index: List[Tuple[float, str]] = []  # (timestamp, entry_id)
        
        # 统计信息
        self._stats = HistoryStats(
            total_entries=0,
            entries_by_type={entry_type.value: 0 for entry_type in HistoryType},
            entries_by_tag={},
            oldest_entry=None,
            newest_entry=None,
            average_importance=0.0,
            storage_size_bytes=0,
            last_cleanup=None
        )
        
        # 清理配置
        self._cleanup_strategies = {
            "by_importance": self._cleanup_by_importance,
            "by_time": self._cleanup_by_time,
            "by_type": self._cleanup_by_type
        }
        
        # 持久化路径
        if persistence_enabled:
            self._persistence_path = f".agent_history_{agent_id}.pkl"
            self._load_history()
        
        self.logger.info(f"历史管理器初始化完成: {agent_id}")
    
    def add_entry(self, entry_type: HistoryType, data: Dict[str, Any],
                  tags: Optional[List[str]] = None, importance: float = 1.0,
                  metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        添加历史记录
        
        Args:
            entry_type: 记录类型
            data: 记录数据
            tags: 标签列表
            importance: 重要性评分
            metadata: 元数据
            
        Returns:
            记录ID
        """
        with self._lock:
            # 创建历史记录
            entry = HistoryEntry(
                entry_id="",  # 将在__post_init__中生成
                entry_type=entry_type,
                timestamp=time.time(),
                data=data,
                metadata=metadata or {},
                tags=tags or [],
                importance=max(0.0, min(1.0, importance))
            )
            
            # 添加到存储
            self._add_to_storage(entry)
            
            # 更新索引
            self._update_indexes(entry)
            
            # 更新统计
            self._update_stats(entry)
            
            # 检查是否需要清理
            if self._should_cleanup():
                self._cleanup_history()
            
            # 持久化
            if self.persistence_enabled:
                self._save_history()
            
            return entry.entry_id
    
    def _add_to_storage(self, entry: HistoryEntry) -> None:
        """添加到存储"""
        self._entries.append(entry)
        self._entries_by_type[entry.entry_type].append(entry)
        
        # 按标签存储
        for tag in entry.tags:
            if tag not in self._entries_by_tag:
                self._entries_by_tag[tag] = deque(maxlen=self.max_entries // 10)
            self._entries_by_tag[tag].append(entry)
    
    def _update_indexes(self, entry: HistoryEntry) -> None:
        """更新索引"""
        # 类型索引
        self._type_index[entry.entry_type].append(entry.entry_id)
        
        # 标签索引
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(entry.entry_id)
        
        # 时间索引
        self._time_index.append((entry.timestamp, entry.entry_id))
        # 保持时间索引有序
        self._time_index.sort(key=lambda x: x[0])
    
    def _update_stats(self, entry: HistoryEntry) -> None:
        """更新统计信息"""
        self._stats.total_entries += 1
        self._stats.entries_by_type[entry.entry_type.value] += 1
        
        # 更新标签统计
        for tag in entry.tags:
            self._stats.entries_by_tag[tag] = self._stats.entries_by_tag.get(tag, 0) + 1
        
        # 更新时间范围
        if self._stats.oldest_entry is None or entry.timestamp < self._stats.oldest_entry:
            self._stats.oldest_entry = entry.timestamp
        if self._stats.newest_entry is None or entry.timestamp > self._stats.newest_entry:
            self._stats.newest_entry = entry.timestamp
        
        # 更新平均重要性
        total_importance = sum(e.importance for e in self._entries)
        self._stats.average_importance = total_importance / len(self._entries) if self._entries else 0.0
        
        # 估算存储大小
        self._stats.storage_size_bytes = len(pickle.dumps(self._entries))
    
    def _should_cleanup(self) -> bool:
        """检查是否需要清理"""
        return len(self._entries) >= self.max_entries * self.cleanup_threshold
    
    def _cleanup_history(self) -> None:
        """清理历史记录"""
        self.logger.info(f"开始清理历史记录，当前条目数: {len(self._entries)}")
        
        # 计算需要删除的条目数
        target_count = int(self.max_entries * 0.7)  # 清理到70%
        current_count = len(self._entries)
        entries_to_remove = current_count - target_count
        
        if entries_to_remove <= 0:
            return
        
        # 使用重要性策略清理
        removed_count = self._cleanup_by_importance(entries_to_remove)
        
        # 重建索引
        self._rebuild_indexes()
        
        # 更新统计
        self._stats.last_cleanup = time.time()
        
        self.logger.info(f"历史记录清理完成，删除了 {removed_count} 个条目")
    
    def _cleanup_by_importance(self, target_count: int) -> int:
        """按重要性清理"""
        # 按重要性排序，删除重要性较低的条目
        sorted_entries = sorted(self._entries, key=lambda e: e.importance)
        entries_to_remove = sorted_entries[:target_count]
        
        for entry in entries_to_remove:
            self._remove_entry(entry)
        
        return len(entries_to_remove)
    
    def _cleanup_by_time(self, target_count: int) -> int:
        """按时间清理（删除最旧的）"""
        sorted_entries = sorted(self._entries, key=lambda e: e.timestamp)
        entries_to_remove = sorted_entries[:target_count]
        
        for entry in entries_to_remove:
            self._remove_entry(entry)
        
        return len(entries_to_remove)
    
    def _cleanup_by_type(self, target_count: int) -> int:
        """按类型清理"""
        # 优先删除错误和活动记录
        priority_types = [HistoryType.ERROR, HistoryType.ACTIVITY, HistoryType.QUERY]
        removed_count = 0
        
        for entry_type in priority_types:
            if removed_count >= target_count:
                break
            
            type_entries = [e for e in self._entries if e.entry_type == entry_type]
            remove_count = min(len(type_entries), target_count - removed_count)
            
            for entry in type_entries[:remove_count]:
                self._remove_entry(entry)
                removed_count += 1
        
        return removed_count
    
    def _remove_entry(self, entry: HistoryEntry) -> None:
        """移除条目"""
        # 从主存储移除
        try:
            self._entries.remove(entry)
        except ValueError:
            pass
        
        # 从类型存储移除
        try:
            self._entries_by_type[entry.entry_type].remove(entry)
        except ValueError:
            pass
        
        # 从标签存储移除
        for tag in entry.tags:
            if tag in self._entries_by_tag:
                try:
                    self._entries_by_tag[tag].remove(entry)
                except ValueError:
                    pass
    
    def _rebuild_indexes(self) -> None:
        """重建索引"""
        self._type_index = {entry_type: [] for entry_type in HistoryType}
        self._tag_index = {}
        self._time_index = []
        
        for entry in self._entries:
            self._update_indexes(entry)
    
    def query_history(self, query: HistoryQuery) -> List[HistoryEntry]:
        """
        查询历史记录
        
        Args:
            query: 查询条件
            
        Returns:
            匹配的历史记录
        """
        with self._lock:
            # 获取候选记录
            candidates = self._get_candidates(query)
            
            # 应用过滤条件
            filtered_entries = self._apply_filters(candidates, query)
            
            # 排序
            sorted_entries = self._sort_entries(filtered_entries, query)
            
            # 分页
            offset = query.offset
            limit = query.limit
            if limit is not None:
                return sorted_entries[offset:offset + limit]
            else:
                return sorted_entries[offset:]
    
    def _get_candidates(self, query: HistoryQuery) -> List[HistoryEntry]:
        """获取候选记录"""
        # 如果没有类型过滤，使用所有记录
        if not query.entry_types:
            return list(self._entries)
        
        # 按类型获取记录
        candidates = []
        for entry_type in query.entry_types:
            candidates.extend(self._entries_by_type[entry_type])
        
        return list(set(candidates))  # 去重
    
    def _apply_filters(self, entries: List[HistoryEntry], query: HistoryQuery) -> List[HistoryEntry]:
        """应用过滤条件"""
        filtered = entries
        
        # 时间过滤
        if query.start_time is not None:
            filtered = [e for e in filtered if e.timestamp >= query.start_time]
        
        if query.end_time is not None:
            filtered = [e for e in filtered if e.timestamp <= query.end_time]
        
        # 标签过滤
        if query.tags:
            filtered = [e for e in filtered if any(tag in e.tags for tag in query.tags)]
        
        # 重要性过滤
        if query.importance_min is not None:
            filtered = [e for e in filtered if e.importance >= query.importance_min]
        
        if query.importance_max is not None:
            filtered = [e for e in filtered if e.importance <= query.importance_max]
        
        # 元数据过滤
        if query.metadata_filter:
            filtered = [e for e in filtered if self._matches_metadata(e, query.metadata_filter)]
        
        return filtered
    
    def _matches_metadata(self, entry: HistoryEntry, metadata_filter: Dict[str, Any]) -> bool:
        """检查元数据是否匹配"""
        for key, value in metadata_filter.items():
            if key not in entry.metadata or entry.metadata[key] != value:
                return False
        return True
    
    def _sort_entries(self, entries: List[HistoryEntry], query: HistoryQuery) -> List[HistoryEntry]:
        """排序记录"""
        reverse = query.sort_order == "desc"
        
        if query.sort_by == "timestamp":
            return sorted(entries, key=lambda e: e.timestamp, reverse=reverse)
        elif query.sort_by == "importance":
            return sorted(entries, key=lambda e: e.importance, reverse=reverse)
        elif query.sort_by == "entry_type":
            return sorted(entries, key=lambda e: e.entry_type.value, reverse=reverse)
        else:
            return entries
    
    def get_entry_by_id(self, entry_id: str) -> Optional[HistoryEntry]:
        """
        根据ID获取记录
        
        Args:
            entry_id: 记录ID
            
        Returns:
            历史记录或None
        """
        with self._lock:
            for entry in self._entries:
                if entry.entry_id == entry_id:
                    return entry
            return None
    
    def get_recent_entries(self, count: int = 10, 
                          entry_types: Optional[List[HistoryType]] = None) -> List[HistoryEntry]:
        """
        获取最近的记录
        
        Args:
            count: 记录数量
            entry_types: 记录类型过滤
            
        Returns:
            记录列表
        """
        query = HistoryQuery(
            entry_types=entry_types,
            limit=count,
            sort_by="timestamp",
            sort_order="desc"
        )
        return self.query_history(query)
    
    def get_entries_by_tag(self, tag: str, limit: Optional[int] = None) -> List[HistoryEntry]:
        """
        根据标签获取记录
        
        Args:
            tag: 标签
            limit: 限制数量
            
        Returns:
            记录列表
        """
        with self._lock:
            if tag not in self._entries_by_tag:
                return []
            
            entries = list(self._entries_by_tag[tag])
            entries.sort(key=lambda e: e.timestamp, reverse=True)
            
            if limit is not None:
                return entries[:limit]
            return entries
    
    def get_history_stats(self) -> HistoryStats:
        """获取历史统计信息"""
        with self._lock:
            return self._stats
    
    def analyze_patterns(self, entry_type: HistoryType, 
                        time_window: Optional[float] = None) -> Dict[str, Any]:
        """
        分析历史模式
        
        Args:
            entry_type: 记录类型
            time_window: 时间窗口（秒）
            
        Returns:
            模式分析结果
        """
        with self._lock:
            entries = list(self._entries_by_type[entry_type])
            
            # 时间窗口过滤
            if time_window is not None:
                current_time = time.time()
                entries = [e for e in entries if current_time - e.timestamp <= time_window]
            
            if not entries:
                return {"error": "没有足够的数据进行分析"}
            
            # 基础统计
            timestamps = [e.timestamp for e in entries]
            importances = [e.importance for e in entries]
            
            # 时间分析
            time_span = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0
            frequency = len(entries) / max(time_span, 1) if time_span > 0 else 0
            
            # 重要性分析
            avg_importance = sum(importances) / len(importances)
            importance_trend = self._calculate_trend(importances)
            
            # 标签分析
            all_tags = []
            for entry in entries:
                all_tags.extend(entry.tags)
            tag_counts = {tag: all_tags.count(tag) for tag in set(all_tags)}
            top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            return {
                "entry_type": entry_type.value,
                "total_entries": len(entries),
                "time_span": time_span,
                "frequency": frequency,
                "average_importance": avg_importance,
                "importance_trend": importance_trend,
                "top_tags": top_tags,
                "analysis_timestamp": time.time()
            }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势"""
        if len(values) < 3:
            return "insufficient_data"
        
        # 简单线性趋势
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
    
    def export_history(self, format: str = "json", 
                      entry_types: Optional[List[HistoryType]] = None,
                      time_range: Optional[Tuple[float, float]] = None) -> Union[str, bytes]:
        """
        导出历史记录
        
        Args:
            format: 导出格式 (json, pickle)
            entry_types: 记录类型过滤
            time_range: 时间范围过滤
            
        Returns:
            导出数据
        """
        with self._lock:
            # 构建查询
            query = HistoryQuery(entry_types=entry_types)
            if time_range:
                query.start_time, query.end_time = time_range
            
            entries = self.query_history(query)
            
            # 转换为可序列化格式
            export_data = {
                "agent_id": self.agent_id,
                "export_timestamp": time.time(),
                "total_entries": len(entries),
                "entries": [asdict(entry) for entry in entries],
                "stats": asdict(self._stats)
            }
            
            if format == "json":
                return json.dumps(export_data, indent=2, default=str)
            elif format == "pickle":
                return pickle.dumps(export_data)
            else:
                raise ValueError(f"不支持的导出格式: {format}")
    
    def clear_history(self, entry_types: Optional[List[HistoryType]] = None,
                      older_than: Optional[float] = None) -> int:
        """
        清除历史记录
        
        Args:
            entry_types: 要清除的记录类型
            older_than: 清除早于此时间的记录
            
        Returns:
            清除的记录数量
        """
        with self._lock:
            entries_to_remove = []
            
            for entry in self._entries:
                # 类型过滤
                if entry_types and entry.entry_type not in entry_types:
                    continue
                
                # 时间过滤
                if older_than and entry.timestamp >= older_than:
                    continue
                
                entries_to_remove.append(entry)
            
            # 移除记录
            for entry in entries_to_remove:
                self._remove_entry(entry)
            
            # 重建索引
            self._rebuild_indexes()
            
            # 持久化
            if self.persistence_enabled:
                self._save_history()
            
            self.logger.info(f"清除了 {len(entries_to_remove)} 条历史记录")
            return len(entries_to_remove)
    
    def _save_history(self) -> None:
        """保存历史到文件"""
        try:
            data = {
                "entries": list(self._entries),
                "stats": self._stats,
                "save_timestamp": time.time()
            }
            with open(self._persistence_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
    
    def _load_history(self) -> None:
        """从文件加载历史"""
        try:
            with open(self._persistence_path, 'rb') as f:
                data = pickle.load(f)
            
            self._entries = deque(data["entries"], maxlen=self.max_entries)
            self._stats = data["stats"]
            
            # 重建索引和分类存储
            self._rebuild_indexes()
            for entry in self._entries:
                self._add_to_storage(entry)
            
            self.logger.info(f"从文件加载了 {len(self._entries)} 条历史记录")
        except Exception as e:
            self.logger.warning(f"加载历史记录失败: {e}")
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        with self._lock:
            entries_size = len(pickle.dumps(self._entries))
            indexes_size = len(pickle.dumps({
                "type_index": self._type_index,
                "tag_index": self._tag_index,
                "time_index": self._time_index
            }))
            
            return {
                "total_entries": len(self._entries),
                "entries_size_bytes": entries_size,
                "indexes_size_bytes": indexes_size,
                "total_size_bytes": entries_size + indexes_size,
                "max_entries": self.max_entries,
                "usage_percentage": (len(self._entries) / self.max_entries) * 100,
                "storage_efficiency": entries_size / len(self._entries) if self._entries else 0
            }