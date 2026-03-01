"""
统一动态阈值管理器
整合所有动态阈值相关方法
"""

import logging
import time
from typing import Dict, Any, Optional, List

from src.core.unified_parameter_learner import get_parameter_learner

import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class UnifiedThresholdManager:
    """统一动态阈值管理器"""

    def __init__(self):
        self.threshold_cache = {}
        self.threshold_history = []
        self.performance_metrics = {}
        self.logger = logging.getLogger(__name__)
        self.parameter_learner = get_parameter_learner()

        self.threshold_cache = {}
        self.threshold_history = []
        self.performance_metrics = {}
        self.logger = logging.getLogger(__name__)

    def get_thresholds(self, agent_name: str, default_thresholds: Dict[str, float]) -> Dict[str, float]:
        """获取Agent的批量阈值配置
        
        Args:
            agent_name: Agent名称
            default_thresholds: 默认阈值字典 {name: value}
            
        Returns:
            阈值配置字典
        """
        results = {}
        for key, default_value in default_thresholds.items():
            # 尝试获取特定阈值，如果没有则使用默认值
            # context包含agent_name，以便将来可以针对特定Agent调整
            context = {'agent_name': agent_name}
            results[key] = self.get_dynamic_threshold(key, context, default_value)
        return results

    def get_dynamic_threshold(self, threshold_type: str, context: Optional[Dict[str, Any]] = None,
    default_value: float = 0.7) -> float:
        """
        统一的动态阈值获取方法

        Args:
            threshold_type: 阈值类型 (confidence, complexity, quality, accuracy, completeness, clarity, relevance)
            context: 上下文信息
            default_value: 默认值

        Returns:
            动态阈值
        """
        try:
            # 验证输入
            if not self._validate_threshold_type(threshold_type):
                return default_value
            
            cache_key = f"{threshold_type}_{hash(str(context)) if context else 'default'}"
            if cache_key in self.threshold_cache:
                return self.threshold_cache[cache_key]

            # 获取基础阈值
            # 先尝试从学习系统获取学习到的阈值
            query_type = context.get('query_type', 'default') if context else 'default'
            learned_threshold = self.parameter_learner.get_best_threshold(query_type)
            if learned_threshold and learned_threshold != 0.7:  # 0.7 is default, not learned
                threshold = learned_threshold
            else:
                threshold = self._get_default_threshold(threshold_type)

            # 根据上下文调整阈值

            threshold = self._get_default_threshold(threshold_type)

            # 根据上下文调整阈值
            if context:
                threshold = self._adjust_threshold_for_context(threshold_type, threshold, context)

            # 缓存结果
            self.threshold_cache[cache_key] = threshold

            return threshold

        except Exception as e:
            logger.warning(f"获取动态阈值失败 {threshold_type}: {e}")
            return default_value
    
    def _validate_threshold_type(self, threshold_type: str) -> bool:
        """验证阈值类型"""
        valid_types = [
            'confidence', 'complexity', 'quality', 'accuracy', 
            'completeness', 'clarity', 'relevance', 'performance',
            'efficiency', 'reliability', 'stability', 'similarity',
            # 🚀 新增：支持更多阈值类型
            'answer_validation',  # 答案验证置信度阈值
            'evidence_relevance',  # 证据相关性阈值
            'diversity_ratio',  # 多样性比率阈值
            'overlap_ratio',  # 重叠比率阈值
            'context_confidence',  # 上下文置信度阈值
            'prompt_confidence',  # 提示词置信度阈值
            'success_rate',  # 成功率阈值
            'evidence_count',  # 证据数量阈值（用于复杂度评估）
        ]
        return threshold_type in valid_types
    
    def _adjust_threshold_for_context(self, threshold_type: str, base_threshold: float, context: Dict[str, Any]) -> float:
        """根据上下文调整阈值"""
        try:
            adjusted_threshold = base_threshold
            
            # 根据上下文类型调整
            if 'user_experience_level' in context:
                level = context['user_experience_level']
                if level == 'beginner':
                    adjusted_threshold *= 0.8  # 降低阈值，更容易满足
                elif level == 'expert':
                    adjusted_threshold *= 1.2  # 提高阈值，更严格
            
            # 根据任务复杂度调整
            if 'task_complexity' in context:
                complexity = context['task_complexity']
                if complexity == 'simple':
                    adjusted_threshold *= 0.9  # 简单任务，降低阈值（更宽松）
                elif complexity == 'complex':
                    adjusted_threshold *= 1.1  # 复杂任务，提高阈值（更严格）
            
            # 🚀 新增：根据查询类型调整相似度阈值
            if threshold_type == 'similarity' and 'query_type' in context:
                query_type = context['query_type']
                if query_type == 'numerical':
                    # 数字查询需要精确匹配，提高阈值
                    adjusted_threshold = max(0.5, adjusted_threshold * 1.2)
                elif query_type == 'factual':
                    # 事实查询（人名、地名）需要精确匹配，提高阈值
                    adjusted_threshold = max(0.5, adjusted_threshold * 1.1)
                elif query_type == 'general':
                    # 一般查询可以接受语义相似，保持或降低阈值
                    adjusted_threshold = min(0.4, adjusted_threshold * 0.95)
            
            # 🆕 根据embedding模型类型调整相似度阈值
            # 本地模型的向量空间可能与Jina不同，相似度分数可能略低，需要更宽松的阈值
            if threshold_type == 'similarity' and 'embedding_model' in context:
                model_type = context['embedding_model']
                if model_type == 'local' or model_type == 'all-mpnet-base-v2':
                    # 本地模型：使用更宽松的阈值（降低约17%）
                    adjusted_threshold = adjusted_threshold * 0.83  # 约等于从0.3降到0.25
                elif model_type == 'jina' or model_type == 'jina-v2':
                    # Jina模型：保持原有阈值
                    pass  # 不调整
            
            # 🚀 新增：根据答案类型调整答案验证阈值
            if threshold_type == 'answer_validation':
                if 'answer_type' in context:
                    answer_type = context['answer_type']
                    if answer_type == 'numerical':
                        adjusted_threshold = 0.1  # 数字答案，阈值最低
                    elif answer_type == 'very_short':
                        adjusted_threshold = 0.15  # 极短答案
                    elif answer_type == 'short':
                        adjusted_threshold = 0.2  # 短答案
                    else:
                        adjusted_threshold = 0.3  # 一般答案
                # 根据查询类型进一步调整
                if 'query_type' in context:
                    query_type = context['query_type']
                    if query_type == 'numerical':
                        adjusted_threshold *= 0.9  # 数字查询，稍微降低阈值
                    elif query_type == 'complex':
                        adjusted_threshold *= 1.1  # 复杂查询，稍微提高阈值
            
            # 🚀 新增：根据证据质量调整证据相关性阈值
            if threshold_type == 'evidence_relevance':
                if 'query_type' in context:
                    query_type = context['query_type']
                    if query_type == 'complex':
                        adjusted_threshold *= 0.9  # 复杂查询，稍微降低阈值（接受更多证据）
                    elif query_type == 'simple':
                        adjusted_threshold *= 1.1  # 简单查询，稍微提高阈值（更严格）
                if 'task_complexity' in context:
                    complexity = context['task_complexity']
                    if complexity == 'complex':
                        # 复杂任务，相关性阈值可以稍微降低（0.5）
                        adjusted_threshold = min(adjusted_threshold, 0.5)
                    elif complexity == 'medium':
                        # 中等任务，相关性阈值（0.7）
                        adjusted_threshold = min(adjusted_threshold, 0.7)
            
            # 🚀 新增：根据上下文调整多样性比率阈值
            if threshold_type == 'diversity_ratio':
                if 'task_complexity' in context:
                    complexity = context['task_complexity']
                    if complexity == 'complex':
                        adjusted_threshold *= 1.1  # 复杂任务，需要更高多样性
                    elif complexity == 'simple':
                        adjusted_threshold *= 0.9  # 简单任务，多样性要求可以降低
            
            # 🚀 新增：根据上下文调整重叠比率阈值
            if threshold_type == 'overlap_ratio':
                if 'query_type' in context:
                    query_type = context['query_type']
                    if query_type == 'factual':
                        adjusted_threshold *= 1.2  # 事实查询，重叠度可以更高
                    elif query_type == 'complex':
                        adjusted_threshold *= 0.8  # 复杂查询，重叠度要求降低
            
            # 根据时间压力调整
            if 'time_pressure' in context:
                pressure = context['time_pressure']
                if pressure == 'high':
                    adjusted_threshold *= 0.85  # 降低阈值，快速响应
                elif pressure == 'low':
                    adjusted_threshold *= 1.05  # 提高阈值，追求质量
            
            # 确保阈值在合理范围内
            return max(0.1, min(1.0, adjusted_threshold))
            
        except Exception as e:
            self.logger.warning(f"调整阈值失败: {e}")
            return base_threshold

    def _get_default_threshold(self, threshold_type: str) -> float:
        """获取默认阈值"""
        defaults = {
            "confidence": 0.7,
            "similarity": 0.3,  # 🚀 优化：答案匹配使用更宽松的阈值（0.3而非0.8）
            "quality": 0.6,
            "relevance": 0.75,
            "accuracy": 0.85,
            # 🚀 新增：更多阈值类型的默认值
            "answer_validation": 0.2,  # 答案验证置信度阈值（默认值，会根据答案类型调整）
            "evidence_relevance": 0.6,  # 证据相关性阈值（默认值）
            "diversity_ratio": 0.65,  # 多样性比率阈值（默认值）
            "overlap_ratio": 0.2,  # 重叠比率阈值（默认值）
            "context_confidence": 0.7,  # 上下文置信度阈值
            "prompt_confidence": 0.65,  # 提示词置信度阈值（默认值）
            "success_rate": 0.7,  # 成功率阈值
            "evidence_count": 7,  # 证据数量阈值（用于复杂度评估，默认7个）
        }
        return defaults.get(threshold_type, 0.5)

    
    def _record_threshold_usage(self, threshold_type: str, threshold: float, context: Optional[Dict[str, Any]]):
        """记录阈值使用情况"""
        try:
            self.threshold_history.append({
                'threshold_type': threshold_type,
                'threshold': threshold,
                'context': context,
                'timestamp': time.time()
            })
            
            # 只保留最近1000条记录
            if len(self.threshold_history) > 1000:
                self.threshold_history = self.threshold_history[-1000:]
                
        except Exception as e:
            self.logger.warning(f"记录阈值使用情况失败: {e}")
    
    def get_threshold_statistics(self) -> Dict[str, Any]:
        """获取阈值统计信息"""
        try:
            if not self.threshold_history:
                return {
                    'total_usage': 0,
                    'threshold_types': {},
                    'average_thresholds': {},
                    'cache_size': len(self.threshold_cache)
                }
            
            # 统计阈值类型使用次数
            type_counts = {}
            type_thresholds = {}
            
            for record in self.threshold_history:
                threshold_type = record['threshold_type']
                threshold = record['threshold']
                
                if threshold_type not in type_counts:
                    type_counts[threshold_type] = 0
                    type_thresholds[threshold_type] = []
                
                type_counts[threshold_type] += 1
                type_thresholds[threshold_type].append(threshold)
            
            # 计算平均阈值
            average_thresholds = {}
            for threshold_type, thresholds in type_thresholds.items():
                average_thresholds[threshold_type] = sum(thresholds) / len(thresholds)
            
            return {
                'total_usage': len(self.threshold_history),
                'threshold_types': type_counts,
                'average_thresholds': average_thresholds,
                'cache_size': len(self.threshold_cache)
            }
            
        except Exception as e:
            self.logger.error(f"获取阈值统计信息失败: {e}")
            return {'error': str(e)}
    

    def get_confidence_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取置信度阈值"""
        return self.get_dynamic_threshold("confidence", context, 0.7)

    def get_complexity_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取复杂度阈值"""
        return self.get_dynamic_threshold("complexity", context, 0.5)

    def get_quality_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取质量阈值"""
        return self.get_dynamic_threshold("quality", context, 0.6)

    def get_accuracy_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取准确度阈值"""
        return self.get_dynamic_threshold("accuracy", context, 0.8)

    def get_completeness_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取完整性阈值"""
        return self.get_dynamic_threshold("completeness", context, 0.7)

    def get_clarity_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取清晰度阈值"""
        return self.get_dynamic_threshold("clarity", context, 0.6)

    def get_relevance_threshold(self, context: Optional[Dict[str, Any]] = None) -> float:
        """获取相关性阈值"""
        return self.get_dynamic_threshold("relevance", context, 0.7)

    def clear_cache(self):
        """清除缓存"""
        self.threshold_cache.clear()

_unified_threshold_manager = None

def get_unified_threshold_manager() -> UnifiedThresholdManager:
    """获取统一阈值管理器实例"""
    global _unified_threshold_manager
    if _unified_threshold_manager is None:
        _unified_threshold_manager = UnifiedThresholdManager()
    return _unified_threshold_manager

def get_dynamic_threshold(threshold_type: str, context: Optional[Dict[str, Any]] = None,
    default_value: float = 0.7) -> float:
    """兼容性函数 - 获取动态阈值"""
    return get_unified_threshold_manager().get_dynamic_threshold(threshold_type, context, default_value)


