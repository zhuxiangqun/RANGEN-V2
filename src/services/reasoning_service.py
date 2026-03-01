#!/usr/bin/env python3
"""
推理服务 - 统一导入模块
Reasoning Service - Unified Import Module

本模块已重构为多个子模块:
- reasoning_strategies: 策略模式实现
- reasoning_engines: 引擎和工厂模式实现
- reasoning_observers: 观察者模式实现

为保持向后兼容，所有类仍可从本模块导入。
"""

# 导入重构后的子模块
from src.services.reasoning_strategies import (
    ReasoningStrategy,
    DeductiveReasoningStrategy,
    InductiveReasoningStrategy,
    AbductiveReasoningStrategy,
)

from src.services.reasoning_engines import (
    ReasoningEngineFactory,
    DeductiveReasoningEngine,
    InductiveReasoningEngine,
    AbductiveReasoningEngine,
    CausalReasoningEngine,
    AnalogicalReasoningEngine,
    LogicalReasoningFactory,
    CausalReasoningFactory,
    DeductiveEngine,
    InductiveEngine,
    AbductiveEngine,
    CausalChainEngine,
    CounterfactualEngine,
    InterventionEngine,
    DefaultLogicalEngine,
    DefaultCausalEngine,
)

from src.services.reasoning_observers import (
    ReasoningObserver,
    ReasoningLogger,
    ReasoningMetrics,
)

# 尝试导入原始模块中的其他类
try:
    from src.services.reasoning_service_original import (
        ReasoningCommand,
        AnalyzeCommand,
        SynthesizeCommand,
        ReasoningHandler,
        PreprocessingHandler,
        AnalysisHandler,
        SynthesisHandler,
        ReasoningDecorator,
        ValidationDecorator,
        CachingDecorator,
        ReasoningEngine,
        ReasoningStep,
        ReasoningService,
    )
except ImportError:
    # 如果原始文件不存在，从原始位置导入
    pass

__all__ = [
    # 策略
    'ReasoningStrategy',
    'DeductiveReasoningStrategy',
    'InductiveReasoningStrategy',
    'AbductiveReasoningStrategy',
    
    # 引擎
    'ReasoningEngineFactory',
    'DeductiveReasoningEngine',
    'InductiveReasoningEngine',
    'AbductiveReasoningEngine',
    'CausalReasoningEngine',
    'AnalogicalReasoningEngine',
    'LogicalReasoningFactory',
    'CausalReasoningFactory',
    'DeductiveEngine',
    'InductiveEngine',
    'AbductiveEngine',
    'CausalChainEngine',
    'CounterfactualEngine',
    'InterventionEngine',
    'DefaultLogicalEngine',
    'DefaultCausalEngine',
    
    # 观察者
    'ReasoningObserver',
    'ReasoningLogger',
    'ReasoningMetrics',
]
