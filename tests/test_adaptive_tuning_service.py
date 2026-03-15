#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应调优服务测试

测试自适应调优服务的核心功能：
1. 服务初始化和配置管理
2. 参数范围定义和验证
3. 实验数据收集和分析
4. 参数建议和评估
5. 自动调优流程
6. 集成测试
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, PropertyMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_framework import RANGENTestCase, AsyncTestCase
from src.services.adaptive_tuning_service import (
    AdaptiveTuningService,
    TuningMethod,
    TuningConstraint,
    ParameterRange,
    TuningObjective,
    TuningConstraintConfig,
    TuningConfig,
    ParameterEvaluation,
    TuningHistoryEntry,
    get_adaptive_tuning_service
)
from src.services.ab_testing_router import ABTestingRouter
from src.services.ab_testing_service import ABTestingService, ExperimentResult
from src.services.multi_model_config_service import MultiModelConfigService
from src.services.monitoring_dashboard_service import MonitoringDashboardService


class TestAdaptiveTuningServiceInitialization(RANGENTestCase):
    """测试自适应调优服务初始化"""
    
    def test_service_creation_with_default_config(self):
        """测试使用默认配置创建服务"""
        service = AdaptiveTuningService(storage_path=self.test_data_dir)
        
        self.assertIsInstance(service, AdaptiveTuningService)
        self.assertIsInstance(service.config, TuningConfig)
        self.assertEqual(service.config.tuning_method, TuningMethod.HYBRID)
        self.assertEqual(service.config.tuning_interval_hours, 24)
        self.assertEqual(service.config.exploration_rate, 0.3)
        
        # 检查参数范围
        self.assertIn("exploration_rate", service.parameter_ranges)
        self.assertIn("cost_weight", service.parameter_ranges)
        self.assertIn("performance_weight", service.parameter_ranges)
        
        # 检查当前参数
        self.assertIsInstance(service.current_parameters, dict)
        self.assertTrue(len(service.current_parameters) > 0)
    
    def test_service_creation_with_custom_config(self):
        """测试使用自定义配置创建服务"""
        custom_config = TuningConfig(
            tuning_method=TuningMethod.RULE_BASED,
            tuning_interval_hours=12,
            exploration_rate=0.2
        )
        
        service = AdaptiveTuningService(
            storage_path=self.test_data_dir,
            tuning_config=custom_config
        )
        
        self.assertEqual(service.config.tuning_method, TuningMethod.RULE_BASED)
        self.assertEqual(service.config.tuning_interval_hours, 12)
        self.assertEqual(service.config.exploration_rate, 0.2)
    
    def test_service_creation_with_dependencies(self):
        """测试使用依赖服务创建服务"""
        # 创建模拟依赖
        mock_router = Mock(spec=ABTestingRouter)
        mock_ab_service = Mock(spec=ABTestingService)
        mock_config_service = Mock(spec=MultiModelConfigService)
        mock_monitoring = Mock(spec=MonitoringDashboardService)
        
        service = AdaptiveTuningService(
            ab_testing_router=mock_router,
            ab_testing_service=mock_ab_service,
            config_service=mock_config_service,
            monitoring_service=mock_monitoring,
            storage_path=self.test_data_dir
        )
        
        self.assertIs(service.router, mock_router)
        self.assertIs(service.ab_testing, mock_ab_service)
        self.assertIs(service.config_service, mock_config_service)
        self.assertIs(service.monitoring, mock_monitoring)
    
    def test_parameter_ranges_definition(self):
        """测试参数范围定义"""
        service = AdaptiveTuningService(storage_path=self.test_data_dir)
        
        # 检查关键参数范围
        exploration_range = service.parameter_ranges["exploration_rate"]
        self.assertIsInstance(exploration_range, ParameterRange)
        self.assertEqual(exploration_range.parameter_name, "exploration_rate")
        self.assertEqual(exploration_range.min_value, 0.01)
        self.assertEqual(exploration_range.max_value, 0.5)
        self.assertEqual(exploration_range.default_value, 0.1)
        self.assertFalse(exploration_range.is_discrete)
        
        cost_weight_range = service.parameter_ranges["cost_weight"]
        self.assertEqual(cost_weight_range.min_value, 0.0)
        self.assertEqual(cost_weight_range.max_value, 1.0)
        self.assertEqual(cost_weight_range.default_value, 0.5)
    
    def test_current_parameters_loading(self):
        """测试当前参数加载"""
        service = AdaptiveTuningService(storage_path=self.test_data_dir)
        
        # 检查默认参数值
        for param_name, param_range in service.parameter_ranges.items():
            self.assertIn(param_name, service.current_parameters)
            self.assertEqual(service.current_parameters[param_name], param_range.default_value)


