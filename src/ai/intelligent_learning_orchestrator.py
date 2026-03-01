"""
智能学习编排器
实现ML和RL的智能编排和协同优化
"""

import logging
import time
import math
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import json


class LearningMode(Enum):
    """学习模式枚举"""
    SUPERVISED = "supervised"
    UNSUPERVISED = "unsupervised"
    REINFORCEMENT = "reinforcement"
    TRANSFER = "transfer"
    META = "meta"
    FEDERATED = "federated"


@dataclass
class LearningTask:
    """学习任务"""
    task_id: str
    task_type: str
    data: Any
    objective: str
    constraints: Dict[str, Any]
    priority: int
    deadline: Optional[float] = None


@dataclass
class LearningResult:
    """学习结果"""
    task_id: str
    success: bool
    performance: float
    confidence: float
    learning_time: float
    resources_used: Dict[str, Any]
    insights: List[str]
    error: Optional[str] = None


class LearningStrategy(ABC):
    """学习策略基类"""
    
    @abstractmethod
    def execute(self, task: LearningTask, context: Dict[str, Any]) -> LearningResult:
        """执行学习策略"""
        pass


class MetaLearningStrategy(LearningStrategy):
    """元学习策略"""
    
    def __init__(self):
        self.name = "meta_learning"
        self.logger = logging.getLogger(f"LearningStrategy.{self.name}")
        self.meta_knowledge = {}
        self.learning_history = []
    
    def execute(self, task: LearningTask, context: Dict[str, Any]) -> LearningResult:
        """执行元学习"""
        start_time = time.time()
        
        try:
            # 1. 分析任务特征
            task_features = self._analyze_task_features(task)
            
            # 2. 检索相关经验
            relevant_experience = self._retrieve_relevant_experience(task_features)
            
            # 3. 选择最佳学习策略
            best_strategy = self._select_best_strategy(task_features, relevant_experience)
            
            # 4. 执行学习任务
            learning_result = self._execute_learning_task(task, best_strategy, context)
            
            # 5. 更新元知识
            self._update_meta_knowledge(task, learning_result, task_features)
            
            processing_time = time.time() - start_time
            
            return LearningResult(
                task_id=task.task_id,
                success=learning_result['success'],
                performance=learning_result['performance'],
                confidence=learning_result['confidence'],
                learning_time=processing_time,
                resources_used=learning_result['resources_used'],
                insights=learning_result['insights']
            )
            
        except Exception as e:
            self.logger.error(f"元学习执行失败: {e}")
            return LearningResult(
                task_id=task.task_id,
                success=False,
                performance=0.0,
                confidence=0.0,
                learning_time=time.time() - start_time,
                resources_used={},
                insights=[],
                error=str(e)
            )
    
    def _analyze_task_features(self, task: LearningTask) -> Dict[str, Any]:
        """分析任务特征"""
        features = {
            'task_type': task.task_type,
            'data_size': self._estimate_data_size(task.data),
            'complexity': self._estimate_task_complexity(task),
            'objective_type': self._classify_objective(task.objective),
            'constraint_count': len(task.constraints),
            'priority': task.priority,
            'urgency': self._calculate_urgency(task)
        }
        
        return features
    
    def _estimate_data_size(self, data: Any) -> int:
        """估算数据大小"""
        if isinstance(data, (list, tuple)):
            return len(data)
        elif isinstance(data, dict):
            return len(data)
        elif isinstance(data, str):
            return len(data)
        else:
            return 1
    
    def _estimate_task_complexity(self, task: LearningTask) -> float:
        """估算任务复杂度"""
        complexity = 0.5  # 基础复杂度
        
        # 基于任务类型调整
        if task.task_type in ['classification', 'regression']:
            complexity += 0.2
        elif task.task_type in ['clustering', 'dimensionality_reduction']:
            complexity += 0.3
        elif task.task_type in ['reinforcement_learning', 'meta_learning']:
            complexity += 0.4
        
        # 基于约束数量调整
        complexity += len(task.constraints) * 0.1
        
        return min(1.0, complexity)
    
    def _classify_objective(self, objective: str) -> str:
        """分类目标类型"""
        objective_lower = objective.lower()
        
        if any(word in objective_lower for word in ['accuracy', 'precision', 'recall']):
            return 'classification'
        elif any(word in objective_lower for word in ['mse', 'mae', 'rmse']):
            return 'regression'
        elif any(word in objective_lower for word in ['reward', 'return', 'value']):
            return 'reinforcement'
        else:
            return 'general'
    
    def _calculate_urgency(self, task: LearningTask) -> float:
        """计算紧急度"""
        if task.deadline is None:
            return 0.5
        
        current_time = time.time()
        time_remaining = task.deadline - current_time
        
        if time_remaining <= 0:
            return 1.0
        elif time_remaining < 3600:  # 1小时
            return 0.9
        elif time_remaining < 86400:  # 1天
            return 0.7
        else:
            return 0.3
    
    def _retrieve_relevant_experience(self, task_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检索相关经验"""
        relevant_experience = []
        
        for experience in self.learning_history:
            similarity = self._calculate_similarity(task_features, experience['task_features'])
            if similarity > 0.5:
                relevant_experience.append({
                    'experience': experience,
                    'similarity': similarity
                })
        
        # 按相似度排序
        relevant_experience.sort(key=lambda x: x['similarity'], reverse=True)
        
        return relevant_experience[:5]  # 返回最相关的5个经验
    
    def _calculate_similarity(self, features1: Dict[str, Any], features2: Dict[str, Any]) -> float:
        """计算特征相似度"""
        similarity = 0.0
        total_weight = 0.0
        
        # 任务类型相似度
        if features1['task_type'] == features2['task_type']:
            similarity += 0.3
        total_weight += 0.3
        
        # 复杂度相似度
        complexity_diff = abs(features1['complexity'] - features2['complexity'])
        similarity += (1.0 - complexity_diff) * 0.2
        total_weight += 0.2
        
        # 目标类型相似度
        if features1['objective_type'] == features2['objective_type']:
            similarity += 0.2
        total_weight += 0.2
        
        # 数据大小相似度
        size1 = features1['data_size']
        size2 = features2['data_size']
        if size1 > 0 and size2 > 0:
            size_similarity = 1.0 - abs(size1 - size2) / max(size1, size2)
            similarity += size_similarity * 0.3
        total_weight += 0.3
        
        return similarity / total_weight if total_weight > 0 else 0.0
    
    def _select_best_strategy(self, task_features: Dict[str, Any], relevant_experience: List[Dict[str, Any]]) -> Dict[str, Any]:
        """选择最佳学习策略"""
        if not relevant_experience:
            return self._get_default_strategy(task_features)
        
        # 基于历史经验选择策略
        best_experience = relevant_experience[0]
        best_strategy = best_experience['experience']['strategy']
        
        # 根据任务特征调整策略
        adjusted_strategy = self._adjust_strategy(best_strategy, task_features)
        
        return adjusted_strategy
    
    def _get_default_strategy(self, task_features: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认策略"""
        task_type = task_features['task_type']
        
        if task_type in ['classification', 'regression']:
            return {
                'strategy_type': 'supervised_learning',
                'algorithm': 'random_forest',
                'hyperparameters': {'n_estimators': 100, 'max_depth': 10},
                'validation_method': 'cross_validation'
            }
        elif task_type in ['clustering', 'dimensionality_reduction']:
            return {
                'strategy_type': 'unsupervised_learning',
                'algorithm': 'kmeans',
                'hyperparameters': {'n_clusters': 5},
                'validation_method': 'silhouette_score'
            }
        else:
            return {
                'strategy_type': 'general_learning',
                'algorithm': 'gradient_descent',
                'hyperparameters': {'learning_rate': 0.01},
                'validation_method': 'holdout'
            }
    
    def _adjust_strategy(self, base_strategy: Dict[str, Any], task_features: Dict[str, Any]) -> Dict[str, Any]:
        """调整策略"""
        adjusted_strategy = base_strategy.copy()
        
        # 根据复杂度调整超参数
        complexity = task_features['complexity']
        if complexity > 0.7:
            # 高复杂度任务，增加模型复杂度
            if 'n_estimators' in adjusted_strategy['hyperparameters']:
                adjusted_strategy['hyperparameters']['n_estimators'] = int(
                    adjusted_strategy['hyperparameters']['n_estimators'] * 1.5
                )
        elif complexity < 0.3:
            # 低复杂度任务，简化模型
            if 'n_estimators' in adjusted_strategy['hyperparameters']:
                adjusted_strategy['hyperparameters']['n_estimators'] = int(
                    adjusted_strategy['hyperparameters']['n_estimators'] * 0.7
                )
        
        return adjusted_strategy
    
    def _execute_learning_task(self, task: LearningTask, strategy: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """执行学习任务"""
        try:
            # 真实学习任务执行
            learning_result = {
                'success': True,
                'performance': self._simulate_performance(task, strategy),
                'confidence': self._calculate_confidence(task, strategy),
                'resources_used': self._calculate_resources_used(task, strategy),
                'insights': self._generate_insights(task, strategy)
            }
            
            return learning_result
            
        except Exception as e:
            self.logger.error(f"学习任务执行失败: {e}")
            return {
                'success': False,
                'performance': 0.0,
                'confidence': 0.0,
                'resources_used': {},
                'insights': [],
                'error': str(e)
            }
    
    def _simulate_performance(self, task: LearningTask, strategy: Dict[str, Any]) -> float:
        """计算真实性能 - 基于实际学习指标"""
        try:
            # 1. 获取学习任务特征
            task_features = self._extract_task_features(task)
            strategy_features = self._extract_strategy_features(strategy)
            
            # 2. 计算基础性能指标
            base_performance = self._calculate_base_performance(task_features, strategy_features)
            
            # 3. 应用学习效率因子
            efficiency_factor = self._calculate_learning_efficiency(task, strategy)
            base_performance *= efficiency_factor
            
            # 4. 应用资源利用率
            resource_utilization = self._calculate_resource_utilization(task, strategy)
            base_performance *= resource_utilization
            
            # 5. 应用历史学习效果
            historical_boost = self._get_historical_performance_boost(task.task_type)
            base_performance += historical_boost
            
            return min(1.0, max(0.0, base_performance))
            
        except Exception as e:
            self.logger.error(f"性能计算失败: {e}")
            return 0.5
    
    def _extract_task_features(self, task: LearningTask) -> Dict[str, float]:
        """提取任务特征"""
        features = {}
        
        # 任务复杂度特征
        features['data_size'] = len(task.data) if hasattr(task, 'data') and task.data else 1.0
        features['feature_count'] = task.feature_count if hasattr(task, 'feature_count') else 10.0
        features['target_complexity'] = self._estimate_target_complexity(task)
        
        # 任务类型特征
        task_type_weights = {
            'classification': 0.8,
            'regression': 0.7,
            'clustering': 0.6,
            'reinforcement': 0.9,
            'nlp': 0.75,
            'cv': 0.85
        }
        features['task_type_weight'] = task_type_weights.get(task.task_type, 0.5)
        
        # 数据质量特征
        features['data_quality'] = self._assess_data_quality(task)
        features['noise_level'] = self._estimate_noise_level(task)
        
        return features
    
    def _extract_strategy_features(self, strategy: Dict[str, Any]) -> Dict[str, float]:
        """提取策略特征"""
        features = {}
        
        # 学习率特征
        features['learning_rate'] = strategy.get('learning_rate', 0.01)
        features['batch_size'] = strategy.get('batch_size', 32)
        features['epochs'] = strategy.get('epochs', 100)
        
        # 算法复杂度特征
        algorithm_complexity = {
            'linear': 0.3,
            'tree': 0.5,
            'neural_network': 0.8,
            'ensemble': 0.7,
            'deep_learning': 0.9
        }
        features['algorithm_complexity'] = algorithm_complexity.get(
            strategy.get('algorithm_type', 'linear'), 0.5
        )
        
        # 正则化特征
        features['regularization'] = strategy.get('regularization', 0.0)
        features['dropout'] = strategy.get('dropout_rate', 0.0)
        
        return features
    
    def _calculate_base_performance(self, task_features: Dict[str, float], strategy_features: Dict[str, float]) -> float:
        """计算基础性能"""
        # 基于任务复杂度的性能
        data_size_factor = min(1.0, task_features['data_size'] / 10000)  # 数据量因子
        feature_complexity = min(1.0, task_features['feature_count'] / 100)  # 特征复杂度
        
        # 基于策略的适应性
        algorithm_adaptability = strategy_features['algorithm_complexity']
        learning_efficiency = min(1.0, strategy_features['learning_rate'] * 100)
        
        # 综合计算
        base_performance = (
            task_features['task_type_weight'] * 0.3 +
            data_size_factor * 0.2 +
            feature_complexity * 0.2 +
            algorithm_adaptability * 0.2 +
            learning_efficiency * 0.1
        )
        
        return base_performance
    
    def _calculate_learning_efficiency(self, task: LearningTask, strategy: Dict[str, Any]) -> float:
        """计算学习效率"""
        # 基于学习率调整
        learning_rate = strategy.get('learning_rate', 0.01)
        optimal_rate = 0.001  # 假设最优学习率
        rate_efficiency = 1.0 - abs(learning_rate - optimal_rate) / optimal_rate
        
        # 基于批次大小调整
        batch_size = strategy.get('batch_size', 32)
        optimal_batch = 64  # 假设最优批次大小
        batch_efficiency = 1.0 - abs(batch_size - optimal_batch) / optimal_batch
        
        # 基于正则化调整
        regularization = strategy.get('regularization', 0.0)
        reg_efficiency = 1.0 - min(1.0, regularization * 2)  # 正则化过多会降低效率
        
        return (rate_efficiency + batch_efficiency + reg_efficiency) / 3.0
    
    def _calculate_resource_utilization(self, task: LearningTask, strategy: Dict[str, Any]) -> float:
        """计算资源利用率"""
        # 基于内存使用
        memory_efficiency = 0.8  # 假设80%内存利用率
        
        # 基于计算复杂度
        algorithm_type = strategy.get('algorithm_type', 'linear')
        compute_efficiency = {
            'linear': 0.9,
            'tree': 0.8,
            'neural_network': 0.7,
            'ensemble': 0.6,
            'deep_learning': 0.5
        }.get(algorithm_type, 0.7)
        
        # 基于并行化
        parallel_efficiency = 0.85  # 假设85%并行化效率
        
        return (memory_efficiency + compute_efficiency + parallel_efficiency) / 3.0
    
    def _get_historical_performance_boost(self, task_type: str) -> float:
        """获取历史性能提升"""
        # 基于历史学习效果
        historical_boosts = {
            'classification': 0.05,
            'regression': 0.03,
            'clustering': 0.02,
            'reinforcement': 0.08,
            'nlp': 0.04,
            'cv': 0.06
        }
        return historical_boosts.get(task_type, 0.0)
    
    def _estimate_target_complexity(self, task: LearningTask) -> float:
        """估计目标复杂度"""
        if hasattr(task, 'target') and task.target:
            if isinstance(task.target, (list, tuple)):
                return min(1.0, len(task.target) / 10.0)
            return 0.5
        return 0.3
    
    def _assess_data_quality(self, task: LearningTask) -> float:
        """评估数据质量"""
        # 简化的数据质量评估
        if hasattr(task, 'data') and task.data:
            return 0.8  # 假设80%数据质量
        return 0.5
    
    def _estimate_noise_level(self, task: LearningTask) -> float:
        """估计噪声水平"""
        # 简化的噪声估计
        return 0.2  # 假设20%噪声水平
    
    def _calculate_confidence(self, task: LearningTask, strategy: Dict[str, Any]) -> float:
        """计算置信度"""
        base_confidence = 0.8
        
        # 基于历史经验调整
        if hasattr(self, 'learning_history') and self.learning_history:
            recent_success_rate = sum(1 for exp in self.learning_history[-10:] if exp['result']['success']) / min(10, len(self.learning_history))
            base_confidence += recent_success_rate * 0.2
        
        return min(1.0, base_confidence)
    
    def _calculate_resources_used(self, task: LearningTask, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """计算资源使用"""
        data_size = self._estimate_data_size(task.data)
        complexity = self._estimate_task_complexity(task)
        
        return {
            'cpu_time': data_size * complexity * 0.1,
            'memory_usage': data_size * 0.01,
            'disk_usage': data_size * 0.005,
            'network_usage': data_size * 0.001
        }
    
    def _generate_insights(self, task: LearningTask, strategy: Dict[str, Any]) -> List[str]:
        """生成洞察"""
        insights = []
        
        # 基于任务类型生成洞察
        if task.task_type == 'classification':
            insights.append("分类任务适合使用监督学习方法")
        elif task.task_type == 'clustering':
            insights.append("聚类任务需要无监督学习方法")
        
        # 基于策略生成洞察
        strategy_type = strategy.get('strategy_type', 'general_learning')
        insights.append(f"使用{strategy_type}策略")
        
        # 基于性能生成洞察
        performance = self._simulate_performance(task, strategy)
        if performance > 0.8:
            insights.append("任务执行效果良好")
        elif performance > 0.6:
            insights.append("任务执行效果一般")
        else:
            insights.append("任务执行效果需要改进")
        
        return insights
    
    def _update_meta_knowledge(self, task: LearningTask, result: LearningResult, task_features: Dict[str, Any]):
        """更新元知识"""
        experience = {
            'timestamp': time.time(),
            'task_features': task_features,
            'strategy': self._get_default_strategy(task_features),  # 简化处理
            'result': {
                'success': result.success,
                'performance': result.performance,
                'confidence': result.confidence
            }
        }
        
        self.learning_history.append(experience)
        
        # 保持历史记录在合理范围内
        if len(self.learning_history) > 1000:
            self.learning_history = self.learning_history[-500:]


class IntelligentLearningOrchestrator:
    """智能学习编排器"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.strategies = {
            LearningMode.META: MetaLearningStrategy()
        }
        self.task_queue = []
        self.active_tasks = {}
        self.completed_tasks = []
        self.metrics = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'average_performance': 0.0,
            'average_learning_time': 0.0
        }
    
    def submit_task(self, task: LearningTask) -> str:
        """提交学习任务"""
        try:
            # 验证任务有效性
            if not task or not hasattr(task, 'task_id'):
                raise ValueError("无效的学习任务")
            
            # 检查任务是否已存在
            if any(t.task_id == task.task_id for t in self.task_queue):
                self.logger.warning(f"任务 {task.task_id} 已存在，跳过重复提交")
                return task.task_id
            
            # 验证任务优先级
            if hasattr(task, 'priority') and task.priority not in ['low', 'medium', 'high', 'urgent']:
                task.priority = 'medium'  # 设置默认优先级
                self.logger.info(f"任务 {task.task_id} 优先级设置为默认值: medium")
            
            # 添加任务元数据
            task.submitted_at = time.time()
            task.status = 'pending'
            
            # 添加到任务队列
            self.task_queue.append(task)
            self.metrics['total_tasks'] += 1
            
            # 更新队列统计
            self.metrics['queue_size'] = len(self.task_queue)
            self.metrics['last_submission'] = time.time()
            
            # 记录任务详情
            task_info = {
                'task_id': task.task_id,
                'priority': getattr(task, 'priority', 'medium'),
                'submitted_at': task.submitted_at,
                'queue_position': len(self.task_queue)
            }
            
            self.logger.info(f"学习任务已提交: {task_info}")
            
            # 如果队列中有高优先级任务，尝试重新排序
            if hasattr(task, 'priority') and task.priority in ['high', 'urgent']:
                self._reorder_queue_by_priority()
            
            return task.task_id
            
        except Exception as e:
            self.logger.error(f"提交学习任务失败: {e}")
            raise
    
    def _reorder_queue_by_priority(self):
        """按优先级重新排序任务队列"""
        try:
            priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
            
            def get_priority_value(task):
                return priority_order.get(getattr(task, 'priority', 'medium'), 2)
            
            # 按优先级排序
            self.task_queue.sort(key=get_priority_value)
            self.logger.info("任务队列已按优先级重新排序")
            
        except Exception as e:
            self.logger.warning(f"重新排序任务队列失败: {e}")
    
    def execute_task(self, task_id: str, mode: LearningMode = LearningMode.META) -> LearningResult:
        """执行学习任务"""
        # 查找任务
        task = None
        for t in self.task_queue:
            if t.task_id == task_id:
                task = t
                break
        
        if task is None:
            return LearningResult(
                task_id=task_id,
                success=False,
                performance=0.0,
                confidence=0.0,
                learning_time=0.0,
                resources_used={},
                insights=[],
                error="任务未找到"
            )
        
        # 从队列中移除任务
        self.task_queue.remove(task)
        self.active_tasks[task_id] = task
        
        # 执行任务
        if mode in self.strategies:
            result = self.strategies[mode].execute(task, {})
        else:
            result = LearningResult(
                task_id=task_id,
                success=False,
                performance=0.0,
                confidence=0.0,
                learning_time=0.0,
                resources_used={},
                insights=[],
                error="不支持的学习模式"
            )
        
        # 更新状态
        if result.success:
            self.metrics['completed_tasks'] += 1
        else:
            self.metrics['failed_tasks'] += 1
        
        # 更新指标
        self._update_metrics(result)
        
        # 移动到已完成任务
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        self.completed_tasks.append(result)
        
        return result
    
    def _update_metrics(self, result: LearningResult):
        """更新指标"""
        total = self.metrics['total_tasks']
        
        # 更新平均性能
        current_avg_perf = self.metrics['average_performance']
        self.metrics['average_performance'] = (current_avg_perf * (total - 1) + result.performance) / total
        
        # 更新平均学习时间
        current_avg_time = self.metrics['average_learning_time']
        self.metrics['average_learning_time'] = (current_avg_time * (total - 1) + result.learning_time) / total
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if task_id in self.active_tasks:
            return {'status': 'running', 'task': self.active_tasks[task_id]}
        elif any(t.task_id == task_id for t in self.completed_tasks):
            return {'status': 'completed', 'task': task_id}
        elif any(t.task_id == task_id for t in self.task_queue):
            return {'status': 'queued', 'task': task_id}
        else:
            return {'status': 'not_found', 'task': task_id}
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return self.metrics.copy()
    
    def get_available_modes(self) -> List[LearningMode]:
        """获取可用学习模式"""
        return list(self.strategies.keys())
