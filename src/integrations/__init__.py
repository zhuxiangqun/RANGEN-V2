#!/usr/bin/env python3
"""
集成模块
集成聊天触发、定时任务、外部系统和线性集成
"""

__version__ = "1.0.0"

# 从 src.integration 合并的内容
from .sop_learning_integrator import SOPLearningIntegrator
from .workflow_integration import WorkflowIntegration
from .test_workflow_integration import TestWorkflowIntegration

# 从 src.integrations 合并的内容
from .linear_integration import LinearIntegration

__all__ = [
    'SOPLearningIntegrator',
    'WorkflowIntegration',
    'TestWorkflowIntegration',
    'LinearIntegration',
]
