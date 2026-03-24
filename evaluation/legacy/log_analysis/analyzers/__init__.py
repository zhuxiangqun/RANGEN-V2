"""
评测系统分析器模块
提供不同维度的分析功能，便于维护和扩展
"""

from .frames_analyzer import FramesAnalyzer
from .performance_analyzer import PerformanceAnalyzer
from .quality_analyzer import QualityAnalyzer
from .intelligence_analyzer import IntelligenceAnalyzer
from .system_health_analyzer import SystemHealthAnalyzer
from .reasoning_analyzer import ReasoningAnalyzer
from .code_quality_analyzer import CodeQualityAnalyzer
from .static_analyzer import (
    StaticArchitectureAnalyzer,
    StaticDataCapabilityAnalyzer,
    StaticPlatformCapabilityAnalyzer,
    run_static_evaluation
)

__all__ = [
    'FramesAnalyzer',
    'PerformanceAnalyzer', 
    'QualityAnalyzer',
    'IntelligenceAnalyzer',
    'SystemHealthAnalyzer',
    'ReasoningAnalyzer',
    'CodeQualityAnalyzer',
    'StaticArchitectureAnalyzer',
    'StaticDataCapabilityAnalyzer',
    'StaticPlatformCapabilityAnalyzer',
    'run_static_evaluation'
]
