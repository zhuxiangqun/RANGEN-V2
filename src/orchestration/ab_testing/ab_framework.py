#!/usr/bin/env python3
"""
A/B 测试框架 - 用于验证学习效果

功能:
- 创建 A/B 测试实验
- 流量分配
- 效果统计
- 胜出者判定
"""

import time
import uuid
import random
import statistics
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ExperimentStatus(str, Enum):
    """实验状态"""
    DRAFT = "draft"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"


class VariantType(str, Enum):
    """变体类型"""
    CONTROL = "control"
    TREATMENT = "treatment"


@dataclass
class Variant:
    """变体"""
    variant_id: str
    name: str
    variant_type: VariantType
    description: str = ""
    traffic_percentage: float = 50.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricResult:
    """指标结果"""
    metric_name: str
    variant_id: str
    value: float
    sample_size: int
    confidence_interval: tuple = field(default_factory=lambda: (0.0, 0.0))
    p_value: float = 0.0
    is_significant: bool = False


@dataclass
class ExperimentResult:
    """实验结果"""
    experiment_id: str
    winner: Optional[str] = None
    confidence_level: float = 0.0
    metrics: List[MetricResult] = field(default_factory=list)
    recommendation: str = ""
    completed_at: Optional[float] = None


@dataclass
class Experiment:
    """A/B 测试实验"""
    experiment_id: str
    name: str
    description: str
    variants: List[Variant]
    status: ExperimentStatus = ExperimentStatus.DRAFT
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metrics_config: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserAssignment:
    """用户分配记录"""
    experiment_id: str
    user_id: str
    variant_id: str
    assigned_at: float = field(default_factory=time.time)


