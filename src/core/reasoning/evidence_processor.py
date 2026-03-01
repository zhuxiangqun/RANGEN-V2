"""
证据处理器 - 处理证据的收集、过滤、分配
"""
import logging
import time
import re
import html
import asyncio
from typing import Dict, List, Any, Optional
from .models import Evidence

logger = logging.getLogger(__name__)


class EvidenceProcessor:
    """证据处理器 - 集成统一架构"""
    
    def __init__(self, knowledge_retrieval_agent=None, config_center=None, learning_manager=None, llm_integration=None):
        self.logger = logging.getLogger(__name__)
        self.knowledge_retrieval_agent = knowledge_retrieval_agent
        self.config_center = config_center
        self.learning_manager = learning_manager
        self.llm_integration = llm_integration  # 🚀 保存LLM集成用于通用查询拆解
        
        # 🚀 修复：添加 knowledge_retrieval_service 属性（从 knowledge_retrieval_agent 获取）
        self.knowledge_retrieval_service = None
        if self.knowledge_retrieval_agent:
            if hasattr(self.knowledge_retrieval_agent, '_get_service'):
                try:
                    self.knowledge_retrieval_service = self.knowledge_retrieval_agent._get_service()
                except Exception as e:
                    self.logger.debug(f"从knowledge_retrieval_agent获取service失败: {e}")
            elif hasattr(self.knowledge_retrieval_agent, 'retrieve_knowledge'):
                # 如果knowledge_retrieval_agent本身就是service，直接使用
                self.knowledge_retrieval_service = self.knowledge_retrieval_agent
        
        # 🚀 方案A：集成证据质量评估器
        from .evidence_quality_assessor import EvidenceQualityAssessor
        
        self.evidence_assessor = EvidenceQualityAssessor(llm_integration=llm_integration)
        
        # 🚀 ML/RL增强：初始化自适应优化器（用于优化证据选择策略）
        self.adaptive_optimizer = None
        try:
            from src.core.adaptive_optimizer import AdaptiveOptimizer
            self.adaptive_optimizer = AdaptiveOptimizer()
            self.logger.info("✅ 证据处理器：自适应优化器已初始化（ML/RL增强）")
        except Exception as e:
            self.logger.warning(f"自适应优化器初始化失败（证据处理器）: {e}")
        
        # 🚀 P0修复：添加查询级别的缓存，避免重复检索
        from typing import Tuple
        self._query_cache: Dict[str, Tuple[List[Evidence], float]] = {}  # query -> (evidence_list, timestamp)
        self._cache_ttl = 300.0  # 缓存有效期：5分钟
    
    def can_reuse_previous_evidence(self, step_type: str, sub_query: str, previous_evidence: List[Evidence]) -> bool:
        """🚀 新增：判断是否可以复用前一步的证据"""
        try:
            if not previous_evidence or len(previous_evidence) == 0:
                return False
            
            reusable_step_types = [
                'logical_deduction',
                'causal_reasoning',
                'pattern_recognition',
                'answer_synthesis'
            ]
            
            if step_type in reusable_step_types:
                return True
            
            calculation_keywords = ['calculate', 'compute', 'based on', 'using', 'from']
            if any(keyword in sub_query.lower() for keyword in calculation_keywords):
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"判断是否可以复用前一步证据失败: {e}")
            return False
    
    def filter_relevant_previous_evidence(self, previous_evidence: List[Evidence], sub_query: str, step: Dict[str, Any]) -> List[Evidence]:
        """🚀 新增：从前一步的证据中过滤出与当前步骤相关的证据"""
        try:
            if not previous_evidence:
                return []
            
            relevant_evidence = []
            
            # 提取子查询中的关键词
            query_keywords = set()
            for word in sub_query.lower().split():
                stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'who', 'where', 'when', 'why', 'how', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by'}
                if word not in stop_words and len(word) > 2:
                    query_keywords.add(word)
            
            # 检查每条前一步的证据是否包含子查询的关键词
            for ev in previous_evidence:
                if hasattr(ev, 'content'):
                    content = ev.content.lower()
                    if any(keyword in content for keyword in query_keywords):
                        relevant_evidence.append(ev)
                elif isinstance(ev, str):
                    if any(keyword in ev.lower() for keyword in query_keywords):
                        relevant_evidence.append(ev)
            
            return relevant_evidence
            
        except Exception as e:
            self.logger.debug(f"过滤相关的前一步证据失败: {e}")
            return []
    
    def allocate_evidence_for_step(self, evidence_list: List[Evidence], step: Dict[str, Any]) -> List[Evidence]:
        """🚀 新增：根据步骤类型和内容，智能分配最相关的证据"""
        try:
            if not evidence_list:
                return []
            
            step_type = step.get('type', 'unknown')
            step_description = step.get('description', '')
            sub_query = step.get('sub_query', '')
            
            # 🚀 ML/RL增强：使用AdaptiveOptimizer优化证据数量
            optimal_evidence_count = len(evidence_list)  # 默认使用所有证据
            if self.adaptive_optimizer:
                try:
                    # 从步骤中推断查询类型（简化版）
                    query_type = 'general'
                    if 'first' in sub_query.lower() or '15th' in sub_query.lower() or 'ranking' in step_type:
                        query_type = 'ranking'
                    elif 'name' in sub_query.lower() or 'who' in sub_query.lower():
                        query_type = 'name'
                    
                    optimal_count, min_count, max_count = self.adaptive_optimizer.get_optimized_evidence_count(
                        query_type, default_count=len(evidence_list)
                    )
                    optimal_evidence_count = min(max_count, max(min_count, optimal_count))
                    self.logger.debug(f"✅ [ML/RL] 使用优化的证据数量: {optimal_evidence_count} (查询类型: {query_type})")
                except Exception as e:
                    self.logger.debug(f"AdaptiveOptimizer优化证据分配失败: {e}")
            
            # 提取步骤的关键词
            step_keywords = set()
            for text in [step_description, sub_query]:
                if text:
                    for word in text.lower().split():
                        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'who', 'where', 'when', 'why', 'how', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by', 'find', 'identify', 'determine'}
                        if word not in stop_words and len(word) > 2:
                            step_keywords.add(word)
            
            # 为每条证据计算相关性分数
            scored_evidence = []
            for ev in evidence_list:
                score = 0.0
                
                # 基础分数：证据的原始相关性
                if hasattr(ev, 'relevance_score'):
                    score += ev.relevance_score * 0.5
                elif hasattr(ev, 'confidence'):
                    score += ev.confidence * 0.5
                else:
                    score += 0.5
                
                # 关键词匹配分数
                if hasattr(ev, 'content'):
                    content = ev.content.lower()
                    matched_keywords = sum(1 for keyword in step_keywords if keyword in content)
                    if step_keywords:
                        keyword_score = matched_keywords / len(step_keywords)
                        score += keyword_score * 0.3
                
                # 步骤类型匹配分数
                type_weights = {
                    'evidence_gathering': 0.9,
                    'logical_deduction': 0.8,
                    'causal_reasoning': 0.8,
                    'pattern_recognition': 0.7,
                    'answer_synthesis': 0.6,
                    'query_analysis': 0.5
                }
                type_weight = type_weights.get(step_type, 0.5)
                score *= type_weight
                
                scored_evidence.append((ev, score))
            
            # 按分数排序，返回前N条最相关的证据
            scored_evidence.sort(key=lambda x: x[1], reverse=True)
            
            # 🚀 ML/RL增强：根据步骤类型决定返回的证据数量（优先使用ML/RL优化的数量）
            max_evidence_per_step = {
                'evidence_gathering': 5,
                'logical_deduction': 3,
                'causal_reasoning': 3,
                'pattern_recognition': 3,
                'answer_synthesis': 2,
                'query_analysis': 2
            }
            default_max_count = max_evidence_per_step.get(step_type, 3)
            
            # 如果ML/RL优化了证据数量，使用优化的数量
            if 'optimal_evidence_count' in locals() and optimal_evidence_count > 0:
                max_count = min(optimal_evidence_count, default_max_count * 2)  # 最多不超过默认值的2倍
                self.logger.debug(f"✅ [ML/RL] 使用优化的证据数量: {max_count} (默认: {default_max_count})")
            else:
                max_count = default_max_count
            
            allocated = [ev for ev, score in scored_evidence[:max_count]]
            
            if len(allocated) < len(evidence_list):
                self.logger.debug(f"步骤类型={step_type}: 从{len(evidence_list)}条证据中选择了{len(allocated)}条最相关的证据")
            
            return allocated
            
        except Exception as e:
            self.logger.warning(f"智能分配证据失败: {e}")
            return evidence_list
    
    def _is_relevant_evidence(self, evidence: Evidence, query: str) -> bool:
        """判断证据是否相关"""
        try:
            if not evidence or not evidence.content:
                return False
            # 🚀 彻底修复：降低confidence阈值，从0.3降低到0.1，避免过度过滤
            # 因为检索结果的confidence可能不准确，应该让更多结果通过，由LLM判断相关性
            is_valid = len(evidence.content) > 10 and evidence.confidence > 0.1
            if not is_valid:
                self.logger.debug(f"证据被过滤: content长度={len(evidence.content)}, confidence={evidence.confidence} (阈值=0.1)")
            return is_valid
        except Exception as e:
            self.logger.error(f"判断证据相关性失败: {e}")
            return False
    
    def _calculate_relevance(self, evidence: Evidence, query: str) -> float:
        """计算证据相关性（单个证据）
        
        🚀 P0修复：改进相关性计算，优先使用confidence/similarity评分
        """
        try:
            if not evidence or not evidence.content:
                return 0.0
            
            # 🚀 改进：优先使用confidence或similarity评分
            base_relevance = evidence.confidence
            
            # 如果confidence为0或很低，尝试从metadata获取similarity
            if base_relevance < 0.3 and evidence.metadata:
                similarity = evidence.metadata.get('similarity', evidence.metadata.get('similarity_score', 0.0))
                if similarity > base_relevance:
                    base_relevance = float(similarity)
            
            # 🚀 改进：长度因子应该适度，避免过长内容获得过高评分
            # 理想长度：500-2000字符，过长或过短都降低评分
            content_length = len(evidence.content)
            if content_length < 100:
                length_factor = 0.5  # 过短内容降低评分
            elif content_length > 5000:
                length_factor = 0.8  # 过长内容适度降低评分
            else:
                # 理想长度范围：100-5000字符
                length_factor = 1.0
            
            relevance_score = base_relevance * length_factor
            
            # 确保评分在合理范围内
            return min(max(relevance_score, 0.0), 1.0)
        except Exception as e:
            self.logger.error(f"计算证据相关性失败: {e}")
            return 0.0
    
    def _extract_ranking_section(self, evidence_text: str, query: str) -> Optional[str]:
        """🚀 新增：提取排名列表部分"""
        try:
            ranking_patterns = [
                r'\d+[th|st|nd|rd]\.?\s+[^\n]+',
                r'\d+\.\s+[^\n]+',
                r'Rank\s+\d+[:\s]+[^\n]+',
                r'#\d+[:\s]+[^\n]+',
            ]
            
            ranking_lines = []
            for pattern in ranking_patterns:
                matches = re.finditer(pattern, evidence_text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    line = match.group(0).strip()
                    if len(line) > 10:
                        ranking_lines.append(line)
            
            if ranking_lines:
                ranking_section = '\n'.join(ranking_lines[:100])
                query_words = set(word.lower() for word in query.split() if len(word) > 3)
                section_lower = ranking_section.lower()
                relevant_words = [word for word in query_words if word in section_lower]
                
                if relevant_words or len(ranking_lines) >= 10:
                    return ranking_section
            
            return None
            
        except Exception as e:
            self.logger.debug(f"提取排名列表失败: {e}")
            return None
    
    def _extract_relevant_segments(self, query: str, evidence_text: str, evidence_list: List[Any], target_length: int) -> str:
        """提取与查询最相关的证据片段"""
        try:
            query_words = [w.lower() for w in query.split() if len(w) > 3]
            if not query_words:
                return ""
            
            sentences = re.split(r'[.!?。！？]\s+', evidence_text)
            
            scored_sentences = []
            for sentence in sentences:
                if len(sentence.strip()) < 10:
                    continue
                
                sentence_lower = sentence.lower()
                matches = sum(1 for word in query_words if word in sentence_lower)
                relevance_score = matches / max(len(query_words), 1)
                
                if relevance_score > 0:
                    scored_sentences.append((relevance_score, sentence))
            
            scored_sentences.sort(reverse=True, key=lambda x: x[0])
            
            selected_segments = []
            current_length = 0
            for score, sentence in scored_sentences:
                if current_length + len(sentence) > target_length:
                    break
                selected_segments.append(sentence)
                current_length += len(sentence)
            
            if len(selected_segments) < 3 and evidence_list:
                for ev in evidence_list[:3]:
                    if hasattr(ev, 'content'):
                        content = ev.content if hasattr(ev, 'content') else str(ev)
                    else:
                        content = str(ev)
                    if content and len(content.strip()) > 20:
                        first_sentence = content.split('.')[0].strip() if '.' in content else content[:100].strip()
                        if first_sentence and first_sentence not in selected_segments:
                            if current_length + len(first_sentence) <= target_length:
                                selected_segments.append(first_sentence)
                                current_length += len(first_sentence)
                            else:
                                break
            
            if selected_segments:
                return ' '.join(selected_segments[:target_length // 50])
            
            return ""
            
        except Exception as e:
            self.logger.debug(f"提取相关片段失败: {e}")
            return ""
    
    def _assess_query_complexity_for_evidence(self, query: str, query_type: str, current_evidence_count: int) -> int:
        """🚀 优化：使用统一服务评估查询复杂度（用于动态调整证据数量）"""
        try:
            # 🚀 优化：使用统一复杂度判断服务
            from src.utils.unified_complexity_model_service import get_unified_complexity_model_service
            
            service = get_unified_complexity_model_service()
            complexity_result = service.assess_complexity(
                query=query,
                query_type=query_type,
                evidence_count=current_evidence_count
            )
            
            # 将复杂度评分转换为0-5的整数（用于证据数量调整）
            complexity_score_int = int(min(complexity_result.score, 5.0))
            self.logger.debug(f"✅ [EvidenceProcessor] 统一服务复杂度评估: {complexity_result.level.value} (评分: {complexity_result.score:.2f} -> {complexity_score_int})")
            return complexity_score_int
            
        except Exception as e:
            self.logger.warning(f"⚠️ [EvidenceProcessor] 统一服务复杂度评估失败: {e}，使用fallback规则")
            # Fallback: 简单规则判断
            complexity_score = 0
            query_length = len(query)
            if query_length > 200:
                complexity_score += 2
            elif query_length > 100:
                complexity_score += 1
            
            complex_types = ['temporal', 'multi_hop', 'complex', 'numerical', 'spatial']
            if query_type in complex_types:
                complexity_score += 2
            elif query_type in ['causal', 'comparative', 'analytical']:
                complexity_score += 1
            
            if current_evidence_count > 5:
                complexity_score += 1
            
            return min(complexity_score, 5)
    
    async def gather_evidence(self, query: str, context: Dict[str, Any], query_analysis: Dict[str, Any]) -> List[Evidence]:
        """收集相关证据 - 🚀 改进：增强知识提取和日志"""
        # 这个方法非常长（500+行），需要完整迁移
        # 由于代码量太大，先提供一个简化版本，后续可以完善
        perf_start = time.time()
        evidence = []
        
        from src.utils.research_logger import log_info
        
        # 🚀 P0修复：检查查询缓存，避免重复检索
        cache_key = query.strip().lower()
        current_time = time.time()
        if cache_key in self._query_cache:
            cached_evidence, cache_timestamp = self._query_cache[cache_key]
            if current_time - cache_timestamp < self._cache_ttl:
                log_info(f"✅ [证据收集-缓存命中] 查询='{query[:80]}...', 返回缓存结果({len(cached_evidence)}条证据)")
                self.logger.debug(f"✅ [证据收集-缓存命中] 查询='{query[:80]}...', 缓存时间: {current_time - cache_timestamp:.2f}秒前")
                return cached_evidence.copy()  # 返回副本，避免修改缓存
            else:
                # 缓存过期，删除
                del self._query_cache[cache_key]
                log_info(f"⏰ [证据收集-缓存过期] 查询='{query[:80]}...', 缓存已过期，重新检索")
        
        # 从context中提取知识数据
        knowledge_data = context.get('knowledge', []) or context.get('knowledge_data', []) or []
        already_retrieved = context.get('_knowledge_retrieved', False)
        
        if isinstance(knowledge_data, dict):
            knowledge_data = [knowledge_data]
        
        log_info(f"证据收集开始: 查询='{query[:80]}...', 知识数据数量={len(knowledge_data)}, 已检索标志={already_retrieved}")
        
        # 处理知识数据列表
        processed_knowledge = []
        for item in knowledge_data:
            if isinstance(item, dict):
                processed_knowledge.append(item)
            elif isinstance(item, list):
                processed_knowledge.extend(item)
        
        # 处理知识项（简化版本，完整版本需要并行处理等优化）
        for knowledge_item in processed_knowledge:
            if not isinstance(knowledge_item, dict):
                continue
            
            content = (knowledge_item.get('content', '') or 
                      knowledge_item.get('text', '') or 
                      knowledge_item.get('data', '') or
                      str(knowledge_item.get('result', '')))
            
            if isinstance(content, dict):
                content = content.get('content', '') or content.get('text', '') or str(content)
            
            if content:
                content = html.unescape(str(content))
                content = content.replace('&apos;', "'").replace('&quot;', '"')
                content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
                
                # 🚀 修复：清理实体类型标签（如 "United States (Entity): ..."）
                # 移除格式：Entity Name (EntityType): content 或 Entity Name (EntityType):
                # 匹配模式：Entity Name (EntityType): 或 Entity Name (EntityType):
                entity_label_pattern = r'^[A-Z][^:]*\s*\([^)]+\)\s*:\s*'
                content = re.sub(entity_label_pattern, '', content, flags=re.MULTILINE)
                # 也处理行内的实体标签
                content = re.sub(r'\s*\(Entity\)\s*:', ':', content)
                content = re.sub(r'\s*\(Person\)\s*:', ':', content)
                content = re.sub(r'\s*\(Location\)\s*:', ':', content)
                content = re.sub(r'\s*\(Organization\)\s*:', ':', content)
                content = content.strip()
            
            if not content or not content.strip():
                continue
            
            temp_evidence = Evidence(
                content=content.strip(),
                source=knowledge_item.get('source', knowledge_item.get('metadata', {}).get('source', 'unknown')),
                confidence=float(knowledge_item.get('confidence', knowledge_item.get('similarity', 0.5)) or 0.5),
                relevance_score=0.0,
                evidence_type=knowledge_item.get('type', 'general'),
                metadata=knowledge_item.get('metadata', {})
            )
            
            # 🚀 彻底修复：添加详细日志，诊断为什么证据被过滤
            is_relevant = self._is_relevant_evidence(temp_evidence, query)
            log_info(f"🔍 [证据转换] 检查证据相关性: content长度={len(temp_evidence.content) if temp_evidence.content else 0}, confidence={temp_evidence.confidence}, is_relevant={is_relevant}")
            
            if is_relevant:
                temp_evidence.relevance_score = self._calculate_relevance(temp_evidence, query)
                evidence.append(temp_evidence)
                log_info(f"✅ [证据转换] 证据已添加: relevance_score={temp_evidence.relevance_score}")
            else:
                log_info(f"❌ [证据转换] 证据被过滤: content长度={len(temp_evidence.content) if temp_evidence.content else 0}, confidence={temp_evidence.confidence} (阈值=0.1), content='{temp_evidence.content[:100] if temp_evidence.content else 'None'}...'")
                print(f"❌ [证据转换] 证据被过滤: content长度={len(temp_evidence.content) if temp_evidence.content else 0}, confidence={temp_evidence.confidence} (阈值=0.1)")
        
        # 🚀 P1修复：动态调整相关性阈值，根据查询类型和证据数量智能调整
        # 1. 根据查询类型和证据数量动态调整阈值
        query_type_str = query_analysis.get('type', 'general') if isinstance(query_analysis, dict) else 'general'
        evidence_count = len(evidence)
        
        # 动态阈值调整策略
        if query_type_str in ['ordinal', 'ranking', 'numerical']:
            # 序数查询、排名查询需要更多证据（因为可能需要列表）
            base_threshold = 0.35  # 降低阈值
            relaxed_threshold = 0.25
        elif query_type_str in ['relationship', 'causal', 'multi_hop']:
            # 关系查询、因果查询需要更精确的证据
            base_threshold = 0.40  # 降低阈值
            relaxed_threshold = 0.30
        else:
            # 一般查询使用默认阈值
            base_threshold = 0.35  # 降低阈值 (原0.50)
            relaxed_threshold = 0.25  # (原0.40)
        
        # 如果证据数量少，进一步降低阈值
        if evidence_count < 5:
            base_threshold = max(0.20, base_threshold - 0.10)
            relaxed_threshold = max(0.15, relaxed_threshold - 0.10)
        
        relevance_threshold = base_threshold
        filtered_evidence = [
            ev for ev in evidence 
            if ev.relevance_score >= relevance_threshold or ev.confidence >= relevance_threshold
        ]
        
        # 如果过滤后证据太少（<3条），使用更宽松的阈值
        if len(filtered_evidence) < 3 and len(evidence) > 0:
            filtered_evidence = [
                ev for ev in evidence 
                if ev.relevance_score >= relaxed_threshold or ev.confidence >= relaxed_threshold
            ][:10]  # 最多保留10条
            log_info(f"🔍 [证据过滤-动态阈值] 使用宽松阈值={relaxed_threshold:.2f} (查询类型: {query_type_str}), 筛选后={len(filtered_evidence)}条")
        else:
            log_info(f"🔍 [证据过滤-动态阈值] 使用标准阈值={relevance_threshold:.2f} (查询类型: {query_type_str}), 筛选后={len(filtered_evidence)}条")
        
        # 2. 限制证据数量（最多5条）
        if len(filtered_evidence) > 5:
            # 按相关性评分排序，保留最相关的5条
            filtered_evidence.sort(key=lambda ev: ev.relevance_score or ev.confidence, reverse=True)
            filtered_evidence = filtered_evidence[:5]
            log_info(f"🔍 [证据过滤] 限制证据数量: 保留最相关的5条")
        
        # 3. 限制证据长度（每条最多2000字符）
        max_evidence_length = 2000
        for ev in filtered_evidence:
            if ev.content and len(ev.content) > max_evidence_length:
                original_length = len(ev.content)
                # 保留前1000字符和后1000字符，中间用省略号
                ev.content = ev.content[:1000] + "\n[... 中间内容已省略 ...]\n" + ev.content[-1000:]
                log_info(f"🔍 [证据过滤] 证据长度超限: {original_length} -> {len(ev.content)}字符")
        
        evidence = filtered_evidence
        log_info(f"✅ [证据过滤] 最终证据数量: {len(evidence)}条 (原始: {len(evidence) + len([ev for ev in evidence if ev not in filtered_evidence])}条)")
        
        # 如果没有证据且未检索过，主动检索知识库
        if not evidence and not already_retrieved:
            log_info(f"证据收集: 无外部知识且未检索过，主动检索知识库")
            try:
                # 🚀 P0修复：优先使用已初始化的knowledge_retrieval_agent，避免重复创建和初始化
                if self.knowledge_retrieval_agent:
                    # 检查是否是KnowledgeRetrievalAgent（有_get_service方法）
                    if hasattr(self.knowledge_retrieval_agent, '_get_service'):
                        # 从KnowledgeRetrievalAgent获取内部的KnowledgeRetrievalService
                        knowledge_agent = self.knowledge_retrieval_agent._get_service()
                        log_info(f"🔍 [证据收集] 使用已初始化的knowledge_retrieval_agent的service")
                    elif hasattr(self.knowledge_retrieval_agent, 'retrieve_knowledge'):
                        # 直接使用（如果是KnowledgeRetrievalService）
                        knowledge_agent = self.knowledge_retrieval_agent
                        log_info(f"🔍 [证据收集] 使用已初始化的knowledge_retrieval_agent（直接使用）")
                    else:
                        # 回退：创建新的KnowledgeRetrievalService
                        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
                        knowledge_agent = KnowledgeRetrievalService()
                        log_info(f"🔍 [证据收集] knowledge_retrieval_agent类型不支持，创建新的KnowledgeRetrievalService实例")
                else:
                    from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
                    knowledge_agent = KnowledgeRetrievalService()
                    log_info(f"🔍 [证据收集] 创建新的KnowledgeRetrievalService实例")
                
                if isinstance(query_analysis, dict):
                    query_type_str = query_analysis.get('type', 'general')
                elif isinstance(query_analysis, str):
                    query_type_str = query_analysis
                else:
                    query_type_str = 'general'
                
                complexity_score = self._assess_query_complexity_for_evidence(query, query_type_str, 0)
                
                if complexity_score >= 4:
                    dynamic_top_k = 20
                elif complexity_score >= 3:
                    dynamic_top_k = 15
                elif complexity_score >= 2:
                    dynamic_top_k = 10
                else:
                    dynamic_top_k = 5
                
                # 🚀 P1修复：传递上下文信息到检索服务，用于消歧
                retrieval_context = context.copy() if context else {}
                # 提取上下文信息用于消歧
                if 'previous_steps_context' in context:
                    retrieval_context['previous_steps_context'] = context['previous_steps_context']
                if 'original_query' in context:
                    retrieval_context['original_query'] = context['original_query']
                
                # 调用知识检索服务
                # 🚀 P0修复：确保knowledge_agent有retrieve_knowledge方法
                if hasattr(knowledge_agent, 'retrieve_knowledge'):
                    retrieval_result = await knowledge_agent.retrieve_knowledge(query, top_k=dynamic_top_k, context=retrieval_context)
                else:
                    # 回退：使用execute方法
                    log_info(f"⚠️ [证据收集] knowledge_agent没有retrieve_knowledge方法，使用execute方法")
                    context = {"query": query, "top_k": dynamic_top_k}
                    result = await knowledge_agent.execute(context)
                    # 转换AgentResult格式
                    if result and result.success and result.data:
                        # 尝试从result.data中提取knowledge
                        data = result.data
                        if isinstance(data, dict) and 'sources' in data:
                            # 转换格式
                            knowledge_list = []
                            sources = data.get('sources', [])
                            for source in sources:
                                if isinstance(source, dict):
                                    knowledge_list.append({
                                        'content': source.get('content', '') or source.get('text', ''),
                                        'source': source.get('source', 'unknown'),
                                        'confidence': source.get('similarity', 0.0) or source.get('confidence', 0.0),
                                        'similarity': source.get('similarity', 0.0),
                                        'metadata': source.get('metadata', {})
                                    })
                            retrieval_result = {
                                'knowledge': knowledge_list,
                                'total_results': len(knowledge_list),
                                'confidence': result.confidence
                            }
                        else:
                            retrieval_result = {'knowledge': [], 'total_results': 0, 'confidence': 0.0}
                    else:
                        retrieval_result = {'knowledge': [], 'total_results': 0, 'confidence': 0.0}
                
                # 🚀 P0修复：添加详细日志，确保检索结果正确传递（只记录到日志文件，不在终端显示）
                log_info(f"🔍 [证据收集] 检索结果: 是否有结果={retrieval_result is not None}, knowledge字段={retrieval_result.get('knowledge') if retrieval_result else None}")
                self.logger.debug(f"🔍 [证据收集] 检索结果: 是否有结果={retrieval_result is not None}, knowledge字段类型={type(retrieval_result.get('knowledge')) if retrieval_result else None}")
                
                # 🚀 修复：检查knowledge字段是否存在且不为空
                knowledge_data = None
                if retrieval_result:
                    knowledge_data = retrieval_result.get('knowledge')
                    if knowledge_data is not None:
                        if isinstance(knowledge_data, list):
                            log_info(f"🔍 [证据收集] knowledge字段是列表，长度={len(knowledge_data)}")
                            self.logger.debug(f"🔍 [证据收集] knowledge字段是列表，长度={len(knowledge_data)}")
                        else:
                            log_info(f"⚠️ [证据收集] knowledge字段不是列表: {type(knowledge_data)}")
                            self.logger.warning(f"⚠️ [证据收集] knowledge字段不是列表: {type(knowledge_data)}")
                
                if retrieval_result and knowledge_data and len(knowledge_data) > 0:
                    log_info(f"🔍 [证据收集] 检索到 {len(knowledge_data)} 条知识，准备添加到context")
                    self.logger.debug(f"🔍 [证据收集] 检索到 {len(knowledge_data)} 条知识，准备转换为证据")
                    
                    # 🚀 诊断：检查knowledge_data的类型和内容
                    if not isinstance(knowledge_data, list):
                        log_info(f"⚠️ [证据收集诊断] knowledge_data不是列表类型: {type(knowledge_data)}")
                        self.logger.warning(f"⚠️ [证据收集诊断] knowledge_data不是列表类型: {type(knowledge_data)}")
                        # 尝试转换
                        if isinstance(knowledge_data, dict):
                            knowledge_data = [knowledge_data]
                        else:
                            knowledge_data = []
                    
                    # 🚀 诊断：检查knowledge_data的格式
                    if knowledge_data and len(knowledge_data) > 0:
                        first_item = knowledge_data[0]
                        log_info(f"🔍 [证据收集诊断] 第一条知识格式: type={type(first_item)}, keys={list(first_item.keys()) if isinstance(first_item, dict) else 'not dict'}")
                        if isinstance(first_item, dict):
                            content = first_item.get('content', '') or first_item.get('text', '')
                            confidence = first_item.get('confidence', 0.0) or first_item.get('similarity', 0.0)
                            log_info(f"🔍 [证据收集诊断] 第一条知识: content长度={len(str(content))}, confidence={confidence}")
                            self.logger.debug(f"🔍 [证据收集诊断] 第一条知识: content长度={len(str(content))}, confidence={confidence}")
                    
                    context['knowledge'] = knowledge_data
                    context['_knowledge_retrieved'] = True
                    
                    # 递归调用处理新检索的知识
                    evidence = await self.gather_evidence(query, context, query_analysis)
                    
                    # 🚀 诊断：检查转换后的证据数量
                    # 🚀 优化：降级为DEBUG级别（这是正常的过滤行为，不是错误）
                    log_info(f"🔍 [证据收集诊断] 转换后证据数量: {len(evidence)} (原始知识数量: {len(knowledge_data)})")
                    if len(evidence) < len(knowledge_data):
                        log_info(f"🔍 [证据收集诊断] 部分知识被过滤: {len(knowledge_data)} -> {len(evidence)}")
                        self.logger.debug(f"🔍 [证据收集诊断] 部分知识被过滤: {len(knowledge_data)} -> {len(evidence)}")
                    
                    return evidence
                else:
                    # 🚀 修复：提供更详细的错误信息
                    if not retrieval_result:
                        log_info(f"⚠️ [证据收集] 检索结果为空: retrieval_result=None")
                        self.logger.warning(f"⚠️ [证据收集] 检索结果为空")
                    elif not knowledge_data:
                        log_info(f"⚠️ [证据收集] knowledge字段为空或不存在: retrieval_result.keys={list(retrieval_result.keys()) if retrieval_result else []}")
                        self.logger.warning(f"⚠️ [证据收集] knowledge字段为空或不存在")
                    elif len(knowledge_data) == 0:
                        log_info(f"⚠️ [证据收集] knowledge列表为空（可能被验证过滤）: total_results={retrieval_result.get('total_results', 0)}")
                        self.logger.warning(f"⚠️ [证据收集] knowledge列表为空（可能被验证过滤），total_results={retrieval_result.get('total_results', 0)}")
                    else:
                        log_info(f"⚠️ [证据收集] 检索结果为空或没有knowledge字段: retrieval_result={retrieval_result}")
                        self.logger.warning(f"⚠️ [证据收集] 检索结果为空或没有knowledge字段")
            except Exception as e:
                self.logger.debug(f"主动知识检索失败: {e}")
        
        # 按相关性排序并限制数量
        if evidence:
            evidence = sorted(evidence, key=lambda e: e.relevance_score, reverse=True)
            
            if isinstance(query_analysis, dict):
                query_type_str = query_analysis.get('type', 'general')
            elif isinstance(query_analysis, str):
                query_type_str = query_analysis
            else:
                query_type_str = 'general'
            
            complexity_score = self._assess_query_complexity_for_evidence(query, query_type_str, len(evidence))
            
            if complexity_score >= 4:
                max_evidence = 15
            elif complexity_score >= 3:
                max_evidence = 12
            elif complexity_score >= 2:
                max_evidence = 8
            else:
                max_evidence = 3
            
            if len(evidence) > max_evidence:
                evidence = evidence[:max_evidence]
        
        perf_time = time.time() - perf_start
        self.logger.info(f"✅ 证据收集完成: 证据数={len(evidence)}, 耗时={perf_time:.3f}秒")
        
        # 🚀 P0修复：将结果保存到缓存（仅当有证据时）
        if evidence:
            cache_key = query.strip().lower()
            self._query_cache[cache_key] = (evidence.copy(), current_time)
            log_info(f"💾 [证据收集-缓存保存] 查询='{query[:80]}...', 保存{len(evidence)}条证据到缓存")
            self.logger.debug(f"💾 [证据收集-缓存保存] 查询='{query[:80]}...', 缓存大小: {len(self._query_cache)}")
        
        return evidence
    
    async def gather_evidence_for_step(self, sub_query: str, step: Dict[str, Any], context: Dict[str, Any], query_analysis: Dict[str, Any], previous_evidence: Optional[List[Evidence]] = None) -> List[Evidence]:
        """🚀 优化：为单个推理步骤检索证据（支持复用前一步的证据）"""
        try:
            self.logger.info(f"🔍 [证据检索] 开始为推理步骤检索证据")
            self.logger.info(f"   🔎 子查询: {sub_query}")
            self.logger.info(f"   🏷️  步骤类型: {step.get('type', 'unknown')}")
            
            step_type = step.get('type', 'unknown')
            if step_type == 'answer_synthesis':
                combined_evidence: List[Evidence] = []
                if previous_evidence:
                    combined_evidence.extend(previous_evidence)
                previous_steps_context = context.get('previous_steps_context', [])
                if previous_steps_context:
                    for prev_ctx in previous_steps_context:
                        answer_text = prev_ctx.get('answer')
                        query_text = prev_ctx.get('query')
                        if not answer_text:
                            continue
                        content_parts = []
                        if query_text:
                            content_parts.append(f"Step query: {query_text}")
                        content_parts.append(f"Step answer: {answer_text}")
                        content = " | ".join(content_parts)
                        ev = Evidence(
                            content=content,
                            source="previous_step",
                            confidence=1.0,
                            relevance_score=1.0,
                            evidence_type="reasoning_step",
                            metadata={"step": prev_ctx.get('step')}
                        )
                        combined_evidence.append(ev)
                if combined_evidence:
                    self.logger.info(f"✅ [证据检索] answer_synthesis 步骤直接复用前面步骤证据和答案，不检索知识库")
                    print(f"✅ [证据检索] answer_synthesis 步骤使用 {len(combined_evidence)} 条前面步骤证据/答案")
                    return combined_evidence
            
            # 🚀 P0修复：验证并修复查询格式（在检索前）
            cleaned_query = self._validate_and_fix_query_format(sub_query)
            if not cleaned_query:
                self.logger.warning(f"⚠️ [证据检索] 查询格式验证失败，无法修复: {sub_query}")
                print(f"⚠️ [证据检索] 查询格式验证失败，无法修复: {sub_query}")
                return []
            
            if cleaned_query != sub_query:
                self.logger.info(f"🔄 [证据检索] 查询格式已修复: '{sub_query}' -> '{cleaned_query}'")
                print(f"🔄 [证据检索] 查询格式已修复: '{sub_query}' -> '{cleaned_query}'")
                sub_query = cleaned_query
            
            # 🚀 修复：确保context中没有已检索标志，允许主动检索
            # 因为这是新的子查询，需要重新检索
            context_for_query = context.copy()
            context_for_query['_knowledge_retrieved'] = False
            context_for_query.pop('knowledge', None)  # 清除之前的knowledge数据
            
            # 🚀 P1修复：增强检索系统的消歧能力，使用上下文信息增强查询
            enhanced_query = sub_query
            previous_steps_context = context.get('previous_steps_context', [])
            original_query = context.get('original_query', '')
            
            # 🚀 P0新增：查询重写 - 生成多个查询变体以提高检索质量
            query_variants = self._generate_query_variants_for_retrieval(sub_query, previous_steps_context, original_query)
            
            # 🚀 P0修复：对于序数查询，尝试更多变体
            is_ordinal_query = bool(re.search(r'\d+(?:st|nd|rd|th)', sub_query, re.IGNORECASE))
            max_variants = 5 if is_ordinal_query else 3
            
            # 🚀 方案2：对于序数查询，优先检索列表格式的内容
            if is_ordinal_query:
                ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', sub_query, re.IGNORECASE)
                if ordinal_match:
                    ordinal_num = ordinal_match.group(1)
                    
                    # 提取实体类型和上下文（通用模式，不硬编码）
                    ordinal_entity_pattern = r'(\d+(?:st|nd|rd|th))\s+([^?\'"]+?)(?:\s+of\s+the\s+[^?\'"]*?)?(?:\'s|of|$|\?)'
                    entity_match = re.search(ordinal_entity_pattern, sub_query, re.IGNORECASE)
                    
                    if entity_match:
                        entity_type = entity_match.group(2).strip()
                        # 移除常见的修饰语
                        entity_type = re.sub(r'\s+of\s+the\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', entity_type, flags=re.IGNORECASE)
                        entity_type = entity_type.strip()
                        
                        # 提取上下文
                        context_match = re.search(r'of\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sub_query, re.IGNORECASE)
                        context_str = context_match.group(1) if context_match else None
                        
                        if entity_type:
                            # 🚀 方案2：生成列表查询变体（优先检索）
                            list_queries = [
                                f"list of {entity_type} chronological order",
                                f"{entity_type} complete list order",
                                f"{ordinal_num}th {entity_type} list order chronological"
                            ]
                            
                            if context_str:
                                list_queries.extend([
                                    f"list of {entity_type} of {context_str} chronological order",
                                    f"{entity_type} of {context_str} complete list order",
                                    f"{ordinal_num}th {entity_type} {context_str} list order chronological"
                                ])
                            
                            # 将列表查询添加到查询变体的最前面（优先检索）
                            query_variants = list_queries + query_variants
                            self.logger.info(f"✅ [方案2] 序数查询优先检索列表格式: {len(list_queries)}个列表查询变体")
                            print(f"✅ [方案2] 序数查询优先检索列表格式: {len(list_queries)}个列表查询变体")
            
            # 尝试使用原始查询和所有变体检索证据
            all_evidence = []
            # 🚀 修复：对于序数查询，优先使用列表查询变体
            if is_ordinal_query:
                # 将列表查询变体放在最前面（优先检索）
                list_query_variants = [q for q in query_variants if 'list' in q.lower() or 'chronological' in q.lower()]
                other_variants = [q for q in query_variants if q not in list_query_variants]
                tried_queries = list_query_variants[:3] + [enhanced_query] + other_variants[:max_variants-3]
                self.logger.info(f"✅ [序数查询优化] 优先使用{len(list_query_variants[:3])}个列表查询变体")
                print(f"✅ [序数查询优化] 优先使用{len(list_query_variants[:3])}个列表查询变体")
            else:
                tried_queries = [enhanced_query] + query_variants[:max_variants]  # 最多尝试6个查询变体（原始+5个变体，对于序数查询）
            
            for idx, query_variant in enumerate(tried_queries):
                # 🚀 新增：记录使用的查询变体（用于诊断）
                is_list_query = 'list' in query_variant.lower() or 'chronological' in query_variant.lower()
                query_type_label = "列表查询" if is_list_query else "普通查询"
                self.logger.info(f"🔍 [证据检索-{idx+1}/{len(tried_queries)}] 使用{query_type_label}: {query_variant[:100]}")
                
                if previous_steps_context and len(previous_steps_context) > 0:
                    # 提取前面步骤的关键信息，用于消歧
                    context_keywords = []
                    for prev_step_ctx in previous_steps_context:
                        prev_answer = prev_step_ctx.get('answer', '')
                        prev_query = prev_step_ctx.get('query', '')
                        if prev_answer:
                            # 提取人名、地名等关键实体
                            # 提取完整人名（首字母大写的多个单词）
                            name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
                            names = re.findall(name_pattern, prev_answer)
                            if names:
                                context_keywords.extend(names[:2])  # 最多取前2个名字
                    
                    # 如果有关键词，增强查询
                    if context_keywords:
                        # 构建增强查询：在原始查询中添加上下文信息
                        context_str = ' '.join(context_keywords[:3])  # 最多3个关键词
                        query_variant = f"{query_variant} (context: {context_str})"
                
                # 使用查询变体检索证据
                variant_evidence = await self.gather_evidence(query_variant, context_for_query, query_analysis)
                if variant_evidence:
                    # 🚀 新增：检查是否包含列表格式的证据
                    list_evidence_count = 0
                    for ev in variant_evidence:
                        content = ev.content if hasattr(ev, 'content') and ev.content else str(ev)
                        if re.search(r'\d+[\.\)]\s+[A-Z][a-z]+', content):
                            list_evidence_count += 1
                    
                    if list_evidence_count > 0:
                        self.logger.info(f"✅ [证据检索-{idx+1}] 找到{len(variant_evidence)}条证据，其中{list_evidence_count}条包含列表格式")
                        print(f"✅ [证据检索-{idx+1}] 找到{len(variant_evidence)}条证据，其中{list_evidence_count}条包含列表格式")
                    else:
                        # 🚀 优化：对于非序数查询，列表格式不是必需的，降级为DEBUG级别
                        if is_ordinal_query:
                            # 序数查询需要列表格式，保持WARNING级别
                            self.logger.warning(f"⚠️ [证据检索-{idx+1}] 找到{len(variant_evidence)}条证据，但都不包含列表格式（序数查询可能需要列表格式）")
                            print(f"⚠️ [证据检索-{idx+1}] 找到{len(variant_evidence)}条证据，但都不包含列表格式（序数查询可能需要列表格式）")
                        else:
                            # 非序数查询，列表格式不是必需的，使用DEBUG级别
                            self.logger.debug(f"ℹ️ [证据检索-{idx+1}] 找到{len(variant_evidence)}条证据（不包含列表格式，对于非序数查询这是正常的）")
                    
                    all_evidence.extend(variant_evidence)
                    # 🚀 修复：对于序数查询，如果找到包含列表格式的证据，优先停止
                    if is_ordinal_query and list_evidence_count > 0:
                        self.logger.info(f"✅ [序数查询优化] 找到包含列表格式的证据，停止尝试其他变体")
                        print(f"✅ [序数查询优化] 找到包含列表格式的证据，停止尝试其他变体")
                        break
                    # 如果找到足够证据，停止尝试其他变体
                    elif len(all_evidence) >= 5:
                        break
                else:
                    self.logger.debug(f"⚠️ [证据检索-{idx+1}] 查询变体未找到证据: {query_variant[:100]}")
            
            # 去重并排序（按相关性）
            if all_evidence:
                # 使用集合去重（基于内容）
                seen_contents = set()
                unique_evidence = []
                for ev in all_evidence:
                    content_key = ev.content[:200] if hasattr(ev, 'content') and ev.content else str(ev)[:200]
                    if content_key not in seen_contents:
                        seen_contents.add(content_key)
                        unique_evidence.append(ev)
                
                # 🚀 修复：对于序数查询，优先保留包含列表格式的证据
                if is_ordinal_query:
                    # 计算每个证据的优先级分数
                    def calculate_priority(ev):
                        content = ev.content if hasattr(ev, 'content') and ev.content else str(ev)
                        relevance = ev.relevance_score or ev.confidence or 0.0
                        
                        # 检查是否包含列表格式（编号列表、项目符号等）
                        has_list_format = bool(re.search(r'\d+[\.\)]\s+[A-Z][a-z]+', content))
                        # 检查是否包含多个列表项（至少5个）
                        list_items = re.findall(r'\d+[\.\)]\s+[A-Z][a-z]+', content)
                        has_multiple_items = len(list_items) >= 5
                        # 检查内容长度（较长的内容更可能包含完整列表）
                        is_long_content = len(content) > 200
                        
                        # 计算优先级分数
                        priority = relevance
                        if has_list_format:
                            priority += 0.3  # 包含列表格式，加分
                        if has_multiple_items:
                            priority += 0.2  # 包含多个列表项，加分
                        if is_long_content:
                            priority += 0.1  # 较长内容，加分
                        
                        return priority
                    
                    unique_evidence.sort(key=calculate_priority, reverse=True)
                    self.logger.info(f"✅ [序数查询优化] 按列表格式优先级排序证据")
                    print(f"✅ [序数查询优化] 按列表格式优先级排序证据")
                else:
                    # 非序数查询，按相关性排序
                    unique_evidence.sort(key=lambda e: e.relevance_score or e.confidence, reverse=True)
                
                evidence = unique_evidence[:10]  # 最多保留10条最相关的证据
                self.logger.info(f"✅ [查询重写] 使用{len(tried_queries)}个查询变体，找到{len(evidence)}条去重后的证据")
            else:
                evidence = []
            
            # 🚀 P1新增：如果证据不相关，尝试重新检索（使用更具体的查询）
            # 🚀 修复：检查是否已经由UnifiedEvidenceFramework处理过（避免重复检查）
            # 如果context中有_relevance_checked标志，说明已经检查过，跳过
            if evidence and len(evidence) > 0 and not context_for_query.get('_relevance_checked', False):
                # 检查证据是否直接回答了问题
                try:
                    from src.core.reasoning.evidence_preprocessor import EvidencePreprocessor, ProcessedEvidence
                    preprocessor = EvidencePreprocessor()
                    # 🚀 方案1：传递query参数，用于针对序数查询进行特殊过滤
                    processed_evidence = preprocessor.clean_retrieved_chunks(evidence, query=sub_query)
                    
                    if processed_evidence and len(processed_evidence) > 0:
                        answer_relevance = preprocessor.check_answer_relevance(processed_evidence, sub_query)
                        
                        # 如果证据不直接回答问题，尝试重新检索
                        if not answer_relevance.get('has_direct_answer', False):
                            # 🚀 优化：这是正常的重试机制，降级为INFO级别
                            self.logger.info(
                                f"ℹ️ [证据相关性检查] 证据不直接回答问题，尝试重新检索: {sub_query[:80]}..."
                            )
                            self.logger.debug(f"🔍 [证据相关性检查] 相关性评分: {answer_relevance.get('relevance_score', 0.0):.2f}")
                            
                            # 🚀 重构：生成更具体的查询变体（使用通用模式，不硬编码特定实体）
                            ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', sub_query, re.IGNORECASE)
                            if ordinal_match:
                                ordinal_num = ordinal_match.group(1)
                                
                                # 🚀 通用化：提取实体类型和上下文（不硬编码"first lady"、"president"等）
                                ordinal_entity_pattern = r'(\d+(?:st|nd|rd|th))\s+([^?\'"]+?)(?:\s+of\s+the\s+[^?\'"]*?)?(?:\'s|of|$|\?)'
                                entity_match = re.search(ordinal_entity_pattern, sub_query, re.IGNORECASE)
                                
                                if entity_match:
                                    entity_type = entity_match.group(2).strip()
                                    # 移除常见的修饰语
                                    entity_type = re.sub(r'\s+of\s+the\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', entity_type, flags=re.IGNORECASE)
                                    entity_type = entity_type.strip()
                                    
                                    # 提取上下文
                                    context_match = re.search(r'of\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', sub_query, re.IGNORECASE)
                                    context_str: Optional[str] = context_match.group(1) if context_match else None
                                    
                                    if entity_type:
                                        # 生成通用列表查询变体
                                        retry_queries = [
                                            f"list of {entity_type} chronological order",
                                            f"{entity_type} complete list order",
                                            f"{ordinal_num}th {entity_type} list order chronological"
                                        ]
                                        
                                        if context_str:
                                            retry_queries.extend([
                                                f"list of {entity_type} of {context_str} chronological order",
                                                f"{entity_type} of {context_str} complete list order",
                                                f"{ordinal_num}th {entity_type} {context_str} list order chronological"
                                            ])
                                    else:
                                        # 从答案相关性结果中获取建议，确保是列表类型
                                        suggestions = answer_relevance.get('suggestions', []) if answer_relevance else []
                                        retry_queries = suggestions if isinstance(suggestions, list) else []
                                else:
                                    # 从答案相关性结果中获取建议，确保是列表类型
                                    suggestions = answer_relevance.get('suggestions', []) if answer_relevance else []
                                    retry_queries = suggestions if isinstance(suggestions, list) else []
                                
                                # 尝试使用更具体的查询重新检索
                                for retry_query in retry_queries[:2]:  # 最多尝试2个变体
                                    retry_evidence = await self.gather_evidence(
                                        retry_query, context_for_query, query_analysis
                                    )
                                    if retry_evidence:
                                        # 检查重新检索的证据是否更相关
                                        retry_processed = preprocessor.clean_retrieved_chunks(retry_evidence, query=sub_query)
                                        if retry_processed and len(retry_processed) > 0:
                                            retry_relevance = preprocessor.check_answer_relevance(
                                                retry_processed, sub_query
                                            )
                                            if retry_relevance.get('has_direct_answer', False):
                                                # 重新检索的证据更相关，使用它
                                                evidence = retry_evidence
                                                self.logger.info(
                                                    f"✅ [证据相关性检查] 重新检索成功，找到更相关的证据: {retry_query[:80]}..."
                                                )
                                                print(f"✅ [证据相关性检查] 重新检索成功，找到更相关的证据: {retry_query[:80]}...")
                                                break
                except Exception as e:
                    self.logger.debug(f"检查答案相关性失败: {e}")
            
            # 🚀 ML/RL增强：使用AdaptiveOptimizer优化证据数量
            if self.adaptive_optimizer and evidence:
                try:
                    query_type = query_analysis.get('query_type', 'general') if isinstance(query_analysis, dict) else 'general'
                    # 获取优化的证据数量
                    optimal_count, min_count, max_count = self.adaptive_optimizer.get_optimized_evidence_count(
                        query_type, default_count=len(evidence)
                    )
                    # 如果当前证据数量与优化数量差异较大，调整证据数量
                    if len(evidence) > max_count:
                        evidence = evidence[:max_count]
                        self.logger.info(f"✅ [ML/RL] 使用优化的最大证据数量: {max_count} (原始: {len(evidence)})")
                    elif len(evidence) < min_count and len(evidence) > 0:
                        # 如果证据数量少于最小值，尝试检索更多（但这里已经检索完成，只能记录）
                        self.logger.debug(f"⚠️ [ML/RL] 证据数量({len(evidence)})少于优化最小值({min_count})，但已检索完成")
                except Exception as e:
                    self.logger.debug(f"AdaptiveOptimizer优化证据数量失败: {e}")
            
            # 🚀 彻底修复：如果检索失败且子查询是多跳查询，尝试拆解并尝试所有拆解后的查询
            if not evidence or len(evidence) == 0:
                print(f"⚠️ [证据检索] 初始检索未找到证据，尝试其他方法...")
                if self._is_multi_hop_query(sub_query):
                    print(f"⚠️ [证据检索] 多跳查询检索失败，尝试拆解: {sub_query[:80]}...")
                    self.logger.warning(f"⚠️ 多跳查询检索失败，尝试拆解: {sub_query[:80]}...")
                    decomposed_queries = await self._decompose_multi_hop_query(sub_query, previous_evidence)
                    if decomposed_queries:
                        # 🚀 彻底修复：尝试所有拆解后的查询，而不是只尝试第一个
                        for decomposed_query in decomposed_queries:
                            print(f"🔍 [证据检索] 尝试拆解后的查询: {decomposed_query}")
                            self.logger.info(f"🔍 尝试拆解后的查询: {decomposed_query}")
                            evidence = await self.gather_evidence(decomposed_query, context, query_analysis)
                            if evidence and len(evidence) > 0:
                                print(f"✅ [证据检索] 拆解后的查询检索成功: {decomposed_query}, 证据数={len(evidence)}")
                                self.logger.info(f"✅ 拆解后的查询检索成功: {decomposed_query}, 证据数={len(evidence)}")
                                break
                        else:
                            # 如果所有拆解后的查询都失败，尝试更简单的查询
                            print(f"⚠️ [证据检索] 所有拆解后的查询都失败，尝试更简单的查询")
                            self.logger.warning(f"⚠️ 所有拆解后的查询都失败，尝试更简单的查询")
                            # 提取核心实体和关系，生成更简单的查询
                            simplified_query = self._simplify_query_for_retrieval(sub_query)
                            if simplified_query and simplified_query != sub_query:
                                print(f"🔍 [证据检索] 尝试简化后的查询: {simplified_query}")
                                self.logger.info(f"🔍 尝试简化后的查询: {simplified_query}")
                                evidence = await self.gather_evidence(simplified_query, context, query_analysis)
                                if evidence and len(evidence) > 0:
                                    print(f"✅ [证据检索] 简化后的查询检索成功: {simplified_query}, 证据数={len(evidence)}")
                                    self.logger.info(f"✅ 简化后的查询检索成功: {simplified_query}, 证据数={len(evidence)}")
            
            # 如果前一步有证据，尝试复用或合并
            if previous_evidence and len(previous_evidence) > 0:
                relevant_previous_evidence = self.filter_relevant_previous_evidence(
                    previous_evidence, sub_query, step
                )
                if relevant_previous_evidence:
                    for prev_ev in relevant_previous_evidence:
                        if prev_ev not in evidence:
                            evidence.insert(0, prev_ev)
                    self.logger.debug(f"✅ 合并了{len(relevant_previous_evidence)}条前一步的相关证据")
            
            # 🚀 添加终端输出：显示证据检索结果
            if evidence and len(evidence) > 0:
                print(f"✅ [证据检索] 找到 {len(evidence)} 条证据 (子查询: {sub_query[:80]}...)")
                self.logger.info(f"✅ [证据检索] 推理步骤证据检索完成: 证据数={len(evidence)} (子查询: {sub_query})")
            else:
                print(f"❌ [证据检索] 未找到证据 (子查询: {sub_query[:80]}...)")
                self.logger.warning(f"❌ [证据检索] 推理步骤证据检索完成: 未找到证据 (子查询: {sub_query})")
            return evidence
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            self.logger.error(f"❌ 为推理步骤检索证据失败: {e}\n详细错误堆栈:\n{error_traceback}")
            return []
    
    def _is_multi_hop_query(self, query: str) -> bool:
        """🚀 P0修复：判断是否为多跳查询"""
        if not query:
            return False
        
        # 多跳查询的特征：包含多个关系链（如"15th first lady's mother's first name"）
        multi_hop_indicators = [
            r"'\s*(mother|father|parent|child|son|daughter|wife|husband|spouse)",
            r"of\s+the\s+\d+(st|nd|rd|th)",
            r"the\s+\d+(st|nd|rd|th)\s+\w+\s+of",
            r"\w+\s+of\s+\w+\s+of",  # "X of Y of Z"
            r"\w+\s+'s\s+\w+\s+'s",  # "X's Y's Z"
        ]
        
        for pattern in multi_hop_indicators:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        return False
    
    async def _decompose_multi_hop_query(
        self, 
        query: str, 
        previous_evidence: Optional[List[Evidence]] = None
    ) -> List[str]:
        """🚀 重构：通用多跳查询拆解（使用LLM或通用模式，而非硬编码规则）
        
        Args:
            query: 多跳查询
            previous_evidence: 前一步的证据（可选）
            
        Returns:
            拆解后的单跳查询列表
        """
        try:
            
            # 🚀 策略1: 使用LLM智能拆解（如果可用）
            if self.llm_integration:
                try:
                    decomposed = await self._decompose_with_llm(query)
                    if decomposed:
                        self.logger.info(f"✅ LLM拆解多跳查询: {len(decomposed)} 个中间步骤")
                        return decomposed
                except Exception as e:
                    self.logger.debug(f"LLM拆解失败，使用通用模式: {e}")
            
            # 🚀 策略2: 使用通用关系模式拆解
            decomposed = self._decompose_with_generic_patterns(query)
            if decomposed:
                self.logger.info(f"✅ 通用模式拆解多跳查询: {len(decomposed)} 个中间步骤")
                return decomposed
            
            return []
            
        except Exception as e:
            self.logger.debug(f"拆解多跳查询失败: {e}")
            return []
    
    def _simplify_query_for_retrieval(self, query: str) -> Optional[str]:
        """🚀 彻底修复：简化查询以便检索（当拆解失败时使用）
        
        从复杂查询中提取核心实体和关系，生成更简单的查询
        例如："What is the first name of the 15th first lady of the United States' mother?"
        -> "Who was the 15th first lady of the United States?"
        """
        try:
            
            # 提取序数+实体模式（如"15th first lady"）
            ordinal_entity_match = re.search(r'(\d+(?:st|nd|rd|th))\s+([^?\'"]+?)(?:\'s|of|$)', query, re.IGNORECASE)
            if ordinal_entity_match:
                ordinal = ordinal_entity_match.group(1)
                entity_part = ordinal_entity_match.group(2).strip()
                
                # 🚀 通用化：移除常见的修饰语（不限于"of the United States"）
                # 移除"of the X"格式的修饰语（如"of the United States"、"of the country"等）
                entity_part = re.sub(r'\s+of\s+the\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', entity_part, flags=re.IGNORECASE)
                # 移除"of X"格式的修饰语（如"of America"、"of China"等）
                entity_part = re.sub(r'\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', entity_part, flags=re.IGNORECASE)
                entity_part = entity_part.strip()
                if entity_part:
                    return f"Who was the {ordinal} {entity_part}?"
            
            # 提取"first name of X"模式
            first_name_match = re.search(r'first\s+name\s+of\s+([^?]+)', query, re.IGNORECASE)
            if first_name_match:
                entity = first_name_match.group(1).strip()
                # 移除"the"等冠词
                entity = re.sub(r'^(the|a|an)\s+', '', entity, flags=re.IGNORECASE)
                if entity:
                    return f"Who is {entity}?"
            
            # 提取"mother of X"模式
            mother_match = re.search(r'mother\s+of\s+([^?]+)', query, re.IGNORECASE)
            if mother_match:
                entity = mother_match.group(1).strip()
                entity = re.sub(r'^(the|a|an)\s+', '', entity, flags=re.IGNORECASE)
                if entity:
                    return f"Who is {entity}'s mother?"
            
            return None
        except Exception as e:
            self.logger.debug(f"简化查询失败: {e}")
            return None
    
    def _validate_and_fix_query_format(self, query: str) -> Optional[str]:
        """🚀 P0新增：验证并修复查询格式
        
        功能：
        1. 检测格式错误的查询（如"Harriet Lane What name mother"）
        2. 尝试修复查询格式（添加问号、重构为完整疑问句）
        3. 如果无法修复，返回None
        
        Args:
            query: 原始查询
            
        Returns:
            修复后的查询，如果无法修复返回None
        """
        try:
            if not query or not query.strip():
                return None
            
            query = query.strip()
            query_lower = query.lower()
            
            # 🚀 检测格式错误的查询模式（如"Harriet Lane What name mother"）
            # 模式：实体名 + 疑问词 + 关键词（缺少问号，不是完整疑问句）
            malformed_pattern = r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(what|who|where|when|which)\s+(name|mother|father|first|last|maiden)\s*$'
            match = re.match(malformed_pattern, query, re.IGNORECASE)
            
            if match:
                entity_name = match.group(1)
                question_word = match.group(2).lower()
                keyword = match.group(3).lower()
                
                # 尝试修复查询格式
                if keyword == 'mother':
                    fixed_query = f"Who was {entity_name}'s mother?"
                elif keyword == 'father':
                    fixed_query = f"Who was {entity_name}'s father?"
                elif keyword in ['name', 'first', 'last', 'maiden']:
                    # 需要更多上下文来确定正确的查询，尝试通用修复
                    if 'first' in keyword or keyword == 'name':
                        fixed_query = f"What was {entity_name}'s first name?"
                    elif keyword == 'last':
                        fixed_query = f"What was {entity_name}'s last name?"
                    elif keyword == 'maiden':
                        fixed_query = f"What was {entity_name}'s maiden name?"
                    else:
                        fixed_query = f"What was {entity_name}'s {keyword}?"
                else:
                    # 无法确定，返回None
                    self.logger.warning(f"⚠️ [查询修复] 无法修复查询格式: {query}")
                    return None
                
                self.logger.info(f"✅ [查询修复] 修复查询格式: '{query}' -> '{fixed_query}'")
                print(f"✅ [查询修复] 修复查询格式: '{query}' -> '{fixed_query}'")
                return fixed_query
            
            # 🚀 检测缺少问号的查询
            if '?' not in query:
                # 检查是否以疑问词开头
                question_words = ['what', 'who', 'where', 'when', 'which', 'how', 'why']
                first_word = query_lower.split()[0] if query_lower.split() else ""
                
                if first_word in question_words:
                    # 是疑问句，但缺少问号，添加问号
                    fixed_query = query.rstrip('.!') + '?'
                    self.logger.info(f"✅ [查询修复] 添加问号: '{query}' -> '{fixed_query}'")
                    return fixed_query
                else:
                    # 不是疑问句格式，尝试修复
                    # 如果包含常见关键词，尝试重构为疑问句
                    if 'mother' in query_lower:
                        # 提取实体名（假设是第一个大写词序列）
                        entity_match = re.search(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', query)
                        if entity_match:
                            entity_name = entity_match.group(1)
                            fixed_query = f"Who was {entity_name}'s mother?"
                            self.logger.info(f"✅ [查询修复] 重构为疑问句: '{query}' -> '{fixed_query}'")
                            return fixed_query
            
            # 查询格式正确，直接返回
            return query
            
        except Exception as e:
            self.logger.debug(f"验证和修复查询格式失败: {e}")
            return query  # 失败时返回原始查询
    
    async def _decompose_with_llm(self, query: str) -> List[str]:
        """使用LLM智能拆解多跳查询"""
        try:
            if not self.llm_integration:
                return []
            
            prompt = f"""Decompose the following multi-hop query into sequential single-hop queries.

**Rules:**
1. Each sub-query should be a standalone question that can be answered by a knowledge base
2. Sub-queries should be ordered logically (earlier queries provide context for later ones)
3. Use placeholders like [ENTITY] for entities that will be filled from previous steps
4. Return ONLY a JSON array of sub-queries, no explanations

**Example:**
Query: "What is the first name of the 15th first lady's mother?"
Sub-queries:
[
  "Who was the 15th first lady of the United States?",
  "Who was [first lady]'s mother?",
  "What is [mother]'s first name?"
]

**Query to decompose:**
{query}

**Sub-queries (JSON array):**
"""
            
            response = self.llm_integration._call_llm(prompt)
            if not response:
                return []
            
            # 尝试解析JSON数组
            import json
            # 移除可能的markdown代码块标记
            response = re.sub(r'```json\s*', '', response)
            response = re.sub(r'```\s*', '', response)
            response = response.strip()
            
            try:
                sub_queries = json.loads(response)
                if isinstance(sub_queries, list) and all(isinstance(q, str) for q in sub_queries):
                    return sub_queries
            except json.JSONDecodeError:
                # 尝试提取数组内容
                array_match = re.search(r'\[(.*?)\]', response, re.DOTALL)
                if array_match:
                    # 简单提取引号内的内容
                    quoted_items = re.findall(r'"([^"]+)"', array_match.group(1))
                    if quoted_items:
                        return quoted_items
            
            return []
        except Exception as e:
            self.logger.debug(f"LLM拆解查询失败: {e}")
            return []
    
    def _decompose_with_generic_patterns(self, query: str) -> List[str]:
        """使用通用关系模式拆解多跳查询
        
        识别通用的关系链模式：
        - X's Y's Z (所有格链)
        - X of Y of Z (of链)
        - ordinal + entity (序数+实体)
        - filtered entity (筛选实体，如"assassinated president")
        """
        try:
            decomposed = []
            
            # 🚀 通用模式1: 识别所有格链 (X's Y's Z)
            possessive_chain = re.search(r"(\w+(?:\s+\w+)*)'s\s+(\w+(?:\s+\w+)*)'s\s+(\w+(?:\s+\w+)*)", query, re.IGNORECASE)
            if possessive_chain:
                # 提取链中的实体
                entity1 = possessive_chain.group(1)
                entity2 = possessive_chain.group(2)
                entity3 = possessive_chain.group(3)
                
                # 生成中间查询
                # 步骤1: 找到第一个实体
                if re.search(r'\d+(st|nd|rd|th)', entity1, re.IGNORECASE):
                    # 如果是序数+实体，生成查询
                    ordinal_match = re.search(r'(\d+(st|nd|rd|th))', entity1, re.IGNORECASE)
                    if ordinal_match:
                        ordinal = ordinal_match.group(1)
                        entity_type = re.sub(r'\d+(st|nd|rd|th)\s+', '', entity1, flags=re.IGNORECASE).strip()
                        decomposed.append(f"Who was the {ordinal} {entity_type}?")
                else:
                    decomposed.append(f"Who is {entity1}?")
                
                # 步骤2: 找到第二个实体（使用占位符）
                decomposed.append(f"Who is [entity1]'s {entity2}?")
                
                # 步骤3: 找到第三个实体（使用占位符）
                decomposed.append(f"What is [entity2]'s {entity3}?")
                
                return decomposed
            
            # 🚀 通用模式2: 识别of链 (X of Y of Z)
            of_chain = re.search(r"(\w+(?:\s+\w+)*)\s+of\s+(\w+(?:\s+\w+)*)\s+of\s+(\w+(?:\s+\w+)*)", query, re.IGNORECASE)
            if of_chain:
                attr1 = of_chain.group(1)
                entity1 = of_chain.group(2)
                entity2 = of_chain.group(3)
                
                # 生成中间查询
                decomposed.append(f"Who is {entity2}?")
                decomposed.append(f"Who is the {entity1} of [entity2]?")
                decomposed.append(f"What is the {attr1} of [entity1]?")
                
                return decomposed
            
            # 🚀 通用模式3: 识别序数+实体+关系链
            # 例如: "15th first lady's mother's first name"
            ordinal_entity_pattern = r"(\d+(st|nd|rd|th))\s+(\w+(?:\s+\w+)*)(?:'s\s+(\w+(?:\s+\w+)*))?"
            match = re.search(ordinal_entity_pattern, query, re.IGNORECASE)
            if match:
                ordinal = match.group(1)
                entity_type = match.group(3)
                
                # 检查是否有后续关系
                if match.group(4):
                    relation = match.group(4)
                    decomposed.append(f"Who was the {ordinal} {entity_type}?")
                    decomposed.append(f"Who was [entity]'s {relation}?")
                    
                    # 检查是否有属性查询
                    if "first name" in query.lower():
                        decomposed.append("What is [relation]'s first name?")
                    elif "last name" in query.lower() or "surname" in query.lower():
                        decomposed.append("What is [relation]'s last name?")
                    elif "maiden name" in query.lower():
                        decomposed.append("What is [relation]'s maiden name?")
                else:
                    decomposed.append(f"Who was the {ordinal} {entity_type}?")
                
                return decomposed
            
            # 🚀 通用模式4: 识别筛选实体+关系链
            # 例如: "second assassinated president's mother's maiden name"
            filtered_entity_pattern = r"(\w+)\s+(\w+(?:\s+\w+)*)(?:'s\s+(\w+(?:\s+\w+)*))?"
            
            # 🚀 通用化：从统一配置中心获取筛选词列表（不硬编码）
            filter_keywords = []
            try:
                from src.utils.unified_rule_manager import get_unified_rule_manager
                rule_manager = get_unified_rule_manager()
                if rule_manager:
                    filter_keywords = rule_manager.get_keywords('filter_keywords', query)
            except Exception as e:
                self.logger.debug(f"从统一规则管理器获取筛选词失败: {e}")
            
            # Fallback: 如果配置中心没有，使用默认的通用筛选词
            if not filter_keywords:
                filter_keywords = ['first', 'second', 'third', 'fourth', 'fifth', 'last', 
                                 'assassinated', 'elected', 'appointed', 'nominated', 'selected']
            
            query_lower = query.lower()
            for keyword in filter_keywords:
                if keyword in query_lower:
                    # 尝试提取筛选实体
                    pattern = rf"{keyword}\s+(\w+(?:\s+\w+)*)"
                    match = re.search(pattern, query, re.IGNORECASE)
                    if match:
                        entity_type = match.group(1)
                        decomposed.append(f"Who was the {keyword} {entity_type}?")
                        
                        # 检查是否有后续关系
                        remaining = query[match.end():].strip()
                        if remaining.startswith("'s"):
                            relation_match = re.search(r"'s\s+(\w+(?:\s+\w+)*)", remaining, re.IGNORECASE)
                            if relation_match:
                                relation = relation_match.group(1)
                                decomposed.append(f"Who was [entity]'s {relation}?")
                                
                                # 检查是否有属性查询
                                if "first name" in query.lower():
                                    decomposed.append("What is [relation]'s first name?")
                                elif "last name" in query.lower() or "surname" in query.lower():
                                    decomposed.append("What is [relation]'s last name?")
                                elif "maiden name" in query.lower():
                                    decomposed.append("What is [relation]'s maiden name?")
                        
                        return decomposed
            
            return []
            
        except Exception as e:
            self.logger.debug(f"通用模式拆解失败: {e}")
            return []
    
    def process_evidence_intelligently(self, query: str, evidence_text: str, evidence_list: List[Any], query_type: str = "general", get_evidence_target_length=None, is_ranking_query=None) -> str:
        """🚀 改进：智能处理证据 - 根据查询类型调整压缩策略，智能保留关键信息"""
        original_length = len(evidence_text) if evidence_text else 0
        
        try:
            if not evidence_text or len(evidence_text.strip()) < 50:
                return evidence_text
            
            # 使用传入的函数获取目标长度（如果提供）
            if get_evidence_target_length:
                target_length = get_evidence_target_length(query, query_type)
            else:
                # 默认目标长度
                target_length = 1000
            
            if len(evidence_text) <= target_length:
                return evidence_text
            
            # 检查是否是排名查询
            if is_ranking_query and is_ranking_query(query, query_type):
                ranking_section = self._extract_ranking_section(evidence_text, query)
                if ranking_section and len(ranking_section) <= target_length * 1.2:
                    return ranking_section
            
            # 策略1: 提取与查询最相关的证据片段
            relevant_segments = self._extract_relevant_segments(query, evidence_text, evidence_list, target_length)
            if relevant_segments and len(relevant_segments) >= target_length * 0.8:
                return relevant_segments
            
            # 策略2: 使用智能截断
            if len(evidence_text) > target_length * 1.5:
                first_part_length = int(target_length * 0.6)
                last_part_length = int(target_length * 0.4)
                first_part = evidence_text[:first_part_length]
                last_part = evidence_text[-last_part_length:]
                return f"{first_part}\n\n[... middle content omitted for length, {len(evidence_text) - first_part_length - last_part_length} characters ...]\n\n{last_part}"
            
            # 策略3: 简单截断
            return evidence_text[:target_length]
            
        except Exception as e:
            self.logger.warning(f"智能证据处理失败，使用原始证据: {e}")
            return evidence_text[:1000] if len(evidence_text) > 1000 else evidence_text
    
    def _generate_query_variants_for_retrieval(
        self, 
        query: str, 
        previous_steps_context: List[Dict[str, Any]], 
        original_query: str
    ) -> List[str]:
        """🚀 P1新增：生成查询变体以提高检索质量
        
        策略：
        1. 提取关键词生成简化查询
        2. 使用同义词替换
        3. 添加相关实体名称（从上下文）
        4. 重构查询结构（如"X's Y" -> "Y of X"）
        
        Args:
            query: 原始查询
            previous_steps_context: 前面步骤的上下文
            original_query: 原始查询
            
        Returns:
            查询变体列表
        """
        try:
            variants = []
            query_lower = query.lower()
            
            # 策略1: 提取核心关键词生成简化查询
            # 提取重要关键词（排除停用词）
            stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'who', 'where', 'when', 'why', 'how', 'of', 'in', 'on', 'at', 'to', 'for', 'with', 'from', 'by', 'and', 'or', 'but'}
            keywords = [w for w in query.split() if w.lower() not in stop_words and len(w) > 2]
            
            if keywords:
                # 生成关键词查询
                keyword_query = ' '.join(keywords[:5])  # 最多5个关键词
                if keyword_query and keyword_query != query:
                    variants.append(keyword_query)
            
            # 策略2: 从上下文提取实体名称，生成实体查询
            if previous_steps_context:
                for prev_step_ctx in previous_steps_context[:2]:  # 最多检查前2个步骤
                    prev_answer = prev_step_ctx.get('answer', '')
                    if prev_answer:
                        # 提取完整人名
                        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
                        names = re.findall(name_pattern, prev_answer)
                        if names:
                            # 如果查询包含关系词（如"mother"、"father"），生成实体+关系查询
                            if 'mother' in query_lower:
                                for name in names[:1]:  # 只取第一个名字
                                    variants.append(f"{name} mother")
                            elif 'father' in query_lower:
                                for name in names[:1]:
                                    variants.append(f"{name} father")
                            elif 'first name' in query_lower or 'maiden name' in query_lower:
                                for name in names[:1]:
                                    variants.append(f"{name} {'first name' if 'first name' in query_lower else 'maiden name'}")
            
            # 策略3: 重构查询结构（如"X's Y" -> "Y of X"）
            # 匹配"X's Y"模式
            possessive_match = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'s\s+(\w+(?:\s+\w+)*)", query)
            if possessive_match:
                entity = possessive_match.group(1)
                relation = possessive_match.group(2)
                # 生成"Y of X"格式
                if 'who' in query_lower:
                    variants.append(f"Who is the {relation} of {entity}?")
                elif 'what' in query_lower:
                    variants.append(f"What is the {relation} of {entity}?")
            
            # 策略4: 如果查询包含序数词，生成更具体的查询变体（用于查找列表和序号对应）
            # 🚀 重构：使用通用模式匹配，不硬编码特定实体类型
            ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', query, re.IGNORECASE)
            if ordinal_match:
                ordinal_num = ordinal_match.group(1)
                
                # 🚀 通用化：提取实体类型和上下文（不硬编码"first lady"、"president"等）
                # 模式1: 提取序数词后的实体类型（如"15th first lady" -> "first lady"）
                ordinal_entity_pattern = r'(\d+(?:st|nd|rd|th))\s+([^?\'"]+?)(?:\s+of\s+the\s+[^?\'"]*?)?(?:\'s|of|$|\?)'
                entity_match = re.search(ordinal_entity_pattern, query, re.IGNORECASE)
                
                if entity_match:
                    entity_type = entity_match.group(2).strip()
                    # 移除常见的修饰语（如"of the United States"）
                    entity_type = re.sub(r'\s+of\s+the\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', '', entity_type, flags=re.IGNORECASE)
                    entity_type = entity_type.strip()
                    
                    # 提取上下文（如"United States"、"US"等）
                    context_match = re.search(r'of\s+the\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', query, re.IGNORECASE)
                    context = context_match.group(1) if context_match else None
                    
                    if entity_type:
                        # 🚀 通用化：生成列表查询变体（适用于任何实体类型）
                        # 变体1: 完整列表查询（不带序数词）
                        list_variants = [
                            f"list of {entity_type} chronological order",
                            f"{entity_type} complete list order",
                            f"{entity_type} numbered list",
                            f"all {entity_type} in order"
                        ]
                        
                        # 如果有关键词，添加带上下文的变体
                        if context:
                            list_variants.extend([
                                f"list of {entity_type} of {context} chronological order",
                                f"{entity_type} of {context} complete list order",
                                f"all {entity_type} of {context} in order"
                            ])
                        
                        variants.extend(list_variants)
                        
                        # 变体2: 包含序数词的更具体查询
                        ordinal_variants = [
                            f"{ordinal_num}th {entity_type} list order chronological",
                            f"{entity_type} number {ordinal_num}",
                            f"name of the {ordinal_num}th {entity_type}",
                            f"who was the {ordinal_num}th {entity_type}"
                        ]
                        
                        if context:
                            ordinal_variants.extend([
                                f"{ordinal_num}th {entity_type} {context} list order chronological",
                                f"{entity_type} number {ordinal_num} {context}",
                                f"name of the {ordinal_num}th {entity_type} of {context}",
                                f"who was the {ordinal_num}th {entity_type} of {context}"
                            ])
                        
                        variants.extend(ordinal_variants)
            
            # 去重并限制数量
            unique_variants = []
            seen = {query.lower()}
            for variant in variants:
                variant_lower = variant.lower()
                if variant_lower not in seen and len(variant.strip()) > 5:
                    seen.add(variant_lower)
                    unique_variants.append(variant)
            
            # 🚀 P0修复：对于序数查询，返回更多变体（最多5个），其他查询返回3个
            max_variants = 5 if ordinal_match else 3
            return unique_variants[:max_variants]
            
        except Exception as e:
            self.logger.debug(f"生成查询变体失败: {e}")
            return []
    
    async def attempt_robust_retrieval(
        self,
        sub_query: str,
        original_query: str,
        previous_step_answer: Optional[str],
        context: Dict[str, Any],
        step: Dict[str, Any],
        answer_extractor: Optional[Any] = None,
        subquery_processor: Optional[Any] = None
    ) -> Optional[str]:
        """🚀 增强：尝试多种检索策略获取证据
        
        从 engine.py 迁移的方法，用于尝试多种检索策略获取证据。
        
        Args:
            sub_query: 子查询
            original_query: 原始查询
            previous_step_answer: 上一步答案
            context: 上下文
            step: 步骤信息
            answer_extractor: 答案提取器（可选，从engine传入）
            subquery_processor: 子查询处理器（可选，从engine传入）
            
        Returns:
            提取的答案，如果失败返回None
        """
        if not self:
            return None
        
        try:
            self.logger.info(f"🔄 [增强检索] 尝试多种检索策略: {sub_query[:100]}")
            print(f"🔄 [增强检索] 尝试多种检索策略: {sub_query[:100]}")
            
            # 策略1: 使用原始子查询检索（🚀 优化：设置30秒超时）
            try:
                evidence = await asyncio.wait_for(
                    self.gather_evidence(
                        sub_query, context, {'type': 'evidence_gathering'}
                    ),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                self.logger.warning(f"⚠️ [增强检索] 策略1检索超时（30秒），跳过")
                evidence = None
            
            if evidence and len(evidence) > 0:
                if answer_extractor:
                    answer = answer_extractor.extract_step_result(
                        evidence, step, previous_step_answer, original_query, sub_query
                    )
                    if answer:
                        return answer
            
            # 策略2: 如果包含占位符，替换为实际值后检索
            if previous_step_answer and ('[result' in sub_query.lower() or '[step' in sub_query.lower() or '[previous' in sub_query.lower()):
                # 🚀 改进：使用subquery_processor的占位符替换方法，支持所有占位符模式
                if subquery_processor:
                    # 获取前一步的证据用于实体规范化
                    prev_step_evidence = context.get('previous_step_evidence', [])
                    enhanced_query = subquery_processor._replace_placeholders_generic(
                        sub_query, 
                        previous_step_answer,
                        previous_step_evidence=prev_step_evidence,
                        original_query=original_query
                    )
                else:
                    # Fallback：手动替换常见占位符
                    enhanced_query = sub_query.replace('[result from step 1]', previous_step_answer)
                    enhanced_query = enhanced_query.replace('[result from step 2]', previous_step_answer)
                    enhanced_query = enhanced_query.replace('[step 1 result]', previous_step_answer)
                    enhanced_query = enhanced_query.replace('[step 2 result]', previous_step_answer)
                    enhanced_query = enhanced_query.replace('[result from previous step]', previous_step_answer)
                    enhanced_query = enhanced_query.replace('[previous step result]', previous_step_answer)
                
                if enhanced_query != sub_query:
                    # 🚀 优化：设置30秒超时
                    try:
                        evidence = await asyncio.wait_for(
                            self.gather_evidence(
                                enhanced_query, context, {'type': 'evidence_gathering'}
                            ),
                            timeout=30.0
                        )
                    except asyncio.TimeoutError:
                        self.logger.warning(f"⚠️ [增强检索] 策略2检索超时（30秒），跳过")
                        evidence = None
                    if evidence and len(evidence) > 0:
                        if answer_extractor:
                            answer = answer_extractor.extract_step_result(
                                evidence, step, previous_step_answer, original_query, enhanced_query
                            )
                            if answer:
                                return answer
            
            # 策略3: 生成多个查询变体（🚀 优化：设置30秒超时）
            query_variants = self.generate_query_variants(sub_query, previous_step_answer, original_query)
            for variant in query_variants[:3]:  # 最多尝试3个变体
                try:
                    evidence = await asyncio.wait_for(
                        self.gather_evidence(
                            variant, context, {'type': 'evidence_gathering'}
                        ),
                        timeout=30.0
                    )
                except asyncio.TimeoutError:
                    self.logger.warning(f"⚠️ [增强检索] 策略3检索超时（30秒），跳过变体: {variant[:50]}...")
                    evidence = None
                    continue
                if evidence and len(evidence) > 0:
                    if answer_extractor:
                        answer = answer_extractor.extract_step_result(
                            evidence, step, previous_step_answer, original_query, variant
                        )
                        if answer:
                            return answer
            
            return None
            
        except Exception as e:
            self.logger.debug(f"增强检索失败: {e}")
            return None
    
    def generate_query_variants(self, sub_query: str, previous_answer: Optional[str], original_query: str) -> List[str]:
        """生成查询变体
        
        从 engine.py 迁移的方法，用于生成查询变体。
        内部调用 `_generate_query_variants_for_retrieval` 以获得更好的变体生成。
        
        Args:
            sub_query: 原始子查询
            previous_answer: 上一步答案
            original_query: 原始查询
            
        Returns:
            查询变体列表
        """
        try:
            # 如果 previous_answer 存在，构建 previous_steps_context
            previous_steps_context = []
            if previous_answer:
                previous_steps_context.append({'answer': previous_answer})
            
            # 使用更完善的查询变体生成方法
            variants = self._generate_query_variants_for_retrieval(
                sub_query, previous_steps_context, original_query
            )
            
            # 如果变体生成失败或返回空，使用简单的fallback策略
            if not variants:
                variants = [sub_query]  # 保留原始查询
                
                # 如果包含占位符，替换为实际值
                if previous_answer:
                    variants.append(sub_query.replace('[result from step 1]', previous_answer))
                    variants.append(sub_query.replace('[result from step 2]', previous_answer))
                    variants.append(sub_query.replace('[step 1 result]', previous_answer))
                    variants.append(sub_query.replace('[step 2 result]', previous_answer))
                
                # 简化查询（提取关键词）
                import re
                keywords = re.findall(r'\b(?:who|what|when|where|which|name|first|last|mother|father|president|first lady)\b', sub_query, re.IGNORECASE)
                if keywords and previous_answer:
                    # 构建简化查询
                    simplified = f"{previous_answer} {' '.join(keywords[:3])}"
                    variants.append(simplified)
            
            # 去重
            return list(dict.fromkeys(variants))
            
        except Exception as e:
            self.logger.debug(f"生成查询变体失败: {e}")
            # Fallback: 返回原始查询
            return [sub_query] if sub_query else []
