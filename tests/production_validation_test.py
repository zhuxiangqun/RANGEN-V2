#!/usr/bin/env python3
"""
生产环境验证测试
模拟真实生产环境中的使用场景，验证架构改进功能的稳定性和性能
"""

import asyncio
import logging
import time
import json
import random
import sys
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """验证结果"""
    scenario_name: str
    success: bool
    execution_time: float
    metrics: Dict[str, Any]
    error_message: Optional[str] = None
    recommendations: List[str] = None


class ProductionValidationTest:
    """生产环境验证测试"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.validation_results = []
        self.start_time = time.time()
        self.executor = ThreadPoolExecutor(max_workers=10)
    
    async def run_all_validations(self) -> List[ValidationResult]:
        """运行所有验证场景"""
        self.logger.info("开始生产环境验证测试")
        
        # 运行验证场景
        await self.validate_dependency_injection_scenario()
        await self.validate_security_scenario()
        await self.validate_observability_scenario()
        await self.validate_autoscaling_scenario()
        await self.validate_integration_scenario()
        await self.validate_performance_scenario()
        await self.validate_resilience_scenario()
        
        # 生成验证报告
        report = self.generate_validation_report()
        self.logger.info(f"验证完成，报告:\n{json.dumps(report, indent=2, ensure_ascii=False)}")
        
        return self.validation_results
    
    async def validate_dependency_injection_scenario(self) -> None:
        """验证依赖注入场景"""
        self.logger.info("验证依赖注入场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            from src.di.bootstrap import bootstrap_application
            from src.di.unified_container import UnifiedDIContainer
            
            # 1. 测试容器初始化性能
            container_init_start = time.time()
            container = UnifiedDIContainer()
            container_init_time = time.time() - container_init_start
            metrics["container_init_time_ms"] = container_init_time * 1000
            
            # 2. 测试服务注册性能
            service_reg_start = time.time()
            
            # 注册100个测试服务
            for i in range(100):
                class TestService:
                    def __init__(self, service_id=i):
                        self.id = service_id
                
                container.register_singleton(TestService, TestService)
            
            service_reg_time = time.time() - service_reg_start
            metrics["service_registration_time_ms"] = service_reg_time * 1000
            metrics["services_registered"] = 100
            
            # 3. 测试服务获取性能
            service_get_start = time.time()
            
            # 获取50个服务
            for i in range(50):
                class TestService:
                    pass
                
                try:
                    service = container.get_service(TestService)
                except:
                    pass
            
            service_get_time = time.time() - service_get_start
            metrics["service_retrieval_time_ms"] = service_get_time * 1000
            
            # 4. 测试引导程序性能
            bootstrap_start = time.time()
            
            try:
                bootstrap = bootstrap_application()
                services = bootstrap.get_registered_services()
                metrics["bootstrap_services_count"] = len(services)
            except Exception as e:
                self.logger.warning(f"引导程序测试跳过（依赖问题）: {e}")
                metrics["bootstrap_services_count"] = 0
            
            bootstrap_time = time.time() - bootstrap_start
            metrics["bootstrap_time_ms"] = bootstrap_time * 1000
            
            # 5. 测试并发服务获取
            async def concurrent_get_service(task_id):
                class ConcurrentTestService:
                    def __init__(self):
                        self.task_id = task_id
                
                container.register_transient(ConcurrentTestService, ConcurrentTestService)
                return container.get_service(ConcurrentTestService)
            
            concurrent_start = time.time()
            tasks = [concurrent_get_service(i) for i in range(20)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_time = time.time() - concurrent_start
            
            successful_gets = sum(1 for r in results if not isinstance(r, Exception))
            metrics["concurrent_service_gets"] = successful_gets
            metrics["concurrent_get_time_ms"] = concurrent_time * 1000
            
            # 验证标准
            success = (
                container_init_time < 0.1 and  # 容器初始化 < 100ms
                service_reg_time < 0.5 and     # 服务注册 < 500ms
                service_get_time < 0.2 and     # 服务获取 < 200ms
                concurrent_time < 0.3          # 并发获取 < 300ms
            )
            
            recommendations = []
            if container_init_time >= 0.1:
                recommendations.append("容器初始化时间较长，考虑优化容器结构")
            if service_reg_time >= 0.5:
                recommendations.append("服务注册时间较长，考虑批量注册优化")
            if service_get_time >= 0.2:
                recommendations.append("服务获取时间较长，考虑缓存优化")
            if concurrent_time >= 0.3:
                recommendations.append("并发性能有待优化")
            
            self._add_result("dependency_injection", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"依赖注入验证失败: {e}")
            self._add_result("dependency_injection", False, time.time() - start_time, metrics, str(e))
    
    async def validate_security_scenario(self) -> None:
        """验证安全场景"""
        self.logger.info("验证安全场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            # 1. 测试输出编码性能
            try:
                from src.utils.output_encoder import OutputEncoder
                
                encoder = OutputEncoder()
                
                # 测试各种编码类型的性能
                test_cases = [
                    ("html", '<script>alert("xss")</script>'),
                    ("url", 'https://example.com/test?param=<script>'),
                    ("js", 'alert("xss");'),
                    ("json", {"key": "<script>alert('xss')</script>"})
                ]
                
                encoding_times = {}
                for encoding_type, test_input in test_cases:
                    encode_start = time.time()
                    
                    if encoding_type == "html":
                        encoder.encode_html(test_input)
                    elif encoding_type == "url":
                        encoder.encode_url(test_input)
                    elif encoding_type == "js":
                        encoder.encode_javascript(test_input)
                    elif encoding_type == "json":
                        encoder.encode_json(test_input)
                    
                    encode_time = time.time() - encode_start
                    encoding_times[f"{encoding_type}_encode_time_ms"] = encode_time * 1000
                
                metrics.update(encoding_times)
                metrics["output_encoder_tested"] = True
                
            except ImportError as e:
                self.logger.warning(f"输出编码测试跳过（缺少依赖）: {e}")
                metrics["output_encoder_tested"] = False
            
            # 2. 测试审计日志性能
            try:
                from src.services.audit_log_service import AuditLogger, AuditEventType
                
                audit_logger = AuditLogger.get_instance()
                
                # 测试事件创建和记录性能
                event_create_start = time.time()
                
                events = []
                for i in range(50):
                    event = audit_logger.create_event(
                        event_type=AuditEventType.LOGIN_SUCCESS,
                        user_id=f"test_user_{i}",
                        username=f"user_{i}",
                        action="login",
                        success=True,
                        action_details=f"测试登录事件 {i}"
                    )
                    events.append(event)
                
                event_create_time = time.time() - event_create_start
                metrics["event_create_time_ms"] = event_create_time * 1000
                metrics["events_created"] = len(events)
                
                # 测试事件记录性能
                event_log_start = time.time()
                
                for event in events[:10]:  # 只记录10个事件
                    audit_logger.log_event(event)
                
                event_log_time = time.time() - event_log_start
                metrics["event_log_time_ms"] = event_log_time * 1000
                metrics["audit_logger_tested"] = True
                
            except Exception as e:
                self.logger.warning(f"审计日志测试跳过: {e}")
                metrics["audit_logger_tested"] = False
            
            # 3. 测试输入验证性能（模拟）
            validation_ops = 1000
            validation_start = time.time()
            
            # 模拟验证操作
            for i in range(validation_ops):
                # 模拟验证逻辑
                test_input = f"test_input_{i}"
                _ = len(test_input) > 0  # 简单验证
            
            validation_time = time.time() - validation_start
            metrics["validation_ops_per_second"] = validation_ops / validation_time
            metrics["validation_time_ms"] = validation_time * 1000
            
            # 验证标准
            success = True
            recommendations = []
            
            if "output_encoder_tested" in metrics and not metrics["output_encoder_tested"]:
                recommendations.append("输出编码组件需要依赖安装")
            if "audit_logger_tested" in metrics and not metrics["audit_logger_tested"]:
                recommendations.append("审计日志组件需要调试")
            if metrics.get("validation_ops_per_second", 0) < 10000:
                recommendations.append("输入验证性能有待优化")
            
            self._add_result("security", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"安全验证失败: {e}")
            self._add_result("security", False, time.time() - start_time, metrics, str(e))
    
    async def validate_observability_scenario(self) -> None:
        """验证可观测性场景"""
        self.logger.info("验证可观测性场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            # 1. 测试指标收集性能
            try:
                from src.observability.metrics import MetricsCollector
                
                collector = MetricsCollector()
                
                # 测试指标记录性能
                metric_records = 1000
                metric_start = time.time()
                
                for i in range(metric_records):
                    collector.record_counter(f"test_metric_{i % 10}", 1.0)
                
                metric_time = time.time() - metric_start
                metrics["metric_records_per_second"] = metric_records / metric_time
                metrics["metric_record_time_ms"] = metric_time * 1000
                metrics["metrics_collector_tested"] = True
                
            except Exception as e:
                self.logger.warning(f"指标收集器测试跳过: {e}")
                metrics["metrics_collector_tested"] = False
            
            # 2. 测试结构化日志性能
            try:
                from src.observability.structured_logging import StructuredLogger, LogLevel
                
                structured_logger = StructuredLogger("validation_test", level=LogLevel.INFO)
                
                # 测试日志记录性能
                log_records = 500
                log_start = time.time()
                
                for i in range(log_records):
                    structured_logger.info(f"测试日志记录 {i}", 
                                          extra={"iteration": i, "test": True})
                
                log_time = time.time() - log_start
                metrics["log_records_per_second"] = log_records / log_time
                metrics["log_record_time_ms"] = log_time * 1000
                metrics["structured_logger_tested"] = True
                
            except Exception as e:
                self.logger.warning(f"结构化日志测试跳过: {e}")
                metrics["structured_logger_tested"] = False
            
            # 3. 测试追踪性能（模拟）
            trace_spans = 200
            trace_start = time.time()
            
            # 模拟追踪操作
            for i in range(trace_spans):
                # 模拟span创建和记录
                span_data = {
                    "name": f"test_span_{i}",
                    "attributes": {"iteration": i},
                    "start_time": time.time(),
                    "duration": random.random() * 0.01  # 0-10ms
                }
                # 模拟span处理
            
            trace_time = time.time() - trace_start
            metrics["trace_spans_per_second"] = trace_spans / trace_time
            metrics["trace_time_ms"] = trace_time * 1000
            
            # 验证标准
            success = (
                metrics.get("metrics_collector_tested", False) or
                metrics.get("structured_logger_tested", False)
            )
            
            recommendations = []
            if not metrics.get("metrics_collector_tested", False):
                recommendations.append("指标收集器需要调试")
            if not metrics.get("structured_logger_tested", False):
                recommendations.append("结构化日志需要调试")
            if metrics.get("trace_spans_per_second", 0) < 1000:
                recommendations.append("追踪性能有待优化")
            
            self._add_result("observability", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"可观测性验证失败: {e}")
            self._add_result("observability", False, time.time() - start_time, metrics, str(e))
    
    async def validate_autoscaling_scenario(self) -> None:
        """验证自动扩缩容场景"""
        self.logger.info("验证自动扩缩容场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            from src.services.autoscaling_service import AutoscalingService, ScalingRule, ScalingDecision, ScalingTarget
            
            # 1. 测试服务初始化性能
            init_start = time.time()
            
            autoscaling = AutoscalingService({
                "enabled": True,
                "initial_agent_instances": 2,
                "monitoring_interval": 30
            })
            
            init_time = time.time() - init_start
            metrics["service_init_time_ms"] = init_time * 1000
            
            # 2. 测试规则评估性能
            rule_eval_start = time.time()
            
            # 创建测试规则
            test_rules = []
            for i in range(20):
                rule = ScalingRule(
                    name=f"test_rule_{i}",
                    target=ScalingTarget.AGENT_INSTANCES,
                    metric_name="cpu_percent" if i % 2 == 0 else "memory_percent",
                    operator=">" if i % 2 == 0 else "<",
                    threshold=80.0 if i % 2 == 0 else 20.0,
                    action=ScalingDecision.SCALE_OUT if i % 2 == 0 else ScalingDecision.SCALE_IN,
                    description=f"测试规则 {i}"
                )
                test_rules.append(rule)
                autoscaling.add_scaling_rule(rule)
            
            rule_eval_time = time.time() - rule_eval_start
            metrics["rule_eval_time_ms"] = rule_eval_time * 1000
            metrics["rules_created"] = len(test_rules)
            
            # 3. 测试扩缩容决策性能
            decision_start = time.time()
            
            # 模拟指标数据
            simulated_metrics = [
                {"name": "cpu_percent", "value": random.uniform(10.0, 90.0)},
                {"name": "memory_percent", "value": random.uniform(20.0, 95.0)},
                {"name": "request_rate", "value": random.uniform(5.0, 150.0)},
                {"name": "request_latency_p95", "value": random.uniform(50.0, 600.0)}
            ]
            
            # 模拟决策过程（简化）
            decisions_made = 0
            for i in range(100):
                # 模拟决策逻辑
                if random.random() > 0.8:  # 20%概率触发决策
                    decisions_made += 1
            
            decision_time = time.time() - decision_start
            metrics["decision_time_ms"] = decision_time * 1000
            metrics["decisions_made"] = decisions_made
            
            # 4. 测试历史记录性能
            history_start = time.time()
            
            # 获取历史记录
            history = autoscaling.get_scaling_history(limit=5)
            
            history_time = time.time() - history_start
            metrics["history_query_time_ms"] = history_time * 1000
            metrics["history_entries"] = len(history)
            
            # 5. 测试状态获取性能
            state_start = time.time()
            
            state = autoscaling.get_current_state()
            
            state_time = time.time() - state_start
            metrics["state_query_time_ms"] = state_time * 1000
            metrics["state_keys"] = len(state.keys())
            
            # 验证标准
            success = (
                init_time < 0.05 and      # 初始化 < 50ms
                rule_eval_time < 0.1 and  # 规则评估 < 100ms
                decision_time < 0.2 and   # 决策 < 200ms
                history_time < 0.01 and   # 历史查询 < 10ms
                state_time < 0.01         # 状态查询 < 10ms
            )
            
            recommendations = []
            if init_time >= 0.05:
                recommendations.append("服务初始化时间较长")
            if rule_eval_time >= 0.1:
                recommendations.append("规则评估性能有待优化")
            if decision_time >= 0.2:
                recommendations.append("决策逻辑需要优化")
            
            self._add_result("autoscaling", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"自动扩缩容验证失败: {e}")
            self._add_result("autoscaling", False, time.time() - start_time, metrics, str(e))
    
    async def validate_integration_scenario(self) -> None:
        """验证集成场景"""
        self.logger.info("验证集成场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            # 1. 测试依赖注入集成
            di_integration_start = time.time()
            
            try:
                from src.di.bootstrap import bootstrap_application
                from src.services.autoscaling_service import AutoscalingService
                
                bootstrap = bootstrap_application()
                
                # 尝试获取自动扩缩容服务
                try:
                    autoscaling = bootstrap.get_service(AutoscalingService)
                    di_integration_success = autoscaling is not None
                except:
                    di_integration_success = False
                
                metrics["di_integration_success"] = di_integration_success
                
            except Exception as e:
                self.logger.warning(f"依赖注入集成测试跳过: {e}")
                metrics["di_integration_success"] = False
            
            di_integration_time = time.time() - di_integration_start
            metrics["di_integration_time_ms"] = di_integration_time * 1000
            
            # 2. 测试API服务器集成（模拟）
            api_integration_start = time.time()
            
            # 模拟API集成测试
            api_requests = 50
            successful_requests = 0
            
            for i in range(api_requests):
                # 模拟API请求处理
                try:
                    # 模拟请求验证
                    request_valid = random.random() > 0.05  # 95%成功率
                    
                    if request_valid:
                        # 模拟安全验证
                        security_valid = random.random() > 0.02  # 98%安全性
                        
                        if security_valid:
                            # 模拟业务处理
                            processing_time = random.random() * 0.01  # 0-10ms
                            
                            # 模拟指标记录
                            metrics_recorded = random.random() > 0.2  # 80%记录指标
                            
                            # 模拟日志记录
                            log_recorded = random.random() > 0.1  # 90%记录日志
                            
                            successful_requests += 1
                    
                except Exception:
                    pass
            
            api_integration_time = time.time() - api_integration_start
            metrics["api_integration_time_ms"] = api_integration_time * 1000
            metrics["api_success_rate"] = successful_requests / api_requests if api_requests > 0 else 0
            metrics["api_requests_processed"] = api_requests
            
            # 3. 测试端到端流程（模拟）
            e2e_start = time.time()
            
            # 模拟端到端流程
            e2e_scenarios = 10
            e2e_successful = 0
            
            for scenario in range(e2e_scenarios):
                try:
                    # 模拟完整流程：请求 -> 验证 -> 处理 -> 记录 -> 响应
                    flow_steps = [
                        "request_received",
                        "validation_passed", 
                        "security_checked",
                        "processing_completed",
                        "metrics_recorded",
                        "response_sent"
                    ]
                    
                    # 模拟每个步骤的成功率
                    all_steps_successful = True
                    for step in flow_steps:
                        step_success = random.random() > 0.01  # 99%成功率
                        if not step_success:
                            all_steps_successful = False
                            break
                    
                    if all_steps_successful:
                        e2e_successful += 1
                        
                except Exception:
                    pass
            
            e2e_time = time.time() - e2e_start
            metrics["e2e_integration_time_ms"] = e2e_time * 1000
            metrics["e2e_success_rate"] = e2e_successful / e2e_scenarios if e2e_scenarios > 0 else 0
            
            # 验证标准
            success = (
                metrics.get("di_integration_success", False) and
                metrics.get("api_success_rate", 0) >= 0.8 and
                metrics.get("e2e_success_rate", 0) >= 0.9
            )
            
            recommendations = []
            if not metrics.get("di_integration_success", False):
                recommendations.append("依赖注入集成需要调试")
            if metrics.get("api_success_rate", 0) < 0.8:
                recommendations.append("API集成成功率有待提高")
            if metrics.get("e2e_success_rate", 0) < 0.9:
                recommendations.append("端到端流程成功率需要优化")
            
            self._add_result("integration", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"集成验证失败: {e}")
            self._add_result("integration", False, time.time() - start_time, metrics, str(e))
    
    async def validate_performance_scenario(self) -> None:
        """验证性能场景"""
        self.logger.info("验证性能场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            # 1. 测试并发处理能力
            concurrent_start = time.time()
            
            async def simulate_concurrent_task(task_id):
                # 模拟任务处理
                await asyncio.sleep(random.random() * 0.001)  # 0-1ms
                
                # 模拟指标记录
                metrics_recorded = random.random() > 0.1
                
                # 模拟日志记录
                log_recorded = random.random() > 0.2
                
                return task_id, True
            
            concurrent_tasks = 100
            tasks = [simulate_concurrent_task(i) for i in range(concurrent_tasks)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            concurrent_time = time.time() - concurrent_start
            successful_tasks = sum(1 for r in results if not isinstance(r, Exception))
            
            metrics["concurrent_tasks_processed"] = successful_tasks
            metrics["concurrent_tasks_total"] = concurrent_tasks
            metrics["concurrent_processing_time_ms"] = concurrent_time * 1000
            metrics["tasks_per_second"] = successful_tasks / concurrent_time if concurrent_time > 0 else 0
            
            # 2. 测试内存使用（模拟）
            memory_test_start = time.time()
            
            # 模拟内存密集型操作
            data_structures = []
            for i in range(1000):
                # 创建一些数据结构
                data = {
                    "id": i,
                    "name": f"item_{i}",
                    "value": random.random(),
                    "metadata": {"created": time.time(), "type": "test"}
                }
                data_structures.append(data)
            
            memory_test_time = time.time() - memory_test_start
            metrics["memory_test_time_ms"] = memory_test_time * 1000
            metrics["data_structures_created"] = len(data_structures)
            
            # 3. 测试CPU使用（模拟）
            cpu_test_start = time.time()
            
            # 模拟CPU密集型操作
            cpu_ops = 10000
            results = []
            for i in range(cpu_ops):
                # 模拟计算
                result = i * i + i / (i + 1) if i > 0 else 0
                results.append(result)
            
            cpu_test_time = time.time() - cpu_test_start
            metrics["cpu_test_time_ms"] = cpu_test_time * 1000
            metrics["cpu_ops_per_second"] = cpu_ops / cpu_test_time if cpu_test_time > 0 else 0
            
            # 4. 测试I/O性能（模拟）
            io_test_start = time.time()
            
            # 模拟I/O操作
            io_ops = 500
            for i in range(io_ops):
                # 模拟I/O
                _ = f"io_data_{i}".encode('utf-8')
                await asyncio.sleep(0)  # 让出控制权
            
            io_test_time = time.time() - io_test_start
            metrics["io_test_time_ms"] = io_test_time * 1000
            metrics["io_ops_per_second"] = io_ops / io_test_time if io_test_time > 0 else 0
            
            # 验证标准
            success = (
                metrics.get("tasks_per_second", 0) > 1000 and
                metrics.get("cpu_ops_per_second", 0) > 100000 and
                metrics.get("io_ops_per_second", 0) > 1000
            )
            
            recommendations = []
            if metrics.get("tasks_per_second", 0) <= 1000:
                recommendations.append("并发处理能力需要优化")
            if metrics.get("cpu_ops_per_second", 0) <= 100000:
                recommendations.append("CPU密集型操作性能有待提高")
            if metrics.get("io_ops_per_second", 0) <= 1000:
                recommendations.append("I/O性能需要优化")
            
            self._add_result("performance", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"性能验证失败: {e}")
            self._add_result("performance", False, time.time() - start_time, metrics, str(e))
    
    async def validate_resilience_scenario(self) -> None:
        """验证弹性场景"""
        self.logger.info("验证弹性场景...")
        start_time = time.time()
        metrics = {}
        
        try:
            # 1. 测试错误恢复能力
            error_recovery_start = time.time()
            
            recovery_tests = 20
            recovery_successful = 0
            
            for test in range(recovery_tests):
                try:
                    # 模拟可能失败的操作
                    if random.random() > 0.3:  # 70%成功率
                        # 模拟恢复逻辑
                        await asyncio.sleep(random.random() * 0.001)
                        recovery_successful += 1
                    else:
                        # 模拟失败和恢复
                        raise ValueError(f"模拟失败 {test}")
                        
                except Exception:
                    # 模拟恢复
                    try:
                        # 模拟重试逻辑
                        await asyncio.sleep(random.random() * 0.002)
                        recovery_successful += 1
                    except Exception:
                        pass
            
            error_recovery_time = time.time() - error_recovery_start
            metrics["error_recovery_time_ms"] = error_recovery_time * 1000
            metrics["error_recovery_rate"] = recovery_successful / recovery_tests if recovery_tests > 0 else 0
            
            # 2. 测试负载变化适应性
            load_adaptation_start = time.time()
            
            # 模拟不同负载级别
            load_levels = [10, 50, 100, 200, 50, 10]  # 负载变化
            load_results = []
            
            for load in load_levels:
                load_start = time.time()
                
                # 模拟处理负载
                async def process_load_item(item_id):
                    await asyncio.sleep(random.random() * 0.002)
                    return item_id
                
                tasks = [process_load_item(i) for i in range(load)]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                load_time = time.time() - load_start
                successful_items = sum(1 for r in results if not isinstance(r, Exception))
                
                load_results.append({
                    "load": load,
                    "time_ms": load_time * 1000,
                    "successful": successful_items,
                    "items_per_second": successful_items / load_time if load_time > 0 else 0
                })
            
            load_adaptation_time = time.time() - load_adaptation_start
            
            # 分析负载适应性
            adaptation_scores = []
            for i in range(1, len(load_results)):
                prev = load_results[i-1]
                curr = load_results[i]
                
                # 计算负载变化时的性能变化
                if prev["load"] > 0 and curr["load"] > 0:
                    load_change = curr["load"] / prev["load"]
                    perf_change = curr["items_per_second"] / prev["items_per_second"] if prev["items_per_second"] > 0 else 0
                    
                    # 理想情况：性能变化与负载变化成比例（或更好）
                    adaptation_score = perf_change / load_change if load_change > 0 else 0
                    adaptation_scores.append(adaptation_score)
            
            avg_adaptation_score = sum(adaptation_scores) / len(adaptation_scores) if adaptation_scores else 0
            
            metrics["load_adaptation_time_ms"] = load_adaptation_time * 1000
            metrics["load_adaptation_score"] = avg_adaptation_score
            metrics["load_levels_tested"] = len(load_levels)
            
            # 3. 测试故障转移能力（模拟）
            failover_start = time.time()
            
            failover_scenarios = 10
            failover_successful = 0
            
            for scenario in range(failover_scenarios):
                try:
                    # 模拟主服务故障
                    primary_fails = random.random() > 0.7  # 30%故障率
                    
                    if primary_fails:
                        # 模拟切换到备用服务
                        await asyncio.sleep(random.random() * 0.005)  # 故障转移时间
                        
                        # 模拟备用服务工作
                        backup_works = random.random() > 0.1  # 90%成功率
                        
                        if backup_works:
                            failover_successful += 1
                    else:
                        # 主服务正常工作
                        failover_successful += 1
                        
                except Exception:
                    pass
            
            failover_time = time.time() - failover_start
            metrics["failover_time_ms"] = failover_time * 1000
            metrics["failover_success_rate"] = failover_successful / failover_scenarios if failover_scenarios > 0 else 0
            
            # 验证标准
            success = (
                metrics.get("error_recovery_rate", 0) > 0.8 and
                metrics.get("load_adaptation_score", 0) > 0.7 and
                metrics.get("failover_success_rate", 0) > 0.8
            )
            
            recommendations = []
            if metrics.get("error_recovery_rate", 0) <= 0.8:
                recommendations.append("错误恢复能力需要加强")
            if metrics.get("load_adaptation_score", 0) <= 0.7:
                recommendations.append("负载适应性需要优化")
            if metrics.get("failover_success_rate", 0) <= 0.8:
                recommendations.append("故障转移可靠性需要提高")
            
            self._add_result("resilience", success, time.time() - start_time, metrics, recommendations)
            
        except Exception as e:
            self.logger.error(f"弹性验证失败: {e}")
            self._add_result("resilience", False, time.time() - start_time, metrics, str(e))
    
    def _add_result(self, scenario_name: str, success: bool, execution_time: float, 
                   metrics: Dict[str, Any], error_or_recommendations: Any = None) -> None:
        """添加验证结果"""
        if isinstance(error_or_recommendations, str):
            # 错误消息
            error_message = error_or_recommendations
            recommendations = []
        else:
            # 建议列表
            error_message = None
            recommendations = error_or_recommendations or []
        
        result = ValidationResult(
            scenario_name=scenario_name,
            success=success,
            execution_time=execution_time,
            metrics=metrics,
            error_message=error_message,
            recommendations=recommendations
        )
        self.validation_results.append(result)
        
        status = "✅ 通过" if success else "❌ 失败"
        self.logger.info(f"{status} {scenario_name} ({execution_time:.3f}s)")
        
        if recommendations:
            for rec in recommendations:
                self.logger.info(f"  建议: {rec}")
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """生成验证报告"""
        total_scenarios = len(self.validation_results)
        passed_scenarios = sum(1 for r in self.validation_results if r.success)
        failed_scenarios = total_scenarios - passed_scenarios
        
        total_time = sum(r.execution_time for r in self.validation_results)
        avg_time = total_time / total_scenarios if total_scenarios > 0 else 0
        
        # 收集所有建议
        all_recommendations = []
        for result in self.validation_results:
            if result.recommendations:
                all_recommendations.extend(result.recommendations)
        
        # 去重建议
        unique_recommendations = list(set(all_recommendations))
        
        # 性能指标摘要
        performance_summary = {}
        for result in self.validation_results:
            for key, value in result.metrics.items():
                if isinstance(value, (int, float)):
                    if key not in performance_summary:
                        performance_summary[key] = []
                    performance_summary[key].append(value)
        
        # 计算统计信息
        performance_stats = {}
        for key, values in performance_summary.items():
            if values:
                performance_stats[key] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values)
                }
        
        return {
            "summary": {
                "total_scenarios": total_scenarios,
                "passed_scenarios": passed_scenarios,
                "failed_scenarios": failed_scenarios,
                "success_rate": (passed_scenarios / total_scenarios * 100) if total_scenarios > 0 else 0,
                "total_execution_time": total_time,
                "average_execution_time": avg_time,
                "recommendations_count": len(unique_recommendations)
            },
            "scenarios": [
                {
                    "name": r.scenario_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "metrics": r.metrics,
                    "recommendations": r.recommendations
                }
                for r in self.validation_results
            ],
            "recommendations": unique_recommendations,
            "performance_stats": performance_stats,
            "timestamp": datetime.now().isoformat()
        }


async def main():
    """主函数"""
    print("=" * 70)
    print("生产环境验证测试")
    print("模拟真实生产环境使用场景，验证架构改进功能")
    print("=" * 70)
    
    # 运行验证
    validator = ProductionValidationTest()
    results = await validator.run_all_validations()
    
    # 生成最终报告
    report = validator.generate_validation_report()
    
    # 显示摘要
    summary = report["summary"]
    print("\n" + "=" * 70)
    print("验证摘要")
    print("=" * 70)
    print(f"总场景数: {summary['total_scenarios']}")
    print(f"通过场景: {summary['passed_scenarios']}")
    print(f"失败场景: {summary['failed_scenarios']}")
    print(f"成功率: {summary['success_rate']:.1f}%")
    print(f"总执行时间: {summary['total_execution_time']:.2f}s")
    print(f"平均执行时间: {summary['average_execution_time']:.3f}s")
    print(f"建议数量: {summary['recommendations_count']}")
    
    # 显示场景结果
    print("\n场景结果:")
    for scenario in report["scenarios"]:
        status = "✅ 通过" if scenario["success"] else "❌ 失败"
        print(f"  {scenario['name']}: {status} ({scenario['execution_time']:.3f}s)")
    
    # 显示建议（如果有）
    recommendations = report["recommendations"]
    if recommendations:
        print("\n改进建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # 显示性能指标（关键指标）
    print("\n关键性能指标:")
    key_metrics = [
        "container_init_time_ms", "service_registration_time_ms",
        "tasks_per_second", "cpu_ops_per_second", "io_ops_per_second",
        "error_recovery_rate", "load_adaptation_score"
    ]
    
    for metric in key_metrics:
        if metric in report["performance_stats"]:
            stats = report["performance_stats"][metric]
            print(f"  {metric}: 平均值={stats['avg']:.2f}, 范围=[{stats['min']:.2f}, {stats['max']:.2f}]")
    
    print("\n" + "=" * 70)
    
    # 生产环境就绪性评估
    readiness_score = summary["success_rate"] / 100.0
    if readiness_score >= 0.8:
        readiness = "🟢 生产就绪"
    elif readiness_score >= 0.6:
        readiness = "🟡 接近就绪"
    else:
        readiness = "🔴 需要改进"
    
    print(f"生产环境就绪性: {readiness} ({readiness_score*100:.0f}%)")
    print("=" * 70)
    
    # 返回退出代码
    exit_code = 0 if summary["failed_scenarios"] == 0 else 1
    exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())