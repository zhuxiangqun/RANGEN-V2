#!/usr/bin/env python3
"""
Learning-Enabled Memory Manager
================================

将自我学习能力集成到记忆管理系统中

功能:
- 基于学习的重要性评分
- 自适应压缩策略
- 智能遗忘管理
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..agents.memory_manager import MemoryManager, Memory, MemoryType
from src.core.self_learning import (
    get_context_management_learner,
    ContextItem,
    UsageOutcome
)

logger = logging.getLogger(__name__)


class LearningMemoryManager(MemoryManager):
    """
    带学习能力的记忆管理器
    
    继承MemoryManager的所有功能，并增加:
    - 基于学习的重要性评分
    - 自适应压缩
    - 智能遗忘
    """
    
    def __init__(self, *args, **kwargs):
        """初始化带学习的记忆管理器"""
        super().__init__(*args, **kwargs)
        
        # 初始化上下文管理学习器
        self.context_learner = get_context_management_learner()
        
        # 学习开关
        self.learning_enabled = True
        
        # 学习统计
        self._learning_memory_stats = {
            "importance_predictions": 0,
            "compression_decisions": 0,
            "forgetting_decisions": 0
        }
        
        logger.info("✅ LearningMemoryManager initialized")
    
    def add_memory_with_learning(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        importance: float = 0.5,
        metadata: Dict = None
    ) -> str:
        """
        添加记忆（带学习功能）
        
        自动预测重要性并学习
        """
        # 使用学习器预测重要性
        if self.learning_enabled:
            predicted_importance = self.context_learner.predict_importance(
                content=content,
                metadata=metadata
            )
            
            # 综合重要性
            final_importance = (importance + predicted_importance) / 2
        else:
            final_importance = importance
        
        # 添加记忆
        memory_id = self.add_memory(
            content=content,
            memory_type=memory_type,
            importance=final_importance,
            metadata=metadata
        )
        
        # 记录到学习系统
        if self.learning_enabled and memory_id:
            self.context_learner.add_context_item(
                item_id=memory_id,
                content=content,
                base_importance=final_importance,
                keywords=metadata.get("keywords", []) if metadata else [],
                metadata=metadata
            )
            
            self._learning_memory_stats["importance_predictions"] += 1
        
        return memory_id
    
    def retrieve_with_learning(
        self,
        query: str,
        limit: int = 10,
        context_keywords: List[str] = None
    ) -> List[Memory]:
        """
        检索记忆（带学习功能）
        
        使用学习的重要性排序
        """
        # 获取所有记忆
        all_memories = self.search_memories(query)
        
        if not all_memories:
            return []
        
        # 使用学习器获取重要上下文
        if self.learning_enabled:
            important_items = self.context_learner.get_important_context(
                context_keywords=context_keywords or self._extract_keywords(query),
                max_items=limit * 2
            )
            
            important_ids = {item.item_id for item in important_items}
            
            # 重新排序：优先返回重要的
            def sort_key(m: Memory) -> float:
                base_score = m.importance_score
                
                # 如果在重要上下文中，加分
                if m.memory_id in important_ids:
                    base_score += 0.3
                
                # 考虑记忆类型
                if m.memory_type == MemoryType.LONG_TERM:
                    base_score += 0.1
                
                return base_score
            
            all_memories.sort(key=sort_key, reverse=True)
        
        return all_memories[:limit]
    
    def compress_with_learning(self) -> Dict[str, Any]:
        """
        压缩记忆（带学习功能）
        
        基于学习决定压缩策略
        """
        # 调用父类压缩
        result = self.compress()
        
        if self.learning_enabled:
            # 记录压缩决策
            should_compress, to_remove = self.context_learner.should_compress()
            
            result["learning_decision"] = {
                "should_compress": should_compress,
                "items_to_remove": len(to_remove),
                "reason": "Based on learned importance"
            }
            
            self._learning_memory_stats["compression_decisions"] += 1
        
        return result
    
    def record_memory_usage(
        self,
        memory_id: str,
        was_useful: bool,
        quality_improvement: float = 0.0
    ):
        """
        记录记忆使用结果，用于学习
        """
        if not self.learning_enabled:
            return
        
        # 获取记忆
        memory = self.get_memory(memory_id)
        if not memory:
            return
        
        # 记录到学习系统
        outcome = UsageOutcome(
            item_used=True,
            useful=was_useful,
            quality_improvement=quality_improvement
        )
        
        self.context_learner.record_usage(
            item_id=memory_id,
            outcome=outcome
        )
        
        # 更新记忆重要性
        if was_useful:
            memory.importance_score = min(
                1.0,
                memory.importance_score + 0.05
            )
        
        self._learning_memory_stats["forgetting_decisions"] += 1
    
    def get_memories_to_forget(self, max_count: int = 10) -> List[str]:
        """
        获取应该被遗忘的记忆（基于学习）
        """
        if not self.learning_enabled:
            return super().get_memories_to_forget(max_count)
        
        # 使用学习器判断
        should_compress, to_remove = self.context_learner.should_compress()
        
        if should_compress:
            return to_remove[:max_count]
        
        return []
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        import re
        
        chinese_words = re.findall(r'[\u4e00-\u9fa5]+', text)
        english_words = re.findall(r'[a-zA-Z]+', text)
        
        keywords = list(set(chinese_words + english_words))
        keywords = [k for k in keywords if len(k) >= 2]
        
        return keywords[:10]
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        stats = {
            "learning_enabled": self.learning_enabled,
            "learning_stats": self._learning_memory_stats,
            "context_learner_stats": self.context_learner.get_statistics()
        }
        
        return stats


def create_learning_memory_manager() -> LearningMemoryManager:
    """创建带学习能力的记忆管理器"""
    return LearningMemoryManager()
