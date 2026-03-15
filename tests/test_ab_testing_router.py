#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AB测试路由器测试

测试AB测试路由器的核心功能：
1. 路由器初始化和策略管理
2. 实验创建和管理
3. 不同路由策略的执行
4. 性能统计和结果记录
5. 集成测试
"""

import os
import sys
import time
import json
import tempfile
import asyncio
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_framework import RANGENTestCase, AsyncTestCase
from src.services.intelligent_model_router import (
    IntelligentModelRouter, 
    TaskType, 
    TaskContext, 
    ModelCapability, 
    ModelStatus
)
from src.services.ab_testing_router import (
    ABTestingRouter,
    RoutingStrategy,
    StrategyConfig,
    StrategyPerformance,
    get_ab_testing_router
)


class TestABTestingRouterInitialization(RANGENTestCase):
    """测试AB测试路由器初始化"""
    
    def test_router_creation_without_base_router(self):
        """测试无基础路由器的创建"""
        router = ABTestingRouter()
        
        self.assertIsInstance(router, ABTestingRouter)
        self.assertIsInstance(router, IntelligentModelRouter)
        self.assertIsNotNone(router.ab_testing)
        self.assertIsNone(router.cost_monitor)
        self.assertIsNone(router.cost_controller)
        self.assertTrue(len(router.strategies) > 0)
    
    def test_router_creation_with_base_router(self):
        """测试有基础路由器的创建"""
        # 创建基础路由器
        base_router = IntelligentModelRouter()
        
        # 配置基础路由器
        base_router.model_status["deepseek-model"] = ModelStatus.HEALTHY
        base_router.model_status["stepflash-model"] = ModelStatus.HEALTHY
        
        capability = ModelCapability(
            model_name="deepseek-model",
            supported_tasks=[TaskType.GENERAL, TaskType.REASONING],
            strengths=["推理", "代码生成"],
            weaknesses=[],  # 添加空弱点列表
            max_tokens=8000
        )
        base_router.model_capabilities["deepseek-model"] = capability
        
        # 创建AB测试路由器
        router = ABTestingRouter(base_router=base_router)
        
        self.assertIsInstance(router, ABTestingRouter)
        self.assertIn("deepseek-model", router.model_status)
        self.assertIn("deepseek-model", router.model_capabilities)
        self.assertEqual(router.model_status["deepseek-model"], ModelStatus.HEALTHY)
    
    def test_default_strategies_initialization(self):
        """测试默认策略初始化"""
        router = ABTestingRouter()
        
        expected_strategy_names = [
            "intelligent_base",
            "random_baseline", 
            "cost_optimized",
            "performance_optimized",
            "balanced_hybrid"
        ]
        
        for strategy_name in expected_strategy_names:
            self.assertIn(strategy_name, router.strategies)
            self.assertIn(strategy_name, router.strategy_performance)
            
            strategy = router.strategies[strategy_name]
            perf = router.strategy_performance[strategy_name]
            
            self.assertEqual(perf.strategy_name, strategy_name)
            self.assertEqual(perf.sample_count, 0)
            self.assertEqual(perf.success_count, 0)


class TestStrategyManagement(RANGENTestCase):
    """测试策略管理功能"""
    
    def setUp(self):
        super().setUp()
        self.router = ABTestingRouter()
    
    def test_add_strategy(self):
        """测试添加新策略"""
        new_strategy = StrategyConfig(
            strategy_name="custom_exploration",
            strategy_type=RoutingStrategy.EXPLORATION,
            description="自定义探索策略",
            parameters={"exploration_rate": 0.3, "exploration_budget": 100},
            weight=0.5
        )
        
        result = self.router.add_strategy(new_strategy)
        
        self.assertTrue(result)
        self.assertIn("custom_exploration", self.router.strategies)
        self.assertIn("custom_exploration", self.router.strategy_performance)
        
        strategy = self.router.strategies["custom_exploration"]
        self.assertEqual(strategy.strategy_type, RoutingStrategy.EXPLORATION)
        self.assertEqual(strategy.description, "自定义探索策略")
    
    def test_add_duplicate_strategy(self):
        """测试添加重复策略"""
        new_strategy = StrategyConfig(
            strategy_name="intelligent_base",  # 已存在的策略名称
            strategy_type=RoutingStrategy.EXPLORATION,
            description="重复策略"
        )
        
        result = self.router.add_strategy(new_strategy)
        
        self.assertFalse(result)
    
    def test_get_all_strategies(self):
        """测试获取所有策略"""
        strategies = self.router.get_all_strategies()
        
        self.assertIsInstance(strategies, list)
        self.assertTrue(len(strategies) >= 5)  # 至少5个默认策略
        
        for strategy_info in strategies:
            self.assertIn("strategy_name", strategy_info)
            self.assertIn("strategy_type", strategy_info)
            self.assertIn("description", strategy_info)
            self.assertIn("sample_count", strategy_info)
            self.assertIn("success_rate", strategy_info)
    
    def test_get_strategy_performance(self):
        """测试获取策略性能"""
        perf = self.router.get_strategy_performance("intelligent_base")
        
        self.assertIsInstance(perf, StrategyPerformance)
        self.assertEqual(perf.strategy_name, "intelligent_base")
        self.assertEqual(perf.sample_count, 0)
        self.assertEqual(perf.success_count, 0)


class TestExperimentManagement(RANGENTestCase):
    """测试实验管理功能"""
    
    def setUp(self):
        super().setUp()
        self.router = ABTestingRouter(storage_path=self.test_data_dir)
    
    def test_create_routing_experiment(self):
        """测试创建路由实验"""
        experiment_id = self.router.create_routing_experiment(
            experiment_id="test_exp_001",
            experiment_name="策略比较实验",
            strategies_to_test=["intelligent_base", "random_baseline", "cost_optimized"],
            traffic_percentage=5.0,
            duration_days=3,
            primary_metric="success_rate",
            hypothesis="测试不同路由策略的性能差异"
        )
        
        self.assertIsNotNone(experiment_id)
        self.assertEqual(experiment_id, "test_exp_001")
        self.assertIn(experiment_id, self.router.active_experiments)
        
        exp_data = self.router.active_experiments[experiment_id]
        self.assertEqual(exp_data["experiment_id"], experiment_id)
        self.assertIn("strategies", exp_data)
        self.assertEqual(len(exp_data["strategies"]), 3)
    
    def test_create_experiment_with_invalid_strategy(self):
        """测试使用无效策略创建实验"""
        experiment_id = self.router.create_routing_experiment(
            experiment_id="test_exp_002",
            experiment_name="无效策略实验",
            strategies_to_test=["intelligent_base", "invalid_strategy"],  # 无效策略
            traffic_percentage=5.0
        )
        
        self.assertIsNone(experiment_id)
    
    def test_get_experiment_summary(self):
        """测试获取实验摘要"""
        # 先创建实验
        experiment_id = self.router.create_routing_experiment(
            experiment_id="test_exp_003",
            experiment_name="摘要测试实验",
            strategies_to_test=["intelligent_base", "random_baseline"],
            traffic_percentage=5.0
        )
        
        self.assertIsNotNone(experiment_id)
        
        # 获取实验摘要
        summary = self.router.get_experiment_summary(experiment_id)
        
        self.assertIsNotNone(summary)
        self.assertEqual(summary["experiment_id"], experiment_id)
        self.assertIn("status", summary)
        self.assertIn("result", summary)
        self.assertIn("local_performance", summary)
        
        # 检查本地性能统计
        local_perf = summary["local_performance"]
        self.assertIn("intelligent_base", local_perf)
        self.assertIn("random_baseline", local_perf)


class TestRoutingStrategies(AsyncTestCase):
    """测试路由策略执行"""
    
    def setUp(self):
        super().setUp()
        self.router = ABTestingRouter(storage_path=self.test_data_dir)
        
        # 配置模拟模型
        self.router.model_status["deepseek-model"] = ModelStatus.HEALTHY
        self.router.model_status["stepflash-model"] = ModelStatus.HEALTHY
        self.router.model_status["local-model"] = ModelStatus.HEALTHY
        
        # 配置模型能力
        capabilities = [
            ModelCapability(
                model_name="deepseek-model",
                supported_tasks=[TaskType.GENERAL, TaskType.REASONING, TaskType.CODE_GENERATION],
                strengths=["推理", "代码生成", "数学计算"],
                weaknesses=[],  # 添加空弱点列表
                max_tokens=8000
            ),
            ModelCapability(
                model_name="stepflash-model",
                supported_tasks=[TaskType.GENERAL, TaskType.SUMMARIZATION, TaskType.TRANSLATION],
                strengths=["摘要", "翻译", "快速响应"],
                weaknesses=[],  # 添加空弱点列表
                max_tokens=4000
            ),
            ModelCapability(
                model_name="local-model",
                supported_tasks=[TaskType.GENERAL, TaskType.SUMMARIZATION],
                strengths=["本地推理", "隐私保护", "低成本"],
                weaknesses=[],  # 添加空弱点列表
                max_tokens=2000
            )
        ]
        
        for capability in capabilities:
            self.router.model_capabilities[capability.model_name] = capability
        
        # 配置预测器（模拟）
        self.router.predictor.predict = MagicMock(return_value=MagicMock(
            model_name="test-model",
            predicted_latency_ms=500.0,
            confidence=0.8,
            availability_probability=0.95,
            recommendation_score=0.85,
            factors=["模拟预测"]
        ))
    
    async def test_random_routing_strategy(self):
        """测试随机路由策略"""
        task_context = TaskContext(
            task_type=TaskType.GENERAL,
            estimated_tokens=500,
            priority=5
        )
        
        decision = await self.router._route_random(task_context)
        
        self.assertIsNotNone(decision)
        self.assertIsNotNone(decision.selected_model)
        self.assertIn(decision.selected_model, ["deepseek-model", "stepflash-model", "local-model"])
        self.assertIsInstance(decision.alternative_models, list)
        self.assertIsInstance(decision.reasoning, list)
        
        # 检查是否包含随机策略说明
        reasoning_text = " ".join(decision.reasoning).lower()
        self.assertIn("随机", reasoning_text)
    
    async def test_cost_first_routing_strategy_without_monitor(self):
        """测试无成本监控时的成本优先策略"""
        task_context = TaskContext(
            task_type=TaskType.GENERAL,
            estimated_tokens=500,
            priority=5
        )
        
        # 没有配置成本监控，应回退到智能路由
        decision = await self.router._route_cost_first(task_context)
        
        self.assertIsNotNone(decision)
        self.assertIsNotNone(decision.selected_model)
    
    async def test_performance_first_routing_strategy(self):
        """测试性能优先路由策略"""
        task_context = TaskContext(
            task_type=TaskType.REASONING,
            estimated_tokens=1000,
            priority=7
        )
        
        decision = await self.router._route_performance_first(task_context)
        
        self.assertIsNotNone(decision)
        self.assertIsNotNone(decision.selected_model)
        self.assertIsInstance(decision.predicted_performance, MagicMock)
        
        # 检查是否包含性能优先说明
        reasoning_text = " ".join(decision.reasoning).lower()
        self.assertIn("性能", reasoning_text)
    
    async def test_hybrid_routing_strategy(self):
        """测试混合路由策略"""
        task_context = TaskContext(
            task_type=TaskType.ANALYTICAL,
            estimated_tokens=800,
            priority=6
        )
        
        # 配置模拟成本监控
        mock_cost_monitor = MagicMock()
        mock_cost_monitor.estimate_cost = MagicMock(return_value=0.005)
        self.router.cost_monitor = mock_cost_monitor
        
        decision = await self.router._route_hybrid(task_context)
        
        self.assertIsNotNone(decision)
        self.assertIsNotNone(decision.selected_model)
        
        # 检查是否包含混合策略说明
        reasoning_text = " ".join(decision.reasoning).lower()
        self.assertIn("混合", reasoning_text) or self.assertIn("综合", reasoning_text)
    
    async def test_route_with_experiment(self):
        """测试实验路由"""
        # 创建实验
        experiment_id = self.router.create_routing_experiment(
            experiment_id="test_exp_routing",
            experiment_name="路由策略实验",
            strategies_to_test=["intelligent_base", "random_baseline"],
            traffic_percentage=10.0
        )
        
        self.assertIsNotNone(experiment_id)
        
        # 启动实验（模拟）
        with patch.object(self.router.ab_testing, 'assign_variant') as mock_assign:
            mock_assign.return_value = {
                "variant_id": "variant_0",
                "variant_config": {
                    "strategy_name": "intelligent_base",
                    "strategy_type": "intelligent",
                    "parameters": {"exploration_rate": 0.1},
                    "description": "智能路由基础策略"
                },
                "experiment_id": experiment_id
            }
            
            task_context = TaskContext(
                task_type=TaskType.GENERAL,
                estimated_tokens=500,
                priority=5
            )
            
            decision, variant_id = await self.router.route_with_experiment(
                task_context, experiment_id, "test_user_001"
            )
            
            self.assertIsNotNone(decision)
            self.assertIsNotNone(variant_id)
            self.assertEqual(variant_id, "variant_0")
            
            # 检查策略性能统计是否更新
            perf = self.router.get_strategy_performance("intelligent_base")
            self.assertEqual(perf.sample_count, 1)
            self.assertEqual(perf.success_count, 1)  # 假设成功


class TestResultRecording(RANGENTestCase):
    """测试结果记录功能"""
    
    def setUp(self):
        super().setUp()
        self.router = ABTestingRouter(storage_path=self.test_data_dir)
    
    def test_record_experiment_result(self):
        """测试记录实验结果"""
        # 创建实验
        experiment_id = self.router.create_routing_experiment(
            experiment_id="test_exp_recording",
            experiment_name="结果记录实验",
            strategies_to_test=["intelligent_base"],
            traffic_percentage=5.0
        )
        
        self.assertIsNotNone(experiment_id)
        
        # 记录结果
        metrics = {
            "success_rate": 0.95,
            "response_time_ms": 1250.5,
            "cost": 0.012,
            "user_satisfaction": 4.2
        }
        
        with patch.object(self.router.ab_testing, 'record_result') as mock_record:
            mock_record.return_value = True
            
            result = self.router.record_experiment_result(
                experiment_id, "variant_0", metrics
            )
            
            self.assertTrue(result)
            mock_record.assert_called_once_with(experiment_id, "variant_0", metrics)


class TestSingletonPattern(RANGENTestCase):
    """测试单例模式"""
    
    def test_get_ab_testing_router_singleton(self):
        """测试获取单例实例"""
        router1 = get_ab_testing_router(storage_path=self.test_data_dir)
        router2 = get_ab_testing_router(storage_path=self.test_data_dir)
        
        self.assertIs(router1, router2)
        self.assertIsInstance(router1, ABTestingRouter)
    
    def test_singleton_with_different_parameters(self):
        """测试带不同参数的单例模式"""
        router1 = get_ab_testing_router(storage_path=self.test_data_dir)
        
        # 再次调用时，storage_path参数应被忽略（单例已存在）
        router2 = get_ab_testing_router(storage_path="/different/path")
        
        self.assertIs(router1, router2)


class TestIntegrationWithExistingServices(RANGENTestCase):
    """测试与现有服务的集成"""
    
    def test_integration_with_cost_services(self):
        """测试与成本服务集成"""
        # 模拟成本监控服务
        mock_cost_monitor = MagicMock()
        mock_cost_monitor.estimate_cost = MagicMock(return_value=0.008)
        
        # 模拟成本控制服务
        mock_cost_controller = MagicMock()
        mock_cost_controller.get_pricing = MagicMock(return_value={"deepseek-model": 0.002, "stepflash-model": 0.001})
        
        # 创建路由器并注入模拟服务
        router = ABTestingRouter(
            cost_monitor=mock_cost_monitor,
            cost_controller=mock_cost_controller,
            storage_path=self.test_data_dir
        )
        
        self.assertIs(router.cost_monitor, mock_cost_monitor)
        self.assertIs(router.cost_controller, mock_cost_controller)
        
        # 测试成本估算
        cost = mock_cost_monitor.estimate_cost(1000, "deepseek-model")
        self.assertEqual(cost, 0.008)
        
        # 测试定价获取
        pricing = mock_cost_controller.get_pricing()
        self.assertIn("deepseek-model", pricing)
        self.assertEqual(pricing["deepseek-model"], 0.002)


if __name__ == "__main__":
    # 运行测试
    import unittest
    unittest.main()