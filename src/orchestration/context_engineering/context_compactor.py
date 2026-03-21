"""
Context Compaction System - 上下文压缩机制
基于 Anthropic Context Engineering 原则

核心思想：
- 当对话接近上下文窗口限制时，进行压缩
- 总结关键信息，用摘要替代完整历史
- 保留最重要的上下文：决策、未解决的问题、架构细节
"""
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class CompactionTrigger(Enum):
    """压缩触发条件"""
    TOKEN_THRESHOLD = "token_threshold"      # Token 数量达到阈值
    MESSAGE_COUNT = "message_count"          # 消息数量达到阈值
    MANUAL = "manual"                        # 手动触发
    IDLE_TIMEOUT = "idle_timeout"           # 空闲超时


@dataclass
class ConversationMessage:
    """对话消息"""
    role: str
    content: str
    timestamp: float
    token_count: int
    importance: float = 0.5  # 0-1 重要性评分
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "token_count": self.token_count,
            "importance": self.importance,
            "metadata": self.metadata
        }


@dataclass
class ContextSummary:
    """上下文摘要"""
    summary_text: str
    key_decisions: List[str]
    unresolved_issues: List[str]
    important_context: Dict[str, Any]
    original_message_count: int
    compressed_to_count: int
    token_saved: int
    created_at: float


