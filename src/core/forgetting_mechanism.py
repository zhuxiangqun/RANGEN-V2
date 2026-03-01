#!/usr/bin/env python3
"""
遗忘机制模块 - L4层智能清理
对齐pc-agent-loop的记忆管理理念

功能:
- 定期清理低频使用的SOP和技能
- 基于时间衰减的活跃度计算
- 自动归档而非直接删除
- 可配置的保留策略
"""
import time
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MemoryLevel(str, Enum):
    """记忆层级"""
    L0_META = "l0_meta"        # 元认知
    L1_RECENT = "l1_recent"   # 近期会话
    L2_FACTS = "l2_facts"     # 跨会话事实
    L3_SKILLS = "l3_skills"  # 技能库 (SOPs)
    L4_ARCHIVE = "l4_archive"  # 归档


class MemoryStatus(str, Enum):
    """记忆状态"""
    ACTIVE = "active"        # 活跃
    DORMANT = "dormant"     # 休眠
    ARCHIVED = "archived"   # 已归档
    FORGOTTEN = "forgotten" # 已遗忘


@dataclass
class MemoryItem:
    """记忆项"""
    item_id: str
    item_type: str          # "sop" or "skill"
    name: str
    description: str
    
    # 活跃度指标
    usage_count: int = 0           # 使用次数
    last_used: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # 计算指标
    relevance_score: float = 0.0   # 相关度分数
    activity_score: float = 0.0    # 活跃度分数
    
    # 层级
    level: MemoryLevel = MemoryLevel.L3_SKILLS
    status: MemoryStatus = MemoryStatus.ACTIVE
    
    # 归档信息
    archived_at: Optional[float] = None
    archive_reason: Optional[str] = None
    
    def calculate_activity(self, decay_factor: float = 0.1) -> float:
        """计算活跃度分数
        
        基于时间衰减和使用频率
        """
        now = time.time()
        days_since_use = (now - self.last_used) / 86400  # 转换为天
        days_since_create = (now - self.created_at) / 86400
        
        # 时间衰减因子
        time_decay = max(0, 1 - (days_since_use * decay_factor))
        
        # 使用频率因子
        usage_factor = min(self.usage_count / 10, 1.0)  # 10次达到饱和
        
        # 新鲜度因子
        freshness = min(days_since_create / 30, 1.0)  # 30天内算新鲜
        
        # 综合活跃度
        self.activity_score = (
            time_decay * 0.5 +
            usage_factor * 0.3 +
            freshness * 0.2
        )
        
        return self.activity_score
    
    def calculate_relevance(self, context_keywords: List[str]) -> float:
        """计算与当前上下文的相关度"""
        # 简化的相关度计算
        item_keywords = set(self.name.lower().split())
        
        if not context_keywords:
            self.relevance_score = 0.5
        else:
            overlap = len(item_keywords.intersection(set(context_keywords)))
            self.relevance_score = overlap / max(len(context_keywords), 1)
        
        return self.relevance_score


class ForgettingConfig:
    """遗忘配置"""
    
    def __init__(self):
        # 活跃度阈值
        self.activity_threshold = 0.1  # 低于此值进入休眠
        self.archive_threshold = 0.05   # 低于此值归档
        self.forget_threshold = 0.01   # 低于此值遗忘
        
        # 时间阈值 (天)
        self.dormant_days = 30         # 30天未用进入休眠
        self.archive_days = 90         # 90天未用归档
        self.forget_days = 180         # 180天未用遗忘
        
        # 保留策略
        self.min_usage_to_never_forget = 50  # 使用50次以上永不遗忘
        self.preserve_categories: List[str] = ["core", "system"]  # 保留类别
        
        # 归档保留天数
        self.archive_retention_days = 30
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "activity_threshold": self.activity_threshold,
            "archive_threshold": self.archive_threshold,
            "forget_threshold": self.forget_threshold,
            "dormant_days": self.dormant_days,
            "archive_days": self.archive_days,
            "forget_days": self.forget_days,
            "min_usage_to_never_forget": self.min_usage_to_never_forget,
            "preserve_categories": self.preserve_categories,
            "archive_retention_days": self.archive_retention_days
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForgettingConfig":
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config


