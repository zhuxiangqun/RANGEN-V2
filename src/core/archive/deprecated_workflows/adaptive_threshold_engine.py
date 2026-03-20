#!/usr/bin/env python3
"""
Adaptive Threshold Engine - 自适应阈值引擎

核心思想：阈值不应该被硬编码，而应该基于数据和反馈动态计算。

与LearningManager集成：
- 使用LearningManager作为持久化后端
- 学习到的阈值自动保存到learning_data
- 启动时从持久化数据恢复阈值
"""
from typing import Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from abc import ABC, abstractmethod
import numpy as np
from collections import deque
import time
import logging

if TYPE_CHECKING:
    from src.core.reasoning.learning_manager import LearningManager


@dataclass
class PerformanceFeedback:
    """性能反馈数据"""
    query_type: str
    threshold: float
    was_successful: bool
    precision: float = 0.0
    recall: float = 0.0
    user_satisfaction: float = 0.0
    timestamp: float = 0.0


class ThresholdStrategy(ABC):
    """阈值计算策略基类"""
    
    @abstractmethod
    def compute(
        self, 
        base_value: float,
        context: Dict[str, Any],
        feedback_history: deque
    ) -> float:
        """基于上下文和反馈计算阈值"""
        pass
    
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass


class HistoricalStatisticsStrategy(ThresholdStrategy):
    """基于历史统计的策略"""
    
    def name(self) -> str:
        return "historical_statistics"
    
    def compute(
        self, 
        base_value: float,
        context: Dict[str, Any],
        feedback_history: deque
    ) -> float:
        if not feedback_history:
            return base_value
        
        successful = [f.threshold for f in feedback_history if f.was_successful]
        if successful:
            weights = np.exp(np.linspace(0, 1, len(successful)))
            weights /= weights.sum()
            return float(np.average(successful, weights=weights))
        
        return base_value


class ContextAwareStrategy(ThresholdStrategy):
    """基于上下文的策略"""
    
    CONTEXT_FACTORS = {
        'factual': 0.8,
        'comparison': 0.7,
        'procedural': 0.6,
        'causal': 0.65,
        'temporal': 0.75,
    }
    
    def name(self) -> str:
        return "context_aware"
    
    def compute(
        self, 
        base_value: float,
        context: Dict[str, Any],
        feedback_history: deque
    ) -> float:
        query_type = context.get('query_type', 'default')
        factor = self.CONTEXT_FACTORS.get(query_type, 1.0)
        return base_value * factor


class BanditStrategy(ThresholdStrategy):
    """多臂老虎机策略"""
    
    def __init__(self, epsilon: float = 0.1):
        self.epsilon = epsilon
        self.arm_stats: Dict[str, Dict] = {}
    
    def name(self) -> str:
        return "bandit"
    
    def compute(
        self, 
        base_value: float,
        context: Dict[str, Any],
        feedback_history: deque
    ) -> float:
        query_type = context.get('query_type', 'default')
        
        if query_type not in self.arm_stats:
            self.arm_stats[query_type] = {'count': 0, 'sum_reward': 0.0}
        
        stats = self.arm_stats[query_type]
        
        if np.random.random() < self.epsilon:
            return base_value * np.random.uniform(0.5, 1.0)
        
        if stats['count'] > 0:
            return stats['sum_reward'] / stats['count']
        
        return base_value
    
    def update(self, query_type: str, threshold: float, reward: float):
        if query_type not in self.arm_stats:
            self.arm_stats[query_type] = {'count': 0, 'sum_reward': 0.0}
        
        stats = self.arm_stats[query_type]
        stats['count'] += 1
        stats['sum_reward'] += reward


