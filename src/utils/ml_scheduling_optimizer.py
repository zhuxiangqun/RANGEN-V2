#!/usr/bin/env python3
"""
ML驱动的调度优化器
基于历史数据选择最优调度策略
"""

import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class SchedulingStrategy:
    """调度策略"""
    knowledge_timeout: float
    reasoning_timeout: float
    answer_timeout: float
    citation_timeout: float
    parallel_knowledge_reasoning: bool  # 是否并行执行知识检索和推理
    skip_answer_generation: bool  # 是否跳过答案生成（如果推理结果足够好）


@dataclass
class SchedulingPerformance:
    """调度性能指标"""
    query_type: str
    query_complexity: str
    strategy: SchedulingStrategy
    total_time: float
    knowledge_time: float
    reasoning_time: float
    answer_time: float
    success: bool
    accuracy: float
    timestamp: float


class MLSchedulingOptimizer:
    """ML驱动的调度优化器"""
    
    def __init__(
        self,
        data_path: str = "data/learning/ml_scheduling.json"
    ):
        """
        初始化ML调度优化器
        
        Args:
            data_path: 学习数据存储路径
        """
        self.logger = logger
        self.data_path = Path(data_path)
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 性能历史记录
        self.performance_history: List[SchedulingPerformance] = []
        
        # ML学习数据：查询特征 -> 最优调度策略
        self.ml_learning_data: Dict[str, Dict[str, Any]] = {}
        
        # 统计信息
        self.stats = {
            'total_queries': 0,
            'ml_predictions': 0,
            'avg_improvement': 0.0
        }
        
        # 加载历史数据
        self._load_history()
    
    def _load_history(self):
        """加载历史学习数据"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'performance_history' in data:
                        # 加载性能历史（最近1000条）
                        history = data['performance_history'][-1000:]
                        self.performance_history = [
                            SchedulingPerformance(**item) for item in history
                        ]
                    
                    if 'ml_learning_data' in data:
                        self.ml_learning_data = data['ml_learning_data']
                    
                    if 'stats' in data:
                        self.stats.update(data['stats'])
                    
                    self.logger.info(f"✅ 加载ML调度优化历史数据: 性能记录={len(self.performance_history)}, ML数据={len(self.ml_learning_data)}")
        except Exception as e:
            self.logger.warning(f"加载ML调度优化历史数据失败: {e}")
    
    def _save_history(self):
        """保存历史学习数据"""
        try:
            # 只保存最近1000条性能记录
            recent_history = self.performance_history[-1000:]
            
            data = {
                'performance_history': [asdict(perf) for perf in recent_history],
                'ml_learning_data': self.ml_learning_data,
                'stats': self.stats
            }
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"保存ML调度优化历史数据失败: {e}")
    
    def get_optimal_strategy(
        self,
        query: str,
        query_type: Optional[str] = None,
        query_complexity: Optional[str] = None
    ) -> SchedulingStrategy:
        """
        🚀 获取最优调度策略（基于ML）
        
        Args:
            query: 查询文本
            query_type: 查询类型（factual, multi_hop, comparative等）
            query_complexity: 查询复杂度（simple, medium, complex, very_complex）
            
        Returns:
            SchedulingStrategy: 最优调度策略
        """
        try:
            # 1. 提取特征
            features = self._extract_features(query, query_type, query_complexity)
            
            # 2. ML预测：根据历史数据预测最优调度策略
            predicted_strategy = self._ml_predict_strategy(features)
            
            self.stats['total_queries'] += 1
            self.stats['ml_predictions'] += 1
            
            return predicted_strategy
            
        except Exception as e:
            self.logger.warning(f"获取最优调度策略失败: {e}，使用默认策略")
            return self._get_default_strategy()
    
    def _extract_features(
        self,
        query: str,
        query_type: Optional[str],
        query_complexity: Optional[str]
    ) -> Dict[str, Any]:
        """提取特征用于ML"""
        # 如果没有提供，尝试推断
        if not query_type:
            query_type = self._infer_query_type(query)
        
        if not query_complexity:
            query_complexity = self._infer_complexity(query)
        
        # 🚀 ML/RL优化：添加更多特征用于ML预测
        query_lower = query.lower()
        
        # 提取更多特征
        features = {
            'query_type': query_type,
            'query_complexity': query_complexity,
            'query_length': len(query),
            # 新增特征
            'word_count': len(query.split()),
            'has_numbers': any(char.isdigit() for char in query),
            'has_question_words': any(word in query_lower for word in ['who', 'what', 'when', 'where', 'why', 'how', 'which']),
            'has_comparison_words': any(word in query_lower for word in ['compare', 'difference', 'vs', 'versus', 'better', 'best']),
            'has_temporal_words': any(word in query_lower for word in ['when', 'time', 'date', 'year', 'month', 'day', 'before', 'after']),
            'has_relationship_words': any(word in query_lower for word in ['mother', 'father', 'parent', 'child', 'sibling', 'same as', 'named after']),
            'has_causal_words': any(word in query_lower for word in ['why', 'because', 'cause', 'reason', 'due to', 'result']),
            'has_numerical_words': any(word in query_lower for word in ['how many', 'how much', 'number', 'count', 'total', 'sum']),
            'question_mark_count': query.count('?'),
            'and_count': query_lower.count(' and '),
            'or_count': query_lower.count(' or '),
            'apostrophe_count': query.count("'"),
            'capital_letter_ratio': sum(1 for c in query if c.isupper()) / max(len(query), 1),
            'punctuation_count': sum(1 for c in query if c in '.,!?;:')
        }
        
        return features
    
    def _infer_query_type(self, query: str) -> str:
        """推断查询类型"""
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['same as', 'mother', 'father', 'named after']):
            return 'multi_hop'
        elif any(keyword in query_lower for keyword in ['compare', 'difference', 'vs']):
            return 'comparative'
        elif any(keyword in query_lower for keyword in ['why', 'because', 'cause']):
            return 'causal'
        elif any(keyword in query_lower for keyword in ['how many', 'how much', 'number']):
            return 'numerical'
        elif any(keyword in query_lower for keyword in ['who', 'what', 'when', 'where']):
            return 'factual'
        return 'general'
    
    def _infer_complexity(self, query: str) -> str:
        """推断查询复杂度"""
        query_length = len(query)
        
        if query_length < 50:
            return 'simple'
        elif query_length > 150 or query.count(' and ') > 1:
            return 'complex'
        elif query.count("'s ") > 2:
            return 'very_complex'
        return 'medium'
    
    def _ml_predict_strategy(self, features: Dict[str, Any]) -> SchedulingStrategy:
        """
        🚀 ML预测：根据历史数据预测最优调度策略
        """
        try:
            # 构建特征键
            feature_key = self._features_to_key(features)
            
            # 查找历史数据中的最优策略
            if feature_key in self.ml_learning_data:
                learned_strategy = self.ml_learning_data[feature_key]
                return SchedulingStrategy(
                    knowledge_timeout=learned_strategy.get('optimal_knowledge_timeout', 12.0),
                    reasoning_timeout=learned_strategy.get('optimal_reasoning_timeout', 200.0),
                    answer_timeout=learned_strategy.get('optimal_answer_timeout', 10.0),
                    citation_timeout=learned_strategy.get('optimal_citation_timeout', 10.0),
                    parallel_knowledge_reasoning=learned_strategy.get('optimal_parallel', False),
                    skip_answer_generation=learned_strategy.get('optimal_skip_answer', False)
                )
            
            # 如果没有历史数据，使用基于规则的预测
            return self._rule_based_predict(features)
            
        except Exception as e:
            self.logger.warning(f"ML预测失败: {e}，使用基于规则的预测")
            return self._rule_based_predict(features)
    
    def _rule_based_predict(self, features: Dict[str, Any]) -> SchedulingStrategy:
        """
        基于规则的预测（当ML数据不足时使用）
        """
        query_type = features.get('query_type', 'general')
        query_complexity = features.get('query_complexity', 'medium')
        
        # 根据查询类型和复杂度调整超时时间
        knowledge_timeout = 12.0
        reasoning_timeout = 200.0
        answer_timeout = 10.0
        citation_timeout = 10.0
        parallel_knowledge_reasoning = False  # 默认不并行（推理需要知识支持）
        skip_answer_generation = False
        
        # 复杂查询：增加超时时间
        if query_complexity in ['complex', 'very_complex']:
            knowledge_timeout = 15.0
            reasoning_timeout = 250.0
        
        # 简单查询：减少超时时间
        if query_complexity == 'simple':
            knowledge_timeout = 10.0
            reasoning_timeout = 150.0
        
        # 多跳查询：不并行，需要更多时间
        if query_type == 'multi_hop':
            parallel_knowledge_reasoning = False
            knowledge_timeout = 15.0
            reasoning_timeout = 250.0
        
        return SchedulingStrategy(
            knowledge_timeout=knowledge_timeout,
            reasoning_timeout=reasoning_timeout,
            answer_timeout=answer_timeout,
            citation_timeout=citation_timeout,
            parallel_knowledge_reasoning=parallel_knowledge_reasoning,
            skip_answer_generation=skip_answer_generation
        )
    
    def _features_to_key(self, features: Dict[str, Any]) -> str:
        """将特征转换为键"""
        return f"{features.get('query_type', 'general')}_{features.get('query_complexity', 'medium')}"
    
    def _get_default_strategy(self) -> SchedulingStrategy:
        """获取默认策略"""
        return SchedulingStrategy(
            knowledge_timeout=12.0,
            reasoning_timeout=200.0,
            answer_timeout=10.0,
            citation_timeout=10.0,
            parallel_knowledge_reasoning=False,
            skip_answer_generation=False
        )
    
    def record_performance(
        self,
        query_type: str,
        query_complexity: str,
        strategy: SchedulingStrategy,
        total_time: float,
        knowledge_time: float,
        reasoning_time: float,
        answer_time: float,
        success: bool,
        accuracy: float
    ):
        """
        🚀 记录性能数据，用于ML学习
        
        Args:
            query_type: 查询类型
            query_complexity: 查询复杂度
            strategy: 使用的调度策略
            total_time: 总处理时间
            knowledge_time: 知识检索时间
            reasoning_time: 推理时间
            answer_time: 答案生成时间
            success: 是否成功
            accuracy: 答案准确率
        """
        try:
            performance = SchedulingPerformance(
                query_type=query_type,
                query_complexity=query_complexity,
                strategy=strategy,
                total_time=total_time,
                knowledge_time=knowledge_time,
                reasoning_time=reasoning_time,
                answer_time=answer_time,
                success=success,
                accuracy=accuracy,
                timestamp=time.time()
            )
            
            self.performance_history.append(performance)
            
            # 更新ML学习数据
            self._update_ml_learning_data(performance)
            
            # 定期保存
            if len(self.performance_history) % 10 == 0:
                self._save_history()
            
        except Exception as e:
            self.logger.warning(f"记录性能数据失败: {e}")
    
    def _update_ml_learning_data(self, performance: SchedulingPerformance):
        """更新ML学习数据"""
        try:
            feature_key = f"{performance.query_type}_{performance.query_complexity}"
            
            if feature_key not in self.ml_learning_data:
                self.ml_learning_data[feature_key] = {
                    'strategies': [],
                    'performances': [],
                    'optimal_knowledge_timeout': performance.strategy.knowledge_timeout,
                    'optimal_reasoning_timeout': performance.strategy.reasoning_timeout,
                    'optimal_answer_timeout': performance.strategy.answer_timeout,
                    'optimal_citation_timeout': performance.strategy.citation_timeout,
                    'optimal_parallel': performance.strategy.parallel_knowledge_reasoning,
                    'optimal_skip_answer': performance.strategy.skip_answer_generation,
                    'best_total_time': performance.total_time,
                    'best_accuracy': performance.accuracy
                }
            
            data = self.ml_learning_data[feature_key]
            data['strategies'].append(asdict(performance.strategy))
            data['performances'].append({
                'total_time': performance.total_time,
                'accuracy': performance.accuracy,
                'success': performance.success
            })
            
            # 只保留最近100条记录
            if len(data['strategies']) > 100:
                data['strategies'] = data['strategies'][-100:]
                data['performances'] = data['performances'][-100:]
            
            # 更新最优策略（基于总时间和准确率的加权平均）
            if len(data['performances']) >= 5:
                # 计算加权分数：准确率 * 0.7 + (1 - 总时间/600) * 0.3
                best_score = -1
                best_idx = 0
                for i, perf in enumerate(data['performances']):
                    score = perf['accuracy'] * 0.7 + (1 - min(perf['total_time'] / 600.0, 1.0)) * 0.3
                    if score > best_score:
                        best_score = score
                        best_idx = i
                
                best_strategy = data['strategies'][best_idx]
                data['optimal_knowledge_timeout'] = best_strategy['knowledge_timeout']
                data['optimal_reasoning_timeout'] = best_strategy['reasoning_timeout']
                data['optimal_answer_timeout'] = best_strategy['answer_timeout']
                data['optimal_citation_timeout'] = best_strategy['citation_timeout']
                data['optimal_parallel'] = best_strategy['parallel_knowledge_reasoning']
                data['optimal_skip_answer'] = best_strategy['skip_answer_generation']
                data['best_total_time'] = data['performances'][best_idx]['total_time']
                data['best_accuracy'] = data['performances'][best_idx]['accuracy']
            
        except Exception as e:
            self.logger.debug(f"更新ML学习数据失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'performance_history_count': len(self.performance_history),
            'ml_learning_patterns': len(self.ml_learning_data)
        }


# 单例模式
_ml_scheduling_optimizer_instance = None

def get_ml_scheduling_optimizer() -> MLSchedulingOptimizer:
    """获取ML调度优化器单例"""
    global _ml_scheduling_optimizer_instance
    if _ml_scheduling_optimizer_instance is None:
        _ml_scheduling_optimizer_instance = MLSchedulingOptimizer()
    return _ml_scheduling_optimizer_instance

