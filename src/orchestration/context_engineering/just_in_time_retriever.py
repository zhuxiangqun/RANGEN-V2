"""
Just-in-Time Context Retrieval System
基于 Anthropic Context Engineering 原则实现

核心思想：
- 不是预先加载所有相关数据
- 而是维护轻量级标识符（文件路径、存储查询等）
- 让 Agent 在运行时动态加载上下文
"""
import os
import json
import time
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import hashlib


class ContextPriority(Enum):
    """上下文优先级"""
    CRITICAL = "critical"      # 必须保留
    HIGH = "high"             # 重要但可压缩
    MEDIUM = "medium"         # 中等重要性
    LOW = "low"               # 可丢弃


@dataclass
class ContextEntry:
    """上下文条目"""
    key: str
    content: str
    priority: ContextPriority = ContextPriority.MEDIUM
    created_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    token_count: int = 0
    
    def refresh_access(self):
        """刷新访问时间"""
        self.access_count += 1
        self.last_accessed = time.time()


@dataclass
class ContextReference:
    """上下文引用 - 轻量级标识符"""
    ref_id: str
    ref_type: str  # "file", "query", "search", "memory"
    path: Optional[str] = None
    query: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_string(self) -> str:
        """转换为简洁的引用字符串"""
        if self.ref_type == "file":
            return f"📄 {self.path}"
        elif self.ref_type == "query":
            return f"🔍 {self.query}"
        elif self.ref_type == "memory":
            return f"💭 {self.metadata.get('summary', self.ref_id)}"
        return f"📌 {self.ref_id}"


class JustInTimeContextRetriever:
    """
    Just-in-Time 上下文检索器
    
    核心原则：
    1. 只在需要时加载上下文
    2. 维护轻量级引用而非完整内容
    3. 支持渐进式上下文发现
    """
    
    def __init__(
        self,
        max_token_budget: int = 40000,
        base_dir: str = "data/context"
    ):
        self.max_token_budget = max_token_budget
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中的上下文缓存
        self._context_cache: Dict[str, ContextEntry] = {}
        
        # 上下文引用（轻量级标识符）
        self._references: List[ContextReference] = []
        
        # 已加载的完整上下文
        self._loaded_contexts: Dict[str, str] = {}
        
        # 统计信息
        self.stats = {
            "total_loads": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "token_saved": 0
        }
    
    def register_reference(
        self,
        ref_type: str,
        path: Optional[str] = None,
        query: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextReference:
        """
        注册一个上下文引用
        这是轻量级操作，不加载实际内容
        """
        ref_id = hashlib.md5(
            f"{ref_type}:{path or query}:{time.time()}".encode()
        ).hexdigest()[:8]
        
        ref = ContextReference(
            ref_id=ref_id,
            ref_type=ref_type,
            path=path,
            query=query,
            metadata=metadata or {}
        )
        
        self._references.append(ref)
        return ref
    
    def load_context(
        self,
        reference: ContextReference,
        priority: ContextPriority = ContextPriority.MEDIUM
    ) -> str:
        """
        按需加载上下文内容
        只有被明确请求时才加载完整内容
        """
        self.stats["total_loads"] += 1
        
        # 检查缓存
        if reference.ref_id in self._loaded_contexts:
            self.stats["cache_hits"] += 1
            return self._loaded_contexts[reference.ref_id]
        
        self.stats["cache_misses"] += 1
        
        # 根据类型加载内容
        content = self._load_by_type(reference)
        
        if content:
            # 估算 token 数
            token_count = len(content) // 4
            
            # 存储到缓存
            self._loaded_contexts[reference.ref_id] = content
            self._context_cache[reference.ref_id] = ContextEntry(
                key=reference.ref_id,
                content=content,
                priority=priority,
                token_count=token_count
            )
        
        return content or ""
    
    def _load_by_type(self, ref: ContextReference) -> str:
        """根据引用类型加载内容"""
        if ref.ref_type == "file" and ref.path:
            return self._load_file(ref.path)
        elif ref.ref_type == "query":
            return self._load_search_results(ref.query)
        elif ref.ref_type == "memory":
            return self._load_memory(ref.ref_id)
        return ""
    
    def _load_file(self, path: str) -> str:
        """加载文件内容"""
        try:
            full_path = self.base_dir.parent / path
            if full_path.exists():
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception:
            pass
        return ""
    
    def _load_search_results(self, query: Optional[str]) -> str:
        """加载搜索结果（模拟）"""
        if not query:
            return ""
        # 实际实现中，这里会调用搜索服务
        return f"[Search results for: {query}]"
    
    def _load_memory(self, ref_id: str) -> str:
        """加载记忆内容"""
        memory_file = self.base_dir / "memories" / f"{ref_id}.md"
        if memory_file.exists():
            with open(memory_file, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def get_context_for_prompt(
        self,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        获取当前上下文的摘要，供 prompt 使用
        只返回轻量级引用，而非完整内容
        """
        if max_tokens is None:
            max_tokens = self.max_token_budget
        
        # 返回引用列表而非完整内容
        refs_summary = "\n".join([
            f"- {ref.to_string()}"
            for ref in self._references[-10:]  # 最近10个引用
        ])
        
        return f"""
## Available Context References:
{refs_summary}

Note: Use load_context() to retrieve full content when needed.
"""
    
    def compact_context(
        self,
        summary_prompt: str = "Summarize this conversation, preserving key decisions, unresolved issues, and important context."
    ) -> Dict[str, Any]:
        """
        上下文压缩
        保留关键信息，清理冗余内容
        """
        # 按优先级和访问频率排序
        sorted_contexts = sorted(
            self._context_cache.values(),
            key=lambda x: (
                x.priority.value,
                x.access_count,
                x.last_accessed
            ),
            reverse=True
        )
        
        # 保留高优先级的上下文
        kept = []
        total_tokens = 0
        
        for ctx in sorted_contexts:
            if total_tokens + ctx.token_count <= self.max_token_budget // 2:
                kept.append(ctx)
                total_tokens += ctx.token_count
            else:
                break
        
        # 更新缓存
        self._context_cache = {c.key: c for c in kept}
        self.stats["token_saved"] = total_tokens
        
        return {
            "kept_count": len(kept),
            "total_tokens": total_tokens,
            "summary": f"Compressed to {len(kept)} context entries"
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_hit_rate = (
            self.stats["cache_hits"] / self.stats["total_loads"]
            if self.stats["total_loads"] > 0 else 0
        )
        
        return {
            **self.stats,
            "cache_hit_rate": f"{cache_hit_rate:.1%}",
            "references_count": len(self._references),
            "cached_contexts": len(self._context_cache)
        }


# 全局实例
_retriever: Optional[JustInTimeContextRetriever] = None


def get_context_retriever() -> JustInTimeContextRetriever:
    """获取全局上下文检索器实例"""
    global _retriever
    if _retriever is None:
        _retriever = JustInTimeContextRetriever()
    return _retriever
