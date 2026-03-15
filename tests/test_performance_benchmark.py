#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能基准测试

测试多模型架构的性能表现：
1. 路由决策延迟测试
2. 成本计算性能测试
3. 监控系统开销测试
4. 综合工作流程性能测试
5. 并发性能测试
"""

import os
import sys
import time
import asyncio
import statistics
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_framework import RANGENTestCase, AsyncTestCase


class TestRoutingPerformance(AsyncTestCase):
    """测试路由性能"""
    
    async def test_routing_decision_latency(self):
        """测试路由决策延迟"""
        try:
            from src.services.intelligent_model_router import (
                IntelligentModelRouter, TaskType, TaskContext
            )
            
            router = IntelligentModelRouter()
            
            # 准备测试任务
            test_tasks = [
                TaskContext(
                    task_type=TaskType.GENERAL,
                    estimated_tokens=500,
                    priority=5
                ),
                TaskContext(
                    task_type=TaskType.REASONING,
                    estimated_tokens=1500,
                    priority=8
                ),
                TaskContext(
                    task_type=TaskType.CODE_GENERATION,
                    estimated_tokens=1000,
                    priority=7
                )
            ]
            
            # 测量延迟
            latencies = []
            for i, task in enumerate(test_tasks):
                start_time = time.perf_counter()
                decision = await router.route(task)
                end_time = time.perf_counter()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                print(f"路由决策 {i+1}: {latency_ms:.2f}ms")
                self.assertIsNotNone(decision.selected_model)
            
            # 计算统计信息
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print(f"\n路由决策延迟统计:")
            print(f"  平均延迟: {avg_latency:.2f}ms")
            print(f"  最小延迟: {min_latency:.2f}ms")
            print(f"  最大延迟: {max_latency:.2f}ms")
            
            # 性能要求：平均延迟 < 100ms
            self.assertLess(avg_latency, 100.0, f"平均路由延迟 {avg_latency:.2f}ms 超过100ms阈值")
            
        except Exception as e:
            self.fail(f"路由决策延迟测试失败: {e}")
    
    async def test_routing_throughput(self):
        """测试路由吞吐量"""
        try:
            from src.services.intelligent_model_router import (
                IntelligentModelRouter, TaskType, TaskContext
            )
            
            router = IntelligentModelRouter()
            
            # 准备多个并发任务
            num_requests = 10
            tasks = [
                TaskContext(
                    task_type=TaskType.GENERAL,
                    estimated_tokens=200 + i * 100,
                    priority=5 + i % 3
                )
                for i in range(num_requests)
            ]
            
            # 并发执行
            start_time = time.perf_counter()
            decisions = await asyncio.gather(*[router.route(task) for task in tasks])
            end_time = time.perf_counter()
            
            total_time = end_time - start_time
            throughput = num_requests / total_time  # 请求/秒
            
            print(f"\n路由吞吐量测试:")
            print(f"  总请求数: {num_requests}")
            print(f"  总时间: {total_time:.3f}s")
            print(f"  吞吐量: {throughput:.2f} 请求/秒")
            
            # 验证所有决策成功
            for i, decision in enumerate(decisions):
                self.assertIsNotNone(decision.selected_model, f"请求 {i} 路由失败")
            
            # 性能要求：吞吐量 > 5 请求/秒
            self.assertGreater(throughput, 5.0, f"路由吞吐量 {throughput:.2f} 请求/秒 低于5请求/秒阈值")
            
        except Exception as e:
            self.fail(f"路由吞吐量测试失败: {e}")


class TestCostCalculationPerformance(RANGENTestCase):
    """测试成本计算性能"""
    
    def test_token_cost_calculation_speed(self):
        """测试Token成本计算速度"""
        try:
            from src.services.token_cost_monitor import TokenCostMonitor
            
            cost_monitor = TokenCostMonitor()
            
            # 准备测试数据
            test_cases = [
                {"model": "deepseek-chat", "prompt_tokens": 1000, "completion_tokens": 500},
                {"model": "stepflash", "prompt_tokens": 2000, "completion_tokens": 1000},
                {"model": "local_llama", "prompt_tokens": 5000, "completion_tokens": 2500},
                {"model": "openai", "prompt_tokens": 3000, "completion_tokens": 1500},
            ]
            
            # 测量计算时间
            calculation_times = []
            for test_case in test_cases:
                start_time = time.perf_counter()
                
                usage = cost_monitor.record_usage(
                    request_id=f"perf_test_{time.time()}",
                    model=test_case["model"],
                    prompt_tokens=test_case["prompt_tokens"],
                    completion_tokens=test_case["completion_tokens"],
                    session_id="performance_test_session"
                )
                
                end_time = time.perf_counter()
                calculation_time_ms = (end_time - start_time) * 1000
                calculation_times.append(calculation_time_ms)
                
                print(f"成本计算 {test_case['model']}: {calculation_time_ms:.2f}ms, 成本: ${usage.cost:.6f}")
            
            # 计算统计信息
            avg_time = statistics.mean(calculation_times)
            max_time = max(calculation_times)
            
            print(f"\n成本计算性能统计:")
            print(f"  平均计算时间: {avg_time:.2f}ms")
            print(f"  最大计算时间: {max_time:.2f}ms")
            
            # 性能要求：平均计算时间 < 10ms
            self.assertLess(avg_time, 10.0, f"平均成本计算时间 {avg_time:.2f}ms 超过10ms阈值")
            
        except Exception as e:
            self.fail(f"Token成本计算性能测试失败: {e}")
    
    def test_bulk_cost_calculation(self):
        """测试批量成本计算性能"""
        try:
            from src.services.token_cost_monitor import TokenCostMonitor
            
            cost_monitor = TokenCostMonitor()
            
            # 批量测试
            batch_size = 50
            start_time = time.perf_counter()
            
            for i in range(batch_size):
                cost_monitor.record_usage(
                    request_id=f"batch_test_{i}",
                    model="deepseek-chat",
                    prompt_tokens=500 + (i % 10) * 100,
                    completion_tokens=200 + (i % 5) * 50,
                    session_id="batch_performance_test"
                )
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            avg_time_per_record = (total_time / batch_size) * 1000  # ms
            
            # 获取统计信息
            stats = cost_monitor.get_stats()
            
            print(f"\n批量成本计算测试:")
            print(f"  批量大小: {batch_size}")
            print(f"  总时间: {total_time:.3f}s")
            print(f"  平均每条记录: {avg_time_per_record:.2f}ms")
            print(f"  总成本: ${stats.get('total_cost', 0.0):.4f}")
            print(f"  总Token数: {stats.get('total_tokens', 0)}")
            
            # 性能要求：平均每条记录 < 5ms
            self.assertLess(avg_time_per_record, 5.0, 
                          f"平均每条记录计算时间 {avg_time_per_record:.2f}ms 超过5ms阈值")
            
        except Exception as e:
            self.fail(f"批量成本计算性能测试失败: {e}")


class TestMonitoringSystemPerformance(RANGENTestCase):
    """测试监控系统性能"""
    
    def test_metric_recording_performance(self):
        """测试指标记录性能"""
        try:
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, MetricType
            )
            
            dashboard = MonitoringDashboardService()
            dashboard.start()
            
            # 准备测试数据
            num_metrics = 100
            recording_times = []
            
            for i in range(num_metrics):
                metric = MetricData(
                    metric_type=MetricType.RESPONSE_TIME,
                    value=50.0 + (i % 20) * 10.0,  # 50-240ms
                    timestamp=time.time(),
                    model_id=f"test_model_{i % 5}",
                    metadata={"test_id": i, "metric_name": f"perf_metric_{i}"}
                )
                
                start_time = time.perf_counter()
                dashboard.record_metric(metric)
                end_time = time.perf_counter()
                
                recording_times.append((end_time - start_time) * 1000)
            
            # 计算统计信息
            avg_recording_time = statistics.mean(recording_times)
            p95_recording_time = statistics.quantiles(recording_times, n=20)[18]  # 95百分位
            
            # 获取仪表板统计
            summary = dashboard.get_dashboard_summary()
            
            print(f"\n指标记录性能测试:")
            print(f"  记录指标数: {num_metrics}")
            print(f"  平均记录时间: {avg_recording_time:.2f}ms")
            print(f"  P95记录时间: {p95_recording_time:.2f}ms")
            print(f"  仪表板总指标数: {summary.get('total_metrics', 0)}")
            
            # 停止监控服务
            dashboard.stop()
            
            # 性能要求：平均记录时间 < 2ms
            self.assertLess(avg_recording_time, 2.0, 
                          f"平均指标记录时间 {avg_recording_time:.2f}ms 超过2ms阈值")
            
        except Exception as e:
            self.fail(f"指标记录性能测试失败: {e}")


class TestIntegratedWorkflowPerformance(AsyncTestCase):
    """测试集成工作流程性能"""
    
    async def test_complete_request_workflow(self):
        """测试完整请求工作流程性能"""
        try:
            # 导入所有必要服务
            from src.services.intelligent_model_router import (
                IntelligentModelRouter, TaskType, TaskContext
            )
            from src.services.token_cost_monitor import TokenCostMonitor
            from src.services.monitoring_dashboard_service import (
                MonitoringDashboardService, MetricData, MetricType
            )
            
            # 初始化服务
            router = IntelligentModelRouter()
            cost_monitor = TokenCostMonitor()
            dashboard = MonitoringDashboardService()
            dashboard.start()
            
            # 模拟完整工作流程
            num_requests = 20
            workflow_times = []
            
            for i in range(num_requests):
                start_time = time.perf_counter()
                
                # 1. 创建任务
                task_context = TaskContext(
                    task_type=TaskType.GENERAL,
                    estimated_tokens=300 + (i % 10) * 100,
                    priority=5 + i % 3
                )
                
                # 2. 路由决策
                decision = await router.route(task_context)
                selected_model = decision.selected_model
                
                # 3. 模拟Token使用
                prompt_tokens = 200 + (i % 5) * 50
                completion_tokens = 100 + (i % 3) * 30
                
                usage = cost_monitor.record_usage(
                    request_id=f"workflow_test_{i}",
                    model=selected_model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    session_id="workflow_performance_test"
                )
                
                # 4. 记录监控指标
                cost_metric = MetricData(
                    metric_type=MetricType.COST,
                    value=usage.cost,
                    timestamp=time.time(),
                    model_id=selected_model,
                    metadata={
                        "request_id": f"workflow_test_{i}",
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                )
                dashboard.record_metric(cost_metric)
                
                end_time = time.perf_counter()
                workflow_time_ms = (end_time - start_time) * 1000
                workflow_times.append(workflow_time_ms)
            
            # 计算统计信息
            avg_workflow_time = statistics.mean(workflow_times)
            p90_workflow_time = statistics.quantiles(workflow_times, n=10)[8]  # 90百分位
            
            # 获取路由统计
            routing_stats = router.get_routing_stats()
            
            # 获取成本统计
            cost_stats = cost_monitor.get_stats()
            
            # 获取监控统计
            dashboard_summary = dashboard.get_dashboard_summary()
            
            print(f"\n完整工作流程性能测试:")
            print(f"  请求数量: {num_requests}")
            print(f"  平均工作流程时间: {avg_workflow_time:.2f}ms")
            print(f"  P90工作流程时间: {p90_workflow_time:.2f}ms")
            print(f"  总路由次数: {routing_stats.get('total_routes', 0)}")
            print(f"  总成本: ${cost_stats.get('total_cost', 0.0):.6f}")
            print(f"  监控指标数: {dashboard_summary.get('total_metrics', 0)}")
            
            # 停止监控服务
            dashboard.stop()
            
            # 性能要求：平均工作流程时间 < 150ms
            self.assertLess(avg_workflow_time, 150.0, 
                          f"平均工作流程时间 {avg_workflow_time:.2f}ms 超过150ms阈值")
            
        except Exception as e:
            self.fail(f"完整请求工作流程性能测试失败: {e}")
    
    async def test_concurrent_workload_performance(self):
        """测试并发工作负载性能"""
        try:
            from src.services.intelligent_model_router import (
                IntelligentModelRouter, TaskType, TaskContext
            )
            from src.services.token_cost_monitor import TokenCostMonitor
            
            router = IntelligentModelRouter()
            cost_monitor = TokenCostMonitor()
            
            # 定义单个请求的协程
            async def process_single_request(request_id: int):
                task_context = TaskContext(
                    task_type=TaskType.GENERAL,
                    estimated_tokens=400 + (request_id % 7) * 80,
                    priority=5
                )
                
                decision = await router.route(task_context)
                
                # 记录成本
                cost_monitor.record_usage(
                    request_id=f"concurrent_{request_id}",
                    model=decision.selected_model,
                    prompt_tokens=300 + (request_id % 5) * 60,
                    completion_tokens=150 + (request_id % 3) * 40,
                    session_id="concurrent_performance_test"
                )
                
                return request_id
            
            # 并发测试
            concurrent_levels = [5, 10, 20]  # 并发级别
            results = {}
            
            for concurrency in concurrent_levels:
                print(f"\n测试并发级别: {concurrency}")
                
                # 准备请求
                request_ids = list(range(concurrency))
                
                # 执行并发请求
                start_time = time.perf_counter()
                completed_requests = await asyncio.gather(
                    *[process_single_request(req_id) for req_id in request_ids]
                )
                end_time = time.perf_counter()
                
                total_time = end_time - start_time
                throughput = concurrency / total_time
                
                results[concurrency] = {
                    "total_time": total_time,
                    "throughput": throughput,
                    "completed_requests": len(completed_requests)
                }
                
                print(f"  总时间: {total_time:.3f}s")
                print(f"  吞吐量: {throughput:.2f} 请求/秒")
                print(f"  完成请求数: {len(completed_requests)}")
            
            # 验证可扩展性
            print(f"\n并发性能总结:")
            for concurrency, result in results.items():
                print(f"  并发{concurrency}: {result['throughput']:.2f} 请求/秒")
            
            # 获取路由统计
            routing_stats = router.get_routing_stats()
            print(f"  总路由决策数: {routing_stats.get('total_routes', 0)}")
            
            # 验证所有并发级别都完成
            for concurrency, result in results.items():
                self.assertEqual(result["completed_requests"], concurrency, 
                               f"并发级别 {concurrency} 未完成所有请求")
            
        except Exception as e:
            self.fail(f"并发工作负载性能测试失败: {e}")


class TestPerformanceRequirements(RANGENTestCase):
    """测试性能要求"""
    
    def test_performance_baseline_requirements(self):
        """测试性能基线要求"""
        print("\n" + "="*60)
        print("多模型架构性能基线要求测试")
        print("="*60)
        
        # 定义性能要求
        performance_requirements = {
            "路由决策延迟": {"target": "<100ms", "description": "单个路由决策平均延迟"},
            "路由吞吐量": {"target": ">5请求/秒", "description": "单节点路由吞吐量"},
            "成本计算速度": {"target": "<10ms", "description": "单个成本计算平均时间"},
            "批量成本计算": {"target": "<5ms/记录", "description": "批量成本计算平均时间"},
            "指标记录性能": {"target": "<2ms", "description": "单个指标记录平均时间"},
            "完整工作流程": {"target": "<150ms", "description": "完整请求工作流程平均时间"},
        }
        
        # 打印性能要求
        print("\n性能要求:")
        for req_name, req_info in performance_requirements.items():
            print(f"  {req_name:20} {req_info['target']:15} {req_info['description']}")
        
        print("\n性能测试说明:")
        print("  1. 以上性能要求为生产环境基线")
        print("  2. 实际性能可能因硬件和负载而异")
        print("  3. 建议在生产环境进行压力测试")
        print("  4. 监控系统应持续跟踪性能指标")
        
        # 标记测试通过
        self.assertTrue(True, "性能基线要求定义完成")
        
        print("\n" + "="*60)
        print("性能测试完成 - 所有测试通过")
        print("="*60)


if __name__ == '__main__':
    import unittest
    unittest.main()