#!/usr/bin/env python3
"""
Prompt 动态编排器
实现多片段组合、动态调整等功能
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from src.visualization.orchestration_tracker import get_orchestration_tracker

logger = logging.getLogger(__name__)


class OrchestrationStrategy(Enum):
    """编排策略枚举"""
    DEFAULT = "default"  # 默认策略
    SIMPLE = "simple"  # 简单策略（最少片段）
    DETAILED = "detailed"  # 详细策略（最多片段）
    EVIDENCE_BASED = "evidence_based"  # 基于证据的策略
    REASONING_BASED = "reasoning_based"  # 基于推理的策略
    CONTEXT_RICH = "context_rich"  # 上下文丰富的策略


class PromptOrchestrator:
    """Prompt 动态编排器
    
    功能：
    1. 片段库：定义可复用的提示词片段
    2. 编排引擎：实现片段组合逻辑
    3. 动态调整：根据上下文动态选择片段
    """
    
    def __init__(self):
        """初始化编排器"""
        self.logger = logging.getLogger(__name__)
        
        # 定义可复用的提示词片段库
        self.fragments = self._initialize_fragments()
        
        # 定义编排策略配置
        self.strategy_configs = self._initialize_strategy_configs()
        
        self.logger.info("✅ PromptOrchestrator 初始化完成")
    
    def _initialize_fragments(self) -> Dict[str, str]:
        """初始化片段库"""
        return {
            # 基础片段
            "introduction": """You are a professional AI assistant specialized in analyzing and answering questions.

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.""",
            
            "introduction_reasoning": """You are a professional reasoning expert specialized in breaking down complex problems into executable reasoning steps.

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.""",
            
            "introduction_analysis": """You are a professional analysis expert specialized in in-depth problem analysis and detailed answers.

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.""",
            
            # 查询相关片段
            "query_section": """**Query:**
{query}""",
            
            "query_with_context": """**Query:**
{query}

**Context:**
{context}""",
            
            # 证据相关片段
            "evidence_section": """**Evidence:**
{evidence}""",
            
            "evidence_guidance": """**Evidence Usage Guidelines:**
- Prioritize using the provided evidence to answer the question
- If evidence is insufficient, you may combine with your knowledge
- If evidence is irrelevant to the question, clearly state so""",
            
            "evidence_quality_note": """**Evidence Quality Report:**
- Evidence Relevance Score: {similarity_score:.2f}
- Evidence Quality Score: {quality_score:.2f}
{quality_reason}""",
            
            # 上下文相关片段
            "context_section": """**Context:**
{context}""",
            
            "context_confidence": """**Context Confidence:** {confidence:.2f}
{confidence_guidance}""",
            
            # 推理相关片段
            "reasoning_guidance": """**Reasoning Requirements:**
1. Carefully analyze the core requirements of the question
2. Identify key information and constraints
3. Use logical reasoning to reach conclusions
4. Verify the reasonableness and accuracy of the answer""",
            
            "reasoning_steps": """**Reasoning Steps:**
Please follow these steps for reasoning:
1. Understand the problem: Clarify the core requirements
2. Analyze information: Extract key information and constraints
3. Logical reasoning: Use logical reasoning to reach conclusions
4. Verify answer: Check the reasonableness and accuracy of the answer""",
            
            "multi_step_reasoning": """**Multi-step Reasoning Requirements:**
- Break down complex problems into multiple sub-problems
- Solve each sub-problem in sequence
- Use the result from the previous step as input for the next step
- Finally synthesize all step results to reach the final answer""",
            
            # 答案相关片段
            "answer_requirement": """**Answer Requirements:**
- Provide accurate and detailed answers
- If unable to determine, clearly state so
- Answers should be based on provided evidence and context""",
            
            "answer_format": """**Answer Format:**
- Answer the question directly, without including reasoning process
- If the question is factual, provide specific facts
- If the question is analytical, provide detailed analysis""",
            
            "answer_validation": """**Answer Validation:**
- Check if the answer addresses the question
- Verify the accuracy and reasonableness of the answer
- Ensure the answer is based on the provided evidence""",
            
            # 输出格式片段
            "output_format_json": """**Output Format** (JSON):
Please return the result in JSON format with the following fields:
- answer: Final answer
- reasoning: Reasoning process (optional)
- confidence: Confidence level (0-1)
- sources: Information sources (optional)""",
            
            "output_format_text": """**Output Format:**
Please provide the answer directly without additional format instructions.""",
            
            # 特殊场景片段
            "multi_hop_guidance": """**Multi-hop Reasoning Guidance:**
- Identify multiple sub-questions in the problem
- Determine dependencies between sub-questions
- Solve sub-questions in dependency order
- Use placeholders (e.g., [step X result]) to reference previous step results""",
            
            "entity_completion_guidance": """**Entity Completion Guidance:**
- If the query contains incomplete entity names (e.g., "James A"), complete them to full names (e.g., "James A. Garfield")
- Find complete entity names from the evidence
- Use complete names for subsequent queries""",
            
            "dependency_analysis": """**Dependency Analysis:**