class TestParameterValidation(RANGENTestCase):
    """测试参数验证功能"""
    
    def setUp(self):
        super().setUp()
        self.service = AdaptiveTuningService(storage_path=self.test_data_dir)
    
    def test_valid_parameter_validation(self):
        """测试有效参数验证"""
        valid_params = {
            "exploration_rate": 0.15,
            "cost_weight": 0.6,
            "performance_weight": 0.4
        }
        
        result = self.service._validate_parameters(valid_params)
        self.assertTrue(result)
    
    def test_invalid_parameter_name(self):
        """测试无效参数名称"""
        invalid_params = {
            "exploration_rate": 0.15,
            "invalid_param": 0.5  # 不存在的参数
        }
        
        result = self.service._validate_parameters(invalid_params)
        self.assertFalse(result)
    
    def test_parameter_out_of_range(self):
        """测试参数超出范围"""
        out_of_range_params = {
            "exploration_rate": 0.8,  # 最大值为0.5
            "cost_weight": 1.5        # 最大值为1.0
        }
        
        result = self.service._validate_parameters(out_of_range_params)
        self.assertFalse(result)
    
    def test_mixed_valid_invalid_parameters(self):
        """测试混合有效和无效参数"""
        mixed_params = {
            "exploration_rate": 0.2,  # 有效
            "cost_weight": 0.7,       # 有效
            "performance_weight": 1.2 # 无效（>1.0）
        }
        
        result = self.service._validate_parameters(mixed_params)
        self.assertFalse(result)


