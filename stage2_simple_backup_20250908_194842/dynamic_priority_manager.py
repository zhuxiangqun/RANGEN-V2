"""
动态优先级管理系统
实现真正的智能优先级调整，基于上下文、用户行为和系统性能动态调整优先级
"""

import logging
import time
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import random
from collections import defaultdict, deque

# 智能配置系统导入
from src.utils.smart_config_system import get_smart_config, create_query_context

logger = logging.getLogger(__name__)

@dataclass
class PriorityContext:
    """优先级上下文"""
    task_type: str
    user_level: str
    urgency_level: str
    complexity: float
    resource_availability: float
    historical_success_rate: float
    user_preference_weight: float
    system_load: float
    time_of_day: float = config.DEFAULT_ONE_VALUEconfig.DEFAULT_TWO_VALUE.config.DEFAULT_ZERO_VALUE
    day_of_week: int = config.DEFAULT_ONE_VALUE

@dataclass
class PriorityDecision:
    """优先级决策结果"""
    calculated_priority: float
    priority_level: str
    reasoning: str
    confidence: float
    adjustment_factors: Dict[str, float]
    recommended_actions: List[str]

class DynamicPriorityManager:
    """动态优先级管理器"""
    
    def __init__(self):
        self.priority_history: deque = deque(maxlen=config.DEFAULT_LIMIT0)
        self.user_behavior_patterns: Dict[str, Dict[str, Any]] = {}
        self.system_performance_metrics: Dict[str, List[float]] = {}
        self.context_weights: Dict[str, float] = {}
        self.learning_rate: float = config.DEFAULT_LOW_DECIMAL_THRESHOLD
        self.evolution_counter: int = config.DEFAULT_ZERO_VALUE
        
        # 初始化基础权重
        self._initialize_base_weights()
        
    def _initialize_base_weights(self):
        """初始化基础权重"""
        self.context_weights = {
            'task_type': config.DEFAULT_MEDIUM_THRESHOLD,
            'user_level': config.DEFAULT_ZERO_VALUE.config.DEFAULT_ONE_VALUEconfig.DEFAULT_TWO_VALUE,
            'urgency_level': config.DEFAULT_ZERO_VALUE.config.DEFAULT_MEDIUM_LIMIT,
            'complexity': config.DEFAULT_ZERO_VALUE.config.DEFAULT_SMALL_LIMIT,
            'resource_availability': config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE8,
            'historical_success_rate': config.DEFAULT_ZERO_VALUE.config.DEFAULT_SMALL_LIMIT,
            'user_preference_weight': config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE8,
            'system_load': config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE7,
            'time_of_day': config.DEFAULT_LOW_THRESHOLD,
            'day_of_week': config.DEFAULT_LOW_THRESHOLD
        }
    
    def calculate_dynamic_priority(self, context: PriorityContext) -> PriorityDecision:
        """计算动态优先级"""
        try:
            # 计算各因素的优先级贡献
            factor_scores = self._calculate_factor_scores(context)
            
            # 应用动态权重
            weighted_score = self._apply_dynamic_weights(factor_scores)
            
            # 应用上下文调整
            adjusted_score = self._apply_context_adjustments(weighted_score, context)
            
            # 确定优先级级别
            priority_level = self._determine_priority_level(adjusted_score)
            
            # 生成推理说明
            reasoning = self._generate_priority_reasoning(context, factor_scores, adjusted_score)
            
            # 计算置信度
            confidence = self._calculate_confidence(context, factor_scores)
            
            # 生成推荐行动
            recommended_actions = self._generate_recommended_actions(context, adjusted_score)
            
            # 记录决策历史
            self._record_priority_decision(context, adjusted_score, priority_level)
            
            return PriorityDecision(
                calculated_priority=adjusted_score,
                priority_level=priority_level,
                reasoning=reasoning,
                confidence=confidence,
                adjustment_factors=factor_scores,
                recommended_actions=recommended_actions
            )
            
        except Exception as e:
            logger.error(f"动态优先级计算失败: {e}")
            return PriorityDecision(
                calculated_priority=get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")),
                priority_level="medium",
                reasoning=f"优先级计算失败: {str(e)}",
                confidence=config.DEFAULT_ZERO_VALUE.config.DEFAULT_MAX_RETRIES,
                adjustment_factors={},
                recommended_actions=["使用默认优先级"]
            )
    
    def learn_from_priority_outcome(self, context: PriorityContext, assigned_priority: float, outcome: Dict[str, Any]):
        """从优先级结果中学习"""
        try:
            # 记录学习数据
            learning_entry = {
                'timestamp': time.time(),
                'context': asdict(context),
                'assigned_priority': assigned_priority,
                'outcome': outcome,
                'success': outcome.get('success', False),
                'user_satisfaction': outcome.get('user_satisfaction', config.DEFAULT_ZERO_VALUE.5),
                'completion_time': outcome.get('completion_time', config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE),
                'resource_usage': outcome.get('resource_usage', config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE)
            }
            
            self.priority_history.append(learning_entry)
            
            # 更新用户行为模式
            self._update_user_behavior_patterns(context, outcome)
            
            # 更新系统性能指标
            self._update_system_performance_metrics(context, outcome)
            
            # 调整上下文权重
            self._adjust_context_weights(context, outcome)
            
            # 定期进化
            self.evolution_counter += 1
            if self.evolution_counter % config.DEFAULT_MEDIUM_LIMIT == 0:
                self._evolve_priority_system()
            
            logger.info(f"优先级学习完成，成功率: {outcome.get('success', False)}")
            
        except Exception as e:
            logger.error(f"优先级学习失败: {e}")
    
    def adapt_to_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """适应用户偏好"""
        try:
            if user_id not in self.user_behavior_patterns:
                self.user_behavior_patterns[user_id] = {
                    'preferences': {},
                    'priority_history': [],
                    'success_patterns': [],
                    'failure_patterns': []
                }
            
            user_patterns = self.user_behavior_patterns[user_id]
            
            # 更新用户偏好
            user_patterns['preferences'].update(preferences)
            
            # 分析用户偏好对优先级的影响
            self._analyze_user_preference_impact(user_id, preferences)
            
            logger.info(f"用户偏好适应完成: {user_id}")
            
        except Exception as e:
            logger.error(f"用户偏好适应失败: {e}")
    
    def _calculate_factor_scores(self, context: PriorityContext) -> Dict[str, float]:
        """计算各因素的优先级贡献"""
        try:
            factor_scores = {}
            
            # 使用智能配置系统获取任务类型优先级
            priority_context = create_query_context(query_type="priority_config")
            task_type_scores = {
                'critical': get_smart_config("task_type_critical_score", priority_context),
                'high': get_smart_config("task_type_high_score", priority_context),
                'medium': get_smart_config("task_type_medium_score", priority_context),
                'low': get_smart_config("task_type_low_score", priority_context),
                'background': get_smart_config("task_type_background_score", priority_context)
            }
            factor_scores['task_type'] = task_type_scores.get(context.task_type, get_smart_config("task_type_default_score", priority_context))

            # 使用智能配置系统获取用户级别优先级
            user_level_scores = {
                'admin': get_smart_config("user_level_admin_score", priority_context),
                'expert': get_smart_config("user_level_expert_score", priority_context),
                'advanced': get_smart_config("user_level_advanced_score", priority_context),
                'standard': get_smart_config("user_level_standard_score", priority_context),
                'basic': get_smart_config("user_level_basic_score", priority_context)
            }
            factor_scores['user_level'] = user_level_scores.get(context.user_level, get_smart_config("user_level_default_score", priority_context))

            # 使用智能配置系统获取紧急程度优先级
            urgency_scores = {
                'immediate': get_smart_config("urgency_immediate_score", priority_context),
                'urgent': get_smart_config("urgency_urgent_score", priority_context),
                'high': get_smart_config("urgency_high_score", priority_context),
                'normal': get_smart_config("urgency_normal_score", priority_context),
                'low': get_smart_config("urgency_low_score", priority_context)
            }
            factor_scores['urgency_level'] = urgency_scores.get(context.urgency_level, get_smart_config("urgency_default_score", priority_context))
            
            # 复杂度优先级（复杂任务可能需要更多资源）
            complexity_multiplier = get_smart_config("complexity_multiplier", priority_context)
            complexity_max = get_smart_config("complexity_max", priority_context)
            factor_scores['complexity'] = min(context.complexity * complexity_multiplier, complexity_max)
            
            # 资源可用性优先级
            factor_scores['resource_availability'] = context.resource_availability
            
            # 历史成功率优先级
            factor_scores['historical_success_rate'] = context.historical_success_rate
            
            # 用户偏好权重
            factor_scores['user_preference_weight'] = context.user_preference_weight
            
            # 系统负载优先级（负载高时降低非关键任务优先级）
            # 使用智能配置系统获取系统负载参数
            system_load_min = get_smart_config("system_load_min", priority_context)
            system_load_max = get_smart_config("system_load_max", priority_context)
            system_load_multiplier = get_smart_config("system_load_multiplier", priority_context)
            factor_scores['system_load'] = max(system_load_min, system_load_max - context.system_load * system_load_multiplier)
            
            # 时间因素优先级
            factor_scores['time_of_day'] = self._calculate_time_priority(context.time_of_day)
            
            # 星期因素优先级
            factor_scores['day_of_week'] = self._calculate_day_priority(context.day_of_week)
            
            return factor_scores
            
        except Exception as e:
            logger.error(f"因素得分计算失败: {e}")
            return {key: get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")) for key in self.context_weights.keys()}
    
    def _apply_dynamic_weights(self, factor_scores: Dict[str, float]) -> float:
        """应用动态权重"""
        try:
            weighted_sum = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            total_weight = config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE
            
            # 使用智能配置系统获取默认权重
            default_weight = get_smart_config("default_weight", priority_context)
            for factor, score in factor_scores.items():
                weight = self.context_weights.get(factor, default_weight)
                weighted_sum += score * weight
                total_weight += weight
            
            if total_weight > 0:
                return weighted_sum / total_weight
            else:
                return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
                
        except Exception as e:
            logger.error(f"动态权重应用失败: {e}")
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def _apply_context_adjustments(self, base_score: float, context: PriorityContext) -> float:
        """应用上下文调整"""
        try:
            adjusted_score = base_score
            
            # 基于历史性能调整
            if context.historical_success_rate > config.DEFAULT_ZERO_VALUE.8:
                adjusted_score *= config.DEFAULT_ONE_VALUE.config.DEFAULT_ONE_VALUE  # 成功率高，提高优先级
            elif context.historical_success_rate < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                adjusted_score *= config.DEFAULT_NEAR_MAX_THRESHOLD  # 成功率低，降低优先级
            
            # 基于系统负载调整
            if context.system_load > config.DEFAULT_ZERO_VALUE.8:
                # 系统负载高时，优先处理简单任务
                if context.complexity < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                    adjusted_score *= config.DEFAULT_ONE_VALUE.config.DEFAULT_TWO_VALUE
                else:
                    adjusted_score *= config.DEFAULT_ZERO_VALUE.8
            
            # 基于资源可用性调整
            if context.resource_availability < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                # 资源不足时，优先处理资源需求低的任务
                adjusted_score *= config.DEFAULT_ZERO_VALUE.8
            
            # 基于用户级别调整
            if context.user_level in ['admin', 'expert']:
                adjusted_score *= config.DEFAULT_ONE_VALUE.config.DEFAULT_ONE_VALUE
            
            # 确保分数在合理范围内
            return max(get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")), min(get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")), adjusted_score))
            
        except Exception as e:
            logger.error(f"上下文调整失败: {e}")
            return base_score
    
    def _determine_priority_level(self, score: float) -> str:
        """确定优先级级别"""
        try:
            if score >= get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold")):
                return "critical"
            elif score >= config.DEFAULT_MEDIUM_HIGH_THRESHOLD:
                return "high"
            elif score >= config.DEFAULT_MEDIUM_LOW_THRESHOLD:
                return "medium"
            elif score >= 0.2:
                return "low"
            else:
                return "background"
                
        except Exception:
            return "medium"
    
    def _generate_priority_reasoning(self, context: PriorityContext, factor_scores: Dict[str, float], final_score: float) -> str:
        """生成优先级推理说明"""
        try:
            reasoning_parts = []
            
            # 主要影响因素
            # 使用智能配置系统获取top_factors数量
            priority_context = create_query_context(query_type="priority_config")
            top_factors_count = get_smart_config("top_factors_count", priority_context)
            top_factors = sorted(factor_scores.items(), key=lambda x: x[config.DEFAULT_ONE_VALUE], reverse=True)[:top_factors_count]
            reasoning_parts.append(f"主要影响因素: {', '.join([f'{factor}({score:.config.DEFAULT_TWO_VALUEf})' for factor, score in top_factors])}")
            
            # 上下文特征
            reasoning_parts.append(f"任务类型: {context.task_type}, 用户级别: {context.user_level}, 紧急程度: {context.urgency_level}")
            
            # 系统状态
            if context.system_load > config.DEFAULT_HIGH_MEDIUM_THRESHOLD:
                reasoning_parts.append(f"系统负载较高({context.system_load:.config.DEFAULT_TWO_VALUEf})，已相应调整优先级")
            
            # 历史表现
            if context.historical_success_rate > config.DEFAULT_ZERO_VALUE.8:
                reasoning_parts.append("历史成功率较高，提升优先级")
            elif context.historical_success_rate < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                reasoning_parts.append("历史成功率较低，降低优先级")
            
            # 最终优先级
            priority_level = self._determine_priority_level(final_score)
            reasoning_parts.append(f"最终优先级: {priority_level} (得分: {final_score:.2f})")
            
            return "; ".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"优先级推理生成失败: {e}")
            return f"优先级计算完成，得分: {final_score:.2f}"
    
    def _calculate_confidence(self, context: PriorityContext, factor_scores: Dict[str, float]) -> float:
        """计算置信度"""
        try:
            # 基于历史数据量计算置信度
            history_size = len(self.priority_history)
            base_confidence = min(history_size / config.DEFAULT_LIMIT, get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
            
            # 基于因素得分的一致性计算置信度
            score_variance = np.var(list(factor_scores.values())) if factor_scores else config.DEFAULT_LOW_DECIMAL_THRESHOLD
            consistency_confidence = max(config.DEFAULT_LOW_DECIMAL_THRESHOLD, config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE - score_variance)
            
            # 基于上下文完整性计算置信度
            context_completeness = sum(1 for value in asdict(context).values() if value is not None) / len(asdict(context))
            
            # 综合置信度
            final_confidence = (base_confidence * config.DEFAULT_MEDIUM_LOW_THRESHOLD + consistency_confidence * config.DEFAULT_MEDIUM_LOW_THRESHOLD + context_completeness * 0.2)
            
            return min(final_confidence, get_smart_config("DEFAULT_ONE_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_one_value")))
            
        except Exception:
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def _generate_recommended_actions(self, context: PriorityContext, priority_score: float) -> List[str]:
        """生成推荐行动"""
        try:
            actions = []
            
            if priority_score >= config.DEFAULT_ZERO_VALUE.8:
                actions.extend([
                    "立即分配资源",
                    "通知相关团队",
                    "设置监控告警",
                    "准备回滚方案"
                ])
            elif priority_score >= config.DEFAULT_MEDIUM_HIGH_THRESHOLD:
                actions.extend([
                    "优先处理",
                    "分配必要资源",
                    "定期状态更新"
                ])
            elif priority_score >= config.DEFAULT_MEDIUM_LOW_THRESHOLD:
                actions.extend([
                    "正常处理",
                    "按计划执行"
                ])
            else:
                actions.extend([
                    "后台处理",
                    "资源空闲时执行"
                ])
            
            # 基于系统负载的特殊建议
            if context.system_load > config.DEFAULT_ZERO_VALUE.8:
                actions.append("考虑延迟非关键任务")
            
            # 基于资源可用性的建议
            if context.resource_availability < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                actions.append("等待资源释放")
            
            return actions
            
        except Exception:
            return ["按默认流程处理"]
    
    def _calculate_time_priority(self, time_of_day: float) -> float:
        """计算时间优先级"""
        try:
            # 工作时间优先级较高
            if config.DEFAULT_EIGHT_VALUE <= time_of_day <= 18:
                return get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))
            elif config.DEFAULT_SIX_VALUE <= time_of_day <= 22:
                return config.DEFAULT_MEDIUM_HIGH_THRESHOLD
            else:
                return config.DEFAULT_LOW_MEDIUM_THRESHOLD
                
        except Exception:
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def _calculate_day_priority(self, day_of_week: int) -> float:
        """计算星期优先级"""
        try:
            # 工作日优先级较高
            if config.DEFAULT_ONE_VALUE <= day_of_week <= 5:  # 周一到周五
                return get_smart_config("high_threshold", {"config_type": "auto"}, create_query_context(query_type="high_threshold"))
            elif day_of_week == 6:  # 周六
                return config.DEFAULT_MEDIUM_HIGH_THRESHOLD
            else:  # 周日
                return config.DEFAULT_MEDIUM_LOW_THRESHOLD
                
        except Exception:
            return get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))
    
    def _update_user_behavior_patterns(self, context: PriorityContext, outcome: Dict[str, Any]):
        """更新用户行为模式"""
        try:
            user_level = context.user_level
            
            if user_level not in self.user_behavior_patterns:
                self.user_behavior_patterns[user_level] = {
                    'priority_preferences': {},
                    'success_patterns': [],
                    'failure_patterns': [],
                    'average_satisfaction': config.DEFAULT_ZERO_VALUE.5
                }
            
            user_patterns = self.user_behavior_patterns[user_level]
            
            # 更新优先级偏好
            task_type = context.task_type
            if task_type not in user_patterns['priority_preferences']:
                user_patterns['priority_preferences'][task_type] = []
            
            user_patterns['priority_preferences'][task_type].append({
                'priority': outcome.get('assigned_priority', config.DEFAULT_ZERO_VALUE.5),
                'satisfaction': outcome.get('user_satisfaction', config.DEFAULT_ZERO_VALUE.5),
                'timestamp': time.time()
            })
            
            # 更新成功/失败模式
            if outcome.get('success', False):
                user_patterns['success_patterns'].append({
                    'task_type': task_type,
                    'complexity': context.complexity,
                    'urgency': context.urgency_level
                })
            else:
                user_patterns['failure_patterns'].append({
                    'task_type': task_type,
                    'complexity': context.complexity,
                    'urgency': context.urgency_level
                })
            
            # 更新平均满意度
            satisfaction = outcome.get('user_satisfaction', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold")))
            current_avg = user_patterns['average_satisfaction']
            pattern_count = len(user_patterns['success_patterns']) + len(user_patterns['failure_patterns'])
            user_patterns['average_satisfaction'] = (current_avg * (pattern_count - 1) + satisfaction) / pattern_count
            
        except Exception as e:
            logger.error(f"用户行为模式更新失败: {e}")
    
    def _update_system_performance_metrics(self, context: PriorityContext, outcome: Dict[str, Any]):
        """更新系统性能指标"""
        try:
            task_type = context.task_type
            
            if task_type not in self.system_performance_metrics:
                self.system_performance_metrics[task_type] = []
            
            # 记录性能指标
            performance_metric = {
                'completion_time': outcome.get('completion_time', config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE),
                'resource_usage': outcome.get('resource_usage', config.DEFAULT_ZERO_VALUE.config.DEFAULT_ZERO_VALUE),
                'success': outcome.get('success', False),
                'timestamp': time.time()
            }
            
            self.system_performance_metrics[task_type].append(performance_metric)
            
            # 限制历史记录数量
            if len(self.system_performance_metrics[task_type]) > config.DEFAULT_LIMIT:
                self.system_performance_metrics[task_type] = self.system_performance_metrics[task_type][-50:]
                
        except Exception as e:
            logger.error(f"系统性能指标更新失败: {e}")
    
    def _adjust_context_weights(self, context: PriorityContext, outcome: Dict[str, Any]):
        """调整上下文权重"""
        try:
            success = outcome.get('success', False)
            satisfaction = outcome.get('user_satisfaction', config.DEFAULT_ZERO_VALUE.5)
            
            # 基于结果调整权重
            if success and satisfaction > config.DEFAULT_HIGH_MEDIUM_THRESHOLD:
                # 成功且满意度高，增加相关因素权重
                self._increase_relevant_weights(context)
            elif not success or satisfaction < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                # 失败或满意度低，减少相关因素权重
                self._decrease_relevant_weights(context)
            
            # 归一化权重
            self._normalize_weights()
            
        except Exception as e:
            logger.error(f"上下文权重调整失败: {e}")
    
    def _increase_relevant_weights(self, context: PriorityContext):
        """增加相关因素权重"""
        try:
            # 使用智能配置系统获取权重调整因子
            weight_context = create_query_context(query_type="weight_adjustment")
            high_increase_factor = get_smart_config("high_increase_factor", weight_context)
            medium_increase_factor = get_smart_config("medium_increase_factor", weight_context)
            high_complexity_threshold = get_smart_config("high_complexity_threshold", weight_context)

            # 根据任务类型增加相关权重
            if context.task_type == 'critical':
                self.context_weights['urgency_level'] *= high_increase_factor
                self.context_weights['user_level'] *= medium_increase_factor

            # 根据用户级别增加相关权重
            if context.user_level in ['admin', 'expert']:
                self.context_weights['user_level'] *= high_increase_factor
                self.context_weights['user_preference_weight'] *= medium_increase_factor

            # 根据复杂度增加相关权重
            if context.complexity > high_complexity_threshold:
                self.context_weights['complexity'] *= high_increase_factor
                self.context_weights['resource_availability'] *= medium_increase_factor
                
        except Exception as e:
            logger.error(f"权重增加失败: {e}")
    
    def _decrease_relevant_weights(self, context: PriorityContext):
        """减少相关因素权重"""
        try:
            # 根据任务类型减少相关权重
            if context.task_type == 'background':
                self.context_weights['urgency_level'] *= config.DEFAULT_HIGH_THRESHOLD
                self.context_weights['user_level'] *= 0.97
            
            # 根据用户级别减少相关权重
            if context.user_level == 'basic':
                self.context_weights['user_level'] *= config.DEFAULT_HIGH_THRESHOLD
                self.context_weights['user_preference_weight'] *= 0.97
            
            # 根据复杂度减少相关权重
            if context.complexity < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                self.context_weights['complexity'] *= config.DEFAULT_HIGH_THRESHOLD
                self.context_weights['resource_availability'] *= config.DEFAULT_ZERO_VALUE.97
                
        except Exception as e:
            logger.error(f"权重减少失败: {e}")
    
    def _normalize_weights(self):
        """归一化权重"""
        try:
            total_weight = sum(self.context_weights.values())
            if total_weight > config.DEFAULT_ZERO_VALUE:
                for key in self.context_weights:
                    self.context_weights[key] /= total_weight
                    
        except Exception as e:
            logger.error(f"权重归一化失败: {e}")
    
    def _evolve_priority_system(self):
        """进化优先级系统"""
        try:
            # 分析历史数据
            success_patterns = self._analyze_success_patterns()
            failure_patterns = self._analyze_failure_patterns()
            
            # 基于成功模式调整权重
            for pattern in success_patterns:
                self._apply_success_pattern_adjustment(pattern)
            
            # 基于失败模式调整权重
            for pattern in failure_patterns:
                self._apply_failure_pattern_adjustment(pattern)
            
            # 生成新的优先级规则
            new_rules = self._generate_new_priority_rules(success_patterns)
            
            logger.info(f"优先级系统进化完成，识别到 {len(success_patterns)} 个成功模式，{len(failure_patterns)} 个失败模式")
            
        except Exception as e:
            logger.error(f"优先级系统进化失败: {e}")
    
    def _analyze_success_patterns(self) -> List[Dict[str, Any]]:
        """分析成功模式"""
        try:
            success_patterns = []
            
            for entry in self.priority_history:
                if entry.get('success', False) and entry.get('user_satisfaction', config.DEFAULT_ZERO_VALUE) > config.DEFAULT_HIGH_MEDIUM_THRESHOLD:
                    context = entry.get('context', {})
                    pattern = {
                        'task_type': context.get('task_type'),
                        'user_level': context.get('user_level'),
                        'urgency_level': context.get('urgency_level'),
                        'complexity_range': [context.get('complexity', config.DEFAULT_ZERO_VALUE.5) - config.DEFAULT_LOW_DECIMAL_THRESHOLD, context.get('complexity', config.DEFAULT_ZERO_VALUE.5) + config.DEFAULT_LOW_DECIMAL_THRESHOLD],
                        'frequency': config.DEFAULT_ONE_VALUE
                    }
                    
                    # 查找相似模式
                    found = False
                    for existing in success_patterns:
                        if (existing['task_type'] == pattern['task_type'] and 
                            existing['user_level'] == pattern['user_level'] and
                            existing['urgency_level'] == pattern['urgency_level']):
                            existing['frequency'] += config.DEFAULT_ONE_VALUE
                            found = True
                            break
                    
                    if not found:
                        success_patterns.append(pattern)
            
            return success_patterns
            
        except Exception as e:
            logger.error(f"成功模式分析失败: {e}")
            return []
    
    def _analyze_failure_patterns(self) -> List[Dict[str, Any]]:
        """分析失败模式"""
        try:
            failure_patterns = []
            
            for entry in self.priority_history:
                if not entry.get('success', True) or entry.get('user_satisfaction', config.DEFAULT_ONE_VALUE) < config.DEFAULT_LOW_MEDIUM_THRESHOLD:
                    context = entry.get('context', {})
                    pattern = {
                        'task_type': context.get('task_type'),
                        'user_level': context.get('user_level'),
                        'urgency_level': context.get('urgency_level'),
                        'complexity_range': [context.get('complexity', config.DEFAULT_ZERO_VALUE.5) - config.DEFAULT_LOW_DECIMAL_THRESHOLD, context.get('complexity', config.DEFAULT_ZERO_VALUE.5) + config.DEFAULT_LOW_DECIMAL_THRESHOLD],
                        'frequency': config.DEFAULT_ONE_VALUE
                    }
                    
                    # 查找相似模式
                    found = False
                    for existing in failure_patterns:
                        if (existing['task_type'] == pattern['task_type'] and 
                            existing['user_level'] == pattern['user_level'] and
                            existing['urgency_level'] == pattern['urgency_level']):
                            existing['frequency'] += config.DEFAULT_ONE_VALUE
                            found = True
                            break
                    
                    if not found:
                        failure_patterns.append(pattern)
            
            return failure_patterns
            
        except Exception as e:
            logger.error(f"失败模式分析失败: {e}")
            return []
    
    def _apply_success_pattern_adjustment(self, pattern: Dict[str, Any]):
        """应用成功模式调整"""
        try:
            if pattern['frequency'] > 3:  # 频繁成功模式
                # 增加相关权重
                if pattern['task_type'] == 'critical':
                    self.context_weights['urgency_level'] *= 1.02
                if pattern['user_level'] in ['admin', 'expert']:
                    self.context_weights['user_level'] *= config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUEconfig.DEFAULT_TWO_VALUE
                    
        except Exception as e:
            logger.error(f"成功模式调整失败: {e}")
    
    def _apply_failure_pattern_adjustment(self, pattern: Dict[str, Any]):
        """应用失败模式调整"""
        try:
            if pattern['frequency'] > 3:  # 频繁失败模式
                # 减少相关权重
                if pattern['task_type'] == 'background':
                    self.context_weights['urgency_level'] *= 0.98
                if pattern['user_level'] == 'basic':
                    self.context_weights['user_level'] *= 0.98
                    
        except Exception as e:
            logger.error(f"失败模式调整失败: {e}")
    
    def _generate_new_priority_rules(self, success_patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成新的优先级规则"""
        try:
            new_rules = []
            
            # 基于成功模式生成新规则
            for pattern in success_patterns:
                if pattern['frequency'] > 5:  # 高频成功模式
                    rule = {
                        'condition': {
                            'task_type': pattern['task_type'],
                            'user_level': pattern['user_level'],
                            'urgency_level': pattern['urgency_level']
                        },
                        'action': 'increase_priority',
                        'factor': config.DEFAULT_ONE_VALUE.config.DEFAULT_ONE_VALUE,
                        'confidence': min(pattern['frequency'] / config.DEFAULT_SMALL_LIMIT, config.DEFAULT_ONE_VALUE.config.DEFAULT_ZERO_VALUE)
                    }
                    new_rules.append(rule)
            
            return new_rules
            
        except Exception as e:
            logger.error(f"新优先级规则生成失败: {e}")
            return []
    
    def _record_priority_decision(self, context: PriorityContext, priority_score: float, priority_level: str):
        """记录优先级决策"""
        try:
            decision_record = {
                'timestamp': time.time(),
                'context': asdict(context),
                'priority_score': priority_score,
                'priority_level': priority_level
            }
            
            # 这里可以保存到数据库或文件
            logger.debug(f"优先级决策记录: {priority_level} ({priority_score:.config.DEFAULT_TWO_VALUEf})")
            
        except Exception as e:
            logger.error(f"优先级决策记录失败: {e}")
    
    def get_priority_summary(self) -> Dict[str, Any]:
        """获取优先级摘要"""
        try:
            summary = {
                'total_decisions': len(self.priority_history),
                'average_priority_score': get_smart_config("DEFAULT_ZERO_VALUE", {"config_type": "auto"}, create_query_context(query_type="default_zero_value")),
                'priority_distribution': {},
                'user_patterns_count': len(self.user_behavior_patterns),
                'system_metrics_count': len(self.system_performance_metrics),
                'evolution_count': self.evolution_counter,
                'context_weights': self.context_weights.copy()
            }
            
            # 计算平均优先级得分
            if self.priority_history:
                scores = [entry.get('assigned_priority', get_smart_config("medium_threshold", {"config_type": "auto"}, create_query_context(query_type="medium_threshold"))) for entry in self.priority_history]
                summary['average_priority_score'] = sum(scores) / len(scores)
            
            # 计算优先级分布
            priority_levels = [entry.get('priority_level', 'medium') for entry in self.priority_history]
            for level in priority_levels:
                summary['priority_distribution'][level] = summary['priority_distribution'].get(level, 0) + 1
            
            return summary
            
        except Exception as e:
            logger.error(f"优先级摘要获取失败: {e}")
            return {}

# 全局实例
_dynamic_priority_manager = None

def get_dynamic_priority_manager():
    """获取动态优先级管理器实例"""
    global _dynamic_priority_manager
    if _dynamic_priority_manager is None:
        _dynamic_priority_manager = DynamicPriorityManager()
    return _dynamic_priority_manager
