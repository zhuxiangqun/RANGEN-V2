#!/usr/bin/env python3
"""
统一证据处理框架 - 整合所有证据相关的处理功能
遵循统一中心系统原则，提供一站式证据处理服务
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class EvidenceProcessingStage(Enum):
    """证据处理阶段"""
    RETRIEVAL = "检索"
    PREPROCESSING = "预处理"
    VALIDATION = "验证"
    QUALITY_ASSESSMENT = "质量评估"
    FORMATTING = "格式化"
    COMPLETE = "完成"


@dataclass
class EvidenceProcessingResult:
    """证据处理结果"""
    evidence: List[Any]
    stage: EvidenceProcessingStage
    metadata: Dict[str, Any]
    validation_result: Optional[Any] = None
    quality_assessment: Optional[Dict[str, Any]] = None
    formatted_text: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UnifiedEvidenceFramework:
    """
    统一证据处理框架
    
    整合以下功能：
    1. 证据检索 (EvidenceProcessor)
    2. 证据预处理 (EvidencePreprocessor)
    3. 证据验证 (EvidenceValidator)
    4. 质量评估 (EvidenceQualityAssessor)
    5. 格式化 (format_for_prompt)
    
    遵循统一中心系统原则，提供一站式证据处理服务
    """
    
    def __init__(
        self,
        knowledge_retrieval_agent=None,
        config_center=None,
        learning_manager=None,
        llm_integration=None,
        max_tokens: int = 4000,
        relevance_threshold: float = 0.1
    ):
        """
        初始化统一证据处理框架
        
        Args:
            knowledge_retrieval_agent: 知识检索智能体
            config_center: 统一配置中心
            learning_manager: 学习管理器
            llm_integration: LLM集成
            max_tokens: 最大token数
            relevance_threshold: 相关性阈值
        """
        self.logger = logging.getLogger(__name__)
        
        # 🚀 初始化各个处理模块
        self._initialize_modules(
            knowledge_retrieval_agent,
            config_center,
            learning_manager,
            llm_integration,
            max_tokens,
            relevance_threshold
        )
    
    def _initialize_modules(
        self,
        knowledge_retrieval_agent,
        config_center,
        learning_manager,
        llm_integration,
        max_tokens,
        relevance_threshold
    ):
        """初始化各个处理模块"""
        # 1. 证据检索模块 (EvidenceProcessor)
        try:
            from src.core.reasoning.evidence_processor import EvidenceProcessor
            self.retrieval_processor = EvidenceProcessor(
                knowledge_retrieval_agent=knowledge_retrieval_agent,
                config_center=config_center,
                learning_manager=learning_manager,
                llm_integration=llm_integration
            )
            self.logger.debug("✅ 证据检索模块已初始化")
        except Exception as e:
            self.logger.warning(f"证据检索模块初始化失败: {e}")
            self.retrieval_processor = None
        
        # 2. 证据预处理模块 (EvidencePreprocessor)
        try:
            from src.core.reasoning.evidence_preprocessor import EvidencePreprocessor
            self.preprocessor = EvidencePreprocessor(
                max_tokens=max_tokens,
                relevance_threshold=relevance_threshold
            )
            self.logger.debug("✅ 证据预处理模块已初始化")
        except Exception as e:
            self.logger.warning(f"证据预处理模块初始化失败: {e}")
            self.preprocessor = None
        
        # 3. 证据验证模块 (EvidenceValidator)
        try:
            from src.core.reasoning.evidence_validator import EvidenceValidator
            self.validator = EvidenceValidator()
            self.logger.debug("✅ 证据验证模块已初始化")
        except Exception as e:
            self.logger.warning(f"证据验证模块初始化失败: {e}")
            self.validator = None
        
        # 4. 质量评估模块 (EvidenceQualityAssessor)
        try:
            from src.core.reasoning.evidence_quality_assessor import EvidenceQualityAssessor
            self.quality_assessor = EvidenceQualityAssessor(llm_integration=llm_integration)
            self.logger.debug("✅ 证据质量评估模块已初始化")
        except Exception as e:
            self.logger.warning(f"证据质量评估模块初始化失败: {e}")
            self.quality_assessor = None
    
    async def process_evidence_complete(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        query_analysis: Optional[Dict[str, Any]] = None,
        format_type: str = "structured"
    ) -> EvidenceProcessingResult:
        """
        完整的证据处理流程
        
        流程：
        1. 检索证据 (Retrieval)
        2. 预处理证据 (Preprocessing)
        3. 验证证据 (Validation)
        4. 质量评估 (Quality Assessment)
        5. 格式化证据 (Formatting)
        
        Args:
            query: 查询文本
            context: 上下文信息
            query_analysis: 查询分析结果
            format_type: 格式化类型 ("structured", "qa", "summary")
            
        Returns:
            证据处理结果
        """
        try:
            context = context or {}
            query_analysis = query_analysis or {}
            
            # 阶段1: 检索证据
            raw_evidence = await self._retrieve_evidence(query, context, query_analysis)
            if not raw_evidence:
                self.logger.warning(f"⚠️ 未检索到证据: {query[:100]}")
                return EvidenceProcessingResult(
                    evidence=[],
                    stage=EvidenceProcessingStage.RETRIEVAL,
                    metadata={'error': 'no_evidence_retrieved'}
                )
            
            # 阶段2: 预处理证据（传递query参数）
            preprocessed_evidence = self._preprocess_evidence(raw_evidence, query=query)
            if not preprocessed_evidence:
                self.logger.warning(f"⚠️ 预处理后无有效证据: {query[:100]}")
                return EvidenceProcessingResult(
                    evidence=[],
                    stage=EvidenceProcessingStage.PREPROCESSING,
                    metadata={'error': 'no_valid_evidence_after_preprocessing'}
                )
            
            # 🚀 新增：阶段2.5: 检查证据是否直接回答了问题
            answer_relevance = None
            if self.preprocessor:
                try:
                    from src.core.reasoning.evidence_preprocessor import ProcessedEvidence
                    # 检查是否是ProcessedEvidence列表
                    if preprocessed_evidence and len(preprocessed_evidence) > 0:
                        if isinstance(preprocessed_evidence[0], ProcessedEvidence):
                            answer_relevance = self.preprocessor.check_answer_relevance(preprocessed_evidence, query)
                            
                            # 🚀 新增：如果证据不直接回答问题，尝试重新检索
                            if not answer_relevance.get('has_direct_answer', False):
                                # 🚀 优化：这是正常的重试机制，降级为INFO级别
                                self.logger.info(
                                    f"ℹ️ [证据相关性检查] 证据不直接回答问题，尝试重新检索: {query[:80]}..."
                                )
                                self.logger.debug(f"🔍 [证据相关性检查] 相关性评分: {answer_relevance.get('relevance_score', 0.0):.2f}")
                                
                                # 生成更具体的查询变体
                                if self.retrieval_processor:
                                    # 🚀 重构：对于序数查询，生成更具体的查询（使用通用模式，不硬编码特定实体）
                                    ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', query, re.IGNORECASE)
                                    if ordinal_match:
                                        ordinal_num = ordinal_match.group(1)
                                        
                                        # 🚀 通用化：提取实体类型和上下文（不硬编码"first lady"、"president"等）
                                        ordinal_entity_pattern = r'(\d+(?:st|nd|rd|th))\s+([^?\'"]+?)(?:\s+of\s+the\s+[^?\'"]*?)?(?:\'s|of|$|\?)'
                                        entity_match = re.search(ordinal_entity_pattern, query, re.IGNORECASE)
                                        
                                        if entity_match:
                                            entity_type = entity_match.group(2).strip()
                                            # 移除常见的修饰语
                                            entity_type = re.sub(r'\s+of\s+the\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', entity_type, flags=re.IGNORECASE)
                                            entity_type = entity_type.strip()
                                            
                                            # 提取上下文
                                            context_match = re.search(r'of\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', query, re.IGNORECASE)
                                            context = context_match.group(1) if context_match else None
                                            
                                            if entity_type:
                                                # 生成通用列表查询变体
                                                retry_queries = [
                                                    f"list of {entity_type} chronological order",
                                                    f"{entity_type} complete list order",
                                                    f"{ordinal_num}th {entity_type} list order chronological"
                                                ]
                                                
                                                if context:
                                                    retry_queries.extend([
                                                        f"list of {entity_type} of {context} chronological order",
                                                        f"{entity_type} of {context} complete list order",
                                                        f"{ordinal_num}th {entity_type} {context} list order chronological"
                                                    ])
                                            else:
                                                retry_queries = [query]
                                        else:
                                            retry_queries = [query]
                                        
                                        # 尝试使用更具体的查询重新检索
                                        for retry_query in retry_queries[:2]:  # 最多尝试2个变体
                                            retry_evidence = await self._retrieve_evidence(
                                                retry_query, context, query_analysis
                                            )
                                            if retry_evidence:
                                                # 检查重新检索的证据是否更相关
                                                retry_preprocessed = self._preprocess_evidence(retry_evidence, query=query)
                                                if retry_preprocessed and len(retry_preprocessed) > 0:
                                                    if isinstance(retry_preprocessed[0], ProcessedEvidence):
                                                        retry_relevance = self.preprocessor.check_answer_relevance(
                                                            retry_preprocessed, query
                                                        )
                                                        if retry_relevance.get('has_direct_answer', False):
                                                            # 重新检索的证据更相关，使用它
                                                            preprocessed_evidence = retry_preprocessed
                                                            raw_evidence = retry_evidence
                                                            answer_relevance = retry_relevance
                                                            self.logger.info(
                                                                f"✅ [证据相关性检查] 重新检索成功，找到更相关的证据: {retry_query[:80]}..."
                                                            )
                                                            print(f"✅ [证据相关性检查] 重新检索成功，找到更相关的证据: {retry_query[:80]}...")
                                                            break
                except Exception as e:
                    self.logger.debug(f"检查答案相关性失败: {e}")
            
            # 🚀 新增：将答案相关性检查结果添加到证据元数据中
            if answer_relevance and preprocessed_evidence:
                for ev in preprocessed_evidence:
                    if hasattr(ev, 'metadata'):
                        ev.metadata = ev.metadata or {}
                        ev.metadata['answer_relevance'] = answer_relevance
            
            # 阶段3: 验证证据
            validation_result = None
            if self.validator:
                validation_result = self.validator.validate_retrieved_content(
                    preprocessed_evidence, query
                )
            
            # 阶段4: 质量评估
            quality_assessment = None
            if self.quality_assessor and preprocessed_evidence:
                # 合并证据文本用于质量评估
                evidence_text = self._merge_evidence_for_assessment(preprocessed_evidence)
                quality_assessment = self.quality_assessor.assess(
                    evidence_text, query, preprocessed_evidence
                )
            
            # 阶段5: 格式化证据
            formatted_text = None
            if self.preprocessor:
                formatted_text = self.preprocessor.format_for_prompt(
                    preprocessed_evidence,
                    query=query,
                    format_type=format_type
                )
            
            # 构建处理结果
            result = EvidenceProcessingResult(
                evidence=preprocessed_evidence,
                stage=EvidenceProcessingStage.COMPLETE,
                metadata={
                    'raw_count': len(raw_evidence),
                    'processed_count': len(preprocessed_evidence),
                    'format_type': format_type,
                    'answer_relevance': answer_relevance  # 🚀 新增：包含答案相关性检查结果
                },
                validation_result=validation_result,
                quality_assessment=quality_assessment,
                formatted_text=formatted_text
            )
            
            self.logger.info(
                f"✅ 证据处理完成: {len(raw_evidence)} -> {len(preprocessed_evidence)} 条证据, "
                f"质量评分: {quality_assessment.get('overall_score', 0.0):.2f if quality_assessment else 'N/A'}, "
                f"直接答案: {answer_relevance.get('has_direct_answer', False) if answer_relevance else 'N/A'}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"证据处理失败: {e}", exc_info=True)
            return EvidenceProcessingResult(
                evidence=[],
                stage=EvidenceProcessingStage.RETRIEVAL,
                metadata={'error': str(e)}
            )
    
    async def _retrieve_evidence(
        self,
        query: str,
        context: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> List[Any]:
        """阶段1: 检索证据"""
        if not self.retrieval_processor:
            self.logger.warning("证据检索模块不可用")
            return []
        
        try:
            evidence = await self.retrieval_processor.gather_evidence(
                query, context, query_analysis
            )
            return evidence
        except Exception as e:
            self.logger.error(f"证据检索失败: {e}")
            return []
    
    def _preprocess_evidence(self, raw_evidence: List[Any], query: Optional[str] = None) -> List[Any]:
        """阶段2: 预处理证据"""
        if not self.preprocessor:
            self.logger.warning("证据预处理模块不可用，返回原始证据")
            return raw_evidence
        
        try:
            # 清洗证据（传递query参数，用于针对序数查询进行特殊过滤）
            cleaned_evidence = self.preprocessor.clean_retrieved_chunks(raw_evidence, query=query)
            
            # 压缩以适应上下文窗口
            compressed_evidence = self.preprocessor.compress_for_context(
                cleaned_evidence,
                max_tokens=3000  # 为提示词模板留出空间
            )
            
            return compressed_evidence
        except Exception as e:
            self.logger.error(f"证据预处理失败: {e}")
            return raw_evidence
    
    def _merge_evidence_for_assessment(self, evidence_list: List[Any]) -> str:
        """合并证据文本用于质量评估"""
        texts = []
        for ev in evidence_list:
            if hasattr(ev, 'content'):
                texts.append(ev.content)
            elif isinstance(ev, dict):
                texts.append(ev.get('content', '') or ev.get('text', '') or str(ev))
            else:
                texts.append(str(ev))
        return "\n\n".join(texts)
    
    # 🚀 便捷方法：提供各个阶段的独立访问
    
    async def retrieve_only(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        query_analysis: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """仅检索证据（不进行后续处理）"""
        return await self._retrieve_evidence(query, context or {}, query_analysis or {})
    
    def preprocess_only(self, raw_evidence: List[Any], query: Optional[str] = None) -> List[Any]:
        """仅预处理证据（不进行检索）"""
        return self._preprocess_evidence(raw_evidence, query=query)
    
    def validate_only(
        self,
        evidence: List[Any],
        query: str
    ) -> Optional[Any]:
        """仅验证证据（不进行其他处理）"""
        if not self.validator:
            return None
        return self.validator.validate_retrieved_content(evidence, query)
    
    def assess_quality_only(
        self,
        evidence: List[Any],
        query: str
    ) -> Optional[Dict[str, Any]]:
        """仅评估质量（不进行其他处理）"""
        if not self.quality_assessor:
            return None
        evidence_text = self._merge_evidence_for_assessment(evidence)
        return self.quality_assessor.assess(evidence_text, query, evidence)
    
    def format_only(
        self,
        evidence: List[Any],
        query: str,
        format_type: str = "structured"
    ) -> Optional[str]:
        """仅格式化证据（不进行其他处理）"""
        if not self.preprocessor:
            return None
        return self.preprocessor.format_for_prompt(evidence, query, format_type)
    
    # 🚀 高级方法：支持步骤级别的证据处理
    
    async def process_evidence_for_step(
        self,
        sub_query: str,
        step: Dict[str, Any],
        context: Dict[str, Any],
        query_analysis: Dict[str, Any],
        previous_evidence: Optional[List[Any]] = None,
        format_type: str = "structured"
    ) -> EvidenceProcessingResult:
        """
        为推理步骤处理证据
        
        Args:
            sub_query: 子查询
            step: 步骤信息
            context: 上下文
            query_analysis: 查询分析
            previous_evidence: 前一步的证据（可选，用于复用）
            format_type: 格式化类型
            
        Returns:
            证据处理结果
        """
        try:
            # 阶段1: 检索证据（支持复用前一步的证据）
            if not self.retrieval_processor:
                return EvidenceProcessingResult(
                    evidence=[],
                    stage=EvidenceProcessingStage.RETRIEVAL,
                    metadata={'error': 'retrieval_processor_unavailable'}
                )
            
            # 🚀 修复：标记已检查相关性，避免在gather_evidence_for_step中重复检查
            context_with_flag = context.copy()
            context_with_flag['_relevance_checked'] = True
            
            raw_evidence = await self.retrieval_processor.gather_evidence_for_step(
                sub_query, step, context_with_flag, query_analysis, previous_evidence
            )
            
            if not raw_evidence:
                return EvidenceProcessingResult(
                    evidence=[],
                    stage=EvidenceProcessingStage.RETRIEVAL,
                    metadata={'error': 'no_evidence_retrieved'}
                )
            
            # 阶段2: 预处理证据（传递sub_query参数）
            preprocessed_evidence = self._preprocess_evidence(raw_evidence, query=sub_query)
            if not preprocessed_evidence:
                return EvidenceProcessingResult(
                    evidence=[],
                    stage=EvidenceProcessingStage.PREPROCESSING,
                    metadata={'error': 'no_valid_evidence_after_preprocessing'}
                )
            
            # 🚀 P1新增：阶段2.5: 检查证据是否直接回答了问题（与process_evidence_complete保持一致）
            answer_relevance = None
            if self.preprocessor:
                try:
                    from src.core.reasoning.evidence_preprocessor import ProcessedEvidence
                    # 检查是否是ProcessedEvidence列表
                    if preprocessed_evidence and len(preprocessed_evidence) > 0:
                        if isinstance(preprocessed_evidence[0], ProcessedEvidence):
                            answer_relevance = self.preprocessor.check_answer_relevance(preprocessed_evidence, sub_query)
                            
                            # 🚀 新增：如果证据不直接回答问题，尝试重新检索
                            if not answer_relevance.get('has_direct_answer', False):
                                self.logger.warning(
                                    f"⚠️ [证据相关性检查] 证据不直接回答问题，尝试重新检索: {sub_query[:80]}..."
                                )
                                print(f"⚠️ [证据相关性检查] 证据不直接回答问题，尝试重新检索: {sub_query[:80]}...")
                                
                                # 生成更具体的查询变体
                                if self.retrieval_processor:
                                    # 对于序数查询，生成更具体的查询
                                    ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', sub_query, re.IGNORECASE)
                                    if ordinal_match:
                                        ordinal_num = ordinal_match.group(1)
                                        # 生成列表查询变体
                                        if 'first lady' in sub_query.lower():
                                            retry_queries = [
                                                f"list of first ladies of the United States chronological order",
                                                f"first ladies of the United States complete list order",
                                                f"{ordinal_num}th first lady United States list order chronological"
                                            ]
                                        elif 'president' in sub_query.lower():
                                            retry_queries = [
                                                f"list of presidents of the United States chronological order",
                                                f"presidents of the United States complete list order",
                                                f"{ordinal_num}th president United States list order chronological"
                                            ]
                                        else:
                                            retry_queries = answer_relevance.get('suggestions', [])
                                        
                                        # 尝试使用更具体的查询重新检索
                                        for retry_query in retry_queries[:2]:  # 最多尝试2个变体
                                            retry_evidence = await self.retrieval_processor.gather_evidence_for_step(
                                                retry_query, step, context, query_analysis, previous_evidence
                                            )
                                            if retry_evidence:
                                                # 检查重新检索的证据是否更相关
                                                retry_preprocessed = self._preprocess_evidence(retry_evidence, query=sub_query)
                                                if retry_preprocessed and len(retry_preprocessed) > 0:
                                                    if isinstance(retry_preprocessed[0], ProcessedEvidence):
                                                        retry_relevance = self.preprocessor.check_answer_relevance(
                                                            retry_preprocessed, sub_query
                                                        )
                                                        if retry_relevance.get('has_direct_answer', False):
                                                            # 重新检索的证据更相关，使用它
                                                            preprocessed_evidence = retry_preprocessed
                                                            raw_evidence = retry_evidence
                                                            answer_relevance = retry_relevance
                                                            self.logger.info(
                                                                f"✅ [证据相关性检查] 重新检索成功，找到更相关的证据: {retry_query[:80]}..."
                                                            )
                                                            print(f"✅ [证据相关性检查] 重新检索成功，找到更相关的证据: {retry_query[:80]}...")
                                                            break
                except Exception as e:
                    self.logger.debug(f"检查答案相关性失败: {e}")
            
            # 🚀 新增：将答案相关性检查结果添加到证据元数据中
            if answer_relevance and preprocessed_evidence:
                for ev in preprocessed_evidence:
                    if hasattr(ev, 'metadata'):
                        ev.metadata = ev.metadata or {}
                        ev.metadata['answer_relevance'] = answer_relevance
            
            # 阶段3: 验证证据
            validation_result = None
            if self.validator:
                validation_result = self.validator.validate_retrieved_content(
                    preprocessed_evidence, sub_query
                )
            
            # 阶段4: 质量评估
            quality_assessment = None
            if self.quality_assessor and preprocessed_evidence:
                evidence_text = self._merge_evidence_for_assessment(preprocessed_evidence)
                quality_assessment = self.quality_assessor.assess(
                    evidence_text, sub_query, preprocessed_evidence
                )
            
            # 阶段5: 格式化证据
            formatted_text = None
            if self.preprocessor:
                formatted_text = self.preprocessor.format_for_prompt(
                    preprocessed_evidence,
                    query=sub_query,
                    format_type=format_type
                )
            
            return EvidenceProcessingResult(
                evidence=preprocessed_evidence,
                stage=EvidenceProcessingStage.COMPLETE,
                metadata={
                    'raw_count': len(raw_evidence),
                    'processed_count': len(preprocessed_evidence),
                    'format_type': format_type,
                    'step_type': step.get('type', 'unknown')
                },
                validation_result=validation_result,
                quality_assessment=quality_assessment,
                formatted_text=formatted_text
            )
            
        except Exception as e:
            self.logger.error(f"步骤证据处理失败: {e}", exc_info=True)
            return EvidenceProcessingResult(
                evidence=[],
                stage=EvidenceProcessingStage.RETRIEVAL,
                metadata={'error': str(e)}
            )
    
    # 🚀 工具方法：列表格式化（通用）
    
    def format_list_evidence(
        self,
        evidence_text: str,
        query: str
    ) -> str:
        """
        格式化列表证据（通用方法）
        
        Args:
            evidence_text: 证据文本
            query: 查询文本
            
        Returns:
            格式化后的列表文本
        """
        if not self.preprocessor:
            return evidence_text
        
        return self.preprocessor.format_list_evidence(evidence_text, query)

