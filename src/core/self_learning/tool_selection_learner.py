#!/usr/bin/env python3
"""
工具选择学习器 (Tool Selection Learner)
========================================

学习什么场景用什么工具效果最好

功能:
- 记录工具使用与成功率的映射
- 分析任务特征与最佳工具的关系
- 预测新任务应该使用什么工具
- 自动优化工具选择策略
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"       # 简单任务
    MODERATE = "moderate"   # 中等任务
    COMPLEX = "complex"     # 复杂任务


class TaskCategory(Enum):
    """任务类别"""
    RETRIEVAL = "retrieval"         # 检索
    ANALYSIS = "analysis"           # 分析
    GENERATION = "generation"       # 生成
    REASONING = "reasoning"         # 推理
    EXECUTION = "execution"         # 执行
    QUESTION_ANSWER = "qa"          # 问答
    CONVERSATION = "conversation"   # 对话
    UNKNOWN = "unknown"              # 未知


@dataclass
class TaskContext:
    """任务上下文"""
    query: str
    task_category: TaskCategory = TaskCategory.UNKNOWN
    complexity: TaskComplexity = TaskComplexity.MODERATE
    
    # 额外特征
    has_context: bool = False
    requires_citation: bool = False
    is_urgent: bool = False
    
    # 历史特征
    is_repeated: bool = False
    related_queries_count: int = 0
    
    def to_feature_vector(self) -> List[float]:
        """转换为特征向量"""
        features = [
            # 任务类别 (one-hot)
            1.0 if self.task_category == TaskCategory.RETRIEVAL else 0.0,
            1.0 if self.task_category == TaskCategory.ANALYSIS else 0.0,
            1.0 if self.task_category == TaskCategory.GENERATION else 0.0,
            1.0 if self.task_category == TaskCategory.REASONING else 0.0,
            1.0 if self.task_category == TaskCategory.EXECUTION else 0.0,
            1.0 if self.task_category == TaskCategory.QUESTION_ANSWER else 0.0,
            1.0 if self.task_category == TaskCategory.CONVERSATION else 0.0,
            
            # 复杂度
            1.0 if self.complexity == TaskComplexity.SIMPLE else 0.0,
            1.0 if self.complexity == TaskComplexity.MODERATE else 0.0,
            1.0 if self.complexity == TaskComplexity.COMPLEX else 0.0,
            
            # 额外特征
            1.0 if self.has_context else 0.0,
            1.0 if self.requires_citation else 0.0,
            1.0 if self.is_urgent else 0.0,
            1.0 if self.is_repeated else 0.0,
            
            # 数值特征
            min(self.related_queries_count / 10.0, 1.0),
        ]
        return features
    
    @classmethod
    def from_query(cls, query: str, context: Dict = None) -> 'TaskContext':
        """从查询创建任务上下文"""
        query_lower = query.lower()
        context = context or {}
        
        # 推断任务类别
        task_category = TaskCategory.UNKNOWN
        
        if any(kw in query_lower for kw in ["搜索", "查找", "检索", "search", "find", "lookup"]):
            task_category = TaskCategory.RETRIEVAL
        elif any(kw in query_lower for kw in ["分析", "比较", "评估", "analyze", "compare", "evaluate"]):
            task_category = TaskCategory.ANALYSIS
        elif any(kw in query_lower for kw in ["生成", "写", "创建", "生成", "generate", "write", "create"]):
            task_category = TaskCategory.GENERATION
        elif any(kw in query_lower for kw in ["推理", "原因", "为什么", "reason", "why"]):
            task_category = TaskCategory.REASONING
        elif any(kw in query_lower for kw in ["执行", "运行", "做", "execute", "run", "do"]):
            task_category = TaskCategory.EXECUTION
        elif any(kw in query_lower for kw in ["什么", "怎么", "如何", "who", "what", "how"]):
            task_category = TaskCategory.QUESTION_ANSWER
        elif any(kw in query_lower for kw in ["你好", "帮助", "hello", "help"]):
            task_category = TaskCategory.CONVERSATION
        
        # 推断复杂度
        complexity = TaskComplexity.MODERATE
        if len(query) < 20:
            complexity = TaskComplexity.SIMPLE
        elif len(query) > 100:
            complexity = TaskComplexity.COMPLEX
        
        return cls(
            query=query,
            task_category=task_category,
            complexity=complexity,
            has_context=bool(context),
            requires_citation=context.get("requires_citation", False),
            is_urgent=context.get("priority") == "high",
            is_repeated=context.get("is_repeated", False),
            related_queries_count=context.get("related_queries_count", 0)
        )


@dataclass
class ToolUsageRecord:
    """工具使用记录"""
    tool_name: str
    task_context: TaskContext
    success: bool
    quality_score: float          # 0-1 质量评分
    execution_time: float         # 执行时间(秒)
    timestamp: datetime = field(default_factory=datetime.now)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "tool_name": self.tool_name,
            "task_category": self.task_context.task_category.value,
            "complexity": self.task_context.complexity.value,
            "success": self.success,
            "quality_score": self.quality_score,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
            "error": self.error
        }


class ToolSelectionLearner:
    """
    工具选择学习器
    
    从历史工具使用记录中学习，预测最佳工具选择
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 学习参数
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.min_samples = self.config.get("min_samples", 5)  # 最少样本数才开始预测
        self.decay_factor = self.config.get("decay_factor", 0.95)  # 历史衰减
        
        # 工具成功率记录
        # {(task_category, complexity, tool_name): [records]}
        self._tool_success_records: Dict[Tuple, List[ToolUsageRecord]] = defaultdict(list)
        
        # 工具性能统计
        # {(task_category, complexity): {tool_name: avg_quality}}
        self._tool_performance: Dict[Tuple, Dict[str, float]] = defaultdict(dict)
        
        # 锁
        self._lock = threading.RLock()
        
        # 统计数据
        self._total_records = 0
        self._total_predictions = 0
        self._correct_predictions = 0
        
        logger.info("ToolSelectionLearner initialized")
    
    def record_usage(
        self,
        tool_name: str,
        task_context: TaskContext,
        success: bool,
        quality_score: float = 0.5,
        execution_time: float = 0.0,
        error: Optional[str] = None
    ):
        """记录工具使用"""
        with self._lock:
            key = (task_context.task_category, task_context.complexity)
            tool_key = (key[0], key[1], tool_name)
            
            record = ToolUsageRecord(
                tool_name=tool_name,
                task_context=task_context,
                success=success,
                quality_score=quality_score,
                execution_time=execution_time,
                error=error
            )
            
            self._tool_success_records[tool_key].append(record)
            self._total_records += 1
            
            # 更新性能统计
            self._update_performance(key, tool_name)
            
            # 限制记录数量
            max_records = self.config.get("max_records_per_key", 1000)
            if len(self._tool_success_records[tool_key]) > max_records:
                self._tool_success_records[tool_key] = \
                    self._tool_success_records[tool_key][-max_records:]
            
            logger.debug(f"Recorded tool usage: {tool_name} for {key}, success={success}")
    
    def _update_performance(self, task_key, tool_name: str):
        """更新工具性能统计"""
        tool_key = (task_key[0], task_key[1], tool_name)
        records = self._tool_success_records.get(tool_key, [])
        
        if not records:
            return
        
        # 计算加权平均质量分数 (近期权重更高)
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for i, record in enumerate(records):
            weight = self.decay_factor ** (len(records) - i - 1)
            weighted_sum += record.quality_score * weight
            weight_sum += weight
        
        avg_quality = weighted_sum / weight_sum if weight_sum > 0 else 0.0
        self._tool_performance[task_key][tool_name] = avg_quality
    
    def predict_best_tool(
        self,
        task_context: TaskContext,
        available_tools: List[str]
    ) -> Tuple[Optional[str], Dict[str, float]]:
        """
        预测最佳工具
        
        Args:
            task_context: 任务上下文
            available_tools: 可用工具列表
            
        Returns:
            (最佳工具, 所有工具评分)
        """
        with self._lock:
            self._total_predictions += 1
            
            key = (task_context.task_category, task_context.complexity)
            
            # 如果没有足够样本，返回默认或None
            if self._total_records < self.min_samples:
                return None, {tool: 0.5 for tool in available_tools}
            
            # 获取各工具的预测分数
            scores = {}
            for tool in available_tools:
                score = self._tool_performance.get(key, {}).get(tool, 0.5)
                
                # 如果没有数据，给一个中间值
                if score == 0:
                    score = 0.5
                
                scores[tool] = score
            
            # 选择最佳工具
            if not scores:
                return None, {}
            
            best_tool = max(scores.items(), key=lambda x: x[1])[0]
            
            logger.debug(f"Predicted best tool: {best_tool} for {key}, scores={scores}")
            
            return best_tool, scores
    
    def learn_from_feedback(
        self,
        task_context: TaskContext,
        predicted_tool: str,
        actual_tool: str,
        success: bool,
        quality_score: float
    ):
        """从反馈中学习"""
        with self._lock:
            # 记录实际使用的工具
            self.record_usage(
                tool_name=actual_tool,
                task_context=task_context,
                success=success,
                quality_score=quality_score
            )
            
            # 更新预测准确率
            if predicted_tool == actual_tool:
                self._correct_predictions += 1
            
            logger.debug(f"Learned from feedback: predicted={predicted_tool}, actual={actual_tool}")
    
    def get_tool_recommendations(
        self,
        task_context: TaskContext,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """获取工具推荐"""
        key = (task_context.task_category, task_context.complexity)
        
        tool_scores = self._tool_performance.get(key, {})
        
        if not tool_scores:
            return []
        
        # 排序返回top_k
        sorted_tools = sorted(
            tool_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_tools[:top_k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        with self._lock:
            return {
                "total_records": self._total_records,
                "total_predictions": self._total_predictions,
                "prediction_accuracy": (
                    self._correct_predictions / self._total_predictions
                    if self._total_predictions > 0 else 0
                ),
                "task_categories_learned": len(self._tool_performance),
                "tool_performance": {
                    f"{k[0].value}_{k[1].value}": v
                    for k, v in self._tool_performance.items()
                }
            }
    
    def export_knowledge(self, path: str):
        """导出学习到的知识"""
        with self._lock:
            data = {
                "tool_performance": {
                    f"{k[0].value}_{k[1].value}": v
                    for k, v in self._tool_performance.items()
                },
                "statistics": self.get_statistics()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported tool selection knowledge to {path}")
    
    def import_knowledge(self, path: str):
        """导入知识"""
        with self._lock:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 恢复性能数据
                for key_str, tools in data.get("tool_performance", {}).items():
                    parts = key_str.rsplit('_', 1)
                    if len(parts) == 2:
                        category = TaskCategory(parts[0])
                        complexity = TaskComplexity(parts[1])
                        key = (category, complexity)
                        self._tool_performance[key] = tools
                
                logger.info(f"Imported tool selection knowledge from {path}")
            except Exception as e:
                logger.error(f"Failed to import knowledge: {e}")


# 全局实例
_tool_selection_learner: Optional[ToolSelectionLearner] = None


def get_tool_selection_learner(config: Optional[Dict] = None) -> ToolSelectionLearner:
    """获取工具选择学习器实例"""
    global _tool_selection_learner
    if _tool_selection_learner is None:
        _tool_selection_learner = ToolSelectionLearner(config)
    return _tool_selection_learner
