#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML/RL协同协调器
实现真正的机器学习和强化学习协同机制，解决协同能力不足问题
"""

import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import threading
from collections import deque


class SynergyMode(Enum):
    """协同模式"""
    SEQUENTIAL = "sequential"      # 顺序协同：ML -> RL
    PARALLEL = "parallel"          # 并行协同：ML || RL
    ITERATIVE = "iterative"        # 迭代协同：ML <-> RL
    ADAPTIVE = "adaptive"          # 自适应协同：动态选择模式


@dataclass
class MLPrediction:
    """ML预测结果"""
    prediction: Any
    confidence: float
    features: Dict[str, Any]
    model_type: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class RLAction:
    """RL动作结果"""
    action: Any
    reward: float
    state: Dict[str, Any]
    policy_type: str
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SynergyResult:
    """协同结果"""
    success: bool
    ml_prediction: MLPrediction
    rl_action: RLAction
    synergy_score: float
    confidence: float
    mode: SynergyMode
    iterations: int
    processing_time: float
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MLRLSynergyCoordinator:
    """ML/RL协同协调器 - 实现真正的协同机制"""
    
    def __init__(self, 
                 ml_engine: Any = None,
                 rl_engine: Any = None,
                 synergy_mode: SynergyMode = SynergyMode.ADAPTIVE,
                 max_iterations: int = 5,
                 convergence_threshold: float = 0.01):
        self.logger = logging.getLogger(__name__)
        self.ml_engine = ml_engine
        self.rl_engine = rl_engine
        self.synergy_mode = synergy_mode
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        
        # 协同历史和学习
        self.synergy_history: deque = deque(maxlen=1000)
        self.performance_metrics = {
            'total_synergies': 0,
            'successful_synergies': 0,
            'failed_synergies': 0,
            'average_synergy_score': 0.0,
            'average_confidence': 0.0,
            'mode_performance': {}
        }
        
        # 自适应学习
        self.adaptive_weights = {
            'ml_weight': 0.6,
            'rl_weight': 0.4,
            'interaction_weight': 0.2
        }
        
        self._lock = threading.Lock()
    
    def coordinate(self, 
                   query: str,
                   context: Optional[Dict[str, Any]] = None,
                   mode: Optional[SynergyMode] = None) -> SynergyResult:
        """协调ML和RL进行协同处理"""
        start_time = time.time()
        mode = mode or self.synergy_mode
        
        try:
            self.logger.info(f"开始ML/RL协同处理，模式: {mode.value}")
            
            # 根据模式选择协同策略
            if mode == SynergyMode.SEQUENTIAL:
                result = self._sequential_synergy(query, context)
            elif mode == SynergyMode.PARALLEL:
                result = self._parallel_synergy(query, context)
            elif mode == SynergyMode.ITERATIVE:
                result = self._iterative_synergy(query, context)
            elif mode == SynergyMode.ADAPTIVE:
                result = self._adaptive_synergy(query, context)
            else:
                raise ValueError(f"未知的协同模式: {mode}")
            
            # 更新性能指标
            self._update_performance_metrics(result)
            
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            self.logger.info(f"协同处理完成，得分: {result.synergy_score:.3f}, 耗时: {processing_time:.3f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"协同处理失败: {e}")
            return self._create_error_result(query, str(e), start_time)
    
    def _sequential_synergy(self, query: str, context: Optional[Dict[str, Any]]) -> SynergyResult:
        """顺序协同：ML -> RL"""
        # 1. ML预测
        ml_prediction = self._get_ml_prediction(query, context)
        
        # 2. 基于ML结果进行RL决策
        rl_action = self._get_rl_action(query, context, ml_prediction)
        
        # 3. 计算协同分数
        synergy_score = self._calculate_synergy_score(ml_prediction, rl_action)
        
        return SynergyResult(
            success=True,
            ml_prediction=ml_prediction,
            rl_action=rl_action,
            synergy_score=synergy_score,
            confidence=min(ml_prediction.confidence, rl_action.reward),
            mode=SynergyMode.SEQUENTIAL,
            iterations=1,
            processing_time=0.0,
            timestamp=time.time()
        )
    
    def _parallel_synergy(self, query: str, context: Optional[Dict[str, Any]]) -> SynergyResult:
        """并行协同：ML || RL"""
        import concurrent.futures
        
        # 并行执行ML和RL
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            ml_future = executor.submit(self._get_ml_prediction, query, context)
            rl_future = executor.submit(self._get_rl_action, query, context, None)
            
            ml_prediction = ml_future.result()
            rl_action = rl_future.result()
        
        # 融合结果
        synergy_score = self._calculate_synergy_score(ml_prediction, rl_action)
        
        return SynergyResult(
            success=True,
            ml_prediction=ml_prediction,
            rl_action=rl_action,
            synergy_score=synergy_score,
            confidence=(ml_prediction.confidence + rl_action.reward) / 2,
            mode=SynergyMode.PARALLEL,
            iterations=1,
            processing_time=0.0,
            timestamp=time.time()
        )
    
    def _iterative_synergy(self, query: str, context: Optional[Dict[str, Any]]) -> SynergyResult:
        """迭代协同：ML <-> RL"""
        best_result = None
        best_score = 0.0
        
        for iteration in range(self.max_iterations):
            # ML预测
            ml_prediction = self._get_ml_prediction(query, context)
            
            # RL决策（基于ML结果）
            rl_action = self._get_rl_action(query, context, ml_prediction)
            
            # 计算协同分数
            synergy_score = self._calculate_synergy_score(ml_prediction, rl_action)
            
            # 更新最佳结果
            if synergy_score > best_score:
                best_score = synergy_score
                best_result = SynergyResult(
                    success=True,
                    ml_prediction=ml_prediction,
                    rl_action=rl_action,
                    synergy_score=synergy_score,
                    confidence=min(ml_prediction.confidence, rl_action.reward),
                    mode=SynergyMode.ITERATIVE,
                    iterations=iteration + 1,
                    processing_time=0.0,
                    timestamp=time.time()
                )
            
            # 检查收敛
            if iteration > 0 and abs(synergy_score - best_score) < self.convergence_threshold:
                break
            
            # 更新上下文用于下一次迭代
            context = self._update_context_for_iteration(context, ml_prediction, rl_action)
        
        return best_result
    
    def _adaptive_synergy(self, query: str, context: Optional[Dict[str, Any]]) -> SynergyResult:
        """自适应协同：动态选择最佳模式"""
        # 分析查询特征
        query_features = self._analyze_query_features(query, context)
        
        # 选择最佳协同模式
        best_mode = self._select_best_mode(query_features)
        
        # 执行协同
        if best_mode == SynergyMode.SEQUENTIAL:
            return self._sequential_synergy(query, context)
        elif best_mode == SynergyMode.PARALLEL:
            return self._parallel_synergy(query, context)
        elif best_mode == SynergyMode.ITERATIVE:
            return self._iterative_synergy(query, context)
        else:
            return self._sequential_synergy(query, context)
    
    def _get_ml_prediction(self, query: str, context: Optional[Dict[str, Any]]) -> MLPrediction:
        """获取ML预测结果"""
        if self.ml_engine:
            try:
                prediction = self.ml_engine.predict(query, context)
                return MLPrediction(
                    prediction=prediction.get('result'),
                    confidence=prediction.get('confidence', 0.5),
                    features=prediction.get('features', {}),
                    model_type=prediction.get('model_type', 'unknown'),
                    timestamp=time.time(),
                    metadata=prediction.get('metadata')
                )
            except Exception as e:
                self.logger.warning(f"ML预测失败: {e}")
        
        # 默认预测
        return MLPrediction(
            prediction="default_ml_prediction",
            confidence=0.3,
            features={'query_length': len(query)},
            model_type='default',
            timestamp=time.time()
        )
    
    def _get_rl_action(self, query: str, context: Optional[Dict[str, Any]], ml_prediction: Optional[MLPrediction]) -> RLAction:
        """获取RL动作结果"""
        if self.rl_engine:
            try:
                # 构建RL状态
                rl_state = self._build_rl_state(query, context, ml_prediction)
                
                action = self.rl_engine.decide(rl_state)
                return RLAction(
                    action=action.get('action'),
                    reward=action.get('reward', 0.0),
                    state=rl_state,
                    policy_type=action.get('policy_type', 'unknown'),
                    timestamp=time.time(),
                    metadata=action.get('metadata')
                )
            except Exception as e:
                self.logger.warning(f"RL决策失败: {e}")
        
        # 默认动作
        return RLAction(
            action="default_rl_action",
            reward=0.3,
            state={'query': query},
            policy_type='default',
            timestamp=time.time()
        )
    
    def _build_rl_state(self, query: str, context: Optional[Dict[str, Any]], ml_prediction: Optional[MLPrediction]) -> Dict[str, Any]:
        """构建RL状态"""
        state = {
            'query': query,
            'context': context or {},
            'timestamp': time.time()
        }
        
        if ml_prediction:
            state['ml_prediction'] = ml_prediction.prediction
            state['ml_confidence'] = ml_prediction.confidence
            state['ml_features'] = ml_prediction.features
        
        return state
    
    def _calculate_synergy_score(self, ml_prediction: MLPrediction, rl_action: RLAction) -> float:
        """计算协同分数"""
        # 基础分数
        ml_score = ml_prediction.confidence * self.adaptive_weights['ml_weight']
        rl_score = rl_action.reward * self.adaptive_weights['rl_weight']
        
        # 交互效应
        interaction_score = self._calculate_interaction_effect(ml_prediction, rl_action)
        interaction_score *= self.adaptive_weights['interaction_weight']
        
        # 协同分数
        synergy_score = ml_score + rl_score + interaction_score
        
        # 归一化到[0, 1]
        return min(1.0, max(0.0, synergy_score))
    
    def _calculate_interaction_effect(self, ml_prediction: MLPrediction, rl_action: RLAction) -> float:
        """计算交互效应"""
        # 基于预测和动作的一致性
        if isinstance(ml_prediction.prediction, (int, float)) and isinstance(rl_action.action, (int, float)):
            # 数值一致性
            diff = abs(ml_prediction.prediction - rl_action.action)
            consistency = 1.0 / (1.0 + diff)
        else:
            # 字符串或其他类型的一致性
            ml_str = str(ml_prediction.prediction)
            rl_str = str(rl_action.action)
            consistency = 1.0 if ml_str == rl_str else 0.5
        
        # 置信度加权
        confidence_weight = (ml_prediction.confidence + rl_action.reward) / 2
        
        return consistency * confidence_weight
    
    def _analyze_query_features(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """分析查询特征"""
        features = {
            'query_length': len(query),
            'complexity': self._estimate_complexity(query),
            'urgency': context.get('urgency', 'normal') if context else 'normal',
            'domain': context.get('domain', 'general') if context else 'general'
        }
        
        return features
    
    def _estimate_complexity(self, query: str) -> str:
        """估计查询复杂度"""
        if len(query) < 20:
            return 'simple'
        elif len(query) < 100:
            return 'medium'
        else:
            return 'complex'
    
    def _select_best_mode(self, query_features: Dict[str, Any]) -> SynergyMode:
        """选择最佳协同模式"""
        # 基于历史性能选择模式
        if not self.performance_metrics['mode_performance']:
            return SynergyMode.SEQUENTIAL
        
        # 根据查询特征选择
        if query_features['complexity'] == 'simple':
            return SynergyMode.SEQUENTIAL
        elif query_features['complexity'] == 'medium':
            return SynergyMode.PARALLEL
        else:
            return SynergyMode.ITERATIVE
    
    def _update_context_for_iteration(self, context: Optional[Dict[str, Any]], 
                                    ml_prediction: MLPrediction, 
                                    rl_action: RLAction) -> Dict[str, Any]:
        """为下一次迭代更新上下文"""
        if context is None:
            context = {}
        
        context['ml_prediction'] = ml_prediction.prediction
        context['rl_action'] = rl_action.action
        context['iteration_count'] = context.get('iteration_count', 0) + 1
        
        return context
    
    def _update_performance_metrics(self, result: SynergyResult):
        """更新性能指标"""
        with self._lock:
            self.performance_metrics['total_synergies'] += 1
            
            if result.success:
                self.performance_metrics['successful_synergies'] += 1
                
                # 更新平均分数
                total = self.performance_metrics['total_synergies']
                current_avg = self.performance_metrics['average_synergy_score']
                self.performance_metrics['average_synergy_score'] = (
                    (current_avg * (total - 1) + result.synergy_score) / total
                )
                
                current_avg_conf = self.performance_metrics['average_confidence']
                self.performance_metrics['average_confidence'] = (
                    (current_avg_conf * (total - 1) + result.confidence) / total
                )
                
                # 更新模式性能
                mode = result.mode.value
                if mode not in self.performance_metrics['mode_performance']:
                    self.performance_metrics['mode_performance'][mode] = {
                        'count': 0,
                        'total_score': 0.0,
                        'average_score': 0.0
                    }
                
                mode_perf = self.performance_metrics['mode_performance'][mode]
                mode_perf['count'] += 1
                mode_perf['total_score'] += result.synergy_score
                mode_perf['average_score'] = mode_perf['total_score'] / mode_perf['count']
            else:
                self.performance_metrics['failed_synergies'] += 1
            
            # 记录历史
            self.synergy_history.append(result)
    
    def _create_error_result(self, query: str, error: str, start_time: float) -> SynergyResult:
        """创建错误结果"""
        return SynergyResult(
            success=False,
            ml_prediction=MLPrediction("", 0.0, {}, "error", time.time()),
            rl_action=RLAction("", 0.0, {}, "error", time.time()),
            synergy_score=0.0,
            confidence=0.0,
            mode=SynergyMode.SEQUENTIAL,
            iterations=0,
            processing_time=time.time() - start_time,
            timestamp=time.time(),
            error=error
        )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            return self.performance_metrics.copy()
    
    def optimize_weights(self):
        """优化自适应权重"""
        # 基于历史性能调整权重
        if len(self.synergy_history) < 10:
            return
        
        recent_results = list(self.synergy_history)[-50:]  # 最近50个结果
        
        # 分析不同权重的性能
        # 这里可以实现更复杂的优化算法
        successful_results = [r for r in recent_results if r.success]
        
        if successful_results:
            avg_score = sum(r.synergy_score for r in successful_results) / len(successful_results)
            
            # 如果性能较好，保持当前权重
            if avg_score > 0.7:
                return
            
            # 否则调整权重
            self.adaptive_weights['ml_weight'] = min(0.8, self.adaptive_weights['ml_weight'] + 0.05)
            self.adaptive_weights['rl_weight'] = min(0.6, self.adaptive_weights['rl_weight'] + 0.05)
            self.adaptive_weights['interaction_weight'] = min(0.4, self.adaptive_weights['interaction_weight'] + 0.02)
    
    def reset_metrics(self):
        """重置性能指标"""
        with self._lock:
            self.performance_metrics = {
                'total_synergies': 0,
                'successful_synergies': 0,
                'failed_synergies': 0,
                'average_synergy_score': 0.0,
                'average_confidence': 0.0,
                'mode_performance': {}
            }
            self.synergy_history.clear()


# 示例使用
if __name__ == "__main__":
    # 创建协同协调器
    coordinator = MLRLSynergyCoordinator()
    
    # 测试协同处理
    result = coordinator.coordinate("测试查询", {"urgency": "high"})
    
    print(f"协同结果: {result.synergy_score:.3f}")
    print(f"性能指标: {coordinator.get_performance_metrics()}")
