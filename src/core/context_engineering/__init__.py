"""
Context Engineering Module
基于 Anthropic Context Engineering 原则的上下文工程组件

包含：
- JustInTimeContextRetriever: Just-in-time 上下文检索
- ContextCompactor: 上下文压缩
- SimplifiedToolRegistry: 精简工具集
- StructuredMemorySystem: 结构化记忆系统
"""
from src.core.context_engineering.just_in_time_retriever import (
    JustInTimeContextRetriever,
    ContextPriority,
    ContextReference,
    get_context_retriever
)

from src.core.context_engineering.context_compactor import (
    ContextCompactor,
    CompactionTrigger,
    ConversationMessage,
    ContextSummary,
    get_context_compactor
)

from src.core.context_engineering.simplified_tools import (
    SimplifiedToolRegistry,
    ToolCategory,
    ToolSpec,
    get_simplified_registry
)

from src.core.context_engineering.structured_memory import (
    StructuredMemorySystem,
    MemoryType,
    MemoryEntry,
    get_memory_system
)

__all__ = [
    # Just-in-time retrieval
    "JustInTimeContextRetriever",
    "ContextPriority", 
    "ContextReference",
    "get_context_retriever",
    
    # Context compaction
    "ContextCompactor",
    "CompactionTrigger",
    "ConversationMessage",
    "ContextSummary",
    "get_context_compactor",
    
    # Simplified tools
    "SimplifiedToolRegistry",
    "ToolCategory",
    "ToolSpec",
    "get_simplified_registry",
    
    # Structured memory
    "StructuredMemorySystem",
    "MemoryType",
    "MemoryEntry",
    "get_memory_system",
]
