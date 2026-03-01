"""
分层架构核心数据类型定义

此模块定义了分层架构中使用的核心数据结构和类型。
包括战略决策层、战术优化层、执行协调层的数据模型。
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ExecutionStrategy(Enum):
    """执行策略枚举"""
    PARALLEL = "parallel"
    SERIAL = "serial"
    MIXED = "mixed"


class TaskType(Enum):
    """任务类型枚举"""
    KNOWLEDGE_RETRIEVAL = "knowledge_retrieval"
    REASONING = "reasoning"
    ANSWER_GENERATION = "answer_generation"
    CITATION = "citation"
    MEMORY = "memory"
    ANALYSIS = "analysis"


@dataclass
class TaskDefinition:
    """任务定义"""
    task_id: str
    task_type: TaskType
    description: str
    dependencies: List[str] = field(default_factory=list)
    priority: float = 1.0
    estimated_complexity: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategicPlan:
    """战略决策结果"""
    tasks: List[TaskDefinition]
    execution_strategy: ExecutionStrategy
    task_dependencies: Dict[str, List[str]] = field(default_factory=dict)
    priority_weights: Dict[str, float] = field(default_factory=dict)
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)
    timeline_constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionParams:
    """战术优化结果"""
    timeouts: Dict[str, float] = field(default_factory=dict)          # 各任务超时时间
    parallelism: Dict[str, bool] = field(default_factory=dict)        # 各任务是否并行
    resource_allocation: Dict[str, int] = field(default_factory=dict) # 资源分配
    retry_strategy: Dict[str, int] = field(default_factory=dict)      # 重试策略
    batch_sizes: Dict[str, int] = field(default_factory=dict)         # 批处理大小
    concurrency_limits: Dict[str, int] = field(default_factory=dict)  # 并发限制


@dataclass
class TaskResult:
    """单个任务执行结果"""
    task_id: str
    task_type: TaskType
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """执行协调结果"""
    final_answer: str
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    execution_metrics: Dict[str, Any] = field(default_factory=dict)
    quality_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class QueryAnalysis:
    """查询分析结果"""
    query: str
    query_type: str = "general"
    complexity_score: float = 1.0
    estimated_tasks: List[str] = field(default_factory=list)
    domain_knowledge: List[str] = field(default_factory=list)
    reasoning_requirements: Dict[str, Any] = field(default_factory=dict)
    evidence_requirements: Dict[str, Any] = field(default_factory=dict)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemState:
    """系统状态信息"""
    available_resources: Dict[str, Any] = field(default_factory=dict)
    current_load: Dict[str, float] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    active_tasks: List[str] = field(default_factory=list)
    system_health: Dict[str, Any] = field(default_factory=dict)


# 类型别名
TaskId = str
TaskTypeStr = str
ExecutionStrategyStr = str
