#!/usr/bin/env python3
"""
Hook类型定义
定义Hook透明化系统使用的核心数据类型
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class HookEventType(Enum):
    """Hook事件类型"""
    AGENT_DECISION = "agent_decision"  # 智能体决策
    EVOLUTION_PLAN = "evolution_plan"  # 进化计划
    HAND_EXECUTION = "hand_execution"  # Hand执行
    CONSTITUTION_CHECK = "constitution_check"  # 宪法检查
    MODEL_REVIEW = "model_review"  # 模型审查
    WORKFLOW_STEP = "workflow_step"  # 工作流步骤
    ERROR_OCCURRED = "error_occurred"  # 错误发生
    SYSTEM_STATE_CHANGE = "system_state_change"  # 系统状态变化
    BACKGROUND_THINKING = "background_thinking"  # 后台思考
    GIT_OPERATION = "git_operation"  # Git操作


class HookVisibilityLevel(Enum):
    """Hook可见性级别"""
    INTERNAL = "internal"  # 内部调试
    DEVELOPER = "developer"  # 开发者
    ENTREPRENEUR = "entrepreneur"  # 创业者
    PUBLIC = "public"  # 公开


@dataclass
class HookEvent:
    """Hook事件"""
    event_id: str
    event_type: HookEventType
    timestamp: str
    source: str  # 事件来源
    data: Dict[str, Any]  # 事件数据
    visibility: HookVisibilityLevel = HookVisibilityLevel.DEVELOPER