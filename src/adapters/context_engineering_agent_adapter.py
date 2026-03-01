#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ContextEngineeringAgent → MemoryManager 迁移适配器

将 ContextEngineeringAgent 的调用适配到 MemoryManager，实现平滑迁移。
注意：ContextEngineeringAgent专注于上下文工程，而MemoryManager专注于记忆管理。
适配器将上下文工程任务转换为记忆管理任务。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.memory_manager import MemoryManager
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class ContextEngineeringAgentAdapter(MigrationAdapter):
    """ContextEngineeringAgent → MemoryManager 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="ContextEngineeringAgent",
            target_agent_name="MemoryManager"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（MemoryManager）"""
        return MemoryManager()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        ContextEngineeringAgent 参数格式:
        {
            'task_type': str,  # 'add_context', 'get_context', 'compress_context', 'manage_memory', 'associate_context'
            'session_id': str,  # 会话ID
            'content': str,  # 上下文内容（用于add_context）
            'category': str,  # 上下文类别
            'scope': str,  # 上下文范围（short_term/long_term）
            'source': str,  # 上下文来源
            'metadata': Dict,  # 元数据
            'max_fragments': int,  # 最大片段数（用于get_context）
            'fragment_id': str,  # 片段ID（用于管理）
            ...
        }
        
        MemoryManager 参数格式:
        {
            'action': str,  # 'store', 'retrieve', 'associate', 'compress', 'stats'
            'content': str,  # 要存储的内容 (store时需要)
            'memory_type': str,  # 记忆类型 (store时需要)
            'query': str,  # 检索查询 (retrieve时需要)
            'source_id/target_id': str,  # 关联ID (associate时需要)
            'limit': int,  # 检索数量限制 (retrieve时可选，默认10)
            ...
        }
        """
        adapted = super().adapt_context(old_context)
        
        # 提取原始参数
        task_type = old_context.get("task_type", "get_context")
        session_id = old_context.get("session_id", "")
        content = old_context.get("content", "")
        category = old_context.get("category", "informational")
        scope = old_context.get("scope", "short_term")
        source = old_context.get("source", "user_input")
        metadata = old_context.get("metadata", {})
        max_fragments = old_context.get("max_fragments", 10)
        fragment_id = old_context.get("fragment_id", "")
        
        # 将task_type映射到action
        action_mapping = {
            "add_context": "store",
            "get_context": "retrieve",
            "compress_context": "compress",
            "manage_memory": "store",  # 管理记忆 -> 存储
            "associate_context": "associate",
        }
        action = action_mapping.get(task_type, "retrieve")
        
        # 将scope映射到memory_type
        memory_type_mapping = {
            "short_term": "short_term",
            "long_term": "long_term",
            "implicit": "episodic",
        }
        memory_type = memory_type_mapping.get(scope, "short_term")
        
        # 转换参数格式
        adapted.update({
            "action": action,
            # 对于store操作
            "content": content,
            "memory_type": memory_type,
            # 对于retrieve操作
            "query": old_context.get("query", content),  # 如果没有query，使用content
            "limit": max_fragments,
            # 对于associate操作
            "source_id": fragment_id or session_id,
            "target_id": old_context.get("target_id", ""),
            # 保留原始参数供参考
            "session_id": session_id,
            "category": category,
            "scope": scope,
            "source": source,
            "metadata": metadata,
            "fragment_id": fragment_id,
            "_original_task_type": task_type,
        })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_context",
            "original_keys": list(old_context.keys()),
            "adapted_keys": list(adapted.keys()),
            "task_type": task_type,
            "mapped_action": action
        })
        
        return adapted
    
    def adapt_result(self, new_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换执行结果
        
        MemoryManager 返回格式:
        {
            'success': bool,
            'data': {
                'memories': List,  # 记忆列表
                'memory_id': str,  # 记忆ID
                'compressed_content': str,  # 压缩后的内容
                'associations': List,  # 关联关系
                ...
            },
            'confidence': float,
            ...
        }
        
        ContextEngineeringAgent 期望格式:
        {
            'success': bool,
            'data': {
                'context': Dict,  # 上下文
                'user_context': Dict,  # 用户上下文
                'fragments': List,  # 上下文片段
                'compressed_context': str,  # 压缩后的上下文
                ...
            },
            'confidence': float,
            ...
        }
        """
        adapted = super().adapt_result(new_result)
        
        # 如果结果是AgentResult对象，转换为字典
        if hasattr(new_result, 'success'):
            data = new_result.data if hasattr(new_result, 'data') else {}
            
            # 提取上下文工程相关数据
            context_data = self._extract_context_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": context_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取上下文工程相关数据
            context_data = self._extract_context_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": context_data,
                "confidence": new_result.get("confidence", 0.7),
                "error": new_result.get("error"),
            })
        
        # 记录转换详情
        self.log_migration({
            "action": "adapt_result",
            "result_keys": list(adapted.keys()),
            "has_context": "context" in str(adapted.get("data", {}))
        })
        
        return adapted
    
    def _extract_context_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从MemoryManager的结果中提取上下文工程数据"""
        context_data = {}
        
        # 提取memories（转换为fragments）
        if "memories" in data:
            memories = data["memories"]
            if isinstance(memories, list):
                # 将memories转换为fragments格式
                fragments = []
                for memory in memories:
                    if isinstance(memory, dict):
                        fragment = {
                            "id": memory.get("id", memory.get("memory_id", "")),
                            "content": memory.get("content", ""),
                            "category": memory.get("category", "informational"),
                            "scope": memory.get("scope", "short_term"),
                            "source": memory.get("source", "user_input"),
                            "metadata": memory.get("metadata", {}),
                        }
                        fragments.append(fragment)
                context_data["fragments"] = fragments
                context_data["context"] = {"fragments": fragments}
        
        # 提取compressed_content（转换为compressed_context）
        if "compressed_content" in data:
            context_data["compressed_context"] = data["compressed_content"]
        
        # 提取memory_id（如果有）
        if "memory_id" in data:
            context_data["memory_id"] = data["memory_id"]
        
        # 提取associations（如果有）
        if "associations" in data:
            context_data["associations"] = data["associations"]
        
        # 如果没有找到上下文数据，返回空结构
        if not context_data:
            context_data = {
                "context": {},
                "user_context": {},
                "fragments": [],
                "compressed_context": ""
            }
        
        return context_data

