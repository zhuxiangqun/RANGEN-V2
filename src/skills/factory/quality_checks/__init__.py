"""
Skill Factory 质量检查模块

提供自动化技能质量检查功能，包括：
1. 文件存在性检查
2. 格式正确性检查
3. 必填字段完整性检查
4. 结构合理性检查
"""

from .checker import (
    SkillQualityChecker,
    QualityReport,
    CheckResult,
    CheckStatus
)

__all__ = [
    "SkillQualityChecker",
    "QualityReport", 
    "CheckResult",
    "CheckStatus"
]

__version__ = "1.0.0"