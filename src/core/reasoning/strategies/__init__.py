"""
推理策略模块

该模块包含各种推理策略，用于根据查询特征选择不同的生成方法。
采用策略模式，支持动态扩展新的推理策略。
"""

from .base_strategy import BaseStepGenerationStrategy
from .simple_strategy import SimpleQueryStrategy
from .complex_strategy import ComplexQueryStrategy
from .strategy_selector import StepGenerationStrategySelector

__all__ = [
    'BaseStepGenerationStrategy',
    'SimpleQueryStrategy',
    'ComplexQueryStrategy',
    'StepGenerationStrategySelector'
]
