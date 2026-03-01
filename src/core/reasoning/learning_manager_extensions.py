"""
Learning Manager Extensions - 学习管理器扩展

扩展 LearningManager 的数据结构，支持更多参数的自适应学习：
- ML超参数 (learning_rate, epsilon, gamma, alpha)
- 上下文因子 (user_expertise_weight, task_complexity_weight)
- 性能阈值 (timeout, retry_count, max_evidence)
- 权重参数 (feature_weights, ensemble_weights)

这个模块作为 LearningManager 的扩展，可以通过以下方式使用：
    from src.core.reasoning.learning_manager_extensions import LearningManagerExtensions
    
    # 获取扩展实例
    extensions = LearningManagerExtensions(learning_manager)
    
    # 获取学习后的参数
    timeout = extensions.get_learned_timeout('factual', complexity=0.5)
    retry_count = extensions.get_learned_retry_count('factual')
    max_evidence = extensions.get_learned_max_evidence('factual', complexity_score=3)
"""
import logging
import time
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class LearningManagerExtensions:
    """LearningManager 扩展 - 提供额外的参数学习功能"""
    
    # 新增的学习数据结构
    LEARNING_DATA_SCHEMA = {
        'ml_parameters': {
            'learning_rate': {},      # {query_type: {best: 0.01, history: [...]}}
            'epsilon': {},          # 探索率
            'gamma': {},            # 折扣因子
            'alpha': {},            # 学习率(RL)
        },
        'context_factors': {
            'user_expertise_weight': {},    # 用户专业程度权重
            'task_complexity_weight': {},   # 任务复杂度权重
            'query_type_weights': {},       # 查询类型权重
        },
        'performance_thresholds': {
            'timeout': {},           # 超时阈值
            'retry_count': {},       # 重试次数
            'max_evidence': {},     # 最大证据数量
            'batch_size': {},        # 批处理大小
        },
        'weight_parameters': {
            'feature_weights': {},    # 特征权重
            'ensemble_weights': {},  # 集成权重
        }
    }
    
    def __init__(self, learning_manager):
        """
        初始化扩展
        
        Args:
            learning_manager: 现有的 LearningManager 实例
        """
        self.lm = learning_manager
        self.logger = logging.getLogger(__name__)
        
        # 确保学习数据结构已初始化
        self._ensure_schema_initialized()
    
    def _ensure_schema_initialized(self):
        """确保新的学习数据结构已初始化"""
        for category, params in self.LEARNING_DATA_SCHEMA.items():
            if category not in self.lm.learning_data:
                self.lm.learning_data[category] = {}
            for param_name in params.keys():
                if param_name not in self.lm.learning_data[category]:
                    self.lm.learning_data[category][param_name] = {}
    
    # ========== 通用方法 ==========
    
    def get_learned_parameter(
        self, 
        param_category: str, 
        param_name: str, 
        query_type: str, 
        default: float
    ) -> float:
        """
        从学习数据中获取参数值
        
        Args:
            param_category: 参数类别 (ml_parameters, context_factors, performance_thresholds, weight_parameters)
            param_name: 参数名称
            query_type: 查询类型
            default: 默认值
            
        Returns:
            学习后的参数值，如果无数据则返回默认值
        """
        try:
            if param_category not in self.lm.learning_data:
                return default
            
            category_data = self.lm.learning_data[param_category]
            if param_name not in category_data:
                return default
            
            param_data = category_data[param_name]
            if query_type not in param_data:
                return default
            
            query_data = param_data[query_type]
            usage_count = query_data.get('usage_count', 0)
            
            # 需要至少5次使用才返回学习值
            if usage_count < 5:
                return default
            
            return query_data.get('best_value', default)
            
        except Exception as e:
            self.logger.debug(f"获取学习参数失败 ({param_category}.{param_name}): {e}")
            return default
    
    def record_parameter_result(
        self,
        param_category: str,
        param_name: str,
        query_type: str,
        param_value: float,
        success: bool,
        metrics: Optional[Dict[str, Any]] = None
    ):
        """
        记录参数使用结果，用于学习优化
        
        Args:
            param_category: 参数类别
            param_name: 参数名称
            query_type: 查询类型
            param_value: 使用的参数值
            success: 是否成功
            metrics: 额外的性能指标
        """
        if not self.lm.learning_enabled:
            return
        
        try:
            # 确保数据结构存在
            if param_category not in self.lm.learning_data:
                self.lm.learning_data[param_category] = {}
            if param_name not in self.lm.learning_data[param_category]:
                self.lm.learning_data[param_category][param_name] = {}
            if query_type not in self.lm.learning_data[param_category][param_name]:
                self.lm.learning_data[param_category][param_name][query_type] = {
                    'best_value': param_value,
                    'usage_count': 0,
                    'success_count': 0,
                    'total_score': 0.0,
                    'history': []
                }
            
            param_data = self.lm.learning_data[param_category][param_name][query_type]
            
            # 计算成功得分
            success_score = 1.0 if success else 0.0
            if metrics:
                if 'score' in metrics:
                    success_score = metrics['score']
                elif 'accuracy' in metrics:
                    success_score = metrics['accuracy']
                elif 'user_satisfaction' in metrics:
                    success_score = metrics['user_satisfaction']
            
            # 更新统计
            param_data['usage_count'] = param_data.get('usage_count', 0) + 1
            if success:
                param_data['success_count'] = param_data.get('success_count', 0) + 1
            
            param_data['total_score'] = param_data.get('total_score', 0.0) + success_score
            
            # 使用指数移动平均更新最佳值
            old_best = param_data.get('best_value', param_value)
            if success:
                param_data['best_value'] = old_best * 0.7 + param_value * 0.3
            
            # 记录历史
            history_entry = {
                'value': param_value,
                'success': success,
                'score': success_score,
                'timestamp': time.time(),
                'metrics': metrics or {}
            }
            param_data['history'].append(history_entry)
            
            # 限制历史大小
            if len(param_data['history']) > 100:
                param_data['history'] = param_data['history'][-100:]
            
            # 触发保存
            if hasattr(self.lm, '_learn_count'):
                self.lm._learn_count += 1
            else:
                self.lm._learn_count = 1
            
            if self.lm._learn_count % 10 == 0:
                self.lm._save_learning_data()
                
        except Exception as e:
            self.logger.warning(f"记录参数结果失败: {e}")
    
    # ========== 便捷方法 ==========
    
    def get_learned_timeout(self, query_type: str, complexity: float = 0.5) -> float:
        """获取学习后的超时阈值"""
        default_timeout = 30.0
        if complexity > 0.7:
            default_timeout = 60.0
        elif complexity < 0.3:
            default_timeout = 15.0
        
        return self.get_learned_parameter(
            'performance_thresholds', 
            'timeout', 
            query_type, 
            default_timeout
        )
    
    def get_learned_retry_count(self, query_type: str) -> int:
        """获取学习后的重试次数"""
        default = 3
        learned = self.get_learned_parameter(
            'performance_thresholds',
            'retry_count',
            query_type,
            default
        )
        return max(1, min(5, int(learned)))
    
    def get_learned_max_evidence(self, query_type: str, complexity_score: int) -> int:
        """获取学习后的最大证据数量"""
        learned = self.get_learned_parameter(
            'performance_thresholds',
            'max_evidence',
            query_type,
            None
        )
        if learned is not None:
            return int(learned)
        
        # 如果没有学习数据，使用基于复杂度的默认值
        if complexity_score >= 4:
            return 15
        elif complexity_score >= 3:
            return 12
        elif complexity_score >= 2:
            return 8
        else:
            return 3
    
    def get_learned_learning_rate(self, query_type: str) -> float:
        """获取学习后的学习率"""
        return self.get_learned_parameter(
            'ml_parameters',
            'learning_rate',
            query_type,
            0.01
        )
    
    def get_learned_epsilon(self, query_type: str) -> float:
        """获取学习后的探索率 (epsilon)"""
        return self.get_learned_parameter(
            'ml_parameters',
            'epsilon',
            query_type,
            0.1
        )
    
    def get_learned_gamma(self, query_type: str) -> float:
        """获取学习后的折扣因子 (gamma)"""
        return self.get_learned_parameter(
            'ml_parameters',
            'gamma',
            query_type,
            0.9
        )
    
    def get_learned_alpha(self, query_type: str) -> float:
        """获取学习后的学习率 (alpha)"""
        return self.get_learned_parameter(
            'ml_parameters',
            'alpha',
            query_type,
            0.1
        )
    
    def get_learned_context_weight(self, weight_type: str, query_type: str) -> float:
        """获取学习后的上下文权重"""
        defaults = {
            'user_expertise_weight': 0.5,
            'task_complexity_weight': 0.5,
            'query_type_weights': 0.5
        }
        default = defaults.get(weight_type, 0.5)
        
        return self.get_learned_parameter(
            'context_factors',
            weight_type,
            query_type,
            default
        )
    
    def get_all_learned_params(self) -> Dict[str, Any]:
        """获取所有学习参数的摘要"""
        summary = {}
        for category, params in self.lm.learning_data.items():
            if isinstance(params, dict):
                category_summary = {}
                for param_name, query_data in params.items():
                    if isinstance(query_data, dict):
                        for query_type, data in query_data.items():
                            if isinstance(data, dict) and 'best_value' in data:
                                category_summary[f"{param_name}_{query_type}"] = {
                                    'best_value': data.get('best_value'),
                                    'usage_count': data.get('usage_count', 0),
                                    'success_rate': data.get('success_count', 0) / max(1, data.get('usage_count', 1))
                                }
                if category_summary:
                    summary[category] = category_summary
        return summary


# ========== 便捷函数 ==========

_extensions_cache: Dict[str, LearningManagerExtensions] = {}


def get_learning_extensions(learning_manager) -> LearningManagerExtensions:
    """获取 LearningManager 的扩展实例"""
    # 使用 id 作为缓存键，确保每个 LM 实例有唯一的扩展
    cache_key = id(learning_manager)
    if cache_key not in _extensions_cache:
        _extensions_cache[cache_key] = LearningManagerExtensions(learning_manager)
    return _extensions_cache[cache_key]
