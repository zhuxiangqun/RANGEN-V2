#!/usr/bin/env python3
"""
执行策略学习器 (Execution Strategy Learner)
============================================

学习什么任务用什么执行策略效果最好

功能:
- 记录不同策略的执行结果
- 分析任务特征与最佳策略的关系
- 预测新任务应该使用什么策略
- 自动优化执行流程
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """策略类型"""
    DIRECT = "direct"                 # 直接执行
    CHAINED = "chained"             # 链式执行
    PARALLEL = "parallel"           # 并行执行
    ITERATIVE = "iterative"         # 迭代执行
    STEPPED = "stepped"             # 分步执行
    REFLECTIVE = "reflective"       # 反思执行
    PLANNED = "planned"             # 计划执行
    HYBRID = "hybrid"              # 混合策略


class StrategyOutcome:
    """策略执行结果"""
    
    def __init__(
        self,
        success: bool,
        quality_score: float = 0.0,
        execution_time: float = 0.0,
        iterations: int = 0,
        tool_calls: int = 0,
        errors: List[str] = None,
        metadata: Dict = None
    ):
        self.success = success
        self.quality_score = quality_score
        self.execution_time = execution_time
        self.iterations = iterations
        self.tool_calls = tool_calls
        self.errors = errors or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "quality_score": self.quality_score,
            "execution_time": self.execution_time,
            "iterations": self.iterations,
            "tool_calls": self.tool_calls,
            "errors": self.errors,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyOutcome':
        return cls(**data)


@dataclass
class TaskFeatures:
    """任务特征"""
    query: str
    query_length: int
    complexity: str                    # simple, moderate, complex
    task_type: str                    # 任务类型
    has_context: bool = False
    requires_multiple_steps: bool = False
    requires_citation: bool = False
    is_ambiguous: bool = False
    domain: str = "general"            # 领域
    
    @classmethod
    def from_query(cls, query: str, context: Dict = None) -> 'TaskFeatures':
        context = context or {}
        
        query_length = len(query)
        query_lower = query.lower()
        
        # 判断复杂度
        complexity = "moderate"
        if query_length < 30:
            complexity = "simple"
        elif query_length > 150:
            complexity = "complex"
        
        # 判断任务类型
        task_type = "unknown"
        if any(kw in query_lower for kw in ["查找", "搜索", "search"]):
            task_type = "retrieval"
        elif any(kw in query_lower for kw in ["分析", "compare"]):
            task_type = "analysis"
        elif any(kw in query_lower for kw in ["生成", "写", "create"]):
            task_type = "generation"
        elif any(kw in query_lower for kw in ["为什么", "reason"]):
            task_type = "reasoning"
        
        # 判断是否需要多步骤
        requires_multiple_steps = (
            "首先" in query or "然后" in query or
            "first" in query_lower and "then" in query_lower
        )
        
        return cls(
            query=query,
            query_length=query_length,
            complexity=complexity,
            task_type=task_type,
            has_context=bool(context),
            requires_multiple_steps=requires_multiple_steps,
            requires_citation=context.get("requires_citation", False),
            is_ambiguous=context.get("is_ambiguous", False),
            domain=context.get("domain", "general")
        )
    
    def to_feature_vector(self) -> List[float]:
        """转换为特征向量"""
        return [
            self.query_length / 200.0,
            1.0 if self.complexity == "simple" else 0.0,
            1.0 if self.complexity == "moderate" else 0.0,
            1.0 if self.complexity == "complex" else 0.0,
            1.0 if self.task_type == "retrieval" else 0.0,
            1.0 if self.task_type == "analysis" else 0.0,
            1.0 if self.task_type == "generation" else 0.0,
            1.0 if self.task_type == "reasoning" else 0.0,
            1.0 if self.has_context else 0.0,
            1.0 if self.requires_multiple_steps else 0.0,
            1.0 if self.requires_citation else 0.0,
            1.0 if self.is_ambiguous else 0.0,
        ]


class StrategyRecord:
    """策略执行记录"""
    
    def __init__(
        self,
        strategy: StrategyType,
        task_features: TaskFeatures,
        outcome: StrategyOutcome
    ):
        self.strategy = strategy
        self.task_features = task_features
        self.outcome = outcome
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "strategy": self.strategy.value,
            "task_features": {
                "query_length": self.task_features.query_length,
                "complexity": self.task_features.complexity,
                "task_type": self.task_features.task_type,
                "has_context": self.task_features.has_context,
                "requires_multiple_steps": self.task_features.requires_multiple_steps,
            },
            "outcome": self.outcome.to_dict(),
            "timestamp": self.timestamp.isoformat()
        }


class ExecutionStrategyLearner:
    """
    执行策略学习器
    
    从历史执行记录中学习，预测最佳执行策略
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # 学习参数
        self.learning_rate = self.config.get("learning_rate", 0.1)
        self.min_samples = self.config.get("min_samples", 10)
        self.decay_factor = self.config.get("decay_factor", 0.9)
        
        # 策略表现记录
        # {task_key: {strategy: [outcomes]}}
        self._strategy_records: Dict[str, Dict[str, List[StrategyOutcome]]] = defaultdict(
            lambda: defaultdict(list)
        )
        
        # 策略性能缓存
        self._strategy_performance: Dict[str, Dict[str, float]] = defaultdict(dict)
        
        # 锁
        self._lock = threading.RLock()
        
        # 统计
        self._total_records = 0
        self._total_predictions = 0
        self._correct_predictions = 0
        
        logger.info("ExecutionStrategyLearner initialized")
    
    def _get_task_key(self, task_features: TaskFeatures) -> str:
        """生成任务key"""
        return f"{task_features.complexity}_{task_features.task_type}"
    
    def record_execution(
        self,
        task_features: TaskFeatures,
        strategy: StrategyType,
        outcome: StrategyOutcome
    ):
        """记录策略执行结果"""
        with self._lock:
            task_key = self._get_task_key(task_features)
            
            record = StrategyRecord(strategy, task_features, outcome)
            
            self._strategy_records[task_key][strategy.value].append(outcome)
            self._total_records += 1
            
            # 更新性能缓存
            self._update_performance_cache(task_key, strategy)
            
            # 限制记录数量
            max_records = self.config.get("max_records_per_key", 500)
            if len(self._strategy_records[task_key][strategy.value]) > max_records:
                self._strategy_records[task_key][strategy.value] = \
                    self._strategy_records[task_key][strategy.value][-max_records:]
            
            logger.debug(f"Recorded strategy execution: {strategy.value} for {task_key}")
    
    def _update_performance_cache(self, task_key: str, strategy: StrategyType):
        """更新策略性能缓存"""
        outcomes = self._strategy_records[task_key].get(strategy.value, [])
        
        if not outcomes:
            return
        
        # 计算综合分数 (质量优先，兼顾效率)
        total_quality = sum(o.quality_score for o in outcomes)
        avg_quality = total_quality / len(outcomes)
        
        # 考虑执行时间 (越快越好)
        avg_time = sum(o.execution_time for o in outcomes) / len(outcomes)
        time_score = max(0, 1.0 - (avg_time / 60.0))  # 60秒为满分
        
        # 综合分数
        combined_score = 0.7 * avg_quality + 0.3 * time_score
        
        self._strategy_performance[task_key][strategy.value] = combined_score
    
    def predict_best_strategy(
        self,
        task_features: TaskFeatures
    ) -> Tuple[Optional[StrategyType], Dict[str, float]]:
        """
        预测最佳策略
        
        Args:
            task_features: 任务特征
            
        Returns:
            (最佳策略, 所有策略评分)
        """
        with self._lock:
            self._total_predictions += 1
            
            task_key = self._get_task_key(task_features)
            
            # 如果没有足够样本，返回默认策略
            if self._total_records < self.min_samples:
                return StrategyType.DIRECT, self._get_default_scores()
            
            # 获取各策略的预测分数
            scores = {}
            for strategy in StrategyType:
                score = self._strategy_performance.get(task_key, {}).get(
                    strategy.value, 0.5
                )
                if score == 0:
                    score = 0.5
                scores[strategy.value] = score
            
            # 选择最佳策略
            if not scores:
                return StrategyType.DIRECT, self._get_default_scores()
            
            best_strategy_str = max(scores.items(), key=lambda x: x[1])[0]
            best_strategy = StrategyType(best_strategy_str)
            
            # 检查置信度
            best_score = scores[best_strategy_str]
            if best_score < 0.4:
                # 置信度太低，使用默认策略
                return StrategyType.DIRECT, scores
            
            logger.debug(f"Predicted best strategy: {best_strategy} for {task_key}")
            
            return best_strategy, scores
    
    def _get_default_scores(self) -> Dict[str, float]:
        """获取默认分数"""
        return {s.value: 0.5 for s in StrategyType}
    
    def learn_from_feedback(
        self,
        task_features: TaskFeatures,
        predicted_strategy: StrategyType,
        actual_strategy: StrategyType,
        outcome: StrategyOutcome
    ):
        """从反馈中学习"""
        with self._lock:
            # 记录实际使用的策略
            self.record_execution(task_features, actual_strategy, outcome)
            
            # 更新预测准确率
            if predicted_strategy == actual_strategy:
                self._correct_predictions += 1
            
            logger.debug(
                f"Learned from feedback: predicted={predicted_strategy.value}, "
                f"actual={actual_strategy.value}"
            )
    
    def get_strategy_recommendations(
        self,
        task_features: TaskFeatures,
        top_k: int = 3
    ) -> List[Tuple[StrategyType, float]]:
        """获取策略推荐"""
        task_key = self._get_task_key(task_features)
        
        strategy_scores = self._strategy_performance.get(task_key, {})
        
        if not strategy_scores:
            return []
        
        # 排序返回top_k
        sorted_strategies = sorted(
            strategy_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            (StrategyType(s), score) for s, score in sorted_strategies[:top_k]
        ]
    
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
                "tasks_learned": len(self._strategy_records),
                "strategy_performance": dict(self._strategy_performance)
            }
    
    def get_best_strategy_for_complexity(
        self,
        complexity: str
    ) -> Dict[str, StrategyType]:
        """获取某复杂度的最佳策略"""
        with self._lock:
            result = {}
            
            for task_type in ["retrieval", "analysis", "generation", "reasoning", "unknown"]:
                task_key = f"{complexity}_{task_type}"
                scores = self._strategy_performance.get(task_key, {})
                
                if scores:
                    best = max(scores.items(), key=lambda x: x[1])
                    result[task_type] = StrategyType(best[0])
                else:
                    result[task_type] = StrategyType.DIRECT
            
            return result
    
    def export_knowledge(self, path: str):
        """导出学习到的知识"""
        with self._lock:
            data = {
                "strategy_performance": dict(self._strategy_performance),
                "statistics": self.get_statistics()
            }
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported strategy knowledge to {path}")
    
    def import_knowledge(self, path: str):
        """导入知识"""
        with self._lock:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self._strategy_performance = defaultdict(
                    dict, data.get("strategy_performance", {})
                )
                
                logger.info(f"Imported strategy knowledge from {path}")
            except Exception as e:
                logger.error(f"Failed to import knowledge: {e}")


# 全局实例
_execution_strategy_learner: Optional[ExecutionStrategyLearner] = None


def get_execution_strategy_learner(config: Optional[Dict] = None) -> ExecutionStrategyLearner:
    """获取执行策略学习器实例"""
    global _execution_strategy_learner
    if _execution_strategy_learner is None:
        _execution_strategy_learner = ExecutionStrategyLearner(config)
    return _execution_strategy_learner
