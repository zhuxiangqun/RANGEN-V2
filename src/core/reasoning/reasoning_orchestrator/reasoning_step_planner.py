"""
推理步骤规划器
根据查询类型和分析结果生成推理步骤骨架
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ReasoningStepPlanner:
    """
    推理步骤规划器 - 确保推理方向正确

    功能：
    - 根据查询类型生成推理骨架
    - 识别关键推理阶段
    - 确保推理路径的完整性
    """

    def __init__(self):
        # 查询类型处理器
        self.type_handlers = {
            'logic_trap': self._plan_logic_trap_steps,
            'factual_chain': self._plan_factual_chain_steps,
            'cross_domain': self._plan_cross_domain_steps,
            'historical_fact': self._plan_historical_fact_steps,
            'general': self._plan_general_steps
        }

        # 推理阶段模板
        self.phase_templates = {
            'premise_identification': {
                'description': '识别问题前提和关键假设',
                'required_capabilities': ['entity_extraction', 'context_analysis'],
                'step_types': ['information_retrieval', 'data_processing']
            },
            'logic_analysis': {
                'description': '分析逻辑关系和推理路径',
                'required_capabilities': ['logical_reasoning', 'pattern_recognition'],
                'step_types': ['logical_reasoning', 'evidence_gathering']
            },
            'information_gathering': {
                'description': '收集必要的信息和证据',
                'required_capabilities': ['information_retrieval', 'fact_verification'],
                'step_types': ['information_retrieval', 'evidence_gathering']
            },
            'relationship_tracing': {
                'description': '追踪实体间的关系链',
                'required_capabilities': ['entity_linking', 'relationship_analysis'],
                'step_types': ['information_retrieval', 'logical_reasoning']
            },
            'domain_integration': {
                'description': '整合跨领域的信息',
                'required_capabilities': ['domain_mapping', 'knowledge_integration'],
                'step_types': ['data_processing', 'logical_reasoning']
            },
            'conclusion_synthesis': {
                'description': '综合分析结果得出结论',
                'required_capabilities': ['answer_synthesis', 'reasoning_validation'],
                'step_types': ['answer_synthesis', 'logical_reasoning']
            }
        }

        logger.info("✅ ReasoningStepPlanner 初始化完成")

    def plan_reasoning_steps(self, query: str, query_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        规划推理步骤
        返回完整的推理规划方案
        """
        query_type = query_analysis.get('query_type', 'general')

        # 获取对应的规划器
        planner_func = self.type_handlers.get(query_type, self._plan_general_steps)

        try:
            # 生成推理骨架
            skeleton = planner_func(query, query_analysis)

            # 验证骨架完整性
            validation_result = self._validate_skeleton(skeleton, query_analysis)

            # 生成推理指导
            guidance = self._generate_reasoning_guidance(query_type, skeleton, query_analysis)

            planning_result = {
                'query_type': query_type,
                'step_skeleton': skeleton,
                'reasoning_guidance': guidance,
                'validation_result': validation_result,
                'estimated_complexity': self._estimate_complexity(skeleton),
                'confidence': query_analysis.get('confidence', 0.5)
            }

            logger.debug(f"推理步骤规划完成: {query_type}, 步骤数: {len(skeleton)}")
            return planning_result

        except Exception as e:
            logger.error(f"推理步骤规划失败: {e}")
            # 回退到通用规划
            return self._plan_fallback_steps(query, query_analysis)

    def _plan_logic_trap_steps(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划逻辑陷阱题的推理步骤"""

        skeleton = []

        # 阶段1：前提识别
        if 'capitol' in query.lower() and 'state' in query.lower():
            # D.C.不是州的问题
            skeleton.append({
                'phase': 'premise_identification',
                'description': 'Identify the location and administrative status of the US Capitol',
                'required_steps': [
                    {
                        'type': 'information_retrieval',
                        'focus': 'US Capitol location',
                        'description': 'Determine where the US Capitol is located'
                    },
                    {
                        'type': 'information_retrieval',
                        'focus': 'D.C. administrative status',
                        'description': 'Verify the administrative status of Washington D.C.'
                    }
                ]
            })

            # 阶段2：逻辑分析
            skeleton.append({
                'phase': 'logic_analysis',
                'description': 'Analyze the logical impossibility of the premise',
                'required_steps': [
                    {
                        'type': 'logical_reasoning',
                        'focus': 'premise evaluation',
                        'description': 'Evaluate whether D.C. can be considered a state'
                    },
                    {
                        'type': 'logical_reasoning',
                        'focus': 'contradiction detection',
                        'description': 'Identify the logical contradiction in the question'
                    }
                ]
            })

        elif 'dewey decimal' in query.lower():
            # Dewey Decimal转换问题
            skeleton.append({
                'phase': 'premise_identification',
                'description': 'Identify the classification system and conversion requirements',
                'required_steps': [
                    {
                        'type': 'information_retrieval',
                        'focus': 'Dewey Decimal system',
                        'description': 'Understand how Dewey Decimal classification works'
                    },
                    {
                        'type': 'information_retrieval',
                        'focus': 'book classification',
                        'description': 'Find the Dewey number for the specified book'
                    }
                ]
            })

            skeleton.append({
                'phase': 'domain_integration',
                'description': 'Convert classification number to physical measurement',
                'required_steps': [
                    {
                        'type': 'data_processing',
                        'focus': 'unit conversion',
                        'description': 'Convert Dewey number to building height'
                    }
                ]
            })

        else:
            # 通用逻辑陷阱
            skeleton.append({
                'phase': 'logic_analysis',
                'description': 'Analyze the logical structure and identify potential traps',
                'required_steps': [
                    {
                        'type': 'logical_reasoning',
                        'focus': 'premise analysis',
                        'description': 'Examine all premises in the question'
                    },
                    {
                        'type': 'logical_reasoning',
                        'focus': 'contradiction detection',
                        'description': 'Look for logical contradictions or impossibilities'
                    }
                ]
            })

        # 阶段3：结论合成
        skeleton.append({
            'phase': 'conclusion_synthesis',
            'description': 'Formulate the answer based on logical analysis',
            'required_steps': [
                {
                    'type': 'answer_synthesis',
                    'focus': 'logical conclusion',
                    'description': 'Provide the logically correct answer'
                }
            ]
        })

        return skeleton

    def _plan_factual_chain_steps(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划事实链查询的推理步骤"""

        skeleton = []

        # 分析实体数量和关系复杂度
        entity_count = analysis.get('features', {}).get('entity_indicators', 0)
        has_relationships = 'mother' in query.lower() or 'father' in query.lower() or 'wife' in query.lower()

        if has_relationships:
            # 关系链查询（如政治人物关系）
            skeleton.append({
                'phase': 'information_gathering',
                'description': 'Gather information about all entities in the relationship chain',
                'required_steps': [
                    {
                        'type': 'information_retrieval',
                        'focus': 'primary entity',
                        'description': 'Identify the main entity and its basic information'
                    },
                    {
                        'type': 'information_retrieval',
                        'focus': 'relationship chain',
                        'description': 'Trace relationships between entities'
                    }
                ]
            })

            skeleton.append({
                'phase': 'relationship_tracing',
                'description': 'Connect the relationship chain to find the required information',
                'required_steps': [
                    {
                        'type': 'logical_reasoning',
                        'focus': 'relationship linking',
                        'description': 'Link all entities through their relationships'
                    },
                    {
                        'type': 'data_processing',
                        'focus': 'information extraction',
                        'description': 'Extract the specific required information'
                    }
                ]
            })

        else:
            # 一般事实链
            skeleton.append({
                'phase': 'information_gathering',
                'description': 'Collect all necessary factual information',
                'required_steps': [
                    {
                        'type': 'information_retrieval',
                        'focus': 'key facts',
                        'description': 'Retrieve essential facts needed to answer'
                    }
                ]
            })

        # 结论阶段
        skeleton.append({
            'phase': 'conclusion_synthesis',
            'description': 'Combine facts to form the final answer',
            'required_steps': [
                {
                    'type': 'answer_synthesis',
                    'focus': 'fact synthesis',
                    'description': 'Synthesize all gathered facts into the answer'
                }
            ]
        })

        return skeleton

    def _plan_cross_domain_steps(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划跨领域查询的推理步骤"""

        skeleton = []

        # 阶段1：领域分离
        skeleton.append({
            'phase': 'information_gathering',
            'description': 'Gather information from each domain separately',
            'required_steps': [
                {
                    'type': 'information_retrieval',
                    'focus': 'domain 1 facts',
                    'description': 'Collect facts from the first domain'
                },
                {
                    'type': 'information_retrieval',
                    'focus': 'domain 2 facts',
                    'description': 'Collect facts from the second domain'
                }
            ]
        })

        # 阶段2：领域映射
        skeleton.append({
            'phase': 'domain_integration',
            'description': 'Find connections and mappings between domains',
            'required_steps': [
                {
                    'type': 'logical_reasoning',
                    'focus': 'domain mapping',
                    'description': 'Identify how to connect information from different domains'
                },
                {
                    'type': 'data_processing',
                    'focus': 'information transformation',
                    'description': 'Transform information from one domain to another'
                }
            ]
        })

        # 阶段3：综合分析
        skeleton.append({
            'phase': 'conclusion_synthesis',
            'description': 'Combine cross-domain information to answer',
            'required_steps': [
                {
                    'type': 'answer_synthesis',
                    'focus': 'integrated answer',
                    'description': 'Provide answer based on integrated domain knowledge'
                }
            ]
        })

        return skeleton

    def _plan_historical_fact_steps(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划历史事实查询的推理步骤"""

        skeleton = []

        # 历史事实通常需要时间上下文
        skeleton.append({
            'phase': 'information_gathering',
            'description': 'Gather historical facts with proper temporal context',
            'required_steps': [
                {
                    'type': 'information_retrieval',
                    'focus': 'historical facts',
                    'description': 'Find relevant historical information'
                },
                {
                    'type': 'information_retrieval',
                    'focus': 'temporal context',
                    'description': 'Verify the time period and context'
                }
            ]
        })

        skeleton.append({
            'phase': 'logic_analysis',
            'description': 'Verify historical accuracy and context',
            'required_steps': [
                {
                    'type': 'logical_reasoning',
                    'focus': 'historical verification',
                    'description': 'Ensure historical facts are accurate'
                }
            ]
        })

        skeleton.append({
            'phase': 'conclusion_synthesis',
            'description': 'Provide historically accurate answer',
            'required_steps': [
                {
                    'type': 'answer_synthesis',
                    'focus': 'historical answer',
                    'description': 'Give the correct historical answer'
                }
            ]
        })

        return skeleton

    def _plan_general_steps(self, query: str, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划通用查询的推理步骤"""

        skeleton = []

        # 通用查询的简单推理链
        skeleton.append({
            'phase': 'information_gathering',
            'description': 'Gather basic information needed to answer',
            'required_steps': [
                {
                    'type': 'information_retrieval',
                    'focus': 'basic facts',
                    'description': 'Find the fundamental facts'
                }
            ]
        })

        skeleton.append({
            'phase': 'conclusion_synthesis',
            'description': 'Formulate the answer based on facts',
            'required_steps': [
                {
                    'type': 'answer_synthesis',
                    'focus': 'direct answer',
                    'description': 'Provide the answer'
                }
            ]
        })

        return skeleton

    def _plan_fallback_steps(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """回退规划 - 当规划失败时使用"""

        logger.warning("使用回退推理规划")

        return {
            'query_type': 'general',
            'step_skeleton': self._plan_general_steps(query, analysis),
            'reasoning_guidance': 'Use standard reasoning approach',
            'validation_result': {'is_valid': False, 'issues': ['fallback_planning_used']},
            'estimated_complexity': 'medium',
            'confidence': 0.3
        }

    def _validate_skeleton(self, skeleton: List[Dict[str, Any]], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """验证推理骨架的完整性"""

        issues = []
        is_valid = True

        # 检查是否有推理阶段
        if not skeleton:
            issues.append('no_reasoning_phases')
            is_valid = False

        # 检查阶段连贯性
        phase_names = [phase.get('phase') for phase in skeleton]
        if 'conclusion_synthesis' not in phase_names:
            issues.append('missing_conclusion_phase')
            is_valid = False

        # 检查是否有信息收集阶段
        info_phases = ['information_gathering', 'premise_identification']
        if not any(phase in phase_names for phase in info_phases):
            issues.append('missing_information_gathering')
            is_valid = False

        return {
            'is_valid': is_valid,
            'issues': issues,
            'phase_count': len(skeleton),
            'phase_names': phase_names
        }

    def _generate_reasoning_guidance(self, query_type: str, skeleton: List[Dict[str, Any]],
                                   analysis: Dict[str, Any]) -> str:
        """生成推理指导"""

        guidance_parts = []

        if query_type == 'logic_trap':
            guidance_parts.append("这是一个逻辑陷阱题。关键是识别问题的前提是否成立：")
            guidance_parts.append("1. 仔细分析问题中的关键假设")
            guidance_parts.append("2. 验证这些假设是否符合现实")
            guidance_parts.append("3. 如果假设不成立，问题本身就是矛盾的")

        elif query_type == 'factual_chain':
            guidance_parts.append("这是一个事实链查询。需要追踪实体间的关系：")
            guidance_parts.append("1. 识别所有相关实体")
            guidance_parts.append("2. 确定实体间的关系链")
            guidance_parts.append("3. 沿着关系链查找所需信息")

        elif query_type == 'cross_domain':
            guidance_parts.append("这是一个跨领域查询。需要整合不同领域的信息：")
            guidance_parts.append("1. 分离不同领域的问题")
            guidance_parts.append("2. 在每个领域收集信息")
            guidance_parts.append("3. 找到领域间的连接点")

        else:
            guidance_parts.append("使用标准推理方法：")
            guidance_parts.append("1. 收集必要的信息")
            guidance_parts.append("2. 分析信息间的关系")
            guidance_parts.append("3. 得出结论")

        return "\n".join(guidance_parts)

    def _estimate_complexity(self, skeleton: List[Dict[str, Any]]) -> str:
        """估算推理复杂度"""

        phase_count = len(skeleton)
        total_steps = sum(len(phase.get('required_steps', [])) for phase in skeleton)

        if phase_count >= 4 or total_steps >= 6:
            return 'high'
        elif phase_count >= 3 or total_steps >= 4:
            return 'medium'
        else:
            return 'low'
