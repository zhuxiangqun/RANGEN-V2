"""
智能Prompt增强器
将推理骨架转换为具体的LLM指导，并注入领域知识
"""

import logging
from typing import Dict, Any, List, Optional
from src.utils.query_extraction import QueryExtractionTool

logger = logging.getLogger(__name__)

class PromptEnhancer:
    """
    智能Prompt增强器

    功能：
    - 将推理骨架转换为LLM可理解的指导
    - 注入领域特定知识
    - 生成结构化的推理提示
    """

    def __init__(self):
        """初始化提示增强器"""
        # 推理阶段到LLM指导的映射
        self.phase_guidance_templates = {
            'premise_identification': {
                'instruction': 'First, identify and verify all premises and assumptions in the question.',
                'focus': 'Look for hidden assumptions or definitions that might not be true.',
                'example': 'For questions about "states", verify what constitutes a state.'
            },
            'logic_analysis': {
                'instruction': 'Analyze the logical structure and relationships between concepts.',
                'focus': 'Check for contradictions, impossibilities, or logical fallacies.',
                'example': 'If something cannot logically exist, the answer involves impossibility.'
            },
            'information_gathering': {
                'instruction': 'Gather all necessary factual information systematically.',
                'focus': 'Collect data from reliable sources and cross-verify facts.',
                'example': 'Find exact facts, dates, names, and relationships.'
            },
            'relationship_tracing': {
                'instruction': 'Trace connections and relationships between entities.',
                'focus': 'Follow relationship chains to find the required information.',
                'example': 'Connect A→B→C to find the relationship between A and C.'
            },
            'domain_integration': {
                'instruction': 'Integrate information from different domains or fields.',
                'focus': 'Find meaningful connections between different types of knowledge.',
                'example': 'Convert information from one domain to be usable in another.'
            },
            'conclusion_synthesis': {
                'instruction': 'Synthesize all findings into a coherent final answer.',
                'focus': 'Ensure the conclusion logically follows from the evidence.',
                'example': 'Combine all verified facts to answer the original question.'
            }
        }

        # 步骤类型到具体指导的映射
        self.step_type_guidance = {
            'information_retrieval': 'Find and verify specific factual information.',
            'data_processing': 'Transform or convert data from one format to another.',
            'logical_reasoning': 'Apply logical analysis to draw conclusions.',
            'evidence_gathering': 'Collect supporting evidence for claims.',
            'answer_synthesis': 'Combine information to create the final answer.'
        }

        # 领域知识库（扩展版）
        self.domain_knowledge = self._initialize_domain_knowledge()

        logger.info("✅ PromptEnhancer 初始化完成")

    def enhance_prompt(self, base_prompt: str, planning_result: Dict[str, Any],
                      knowledge_results: Optional[List[Dict]] = None) -> str:
        """
        增强基础prompt

        Args:
            base_prompt: 原始prompt
            planning_result: 推理规划结果
            knowledge_results: 知识检索结果

        Returns:
            增强后的prompt
        """
        try:
            enhanced_parts = []

            # 1. 添加推理指导
            guidance_section = self._generate_reasoning_guidance(planning_result)
            enhanced_parts.append(guidance_section)

            # 2. 添加领域知识
            knowledge_section = self._generate_knowledge_section(planning_result, knowledge_results)
            if knowledge_section:
                enhanced_parts.append(knowledge_section)

            # 3. 添加结构化推理框架
            framework_section = self._generate_reasoning_framework(planning_result)
            enhanced_parts.append(framework_section)

            # 4. 添加查询特定的增强
            query_specific_section = self._generate_query_specific_enhancement(planning_result)
            if query_specific_section:
                enhanced_parts.append(query_specific_section)

            # 5. 原始查询
            enhanced_parts.append(f"ORIGINAL QUERY:\n{self._extract_query_from_prompt(base_prompt)}")

            # 6. 输出格式要求
            format_section = self._generate_format_requirements(planning_result)
            enhanced_parts.append(format_section)

            return "\n\n".join(enhanced_parts)

        except Exception as e:
            logger.error(f"Prompt增强失败: {e}")
            return base_prompt  # 回退到原始prompt

    def _generate_reasoning_guidance(self, planning_result: Dict[str, Any]) -> str:
        """生成推理指导部分"""
        guidance = planning_result.get('reasoning_guidance', '')

        return f"""REASONING APPROACH:
{guidance}

IMPORTANT: Follow this reasoning approach exactly. Do not skip steps or take shortcuts."""

    def _generate_knowledge_section(self, planning_result: Dict[str, Any],
                                   knowledge_results: Optional[List[Dict]] = None) -> Optional[str]:
        """生成知识注入部分"""

        knowledge_parts = []

        # 1. 从知识检索结果添加知识（二次过滤）
        if knowledge_results:
            filtered_knowledge = self._filter_relevant_knowledge(knowledge_results, planning_result)
            for knowledge in filtered_knowledge[:3]:  # 限制数量
                content = knowledge.get('content', '')
                if content:
                    knowledge_parts.append(f"- {content}")

        # 2. 从领域知识库添加相关知识
        # 🚨 禁用自动领域知识注入，防止话题漂移（特别是对于不相关的查询）
        # query_type = planning_result.get('query_type', '')
        # domain_knowledge = self._get_domain_knowledge_for_type(query_type)
        # if domain_knowledge:
        #    knowledge_parts.extend(domain_knowledge)
        
        # 仅在有非常明确的匹配时才注入（待实现）
        pass

        if not knowledge_parts:
            return None

        knowledge_text = "\n".join(knowledge_parts)
        return f"""RELEVANT KNOWLEDGE:
{knowledge_text}

Use this knowledge to inform your reasoning."""

    def _generate_reasoning_framework(self, planning_result: Dict[str, Any]) -> str:
        """生成推理框架部分"""
        skeleton = planning_result.get('step_skeleton', [])

        if not skeleton:
            return "STANDARD REASONING FRAMEWORK:\n1. Gather information\n2. Analyze relationships\n3. Draw conclusions"

        framework_parts = ["REQUIRED REASONING FRAMEWORK:"]

        for i, phase in enumerate(skeleton, 1):
            phase_name = phase.get('phase', 'unknown')
            description = phase.get('description', '')

            framework_parts.append(f"{i}. {phase_name.upper()}: {description}")

            # 添加该阶段的具体步骤
            required_steps = phase.get('required_steps', [])
            for j, step in enumerate(required_steps, 1):
                step_type = step.get('type', 'unknown')
                step_description = step.get('description', '')
                focus = step.get('focus', '')

                step_guidance = self.step_type_guidance.get(step_type, 'Perform the required analysis.')
                framework_parts.append(f"   {i}.{j} {step_type.upper()}: {step_description}")
                if focus:
                    framework_parts.append(f"      Focus: {focus}")
                framework_parts.append(f"      Guidance: {step_guidance}")

        return "\n".join(framework_parts)

    def _generate_query_specific_enhancement(self, planning_result: Dict[str, Any]) -> Optional[str]:
        """生成查询特定的增强内容"""

        query_type = planning_result.get('query_type', '')

        if query_type == 'logic_trap':
            return """LOGIC TRAP DETECTION:
- Check for impossible premises
- Verify definitions and assumptions
- If something is logically impossible, state it clearly
- Do not try to "solve" impossible problems"""

        elif query_type == 'factual_chain':
            return """RELATIONSHIP TRACING:
- Identify all entities mentioned
- Map relationships between entities
- Follow the relationship chain step by step
- Verify each connection in the chain"""

        elif query_type == 'cross_domain':
            return """CROSS-DOMAIN INTEGRATION:
- Separate information from different domains
- Find conversion methods between domains
- Apply appropriate transformations
- Ensure domain-specific knowledge is correctly applied"""

        elif query_type == 'historical_fact':
            return """HISTORICAL VERIFICATION:
- Verify time periods and contexts
- Check historical accuracy
- Consider historical definitions and meanings
- Account for changes over time"""

        return None

    def _generate_format_requirements(self, planning_result: Dict[str, Any]) -> str:
        """生成输出格式要求"""

        query_type = planning_result.get('query_type', '')

        base_format = """OUTPUT FORMAT:
Generate a JSON array of reasoning steps with this exact structure:
[
    {
        "step": 1,
        "type": "information_retrieval|data_processing|logical_reasoning|answer_synthesis",
        "description": "Clear description of what this step does",
        "sub_query": "Specific question or instruction for this step",
        "output_format": "text|json|number|boolean|list"
    }
]"""

        if query_type == 'logic_trap':
            base_format += "\n\nIMPORTANT: If the query contains a logical impossibility, include steps that clearly identify and address this impossibility."

        return base_format

    def _extract_query_from_prompt(self, prompt: str) -> str:
        """使用统一的查询提取工具"""
        return QueryExtractionTool.extract_query(prompt) or ""

    def _get_domain_knowledge_for_type(self, query_type: str) -> List[str]:
        """根据查询类型获取领域知识"""

        knowledge_map = {
            'logic_trap': [
                'Washington D.C. is the capital of the United States but is NOT a state. It is a federal district.',
                'A state is one of the 50 constituent political entities that together form the United States.',
                'If a premise is impossible or contradictory, the conclusion cannot be reached through normal logic.'
            ],
            'factual_chain': [
                'Political titles like "President" and "First Lady" have specific historical contexts.',
                'Family relationships (mother, father, wife, etc.) need to be traced through historical records.',
                'Ordinal numbers (15th, 2nd, etc.) refer to chronological sequences in history.'
            ],
            'cross_domain': [
                'Dewey Decimal classification is a library cataloging system using decimal numbers.',
                'Building heights are physical measurements typically in feet or meters.',
                'Conversions between different types of measurements require appropriate scaling.'
            ],
            'historical_fact': [
                'Historical facts must be verified against the time period they occurred in.',
                'Definitions and meanings can change over time.',
                'Context is crucial for understanding historical events and relationships.'
            ]
        }

        return knowledge_map.get(query_type, [])

    def _initialize_domain_knowledge(self) -> Dict[str, List[str]]:
        """初始化领域知识库"""
        return {
            'geography': [
                'Washington D.C. is the capital of the United States but is NOT a state.',
                'A state is one of the 50 constituent political entities that share sovereignty with the federal government.',
                'Federal districts are administered directly by the federal government.',
                'The United States consists of 50 states plus federal territories and districts.'
            ],

            'politics': [
                'The President of the United States is elected every 4 years.',
                'The First Lady is traditionally the wife of the President.',
                'James Buchanan (1857-1861) was the 15th President and never married.',
                'Harriet Lane served as White House hostess during Buchanan\'s presidency.'
            ],

            'literature': [
                'Charlotte Brontë wrote "Jane Eyre" which was published in 1847.',
                'Dewey Decimal classification 823.8 represents English fiction by women authors.',
                'Library classification systems organize books by subject matter.'
            ],

            'measurement': [
                'Building heights are typically measured in feet or meters.',
                'Dewey Decimal numbers are categorical, not measurements.',
                'Converting between different types of quantities requires appropriate methods.'
            ],

            'logic': [
                'A logical contradiction means the premises cannot all be true simultaneously.',
                'If premises contain a contradiction, any conclusion can be drawn.',
                'Impossibility in logic means the situation cannot exist in reality.',
                'Some questions are designed to contain logical traps or impossibilities.'
            ]
        }

    def _filter_relevant_knowledge(self, knowledge_results: List[Dict], planning_result: Dict[str, Any]) -> List[Dict]:
        """过滤高度相关的知识（PromptEnhancer的二次过滤）"""
        if not knowledge_results:
            return []

        query = planning_result.get('original_query', '')
        query_type = planning_result.get('query_type', 'general')

        filtered_results = []

        for knowledge in knowledge_results:
            content = knowledge.get('content', '')
            relevance_score = knowledge.get('relevance_score', 0)

            # 必须满足基本相关性阈值
            if relevance_score < 0.4:
                continue

            # 进行语义相关性检查
            if not self._is_knowledge_semantically_relevant(query, content, query_type):
                continue

            # 检查内容质量
            if not self._is_knowledge_quality_good(content):
                continue

            filtered_results.append(knowledge)

        # 按相关性得分排序
        filtered_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return filtered_results[:3]  # 最多返回3条

    def _is_knowledge_semantically_relevant(self, query: str, content: str, query_type: str) -> bool:
        """检查知识的语义相关性"""
        query_lower = query.lower()
        content_lower = content.lower()

        # 基于查询类型的语义检查
        if query_type == 'factual_chain':
            # 检查是否包含相关实体或关系
            relevant_indicators = ['president', 'lady', 'first lady', 'mother', 'wife', 'born', 'died', 'name']
            has_relevant_content = any(indicator in content_lower for indicator in relevant_indicators)
            if not has_relevant_content:
                return False

        elif query_type == 'logic_trap':
            # 检查是否包含逻辑相关的概念
            logic_indicators = ['if', 'then', 'when', 'where', 'which', 'what', 'state', 'capital']
            has_logic_content = any(indicator in content_lower for indicator in logic_indicators)
            if not has_logic_content:
                return False

        # 检查是否有共同的关键词
        query_keywords = self._extract_query_keywords(query)
        content_keywords = self._extract_content_keywords(content)

        common_keywords = set(query_keywords) & set(content_keywords)
        if len(common_keywords) == 0:
            return False

        # 检查内容是否太短或太长
        if len(content.split()) < 3 or len(content) > 500:
            return False

        return True

    def _extract_query_keywords(self, query: str) -> List[str]:
        """从查询中提取关键词"""
        words = query.lower().split()
        keywords = []

        for word in words:
            if len(word) > 2 and word.isalnum():
                keywords.append(word)

        return keywords

    def _extract_content_keywords(self, content: str) -> List[str]:
        """从知识内容中提取关键词"""
        words = content.lower().split()
        keywords = []

        for word in words:
            if len(word) > 2 and word.isalnum():
                keywords.append(word)

        return keywords

    def _is_knowledge_quality_good(self, content: str) -> bool:
        """检查知识内容的质量"""
        # 检查是否包含有意义的内容
        if not content or len(content.strip()) < 10:
            return False

        # 检查是否包含太多特殊字符
        special_chars = sum(1 for char in content if not char.isalnum() and char not in ' .,-()')
        if special_chars > len(content) * 0.3:
            return False

        # 检查是否看起来像错误信息
        error_indicators = ['error', 'failed', 'exception', 'not found', 'null']
        if any(indicator in content.lower() for indicator in error_indicators):
            return False

        return True
