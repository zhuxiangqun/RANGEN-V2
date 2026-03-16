#!/usr/bin/env python3
"""
ADR (Architecture Decision Record) 注册中心

用于记录架构决策，响应文章洞见：
"原型负责回答能不能做，ADR 负责回答该不该这么做"

ADR 结构:
- 状态: Proposed / Accepted / Deprecated / Superseded
- 背景: 决策前的上下文
- 决策: 实际选择
- 后果: 决策的影响
- 回滚条件: 什么时候应该撤销这个决策
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json


class ADRStatus(Enum):
    """ADR 状态"""
    PROPOSED = "proposed"       # 已提出，待评审
    ACCEPTED = "accepted"       # 已通过，正在实施
    DEPRECATED = "deprecated"   # 已废弃
    SUPERSEDED = "superseded"  # 被新 ADR 取代


@dataclass
class ADR:
    """
    Architecture Decision Record
    
    架构决策记录，参考 Michael Nygard 的 ADR 格式
    """
    adr_id: str                    # 如 "ADR-001"
    title: str                     # 决策标题
    status: ADRStatus              # 当前状态
    date_created: str              # 创建日期 (YYYY-MM-DD)
    date_updated: str              # 更新日期
    
    # 核心内容
    background: str                 # 背景：决策前的上下文
    decision: str                   # 决策：实际选择
    consequences: str               # 后果：正面和负面影响
    
    # 附加信息
    alternatives_considered: List[str] = field(default_factory=list)  # 考虑的替代方案
    superseded_by: Optional[str] = None  # 被哪个 ADR 取代
    supersedes: Optional[str] = None      # 取代了哪个 ADR
    tags: List[str] = field(default_factory=list)  # 标签
    
    # 上下文
    author: str = "RANGEN Team"
    notes: str = ""


class ADRRegistry:
    """
    ADR 注册中心
    
    管理所有架构决策记录
    """
    _instance: Optional['ADRRegistry'] = None
    _records: Dict[str, ADR] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance
    
    def _initialize_defaults(self):
        """初始化默认 ADR"""
        self._records = {}
    
    def add(self, adr: ADR) -> None:
        """添加 ADR 记录"""
        self._records[adr.adr_id] = adr
    
    def get(self, adr_id: str) -> Optional[ADR]:
        """获取 ADR"""
        return self._records.get(adr_id)
    
    def get_all(self) -> List[ADR]:
        """获取所有 ADR"""
        return list(self._records.values())
    
    def get_by_status(self, status: ADRStatus) -> List[ADR]:
        """按状态筛选"""
        return [adr for adr in self._records.values() if adr.status == status]
    
    def get_active(self) -> List[ADR]:
        """获取活跃的 ADR (非 deprecated/superseded)"""
        return [
            adr for adr in self._records.values()
            if adr.status in [ADRStatus.PROPOSED, ADRStatus.ACCEPTED]
        ]
    
    def search(self, query: str) -> List[ADR]:
        """全文搜索"""
        q = query.lower()
        return [
            adr for adr in self._records.values()
            if q in adr.title.lower() or q in adr.background.lower() 
            or q in adr.decision.lower()
        ]
    
    def deprecate(self, adr_id: str, reason: str) -> bool:
        """废弃 ADR"""
        adr = self._records.get(adr_id)
        if adr:
            adr.status = ADRStatus.DEPRECATED
            adr.date_updated = datetime.now().strftime("%Y-%m-%d")
            adr.notes = f"Deprecated: {reason}"
            return True
        return False
    
    def supersede(self, adr_id: str, new_adr_id: str) -> bool:
        """取代 ADR"""
        old_adr = self._records.get(adr_id)
        new_adr = self._records.get(new_adr_id)
        
        if old_adr and new_adr:
            old_adr.status = ADRStatus.SUPERSEDED
            old_adr.date_updated = datetime.now().strftime("%Y-%m-%d")
            old_adr.superseded_by = new_adr_id
            
            new_adr.supersedes = adr_id
            return True
        return False
    
    def to_markdown(self) -> str:
        """导出为 Markdown 格式"""
        lines = ["# ADR (Architecture Decision Records)\n"]
        
        for adr in sorted(self._records.values(), key=lambda x: x.adr_id):
            status_icon = {
                ADRStatus.PROPOSED: "🔶",
                ADRStatus.ACCEPTED: "✅",
                ADRStatus.DEPRECATED: "❌",
                ADRStatus.SUPERSEDED: "📦"
            }.get(adr.status, "❓")
            
            lines.append(f"## {adr.adr_id}: {adr.title} {status_icon}\n")
            lines.append(f"**Date**: {adr.date_created}")
            lines.append(f"**Author**: {adr.author}")
            lines.append(f"**Status**: {adr.status.value}\n")
            
            lines.append("### Background")
            lines.append(adr.background + "\n")
            
            lines.append("### Decision")
            lines.append(adr.decision + "\n")
            
            lines.append("### Consequences")
            lines.append(adr.consequences + "\n")
            
            if adr.alternatives_considered:
                lines.append("### Alternatives Considered")
                for alt in adr.alternatives_considered:
                    lines.append(f"- {alt}")
                lines.append("")
            
            if adr.tags:
                lines.append(f"**Tags**: {', '.join(adr.tags)}\n")
            
            lines.append("---\n")
        
        return "\n".join(lines)


def get_adr_registry() -> ADRRegistry:
    """获取 ADR 注册中心单例"""
    return ADRRegistry()


# === 便捷函数 ===

def create_adr(
    adr_id: str,
    title: str,
    background: str,
    decision: str,
    consequences: str,
    alternatives: List[str] = None,
    tags: List[str] = None
) -> ADR:
    """快速创建 ADR"""
    now = datetime.now().strftime("%Y-%m-%d")
    return ADR(
        adr_id=adr_id,
        title=title,
        status=ADRStatus.PROPOSED,
        date_created=now,
        date_updated=now,
        background=background,
        decision=decision,
        consequences=consequences,
        alternatives_considered=alternatives or [],
        tags=tags or []
    )


def get_active_adrs() -> List[ADR]:
    """获取活跃 ADR"""
    return get_adr_registry().get_active()


def search_adrs(query: str) -> List[ADR]:
    """搜索 ADR"""
    return get_adr_registry().search(query)
