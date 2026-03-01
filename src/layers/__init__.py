#!/usr/bin/env python3
"""
分层架构模块 - 统一导入
Layered Architecture Module - Unified Imports
"""

# 业务层导入 - 从重构后的模块
from src.layers.business_strategies import (
    EvaluationStrategy,
    QueryEvaluationStrategy,
    PerformanceEvaluationStrategy,
    QualityEvaluationStrategy,
)

from src.layers.business_commands import (
    BusinessCommand,
    BusinessCommandProcessor,
)

from src.layers.business_handlers import (
    RuleHandler,
    ValidationRuleHandler,
    ProcessingRuleHandler,
    DefaultRuleHandler,
)

from src.layers.business_states import (
    BusinessState,
    IdleState,
    ProcessingState,
    ErrorState,
    BusinessStateManager,
)

# 表示层
try:
    from src.layers.presentation_layer import (
        PresentationInterface,
        ResearchAPI,
        WebInterface,
        PresentationLayer
    )
except ImportError:
    PresentationInterface = None
    ResearchAPI = None
    WebInterface = None
    PresentationLayer = None

# 数据层
try:
    from src.layers.data_layer import DataLayer
except ImportError:
    DataLayer = None

__all__ = [
    # 策略模式
    'EvaluationStrategy',
    'QueryEvaluationStrategy', 
    'PerformanceEvaluationStrategy',
    'QualityEvaluationStrategy',
    
    # 命令模式
    'BusinessCommand',
    'BusinessCommandProcessor',
    
    # 责任链模式
    'RuleHandler',
    'ValidationRuleHandler',
    'ProcessingRuleHandler',
    'DefaultRuleHandler',
    
    # 状态模式
    'BusinessState',
    'IdleState',
    'ProcessingState',
    'ErrorState',
    'BusinessStateManager',
    
    # 表示层
    'PresentationInterface',
    'ResearchAPI',
    'WebInterface',
    'PresentationLayer',
    
    # 数据层
    'DataLayer',
]