class ContextCompactor:
    """
    上下文压缩器
    
    功能：
    1. 监控上下文使用情况
    2. 触发压缩时机
    3. 生成高质量摘要
    4. 保留最关键的信息
    """
    
    def __init__(
        self,
        token_threshold: int = 80000,
        message_threshold: int = 50,
        min_messages_to_compact: int = 10,
        preserve_recent: int = 5
    ):
        # 阈值配置
        self.token_threshold = token_threshold
        self.message_threshold = message_threshold
        self.min_messages_to_compact = min_messages_to_compact
        self.preserve_recent = preserve_recent  # 保留最近N条消息
        
        # 消息历史
        self.messages: List[ConversationMessage] = []
        
        # 摘要历史
        self.summaries: List[ContextSummary] = []
        
        # 统计
        self.stats = {
            "compaction_count": 0,
            "total_tokens_saved": 0,
            "last_compaction": None
        }
    
    def add_message(
        self,
        role: str,
        content: str,
        token_count: Optional[int] = None,
        importance: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """添加消息到历史"""
        if token_count is None:
            token_count = len(content) // 4  # 粗略估算
        
        msg = ConversationMessage(
            role=role,
            content=content,
            timestamp=time.time(),
            token_count=token_count,
            importance=importance,
            metadata=metadata or {}
        )
        self.messages.append(msg)
    
    def should_compact(self) -> Tuple[bool, CompactionTrigger]:
        """检查是否应该触发压缩"""
        total_tokens = sum(m.token_count for m in self.messages)
        
        # Token 阈值检查
        if total_tokens >= self.token_threshold:
            return True, CompactionTrigger.TOKEN_THRESHOLD
        
        # 消息数量检查
        if len(self.messages) >= self.message_threshold:
            return True, CompactionTrigger.MESSAGE_COUNT
        
        return False, None
    
    def compact(
        self,
        llm_summarizer: Optional[Any] = None,
        preserve_patterns: Optional[List[str]] = None
    ) -> ContextSummary:
        """
        执行上下文压缩
        
        保留：
        1. 架构决策
        2. 未解决的 bug
        3. 实现细节
        4. 最近的消息（对话上下文）
        
        丢弃：
        1. 冗余的工具调用结果
        2. 早期的探索性对话
        3. 重复的信息
        """
        if len(self.messages) < self.min_messages_to_compact:
            raise ValueError("消息数量不足，无法压缩")
        
        # 保留最近的消息
        recent_messages = self.messages[-self.preserve_recent:]
        recent_tokens = sum(m.token_count for m in recent_messages)
        
        # 需要压缩的历史消息
        history_to_compact = self.messages[:-self.preserve_recent]
        
        if not history_to_compact:
            raise ValueError("没有需要压缩的历史消息")
        
        # 按重要性排序
        sorted_history = sorted(
            history_to_compact,
            key=lambda m: (
                m.importance,
                m.token_count  # 优先保留内容丰富的
            ),
            reverse=True
        )
        
        # 选择要保留的高重要性消息
        kept_messages = []
        kept_tokens = 0
        target_tokens = self.token_threshold - recent_tokens - 10000  # 留 10K buffer
        
        for msg in sorted_history:
            if kept_tokens + msg.token_count <= target_tokens:
                kept_messages.append(msg)
                kept_tokens += msg.token_count
        
        # 生成摘要
        summary = self._generate_summary(
            kept_messages,
            len(self.messages),
            sum(m.token_count for m in history_to_compact)
        )
        
        # 压缩后的消息
        compressed_messages = recent_messages + kept_messages
        
        # 更新历史
        old_count = len(self.messages)
        self.messages = compressed_messages
        
        # 记录统计
        self.stats["compaction_count"] += 1
        self.stats["total_tokens_saved"] += summary.token_saved
        self.stats["last_compact"] = time.time()
        self.summaries.append(summary)
        
        return summary
    
    def _generate_summary(
        self,
        kept_messages: List[ConversationMessage],
        original_count: int,
        original_tokens: int
    ) -> ContextSummary:
        """生成摘要（简化版，实际可用 LLM）"""
        
        # 提取关键信息
        key_decisions = []
        unresolved_issues = []
        
        for msg in kept_messages:
            content = msg.content.lower()
            
            # 简单关键词检测
            if any(k in content for k in ["decided", "decision", "选择", "决定"]):
                key_decisions.append(msg.content[:100])
            
            if any(k in content for k in ["bug", "issue", "problem", "未解决", "问题"]):
                unresolved_issues.append(msg.content[:100])
        
        # 限制数量
        key_decisions = key_decisions[-5:]
        unresolved_issues = unresolved_issues[-5:]
        
        # 摘要文本
        summary_text = f"压缩了 {original_count} 条消息。保留 {len(kept_messages)} 条重要消息。"
        
        if key_decisions:
            summary_text += f" 关键决策: {'; '.join(key_decisions[:2])}"
        
        compressed_tokens = sum(m.token_count for m in kept_messages)
        
        return ContextSummary(
            summary_text=summary_text,
            key_decisions=key_decisions,
            unresolved_issues=unresolved_issues,
            important_context={
                "message_count": len(kept_messages),
                "roles": list(set(m.role for m in kept_messages))
            },
            original_message_count=original_count,
            compressed_to_count=len(kept_messages),
            token_saved=original_tokens - compressed_tokens,
            created_at=time.time()
        )
    
    def get_compacted_messages(self) -> List[Dict]:
        """获取压缩后的消息列表（适合放入 prompt）"""
        result = []
        
        # 添加摘要
        if self.summaries:
            latest = self.summaries[-1]
            result.append({
                "role": "system",
                "content": f"""[Context Summary - Previous Conversation]
{latest.summary_text}

Key Decisions Made:
{chr(10).join(f"- {d}" for d in latest.key_decisions)}

Unresolved Issues:
{chr(10).join(f"- {i}" for i in latest.unresolved_issues)}

This summary replaces {latest.original_message_count - latest.compressed_to_count} earlier messages.
"""
            })
        
        # 添加保留的消息
        for msg in self.messages:
            result.append(msg.to_dict())
        
        return result
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "current_message_count": len(self.messages),
            "current_token_estimate": sum(m.token_count for m in self.messages),
            "summary_count": len(self.summaries)
        }
    
    def clear_history(self) -> None:
        """清除历史（用于新会话）"""
        self.messages = []
        self.summaries = []


# 工具函数：安全地清理工具结果
def should_clear_tool_result(message: ConversationMessage) -> bool:
    """
    判断是否应该清除工具调用结果
    最轻量的压缩形式：只清除旧工具结果
    """
    if message.role != "tool":
        return False
    
    # 检查是否是深层历史中的工具调用
    # 实际实现需要结合上下文位置判断
    return True


# 全局实例
_compactor: Optional[ContextCompactor] = None


def get_context_compactor() -> ContextCompactor:
    """获取全局上下文压缩器"""
    global _compactor
    if _compactor is None:
        _compactor = ContextCompactor()
    return _compactor
