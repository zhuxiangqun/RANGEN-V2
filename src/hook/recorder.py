#!/usr/bin/env python3
"""
Hook记录器
负责记录和存储系统事件
"""

import asyncio
import logging
import json
import pickle
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from .hook_types import HookEvent


class HookRecorder:
    """Hook事件记录器"""
    
    def __init__(self, system_name: str):
        self.logger = logging.getLogger(__name__)
        self.system_name = system_name
        
        # 存储目录
        self.storage_dir = Path("data") / "hook_events" / system_name
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # 数据库文件
        self.db_file = self.storage_dir / "events.db"
        
        # 内存缓存（限制大小）
        self.event_cache: Dict[str, HookEvent] = {}
        self.max_cache_size = 1000
        
        # 事件订阅者
        self.subscribers: Dict[str, List[Callable]] = {}
        
        # 初始化数据库
        self._init_database()
        
        self.logger.info(f"Hook记录器初始化: {system_name}")
    
    def _init_database(self):
        """初始化数据库"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 创建事件表
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS hook_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    source TEXT NOT NULL,
                    data_json TEXT NOT NULL,
                    visibility TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON hook_events(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON hook_events(event_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON hook_events(source)')
                
                conn.commit()
                self.logger.info("Hook事件数据库初始化完成")
                
        except Exception as e:
            self.logger.error(f"初始化数据库失败: {e}")
    
    @contextmanager
    def _get_db_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        try:
            yield conn
        finally:
            conn.close()
    
    def subscribe(self, event_type: str, callback: Callable):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
        self.logger.debug(f"订阅事件类型: {event_type}")
    
    def _notify_subscribers(self, event: HookEvent):
        """通知订阅者"""
        event_type = event.event_type.value
        
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    # 异步调用回调
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(event))
                    else:
                        callback(event)
                except Exception as e:
                    self.logger.error(f"事件回调执行失败: {e}")
    
    async def record_event(self, event: HookEvent) -> bool:
        """记录事件"""
        try:
            # 序列化数据
            data_json = json.dumps(event.data, ensure_ascii=False)
            metadata_json = json.dumps(event.metadata, ensure_ascii=False)
            created_at = datetime.now().isoformat()
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO hook_events 
                (event_id, event_type, timestamp, source, data_json, visibility, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp,
                    event.source,
                    data_json,
                    event.visibility.value,
                    metadata_json,
                    created_at
                ))
                
                conn.commit()
                
            # 通知订阅者
            self._notify_subscribers(event)
            
            # 更新缓存
            self._update_cache(event)
            
            # 异步保存到文件备份
            asyncio.create_task(self._save_to_backup_file(event))
            
            self.logger.debug(f"事件记录成功: {event.event_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"记录事件失败: {e}")
            return False
    
    def _update_cache(self, event: HookEvent):
        """更新内存缓存"""
        self.event_cache[event.event_id] = event
        
        # 限制缓存大小
        if len(self.event_cache) > self.max_cache_size:
            # 移除最旧的事件（基于ID中的时间戳）
            oldest_ids = sorted(self.event_cache.keys())[:100]
            for event_id in oldest_ids:
                del self.event_cache[event_id]
    
    async def _save_to_backup_file(self, event: HookEvent):
        """保存到备份文件"""
        try:
            # 按日期组织文件
            event_date = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00')).date()
            backup_dir = self.storage_dir / "backup" / str(event_date.year) / f"{event_date.month:02d}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            backup_file = backup_dir / f"{event_date.day:02d}.jsonl"
            
            # 追加到文件
            event_dict = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "source": event.source,
                "data": event.data,
                "visibility": event.visibility.value,
                "metadata": event.metadata
            }
            
            with open(backup_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event_dict, ensure_ascii=False) + '\n')
                
        except Exception as e:
            self.logger.error(f"保存到备份文件失败: {e}")
    
    async def get_event(self, event_id: str) -> Optional[HookEvent]:
        """获取事件"""
        try:
            # 首先尝试从缓存获取
            if event_id in self.event_cache:
                return self.event_cache[event_id]
            
            # 从数据库获取
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM hook_events WHERE event_id = ?
                ''', (event_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # 解析数据
                event = self._row_to_event(row)
                
                # 更新缓存
                self.event_cache[event_id] = event
                
                return event
                
        except Exception as e:
            self.logger.error(f"获取事件失败: {e}")
            return None
    
    def _row_to_event(self, row) -> HookEvent:
        """数据库行转换为HookEvent"""
        from .hook_types import HookEvent, HookEventType, HookVisibilityLevel
        
        event_type = HookEventType(row['event_type'])
        visibility = HookVisibilityLevel(row['visibility'])
        
        # 解析JSON数据
        data = json.loads(row['data_json'])
        metadata = json.loads(row['metadata_json'])
        
        return HookEvent(
            event_id=row['event_id'],
            event_type=event_type,
            timestamp=row['timestamp'],
            source=row['source'],
            data=data,
            visibility=visibility,
            metadata=metadata
        )
    
    async def get_events_by_time_range(self, hours: int = 24) -> List[HookEvent]:
        """获取指定时间范围内的事件"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            events = []
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM hook_events 
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                ''', (cutoff_time,))
                
                for row in cursor.fetchall():
                    event = self._row_to_event(row)
                    events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"获取时间范围内事件失败: {e}")
            return []
    
    async def get_events_by_type(self, event_type: str, limit: int = 100) -> List[HookEvent]:
        """按类型获取事件"""
        try:
            events = []
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM hook_events 
                WHERE event_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (event_type, limit))
                
                for row in cursor.fetchall():
                    event = self._row_to_event(row)
                    events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"按类型获取事件失败: {e}")
            return []
    
    async def get_events_by_source(self, source: str, limit: int = 100) -> List[HookEvent]:
        """按来源获取事件"""
        try:
            events = []
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                SELECT * FROM hook_events 
                WHERE source LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                ''', (f"%{source}%", limit))
                
                for row in cursor.fetchall():
                    event = self._row_to_event(row)
                    events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"按来源获取事件失败: {e}")
            return []
    
    async def search_events(self, query: str, field: str = "all", limit: int = 50) -> List[HookEvent]:
        """搜索事件"""
        try:
            events = []
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                if field == "all":
                    # 在所有文本字段中搜索
                    cursor.execute('''
                    SELECT * FROM hook_events 
                    WHERE event_id LIKE ? OR 
                          event_type LIKE ? OR 
                          source LIKE ? OR 
                          data_json LIKE ? OR 
                          metadata_json LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    ''', (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
                else:
                    # 在指定字段中搜索
                    if field == "data":
                        field_name = "data_json"
                    elif field == "metadata":
                        field_name = "metadata_json"
                    else:
                        field_name = field
                    
                    cursor.execute(f'''
                    SELECT * FROM hook_events 
                    WHERE {field_name} LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    ''', (f"%{query}%", limit))
                
                for row in cursor.fetchall():
                    event = self._row_to_event(row)
                    events.append(event)
            
            return events
            
        except Exception as e:
            self.logger.error(f"搜索事件失败: {e}")
            return []
    
    async def get_event_statistics(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """获取事件统计"""
        try:
            cutoff_time = (datetime.now() - timedelta(hours=time_range_hours)).isoformat()
            
            stats = {
                "time_range_hours": time_range_hours,
                "total_events": 0,
                "by_event_type": {},
                "by_source": {},
                "by_hour": {},
                "by_visibility": {}
            }
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 总事件数
                cursor.execute('''
                SELECT COUNT(*) as count FROM hook_events WHERE timestamp >= ?
                ''', (cutoff_time,))
                stats["total_events"] = cursor.fetchone()["count"]
                
                # 按事件类型统计
                cursor.execute('''
                SELECT event_type, COUNT(*) as count 
                FROM hook_events 
                WHERE timestamp >= ?
                GROUP BY event_type
                ORDER BY count DESC
                ''', (cutoff_time,))
                
                for row in cursor.fetchall():
                    stats["by_event_type"][row["event_type"]] = row["count"]
                
                # 按来源统计
                cursor.execute('''
                SELECT source, COUNT(*) as count 
                FROM hook_events 
                WHERE timestamp >= ?
                GROUP BY source
                ORDER BY count DESC
                LIMIT 20
                ''', (cutoff_time,))
                
                for row in cursor.fetchall():
                    stats["by_source"][row["source"]] = row["count"]
                
                # 按小时统计（最近24小时）
                cursor.execute('''
                SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                FROM hook_events 
                WHERE timestamp >= ?
                GROUP BY hour
                ORDER BY hour
                ''', (cutoff_time,))
                
                for row in cursor.fetchall():
                    stats["by_hour"][row["hour"]] = row["count"]
                
                # 按可见性级别统计
                cursor.execute('''
                SELECT visibility, COUNT(*) as count 
                FROM hook_events 
                WHERE timestamp >= ?
                GROUP BY visibility
                ORDER BY count DESC
                ''', (cutoff_time,))
                
                for row in cursor.fetchall():
                    stats["by_visibility"][row["visibility"]] = row["count"]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取事件统计失败: {e}")
            return {}
    
    async def clear_old_events(self, days_old: int = 30) -> int:
        """清理旧事件"""
        try:
            cutoff_time = (datetime.now() - timedelta(days=days_old)).isoformat()
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # 获取要删除的数量
                cursor.execute('''
                SELECT COUNT(*) as count FROM hook_events WHERE timestamp < ?
                ''', (cutoff_time,))
                count = cursor.fetchone()["count"]
                
                # 删除旧事件
                cursor.execute('''
                DELETE FROM hook_events WHERE timestamp < ?
                ''', (cutoff_time,))
                
                conn.commit()
                
                # 清理缓存
                self._clean_cache()
                
                self.logger.info(f"清理了 {count} 个超过 {days_old} 天的旧事件")
                return count
                
        except Exception as e:
            self.logger.error(f"清理旧事件失败: {e}")
            return 0
    
    def _clean_cache(self):
        """清理缓存"""
        # 简单的缓存清理策略：移除一半
        if len(self.event_cache) > self.max_cache_size // 2:
            keys_to_remove = list(self.event_cache.keys())[:self.max_cache_size // 2]
            for key in keys_to_remove:
                del self.event_cache[key]
    
    async def export_events(self, event_ids: List[str], format: str = "json") -> Optional[str]:
        """导出事件"""
        try:
            events = []
            
            for event_id in event_ids:
                event = await self.get_event(event_id)
                if event:
                    events.append(event)
            
            if format == "json":
                export_data = []
                for event in events:
                    event_dict = {
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp,
                        "source": event.source,
                        "data": event.data,
                        "visibility": event.visibility.value,
                        "metadata": event.metadata
                    }
                    export_data.append(event_dict)
                
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=[
                    "event_id", "event_type", "timestamp", "source", 
                    "visibility", "data_summary"
                ])
                writer.writeheader()
                
                for event in events:
                    writer.writerow({
                        "event_id": event.event_id,
                        "event_type": event.event_type.value,
                        "timestamp": event.timestamp,
                        "source": event.source,
                        "visibility": event.visibility.value,
                        "data_summary": f"{len(event.data)} items"
                    })
                
                return output.getvalue()
            
            else:
                self.logger.warning(f"不支持的导出格式: {format}")
                return None
                
        except Exception as e:
            self.logger.error(f"导出事件失败: {e}")
            return None
    
    async def get_database_info(self) -> Dict[str, Any]:
        """获取数据库信息"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                info = {
                    "database_file": str(self.db_file),
                    "storage_dir": str(self.storage_dir),
                    "cache_size": len(self.event_cache),
                    "max_cache_size": self.max_cache_size
                }
                
                # 表信息
                cursor.execute("SELECT COUNT(*) as count FROM hook_events")
                info["total_events"] = cursor.fetchone()["count"]
                
                cursor.execute("SELECT MIN(timestamp) as oldest, MAX(timestamp) as newest FROM hook_events")
                row = cursor.fetchone()
                info["oldest_event"] = row["oldest"]
                info["newest_event"] = row["newest"]
                
                # 数据库大小
                import os
                info["database_size_mb"] = os.path.getsize(self.db_file) / (1024 * 1024)
                
                return info
                
        except Exception as e:
            self.logger.error(f"获取数据库信息失败: {e}")
            return {}