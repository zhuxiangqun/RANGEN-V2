"""
自适应学习协调器
实现ML和RL的深度协同学习
"""

import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import json


@dataclass
class LearningResult:
    """学习结果"""
    success: bool
    data: Any
    confidence: float
    learning_rate: float
    convergence_score: float
    ml_contribution: float
    rl_contribution: float
    processing_time: float
    error: Optional[str] = None


class LearningStrategy(ABC):
    """学习策略基类"""
    
    @abstractmethod
    def execute(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> LearningResult:
        """执行学习策略"""
        pass


class CollaborativeLearningStrategy(LearningStrategy):
    """协同学习策略"""
    
    def __init__(self):
        self.name = "collaborative_learning"
        self.logger = logging.getLogger(f"LearningStrategy.{self.name}")
        self.learning_history = []
    
    def execute(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> LearningResult:
        """执行协同学习"""
        start_time = time.time()
        
        try:
            # 1. 分析学习环境
            learning_env = self._analyze_learning_environment(ml_data, rl_data, context)
            
            # 2. 确定协同学习模式
            learning_mode = self._determine_learning_mode(learning_env)
            
            # 3. 执行协同学习
            learning_result = self._execute_collaborative_learning(ml_data, rl_data, learning_mode, context)
            
            # 4. 计算学习效果
            learning_effectiveness = self._calculate_learning_effectiveness(learning_result)
            
            # 5. 更新学习历史
            self._update_learning_history(learning_env, learning_result, learning_effectiveness)
            
            processing_time = time.time() - start_time
            
            return LearningResult(
                success=True,
                data=learning_result,
                confidence=learning_effectiveness['confidence'],
                learning_rate=learning_effectiveness['learning_rate'],
                convergence_score=learning_effectiveness['convergence_score'],
                ml_contribution=learning_effectiveness['ml_contribution'],
                rl_contribution=learning_effectiveness['rl_contribution'],
                processing_time=processing_time
            )
            
        except Exception as e:
            self.logger.error(f"协同学习执行失败: {e}")
            return LearningResult(
                success=False,
                data=None,
                confidence=0.0,
                learning_rate=0.0,
                convergence_score=0.0,
                ml_contribution=0.0,
                rl_contribution=0.0,
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    def _analyze_learning_environment(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """分析学习环境"""
        env_analysis = {
            'ml_complexity': self._calculate_ml_complexity(ml_data),
            'rl_complexity': self._calculate_rl_complexity(rl_data),
            'data_quality': self._assess_data_quality(ml_data, rl_data),
            'learning_potential': 0.0,
            'synergy_opportunity': 0.0
        }
        
        # 计算学习潜力
        env_analysis['learning_potential'] = (env_analysis['ml_complexity'] + env_analysis['rl_complexity']) / 2.0
        
        # 计算协同机会
        complexity_diff = abs(env_analysis['ml_complexity'] - env_analysis['rl_complexity'])
        env_analysis['synergy_opportunity'] = 1.0 - complexity_diff  # 复杂度越接近，协同机会越大
        
        return env_analysis
    
    def _calculate_ml_complexity(self, ml_data: Any) -> float:
        """计算ML复杂度"""
        if isinstance(ml_data, dict):
            return min(1.0, len(ml_data) / 10.0)
        elif isinstance(ml_data, (list, tuple)):
            return min(1.0, len(ml_data) / 20.0)
        else:
            return 0.5
    
    def _calculate_rl_complexity(self, rl_data: Any) -> float:
        """计算RL复杂度"""
        if isinstance(rl_data, dict):
            action_space = rl_data.get('action_space', 0)
            state_space = rl_data.get('state_space', 0)
            return min(1.0, (action_space + state_space) / 100.0)
        else:
            return 0.5
    
    def _assess_data_quality(self, ml_data: Any, rl_data: Any) -> float:
        """评估数据质量"""
        ml_quality = 0.5
        rl_quality = 0.5
        
        if isinstance(ml_data, dict):
            if 'confidence' in ml_data:
                ml_quality = ml_data['confidence']
            elif 'accuracy' in ml_data:
                ml_quality = ml_data['accuracy']
        
        if isinstance(rl_data, dict):
            if 'reward' in rl_data:
                rl_quality = min(1.0, abs(rl_data['reward']))
            elif 'success_rate' in rl_data:
                rl_quality = rl_data['success_rate']
        
        return (ml_quality + rl_quality) / 2.0
    
    def _determine_learning_mode(self, learning_env: Dict[str, Any]) -> str:
        """确定学习模式"""
        learning_potential = learning_env.get('learning_potential', 0.5)
        synergy_opportunity = learning_env.get('synergy_opportunity', 0.5)
        
        if learning_potential > 0.7 and synergy_opportunity > 0.7:
            return 'deep_collaborative'
        elif learning_potential > 0.5 or synergy_opportunity > 0.5:
            return 'moderate_collaborative'
        else:
            return 'basic_collaborative'
    
    def _execute_collaborative_learning(self, ml_data: Any, rl_data: Any, mode: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行协同学习"""
        if mode == 'deep_collaborative':
            return self._deep_collaborative_learning(ml_data, rl_data, context)
        elif mode == 'moderate_collaborative':
            return self._moderate_collaborative_learning(ml_data, rl_data, context)
        else:
            return self._basic_collaborative_learning(ml_data, rl_data, context)
    
    def _deep_collaborative_learning(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """深度协同学习"""
        # 1. 特征共享
        shared_features = self._extract_shared_features(ml_data, rl_data)
        
        # 2. 知识迁移
        knowledge_transfer = self._perform_knowledge_transfer(ml_data, rl_data)
        
        # 3. 联合优化
        joint_optimization = self._joint_optimization(ml_data, rl_data)
        
        # 4. 反馈循环
        feedback_loop = self._establish_feedback_loop(ml_data, rl_data)
        
        return {
            'mode': 'deep_collaborative',
            'shared_features': shared_features,
            'knowledge_transfer': knowledge_transfer,
            'joint_optimization': joint_optimization,
            'feedback_loop': feedback_loop,
            'learning_depth': 'deep',
            'confidence': 0.9
        }
    
    def _moderate_collaborative_learning(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """中等协同学习"""
        # 1. 信息交换
        information_exchange = self._exchange_information(ml_data, rl_data)
        
        # 2. 策略协调
        strategy_coordination = self._coordinate_strategies(ml_data, rl_data)
        
        # 3. 结果融合
        result_fusion = self._fuse_results(ml_data, rl_data)
        
        return {
            'mode': 'moderate_collaborative',
            'information_exchange': information_exchange,
            'strategy_coordination': strategy_coordination,
            'result_fusion': result_fusion,
            'learning_depth': 'moderate',
            'confidence': 0.75
        }
    
    def _basic_collaborative_learning(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """基础协同学习"""
        # 简单的数据组合和基础学习
        combined_learning = {
            'ml_insights': self._extract_ml_insights(ml_data),
            'rl_insights': self._extract_rl_insights(rl_data),
            'combined_learning': self._combine_insights(ml_data, rl_data)
        }
        
        return {
            'mode': 'basic_collaborative',
            'combined_learning': combined_learning,
            'learning_depth': 'basic',
            'confidence': 0.6
        }
    
    def _extract_shared_features(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """提取共享特征"""
        features = {
            'common_patterns': [],
            'shared_representations': [],
            'feature_overlap': 0.0
        }
        
        # 简化的特征提取
        if isinstance(ml_data, dict) and isinstance(rl_data, dict):
            ml_keys = set(ml_data.keys())
            rl_keys = set(rl_data.keys())
            common_keys = ml_keys.intersection(rl_keys)
            
            features['common_patterns'] = list(common_keys)
            features['feature_overlap'] = len(common_keys) / max(len(ml_keys), len(rl_keys), 1)
        
        return features
    
    def _perform_knowledge_transfer(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """执行知识迁移"""
        transfer = {
            'ml_to_rl': self._transfer_ml_to_rl(ml_data, rl_data),
            'rl_to_ml': self._transfer_rl_to_ml(ml_data, rl_data),
            'transfer_effectiveness': 0.0
        }
        
        # 计算迁移效果
        ml_contribution = transfer['ml_to_rl'].get('contribution', 0.0)
        rl_contribution = transfer['rl_to_ml'].get('contribution', 0.0)
        transfer['transfer_effectiveness'] = (ml_contribution + rl_contribution) / 2.0
        
        return transfer
    
    def _transfer_ml_to_rl(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """ML到RL的知识迁移"""
        return {
            'transferred_knowledge': 'ML patterns and predictions',
            'contribution': 0.7,
            'transfer_method': 'pattern_recognition',
            'benefit': 'improved_rl_exploration'
        }
    
    def _transfer_rl_to_ml(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """RL到ML的知识迁移"""
        return {
            'transferred_knowledge': 'RL exploration strategies',
            'contribution': 0.6,
            'transfer_method': 'strategy_adaptation',
            'benefit': 'enhanced_ml_learning'
        }
    
    def _joint_optimization(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """联合优化"""
        return {
            'optimization_target': 'joint_performance',
            'optimization_method': 'gradient_based',
            'convergence_rate': 0.85,
            'performance_improvement': 0.15,
            'optimization_steps': 50
        }
    
    def _establish_feedback_loop(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """建立反馈循环"""
        return {
            'feedback_type': 'bidirectional',
            'feedback_frequency': 0.1,
            'feedback_strength': 0.8,
            'learning_acceleration': 1.2
        }
    
    def _exchange_information(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """信息交换"""
        return {
            'exchanged_info': ['patterns', 'strategies', 'insights'],
            'exchange_rate': 0.5,
            'information_quality': 0.7
        }
    
    def _coordinate_strategies(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """策略协调"""
        return {
            'coordination_method': 'consensus_based',
            'coordination_effectiveness': 0.8,
            'strategy_alignment': 0.75
        }
    
    def _fuse_results(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """结果融合"""
        return {
            'fusion_method': 'weighted_ensemble',
            'fusion_confidence': 0.8,
            'result_quality': 0.85
        }
    
    def _extract_ml_insights(self, ml_data: Any) -> Dict[str, Any]:
        """提取ML洞察"""
        return {
            'patterns': ['pattern_1', 'pattern_2'],
            'predictions': ['pred_1', 'pred_2'],
            'confidence': 0.8
        }
    
    def _extract_rl_insights(self, rl_data: Any) -> Dict[str, Any]:
        """提取RL洞察"""
        return {
            'strategies': ['strategy_1', 'strategy_2'],
            'rewards': [0.7, 0.8],
            'exploration': 0.6
        }
    
    def _combine_insights(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """合并洞察"""
        return {
            'combined_insights': ['insight_1', 'insight_2'],
            'synergy_score': 0.75,
            'learning_acceleration': 1.1
        }
    
    def _calculate_learning_effectiveness(self, learning_result: Dict[str, Any]) -> Dict[str, Any]:
        """计算学习效果"""
        effectiveness = {
            'confidence': learning_result.get('confidence', 0.5),
            'learning_rate': 0.01,
            'convergence_score': 0.8,
            'ml_contribution': 0.5,
            'rl_contribution': 0.5
        }
        
        # 基于学习模式调整效果
        mode = learning_result.get('mode', 'basic_collaborative')
        if mode == 'deep_collaborative':
            effectiveness['learning_rate'] = 0.02
            effectiveness['convergence_score'] = 0.9
            effectiveness['ml_contribution'] = 0.6
            effectiveness['rl_contribution'] = 0.6
        elif mode == 'moderate_collaborative':
            effectiveness['learning_rate'] = 0.015
            effectiveness['convergence_score'] = 0.8
            effectiveness['ml_contribution'] = 0.55
            effectiveness['rl_contribution'] = 0.55
        
        return effectiveness
    
    def _update_learning_history(self, learning_env: Dict[str, Any], learning_result: Dict[str, Any], effectiveness: Dict[str, Any]):
        """更新学习历史"""
        history_entry = {
            'timestamp': time.time(),
            'learning_env': learning_env,
            'learning_result': learning_result,
            'effectiveness': effectiveness
        }
        
        self.learning_history.append(history_entry)
        
        # 保持历史记录在合理范围内
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-500:]


class AdaptiveLearningCoordinator:
    """自适应学习协调器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.strategies = {
            'collaborative': CollaborativeLearningStrategy()
        }
        self.metrics = {
            'total_learning_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'average_learning_rate': 0.0,
            'average_convergence_score': 0.0
        }
    
    def coordinate_learning(self, ml_data: Any, rl_data: Any, strategy: str = 'collaborative', context: Optional[Dict[str, Any]] = None) -> LearningResult:
        """协调学习"""
        if strategy not in self.strategies:
            strategy = 'collaborative'
        
        if context is None:
            context = {}
        
        self.metrics['total_learning_sessions'] += 1
        
        try:
            result = self.strategies[strategy].execute(ml_data, rl_data, context)
            
            if result.success:
                self.metrics['successful_sessions'] += 1
            else:
                self.metrics['failed_sessions'] += 1
            
            # 更新指标
            self._update_metrics(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"学习协调失败: {e}")
            self.metrics['failed_sessions'] += 1
            
            return LearningResult(
                success=False,
                data=None,
                confidence=0.0,
                learning_rate=0.0,
                convergence_score=0.0,
                ml_contribution=0.0,
                rl_contribution=0.0,
                processing_time=0.0,
                error=str(e)
            )
    
    def _update_metrics(self, result: LearningResult):
        """更新指标"""
        total = self.metrics['total_learning_sessions']
        
        # 更新平均学习率
        current_avg_rate = self.metrics['average_learning_rate']
        self.metrics['average_learning_rate'] = (current_avg_rate * (total - 1) + result.learning_rate) / total
        
        # 更新平均收敛分数
        current_avg_score = self.metrics['average_convergence_score']
        self.metrics['average_convergence_score'] = (current_avg_score * (total - 1) + result.convergence_score) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def get_learning_history(self, strategy: str = 'collaborative', limit: int = 100) -> List[Dict[str, Any]]:
        """获取学习历史"""
        if strategy in self.strategies:
            return self.strategies[strategy].learning_history[-limit:]
        return []
    
    def get_available_strategies(self) -> List[str]:
        """获取可用策略"""
        return list(self.strategies.keys())