class ABTestingFramework:
    """
    A/B 测试框架
    
    用于验证学习效果和策略优化
    """
    
    def __init__(self):
        self._experiments: Dict[str, Experiment] = {}
        self._assignments: Dict[str, List[UserAssignment]] = {}
        self._results: Dict[str, Dict[str, List[float]]] = {}
        self._min_sample_size = 100
        self._confidence_level = 0.95
    
    def create_experiment(
        self,
        name: str,
        description: str,
        control_name: str = "Control",
        treatment_name: str = "Treatment",
        traffic_split: float = 50.0
    ) -> Experiment:
        """
        创建实验
        
        Args:
            name: 实验名称
            description: 实验描述
            control_name: 对照组名称
            treatment_name: 实验组名称
            traffic_split: 实验组流量比例 (0-100)
            
        Returns:
            Experiment
        """
        experiment_id = f"exp_{uuid.uuid4().hex[:8]}"
        
        control = Variant(
            variant_id=f"{experiment_id}_ctrl",
            name=control_name,
            variant_type=VariantType.CONTROL,
            traffic_percentage=100 - traffic_split
        )
        
        treatment = Variant(
            variant_id=f"{experiment_id}_treat",
            name=treatment_name,
            variant_type=VariantType.TREATMENT,
            traffic_percentage=traffic_split
        )
        
        experiment = Experiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            variants=[control, treatment],
            status=ExperimentStatus.DRAFT
        )
        
        self._experiments[experiment_id] = experiment
        self._assignments[experiment_id] = []
        self._results[experiment_id] = {control.variant_id: [], treatment.variant_id: []}
        
        return experiment
    
    def start_experiment(self, experiment_id: str) -> bool:
        """启动实验"""
        if experiment_id not in self._experiments:
            return False
        
        experiment = self._experiments[experiment_id]
        if experiment.status == ExperimentStatus.RUNNING:
            return True
        
        experiment.status = ExperimentStatus.RUNNING
        experiment.started_at = time.time()
        return True
    
    def assign_user(self, experiment_id: str, user_id: str) -> str:
        """
        为用户分配变体
        
        Args:
            experiment_id: 实验ID
            user_id: 用户ID
            
        Returns:
            variant_id
        """
        if experiment_id not in self._experiments:
            raise ValueError("Experiment not found")
        
        experiment = self._experiments[experiment_id]
        if experiment.status != ExperimentStatus.RUNNING:
            raise ValueError("Experiment not running")
        
        existing = self._get_user_assignment(experiment_id, user_id)
        if existing:
            return existing
        
        rand = random.uniform(0, 100)
        cumulative = 0
        selected_variant = experiment.variants[0]
        
        for variant in experiment.variants:
            cumulative += variant.traffic_percentage
            if rand <= cumulative:
                selected_variant = variant
                break
        
        assignment = UserAssignment(
            experiment_id=experiment_id,
            user_id=user_id,
            variant_id=selected_variant.variant_id
        )
        
        self._assignments[experiment_id].append(assignment)
        return selected_variant.variant_id
    
    def record_metric(self, experiment_id: str, user_id: str, 
                     metric_name: str, value: float):
        """
        记录指标
        
        Args:
            experiment_id: 实验ID
            user_id: 用户ID
            metric_name: 指标名称
            value: 指标值
        """
        variant_id = self._get_user_assignment(experiment_id, user_id)
        if not variant_id:
            return
        
        if experiment_id in self._results:
            self._results[experiment_id].setdefault(variant_id, [])
            self._results[experiment_id][variant_id].append(value)
    
    def analyze_experiment(self, experiment_id: str) -> ExperimentResult:
        """
        分析实验结果
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            ExperimentResult
        """
        if experiment_id not in self._experiments:
            raise ValueError("Experiment not found")
        
        experiment = self._experiments[experiment_id]
        results = self._results.get(experiment_id, {})
        
        metrics = []
        winner = None
        max_effect = 0.0
        
        variant_results = {}
        for variant in experiment.variants:
            values = results.get(variant.variant_id, [])
            if len(values) >= self._min_sample_size:
                mean = statistics.mean(values)
                stdev = statistics.stdev(values) if len(values) > 1 else 0
                se = stdev / (len(values) ** 0.5) if stdev else 0
                
                ci_lower = mean - 1.96 * se
                ci_upper = mean + 1.96 * se
                
                variant_results[variant.variant_id] = {
                    "mean": mean,
                    "sample_size": len(values),
                    "ci": (ci_lower, ci_upper),
                    "stdev": stdev
                }
        
        if len(variant_results) == 2:
            ctrl = None
            treat = None
            
            for variant in experiment.variants:
                if variant.variant_type == VariantType.CONTROL:
                    ctrl = variant_results.get(variant.variant_id)
                else:
                    treat = variant_results.get(variant.variant_id)
            
            if ctrl and treat:
                effect = treat["mean"] - ctrl["mean"]
                effect_pct = (effect / ctrl["mean"] * 100) if ctrl["mean"] != 0 else 0
                
                pool_stdev = ((ctrl["stdev"] ** 2 + treat["stdev"] ** 2) ** 0.5)
                cohens_d = effect / pool_stdev if pool_stdev else 0
                
                is_significant = abs(cohens_d) >= 0.2
                
                metric_result = MetricResult(
                    metric_name="conversion",
                    variant_id="treatment",
                    value=treat["mean"],
                    sample_size=treat["sample_size"],
                    confidence_interval=treat["ci"],
                    is_significant=is_significant
                )
                metrics.append(metric_result)
                
                if is_significant and effect > 0:
                    winner = [v for v in experiment.variants if v.variant_type == VariantType.TREATMENT][0].variant_id
                    max_effect = effect_pct
        
        recommendation = self._generate_recommendation(winner, max_effect)
        
        experiment.status = ExperimentStatus.COMPLETED
        experiment.completed_at = time.time()
        
        return ExperimentResult(
            experiment_id=experiment_id,
            winner=winner,
            confidence_level=max_effect,
            metrics=metrics,
            recommendation=recommendation,
            completed_at=time.time()
        )
    
    def _get_user_assignment(self, experiment_id: str, user_id: str) -> Optional[str]:
        """获取用户分配"""
        assignments = self._assignments.get(experiment_id, [])
        for assignment in assignments:
            if assignment.user_id == user_id:
                return assignment.variant_id
        return None
    
    def _generate_recommendation(self, winner: Optional[str], effect: float) -> str:
        """生成建议"""
        if not winner:
            return "没有足够的统计显著性差异。建议增加样本量或调整实验参数。"
        
        if effect > 10:
            return f"实验组显著优于对照组 (提升 {effect:.1f}%)。建议全量推广实验组策略。"
        elif effect > 5:
            return f"实验组优于对照组 (提升 {effect:.1f}%)。建议逐步推广实验组策略。"
        else:
            return f"实验组略优于对照组 (提升 {effect:.1f}%)。建议继续观察或扩大实验。"
    
    def get_experiment_status(self, experiment_id: str) -> Dict[str, Any]:
        """获取实验状态"""
        if experiment_id not in self._experiments:
            return {}
        
        experiment = self._experiments[experiment_id]
        results = self._results.get(experiment_id, {})
        
        variant_stats = {}
        for variant in experiment.variants:
            values = results.get(variant.variant_id, [])
            variant_stats[variant.variant_id] = {
                "name": variant.name,
                "sample_size": len(values),
                "mean": statistics.mean(values) if values else 0,
            }
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status.value,
            "variants": variant_stats,
            "started_at": experiment.started_at,
            "duration_hours": (time.time() - experiment.started_at) / 3600 if experiment.started_at else 0
        }
    
    def list_experiments(self) -> List[Dict[str, Any]]:
        """列出所有实验"""
        return [
            {
                "experiment_id": exp.experiment_id,
                "name": exp.name,
                "status": exp.status.value,
                "created_at": exp.created_at
            }
            for exp in self._experiments.values()
        ]


_ab_framework: Optional[ABTestingFramework] = None

def get_ab_testing_framework() -> ABTestingFramework:
    """获取 A/B 测试框架实例"""
    global _ab_framework
    if _ab_framework is None:
        _ab_framework = ABTestingFramework()
    return _ab_framework
