from enum import Enum
from dataclasses import dataclass
from typing import Optional

class DDLPhase(str, Enum):
    """DDL应用阶段 - 明确β在不同阶段的意义"""
    RETRIEVAL = "retrieval"      # β≈0:简单召回, β≈1:HyDE联想, β≈2:CoT辩证
    REASONING = "reasoning"      # β≈0:直觉推理, β≈1:系统分析, β≈2:反思迭代
    MEMORY = "memory"           # β≈1:智能遗忘
    CONTEXT = "context"         # β相关:上下文选择

@dataclass
class DDLParameters:
    """DDL参数包 - 统一输出格式"""
    base_beta: float
    
    # 元数据
    phase: DDLPhase
    confidence: float = 1.0
    explanation: str = ""
