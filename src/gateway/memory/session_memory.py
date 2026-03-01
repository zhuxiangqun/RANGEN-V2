"""
Session Memory - 会话记忆管理

实现分层记忆系统
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import json

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class MemoryEntry:
    """记忆条目"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionMemory:
    """
    会话记忆管理
    
    实现短期记忆（当前会话）和上下文窗口管理
    """
    
    def __init__(
        self,
        context_window: int = 10,
        max_memory_entries: int = 100
    ):
        self.context_window = context_window  # 保留最近 N 轮
        self.max_memory_entries = max_memory_entries
        
        # 内存存储: session_id -> deque of MemoryEntry
        self._memories: Dict[str, deque] = {}
        
        # 持久化存储（可选）
        self._storage = None
        
        # 锁
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, session_id: str) -> asyncio.Lock:
        """获取会话锁"""
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]
    
    def _get_memory_deque(self, session_id: str) -> deque:
        """获取会话的记忆队列"""
        if session_id not in self._memories:
            self._memories[session_id] = deque(maxlen=self.max_memory_entries)
        return self._memories[session_id]
    
    async def get_memory(self, session_id: str) -> List[Dict]:
        """
        获取会话记忆
        
        Args:
            session_id: 会话ID
            
        Returns:
            List[Dict]: 记忆列表 [{"role": "user", "content": "..."}, ...]
        """
        lock = self._get_lock(session_id)
        async with lock:
            memory_deque = self._get_memory_deque(session_id)
            
            # 获取最近 N 轮
            recent_entries = list(memory_deque)[-self.context_window:]
            
            return [
                {"role": entry.role, "content": entry.content}
                for entry in recent_entries
            ]
    
    async def add_interaction(
        self,
        session_id: str,
        user_input: str,
        agent_response: str
    ):
        """
        添加交互到记忆
        
        Args:
            session_id: 会话ID
            user_input: 用户输入
            agent_response: Agent 响应
        """
        lock = self._get_lock(session_id)
        async with lock:
            memory_deque = self._get_memory_deque(session_id)
            
            # 添加用户消息
            memory_deque.append(MemoryEntry(
                role="user",
                content=user_input
            ))
            
            # 添加助手消息
            memory_deque.append(MemoryEntry(
                role="assistant",
                content=agent_response
            ))
            
            logger.debug(f"Added interaction to session {session_id}")
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """
        添加单条消息到记忆
        
        Args:
            session_id: 会话ID
            role: 角色 ("user", "assistant", "system")
            content: 内容
            metadata: 元数据
        """
        lock = self._get_lock(session_id)
        async with lock:
            memory_deque = self._get_memory_deque(session_id)
            
            memory_deque.append(MemoryEntry(
                role=role,
                content=content,
                metadata=metadata or {}
            ))
    
    async def clear_session(self, session_id: str):
        """
        清除会话记忆
        
        Args:
            session_id: 会话ID
        """
        lock = self._get_lock(session_id)
        async with lock:
            if session_id in self._memories:
                self._memories[session_id].clear()
                
                # 移除锁
                if session_id in self._locks:
                    del self._locks[session_id]
            
            logger.info(f"Cleared memory for session {session_id}")
    
    async def get_summary(self, session_id: str) -> str:
        """
        获取会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            str: 摘要文本
        """
        memory = await self.get_memory(session_id)
        
        if not memory:
            return "No conversation history."
        
        # 简单摘要：显示轮数和首尾消息
        turns = len(memory) // 2
        first_msg = memory[0]["content"][:100] if memory else ""
        last_msg = memory[-1]["content"][:100] if memory else ""
        
        return f"Conversation: {turns} turns. Started with: '{first_msg}...' Recent: '{last_msg}...'"
    
    async def save_all(self):
        """保存所有会话到持久化存储"""
        # 如果配置了持久化存储
        if not self._storage:
            return
        
        for session_id, memory_deque in self._memories.items():
            entries = [
                {
                    "role": e.role,
                    "content": e.content,
                    "timestamp": e.timestamp.isoformat(),
                    "metadata": e.metadata
                }
                for e in memory_deque
            ]
            
            await self._storage.save(session_id, entries)
    
    async def load_session(self, session_id: str) -> bool:
        """
        从持久化存储加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 是否成功加载
        """
        if not self._storage:
            return False
        
        entries = await self._storage.load(session_id)
        
        if not entries:
            return False
        
        lock = self._get_lock(session_id)
        async with lock:
            memory_deque = self._get_memory_deque(session_id)
            
            for entry in entries:
                memory_deque.append(MemoryEntry(
                    role=entry["role"],
                    content=entry["content"],
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                    metadata=entry.get("metadata", {})
                ))
        
        logger.info(f"Loaded session {session_id} with {len(entries)} entries")
        return True
    
    def set_storage(self, storage: Any):
        """设置持久化存储"""
        self._storage = storage
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_sessions": len(self._memories),
            "total_entries": sum(len(d) for d in self._memories.values()),
            "active_locks": len(self._locks)
        }


class FileStorage:
    """简单的文件存储"""
    
    def __init__(self, storage_dir: str = "data/memory"):
        self.storage_dir = storage_dir
        import os
        os.makedirs(storage_dir, exist_ok=True)
    
    async def save(self, session_id: str, entries: List[Dict]):
        """保存到文件"""
        import aiofiles
        
        filepath = f"{self.storage_dir}/{session_id}.json"
        async with aiofiles.open(filepath, 'w') as f:
            await f.write(json.dumps(entries, ensure_ascii=False))
    
    async def load(self, session_id: str) -> List[Dict]:
        """从文件加载"""
        import aiofiles
        import os
        
        filepath = f"{self.storage_dir}/{session_id}.json"
        
        if not os.path.exists(filepath):
            return []
        
        async with aiofiles.open(filepath, 'r') as f:
            content = await f.read()
            return json.loads(content)
