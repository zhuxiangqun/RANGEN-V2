"""
学习管理器 - 管理学习数据和优化策略
"""
import logging
import time
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


class LearningManager:
    """学习管理器"""
    
    def __init__(self, learning_data_path: Optional[Path] = None, learning_enabled: bool = True):
        self.logger = logging.getLogger(__name__)
        self.learning_data_path = learning_data_path or Path("data/learning/learning_data.json")
        self.learning_data_path.parent.mkdir(parents=True, exist_ok=True)
        self.learning_enabled = learning_enabled
        self.learning_data = {
            # 现有数据结构
            'error_patterns': {},
            'success_patterns': {},
            'performance_metrics': {},
            'adaptive_weights': {},
            'query_difficulty_scores': {},
            'template_performance': {},
            'model_selection_performance': {},
            'confidence_thresholds': {},
            'reasoning_steps_optimization': {},
            'prompt_length_optimization': {},
            'retry_strategy_performance': {},
            # 新增：支持更多参数学习
            'ml_parameters': {
                'learning_rate': {},
                'epsilon': {},
                'gamma': {},
                'alpha': {},
            },
            'context_factors': {
                'user_expertise_weight': {},
                'task_complexity_weight': {},
                'query_type_weights': {},
            },
            'performance_thresholds': {
                'timeout': {},
                'retry_count': {},
                'max_evidence': {},
                'batch_size': {},
            },
            'weight_parameters': {
                'feature_weights': {},
                'ensemble_weights': {},
            }
        }
        self._load_learning_data()
    
    def _load_learning_data(self) -> None:
        """从文件加载历史学习数据"""
        try:
            if self.learning_data_path.exists():
                with open(self.learning_data_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    for key in self.learning_data.keys():
                        if key in loaded_data:
                            if isinstance(loaded_data[key], dict):
                                if isinstance(self.learning_data[key], dict):
                                    self.learning_data[key].update(loaded_data[key])
                            elif isinstance(loaded_data[key], list):
                                if isinstance(self.learning_data[key], list):
                                    self.learning_data[key].extend(loaded_data[key])
                    
                    max_patterns = 1000
                    for key in ['error_patterns', 'success_patterns']:
                        if key in self.learning_data and isinstance(self.learning_data[key], dict):
                            for query_type, patterns in self.learning_data[key].items():
                                if isinstance(patterns, list) and len(patterns) > max_patterns:
                                    self.learning_data[key][query_type] = patterns[-max_patterns:]
                    
                    error_count = sum(len(v) if isinstance(v, list) else 0 for v in self.learning_data.get('error_patterns', {}).values())
                    success_count = sum(len(v) if isinstance(v, list) else 0 for v in self.learning_data.get('success_patterns', {}).values())
                    self.logger.info(f"学习数据已从文件加载: {self.learning_data_path}")
                    self.logger.info(f"错误模式: {error_count}条, 成功模式: {success_count}条")
            else:
                self.logger.info(f"学习数据文件不存在，使用空数据: {self.learning_data_path}")
        except Exception as e:
            self.logger.warning(f"加载学习数据失败，使用空数据: {e}")
    
    def _save_learning_data(self) -> None:
        """保存学习数据到文件"""
        try:
            self.learning_data_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.learning_data_path, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
            self.logger.debug(f"学习数据已保存到: {self.learning_data_path}")
        except Exception as e:
            self.logger.warning(f"保存学习数据失败: {e}")
    
    def get_learned_confidence_threshold(self, query_type: str) -> float:
        """基于学习数据获取最优置信度阈值"""
        try:
            if 'confidence_thresholds' not in self.learning_data:
                return 0.7
            
            if query_type not in self.learning_data['confidence_thresholds']:
                return 0.7
            
            threshold_data = self.learning_data['confidence_thresholds'][query_type]
            usage_count = threshold_data.get('usage_count', 0)
            
            if usage_count < 5:
                return 0.7
            
            return threshold_data.get('best_threshold', 0.7)
            
        except Exception as e:
            self.logger.debug(f"获取学习置信度阈值失败: {e}")
            return 0.7
    
    def get_learned_reasoning_steps_count(self, query_type: str, complexity_score: float) -> Optional[int]:
        """基于学习数据获取最优推理步骤数量"""
        try:
            if 'reasoning_steps_optimization' not in self.learning_data:
                return None
            
            complexity_level = 'simple' if complexity_score < 3 else ('medium' if complexity_score < 5 else 'complex')
            key = f"{query_type}_{complexity_level}"
            
            if key not in self.learning_data['reasoning_steps_optimization']:
                return None
            
            steps_data = self.learning_data['reasoning_steps_optimization'][key]
            usage_count = steps_data.get('usage_count', 0)
            
            if usage_count < 5:
                return None
            
            return steps_data.get('best_steps_count', None)
            
        except Exception as e:
            self.logger.debug(f"获取学习推理步骤数失败: {e}")
            return None
    
    def get_learned_evidence_count(self, query_type: str, complexity_score: int) -> Optional[int]:
        """从学习数据中获取优化的证据数量配置"""
        try:
            if complexity_score >= 4:
                return 15
            elif complexity_score >= 3:
                return 12
            elif complexity_score >= 2:
                return 8
            else:
                return 3
        except Exception as e:
            self.logger.debug(f"获取学习证据数量失败: {e}")
            return None
    
    def get_learned_parameter(
        self, 
        param_category: str, 
        param_name: str, 
        query_type: str, 
        default: float
    ) -> float:
        """从学习数据中获取参数值"""
        try:
            if param_category not in self.learning_data:
                return default
            
            category_data = self.learning_data[param_category]
            if param_name not in category_data:
                return default
            
            param_data = category_data[param_name]
            if query_type not in param_data:
                return default
            
            query_data = param_data[query_type]
            usage_count = query_data.get('usage_count', 0)
            
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
        """记录参数使用结果，用于学习优化"""
        if not self.learning_enabled:
            return
        
        try:
            if param_category not in self.learning_data:
                self.learning_data[param_category] = {}
            
            if param_name not in self.learning_data[param_category]:
                self.learning_data[param_category][param_name] = {}
            
            if query_type not in self.learning_data[param_category][param_name]:
                self.learning_data[param_category][param_name][query_type] = {
                    'best_value': param_value,
                    'usage_count': 0,
                    'success_count': 0,
                    'total_score': 0.0,
                    'history': []
                }
            
            param_data = self.learning_data[param_category][param_name][query_type]
            
            success_score = 1.0 if success else 0.0
            if metrics:
                if 'score' in metrics:
                    success_score = metrics['score']
                elif 'accuracy' in metrics:
                    success_score = metrics['accuracy']
                elif 'user_satisfaction' in metrics:
                    success_score = metrics['user_satisfaction']
            
            param_data['usage_count'] = param_data.get('usage_count', 0) + 1
            if success:
                param_data['success_count'] = param_data.get('success_count', 0) + 1
            
            param_data['total_score'] = param_data.get('total_score', 0.0) + success_score
            
            old_best = param_data.get('best_value', param_value)
            if success:
                param_data['best_value'] = old_best * 0.7 + param_value * 0.3
            
            history_entry = {
                'value': param_value,
                'success': success,
                'score': success_score,
                'timestamp': time.time(),
                'metrics': metrics or {}
            }
            param_data['history'].append(history_entry)
            
            if len(param_data['history']) > 100:
                param_data['history'] = param_data['history'][-100:]
            
            if hasattr(self, '_learn_count'):
                self._learn_count += 1
            else:
                self._learn_count = 1
            
            if self._learn_count % 10 == 0:
                self._save_learning_data()
                
        except Exception as e:
            self.logger.warning(f"记录参数结果失败: {e}")
    
    def get_learned_timeout(self, query_type: str, complexity: float = 0.5) -> float:
        """获取学习后的超时阈值"""
        default_timeout = 30.0
        if complexity > 0.7:
            default_timeout = 60.0
        elif complexity < 0.3:
            default_timeout = 15.0
        
        return self.get_learned_parameter('performance_thresholds', 'timeout', query_type, default_timeout)
    
    def get_learned_retry_count(self, query_type: str) -> int:
        """获取学习后的重试次数"""
        default = 3
        learned = self.get_learned_parameter('performance_thresholds', 'retry_count', query_type, default)
        return max(1, min(5, int(learned)))
    
    def get_learned_max_evidence(self, query_type: str, complexity_score: int) -> int:
        """获取学习后的最大证据数量"""
        learned = self.get_learned_parameter('performance_thresholds', 'max_evidence', query_type, None)
        if learned is not None:
            return int(learned)
        
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
        return self.get_learned_parameter('ml_parameters', 'learning_rate', query_type, 0.01)
    
    def get_learned_epsilon(self, query_type: str) -> float:
        """获取学习后的探索率 (epsilon)"""
        return self.get_learned_parameter('ml_parameters', 'epsilon', query_type, 0.1)
    
    def get_learned_context_weight(self, weight_type: str, query_type: str) -> float:
        """获取学习后的上下文权重"""
        defaults = {'user_expertise_weight': 0.5, 'task_complexity_weight': 0.5, 'query_type_weights': 0.5}
        return self.get_learned_parameter('context_factors', weight_type, query_type, defaults.get(weight_type, 0.5))
    
    def get_all_learned_params(self) -> Dict[str, Any]:
        """获取所有学习参数的摘要"""
        summary = {}
        for category, params in self.learning_data.items():
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
