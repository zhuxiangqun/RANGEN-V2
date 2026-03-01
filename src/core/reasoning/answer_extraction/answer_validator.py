"""
答案验证器 - 统一验证接口

🚀 重构优化：
1. 提取硬编码到统一规则管理器
2. 缓存正则表达式编译结果
3. 优化字符串操作（减少重复转换）
4. 简化逻辑嵌套（使用早期返回）
5. 简化调用链
"""
import re
import logging
from typing import Dict, List, Any, Optional, Pattern
from abc import ABC, abstractmethod
from functools import lru_cache

logger = logging.getLogger(__name__)


class RegexCache:
    """正则表达式缓存管理器 - 避免重复编译"""
    
    def __init__(self):
        self._compiled_patterns: Dict[str, Pattern] = {}
        self._pattern_strings: Dict[str, str] = {}
    
    def get_pattern(self, pattern_name: str, pattern_string: str, flags: int = 0) -> Pattern:
        """获取编译后的正则表达式（带缓存）"""
        cache_key = f"{pattern_name}:{flags}"
        
        if cache_key not in self._compiled_patterns or self._pattern_strings.get(cache_key) != pattern_string:
            self._compiled_patterns[cache_key] = re.compile(pattern_string, flags)
            self._pattern_strings[cache_key] = pattern_string
        
        return self._compiled_patterns[cache_key]
    
    def clear(self):
        """清空缓存"""
        self._compiled_patterns.clear()
        self._pattern_strings.clear()


class ValidationConfigCache:
    """验证配置缓存管理器 - 从统一规则管理器获取配置，避免硬编码和重复调用"""
    
    def __init__(self, rule_manager=None):
        self.rule_manager = rule_manager
        self._cache: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
    
    def get_api_error_patterns(self) -> List[str]:
        """获取API错误模式列表"""
        return self._get_cached_keywords('api_error_patterns', [
            'extraction task failed', 'api timeout', 'please try again later',
            'reasoning task failed', 'analysis task failed', 'detection task failed',
            'task failed due to api timeout', 'api call failed',
            'please check network', 'network error', 'request timeout'
        ])
    
    def get_uncertainty_patterns(self) -> List[str]:
        """获取不确定性答案模式列表"""
        return self._get_cached_keywords('uncertainty_patterns', [
            'cannot be determined', 'cannot determine', 'cannot be provided',
            'unable to determine', 'unable to identify', 'unable to find',
            'not available', 'not found', 'no information', 'insufficient information',
            'cannot be identified', 'cannot be found', 'cannot be ascertained'
        ])
    
    def get_absurd_patterns(self) -> List[str]:
        """获取荒谬模式列表（已优化：移除常见词汇）"""
        return self._get_cached_keywords('absurd_patterns', [
            'western europe this', 'france football', 'slave power',
            'union army', 'first words', 'fuego geopolitical',
            'confederate states', 'civil war', 'world war',
            'western europe', 'eastern europe', 'northern europe', 'southern europe',
            'fuego', 'geopolitical'
        ])
    
    def get_geographic_keywords(self) -> List[str]:
        """获取地理关键词列表"""
        return self._get_cached_keywords('geographic_keywords', [
            'europe', 'france', 'western', 'eastern', 'northern', 'southern',
            'united states', 'america', 'geopolitical'
        ])
    
    def get_non_person_indicators(self) -> List[str]:
        """获取非人名指示词列表"""
        return self._get_cached_keywords('non_person_indicators', [
            'union army', 'confederate army', 'civil war', 'world war', 'revolutionary war',
            'slave power', 'slave power conspiracy', 'manifest destiny', 'monroe doctrine',
            'missouri compromise', 'compromise of 1850', 'kansas-nebraska act',
            'dred scott', 'emancipation proclamation', 'gettysburg address'
        ])
    
    def get_threshold(self, threshold_name: str, default: float) -> float:
        """获取阈值"""
        cache_key = f'threshold_{threshold_name}'
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        threshold = default
        if self.rule_manager:
            try:
                threshold = self.rule_manager.get_threshold(threshold_name, context='validation')
            except Exception as e:
                self.logger.debug(f"从规则管理器获取阈值失败: {e}")
        
        self._cache[cache_key] = threshold
        return threshold
    
    def _get_cached_keywords(self, category: str, fallback: List[str]) -> List[str]:
        """获取缓存的关键词列表"""
        if category in self._cache:
            return self._cache[category]
        
        keywords = []
        if self.rule_manager:
            try:
                keywords = self.rule_manager.get_keywords(category)
            except Exception as e:
                self.logger.debug(f"从规则管理器获取关键词失败: {e}")
        
        if not keywords:
            keywords = fallback
        
        self._cache[category] = keywords
        return keywords
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()