class ReinforcementLearningStrategy(ThresholdStrategy):
    """强化学习策略"""
    
    def __init__(self, learning_rate: float = 0.1, discount: float = 0.9):
        self.lr = learning_rate
        self.discount = discount
        self.value_table: Dict[str, float] = {}
    
    def name(self) -> str:
        return "reinforcement_learning"
    
    def compute(
        self, 
        base_value: float,
        context: Dict[str, Any],
        feedback_history: deque
    ) -> float:
        state = context.get('query_type', 'default')
        
        if feedback_history:
            recent_reward = sum(
                f.user_satisfaction for f in list(feedback_history)[-5:]
            ) / min(5, len(feedback_history))
            
            if state in self.value_table:
                td_error = recent_reward - self.value_table[state]
                self.value_table[state] += self.lr * td_error
            else:
                self.value_table[state] = recent_reward
        
        learned_value = self.value_table.get(state, base_value)
        return learned_value


class AdaptiveThresholdEngine:
    """自适应阈值引擎 - 统一入口，支持LearningManager集成"""
    
    def __init__(self, learning_manager: Optional['LearningManager'] = None):
        self.learning_manager = learning_manager
        self.strategies: Dict[str, ThresholdStrategy] = {}
        self.current_strategy: Optional[ThresholdStrategy] = None
        self.feedback_buffer: Dict[str, deque] = {}
        self.default_base_threshold = 0.5
        self.logger = logging.getLogger(__name__)
        
        # 如果有LearningManager，从持久化数据恢复
        if self.learning_manager:
            self._load_from_learning_manager()
        
        # 注册默认策略
        self.register_strategy(HistoricalStatisticsStrategy())
        self.register_strategy(ContextAwareStrategy())
        self.register_strategy(BanditStrategy(epsilon=0.1))
        self.register_strategy(ReinforcementLearningStrategy())
        
        # 默认使用上下文感知策略
        self.use_strategy("context_aware")
    
    def _load_from_learning_manager(self):
        """从LearningManager加载已学习的阈值"""
        if not self.learning_manager:
            return
            
        try:
            conf_thresholds = self.learning_manager.learning_data.get('confidence_thresholds', {})
            for query_type, data in conf_thresholds.items():
                if isinstance(data, dict) and 'feedback_history' in data:
                    for fb_data in data['feedback_history']:
                        try:
                            feedback = PerformanceFeedback(
                                query_type=fb_data['query_type'],
                                threshold=fb_data['threshold'],
                                was_successful=fb_data['was_successful'],
                                precision=fb_data.get('precision', 0.0),
                                recall=fb_data.get('recall', 0.0),
                                user_satisfaction=fb_data.get('user_satisfaction', 0.0),
                                timestamp=fb_data.get('timestamp', 0.0)
                            )
                            self.record_feedback(feedback, persist=False)
                        except Exception as e:
                            self.logger.debug(f"加载反馈数据失败: {e}")
            
            self.logger.info(f"从LearningManager加载了 {len(conf_thresholds)} 个查询类型的阈值数据")
        except Exception as e:
            self.logger.warning(f"加载LearningManager数据失败: {e}")
    
    def _persist_to_learning_manager(self, query_type: str, feedback: PerformanceFeedback):
        """持久化到LearningManager"""
        if not self.learning_manager:
            return
        
        try:
            if 'confidence_thresholds' not in self.learning_manager.learning_data:
                self.learning_manager.learning_data['confidence_thresholds'] = {}
            
            if query_type not in self.learning_manager.learning_data['confidence_thresholds']:
                self.learning_manager.learning_data['confidence_thresholds'][query_type] = {
                    'best_threshold': feedback.threshold,
                    'usage_count': 1,
                    'feedback_history': []
                }
            
            data = self.learning_manager.learning_data['confidence_thresholds'][query_type]
            
            # 使用指数移动平均更新最佳阈值
            if feedback.was_successful:
                old_threshold = data.get('best_threshold', feedback.threshold)
                data['best_threshold'] = old_threshold * 0.7 + feedback.threshold * 0.3
            
            data['usage_count'] = data.get('usage_count', 0) + 1
            
            if 'feedback_history' not in data:
                data['feedback_history'] = []
            
            fb_dict = {
                'query_type': feedback.query_type,
                'threshold': feedback.threshold,
                'was_successful': feedback.was_successful,
                'precision': feedback.precision,
                'recall': feedback.recall,
                'user_satisfaction': feedback.user_satisfaction,
                'timestamp': feedback.timestamp
            }
            data['feedback_history'].append(fb_dict)
            
            if len(data['feedback_history']) > 100:
                data['feedback_history'] = data['feedback_history'][-100:]
            
            # 触发LearningManager保存
            self.learning_manager._save_learning_data()
        except Exception as e:
            self.logger.warning(f"持久化到LearningManager失败: {e}")
    
    def register_strategy(self, strategy: ThresholdStrategy):
        """注册新策略"""
        self.strategies[strategy.name()] = strategy
    
    def use_strategy(self, name: str):
        """切换策略"""
        if name in self.strategies:
            self.current_strategy = self.strategies[name]
    
    def compute_threshold(
        self,
        context: Dict[str, Any],
        base_threshold: Optional[float] = None
    ) -> float:
        """计算阈值"""
        base = base_threshold or self.default_base_threshold
        query_type = context.get('query_type', 'default')
        
        # 优先从LearningManager获取已学习的阈值
        if self.learning_manager:
            learned = self.learning_manager.get_learned_confidence_threshold(query_type)
            if learned != 0.7:  # 非默认值，说明有学习数据
                return learned
        
        history = self.feedback_buffer.get(query_type, deque(maxlen=100))
        threshold = self.current_strategy.compute(base, context, history)
        
        return max(0.1, min(0.95, threshold))
    
    def record_feedback(self, feedback: PerformanceFeedback, persist: bool = True):
        """记录反馈，用于学习"""
        query_type = feedback.query_type
        
        if query_type not in self.feedback_buffer:
            self.feedback_buffer[query_type] = deque(maxlen=100)
        
        self.feedback_buffer[query_type].append(feedback)
        
        if isinstance(self.current_strategy, BanditStrategy):
            reward = 1.0 if feedback.was_successful else 0.0
            self.current_strategy.update(query_type, feedback.threshold, reward)
        
        if persist:
            self._persist_to_learning_manager(query_type, feedback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取学习统计"""
        stats = {}
        for query_type, history in self.feedback_buffer.items():
            if history:
                successful = [f.threshold for f in history if f.was_successful]
                stats[query_type] = {
                    'total_feedback': len(history),
                    'success_rate': len(successful) / len(history) if history else 0,
                    'avg_threshold': np.mean([f.threshold for f in history]),
                    'current_value': self.compute_threshold({'query_type': query_type})
                }
        return stats
    
    def save_state(self):
        """保存状态到LearningManager"""
        if self.learning_manager:
            self.learning_manager._save_learning_data()
    
    def load_state(self):
        """从LearningManager加载状态"""
        if self.learning_manager:
            self._load_from_learning_manager()


# 全局实例（保持向后兼容）
_threshold_engine = AdaptiveThresholdEngine()


def get_threshold_engine(learning_manager: Optional['LearningManager'] = None) -> AdaptiveThresholdEngine:
    """获取阈值引擎实例"""
    if learning_manager:
        return AdaptiveThresholdEngine(learning_manager)
    return _threshold_engine


def compute_threshold(
    query_type: str,
    base_threshold: Optional[float] = None,
    context: Optional[Dict[str, Any]] = None
) -> float:
    """便捷函数：计算阈值"""
    ctx = context or {}
    ctx['query_type'] = query_type
    return _threshold_engine.compute_threshold(ctx, base_threshold)


def record_threshold_feedback(
    query_type: str,
    threshold: float,
    was_successful: bool,
    precision: float = 0.0,
    recall: float = 0.0,
    satisfaction: float = 0.0
):
    """便捷函数：记录阈值反馈"""
    feedback = PerformanceFeedback(
        query_type=query_type,
        threshold=threshold,
        was_successful=was_successful,
        precision=precision,
        recall=recall,
        user_satisfaction=satisfaction,
        timestamp=time.time()
    )
    _threshold_engine.record_feedback(feedback)