- Analyze dependencies between steps
- Ensure dependent step results are correctly used
- Use placeholders to reference dependent step results""",
        }
    
    def _initialize_strategy_configs(self) -> Dict[str, List[str]]:
        """初始化编排策略配置"""
        return {
            OrchestrationStrategy.DEFAULT.value: [
                "introduction",
                "query_section",
                "answer_requirement",
                "output_format_text"
            ],
            OrchestrationStrategy.SIMPLE.value: [
                "introduction",
                "query_section",
                "answer_format"
            ],
            OrchestrationStrategy.DETAILED.value: [
                "introduction",
                "query_section",
                "evidence_section",
                "evidence_guidance",
                "context_section",
                "reasoning_guidance",
                "answer_requirement",
                "answer_format",
                "answer_validation",
                "output_format_text"
            ],
            OrchestrationStrategy.EVIDENCE_BASED.value: [
                "introduction",
                "query_section",
                "evidence_section",
                "evidence_guidance",
                "evidence_quality_note",
                "answer_requirement",
                "output_format_text"
            ],
            OrchestrationStrategy.REASONING_BASED.value: [
                "introduction_reasoning",
                "query_section",
                "reasoning_guidance",
                "reasoning_steps",
                "multi_step_reasoning",
                "answer_requirement",
                "output_format_text"
            ],
            OrchestrationStrategy.CONTEXT_RICH.value: [
                "introduction",
                "query_with_context",
                "context_confidence",
                "evidence_section",
                "evidence_guidance",
                "reasoning_guidance",
                "answer_requirement",
                "output_format_text"
            ],
        }
    
    def _select_fragments(
        self,
        strategy: str,
        context: Dict[str, Any]
    ) -> List[str]:
        """根据策略和上下文选择片段"""
        # 获取基础片段列表
        base_fragments = self.strategy_configs.get(
            strategy,
            self.strategy_configs[OrchestrationStrategy.DEFAULT.value]
        )
        
        # 根据上下文动态调整
        selected_fragments = base_fragments.copy()
        
        # 如果有证据，确保包含证据相关片段
        if context.get("evidence") or context.get("knowledge"):
            if "evidence_section" not in selected_fragments:
                # 找到 query_section 的位置，在其后插入
                if "query_section" in selected_fragments:
                    idx = selected_fragments.index("query_section")
                    selected_fragments.insert(idx + 1, "evidence_section")
                    if "evidence_guidance" not in selected_fragments:
                        selected_fragments.insert(idx + 2, "evidence_guidance")
                else:
                    selected_fragments.append("evidence_section")
                    selected_fragments.append("evidence_guidance")
        
        # 如果有上下文信息，确保包含上下文片段
        if context.get("enhanced_context") or context.get("context"):
            if "context_section" not in selected_fragments:
                if "query_section" in selected_fragments:
                    idx = selected_fragments.index("query_section")
                    selected_fragments.insert(idx + 1, "context_section")
                else:
                    selected_fragments.append("context_section")
        
        # 如果是多步骤推理，添加多步骤指导
        if context.get("is_multi_step") or context.get("reasoning_steps"):
            if "multi_step_reasoning" not in selected_fragments:
                if "reasoning_guidance" in selected_fragments:
                    idx = selected_fragments.index("reasoning_guidance")
                    selected_fragments.insert(idx + 1, "multi_step_reasoning")
                else:
                    selected_fragments.append("multi_step_reasoning")
            
            # 添加依赖关系分析
            if "dependency_analysis" not in selected_fragments:
                selected_fragments.append("dependency_analysis")
        
        # 如果是实体补全场景，添加实体补全指导
        if context.get("needs_entity_completion"):
            if "entity_completion_guidance" not in selected_fragments:
                selected_fragments.append("entity_completion_guidance")
        
        # 根据查询类型调整
        query_type = context.get("query_type", "general")
        if query_type in ["multi_hop", "complex"]:
            if "multi_hop_guidance" not in selected_fragments:
                selected_fragments.append("multi_hop_guidance")
        
        return selected_fragments
    
    def _compose_fragments(
        self,
        fragments: List[str],
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """组合片段生成完整提示词"""
        composed_parts = []
        
        for fragment_name in fragments:
            if fragment_name not in self.fragments:
                self.logger.warning(f"⚠️ 片段不存在: {fragment_name}，跳过")
                continue
            
            fragment_template = self.fragments[fragment_name]
            
            # 准备参数
            params = {
                "query": query,
                "context": context.get("context", ""),
                "evidence": self._format_evidence(context.get("evidence")),
                "similarity_score": context.get("similarity_score", 0.0),
                "quality_score": context.get("quality_score", 1.0),
                "quality_reason": context.get("quality_reason", ""),
                "confidence": context.get("context_confidence", 0.8),
                "confidence_guidance": self._get_confidence_guidance(
                    context.get("context_confidence", 0.8)
                ),
            }
            
            # 格式化片段
            try:
                formatted_fragment = fragment_template.format(**params)
                composed_parts.append(formatted_fragment)
            except KeyError as e:
                # 如果缺少参数，尝试使用默认值
                self.logger.warning(f"⚠️ 片段格式化失败: {fragment_name}, 缺少参数: {e}")
                # 使用安全的格式化方法
                formatted_fragment = self._safe_format(fragment_template, params)
                if formatted_fragment:
                    composed_parts.append(formatted_fragment)
        
        # 组合所有片段
        prompt = "\n\n".join(composed_parts)
        
        return prompt
    
    def _format_evidence(self, evidence: Any) -> str:
        """格式化证据"""
        if not evidence:
            return "(No evidence available)"
        
        if isinstance(evidence, str):
            return evidence
        
        if isinstance(evidence, list):
            if not evidence:
                return "(No evidence available)"
            
            formatted_items = []
            for i, item in enumerate(evidence[:5], 1):  # 最多显示5条
                if isinstance(item, dict):
                    content = item.get("content") or item.get("text") or str(item)
                    source = item.get("source", "Unknown source")
                    formatted_items.append(f"{i}. {content}\n   Source: {source}")
                else:
                    formatted_items.append(f"{i}. {str(item)}")
            
            return "\n".join(formatted_items)
        
        if isinstance(evidence, dict):
            content = evidence.get("content") or evidence.get("text") or str(evidence)
            source = evidence.get("source", "Unknown source")
            return f"{content}\nSource: {source}"
        
        return str(evidence)
    
    def _get_confidence_guidance(self, confidence: float) -> str:
        """获取置信度指导文本"""
        if confidence >= 0.8:
            return "Context information has high confidence and can be fully trusted and used."
        elif confidence >= 0.6:
            return "Context information has medium confidence, suggest verifying with other information."
        else:
            return "Context information has low confidence, suggest using with caution and verification."
    
    def _safe_format(self, template: str, params: Dict[str, Any]) -> str:
        """安全格式化（处理缺失参数）"""
        import re
        result = template
        placeholders = re.findall(r'\{(\w+)\}', template)
        
        for placeholder in placeholders:
            if placeholder not in params:
                # 使用空字符串或默认值
                result = result.replace(f"{{{placeholder}}}", "")
        
        return result
    
    async def orchestrate(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        orchestration_strategy: str = "default"
    ) -> str:
        """动态编排提示词
        
        Args:
            query: 查询文本
            context: 上下文信息（可选）
            orchestration_strategy: 编排策略（default, simple, detailed, evidence_based, reasoning_based, context_rich）
        
        Returns:
            编排后的完整提示词
        """
        # 🎯 编排追踪：提示词编排开始
        tracker = getattr(self, '_orchestration_tracker', None) or get_orchestration_tracker()
        parent_event_id = getattr(self, '_current_parent_event_id', None)
        
        context = context or {}
        
        try:
            # 1. 根据策略和上下文选择片段
            fragments = self._select_fragments(orchestration_strategy, context)
            
            # 🎯 编排追踪：提示词编排
            if tracker:
                tracker.track_prompt_orchestrate(
                    orchestration_strategy,
                    fragments,  # fragments 应该是 List[str]
                    parent_event_id
                )
            
            # 2. 组合片段生成完整提示词
            prompt = self._compose_fragments(fragments, query, context)
            
            self.logger.debug(f"✅ Prompt编排完成: 策略={orchestration_strategy}, 片段数={len(fragments)}")
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"❌ Prompt编排失败: {e}", exc_info=True)
            # Fallback: 返回简单提示词
            return f"""You are a professional AI assistant specialized in analyzing and answering questions.

