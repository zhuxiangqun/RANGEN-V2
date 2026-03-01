#!/usr/bin/env python3
"""
进化类型定义
定义自进化系统使用的核心数据类型
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Dict, List, Any, Optional


class EvolutionImpactLevel(Enum):
    """进化影响级别"""
    MINOR = "minor"      # 微优化，低风险
    MODERATE = "moderate"  # 中等改进，需简单验证
    MAJOR = "major"      # 重大修改，需多重验证和创业者确认
    ARCHITECTURAL = "architectural"  # 架构级变更，需严格审查


class EvolutionStatus(Enum):
    """进化状态"""
    PENDING = "pending"          # 待开始
    ANALYZING = "analyzing"      # 分析中
    PLANNING = "planning"        # 规划中
    REVIEWING = "reviewing"      # 审查中
    APPROVED = "approved"        # 已批准
    EXECUTING = "executing"      # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    REJECTED = "rejected"        # 被拒绝


@dataclass
class EvolutionPlan:
    """进化计划"""
    plan_id: str
    description: str
    impact_level: EvolutionImpactLevel
    target_files: List[str]
    expected_benefits: List[str]
    risks: List[str]
    validation_methods: List[str]
    estimated_effort: int  # 小时
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: EvolutionStatus = EvolutionStatus.PENDING
    goal: Optional[str] = None
    changes: Optional[List[Dict[str, Any]]] = None
    success_metrics: Optional[List[str]] = None
    estimated_duration: Optional[str] = None


@dataclass
class EvolutionResult:
    """进化结果"""
    plan_id: str
    status: EvolutionStatus
    execution_time: float  # 秒
    changes_made: List[str]
    git_commit_hash: Optional[str] = None
    performance_impact: Optional[Dict[str, Any]] = None
    validation_results: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    completed_at: Optional[str] = None