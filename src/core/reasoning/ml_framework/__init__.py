"""
ML/RL框架 - 为推理系统提供机器学习能力

这个包提供了ML/RL集成的基础框架，包括：
- 并行结构检测
- 置信度评估
- 逻辑结构解析
- 计划优化
- 持续学习
"""
from .data_collection import DataCollectionPipeline
from .parallel_query_classifier import ParallelQueryClassifier
from .base_ml_component import BaseMLComponent, BaseRLComponent
from .logic_structure_parser import LogicStructureParser
from .adaptive_retry_agent import AdaptiveRetryAgent
from .dynamic_planner import DynamicPlanner
from .fewshot_pattern_learner import FewShotPatternLearner
from .cross_task_transfer import CrossTaskKnowledgeTransfer
from .rl_parallel_planner import RLParallelPlanner
from .deep_confidence_estimator import DeepConfidenceEstimator
from .transformer_planner import TransformerPlanner
from .gnn_plan_optimizer import GNNPlanOptimizer
from .continuous_learning_system import ContinuousLearningSystem
from .model_auto_loader import auto_load_model
from .model_performance_monitor import ModelPerformanceMonitor
from .data_augmentation import DataAugmentation
from .complexity_predictor import ComplexityPredictor
from .execution_time_predictor import ExecutionTimePredictor

__all__ = [
    'DataCollectionPipeline',
    'ParallelQueryClassifier',
    'BaseMLComponent',
    'BaseRLComponent',
    'LogicStructureParser',
    'AdaptiveRetryAgent',
    'DynamicPlanner',
    'FewShotPatternLearner',
    'CrossTaskKnowledgeTransfer',
    'RLParallelPlanner',
    'DeepConfidenceEstimator',
    'TransformerPlanner',
    'GNNPlanOptimizer',
    'ContinuousLearningSystem',
    'DataAugmentation',
    'ComplexityPredictor',
    'ExecutionTimePredictor',
]

__version__ = "0.2.0"
