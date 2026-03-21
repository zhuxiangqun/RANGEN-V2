"""
Self-Learning System - 统一自我学习系统

整合所有学习模块的统一接口
"""

from .tool_selection_learner import (
    ToolSelectionLearner,
    TaskContext,
    TaskCategory,
    TaskComplexity,
    get_tool_selection_learner
)

from .execution_strategy_learner import (
    ExecutionStrategyLearner,
    TaskFeatures,
    StrategyType,
    StrategyOutcome,
    get_execution_strategy_learner
)

from .context_management_learner import (
    ContextManagementLearner,
    ContextItem,
    InfoType,
    UsageOutcome,
    get_context_management_learner
)

from .skill_trigger_learner import (
    SkillTriggerLearner,
    TriggerCondition,
    SkillTriggerRecord,
    get_skill_trigger_learner
)

__all__ = [
    # Tool Selection
    "ToolSelectionLearner",
    "TaskContext", 
    "TaskCategory",
    "TaskComplexity",
    "get_tool_selection_learner",
    
    # Execution Strategy
    "ExecutionStrategyLearner",
    "TaskFeatures",
    "StrategyType",
    "StrategyOutcome",
    "get_execution_strategy_learner",
    
    # Context Management
    "ContextManagementLearner",
    "ContextItem",
    "InfoType",
    "UsageOutcome",
    "get_context_management_learner",
    
    # Skill Trigger
    "SkillTriggerLearner",
    "TriggerCondition",
    "SkillTriggerRecord",
    "get_skill_trigger_learner"
]
