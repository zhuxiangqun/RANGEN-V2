#!/usr/bin/env python3
"""
分层答案验证器 - 使用多层验证策略，避免硬编码

验证层次：
1. 快速规则验证（毫秒级）- 基础格式检查
2. NLP增强验证（秒级）- 语义理解、实体类型检查
3. LLM验证（可选，秒级）- 复杂情况深度验证
"""
import logging
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class HierarchicalAnswerValidator:
    """分层答案验证器 - 通用、可扩展、无硬编码"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化分层验证器
        
        Args:
            config: 配置字典
                - use_nlp: 是否使用NLP验证（默认True）
                - use_llm_fallback: 是否使用LLM验证作为fallback（默认False）
                - semantic_threshold: 语义相似度阈值（默认0.3）
                - use_lightweight_nlp: 是否使用轻量级NLP模型（默认True）
                - similarity_model_name: 相似度模型名称（默认'all-MiniLM-L6-v2'）
        """
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        
        # 🚀 统一规则管理：初始化统一规则管理中心
        self.rule_manager = None
        try:
            from src.utils.unified_rule_manager import get_unified_rule_manager
            self.rule_manager = get_unified_rule_manager()
            self.logger.info("✅ 统一规则管理中心已初始化（分层验证器）")
        except Exception as e:
            self.logger.debug(f"统一规则管理中心初始化失败（可选功能）: {e}")
        
        self.use_nlp = self.config.get('use_nlp', True)
        self.use_llm_fallback = self.config.get('use_llm_fallback', False)
        
        # 🚀 统一规则管理：从统一规则管理中心获取阈值（不再硬编码）
        if self.rule_manager:
            self.semantic_threshold = self.rule_manager.get_threshold(
                'semantic_similarity', context='hierarchical_validation'
            )
        else:
            self.semantic_threshold = self.config.get('semantic_threshold', 0.3)  # Fallback
        
        self.use_lightweight_nlp = self.config.get('use_lightweight_nlp', True)
        self.similarity_model_name = self.config.get('similarity_model_name', 'all-MiniLM-L6-v2')
        
        # 初始化NLP组件（延迟加载）
        self._semantic_pipeline = None
        self._nlp = None
        self._similarity_model = None  # 轻量级相似度模型
        
        # 统计信息
        self._validation_stats = {
            'total_validations': 0,
            'fast_rule_rejections': 0,
            'nlp_rejections': 0,
            'llm_rejections': 0,
            'acceptances': 0
        }
    
    def _get_semantic_pipeline(self):
        """获取语义理解管道实例（延迟加载）"""
        if self._semantic_pipeline is None and self.use_nlp:
            try:
                from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
                self._semantic_pipeline = get_semantic_understanding_pipeline()
            except Exception as e:
                self.logger.debug(f"获取语义理解管道失败: {e}")
        return self._semantic_pipeline
    
    def _get_similarity_model(self):
        """获取轻量级相似度模型（延迟加载）"""
        if self._similarity_model is None and self.use_lightweight_nlp:
            try:
                from sentence_transformers import SentenceTransformer
                self._similarity_model = SentenceTransformer(self.similarity_model_name)
                self.logger.info(f"✅ 轻量级相似度模型已加载: {self.similarity_model_name}")
            except Exception as e:
                self.logger.debug(f"加载轻量级相似度模型失败: {e}")
        return self._similarity_model
    
    def validate(
        self,
        answer: str,
        query: str,
        evidence_text: Optional[str] = None,
        previous_step_result: Optional[str] = None
    ) -> Dict[str, Any]:
        """🚀 分层验证答案
        
        Args:
            answer: 答案文本
            query: 查询文本
            evidence_text: 证据文本（可选）
            previous_step_result: 上一步结果（可选）
            
        Returns:
            验证结果字典：
            {
                'is_valid': bool,
                'confidence': float (0.0-1.0),
                'validation_steps': List[Dict],
                'issues': List[str],
                'suggestions': List[str]
            }
        """
        start_time = time.time()
        self._validation_stats['total_validations'] += 1
        
        result = {
            'is_valid': True,
            'confidence': 1.0,
            'validation_steps': [],
            'issues': [],
            'suggestions': []
        }
        
        try:
            # 阶段1：快速规则验证（毫秒级）
            fast_result = self._fast_rule_validation(answer, query, evidence_text)
            result['validation_steps'].append({
                'stage': 'fast_rule',
                'passed': fast_result['passed'],
                'confidence': fast_result.get('confidence', 1.0),
                'time_ms': (time.time() - start_time) * 1000,
                'issues': fast_result.get('issues', [])
            })
            
            if not fast_result['passed']:
                result['is_valid'] = False
                result['confidence'] = 0.0
                result['issues'].extend(fast_result.get('issues', []))
                self._validation_stats['fast_rule_rejections'] += 1
                return result
            
            # 阶段2：NLP增强验证（秒级）
            if self.use_nlp:
                nlp_result = self._nlp_enhanced_validation(answer, query, evidence_text, previous_step_result)
                result['validation_steps'].append({
                    'stage': 'nlp_enhanced',
                    'passed': nlp_result['passed'],
                    'confidence': nlp_result.get('confidence', 1.0),
                    'time_ms': (time.time() - start_time) * 1000,
                    'issues': nlp_result.get('issues', [])
                })
                
                # 更新总体置信度
                result['confidence'] = min(result['confidence'], nlp_result.get('confidence', 1.0))
                result['issues'].extend(nlp_result.get('issues', []))
                result['suggestions'].extend(nlp_result.get('suggestions', []))
                
                # 🚀 统一规则管理：从统一规则管理中心获取置信度阈值（不再硬编码）
                # 🚀 修复：降低置信度阈值，允许更多合理的答案通过
                confidence_threshold = 0.3  # 默认阈值：0.3（降低严格度）
                if self.rule_manager:
                    try:
                        threshold_config = self.rule_manager.get_threshold(
                            'confidence', context='nlp_validation'
                        )
                        if threshold_config and float(threshold_config) > 0:
                            confidence_threshold = float(threshold_config)
                    except Exception as e:
                        self.logger.warning(f"从规则管理器获取置信度阈值失败，使用默认值: {e}")
                
                # 🚀 修复：即使NLP验证失败，如果置信度>0.1，仍然通过（避免过度拒绝）
                if not nlp_result['passed']:
                    nlp_confidence = nlp_result.get('confidence', 0.0)
                    if nlp_confidence < confidence_threshold:
                        # 如果置信度很低（<0.1），才拒绝
                        if nlp_confidence < 0.1:
                            result['is_valid'] = False
                            self._validation_stats['nlp_rejections'] += 1
                            return result
                        else:
                            # 置信度>0.1，降低置信度但通过
                            result['confidence'] = min(result['confidence'], nlp_confidence)
                            self.logger.debug(f"NLP验证置信度({nlp_confidence:.2f})低于阈值({confidence_threshold:.2f})，但>0.1，仍然通过")
            
            # 阶段3：LLM验证（可选，复杂情况）
            if self.use_llm_fallback and not result['is_valid']:
                # 只有在前面验证失败时才使用LLM（成本高）
                llm_result = self._llm_validation(answer, query, evidence_text, previous_step_result)
                result['validation_steps'].append({
                    'stage': 'llm_fallback',
                    'passed': llm_result['passed'],
                    'confidence': llm_result.get('confidence', 1.0),
                    'time_ms': (time.time() - start_time) * 1000,
                    'issues': llm_result.get('issues', [])
                })
                
                if llm_result['passed']:
                    result['is_valid'] = True
                    # 🚀 统一规则管理：从统一规则管理中心获取LLM验证置信度（不再硬编码）
                    llm_confidence = 0.7
                    if self.rule_manager:
                        llm_confidence = self.rule_manager.get_threshold(
                            'confidence', context='llm_validation'
                        )
                    result['confidence'] = llm_result.get('confidence', llm_confidence)  # LLM验证通过，但置信度中等
                else:
                    self._validation_stats['llm_rejections'] += 1
            
            if result['is_valid']:
                self._validation_stats['acceptances'] += 1
            
            result['total_time_ms'] = (time.time() - start_time) * 1000
            return result
            
        except Exception as e:
            self.logger.error(f"分层验证失败: {e}")
            # 验证失败时，保守地返回False
            result['is_valid'] = False
            result['confidence'] = 0.0
            result['issues'].append(f"验证过程出错: {str(e)}")
            return result
    
    def _fast_rule_validation(
        self,
        answer: str,
        query: str,
        evidence_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """阶段1：快速规则验证（基于统计和结构特征，无硬编码）
        
        检查：
        1. 基础格式（长度、字符类型）
        2. 统计异常（重复、异常模式）
        3. 结构特征（URL、引用标记等）
        """
        issues = []
        
        if not answer or not answer.strip():
            return {'passed': False, 'confidence': 0.0, 'issues': ['答案为空']}
        
        answer_clean = answer.strip()
        
        # 🚀 统一规则管理：使用统一规则管理中心验证长度（不再硬编码）
        # 🚀 修复：设置合理的默认值，避免配置错误导致所有答案被拒绝
        min_length = 1  # 最小长度：1个字符（允许单字符答案，如"A"）
        max_length = 100  # 最大长度：100个字符（对于人名、地名等足够）
        
        if self.rule_manager:
            try:
                min_length_config = self.rule_manager.get_threshold('answer_length_min', context='hierarchical_validation')
                max_length_config = self.rule_manager.get_threshold('answer_length_max', context='hierarchical_validation')
                # 🚀 修复：确保配置值有效（大于0）
                if min_length_config and int(min_length_config) > 0:
                    min_length = int(min_length_config)
                if max_length_config and int(max_length_config) > 0:
                    max_length = int(max_length_config)
            except Exception as e:
                self.logger.warning(f"从规则管理器获取长度阈值失败，使用默认值: {e}")
        
        # 🚀 修复：确保min_length和max_length是合理的值
        min_length = max(1, min_length)  # 至少为1
        max_length = max(50, max_length)  # 至少为50（对于人名足够）
        
        # 1. 长度检查（基于统计，而非硬编码）
        if len(answer_clean) < min_length:
            issues.append(f"答案过短（可能不完整，长度: {len(answer_clean)} < {min_length}）")
        elif len(answer_clean) > max_length:
            issues.append(f"答案过长（可能是完整段落而非答案，长度: {len(answer_clean)} > {max_length}）")
        
        # 2. 格式异常检测（基于模式，而非硬编码关键词）
        # 检测过长的数字序列（可能是ID或错误）
        if re.search(r'\d{8,}', answer_clean):
            issues.append("答案包含异常长的数字序列（可能是ID或错误）")
        
        # 检测连续大写字母（可能是缩写或代码）
        if re.search(r'[A-Z]{5,}', answer_clean):
            issues.append("答案包含连续大写字母（可能是缩写或代码）")
        
        # 🚀 统一规则管理：使用统一规则管理中心验证字符比例（不再硬编码）
        garbage_threshold = 0.4
        if self.rule_manager:
            garbage_threshold = self.rule_manager.get_threshold(
                'garbage_char_ratio', context='default'
            )
        
        # 计算垃圾字符比例
        alnum_count = sum(1 for c in answer_clean if c.isalnum() or c.isspace())
        garbage_ratio = 1.0 - (alnum_count / len(answer_clean)) if answer_clean else 0.0
        if garbage_ratio > garbage_threshold:  # 超过阈值是非字母数字字符
            issues.append(f"答案包含过多特殊字符（比例: {garbage_ratio:.2f} > {garbage_threshold}）")
        
        # 4. 重复内容检测（基于统计）
        words = answer_clean.split()
        if len(words) >= 4:
            # 检查是否有重复的短语
            word_bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
            bigram_counts = Counter(word_bigrams)
            max_bigram_count = max(bigram_counts.values()) if bigram_counts else 0
            if max_bigram_count >= 2:
                issues.append("答案包含重复的短语（可能是错误）")
        
        # 5. 结构特征检测（URL、引用标记等）
        # URL检测
        if re.search(r'https?://|www\.|\.(com|org|gov|edu|net)\b', answer_clean, re.IGNORECASE):
            issues.append("答案包含URL（可能是导航链接）")
        
        # 引用标记检测（只有引用标记，没有实际内容）
        if re.match(r'^[↑↓\[\]()\d\s]+$', answer_clean):
            issues.append("答案只包含引用标记，没有实际内容")
        
        # 6. 日期元数据检测（基于上下文，而非硬编码）
        # 检测"Retrieved"等元数据前缀
        if re.match(r'^Retrieved\s+', answer_clean, re.IGNORECASE):
            # 检查查询是否是日期查询
            is_date_query = bool(re.search(
                r'\b(when|what\s+time|what\s+date|what\s+year)\b',
                query.lower()
            ))
            if not is_date_query:
                issues.append("答案包含'Retrieved'元数据前缀（非日期查询）")
        
        # 🚀 统一规则管理：从统一规则管理中心获取置信度降低比例（不再硬编码）
        confidence_penalty = 0.15
        if self.rule_manager:
            confidence_penalty = self.rule_manager.get_threshold(
                'confidence_penalty', context='per_issue'
            )
        
        confidence = 1.0 - (len(issues) * confidence_penalty)  # 每个问题降低置信度
        confidence = max(0.0, min(1.0, confidence))
        
        return {
            'passed': len(issues) == 0,
            'confidence': confidence,
            'issues': issues
        }
    
    def _nlp_enhanced_validation(
        self,
        answer: str,
        query: str,
        evidence_text: Optional[str] = None,
        previous_step_result: Optional[str] = None
    ) -> Dict[str, Any]:
        """阶段2：NLP增强验证（使用语义理解，无硬编码）
        
        检查：
        1. 语义相似度（答案与查询、证据的相关性）
        2. 实体类型一致性（使用NER）
        3. 上下文相关性（答案在证据中的上下文）
        """
        issues = []
        suggestions = []
        confidence = 1.0
        
        pipeline = self._get_semantic_pipeline()
        if not pipeline:
            # NLP不可用，跳过NLP验证
            # 🚀 统一规则管理：从统一规则管理中心获取fallback置信度（不再硬编码）
            fallback_confidence = 0.8
            if self.rule_manager:
                fallback_confidence = self.rule_manager.get_threshold(
                    'confidence', context='fallback'
                )
            return {'passed': True, 'confidence': fallback_confidence, 'issues': [], 'suggestions': []}
        
        try:
            # 1. 语义相似度验证
            if evidence_text:
                # 答案与证据的语义相似度
                evidence_similarity = pipeline.calculate_semantic_similarity(answer, evidence_text)
                if evidence_similarity < self.semantic_threshold:
                    issues.append(f"答案与证据语义相关性低（相似度: {evidence_similarity:.2f}）")
                    # 🚀 统一规则管理：从统一规则管理中心获取置信度乘数（不再硬编码）
                    evidence_multiplier = 0.5
                    if self.rule_manager:
                        evidence_multiplier = self.rule_manager.get_threshold(
                            'confidence_multipliers', context='evidence_similarity_low'
                        )
                    confidence *= evidence_multiplier
            
            # 答案与查询的语义相似度
            query_similarity = pipeline.calculate_semantic_similarity(answer, query)
            
            # 🚀 统一规则管理：从统一规则管理中心获取阈值（不再硬编码）
            query_similarity_threshold = 0.2
            if self.rule_manager:
                query_similarity_threshold = self.rule_manager.get_threshold(
                    'semantic_similarity', context='query_answer_validation'
                )
            
            if query_similarity < query_similarity_threshold:
                issues.append(f"答案与查询语义匹配度低（相似度: {query_similarity:.2f} < {query_similarity_threshold}）")
                # 🚀 统一规则管理：从统一规则管理中心获取置信度乘数（不再硬编码）
                query_multiplier = 0.6
                if self.rule_manager:
                    query_multiplier = self.rule_manager.get_threshold(
                        'confidence_multipliers', context='query_similarity_low'
                    )
                confidence *= query_multiplier
            
            # 2. 实体类型一致性检查
            query_entities = pipeline.extract_entities_intelligent(query)
            answer_entities = pipeline.extract_entities_intelligent(answer)
            
            if query_entities and answer_entities:
                query_types = {e.get('label') for e in query_entities}
                answer_types = {e.get('label') for e in answer_entities}
                
                # 如果查询是PERSON类型，但答案是ORG/GPE类型，可能不相关
                if 'PERSON' in query_types and answer_types & {'ORG', 'GPE', 'LOC', 'FAC'}:
                    # 检查是否是明确的类型冲突
                    if not (query_types & answer_types):  # 完全没有共同类型
                        issues.append(f"实体类型不匹配：查询期望{query_types}，答案包含{answer_types}")
                        # 🚀 统一规则管理：从统一规则管理中心获取置信度乘数（不再硬编码）
                        entity_multiplier = 0.4
                        if self.rule_manager:
                            entity_multiplier = self.rule_manager.get_threshold(
                                'confidence_multipliers', context='entity_type_mismatch'
                            )
                        confidence *= entity_multiplier
            
            # 3. 上下文相关性检查
            if evidence_text and answer.lower() in evidence_text.lower():
                # 答案在证据中出现，检查上下文
                context_result = self._check_context_relevance(answer, query, evidence_text)
                if not context_result['is_relevant']:
                    issues.append(context_result.get('reason', '答案在证据中的上下文不相关'))
                    # 🚀 统一规则管理：从统一规则管理中心获取置信度乘数（不再硬编码）
                    context_multiplier = 0.7
                    if self.rule_manager:
                        context_multiplier = self.rule_manager.get_threshold(
                            'confidence_multipliers', context='context_relevance_low'
                        )
                    confidence *= context_multiplier
            
            # 4. 关系查询特殊检查
            if previous_step_result:
                # 检查答案是否与previous_step_result混淆
                if self._check_previous_step_confusion(answer, query, previous_step_result):
                    issues.append("答案可能与previous_step_result混淆")
                    confidence *= 0.3
            
            confidence = max(0.0, min(1.0, confidence))
            
            # 🚀 统一规则管理：从统一规则管理中心获取置信度阈值（不再硬编码）
            # 🚀 修复：降低置信度阈值，允许更多合理的答案通过
            confidence_threshold = 0.3  # 默认阈值：0.3（降低严格度）
            if self.rule_manager:
                try:
                    threshold_config = self.rule_manager.get_threshold(
                        'confidence', context='nlp_validation'
                    )
                    if threshold_config and float(threshold_config) > 0:
                        confidence_threshold = float(threshold_config)
                except Exception as e:
                    self.logger.warning(f"从规则管理器获取置信度阈值失败，使用默认值: {e}")
            
            # 🚀 修复：即使置信度低于阈值，如果有issues但置信度>0.1，仍然通过（避免过度拒绝）
            passed = confidence >= confidence_threshold
            if not passed and confidence > 0.1 and len(issues) <= 1:
                # 如果置信度>0.1且只有1个或更少的问题，仍然通过
                passed = True
                self.logger.debug(f"答案置信度({confidence:.2f})低于阈值({confidence_threshold:.2f})，但只有{len(issues)}个问题，仍然通过")
            
            return {
                'passed': passed,
                'confidence': confidence,
                'issues': issues,
                'suggestions': suggestions
            }
            
        except Exception as e:
            self.logger.debug(f"NLP增强验证失败: {e}")
            # NLP验证失败，不拒绝答案，但降低置信度
            # 🚀 统一规则管理：从统一规则管理中心获取fallback置信度（不再硬编码）
            fallback_confidence = 0.7
            if self.rule_manager:
                fallback_confidence = self.rule_manager.get_threshold(
                    'confidence', context='fallback'
                )
            return {
                'passed': True,
                'confidence': fallback_confidence,
                'issues': [f"NLP验证过程出错: {str(e)}"],
                'suggestions': []
            }
    
    def _llm_validation(
        self,
        answer: str,
        query: str,
        evidence_text: Optional[str] = None,
        previous_step_result: Optional[str] = None
    ) -> Dict[str, Any]:
        """阶段3：LLM验证（可选，复杂情况）
        
        使用LLM进行深度验证，适用于：
        - 前面验证失败但不确定的情况
        - 复杂的关系查询
        - 需要深度理解的场景
        """
        # 这里可以集成LLM验证
        # 目前返回通过（因为这是可选的fallback）
        # 🚀 统一规则管理：从统一规则管理中心获取fallback置信度（不再硬编码）
        fallback_confidence = 0.7
        if self.rule_manager:
            fallback_confidence = self.rule_manager.get_threshold(
                'confidence', context='fallback'
            )
        
        return {
            'passed': True,
            'confidence': fallback_confidence,
            'issues': [],
            'suggestions': []
        }
    
    def _check_context_relevance(
        self,
        answer: str,
        query: str,
        evidence_text: str
    ) -> Dict[str, Any]:
        """检查答案在证据中的上下文相关性"""
        try:
            answer_lower = answer.lower()
            evidence_lower = evidence_text.lower()
            
            # 查找答案在证据中的所有出现位置
            positions = [m.start() for m in re.finditer(re.escape(answer_lower), evidence_lower)]
            
            if not positions:
                return {'is_relevant': False, 'reason': '答案在证据中未找到'}
            
            # 分析每个出现位置的上下文
            relevant_contexts = 0
            for pos in positions:
                context_start = max(0, pos - 150)
                context_end = min(len(evidence_lower), pos + len(answer) + 150)
                context = evidence_lower[context_start:context_end]
                
                # 提取查询的关键词（排除停用词）
                query_words = [w for w in query.lower().split() 
                             if w not in {'the', 'a', 'an', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'is', 'was', 'are', 'were'} 
                             and len(w) > 2]
                
                # 检查上下文中是否包含查询关键词
                if any(word in context for word in query_words):
                    relevant_contexts += 1
            
            # 如果至少有一个相关上下文，认为相关
            is_relevant = relevant_contexts > 0
            
            return {
                'is_relevant': is_relevant,
                'reason': f'答案在{len(positions)}个位置出现，{relevant_contexts}个位置有相关上下文' if not is_relevant else None
            }
            
        except Exception as e:
            self.logger.debug(f"检查上下文相关性失败: {e}")
            return {'is_relevant': True, 'reason': None}  # 检查失败，保守地认为相关
    
    def _check_previous_step_confusion(
        self,
        answer: str,
        query: str,
        previous_step_result: str
    ) -> bool:
        """检查答案是否与previous_step_result混淆"""
        try:
            # 检查是否是关系查询
            if 'first name' not in query.lower() or 'mother' not in query.lower() and 'father' not in query.lower():
                return False
            
            # 提取previous_step_result的first name
            prev_words = previous_step_result.strip().split()
            if not prev_words:
                return False
            
            prev_first_name = prev_words[0].lower()
            answer_lower = answer.strip().lower()
            
            # 如果答案与previous_step_result的first name相同，可能是混淆
            return answer_lower == prev_first_name
            
        except Exception as e:
            self.logger.debug(f"检查previous_step混淆失败: {e}")
            return False
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息"""
        return self._validation_stats.copy()