class ForgettingMechanism:
    """遗忘机制
    
    智能管理记忆的层级和生命周期
    """
    
    def __init__(self, config: Optional[ForgettingConfig] = None):
        self.config = config or ForgettingConfig()
        self.archive: Dict[str, MemoryItem] = {}
        
        # 统计
        self.stats = {
            "dormant_count": 0,
            "archived_count": 0,
            "forgotten_count": 0,
            "last_cleanup": None
        }
        
        logger.info("Forgetting mechanism initialized")
    
    def evaluate(self, items: List[MemoryItem], 
                context_keywords: Optional[List[str]] = None) -> Dict[str, List[MemoryItem]]:
        """评估所有记忆项
        
        Args:
            items: 记忆项列表
            context_keywords: 当前上下文关键词
            
        Returns:
            按状态分类的项
        """
        categorized = {
            "active": [],
            "dormant": [],
            "to_archive": [],
            "to_forget": [],
            "never_forget": []
        }
        
        for item in items:
            # 跳过已归档的
            if item.status == MemoryStatus.ARCHIVED:
                continue
            
            # 计算活跃度
            activity = item.calculate_activity()
            
            # 计算相关度
            if context_keywords:
                item.calculate_relevance(context_keywords)
            
            # 永不遗忘检查
            if item.usage_count >= self.config.min_usage_to_never_forget:
                categorized["never_forget"].append(item)
                continue
            
            # 保留类别检查
            if any(cat in item.name.lower() for cat in self.config.preserve_categories):
                categorized["never_forget"].append(item)
                continue
            
            # 分类
            days_since_use = (time.time() - item.last_used) / 86400
            
            if activity >= self.config.activity_threshold and days_since_use < self.config.dormant_days:
                item.status = MemoryStatus.ACTIVE
                categorized["active"].append(item)
            elif activity < self.config.forget_threshold or days_since_use >= self.config.forget_days:
                item.status = MemoryStatus.FORGOTTEN
                categorized["to_forget"].append(item)
            elif activity < self.config.archive_threshold or days_since_use >= self.config.archive_days:
                item.status = MemoryStatus.ARCHIVED
                categorized["to_archive"].append(item)
            else:
                item.status = MemoryStatus.DORMANT
                categorized["dormant"].append(item)
        
        return categorized
    
    def cleanup(self, items: List[MemoryItem], 
               context_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """执行清理
        
        Args:
            items: 记忆项列表
            context_keywords: 当前上下文
            
        Returns:
            清理报告
        """
        report = {
            "timestamp": time.time(),
            "total_items": len(items),
            "actions": {
                "activated": 0,
                "dormant": 0,
                "archived": 0,
                "forgotten": 0
            },
            "details": []
        }
        
        categorized = self.evaluate(items, context_keywords)
        
        # 处理激活
        for item in categorized["active"]:
            item.status = MemoryStatus.ACTIVE
            item.level = MemoryLevel.L3_SKILLS
            report["actions"]["activated"] += 1
        
        # 处理休眠
        for item in categorized["dormant"]:
            item.status = MemoryStatus.DORMANT
            report["actions"]["dormant"] += 1
        
        # 处理归档
        for item in categorized["to_archive"]:
            item.status = MemoryStatus.ARCHIVED
            item.archived_at = time.time()
            item.archive_reason = "low_activity"
            self.archive[item.item_id] = item
            report["actions"]["archived"] += 1
            report["details"].append({
                "item_id": item.item_id,
                "action": "archived",
                "reason": "inactive for {} days".format(
                    int((time.time() - item.last_used) / 86400)
                )
            })
        
        # 处理遗忘
        for item in categorized["to_forget"]:
            item.status = MemoryStatus.FORGOTTEN
            report["actions"]["forgotten"] += 1
            report["details"].append({
                "item_id": item.item_id,
                "action": "forgotten",
                "reason": "very low activity"
            })
        
        # 更新统计
        self.stats["dormant_count"] = len(categorized["dormant"])
        self.stats["archived_count"] = len(self.archive)
        self.stats["forgotten_count"] = len(categorized["to_forget"])
        self.stats["last_cleanup"] = time.time()
        
        return report
    
    def recall_from_archive(self, item_id: str) -> Optional[MemoryItem]:
        """从归档中恢复
        
        Args:
            item_id: 记忆项ID
            
        Returns:
            恢复的记忆项
        """
        if item_id in self.archive:
            item = self.archive[item_id]
            item.status = MemoryStatus.ACTIVE
            item.last_used = time.time()
            del self.archive[item_id]
            
            logger.info(f"Recalled from archive: {item.name}")
            return item
        
        return None
    
    def get_archive(self, since: Optional[float] = None) -> List[MemoryItem]:
        """获取归档列表
        
        Args:
            since: 可选时间过滤
            
        Returns:
            归档项列表
        """
        if since is None:
            return list(self.archive.values())
        
        return [
            item for item in self.archive.values()
            if item.archived_at and item.archived_at >= since
        ]
    
    def auto_cleanup_old_archives(self) -> int:
        """自动清理过期归档
        
        Returns:
            清理数量
        """
        cutoff = time.time() - (self.config.archive_retention_days * 86400)
        
        to_remove = []
        for item_id, item in self.archive.items():
            if item.archived_at and item.archived_at < cutoff:
                to_remove.append(item_id)
        
        for item_id in to_remove:
            del self.archive[item_id]
        
        logger.info(f"Auto-cleaned {len(to_remove)} expired archives")
        return len(to_remove)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "config": self.config.to_dict(),
            "stats": self.stats,
            "archive_count": len(self.archive),
            "active_count": sum(1 for i in self.archive.values() if i.status == MemoryStatus.ACTIVE),
            "total_archived": self.stats["archived_count"],
            "total_forgotten": self.stats["forgotten_count"]
        }
    
    def export_config(self) -> str:
        """导出配置"""
        return json.dumps(self.config.to_dict(), indent=2)
    
    def import_config(self, config_json: str):
        """导入配置"""
        self.config = ForgettingConfig.from_dict(json.loads(config_json))
        logger.info("Configuration updated")


