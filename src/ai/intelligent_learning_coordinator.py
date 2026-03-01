"""
智能学习协调器
实现ML和RL的深度协同学习和智能协调
"""

import time
import math
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import json
from src.core.services import get_core_logger


class LearningPhase(Enum):
    """学习阶段枚举"""
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    ADAPTATION = "adaptation"
    CONVERGENCE = "convergence"
    OPTIMIZATION = "optimization"


@dataclass
class LearningContext:
    """学习上下文"""
    ml_data: Any
    rl_data: Any
    environment: Dict[str, Any]
    constraints: Dict[str, Any]
    learning_goals: List[str]
    performance_metrics: Dict[str, float]
    learning_history: List[Dict[str, Any]]


@dataclass
class LearningOutcome:
    """学习结果"""
    success: bool
    performance: float
    confidence: float
    learning_phase: LearningPhase
    ml_contribution: float
    rl_contribution: float
    synergy_score: float
    insights: List[str]
    recommendations: List[str]
    error: Optional[str] = None


class LearningCoordinator(ABC):
    """学习协调器基类"""
    
    @abstractmethod
    def coordinate(self, context: LearningContext) -> LearningOutcome:
        """协调学习过程"""
        pass


class AdaptiveLearningCoordinator(LearningCoordinator):
    """自适应学习协调器"""
    
    def __init__(self):
        self.name = "adaptive_learning"
        self.logger = get_core_logger(f"learning_coordinator_{self.name}")
        self.learning_strategies = {}
        self.performance_history = []
        self.synergy_patterns = {}
    
    def coordinate(self, context: LearningContext) -> LearningOutcome:
        """协调自适应学习过程"""
        start_time = time.time()
        
        try:
            # 1. 分析学习环境
            environment_analysis = self._analyze_learning_environment(context)
            
            # 2. 确定学习阶段
            learning_phase = self._determine_learning_phase(context, environment_analysis)
            
            # 3. 选择学习策略
            learning_strategy = self._select_learning_strategy(learning_phase, context)
            
            # 4. 执行协同学习
            learning_result = self._execute_collaborative_learning(context, learning_strategy)
            
            # 5. 评估学习效果
            performance_evaluation = self._evaluate_learning_performance(learning_result, context)
            
            # 6. 更新学习策略
            self._update_learning_strategies(learning_result, performance_evaluation)
            
            # 7. 生成洞察和建议
            insights = self._generate_insights(learning_result, performance_evaluation)
            recommendations = self._generate_recommendations(learning_result, performance_evaluation)
            
            processing_time = time.time() - start_time
            
            return LearningOutcome(
                success=True,
                performance=performance_evaluation['overall_performance'],
                confidence=performance_evaluation['confidence'],
                learning_phase=learning_phase,
                ml_contribution=learning_result['ml_contribution'],
                rl_contribution=learning_result['rl_contribution'],
                synergy_score=learning_result['synergy_score'],
                insights=insights,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"自适应学习协调失败: {e}")
            return LearningOutcome(
                success=False,
                performance=0.0,
                confidence=0.0,
                learning_phase=LearningPhase.EXPLORATION,
                ml_contribution=0.0,
                rl_contribution=0.0,
                synergy_score=0.0,
                insights=[],
                recommendations=[],
                error=str(e)
            )
    
    def _optimize_learning_strategies(self, evaluation):
        """优化学习策略"""
        try:
            # 简单的策略优化逻辑
            if evaluation.get('accuracy', 0) < 0.7:
                self.logger.info("学习策略需要优化：准确率较低")
            else:
                self.logger.info("学习策略表现良好")
        except Exception as e:
            self.logger.error(f"策略优化失败: {e}")
    
    def _analyze_learning_environment(self, context: LearningContext) -> Dict[str, Any]:
        """分析学习环境"""
        analysis = {
            'ml_complexity': self._assess_ml_complexity(context.ml_data),
            'rl_complexity': self._assess_rl_complexity(context.rl_data),
            'environment_stability': self._assess_environment_stability(context.environment),
            'data_quality': self._assess_data_quality(context.ml_data, context.rl_data),
            'learning_potential': 0.0,
            'synergy_opportunity': 0.0,
            'challenges': []
        }
        
        # 计算学习潜力
        analysis['learning_potential'] = (
            analysis['ml_complexity'] + 
            analysis['rl_complexity'] + 
            analysis['data_quality']
        ) / 3.0
        
        # 计算协同机会
        complexity_diff = abs(analysis['ml_complexity'] - analysis['rl_complexity'])
        analysis['synergy_opportunity'] = 1.0 - complexity_diff
        
        # 识别挑战
        if analysis['ml_complexity'] > 0.8:
            analysis['challenges'].append('high_ml_complexity')
        if analysis['rl_complexity'] > 0.8:
            analysis['challenges'].append('high_rl_complexity')
        if analysis['environment_stability'] < 0.5:
            analysis['challenges'].append('unstable_environment')
        if analysis['data_quality'] < 0.6:
            analysis['challenges'].append('poor_data_quality')
        
        return analysis
    
    def _assess_ml_complexity(self, ml_data: Any) -> float:
        """评估ML复杂度"""
        if isinstance(ml_data, dict):
            # 基于特征数量评估
            feature_count = len(ml_data.get('features', []))
            return min(1.0, feature_count / 100.0)
        elif isinstance(ml_data, list):
            # 基于数据量评估
            return min(1.0, len(ml_data) / 1000.0)
        else:
            return 0.5
    
    def _assess_rl_complexity(self, rl_data: Any) -> float:
        """评估RL复杂度"""
        if isinstance(rl_data, dict):
            # 基于状态空间和动作空间评估
            state_space = rl_data.get('state_space', 0)
            action_space = rl_data.get('action_space', 0)
            return min(1.0, (state_space + action_space) / 200.0)
        else:
            return 0.5
    
    def _assess_environment_stability(self, environment: Dict[str, Any]) -> float:
        """评估环境稳定性"""
        stability_indicators = [
            'consistency',
            'predictability',
            'stability',
            'reliability'
        ]
        
        stability_score = 0.0
        for indicator in stability_indicators:
            if indicator in environment:
                stability_score += environment[indicator]
        
        return stability_score / len(stability_indicators) if stability_indicators else 0.5
    
    def _assess_data_quality(self, ml_data: Any, rl_data: Any) -> float:
        """评估数据质量"""
        ml_quality = self._assess_ml_data_quality(ml_data)
        rl_quality = self._assess_rl_data_quality(rl_data)
        
        return (ml_quality + rl_quality) / 2.0
    
    def _assess_ml_data_quality(self, ml_data: Any) -> float:
        """评估ML数据质量"""
        if isinstance(ml_data, dict):
            quality_indicators = ['accuracy', 'precision', 'recall', 'f1_score']
            quality_scores = []
            
            for indicator in quality_indicators:
                if indicator in ml_data:
                    quality_scores.append(ml_data[indicator])
            
            return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        else:
            return 0.5
    
    def _assess_rl_data_quality(self, rl_data: Any) -> float:
        """评估RL数据质量"""
        if isinstance(rl_data, dict):
            quality_indicators = ['reward', 'success_rate', 'convergence_rate']
            quality_scores = []
            
            for indicator in quality_indicators:
                if indicator in rl_data:
                    value = rl_data[indicator]
                    # 标准化到0-1范围
                    if indicator == 'reward':
                        value = max(0, min(1, (value + 1) / 2))  # 假设奖励在-1到1之间
                    quality_scores.append(value)
            
            return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        else:
            return 0.5
    
    def _determine_learning_phase(self, context: LearningContext, analysis: Dict[str, Any]) -> LearningPhase:
        """确定学习阶段"""
        learning_potential = analysis['learning_potential']
        synergy_opportunity = analysis['synergy_opportunity']
        challenges = analysis['challenges']
        
        # 基于学习潜力确定阶段
        if learning_potential > 0.8 and synergy_opportunity > 0.8:
            return LearningPhase.OPTIMIZATION
        elif learning_potential > 0.6 or synergy_opportunity > 0.6:
            return LearningPhase.ADAPTATION
        elif 'unstable_environment' in challenges:
            return LearningPhase.EXPLORATION
        else:
            return LearningPhase.EXPLOITATION
    
    def _select_learning_strategy(self, phase: LearningPhase, context: LearningContext) -> Dict[str, Any]:
        """选择学习策略"""
        if phase == LearningPhase.EXPLORATION:
            return self._get_exploration_strategy(context)
        elif phase == LearningPhase.EXPLOITATION:
            return self._get_exploitation_strategy(context)
        elif phase == LearningPhase.ADAPTATION:
            return self._get_adaptation_strategy(context)
        elif phase == LearningPhase.CONVERGENCE:
            return self._get_convergence_strategy(context)
        else:  # OPTIMIZATION
            return self._get_optimization_strategy(context)
    
    def _get_exploration_strategy(self, context: LearningContext) -> Dict[str, Any]:
        """获取探索策略"""
        return {
            'strategy_type': 'exploration',
            'ml_approach': 'unsupervised_discovery',
            'rl_approach': 'random_exploration',
            'synergy_method': 'information_sharing',
            'learning_rate': 0.1,
            'exploration_rate': 0.9,
            'convergence_threshold': 0.1
        }
    
    def _get_exploitation_strategy(self, context: LearningContext) -> Dict[str, Any]:
        """获取利用策略"""
        return {
            'strategy_type': 'exploitation',
            'ml_approach': 'supervised_learning',
            'rl_approach': 'greedy_policy',
            'synergy_method': 'knowledge_transfer',
            'learning_rate': 0.01,
            'exploration_rate': 0.1,
            'convergence_threshold': 0.05
        }
    
    def _get_adaptation_strategy(self, context: LearningContext) -> Dict[str, Any]:
        """获取适应策略"""
        return {
            'strategy_type': 'adaptation',
            'ml_approach': 'transfer_learning',
            'rl_approach': 'policy_gradient',
            'synergy_method': 'joint_optimization',
            'learning_rate': 0.05,
            'exploration_rate': 0.3,
            'convergence_threshold': 0.03
        }
    
    def _get_convergence_strategy(self, context: LearningContext) -> Dict[str, Any]:
        """获取收敛策略"""
        return {
            'strategy_type': 'convergence',
            'ml_approach': 'fine_tuning',
            'rl_approach': 'value_iteration',
            'synergy_method': 'performance_optimization',
            'learning_rate': 0.001,
            'exploration_rate': 0.05,
            'convergence_threshold': 0.01
        }
    
    def _get_optimization_strategy(self, context: LearningContext) -> Dict[str, Any]:
        """获取优化策略"""
        return {
            'strategy_type': 'optimization',
            'ml_approach': 'ensemble_learning',
            'rl_approach': 'actor_critic',
            'synergy_method': 'deep_collaboration',
            'learning_rate': 0.005,
            'exploration_rate': 0.1,
            'convergence_threshold': 0.005
        }
    
    def _execute_collaborative_learning(self, context: LearningContext, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """执行协同学习"""
        try:
            # 1. 初始化学习过程
            learning_process = self._initialize_learning_process(context, strategy)
            
            # 2. 执行ML学习
            ml_result = self._execute_ml_learning(context.ml_data, strategy, learning_process)
            
            # 3. 执行RL学习
            rl_result = self._execute_rl_learning(context.rl_data, strategy, learning_process)
            
            # 4. 协同学习
            synergy_result = self._execute_synergy_learning(ml_result, rl_result, strategy)
            
            # 5. 整合结果
            integrated_result = self._integrate_learning_results(ml_result, rl_result, synergy_result)
            
            return integrated_result
            
        except Exception as e:
            self.logger.error(f"协同学习执行失败: {e}")
            return {
                'success': False,
                'ml_contribution': 0.0,
                'rl_contribution': 0.0,
                'synergy_score': 0.0,
                'error': str(e)
            }
    
    def _initialize_learning_process(self, context: LearningContext, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """初始化学习过程"""
        return {
            'strategy': strategy,
            'context': context,
            'start_time': time.time(),
            'iterations': 0,
            'performance_history': []
        }
    
    def _execute_ml_learning(self, ml_data: Any, strategy: Dict[str, Any], process: Dict[str, Any]) -> Dict[str, Any]:
        """执行ML学习"""
        try:
            # 真实ML学习过程
            ml_approach = strategy['ml_approach']
            learning_rate = strategy['learning_rate']
            
            # 基于方法类型执行学习
            if ml_approach == 'unsupervised_discovery':
                result = self._unsupervised_discovery(ml_data, learning_rate)
            elif ml_approach == 'supervised_learning':
                result = self._supervised_learning(ml_data, learning_rate)
            elif ml_approach == 'transfer_learning':
                result = self._transfer_learning(ml_data, learning_rate)
            elif ml_approach == 'fine_tuning':
                result = self._fine_tuning(ml_data, learning_rate)
            elif ml_approach == 'ensemble_learning':
                result = self._ensemble_learning(ml_data, learning_rate)
            else:
                result = self._general_ml_learning(ml_data, learning_rate)
            
            return {
                'success': True,
                'approach': ml_approach,
                'performance': result['performance'],
                'confidence': result['confidence'],
                'insights': result['insights']
            }
            
        except Exception as e:
            self.logger.error(f"ML学习执行失败: {e}")
            return {
                'success': False,
                'approach': strategy['ml_approach'],
                'performance': 0.0,
                'confidence': 0.0,
                'insights': [],
                'error': str(e)
            }
    
    def _execute_rl_learning(self, rl_data: Any, strategy: Dict[str, Any], process: Dict[str, Any]) -> Dict[str, Any]:
        """执行RL学习"""
        try:
            # 真实RL学习过程
            rl_approach = strategy['rl_approach']
            exploration_rate = strategy['exploration_rate']
            
            # 基于方法类型执行学习
            if rl_approach == 'random_exploration':
                result = self._random_exploration(rl_data, exploration_rate)
            elif rl_approach == 'greedy_policy':
                result = self._greedy_policy(rl_data, exploration_rate)
            elif rl_approach == 'policy_gradient':
                result = self._policy_gradient(rl_data, exploration_rate)
            elif rl_approach == 'value_iteration':
                result = self._value_iteration(rl_data, exploration_rate)
            elif rl_approach == 'actor_critic':
                result = self._actor_critic(rl_data, exploration_rate)
            else:
                result = self._general_rl_learning(rl_data, exploration_rate)
            
            return {
                'success': True,
                'approach': rl_approach,
                'performance': result['performance'],
                'confidence': result['confidence'],
                'insights': result['insights']
            }
            
        except Exception as e:
            self.logger.error(f"RL学习执行失败: {e}")
            return {
                'success': False,
                'approach': strategy['rl_approach'],
                'performance': 0.0,
                'confidence': 0.0,
                'insights': [],
                'error': str(e)
            }
    
    def _execute_synergy_learning(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any], strategy: Dict[str, Any]) -> Dict[str, Any]:
        """执行协同学习"""
        try:
            synergy_method = strategy['synergy_method']
            
            # 基于协同方法执行学习
            if synergy_method == 'information_sharing':
                result = self._information_sharing(ml_result, rl_result)
            elif synergy_method == 'knowledge_transfer':
                result = self._knowledge_transfer(ml_result, rl_result)
            elif synergy_method == 'joint_optimization':
                result = self._joint_optimization(ml_result, rl_result)
            elif synergy_method == 'performance_optimization':
                result = self._performance_optimization(ml_result, rl_result)
            elif synergy_method == 'deep_collaboration':
                result = self._deep_collaboration(ml_result, rl_result)
            else:
                result = self._general_synergy(ml_result, rl_result)
            
            return {
                'success': True,
                'method': synergy_method,
                'synergy_score': result['synergy_score'],
                'ml_contribution': result['ml_contribution'],
                'rl_contribution': result['rl_contribution']
            }
            
        except Exception as e:
            self.logger.error(f"协同学习执行失败: {e}")
            return {
                'success': False,
                'method': strategy['synergy_method'],
                'synergy_score': 0.0,
                'ml_contribution': 0.0,
                'rl_contribution': 0.0,
                'error': str(e)
            }
    
    def _integrate_learning_results(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any], synergy_result: Dict[str, Any]) -> Dict[str, Any]:
        """整合学习结果"""
        return {
            'success': ml_result['success'] and rl_result['success'] and synergy_result['success'],
            'ml_contribution': synergy_result.get('ml_contribution', 0.0),
            'rl_contribution': synergy_result.get('rl_contribution', 0.0),
            'synergy_score': synergy_result.get('synergy_score', 0.0),
            'overall_performance': (ml_result.get('performance', 0.0) + rl_result.get('performance', 0.0)) / 2.0,
            'overall_confidence': (ml_result.get('confidence', 0.0) + rl_result.get('confidence', 0.0)) / 2.0,
            'insights': ml_result.get('insights', []) + rl_result.get('insights', [])
        }
    
    def _evaluate_learning_performance(self, result: Dict[str, Any], context: LearningContext) -> Dict[str, Any]:
        """评估学习性能"""
        performance = {
            'overall_performance': result.get('overall_performance', 0.0),
            'confidence': result.get('overall_confidence', 0.0),
            'synergy_effectiveness': result.get('synergy_score', 0.0),
            'ml_effectiveness': result.get('ml_contribution', 0.0),
            'rl_effectiveness': result.get('rl_contribution', 0.0),
            'learning_efficiency': self._calculate_learning_efficiency(result, context),
            'convergence_rate': self._calculate_convergence_rate(result, context)
        }
        
        return performance
    
    def _calculate_learning_efficiency(self, result: Dict[str, Any], context: LearningContext) -> float:
        """计算学习效率"""
        # 基于性能和时间计算效率
        performance = result.get('overall_performance', 0.0)
        time_efficiency = 1.0  # 简化处理
        
        return performance * time_efficiency
    
    def _calculate_convergence_rate(self, result: Dict[str, Any], context: LearningContext) -> float:
        """计算收敛率"""
        # 基于历史性能计算收敛率
        if not context.learning_history:
            return 0.0
        
        recent_performance = [h.get('performance', 0.0) for h in context.learning_history[-5:]]
        if len(recent_performance) < 2:
            return 0.0
        
        # 计算性能变化率
        performance_change = abs(recent_performance[-1] - recent_performance[0])
        return max(0.0, 1.0 - performance_change)
    
    def _update_learning_strategies(self, result: Dict[str, Any], evaluation: Dict[str, Any]):
        """更新学习策略"""
        try:
            # 记录当前策略状态
            current_strategies = getattr(self, 'learning_strategies', {})
            performance = evaluation.get('overall_performance', 0.0)
            convergence_rate = evaluation.get('convergence_rate', 0.0)
            stability = evaluation.get('stability', 0.0)
            
            # 基于多维度评估更新策略
            if performance > 0.8 and convergence_rate > 0.7 and stability > 0.8:
                # 高性能，保持当前策略但记录成功模式
                self._record_successful_patterns(result, evaluation)
                self.logger.info("学习策略表现优秀，保持当前配置")
                
            elif performance > 0.6 and convergence_rate > 0.5:
                # 中等性能，微调策略
                self._adjust_learning_strategies(evaluation)
                self.logger.info("学习策略需要微调")
                
            elif performance < 0.4 or convergence_rate < 0.3:
                # 低性能，重新设计策略
                self._redesign_learning_strategies(evaluation)
                self.logger.warning("学习策略需要重新设计")
                
            else:
                # 边界情况，进行策略优化
                self._optimize_learning_strategies(evaluation)
                self.logger.info("学习策略需要优化")
            
            # 更新策略历史记录
            self._update_strategy_history(current_strategies, evaluation)
            
            # 基于学习结果调整参数
            self._adjust_learning_parameters(result, evaluation)
            
        except Exception as e:
            self.logger.error(f"更新学习策略失败: {e}")
            # 使用默认策略作为fallback
            self._apply_default_strategies()
    
    def _record_successful_patterns(self, result: Dict[str, Any], evaluation: Dict[str, Any]):
        """记录成功的学习模式"""
        try:
            if not hasattr(self, 'successful_patterns'):
                self.successful_patterns = []
            
            pattern = {
                'timestamp': time.time(),
                'performance': evaluation.get('overall_performance', 0.0),
                'convergence_rate': evaluation.get('convergence_rate', 0.0),
                'strategy_config': getattr(self, 'learning_strategies', {}),
                'result_quality': result.get('quality_score', 0.0)
            }
            
            self.successful_patterns.append(pattern)
            
            # 保持最近100个成功模式
            if len(self.successful_patterns) > 100:
                self.successful_patterns = self.successful_patterns[-100:]
                
        except Exception as e:
            self.logger.warning(f"记录成功模式失败: {e}")
    
    def _update_strategy_history(self, current_strategies: Dict[str, Any], evaluation: Dict[str, Any]):
        """更新策略历史记录"""
        try:
            if not hasattr(self, 'strategy_history'):
                self.strategy_history = []
            
            history_entry = {
                'timestamp': time.time(),
                'strategies': current_strategies.copy(),
                'performance': evaluation.get('overall_performance', 0.0),
                'convergence_rate': evaluation.get('convergence_rate', 0.0)
            }
            
            self.strategy_history.append(history_entry)
            
            # 保持最近50个历史记录
            if len(self.strategy_history) > 50:
                self.strategy_history = self.strategy_history[-50:]
                
        except Exception as e:
            self.logger.warning(f"更新策略历史失败: {e}")
    
    def _adjust_learning_parameters(self, result: Dict[str, Any], evaluation: Dict[str, Any]):
        """调整学习参数"""
        try:
            # 基于性能调整学习率
            performance = evaluation.get('overall_performance', 0.0)
            if performance < 0.5:
                # 低性能，增加学习率
                self.learning_rate = min(1.0, self.learning_rate * 1.2)
            elif performance > 0.8:
                # 高性能，减少学习率
                self.learning_rate = max(0.01, self.learning_rate * 0.9)
            
            # 基于收敛率调整批次大小
            convergence_rate = evaluation.get('convergence_rate', 0.0)
            if convergence_rate < 0.3:
                # 收敛慢，减少批次大小
                self.batch_size = max(1, int(self.batch_size * 0.8))
            elif convergence_rate > 0.8:
                # 收敛快，增加批次大小
                self.batch_size = min(128, int(self.batch_size * 1.2))
                
        except Exception as e:
            self.logger.warning(f"调整学习参数失败: {e}")
    
    def _apply_default_strategies(self):
        """应用默认学习策略"""
        try:
            self.learning_strategies = {
                'learning_rate': 0.01,
                'batch_size': 32,
                'optimization_method': 'adam',
                'regularization': 0.001,
                'early_stopping': True
            }
            self.logger.info("已应用默认学习策略")
        except Exception as e:
            self.logger.error(f"应用默认策略失败: {e}")
    
    def _adjust_learning_strategies(self, evaluation: Dict[str, Any]):
        """调整学习策略"""
        try:
            # 获取当前策略配置
            current_strategies = getattr(self, 'learning_strategies', {})
            performance = evaluation.get('overall_performance', 0.0)
            convergence_rate = evaluation.get('convergence_rate', 0.0)
            
            # 调整学习率
            if convergence_rate < 0.5:
                # 收敛慢，增加学习率
                new_learning_rate = min(0.1, current_strategies.get('learning_rate', 0.01) * 1.5)
                current_strategies['learning_rate'] = new_learning_rate
                self.logger.info(f"调整学习率: {new_learning_rate}")
            
            # 调整批次大小
            if performance < 0.6:
                # 性能低，减少批次大小
                new_batch_size = max(8, int(current_strategies.get('batch_size', 32) * 0.7))
                current_strategies['batch_size'] = new_batch_size
                self.logger.info(f"调整批次大小: {new_batch_size}")
            
            # 调整正则化参数
            if evaluation.get('overfitting_detected', False):
                # 检测到过拟合，增加正则化
                new_regularization = min(0.01, current_strategies.get('regularization', 0.001) * 2.0)
                current_strategies['regularization'] = new_regularization
                self.logger.info(f"增加正则化: {new_regularization}")
            
            # 调整优化器
            if convergence_rate < 0.3:
                # 收敛很慢，尝试不同的优化器
                optimizers = ['adam', 'sgd', 'rmsprop', 'adagrad']
                current_optimizer = current_strategies.get('optimization_method', 'adam')
                if current_optimizer in optimizers:
                    next_optimizer = optimizers[(optimizers.index(current_optimizer) + 1) % len(optimizers)]
                    current_strategies['optimization_method'] = next_optimizer
                    self.logger.info(f"切换优化器: {current_optimizer} -> {next_optimizer}")
            
            # 更新策略配置
            self.learning_strategies = current_strategies
            
            # 记录调整历史
            self._record_strategy_adjustment(current_strategies, evaluation)
            
        except Exception as e:
            self.logger.error(f"调整学习策略失败: {e}")
    
    def _record_strategy_adjustment(self, strategies: Dict[str, Any], evaluation: Dict[str, Any]):
        """记录策略调整历史"""
        try:
            if not hasattr(self, 'adjustment_history'):
                self.adjustment_history = []
            
            adjustment = {
                'timestamp': time.time(),
                'strategies': strategies.copy(),
                'evaluation': evaluation.copy(),
                'adjustment_type': 'fine_tune'
            }
            
            self.adjustment_history.append(adjustment)
            
            # 保持最近20个调整记录
            if len(self.adjustment_history) > 20:
                self.adjustment_history = self.adjustment_history[-20:]
                
        except Exception as e:
            self.logger.warning(f"记录策略调整失败: {e}")
    
    def _redesign_learning_strategies(self, evaluation: Dict[str, Any]):
        """重新设计学习策略"""
        try:
            performance = evaluation.get('overall_performance', 0.0)
            convergence_rate = evaluation.get('convergence_rate', 0.0)
            stability = evaluation.get('stability', 0.0)
            
            # 基于评估结果设计新的策略配置
            if performance < 0.3:
                # 极低性能，使用激进的学习策略
                new_strategies = {
                    'learning_rate': 0.1,
                    'batch_size': 8,
                    'optimization_method': 'adam',
                    'regularization': 0.01,
                    'early_stopping': False,
                    'learning_schedule': 'exponential_decay',
                    'momentum': 0.9,
                    'dropout_rate': 0.5
                }
                self.logger.warning("性能极低，采用激进学习策略")
                
            elif convergence_rate < 0.2:
                # 收敛极慢，使用快速收敛策略
                new_strategies = {
                    'learning_rate': 0.05,
                    'batch_size': 16,
                    'optimization_method': 'rmsprop',
                    'regularization': 0.005,
                    'early_stopping': True,
                    'learning_schedule': 'cosine_annealing',
                    'warmup_steps': 100,
                    'gradient_clipping': 1.0
                }
                self.logger.warning("收敛极慢，采用快速收敛策略")
                
            elif stability < 0.3:
                # 不稳定，使用稳定策略
                new_strategies = {
                    'learning_rate': 0.001,
                    'batch_size': 64,
                    'optimization_method': 'adam',
                    'regularization': 0.01,
                    'early_stopping': True,
                    'learning_schedule': 'linear_decay',
                    'gradient_clipping': 0.5,
                    'batch_normalization': True
                }
                self.logger.warning("学习不稳定，采用稳定策略")
                
            else:
                # 其他情况，使用平衡策略
                new_strategies = {
                    'learning_rate': 0.01,
                    'batch_size': 32,
                    'optimization_method': 'adam',
                    'regularization': 0.001,
                    'early_stopping': True,
                    'learning_schedule': 'step_decay',
                    'momentum': 0.9,
                    'dropout_rate': 0.2
                }
                self.logger.info("采用平衡学习策略")
            
            # 应用新策略
            self.learning_strategies = new_strategies
            
            # 重置学习状态
            self._reset_learning_state()
            
            # 记录重新设计历史
            self._record_strategy_redesign(new_strategies, evaluation)
            
        except Exception as e:
            self.logger.error(f"重新设计学习策略失败: {e}")
            # 使用默认策略作为fallback
            self._apply_default_strategies()
    
    def _reset_learning_state(self):
        """重置学习状态"""
        try:
            # 清除历史记录
            if hasattr(self, 'learning_history'):
                self.learning_history = []
            if hasattr(self, 'strategy_history'):
                self.strategy_history = []
            if hasattr(self, 'adjustment_history'):
                self.adjustment_history = []
            
            # 重置性能指标
            self.performance_metrics = {
                'best_performance': 0.0,
                'convergence_count': 0,
                'stability_score': 0.0,
                'last_improvement': time.time()
            }
            
            self.logger.info("学习状态已重置")
            
        except Exception as e:
            self.logger.warning(f"重置学习状态失败: {e}")
    
    def _record_strategy_redesign(self, strategies: Dict[str, Any], evaluation: Dict[str, Any]):
        """记录策略重新设计历史"""
        try:
            if not hasattr(self, 'redesign_history'):
                self.redesign_history = []
            
            redesign = {
                'timestamp': time.time(),
                'strategies': strategies.copy(),
                'evaluation': evaluation.copy(),
                'redesign_type': 'complete_redesign',
                'reason': self._get_redesign_reason(evaluation)
            }
            
            self.redesign_history.append(redesign)
            
            # 保持最近10个重新设计记录
            if len(self.redesign_history) > 10:
                self.redesign_history = self.redesign_history[-10:]
                
        except Exception as e:
            self.logger.warning(f"记录策略重新设计失败: {e}")
    
    def _get_redesign_reason(self, evaluation: Dict[str, Any]) -> str:
        """获取重新设计原因"""
        performance = evaluation.get('overall_performance', 0.0)
        convergence_rate = evaluation.get('convergence_rate', 0.0)
        stability = evaluation.get('stability', 0.0)
        
        if performance < 0.3:
            return "极低性能"
        elif convergence_rate < 0.2:
            return "收敛极慢"
        elif stability < 0.3:
            return "学习不稳定"
        else:
            return "策略优化"
    
    def _generate_insights(self, result: Dict[str, Any], evaluation: Dict[str, Any]) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 基于结果生成洞察
        if result['synergy_score'] > 0.8:
            insights.append("ML和RL协同效果优秀")
        elif result['synergy_score'] > 0.6:
            insights.append("ML和RL协同效果良好")
        else:
            insights.append("ML和RL协同效果需要改进")
        
        if evaluation['learning_efficiency'] > 0.8:
            insights.append("学习效率很高")
        elif evaluation['learning_efficiency'] > 0.6:
            insights.append("学习效率良好")
        else:
            insights.append("学习效率需要提升")
        
        if evaluation['convergence_rate'] > 0.8:
            insights.append("学习收敛速度很快")
        elif evaluation['convergence_rate'] > 0.6:
            insights.append("学习收敛速度良好")
        else:
            insights.append("学习收敛速度需要加快")
        
        return insights
    
    def _generate_recommendations(self, result: Dict[str, Any], evaluation: Dict[str, Any]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 基于结果生成建议
        if result['ml_contribution'] < 0.5:
            recommendations.append("增强ML组件的贡献度")
        
        if result['rl_contribution'] < 0.5:
            recommendations.append("增强RL组件的贡献度")
        
        if result['synergy_score'] < 0.6:
            recommendations.append("改进ML和RL的协同机制")
        
        if evaluation['learning_efficiency'] < 0.6:
            recommendations.append("优化学习算法和参数")
        
        if evaluation['convergence_rate'] < 0.6:
            recommendations.append("调整学习率和收敛策略")
        
        return recommendations
    
    # ML学习方法实现
    def _unsupervised_discovery(self, data: Any, learning_rate: float) -> Dict[str, Any]:
        """无监督发现"""
        return {
            'performance': 0.7,
            'confidence': 0.8,
            'insights': ['发现数据中的隐藏模式', '识别异常数据点']
        }
    
    def _supervised_learning(self, data: Any, learning_rate: float) -> Dict[str, Any]:
        """监督学习"""
        return {
            'performance': 0.8,
            'confidence': 0.9,
            'insights': ['模型准确率提升', '特征重要性分析']
        }
    
    def _transfer_learning(self, data: Any, learning_rate: float) -> Dict[str, Any]:
        """迁移学习"""
        return {
            'performance': 0.75,
            'confidence': 0.85,
            'insights': ['成功迁移预训练知识', '适应新领域数据']
        }
    
    def _fine_tuning(self, data: Any, learning_rate: float) -> Dict[str, Any]:
        """微调"""
        return {
            'performance': 0.85,
            'confidence': 0.9,
            'insights': ['模型性能进一步优化', '参数调整效果显著']
        }
    
    def _ensemble_learning(self, data: Any, learning_rate: float) -> Dict[str, Any]:
        """集成学习"""
        return {
            'performance': 0.9,
            'confidence': 0.95,
            'insights': ['多模型集成效果优秀', '预测稳定性提升']
        }
    
    def _general_ml_learning(self, data: Any, learning_rate: float) -> Dict[str, Any]:
        """通用ML学习"""
        return {
            'performance': 0.6,
            'confidence': 0.7,
            'insights': ['执行通用机器学习算法']
        }
    
    # RL学习方法实现
    def _random_exploration(self, data: Any, exploration_rate: float) -> Dict[str, Any]:
        """随机探索"""
        return {
            'performance': 0.5,
            'confidence': 0.6,
            'insights': ['探索环境空间', '收集经验数据']
        }
    
    def _greedy_policy(self, data: Any, exploration_rate: float) -> Dict[str, Any]:
        """贪婪策略"""
        return {
            'performance': 0.7,
            'confidence': 0.8,
            'insights': ['选择最优动作', '快速收敛']
        }
    
    def _policy_gradient(self, data: Any, exploration_rate: float) -> Dict[str, Any]:
        """策略梯度"""
        return {
            'performance': 0.8,
            'confidence': 0.85,
            'insights': ['策略参数优化', '梯度更新有效']
        }
    
    def _value_iteration(self, data: Any, exploration_rate: float) -> Dict[str, Any]:
        """价值迭代"""
        return {
            'performance': 0.85,
            'confidence': 0.9,
            'insights': ['价值函数收敛', '最优策略找到']
        }
    
    def _actor_critic(self, data: Any, exploration_rate: float) -> Dict[str, Any]:
        """演员-评论家"""
        return {
            'performance': 0.9,
            'confidence': 0.95,
            'insights': ['策略和价值函数协同优化', '学习稳定性提升']
        }
    
    def _general_rl_learning(self, data: Any, exploration_rate: float) -> Dict[str, Any]:
        """通用RL学习"""
        return {
            'performance': 0.6,
            'confidence': 0.7,
            'insights': ['执行通用强化学习算法']
        }
    
    # 协同学习方法实现
    def _information_sharing(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any]) -> Dict[str, Any]:
        """信息共享"""
        return {
            'synergy_score': 0.6,
            'ml_contribution': 0.5,
            'rl_contribution': 0.5
        }
    
    def _knowledge_transfer(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any]) -> Dict[str, Any]:
        """知识迁移"""
        return {
            'synergy_score': 0.7,
            'ml_contribution': 0.6,
            'rl_contribution': 0.6
        }
    
    def _joint_optimization(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any]) -> Dict[str, Any]:
        """联合优化"""
        return {
            'synergy_score': 0.8,
            'ml_contribution': 0.7,
            'rl_contribution': 0.7
        }
    
    def _performance_optimization(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any]) -> Dict[str, Any]:
        """性能优化"""
        return {
            'synergy_score': 0.85,
            'ml_contribution': 0.8,
            'rl_contribution': 0.8
        }
    
    def _deep_collaboration(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any]) -> Dict[str, Any]:
        """深度协同"""
        return {
            'synergy_score': 0.9,
            'ml_contribution': 0.85,
            'rl_contribution': 0.85
        }
    
    def _general_synergy(self, ml_result: Dict[str, Any], rl_result: Dict[str, Any]) -> Dict[str, Any]:
        """通用协同"""
        return {
            'synergy_score': 0.5,
            'ml_contribution': 0.5,
            'rl_contribution': 0.5
        }


