#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AB测试路由器 - 集成A/B测试的多模型路由实验框架

基于现有的智能模型路由器，集成A/B测试服务，支持：
1. 多种路由策略实验（基础策略、随机策略、成本优先、性能优先、混合策略）
2. 自动化实验管理和流量分配
3. 多维度性能指标跟踪和分析
4. 统计显著性检验和自动决策
5. 实验结果持久化和报告生成

与现有系统集成：
- 继承 IntelligentModelRouter，保持兼容性
- 集成 ABTestingService 进行实验管理
- 与监控系统集成，收集详细指标
- 支持多模型配置和成本控制
"""

import time
import random
import logging
import asyncio
import threading
import statistics
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from collections import defaultdict

from .intelligent_model_router import (
    IntelligentModelRouter, 
    TaskType, 
    TaskContext, 
    ModelCapability, 
    ModelStatus, 
    RoutingDecision,
    ModelPerformancePrediction
)
from .ab_testing_service import (
    ABTestingService, 
    ExperimentConfig, 
    VariantType, 
    get_ab_testing_service
)
from .token_cost_monitor import TokenCostMonitor
from .cost_control import CostController

logger = logging.getLogger(__name__)


class RoutingStrategy(str, Enum):
    """路由策略类型"""
    INTELLIGENT = "intelligent"          # 智能路由（基础策略）
    RANDOM = "random"                    # 随机选择
    COST_FIRST = "cost_first"            # 成本优先
    PERFORMANCE_FIRST = "performance_first"  # 性能优先
    HYBRID = "hybrid"                    # 混合策略（成本+性能）
    EXPLORATION = "exploration"          # 探索策略（用于发现新模型）


@dataclass
class StrategyConfig:
    """策略配置"""
    strategy_name: str                    # 策略名称
    strategy_type: RoutingStrategy        # 策略类型
    description: str                      # 策略描述
    parameters: Dict[str, Any] = field(default_factory=dict)  # 策略参数
    weight: float = 1.0                   # 流量权重


@dataclass  
class StrategyPerformance:
    """策略性能统计"""
    strategy_name: str
    sample_count: int = 0
    success_count: int = 0
    total_latency_ms: float = 0.0
    total_cost: float = 0.0
    user_satisfaction_score: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.sample_count == 0:
            return 0.0
        return self.success_count / self.sample_count
    
    @property
    def avg_latency_ms(self) -> float:
        """平均延迟"""
        if self.success_count == 0:
            return 0.0
        return self.total_latency_ms / self.success_count
    
    @property
    def avg_cost_per_request(self) -> float:
        """平均每请求成本"""
        if self.success_count == 0:
            return 0.0
        return self.total_cost / self.success_count


class ABTestingRouter(IntelligentModelRouter):
    """AB测试路由器"""
    
    def __init__(
        self,
        base_router: Optional[IntelligentModelRouter] = None,
        ab_testing_service: Optional[ABTestingService] = None,
        cost_monitor: Optional[TokenCostMonitor] = None,
        cost_controller: Optional[CostController] = None,
        storage_path: str = "data/ab_testing_router"
    ):
        """
        初始化AB测试路由器
        
        Args:
            base_router: 基础路由器实例
            ab_testing_service: A/B测试服务实例
            cost_monitor: Token成本监控服务
            cost_controller: 成本控制服务
            storage_path: 数据存储路径
        """
        # 初始化父类
        if base_router:
            # 复制基础路由器的状态
            self.model_status = base_router.model_status.copy()
            self.model_capabilities = base_router.model_capabilities.copy()
            self.predictor = base_router.predictor
            self.fallback_chains = base_router.fallback_chains.copy()
            self.stats = base_router.stats.copy()
            self.routing_history = base_router.routing_history.copy()
            self.lock = threading.RLock()
        else:
            super().__init__()
        
        self.storage_path = storage_path
        
        # 初始化服务
        self.ab_testing = ab_testing_service or get_ab_testing_service(storage_path)
        self.cost_monitor = cost_monitor
        self.cost_controller = cost_controller
        
        # 策略配置
        self.strategies: Dict[str, StrategyConfig] = {}
        self.strategy_performance: Dict[str, StrategyPerformance] = defaultdict(
            lambda: StrategyPerformance(strategy_name="")
        )
        
        # 实验状态
        self.active_experiments: Dict[str, Dict[str, Any]] = {}
        self.experiment_results: Dict[str, Dict[str, Any]] = {}
        
        # 默认策略
        self._initialize_default_strategies()
        
        logger.info(f"AB测试路由器初始化完成，存储路径: {storage_path}")
    
    def _initialize_default_strategies(self) -> None:
        """初始化默认策略"""
        default_strategies = [
            StrategyConfig(
                strategy_name="intelligent_base",
                strategy_type=RoutingStrategy.INTELLIGENT,
                description="智能路由基础策略，基于性能预测和任务匹配",
                parameters={"exploration_rate": 0.1}
            ),
            StrategyConfig(
                strategy_name="random_baseline",
                strategy_type=RoutingStrategy.RANDOM,
                description="随机选择策略，作为性能基准",
                parameters={"exploration_rate": 1.0}
            ),
            StrategyConfig(
                strategy_name="cost_optimized",
                strategy_type=RoutingStrategy.COST_FIRST,
                description="成本优先策略，优先选择成本最低的模型",
                parameters={"cost_weight": 0.7, "performance_weight": 0.3}
            ),
            StrategyConfig(
                strategy_name="performance_optimized",
                strategy_type=RoutingStrategy.PERFORMANCE_FIRST,
                description="性能优先策略，优先选择延迟最低的模型",
                parameters={"cost_weight": 0.3, "performance_weight": 0.7}
            ),
            StrategyConfig(
                strategy_name="balanced_hybrid",
                strategy_type=RoutingStrategy.HYBRID,
                description="平衡混合策略，综合考虑成本和性能",
                parameters={"cost_weight": 0.5, "performance_weight": 0.5}
            )
        ]
        
        for strategy in default_strategies:
            self.strategies[strategy.strategy_name] = strategy
            self.strategy_performance[strategy.strategy_name] = StrategyPerformance(
                strategy_name=strategy.strategy_name
            )
    
    def add_strategy(self, strategy: StrategyConfig) -> bool:
        """
        添加路由策略
        
        Args:
            strategy: 策略配置
            
        Returns:
            是否成功添加
        """
        if strategy.strategy_name in self.strategies:
            logger.warning(f"策略已存在: {strategy.strategy_name}")
            return False
        
        self.strategies[strategy.strategy_name] = strategy
        self.strategy_performance[strategy.strategy_name] = StrategyPerformance(
            strategy_name=strategy.strategy_name
        )
        
        logger.info(f"添加路由策略: {strategy.strategy_name} ({strategy.strategy_type.value})")
        return True
    
    def create_routing_experiment(
        self, 
        experiment_id: str,
        experiment_name: str,
        strategies_to_test: List[str],
        traffic_percentage: float = 10.0,
        duration_days: int = 7,
        primary_metric: str = "success_rate",
        hypothesis: Optional[str] = None
    ) -> Optional[str]:
        """
        创建路由策略实验
        
        Args:
            experiment_id: 实验ID
            experiment_name: 实验名称
            strategies_to_test: 要测试的策略列表
            traffic_percentage: 流量百分比
            duration_days: 持续时间（天）
            primary_metric: 主要指标
            hypothesis: 实验假设
            
        Returns:
            实验ID，如果创建失败返回None
        """
        # 验证策略
        for strategy_name in strategies_to_test:
            if strategy_name not in self.strategies:
                logger.error(f"策略不存在: {strategy_name}")
                return None
        
        # 准备变体配置
        variants = []
        for strategy_name in strategies_to_test:
            strategy = self.strategies[strategy_name]
            variants.append({
                "strategy_name": strategy_name,
                "strategy_type": strategy.strategy_type.value,
                "parameters": strategy.parameters,
                "description": strategy.description
            })
        
        # 创建实验配置
        config = ExperimentConfig(
            experiment_id=experiment_id,
            name=experiment_name,
            description=f"路由策略实验: {', '.join(strategies_to_test)}",
            variant_type=VariantType.ROUTING_STRATEGY,
            variants=variants,
            traffic_percentage=traffic_percentage,
            duration_days=duration_days,
            min_samples_per_variant=100,
            primary_metric=primary_metric,
            hypothesis=hypothesis or f"比较不同路由策略的性能，寻找最优策略"
        )
        
        try:
            # 创建实验
            exp_id = self.ab_testing.create_experiment(config)
            
            # 记录实验元数据
            self.active_experiments[exp_id] = {
                "experiment_id": exp_id,
                "strategies": strategies_to_test,
                "start_time": datetime.now(),
                "config": config
            }
            
            logger.info(f"创建路由策略实验: {exp_id} ({experiment_name})")
            return exp_id
            
        except Exception as e:
            logger.error(f"创建实验失败: {experiment_id}, 错误: {e}")
            return None
    
    async def route_with_experiment(
        self, 
        task_context: TaskContext,
        experiment_id: str,
        user_id: str
    ) -> Tuple[Optional[RoutingDecision], Optional[str]]:
        """
        使用实验进行路由
        
        Args:
            task_context: 任务上下文
            experiment_id: 实验ID
            user_id: 用户ID
            
        Returns:
            (路由决策, 分配的变体ID) 或 (None, None)
        """
        # 分配实验变体
        variant_info = self.ab_testing.assign_variant(experiment_id, user_id)
        if not variant_info:
            logger.warning(f"无法为实验 {experiment_id} 分配变体")
            return None, None
        
        variant_id = variant_info["variant_id"]
        variant_config = variant_info["variant_config"]
        strategy_name = variant_config["strategy_name"]
        
        # 记录分配
        logger.debug(f"实验 {experiment_id}: 为用户 {user_id} 分配策略 {strategy_name}")
        
        # 使用指定策略进行路由
        start_time = time.perf_counter()
        
        try:
            # 根据策略类型执行路由
            if strategy_name == "random_baseline":
                decision = await self._route_random(task_context)
            elif strategy_name == "cost_optimized":
                decision = await self._route_cost_first(task_context)
            elif strategy_name == "performance_optimized":
                decision = await self._route_performance_first(task_context)
            elif strategy_name == "balanced_hybrid":
                decision = await self._route_hybrid(task_context)
            else:  # 默认使用智能路由
                decision = await super().route(task_context)
            
            end_time = time.perf_counter()
            latency_ms = (end_time - start_time) * 1000
            
            # 记录策略使用
            if strategy_name in self.strategy_performance:
                perf = self.strategy_performance[strategy_name]
                perf.sample_count += 1
                if decision and decision.selected_model:
                    perf.success_count += 1
                    perf.total_latency_ms += latency_ms
                    # 记录成本（如果有成本监控）
                    if self.cost_monitor and hasattr(task_context, 'estimated_tokens'):
                        cost = self.cost_monitor.estimate_cost(
                            task_context.estimated_tokens, 
                            decision.selected_model
                        )
                        perf.total_cost += cost
            
            return decision, variant_id
            
        except Exception as e:
            logger.error(f"实验路由失败: {experiment_id}, 策略 {strategy_name}, 错误: {e}")
            return None, None
    
    async def _route_random(self, task_context: TaskContext) -> RoutingDecision:
        """随机路由策略"""
        # 筛选可用模型
        available_models = self._filter_available_models(task_context)
        
        if not available_models:
            return self._create_error_decision("无可用模型")
        
        # 随机选择
        selected_model = random.choice(available_models)
        
        # 创建预测对象（简化）
        prediction = ModelPerformancePrediction(
            model_name=selected_model,
            predicted_latency_ms=1000.0,  # 默认值
            confidence=0.5,
            availability_probability=0.9,
            recommendation_score=0.5,
            factors=["随机选择策略"]
        )
        
        # 准备备选模型
        alternatives = [m for m in available_models if m != selected_model][:2]
        
        return RoutingDecision(
            selected_model=selected_model,
            alternative_models=alternatives,
            predicted_performance=prediction,
            reasoning=["随机选择策略", f"可用模型: {len(available_models)}个"]
        )
    
    async def _route_cost_first(self, task_context: TaskContext) -> RoutingDecision:
        """成本优先路由策略"""
        if not self.cost_monitor:
            logger.warning("成本监控服务未配置，回退到智能路由")
            return await super().route(task_context)
        
        # 筛选可用模型
        available_models = self._filter_available_models(task_context)
        
        if not available_models:
            return self._create_error_decision("无可用模型")
        
        # 计算每个模型的成本
        model_costs = []
        for model_name in available_models:
            cost = self.cost_monitor.estimate_cost(task_context.estimated_tokens, model_name)
            model_costs.append((model_name, cost))
        
        # 按成本排序（升序）
        model_costs.sort(key=lambda x: x[1])
        
        # 选择成本最低的模型
        selected_model, min_cost = model_costs[0]
        
        # 创建预测对象
        prediction = ModelPerformancePrediction(
            model_name=selected_model,
            predicted_latency_ms=1000.0,  # 成本优先不考虑延迟
            confidence=0.7,
            availability_probability=0.9,
            recommendation_score=0.8,
            factors=["成本优先策略", f"预估成本: ${min_cost:.4f}"]
        )
        
        # 备选模型（次优成本）
        alternatives = [model for model, _ in model_costs[1:3]]
        
        return RoutingDecision(
            selected_model=selected_model,
            alternative_models=alternatives,
            predicted_performance=prediction,
            reasoning=[f"成本优先策略", f"预估成本: ${min_cost:.4f}", f"可用模型: {len(available_models)}个"]
        )
    
    async def _route_performance_first(self, task_context: TaskContext) -> RoutingDecision:
        """性能优先路由策略"""
        # 筛选可用模型
        available_models = self._filter_available_models(task_context)
        
        if not available_models:
            return self._create_error_decision("无可用模型")
        
        # 为每个模型预测性能
        predictions = []
        for model_name in available_models:
            prediction = self.predictor.predict(model_name, task_context)
            predictions.append((model_name, prediction))
        
        # 按推荐分数排序（降序）
        predictions.sort(key=lambda x: x[1].recommendation_score, reverse=True)
        
        # 选择性能最好的模型
        selected_model, best_prediction = predictions[0]
        
        # 备选模型
        alternatives = [model for model, _ in predictions[1:3]]
        
        return RoutingDecision(
            selected_model=selected_model,
            alternative_models=alternatives,
            predicted_performance=best_prediction,
            reasoning=["性能优先策略", f"预测延迟: {best_prediction.predicted_latency_ms:.0f}ms"]
        )
    
    async def _route_hybrid(self, task_context: TaskContext) -> RoutingDecision:
        """混合路由策略（成本+性能）"""
        # 筛选可用模型
        available_models = self._filter_available_models(task_context)
        
        if not available_models:
            return self._create_error_decision("无可用模型")
        
        # 收集成本和性能数据
        model_scores = []
        
        for model_name in available_models:
            # 性能预测
            performance_pred = self.predictor.predict(model_name, task_context)
            
            # 成本估算（如果有成本监控）
            cost = 0.0
            if self.cost_monitor:
                cost = self.cost_monitor.estimate_cost(task_context.estimated_tokens, model_name)
            
            # 归一化分数（假设：性能分数越高越好，成本越低越好）
            perf_score = performance_pred.recommendation_score  # 0-1
            
            # 成本分数（成本越低分数越高）
            # 这里需要成本范围信息，暂时简化处理
            cost_score = 1.0 - min(cost, 1.0)  # 假设成本在0-1之间
            
            # 混合分数（权重可配置）
            hybrid_score = 0.5 * perf_score + 0.5 * cost_score
            
            model_scores.append((model_name, hybrid_score, performance_pred, cost))
        
        # 按混合分数排序
        model_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 选择最佳模型
        selected_model, best_score, best_prediction, best_cost = model_scores[0]
        
        # 备选模型
        alternatives = [model for model, _, _, _ in model_scores[1:3]]
        
        return RoutingDecision(
            selected_model=selected_model,
            alternative_models=alternatives,
            predicted_performance=best_prediction,
            reasoning=[
                "混合策略（成本+性能）", 
                f"综合分数: {best_score:.2f}",
                f"预测延迟: {best_prediction.predicted_latency_ms:.0f}ms",
                f"预估成本: ${best_cost:.4f}" if best_cost > 0 else "成本估算不可用"
            ]
        )
    
    def record_experiment_result(
        self,
        experiment_id: str,
        variant_id: str,
        metrics: Dict[str, float]
    ) -> bool:
        """
        记录实验结果
        
        Args:
            experiment_id: 实验ID
            variant_id: 变体ID
            metrics: 指标数据
            
        Returns:
            是否成功记录
        """
        success = self.ab_testing.record_result(experiment_id, variant_id, metrics)
        
        if success:
            # 同时更新本地性能统计
            if experiment_id in self.active_experiments:
                exp_data = self.active_experiments[experiment_id]
                for strategy_name in exp_data.get("strategies", []):
                    if strategy_name in self.strategy_performance:
                        perf = self.strategy_performance[strategy_name]
                        # 这里可以更新更详细的性能数据
        
        return success
    
    def get_strategy_performance(self, strategy_name: str) -> Optional[StrategyPerformance]:
        """
        获取策略性能统计
        
        Args:
            strategy_name: 策略名称
            
        Returns:
            策略性能统计
        """
        return self.strategy_performance.get(strategy_name)
    
    def get_all_strategies(self) -> List[Dict[str, Any]]:
        """
        获取所有策略信息
        
        Returns:
            策略信息列表
        """
        strategies = []
        for name, config in self.strategies.items():
            perf = self.strategy_performance[name]
            strategies.append({
                "strategy_name": name,
                "strategy_type": config.strategy_type.value,
                "description": config.description,
                "sample_count": perf.sample_count,
                "success_rate": perf.success_rate,
                "avg_latency_ms": perf.avg_latency_ms,
                "avg_cost_per_request": perf.avg_cost_per_request,
                "user_satisfaction_score": perf.user_satisfaction_score
            })
        return strategies
    
    def get_experiment_summary(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        获取实验摘要
        
        Args:
            experiment_id: 实验ID
            
        Returns:
            实验摘要信息
        """
        # 获取A/B测试服务中的实验状态
        status = self.ab_testing.get_experiment_status(experiment_id)
        if not status:
            return None
        
        # 获取实验结果
        result = self.ab_testing.get_experiment_result(experiment_id)
        
        summary = {
            "experiment_id": experiment_id,
            "status": status,
            "result": result.to_dict() if result else None,
            "local_performance": {}
        }
        
        # 添加本地性能统计
        if experiment_id in self.active_experiments:
            exp_data = self.active_experiments[experiment_id]
            for strategy_name in exp_data.get("strategies", []):
                perf = self.strategy_performance.get(strategy_name)
                if perf:
                    summary["local_performance"][strategy_name] = {
                        "sample_count": perf.sample_count,
                        "success_rate": perf.success_rate,
                        "avg_latency_ms": perf.avg_latency_ms,
                        "avg_cost_per_request": perf.avg_cost_per_request
                    }
        
        return summary


def get_ab_testing_router(
    base_router: Optional[IntelligentModelRouter] = None,
    storage_path: str = "data/ab_testing_router"
) -> ABTestingRouter:
    """
    获取AB测试路由器实例（单例模式）
    
    Args:
        base_router: 基础路由器实例
        storage_path: 存储路径
        
    Returns:
        AB测试路由器实例
    """
    if not hasattr(get_ab_testing_router, "_instance"):
        # 获取服务实例
        ab_service = get_ab_testing_service(f"{storage_path}/experiments")
        
        # 创建路由器实例
        get_ab_testing_router._instance = ABTestingRouter(
            base_router=base_router,
            ab_testing_service=ab_service,
            storage_path=storage_path
        )
    
    return get_ab_testing_router._instance


__all__ = [
    "RoutingStrategy",
    "StrategyConfig",
    "StrategyPerformance",
    "ABTestingRouter",
    "get_ab_testing_router"
]