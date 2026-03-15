#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控系统集成测试

测试监控仪表板服务与其他系统组件的集成：
1. 监控仪表板接收Token成本监控数据
2. 监控仪表板接收路由决策统计
3. 监控仪表板接收模型性能指标
4. 告警系统与监控仪表板的集成
5. 监控数据的持久化和查询
"""

import os
import sys
import time
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_framework import RANGENTestCase, AsyncTestCase


class TestMonitoringDashboardIntegration(RANGENTestCase):
    """测试监控仪表板服务集成"""
    
    def test_monitoring_dashboard_import(self):
        """测试监控仪表板服务导入"""
        try:
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, Alert, AlertConfig
            )
            self.assertTrue(True, "监控仪表板服务导入成功")
        except ImportError as e:
            self.fail(f"监控仪表板服务导入失败: {e}")
    
    def test_metric_data_structure(self):
        """测试指标数据结构"""
        try:
            from src.services.monitoring_dashboard_service import MetricData, MetricType
            
            # 创建指标数据
            metric = MetricData(
                metric_type=MetricType.RESPONSE_TIME,
                value=150.5,
                timestamp=time.time(),  # float类型的时间戳
                model_id="deepseek-model",
                metadata={"task_type": "general", "user_id": "test_user_001"}
            )
            
            # 验证数据结构
            self.assertEqual(metric.metric_type, MetricType.RESPONSE_TIME)
            self.assertEqual(metric.value, 150.5)
            self.assertEqual(metric.model_id, "deepseek-model")
            self.assertIsInstance(metric.timestamp, float)
            self.assertIn("task_type", metric.metadata)
            
        except Exception as e:
            self.fail(f"指标数据结构测试失败: {e}")


class TestTokenCostMonitoringIntegration(AsyncTestCase):
    """测试Token成本监控与仪表板集成"""
    
    async def test_token_cost_metrics_to_dashboard(self):
        """测试Token成本指标发送到仪表板"""
        try:
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, MetricType
            )
            from src.services.token_cost_monitor import TokenCostMonitor
            from datetime import datetime
            
            # 创建服务实例
            dashboard = MonitoringDashboardService()
            cost_monitor = TokenCostMonitor()
            
            # 启动监控服务
            dashboard.start()
            
            # 模拟Token使用记录
            usage = cost_monitor.record_usage(
                request_id="integration_test_001",
                model="deepseek-chat",
                prompt_tokens=1200,
                completion_tokens=800,
                session_id="session_test_001"
            )
            
            # 创建成本指标数据
            cost_metric = MetricData(
                metric_type=MetricType.COST,
                value=usage.cost,
                timestamp=time.time(),
                model_id="deepseek-chat",
                metadata={
                    "request_id": "integration_test_001",
                    "prompt_tokens": 1200,
                    "completion_tokens": 800,
                    "total_tokens": 2000
                }
            )
            
            # 发送指标到仪表板
            dashboard.record_metric(cost_metric)
            
            # 获取当前指标
            current_metrics = dashboard.get_current_metrics()
            self.assertIsInstance(current_metrics, list)
            
            # 验证指标数量增加
            self.assertGreater(len(current_metrics), 0)
            
            # 停止监控服务
            dashboard.stop()
            
        except Exception as e:
            self.fail(f"Token成本指标仪表板集成测试失败: {e}")


class TestRoutingMetricsIntegration(AsyncTestCase):
    """测试路由指标与监控集成"""
    
    async def test_routing_decision_metrics(self):
        """测试路由决策指标监控"""
        try:
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, MetricType
            )
            from src.services.intelligent_model_router import (
                IntelligentModelRouter, TaskType, TaskContext
            )
            from datetime import datetime
            
            # 创建服务实例
            dashboard = MonitoringDashboardService()
            router = IntelligentModelRouter()
            
            # 启动监控服务
            dashboard.start()
            
            # 创建测试任务
            task_context = TaskContext(
                task_type=TaskType.GENERAL,
                estimated_tokens=500,
                priority=5
            )
            
            # 执行路由决策
            decision = await router.route(task_context)
            
            # 创建路由决策指标
            routing_metric = MetricData(
                metric_type=MetricType.SUCCESS_RATE,  # 使用成功率指标类型
                value=1.0,  # 二进制指标：1=决策完成
                timestamp=time.time(),
                model_id=decision.selected_model,
                metadata={
                    "task_type": task_context.task_type.value,
                    "estimated_tokens": task_context.estimated_tokens,
                    "selected_model": decision.selected_model,
                    "alternative_models": str(decision.alternative_models),
                    "routing_time_ms": getattr(decision, 'routing_time_ms', 0),
                    "metric_name": "routing_decision"  # 原始指标名称存储在metadata中
                }
            )
            
            # 发送指标到仪表板
            dashboard.record_metric(routing_metric)
            
            # 获取路由统计
            routing_stats = router.get_routing_stats()
            
            # 创建路由统计指标
            stats_metric = MetricData(
                metric_type=MetricType.MODEL_USAGE,  # 使用模型使用率指标类型
                value=routing_stats.get('total_routes', 0),
                timestamp=time.time(),
                model_id="routing_system",
                metadata={**routing_stats, "metric_name": "routing_stats_total"}
            )
            
            dashboard.record_metric(stats_metric)
            
            # 验证仪表板有数据
            summary = dashboard.get_dashboard_summary()
            self.assertIsInstance(summary, dict)
            self.assertIn('total_metrics', summary)
            
            # 停止监控服务
            dashboard.stop()
            
        except Exception as e:
            self.fail(f"路由决策指标监控测试失败: {e}")


class TestAlertSystemIntegration(AsyncTestCase):
    """测试告警系统集成"""
    
    async def test_cost_alert_generation(self):
        """测试成本告警生成"""
        try:
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, Alert, AlertConfig, MetricType, AlertLevel
            )
            from src.services.token_cost_monitor import TokenCostMonitor
            from datetime import datetime
            
            # 创建服务实例
            dashboard = MonitoringDashboardService()
            cost_monitor = TokenCostMonitor()
            
            # 启动监控服务
            dashboard.start()
            
            # 创建成本告警配置
            alert_config = AlertConfig(
                metric_type=MetricType.COST,
                threshold=100.0,  # $100阈值
                alert_level=AlertLevel.WARNING,
                duration_seconds=300,  # 5分钟
                notification_channels=["email", "slack"],
                enabled=True,
                cooldown_seconds=600  # 10分钟冷却
            )
            
            # 添加告警配置
            dashboard.add_alert_config(alert_config)
            
            # 模拟高成本使用
            for i in range(5):
                cost_monitor.record_usage(
                    request_id=f"high_cost_test_{i}",
                    model="deepseek-chat",
                    prompt_tokens=50000,  # 高token数
                    completion_tokens=25000,
                    session_id="high_cost_session"
                )
            
            # 获取活动告警
            active_alerts = dashboard.get_active_alerts()
            self.assertIsInstance(active_alerts, list)
            
            # 检查是否有成本相关告警
            cost_alerts = [
                alert for alert in active_alerts 
                if alert.metric_type == MetricType.COST
            ]
            
            # 记录告警统计
            if cost_alerts:
                print(f"检测到 {len(cost_alerts)} 个成本告警")
            
            # 停止监控服务
            dashboard.stop()
            
        except Exception as e:
            self.fail(f"成本告警生成测试失败: {e}")


class TestMultiServiceMonitoringIntegration(AsyncTestCase):
    """测试多服务监控集成"""
    
    async def test_comprehensive_monitoring_workflow(self):
        """测试综合监控工作流程"""
        try:
            # 导入所需服务
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, AlertConfig, MetricType, AlertLevel
            )
            from src.services.intelligent_model_router import (
                IntelligentModelRouter, TaskType, TaskContext
            )
            from src.services.token_cost_monitor import TokenCostMonitor
            from src.services.cost_control import CostController
            from datetime import datetime
            
            # 创建所有服务实例
            dashboard = MonitoringDashboardService()
            router = IntelligentModelRouter()
            cost_monitor = TokenCostMonitor()
            cost_control = CostController()
            
            # 启动监控服务
            dashboard.start()
            
            # 1. 配置告警
            cost_alert_config = AlertConfig(
                metric_type=MetricType.COST,
                threshold=50.0,  # 每日$50限制
                alert_level=AlertLevel.CRITICAL,
                duration_seconds=86400,  # 24小时
                notification_channels=["email", "slack", "pagerduty"],
                enabled=True,
                cooldown_seconds=3600  # 1小时冷却
            )
            dashboard.add_alert_config(cost_alert_config)
            
            # 2. 模拟多个请求
            request_count = 3
            for i in range(request_count):
                # 创建任务
                task_context = TaskContext(
                    task_type=TaskType.GENERAL,
                    estimated_tokens=800 + i * 200,
                    priority=5
                )
                
                # 路由决策
                decision = await router.route(task_context)
                selected_model = decision.selected_model
                
                # 模拟Token使用
                usage = cost_monitor.record_usage(
                    request_id=f"monitoring_test_{i}",
                    model=selected_model,
                    prompt_tokens=700 + i * 150,
                    completion_tokens=300 + i * 100,
                    session_id="monitoring_session"
                )
                
                # 发送路由指标
                routing_metric = MetricData(
                    metric_type=MetricType.SUCCESS_RATE,
                    value=1.0,
                    timestamp=time.time(),
                    model_id=selected_model,
                    metadata={
                        "request_id": f"monitoring_test_{i}",
                        "task_type": task_context.task_type.value,
                        "metric_name": "routing_success"
                    }
                )
                dashboard.record_metric(routing_metric)
                
                # 发送成本指标
                cost_metric = MetricData(
                    metric_type=MetricType.COST,
                    value=usage.cost,
                    timestamp=time.time(),
                    model_id=selected_model,
                    metadata={
                        "request_id": f"monitoring_test_{i}",
                        "total_tokens": usage.prompt_tokens + usage.completion_tokens,
                        "metric_name": "request_cost_usd"
                    }
                )
                dashboard.record_metric(cost_metric)
                
                # 短暂延迟
                await asyncio.sleep(0.1)
            
            # 3. 获取综合统计
            dashboard_summary = dashboard.get_dashboard_summary()
            self.assertIsInstance(dashboard_summary, dict)
            
            # 验证关键指标存在
            expected_metrics = [
                'total_metrics', 'active_alerts', 'service_status'
            ]
            for metric in expected_metrics:
                self.assertIn(metric, dashboard_summary)
            
            # 4. 获取活动告警
            active_alerts = dashboard.get_active_alerts()
            self.assertIsInstance(active_alerts, list)
            
            # 5. 获取路由统计
            routing_stats = router.get_routing_stats()
            self.assertIsInstance(routing_stats, dict)
            
            # 6. 获取成本统计
            cost_stats = cost_monitor.get_stats()
            self.assertIsInstance(cost_stats, dict)
            
            # 7. 获取成本控制状态
            budget_check = cost_control.check_budget()
            self.assertIsInstance(budget_check, dict)
            
            # 停止监控服务
            dashboard.stop()
            
            print(f"综合监控测试完成:")
            print(f"  记录指标数: {dashboard_summary.get('total_metrics', 0)}")
            print(f"  活动告警数: {len(active_alerts)}")
            print(f"  总路由次数: {routing_stats.get('total_routes', 0)}")
            print(f"  总成本: ${cost_stats.get('total_cost', 0.0):.4f}")
            
        except Exception as e:
            self.fail(f"综合监控工作流程测试失败: {e}")


if __name__ == '__main__':
    import unittest
    unittest.main()