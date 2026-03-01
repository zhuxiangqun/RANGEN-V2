"""
推理引擎模块 - 重构后的模块化实现
"""
from .models import (
    ReasoningStepType,
    Evidence,
    ReasoningStep,
    ReasoningResult
)
from .engine import RealReasoningEngine

# 🚀 方案A：统一架构组件
from .unified_output_formatter import UnifiedOutputFormatter
from .template_selector import TemplateSelector
from .evidence_quality_assessor import EvidenceQualityAssessor
from .confidence_calibrator import ConfidenceCalibrator

# 🚀 Phase 1: 答案验证模块
from .answer_validator import AnswerValidator
from .hierarchical_answer_validator import HierarchicalAnswerValidator

__all__ = [
    'ReasoningStepType',
    'Evidence',
    'ReasoningStep',
    'ReasoningResult',
    'RealReasoningEngine',
    # 统一架构组件
    'UnifiedOutputFormatter',
    'TemplateSelector',
    'EvidenceQualityAssessor',
    'ConfidenceCalibrator',
    # Phase 1: 答案验证模块
    'AnswerValidator',
]