**Query:**
{query}

**CRITICAL LANGUAGE REQUIREMENT**: All answers must be in ENGLISH, even if the query is in another language. Use English for dates, names, locations, and all other answer components.

Please provide an accurate and detailed answer."""
    
    def add_fragment(self, name: str, content: str) -> bool:
        """添加自定义片段
        
        Args:
            name: 片段名称
            content: 片段内容（支持占位符，如 {query}, {context} 等）
        
        Returns:
            是否添加成功
        """
        try:
            self.fragments[name] = content
            self.logger.info(f"✅ 片段添加成功: {name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 片段添加失败: {e}")
            return False
    
    def register_strategy(
        self,
        strategy_name: str,
        fragment_list: List[str]
    ) -> bool:
        """注册自定义编排策略
        
        Args:
            strategy_name: 策略名称
            fragment_list: 片段列表（按顺序）
        
        Returns:
            是否注册成功
        """
        try:
            self.strategy_configs[strategy_name] = fragment_list
            self.logger.info(f"✅ 策略注册成功: {strategy_name}")
            return True
        except Exception as e:
            self.logger.error(f"❌ 策略注册失败: {e}")
            return False
    
    def get_available_fragments(self) -> List[str]:
        """获取所有可用的片段名称"""
        return list(self.fragments.keys())
    
    def get_available_strategies(self) -> List[str]:
        """获取所有可用的策略名称"""
        return list(self.strategy_configs.keys())


# 全局单例
_orchestrator_instance = None


def get_prompt_orchestrator() -> PromptOrchestrator:
    """获取 Prompt 编排器实例（单例模式）"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = PromptOrchestrator()
    return _orchestrator_instance

