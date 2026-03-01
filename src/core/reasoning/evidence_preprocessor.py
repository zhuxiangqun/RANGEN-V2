#!/usr/bin/env python3
"""
证据预处理器 - 按照最佳实践清洗、过滤和格式化检索到的证据
"""
import re
import html
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# 🚀 新增：导入证据验证器
try:
    from src.core.reasoning.evidence_validator import EvidenceValidator, MarkedEvidence
    EVIDENCE_VALIDATOR_AVAILABLE = True
except ImportError:
    EVIDENCE_VALIDATOR_AVAILABLE = False
    logger.warning("证据验证器不可用，将跳过验证功能")


@dataclass
class ProcessedEvidence:
    """处理后的证据"""
    content: str
    source: Optional[str] = None
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EvidencePreprocessor:
    """证据预处理器 - 实现完整的预处理流程"""
    
    def __init__(self, max_tokens: int = 4000, relevance_threshold: float = 0.1):
        """
        初始化证据预处理器
        
        Args:
            max_tokens: 最大token数（用于上下文窗口优化）
            relevance_threshold: 相关性阈值（低于此值的证据将被过滤）
        """
        self.logger = logging.getLogger(__name__)
        self.max_tokens = max_tokens
        self.relevance_threshold = relevance_threshold
        
        # 🚀 新增：初始化证据验证器
        if EVIDENCE_VALIDATOR_AVAILABLE:
            self.evidence_validator = EvidenceValidator()
        else:
            self.evidence_validator = None
        
        # 噪音模式（需要移除的内容）
        self.noise_patterns = [
            r'Retrieved\s+\w+\s+\d+,\s+\d+',  # "Retrieved March 11, 2021"
            r'via\s+National\s+Archives',  # "via National Archives"
            r'External\s+links',  # "External links"
            r'v\s+t\s+e\s+',  # "v t e" (维基百科模板标记)
            r'\[edit\]',  # "[edit]"
            r'\[citation needed\]',  # "[citation needed]"
            r'&[a-z]+;',  # HTML实体（如 &amp;）
            r'<[^>]+>',  # HTML标签
            r'http[s]?://[^\s]+',  # URL
            r'www\.[^\s]+',  # www链接
        ]
        
        # 低质量内容指示词
        self.low_quality_indicators = [
            'navigation menu',
            'edit section',
            'jump to',
            'main article',
            'see also',
            'references',
            'external links',
            'categories',
        ]
    
    def clean_retrieved_chunks(self, chunks: List[Any], query: Optional[str] = None) -> List[ProcessedEvidence]:
        """
        清洗检索结果
        
        实现：
        1. 去重（基于语义或指纹）
        2. 质量过滤（移除低质量片段）
        3. 🚀 方案1新增：针对序数查询的特殊过滤（过滤定义性内容、不完整片段、序号不匹配等）
        4. 标准化（统一格式、编码、换行符）
        
        Args:
            chunks: 原始证据块列表
            query: 查询文本（可选，用于针对序数查询进行特殊过滤）
            
        Returns:
            清洗后的证据列表
        """
        cleaned = []
        seen_content = set()
        
        for chunk in chunks:
            # 提取内容
            content = self._extract_content(chunk)
            if not content:
                continue
            
            # 去重：基于内容指纹
            content_fingerprint = self._generate_fingerprint(content)
            if content_fingerprint in seen_content:
                self.logger.debug(f"跳过重复证据: {content[:50]}...")
                continue
            seen_content.add(content_fingerprint)
            
            # 质量过滤
            if not self._meets_quality_threshold(content):
                self.logger.debug(f"跳过低质量证据: {content[:50]}...")
                continue
            
            # 🚀 方案1：针对序数查询的特殊过滤
            if query and self._filter_irrelevant_for_ordinal_query(content, query):
                self.logger.debug(f"过滤序数查询不相关证据: {content[:100]}...")
                print(f"⚠️ [证据过滤] 过滤不相关证据（序数查询）: {content[:100]}...")
                continue
            
            # 标准化
            normalized = self._normalize_text(content)
            
            # 提取元数据
            source = self._extract_source(chunk)
            relevance_score = self._extract_relevance_score(chunk)
            
            processed = ProcessedEvidence(
                content=normalized,
                source=source,
                relevance_score=relevance_score,
                metadata=self._extract_metadata(chunk)
            )
            cleaned.append(processed)
        
        return cleaned
    
    def format_for_prompt(
        self,
        evidence_list: List[ProcessedEvidence],
        query: str,
        format_type: str = "structured"
    ) -> str:
        """
        格式化证据用于提示词
        
        策略：
        1. 清晰分段标记
        2. 添加元数据（来源、置信度）
        3. 结构化组织
        4. 🚀 新增：验证证据并添加标记
        5. 🚀 新增：检查证据是否直接回答了问题
        
        Args:
            evidence_list: 处理后的证据列表
            query: 查询文本
            format_type: 格式类型（"structured", "qa", "summary"）
            
        Returns:
            格式化后的证据文本（包含质量评估报告）
        """
        if not evidence_list:
            return ""
        
        # 🚀 新增：检查证据是否直接回答了问题
        answer_relevance = self.check_answer_relevance(evidence_list, query)
        
        # 🚀 新增：验证证据并添加标记
        validation_info = None
        if self.evidence_validator:
            try:
                # 验证证据
                validation_result = self.evidence_validator.validate_retrieved_content(
                    evidence_list, query
                )
                
                # 添加标记
                marked_evidence = self.evidence_validator.add_contextual_marks(
                    evidence_list, validation_result, query
                )
                
                # 将标记后的证据转换为ProcessedEvidence（保持兼容性）
                for i, marked in enumerate(marked_evidence):
                    if i < len(evidence_list):
                        evidence_list[i].metadata = evidence_list[i].metadata or {}
                        evidence_list[i].metadata.update({
                            'validation_confidence': marked.metadata.get('validation_confidence', 0.5),
                            'uncertainty_level': marked.metadata.get('uncertainty_level', 'Medium Confidence'),
                            'has_contradictions': marked.metadata.get('has_contradictions', False),
                            'sequence_note': marked.sequence_note,
                            'warning': marked.warning
                        })
                
                validation_info = {
                    'result': validation_result,
                    'marked_evidence': marked_evidence,
                    'answer_relevance': answer_relevance  # 🚀 新增：包含答案相关性检查结果
                }
            except Exception as e:
                self.logger.debug(f"证据验证失败: {e}，继续使用未验证的证据")
                validation_info = {
                    'answer_relevance': answer_relevance  # 即使验证失败，也包含答案相关性检查结果
                }
        else:
            # 即使没有验证器，也包含答案相关性检查结果
            validation_info = {
                'answer_relevance': answer_relevance
            }
        
        # 根据格式类型选择格式化策略
        if format_type == "qa":
            return self._format_as_qa(evidence_list, query, validation_info)
        elif format_type == "summary":
            return self._format_as_summary(evidence_list, query, validation_info)
        else:  # structured (默认)
            return self._format_as_structured(evidence_list, query, validation_info)
    
    def compress_for_context(
        self,
        evidence_list: List[ProcessedEvidence],
        max_tokens: Optional[int] = None
    ) -> List[ProcessedEvidence]:
        """
        压缩证据以适应上下文窗口
        
        策略：
        1. 提取关键句（基于位置、关键词等）
        2. 按相关性排序
        3. 动态选择Top-K
        
        Args:
            evidence_list: 证据列表
            max_tokens: 最大token数（默认使用初始化时的值）
            
        Returns:
            压缩后的证据列表
        """
        max_tokens = max_tokens or self.max_tokens
        
        # 按相关性排序
        sorted_evidence = sorted(
            evidence_list,
            key=lambda x: x.relevance_score,
            reverse=True
        )
        
        compressed = []
        used_tokens = 0
        
        for evidence in sorted_evidence:
            # 提取关键句
            key_sentences = self._extract_key_sentences(evidence.content, query=None)
            compressed_content = " ".join(key_sentences)
            
            # 估算token数（简单估算：1 token ≈ 4字符）
            estimated_tokens = len(compressed_content) // 4
            
            if used_tokens + estimated_tokens < max_tokens:
                evidence.content = compressed_content
                compressed.append(evidence)
                used_tokens += estimated_tokens
            else:
                # 如果还有空间，尝试截断当前证据
                remaining_tokens = max_tokens - used_tokens
                if remaining_tokens > 50:  # 至少保留50 tokens
                    truncated = compressed_content[:remaining_tokens * 4]
                    evidence.content = truncated + "..."
                    compressed.append(evidence)
                break
        
        return compressed
    
    def _extract_content(self, chunk: Any) -> str:
        """从证据块中提取内容"""
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            return chunk.get('content', '') or chunk.get('text', '') or chunk.get('data', '') or str(chunk)
        elif hasattr(chunk, 'content'):
            return chunk.content
        else:
            return str(chunk)
    
    def _generate_fingerprint(self, content: str) -> str:
        """生成内容指纹用于去重"""
        # 简单实现：使用前100个字符的hash
        normalized = re.sub(r'\s+', ' ', content.strip().lower())
        return normalized[:100]
    
    def check_answer_relevance(self, evidence_list: List[ProcessedEvidence], query: str) -> Dict[str, Any]:
        """
        🚀 新增：检查证据是否直接回答了查询问题
        
        检查策略：
        1. 对于序数查询（如"15th first lady"），检查是否包含序号对应信息
        2. 对于关系查询（如"mother of X"），检查是否包含关系描述
        3. 对于实体查询（如"who is X"），检查是否包含实体信息
        
        Args:
            evidence_list: 证据列表
            query: 查询文本
            
        Returns:
            验证结果字典：
            {
                'has_direct_answer': bool,  # 是否包含直接答案
                'answer_type': str,  # 答案类型（'ordinal', 'relationship', 'entity', 'none'）
                'issues': List[str],  # 发现的问题
                'suggestions': List[str]  # 改进建议
            }
        """
        try:
            result = {
                'has_direct_answer': False,
                'answer_type': 'none',
                'issues': [],
                'suggestions': []
            }
            
            if not evidence_list or not query:
                result['issues'].append('证据列表或查询为空')
                return result
            
            query_lower = query.lower()
            all_evidence_text = ' '.join([ev.content.lower() for ev in evidence_list])
            
            # 检查是否是序数查询
            ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', query_lower)
            if ordinal_match:
                ordinal_num = ordinal_match.group(1)
                result['answer_type'] = 'ordinal'
                
                # 检查是否包含序号对应信息
                # 模式1: 明确的序号+实体对应（如"15th first lady is Sarah Polk"）
                ordinal_patterns = [
                    rf'{ordinal_num}(?:st|nd|rd|th)\s+(?:first\s+lady|president|etc\.)',
                    rf'(?:first\s+lady|president)\s+number\s+{ordinal_num}',
                    rf'#{ordinal_num}',
                ]
                
                has_ordinal_reference = any(re.search(pattern, all_evidence_text, re.IGNORECASE) for pattern in ordinal_patterns)
                
                # 模式2: 检查是否包含列表格式（可能包含序号信息）
                has_list_format = bool(re.search(r'\d+[\.\)]\s+[A-Z][a-z]+', all_evidence_text))
                
                if has_ordinal_reference or has_list_format:
                    result['has_direct_answer'] = True
                else:
                    result['issues'].append(f'No clear correspondence found for the {ordinal_num}th position in the evidence')
                    result['suggestions'].append(f'Need to retrieve knowledge entries containing "the {ordinal_num}th" or a complete list')
            
            # 检查是否是关系查询
            elif any(rel_word in query_lower for rel_word in ['mother', 'father', 'wife', 'husband', 'daughter', 'son', 'parent', 'child']):
                result['answer_type'] = 'relationship'
                
                # 检查是否包含关系描述
                relationship_patterns = [
                    r"(?:mother|father|wife|husband|daughter|son|parent|child)\s+(?:of|was|is)\s+[A-Z][a-z]+",
                    r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*['']s\s+(?:mother|father|wife|husband|daughter|son)",
                ]
                
                has_relationship = any(re.search(pattern, all_evidence_text, re.IGNORECASE) for pattern in relationship_patterns)
                
                if has_relationship:
                    result['has_direct_answer'] = True
                else:
                    result['issues'].append('No clear relationship description found in the evidence')
                    result['suggestions'].append('Need to retrieve knowledge entries containing specific relationship information')
            
            # 检查是否是实体查询
            elif any(q_word in query_lower for q_word in ['who is', 'what is', 'who was', 'what was']):
                result['answer_type'] = 'entity'
                
                # 检查是否包含实体信息（人名、地名等）
                entity_patterns = [
                    r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+',  # 人名格式
                    r'(?:born|died|was|is)\s+[A-Z][a-z]+',  # 实体描述
                ]
                
                has_entity = any(re.search(pattern, all_evidence_text) for pattern in entity_patterns)
                
                if has_entity:
                    result['has_direct_answer'] = True
                else:
                    result['issues'].append('No clear entity information found in the evidence')
                    result['suggestions'].append('Need to retrieve knowledge entries containing specific entity information')
            
            # 如果所有证据都不相关，添加通用建议
            if not result['has_direct_answer']:
                result['suggestions'].append('Suggest re-retrieving or using a more specific query')
            
            return result
            
        except Exception as e:
            self.logger.debug(f"检查答案相关性失败: {e}")
            return {
                'has_direct_answer': False,
                'answer_type': 'none',
                'issues': [f'检查过程出错: {str(e)}'],
                'suggestions': []
            }
    
    def _meets_quality_threshold(self, content: str) -> bool:
        """检查内容是否满足质量阈值"""
        if not content or len(content.strip()) < 5:
            return False
        
        content_lower = content.lower()
        
        # 检查是否包含低质量指示词
        for indicator in self.low_quality_indicators:
            if indicator in content_lower:
                return False
        
        # 检查是否主要是噪音
        noise_ratio = sum(
            len(re.findall(pattern, content, re.IGNORECASE))
            for pattern in self.noise_patterns
        ) / max(len(content.split()), 1)
        
        if noise_ratio > 0.3:  # 如果噪音比例超过30%，认为是低质量
            return False
        
        return True
    
    def _filter_irrelevant_for_ordinal_query(self, content: str, query: str) -> bool:
        """
        🚀 方案1：针对序数查询的特殊过滤
        
        对于序数查询（如"15th first lady"），过滤不相关的证据：
        1. 定义性内容（只解释概念，不包含具体列表）
        2. 不完整的片段（如只有日期、片段信息）
        3. 序号不匹配的内容（如查询"15th"但证据中只有"1st"）
        4. 没有列表格式的内容（对于序数查询，应该优先包含列表）
        
        Args:
            content: 证据内容
            query: 查询文本
            
        Returns:
            True: 应该过滤掉（不相关）
            False: 保留（相关）
        """
        try:
            # 检查是否是序数查询
            ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', query, re.IGNORECASE)
            if not ordinal_match:
                return False  # 不是序数查询，不过滤
            
            ordinal_num = int(ordinal_match.group(1))
            content_lower = content.lower()
            
            # 1. 过滤定义性内容（只解释概念，不包含具体列表）
            definition_patterns = [
                r'is\s+(?:traditionally|typically|usually|generally)\s+(?:filled|applied|used)',
                r'is\s+not\s+an\s+(?:elected|official)',
                r'carries\s+no\s+(?:official|duties)',
                r'receives\s+no\s+salary',
                r'position\s+is\s+traditionally',
            ]
            if any(re.search(pattern, content_lower) for pattern in definition_patterns):
                # 但如果同时包含列表格式，保留
                if not re.search(r'\d+[\.\)]\s+[A-Z][a-z]+', content):
                    self.logger.debug(f"过滤定义性内容: {content[:100]}...")
                    return True
            
            # 2. 过滤不完整的片段（如只有日期、片段信息）
            # 检查是否主要是日期、片段信息，没有完整的实体名称
            if len(content.strip()) < 50:  # 太短的内容
                # 检查是否主要是日期、地点等片段信息
                fragment_patterns = [
                    r'^(?:died|born|aged|spouse|children|signature)',
                    r'^\d{4}-\d{2}-\d{2}',  # 日期格式
                    r'^[A-Z][a-z]+\s+\d+,\s+\d{4}',  # "December 28, 1961"
                ]
                if any(re.match(pattern, content.strip(), re.IGNORECASE) for pattern in fragment_patterns):
                    # 但如果包含完整的人名和上下文，保留
                    if not re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*', content):
                        self.logger.debug(f"过滤不完整片段: {content[:100]}...")
                        return True
            
            # 3. 检查序号不匹配（如果证据中明确提到其他序号，且与查询序号差距较大）
            # 提取证据中提到的所有序号
            evidence_ordinals = re.findall(r'(\d+)(?:st|nd|rd|th)', content, re.IGNORECASE)
            if evidence_ordinals:
                evidence_ordinal_nums = [int(n) for n in evidence_ordinals]
                # 如果证据中提到的序号与查询序号差距较大（超过5），且没有列表格式，可能不相关
                min_diff = min(abs(int(n) - ordinal_num) for n in evidence_ordinal_nums)
                if min_diff > 5:
                    # 但如果包含列表格式，保留（可能包含完整列表）
                    if not re.search(r'\d+[\.\)]\s+[A-Z][a-z]+', content):
                        self.logger.debug(f"过滤序号不匹配内容: {content[:100]}...")
                        return True
            
            # 4. 对于序数查询，优先保留包含列表格式的内容
            # 如果内容不包含列表格式，且长度较短，可能是片段，过滤
            has_list_format = bool(re.search(r'\d+[\.\)]\s+[A-Z][a-z]+', content))
            if not has_list_format and len(content.strip()) < 100:
                # 检查是否包含查询相关的实体类型（如"first lady"）
                entity_type_match = re.search(r'first\s+lady|president|etc\.', query, re.IGNORECASE)
                if entity_type_match:
                    entity_type = entity_type_match.group(0)
                    if entity_type.lower() not in content_lower:
                        # 不包含实体类型，且没有列表格式，过滤
                        self.logger.debug(f"过滤不包含实体类型且无列表格式的内容: {content[:100]}...")
                        return True
            
            # 默认保留
            return False
            
        except Exception as e:
            self.logger.debug(f"序数查询过滤检查失败: {e}，保留证据")
            return False  # 出错时保留证据
    
    def _normalize_text(self, text: str) -> str:
        """标准化文本"""
        # 移除HTML标签和实体
        text = html.unescape(text)
        
        # 移除噪音模式
        for pattern in self.noise_patterns:
            text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
        
        # 标准化空白字符
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)  # 最多保留两个换行
        
        # 移除首尾空白
        text = text.strip()
        
        return text
    
    def _extract_source(self, chunk: Any) -> Optional[str]:
        """提取来源信息"""
        if isinstance(chunk, dict):
            return chunk.get('source') or chunk.get('url') or chunk.get('title')
        elif hasattr(chunk, 'source'):
            return chunk.source
        return None
    
    def _extract_relevance_score(self, chunk: Any) -> float:
        """提取相关性分数"""
        if isinstance(chunk, dict):
            return chunk.get('similarity', 0.0) or chunk.get('score', 0.0) or chunk.get('confidence', 0.0)
        elif hasattr(chunk, 'similarity'):
            return chunk.similarity
        elif hasattr(chunk, 'confidence'):
            return chunk.confidence
        return 0.0
    
    def _extract_metadata(self, chunk: Any) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}
        
        if isinstance(chunk, dict):
            metadata = {k: v for k, v in chunk.items() 
                       if k not in ['content', 'text', 'data', 'source', 'similarity', 'score', 'confidence']}
        elif hasattr(chunk, '__dict__'):
            metadata = {k: v for k, v in chunk.__dict__.items() 
                       if k not in ['content', 'source', 'similarity', 'confidence']}
        
        return metadata
    
    def _extract_key_sentences(self, content: str, query: Optional[str] = None) -> List[str]:
        """提取关键句子"""
        # 简单实现：按句子分割，优先选择包含查询关键词的句子
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not query:
            # 如果没有查询，返回前3个句子
            return sentences[:3]
        
        # 如果有查询，优先选择包含查询关键词的句子
        query_keywords = set(query.lower().split())
        scored_sentences = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            score = sum(1 for keyword in query_keywords if keyword in sentence_lower)
            if score > 0:
                scored_sentences.append((score, sentence))
        
        # 按分数排序
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        # 返回前5个最相关的句子
        key_sentences = [s for _, s in scored_sentences[:5]]
        
        # 如果相关句子不足，补充前面的句子
        if len(key_sentences) < 3:
            key_sentences.extend(sentences[:3 - len(key_sentences)])
        
        return key_sentences
    
    def _format_as_structured(
        self,
        evidence_list: List[ProcessedEvidence],
        query: str = "",
        validation_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """格式化为结构化格式（🚀 增强：添加验证信息和答案相关性检查）"""
        formatted_parts = []
        
        # 🚀 新增：添加答案相关性检查结果（优先级最高）
        answer_relevance = None
        if validation_info and 'answer_relevance' in validation_info:
            answer_relevance = validation_info['answer_relevance']
        
        if answer_relevance and not answer_relevance.get('has_direct_answer', False):
            # 🚀 修复：即使证据不直接回答问题，也要显示完整的证据内容
            # 添加警告信息，但不影响证据内容的显示
            formatted_parts.append("=" * 70)
            formatted_parts.append("⚠️ Note: Retrieved content may not fully match the question")
            formatted_parts.append("=" * 70)
            if answer_relevance.get('issues'):
                formatted_parts.append("")
                formatted_parts.append("Issues Found:")
                for issue in answer_relevance.get('issues', []):
                    formatted_parts.append(f"- {issue}")
            formatted_parts.append("")
            formatted_parts.append("=" * 70)
            formatted_parts.append("")
            # 🚀 修复：不再显示摘要，直接显示完整证据内容（在下面的循环中）
        
        # 🚀 新增：添加验证信息头部（如果答案相关性检查通过）
        if validation_info and 'result' in validation_info:
            validation_result = validation_info['result']
            # 🚀 修复：使用英文判断
            high_confidence_values = ['High Confidence', 'high confidence']
            is_high_confidence = validation_result.uncertainty_level.value in high_confidence_values if hasattr(validation_result.uncertainty_level, 'value') else False
            
            if validation_result.issues or not is_high_confidence:
                formatted_parts.append("=" * 70)
                formatted_parts.append("⚠️ Evidence Quality Assessment")
                formatted_parts.append("=" * 70)
                
                if validation_result.issues:
                    formatted_parts.append(f"Issues Detected: {', '.join(validation_result.issues)}")
                
                formatted_parts.append(f"Confidence: {validation_result.confidence:.2f}")
                # 🚀 修复：将不确定性级别转换为英文
                uncertainty_level_str = validation_result.uncertainty_level.value if hasattr(validation_result.uncertainty_level, 'value') else str(validation_result.uncertainty_level)
                # 映射中文到英文
                uncertainty_mapping = {
                    '高置信度': 'High Confidence',
                    '中等置信度': 'Medium Confidence',
                    '低置信度': 'Low Confidence',
                    'High Confidence': 'High Confidence',
                    'Medium Confidence': 'Medium Confidence',
                    'Low Confidence': 'Low Confidence'
                }
                uncertainty_level_en = uncertainty_mapping.get(uncertainty_level_str, uncertainty_level_str)
                formatted_parts.append(f"Uncertainty Level: {uncertainty_level_en}")
                
                if validation_result.contradictions:
                    formatted_parts.append(f"Found {len(validation_result.contradictions)} contradiction(s)")
                
                formatted_parts.append("=" * 70)
                formatted_parts.append("")
        
        for i, evidence in enumerate(evidence_list[:5], 1):  # 最多5条证据
            part = f"---\n[Evidence {i}]"
            
            if evidence.source:
                part += f"\nSource: {evidence.source}"
            
            if evidence.relevance_score > 0:
                part += f"\nRelevance: {evidence.relevance_score:.2f}"
            
            # 🚀 新增：添加验证标记
            if evidence.metadata:
                if evidence.metadata.get('sequence_note'):
                    part += f"\n📌 Statistical Note: {evidence.metadata['sequence_note']}"
                if evidence.metadata.get('warning'):
                    part += f"\n⚠️ Warning: {evidence.metadata['warning']}"
                if evidence.metadata.get('uncertainty_level'):
                    uncertainty_level_str = evidence.metadata.get('uncertainty_level', '')
                    # 映射中文到英文
                    uncertainty_mapping = {
                        '高置信度': 'High Confidence',
                        '中等置信度': 'Medium Confidence',
                        '低置信度': 'Low Confidence',
                        'High Confidence': 'High Confidence',
                        'Medium Confidence': 'Medium Confidence',
                        'Low Confidence': 'Low Confidence'
                    }
                    uncertainty_level_en = uncertainty_mapping.get(uncertainty_level_str, uncertainty_level_str)
                    part += f"\nConfidence Level: {uncertainty_level_en}"
            
            part += f"\nContent:\n{evidence.content}\n---"
            formatted_parts.append(part)
        
        return "\n\n".join(formatted_parts)
    
    def _format_as_qa(
        self,
        evidence_list: List[ProcessedEvidence],
        query: str,
        validation_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """格式化为问答对格式（🚀 增强：添加验证信息）"""
        formatted_parts = []
        
        # 🚀 新增：添加验证信息
        if validation_info:
            validation_result = validation_info['result']
            if validation_result.issues:
                formatted_parts.append(f"⚠️ Note: {', '.join(validation_result.issues)}")
                formatted_parts.append("")
        
        for i, evidence in enumerate(evidence_list[:3], 1):
            part = f"Q{i}: {query}\nA{i}: {evidence.content}"
            if evidence.source:
                part += f" [Source: {evidence.source}]"
            if evidence.metadata and evidence.metadata.get('sequence_note'):
                part += f" [Note: {evidence.metadata['sequence_note']}]"
            formatted_parts.append(part)
        
        return "\n\n".join(formatted_parts)
    
    def _format_as_summary(
        self,
        evidence_list: List[ProcessedEvidence],
        query: str,
        validation_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """格式化为摘要+细节层次化格式（🚀 增强：添加验证信息）"""
        # 🚀 新增：添加验证信息
        validation_header = ""
        if validation_info:
            validation_result = validation_info['result']
            # Check if uncertainty level is not HIGH (using English value)
            is_high_confidence = validation_result.uncertainty_level.value == "High Confidence"
            if validation_result.issues or not is_high_confidence:
                validation_header = f"⚠️ Evidence Quality Assessment: {validation_result.uncertainty_level.value}\n"
                if validation_result.issues:
                    validation_header += f"Issues Detected: {', '.join(validation_result.issues)}\n"
                validation_header += "\n"
        
        # 核心要点摘要
        summary_parts = []
        for i, evidence in enumerate(evidence_list[:3], 1):
            summary_parts.append(f"{i}. {evidence.content[:100]}... [Source: {evidence.source or 'Unknown'}]")
        
        summary = validation_header + "Key Points Summary:\n" + "\n".join(summary_parts)
        
        # 详细信息
        details = "\n\nDetailed Information:\n"
        for i, evidence in enumerate(evidence_list[:3], 1):
            details += f"\n[Evidence {i}]\n"
            if evidence.metadata and evidence.metadata.get('sequence_note'):
                details += f"📌 Statistical Note: {evidence.metadata['sequence_note']}\n"
            details += f"{evidence.content}\n"
        
        return summary + details
    
    def format_list_evidence(self, evidence_text: str, query: str) -> str:
        """
        通用列表格式化方法 - 检测并格式化证据中的列表
        
        策略：
        1. 检测证据是否包含列表格式（编号列表、项目符号、连续人名等）
        2. 提取列表项并按顺序编号
        3. 格式化为清晰的编号列表
        
        Args:
            evidence_text: 原始证据文本
            query: 查询文本（用于判断是否需要列表格式化）
            
        Returns:
            格式化后的证据文本（如果是列表格式），否则返回原始文本
        """
        try:
            if not evidence_text or len(evidence_text.strip()) < 20:
                return evidence_text
            
            # 检测是否是序数查询（需要从列表中提取第N个）
            ordinal_patterns = [
                r'\b(\d+)(?:st|nd|rd|th)\b',  # 15th, 1st, 2nd, etc.
                r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth)\b',
            ]
            is_ordinal_query = any(re.search(pattern, query, re.IGNORECASE) for pattern in ordinal_patterns)
            
            if not is_ordinal_query:
                # 如果不是序数查询，不需要列表格式化
                return evidence_text
            
            # 检测列表格式模式
            list_patterns = [
                # 编号列表：数字后跟点或括号
                r'^\s*\d+[\.\)]\s+([^\n]+)',
                # 项目符号列表
                r'^\s*[-*•]\s+([^\n]+)',
                # 连续的人名格式（每行一个人名，首字母大写）
                r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*$',
            ]
            
            lines = evidence_text.split('\n')
            list_items = []
            list_start_pos = -1
            
            # 查找列表开始位置（查找常见的列表标记）
            list_markers = [
                'first', 'second', 'third', 'list', 'names', 'items',
                'martha', 'abigail', 'dolley', 'elizabeth', 'louisa'  # 常见人名开头（通用模式）
            ]
            
            for i, line in enumerate(lines):
                line_lower = line.lower().strip()
                # 检查是否包含列表标记
                if any(marker in line_lower for marker in list_markers):
                    # 检查后续行是否匹配列表模式
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        for pattern in list_patterns:
                            if re.match(pattern, next_line, re.IGNORECASE):
                                list_start_pos = i
                                break
                    if list_start_pos != -1:
                        break
            
            # 如果找不到明确的列表开始位置，尝试从文本开头查找
            if list_start_pos == -1:
                list_start_pos = 0
            
            # 提取列表项（从列表开始位置到文本末尾，但限制长度）
            list_text = '\n'.join(lines[list_start_pos:list_start_pos + 100])
            
            # 尝试提取列表项
            for pattern in list_patterns:
                matches = re.finditer(pattern, list_text, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    if len(match.groups()) > 0:
                        item = match.group(1).strip() if match.group(1) else match.group(0).strip()
                    else:
                        item = match.group(0).strip()
                    
                    # 清理项目符号和多余空格
                    item = re.sub(r'^[•\-\*]\s+', '', item)
                    item = re.sub(r'^\d+[\.\)]\s+', '', item)
                    item = item.strip()
                    
                    # 过滤掉明显不是列表项的内容
                    if item and len(item) > 2 and len(item) < 100:
                        # 排除明显的非列表项（如URL、日期、引用等）
                        if not re.search(r'http|www|\.com|\.org|retrieved|via|external links', item, re.IGNORECASE):
                            if item not in list_items:  # 去重
                                list_items.append(item)
                
                if len(list_items) >= 5:  # 如果找到足够多的列表项，停止
                    break
            
            # 如果找到了足够多的列表项（至少5个），格式化为编号列表
            if len(list_items) >= 5:
                formatted_list = []
                for i, item in enumerate(list_items[:50], 1):  # 最多50项
                    formatted_list.append(f"{i}. {item}")
                
                formatted_text = "\n".join(formatted_list)
                self.logger.debug(f"✅ [通用列表格式化] 成功格式化列表，找到{len(list_items)}个列表项")
                return formatted_text
            
            # 如果列表项不足，返回原始文本
            return evidence_text
            
        except Exception as e:
            self.logger.debug(f"通用列表格式化失败: {e}，返回原始文本")
            return evidence_text
