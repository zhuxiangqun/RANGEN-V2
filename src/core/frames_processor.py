#!/usr/bin/env python3
"""
FRAMES问题处理核心模块 - 统一导入
FRAMES Problem Processing Core Module - Unified Import

本模块已重构为多个子模块:
- frames_models: 数据模型和枚举类型

主要类 FramesProcessor 仍保留在本文件中。
"""

# 导入重构后的子模块
from src.core.frames_models import (
    FramesProblemType,
    ProcessingStatus,
    FramesProblem,
    ReasoningStep,
    FramesResult,
)

__all__ = [
    'FramesProblemType',
    'ProcessingStatus', 
    'FramesProblem',
    'ReasoningStep',
    'FramesResult',
]
