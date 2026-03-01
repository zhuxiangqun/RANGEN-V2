#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MemoryAgent → MemoryManager 迁移适配器

将 MemoryAgent 的调用适配到 MemoryManager，实现平滑迁移。
注意：MemoryAgent和MemoryManager功能相似，都是记忆管理，但接口略有不同。
"""

from typing import Dict, Any, Optional
import logging

from .base_adapter import MigrationAdapter
from ..agents.memory_manager import MemoryManager
from ..agents.base_agent import AgentResult

logger = logging.getLogger(__name__)


class MemoryAgentAdapter(MigrationAdapter):
    """MemoryAgent → MemoryManager 适配器"""
    
    def __init__(self):
        """初始化适配器"""
        super().__init__(
            source_agent_name="MemoryAgent",
            target_agent_name="MemoryManager"
        )
        logger.info(f"初始化适配器: {self.source} → {self.target}")
    
    def _initialize_target_agent(self):
        """初始化目标Agent（MemoryManager）"""
        return MemoryManager()
    
    def adapt_context(self, old_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换上下文参数
        
        MemoryAgent 参数格式:
        {
            'task_type': str,  # 'store', 'retrieve', 'compress', 'manage'
            'session_id': str,  # 会话ID
            'content': str,  # 要存储的内容 (store时需要)
            'category': str,  # 上下文类别
            'scope': str,  # 上下文范围（short_term/long_term）
            'source': str,  # 上下文来源
            'metadata': Dict,  # 元数据
            'max_fragments': int,  # 最大片段数（用于retrieve）
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
        task_type = old_context.get("task_type", "retrieve")
        session_id = old_context.get("session_id", "")
        content = old_context.get("content", "")
        category = old_context.get("category", "informational")
        scope = old_context.get("scope", "short_term")
        source = old_context.get("source", "user_input")
        metadata = old_context.get("metadata", {})
        max_fragments = old_context.get("max_fragments", 10)
        
        # 将task_type映射到action（基本一致）
        action = task_type if task_type in ["store", "retrieve", "compress", "associate", "stats"] else "retrieve"
        
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
            # 保留原始参数供参考
            "session_id": session_id,
            "category": category,
            "scope": scope,
            "source": source,
            "metadata": metadata,
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
        
        MemoryAgent 期望格式:
        {
            'success': bool,
            'data': {
                'user_context': Dict,  # 用户上下文
                'context': Dict,  # 上下文
                'fragments': List,  # 上下文片段
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
            
            # 提取记忆管理相关数据
            memory_data = self._extract_memory_data(data)
            
            adapted.update({
                "success": new_result.success,
                "data": memory_data,
                "confidence": new_result.confidence if hasattr(new_result, 'confidence') else 0.7,
                "error": new_result.error if hasattr(new_result, 'error') else None,
            })
        elif isinstance(new_result, dict):
            # 处理字典格式的结果
            data = new_result.get("data", {})
            
            # 提取记忆管理相关数据
            memory_data = self._extract_memory_data(data)
            
            adapted.update({
                "success": new_result.get("success", True),
                "data": memory_data,
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
    
    def _extract_memory_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """从MemoryManager的结果中提取记忆管理数据"""
        memory_data = {}
        
        # 提取memories（转换为fragments和context）
        if "memories" in data:
            memories = data["memories"]
            if isinstance(memories, list):
                # 将memories转换为fragments格式
                fragments = []
                context_dict = {}
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
                        # 构建context字典
                        context_dict[memory.get("id", "")] = fragment
                memory_data["fragments"] = fragments
                memory_data["context"] = context_dict
                memory_data["user_context"] = context_dict
        
        # 提取compressed_content（如果有）
        if "compressed_content" in data:
            memory_data["compressed_content"] = data["compressed_content"]
        
        # 提取memory_id（如果有）
        if "memory_id" in data:
            memory_data["memory_id"] = data["memory_id"]
        
        # 如果没有找到记忆数据，返回空结构
        if not memory_data:
            memory_data = {
                "user_context": {},
                "context": {},
                "fragments": []
            }
        
        return memory_data

