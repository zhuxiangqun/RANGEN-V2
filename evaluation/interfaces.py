#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
评测系统接口定义

定义评测系统与生产系统之间的标准接口，确保解耦和可维护性。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class EvaluationRequest:
    """评测请求"""
    query: str
    context: Dict[str, Any] = None
    timeout: float = 30.0
    metadata: Dict[str, Any] = None

@dataclass
class EvaluationResult:
    """评测结果"""
    query: str
    answer: str
    confidence: float
    execution_time: float
    success: bool
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class EvaluationReport:
    """评测报告"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_accuracy: float
    average_execution_time: float
    results: List[EvaluationResult]
    metadata: Dict[str, Any] = None
    generated_at: datetime = None

    def __post_init__(self):
        if self.generated_at is None:
            self.generated_at = datetime.now()

class ResearchSystemInterface(ABC):
    """研究系统接口"""
    
    @abstractmethod
    async def research(self, request: EvaluationRequest) -> EvaluationResult:
        """执行研究请求"""
        pass
    
    @abstractmethod
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        pass

class DatasetInterface(ABC):
    """数据集接口"""
    
    @abstractmethod
    def load_samples(self, count: int = None) -> List[Dict[str, Any]]:
        """加载数据集样本"""
        pass
    
    @abstractmethod
    def get_dataset_info(self) -> Dict[str, Any]:
        """获取数据集信息"""
        pass

class MetricsInterface(ABC):
    """评测指标接口"""
    
    @abstractmethod
    def calculate_accuracy(self, result: EvaluationResult, expected: str) -> float:
        """计算准确率"""
        pass
    
    @abstractmethod
    def calculate_quality_score(self, result: EvaluationResult) -> float:
        """计算质量分数"""
        pass
    
    @abstractmethod
    def calculate_performance_metrics(self, results: List[EvaluationResult]) -> Dict[str, float]:
        """计算性能指标"""
        pass

class ReportGeneratorInterface(ABC):
    """报告生成器接口"""
    
    @abstractmethod
    def generate_report(self, report: EvaluationReport, format: str = "markdown") -> str:
        """生成评测报告"""
        pass
    
    @abstractmethod
    def save_report(self, report: EvaluationReport, filepath: str, format: str = "markdown") -> None:
        """保存评测报告"""
        pass