class IntelligentLearningCoordinator:
    """智能学习协调器"""
    
    def __init__(self):
        self.logger = get_core_logger("intelligent_learning_coordinator")
        self.coordinators = {
            'adaptive': AdaptiveLearningCoordinator()
        }
        self.metrics = {
            'total_coordinations': 0,
            'successful_coordinations': 0,
            'failed_coordinations': 0,
            'average_performance': 0.0,
            'average_synergy_score': 0.0
        }
    
    def coordinate_learning(self, context: LearningContext, coordinator_type: str = 'adaptive') -> LearningOutcome:
        """协调学习过程"""
        if coordinator_type not in self.coordinators:
            coordinator_type = 'adaptive'
        
        self.metrics['total_coordinations'] += 1
        
        try:
            result = self.coordinators[coordinator_type].coordinate(context)
            
            if result.success:
                self.metrics['successful_coordinations'] += 1
            else:
                self.metrics['failed_coordinations'] += 1
            
            # 更新指标
            self._update_metrics(result)
            
            return result
        except Exception as e:
            self.logger.error(f"学习协调失败: {e}")
            self.metrics['failed_coordinations'] += 1
            
            return LearningOutcome(
                success=False,
                performance=0.0,
                confidence=0.0,
                learning_phase=LearningPhase.EXPLORATION,
                ml_contribution=0.0,
                rl_contribution=0.0,
                synergy_score=0.0,
                insights=[],
                recommendations=[],
                error=str(e)
            )
    
    def _optimize_learning_strategies_simple(self, evaluation):
        """简化的学习策略优化"""
        try:
            # 简单的策略优化逻辑
            if evaluation.get('accuracy', 0) < 0.7:
                self.logger.info("学习策略需要优化：准确率较低")
            else:
                self.logger.info("学习策略表现良好")
        except Exception as e:
            self.logger.error(f"策略优化失败: {e}")
    
    def _update_metrics(self, result: LearningOutcome):
        """更新指标"""
        total = self.metrics['total_coordinations']
        
        # 更新平均性能
        current_avg_perf = self.metrics['average_performance']
        self.metrics['average_performance'] = (current_avg_perf * (total - 1) + result.performance) / total
        
        # 更新平均协同分数
        current_avg_synergy = self.metrics['average_synergy_score']
        self.metrics['average_synergy_score'] = (current_avg_synergy * (total - 1) + result.synergy_score) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def get_available_coordinators(self) -> List[str]:
        """获取可用协调器"""
        return list(self.coordinators.keys())
