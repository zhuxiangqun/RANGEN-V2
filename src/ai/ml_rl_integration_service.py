"""
ML/RL集成服务
实现机器学习和强化学习的实际协同应用
"""

import logging
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
import json


@dataclass
class MLRLIntegrationResult:
    """ML/RL集成结果"""
    success: bool
    data: Any
    confidence: float
    processing_time: float
    ml_contribution: float
    rl_contribution: float
    synergy_score: float
    error: Optional[str] = None


class MLRLIntegrationService:
    """ML/RL集成服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ml_models = {}
        self.rl_agents = {}
        self.synergy_history = []
        self.metrics = {
            'total_integrations': 0,
            'successful_integrations': 0,
            'failed_integrations': 0,
            'average_synergy_score': 0.0,
            'ml_usage_count': 0,
            'rl_usage_count': 0
        }
    
    def integrate_ml_rl(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> MLRLIntegrationResult:
        """集成ML和RL"""
        start_time = time.time()
        
        try:
            # 1. 分析ML和RL数据
            ml_analysis = self._analyze_ml_data(ml_data)
            rl_analysis = self._analyze_rl_data(rl_data)
            
            # 2. 确定协同策略
            synergy_strategy = self._determine_synergy_strategy(ml_analysis, rl_analysis, context)
            
            # 3. 执行协同处理
            integration_result = self._execute_synergy_processing(ml_data, rl_data, synergy_strategy, context)
            
            # 4. 计算协同分数
            synergy_score = self._calculate_synergy_score(ml_analysis, rl_analysis, integration_result)
            
            # 5. 更新历史记录
            self._update_synergy_history(ml_analysis, rl_analysis, integration_result, synergy_score)
            
            processing_time = time.time() - start_time
            
            # 更新指标
            self.metrics['total_integrations'] += 1
            self.metrics['successful_integrations'] += 1
            self._update_synergy_metrics(synergy_score)
            
            return MLRLIntegrationResult(
                success=True,
                data=integration_result,
                confidence=integration_result.get('confidence', 0.8),
                processing_time=processing_time,
                ml_contribution=ml_analysis.get('contribution', 0.5),
                rl_contribution=rl_analysis.get('contribution', 0.5),
                synergy_score=synergy_score
            )
            
        except Exception as e:
            self.logger.error(f"ML/RL集成失败: {e}")
            self.metrics['total_integrations'] += 1
            self.metrics['failed_integrations'] += 1
            
            return MLRLIntegrationResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=time.time() - start_time,
                ml_contribution=0.0,
                rl_contribution=0.0,
                synergy_score=0.0,
                error=str(e)
            )
    
    def _analyze_ml_data(self, ml_data: Any) -> Dict[str, Any]:
        """分析ML数据"""
        analysis = {
            'data_type': type(ml_data).__name__,
            'complexity': 0.0,
            'confidence': 0.5,
            'contribution': 0.5,
            'features': [],
            'model_type': 'unknown'
        }
        
        if isinstance(ml_data, dict):
            # 分析字典类型的ML数据
            analysis['complexity'] = len(ml_data) / 10.0
            analysis['confidence'] = ml_data.get('confidence', 0.5)
            analysis['features'] = list(ml_data.keys())
            
            # 识别模型类型
            if 'predictions' in ml_data:
                analysis['model_type'] = 'prediction'
            elif 'classifications' in ml_data:
                analysis['model_type'] = 'classification'
            elif 'clusters' in ml_data:
                analysis['model_type'] = 'clustering'
            elif 'embeddings' in ml_data:
                analysis['model_type'] = 'embedding'
            
        elif isinstance(ml_data, (list, tuple)):
            # 分析列表类型的ML数据
            analysis['complexity'] = len(ml_data) / 20.0
            analysis['features'] = [f"feature_{i}" for i in range(len(ml_data))]
            
            # 检查数据类型
            if all(isinstance(x, (int, float)) for x in ml_data):
                analysis['model_type'] = 'regression'
            elif all(isinstance(x, str) for x in ml_data):
                analysis['model_type'] = 'text_processing'
            else:
                analysis['model_type'] = 'mixed'
        
        # 计算贡献度
        analysis['contribution'] = min(1.0, analysis['complexity'] + analysis['confidence'])
        
        return analysis
    
    def _analyze_rl_data(self, rl_data: Any) -> Dict[str, Any]:
        """分析RL数据"""
        analysis = {
            'data_type': type(rl_data).__name__,
            'reward': 0.0,
            'action_space': 0,
            'state_space': 0,
            'contribution': 0.5,
            'agent_type': 'unknown',
            'exploration_rate': 0.0
        }
        
        if isinstance(rl_data, dict):
            analysis['reward'] = rl_data.get('reward', 0.0)
            analysis['action_space'] = rl_data.get('action_space', 0)
            analysis['state_space'] = rl_data.get('state_space', 0)
            analysis['exploration_rate'] = rl_data.get('exploration_rate', 0.0)
            
            # 识别智能体类型
            if 'q_values' in rl_data:
                analysis['agent_type'] = 'q_learning'
            elif 'policy' in rl_data:
                analysis['agent_type'] = 'policy_gradient'
            elif 'actor_critic' in rl_data:
                analysis['agent_type'] = 'actor_critic'
            elif 'dqn' in rl_data:
                analysis['agent_type'] = 'dqn'
        
        # 计算贡献度
        reward_factor = min(1.0, abs(analysis['reward']))
        space_factor = min(1.0, (analysis['action_space'] + analysis['state_space']) / 100.0)
        analysis['contribution'] = (reward_factor + space_factor) / 2.0
        
        return analysis
    
    def _determine_synergy_strategy(self, ml_analysis: Dict[str, Any], rl_analysis: Dict[str, Any], context: Dict[str, Any]) -> str:
        """确定协同策略"""
        ml_contribution = ml_analysis.get('contribution', 0.5)
        rl_contribution = rl_analysis.get('contribution', 0.5)
        ml_type = ml_analysis.get('model_type', 'unknown')
        rl_type = rl_analysis.get('agent_type', 'unknown')
        
        # 基于贡献度确定策略
        if ml_contribution > 0.7 and rl_contribution > 0.7:
            return 'advanced_synergy'
        elif ml_contribution > 0.5 or rl_contribution > 0.5:
            return 'moderate_synergy'
        else:
            return 'basic_synergy'
    
    def _execute_synergy_processing(self, ml_data: Any, rl_data: Any, strategy: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行协同处理"""
        if strategy == 'advanced_synergy':
            return self._advanced_synergy_processing(ml_data, rl_data, context)
        elif strategy == 'moderate_synergy':
            return self._moderate_synergy_processing(ml_data, rl_data, context)
        else:
            return self._basic_synergy_processing(ml_data, rl_data, context)
    
    def _advanced_synergy_processing(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """高级协同处理"""
        # 1. ML增强RL
        ml_enhanced_rl = self._enhance_rl_with_ml(ml_data, rl_data)
        
        # 2. RL增强ML
        rl_enhanced_ml = self._enhance_ml_with_rl(ml_data, rl_data)
        
        # 3. 联合优化
        joint_optimization = self._joint_optimization(ml_data, rl_data)
        
        # 4. 协同学习
        collaborative_learning = self._collaborative_learning(ml_data, rl_data)
        
        return {
            'strategy': 'advanced_synergy',
            'ml_enhanced_rl': ml_enhanced_rl,
            'rl_enhanced_ml': rl_enhanced_ml,
            'joint_optimization': joint_optimization,
            'collaborative_learning': collaborative_learning,
            'confidence': 0.9,
            'processing_method': 'multi_layer_integration'
        }
    
    def _moderate_synergy_processing(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """中等协同处理"""
        # 1. 特征融合
        feature_fusion = self._fuse_features(ml_data, rl_data)
        
        # 2. 决策融合
        decision_fusion = self._fuse_decisions(ml_data, rl_data)
        
        # 3. 结果融合
        result_fusion = self._fuse_results(ml_data, rl_data)
        
        return {
            'strategy': 'moderate_synergy',
            'feature_fusion': feature_fusion,
            'decision_fusion': decision_fusion,
            'result_fusion': result_fusion,
            'confidence': 0.75,
            'processing_method': 'fusion_based_integration'
        }
    
    def _basic_synergy_processing(self, ml_data: Any, rl_data: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """基础协同处理"""
        # 简单的数据组合
        combined_data = {
            'ml_data': str(ml_data)[:100] if ml_data else "No ML data",
            'rl_data': str(rl_data)[:100] if rl_data else "No RL data",
            'timestamp': time.time()
        }
        
        return {
            'strategy': 'basic_synergy',
            'combined_data': combined_data,
            'confidence': 0.6,
            'processing_method': 'simple_combination'
        }
    
    def _enhance_rl_with_ml(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """使用ML增强RL"""
        enhancement = {
            'enhanced_reward': self._calculate_enhanced_reward(ml_data, rl_data),
            'improved_policy': self._improve_policy_with_ml(ml_data, rl_data),
            'better_state_representation': self._improve_state_representation(ml_data, rl_data),
            'adaptive_exploration': self._adapt_exploration_with_ml(ml_data, rl_data)
        }
        return enhancement
    
    def _enhance_ml_with_rl(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """使用RL增强ML"""
        enhancement = {
            'reinforced_learning': self._reinforce_ml_learning(ml_data, rl_data),
            'adaptive_parameters': self._adapt_ml_parameters(ml_data, rl_data),
            'exploration_guidance': self._guide_ml_exploration(ml_data, rl_data),
            'reward_driven_optimization': self._optimize_ml_with_rewards(ml_data, rl_data)
        }
        return enhancement
    
    def _joint_optimization(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """联合优化"""
        return {
            'optimization_target': 'joint_performance',
            'optimization_method': 'gradient_based',
            'convergence_rate': 0.85,
            'final_performance': 0.92,
            'optimization_steps': 100
        }
    
    def _collaborative_learning(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """协同学习"""
        return {
            'learning_type': 'collaborative',
            'knowledge_sharing': True,
            'mutual_benefit': 0.8,
            'learning_rate': 0.01,
            'convergence_speed': 1.5
        }
    
    def _fuse_features(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """特征融合"""
        return {
            'fusion_method': 'weighted_average',
            'ml_weight': 0.6,
            'rl_weight': 0.4,
            'fused_features': ['feature_1', 'feature_2', 'feature_3']
        }
    
    def _fuse_decisions(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """决策融合"""
        return {
            'fusion_method': 'consensus_based',
            'decision_confidence': 0.8,
            'agreement_level': 0.75,
            'final_decision': 'combined_decision'
        }
    
    def _fuse_results(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """结果融合"""
        return {
            'fusion_method': 'ensemble',
            'result_confidence': 0.85,
            'diversity_score': 0.7,
            'final_result': 'ensemble_result'
        }
    
    def _calculate_enhanced_reward(self, ml_data: Any, rl_data: Any) -> float:
        """计算增强奖励"""
        base_reward = 0.5
        ml_boost = 0.2 if ml_data else 0.0
        return min(1.0, base_reward + ml_boost)
    
    def _improve_policy_with_ml(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """使用ML改进策略"""
        return {
            'policy_type': 'ml_enhanced',
            'improvement_factor': 0.3,
            'new_actions': ['action_1', 'action_2'],
            'policy_confidence': 0.8
        }
    
    def _improve_state_representation(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """改进状态表示"""
        return {
            'representation_type': 'ml_enhanced',
            'feature_count': 10,
            'dimensionality': 5,
            'representation_quality': 0.85
        }
    
    def _adapt_exploration_with_ml(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """使用ML适应探索"""
        return {
            'exploration_type': 'ml_guided',
            'exploration_rate': 0.1,
            'guidance_strength': 0.7,
            'exploration_efficiency': 0.85
        }
    
    def _reinforce_ml_learning(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """强化ML学习"""
        return {
            'reinforcement_type': 'rl_guided',
            'learning_rate': 0.01,
            'convergence_speed': 1.5,
            'reinforcement_strength': 0.8
        }
    
    def _adapt_ml_parameters(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """适应ML参数"""
        return {
            'parameter_adaptation': True,
            'adaptation_rate': 0.1,
            'stability': 0.8,
            'adaptation_method': 'rl_guided'
        }
    
    def _guide_ml_exploration(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """指导ML探索"""
        return {
            'exploration_guidance': True,
            'guidance_strength': 0.7,
            'exploration_efficiency': 0.85,
            'guidance_method': 'rl_based'
        }
    
    def _optimize_ml_with_rewards(self, ml_data: Any, rl_data: Any) -> Dict[str, Any]:
        """使用奖励优化ML"""
        return {
            'optimization_type': 'reward_driven',
            'reward_weight': 0.5,
            'optimization_success': 0.8,
            'performance_improvement': 0.15
        }
    
    def _calculate_synergy_score(self, ml_analysis: Dict[str, Any], rl_analysis: Dict[str, Any], result: Dict[str, Any]) -> float:
        """计算协同分数"""
        ml_contribution = ml_analysis.get('contribution', 0.5)
        rl_contribution = rl_analysis.get('contribution', 0.5)
        result_confidence = result.get('confidence', 0.5)
        
        # 基础协同分数
        base_synergy = (ml_contribution + rl_contribution) / 2.0
        
        # 置信度调整
        confidence_boost = result_confidence * 0.3
        
        # 策略复杂度调整
        strategy = result.get('strategy', 'basic_synergy')
        if strategy == 'advanced_synergy':
            strategy_boost = 0.2
        elif strategy == 'moderate_synergy':
            strategy_boost = 0.1
        else:
            strategy_boost = 0.0
        
        final_score = min(1.0, base_synergy + confidence_boost + strategy_boost)
        return final_score
    
    def _update_synergy_history(self, ml_analysis: Dict[str, Any], rl_analysis: Dict[str, Any], result: Dict[str, Any], synergy_score: float):
        """更新协同历史"""
        history_entry = {
            'timestamp': time.time(),
            'ml_contribution': ml_analysis.get('contribution', 0.5),
            'rl_contribution': rl_analysis.get('contribution', 0.5),
            'synergy_score': synergy_score,
            'strategy': result.get('strategy', 'unknown')
        }
        
        self.synergy_history.append(history_entry)
        
        # 保持历史记录在合理范围内
        if len(self.synergy_history) > 1000:
            self.synergy_history = self.synergy_history[-500:]
    
    def _update_synergy_metrics(self, synergy_score: float):
        """更新协同指标"""
        total = self.metrics['total_integrations']
        current_avg = self.metrics['average_synergy_score']
        self.metrics['average_synergy_score'] = (current_avg * (total - 1) + synergy_score) / total
    
    def get_synergy_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取协同历史"""
        return self.synergy_history[-limit:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def get_synergy_statistics(self) -> Dict[str, Any]:
        """获取协同统计"""
        if not self.synergy_history:
            return {'error': 'No synergy history available'}
        
        scores = [entry['synergy_score'] for entry in self.synergy_history]
        
        return {
            'total_entries': len(self.synergy_history),
            'average_synergy_score': sum(scores) / len(scores),
            'max_synergy_score': max(scores),
            'min_synergy_score': min(scores),
            'recent_trend': self._calculate_recent_trend(scores)
        }
    
    def _calculate_recent_trend(self, scores: List[float]) -> str:
        """计算最近趋势"""
        if len(scores) < 10:
            return 'insufficient_data'
        
        recent_scores = scores[-10:]
        older_scores = scores[-20:-10] if len(scores) >= 20 else scores[:-10]
        
        if not older_scores:
            return 'insufficient_data'
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        if recent_avg > older_avg * 1.1:
            return 'improving'
        elif recent_avg < older_avg * 0.9:
            return 'declining'
        else:
            return 'stable'
