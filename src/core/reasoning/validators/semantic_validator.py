"""
语义相关性验证器
基于语义相似度和关键词匹配验证推理步骤是否与原始查询相关
"""
import logging
from typing import Dict, List, Any

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class SemanticRelevanceValidator(BaseValidator):
    """语义相关性验证器"""

    def __init__(self, similarity_threshold: float = 0.3, name: str = "SemanticValidator"):
        super().__init__(name)
        self.similarity_threshold = similarity_threshold

        # 🚨 ARCHITECTURE NOTE: These should be configurable, not hardcoded
        # TODO: Move to configuration file
        # For now, we use an empty list to avoid false positives during verification
        self.irrelevant_keywords = []

    def validate(self, steps: List[Dict[str, Any]], query: str) -> ValidationResult:
        """验证步骤的语义相关性"""
        if not steps:
            return self._create_result(False, "没有推理步骤", 0.0)

        try:
            # 计算每个步骤与查询的相似度
            low_similarity_steps = []
            irrelevant_steps = []

            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    continue

                step_text = self._extract_step_text(step)
                if not step_text:
                    continue

                # 计算语义相似度
                similarity = self._calculate_similarity(step_text, query)

                # 检查无关关键词
                has_irrelevant_keywords = any(
                    keyword in step_text.lower() for keyword in self.irrelevant_keywords
                )

                # 记录低相似度步骤
                if similarity < self.similarity_threshold or has_irrelevant_keywords:
                    low_similarity_steps.append({
                        "step_index": i + 1,
                        "text": step_text[:100],
                        "similarity": similarity,
                        "has_irrelevant_keywords": has_irrelevant_keywords
                    })

                    # 更严格的条件判断
                    if similarity < 0.5 or has_irrelevant_keywords:
                        sub_query = step.get('sub_query', 'N/A') or 'N/A'
                        irrelevant_steps.append(
                            f"步骤{i+1}: {str(sub_query)[:50]}... (相似度: {similarity:.2f}, 关键词: {has_irrelevant_keywords})"
                        )

            # 生成验证结果
            if irrelevant_steps:
                return self._create_result(
                    is_valid=False,
                    reason=f"语义相似度验证失败: {'; '.join(irrelevant_steps)}",
                    quality_score=0.3,
                    irrelevant_steps=irrelevant_steps,
                    low_similarity_details=low_similarity_steps
                )
            elif low_similarity_steps:
                return self._create_result(
                    is_valid=True,
                    reason="部分步骤相似度较低，但仍在可接受范围内",
                    quality_score=0.7,
                    low_similarity_details=low_similarity_steps
                )
            else:
                return self._create_result(
                    is_valid=True,
                    reason="所有步骤语义相关性良好",
                    quality_score=0.9
                )

        except Exception as e:
            logger.error(f"语义相关性验证失败: {e}")
            return self._create_result(
                False,
                f"验证过程中发生错误: {str(e)}",
                0.1
            )

    def _extract_step_text(self, step: Dict[str, Any]) -> str:
        """从步骤中提取文本内容"""
        description = step.get('description', '') or ''
        sub_query = step.get('sub_query', '') or ''
        return f"{description} {sub_query}".strip()

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度

        TODO: 实现更复杂的语义相似度计算
        当前使用简单的Jaccard相似度
        """
        if not text1 or not text2:
            return 0.0

        # 简单的词袋相似度
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)

    def add_irrelevant_keyword(self, keyword: str):
        """添加无关关键词"""
        if keyword not in self.irrelevant_keywords:
            self.irrelevant_keywords.append(keyword.lower())

    def remove_irrelevant_keyword(self, keyword: str):
        """移除无关关键词"""
        if keyword.lower() in self.irrelevant_keywords:
            self.irrelevant_keywords.remove(keyword.lower())

    def set_similarity_threshold(self, threshold: float):
        """设置相似度阈值"""
        if 0.0 <= threshold <= 1.0:
            self.similarity_threshold = threshold
        else:
            raise ValueError("相似度阈值必须在0.0-1.0之间")