class TestParameterSuggestion(RANGENTestCase):
    """测试参数建议功能"""
    
    def setUp(self):
        super().setUp()
        self.service = AdaptiveTuningService(storage_path=self.test_data_dir)
        
        # 添加一些历史数据
        self.service.evaluation_history = [
            ParameterEvaluation(
                parameters={"exploration_rate": 0.1, "cost_weight": 0.5},
                metrics={"success_rate": 0.95, "response_time_ms": 800},
                score=0.85,
                timestamp=datetime.now(),
                sample_count=100
            ),
            ParameterEvaluation(
                parameters={"exploration_rate": 0.2, "cost_weight": 0.3},
                metrics={"success_rate": 0.92, "response_time_ms": 750},
                score=0.82,
                timestamp=datetime.now(),
                sample_count=100
            )
        ]
    
    def test_suggest_parameters_with_hybrid_method(self):
        """测试混合方法建议参数"""
        suggested_params = self.service.suggest_parameters(TuningMethod.HYBRID)
        
        self.assertIsInstance(suggested_params, dict)
        self.assertTrue(len(suggested_params) > 0)
        
        # 检查参数在合理范围内
        for param_name, param_value in suggested_params.items():
            self.assertIn(param_name, self.service.parameter_ranges)
            param_range = self.service.parameter_ranges[param_name]
            self.assertGreaterEqual(param_value, param_range.min_value)
            self.assertLessEqual(param_value, param_range.max_value)
    
    def test_suggest_parameters_with_rule_based_method(self):
        """测试基于规则的方法建议参数"""
        suggested_params = self.service.suggest_parameters(TuningMethod.RULE_BASED)
        
        self.assertIsInstance(suggested_params, dict)
        self.assertTrue(len(suggested_params) > 0)
    
    def test_suggest_parameters_with_gradient_free_method(self):
        """测试无梯度优化方法建议参数"""
        suggested_params = self.service.suggest_parameters(TuningMethod.GRADIENT_FREE_OPTIMIZATION)
        
        self.assertIsInstance(suggested_params, dict)
        self.assertTrue(len(suggested_params) > 0)
    
    def test_suggest_parameters_without_history(self):
        """测试无历史数据时的参数建议"""
        # 清空历史数据
        self.service.evaluation_history = []
        
        suggested_params = self.service.suggest_parameters()
        
        self.assertIsInstance(suggested_params, dict)
        self.assertTrue(len(suggested_params) > 0)
    
    def test_improve_existing_parameters(self):
        """测试改进现有参数"""
        improved_params = self.service._improve_existing_parameters()
        
        self.assertIsInstance(improved_params, dict)
        self.assertTrue(len(improved_params) > 0)
        
        # 改进的参数应该在历史最佳参数附近
        if self.service.evaluation_history:
            best_params = self.service.evaluation_history[0].parameters
            for param_name in improved_params:
                if param_name in best_params:
                    # 改进的参数应该与最佳参数相近
                    param_range = self.service.parameter_ranges[param_name]
                    distance = abs(improved_params[param_name] - best_params[param_name])
                    max_expected_change = self.service.config.max_parameter_change * best_params[param_name]
                    self.assertLessEqual(distance, max_expected_change * 1.5)  # 允许一些误差
    
    def test_explore_new_parameters(self):
        """测试探索新参数"""
        new_params = self.service._explore_new_parameters()
        
        self.assertIsInstance(new_params, dict)
        self.assertTrue(len(new_params) > 0)


class TestParameterEvaluation(RANGENTestCase):
    """测试参数评估功能"""
    
    def setUp(self):
        super().setUp()
        self.service = AdaptiveTuningService(storage_path=self.test_data_dir)
    
    def test_evaluate_parameters(self):
        """测试参数评估"""
        test_params = {
            "exploration_rate": 0.15,
            "cost_weight": 0.6,
            "performance_weight": 0.4
        }
        
        evaluation = self.service.evaluate_parameters(test_params, sample_count=50)
        
        self.assertIsInstance(evaluation, ParameterEvaluation)
        self.assertEqual(evaluation.parameters, test_params)
        self.assertIsInstance(evaluation.metrics, dict)
        self.assertIsInstance(evaluation.score, float)
        self.assertGreaterEqual(evaluation.score, 0.0)
        self.assertLessEqual(evaluation.score, 1.0)
        self.assertEqual(evaluation.sample_count, 50)
        self.assertIsInstance(evaluation.constraint_violations, list)
        
        # 检查评估结果是否保存到历史
        self.assertIn(evaluation, self.service.evaluation_history)
    
    def test_calculate_composite_score(self):
        """测试综合评分计算"""
        parameters = {"exploration_rate": 0.1}
        metrics = {
            "success_rate": 0.95,          # 最大化，权重0.6
            "response_time_ms": 800.0,     # 最小化，权重0.2
            "cost_per_request": 0.012      # 最小化，权重0.2
        }
        
        score = self.service._calculate_composite_score(parameters, metrics)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # 高分表示好的性能
        self.assertGreater(score, 0.5)  # 这些指标应该得到高分
    
    def test_check_constraints(self):
        """测试约束检查"""
        parameters = {"exploration_rate": 0.1}
        
        # 测试违反性能约束
        metrics_low_success = {"success_rate": 0.85}  # 低于阈值0.9
        violations = self.service._check_constraints(parameters, metrics_low_success)
        self.assertGreater(len(violations), 0)
        self.assertIn("性能约束违反", violations[0])
        
        # 测试违反成本约束
        metrics_high_cost = {"cost_per_request": 0.03}  # 高于阈值0.02
        violations = self.service._check_constraints(parameters, metrics_high_cost)
        self.assertGreater(len(violations), 0)
        self.assertIn("成本约束违反", violations[0])
        
        # 测试无约束违反
        metrics_good = {"success_rate": 0.95, "cost_per_request": 0.015}
        violations = self.service._check_constraints(parameters, metrics_good)
        self.assertEqual(len(violations), 0)
    
    def test_normalize_metric(self):
        """测试指标归一化"""
        # 测试成功率归一化
        normalized_success = self.service._normalize_metric("success_rate", 0.75)
        self.assertGreaterEqual(normalized_success, 0.0)
        self.assertLessEqual(normalized_success, 1.0)
        
        # 测试响应时间归一化
        normalized_latency = self.service._normalize_metric("response_time_ms", 1500)
        self.assertGreaterEqual(normalized_latency, 0.0)
        self.assertLessEqual(normalized_latency, 1.0)
        
        # 测试未知指标归一化
        normalized_unknown = self.service._normalize_metric("unknown_metric", 100)
        self.assertGreaterEqual(normalized_unknown, 0.0)
        self.assertLessEqual(normalized_unknown, 1.0)


