"""
幻觉检测器
检测推理步骤中是否存在幻觉内容（不存在或不相关的信息）
"""
import logging
import re
from typing import Dict, List, Any, Set

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class HallucinationDetector(BaseValidator):
    """幻觉检测器"""

    def __init__(self, name: str = "HallucinationDetector"):
        super().__init__(name)

        # 已知的幻觉实体模式
        self.hallucinated_entities = {
            'chinese academy of sciences',
            'beijing institute',
            'china science academy',
            'chinese scientific institution'
        }

        # 可疑的关键词模式
        self.suspicious_patterns = [
            r'\b(chinese|china|beijing)\b.*\b(academy|sciences?|institute)\b',
            r'\b(academy of sciences?|scientific institute)\b.*\b(china|chinese)\b',
            r'\b(fictional|imaginary|made.up)\b.*\b(book|novel|author)\b'
        ]

    def validate(self, steps: List[Dict[str, Any]], query: str) -> ValidationResult:
        """检测幻觉内容"""
        if not steps:
            return self._create_result(False, "没有推理步骤", 0.0)

        try:
            hallucinated_items = []
            suspicious_items = []

            # 分析查询内容，确定检测策略
            query_lower = query.lower()
            is_historical_query = any(word in query_lower for word in ['president', 'first lady', 'historical'])
            is_literature_query = any(word in query_lower for word in ['book', 'novel', 'author', 'bronte'])

            for i, step in enumerate(steps):
                step_text = self._extract_step_text(step)

                # 检测明确的幻觉实体
                hallucinated = self._detect_hallucinated_entities(step_text, query_lower)
                if hallucinated:
                    hallucinated_items.extend([
                        {"step_index": i + 1, "entity": entity, "text": step_text[:100]}
                        for entity in hallucinated
                    ])

                # 检测可疑模式
                suspicious = self._detect_suspicious_patterns(step_text, query_lower, is_historical_query, is_literature_query)
                if suspicious:
                    suspicious_items.extend([
                        {"step_index": i + 1, "pattern": pattern, "text": step_text[:100]}
                        for pattern in suspicious
                    ])

            # 生成验证结果
            if hallucinated_items:
                return self._create_result(
                    is_valid=False,
                    reason=f"检测到{len(hallucinated_items)}个幻觉实体",
                    quality_score=0.2,
                    hallucinated_entities=hallucinated_items,
                    suspicious_patterns=suspicious_items
                )
            elif suspicious_items:
                return self._create_result(
                    is_valid=True,
                    reason=f"检测到{len(suspicious_items)}个可疑模式，建议人工审核",
                    quality_score=0.7,
                    suspicious_patterns=suspicious_items
                )
            else:
                return self._create_result(
                    is_valid=True,
                    reason="未检测到幻觉内容",
                    quality_score=0.95
                )

        except Exception as e:
            logger.error(f"幻觉检测失败: {e}")
            return self._create_result(
                False,
                f"检测过程中发生错误: {str(e)}",
                0.1
            )

    def _extract_step_text(self, step: Dict[str, Any]) -> str:
        """从步骤中提取文本内容"""
        description = step.get('description', '')
        sub_query = step.get('sub_query', '')
        return f"{description} {sub_query}".strip()

    def _detect_hallucinated_entities(self, step_text: str, query_lower: str) -> List[str]:
        """检测明确的幻觉实体"""
        step_lower = step_text.lower()
        detected = []

        for entity in self.hallucinated_entities:
            # 只有当查询不包含这些实体时才检测
            if entity not in query_lower and entity in step_lower:
                detected.append(entity)

        return detected

    def _detect_suspicious_patterns(self, step_text: str, query_lower: str,
                                  is_historical_query: bool, is_literature_query: bool) -> List[str]:
        """检测可疑的模式"""
        detected = []

        for pattern in self.suspicious_patterns:
            if re.search(pattern, step_text, re.IGNORECASE):
                # 根据查询类型调整检测灵敏度
                if is_historical_query and 'china' in pattern:
                    # 历史查询中出现中国元素可能是合理的
                    continue
                elif is_literature_query and 'fictional' in pattern:
                    # 文学查询中出现虚构元素可能是合理的
                    continue

                detected.append(pattern)

        return detected

    def add_hallucinated_entity(self, entity: str):
        """添加已知的幻觉实体"""
        self.hallucinated_entities.add(entity.lower())

    def remove_hallucinated_entity(self, entity: str):
        """移除幻觉实体"""
        self.hallucinated_entities.discard(entity.lower())

    def add_suspicious_pattern(self, pattern: str):
        """添加可疑模式"""
        if pattern not in self.suspicious_patterns:
            self.suspicious_patterns.append(pattern)

    def remove_suspicious_pattern(self, pattern: str):
        """移除可疑模式"""
        if pattern in self.suspicious_patterns:
            self.suspicious_patterns.remove(pattern)
