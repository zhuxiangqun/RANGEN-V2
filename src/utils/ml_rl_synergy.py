#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ML/RL协同模块
提供机器学习和强化学习的协同功能
"""

import os
import logging
import time
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod


@dataclass
class SynergyResult:
    """协同结果数据类"""
    success: bool
    ml_result: Any
    rl_result: Any
    synergy_score: float
    confidence: float
    timestamp: float
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class MLPrediction:
    """ML预测结果"""
    prediction: float
    confidence: float
    model_type: str
    features: List[float]
    timestamp: float


@dataclass
class RLAction:
    """RL动作结果"""
    action: int
    reward: float
    state: List[float]
    q_value: float
    timestamp: float


class SynergyStrategy(ABC):
    """协同策略基类"""
    
    @abstractmethod
    def calculate_synergy(self, ml_prediction: MLPrediction, rl_action: RLAction) -> SynergyResult:
        """计算协同效果"""
        pass


class BasicSynergyStrategy(SynergyStrategy):
    """基础协同策略"""
    
    def calculate_synergy(self, ml_prediction: MLPrediction, rl_action: RLAction) -> SynergyResult:
        """计算基础协同效果"""
        try:
            # 简单的协同计算
            synergy_score = (ml_prediction.confidence + rl_action.reward) / 2.0
            confidence = min(1.0, synergy_score)
            
            return SynergyResult(
                success=True,
                ml_result=ml_prediction.prediction,
                rl_result=rl_action.action,
                synergy_score=float(synergy_score),
                confidence=float(confidence),
                timestamp=time.time(),
                metadata={
                    "strategy": "basic",
                    "ml_confidence": ml_prediction.confidence,
                    "rl_reward": rl_action.reward
                }
            )
        except Exception as e:
            return SynergyResult(
                success=False,
                ml_result=None,
                rl_result=None,
                synergy_score=0.0,
                confidence=0.0,
                timestamp=time.time(),
                error=str(e)
            )


class AdvancedSynergyStrategy(SynergyStrategy):
    """高级协同策略"""
    
    def __init__(self):
        self.weights = {
            "ml_weight": 0.6,
            "rl_weight": 0.4,
            "interaction_weight": 0.2
        }
    
    def calculate_synergy(self, ml_prediction: MLPrediction, rl_action: RLAction) -> SynergyResult:
        """计算高级协同效果"""
        try:
            # 加权协同计算
            ml_score = ml_prediction.confidence * self.weights["ml_weight"]
            rl_score = rl_action.reward * self.weights["rl_weight"]
            
            # 交互效应
            interaction = self._calculate_interaction(ml_prediction, rl_action)
            interaction_score = interaction * self.weights["interaction_weight"]
            
            synergy_score = ml_score + rl_score + interaction_score
            confidence = min(1.0, synergy_score)
            
            return SynergyResult(
                success=True,
                ml_result=ml_prediction.prediction,
                rl_result=rl_action.action,
                synergy_score=float(synergy_score),
                confidence=float(confidence),
                timestamp=time.time(),
                metadata={
                    "strategy": "advanced",
                    "ml_score": ml_score,
                    "rl_score": rl_score,
                    "interaction_score": interaction_score,
                    "weights": self.weights
                }
            )
        except Exception as e:
            return SynergyResult(
                success=False,
                ml_result=None,
                rl_result=None,
                synergy_score=0.0,
                confidence=0.0,
                timestamp=time.time(),
                error=str(e)
            )
    
    def _calculate_interaction(self, ml_prediction: MLPrediction, rl_action: RLAction) -> float:
        """计算交互效应"""
        # 简单的交互效应计算
        ml_norm = (ml_prediction.prediction + 1) / 2  # 归一化到[0,1]
        rl_norm = (rl_action.action + 1) / 2  # 归一化到[0,1]
        return abs(ml_norm - rl_norm)  # 差异越小，交互效应越强


class MLRLSynergy:
    """ML/RL协同管理器"""
    
    def __init__(self, strategy: Optional[SynergyStrategy] = None):
        self.logger = logging.getLogger(__name__)
        self.strategy = strategy or BasicSynergyStrategy()
        self.synergy_history = []
        self.performance_metrics = {
            "total_synergies": 0,
            "successful_synergies": 0,
            "failed_synergies": 0,
            "average_synergy_score": 0.0,
            "average_confidence": 0.0
        }
    
    def process_synergy(self, ml_prediction: MLPrediction, rl_action: RLAction) -> SynergyResult:
        """处理协同"""
        try:
            self.logger.info("开始处理ML/RL协同")
            
            # 计算协同效果
            result = self.strategy.calculate_synergy(ml_prediction, rl_action)
            
            # 记录历史
            self.synergy_history.append(result)
            
            # 更新性能指标
            self._update_performance_metrics(result)
            
            self.logger.info(f"协同处理完成，得分: {result.synergy_score:.3f}")
            return result
            
        except Exception as e:
            self.logger.error(f"协同处理失败: {e}")
            error_result = SynergyResult(
                success=False,
                ml_result=None,
                rl_result=None,
                synergy_score=0.0,
                confidence=0.0,
                timestamp=time.time(),
                error=str(e)
            )
            self.synergy_history.append(error_result)
            return error_result
    
    def _update_performance_metrics(self, result: SynergyResult):
        """更新性能指标"""
        self.performance_metrics["total_synergies"] += 1
        
        if result.success:
            self.performance_metrics["successful_synergies"] += 1
        else:
            self.performance_metrics["failed_synergies"] += 1
        
        # 更新平均协同得分
        total = self.performance_metrics["total_synergies"]
        current_avg = self.performance_metrics["average_synergy_score"]
        self.performance_metrics["average_synergy_score"] = (
            (current_avg * (total - 1) + result.synergy_score) / total
        )
        
        # 更新平均置信度
        current_avg_conf = self.performance_metrics["average_confidence"]
        self.performance_metrics["average_confidence"] = (
            (current_avg_conf * (total - 1) + result.confidence) / total
        )
    
    def get_synergy_statistics(self) -> Dict[str, Any]:
        """获取协同统计信息"""
        return {
            "performance_metrics": self.performance_metrics.copy(),
            "history_count": len(self.synergy_history),
            "strategy_type": self.strategy.__class__.__name__,
            "last_synergy": self.synergy_history[-1] if self.synergy_history else None
        }
    
    def clear_history(self):
        """清空历史记录"""
        self.synergy_history.clear()
        self.logger.info("协同历史记录已清空")
    
    def set_strategy(self, strategy: SynergyStrategy):
        """设置协同策略"""
        self.strategy = strategy
        self.logger.info(f"协同策略已更新为: {strategy.__class__.__name__}")


class MLModel:
    """ML模型基类"""
    
    def __init__(self, model_type: str):
        self.model_type = model_type
        self.trained = False
        self.accuracy = 0.0
    
    def predict(self, features: List[float]) -> MLPrediction:
        """进行预测"""
        # 真实预测逻辑 - 基于特征权重和模型参数
        if not features:
            prediction = 0.0
            confidence = 0.0
        else:
            # 计算加权预测
            weights = self._get_feature_weights(len(features))
            weighted_sum = sum(f * w for f, w in zip(features, weights))
            prediction = self._apply_activation_function(weighted_sum)
            
            # 计算置信度
            confidence = self._calculate_prediction_confidence(features, prediction)
        
        return MLPrediction(
            prediction=float(prediction),
            confidence=float(confidence),
            model_type=self.model_type,
            features=features,
            timestamp=time.time()
        )
    
    def _get_feature_weights(self, feature_count: int) -> List[float]:
        """获取特征权重"""
        # 基于特征数量生成权重
        if feature_count <= 0:
            return []
        
        # 使用递减权重模式
        weights = []
        total_weight = 0.0
        for i in range(feature_count):
            weight = 1.0 / (i + 1)  # 递减权重
            weights.append(weight)
            total_weight += weight
        
        # 归一化权重
        if total_weight > 0:
            weights = [w / total_weight for w in weights]
        
        return weights
    
    def _apply_activation_function(self, weighted_sum: float) -> float:
        """应用激活函数"""
        # 使用sigmoid激活函数
        import math
        return 1.0 / (1.0 + math.exp(-weighted_sum))
    
    def _calculate_prediction_confidence(self, features: List[float], prediction: float) -> float:
        """计算预测置信度"""
        if not features:
            return 0.0
        
        # 基于特征方差计算置信度
        feature_variance = np.var(features) if len(features) > 1 else 0.0
        variance_confidence = 1.0 / (1.0 + feature_variance)
        
        # 基于预测值的合理性
        prediction_confidence = 1.0 - abs(prediction - 0.5) * 2  # 距离0.5越近置信度越高
        
        # 综合置信度
        return (variance_confidence + prediction_confidence) / 2.0


class RLAgent:
    """RL智能体基类"""
    
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.q_table = {}
        self.epsilon = 0.1
    
    def select_action(self, state: List[float]) -> RLAction:
        """选择动作"""
        # 真实动作选择逻辑 - 基于Q-learning
        if not state:
            action = 0
            reward = 0.0
            q_value = 0.0
        else:
            # 计算状态键
            state_key = self._get_state_key(state)
            
            # 获取Q值
            q_values = self._get_q_values(state_key)
            
            # 选择动作（epsilon-greedy策略）
            if np.random.random() < self.epsilon:
                # 探索：随机选择动作
                action = np.random.randint(0, 4)
            else:
                # 利用：选择Q值最高的动作
                action = np.argmax(q_values)
            
            # 计算奖励和Q值
            reward = self._calculate_reward(state, action)
            q_value = q_values[action]
        
        return RLAction(
            action=int(action),
            reward=float(reward),
            state=state,
            q_value=float(q_value),
            timestamp=time.time()
        )
    
    def _get_state_key(self, state: List[float]) -> str:
        """获取状态键"""
        # 将状态向量转换为字符串键
        if not state:
            return "empty"
        
        # 将状态值量化为离散值
        quantized_state = [int(s * 10) for s in state]
        return "_".join(map(str, quantized_state))
    
    def _get_q_values(self, state_key: str) -> List[float]:
        """获取Q值"""
        if state_key not in self.q_table:
            # 初始化Q值
            self.q_table[state_key] = [0.0] * 4  # 4个动作
        
        return self.q_table[state_key]
    
    def _calculate_reward(self, state: List[float], action: int) -> float:
        """计算奖励"""
        if not state:
            return 0.0
        
        # 基于状态和动作计算奖励
        state_value = sum(state) / len(state) if state else 0.0
        
        # 动作奖励映射
        action_rewards = {
            0: 0.1,   # 动作0的基础奖励
            1: 0.2,   # 动作1的基础奖励
            2: 0.3,   # 动作2的基础奖励
            3: 0.4    # 动作3的基础奖励
        }
        
        base_reward = action_rewards.get(action, 0.0)
        
        # 基于状态值调整奖励
        state_factor = 1.0 + state_value * 0.5
        
        return base_reward * state_factor


class SynergyOptimizer:
    """协同优化器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.optimization_history = []
    
    def optimize_weights(self, synergy: MLRLSynergy) -> Dict[str, float]:
        """优化协同权重"""
        try:
            # 基于历史数据优化权重
            if not synergy.synergy_history:
                return {"ml_weight": 0.5, "rl_weight": 0.5}
            
            # 计算最优权重
            ml_scores = [r.synergy_score for r in synergy.synergy_history if r.success]
            rl_scores = [r.confidence for r in synergy.synergy_history if r.success]
            
            if not ml_scores or not rl_scores:
                return {"ml_weight": 0.5, "rl_weight": 0.5}
            
            # 简单的权重优化
            ml_performance = np.mean(ml_scores)
            rl_performance = np.mean(rl_scores)
            
            total_performance = ml_performance + rl_performance
            if total_performance > 0:
                ml_weight = ml_performance / total_performance
                rl_weight = rl_performance / total_performance
            else:
                ml_weight = rl_weight = 0.5
            
            optimized_weights = {
                "ml_weight": float(ml_weight),
                "rl_weight": float(rl_weight)
            }
            
            self.optimization_history.append({
                "weights": optimized_weights,
                "timestamp": time.time()
            })
            
            return optimized_weights
            
        except Exception as e:
            self.logger.error(f"权重优化失败: {e}")
            return {"ml_weight": 0.5, "rl_weight": 0.5}


# 便捷函数
def create_ml_prediction(prediction: float, confidence: float, model_type: str = "default") -> MLPrediction:
    """创建ML预测结果"""
    return MLPrediction(
        prediction=float(prediction),
        confidence=float(confidence),
        model_type=model_type,
        features=[],
        timestamp=time.time()
    )


def create_rl_action(action: int, reward: float, state: List[float]) -> RLAction:
    """创建RL动作结果"""
    return RLAction(
        action=int(action),
        reward=float(reward),
        state=state,
        q_value=0.0,
        timestamp=time.time()
    )


def get_synergy_manager(strategy_type: str = "basic") -> MLRLSynergy:
    """获取协同管理器"""
    if strategy_type == "advanced":
        strategy = AdvancedSynergyStrategy()
    else:
        strategy = BasicSynergyStrategy()
    
    return MLRLSynergy(strategy)


# ML/RL协同模块 - 核心AI协同组件
# 提供机器学习和强化学习的协同处理功能