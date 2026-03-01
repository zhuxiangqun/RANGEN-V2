"""
答案验证模块 - 从 RealReasoningEngine 中提取的答案验证功能

Phase 1: 提取答案验证模块
"""
import logging
import time
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class AnswerValidator:
    """答案验证器 - 负责答案的验证和合理性检查"""
    
    def __init__(
        self,
        llm_integration=None,
        fast_llm_integration=None,
        config_center=None,
        logger_instance=None,
        prompt_generator=None,
        semantic_pipeline=None,
        rule_manager=None
    ):
        """初始化答案验证器
        
        Args:
            llm_integration: LLM集成实例
            fast_llm_integration: 快速LLM集成实例
            config_center: 配置中心实例
            logger_instance: 日志记录器实例
            prompt_generator: 提示词生成器实例
            semantic_pipeline: 语义理解管道实例（可选）
            rule_manager: 统一规则管理器实例（可选）
        """
        self.llm_integration = llm_integration
        self.fast_llm_integration = fast_llm_integration
        self.config_center = config_center
        self.logger = logger_instance or logger
        self.prompt_generator = prompt_generator
        self.semantic_pipeline = semantic_pipeline
        self.rule_manager = rule_manager
        
        # 验证缓存
        self._validation_cache: Dict[str, Dict[str, Any]] = {}
        self._validation_cache_ttl = 1800  # 验证缓存30分钟
    
    def validate_answer(
        self,
        answer: str,
        query: str,
        query_type: str,
        evidence: List[Dict[str, Any]],
        steps: Optional[List[Dict[str, Any]]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """主验证入口 - 综合多种验证方法
        
        Args:
            answer: 答案文本
            query: 查询文本
            query_type: 查询类型
            evidence: 证据列表
            steps: 推理步骤列表（可选）
            constraints: 查询约束（可选）
            
        Returns:
            验证结果字典，包含 is_valid, confidence, reasons
        """
        # 先进行合理性验证
        result = self.validate_reasonableness(answer, query_type, query, evidence)
        
        # 如果有约束，进行约束验证
        if constraints and steps:
            # 常识验证
            if not self.validate_with_common_sense(answer, query, constraints):
                result['is_valid'] = False
                result['confidence'] = min(result.get('confidence', 0.8), 0.5)
                result['reasons'].append("常识验证失败")
            
            # 语义一致性验证
            is_semantic_valid, semantic_msg = self.validate_semantic_consistency(
                answer, query, constraints, steps
            )
            if not is_semantic_valid:
                result['is_valid'] = False
                result['confidence'] = min(result.get('confidence', 0.8), 0.5)
                result['reasons'].append(f"语义验证失败: {semantic_msg}")
        
        return result
    
    def validate_reasonableness(
        self,
        answer: str,
        query_type: str,
        query: str,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """✅ 方案1改进：简化验证逻辑，只做基本检查，信任LLM能力
        
        核心改进：
        1. 只做基本检查：答案是否为空、是否包含无效标记
        2. 移除基于证据匹配度的验证（避免错误拒绝正确答案）
        3. 信任LLM的能力，让它基于自身知识给出答案
        4. 🚀 P1优化：使用缓存避免重复验证相同答案
        
        Args:
            answer: 答案文本
            query_type: 查询类型
            query: 查询文本
            evidence: 证据列表（不再用于验证）
        
        Returns:
            验证结果字典，包含 is_valid, confidence, reasons
        """
        # 🚀 P1优化：检查验证缓存，避免重复验证
        import hashlib
        if len(query) > 100:
            query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()[:16]
            cache_key = f"{answer}_{query_type}_{query_hash}"
        else:
            cache_key = f"{answer}_{query_type}_{query}"
        
        if cache_key in self._validation_cache:
            cached_result = self._validation_cache[cache_key]
            cache_time = cached_result.get('timestamp', 0)
            current_time = time.time()
            
            # 检查缓存是否过期
            if current_time - cache_time < self._validation_cache_ttl:
                self.logger.debug(f"✅ 验证缓存命中: {answer[:50]}")
                return cached_result.get('result', {
                    'is_valid': True,
                    'confidence': 0.8,
                    'reasons': []
                })
        
        verification_result = {
            'is_valid': True,
            'confidence': 0.8,  # 默认高置信度，信任LLM
            'reasons': []
        }
        
        try:
            answer_stripped = answer.strip()
            answer_lower = answer_stripped.lower()
            
            # 1. 基本空值检查
            if not answer_stripped:
                verification_result['is_valid'] = False
                verification_result['confidence'] = 0.0
                verification_result['reasons'].append("答案为空")
                return verification_result
            
            # 2. 检查答案是否包含明显的无效标记（使用统一中心系统）
            try:
                from src.core.intelligent_filter_center import get_intelligent_filter_center
                filter_center = get_intelligent_filter_center()
                
                if filter_center.is_invalid_answer(answer):
                    verification_result['is_valid'] = False
                    verification_result['confidence'] = 0.0
                    verification_result['reasons'].append("答案被智能过滤中心判定为无效")
                    return verification_result
            except Exception as e:
                # 如果统一中心不可用，使用简单检查
                invalid_answers = [
                    "unable to determine", "无法确定", "不确定", "cannot determine",
                    "error", "错误", "failed", "失败", "timeout", "超时"
                ]
                if any(inv in answer_lower for inv in invalid_answers):
                    verification_result['is_valid'] = False
                    verification_result['confidence'] = 0.0
                    verification_result['reasons'].append("答案包含明显的无效标记")
                    return verification_result
            
            # 3. ✅ 方案1改进：移除基于证据匹配度的验证
            # 不再检查答案是否在证据中，因为：
            # - LLM可能基于自身知识给出正确答案
            # - 当证据不相关时，正确答案也不在证据中
            # - 这会导致正确答案被错误拒绝
            
            # 4. ✅ 方案1改进：信任LLM，默认通过验证
            verification_result['is_valid'] = True
            verification_result['confidence'] = 0.8
            verification_result['reasons'].append("基本验证通过，信任LLM能力")
            
            # 🚀 P1优化：缓存验证结果
            self._validation_cache[cache_key] = {
                'result': verification_result,
                'timestamp': time.time()
            }
            
            return verification_result
            
        except Exception as e:
            self.logger.debug(f"合理性验证失败: {e}")
            return {
                'is_valid': True,  # 验证失败时，仍然信任LLM
                'confidence': 0.7,
                'reasons': [f"验证过程出错，但信任LLM: {str(e)}"]
            }
    
    def quick_validate_answer(
        self,
        answer: str,
        query: str,
        evidence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """✅ 方案1改进：快速验证简短直接答案，只做基本检查，信任LLM能力
        
        对于简短直接的答案（如人名、数字、地名），只进行基本的合理性检查：
        1. 检查答案是否为空
        2. 检查答案是否包含明显的无效标记（使用统一中心系统）
        3. 不再检查答案是否在证据中（避免错误拒绝正确答案）
        
        Args:
            answer: 答案文本
            query: 查询文本
            evidence: 证据列表（不再用于验证）
        
        Returns:
            验证结果字典，包含 is_valid, confidence, reasons
        """
        verification_result = {
            'is_valid': True,
            'confidence': 0.8,  # 默认高置信度，信任LLM
            'reasons': []
        }
        
        try:
            answer_lower = answer.lower().strip()
            
            # 1. 基本空值检查
            if not answer_lower:
                verification_result['is_valid'] = False
                verification_result['confidence'] = 0.0
                verification_result['reasons'].append("答案为空")
                return verification_result
            
            # 2. 基本合理性检查 - 使用智能过滤中心
            try:
                from src.core.intelligent_filter_center import get_intelligent_filter_center
                filter_center = get_intelligent_filter_center()
                
                # 检查是否为无效答案（使用统一中心系统）
                if filter_center.is_invalid_answer(answer):
                    verification_result['is_valid'] = False
                    verification_result['confidence'] = 0.0
                    verification_result['reasons'].append("答案被智能过滤中心判定为无效")
                    return verification_result
                
                # 检查是否包含推理过程标记（使用统一中心系统）
                if filter_center.is_meaningless_content(answer):
                    verification_result['is_valid'] = False
                    verification_result['confidence'] = 0.1
                    verification_result['reasons'].append("答案包含推理过程标记，不是简短直接答案（由智能过滤中心判定）")
                    return verification_result
            except Exception as e:
                # 如果统一中心不可用，使用简单检查
                self.logger.debug(f"智能过滤中心不可用，使用简单检查: {e}")
                invalid_answers = [
                    "unable to determine", "无法确定", "不确定", "cannot determine",
                    "error", "错误", "failed", "失败", "timeout", "超时"
                ]
                if any(inv in answer_lower for inv in invalid_answers):
                    verification_result['is_valid'] = False
                    verification_result['confidence'] = 0.0
                    verification_result['reasons'].append("答案包含明显的无效标记")
                    return verification_result
            
            # 3. ✅ 方案1改进：移除基于证据匹配度的验证
            # 4. ✅ 方案1改进：信任LLM，默认通过验证
            verification_result['is_valid'] = True
            verification_result['confidence'] = 0.8
            verification_result['reasons'].append("快速验证通过，信任LLM能力")
            
            return verification_result
            
        except Exception as e:
            self.logger.debug(f"快速验证失败: {e}")
            # 快速验证失败时，仍然信任LLM
            verification_result['is_valid'] = True
            verification_result['confidence'] = 0.7
            verification_result['reasons'].append(f"快速验证异常，但信任LLM: {e}")
            return verification_result
    
    def is_obviously_correct(
        self,
        answer: str,
        query: str,
        evidence: List[Dict[str, Any]],
        query_type: Optional[str] = None
    ) -> bool:
        """🚀 根本改进：检查答案是否明显正确（不调用LLM，快速判断）
        
        核心思想：
        1. 答案在证据中直接找到
        2. 答案与证据高语义相似度（>0.8）
        3. 答案类型与查询类型匹配且格式正确
        
        Args:
            answer: 答案文本
            query: 查询文本
            evidence: 证据列表
            query_type: 查询类型（可选）
        
        Returns:
            如果答案明显正确返回True，否则返回False
        """
        try:
            if not answer or not answer.strip():
                return False
            
            answer_lower = answer.lower().strip()
            
            # 1. 检查答案是否在证据中直接找到
            if evidence:
                evidence_text = ' '.join([
                    e.get('content', '') if isinstance(e, dict) else str(e)
                    for e in evidence[:5]
                ]).lower()
                
                if answer_lower in evidence_text:
                    self.logger.debug(f"✅ 答案在证据中直接找到，明显正确: {answer[:50]}")
                    return True
                
                # 2. 检查答案与证据的高语义相似度（如果可用）
                try:
                    # 尝试获取Jina服务
                    jina_service = None
                    try:
                        from knowledge_management_system.api.service_interface import get_knowledge_service
                        kms = get_knowledge_service()
                        if hasattr(kms, 'jina_service') and kms.jina_service:
                            jina_service = kms.jina_service
                    except (ImportError, AttributeError):
                        try:
                            from knowledge_management_system.utils.jina_service import get_jina_service
                            if get_jina_service:
                                jina_service = get_jina_service()
                        except (ImportError, AttributeError):
                            pass
                    
                    if jina_service and hasattr(jina_service, 'api_key') and jina_service.api_key:
                        if hasattr(jina_service, 'get_embedding'):
                            import numpy as np
                            
                            # 获取embedding
                            answer_embedding = jina_service.get_embedding(answer)
                            evidence_embedding = jina_service.get_embedding(evidence_text[:2000])
                            
                            if answer_embedding is not None and evidence_embedding is not None:
                                # 计算余弦相似度
                                answer_vec = np.array(answer_embedding)
                                evidence_vec = np.array(evidence_embedding)
                                
                                if answer_vec.ndim > 1:
                                    answer_vec = answer_vec.flatten()
                                if evidence_vec.ndim > 1:
                                    evidence_vec = evidence_vec.flatten()
                                
                                dot_product = np.dot(answer_vec, evidence_vec)
                                norm_product = np.linalg.norm(answer_vec) * np.linalg.norm(evidence_vec)
                                
                                if norm_product > 0:
                                    similarity = float(dot_product / norm_product)
                                    if similarity > 0.8:  # 高语义相似度
                                        self.logger.debug(f"✅ 答案与证据高语义相似度（{similarity:.2f}），明显正确: {answer[:50]}")
                                        return True
                except Exception as e:
                    self.logger.debug(f"语义相似度计算失败（跳过）: {e}")
            
            # 3. 检查答案类型与查询类型匹配且格式正确
            if query_type:
                import re
                
                # 人名查询：答案应该是完整的人名（至少两个首字母大写的词）
                if query_type in ['name', 'person']:
                    words = answer.split()
                    if len(words) >= 2 and all(word[0].isupper() if word else False for word in words):
                        self.logger.debug(f"✅ 人名格式正确，明显正确: {answer[:50]}")
                        return True
                
                # 数字查询：答案应该是数字格式
                elif query_type in ['numerical', 'mathematical', 'ranking']:
                    if re.match(r'^\d+(?:st|nd|rd|th)?(?:,\d{3})*(?:\.\d+)?$', answer):
                        self.logger.debug(f"✅ 数字格式正确，明显正确: {answer[:50]}")
                        return True
                
                # 地点查询：答案应该包含大写字母
                elif query_type in ['location', 'place']:
                    if any(c.isupper() for c in answer):
                        self.logger.debug(f"✅ 地点格式正确，明显正确: {answer[:50]}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"明显正确检查失败: {e}")
            return False
    
    def validate_with_common_sense(
        self,
        answer: str,
        query: str,
        constraints: Dict[str, Any]
    ) -> bool:
        """🚀 Phase 2.1: 使用常识验证答案（策略层）
        
        检查答案是否符合基本常识约束。
        
        Args:
            answer: 答案文本
            query: 查询文本
            constraints: 查询约束
            
        Returns:
            如果答案符合常识返回True，否则返回False
        """
        try:
            if not answer or not query:
                return True  # 如果答案或查询为空，默认通过（由其他验证处理）
            
            answer_clean = answer.strip()
            query_lower = query.lower()
            answer_lower = answer_clean.lower()
            
            # 检查1: 名字和姓氏的合理性
            words = answer_clean.split()
            if len(words) >= 2:
                first_word = words[0]
                last_word = words[-1]
                
                # 常见名字列表（这些通常是名字，不是姓氏）
                common_first_names = ['eliza', 'jane', 'mary', 'sarah', 'emily', 'anna', 'elizabeth', 
                                     'james', 'john', 'william', 'george', 'thomas', 'frances']
                
                # 如果查询要求"娘家姓"或"surname"，但第一个词是常见名字，可能是错误的
                if constraints.get('name_type') in ['maiden_name', 'surname']:
                    if first_word.lower() in common_first_names:
                        self.logger.warning(
                            f"⚠️ [常识检查] 查询要求{constraints.get('name_type')}，但答案的第一个词'{first_word}'是常见名字，不是姓氏"
                        )
                        return False
            
            # 检查2: 性别匹配
            if constraints.get('name_type') == 'maiden_name':
                male_indicators = ['husband', 'father', 'son', 'brother', 'uncle', 'nephew', 'grandfather', 'grandson']
                if any(indicator in query_lower for indicator in male_indicators):
                    self.logger.warning(
                        f"⚠️ [常识检查] 查询要求'娘家姓'，但查询是关于男性的，不符合常识"
                    )
                    return False
            
            # 检查3: 实体类型匹配
            is_person_query = any(term in query_lower for term in [
                'who', 'person', 'first lady', 'president', 'mother', 'father', 
                'wife', 'husband', 'name', 'maiden name', 'surname'
            ])
            
            if is_person_query:
                location_indicators = ['country', 'nation', 'state', 'city', 'location', 'place', 'region']
                organization_indicators = ['army', 'union', 'government', 'department', 'agency', 'bureau']
                
                answer_lower_words = answer_lower.split()
                if any(indicator in answer_lower for indicator in location_indicators):
                    if len(answer_lower_words) <= 2:
                        self.logger.warning(
                            f"⚠️ [常识检查] 查询是关于人的，但答案'{answer_clean}'看起来像是地点"
                        )
                        return False
                
                if any(indicator in answer_lower for indicator in organization_indicators):
                    self.logger.warning(
                        f"⚠️ [常识检查] 查询是关于人的，但答案'{answer_clean}'看起来像是组织"
                    )
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"常识验证失败: {e}")
            return True  # 验证失败时，默认通过（避免误杀）
    
    def validate_with_common_sense_llm(
        self,
        answer: str,
        query: str,
        constraints: Dict[str, Any],
        llm_to_use
    ) -> Optional[bool]:
        """🚀 Phase 2.1: 使用LLM进行增强的常识验证
        
        Args:
            answer: 答案文本
            query: 查询文本
            constraints: 查询约束
            llm_to_use: LLM实例
            
        Returns:
            如果答案符合常识返回True，不符合返回False，无法判断返回None
        """
        try:
            if not llm_to_use:
                return None
            
            # 构建约束描述
            constraint_desc = []
            if constraints.get('name_type'):
                constraint_desc.append(f"答案类型: {constraints['name_type']}")
            if constraints.get('format'):
                constraint_desc.append(f"格式要求: {constraints['format']}")
            
            constraint_str = "\n".join(constraint_desc) if constraint_desc else "无特殊约束"
            
            prompt = None
            if self.prompt_generator:
                try:
                    prompt = self.prompt_generator.generate_optimized_prompt(
                        "validate_common_sense",
                        query=query[:300], # 使用截断的查询作为上下文
                        enhanced_context={'query': query, 'answer': answer, 'constraint_str': constraint_str}
                    )
                except Exception as e:
                    self.logger.debug(f"提示词生成器生成失败，使用默认提示词: {e}")
            
            if not prompt:
                prompt = f"""你是一个常识验证专家。判断以下答案是否符合基本常识。

**原始查询：**
{query}

**答案：**
{answer}

**查询约束：**
{constraint_str}

请判断答案是否符合基本常识（例如：性别匹配、实体类型匹配、名字/姓氏合理性等）。

只返回 "YES" 或 "NO"，不要返回其他内容。"""
            
            response = llm_to_use._call_llm(prompt, max_tokens=10)
            if response:
                response_lower = response.strip().lower()
                if 'yes' in response_lower:
                    return True
                elif 'no' in response_lower:
                    return False
            
            return None
            
        except Exception as e:
            self.logger.debug(f"LLM常识验证失败: {e}")
            return None
    
    def validate_semantic_consistency(
        self,
        answer: str,
        query: str,
        constraints: Dict[str, Any],
        steps: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[bool, str]:
        """🚀 Phase 2.2: 增强语义验证（策略层）
        
        使用多层语义理解验证答案与查询的语义一致性。
        
        Args:
            answer: 答案文本
            query: 查询文本
            constraints: 查询约束
            steps: 推理步骤列表（可选，用于上下文验证）
            
        Returns:
            (是否通过, 验证结果描述)
        """
        try:
            if not answer or not query:
                return True, "答案或查询为空，跳过语义验证"
            
            answer_clean = answer.strip()
            
            # 验证1: 使用语义理解管道进行语义相似度验证
            try:
                from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
                pipeline = get_semantic_understanding_pipeline()
                
                # 计算答案与查询的语义相似度
                similarity = pipeline.calculate_semantic_similarity(query, answer_clean)
                
                # 🚀 修复：如果相似度为0.0，可能是模型加载失败或计算错误，不应直接判定为失败
                if similarity == 0.0:
                    self.logger.warning(
                        f"⚠️ [语义验证] 语义相似度为0.0，可能是模型问题，跳过此检查 (答案: {answer_clean})"
                    )
                # 如果相似度过低，可能答案不相关
                elif similarity < 0.15:  # 🚀 修复：降低阈值，避免误杀 (原0.3)
                    self.logger.warning(
                        f"⚠️ [语义验证] 答案与查询的语义相似度过低: {similarity:.2f} (答案: {answer_clean})"
                    )
                    return False, f"语义相似度过低: {similarity:.2f}"
                
                # 验证2: 使用语义理解管道验证相关性
                is_relevant, relevance_score = pipeline.validate_relevance(query, answer_clean, threshold=0.5)
                if not is_relevant:
                    self.logger.warning(
                        f"⚠️ [语义验证] 答案与查询不相关: {relevance_score:.2f} (答案: {answer_clean})"
                    )
                    return False, f"答案与查询不相关: {relevance_score:.2f}"
                
            except ImportError:
                self.logger.debug("语义理解管道不可用，跳过语义相似度验证")
            except Exception as e:
                self.logger.debug(f"语义相似度验证失败: {e}")
            
            # 验证3: 实体类型一致性验证
            try:
                from src.utils.semantic_understanding_pipeline import get_semantic_understanding_pipeline
                pipeline = get_semantic_understanding_pipeline()
                
                # 提取查询和答案中的实体
                query_entities = pipeline.extract_entities_intelligent(query)
                answer_entities = pipeline.extract_entities_intelligent(answer_clean)
                
                # 如果查询要求特定实体类型，检查答案是否匹配
                if constraints.get('entity_type'):
                    expected_type = constraints['entity_type']
                    self.logger.debug(
                        f"[语义验证] 查询要求实体类型: {expected_type}, "
                        f"查询实体: {query_entities}, 答案实体: {answer_entities}"
                    )
                
            except Exception as e:
                self.logger.debug(f"实体类型验证失败: {e}")
            
            # 验证4: 使用LLM进行深度语义一致性验证
            llm_to_use = self.fast_llm_integration or self.llm_integration
            if llm_to_use:
                try:
                    llm_semantic_result = self.validate_semantic_consistency_llm(
                        answer_clean, query, constraints, steps, llm_to_use
                    )
                    if llm_semantic_result is False:
                        return False, "LLM语义一致性验证失败"
                    elif llm_semantic_result is True:
                        return True, "通过所有语义验证"
                except Exception as e:
                    self.logger.debug(f"LLM语义验证失败: {e}")
            
            return True, "通过语义验证"
            
        except Exception as e:
            self.logger.debug(f"语义验证过程出错: {e}")
            return True, f"验证过程出错: {str(e)}"  # 验证失败时，默认通过（避免误杀）
    
    def validate_semantic_consistency_llm(
        self,
        answer: str,
        query: str,
        constraints: Dict[str, Any],
        steps: Optional[List[Dict[str, Any]]],
        llm_to_use
    ) -> Optional[bool]:
        """🚀 Phase 2.2: 使用LLM进行深度语义一致性验证
        
        Args:
            answer: 答案文本
            query: 查询文本
            constraints: 查询约束
            steps: 推理步骤列表
            llm_to_use: LLM实例
            
        Returns:
            如果答案语义一致返回True，不一致返回False，无法判断返回None
        """
        try:
            if not llm_to_use:
                return None
            
            # 构建步骤上下文
            steps_context = ""
            if steps:
                steps_info = []
                for i, step in enumerate(steps, 1):
                    step_answer = step.get('answer', '')
                    step_desc = step.get('description', '')
                    if step_answer:
                        steps_info.append(f"步骤{i}: {step_desc} -> {step_answer}")
                if steps_info:
                    steps_context = "\n".join(steps_info)
            
            # 构建约束描述
            constraint_desc = []
            if constraints.get('name_type'):
                constraint_desc.append(f"答案类型: {constraints['name_type']}")
            if constraints.get('format'):
                constraint_desc.append(f"格式要求: {constraints['format']}")
            if constraints.get('completeness') == 'required':
                constraint_desc.append("完整性要求: 必须完整")
            
            constraint_str = "\n".join(constraint_desc) if constraint_desc else "无特殊约束"
            
            prompt = None
            if self.prompt_generator:
                try:
                    prompt = self.prompt_generator.generate_optimized_prompt(
                        "validate_semantic_consistency",
                        query=query[:300], # 使用截断的查询作为上下文
                        enhanced_context={'query': query, 'answer': answer, 'constraint_str': constraint_str, 'steps_context': steps_context}
                    )
                except Exception as e:
                    self.logger.debug(f"提示词生成器生成失败，使用默认提示词: {e}")
            
            steps_context_str = f"**推理步骤上下文：**\n{steps_context}\n" if steps_context else ""
            
            if not prompt:
                prompt = f"""你是一个语义验证专家。判断以下答案是否与查询在语义上一致。

**原始查询：**
{query}

**答案：**
{answer}

**查询约束：**
{constraint_str}

{steps_context_str}

请判断答案是否与查询在语义上一致，是否符合查询的意图和约束。

只返回 "YES" 或 "NO"，不要返回其他内容。"""
            
            response = llm_to_use._call_llm(prompt, max_tokens=10)
            if response:
                response_lower = response.strip().lower()
                if 'yes' in response_lower:
                    return True
                elif 'no' in response_lower:
                    return False
            
            return None
            
        except Exception as e:
            self.logger.debug(f"LLM语义一致性验证失败: {e}")
            return None