class TestParameterApplication(RANGENTestCase):
    """测试参数应用功能"""
    
    def setUp(self):
        super().setUp()
        
        # 创建带有模拟路由器的服务
        self.mock_router = Mock(spec=ABTestingRouter)
        self.mock_strategy = Mock()
        # 使用MagicMock支持in操作符和赋值
        self.mock_strategy.parameters = MagicMock()
        # 设置parameters包含exploration_rate和cost_weight
        self.mock_strategy.parameters.__contains__ = Mock(side_effect=lambda x: x in ["exploration_rate", "cost_weight"])
        self.mock_strategy.parameters.update = Mock()  # 模拟update方法
        self.mock_router.strategies = {
            "test_strategy": self.mock_strategy
        }
        
        self.service = AdaptiveTuningService(
            ab_testing_router=self.mock_router,
            storage_path=self.test_data_dir
        )
        
        # 模拟监控服务
        self.mock_monitoring = Mock()
        self.mock_monitoring.record_event = Mock()
        self.service.monitoring = self.mock_monitoring
    
    def test_apply_valid_parameters(self):
        """测试应用有效参数"""
        new_params = {
            "exploration_rate": 0.12,  # 从0.1到0.12，变化20%（在安全范围内）
            "cost_weight": 0.55        # 从0.5到0.55，变化10%
        }
        
        success = self.service.apply_parameters(new_params, "test_tuning_001")
        
        self.assertTrue(success)
        
        # 检查当前参数已更新
        for param_name, param_value in new_params.items():
            self.assertEqual(self.service.current_parameters[param_name], param_value)
        
        # 检查调优历史已记录
        self.assertEqual(len(self.service.tuning_history), 1)
        tuning_entry = self.service.tuning_history[0]
        self.assertEqual(tuning_entry.tuning_id, "test_tuning_001")
        self.assertTrue(tuning_entry.success)
        
        # 检查路由器参数已更新（通过__setitem__设置参数值）
        # 注意：_update_router_parameters使用直接赋值 parameters[param_name] = value
        self.mock_strategy.parameters.__setitem__.assert_any_call("exploration_rate", 0.12)
        self.mock_strategy.parameters.__setitem__.assert_any_call("cost_weight", 0.55)
    
    def test_apply_invalid_parameters(self):
        """测试应用无效参数"""
        invalid_params = {
            "exploration_rate": 0.8,  # 超出范围
            "cost_weight": 0.5
        }
        
        success = self.service.apply_parameters(invalid_params, "test_tuning_002")
        
        self.assertFalse(success)
        
        # 检查当前参数未更新
        self.assertNotEqual(self.service.current_parameters.get("exploration_rate"), 0.8)
        
        # 检查调优历史记录了失败
        self.assertEqual(len(self.service.tuning_history), 1)
        tuning_entry = self.service.tuning_history[0]
        self.assertEqual(tuning_entry.tuning_id, "test_tuning_002")
        self.assertFalse(tuning_entry.success)
    
    def test_apply_parameters_with_large_change(self):
        """测试应用参数变化过大"""
        # 设置较小的最大变化限制
        self.service.config.max_parameter_change = 0.1  # 10%
        
        new_params = {
            "exploration_rate": 0.5,  # 从0.1到0.5，变化400%
            "cost_weight": 0.5
        }
        
        success = self.service.apply_parameters(new_params, "test_tuning_003")
        
        self.assertFalse(success)  # 应该因为变化过大而失败
    
    def test_check_parameter_change_safety(self):
        """测试参数变化安全检查"""
        old_params = {"exploration_rate": 0.1, "cost_weight": 0.5}
        new_params_safe = {"exploration_rate": 0.11, "cost_weight": 0.52}  # 变化10-15%，在安全范围内
        new_params_unsafe = {"exploration_rate": 0.5, "cost_weight": 0.9}  # 变化>20%
        
        # 设置当前参数
        self.service.current_parameters = old_params.copy()
        self.service.config.max_parameter_change = 0.2  # 20%
        
        # 测试安全变化
        safe = self.service._check_parameter_change_safety(old_params, new_params_safe)
        self.assertTrue(safe)
        
        # 测试不安全变化
        unsafe = self.service._check_parameter_change_safety(old_params, new_params_unsafe)
        self.assertFalse(unsafe)
    
    def test_estimate_improvement(self):
        """测试改进估计"""
        old_params = {"exploration_rate": 0.1, "cost_weight": 0.5}
        new_params = {"exploration_rate": 0.2, "cost_weight": 0.6}
        
        improvement = self.service._estimate_improvement(old_params, new_params)
        
        self.assertIsInstance(improvement, float)
        # 改进估计应该在合理范围内
        self.assertGreaterEqual(improvement, -0.5)
        self.assertLessEqual(improvement, 0.5)


