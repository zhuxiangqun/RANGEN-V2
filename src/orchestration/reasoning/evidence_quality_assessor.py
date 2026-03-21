"""
证据质量评估器 - 评估证据的相关性、一致性、完整性和可靠性
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class EvidenceQualityAssessor:
    """证据质量评估器"""
    
    def __init__(self, llm_integration=None):
        self.logger = logging.getLogger(__name__)
        self.llm_integration = llm_integration
    
    def assess(
        self,
        evidence: str,
        query: str,
        evidence_list: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """评估证据质量
        
        Args:
            evidence: 证据文本
            query: 查询文本
            evidence_list: 证据列表（可选，用于一致性检查）
            
        Returns:
            包含质量评估结果的字典
        """
        try:
            # 基础评估（基于规则）
            relevance_score = self._assess_relevance(evidence, query)
            completeness_score = self._assess_completeness(evidence, query)
            
            # 一致性评估（如果有多个证据）
            consistency_score = 1.0
            if evidence_list and len(evidence_list) > 1:
                consistency_score = self._assess_consistency(evidence_list)
            
            # 综合评分
            overall_score = (
                relevance_score * 0.4 +
                completeness_score * 0.3 +
                consistency_score * 0.3
            )
            
            # 转换为质量等级
            quality_level = self._score_to_quality(overall_score)
            
            result = {
                "overall_score": overall_score,
                "quality_level": quality_level,
                "relevance_score": relevance_score,
                "completeness_score": completeness_score,
                "consistency_score": consistency_score,
                "recommended_action": self._get_recommended_action(overall_score)
            }
            
            self.logger.info(
                f"✅ 证据质量评估: {quality_level} "
                f"(score={overall_score:.2f}, relevance={relevance_score:.2f}, "
                f"completeness={completeness_score:.2f}, consistency={consistency_score:.2f})"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"证据质量评估失败: {e}")
            return {
                "overall_score": 0.5,
                "quality_level": "medium",
                "relevance_score": 0.5,
                "completeness_score": 0.5,
                "consistency_score": 1.0,
                "recommended_action": "use_with_caution"
            }
    
    def _assess_relevance(self, evidence: str, query: str) -> float:
        """评估相关性"""
        if not evidence or not query:
            return 0.0
        
        # 简单的关键词匹配
        query_words = set(query.lower().split())
        evidence_lower = evidence.lower()
        
        # 计算关键词覆盖率
        matched_words = sum(1 for word in query_words if word in evidence_lower)
        if len(query_words) == 0:
            return 0.5
        
        relevance = matched_words / len(query_words)
        
        # 如果相关性太低，可能是无关证据
        if relevance < 0.2:
            return 0.2
        
        return min(1.0, relevance)
    
    def _assess_completeness(self, evidence: str, query: str) -> float:
        """评估完整性"""
        if not evidence:
            return 0.0
        
        # 检查证据长度（太短可能不完整）
        if len(evidence) < 50:
            return 0.3
        elif len(evidence) < 200:
            return 0.6
        else:
            return 0.9
    
    def _assess_consistency(self, evidence_list: List[Any]) -> float:
        """评估一致性"""
        if not evidence_list or len(evidence_list) < 2:
            return 1.0
        
        # 简单的文本相似度检查
        # 这里使用简单的关键词重叠度
        evidence_texts = []
        for ev in evidence_list:
            if hasattr(ev, 'content'):
                evidence_texts.append(ev.content.lower())
            else:
                evidence_texts.append(str(ev).lower())
        
        # 计算所有证据对之间的相似度
        similarities = []
        for i in range(len(evidence_texts)):
            for j in range(i + 1, len(evidence_texts)):
                sim = self._text_similarity(evidence_texts[i], evidence_texts[j])
                similarities.append(sim)
        
        if not similarities:
            return 1.0
        
        # 返回平均相似度
        avg_similarity = sum(similarities) / len(similarities)
        return avg_similarity
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（简单的词重叠度）"""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _score_to_quality(self, score: float) -> str:
        """将评分转换为质量等级"""
        if score > 0.8:
            return "high"
        elif score > 0.5:
            return "medium"
        elif score > 0.3:
            return "low"
        else:
            return "none"
    
    def _get_recommended_action(self, score: float) -> str:
        """获取推荐操作"""
        if score > 0.7:
            return "use_as_is"
        elif score > 0.5:
            return "supplement"
        elif score > 0.3:
            return "use_with_caution"
        else:
            return "discard"

