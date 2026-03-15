#!/usr/bin/env python3
"""
上下文管理学习器 (Context Management Learner)
============================================

学习什么信息值得记住，什么信息该忘记

功能:
- 分析上下文信息的重要性
- 学习信息的时间衰减模式
- 预测信息何时被需要
- 自动优化上下文压缩策略
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import threading
import math

logger = logging.getLogger(__name__)


class InfoType(Enum):
    """信息类型"""
    USER_PREFERENCE = "user_preference"   # 用户偏好
    TASK_CONTEXT = "task_context"         # 任务上下文
    PREVIOUS_QUERY = "previous_query"     # 历史查询
    TOOL_RESULT = "tool_result"          # 工具结果
    FACT = "fact"                        # 事实信息
    RELATIONSHIP = "relationship"         # 关系信息
    CONVERSATION = "conversation"        # 对话历史
    OTHER = "other"                      # 其他


class ImportancePattern(Enum):
    """重要性模式"""
    ALWAYS_IMPORTANT = "always_important"     # 总是重要
    TIME_DECAY = "time_decay"                 # 时间衰减
    ACCESS_FREQUENCY = "access_frequency"      # 访问频率
    RECENCY = "recency"                       # 最近优先
    CONTEXT_DEPENDENT = "context_dependent"   # 上下文依赖


@dataclass
class ContextItem:
    """上下文项"""
    item_id: str
    content: str
    info_type: InfoType
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    
    # 特征
    length: int = 0
    keywords: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    
    # 评分
    base_importance: float = 0.5  # 基础重要性
    
    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.content)
    
    def calculate_current_importance(
        self,
        current_time: datetime,
        decay_rate: float = 0.1
    ) -> float:
        """计算当前重要性"""
        # 时间衰减
        age_hours = (current_time - self.created_at).total_seconds() / 3600
        time_factor = math.exp(-decay_rate * age_hours)
        
        # 访问频率因子
        access_factor = min(1.0, math.log2(self.access_count + 1) / 5.0)
        
        # 综合重要性
        importance = (
            self.base_importance * 0.4 +
            time_factor * 0.3 +
            access_factor * 0.3
        )
        
        return importance
    
    def to_dict(self) -> Dict:
        return {
            "item_id": self.item_id,
            "content": self.content[:100] + "...",
            "info_type": self.info_type.value,
            "created_at": self.created_at.isoformat(),
            "access_count": self.access_count,
            "base_importance": self.base_importance,
            "length": self.length
        }


@dataclass
class UsageOutcome:
    """使用结果"""
    item_used: bool
    useful: bool           # 是否有用
    quality_improvement: float  # 质量提升 0-1
    context_match: float = 0.0   # 上下文匹配度


class ContextManagementLearner:
    """
    上下文管理学习器
    
    学习如何高效管理上下文信息
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 学习参数
        self.default_decay_rate = self.config.get("decay_rate", 0.1)
        self.importance_threshold = self.config.get("importance_threshold", 0.3)
        self.max_context_items = self.config.get("max_context_items", 50)
        
        # 信息类型的重要性学习
        # {info_type: {importance_pattern: score}}
        self._type_importance: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # 关键词重要性
        # {keyword: importance_score}
        self._keyword_importance: Dict[str, float] = defaultdict(float)
        
        # 上下文项记录
        # {item_id: ContextItem}
        self._context_items: Dict[str, ContextItem] = {}
        
        # 使用记录
        # {info_type: [UsageOutcome]}
        self._usage_records: Dict[str, List[UsageOutcome]] = defaultdict(list)
        
        # 每种类型的最佳衰减率
        # {info_type: decay_rate}
        self._optimal_decay_rates: Dict[str, float] = {}
        
        # 锁
        self._lock = threading.RLock()
        
        # 统计
        self._total_items = 0
        self._useful_items = 0
        self._compression_saved = 0
        
        # 初始化默认衰减率
        for info_type in InfoType:
            self._optimal_decay_rates[info_type.value] = self.default_decay_rate
        
        logger.info("ContextManagementLearner initialized")
    
    def _classify_info_type(self, content: str, metadata: Dict = None) -> InfoType:
        """分类信息类型"""
        content_lower = content.lower()
        metadata = metadata or {}
        
        # 基于关键词和元数据判断
        if metadata.get("info_type"):
            try:
                return InfoType(metadata["info_type"])
            except ValueError:
                pass
        
        if any(kw in content_lower for kw in ["喜欢", "偏好", "prefer", "always"]):
            return InfoType.USER_PREFERENCE
        elif any(kw in content_lower for kw in ["任务", "目标", "task", "goal"]):
            return InfoType.TASK_CONTEXT
        elif any(kw in content_lower for kw in ["之前", "上次", "previous", "before"]):
            return InfoType.PREVIOUS_QUERY
        elif any(kw in content_lower for kw in ["结果", "返回", "result", "found"]):
            return InfoType.TOOL_RESULT
        elif any(kw in content_lower for kw in ["事实", "是", "等于", "fact"]):
            return InfoType.FACT
        elif any(kw in content_lower for kw in ["关系", "与", "和", "relationship"]):
            return InfoType.RELATIONSHIP
        elif any(kw in content_lower for kw in ["说", "问", "道", "said", "asked"]):
            return InfoType.CONVERSATION
        
        return InfoType.OTHER
    
    def add_context_item(
        self,
        item_id: str,
        content: str,
        base_importance: float = 0.5,
        keywords: List[str] = None,
        metadata: Dict = None
    ):
        """添加上下文项"""
        with self._lock:
            info_type = self._classify_info_type(content, metadata)
            
            item = ContextItem(
                item_id=item_id,
                content=content,
                info_type=info_type,
                base_importance=base_importance,
                keywords=keywords or [],
                metadata=metadata or {}
            )
            
            self._context_items[item_id] = item
            self._total_items += 1
            
            # 限制上下文项数量
            if len(self._context_items) > self.max_context_items * 2:
                self._prune_low_importance()
            
            logger.debug(f"Added context item: {item_id}, type={info_type.value}")
    
    def record_usage(
        self,
        item_id: str,
        outcome: UsageOutcome
    ):
        """记录上下文项使用结果"""
        with self._lock:
            if item_id not in self._context_items:
                return
            
            item = self._context_items[item_id]
            
            # 更新访问信息
            item.last_accessed = datetime.now()
            item.access_count += 1
            
            # 记录使用结果
            info_type = item.info_type.value
            self._usage_records[info_type].append(outcome)
            
            # 限制记录数量
            if len(self._usage_records[info_type]) > 200:
                self._usage_records[info_type] = self._usage_records[info_type][-200:]
            
            # 如果有用，更新重要性
            if outcome.useful:
                self._useful_items += 1
                
                # 更新基础重要性
                item.base_importance = min(
                    1.0,
                    item.base_importance + 0.1
                )
                
                # 更新关键词重要性
                for keyword in item.keywords:
                    self._keyword_importance[keyword] = min(
                        1.0,
                        self._keyword_importance[keyword] + 0.05
                    )
                
                # 学习最佳衰减率
                self._learn_decay_rate(info_type, outcome)
            
            logger.debug(f"Recorded usage for {item_id}: useful={outcome.useful}")
    
    def _learn_decay_rate(self, info_type: str, outcome: UsageOutcome):
        """学习最佳衰减率"""
        records = self._usage_records.get(info_type, [])
        
        if len(records) < 5:
            return
        
        # 简单学习：如果质量提升大，降低衰减率
        # 如果质量提升小，增加衰减率
        if outcome.quality_improvement > 0.5:
            self._optimal_decay_rates[info_type] = max(
                0.01,
                self._optimal_decay_rates.get(info_type, 0.1) * 0.9
            )
        else:
            self._optimal_decay_rates[info_type] = min(
                0.5,
                self._optimal_decay_rates.get(info_type, 0.1) * 1.1
            )
    
    def get_important_context(
        self,
        current_time: datetime = None,
        max_items: int = None,
        context_keywords: List[str] = None
    ) -> List[ContextItem]:
        """获取重要的上下文项"""
        with self._lock:
            current_time = current_time or datetime.now()
            max_items = max_items or self.max_context_items
            
            # 计算每项的当前重要性
            scored_items = []
            
            for item_id, item in self._context_items.items():
                # 获取该类型的衰减率
                decay_rate = self._optimal_decay_rates.get(
                    item.info_type.value,
                    self.default_decay_rate
                )
                
                # 计算当前重要性
                importance = item.calculate_current_importance(
                    current_time,
                    decay_rate
                )
                
                # 上下文关键词匹配加分
                if context_keywords:
                    keyword_match = sum(
                        1 for kw in context_keywords
                        if kw in item.content.lower()
                    ) / len(context_keywords)
                    importance += keyword_match * 0.2
                
                scored_items.append((item_id, importance, item))
            
            # 按重要性排序
            scored_items.sort(key=lambda x: x[1], reverse=True)
            
            # 返回top_k
            return [item for _, _, item in scored_items[:max_items]]
    
    def should_compress(self) -> Tuple[bool, List[str]]:
        """判断是否需要压缩上下文"""
        with self._lock:
            if len(self._context_items) < self.max_context_items:
                return False, []
            
            current_time = datetime.now()
            important_items = self.get_important_context(current_time, self.max_context_items)
            
            # 需要删除的项
            to_remove = []
            for item_id, item in self._context_items.items():
                if item not in important_items:
                    to_remove.append(item_id)
            
            return True, to_remove
    
    def _prune_low_importance(self):
        """修剪低重要性项"""
        current_time = datetime.now()
        
        # 获取重要项
        important = self.get_important_context(current_time, self.max_context_items)
        important_ids = {item.item_id for item in important}
        
        # 删除不重要的
        to_delete = [
            item_id for item_id in self._context_items
            if item_id not in important_ids
        ]
        
        for item_id in to_delete:
            del self._context_items[item_id]
        
        self._compression_saved += len(to_delete)
        
        logger.debug(f"Pruned {len(to_delete)} low importance items")
    
    def predict_importance(
        self,
        content: str,
        metadata: Dict = None
    ) -> float:
        """预测信息的重要性"""
        with self._lock:
            info_type = self._classify_info_type(content, metadata)
            
            # 基础分数
            base_score = self._type_importance.get(
                info_type.value, {}
            ).get("base", 0.5)
            
            # 关键词加分
            keyword_boost = 0.0
            content_lower = content.lower()
            for keyword, importance in self._keyword_importance.items():
                if keyword in content_lower:
                    keyword_boost += importance * 0.1
            
            # 长度因子 (太长或太短都可能不重要)
            length = len(content)
            length_factor = 1.0
            if length < 10:
                length_factor = 0.5
            elif length > 500:
                length_factor = 0.8
            
            importance = min(1.0, (base_score + keyword_boost) * length_factor)
            
            return importance
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        with self._lock:
            return {
                "total_items": self._total_items,
                "current_items": len(self._context_items),
                "useful_items": self._useful_items,
                "usage_rate": (
                    self._useful_items / self._total_items
                    if self._total_items > 0 else 0
                ),
                "compression_saved": self._compression_saved,
                "optimal_decay_rates": self._optimal_decay_rates,
                "top_keywords": dict(
                    sorted(
                        self._keyword_importance.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:20]
                )
            }
    
    def export_knowledge(self, path: str):
        """导出学习到的知识"""
        with self._lock:
            data = {
                "type_importance": dict(self._type_importance),
                "keyword_importance": dict(self._keyword_importance),
                "optimal_decay_rates": self._optimal_decay_rates,
                "statistics": self.get_statistics()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported context management knowledge to {path}")
    
    def import_knowledge(self, path: str):
        """导入知识"""
        with self._lock:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._type_importance = defaultdict(
                    dict, data.get("type_importance", {})
                )
                self._keyword_importance = defaultdict(
                    float, data.get("keyword_importance", {})
                )
                self._optimal_decay_rates = data.get(
                    "optimal_decay_rates",
                    {}
                )
                
                logger.info(f"Imported context management knowledge from {path}")
            except Exception as e:
                logger.error(f"Failed to import knowledge: {e}")


# 全局实例
_context_management_learner: Optional[ContextManagementLearner] = None


def get_context_management_learner(config: Optional[Dict] = None) -> ContextManagementLearner:
    """获取上下文管理学习器实例"""
    global _context_management_learner
    if _context_management_learner is None:
        _context_management_learner = ContextManagementLearner(config)
    return _context_management_learner
