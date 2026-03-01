"""
Structured Memory System - 结构化记忆系统
基于 Anthropic Context Engineering 原则

核心思想（类似 Claude Code 的 NOTES.md）：
- Agent 在工作过程中主动记录笔记
- 笔记持久化到文件系统
- 在需要时加载相关笔记
- 支持跨会话持久化
"""
import os
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    PROGRESS = "progress"           # 进度追踪
    DECISION = "decision"           # 决策记录
    ISSUE = "issue"                # 问题/待办
    CONTEXT = "context"            # 上下文信息
    LEARNING = "learning"          # 学习到的知识


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str
    memory_type: MemoryType
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = [
            f"## {self.title}",
            f"*Type: {self.memory_type.value} | Created: {time.strftime('%Y-%m-%d %H:%M')}*",
            "",
            self.content,
        ]
        
        if self.tags:
            lines.append(f"\nTags: {', '.join(self.tags)}")
        
        return "\n".join(lines)


class StructuredMemorySystem:
    """
    结构化记忆系统
    
    功能：
    1. 记录笔记（PROGRESS, DECISION, ISSUE, CONTEXT, LEARNING）
    2. 持久化到文件
    3. 按类型/标签检索
    4. 支持上下文加载
    """
    
    def __init__(
        self,
        memory_dir: str = "data/memory",
        max_memory_tokens: int = 8000
    ):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_tokens = max_memory_tokens
        
        # 内存索引
        self._index: Dict[str, MemoryEntry] = {}
        
        # 加载已有记忆
        self._load_index()
        
        # 统计
        self.stats = {
            "total_entries": len(self._index),
            "sessions": len(set(m.session_id for m in self._index.values() if m.session_id))
        }
    
    def _load_index(self) -> None:
        """加载记忆索引"""
        index_file = self.memory_dir / "index.json"
        
        if index_file.exists():
            with open(index_file, 'r') as f:
                data = json.load(f)
                for entry_data in data.get("entries", []):
                    entry = MemoryEntry(
                        id=entry_data["id"],
                        memory_type=MemoryType(entry_data["memory_type"]),
                        title=entry_data["title"],
                        content=entry_data["content"],
                        tags=entry_data.get("tags", []),
                        created_at=entry_data.get("created_at", time.time()),
                        updated_at=entry_data.get("updated_at", time.time()),
                        session_id=entry_data.get("session_id"),
                        metadata=entry_data.get("metadata", {})
                    )
                    self._index[entry.id] = entry
    
    def _save_index(self) -> None:
        """保存记忆索引"""
        index_file = self.memory_dir / "index.json"
        
        data = {
            "entries": [
                {
                    "id": m.id,
                    "memory_type": m.memory_type.value,
                    "title": m.title,
                    "content": m.content,
                    "tags": m.tags,
                    "created_at": m.created_at,
                    "updated_at": m.updated_at,
                    "session_id": m.session_id,
                    "metadata": m.metadata
                }
                for m in self._index.values()
            ]
        }
        
        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def remember(
        self,
        memory_type: MemoryType,
        title: str,
        content: str,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MemoryEntry:
        """
        记录一条记忆
        
        Agent 在工作过程中应该主动调用此方法记录：
        - 完成的进度
        - 做出的决策
        - 遇到的问题
        - 重要的上下文
        - 学到的知识
        """
        import hashlib
        
        entry_id = hashlib.md5(
            f"{title}:{time.time()}".encode()
        ).hexdigest()[:12]
        
        entry = MemoryEntry(
            id=entry_id,
            memory_type=memory_type,
            title=title,
            content=content,
            tags=tags or [],
            session_id=session_id,
            metadata=metadata or {}
        )
        
        # 保存到索引
        self._index[entry_id] = entry
        
        # 持久化
        self._save_index()
        
        # 保存为单独文件（NOTE.md 风格）
        self._save_as_markdown(entry)
        
        return entry
    
    def _save_as_markdown(self, entry: MemoryEntry) -> None:
        """保存为 Markdown 文件"""
        # 按类型分组目录
        type_dir = self.memory_dir / entry.memory_type.value
        type_dir.mkdir(exist_ok=True)
        
        filename = type_dir / f"{entry.id}.md"
        with open(filename, 'w') as f:
            f.write(entry.to_markdown())
    
    def recall(
        self,
        memory_type: Optional[MemoryType] = None,
        tags: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        检索记忆
        
        根据条件检索相关记忆
        """
        results = list(self._index.values())
        
        # 按类型过滤
        if memory_type:
            results = [m for m in results if m.memory_type == memory_type]
        
        # 按标签过滤
        if tags:
            results = [m for m in results if any(t in m.tags for t in tags)]
        
        # 按会话过滤
        if session_id:
            results = [m for m in results if m.session_id == session_id]
        
        # 按更新时间排序（最新的优先）
        results.sort(key=lambda m: m.updated_at, reverse=True)
        
        return results[:limit]
    
    def get_progress_notes(self, session_id: Optional[str] = None) -> str:
        """
        获取进度笔记（供 prompt 使用）
        以 NOTE.md 风格返回
        """
        memories = self.recall(
            memory_type=MemoryType.PROGRESS,
            session_id=session_id,
            limit=20
        )
        
        if not memories:
            return ""
        
        lines = [
            "# Progress Notes",
            "=" * 50,
            ""
        ]
        
        for m in memories:
            lines.append(m.to_markdown())
            lines.append("")
        
        return "\n".join(lines)
    
    def get_decisions(self, session_id: Optional[str] = None) -> str:
        """获取决策记录"""
        memories = self.recall(
            memory_type=MemoryType.DECISION,
            session_id=session_id,
            limit=10
        )
        
        if not memories:
            return ""
        
        lines = [
            "# Key Decisions",
            "=" * 50,
            ""
        ]
        
        for m in memories:
            lines.append(f"- **{m.title}**: {m.content[:100]}")
        
        return "\n".join(lines)
    
    def get_issues(self, session_id: Optional[str] = None) -> str:
        """获取问题/待办"""
        memories = self.recall(
            memory_type=MemoryType.ISSUE,
            session_id=session_id,
            limit=10
        )
        
        if not memories:
            return ""
        
        lines = [
            "# Unresolved Issues",
            "=" * 50,
            ""
        ]
        
        for m in memories:
            lines.append(f"- [ ] **{m.title}**: {m.content[:100]}")
        
        return "\n".join(lines)
    
    def get_context_for_prompt(
        self,
        session_id: Optional[str] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        获取记忆上下文（供 prompt 使用）
        
        只返回关键信息，控制 token 数量
        """
        if max_tokens is None:
            max_tokens = self.max_memory_tokens
        
        # 获取各类记忆
        decisions = self.get_decisions(session_id)
        issues = self.get_issues(session_id)
        progress = self.get_progress_notes(session_id)
        
        # 合并并截断
        context_parts = []
        current_tokens = 0
        
        for part in [decisions, issues, progress]:
            part_tokens = len(part) // 4
            if current_tokens + part_tokens <= max_tokens:
                context_parts.append(part)
                current_tokens += part_tokens
            else:
                break
        
        if not context_parts:
            return ""
        
        return """
## From Memory (Persistent Context)
---
""" + "\n\n---\n\n".join(context_parts)
    
    def update_progress(
        self,
        task: str,
        status: str,
        details: str = "",
        session_id: Optional[str] = None
    ) -> None:
        """快捷方法：更新进度"""
        self.remember(
            memory_type=MemoryType.PROGRESS,
            title=f"{task} - {status}",
            content=details or f"Task '{task}' status: {status}",
            tags=["progress", task],
            session_id=session_id
        )
    
    def record_decision(
        self,
        decision: str,
        reason: str,
        session_id: Optional[str] = None
    ) -> None:
        """快捷方法：记录决策"""
        self.remember(
            memory_type=MemoryType.DECISION,
            title=f"Decision: {decision[:50]}",
            content=f"Decision: {decision}\n\nReason: {reason}",
            tags=["decision"],
            session_id=session_id
        )
    
    def record_issue(
        self,
        title: str,
        description: str,
        session_id: Optional[str] = None
    ) -> None:
        """快捷方法：记录问题"""
        self.remember(
            memory_type=MemoryType.ISSUE,
            title=f"Issue: {title}",
            content=description,
            tags=["issue", "todo"],
            session_id=session_id
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        type_counts = {}
        for mem_type in MemoryType:
            type_counts[mem_type.value] = len([
                m for m in self._index.values() if m.memory_type == mem_type
            ])
        
        return {
            "total_entries": len(self._index),
            "by_type": type_counts,
            "sessions": self.stats["sessions"]
        }


# 全局实例
_memory_system: Optional[StructuredMemorySystem] = None


def get_memory_system() -> StructuredMemorySystem:
    """获取全局记忆系统"""
    global _memory_system
    if _memory_system is None:
        _memory_system = StructuredMemorySystem()
    return _memory_system
