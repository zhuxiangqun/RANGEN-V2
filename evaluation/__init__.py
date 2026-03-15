#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN 评测系统

独立的评测包，用于评估系统性能、准确性和质量。
与生产代码完全分离，通过标准接口进行交互。

主要功能：
- 基准测试（FRAMES、统一评测等）
- 性能评测
- 质量分析
- 报告生成
"""

__version__ = "1.0.0"
__author__ = "RANGEN Team"

# 导出主要评测器
from .benchmarks.frames_evaluator import FramesEvaluator
from .benchmarks.unified_evaluator import UnifiedEvaluator
from .benchmarks.performance_evaluator import PerformanceEvaluator
from .benchmarks.intelligent_quality_evaluator import IntelligentQualityAnalyzer

__all__ = [
    "FramesEvaluator",
    "UnifiedEvaluator",
    "PerformanceEvaluator",
    "IntelligentQualityAnalyzer"
]
