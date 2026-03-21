"""
验证器基类和数据结构
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    reason: str = ""
    quality_score: float = 1.0
    details: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.suggestions is None:
            self.suggestions = []


class BaseValidator(ABC):
    """验证器基类"""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__

    @abstractmethod
    def validate(self, steps: List[Dict[str, Any]], query: str) -> ValidationResult:
        """验证步骤

        Args:
            steps: 要验证的步骤列表
            query: 原始查询

        Returns:
            ValidationResult: 验证结果
        """
        pass

    def _create_result(self,
                      is_valid: bool,
                      reason: str = "",
                      quality_score: float = 1.0,
                      **details) -> ValidationResult:
        """创建验证结果的辅助方法"""
        return ValidationResult(
            is_valid=is_valid,
            reason=reason,
            quality_score=quality_score,
            details=details
        )
