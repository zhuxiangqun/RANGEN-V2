#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
变更日志管理器
提供系统变更的跟踪和管理功能
"""

import os
import json
import logging
import time
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ChangeType(Enum):
    """变更类型枚举"""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    REFACTOR = "refactor"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DOCUMENTATION = "documentation"


class ChangeStatus(Enum):
    """变更状态枚举"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    COMPLETED = "completed"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"


@dataclass
class ChangeRecord:
    """变更记录数据类"""
    id: str
    title: str
    description: str
    change_type: ChangeType
    status: ChangeStatus
    author: str
    created_at: datetime
    updated_at: datetime
    affected_files: List[str]
    affected_modules: List[str]
    dependencies: List[str]
    rollback_plan: Optional[str] = None
    deployment_notes: Optional[str] = None
    testing_notes: Optional[str] = None
    impact_assessment: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class ChangeLogManager:
    """变更日志管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger("ChangeLogManager")
        self.changes: Dict[str, ChangeRecord] = {}
        self.log_file = os.getenv("CHANGE_LOG_FILE", "changelog.json")
        self.max_changes = int(os.getenv("MAX_CHANGES", "1000"))
        self._load_changes()
    
    def create_change(self, 
                     title: str,
                     description: str,
                     change_type: ChangeType,
                     author: str,
                     affected_files: Optional[List[str]] = None,
                     affected_modules: Optional[List[str]] = None,
                     dependencies: Optional[List[str]] = None) -> str:
        """创建变更记录"""
        try:
            # 验证输入
            if not self._validate_change_input(title, description, change_type, author):
                return ""
            
            change_id = self._generate_change_id()
            
            change_record = ChangeRecord(
                id=change_id,
                title=title,
                description=description,
                change_type=change_type,
                status=ChangeStatus.PLANNED,
                author=author,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                affected_files=affected_files or [],
                affected_modules=affected_modules or [],
                dependencies=dependencies or [],
                impact_assessment={},
                metadata={}
            )
            
            # 保存变更记录
            self.changes[change_id] = change_record
            self._save_changes()
            
            self.logger.info(f"创建变更记录成功: {change_id}")
            return change_id
            
        except Exception as e:
            self.logger.error(f"创建变更记录失败: {e}")
            return ""
    
    def _validate_change_input(self, title: str, description: str, change_type: ChangeType, author: str) -> bool:
        """验证变更输入"""
        try:
            if not title or not title.strip():
                return False
            if not description or not description.strip():
                return False
            if not isinstance(change_type, ChangeType):
                return False
            if not author or not author.strip():
                return False
            return True
        except Exception:
            return False
    
    def _generate_change_id(self) -> str:
        """生成变更ID"""
        try:
            timestamp = int(time.time() * 1000)
            random_suffix = random.randint(1000, 9999)
            return f"CHG_{timestamp}_{random_suffix}"
        except Exception as e:
            self.logger.warning(f"生成变更ID失败: {e}")
            return f"CHG_{int(time.time())}_{random.randint(1000, 9999)}"
    
    def _save_changes(self):
        """保存变更记录"""
        try:
            changes_data = {}
            for change_id, change_record in self.changes.items():
                changes_data[change_id] = {
                    "id": change_record.id,
                    "title": change_record.title,
                    "description": change_record.description,
                    "change_type": change_record.change_type.value,
                    "status": change_record.status.value,
                    "author": change_record.author,
                    "created_at": change_record.created_at.isoformat(),
                    "updated_at": change_record.updated_at.isoformat(),
                    "affected_files": change_record.affected_files,
                    "affected_modules": change_record.affected_modules,
                    "dependencies": change_record.dependencies,
                    "rollback_plan": change_record.rollback_plan,
                    "deployment_notes": change_record.deployment_notes,
                    "testing_notes": change_record.testing_notes,
                    "impact_assessment": change_record.impact_assessment or {},
                    "metadata": change_record.metadata or {}
                }
            
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(changes_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存变更记录失败: {e}")
    
    def _load_changes(self):
        """加载变更记录"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    changes_data = json.load(f)
                
                for change_id, data in changes_data.items():
                    change_record = ChangeRecord(
                        id=data["id"],
                        title=data["title"],
                        description=data["description"],
                        change_type=ChangeType(data["change_type"]),
                        status=ChangeStatus(data["status"]),
                        author=data["author"],
                        created_at=datetime.fromisoformat(data["created_at"]),
                        updated_at=datetime.fromisoformat(data["updated_at"]),
                        affected_files=data.get("affected_files", []),
                        affected_modules=data.get("affected_modules", []),
                        dependencies=data.get("dependencies", []),
                        rollback_plan=data.get("rollback_plan"),
                        deployment_notes=data.get("deployment_notes"),
                        testing_notes=data.get("testing_notes"),
                        impact_assessment=data.get("impact_assessment"),
                        metadata=data.get("metadata")
                    )
                    self.changes[change_id] = change_record
                    
        except Exception as e:
            self.logger.error(f"加载变更记录失败: {e}")
    
    def update_change_status(self, change_id: str, new_status: ChangeStatus) -> bool:
        """更新变更状态"""
        try:
            if change_id not in self.changes:
                return False
            
            self.changes[change_id].status = new_status
            self.changes[change_id].updated_at = datetime.now()
            self._save_changes()
            
            self.logger.info(f"更新变更状态成功: {change_id} -> {new_status.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新变更状态失败: {e}")
            return False
    
    def get_change(self, change_id: str) -> Optional[ChangeRecord]:
        """获取变更记录"""
        try:
            return self.changes.get(change_id)
        except Exception as e:
            self.logger.error(f"获取变更记录失败: {e}")
            return None
    
    def list_changes(self, 
                    change_type: Optional[ChangeType] = None,
                    status: Optional[ChangeStatus] = None,
                    author: Optional[str] = None,
                    limit: int = 100) -> List[ChangeRecord]:
        """列出变更记录"""
        try:
            filtered_changes = []
            
            for change_record in self.changes.values():
                # 按类型过滤
                if change_type and change_record.change_type != change_type:
                    continue
                
                # 按状态过滤
                if status and change_record.status != status:
                    continue
                
                # 按作者过滤
                if author and change_record.author != author:
                    continue
                
                filtered_changes.append(change_record)
            
            # 按更新时间排序
            filtered_changes.sort(key=lambda x: x.updated_at, reverse=True)
            
            # 限制数量
            return filtered_changes[:limit]
            
        except Exception as e:
            self.logger.error(f"列出变更记录失败: {e}")
            return []
    
    def search_changes(self, query: str) -> List[ChangeRecord]:
        """搜索变更记录"""
        try:
            query_lower = query.lower()
            matching_changes = []
            
            for change_record in self.changes.values():
                # 搜索标题和描述
                if (query_lower in change_record.title.lower() or 
                    query_lower in change_record.description.lower()):
                    matching_changes.append(change_record)
            
            # 按更新时间排序
            matching_changes.sort(key=lambda x: x.updated_at, reverse=True)
            
            return matching_changes
            
        except Exception as e:
            self.logger.error(f"搜索变更记录失败: {e}")
            return []
    
    def get_change_statistics(self) -> Dict[str, Any]:
        """获取变更统计信息"""
        try:
            stats = {
                "total_changes": len(self.changes),
                "by_type": {},
                "by_status": {},
                "by_author": {},
                "recent_changes": 0
            }
            
            # 按类型统计
            for change_record in self.changes.values():
                change_type = change_record.change_type.value
                stats["by_type"][change_type] = stats["by_type"].get(change_type, 0) + 1
                
                # 按状态统计
                status = change_record.status.value
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                # 按作者统计
                author = change_record.author
                stats["by_author"][author] = stats["by_author"].get(author, 0) + 1
                
                # 最近变更（7天内）
                if (datetime.now() - change_record.updated_at).days <= 7:
                    stats["recent_changes"] += 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取变更统计失败: {e}")
            return {}
    
    def export_changes(self, file_path: str, format: str = "json") -> bool:
        """导出变更记录"""
        try:
            if format.lower() == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self._serialize_changes(), f, ensure_ascii=False, indent=2)
            elif format.lower() == "csv":
                self._export_to_csv(file_path)
            else:
                return False
            
            self.logger.info(f"导出变更记录成功: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出变更记录失败: {e}")
            return False
    
    def _serialize_changes(self) -> Dict[str, Any]:
        """序列化变更记录"""
        try:
            changes_data = {}
            for change_id, change_record in self.changes.items():
                changes_data[change_id] = asdict(change_record)
                # 转换datetime对象为字符串
                changes_data[change_id]["created_at"] = change_record.created_at.isoformat()
                changes_data[change_id]["updated_at"] = change_record.updated_at.isoformat()
                # 转换枚举为字符串
                changes_data[change_id]["change_type"] = change_record.change_type.value
                changes_data[change_id]["status"] = change_record.status.value
            return changes_data
        except Exception as e:
            self.logger.error(f"序列化变更记录失败: {e}")
            return {}
    
    def _export_to_csv(self, file_path: str):
        """导出为CSV格式"""
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题行
                writer.writerow([
                    "ID", "Title", "Description", "Type", "Status", "Author",
                    "Created At", "Updated At", "Affected Files", "Affected Modules"
                ])
                
                # 写入数据行
                for change_record in self.changes.values():
                    writer.writerow([
                        change_record.id,
                        change_record.title,
                        change_record.description,
                        change_record.change_type.value,
                        change_record.status.value,
                        change_record.author,
                        change_record.created_at.isoformat(),
                        change_record.updated_at.isoformat(),
                        "; ".join(change_record.affected_files),
                        "; ".join(change_record.affected_modules)
                    ])
                    
        except Exception as e:
            self.logger.error(f"导出CSV失败: {e}")
    
    def cleanup_old_changes(self, days: int = 365) -> int:
        """清理旧变更记录"""
        try:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days)
            
            old_changes = []
            for change_id, change_record in self.changes.items():
                if change_record.updated_at < cutoff_date:
                    old_changes.append(change_id)
            
            # 删除旧记录
            for change_id in old_changes:
                del self.changes[change_id]
            
            # 保存更改
            self._save_changes()
            
            self.logger.info(f"清理了 {len(old_changes)} 条旧变更记录")
            return len(old_changes)
            
        except Exception as e:
            self.logger.error(f"清理旧变更记录失败: {e}")
            return 0
    
    def get_manager_status(self) -> Dict[str, Any]:
        """获取管理器状态"""
        try:
            return {
                "initialized": True,
                "total_changes": len(self.changes),
                "log_file": self.log_file,
                "max_changes": self.max_changes,
                "last_updated": max([c.updated_at for c in self.changes.values()]) if self.changes else None,
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"获取管理器状态失败: {e}")
            return {
                "initialized": False,
                "error": str(e)
            }