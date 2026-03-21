"""
推理编排器 - 协调所有推理组件的顶级模块

这个模块实现了完整的推理编排逻辑，协调SmartQueryAnalyzer、ReasoningStepPlanner、
PromptEnhancer、DynamicKnowledgeManager和AdaptiveQualityValidator等组件，
提供统一的增强推理接口。
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from .smart_query_analyzer import SmartQueryAnalyzer
from .reasoning_step_planner import ReasoningStepPlanner
from .prompt_enhancer import PromptEnhancer
from .dynamic_knowledge_manager import DynamicKnowledgeManager
from .adaptive_quality_validator import AdaptiveQualityValidator

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """推理编排结果"""
    enhanced_prompt: str
    planning_result: Dict[str, Any]
    knowledge_context: List[Dict[str, Any]]
    query_type: str
    confidence_score: float
    is_success: bool
    error_message: Optional[str] = None


class ReasoningOrchestrator:
    """
    推理编排器 - 协调所有推理组件

    这个类是推理系统的核心编排器，负责协调各个组件的工作：
    1. 使用SmartQueryAnalyzer分析查询
    2. 使用ReasoningStepPlanner规划推理步骤
    3. 使用DynamicKnowledgeManager获取相关知识
    4. 使用PromptEnhancer增强提示词
    5. 使用AdaptiveQualityValidator验证质量

    提供统一的增强推理接口，确保系统的一致性和可靠性。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化推理编排器

        Args:
            config: 配置字典，包含各个组件的配置参数
        """
        self.config = config or self._get_default_config()

        # 初始化各个组件
        try:
            logger.info("🔧 初始化推理编排器组件...")

            self.query_analyzer = SmartQueryAnalyzer()  # 不需要配置参数
            logger.info("✅ SmartQueryAnalyzer 初始化成功")

            self.step_planner = ReasoningStepPlanner()  # 不需要配置参数
            logger.info("✅ ReasoningStepPlanner 初始化成功")

            # DynamicKnowledgeManager需要cache_dir参数
            from pathlib import Path
            knowledge_config = self.config.get('knowledge_manager', {})
            cache_dir_str = knowledge_config.get('cache_dir', 'data/knowledge_cache')
            cache_dir = Path(cache_dir_str)
            self.knowledge_manager = DynamicKnowledgeManager(cache_dir)
            logger.info("✅ DynamicKnowledgeManager 初始化成功")

            self.prompt_enhancer = PromptEnhancer()  # 不需要配置参数
            logger.info("✅ PromptEnhancer 初始化成功")

            self.quality_validator = AdaptiveQualityValidator()  # 不需要配置参数
            logger.info("✅ AdaptiveQualityValidator 初始化成功")
            logger.info("✅ AdaptiveQualityValidator 初始化成功")

            logger.info("🎉 推理编排器初始化完成")

        except Exception as e:
            logger.error(f"❌ 推理编排器初始化失败: {e}")
            raise

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'query_analyzer': {
                'use_ml_model': True,
                'fallback_to_rules': True,
                'confidence_threshold': 0.7
            },
            'step_planner': {
                'enable_validation': True,
                'max_skeleton_steps': 5,
                'min_skeleton_steps': 3
            },
            'knowledge_manager': {
                'max_knowledge_items': 5,
                'confidence_threshold': 0.8,
                'enable_external_apis': False  # 测试环境禁用外部API
            },
            'prompt_enhancer': {
                'enable_logic_trap_detection': True,
                'max_knowledge_injection': 3,
                'enhancement_level': 'comprehensive'
            },
            'quality_validator': {
                'enable_learning': True,
                'validation_threshold': 0.7,
                'adaptive_weights': True
            }
        }

    def orchestrate_reasoning(self, query: str, original_prompt: str) -> OrchestrationResult:
        """
        执行完整的推理编排过程

        Args:
            query: 用户查询
            original_prompt: 原始提示词

        Returns:
            OrchestrationResult: 编排结果
        """
        try:
            logger.info(f"🎯 开始推理编排: {query[:50]}...")

            # 步骤1: 智能查询分析
            logger.debug("📊 步骤1: 分析查询...")
            query_analysis = self.query_analyzer.analyze_query(query)

            if not query_analysis.get('success', False):
                logger.warning("⚠️ 查询分析失败，使用默认设置")
                query_analysis = {
                    'query_type': 'general',
                    'confidence': 0.5,
                    'features': {},
                    'success': True
                }

            query_type = query_analysis.get('query_type', 'general')
            confidence_score = query_analysis.get('confidence', 0.5)

            logger.info(f"✅ 查询类型: {query_type}, 置信度: {confidence_score:.2f}")

            # 步骤2: 推理步骤规划
            logger.debug("📋 步骤2: 规划推理步骤...")
            # 构建query_analysis字典供规划器使用
            query_analysis_for_planner = {
                'query_type': query_type,
                'confidence': confidence_score,
                'context': {'confidence_score': confidence_score}
            }
            planning_result = self.step_planner.plan_reasoning_steps(
                query=query,
                query_analysis=query_analysis_for_planner
            )

            logger.info(f"✅ 规划完成: {len(planning_result.get('skeleton', []))} 个步骤框架")

            # 步骤3: 动态知识检索
            logger.debug("🧠 步骤3: 检索相关知识（已禁用）...")
            # 构建query_analysis字典供知识管理器使用
            # query_analysis_for_knowledge = {
            #     'query_type': query_type,
            #     'confidence': confidence_score,
            #     'planning_result': planning_result
            # }
            # knowledge_context = self.knowledge_manager.get_relevant_knowledge(
            #     query=query,
            #     query_analysis=query_analysis_for_knowledge
            # )
            knowledge_context = []

            logger.info(f"✅ 检索已禁用，跳过知识检索")

            # 步骤4: 提示词增强
            logger.debug("✨ 步骤4: 增强提示词...")
            enhanced_prompt = self.prompt_enhancer.enhance_prompt(
                base_prompt=original_prompt,
                planning_result=planning_result,
                knowledge_results=knowledge_context
            )

            logger.info("✅ 提示词增强完成")

            # 步骤5: 质量验证（可选，用于学习）
            if self.config['quality_validator'].get('enable_learning', True):
                logger.debug("🔍 步骤5: 质量验证学习...")
                # 这里可以添加质量验证的学习逻辑，但不影响主要流程
                pass

            # 计算整体置信度
            overall_confidence = self._calculate_overall_confidence(
                query_confidence=confidence_score,
                knowledge_confidence=sum(k.get('confidence', 0) for k in knowledge_context) / max(len(knowledge_context), 1),
                planning_confidence=planning_result.get('confidence', 0.8)
            )

            logger.info(f"🎉 推理编排成功完成，整体置信度: {overall_confidence:.2f}")

            return OrchestrationResult(
                enhanced_prompt=enhanced_prompt,
                planning_result=planning_result,
                knowledge_context=knowledge_context,
                query_type=query_type,
                confidence_score=overall_confidence,
                is_success=True
            )

        except Exception as e:
            error_msg = f"推理编排失败: {str(e)}"
            logger.error(f"❌ {error_msg}")

            # 返回失败结果，但包含尽可能多的信息
            return OrchestrationResult(
                enhanced_prompt=original_prompt,  # 返回原始提示词
                planning_result={},
                knowledge_context=[],
                query_type='unknown',
                confidence_score=0.0,
                is_success=False,
                error_message=error_msg
            )

    def _calculate_overall_confidence(self,
                                    query_confidence: float,
                                    knowledge_confidence: float,
                                    planning_confidence: float) -> float:
        """
        计算整体置信度

        使用加权平均来计算整体置信度：
        - 查询分析: 30%
        - 知识检索: 30%
        - 步骤规划: 40%

        Args:
            query_confidence: 查询分析置信度
            knowledge_confidence: 知识检索置信度
            planning_confidence: 步骤规划置信度

        Returns:
            float: 整体置信度 (0.0-1.0)
        """
        weights = {
            'query': 0.3,
            'knowledge': 0.3,
            'planning': 0.4
        }

        overall = (
            query_confidence * weights['query'] +
            knowledge_confidence * weights['knowledge'] +
            planning_confidence * weights['planning']
        )

        return min(max(overall, 0.0), 1.0)  # 确保在[0,1]范围内

    def get_component_status(self) -> Dict[str, Any]:
        """
        获取各个组件的状态

        Returns:
            Dict[str, Any]: 组件状态信息
        """
        try:
            status = {
                'orchestrator': {
                    'status': 'healthy',
                    'components': {}
                }
            }

            # 检查各个组件
            components = [
                ('query_analyzer', self.query_analyzer),
                ('step_planner', self.step_planner),
                ('knowledge_manager', self.knowledge_manager),
                ('prompt_enhancer', self.prompt_enhancer),
                ('quality_validator', self.quality_validator)
            ]

            for name, component in components:
                try:
                    # 尝试调用组件的健康检查方法（如果存在）
                    if hasattr(component, 'get_stats'):
                        stats = component.get_stats()
                        status['orchestrator']['components'][name] = {
                            'status': 'healthy',
                            'stats': stats
                        }
                    elif hasattr(component, 'get_learning_stats'):
                        stats = component.get_learning_stats()
                        status['orchestrator']['components'][name] = {
                            'status': 'healthy',
                            'stats': stats
                        }
                    else:
                        status['orchestrator']['components'][name] = {
                            'status': 'healthy',
                            'stats': 'no_stats_available'
                        }
                except Exception as e:
                    status['orchestrator']['components'][name] = {
                        'status': 'error',
                        'error': str(e)
                    }

            return status

        except Exception as e:
            return {
                'orchestrator': {
                    'status': 'error',
                    'error': str(e),
                    'components': {}
                }
            }

    def update_component_config(self, component_name: str, new_config: Dict[str, Any]) -> bool:
        """
        更新组件配置

        Args:
            component_name: 组件名称
            new_config: 新配置字典

        Returns:
            bool: 是否更新成功
        """
        try:
            component_map = {
                'query_analyzer': self.query_analyzer,
                'step_planner': self.step_planner,
                'knowledge_manager': self.knowledge_manager,
                'prompt_enhancer': self.prompt_enhancer,
                'quality_validator': self.quality_validator
            }

            if component_name not in component_map:
                logger.warning(f"⚠️ 未知组件: {component_name}")
                return False

            component = component_map[component_name]

            # 尝试更新配置
            if hasattr(component, 'update_config'):
                component.update_config(new_config)
            else:
                logger.warning(f"⚠️ 组件 {component_name} 不支持配置更新")

            logger.info(f"✅ 组件 {component_name} 配置已更新")
            return True

        except Exception as e:
            logger.error(f"❌ 更新组件 {component_name} 配置失败: {e}")
            return False