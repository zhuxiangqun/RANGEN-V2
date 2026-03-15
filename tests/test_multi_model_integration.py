#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型架构集成测试（修复版 V2）

测试新创建的多模型架构服务与现有系统的集成。
更新以匹配实际实现的方法和接口。
"""

import os
import sys
import json
import time
import tempfile
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_framework import RANGENTestCase, AsyncTestCase


class TestMultiModelAdapterIntegration(RANGENTestCase):
    """测试多模型适配器框架集成"""
    
    def test_llm_adapter_base_import(self):
        """测试LLM适配器基类导入"""
        try:
            from src.adapters.llm_adapter_base import (
                LLMProvider, AdapterCapability, LLMRequest,
                LLMResponse, AdapterConfig, BaseLLMAdapter
            )
            self.assertTrue(True, "LLM适配器基类导入成功")
        except ImportError as e:
            self.fail(f"LLM适配器基类导入失败: {e}")
    
    def test_llm_adapter_factory_import(self):
        """测试LLM适配器工厂导入"""
        try:
            from src.adapters.llm_adapter_factory import LLMAdapterFactory
            self.assertTrue(True, "LLM适配器工厂导入成功")
            
            # 验证工厂类存在
            self.assertTrue(hasattr(LLMAdapterFactory, 'create_adapter'))
            self.assertTrue(hasattr(LLMAdapterFactory, 'create_adapter_simple'))
            self.assertTrue(hasattr(LLMAdapterFactory, 'register_adapter'))
            
        except ImportError as e:
            self.fail(f"LLM适配器工厂导入失败: {e}")


class TestFaultToleranceServiceIntegration(RANGENTestCase):
    """测试故障容忍服务集成（修复版）"""
    
    def test_fault_tolerance_service_import(self):
        """测试故障容忍服务导入（匹配实际导出）"""
        try:
            from src.services.fault_tolerance_service import (
                FaultToleranceService, ModelPriority, FailureType,
                FallbackChainConfig  # 实际导出的是FallbackChainConfig，不是FallbackChain
            )
            self.assertTrue(True, "故障容忍服务导入成功")
        except ImportError as e:
            self.fail(f"故障容忍服务导入失败: {e}")
    
    def test_fault_tolerance_service_methods(self):
        """测试故障容忍服务方法（匹配实际方法）"""
        try:
            from src.services.fault_tolerance_service import FaultToleranceService
            
            # 创建服务实例
            service = FaultToleranceService()
            
            # 验证服务有实际存在的方法（基于代码分析）
            self.assertTrue(hasattr(service, 'get_model_health'))
            self.assertTrue(hasattr(service, 'get_all_health_status'))
            self.assertTrue(hasattr(service, 'get_stats'))
            self.assertTrue(hasattr(service, 'reset_stats'))
            self.assertTrue(hasattr(service, 'start_health_check'))
            self.assertTrue(hasattr(service, 'force_model_healthy'))
            
        except Exception as e:
            self.fail(f"故障容忍服务方法测试失败: {e}")


class TestMultiModelConfigServiceIntegration(RANGENTestCase):
    """测试多模型配置服务集成（修复版）"""
    
    def test_multi_model_config_service_import(self):
        """测试多模型配置服务导入"""
        try:
            from src.services.multi_model_config_service import (
                MultiModelConfigService, ModelProvider, RoutingStrategy
            )
            self.assertTrue(True, "多模型配置服务导入成功")
        except ImportError as e:
            self.fail(f"多模型配置服务导入失败: {e}")
    
    def test_multi_model_config_service_methods(self):
        """测试多模型配置服务方法（匹配实际方法）"""
        try:
            from src.services.multi_model_config_service import MultiModelConfigService
            
            # 获取服务实例
            service = MultiModelConfigService()
            
            # 验证服务有实际存在的方法
            self.assertTrue(hasattr(service, 'get_model_config'))
            self.assertTrue(hasattr(service, 'get_all_model_configs'))  # 实际方法名
            self.assertTrue(hasattr(service, 'get_enabled_model_configs'))
            self.assertTrue(hasattr(service, 'get_routing_config'))
            self.assertTrue(hasattr(service, 'save_model_config'))
            
        except Exception as e:
            self.fail(f"多模型配置服务方法测试失败: {e}")


class TestContextOptimizationServiceIntegration(RANGENTestCase):
    """测试上下文优化服务集成（修复版）"""
    
    def test_context_optimization_service_import(self):
        """测试上下文优化服务导入"""
        try:
            from src.services.context_optimization_service import (
                ContextOptimizationService, OptimizationStrategy, 
                CompressionMethod, TokenAnalysisResult
            )
            self.assertTrue(True, "上下文优化服务导入成功")
        except ImportError as e:
            self.fail(f"上下文优化服务导入失败: {e}")
    
    def test_context_optimization_service_methods(self):
        """测试上下文优化服务方法（匹配实际方法）"""
        try:
            from src.services.context_optimization_service import ContextOptimizationService
            
            # 创建服务实例
            service = ContextOptimizationService()
            
            # 验证服务有实际存在的方法
            self.assertTrue(hasattr(service, 'optimize_context'))  # 主要方法
            self.assertTrue(hasattr(service, 'analyze_token_usage'))  # 实际方法
            self.assertTrue(hasattr(service, 'get_stats'))
            self.assertTrue(hasattr(service, 'clear_cache'))
            
        except Exception as e:
            self.fail(f"上下文优化服务方法测试失败: {e}")


class TestMonitoringDashboardServiceIntegration(RANGENTestCase):
    """测试监控仪表板服务集成（修复版）"""
    
    def test_monitoring_dashboard_service_import(self):
        """测试监控仪表板服务导入"""
        try:
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, Alert, AlertConfig
            )
            self.assertTrue(True, "监控仪表板服务导入成功")
        except ImportError as e:
            self.fail(f"监控仪表板服务导入失败: {e}")
    
    def test_monitoring_dashboard_service_methods(self):
        """测试监控仪表板服务方法（匹配实际方法）"""
        try:
            from src.services.monitoring_dashboard_service import MonitoringDashboardService
            
            # 创建服务实例
            service = MonitoringDashboardService()
            
            # 验证服务有实际存在的方法
            self.assertTrue(hasattr(service, 'record_metric'))
            self.assertTrue(hasattr(service, 'get_current_metrics'))  # 实际方法名
            self.assertTrue(hasattr(service, 'get_active_alerts'))
            self.assertTrue(hasattr(service, 'get_dashboard_summary'))
            self.assertTrue(hasattr(service, 'start'))
            self.assertTrue(hasattr(service, 'stop'))
            
        except Exception as e:
            self.fail(f"监控仪表板服务方法测试失败: {e}")


class TestABTestingServiceIntegration(RANGENTestCase):
    """测试A/B测试服务集成（修复版）"""
    
    def test_ab_testing_service_import(self):
        """测试A/B测试服务导入（已修复）"""
        try:
            from src.services.ab_testing_service import (
                ABTestingService, ExperimentStatus, VariantType,
                ExperimentConfig, VariantResult, ExperimentResult,
                get_ab_testing_service
            )
            self.assertTrue(True, "A/B测试服务导入成功")
        except ImportError as e:
            self.fail(f"A/B测试服务导入失败: {e}")
    
    def test_ab_testing_service_methods(self):
        """测试A/B测试服务方法"""
        try:
            from src.services.ab_testing_service import ABTestingService
            
            # 创建服务实例
            service = ABTestingService()
            
            # 验证服务有预期的方法
            self.assertTrue(hasattr(service, 'create_experiment'))
            self.assertTrue(hasattr(service, 'start_experiment'))
            self.assertTrue(hasattr(service, 'stop_experiment'))
            self.assertTrue(hasattr(service, 'get_experiment_status'))
            self.assertTrue(hasattr(service, 'assign_variant'))
            self.assertTrue(hasattr(service, 'record_result'))
            
        except Exception as e:
            self.fail(f"A/B测试服务方法测试失败: {e}")


class TestExistingServiceIntegration(RANGENTestCase):
    """测试现有服务与新系统的集成（修复版）"""
    
    def test_config_service_integration(self):
        """测试配置服务与多模型配置的集成"""
        try:
            from src.services.config_service import ConfigService
            
            # 获取配置服务实例
            config_service = ConfigService()
            
            # 测试配置服务基础功能
            llm_provider = config_service.get('LLM_PROVIDER', 'mock')
            
            # 验证配置服务响应
            self.assertIsNotNone(llm_provider)
            
        except Exception as e:
            self.fail(f"配置服务集成测试失败: {e}")
    
    def test_model_benchmark_service_import(self):
        """测试模型基准测试服务导入"""
        try:
            from src.services.model_benchmark_service import ModelBenchmarkService
            self.assertTrue(True, "模型基准测试服务导入成功")
        except ImportError as e:
            self.fail(f"模型基准测试服务导入失败: {e}")


class TestIntegrationSmokeTests(AsyncTestCase):
    """集成冒烟测试"""
    
    async def test_multi_model_service_smoke(self):
        """多模型服务冒烟测试"""
        try:
            # 测试配置服务
            from src.services.config_service import ConfigService
            config_service = ConfigService()
            
            # 测试获取配置
            llm_provider = config_service.get('LLM_PROVIDER', 'mock')
            self.assertIsNotNone(llm_provider)
            
            # 测试多模型配置服务
            from src.services.multi_model_config_service import MultiModelConfigService
            mm_config_service = MultiModelConfigService()
            
            # 验证服务方法
            model_configs = mm_config_service.get_all_model_configs()
            self.assertIsInstance(model_configs, dict)
            
            # 测试A/B测试服务导入
            from src.services.ab_testing_service import get_ab_testing_service
            ab_service = get_ab_testing_service()
            self.assertIsNotNone(ab_service)
            
        except Exception as e:
            self.fail(f"多模型服务冒烟测试失败: {e}")
    
    async def test_service_initialization_smoke(self):
        """服务初始化冒烟测试"""
        try:
            # 测试所有服务的初始化
            services_to_test = [
                ("故障容忍服务", "src.services.fault_tolerance_service", "FaultToleranceService"),
                ("多模型配置服务", "src.services.multi_model_config_service", "MultiModelConfigService"),
                ("上下文优化服务", "src.services.context_optimization_service", "ContextOptimizationService"),
                ("监控仪表板服务", "src.services.monitoring_dashboard_service", "MonitoringDashboardService"),
                ("A/B测试服务", "src.services.ab_testing_service", "ABTestingService"),
            ]
            
            for service_name, module_path, class_name in services_to_test:
                try:
                    module = __import__(module_path, fromlist=[class_name])
                    service_class = getattr(module, class_name)
                    instance = service_class()
                    self.assertIsNotNone(instance, f"{service_name} 初始化成功")
                except Exception as e:
                    self.fail(f"{service_name} 初始化失败: {e}")
                    
        except Exception as e:
            self.fail(f"服务初始化冒烟测试失败: {e}")


if __name__ == '__main__':
    import unittest
    unittest.main()