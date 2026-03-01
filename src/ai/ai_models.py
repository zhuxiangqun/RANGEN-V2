#!/usr/bin/env python3
"""
AI Algorithm Data Models

AI引擎相关的数据模型和类型定义
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class TaskType(Enum):
    """任务类型"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    NLP = "nlp"
    COMPUTER_VISION = "computer_vision"
    REINFORCEMENT = "reinforcement"
    DEFAULT = "default"


class EngineType(Enum):
    """引擎类型"""
    ML = "ml"
    DL = "dl"
    RL = "rl"
    NLP = "nlp"
    CV = "cv"


@dataclass
class AIRequest:
    """AI请求"""
    task_type: str
    data: Any
    config: Optional[Dict[str, Any]] = None


@dataclass
class AIResponse:
    """AI响应"""
    success: bool
    result: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AIResult:
    """AI结果"""
    output: Any
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class ModelArchitecture:
    """模型架构"""
    name: str
    type: str
    parameters: Dict[str, Any]
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None


def create_default_ai_result(output: Any, processing_time: float = 0.0) -> AIResult:
    """创建默认AI结果"""
    return AIResult(
        output=output,
        confidence=0.5,
        processing_time=processing_time,
        metadata={}
    )


def create_error_result(error: str, processing_time: float = 0.0) -> AIResult:
    """创建错误结果"""
    return AIResult(
        output=None,
        confidence=0.0,
        processing_time=processing_time,
        metadata={"error": error}
    )
