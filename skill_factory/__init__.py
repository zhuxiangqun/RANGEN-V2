"""
Skill Factory 主模块

基于Skill Factory模式的AI技能标准化开发工厂。
将AI技能开发从"手工业"升级到"工厂化"生产模式。
"""

from .prototypes.classifier import (
    SkillPrototypeClassifier,
    PrototypeType,
    ClassificationResult
)

from .quality_checks import (
    SkillQualityChecker,
    QualityReport,
    CheckResult,
    CheckStatus
)

__all__ = [
    # 原型分类
    "SkillPrototypeClassifier",
    "PrototypeType",
    "ClassificationResult",
    
    # 质量检查
    "SkillQualityChecker",
    "QualityReport",
    "CheckResult",
    "CheckStatus",
]

__version__ = "1.0.0"
__author__ = "RANGEN V2 Skill Factory Team"

# 工厂口号
__slogan__ = "从原型到生产，只需15分钟"