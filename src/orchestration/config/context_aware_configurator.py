"""
上下文感知配置器

基于头条文章启示实现的智能化配置系统。
根据任务上下文动态调整智能体配置参数。
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ContextProfile:
    """上下文特征"""
    task_complexity: str  # simple, medium, complex
    time_pressure: str    # low, medium, high
    quality_requirement: str  # draft, standard, premium
    domain_expertise: str # general, specialized, expert
    user_experience: str  # novice, intermediate, expert


@dataclass
class AgentConfiguration:
    """智能体配置"""
    agent_type: str
    parameters: Dict[str, Any]
    capability_weights: Dict[str, float]
    collaboration_preferences: Dict[str, Any]


class ContextAwareConfigurator:
    """上下文感知配置器"""

    def __init__(self):
        self.configuration_templates = self._load_configuration_templates()
        self.context_history = []
        self.performance_feedback = {}
        self.learning_enabled = True

        logger.info("✅ 上下文感知配置器初始化完成")

    def generate_optimal_configuration(
        self,
        context: ContextProfile,
        agent_type: str,
        historical_performance: Dict[str, Any] = None
    ) -> AgentConfiguration:
        """生成最优配置"""
        try:
            logger.info(f"🎯 为 {agent_type} 生成上下文感知配置")
            logger.debug(f"📊 上下文特征: 复杂度={context.task_complexity}, 时间压力={context.time_pressure}, 质量要求={context.quality_requirement}")

            # 获取基础配置模板
            base_config = self.configuration_templates.get(agent_type, {}).copy()

            if not base_config:
                logger.warning(f"⚠️ 未找到 {agent_type} 的配置模板，使用默认配置")
                base_config = self._get_default_configuration(agent_type)

            # 基于上下文调整配置
            context_adjusted_config = self._adjust_for_context(base_config, context)
            logger.debug("✅ 上下文调整完成")

            # 基于历史性能优化
            if historical_performance and self.learning_enabled:
                optimized_config = self._optimize_based_on_history(
                    context_adjusted_config, historical_performance
                )
                logger.debug("✅ 历史性能优化完成")
            else:
                optimized_config = context_adjusted_config

            # 记录上下文历史
            self._record_context_history(context, agent_type, optimized_config)

            configuration = AgentConfiguration(
                agent_type=agent_type,
                parameters=optimized_config.get('parameters', {}),
                capability_weights=optimized_config.get('capability_weights', {}),
                collaboration_preferences=optimized_config.get('collaboration_preferences', {})
            )

            logger.info(f"✅ {agent_type} 配置生成完成")
            return configuration

        except Exception as e:
            logger.error(f"❌ 配置生成失败 {agent_type}: {e}")
            # 返回默认配置
            return self._get_fallback_configuration(agent_type)

    def batch_generate_configurations(
        self,
        context: ContextProfile,
        agent_types: List[str],
        historical_performance: Dict[str, Dict[str, Any]] = None
    ) -> Dict[str, AgentConfiguration]:
        """批量生成配置"""
        try:
            logger.info(f"🎯 批量生成配置: {len(agent_types)} 个智能体")

            configurations = {}
            for agent_type in agent_types:
                perf_data = historical_performance.get(agent_type) if historical_performance else None
                config = self.generate_optimal_configuration(context, agent_type, perf_data)
                configurations[agent_type] = config

            logger.info("✅ 批量配置生成完成")
            return configurations

        except Exception as e:
            logger.error(f"❌ 批量配置生成失败: {e}")
            return {}

    def update_configuration_from_feedback(
        self,
        agent_type: str,
        context: ContextProfile,
        performance_result: Dict[str, Any]
    ) -> None:
        """基于反馈更新配置模板"""
        try:
            if not self.learning_enabled:
                return

            logger.info(f"🔄 基于反馈更新 {agent_type} 配置")

            # 分析性能结果
            feedback_score = self._analyze_performance_feedback(performance_result)

            # 更新配置模板
            if agent_type in self.configuration_templates:
                self._update_template_with_feedback(
                    agent_type, context, feedback_score
                )

            # 记录性能反馈
            self._record_performance_feedback(agent_type, context, performance_result)

            logger.info(f"✅ {agent_type} 配置更新完成")

        except Exception as e:
            logger.error(f"❌ 配置反馈更新失败 {agent_type}: {e}")

    def _adjust_for_context(self, config: Dict[str, Any], context: ContextProfile) -> Dict[str, Any]:
        """基于上下文调整配置"""
        try:
            adjusted_config = config.copy()

            # 根据任务复杂度调整
            adjusted_config = self._adjust_for_task_complexity(adjusted_config, context.task_complexity)

            # 根据时间压力调整
            adjusted_config = self._adjust_for_time_pressure(adjusted_config, context.time_pressure)

            # 根据质量要求调整
            adjusted_config = self._adjust_for_quality_requirement(adjusted_config, context.quality_requirement)

            # 根据领域专业性调整
            adjusted_config = self._adjust_for_domain_expertise(adjusted_config, context.domain_expertise)

            # 根据用户经验调整
            adjusted_config = self._adjust_for_user_experience(adjusted_config, context.user_experience)

            return adjusted_config

        except Exception as e:
            logger.error(f"❌ 上下文调整失败: {e}")
            return config

    def _adjust_for_task_complexity(self, config: Dict[str, Any], complexity: str) -> Dict[str, Any]:
        """根据任务复杂度调整"""
        params = config.get('parameters', {})

        if complexity == 'complex':
            # 复杂任务：增加推理深度和知识来源
            params['reasoning_depth'] = min(
                params.get('reasoning_depth', 5) + 2, 10
            )
            params['knowledge_sources'] = max(
                params.get('knowledge_sources', 3) + 1, 5
            )
            params['verification_rounds'] = max(
                params.get('verification_rounds', 1) + 1, 3
            )

        elif complexity == 'simple':
            # 简单任务：降低复杂度设置，优化速度
            params['reasoning_depth'] = max(
                params.get('reasoning_depth', 5) - 1, 1
            )
            params['timeout'] = max(
                params.get('timeout', 30) - 10, 5
            )
            params['parallel_processing'] = True

        # 中等复杂度使用默认设置
        return config

    def _adjust_for_time_pressure(self, config: Dict[str, Any], time_pressure: str) -> Dict[str, Any]:
        """根据时间压力调整"""
        params = config.get('parameters', {})

        if time_pressure == 'high':
            # 高时间压力：减少超时时间，启用并行处理
            params['timeout'] = min(
                params.get('timeout', 30) * 0.7, 10
            )
            params['parallel_processing'] = True
            params['cache_enabled'] = True
            params['max_concurrent_requests'] = min(
                params.get('max_concurrent_requests', 2) + 1, 5
            )

        elif time_pressure == 'low':
            # 低时间压力：增加质量检查，允许更深入的处理
            params['timeout'] = params.get('timeout', 30) * 1.5
            params['verification_rounds'] = max(
                params.get('verification_rounds', 1) + 1, 2
            )
            params['quality_threshold'] = min(
                params.get('quality_threshold', 0.7) + 0.1, 0.9
            )

        # 中等时间压力使用默认设置
        return config

    def _adjust_for_quality_requirement(self, config: Dict[str, Any], quality_req: str) -> Dict[str, Any]:
        """根据质量要求调整"""
        params = config.get('parameters', {})
        weights = config.get('capability_weights', {})

        if quality_req == 'premium':
            # 高级质量：增加验证轮数，提高可靠性权重
            params['verification_rounds'] = max(
                params.get('verification_rounds', 1) + 1, 3
            )
            params['quality_threshold'] = min(
                params.get('quality_threshold', 0.7) + 0.2, 0.95
            )
            weights['reliability'] = min(
                weights.get('reliability', 0.5) + 0.2, 1.0
            )
            weights['reasoning_depth'] = min(
                weights.get('reasoning_depth', 0.2) + 0.1, 0.5
            )

        elif quality_req == 'draft':
            # 草稿质量：减少验证，优化速度
            params['verification_rounds'] = 1
            params['quality_threshold'] = max(
                params.get('quality_threshold', 0.7) - 0.2, 0.3
            )
            weights['speed'] = min(
                weights.get('speed', 0.15) + 0.2, 0.5
            )

        # 标准质量使用默认设置
        return config

    def _adjust_for_domain_expertise(self, config: Dict[str, Any], domain_expertise: str) -> Dict[str, Any]:
        """根据领域专业性调整"""
        params = config.get('parameters', {})

        if domain_expertise == 'expert':
            # 专家级：减少解释性内容，增加专业深度
            params['include_explanations'] = False
            params['technical_detail_level'] = 'expert'
            params['assume_domain_knowledge'] = True

        elif domain_expertise == 'general':
            # 通用：增加解释，降低专业深度
            params['include_explanations'] = True
            params['technical_detail_level'] = 'intermediate'
            params['assume_domain_knowledge'] = False

        # 专业级使用默认设置
        return config

    def _adjust_for_user_experience(self, config: Dict[str, Any], user_exp: str) -> Dict[str, Any]:
        """根据用户经验调整"""
        params = config.get('parameters', {})

        if user_exp == 'novice':
            # 新手用户：简化输出，增加指导性内容
            params['simplify_output'] = True
            params['include_guidance'] = True
            params['use_simple_language'] = True

        elif user_exp == 'expert':
            # 专家用户：保持原始复杂度，提供高级选项
            params['simplify_output'] = False
            params['include_technical_details'] = True
            params['provide_raw_data'] = True

        # 中级用户使用默认设置
        return config

    def _optimize_based_on_history(
        self,
        config: Dict[str, Any],
        performance_history: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于历史性能优化配置"""
        try:
            optimized_config = config.copy()

            # 分析性能模式
            success_rate = performance_history.get('success_rate', 0.8)
            avg_response_time = performance_history.get('avg_response_time', 30)
            quality_score = performance_history.get('quality_score', 0.7)

            params = optimized_config.get('parameters', {})

            # 根据成功率调整
            if success_rate < 0.7:
                # 降低复杂度设置
                params['reasoning_depth'] = max(
                    params.get('reasoning_depth', 5) - 1, 1
                )
                params['verification_rounds'] = max(
                    params.get('verification_rounds', 1) - 1, 1
                )

            elif success_rate > 0.9 and quality_score > 0.8:
                # 尝试更高复杂度设置
                params['reasoning_depth'] = min(
                    params.get('reasoning_depth', 5) + 1, 10
                )

            # 根据响应时间调整
            if avg_response_time > 60:
                # 优化性能设置
                params['parallel_processing'] = True
                params['cache_enabled'] = True
                params['timeout'] = min(params.get('timeout', 30), 45)

            elif avg_response_time < 15:
                # 可以增加质量检查
                params['verification_rounds'] = min(
                    params.get('verification_rounds', 1) + 1, 3
                )

            return optimized_config

        except Exception as e:
            logger.error(f"❌ 历史性能优化失败: {e}")
            return config

    def _analyze_performance_feedback(self, performance_result: Dict[str, Any]) -> Dict[str, float]:
        """分析性能反馈"""
        feedback_score = {
            'overall_success': 0.0,
            'quality_improvement': 0.0,
            'efficiency_gain': 0.0,
            'user_satisfaction': 0.0
        }

        # 计算各项评分
        if 'success' in performance_result:
            feedback_score['overall_success'] = 1.0 if performance_result['success'] else 0.0

        if 'quality_score' in performance_result:
            baseline_quality = 0.7  # 假设基准质量
            feedback_score['quality_improvement'] = performance_result['quality_score'] - baseline_quality

        if 'response_time' in performance_result:
            baseline_time = 30.0  # 假设基准时间
            time_ratio = baseline_time / max(performance_result['response_time'], 1)
            feedback_score['efficiency_gain'] = min(time_ratio - 1, 1.0)

        if 'user_rating' in performance_result:
            feedback_score['user_satisfaction'] = performance_result['user_rating'] / 5.0

        return feedback_score

    def _update_template_with_feedback(self, agent_type: str, context: ContextProfile,
                                     feedback_score: Dict[str, float]) -> None:
        """基于反馈更新模板"""
        try:
            template = self.configuration_templates.get(agent_type, {})
            params = template.get('parameters', {})

            # 根据反馈调整参数
            if feedback_score['overall_success'] < 0.5:
                # 成功率低，降低复杂度
                params['reasoning_depth'] = max(params.get('reasoning_depth', 5) - 1, 1)

            if feedback_score['efficiency_gain'] < -0.5:
                # 效率差，启用性能优化
                params['parallel_processing'] = True
                params['cache_enabled'] = True

            if feedback_score['quality_improvement'] > 0.2:
                # 质量提升，保持当前设置并记录成功模式
                self._record_successful_configuration(agent_type, context, template)

        except Exception as e:
            logger.error(f"❌ 更新模板失败 {agent_type}: {e}")

    def _record_successful_configuration(self, agent_type: str, context: ContextProfile,
                                       configuration: Dict[str, Any]) -> None:
        """记录成功的配置"""
        # 这里可以实现配置模式的聚类和学习
        # 暂时只记录到历史中
        success_record = {
            'agent_type': agent_type,
            'context': context,
            'configuration': configuration,
            'timestamp': datetime.now(),
            'performance_score': 1.0
        }

        # 可以存储到数据库或文件中用于后续学习
        logger.debug(f"📝 记录成功配置: {agent_type}")

    def _load_configuration_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载配置模板"""
        try:
            # 尝试从文件加载
            config_path = Path(__file__).parent / "agent_configuration_templates.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            # 使用内置模板
            return self._get_builtin_templates()

        except Exception as e:
            logger.warning(f"⚠️ 加载配置模板失败，使用内置模板: {e}")
            return self._get_builtin_templates()

    def _get_builtin_templates(self) -> Dict[str, Dict[str, Any]]:
        """获取内置配置模板"""
        return {
            'EnhancedReasoningAgent': {
                'parameters': {
                    'reasoning_depth': 5,
                    'timeout': 30,
                    'parallel_processing': False,
                    'verification_rounds': 1,
                    'quality_threshold': 0.7,
                    'include_explanations': True,
                    'cache_enabled': False
                },
                'capability_weights': {
                    'reasoning_depth': 0.8,
                    'speed': 0.6,
                    'reliability': 0.7
                },
                'collaboration_preferences': {
                    'preferred_partners': ['EnhancedKnowledgeRetrievalAgent'],
                    'collaboration_mode': 'sequential'
                }
            },
            'EnhancedKnowledgeRetrievalAgent': {
                'parameters': {
                    'max_sources': 5,
                    'search_depth': 3,
                    'timeout': 20,
                    'relevance_threshold': 0.7,
                    'include_explanations': False,
                    'cache_enabled': True
                },
                'capability_weights': {
                    'knowledge_retrieval': 0.9,
                    'speed': 0.8,
                    'reliability': 0.8
                },
                'collaboration_preferences': {
                    'preferred_partners': ['EnhancedReasoningAgent', 'FactVerificationAgent'],
                    'collaboration_mode': 'parallel'
                }
            },
            'EnhancedAnswerGenerationAgent': {
                'parameters': {
                    'creativity_level': 0.7,
                    'max_length': 1000,
                    'timeout': 25,
                    'quality_threshold': 0.75,
                    'include_explanations': True,
                    'cache_enabled': False
                },
                'capability_weights': {
                    'creativity': 0.8,
                    'reliability': 0.7,
                    'speed': 0.6
                },
                'collaboration_preferences': {
                    'preferred_partners': ['EnhancedCitationAgent'],
                    'collaboration_mode': 'sequential'
                }
            }
        }

    def _get_default_configuration(self, agent_type: str) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'parameters': {
                'timeout': 30,
                'quality_threshold': 0.7,
                'parallel_processing': False,
                'cache_enabled': False,
                'include_explanations': True
            },
            'capability_weights': {
                'knowledge_retrieval': 0.6,
                'reasoning_depth': 0.6,
                'creativity': 0.5,
                'speed': 0.6,
                'reliability': 0.7,
                'adaptability': 0.5
            },
            'collaboration_preferences': {
                'preferred_partners': [],
                'collaboration_mode': 'sequential'
            }
        }

    def _get_fallback_configuration(self, agent_type: str) -> AgentConfiguration:
        """获取后备配置"""
        return AgentConfiguration(
            agent_type=agent_type,
            parameters={'timeout': 30, 'quality_threshold': 0.5},
            capability_weights={'reliability': 0.5, 'speed': 0.5},
            collaboration_preferences={'collaboration_mode': 'sequential'}
        )

    def _record_context_history(self, context: ContextProfile, agent_type: str,
                              configuration: Dict[str, Any]) -> None:
        """记录上下文历史"""
        history_record = {
            'timestamp': datetime.now(),
            'context': context,
            'agent_type': agent_type,
            'configuration': configuration
        }

        self.context_history.append(history_record)

        # 限制历史记录数量
        if len(self.context_history) > 1000:
            self.context_history = self.context_history[-1000:]

    def _record_performance_feedback(self, agent_type: str, context: ContextProfile,
                                   performance_result: Dict[str, Any]) -> None:
        """记录性能反馈"""
        key = f"{agent_type}_{context.task_complexity}_{context.time_pressure}"

        if key not in self.performance_feedback:
            self.performance_feedback[key] = []

        self.performance_feedback[key].append({
            'timestamp': datetime.now(),
            'performance': performance_result
        })

        # 限制每个键的历史记录
        if len(self.performance_feedback[key]) > 50:
            self.performance_feedback[key] = self.performance_feedback[key][-50:]
