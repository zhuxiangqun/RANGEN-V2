"""
统一参数学习器 - 协调所有系统的参数学习
"""
import logging
from typing import Dict, Any, Optional
from src.core.reasoning.learning_manager import LearningManager

logger = logging.getLogger(__name__)


class UnifiedParameterLearner:
    """统一参数学习器 - 协调所有系统的参数学习"""
    
    _instance: Optional['UnifiedParameterLearner'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.logger = logging.getLogger(__name__)
        self.learning_manager = LearningManager()
        self._initialized = True
        logger.info("UnifiedParameterLearner initialized")
    
    def learn_parameter(
        self,
        param_type: str,
        query_type: str,
        value: float,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录参数学习结果"""
        param_category = self._get_param_category(param_type)
        self.learning_manager.record_parameter_result(
            param_category=param_category,
            param_name=param_type,
            query_type=query_type,
            param_value=value,
            success=success,
            metrics=metrics
        )
    
    def get_parameter(self, param_type: str, query_type: str, default: float) -> float:
        """获取学习后的参数值"""
        param_category = self._get_param_category(param_type)
        return self.learning_manager.get_learned_parameter(
            param_category=param_category,
            param_name=param_type,
            query_type=query_type,
            default=default
        )
    
    def get_best_threshold(self, query_type: str) -> float:
        """获取学习后的最佳阈值"""
        return self.learning_manager.get_learned_confidence_threshold(query_type)
    
    def get_timeout(self, query_type: str, complexity: float = 0.5) -> float:
        """获取学习后的超时值"""
        return self.learning_manager.get_learned_timeout(query_type, complexity)
    
    def get_retry_count(self, query_type: str) -> int:
        """获取学习后的重试次数"""
        return self.learning_manager.get_learned_retry_count(query_type)
    
    def get_evidence_count(self, query_type: str, complexity: int) -> int:
        """获取学习后的证据数量"""
        return self.learning_manager.get_learned_max_evidence(query_type, complexity)
    
    def get_learning_rate(self, query_type: str) -> float:
        """获取学习后的学习率"""
        return self.learning_manager.get_learned_learning_rate(query_type)
    
    def get_context_weight(self, weight_type: str, query_type: str) -> float:
        """获取学习后的上下文权重"""
        return self.learning_manager.get_learned_context_weight(weight_type, query_type)
    
    def _get_param_category(self, param_type: str) -> str:
        """映射参数类型到学习数据类别"""
        mapping = {
            'timeout': 'performance_thresholds',
            'retry_count': 'performance_thresholds',
            'max_evidence': 'performance_thresholds',
            'batch_size': 'performance_thresholds',
            'learning_rate': 'ml_parameters',
            'epsilon': 'ml_parameters',
            'gamma': 'ml_parameters',
            'alpha': 'ml_parameters',
            'user_expertise_weight': 'context_factors',
            'task_complexity_weight': 'context_factors',
            'query_type_weights': 'context_factors',
            'feature_weights': 'weight_parameters',
            'ensemble_weights': 'weight_parameters',
        }
        return mapping.get(param_type, 'performance_thresholds')
    
    def get_all_learned(self) -> Dict[str, Any]:
        """获取所有学习参数摘要"""
        return self.learning_manager.get_all_learned_params()


# 全局单例
_parameter_learner: Optional[UnifiedParameterLearner] = None


def get_parameter_learner() -> UnifiedParameterLearner:
    """获取全局参数学习器实例"""
    global _parameter_learner
    if _parameter_learner is None:
        _parameter_learner = UnifiedParameterLearner()
    return _parameter_learner
