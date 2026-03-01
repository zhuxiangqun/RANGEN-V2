"""
答案提取器 - 重构后的模块化实现
"""
import logging
import time
from typing import Dict, List, Any, Optional
from .models import Evidence, ReasoningStep
from .answer_extraction.extraction_strategies import (
    LLMExtractionStrategy,
    PatternExtractionStrategy,
    SemanticExtractionStrategy,
    CognitiveExtractionStrategy
)
from .answer_extraction.answer_validator import AnswerValidator
from .answer_extraction.answer_formatter import AnswerFormatter

logger = logging.getLogger(__name__)


class AnswerExtractor:
    """答案提取器 - 模块化重构版本
    
    职责：
    - 答案提取：从证据、步骤结果中提取答案
    - 格式验证和清理：清理答案文本，验证格式
    - 基本验证：逻辑一致性、合理性检查
    
    设计原则：
    - 使用策略模式支持多种提取方法
    - 统一验证接口
    - 统一格式化接口
    - 减少硬编码，使用语义理解
    """
    
    def __init__(
        self,
        llm_integration=None,
        fast_llm_integration=None,
        prompt_generator=None,
        evidence_processor=None,
        cache_manager=None,
        unified_config_center=None
    ):
        self.logger = logging.getLogger(__name__)
        self.llm_integration = llm_integration
        self.fast_llm_integration = fast_llm_integration
        self.prompt_generator = prompt_generator
        self.evidence_processor = evidence_processor
        self.cache_manager = cache_manager
        self.unified_config_center = unified_config_center
        
        # 初始化语义理解管道（延迟加载）
        self._semantic_pipeline = None
        
        # 初始化认知提取器（可选）
        self.cognitive_extractor = None
        try:
            from src.core.reasoning.cognitive_answer_extractor import CognitiveAnswerExtractor
            llm_for_cognitive = fast_llm_integration or llm_integration
            self.cognitive_extractor = CognitiveAnswerExtractor(llm_integration=llm_for_cognitive)
            self.logger.info("认知答案提取器已初始化")
        except Exception as e:
            self.logger.debug(f"认知答案提取器初始化失败(可选功能): {e}")
        
        # 初始化提取策略（按优先级排序）
        self.strategies = self._initialize_strategies()
        
        # 初始化验证器和格式化器
        self.validator = AnswerValidator(semantic_pipeline=self._get_semantic_pipeline())
        self.formatter = AnswerFormatter()
        
        # 初始化统一输出格式化器（向后兼容）
        try:
            from .unified_output_formatter import UnifiedOutputFormatter
            from .confidence_calibrator import ConfidenceCalibrator
            self.output_formatter = UnifiedOutputFormatter()
            self.confidence_calibrator = ConfidenceCalibrator()
        except Exception:
            self.output_formatter = None
            self.confidence_calibrator = None
        
        # 🚀 修复：初始化分层验证器（可选）
        self.hierarchical_validator: Optional[Any] = None  # type: ignore
        try:
            from src.core.reasoning.hierarchical_answer_validator import HierarchicalAnswerValidator
            validator_config = {
                'use_nlp': True,
                'use_llm_fallback': False,
                'semantic_threshold': 0.3,
                'use_lightweight_nlp': True,
                'similarity_model_name': 'all-MiniLM-L6-v2'
            }
            self.hierarchical_validator = HierarchicalAnswerValidator(config=validator_config)
            self.logger.info("分层答案验证器已初始化")
        except Exception as e:
            self.logger.debug(f"分层答案验证器初始化失败(可选功能): {e}")
        
        # 🚀 修复：初始化统一规则管理中心（可选）
        self.rule_manager: Optional[Any] = None  # type: ignore
        try:
            from src.utils.unified_rule_manager import get_unified_rule_manager
            self.rule_manager = get_unified_rule_manager(
                config_center=self.unified_config_center,
                semantic_pipeline=self._get_semantic_pipeline()
            )
            self.logger.info("统一规则管理中心已初始化")
        except Exception as e:
            self.logger.debug(f"统一规则管理中心初始化失败(可选功能): {e}")
    
    def _initialize_strategies(self) -> List:
        """初始化提取策略"""
        strategies = []
        
        # 1. 认知增强提取（最高优先级，如果可用）
        if self.cognitive_extractor:
            strategies.append(
                CognitiveExtractionStrategy(self.cognitive_extractor)
            )
        
        # 2. LLM提取
        if self.llm_integration:
            strategies.append(
                LLMExtractionStrategy(
                    self.llm_integration,
                    self.prompt_generator
                )
            )
        
        # 3. 语义理解提取
        semantic_pipeline = self._get_semantic_pipeline()
        if semantic_pipeline:
            strategies.append(
                SemanticExtractionStrategy(semantic_pipeline)
            )
        
        # 4. 模式匹配提取（fallback）
        strategies.append(
            PatternExtractionStrategy(semantic_pipeline)
        )
        
        return strategies
    
    def _get_semantic_pipeline(self):
        """获取语义理解管道（延迟加载）"""
        if self._semantic_pipeline is None:
            try:
                from src.utils.semantic_understanding_pipeline import SemanticUnderstandingPipeline
                pipeline = SemanticUnderstandingPipeline()
                self._semantic_pipeline = pipeline
            except Exception as e:
                self.logger.debug(f"语义理解管道初始化失败: {e}")
                self._semantic_pipeline = None  # 标记为不可用
        
        # 确保返回的是pipeline实例或None
        if self._semantic_pipeline and hasattr(self._semantic_pipeline, 'understand_query'):
            return self._semantic_pipeline
        return None
    
    def extract_step_result(
        self,
        step_evidence: List[Any],
        step: Dict[str, Any],
        previous_step_result: Optional[str],
        original_query: str,
        sub_query: str
    ) -> Optional[str]:
        """从证据中提取当前步骤的中间答案
        
        Args:
            step_evidence: 步骤证据列表
            step: 步骤信息
            previous_step_result: 上一步结果
            original_query: 原始查询
            sub_query: 子查询
            
        Returns:
            提取的答案，如果无法提取则返回None
        """
        try:
            if not step_evidence:
                return None
            
            # 评估证据质量
            evidence_text = self._merge_evidence(step_evidence)
            if not evidence_text:
                return None
            
            evidence_quality = self._assess_evidence_quality(
                evidence_text,
                sub_query,
                previous_step_result
            )
            
            # 根据证据质量决定是否提取
            quality_threshold = 0.15
            if evidence_quality < quality_threshold:
                self.logger.warning(
                    f"证据质量过低({evidence_quality:.2f} < {quality_threshold:.2f})，"
                    f"拒绝提取答案。查询: {sub_query[:100]}"
                )
                return None
            
            # 使用策略提取答案
            context = {
                'previous_step_result': previous_step_result,
                'original_query': original_query,
                'sub_query': sub_query,
                'step': step
            }
            
            answer = self._extract_with_strategies(
                query=sub_query,
                evidence=step_evidence,
                context=context
            )
            
            if not answer:
                return None
            
            # 格式化答案
            formatted_answer = self.formatter.format(answer, sub_query)

            # 过滤占位/模板式回答
            if self._is_placeholder_answer(formatted_answer):
                self.logger.warning(f"占位式回答已过滤: {formatted_answer[:80]}")
                return None
                            
            # 验证答案
            validation_result = self.validator.validate(
                formatted_answer,
                sub_query,
                context
            )
            
            if not validation_result['is_valid']:
                self.logger.warning(
                    f"答案验证失败: {', '.join(validation_result['errors'])}。"
                    f"答案: {formatted_answer[:100]}"
                )
                return None
                                    
            return formatted_answer
            
        except Exception as e:
            self.logger.error(f"提取步骤结果失败: {e}", exc_info=True)
            return None
    
    def _extract_with_strategies(
        self,
        query: str,
        evidence: List[Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """使用策略提取答案"""
        # 分类查询类型
        query_type = self._classify_query_type(query)
        
        # 按优先级尝试各个策略
        for strategy in self.strategies:
            try:
                if strategy.can_handle(query, query_type):
                    answer = strategy.extract(query, evidence, context)
                    if answer:
                        self.logger.debug(
                            f"使用策略 {strategy.__class__.__name__} 成功提取答案"
                        )
                        return answer
            except Exception as e:
                self.logger.debug(f"策略 {strategy.__class__.__name__} 提取失败: {e}")
                continue
                    
        return None
            
    def _classify_query_type(self, query: str) -> Optional[str]:
        """分类查询类型"""
        semantic_pipeline = self._get_semantic_pipeline()
        if semantic_pipeline:
            try:
                # 使用understand_query获取查询理解结果
                result = semantic_pipeline.understand_query(query)
                if isinstance(result, dict):
                    # 从理解结果中提取查询类型
                    intent = result.get('intent', {})
                    if isinstance(intent, dict):
                        query_type = intent.get('type', 'general')
                        if query_type:
                            return query_type
                    # 或者从lexical语义中提取
                    lexical = result.get('lexical', {})
                    if isinstance(lexical, dict):
                        query_type = lexical.get('query_type', 'general')
                        if query_type:
                            return query_type
            except Exception:
                pass
        
        # 简单规则分类（fallback）
        query_lower = query.lower()
        if any(word in query_lower for word in ['who', 'name', 'person']):
            return "person_name"
        elif any(word in query_lower for word in ['when', 'date', 'year']):
            return "date"
        elif any(word in query_lower for word in ['how many', 'number', 'count']):
            return "number"
        
        return "general"
    
    def _merge_evidence(self, evidence: List[Any]) -> str:
        """合并证据文本"""
        if not evidence:
            return ""
        
        texts = []
        for ev in evidence[:5]:  # 限制证据数量
            if hasattr(ev, 'content'):
                content = str(ev.content)
                if content:
                    texts.append(content)
            else:
                text = str(ev)
                if text:
                    texts.append(text)
        
        return "\n".join(texts)
    
    def _assess_evidence_quality(
        self,
        evidence_text: str,
        query: str,
        previous_step_result: Optional[str] = None
    ) -> float:
        """评估证据质量
        
        Returns:
            质量分数 (0.0 - 1.0)
        """
        if not evidence_text:
            return 0.0
        
        # 基础质量评估
        quality = 0.5  # 默认质量
        
        # 检查证据长度
        if len(evidence_text) < 50:
            quality *= 0.5
        elif len(evidence_text) > 500:
            quality *= 0.9
        
        # 使用语义理解检查相关性（如果可用）
        semantic_pipeline = self._get_semantic_pipeline()
        if semantic_pipeline:
            try:
                similarity = semantic_pipeline.calculate_semantic_similarity(
                    evidence_text,
                    query
                )
                quality = quality * 0.5 + similarity * 0.5
            except Exception:
                pass
        
        return min(1.0, max(0.0, quality))
    
    # ========== 向后兼容的方法 ==========
    
    def extract_answer_standard(
        self,
        query: str,
        content: str,
        query_type: Optional[str] = None
    ) -> Optional[str]:
        """标准答案提取（向后兼容）"""
        evidence = [content] if content else []
        answer = self._extract_with_strategies(query, evidence)
        if answer:
            return self.formatter.format(answer, query)
        return None
            
    def clean_answer_text(self, answer: str, needs_full_answer: bool = False) -> str:
        """清理答案文本（向后兼容）"""
        return self.formatter.format(answer)
    
    def validate_answer(
        self,
        answer: str,
        query: str,
        query_type: str,
        evidence: List[Any]
    ) -> bool:
        """验证答案（向后兼容）"""
        result = self.validator.validate(answer, query)
        return result['is_valid']

    def extract_answer_generic(
        self,
        query: str,
        content: str,
        query_type: Optional[str] = None
    ) -> Optional[str]:
        """通用答案提取（向后兼容）"""
        try:
            if not query or not query.strip():
                return None
            query = query.strip()
            evidence = [content] if content else []

            # 识别查询类型，用于下游策略与验证
            detected_query_type = query_type or self._classify_query_type(query)
            context = {'query_type': detected_query_type}

            answer = self._extract_with_strategies(query, evidence, context)
            if not answer:
                return None
            # 过滤占位/模板式回答
            if self._is_placeholder_answer(answer):
                self.logger.warning(f"占位式回答已过滤: {answer[:80]}")
                return None
            
            formatted_answer = self.formatter.format(answer, query)
            validation_result = self.validator.validate(
                formatted_answer,
                query,
                context
            )
            if not validation_result['is_valid']:
                self.logger.warning(
                    f"通用答案验证失败: {', '.join(validation_result['errors'])} | 答案: {formatted_answer[:100]}"
                )
                return None
    
            return formatted_answer
        except Exception as exc:
            self.logger.error(f"通用答案提取失败: {exc}", exc_info=True)
            return None
            
    @staticmethod
    def _is_placeholder_answer(answer: str) -> bool:
        """检测明显的占位/模板式回答，避免误当有效答案"""
        if not answer:
            return True
        answer_lower = answer.strip().lower()
        placeholders = [
            "question is missing. please provide a specific question",
            "please provide a specific question",
            "unable to determine",
            "cannot determine",
            "no answer provided",
        ]
        return any(p in answer_lower for p in placeholders)
    
    async def derive_final_answer_with_ml(
        self, 
        query: str, 
        evidence: List[Any], 
        steps: Optional[List[Dict[str, Any]]] = None,
        enhanced_context: Optional[Dict[str, Any]] = None,
        query_type: Optional[str] = None,
        retrieval_depth: int = 0,
        retry_count: int = 0,
        task_session_id: Optional[str] = None
    ) -> str:  # type: ignore
        """使用ML推导最终答案（向后兼容）
        
        注意：此方法包含策略逻辑，建议使用 RealReasoningEngine 的方法。
        本方法保留仅用于向后兼容。
        """
        # 验证查询
        if not query or not query.strip():
            error_msg = "[ERROR] 查询为空，无法生成答案"
            self.logger.error(error_msg)
            return error_msg
        
        query = query.strip()
        
        # 获取原始查询
        original_query = query
        if enhanced_context:
            original_query = enhanced_context.get('original_query', query)
        
        try:
            # 使用策略提取答案
            context = {
                'original_query': original_query,
                'query_type': query_type,
                'steps': steps,
                'enhanced_context': enhanced_context
            }
            
            answer = self._extract_with_strategies(query, evidence, context)
            
            if not answer:
                # 尝试从步骤中提取
                if steps:
                    for step in reversed(steps):
                        step_answer = step.get('answer')
                        if step_answer:
                            answer = step_answer
                            break
                            
            if not answer:
                return "无法确定(推理步骤执行不完整或知识库信息不足)"
            
            # 格式化答案
            formatted_answer = self.formatter.format(str(answer), query)
            
            # 验证答案
            validation_result = self.validator.validate(
                formatted_answer,
                query,
                context
            )
            
            if not validation_result['is_valid']:
                self.logger.warning(
                    f"最终答案验证失败: {', '.join(validation_result['errors'])}"
                )
                # 仍然返回答案，但记录警告
            
            return formatted_answer
            
        except Exception as e:
            self.logger.error(f"推导最终答案失败: {e}", exc_info=True)
            return f"[ERROR] Failed to derive final answer: {e}"
    
    # ========== 其他向后兼容的方法（简化实现） ==========
    
    def _is_person_query(self, query: str) -> bool:
        """判断是否是查询人名的查询"""
        query_type = self._classify_query_type(query)
        return query_type == "person_name"
    
    def _validate_logical_consistency(self, answer: str, query: str) -> bool:
        """验证逻辑一致性（向后兼容）"""
        result = self.validator.validate(answer, query)
        return result['is_valid']
    
    def _validate_answer_reasonableness(
        self,
        answer: str,
        query: str,
        evidence_text: str,
        previous_step_result: Optional[str] = None
    ) -> bool:
        """验证答案合理性（向后兼容）"""
        context = {
            'evidence_text': evidence_text,
            'previous_step_result': previous_step_result
        }
        result = self.validator.validate(answer, query, context)
        return result['is_valid']
    
    def _is_relationship_query(self, query: str) -> bool:
        """判断是否是关系查询"""
        import re
        query_lower = query.lower()
        relationship_patterns = [
            r'\b(mother|father|parent|wife|husband|spouse|daughter|son|child|sibling|brother|sister)\b',
            r'\b(maiden\s+name|surname|last\s+name|first\s+name)\b',
        ]
        return any(re.search(pattern, query_lower) for pattern in relationship_patterns)
    
    def _validate_relationship_answer_consistency(
        self, 
        answer: str, 
        query: str, 
        previous_step_result: Optional[str], 
        evidence_text: str
    ) -> bool:
        """验证关系查询答案的一致性
        
        验证策略:
        1. 如果查询是关于"X的母亲/父亲",答案不应该是X本人
        2. 如果查询是关于"X的娘家姓",答案不应该是X的姓氏
        3. 如果上一步结果是某个实体,这一步查询关于该实体的关系,答案应该是关系对象,而不是实体本身
        
        Args:
            answer: 提取的答案
            query: 查询文本
            previous_step_result: 上一步的结果(可选)
            evidence_text: 证据文本
            
        Returns:
            如果答案一致返回True,否则返回False
        """
        try:
            if not answer or not query:
                return True  # 如果无法验证,默认通过
            
            import re
            answer_clean = answer.strip()
            query_lower = query.lower()
            
            # 检查是否是关系查询
            is_relationship_query = self._is_relationship_query(query)
            if not is_relationship_query:
                return True  # 不是关系查询,跳过验证
            
            # 策略1: 检查答案是否与查询中的实体相同(错误:返回了实体本身而非关系对象)
            entity_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
            query_entities = re.findall(entity_pattern, query)
            
            # 如果查询中有实体,检查答案是否与实体相同
            for entity in query_entities:
                entity_parts = entity.split()
                answer_parts = answer_clean.split()
                
                # 如果答案与实体完全相同,这是错误的(除非查询就是问实体本身)
                if answer_clean.lower() == entity.lower():
                    # 检查查询是否明确询问实体本身(如"Who was X?")
                    if not re.search(rf'\bwho\s+was\s+{re.escape(entity)}\b', query_lower, re.IGNORECASE):
                        # 如果查询是关于关系(如"mother of X"),但答案返回了X本身,这是错误的
                        if re.search(r'\b(mother|father|parent|wife|husband|spouse|daughter|son|child)\s+of\s+', query_lower):
                            self.logger.warning(
                                f"关系一致性验证失败:查询询问'{entity}'的关系,但答案返回了'{entity}'本身: {answer_clean}"
                            )
                            return False
                
                # 检查答案是否包含实体的主要部分
                if len(entity_parts) >= 2 and len(answer_parts) >= 2:
                    if answer_parts[:2] == entity_parts[:2]:
                        if re.search(r'\b(mother|father|parent|wife|husband|spouse|daughter|son|child)\s+of\s+', query_lower):
                            self.logger.warning(
                                f"关系一致性验证失败:查询询问关系,但答案返回了实体本身: {answer_clean}"
                            )
                            return False
            
            # 策略2: 检查答案是否与上一步结果相同(错误:返回了上一步的实体而非关系对象)
            if previous_step_result:
                prev_result_clean = previous_step_result.strip()
                
                if answer_clean.lower() == prev_result_clean.lower():
                    if re.search(r'\b(mother|father|parent|wife|husband|spouse|daughter|son|child)\b', query_lower):
                        self.logger.warning(
                            f"关系一致性验证失败:查询询问关系,但答案返回了上一步的实体: {answer_clean}"
                        )
                        return False
                
                # 检查答案是否包含上一步结果的主要部分
                prev_parts = prev_result_clean.split()
                answer_parts = answer_clean.split()
                
                if len(prev_parts) >= 2 and len(answer_parts) >= 2:
                    if answer_parts[:2] == prev_parts[:2]:
                        if re.search(r'\b(mother|father|parent|wife|husband|spouse|daughter|son|child)\b', query_lower):
                            self.logger.warning(
                                f"关系一致性验证失败:查询询问关系,但答案与上一步结果相同: {answer_clean}"
                            )
                            return False
                
            # 策略3: 检查"娘家姓"查询的特殊情况
            if re.search(r'\bmaiden\s+name\b', query_lower):
                if previous_step_result:
                    prev_parts = previous_step_result.strip().split()
                    if len(prev_parts) >= 2:
                        prev_surname = prev_parts[-1].lower()
                        answer_lower = answer_clean.lower()
                        
                        # 如果答案与上一步结果的姓氏相同,且查询是关于"娘家姓",这是错误的
                        if answer_lower == prev_surname:
                            self.logger.warning(
                                f"关系一致性验证失败:查询询问娘家姓,但答案返回了已婚后的姓氏: {answer_clean}"
                            )
                            return False
            
            return True  # 所有验证通过
            
        except Exception as e:
            self.logger.debug(f"关系一致性验证失败: {e}")
            return True  # 如果验证失败,默认通过(避免误杀)

