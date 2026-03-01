"""
答案提取器 - 重构后的模块化实现
"""
import logging
import time
from typing import Dict, List, Any, Optional
from .extraction_strategies import (
    LLMExtractionStrategy,
    PatternExtractionStrategy,
    SemanticExtractionStrategy,
    CognitiveExtractionStrategy
)
from .answer_validator import AnswerValidator
from .answer_formatter import AnswerFormatter

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
                self._semantic_pipeline = SemanticUnderstandingPipeline()
            except Exception as e:
                self.logger.debug(f"语义理解管道初始化失败: {e}")
                self._semantic_pipeline = False  # 标记为不可用
        
        return self._semantic_pipeline if self._semantic_pipeline else None
    
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
                result = semantic_pipeline.classify_query_type(query)
                if isinstance(result, dict):
                    return result.get('type', 'general')
                return result
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
                similarity = semantic_pipeline.calculate_similarity(
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
    ) -> str:
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
            formatted_answer = self.formatter.format(answer, query)
            
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

