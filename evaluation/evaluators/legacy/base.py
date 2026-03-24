"""
RANGEN 新的评估框架 - 核心基础类

基于实际运行结果的有意义评估系统
"""

import time
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EvaluationStatus(Enum):
    """评估状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class EvaluationResult:
    """评估结果"""
    dimension: str
    score: float  # 0.0 - 1.0
    status: EvaluationStatus
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    execution_time_ms: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "status": self.status.value,
            "metrics": self.metrics,
            "details": self.details,
            "timestamp": self.timestamp,
            "execution_time_ms": self.execution_time_ms,
            "error": self.error
        }


class BaseEvaluator(ABC):
    """评估器基类 - 所有评估器的父类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        self.system_url = self.config.get("system_url", "http://localhost:8000")
    
    @abstractmethod
    async def evaluate(self) -> EvaluationResult:
        """执行评估 - 子类必须实现"""
        pass
    
    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """评估维度名称"""
        pass
    
    @property
    def weight(self) -> float:
        """在综合评分中的权重"""
        return self.config.get("weight", 0.15)
    
    async def run_evaluation(self) -> EvaluationResult:
        """运行评估并记录时间"""
        start_time = time.time()
        try:
            result = await self.evaluate()
            result.execution_time_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            self.logger.error(f"评估失败: {e}")
            return EvaluationResult(
                dimension=self.dimension_name,
                score=0.0,
                status=EvaluationStatus.FAILED,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000
            )
    
    def _safe_score(self, value: float, default: float = 0.0) -> float:
        """安全地将值转换为分数"""
        if value is None:
            return default
        return max(0.0, min(1.0, float(value)))


class CompositeEvaluator:
    """组合评估器 - 运行多个维度评估并计算综合分数"""
    
    def __init__(self, evaluators: List[BaseEvaluator], config: Optional[Dict[str, Any]] = None):
        self.evaluators = evaluators
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def run_all(self) -> Dict[str, Any]:
        """运行所有评估"""
        results = {}
        overall_score = 0.0
        total_weight = 0.0
        
        for evaluator in self.evaluators:
            self.logger.info(f"开始评估: {evaluator.dimension_name}")
            result = await evaluator.run_evaluation()
            results[evaluator.dimension_name] = result.to_dict()
            
            if result.status == EvaluationStatus.COMPLETED:
                overall_score += result.score * evaluator.weight
                total_weight += evaluator.weight
        
        # 归一化综合分数
        if total_weight > 0:
            overall_score /= total_weight
        
        return {
            "overall_score": overall_score,
            "dimensions": results,
            "timestamp": datetime.now().isoformat(),
            "evaluator_count": len(self.evaluators),
            "completed_count": sum(
                1 for r in results.values() 
                if r["status"] == EvaluationStatus.COMPLETED.value
            )
        }
    
    def add_evaluator(self, evaluator: BaseEvaluator):
        """添加评估器"""
        self.evaluators.append(evaluator)


# 评估配置
EVALUATION_CONFIG = {
    "system_url": "http://localhost:8000",
    "timeout": 30,  # 评估超时时间(秒)
    "retries": 3,   # 重试次数
}
