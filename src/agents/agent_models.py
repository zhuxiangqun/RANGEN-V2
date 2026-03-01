#!/usr/bin/env python3
"""
智能体数据模型 - 避免循环导入
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass
class AgentConfig:
    """智能体配置 - 统一配置管理"""
    agent_id: str
    agent_type: str = "generic"
    enabled: bool = True
    priority: int = 5
    timeout: float = 30.0
    retry_count: int = 3
    confidence_threshold: float = 0.7
    max_retries: int = 3
    use_intelligent_config: bool = True
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "enabled": self.enabled,
            "priority": self.priority,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "confidence_threshold": self.confidence_threshold,
            "max_retries": self.max_retries,
            "use_intelligent_config": self.use_intelligent_config,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentConfig':
        """从字典创建配置"""
        return cls(
            agent_id=data.get("agent_id", "unknown"),
            agent_type=data.get("agent_type", "generic"),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 5),
            timeout=data.get("timeout", 30.0),
            retry_count=data.get("retry_count", 3),
            confidence_threshold=data.get("confidence_threshold", 0.7),
            max_retries=data.get("max_retries", 3),
            use_intelligent_config=data.get("use_intelligent_config", True),
            metadata=data.get("metadata", {})
        )


@dataclass
class AgentState:
    """智能体状态"""
    agent_id: str
    status: str
    last_activity: float
    performance_metrics: Dict[str, float]
    capabilities: List[str]


@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    result: Any
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]


@dataclass
class AgentResult:
    """智能体结果"""
    success: bool
    data: Any
    confidence: float
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentCapability(Enum):
    """智能体能力枚举"""
    EXTENSIBILITY = "extensibility"
    INTELLIGENCE = "intelligence"
    AUTONOMOUS_DECISION = "autonomous_decision"
    DYNAMIC_STRATEGY = "dynamic_strategy"
    STRATEGY_LEARNING = "strategy_learning"
    SELF_LEARNING = "self_learning"
    AUTOMATIC_REASONING = "automatic_reasoning"
    DYNAMIC_CONFIDENCE = "dynamic_confidence"
    LLM_DRIVEN_RECOGNITION = "llm_driven_recognition"
    DYNAMIC_CHAIN_OF_THOUGHT = "dynamic_chain_of_thought"
    DYNAMIC_CLASSIFICATION = "dynamic_classification"


@dataclass
class StrategyDecision:
    """策略决策结果"""
    strategy_name: str
    strategy_type: str
    confidence: float
    reasoning: str
    parameters: Dict[str, Any]
    expected_outcome: str
    fallback_strategies: List[str]


@dataclass
class PerformanceMetrics:
    """性能指标"""
    accuracy: float
    execution_time: float
    success_rate: float
    confidence: float
    quality_score: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class LearningResult:
    """学习结果"""
    learning_type: str
    improvement: float
    confidence: float
    timestamp: datetime = field(default_factory=datetime.now)