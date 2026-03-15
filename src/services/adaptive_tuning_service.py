#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应调优服务 - 基于机器学习的路由参数自动优化

功能：
1. 从A/B测试结果收集性能数据
2. 使用机器学习算法分析参数与性能关系
3. 自动调优路由策略参数
4. 实现安全约束下的自主优化
5. 持续学习和经验积累

集成：
- 与AB测试路由器集成，获取实验数据
- 使用ML框架进行机器学习分析
- 与配置服务集成，安全应用新参数
- 与监控系统集成，跟踪调优效果
"""

import time
import json
import math
import random
import logging
import threading
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path

from .ab_testing_router import ABTestingRouter, StrategyConfig, StrategyPerformance
from .ab_testing_service import ABTestingService, ExperimentResult, get_ab_testing_service
from .multi_model_config_service import MultiModelConfigService, get_multi_model_config_service
from .monitoring_dashboard_service import MonitoringDashboardService, get_monitoring_dashboard_service

# 导入ML框架组件
try:
    from src.core.reasoning.ml_framework.continuous_learning_system import ContinuousLearningSystem
    from src.core.reasoning.ml_framework.data_collection import DataCollectionPipeline
    from src.core.reasoning.ml_framework.model_performance_monitor import ModelPerformanceMonitor
    ML_FRAMEWORK_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("ML框架不可用，将使用简化调优算法")
    ML_FRAMEWORK_AVAILABLE = False


logger = logging.getLogger(__name__)


class TuningMethod(str, Enum):
    """调优方法"""
    BAYESIAN_OPTIMIZATION = "bayesian_optimization"    # 贝叶斯优化
    REINFORCEMENT_LEARNING = "reinforcement_learning"  # 强化学习
    GRADIENT_FREE_OPTIMIZATION = "gradient_free"       # 无梯度优化
    RULE_BASED = "rule_based"                          # 基于规则
    HYBRID = "hybrid"                                  # 混合方法


class TuningConstraint(str, Enum):
    """调优约束"""
    PERFORMANCE = "performance"    # 性能约束（不降低成功率/延迟）
    COST = "cost"                  # 成本约束（不超过预算）
    SAFETY = "safety"              # 安全约束（不违反安全规则）
    STABILITY = "stability"        # 稳定性约束（避免剧烈变化）
    COMPOSITE = "composite"        # 复合约束


@dataclass
class ParameterRange:
    """参数范围定义"""
    parameter_name: str            # 参数名称
    min_value: float              # 最小值
    max_value: float              # 最大值
    default_value: float          # 默认值
    step_size: float = 0.01       # 步长
    is_discrete: bool = False     # 是否离散值
    discrete_values: List[float] = field(default_factory=list)  # 离散值列表
    description: str = ""         # 参数描述
    
    def sample_random(self) -> float:
        """随机采样参数值"""
        if self.is_discrete and self.discrete_values:
            return random.choice(self.discrete_values)
        return random.uniform(self.min_value, self.max_value)
    
    def normalize(self, value: float) -> float:
        """归一化参数值到[0,1]范围"""
        if self.is_discrete and self.discrete_values:
            if not self.discrete_values:
                return 0.0
            idx = self.discrete_values.index(value) if value in self.discrete_values else 0
            return idx / (len(self.discrete_values) - 1) if len(self.discrete_values) > 1 else 0.0
        return (value - self.min_value) / (self.max_value - self.min_value)
    
    def denormalize(self, normalized_value: float) -> float:
        """反归一化参数值"""
        normalized_value = max(0.0, min(1.0, normalized_value))
        if self.is_discrete and self.discrete_values:
            if not self.discrete_values:
                return self.default_value
            idx = int(normalized_value * (len(self.discrete_values) - 1))
            return self.discrete_values[idx]
        return self.min_value + normalized_value * (self.max_value - self.min_value)


@dataclass
class TuningObjective:
    """调优目标"""
    name: str                      # 目标名称
    weight: float = 1.0           # 权重
    maximize: bool = True         # 是否最大化
    threshold: Optional[float] = None  # 阈值（如最小成功率）
    importance: str = "high"      # 重要性（high/medium/low）


@dataclass
class TuningConstraintConfig:
    """调优约束配置"""
    constraint_type: TuningConstraint
    max_value: Optional[float] = None
    min_value: Optional[float] = None
    weight: float = 1.0
    description: str = ""


@dataclass
class TuningConfig:
    """调优配置"""
    # 调优参数
    tuning_method: TuningMethod = TuningMethod.HYBRID
    tuning_interval_hours: int = 24  # 调优间隔（小时）
    exploration_rate: float = 0.3    # 探索率（尝试新参数的概率）
    
    # 目标函数
    objectives: List[TuningObjective] = field(default_factory=lambda: [
        TuningObjective(name="success_rate", weight=0.6, maximize=True, threshold=0.95),
        TuningObjective(name="response_time_ms", weight=0.2, maximize=False, threshold=1000.0),
        TuningObjective(name="cost_per_request", weight=0.2, maximize=False)
    ])
    
    # 约束
    constraints: List[TuningConstraintConfig] = field(default_factory=lambda: [
        TuningConstraintConfig(
            constraint_type=TuningConstraint.PERFORMANCE,
            min_value=0.9,  # 最低成功率90%
            description="保证服务质量"
        ),
        TuningConstraintConfig(
            constraint_type=TuningConstraint.COST,
            max_value=0.02,  # 最高每请求成本$0.02
            description="控制成本"
        )
    ])
    
    # 安全设置
    max_parameter_change: float = 0.2  # 单次最大参数变化
    warmup_requests: int = 100         # 预热请求数
    validation_ratio: float = 0.2      # 验证集比例
    enable_rollback: bool = True       # 启用回滚


@dataclass
class ParameterEvaluation:
    """参数评估结果"""
    parameters: Dict[str, float]       # 参数值
    metrics: Dict[str, float]          # 性能指标
    score: float                       # 综合评分
    timestamp: datetime                # 评估时间
    sample_count: int = 0              # 样本数量
    constraint_violations: List[str] = field(default_factory=list)  # 约束违反列表


@dataclass
class TuningHistoryEntry:
    """调优历史记录"""
    tuning_id: str
    timestamp: datetime
    old_parameters: Dict[str, float]
    new_parameters: Dict[str, float]
    expected_improvement: float
    actual_improvement: Optional[float] = None
    metrics_before: Optional[Dict[str, float]] = None
    metrics_after: Optional[Dict[str, float]] = None
    success: bool = False
    notes: str = ""


class AdaptiveTuningService:
    """自适应调优服务"""
    
    def __init__(
        self,
        ab_testing_router: Optional[ABTestingRouter] = None,
        ab_testing_service: Optional[ABTestingService] = None,
        config_service: Optional[MultiModelConfigService] = None,
        monitoring_service: Optional[MonitoringDashboardService] = None,
        tuning_config: Optional[TuningConfig] = None,
        storage_path: str = "data/adaptive_tuning"
    ):
        """
        初始化自适应调优服务
        
        Args:
            ab_testing_router: AB测试路由器
            ab_testing_service: A/B测试服务
            config_service: 配置服务
            monitoring_service: 监控服务
            tuning_config: 调优配置
            storage_path: 存储路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化服务
        self.router = ab_testing_router
        self.ab_testing = ab_testing_service or get_ab_testing_service()
        self.config_service = config_service or get_multi_model_config_service()
        self.monitoring = monitoring_service or get_monitoring_dashboard_service()
        
        # 配置
        self.config = tuning_config or TuningConfig()
        
        # 参数空间定义（路由策略参数）
        self.parameter_ranges: Dict[str, ParameterRange] = self._define_parameter_ranges()
        
        # 调优状态
        self.current_parameters: Dict[str, float] = self._load_current_parameters()
        self.evaluation_history: List[ParameterEvaluation] = []
        self.tuning_history: List[TuningHistoryEntry] = []
        self.active_tuning_id: Optional[str] = None
        
        # ML框架
        self.ml_system: Optional[ContinuousLearningSystem] = None
        self.data_pipeline: Optional[DataCollectionPipeline] = None
        
        # 锁
        self.lock = threading.RLock()
        
        # 初始化ML框架
        if ML_FRAMEWORK_AVAILABLE:
            try:
                self.ml_system = ContinuousLearningSystem()
                self.data_pipeline = DataCollectionPipeline()
                logger.info("ML框架初始化成功")
            except Exception as e:
                logger.error(f"ML框架初始化失败: {e}")
        
        # 加载历史数据
        self._load_history_data()
        
        logger.info(f"自适应调优服务初始化完成，存储路径: {storage_path}")
        logger.info(f"当前参数: {self.current_parameters}")
    
    def _define_parameter_ranges(self) -> Dict[str, ParameterRange]:
        """定义参数范围"""
        return {
            "exploration_rate": ParameterRange(
                parameter_name="exploration_rate",
                min_value=0.01,
                max_value=0.5,
                default_value=0.1,
                step_size=0.01,
                description="探索率：尝试新策略的概率"
            ),
            "cost_weight": ParameterRange(
                parameter_name="cost_weight",
                min_value=0.0,
                max_value=1.0,
                default_value=0.5,
                step_size=0.05,
                description="成本权重：在混合策略中成本的权重"
            ),
            "performance_weight": ParameterRange(
                parameter_name="performance_weight",
                min_value=0.0,
                max_value=1.0,
                default_value=0.5,
                step_size=0.05,
                description="性能权重：在混合策略中性能的权重"
            ),
            "success_rate_threshold": ParameterRange(
                parameter_name="success_rate_threshold",
                min_value=0.8,
                max_value=0.99,
                default_value=0.95,
                step_size=0.01,
                description="成功率阈值：低于此值触发故障转移"
            ),
            "latency_threshold_ms": ParameterRange(
                parameter_name="latency_threshold_ms",
                min_value=500,
                max_value=5000,
                default_value=2000,
                step_size=100,
                description="延迟阈值：超过此值触发故障转移"
            )
        }
    
    def _load_current_parameters(self) -> Dict[str, float]:
        """加载当前参数"""
        # 从配置文件或使用默认值
        try:
            cost_config = self.config_service.get_cost_optimization_config()
            if hasattr(cost_config, 'enable_auto_tuning') and cost_config.enable_auto_tuning:
                # 如果有保存的调优参数，加载它们
                param_file = self.storage_path / "current_parameters.json"
                if param_file.exists():
                    with open(param_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except Exception as e:
            logger.warning(f"加载当前参数失败: {e}")
        
        # 返回默认值
        return {name: param_range.default_value for name, param_range in self.parameter_ranges.items()}
    
    def _load_history_data(self) -> None:
        """加载历史数据"""
        try:
            # 加载评估历史
            eval_file = self.storage_path / "evaluation_history.json"
            if eval_file.exists():
                with open(eval_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        if "timestamp" in entry:
                            entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                        self.evaluation_history.append(ParameterEvaluation(**entry))
            
            # 加载调优历史
            tuning_file = self.storage_path / "tuning_history.json"
            if tuning_file.exists():
                with open(tuning_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data:
                        if "timestamp" in entry:
                            entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                        self.tuning_history.append(TuningHistoryEntry(**entry))
            
            logger.info(f"加载历史数据：{len(self.evaluation_history)} 个评估，{len(self.tuning_history)} 次调优")
            
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
    
    def _save_history_data(self) -> None:
        """保存历史数据"""
        try:
            # 保存评估历史
            eval_data = []
            for entry in self.evaluation_history:
                entry_dict = {
                    "parameters": entry.parameters,
                    "metrics": entry.metrics,
                    "score": entry.score,
                    "timestamp": entry.timestamp.isoformat(),
                    "sample_count": entry.sample_count,
                    "constraint_violations": entry.constraint_violations
                }
                eval_data.append(entry_dict)
            
            with open(self.storage_path / "evaluation_history.json", 'w', encoding='utf-8') as f:
                json.dump(eval_data, f, ensure_ascii=False, indent=2)
            
            # 保存调优历史
            tuning_data = []
            for entry in self.tuning_history:
                entry_dict = {
                    "tuning_id": entry.tuning_id,
                    "timestamp": entry.timestamp.isoformat(),
                    "old_parameters": entry.old_parameters,
                    "new_parameters": entry.new_parameters,
                    "expected_improvement": entry.expected_improvement,
                    "actual_improvement": entry.actual_improvement,
                    "metrics_before": entry.metrics_before,
                    "metrics_after": entry.metrics_after,
                    "success": entry.success,
                    "notes": entry.notes
                }
                tuning_data.append(entry_dict)
            
            with open(self.storage_path / "tuning_history.json", 'w', encoding='utf-8') as f:
                json.dump(tuning_data, f, ensure_ascii=False, indent=2)
            
            # 保存当前参数
            with open(self.storage_path / "current_parameters.json", 'w', encoding='utf-8') as f:
                json.dump(self.current_parameters, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存历史数据失败: {e}")
    
    def collect_experiment_data(self, experiment_ids: List[str]) -> List[ParameterEvaluation]:
        """
        收集实验数据
        
        Args:
            experiment_ids: 实验ID列表
            
        Returns:
            参数评估结果列表
        """
        evaluations = []
        
        for exp_id in experiment_ids:
            try:
                # 获取实验结果
                result = self.ab_testing.get_experiment_result(exp_id)
                if not result:
                    continue
                
                # 分析每个变体的结果
                for variant_id, variant_result in result.variant_results.items():
                    # 提取参数和指标
                    parameters = self._extract_parameters_from_variant(variant_result.variant_config)
                    metrics = self._extract_metrics_from_variant(variant_result)
                    
                    if parameters and metrics:
                        # 计算综合评分
                        score = self._calculate_composite_score(parameters, metrics)
                        
                        # 检查约束违反
                        violations = self._check_constraints(parameters, metrics)
                        
                        evaluation = ParameterEvaluation(
                            parameters=parameters,
                            metrics=metrics,
                            score=score,
                            timestamp=datetime.now(),
                            sample_count=variant_result.sample_count,
                            constraint_violations=violations
                        )
                        
                        evaluations.append(evaluation)
                        
                        logger.debug(f"收集实验数据: 实验 {exp_id}, 变体 {variant_id}, 评分 {score:.3f}")
                        
            except Exception as e:
                logger.error(f"收集实验数据失败: {exp_id}, 错误: {e}")
        
        # 保存新数据
        self.evaluation_history.extend(evaluations)
        self._save_history_data()
        
        logger.info(f"收集了 {len(evaluations)} 个参数评估")
        return evaluations
    
    def _extract_parameters_from_variant(self, variant_config: Dict[str, Any]) -> Dict[str, float]:
        """从变体配置中提取参数"""
        parameters = {}
        
        # 从策略参数中提取
        if "parameters" in variant_config:
            for param_name, param_value in variant_config["parameters"].items():
                if param_name in self.parameter_ranges:
                    try:
                        parameters[param_name] = float(param_value)
                    except (ValueError, TypeError):
                        pass
        
        return parameters
    
    def _extract_metrics_from_variant(self, variant_result: Any) -> Dict[str, float]:
        """从变体结果中提取指标"""
        metrics = {}
        
        # 主要指标
        if hasattr(variant_result, 'primary_metric_value'):
            metrics["primary_metric"] = variant_result.primary_metric_value
        
        # 辅助指标
        if hasattr(variant_result, 'secondary_metrics'):
            for metric_name, metric_value in variant_result.secondary_metrics.items():
                metrics[metric_name] = metric_value
        
        return metrics
    
    def _calculate_composite_score(self, parameters: Dict[str, float], metrics: Dict[str, float]) -> float:
        """计算综合评分"""
        total_score = 0.0
        total_weight = 0.0
        
        for objective in self.config.objectives:
            if objective.name in metrics:
                metric_value = metrics[objective.name]
                
                # 归一化指标值
                normalized_value = self._normalize_metric(objective.name, metric_value)
                
                # 应用方向（最大化或最小化）
                if not objective.maximize:
                    normalized_value = 1.0 - normalized_value
                
                # 加权求和
                total_score += normalized_value * objective.weight
                total_weight += objective.weight
        
        # 如果有阈值约束，应用惩罚
        for objective in self.config.objectives:
            if objective.threshold is not None and objective.name in metrics:
                metric_value = metrics[objective.name]
                if objective.maximize and metric_value < objective.threshold:
                    # 低于阈值，应用惩罚
                    penalty = (objective.threshold - metric_value) / objective.threshold
                    total_score -= penalty * objective.weight * 2  # 加倍惩罚
                elif not objective.maximize and metric_value > objective.threshold:
                    # 高于阈值，应用惩罚
                    penalty = (metric_value - objective.threshold) / metric_value
                    total_score -= penalty * objective.weight * 2
        
        if total_weight > 0:
            return total_score / total_weight
        return 0.0
    
    def _normalize_metric(self, metric_name: str, value: float) -> float:
        """归一化指标值到[0,1]范围"""
        # 定义各指标的合理范围
        ranges = {
            "success_rate": (0.0, 1.0),
            "response_time_ms": (0.0, 5000.0),
            "cost_per_request": (0.0, 0.1),
            "user_satisfaction": (1.0, 5.0)
        }
        
        if metric_name in ranges:
            min_val, max_val = ranges[metric_name]
            if max_val > min_val:
                normalized = (value - min_val) / (max_val - min_val)
                return max(0.0, min(1.0, normalized))
        
        # 默认归一化：使用sigmoid函数
        return 1.0 / (1.0 + math.exp(-value / 1000))
    
    def _check_constraints(self, parameters: Dict[str, float], metrics: Dict[str, float]) -> List[str]:
        """检查约束违反"""
        violations = []
        
        for constraint in self.config.constraints:
            if constraint.constraint_type == TuningConstraint.PERFORMANCE:
                if "success_rate" in metrics and constraint.min_value is not None:
                    if metrics["success_rate"] < constraint.min_value:
                        violations.append(f"性能约束违反: 成功率 {metrics['success_rate']:.3f} < {constraint.min_value}")
            
            elif constraint.constraint_type == TuningConstraint.COST:
                if "cost_per_request" in metrics and constraint.max_value is not None:
                    if metrics["cost_per_request"] > constraint.max_value:
                        violations.append(f"成本约束违反: 成本 {metrics['cost_per_request']:.3f} > {constraint.max_value}")
        
        return violations
    
    def suggest_parameters(self, method: Optional[TuningMethod] = None) -> Dict[str, float]:
        """
        建议新参数
        
        Args:
            method: 调优方法，如果为None使用配置中的方法
            
        Returns:
            建议的参数值
        """
        method = method or self.config.tuning_method
        
        with self.lock:
            if method == TuningMethod.BAYESIAN_OPTIMIZATION and ML_FRAMEWORK_AVAILABLE:
                return self._suggest_with_bayesian_optimization()
            elif method == TuningMethod.REINFORCEMENT_LEARNING and ML_FRAMEWORK_AVAILABLE:
                return self._suggest_with_reinforcement_learning()
            elif method == TuningMethod.GRADIENT_FREE_OPTIMIZATION:
                return self._suggest_with_gradient_free()
            elif method == TuningMethod.RULE_BASED:
                return self._suggest_with_rules()
            else:  # 默认使用混合方法
                return self._suggest_with_hybrid()
    
    def _suggest_with_hybrid(self) -> Dict[str, float]:
        """使用混合方法建议参数"""
        # 80%的概率使用改进的现有参数，20%的概率探索新参数
        if random.random() < 0.8 and self.evaluation_history:
            # 基于历史数据改进
            return self._improve_existing_parameters()
        else:
            # 探索新参数
            return self._explore_new_parameters()
    
    def _improve_existing_parameters(self) -> Dict[str, float]:
        """改进现有参数"""
        # 找到历史中评分最高的参数
        best_eval = None
        for eval_entry in self.evaluation_history:
            if not eval_entry.constraint_violations:  # 无约束违反
                if best_eval is None or eval_entry.score > best_eval.score:
                    best_eval = eval_entry
        
        if best_eval:
            # 在最佳参数附近进行小幅度扰动
            new_params = {}
            for param_name, param_value in best_eval.parameters.items():
                if param_name in self.parameter_ranges:
                    param_range = self.parameter_ranges[param_name]
                    # 随机扰动，幅度受max_parameter_change限制
                    perturbation = random.uniform(-self.config.max_parameter_change, 
                                                   self.config.max_parameter_change)
                    new_value = param_value * (1 + perturbation)
                    # 确保在范围内
                    new_value = max(param_range.min_value, min(param_range.max_value, new_value))
                    new_params[param_name] = new_value
            
            logger.info(f"基于历史最佳参数改进: {best_eval.score:.3f}")
            return new_params
        
        # 如果没有历史数据，使用当前参数并小幅扰动
        return self._perturb_current_parameters()
    
    def _explore_new_parameters(self) -> Dict[str, float]:
        """探索新参数"""
        new_params = {}
        
        for param_name, param_range in self.parameter_ranges.items():
            # 使用不同的探索策略
            strategy = random.choice(["random", "boundary", "opposite"])
            
            if strategy == "random":
                # 完全随机
                new_value = param_range.sample_random()
            elif strategy == "boundary":
                # 探索边界值
                new_value = random.choice([param_range.min_value, param_range.max_value])
            elif strategy == "opposite":
                # 探索与当前值相反的方向
                current = self.current_parameters.get(param_name, param_range.default_value)
                if param_range.is_discrete and param_range.discrete_values:
                    # 离散值：选择不同的值
                    other_values = [v for v in param_range.discrete_values if v != current]
                    new_value = random.choice(other_values) if other_values else current
                else:
                    # 连续值：向相反方向移动
                    mid = (param_range.min_value + param_range.max_value) / 2
                    if current < mid:
                        new_value = random.uniform(mid, param_range.max_value)
                    else:
                        new_value = random.uniform(param_range.min_value, mid)
            else:
                new_value = param_range.default_value
            
            new_params[param_name] = new_value
        
        logger.info("探索新参数空间")
        return new_params
    
    def _perturb_current_parameters(self) -> Dict[str, float]:
        """扰动当前参数"""
        new_params = {}
        
        for param_name, current_value in self.current_parameters.items():
            if param_name in self.parameter_ranges:
                param_range = self.parameter_ranges[param_name]
                # 小幅度随机扰动
                perturbation = random.uniform(-0.1, 0.1)  # ±10%
                new_value = current_value * (1 + perturbation)
                # 确保在范围内
                new_value = max(param_range.min_value, min(param_range.max_value, new_value))
                new_params[param_name] = new_value
        
        return new_params
    
    def _suggest_with_bayesian_optimization(self) -> Dict[str, float]:
        """使用贝叶斯优化建议参数"""
        # 简化实现：实际中应使用GPyOpt、scikit-optimize等库
        logger.warning("贝叶斯优化简化实现，使用混合方法代替")
        return self._suggest_with_hybrid()
    
    def _suggest_with_reinforcement_learning(self) -> Dict[str, float]:
        """使用强化学习建议参数"""
        # 简化实现
        logger.warning("强化学习简化实现，使用混合方法代替")
        return self._suggest_with_hybrid()
    
    def _suggest_with_gradient_free(self) -> Dict[str, float]:
        """使用无梯度优化建议参数"""
        # 简化实现：使用随机搜索
        if len(self.evaluation_history) < 10:
            # 数据不足，使用随机搜索
            new_params = {}
            for param_name, param_range in self.parameter_ranges.items():
                new_params[param_name] = param_range.sample_random()
            return new_params
        else:
            # 使用简单爬山算法
            return self._improve_existing_parameters()
    
    def _suggest_with_rules(self) -> Dict[str, float]:
        """使用基于规则的方法建议参数"""
        new_params = self.current_parameters.copy()
        
        # 基于性能指标的规则
        recent_perf = self._get_recent_performance()
        
        if recent_perf and "success_rate" in recent_perf:
            success_rate = recent_perf["success_rate"]
            
            # 规则1：如果成功率低，增加探索率
            if success_rate < 0.9 and "exploration_rate" in new_params:
                new_params["exploration_rate"] = min(
                    new_params["exploration_rate"] * 1.2,
                    self.parameter_ranges["exploration_rate"].max_value
                )
            
            # 规则2：如果成功率高但成本高，增加成本权重
            if success_rate > 0.95 and "cost_per_request" in recent_perf:
                cost = recent_perf["cost_per_request"]
                if cost > 0.015:  # 成本较高
                    if "cost_weight" in new_params:
                        new_params["cost_weight"] = min(
                            new_params["cost_weight"] + 0.1,
                            self.parameter_ranges["cost_weight"].max_value
                        )
        
        logger.info("使用基于规则的方法调整参数")
        return new_params
    
    def _get_recent_performance(self) -> Optional[Dict[str, float]]:
        """获取最近性能指标"""
        if not self.evaluation_history:
            return None
        
        # 取最近10个评估的平均值
        recent_evaluations = self.evaluation_history[-10:] if len(self.evaluation_history) > 10 else self.evaluation_history
        
        avg_metrics = defaultdict(float)
        total_weight = 0
        
        for i, eval_entry in enumerate(recent_evaluations):
            weight = 1.0 / (len(recent_evaluations) - i)  # 越近的权重越高
            for metric_name, metric_value in eval_entry.metrics.items():
                avg_metrics[metric_name] += metric_value * weight
            total_weight += weight
        
        if total_weight > 0:
            for metric_name in avg_metrics:
                avg_metrics[metric_name] /= total_weight
        
        return dict(avg_metrics)
    
    def evaluate_parameters(self, parameters: Dict[str, float], 
                           sample_count: int = 100) -> ParameterEvaluation:
        """
        评估参数性能（模拟或通过快速实验）
        
        Args:
            parameters: 要评估的参数
            sample_count: 样本数量
            
        Returns:
            参数评估结果
        """
        # 在实际系统中，这会通过快速A/B测试或模拟完成
        # 这里我们使用简化模拟
        
        # 模拟性能指标
        metrics = {}
        
        # 基础成功率受探索率影响
        base_success_rate = 0.95
        exploration_rate = parameters.get("exploration_rate", 0.1)
        metrics["success_rate"] = base_success_rate * (1 - exploration_rate * 0.3)
        
        # 延迟受性能权重影响
        base_latency = 800.0
        performance_weight = parameters.get("performance_weight", 0.5)
        metrics["response_time_ms"] = base_latency * (1 - performance_weight * 0.2)
        
        # 成本受成本权重影响
        base_cost = 0.01
        cost_weight = parameters.get("cost_weight", 0.5)
        metrics["cost_per_request"] = base_cost * (1 - cost_weight * 0.3)
        
        # 用户满意度
        metrics["user_satisfaction"] = 4.0 + random.uniform(-0.5, 0.5)
        
        # 计算评分
        score = self._calculate_composite_score(parameters, metrics)
        
        # 检查约束
        violations = self._check_constraints(parameters, metrics)
        
        evaluation = ParameterEvaluation(
            parameters=parameters,
            metrics=metrics,
            score=score,
            timestamp=datetime.now(),
            sample_count=sample_count,
            constraint_violations=violations
        )
        
        # 保存评估结果
        self.evaluation_history.append(evaluation)
        self._save_history_data()
        
        logger.info(f"参数评估完成: 评分 {score:.3f}, 约束违反 {len(violations)} 个")
        return evaluation
    
    def apply_parameters(self, parameters: Dict[str, float], 
                        tuning_id: Optional[str] = None) -> bool:
        """
        应用新参数
        
        Args:
            parameters: 新参数
            tuning_id: 调优ID
            
        Returns:
            是否成功应用
        """
        if not tuning_id:
            tuning_id = f"tuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        with self.lock:
            # 记录调优前状态
            old_parameters = self.current_parameters.copy()
            metrics_before = self._get_recent_performance()
            
            # 验证参数
            if not self._validate_parameters(parameters):
                logger.error(f"参数验证失败: {parameters}")
                
                # 记录验证失败历史
                tuning_entry = TuningHistoryEntry(
                    tuning_id=tuning_id,
                    timestamp=datetime.now(),
                    old_parameters=old_parameters,
                    new_parameters=parameters.copy(),
                    expected_improvement=0.0,
                    metrics_before=metrics_before,
                    success=False,
                    notes="参数验证失败"
                )
                self.tuning_history.append(tuning_entry)
                
                return False
            
            # 检查参数变化是否过大
            if not self._check_parameter_change_safety(old_parameters, parameters):
                logger.warning(f"参数变化过大，拒绝应用: {tuning_id}")
                
                # 记录安全检查失败历史
                expected_improvement = self._estimate_improvement(old_parameters, parameters)
                tuning_entry = TuningHistoryEntry(
                    tuning_id=tuning_id,
                    timestamp=datetime.now(),
                    old_parameters=old_parameters,
                    new_parameters=parameters.copy(),
                    expected_improvement=expected_improvement,
                    metrics_before=metrics_before,
                    success=False,
                    notes="参数变化过大，拒绝应用"
                )
                self.tuning_history.append(tuning_entry)
                
                return False
            
            # 记录预期改进（基于历史数据估计）
            expected_improvement = self._estimate_improvement(old_parameters, parameters)
            
            # 应用新参数
            try:
                # 更新当前参数
                self.current_parameters.update(parameters)
                
                # 更新路由器的策略参数
                if self.router:
                    self._update_router_parameters(parameters)
                
                # 保存参数
                self._save_history_data()
                
                # 记录调优历史
                tuning_entry = TuningHistoryEntry(
                    tuning_id=tuning_id,
                    timestamp=datetime.now(),
                    old_parameters=old_parameters,
                    new_parameters=parameters.copy(),
                    expected_improvement=expected_improvement,
                    metrics_before=metrics_before,
                    success=True,
                    notes="参数已应用"
                )
                
                self.tuning_history.append(tuning_entry)
                self.active_tuning_id = tuning_id
                
                # 通知监控系统
                if self.monitoring:
                    self.monitoring.record_event(
                        event_type="parameter_tuning",
                        event_data={
                            "tuning_id": tuning_id,
                            "old_parameters": old_parameters,
                            "new_parameters": parameters,
                            "expected_improvement": expected_improvement
                        }
                    )
                
                logger.info(f"参数应用成功: {tuning_id}, 预期改进: {expected_improvement:.3f}")
                return True
                
            except Exception as e:
                logger.error(f"应用参数失败: {tuning_id}, 错误: {e}")
                
                # 记录失败
                tuning_entry = TuningHistoryEntry(
                    tuning_id=tuning_id,
                    timestamp=datetime.now(),
                    old_parameters=old_parameters,
                    new_parameters=parameters.copy(),
                    expected_improvement=expected_improvement,
                    success=False,
                    notes=f"应用失败: {str(e)}"
                )
                self.tuning_history.append(tuning_entry)
                
                return False
    
    def _validate_parameters(self, parameters: Dict[str, float]) -> bool:
        """验证参数是否有效"""
        for param_name, param_value in parameters.items():
            if param_name not in self.parameter_ranges:
                logger.warning(f"未知参数: {param_name}")
                return False
            
            param_range = self.parameter_ranges[param_name]
            
            # 检查是否在范围内
            if param_value < param_range.min_value or param_value > param_range.max_value:
                logger.warning(f"参数超出范围: {param_name}={param_value}, 范围: [{param_range.min_value}, {param_range.max_value}]")
                return False
            
            # 如果是离散值，检查是否是允许的值
            if param_range.is_discrete and param_range.discrete_values:
                if param_value not in param_range.discrete_values:
                    logger.warning(f"参数不是允许的离散值: {param_name}={param_value}, 允许值: {param_range.discrete_values}")
                    return False
        
        return True
    
    def _check_parameter_change_safety(self, old_params: Dict[str, float], new_params: Dict[str, float]) -> bool:
        """检查参数变化是否安全"""
        max_change = self.config.max_parameter_change
        
        # 只检查新参数中指定的参数
        for param_name in new_params.keys():
            if param_name in self.parameter_ranges:
                old_value = old_params.get(param_name)
                new_value = new_params[param_name]
                
                # 如果旧参数中没有这个参数，视为新增参数（从默认值开始）
                if old_value is None:
                    param_range = self.parameter_ranges[param_name]
                    old_value = param_range.default_value
                
                param_range = self.parameter_ranges[param_name]
                
                # 计算相对变化（对于非零值）
                if old_value != 0:
                    relative_change = abs(new_value - old_value) / abs(old_value)
                else:
                    relative_change = abs(new_value)
                
                if relative_change > max_change:
                    logger.warning(f"参数变化过大: {param_name} {old_value:.3f} -> {new_value:.3f} ({relative_change:.1%}) > {max_change:.1%}")
                    return False
        
        return True
    
    def _estimate_improvement(self, old_params: Dict[str, float], new_params: Dict[str, float]) -> float:
        """估计参数改进"""
        # 基于历史数据的简单估计
        if not self.evaluation_history:
            return 0.0
        
        # 找到与旧参数最相似的历史评估
        best_match = None
        best_distance = float('inf')
        
        for eval_entry in self.evaluation_history:
            if not eval_entry.constraint_violations:
                distance = self._calculate_parameter_distance(old_params, eval_entry.parameters)
                if distance < best_distance:
                    best_distance = distance
                    best_match = eval_entry
        
        if not best_match:
            return 0.0
        
        # 基于距离加权估计
        base_score = best_match.score
        estimated_score = base_score * (1.0 + random.uniform(-0.1, 0.1))  # ±10%随机
        
        return estimated_score - base_score  # 改进量
    
    def _calculate_parameter_distance(self, params1: Dict[str, float], params2: Dict[str, float]) -> float:
        """计算参数距离"""
        distance = 0.0
        param_count = 0
        
        all_param_names = set(params1.keys()) | set(params2.keys())
        
        for param_name in all_param_names:
            if param_name in self.parameter_ranges:
                val1 = params1.get(param_name, 0.0)
                val2 = params2.get(param_name, 0.0)
                param_range = self.parameter_ranges[param_name]
                
                # 归一化后计算欧氏距离
                norm_val1 = param_range.normalize(val1)
                norm_val2 = param_range.normalize(val2)
                
                distance += (norm_val1 - norm_val2) ** 2
                param_count += 1
        
        if param_count > 0:
            return math.sqrt(distance / param_count)
        return 0.0
    
    def _update_router_parameters(self, parameters: Dict[str, float]) -> None:
        """更新路由器参数"""
        if not self.router:
            return
        
        # 更新路由器的策略配置
        for strategy_name, strategy_config in self.router.strategies.items():
            # 更新策略参数
            for param_name, param_value in parameters.items():
                if param_name in strategy_config.parameters:
                    strategy_config.parameters[param_name] = param_value
        
        logger.info(f"路由器参数已更新: {len(parameters)} 个参数")
    
    def auto_tune(self) -> Optional[str]:
        """
        自动调优
        
        Returns:
            调优ID，如果未执行调优则返回None
        """
        # 检查是否应该执行调优
        if not self._should_tune():
            logger.debug("跳过调优：未达到调优条件")
            return None
        
        # 收集最近的实验数据
        recent_experiments = self._get_recent_experiments()
        if not recent_experiments:
            logger.warning("没有可用的实验数据，跳过调优")
            return None
        
        # 收集和分析数据
        evaluations = self.collect_experiment_data(recent_experiments)
        if len(evaluations) < 5:  # 需要足够的数据
            logger.warning(f"数据不足 ({len(evaluations)} 个评估)，跳过调优")
            return None
        
        # 建议新参数
        suggested_params = self.suggest_parameters()
        
        # 评估建议的参数
        evaluation = self.evaluate_parameters(suggested_params, sample_count=50)
        
        # 检查是否满足约束
        if evaluation.constraint_violations:
            logger.warning(f"建议的参数违反约束: {evaluation.constraint_violations}")
            return None
        
        # 检查是否有改进
        current_perf = self._get_recent_performance()
        if current_perf and "primary_metric" in current_perf:
            current_score = current_perf.get("primary_metric", 0.0)
            improvement = evaluation.score - current_score
            
            if improvement < 0.01:  # 改进太小
                logger.info(f"改进太小 ({improvement:.3f})，跳过应用")
                return None
        
        # 应用新参数
        tuning_id = f"auto_tune_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success = self.apply_parameters(suggested_params, tuning_id)
        
        if success:
            logger.info(f"自动调优完成: {tuning_id}, 参数: {suggested_params}")
            return tuning_id
        else:
            logger.warning(f"自动调优失败: {tuning_id}")
            return None
    
    def _should_tune(self) -> bool:
        """检查是否应该执行调优"""
        # 检查配置是否启用自动调优
        try:
            cost_config = self.config_service.get_cost_optimization_config()
            if hasattr(cost_config, 'enable_auto_tuning') and not cost_config.enable_auto_tuning:
                return False
        except Exception:
            pass
        
        # 检查调优间隔
        if self.tuning_history:
            last_tuning = self.tuning_history[-1]
            time_since_last = datetime.now() - last_tuning.timestamp
            hours_since_last = time_since_last.total_seconds() / 3600
            
            if hours_since_last < self.config.tuning_interval_hours:
                logger.debug(f"调优间隔不足: {hours_since_last:.1f} 小时 < {self.config.tuning_interval_hours} 小时")
                return False
        
        # 检查是否有足够的数据
        if len(self.evaluation_history) < 10:
            logger.debug("历史数据不足")
            return False
        
        return True
    
    def _get_recent_experiments(self) -> List[str]:
        """获取最近的实验ID"""
        # 从A/B测试服务获取最近的实验
        try:
            all_experiments = self.ab_testing.list_experiments()
            recent_experiments = []
            
            for exp_id, exp_data in all_experiments.items():
                # 只选择最近7天内完成的实验
                if "end_time" in exp_data and exp_data.get("status") == "completed":
                    end_time = datetime.fromisoformat(exp_data["end_time"])
                    days_ago = (datetime.now() - end_time).days
                    if days_ago <= 7:
                        recent_experiments.append(exp_id)
            
            return recent_experiments
            
        except Exception as e:
            logger.error(f"获取实验列表失败: {e}")
            return []
    
    def get_tuning_status(self) -> Dict[str, Any]:
        """获取调优状态"""
        return {
            "current_parameters": self.current_parameters,
            "evaluation_count": len(self.evaluation_history),
            "tuning_count": len(self.tuning_history),
            "last_tuning": self.tuning_history[-1].to_dict() if self.tuning_history else None,
            "active_tuning_id": self.active_tuning_id,
            "config": {
                "tuning_method": self.config.tuning_method.value,
                "tuning_interval_hours": self.config.tuning_interval_hours,
                "exploration_rate": self.config.exploration_rate
            }
        }
    
    def get_recommendations(self) -> List[Dict[str, Any]]:
        """获取调优建议"""
        recommendations = []
        
        # 基于历史数据生成建议
        if self.evaluation_history:
            # 找到最佳参数配置
            best_eval = None
            for eval_entry in self.evaluation_history:
                if not eval_entry.constraint_violations:
                    if best_eval is None or eval_entry.score > best_eval.score:
                        best_eval = eval_entry
            
            if best_eval:
                recommendations.append({
                    "type": "best_parameters",
                    "description": f"历史最佳参数，评分: {best_eval.score:.3f}",
                    "parameters": best_eval.parameters,
                    "confidence": 0.8
                })
        
        # 基于规则的建议
        recent_perf = self._get_recent_performance()
        if recent_perf:
            if "success_rate" in recent_perf and recent_perf["success_rate"] < 0.9:
                recommendations.append({
                    "type": "performance_issue",
                    "description": "成功率偏低，建议增加探索率或调整策略权重",
                    "suggested_changes": {
                        "exploration_rate": "增加0.05-0.10",
                        "performance_weight": "增加0.10-0.15"
                    },
                    "urgency": "high"
                })
            
            if "cost_per_request" in recent_perf and recent_perf["cost_per_request"] > 0.015:
                recommendations.append({
                    "type": "cost_issue",
                    "description": "成本偏高，建议增加成本权重",
                    "suggested_changes": {
                        "cost_weight": "增加0.10-0.15"
                    },
                    "urgency": "medium"
                })
        
        return recommendations


def get_adaptive_tuning_service(
    storage_path: str = "data/adaptive_tuning",
    tuning_config: Optional[TuningConfig] = None
) -> AdaptiveTuningService:
    """
    获取自适应调优服务实例（单例模式）
    
    Args:
        storage_path: 存储路径
        tuning_config: 调优配置
        
    Returns:
        自适应调优服务实例
    """
    if not hasattr(get_adaptive_tuning_service, "_instance"):
        get_adaptive_tuning_service._instance = AdaptiveTuningService(
            storage_path=storage_path,
            tuning_config=tuning_config
        )
    
    return get_adaptive_tuning_service._instance


__all__ = [
    "TuningMethod",
    "TuningConstraint",
    "ParameterRange",
    "TuningObjective",
    "TuningConstraintConfig",
    "TuningConfig",
    "ParameterEvaluation",
    "TuningHistoryEntry",
    "AdaptiveTuningService",
    "get_adaptive_tuning_service"
]