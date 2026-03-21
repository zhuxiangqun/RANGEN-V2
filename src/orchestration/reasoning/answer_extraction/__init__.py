"""
答案提取模块 - 模块化重构版本
"""
from .answer_extractor import AnswerExtractor
from .extraction_strategies import (
    ExtractionStrategy,
    LLMExtractionStrategy,
    PatternExtractionStrategy,
    SemanticExtractionStrategy,
    CognitiveExtractionStrategy
)
from .answer_validator import AnswerValidator
from .answer_formatter import AnswerFormatter

__all__ = [
    'AnswerExtractor',
    'ExtractionStrategy',
    'LLMExtractionStrategy',
    'PatternExtractionStrategy',
    'SemanticExtractionStrategy',
    'CognitiveExtractionStrategy',
    'AnswerValidator',
    'AnswerFormatter',
]

