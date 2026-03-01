#!/usr/bin/env python3
"""
FRAMES处理器 - 数据模型
FRAMES Processor - Data Models

提供FRAMES问题处理的核心数据结构和枚举类型
"""
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class FramesProblemType(Enum):
    """FRAMES问题类型"""
    MULTIPLE_CONSTRAINTS = "multiple_constraints"  # 多重约束推理
    NUMERICAL_REASONING = "numerical_reasoning"    # 数值推理
    TEMPORAL_REASONING = "temporal_reasoning"      # 时间推理
    TABULAR_REASONING = "tabular_reasoning"        # 表格推理
    CAUSAL_REASONING = "causal_reasoning"          # 因果推理
    COMPARATIVE_REASONING = "comparative_reasoning" # 比较推理
    COMPLEX_QUERY = "complex_query"                # 复杂查询


class ProcessingStatus(Enum):
    """处理状态"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    REASONING = "reasoning"
    INTEGRATING = "integrating"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FramesProblem:
    """FRAMES问题数据结构"""
    problem_id: str
    query: str
    problem_type: FramesProblemType
    expected_answer: Optional[str] = None
    reasoning_types: List[str] = field(default_factory=list)
    constraints: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    difficulty_level: int = 1  # 1-5难度等级
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningStep:
    """推理步骤"""
    step_id: str
    description: str
    input_data: Any
    output_data: Any
    confidence: float
    reasoning_type: str
    timestamp: float = field(default_factory=time.time)
    status: ProcessingStatus = ProcessingStatus.PENDING
    error: Optional[str] = None


@dataclass
class FramesResult:
    """FRAMES处理结果"""
    problem_id: str
    answer: str
    confidence: float
    reasoning_steps: List[ReasoningStep]
    processing_time: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
