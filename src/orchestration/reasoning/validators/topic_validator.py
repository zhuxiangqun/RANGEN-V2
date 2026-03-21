"""
主题一致性验证器
验证推理步骤是否与原始查询保持主题一致性
"""
import logging
from typing import Dict, List, Any, Set

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class TopicConsistencyValidator(BaseValidator):
    """主题一致性验证器"""

    def __init__(self, name: str = "TopicValidator"):
        super().__init__(name)

    def validate(self, steps: List[Dict[str, Any]], query: str) -> ValidationResult:
        """验证主题一致性"""
        if not steps:
            return self._create_result(False, "没有推理步骤", 0.0)

        try:
            # 提取查询主题
            query_topics = self._extract_topics(query)

            # 验证每个步骤的主题一致性
            inconsistent_steps = []
            topic_coverage = set()

            for i, step in enumerate(steps):
                step_text = self._extract_step_text(step)
                step_topics = self._extract_topics(step_text)

                # 计算主题重叠度
                overlap = len(query_topics.intersection(step_topics))
                total_query_topics = len(query_topics)

                if total_query_topics > 0:
                    coverage_ratio = overlap / total_query_topics
                else:
                    coverage_ratio = 1.0  # 如果查询没有明确主题，默认通过

                # 记录主题覆盖
                topic_coverage.update(step_topics)

                # 检查一致性
                if coverage_ratio < 0.3:  # 至少30%的主题重叠
                    inconsistent_steps.append({
                        "step_index": i + 1,
                        "step_text": step_text[:100],
                        "overlap_ratio": coverage_ratio,
                        "query_topics": list(query_topics),
                        "step_topics": list(step_topics)
                    })

            # 生成验证结果
            if inconsistent_steps:
                return self._create_result(
                    is_valid=False,
                    reason=f"发现{inconsistent_steps}个主题不一致的步骤",
                    quality_score=0.4,
                    inconsistent_steps=inconsistent_steps,
                    topic_coverage=list(topic_coverage)
                )
            else:
                coverage_score = min(1.0, len(topic_coverage) / max(1, len(query_topics)))
                return self._create_result(
                    is_valid=True,
                    reason="所有步骤主题一致性良好",
                    quality_score=0.8 + 0.2 * coverage_score,
                    topic_coverage=list(topic_coverage),
                    coverage_score=coverage_score
                )

        except Exception as e:
            logger.error(f"主题一致性验证失败: {e}")
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

    def _extract_topics(self, text: str) -> Set[str]:
        """从文本中提取主题关键词"""
        if not text:
            return set()

        # 转换为小写
        text_lower = text.lower()

        # 定义主题关键词映射
        topic_keywords = {
            'history': ['history', 'historical', 'president', 'first lady', 'politics', 'political'],
            'literature': ['book', 'novel', 'author', 'writer', 'literature', 'bronte', 'charlotte'],
            'science': ['science', 'scientific', 'academy', 'research', 'technology'],
            'geography': ['country', 'capital', 'city', 'location', 'place', 'where'],
            'mathematics': ['number', 'calculate', 'math', 'numerical', 'dewey', 'decimal'],
            'architecture': ['building', 'tower', 'height', 'feet', 'tallest', 'rank'],
            'time': ['year', 'date', 'when', 'published', 'born', 'age'],
            'comparison': ['compare', 'versus', 'vs', 'rank', 'ranking', 'tallest']
        }

        topics = set()

        # 检查每个主题
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.add(topic)

        # 如果没有找到明确主题，尝试提取名词作为主题
        if not topics:
            topics.update(self._extract_noun_phrases(text))

        return topics

    def _extract_noun_phrases(self, text: str) -> Set[str]:
        """提取名词短语作为主题（简化版本）"""
        # 简单的启发式方法：提取大写开头的词和数字
        words = text.split()
        noun_phrases = set()

        for word in words:
            # 去除标点符号
            clean_word = ''.join(c for c in word if c.isalnum() or c in ['-', "'"])

            # 检查是否可能是专有名词（大写开头或包含数字）
            if (clean_word and clean_word[0].isupper()) or any(c.isdigit() for c in clean_word):
                if len(clean_word) > 2:  # 忽略太短的词
                    noun_phrases.add(clean_word.lower())

        return noun_phrases