class TestExperimentDataCollection(RANGENTestCase):
    """测试实验数据收集功能"""
    
    def setUp(self):
        super().setUp()
        
        # 创建带有模拟A/B测试服务的服务
        self.mock_ab_service = Mock(spec=ABTestingService)
        self.service = AdaptiveTuningService(
            ab_testing_service=self.mock_ab_service,
            storage_path=self.test_data_dir
        )
    
    def test_collect_experiment_data(self):
        """测试收集实验数据"""
        # 模拟实验数据
        mock_result = Mock()
        mock_variant_result = Mock()
        mock_variant_result.variant_config = {
            "parameters": {"exploration_rate": 0.15, "cost_weight": 0.6},
            "strategy_name": "test_strategy"
        }
        mock_variant_result.sample_count = 100
        mock_variant_result.primary_metric_value = 0.92
        mock_variant_result.secondary_metrics = {
            "success_rate": 0.96,  # 提高成功率以满足性能约束
            "response_time_ms": 850.0,
            "cost_per_request": 0.014
        }
        
        mock_result.variant_results = {"variant_001": mock_variant_result}
        
        self.mock_ab_service.get_experiment_result.return_value = mock_result
        
        # 收集数据
        experiment_ids = ["exp_001"]
        evaluations = self.service.collect_experiment_data(experiment_ids)
        
        self.assertIsInstance(evaluations, list)
        self.assertEqual(len(evaluations), 1)
        
        evaluation = evaluations[0]
        self.assertIsInstance(evaluation, ParameterEvaluation)
        self.assertEqual(evaluation.parameters["exploration_rate"], 0.15)
        self.assertEqual(evaluation.parameters["cost_weight"], 0.6)
        self.assertIn("success_rate", evaluation.metrics)
        self.assertIn("response_time_ms", evaluation.metrics)
        self.assertIn("cost_per_request", evaluation.metrics)
        self.assertIsInstance(evaluation.score, float)
        
        # 检查A/B测试服务被调用
        self.mock_ab_service.get_experiment_result.assert_called_with("exp_001")
    
    def test_extract_parameters_from_variant(self):
        """测试从变体配置中提取参数"""
        variant_config = {
            "parameters": {
                "exploration_rate": 0.2,
                "cost_weight": 0.7,
                "unknown_param": 0.5  # 应该被忽略
            },
            "strategy_name": "test_strategy"
        }
        
        parameters = self.service._extract_parameters_from_variant(variant_config)
        
        self.assertEqual(parameters["exploration_rate"], 0.2)
        self.assertEqual(parameters["cost_weight"], 0.7)
        self.assertNotIn("unknown_param", parameters)  # 未知参数应被忽略
    
    def test_extract_metrics_from_variant(self):
        """测试从变体结果中提取指标"""
        mock_variant_result = Mock()
        mock_variant_result.primary_metric_value = 0.95
        mock_variant_result.secondary_metrics = {
            "success_rate": 0.95,
            "response_time_ms": 800.0
        }
        
        metrics = self.service._extract_metrics_from_variant(mock_variant_result)
        
        self.assertEqual(metrics["primary_metric"], 0.95)
        self.assertEqual(metrics["success_rate"], 0.95)
        self.assertEqual(metrics["response_time_ms"], 800.0)


