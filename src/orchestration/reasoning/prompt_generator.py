"""
提示词生成器 - 生成优化提示词和管理模板
"""
import logging
import time
from typing import Dict, List, Any, Optional
from .models import Evidence

logger = logging.getLogger(__name__)


class PromptGenerator:
    """提示词生成器 - 集成统一架构"""
    
    def __init__(self, prompt_engineering=None, llm_integration=None, context_manager=None, config_center=None, learning_manager=None):
        self.logger = logging.getLogger(__name__)
        self.prompt_engineering = prompt_engineering
        self.llm_integration = llm_integration
        self.context_manager = context_manager
        self.config_center = config_center
        self.learning_manager = learning_manager
        self._current_template_name = None
        self._current_query_type = None
        
        # 🚀 方案A：集成统一架构组件
        from .template_selector import TemplateSelector
        from .evidence_quality_assessor import EvidenceQualityAssessor
        from .confidence_calibrator import ConfidenceCalibrator
        from .unified_output_formatter import UnifiedOutputFormatter
        
        self.template_selector = TemplateSelector(learning_manager=learning_manager)
        self.evidence_assessor = EvidenceQualityAssessor(llm_integration=llm_integration)
        self.confidence_calibrator = ConfidenceCalibrator()
        self.output_formatter = UnifiedOutputFormatter()
    
    def generate_optimized_prompt(
        self, 
        template_name: str, 
        query: str, 
        evidence: Optional[str] = None, 
        query_type: str = "general",
        enhanced_context: Optional[Dict[str, Any]] = None,
        model_type: str = "reasoning",
        task_session_id: Optional[str] = None
    ) -> str:
        """生成优化的提示词（🚀 方案A：集成统一架构）"""
        # 🚀 P0修复：验证查询是否为空
        if not query or not query.strip():
            self.logger.error(f"❌ 查询为空，无法生成prompt: template_name={template_name}")
            print(f"❌ [PromptGenerator] 查询为空，无法生成prompt: template_name={template_name}")
            return self.get_fallback_prompt(template_name, query or "", evidence, query_type)
        
        # 确保 query 不为空
        query = query.strip()
        # 🚀 方案A：使用模板选择器智能选择模板
        if hasattr(self, 'template_selector'):
            # 评估证据质量（如果有证据）
            evidence_quality = None
            if evidence:
                evidence_list = enhanced_context.get('evidence', []) if enhanced_context else []
                quality_result = self.evidence_assessor.assess(evidence, query, evidence_list)
                evidence_quality = quality_result.get('quality_level', 'medium')
                self.logger.info(f"✅ 证据质量评估: {evidence_quality} (score={quality_result.get('overall_score', 0):.2f})")
            
            # 🚀 优化：使用统一服务评估查询复杂度
            complexity = "medium"
            if enhanced_context:
                # 优先从enhanced_context获取复杂度（如果已计算）
                complexity_score = enhanced_context.get('complexity_score', 0)
                if complexity_score > 0:
                    if complexity_score >= 4.0:
                        complexity = "complex"
                    elif complexity_score <= 2.0:
                        complexity = "simple"
                else:
                    # 如果没有复杂度评分，使用统一服务评估
                    try:
                        from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
                        service = get_unified_complexity_model_service()
                        query = enhanced_context.get('query', '')
                        if query:
                            complexity_result = service.assess_complexity(
                                query=query,
                                query_type=query_type,
                                evidence_count=0,
                                query_analysis=None
                            )
                            complexity = complexity_result.level.value
                            # 将复杂度评分保存到enhanced_context，避免重复计算
                            enhanced_context['complexity_score'] = complexity_result.score
                    except Exception as e:
                        self.logger.debug(f"统一服务复杂度评估失败: {e}，使用默认值")
            
            # 使用模板选择器选择模板
            selection_result = self.template_selector.select(
                query_type=query_type,
                complexity=complexity,
                evidence_quality=evidence_quality,
                has_evidence=bool(evidence),
                query=query
            )
            
            selected_template_name = selection_result.get('template_name', template_name)
            if selected_template_name != template_name:
                self.logger.info(
                    f"✅ 模板选择器选择: {template_name} → {selected_template_name} "
                    f"(原因: {selection_result.get('selection_reason', 'unknown')})"
                )
                template_name = selected_template_name
        else:
            # Fallback: 使用原有逻辑
            selected_template_name = self.select_optimal_template(template_name, query_type, query)
            if selected_template_name != template_name:
                self.logger.info(f"✅ 自动选择模板: {template_name} → {selected_template_name} (基于性能数据)")
                template_name = selected_template_name
        
        # 记录当前使用的模板
        self._current_template_name = template_name
        self._current_query_type = query_type
        
        # 从上下文工程中提取更丰富的上下文信息
        context_info = {}
        if enhanced_context and self.context_manager:
            context_info = self.context_manager.extract_context_for_prompt(enhanced_context, task_session_id)
            self.logger.debug(f"✅ 从上下文工程提取上下文信息: 关键线索数={len(context_info.get('key_clues', []))}, 推理步骤数={len(context_info.get('reasoning_steps', []))}")
        
        try:
            if self.prompt_engineering:
                # 提取增强后的上下文信息
                context_summary = context_info.get('context_summary', '') if context_info else ""
                keywords = context_info.get('keywords_str', '') if context_info else ""
                context_confidence = enhanced_context.get('context_confidence', 0.5) if enhanced_context else 0.5
                
                # 构建提示词参数
                prompt_kwargs = {
                    'query': query,
                    'query_type': query_type
                }
                
                if evidence:
                    # 动态调整证据长度
                    max_evidence_length = 3000
                    if query_type in ['simple', 'factual']:
                        max_evidence_length = 2000
                    elif query_type in ['complex', 'multi_hop']:
                        max_evidence_length = 4000
                    
                    query_length = len(query)
                    if query_length > 200:
                        max_evidence_length = min(max_evidence_length + 500, 4500)
                    elif query_length < 50:
                        max_evidence_length = max(max_evidence_length - 500, 1500)
                    
                    # 如果证据过长，智能压缩
                    if len(evidence) > max_evidence_length:
                        first_part = int(max_evidence_length * 0.3)
                        last_part = int(max_evidence_length * 0.3)
                        middle_part = max_evidence_length - first_part - last_part
                        middle_start = len(evidence) // 2 - middle_part // 2
                        middle_end = middle_start + middle_part
                        
                        evidence_compressed = (
                            evidence[:first_part] + 
                            "\n[... middle content ...]\n" +
                            evidence[max(0, middle_start):min(len(evidence), middle_end)] +
                            "\n[... middle content ...]\n" +
                            evidence[-last_part:]
                        )
                        self.logger.debug(f"⚠️ 证据过长（{len(evidence)}字符），智能压缩到{len(evidence_compressed)}字符")
                        prompt_kwargs['evidence'] = evidence_compressed
                    else:
                        prompt_kwargs['evidence'] = evidence
                
                # 添加上下文相关信息
                if context_summary:
                    prompt_kwargs['context_summary'] = context_summary
                if keywords:
                    prompt_kwargs['keywords'] = keywords
                
                # 添加推理步骤摘要和关键线索
                if context_info:
                    reasoning_summary = context_info.get('reasoning_summary', '')
                    if reasoning_summary:
                        prompt_kwargs['reasoning_steps'] = reasoning_summary
                    
                    key_clues = context_info.get('key_clues', [])
                    if key_clues:
                        key_clues_text = '\n'.join(key_clues[:5])
                        prompt_kwargs['key_clues'] = key_clues_text
                
                # 使用提示词工程生成提示词
                prompt = self.prompt_engineering.generate_prompt(template_name, **prompt_kwargs)
                
                if prompt:
                    # 🚀 P0修复：推理步骤生成模板不应该添加答案生成相关的指令
                    # 推理步骤生成需要返回JSON格式的推理步骤，而不是最终答案
                    # 🚀 优化：增加 reasoning_without_evidence 到排除列表
                    step_generation_templates = [
                        "reasoning_steps_generation", 
                        "fallback_reasoning_steps_generation",
                        "reasoning_without_evidence"
                    ]
                    
                    if template_name in step_generation_templates:
                        # 对于推理步骤生成，只确保JSON格式要求，不添加答案生成指令
                        # 🚀 优化：简化提示词，减少长度，提高响应速度
                        # 🚀 优化：检查prompt是否已经包含了关键的任务定义（无论是来自模板还是PromptGenerator）
                        # 如果模板已经包含了详细的指令（如 CRITICAL TASK DEFINITION），则不再重复添加
                        has_critical_definition = (
                            "CRITICAL TASK DEFINITION" in prompt[:500] or 
                            "CRITICAL: REASONING STEPS GENERATION TASK" in prompt[:500] or
                            "CRITICAL FORMAT REQUIREMENT" in prompt[:500]
                        )
                        
                        if not has_critical_definition:
                            # 🚀 智能示例选择：根据查询内容选择合适的示例
                            coding_keywords = {
                                'python', 'java', 'c++', 'javascript', 'code', 'function', 'class', 
                                'script', 'api', 'library', 'sdk', 'error', 'exception', 'compile', 
                                'run', 'debug', 'test', 'pandas', 'numpy', 'react', 'vue', 'algorithm',
                                'list', 'dict', 'string', 'int', 'variable', 'loop', 'if', 'else'
                            }
                            
                            is_coding_query = (
                                str(query_type).lower() in ['coding', 'code', 'technical'] or
                                any(k in query.lower() for k in coding_keywords)
                            )
                            
                            if is_coding_query:
                                example_text = """Query: "How do I read a CSV file in Python using pandas?"
Response: {{"steps": [{{"type": "evidence_gathering", "description": "Identify pandas function for CSV", "sub_query": "What is the pandas function to read CSV?"}}, {{"type": "evidence_gathering", "description": "Find syntax for read_csv", "sub_query": "How to use pandas.read_csv?"}}]}}"""
                            else:
                                example_text = """Query: "What is the capital of the country where the Eiffel Tower is located?"
Response: {{"steps": [{{"type": "evidence_gathering", "description": "Find the country of Eiffel Tower", "sub_query": "Where is the Eiffel Tower located?"}}, {{"type": "evidence_gathering", "description": "Find the capital", "sub_query": "What is the capital of [step 1 result]?"}}]}}"""

                            json_format_instruction = f"""**🚨 CRITICAL: REASONING STEPS GENERATION TASK 🚨**

**TASK**: Generate JSON format reasoning steps, NOT the final answer.

**REQUIREMENTS**:
1. Return ONLY valid JSON: {{"steps": [...]}}
2. Each step must have: "type", "description", "sub_query"
3. Use placeholders like "[step 1 result]" in sub_queries
4. DO NOT return direct answers like "Jane Ballou"

**EXAMPLE**:
{example_text}

**NOW GENERATE STEPS FOR THE QUERY BELOW:**

"""
                            prompt = json_format_instruction + "\n\n" + prompt
                        return prompt
                    
                    # 为快速模型生成专门的提示词
                    if model_type == "fast":
                        fast_model_instruction = """🎯 CRITICAL INSTRUCTIONS FOR FAST MODEL (READ FIRST):

You are using a FAST model designed for quick, direct answers. Follow these rules:

1. **Return ONLY the direct answer** - No reasoning process, no explanations
2. **Answer format**: Return the answer directly
3. **Do NOT include**: "Reasoning Process:", "Step 1:", "Based on the evidence...", etc.
4. **If you cannot determine the answer**, return "unable to determine"

Remember: FAST = Direct answer, no reasoning process.

"""
                        prompt = fast_model_instruction + "\n\n" + prompt
                    else:
                        # 添加格式要求
                        format_instruction = self.get_answer_format_instruction(query_type, query)
                        if format_instruction:
                            prompt = format_instruction + "\n\n" + prompt
                        
                        # 检测多跳查询
                        is_multi_hop = self._detect_multi_hop_query(query)
                        if is_multi_hop:
                            multi_hop_instruction = """
⚠️ MULTI-HOP REASONING REQUIRED:

This query requires multiple reasoning steps. You MUST:
1. Complete ALL hops sequentially (Hop 1 → Hop 2 → ... → Final Answer)
2. For numerical queries: Continue until you reach the final NUMBER
3. For name queries: Continue until you reach the COMPLETE name
4. Mark your final answer with "Final Answer:" or "最终答案:"

"""
                            prompt = multi_hop_instruction + "\n\n" + prompt
                        
                        # 添加准确性要求
                        accuracy_instruction = """
🎯 CRITICAL: ANSWER ACCURACY REQUIREMENT (READ FIRST):

**CORE REQUIREMENTS**:
1. **Evidence-Based Answering**: If evidence is RELEVANT, base your answer on it
2. **Answer Type**: Ensure your FINAL ANSWER matches the query type
3. **Multi-Hop Reasoning**: Complete ALL hops for multi-hop queries
4. **Answer Completeness**: Use COMPLETE answers (full names, complete phrases)
5. **Mark Your Final Answer**: Use "Final Answer:" or "最终答案:"

"""
                        prompt = accuracy_instruction + "\n\n" + prompt
                    
                    return prompt
                
                # Fallback: 使用简单提示词
                return self.get_fallback_prompt(template_name, query, evidence, query_type)
            
            return self.get_fallback_prompt(template_name, query, evidence, query_type)
            
        except Exception as e:
            self.logger.error(f"生成优化提示词失败: {e}")
            return self.get_fallback_prompt(template_name, query, evidence, query_type)
    
    def get_answer_format_instruction(self, query_type: str, query: str) -> str:
        """🚀 重构：委托给提示词工程生成答案格式要求"""
        try:
            if self.prompt_engineering:
                # 尝试从提示词工程获取格式指令
                format_prompt = self.prompt_engineering.generate_prompt(
                    "answer_format_instruction",
                    query_type=query_type,
                    query=query
                )
                if format_prompt:
                    return format_prompt
            
            # Fallback: 简单的格式指令
            if query_type in ['numerical', 'number']:
                return "⚠️ NUMERICAL ANSWER REQUIRED: Your final answer MUST be a NUMBER (e.g., '506000', '87')."
            elif query_type in ['ranking', 'ordinal']:
                return "⚠️ RANKING ANSWER REQUIRED: Your final answer MUST be an ORDINAL (e.g., '37th', not '37')."
            elif query_type in ['name', 'person_name']:
                return "⚠️ COMPLETE NAME REQUIRED: Your final answer MUST be a COMPLETE name (e.g., 'Jane Ballou', not 'Jane')."
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"获取答案格式指令失败: {e}")
            return ""
    
    def get_fallback_prompt(self, template_name: str, query: str, evidence: Optional[str] = None, query_type: str = "general") -> str:
        """获取回退提示词"""
        try:
            prompt = f"Query: {query}\n\n"
            if evidence:
                prompt += f"Evidence: {evidence[:2000]}\n\n"
            prompt += "Please provide a detailed answer based on the query and evidence."
            return prompt
        except Exception as e:
            self.logger.error(f"生成回退提示词失败: {e}")
            return f"Query: {query}\n\nPlease provide an answer."
    
    def select_optimal_template(self, template_name: str, query_type: str, query: str) -> str:
        """选择最优模板（基于性能数据）"""
        try:
            # 如果学习管理器可用，使用学习到的模板选择
            if self.learning_manager and hasattr(self.learning_manager, 'get_optimal_template'):
                optimal_template = self.learning_manager.get_optimal_template(template_name, query_type, query)
                if optimal_template:
                    return optimal_template
            
            # 默认返回原始模板名称
            return template_name
            
        except Exception as e:
            self.logger.debug(f"选择最优模板失败: {e}")
            return template_name
    
    def _detect_multi_hop_query(self, query: str) -> bool:
        """检测是否是多跳查询"""
        try:
            multi_hop_indicators = [
                "'s",  # 关系查询，如 "X's mother"
                "of the",  # 关系查询，如 "mother of X"
                "and then",  # 顺序查询
                "first", "then",  # 顺序查询
                "based on",  # 基于查询
                "using",  # 使用查询
            ]
            
            query_lower = query.lower()
            # 检查是否包含多个关系指示词
            indicator_count = sum(1 for indicator in multi_hop_indicators if indicator in query_lower)
            
            # 如果包含多个关系指示词，可能是多跳查询
            if indicator_count >= 2:
                return True
            
            # 检查是否包含嵌套关系（如 "X's Y's Z"）
            if query_lower.count("'s") >= 2:
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"检测多跳查询失败: {e}")
            return False
    
    def format_step_evidence_for_prompt(self, steps: List[Dict[str, Any]]) -> str:
        """🚀 新增：格式化步骤级别的证据，用于提示词"""
        try:
            step_evidence_parts = []
            for i, step in enumerate(steps, 1):
                step_evidence = step.get('evidence', [])
                if step_evidence and len(step_evidence) > 0:
                    step_description = step.get('description', f'Step {i}')
                    step_sub_query = step.get('sub_query', '')
                    
                    step_info = f"### Step {i}: {step_description}"
                    if step_sub_query:
                        step_info += f"\nSub-query: {step_sub_query}"
                    
                    evidence_parts = []
                    for ev in step_evidence[:3]:
                        if hasattr(ev, 'content'):
                            content = ev.content[:200]
                            relevance = getattr(ev, 'relevance_score', 0.0)
                            evidence_parts.append(f"  - Evidence (Relevance: {relevance:.2f}): {content}")
                        elif isinstance(ev, str):
                            evidence_parts.append(f"  - Evidence: {ev[:200]}")
                    
                    if evidence_parts:
                        step_info += "\n" + "\n".join(evidence_parts)
                        step_evidence_parts.append(step_info)
            
            if step_evidence_parts:
                return "\n\n".join(step_evidence_parts)
            return ""
            
        except Exception as e:
            self.logger.warning(f"Failed to format step evidence: {e}")
            return ""
    
    def format_step_results_for_prompt(self, steps: List[Dict[str, Any]]) -> str:
        """🚀 P0新增：格式化推理步骤的结果，用于提示词"""
        try:
            step_results_parts = []
            for i, step in enumerate(steps, 1):
                step_type = step.get('type', '')
                step_description = step.get('description', f'步骤{i}')
                step_result = step.get('result', '')
                
                # 特别关注answer_synthesis步骤
                if step_type == 'answer_synthesis' or 'answer_synthesis' in step_type.lower() or 'synthesis' in step_type.lower():
                    if step_result or step_description:
                        result_text = f"### 步骤{i} (答案合成): {step_description}"
                        if step_result:
                            result_text += f"\n结果: {step_result}"
                        step_results_parts.append(result_text)
                elif step_result:
                    result_text = f"### 步骤{i} ({step_type}): {step_description}"
                    result_text += f"\n结果: {step_result}"
                    step_results_parts.append(result_text)
            
            if step_results_parts:
                return "\n\n".join(step_results_parts)
            return ""
            
        except Exception as e:
            self.logger.warning(f"格式化步骤结果失败: {e}")
            return ""

