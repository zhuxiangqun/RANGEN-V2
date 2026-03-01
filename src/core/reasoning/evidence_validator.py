#!/usr/bin/env python3
"""
通用证据验证器 - 处理证据中的序号与历史事实不符等问题
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class UncertaintyLevel(Enum):
    """不确定性级别"""
    HIGH = "High Confidence"
    MEDIUM = "Medium Confidence, further verification suggested"
    LOW = "Low Confidence, information may be contradictory or incomplete"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    issues: List[str]
    confidence: float
    needs_clarification: bool
    uncertainty_level: UncertaintyLevel
    contradictions: List[Dict[str, Any]]
    completeness_score: float
    source_quality: Dict[str, Any]


@dataclass
class MarkedEvidence:
    """标记后的证据"""
    content: str
    source: Optional[str]
    position: int
    confidence: float
    sequence_note: Optional[str] = None
    warning: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class EvidenceValidator:
    """通用证据验证器 - 实现完整的验证流程"""
    
    def __init__(self):
        """初始化证据验证器"""
        self.logger = logging.getLogger(__name__)
        
        # 序列查询模式（用于检测序数查询）
        self.ordinal_patterns = [
            r'\b(\d+)(?:st|nd|rd|th)\b',  # 15th, 1st, 2nd, etc.
            r'\b(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|eleventh|twelfth|thirteenth|fourteenth|fifteenth|sixteenth|seventeenth|eighteenth|nineteenth|twentieth)\b',
        ]
        
        # 历史事实相关的关键词（用于检测可能的统计标准差异）
        self.historical_fact_keywords = [
            'first lady', 'president', 'assassinated', 'inauguration',
            'term', 'served', 'elected', 'appointed'
        ]
    
    def validate_retrieved_content(
        self,
        chunks: List[Any],
        query: str,
        query_type: Optional[str] = None
    ) -> ValidationResult:
        """
        通用验证：检查检索内容的可靠性
        
        Args:
            chunks: 原始证据块列表
            query: 查询文本
            query_type: 查询类型（可选）
            
        Returns:
            验证结果
        """
        issues = []
        contradictions = []
        confidence_scores = []
        source_quality = {}
        
        # A. 内部一致性检查
        if len(chunks) > 1:
            consistency_result = self._check_consistency(chunks, query)
            if not consistency_result['is_consistent']:
                issues.append("Internal contradictions found in retrieved content")
                contradictions.extend(consistency_result['contradictions'])
        
        # B. 完整性检查
        if self._is_sequential_query(query):
            completeness_result = self._check_completeness(chunks, query)
            if not completeness_result['is_complete']:
                issues.append("Sequence may be incomplete")
        
        # C. 置信度评估
        for chunk in chunks:
            confidence = self._assess_confidence(chunk, query)
            confidence_scores.append(confidence)
        
        # D. 来源质量检查
        source_quality = self._check_source_reliability(chunks)
        
        # 计算总体置信度
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # 确定不确定性级别
        if avg_confidence >= 0.8 and len(issues) == 0:
            uncertainty_level = UncertaintyLevel.HIGH
        elif avg_confidence >= 0.5 and len(issues) <= 1:
            uncertainty_level = UncertaintyLevel.MEDIUM
        else:
            uncertainty_level = UncertaintyLevel.LOW
        
        # 计算完整性分数
        completeness_score = completeness_result.get('score', 0.8) if self._is_sequential_query(query) else 1.0
        
        return ValidationResult(
            is_valid=len(issues) == 0,
            issues=issues,
            confidence=avg_confidence,
            needs_clarification=len(issues) > 0 or uncertainty_level != UncertaintyLevel.HIGH,
            uncertainty_level=uncertainty_level,
            contradictions=contradictions,
            completeness_score=completeness_score,
            source_quality=source_quality
        )
    
    def add_contextual_marks(
        self,
        chunks: List[Any],
        validation_result: ValidationResult,
        query: str
    ) -> List[MarkedEvidence]:
        """
        为检索内容添加通用标记
        
        Args:
            chunks: 原始证据块列表
            validation_result: 验证结果
            query: 查询文本
            
        Returns:
            标记后的证据列表
        """
        marked_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 提取内容
            content = self._extract_content(chunk)
            source = self._extract_source(chunk)
            relevance_score = self._extract_relevance_score(chunk)
            
            # 基础标记
            mark = MarkedEvidence(
                content=content,
                source=source,
                position=i + 1,
                confidence=relevance_score
            )
            
            # 根据问题类型添加特定标记
            if self._is_sequential_query(query):
                # 序列查询：添加统计标准说明
                mark.sequence_note = self._generate_sequence_note(query, content)
            
            if validation_result.issues:
                mark.warning = "Please verify this information"
            
            # 添加元数据
            mark.metadata = {
                'validation_confidence': validation_result.confidence,
                'uncertainty_level': validation_result.uncertainty_level.value,
                'has_contradictions': len(validation_result.contradictions) > 0
            }
            
            marked_chunks.append(mark)
        
        return marked_chunks
    
    def _check_consistency(self, chunks: List[Any], query: str) -> Dict[str, Any]:
        """检查内部一致性"""
        contradictions = []
        
        # 提取所有证据中的关键信息
        key_infos = []
        for chunk in chunks:
            content = self._extract_content(chunk)
            if self._is_sequential_query(query):
                # 对于序列查询，提取序号和对应的实体
                sequence_info = self._extract_sequence_info(content, query)
                if sequence_info:
                    key_infos.append(sequence_info)
        
        # 检查是否有矛盾
        if len(key_infos) > 1:
            # 比较不同证据中的序号对应关系
            for i in range(len(key_infos) - 1):
                for j in range(i + 1, len(key_infos)):
                    if self._has_contradiction(key_infos[i], key_infos[j]):
                        contradictions.append({
                            'evidence_1': i,
                            'evidence_2': j,
                            'type': 'sequence_mismatch',
                            'description': 'Sequence number and entity correspondence mismatch'
                        })
        
        return {
            'is_consistent': len(contradictions) == 0,
            'contradictions': contradictions
        }
    
    def _check_completeness(self, chunks: List[Any], query: str) -> Dict[str, Any]:
        """检查完整性"""
        # 提取查询中的序数
        ordinal_match = re.search(r'(\d+)(?:st|nd|rd|th)', query, re.IGNORECASE)
        if not ordinal_match:
            return {'is_complete': True, 'score': 1.0}
        
        target_ordinal = int(ordinal_match.group(1))
        
        # 检查证据中是否包含足够的序列项
        all_items = []
        for chunk in chunks:
            content = self._extract_content(chunk)
            items = self._extract_sequence_items(content)
            all_items.extend(items)
        
        # 去重
        unique_items = list(dict.fromkeys(all_items))
        
        # 如果序列项数量少于目标序数，可能不完整
        if len(unique_items) < target_ordinal:
            return {
                'is_complete': False,
                'score': len(unique_items) / max(target_ordinal, 1),
                'missing_count': target_ordinal - len(unique_items)
            }
        
        return {'is_complete': True, 'score': 1.0}
    
    def _assess_confidence(self, chunk: Any, query: str) -> float:
        """评估置信度"""
        confidence = 0.5  # 默认置信度
        
        # 提取相关性分数
        relevance_score = self._extract_relevance_score(chunk)
        if relevance_score > 0:
            confidence = relevance_score
        
        # 检查来源质量
        source = self._extract_source(chunk)
        if source:
            if 'wikipedia' in source.lower() or 'encyclopedia' in source.lower():
                confidence = min(confidence + 0.1, 1.0)
            elif 'official' in source.lower() or 'government' in source.lower():
                confidence = min(confidence + 0.15, 1.0)
        
        return confidence
    
    def _check_source_reliability(self, chunks: List[Any]) -> Dict[str, Any]:
        """检查来源可靠性"""
        sources = []
        for chunk in chunks:
            source = self._extract_source(chunk)
            if source:
                sources.append(source)
        
        # 统计来源类型
        source_types = {}
        for source in sources:
            source_lower = source.lower()
            if 'wikipedia' in source_lower:
                source_types['wikipedia'] = source_types.get('wikipedia', 0) + 1
            elif 'official' in source_lower or 'government' in source_lower:
                source_types['official'] = source_types.get('official', 0) + 1
            else:
                source_types['other'] = source_types.get('other', 0) + 1
        
        return {
            'total_sources': len(sources),
            'source_types': source_types,
            'has_authoritative_source': 'official' in source_types or 'wikipedia' in source_types
        }
    
    def _is_sequential_query(self, query: str) -> bool:
        """检查是否是序列查询（序数查询）"""
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in self.ordinal_patterns)
    
    def _generate_sequence_note(self, query: str, content: str) -> str:
        """生成序列说明"""
        # 检测是否是历史事实相关的序列查询
        is_historical = any(keyword in query.lower() for keyword in self.historical_fact_keywords)
        
        if is_historical:
            return (
                "Note: Statistical methods for historical facts may vary. "
                "This list may use a specific statistical standard (e.g., 'counting all women who held the role'), "
                "which differs from the common 'by presidential term' counting method."
            )
        
        return "Note: This is a sequence sorted by specific rules"
    
    def _extract_sequence_info(self, content: str, query: str) -> Optional[Dict[str, Any]]:
        """从内容中提取序列信息"""
        # 尝试提取编号列表
        numbered_items = re.findall(r'(\d+)\.\s*([^\n]+)', content)
        if numbered_items:
            return {
                'type': 'numbered_list',
                'items': [(int(num), item.strip()) for num, item in numbered_items]
            }
        
        return None
    
    def _extract_sequence_items(self, content: str) -> List[str]:
        """提取序列项"""
        items = []
        
        # 尝试提取编号列表
        numbered_items = re.findall(r'\d+\.\s*([^\n]+)', content)
        items.extend([item.strip() for item in numbered_items])
        
        # 尝试提取项目符号列表
        bullet_items = re.findall(r'[-*•]\s*([^\n]+)', content)
        items.extend([item.strip() for item in bullet_items])
        
        return items
    
    def _has_contradiction(self, info1: Dict[str, Any], info2: Dict[str, Any]) -> bool:
        """检查两个序列信息是否有矛盾"""
        if info1['type'] != info2['type']:
            return False
        
        if info1['type'] == 'numbered_list':
            items1 = {num: item for num, item in info1['items']}
            items2 = {num: item for num, item in info2['items']}
            
            # 检查相同序号是否对应不同实体
            common_nums = set(items1.keys()) & set(items2.keys())
            for num in common_nums:
                if items1[num].lower() != items2[num].lower():
                    return True
        
        return False
    
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