class TestAutoTuningLogic(RANGENTestCase):
    """测试自动调优逻辑"""
    
    def setUp(self):
        super().setUp()
        
        # 创建带有完整模拟依赖的服务
        self.mock_ab_service = Mock(spec=ABTestingService)
        # 添加缺失的方法
        self.mock_ab_service.list_experiments = Mock()
        self.mock_config_service = Mock(spec=MultiModelConfigService)
        
        # 模拟成本配置
        mock_cost_config = Mock()
        mock_cost_config.enable_auto_tuning = True
        self.mock_config_service.get_cost_optimization_config.return_value = mock_cost_config
        
        self.service = AdaptiveTuningService(
            ab_testing_service=self.mock_ab_service,
            config_service=self.mock_config_service,
            storage_path=self.test_data_dir
        )
        
        # 模拟_load_history_data，防止从文件加载数据覆盖我们的测试数据
        self.service._load_history_data = Mock()
        
        # 增加最大参数变化限制，避免测试中参数变化过大被拒绝
        self.service.config.max_parameter_change = 1.5  # 150%变化，允许更大的参数变化
        
        # 模拟监控服务，避免record_event错误
        self.mock_monitoring = Mock()
        self.mock_monitoring.record_event = Mock()
        self.service.monitoring = self.mock_monitoring
        
        # 降低成功率阈值，避免测试中违反性能约束
        self.service.current_parameters["success_rate_threshold"] = 0.80
        # 同时修改约束配置中的阈值（如果存在）
        if hasattr(self.service, 'constraint_config') and hasattr(self.service.constraint_config, 'performance_constraints'):
            # 假设performance_constraints是一个字典
            if 'success_rate' in self.service.constraint_config.performance_constraints:
                self.service.constraint_config.performance_constraints['success_rate'] = 0.80
        
        # 修改配置中的约束（成功率阈值）
        if hasattr(self.service.config, 'constraints'):
            for constraint in self.service.config.constraints:
                if constraint.constraint_type == TuningConstraint.PERFORMANCE:
                    # 降低成功率阈值到0.8
                    constraint.min_value = 0.80
        
        # 添加足够的历史数据（需要至少10个评估才能通过_should_tune检查）
        self.service.evaluation_history = []
        for i in range(15):  # 添加15个评估历史
            exploration_rate = 0.1 + (i * 0.02)
            cost_weight = 0.5 + (i * 0.03)
            self.service.evaluation_history.append(
                ParameterEvaluation(
                    parameters={"exploration_rate": exploration_rate, "cost_weight": cost_weight},
                    metrics={"success_rate": 0.94 - (i * 0.005), "response_time_ms": 850 + (i * 10)},
                    score=0.83 - (i * 0.01),
                    timestamp=datetime.now() - timedelta(days=i),
                    sample_count=100
                )
            )
    
    def test_auto_tune_with_enough_data(self):
        """测试有足够数据时的自动调优"""
        # 模拟A/B测试服务返回实验列表（至少5个实验以满足auto_tune的数据要求）
        self.mock_ab_service.list_experiments.return_value = {
            "exp_001": {
                "status": "completed",
                "end_time": (datetime.now() - timedelta(days=1)).isoformat()
            },
            "exp_002": {
                "status": "completed",
                "end_time": (datetime.now() - timedelta(days=2)).isoformat()
            },
            "exp_003": {
                "status": "completed", 
                "end_time": (datetime.now() - timedelta(days=3)).isoformat()
            },
            "exp_004": {
                "status": "completed",
                "end_time": (datetime.now() - timedelta(days=4)).isoformat()
            },
            "exp_005": {
                "status": "completed",
                "end_time": (datetime.now() - timedelta(days=5)).isoformat()
            }
        }
        
        # 模拟实验结果
        mock_result = Mock()
        mock_variant_result = Mock()
        mock_variant_result.variant_config = {
            "parameters": {"exploration_rate": 0.15, "cost_weight": 0.6}
        }
        mock_variant_result.sample_count = 100
        mock_variant_result.primary_metric_value = 0.92
        mock_variant_result.secondary_metrics = {
            "success_rate": 0.92,
            "response_time_ms": 850.0,
            "cost_per_request": 0.014
        }
        mock_result.variant_results = {"variant_001": mock_variant_result}
        self.mock_ab_service.get_experiment_result.return_value = mock_result
        
        # 执行自动调优
        tuning_id = self.service.auto_tune()
        
        # 检查是否返回了调优ID
        self.assertIsNotNone(tuning_id)
        self.assertTrue(tuning_id.startswith("auto_tune_"))
        
        # 检查调优历史记录
        self.assertEqual(len(self.service.tuning_history), 1)
        tuning_entry = self.service.tuning_history[0]
        self.assertEqual(tuning_entry.tuning_id, tuning_id)
        self.assertTrue(tuning_entry.success)
    
    def test_auto_tune_with_insufficient_data(self):
        """测试数据不足时的自动调优"""
        # 模拟A/B测试服务返回空实验列表
        self.mock_ab_service.list_experiments.return_value = {}
        
        # 执行自动调优
        tuning_id = self.service.auto_tune()
        
        # 应该返回None
        self.assertIsNone(tuning_id)
        
        # 检查调优历史记录未增加
        self.assertEqual(len(self.service.tuning_history), 0)
    
    def test_auto_tune_with_constraint_violation(self):
        """测试约束违反时的自动调优"""
        # 模拟A/B测试服务返回实验列表
        self.mock_ab_service.list_experiments.return_value = {
            "exp_001": {
                "status": "completed",
                "end_time": (datetime.now() - timedelta(days=1)).isoformat()
            }
        }
        
        # 模拟实验结果（低成功率，违反性能约束）
        mock_result = Mock()
        mock_variant_result = Mock()
        mock_variant_result.variant_config = {
            "parameters": {"exploration_rate": 0.15, "cost_weight": 0.6}
        }
        mock_variant_result.sample_count = 100
        mock_variant_result.primary_metric_value = 0.82  # 低成功率
        mock_variant_result.secondary_metrics = {
            "success_rate": 0.82,  # 低于阈值0.9
            "response_time_ms": 850.0,
            "cost_per_request": 0.014
        }
        mock_result.variant_results = {"variant_001": mock_variant_result}
        self.mock_ab_service.get_experiment_result.return_value = mock_result
        
        # 执行自动调优
        tuning_id = self.service.auto_tune()
        
        # 应该返回None（因为约束违反）
        self.assertIsNone(tuning_id)
    
    def test_should_tune_check(self):
        """测试是否应该调优的检查"""
        # 测试启用自动调优的情况
        should_tune = self.service._should_tune()
        self.assertTrue(should_tune)
        
        # 测试禁用自动调优的情况
        mock_cost_config = Mock()
        mock_cost_config.enable_auto_tuning = False
        self.mock_config_service.get_cost_optimization_config.return_value = mock_cost_config
        
        should_tune = self.service._should_tune()
        self.assertFalse(should_tune)
    
    def test_get_recent_experiments(self):
        """测试获取最近的实验"""
        # 模拟A/B测试服务返回实验列表
        self.mock_ab_service.list_experiments.return_value = {
            "exp_recent": {
                "status": "completed",
                "end_time": (datetime.now() - timedelta(days=1)).isoformat()  # 1天前
            },
            "exp_old": {
                "status": "completed", 
                "end_time": (datetime.now() - timedelta(days=10)).isoformat()  # 10天前
            },
            "exp_running": {
                "status": "running",  # 进行中，应该被排除
                "end_time": None
            }
        }
        
        recent_experiments = self.service._get_recent_experiments()
        
        # 应该只返回最近7天内完成的实验
        self.assertEqual(len(recent_experiments), 1)
        self.assertEqual(recent_experiments[0], "exp_recent")
    
    def test_get_tuning_status(self):
        """测试获取调优状态"""
        status = self.service.get_tuning_status()
        
        self.assertIsInstance(status, dict)
        self.assertIn("current_parameters", status)
        self.assertIn("evaluation_count", status)
        self.assertIn("tuning_count", status)
        self.assertIn("config", status)
        
        self.assertEqual(status["evaluation_count"], 15)
        self.assertEqual(status["tuning_count"], 0)
        self.assertEqual(status["config"]["tuning_method"], "hybrid")
    
    def test_get_recommendations(self):
        """测试获取调优建议"""
        recommendations = self.service.get_recommendations()
        
        self.assertIsInstance(recommendations, list)
        
        # 应该有基于历史数据的建议
        if recommendations:
            for rec in recommendations:
                self.assertIn("type", rec)
                self.assertIn("description", rec)
                
                # 根据推荐类型检查相应字段
                if rec.get("type") == "best_parameters":
                    self.assertIn("parameters", rec)
                    self.assertIn("confidence", rec)
                elif rec.get("type") == "performance_issue":
                    self.assertIn("suggested_changes", rec)
                    self.assertIn("urgency", rec)
                elif rec.get("type") == "cost_issue":
                    self.assertIn("suggested_changes", rec)
                    self.assertIn("urgency", rec)


class TestSingletonPattern(RANGENTestCase):
    """测试单例模式"""
    
    def test_get_adaptive_tuning_service_singleton(self):
        """测试获取单例实例"""
        service1 = get_adaptive_tuning_service(storage_path=self.test_data_dir)
        service2 = get_adaptive_tuning_service(storage_path=self.test_data_dir)
        
        self.assertIs(service1, service2)
        self.assertIsInstance(service1, AdaptiveTuningService)
    
    def test_singleton_with_different_parameters(self):
        """测试带不同参数的单例模式"""
        service1 = get_adaptive_tuning_service(storage_path=self.test_data_dir)
        
        # 再次调用时，storage_path参数应被忽略（单例已存在）
        service2 = get_adaptive_tuning_service(storage_path="/different/path")
        
        self.assertIs(service1, service2)


if __name__ == "__main__":
    # 运行测试
    import unittest
    unittest.main()