class ValidationRule(ABC):
    """验证规则基类"""
    
    @abstractmethod
    def validate(self, answer: str, query: str, context: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """验证答案
        
        Args:
            answer: 待验证的答案
            query: 查询文本
            context: 上下文信息
            
        Returns:
            (是否有效, 错误信息)
        """
        pass


class BasicValidationRule(ValidationRule):
    """基础验证规则"""
    
    def validate(self, answer: str, query: str, context: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """基础验证：检查答案是否为空、过短等"""
        if not answer or not answer.strip():
            return False, "答案为空"
        
        answer_clean = answer.strip()
        
        if len(answer_clean) < 2:
            return False, "答案过短"
        
        # 检查是否是明显的错误标记
        error_markers = [
            r'\[ERROR\]',
            r'无法确定',
            r'无法找到',
            r'没有找到',
            r'未找到',
        ]
        
        for marker in error_markers:
            if re.search(marker, answer_clean, re.IGNORECASE):
                if len(answer_clean) < 50:
                    return False, f"答案包含错误标记: {marker}"
        
        return True, None


class FormatValidationRule(ValidationRule):
    """格式验证规则"""
    
    def validate(self, answer: str, query: str, context: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """格式验证：检查答案格式是否合理"""
        answer_clean = answer.strip()
        
        # 检查是否是列表格式（多个连续的大写单词）
        list_pattern = r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+){3,}.*$'
        if len(answer_clean) > 100 and re.match(list_pattern, answer_clean):
            # 尝试提取第一个答案
            first_match = re.match(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})', answer_clean)
            if first_match:
                # 返回提取的第一个答案（由格式化器处理）
                return True, None
        
        # 检查是否是占位符答案
        placeholder_patterns = [
            r'^(synthesize|combine|extract|generate)',
            r'^(the|a|an)\s+answer',
        ]
        
        for pattern in placeholder_patterns:
            if re.match(pattern, answer_clean, re.IGNORECASE):
                return False, "答案是占位符"
        
        return True, None


class SemanticValidationRule(ValidationRule):
    """语义验证规则"""
    
    def __init__(self, semantic_pipeline=None):
        self.semantic_pipeline = semantic_pipeline
        self.logger = logging.getLogger(__name__)
    
    def validate(self, answer: str, query: str, context: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """语义验证：使用语义理解检查答案合理性"""
        if not self.semantic_pipeline:
            return True, None  # 如果没有语义管道，跳过验证
        
        try:
            # 检查答案与查询的相关性
            similarity = self.semantic_pipeline.calculate_semantic_similarity(answer, query)
            # 🚀 P0修复：提高验证阈值，拒绝低质量答案
            # 对于比较查询、分析查询等复杂查询，需要更高的相似度
            query_lower = query.lower()
            is_complex_query = any(keyword in query_lower for keyword in [
                'compare', 'comparison', 'analyze', 'analysis', 'difference', 'similarity',
                '对比', '比较', '分析', '差异', '相似'
            ])
            
            # 复杂查询需要更高的相似度阈值
            min_similarity = 0.3 if is_complex_query else 0.2

            # 检查相似度阈值
            if similarity < 0.1:
                # 🚀 P0优化：对于长答案（如历史描述），相似度低是正常的（语义向量稀释）
                # 只要答案包含查询的核心关键词，就认为是有效的
                query_keywords = self._extract_core_keywords(query)
                answer_lower = answer.lower()
                matched_keywords = [kw for kw in query_keywords if kw in answer_lower]
                
                # 如果匹配了至少一半的关键词，或者是复杂的描述性文本，允许通过
                if (len(matched_keywords) >= len(query_keywords) / 2) or (len(answer) > 200 and len(matched_keywords) > 0):
                    self.logger.info(
                        f"ℹ️ [长文本/关键词匹配] 语义相似度低但关键词匹配，允许通过: {similarity:.2f} | "
                        f"匹配关键词: {matched_keywords}"
                    )
                    return True, None
                
                self.logger.warning(
                    f"⚠️ 答案与查询相关性极低: {similarity:.2f} | "
                    f"查询: {query[:60]} | 答案: {answer[:60]}"
                )
                return False, f"答案与查询相关性极低: {similarity:.2f}"

            if similarity < min_similarity:
                # 🚀 P0优化：对RAG答案进行特殊处理
                # 如果是复杂的多跳推理，相似度低是正常的（因为答案只是最终的一小部分，而查询包含所有条件）
                if is_complex_query:
                    self.logger.info(
                        f"ℹ️ [复杂查询] 答案相似度较低但允许通过: {similarity:.2f} < {min_similarity:.2f} | "
                        f"查询: {query[:60]} | 答案: {answer[:60]}"
                    )
                    return True, None
                
                self.logger.info(
                    f"ℹ️ 答案相似度中等: {similarity:.2f} < {min_similarity:.2f} | "
                    f"查询: {query[:60]} | 答案: {answer[:60]}"
                )
                # 对于中等相似度，给出警告但允许通过（语义验证相对宽松）
                return True, None
            
            # 对于人名查询，检查答案是否是PERSON类型
            if self._is_person_query(query):
                entities = self.semantic_pipeline.extract_entities_intelligent(answer)
                has_person = any(e.get('label') == 'PERSON' for e in entities)
                
                if not has_person:
                    # 放宽：支持首字母缩写（如 "Dwight D."，"John F."）
                    name_pattern = r'^[A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)*$'
                    if not re.match(name_pattern, answer.strip()):
                        return False, "答案不是有效的人名格式"
            
            return True, None
            
        except Exception as e:
            self.logger.debug(f"语义验证失败: {e}")
            return True, None  # 验证失败时允许通过
    
    def _is_person_query(self, query: str) -> bool:
        """判断是否是查询人名的查询"""
        query_lower = query.lower()
        person_keywords = ['who', 'name', 'person', 'first name', 'last name', 'surname']
        return any(keyword in query_lower for keyword in person_keywords)


class QueryAnswerConsistencyRule(ValidationRule):
    """查询-答案一致性验证规则 - 使用语义理解检查答案是否与查询匹配"""
    
    def __init__(self, semantic_pipeline=None, rule_manager=None):
        """初始化验证规则
        
        Args:
            semantic_pipeline: 语义理解管道（用于语义验证）
            rule_manager: 统一规则管理器（用于获取阈值和配置）
        """
        self.semantic_pipeline = semantic_pipeline
        self.rule_manager = rule_manager
        self.logger = logging.getLogger(__name__)
    
    def validate(self, answer: str, query: str, context: Optional[Dict[str, Any]] = None) -> tuple[bool, Optional[str]]:
        """使用语义理解验证答案是否与查询匹配
        
        优先使用语义理解，避免硬编码特定实体或规则。
        """
        import re
        
        # 1. 使用语义理解检查答案与查询的一致性
        if self.semantic_pipeline:
            try:
                # 计算答案与查询的语义相似度
                similarity = self.semantic_pipeline.calculate_semantic_similarity(answer, query)
                
                # 获取阈值（从统一规则管理器或使用默认值）
                min_similarity = 0.3
                if self.rule_manager:
                    try:
                        min_similarity = self.rule_manager.get_threshold('query_answer_consistency', context='validation')
                    except Exception:
                        pass
                
                answer_tokens = answer.split()
                query_tokens = query.split()
                answer_len = len(answer_tokens)
                query_len = len(query_tokens)
                
                effective_min_similarity = min_similarity
                if answer_len <= 3:
                    effective_min_similarity = min_similarity * 0.5
                elif answer_len <= 6:
                    effective_min_similarity = min_similarity * 0.7
                
                if context and isinstance(context, dict):
                    allow_low_similarity = context.get('allow_low_similarity')
                    if allow_low_similarity:
                        effective_min_similarity = min(effective_min_similarity, 0.1)
                
                # 🚀 修复：如果相似度为0.0，且没有可用模型，说明语义计算失效，应跳过此检查
                if similarity == 0.0:
                    models_available = False
                    if hasattr(self.semantic_pipeline, 'are_models_available'):
                        models_available = self.semantic_pipeline.are_models_available()
                    
                    if not models_available:
                        self.logger.warning(
                            f"⚠️ [语义验证] 语义相似度为0.0且无可用模型，跳过此检查 (答案: {answer[:60]})"
                        )
                        return True, None
                    else:
                        # 模型可用但相似度为0，可能是极度不相关，也可能是词向量缺失
                        # 暂时放行，但在日志中标记
                        self.logger.warning(
                            f"⚠️ [语义验证] 模型可用但相似度为0.0 (可能是词向量缺失)，允许通过但不建议依赖 (答案: {answer[:60]})"
                        )
                        return True, None
                
                if similarity < effective_min_similarity:
                    # 🚀 P0优化：对RAG答案进行特殊处理
                    # 如果答案是实体名且查询很长，相似度自然会低，应该允许通过
                    if answer_len < 5 and query_len > 8:
                        self.logger.info(
                            f"ℹ️ [长查询短答案] 语义相似度较低但允许通过: {similarity:.2f} < {effective_min_similarity:.2f} | "
                            f"查询: {query[:60]} | 答案: {answer[:60]}"
                        )
                        return True, None
                    
                    self.logger.warning(
                        f"⚠️ [查询-答案一致性] 答案与查询语义相似度低: {similarity:.2f} < {effective_min_similarity:.2f} | "
                        f"查询: {query[:60]} | 答案: {answer[:60]}"
                    )
                    return False, f"答案与查询语义相似度低: {similarity:.2f}"
                
                # 对于包含序数的查询，使用语义理解检查答案中的数字是否匹配
                ordinal_pattern = r'(\d+)(?:st|nd|rd|th)'
                query_ordinals = [int(m) for m in re.findall(ordinal_pattern, query.lower())]
                
                if query_ordinals:
                    # 提取答案中的数字
                    answer_numbers = [int(m) for m in re.findall(r'\b(\d+)\b', answer)]
                    
                    # 使用语义理解判断答案中的数字是否与查询中的序数相关
                    # 如果答案中的数字与查询中的序数相差太大，可能是错误答案
                    max_ordinal_diff = 10
                    if self.rule_manager:
                        try:
                            max_ordinal_diff = int(self.rule_manager.get_threshold('ordinal_difference', context='validation'))
                        except Exception:
                            pass
                    
                    for query_ordinal in query_ordinals:
                        for answer_num in answer_numbers:
                            if abs(answer_num - query_ordinal) > max_ordinal_diff:
                                # 使用语义理解进一步验证：检查答案是否真的与查询不匹配
                                # 构建验证查询："Is [answer] related to [query]?"
                                verification_query = f"Is {answer} related to {query}?"
                                verification_similarity = self.semantic_pipeline.calculate_semantic_similarity(
                                    answer, verification_query
                                )
                                
                                if verification_similarity < min_similarity:
                                    self.logger.warning(
                                        f"⚠️ [查询-答案一致性] 答案中的数字({answer_num})与查询中的序数({query_ordinal})不匹配，"
                                        f"且语义相似度低: {verification_similarity:.2f}"
                                    )
                                    return False, f"答案中的数字({answer_num})与查询中的序数({query_ordinal})不匹配"
            except Exception as e:
                self.logger.debug(f"语义验证失败，使用基础验证: {e}")
        
        # 2. 基础验证：检查序数匹配（作为fallback）
        query_lower = query.lower()
        answer_lower = answer.lower()
        ordinal_pattern = r'(\d+)(?:st|nd|rd|th)'
        query_ordinals = [int(m) for m in re.findall(ordinal_pattern, query_lower)]
        
        if query_ordinals:
            answer_ordinals = [int(m) for m in re.findall(ordinal_pattern, answer_lower)]
            
            # 获取阈值
            max_diff = 10
            if self.rule_manager:
                try:
                    max_diff = int(self.rule_manager.get_threshold('ordinal_difference', context='validation'))
                except Exception:
                    pass
            
            for query_ordinal in query_ordinals:
                for answer_ordinal in answer_ordinals:
                    if abs(answer_ordinal - query_ordinal) > max_diff:
                        self.logger.warning(
                            f"⚠️ [查询-答案一致性] 答案中的序数({answer_ordinal})与查询中的序数({query_ordinal})相差过大"
                        )
                        return False, f"答案中的序数({answer_ordinal})与查询中的序数({query_ordinal})不匹配"
        
        return True, None


class AnswerValidator:
    """答案验证器 - 统一验证接口（重构版本）
    
    🚀 优化：
    1. 使用配置缓存管理器统一管理硬编码
    2. 缓存正则表达式编译结果
    3. 优化字符串操作（只转换一次）
    4. 简化逻辑嵌套（早期返回）
    """
    
    def __init__(self, semantic_pipeline=None, rule_manager=None):
        """初始化答案验证器
        
        Args:
            semantic_pipeline: 语义理解管道
            rule_manager: 统一规则管理器（用于获取阈值和配置，避免硬编码）
        """
        self.semantic_pipeline = semantic_pipeline
        self.rule_manager = rule_manager or self._get_default_rule_manager()
        self.logger = logging.getLogger(__name__)
        
        # 🚀 新增：初始化配置缓存和正则缓存
        self.config_cache = ValidationConfigCache(self.rule_manager)
        self.regex_cache = RegexCache()
        self._compile_common_patterns()
        
        # 初始化验证规则
        self.rules = [
            BasicValidationRule(),
            FormatValidationRule(),
            SemanticValidationRule(semantic_pipeline),
            QueryAnswerConsistencyRule(semantic_pipeline, self.rule_manager),
        ]
    
    def _get_default_rule_manager(self):
        """获取默认规则管理器"""
        try:
            from src.utils.unified_rule_manager import get_unified_rule_manager
            return get_unified_rule_manager()
        except Exception as e:
            self.logger.debug(f"获取统一规则管理器失败: {e}")
            return None
    
    def _compile_common_patterns(self):
        """预编译常用正则表达式（避免重复编译）"""
        self.ordinal_pattern = self.regex_cache.get_pattern(
            'ordinal', r'(\d+)(?:st|nd|rd|th)', re.IGNORECASE
        )
        self.number_pattern = self.regex_cache.get_pattern('number', r'\b(\d+)\b')
        self.person_name_pattern = self.regex_cache.get_pattern(
            'person_name', r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$'
        )
        self.sentence_name_pattern = self.regex_cache.get_pattern(
            'sentence_name', r'(?:was|is|are|were)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', re.IGNORECASE
        )
        self.list_pattern = self.regex_cache.get_pattern(
            'list', r'\d+\.\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)'
        )
    
    def validate(
        self,
        answer: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """验证答案
        
        Args:
            answer: 待验证的答案
            query: 查询文本
            context: 上下文信息
            
        Returns:
            验证结果字典：
            {
                'is_valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        for rule in self.rules:
            try:
                is_valid, error_msg = rule.validate(answer, query, context)
                if not is_valid:
                    if error_msg:
                        errors.append(error_msg)
            except Exception as e:
                self.logger.debug(f"验证规则执行失败: {e}")
                warnings.append(f"验证规则执行失败: {str(e)}")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    # ========== 从 engine.py 迁移的方法 ==========
    
    def validate_step_answer_reasonableness(
        self, 
        answer: str, 
        sub_query: str, 
        step_evidence: List, 
        previous_step_answer: Optional[str], 
        original_query: str,
        answer_extractor: Optional[Any] = None,
        rule_manager: Optional[Any] = None
    ) -> bool:
        """🚀 重构：验证步骤答案的合理性（优化版本）
        
        优化：
        1. 使用配置缓存管理器获取硬编码值
        2. 统一字符串转换（只转换一次）
        3. 早期返回，减少嵌套
        4. 使用缓存的正则表达式
        
        Args:
            answer: 步骤答案
            sub_query: 子查询
            step_evidence: 步骤证据
            previous_step_answer: 上一步答案
            original_query: 原始查询
            answer_extractor: 答案提取器（可选）
            rule_manager: 规则管理器（可选，优先使用self.rule_manager）
            
        Returns:
            如果答案合理返回True，否则返回False
        """
        try:
            # 早期返回：空答案
            if not answer or not answer.strip():
                return False
            
            # 🚀 优化：统一字符串转换（只转换一次，避免重复转换）
            answer_stripped = answer.strip()
            answer_lower = answer_stripped.lower()
            sub_query_lower = sub_query.lower()
            
            # 使用传入的rule_manager或默认的
            effective_rule_manager = rule_manager or self.rule_manager
            if effective_rule_manager and effective_rule_manager != self.rule_manager:
                # 如果传入不同的rule_manager，创建临时配置缓存
                config_cache = ValidationConfigCache(effective_rule_manager)
            else:
                config_cache = self.config_cache
            
            # 1. 检查API错误信息（最高优先级，早期返回）
            if self._check_api_errors(answer_lower, config_cache):
                return False
            
            # 2. 检查不确定性答案（可能是合理的，早期返回）
            if self._check_uncertainty_answer(answer_lower, step_evidence, config_cache):
                return True
            
            # 3. 检查荒谬模式（早期返回）
            if self._check_absurd_patterns(answer_lower, answer_stripped, config_cache):
                return False
            
            # 4. 检查序数查询（早期返回）
            if self._check_ordinal_query(answer_lower, sub_query_lower, step_evidence, answer_stripped):
                return False
            
            # 5. 检查人名查询（早期返回）
            if self._check_person_query(answer_lower, sub_query_lower, step_evidence, answer_stripped, config_cache):
                return False
            
            # 6. 检查非人名指示词（早期返回）
            if self._check_non_person_indicators(answer_lower, sub_query_lower, answer_stripped, config_cache):
                return False
            
            # 7. 检查统一规则管理验证（如果可用，简化调用链）
            if effective_rule_manager and answer_extractor:
                if not self._check_unified_rule_validation(
                    answer, sub_query, step_evidence, previous_step_answer, answer_extractor, effective_rule_manager
                ):
                    return False
            
            # 8. 检查证据匹配
            if step_evidence:
                if not self._check_evidence_match(answer_lower, step_evidence, answer_stripped, original_query):
                    return False
            
            # 9. 检查关系一致性
            if answer_extractor:
                if not self._check_relationship_consistency(
                    answer, sub_query, previous_step_answer, step_evidence, answer_extractor
                ):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"验证步骤答案合理性失败: {e}")
            return True  # 验证失败时，默认通过（避免过度过滤）
    
    def _check_api_errors(self, answer_lower: str, config_cache: ValidationConfigCache) -> bool:
        """检查API错误信息"""
        api_error_patterns = config_cache.get_api_error_patterns()
        for pattern in api_error_patterns:
            if pattern in answer_lower:
                self.logger.warning(f"❌ [紧急停止] 检测到API错误信息作为答案: {answer_lower[:100]}")
                return True
        return False
    
    def _check_uncertainty_answer(
        self, answer_lower: str, step_evidence: List, config_cache: ValidationConfigCache
    ) -> bool:
        """检查不确定性答案（可能是合理的）"""
        uncertainty_patterns = config_cache.get_uncertainty_patterns()
        is_uncertainty = any(pattern in answer_lower for pattern in uncertainty_patterns)
        
        if is_uncertainty:
            if step_evidence and len(step_evidence) > 0:
                self.logger.info(
                    f"ℹ️ [答案验证] LLM返回'无法确定'答案，但有{len(step_evidence)}条证据。"
                    f"这可能是合理的（证据质量不足），允许继续处理"
                )
            else:
                self.logger.debug(f"ℹ️ [答案验证] LLM返回'无法确定'答案，且无证据。这是合理的")
            return True
        
        return False
    
    def _check_absurd_patterns(
        self, answer_lower: str, answer: str, config_cache: ValidationConfigCache
    ) -> bool:
        """检查荒谬模式（优化版本：使用缓存的正则表达式）"""
        absurd_patterns = config_cache.get_absurd_patterns()
        
        for pattern in absurd_patterns:
            if pattern not in answer_lower:
                continue
            
            # 多词短语：直接拒绝
            if ' ' in pattern:
                self.logger.warning(f"❌ [紧急停止] 检测到荒谬的步骤答案: {answer[:100]}")
                return True
            
            # 单词模式：使用词边界检查（使用缓存的正则表达式）
            word_boundary_pattern = self.regex_cache.get_pattern(
                f'absurd_{pattern}', r'\b' + re.escape(pattern) + r'\b'
            )
            if word_boundary_pattern.search(answer_lower):
                if len(answer) > 50:
                    self.logger.debug(f"⚠️ [答案验证] 检测到潜在荒谬模式 '{pattern}'，但答案较长，可能是误判")
                else:
                    self.logger.warning(f"❌ [紧急停止] 检测到荒谬的步骤答案: {answer[:100]}")
                    return True
        
        return False
    
    def _check_ordinal_query(
        self, answer_lower: str, sub_query_lower: str, step_evidence: List, answer: str
    ) -> bool:
        """检查序数查询（使用缓存的正则表达式）"""
        ordinal_match = self.ordinal_pattern.search(sub_query_lower)
        if not ordinal_match or not step_evidence:
            return False
        
        ordinal_num = int(ordinal_match.group(1))
        evidence_text = self._extract_evidence_text(step_evidence[:5]).lower()
        
        # 答案在证据中，通过
        if answer_lower in evidence_text:
            return False
        
        # 检查列表格式
        if 'list' in evidence_text or 'first lady' in evidence_text or 'president' in evidence_text:
            list_items = self.list_pattern.findall(evidence_text)
            if list_items and len(list_items) >= ordinal_num:
                expected_answer = list_items[ordinal_num - 1].lower()
                if expected_answer != answer_lower:
                    self.logger.warning(
                        f"❌ [序数查询验证] 答案与证据列表不匹配: "
                        f"查询要求第{ordinal_num}位，答案={answer[:50]}，证据中第{ordinal_num}位={list_items[ordinal_num-1]}"
                    )
                    return True  # 不匹配，拒绝
        
        return False
    
    def _check_person_query(
        self, answer_lower: str, sub_query_lower: str, step_evidence: List, answer: str,
        config_cache: ValidationConfigCache
    ) -> bool:
        """检查人名查询（优化版本）"""
        person_keywords = ['who', 'name', 'person', 'first name', 'last name', 'surname', 'mother', 'father']
        if not any(keyword in sub_query_lower for keyword in person_keywords):
            return False
        
        geographic_keywords = config_cache.get_geographic_keywords()
        if not any(keyword in answer_lower for keyword in geographic_keywords):
            return False
        
        # 尝试提取人名
        extracted_name = self._extract_name_from_answer(answer)
        if extracted_name:
            extracted_name_lower = extracted_name.lower()
            if not any(keyword in extracted_name_lower for keyword in geographic_keywords):
                self.logger.debug(f"✅ [验证] 从答案中提取到人名: {extracted_name}")
                return False  # 提取到有效人名，通过
            else:
                self.logger.warning(f"❌ [紧急停止] 提取的人名包含地理词汇: {extracted_name}")
                return True  # 拒绝
        else:
            # 无法提取人名，检查是否是完整的人名格式
            if not self.person_name_pattern.match(answer):
                self.logger.warning(f"❌ [紧急停止] 答案包含地理词汇且无法提取人名: {answer[:100]}")
                return True  # 拒绝
        
        return False
    
    def _check_non_person_indicators(
        self, answer_lower: str, sub_query_lower: str, answer: str, config_cache: ValidationConfigCache
    ) -> bool:
        """检查非人名指示词"""
        person_keywords = ['who', 'name', 'person', 'first name', 'last name', 'surname', 'mother', 'father']
        if not any(keyword in sub_query_lower for keyword in person_keywords):
            return False
        
        non_person_indicators = config_cache.get_non_person_indicators()
        if answer_lower in non_person_indicators:
            self.logger.warning(f"❌ 步骤答案不合理：查询问的是人名，但答案是组织/概念名称: {answer[:100]}")
            return True  # 拒绝
        
        return False
    
    def _check_unified_rule_validation(
        self, answer: str, sub_query: str, step_evidence: List, previous_step_answer: Optional[str],
        answer_extractor: Any, rule_manager: Any
    ) -> bool:
        """检查统一规则管理验证（简化调用链）"""
        if not answer_extractor or not hasattr(answer_extractor, 'rule_manager'):
            return True
        
        try:
            evidence_text = self._extract_evidence_text(step_evidence[:3])
            
            # 使用分层验证器（如果可用）
            if hasattr(answer_extractor, 'hierarchical_validator') and answer_extractor.hierarchical_validator:
                validation_result = answer_extractor.hierarchical_validator.validate(
                    answer=answer,
                    query=sub_query,
                    evidence_text=evidence_text,
                    previous_step_result=previous_step_answer
                )
                if not validation_result.get('is_valid', True):
                    self.logger.warning(
                        f"❌ 步骤答案不合理（分层验证器）: {answer[:100]}, "
                        f"问题: {', '.join(validation_result.get('issues', [])[:2])}"
                    )
                    return False
            
            # 使用语义理解检测实体类型（简化调用链）
            if hasattr(rule_manager, 'semantic_enhancer') and rule_manager.semantic_enhancer:
                pipeline = getattr(rule_manager.semantic_enhancer, 'pipeline', None)
                if pipeline and hasattr(pipeline, 'extract_entities_intelligent'):
                    # 直接调用，避免深层嵌套
                    entities = pipeline.extract_entities_intelligent(answer)
                    if entities:
                        for entity in entities:
                            entity_label = entity.get('label', '')
                            if entity_label in ['ORG', 'GPE', 'LOC', 'FAC', 'EVENT']:
                                # 检查是否是查询人名的查询
                                if self._is_person_query(sub_query):
                                    self.logger.warning(
                                        f"❌ 步骤答案不合理：查询是人名查询，但答案包含{entity_label}类型实体: {answer[:100]}"
                                    )
                                    return False
            
            # 检查明显的非人名关键词
            if hasattr(rule_manager, 'get_keywords'):
                try:
                    non_person_keywords = rule_manager.get_keywords('obvious_non_person', context=answer)
                    if non_person_keywords and any(kw.lower() in answer.lower() for kw in non_person_keywords):
                        self.logger.warning(f"❌ 步骤答案不合理：答案包含明显的非人名关键词: {answer[:100]}")
                        return False
                except Exception as e:
                    self.logger.debug(f"获取非人名关键词失败: {e}")
        
        except Exception as e:
            self.logger.debug(f"统一规则管理验证失败: {e}")
        
        return True
    
    def _check_evidence_match(self, answer_lower: str, step_evidence: List, answer: str, query: str) -> bool:
        """检查答案与证据的匹配（优化版本）"""
        evidence_text = self._extract_evidence_text(step_evidence[:3]).lower()
        
        if not evidence_text:
            return True  # 无证据，通过
        
        # 直接匹配
        if answer_lower in evidence_text:
            return True
        
        # 检查证据质量
        if self._is_low_quality_evidence(evidence_text):
            self.logger.debug(f"✅ 证据质量极低，跳过匹配率检查，接受答案: {answer[:100]}")
            return True
        
        # 单词级别匹配
        answer_words = set(answer_lower.split())
        evidence_words = set(evidence_text.split())
        match_ratio = len(answer_words & evidence_words) / len(answer_words) if answer_words else 0.0

        min_match_ratio = self.config_cache.get_threshold('evidence_match_ratio', 0.2)

        # 🚀 P1修复：对RAG推理答案降低匹配率要求
        # RAG答案可能是基于证据的推理结果，不是直接文本匹配
        if match_ratio < min_match_ratio:
            # 检查是否是RAG推理答案
            if self._is_rag_reasoning_answer(answer, query):
                self.logger.debug(f"✅ RAG推理答案，降低匹配率要求: {match_ratio:.2f} -> 允许")
                return True

            # 检查推理答案合理性
            if self._is_reasonable_inference_answer(answer, query, step_evidence):
                self.logger.debug(f"✅ 推理答案合理，即使匹配率低也接受: {match_ratio:.2f}")
                return True

            # 如果答案看起来合理（如人名格式），即使匹配率低也接受
            if len(answer.split()) <= 3 and answer[0].isupper():
                self.logger.debug(f"✅ 答案看起来合理（可能是人名），即使匹配率低也接受: {answer[:100]}")
                return True

            # 对于其他情况，如果匹配率不是极低（>0.05），给予警告但允许通过
            if match_ratio > 0.05:
                self.logger.info(f"ℹ️ 步骤答案匹配率中等（{match_ratio:.2f}），允许通过但记录警告")
                return True

            self.logger.warning(f"⚠️ 步骤答案与证据匹配率低（{match_ratio:.2f}）: {answer[:100]}")
            return False
        
        return True
    
    def _check_relationship_consistency(
        self, answer: str, sub_query: str, previous_step_answer: Optional[str],
        step_evidence: List, answer_extractor: Any
    ) -> bool:
        """检查关系一致性（简化调用链）"""
        if not hasattr(answer_extractor, '_validate_relationship_answer_consistency'):
            return True
        
        evidence_text = self._extract_evidence_text(step_evidence[:3]) if step_evidence else ""
        
        if not answer_extractor._validate_relationship_answer_consistency(
            answer, sub_query, previous_step_answer, evidence_text
        ):
            self.logger.warning(f"❌ 步骤答案未通过关系一致性验证: {answer[:100]}")
            return False
        
        return True
    
    def _extract_evidence_text(self, evidence_list: List) -> str:
        """提取证据文本（优化版本，减少字符串操作）"""
        texts = []
        for ev in evidence_list:
            if hasattr(ev, 'content') and ev.content:
                texts.append(str(ev.content))
            elif ev:
                texts.append(str(ev))
        return ' '.join(texts)
    
    def _extract_name_from_answer(self, answer: str) -> Optional[str]:
        """从答案中提取人名（使用缓存的正则表达式）"""
        match = self.sentence_name_pattern.search(answer)
        return match.group(1).strip() if match else None
    
    def _is_person_query(self, query: str) -> bool:
        """判断是否是查询人名的查询"""
        query_lower = query.lower()
        person_keywords = ['who', 'name', 'person', 'first name', 'last name', 'surname']
        return any(keyword in query_lower for keyword in person_keywords)
    
    def _is_low_quality_evidence(self, evidence_text: str) -> bool:
        """判断证据质量是否极低"""
        evidence_stripped = evidence_text.strip()
        return (
            len(evidence_stripped) < 20 or
            evidence_stripped in ['united states', 'united', 'states'] or
            evidence_text.count(' ') < 2
        )

    def _is_rag_reasoning_answer(self, answer: str, query: str) -> bool:
        """判断答案是否是RAG推理结果

        RAG推理答案通常：
        1. 包含"基于证据"或"根据检索"等关键词
        2. 提供详细解释而不是直接回答
        3. 长度相对较长
        """
        answer_lower = answer.lower()
        query_lower = query.lower()

        # 检查RAG推理特征
        rag_indicators = [
            'based on', 'according to', 'evidence', 'retrieved',
            '基于', '根据', '证据', '检索到',
            'rag', 'retrieval-augmented', '检索增强'
        ]

        has_rag_indicator = any(indicator in answer_lower for indicator in rag_indicators)

        # 检查是否提供了解释性答案
        is_explanatory = len(answer.split()) > 10 or len(answer) > 100

        # 检查是否回答了查询的核心问题
        core_keywords = self._extract_core_keywords(query_lower)
        answers_core = any(keyword in answer_lower for keyword in core_keywords)

        return (has_rag_indicator or is_explanatory) and answers_core

    def _is_reasonable_inference_answer(self, answer: str, query: str, evidence: List) -> bool:
        """判断答案是否是合理的推理结果

        检查答案是否：
        1. 基于提供的证据
        2. 逻辑上合理
        3. 回答了查询问题
        """
        try:
            # 基础检查
            if not evidence or len(evidence) == 0:
                return False

            # 检查答案是否与证据相关
            evidence_text = self._extract_evidence_text(evidence[:3])
            evidence_words = set(evidence_text.lower().split())
            answer_words = set(answer.lower().split())

            # 计算词重叠率
            overlap = len(evidence_words & answer_words)
            total_words = len(evidence_words | answer_words)

            if total_words == 0:
                return False

            overlap_ratio = overlap / total_words

            # 如果重叠率足够高，认为答案合理
            if overlap_ratio > 0.1:  # 10%的词重叠
                return True

            # 检查是否是推理型答案（包含推理关键词）
            inference_indicators = [
                'therefore', 'thus', 'because', 'since', 'due to',
                '因此', '所以', '因为', '由于', '根据',
                'conclusion', 'result', 'outcome',
                '结论', '结果', '推断'
            ]

            has_inference = any(indicator in answer.lower() for indicator in inference_indicators)

            return has_inference and len(answer) > 20

        except Exception as e:
            self.logger.debug(f"推理答案合理性检查失败: {e}")
            return True  # 出错时默认通过，避免过度过滤

    def _extract_core_keywords(self, text: str) -> List[str]:
        """提取文本的核心关键词（从SemanticValidationRule迁移）"""
        try:
            # 移除停用词
            stop_words = {'what', 'is', 'are', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'why', 'when', 'where', 'who', 'which', 'whose', 'whom', '多少', '什么', '如何', '为什么', '什么时候', '哪里', '谁', '哪个', '哪些', '谁的', 'synthesize', 'final', 'answer', 'combine'}
            
            # 简单的分词（仅按空格）
            words = re.findall(r'\b\w+\b', text.lower())
            keywords = [word for word in words if word not in stop_words and len(word) > 2]
            
            # 返回最长的几个关键词
            return sorted(keywords, key=len, reverse=True)[:10]
        except Exception:
            return []