class MemoryManager:
    """记忆管理器
    
    统一管理所有层级的记忆
    """
    
    def __init__(self, forgetting_config: Optional[ForgettingConfig] = None):
        self.forgetting = ForgettingMechanism(forgetting_config)
        self.items: Dict[str, MemoryItem] = {}
        
        logger.info("Memory Manager initialized")
    
    def register_item(self, item_id: str, item_type: str, 
                    name: str, description: str) -> MemoryItem:
        """注册记忆项"""
        if item_id in self.items:
            return self.items[item_id]
        
        item = MemoryItem(
            item_id=item_id,
            item_type=item_type,
            name=name,
            description=description
        )
        
        self.items[item_id] = item
        return item
    
    def update_usage(self, item_id: str):
        """更新使用"""
        if item_id in self.items:
            item = self.items[item_id]
            item.usage_count += 1
            item.last_used = time.time()
            item.updated_at = time.time()
            
            # 如果在归档中，自动恢复
            if item.status == MemoryStatus.ARCHIVED:
                self.forgetting.recall_from_archive(item_id)
    
    def run_cleanup(self, context_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """运行清理"""
        return self.forgetting.cleanup(list(self.items.values()), context_keywords)
    
    def get_active_items(self) -> List[MemoryItem]:
        """获取活跃项"""
        return [
            item for item in self.items.values()
            if item.status == MemoryStatus.ACTIVE
        ]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "total_items": len(self.items),
            "active": len(self.get_active_items()),
            "forgetting": self.forgetting.get_statistics()
        }


# 全局实例
_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取记忆管理器单例"""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
