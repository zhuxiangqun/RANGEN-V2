#!/usr/bin/env python3
"""
技能基准测试系统
提供标准化的技能性能测试，建立技能性能基线
"""

import asyncio
import logging
import time
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
import uuid
import random

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    correctness_test_count: int = 10  # 正确性测试次数
    performance_test_count: int = 20  # 性能测试次数  
    reliability_test_duration: int = 300  # 可靠性测试时长（秒）
    scalability_test_levels: int = 5  # 可扩展性测试级别
    compatibility_test_variations: int = 3  # 兼容性测试变体数
    timeout_per_test: float = 30.0  # 单次测试超时（秒）
    max_concurrent_tests: int = 3  # 最大并发测试数
    enable_regression_detection: bool = True  # 启用回归检测
    baseline_threshold: float = 0.8  # 基线阈值


@dataclass
class TestResult:
    """单次测试结果"""
    test_id: str
    test_type: str
    passed: bool
    duration: float  # 执行时长（秒）
    metrics: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    skill_id: str
    benchmark_id: str
    overall_score: float  # 综合得分 (0-100)
    test_results: Dict[str, List[TestResult]]
    aggregated_metrics: Dict[str, Any]
    performance_baseline: Optional[Dict[str, Any]] = None
    regression_detected: bool = False
    regression_details: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    benchmark_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceBaseline:
    """性能基线"""
    skill_id: str
    baseline_id: str
    metrics: Dict[str, float]
    percentile_95: Dict[str, float]  # 95百分位值
    percentile_99: Dict[str, float]  # 99百分位值
    historical_data: List[Dict[str, Any]]
    established_at: datetime = field(default_factory=datetime.now)
    valid_until: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))


class SkillBenchmarkSystem:
    """技能基准测试系统"""
    
    def __init__(self, benchmark_config: Optional[BenchmarkConfig] = None):
        """
        初始化基准测试系统
        
        Args:
            benchmark_config: 基准测试配置
        """
        self.config = benchmark_config or BenchmarkConfig()
        self.logger = logging.getLogger(f"{__name__}.SkillBenchmarkSystem")
        self.baselines: Dict[str, PerformanceBaseline] = {}  # 技能ID -> 性能基线
        self.test_history: Dict[str, List[BenchmarkResult]] = {}  # 技能ID -> 测试历史
    
    async def run_benchmark(self, 
                          skill_data: Any,
                          skill_executor: Callable[[Any, Dict[str, Any]], Any],
                          existing_baseline: Optional[PerformanceBaseline] = None) -> BenchmarkResult:
        """运行完整的基准测试"""
        benchmark_id = f"benchmark_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        self.logger.info(f"🏁 开始技能基准测试: {skill_data.skill_id if hasattr(skill_data, 'skill_id') else 'unknown'}")
        self.logger.info(f"  基准测试ID: {benchmark_id}")
        
        try:
            # 并行运行各个测试类型
            test_tasks = [
                self._run_correctness_tests(skill_data, skill_executor),
                self._run_performance_tests(skill_data, skill_executor),
                self._run_reliability_tests(skill_data, skill_executor),
                self._run_scalability_tests(skill_data, skill_executor),
                self._run_compatibility_tests(skill_data, skill_executor)
            ]
            
            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(self.config.max_concurrent_tests)
            
            async def run_with_semaphore(task):
                async with semaphore:
                    return await task
            
            results = await asyncio.gather(
                *[run_with_semaphore(task) for task in test_tasks],
                return_exceptions=True
            )
            
            # 处理结果
            test_results = {
                "correctness": self._extract_results(results[0], "correctness"),
                "performance": self._extract_results(results[1], "performance"),
                "reliability": self._extract_results(results[2], "reliability"),
                "scalability": self._extract_results(results[3], "scalability"),
                "compatibility": self._extract_results(results[4], "compatibility")
            }
            
            # 聚合指标
            aggregated_metrics = self._aggregate_metrics(test_results)
            
            # 计算综合得分
            overall_score = self._calculate_overall_score(aggregated_metrics)
            
            # 建立或更新性能基线
            performance_baseline = None
            if self.config.enable_regression_detection:
                performance_baseline = await self._establish_baseline(
                    skill_data, aggregated_metrics, existing_baseline
                )
            
            # 检测回归
            regression_detected = False
            regression_details = []
            if performance_baseline and existing_baseline:
                regression_detected, regression_details = self._detect_regressions(
                    aggregated_metrics, existing_baseline, performance_baseline
                )
            
            # 生成建议
            recommendations = self._generate_recommendations(
                overall_score, aggregated_metrics, regression_details
            )
            
            result = BenchmarkResult(
                skill_id=skill_data.skill_id if hasattr(skill_data, 'skill_id') else "unknown",
                benchmark_id=benchmark_id,
                overall_score=overall_score,
                test_results=test_results,
                aggregated_metrics=aggregated_metrics,
                performance_baseline=performance_baseline.metrics if performance_baseline else None,
                regression_detected=regression_detected,
                regression_details=regression_details,
                recommendations=recommendations
            )
            
            # 保存到历史
            skill_id = result.skill_id
            if skill_id not in self.test_history:
                self.test_history[skill_id] = []
            self.test_history[skill_id].append(result)
            
            self.logger.info(f"✅ 技能基准测试完成: {skill_id}")
            self.logger.info(f"  综合得分: {overall_score:.1f}/100")
            self.logger.info(f"  回归检测: {'是' if regression_detected else '否'}")
            self.logger.info(f"  建议数量: {len(recommendations)}个")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ 技能基准测试失败 {benchmark_id}: {e}", exc_info=True)
            # 返回错误结果
            return BenchmarkResult(
                skill_id=skill_data.skill_id if hasattr(skill_data, 'skill_id') else "unknown",
                benchmark_id=benchmark_id,
                overall_score=0.0,
                test_results={},
                aggregated_metrics={"error": str(e)},
                recommendations=["基准测试过程出错"]
            )
    
    async def _run_correctness_tests(self, skill_data: Any, 
                                   skill_executor: Callable[[Any, Dict[str, Any]], Any]) -> List[TestResult]:
        """运行正确性测试"""
        self.logger.info("🔍 运行正确性测试...")
        
        results = []
        
        for i in range(self.config.correctness_test_count):
            test_id = f"correctness_{i+1}"
            
            try:
                # 生成测试用例
                test_case = self._generate_correctness_test_case(skill_data, i)
                
                # 执行测试
                start_time = time.time()
                
                # 使用asyncio.wait_for设置超时
                try:
                    output = await asyncio.wait_for(
                        asyncio.to_thread(skill_executor, skill_data, test_case["input"]),
                        timeout=self.config.timeout_per_test
                    )
                    duration = time.time() - start_time
                    
                    # 验证结果
                    passed, metrics = self._validate_correctness_result(
                        output, test_case["expected"], test_case["input"]
                    )
                    
                    result = TestResult(
                        test_id=test_id,
                        test_type="correctness",
                        passed=passed,
                        duration=duration,
                        metrics=metrics,
                        error_message=None
                    )
                    
                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    result = TestResult(
                        test_id=test_id,
                        test_type="correctness",
                        passed=False,
                        duration=duration,
                        metrics={"timeout": True},
                        error_message="测试超时"
                    )
                    
            except Exception as e:
                result = TestResult(
                    test_id=test_id,
                    test_type="correctness",
                    passed=False,
                    duration=0.0,
                    metrics={"exception": True},
                    error_message=str(e)
                )
            
            results.append(result)
        
        return results
    
    def _generate_correctness_test_case(self, skill_data: Any, index: int) -> Dict[str, Any]:
        """生成正确性测试用例"""
        # 基于技能数据生成测试用例
        # 这里使用模拟数据，实际应该根据技能类型生成
        
        test_types = [
            {"type": "normal", "complexity": "low"},
            {"type": "edge_case", "complexity": "medium"},
            {"type": "boundary", "complexity": "high"}
        ]
        
        test_type = test_types[index % len(test_types)]
        
        return {
            "input": {
                "test_type": test_type["type"],
                "data": f"测试数据_{index}",
                "complexity": test_type["complexity"],
                "timestamp": datetime.now().isoformat()
            },
            "expected": {
                "success": True,
                "has_result": True,
                "quality_threshold": 0.7
            }
        }
    
    def _validate_correctness_result(self, output: Any, expected: Dict[str, Any], 
                                   input_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """验证正确性结果"""
        metrics = {
            "output_valid": False,
            "expected_matched": False,
            "error_detected": False,
            "quality_score": 0.0
        }
        
        try:
            # 检查输出是否有效
            if output is None:
                metrics["error_detected"] = True
                return False, metrics
            
            # 基础验证逻辑
            if isinstance(output, dict):
                metrics["output_valid"] = True
                
                # 检查是否包含成功标志
                if expected.get("success", False):
                    if output.get("success", False):
                        metrics["expected_matched"] = True
                
                # 检查是否有结果
                if expected.get("has_result", False):
                    if "result" in output or "data" in output or "response" in output:
                        metrics["expected_matched"] = True
                
                # 计算质量评分（简单启发式）
                output_keys = set(output.keys())
                expected_keys = {"success", "result", "data", "response", "error"}
                common_keys = output_keys.intersection(expected_keys)
                
                if common_keys:
                    metrics["quality_score"] = len(common_keys) / len(expected_keys)
            
            return metrics["output_valid"] and metrics["expected_matched"], metrics
            
        except Exception:
            return False, metrics
    
    async def _run_performance_tests(self, skill_data: Any, 
                                   skill_executor: Callable[[Any, Dict[str, Any]], Any]) -> List[TestResult]:
        """运行性能测试"""
        self.logger.info("⚡ 运行性能测试...")
        
        results = []
        
        for i in range(self.config.performance_test_count):
            test_id = f"performance_{i+1}"
            
            try:
                # 生成性能测试用例
                test_case = self._generate_performance_test_case(skill_data, i)
                
                # 执行测试（多次执行取平均值）
                execution_times = []
                memory_usages = []
                
                for _ in range(3):  # 每次测试运行3次
                    start_time = time.time()
                    
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(skill_executor, skill_data, test_case),
                            timeout=self.config.timeout_per_test
                        )
                        execution_time = time.time() - start_time
                        execution_times.append(execution_time)
                        
                        # 模拟内存使用（实际应该使用内存分析工具）
                        memory_usage = random.uniform(10.0, 100.0)  # MB
                        memory_usages.append(memory_usage)
                        
                    except asyncio.TimeoutError:
                        execution_times.append(self.config.timeout_per_test)
                        memory_usages.append(0.0)
                
                # 计算性能指标
                avg_execution_time = statistics.mean(execution_times) if execution_times else 0.0
                avg_memory_usage = statistics.mean(memory_usages) if memory_usages else 0.0
                
                # 确定是否通过（基于阈值）
                passed = avg_execution_time < 5.0  # 5秒阈值
                
                metrics = {
                    "avg_execution_time": avg_execution_time,
                    "avg_memory_usage": avg_memory_usage,
                    "min_execution_time": min(execution_times) if execution_times else 0.0,
                    "max_execution_time": max(execution_times) if execution_times else 0.0,
                    "execution_time_std": statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0
                }
                
                result = TestResult(
                    test_id=test_id,
                    test_type="performance",
                    passed=passed,
                    duration=avg_execution_time,
                    metrics=metrics
                )
                
            except Exception as e:
                result = TestResult(
                    test_id=test_id,
                    test_type="performance",
                    passed=False,
                    duration=0.0,
                    metrics={"exception": True},
                    error_message=str(e)
                )
            
            results.append(result)
        
        return results
    
    def _generate_performance_test_case(self, skill_data: Any, index: int) -> Dict[str, Any]:
        """生成性能测试用例"""
        complexity_levels = ["low", "medium", "high"]
        complexity = complexity_levels[index % len(complexity_levels)]
        
        # 根据复杂度调整数据量
        data_size = {
            "low": 100,
            "medium": 1000,
            "high": 10000
        }.get(complexity, 100)
        
        return {
            "test_type": "performance",
            "complexity": complexity,
            "data_size": data_size,
            "iterations": 10,
            "stress_level": index / self.config.performance_test_count
        }
    
    async def _run_reliability_tests(self, skill_data: Any, 
                                   skill_executor: Callable[[Any, Dict[str, Any]], Any]) -> List[TestResult]:
        """运行可靠性测试"""
        self.logger.info("🛡️ 运行可靠性测试...")
        
        results = []
        start_time = time.time()
        end_time = start_time + self.config.reliability_test_duration
        
        test_count = 0
        success_count = 0
        
        while time.time() < end_time and test_count < 100:  # 最多100次测试
            test_id = f"reliability_{test_count+1}"
            test_count += 1
            
            try:
                # 生成可靠性测试用例
                test_case = self._generate_reliability_test_case(skill_data, test_count)
                
                # 执行测试
                execution_start = time.time()
                
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(skill_executor, skill_data, test_case),
                        timeout=self.config.timeout_per_test
                    )
                    execution_time = time.time() - execution_start
                    success_count += 1
                    
                    metrics = {
                        "execution_time": execution_time,
                        "success": True,
                        "failure_rate": 0.0
                    }
                    
                    result = TestResult(
                        test_id=test_id,
                        test_type="reliability",
                        passed=True,
                        duration=execution_time,
                        metrics=metrics
                    )
                    
                except asyncio.TimeoutError:
                    execution_time = time.time() - execution_start
                    metrics = {
                        "execution_time": execution_time,
                        "success": False,
                        "failure_rate": 1.0
                    }
                    
                    result = TestResult(
                        test_id=test_id,
                        test_type="reliability",
                        passed=False,
                        duration=execution_time,
                        metrics=metrics,
                        error_message="可靠性测试超时"
                    )
                    
            except Exception as e:
                result = TestResult(
                    test_id=test_id,
                    test_type="reliability",
                    passed=False,
                    duration=0.0,
                    metrics={"exception": True},
                    error_message=str(e)
                )
            
            results.append(result)
            
            # 短暂暂停，避免过度负载
            await asyncio.sleep(0.1)
        
        # 计算总体可靠性指标
        failure_rate = 1 - (success_count / test_count) if test_count > 0 else 1.0
        avg_duration = statistics.mean([r.duration for r in results]) if results else 0.0
        
        # 添加总体结果
        overall_result = TestResult(
            test_id="reliability_overall",
            test_type="reliability",
            passed=failure_rate < 0.1,  # 故障率低于10%为通过
            duration=avg_duration,
            metrics={
                "total_tests": test_count,
                "success_count": success_count,
                "failure_rate": failure_rate,
                "avg_duration": avg_duration,
                "test_duration": time.time() - start_time
            }
        )
        
        results.append(overall_result)
        
        return results
    
    def _generate_reliability_test_case(self, skill_data: Any, index: int) -> Dict[str, Any]:
        """生成可靠性测试用例"""
        # 模拟不同的故障场景
        fault_scenarios = [
            {"type": "normal", "should_fail": False},
            {"type": "invalid_input", "should_fail": True},
            {"type": "edge_case", "should_fail": False},
            {"type": "resource_limit", "should_fail": True},
            {"type": "network_issue", "should_fail": True}
        ]
        
        scenario = fault_scenarios[index % len(fault_scenarios)]
        
        return {
            "test_type": "reliability",
            "scenario": scenario["type"],
            "should_fail": scenario["should_fail"],
            "data": f"可靠性测试数据_{index}",
            "stress_factor": random.uniform(0.5, 2.0)
        }
    
    async def _run_scalability_tests(self, skill_data: Any, 
                                   skill_executor: Callable[[Any, Dict[str, Any]], Any]) -> List[TestResult]:
        """运行可扩展性测试"""
        self.logger.info("📈 运行可扩展性测试...")
        
        results = []
        
        for level in range(1, self.config.scalability_test_levels + 1):
            test_id = f"scalability_level_{level}"
            
            try:
                # 生成可扩展性测试用例
                test_case = self._generate_scalability_test_case(skill_data, level)
                
                # 执行并发测试
                concurrency_level = level * 2  # 随着级别增加并发数
                
                start_time = time.time()
                
                # 创建并发任务
                tasks = []
                for i in range(concurrency_level):
                    task = asyncio.create_task(
                        asyncio.wait_for(
                            asyncio.to_thread(skill_executor, skill_data, test_case),
                            timeout=self.config.timeout_per_test
                        )
                    )
                    tasks.append(task)
                
                # 等待所有任务完成
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    total_time = time.time() - start_time
                    
                    # 计算可扩展性指标
                    avg_time_per_request = total_time / concurrency_level
                    throughput = concurrency_level / total_time if total_time > 0 else 0
                    
                    # 判断是否通过（吞吐量应随并发数增加）
                    passed = throughput > (level - 1) * 0.5  # 简单阈值
                    
                    metrics = {
                        "concurrency_level": concurrency_level,
                        "total_time": total_time,
                        "avg_time_per_request": avg_time_per_request,
                        "throughput": throughput,
                        "scalability_factor": throughput / level if level > 0 else 0
                    }
                    
                    result = TestResult(
                        test_id=test_id,
                        test_type="scalability",
                        passed=passed,
                        duration=total_time,
                        metrics=metrics
                    )
                    
                except Exception as e:
                    result = TestResult(
                        test_id=test_id,
                        test_type="scalability",
                        passed=False,
                        duration=0.0,
                        metrics={"exception": True},
                        error_message=str(e)
                    )
                
            except Exception as e:
                result = TestResult(
                    test_id=test_id,
                    test_type="scalability",
                    passed=False,
                    duration=0.0,
                    metrics={"exception": True},
                    error_message=str(e)
                )
            
            results.append(result)
        
        return results
    
    def _generate_scalability_test_case(self, skill_data: Any, level: int) -> Dict[str, Any]:
        """生成可扩展性测试用例"""
        load_factor = level * 0.2  # 随着级别增加负载
        
        return {
            "test_type": "scalability",
            "level": level,
            "load_factor": load_factor,
            "data_size": 100 * level,
            "complexity": "medium" if level <= 2 else "high"
        }
    
    async def _run_compatibility_tests(self, skill_data: Any, 
                                     skill_executor: Callable[[Any, Dict[str, Any]], Any]) -> List[TestResult]:
        """运行兼容性测试"""
        self.logger.info("🔄 运行兼容性测试...")
        
        results = []
        
        for variation in range(self.config.compatibility_test_variations):
            test_id = f"compatibility_variation_{variation+1}"
            
            try:
                # 生成兼容性测试用例
                test_case = self._generate_compatibility_test_case(skill_data, variation)
                
                # 执行测试
                start_time = time.time()
                
                try:
                    output = await asyncio.wait_for(
                        asyncio.to_thread(skill_executor, skill_data, test_case),
                        timeout=self.config.timeout_per_test
                    )
                    duration = time.time() - start_time
                    
                    # 验证兼容性
                    passed, metrics = self._validate_compatibility_result(output, test_case)
                    
                    result = TestResult(
                        test_id=test_id,
                        test_type="compatibility",
                        passed=passed,
                        duration=duration,
                        metrics=metrics
                    )
                    
                except asyncio.TimeoutError:
                    duration = time.time() - start_time
                    result = TestResult(
                        test_id=test_id,
                        test_type="compatibility",
                        passed=False,
                        duration=duration,
                        metrics={"timeout": True},
                        error_message="兼容性测试超时"
                    )
                    
            except Exception as e:
                result = TestResult(
                    test_id=test_id,
                    test_type="compatibility",
                    passed=False,
                    duration=0.0,
                    metrics={"exception": True},
                    error_message=str(e)
                )
            
            results.append(result)
        
        return results
    
    def _generate_compatibility_test_case(self, skill_data: Any, variation: int) -> Dict[str, Any]:
        """生成兼容性测试用例"""
        variations = [
            {"format": "json", "encoding": "utf-8", "version": "v1"},
            {"format": "xml", "encoding": "utf-16", "version": "v2"},
            {"format": "yaml", "encoding": "ascii", "version": "legacy"}
        ]
        
        variation_config = variations[variation % len(variations)]
        
        return {
            "test_type": "compatibility",
            "variation": variation_config,
            "data": f"兼容性测试数据_{variation}",
            "require_backward_compat": True
        }
    
    def _validate_compatibility_result(self, output: Any, test_case: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """验证兼容性结果"""
        metrics = {
            "format_supported": False,
            "encoding_supported": False,
            "version_compatible": False,
            "backward_compatible": False
        }
        
        try:
            if isinstance(output, dict):
                # 检查格式支持
                if test_case["variation"]["format"] in ["json", "xml", "yaml"]:
                    metrics["format_supported"] = True
                
                # 检查编码支持
                if test_case["variation"]["encoding"] in ["utf-8", "utf-16", "ascii"]:
                    metrics["encoding_supported"] = True
                
                # 检查版本兼容性
                if test_case["variation"]["version"] in ["v1", "v2", "legacy"]:
                    metrics["version_compatible"] = True
                
                # 检查向后兼容性
                if test_case.get("require_backward_compat", False):
                    if "legacy_support" in output or output.get("compatible", False):
                        metrics["backward_compatible"] = True
            
            passed = all(metrics.values())
            return passed, metrics
            
        except Exception:
            return False, metrics
    
    def _extract_results(self, results: Union[List[TestResult], Exception], test_type: str) -> List[TestResult]:
        """提取测试结果"""
        if isinstance(results, Exception):
            self.logger.error(f"{test_type}测试出错: {results}")
            return [
                TestResult(
                    test_id=f"{test_type}_error",
                    test_type=test_type,
                    passed=False,
                    duration=0.0,
                    metrics={"exception": True},
                    error_message=str(results)
                )
            ]
        
        return results
    
    def _aggregate_metrics(self, test_results: Dict[str, List[TestResult]]) -> Dict[str, Any]:
        """聚合测试指标"""
        aggregated = {
            "correctness_rate": 0.0,
            "avg_performance_time": 0.0,
            "reliability_score": 0.0,
            "scalability_factor": 0.0,
            "compatibility_score": 0.0,
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0
        }
        
        total_tests = 0
        passed_tests = 0
        
        # 计算各维度得分
        for test_type, results in test_results.items():
            if not results:
                continue
            
            type_passed = sum(1 for r in results if r.passed)
            type_total = len(results)
            
            total_tests += type_total
            passed_tests += type_passed
            
            success_rate = type_passed / type_total if type_total > 0 else 0.0
            
            if test_type == "correctness":
                aggregated["correctness_rate"] = success_rate
            elif test_type == "performance":
                # 取性能测试的平均执行时间
                durations = [r.duration for r in results if r.duration > 0]
                aggregated["avg_performance_time"] = statistics.mean(durations) if durations else 0.0
            elif test_type == "reliability":
                aggregated["reliability_score"] = success_rate
            elif test_type == "scalability":
                # 取可扩展性因子
                factors = [r.metrics.get("scalability_factor", 0.0) for r in results]
                aggregated["scalability_factor"] = statistics.mean(factors) if factors else 0.0
            elif test_type == "compatibility":
                aggregated["compatibility_score"] = success_rate
        
        aggregated["total_tests"] = total_tests
        aggregated["passed_tests"] = passed_tests
        aggregated["failed_tests"] = total_tests - passed_tests
        aggregated["overall_success_rate"] = passed_tests / total_tests if total_tests > 0 else 0.0
        
        return aggregated
    
    def _calculate_overall_score(self, aggregated_metrics: Dict[str, Any]) -> float:
        """计算综合得分"""
        weights = {
            "correctness_rate": 0.30,
            "reliability_score": 0.25,
            "compatibility_score": 0.20,
            "scalability_factor": 0.15,
            "performance_score": 0.10  # 性能得分为执行时间的反比
        }
        
        # 计算性能得分（执行时间越短得分越高）
        avg_time = aggregated_metrics.get("avg_performance_time", 0.0)
        if avg_time <= 1.0:
            performance_score = 1.0
        elif avg_time <= 5.0:
            performance_score = 0.8 - (avg_time - 1.0) * 0.1
        elif avg_time <= 10.0:
            performance_score = 0.5 - (avg_time - 5.0) * 0.05
        else:
            performance_score = 0.2
        
        scores = {
            "correctness_rate": aggregated_metrics.get("correctness_rate", 0.0),
            "reliability_score": aggregated_metrics.get("reliability_score", 0.0),
            "compatibility_score": aggregated_metrics.get("compatibility_score", 0.0),
            "scalability_factor": min(aggregated_metrics.get("scalability_factor", 0.0), 1.0),
            "performance_score": performance_score
        }
        
        # 加权平均
        overall_score = sum(scores[key] * weights[key] for key in weights.keys())
        
        # 转换为0-100分
        return overall_score * 100
    
    async def _establish_baseline(self, skill_data: Any, 
                                aggregated_metrics: Dict[str, Any],
                                existing_baseline: Optional[PerformanceBaseline]) -> Optional[PerformanceBaseline]:
        """建立性能基线"""
        skill_id = skill_data.skill_id if hasattr(skill_data, 'skill_id') else "unknown"
        
        if not existing_baseline:
            # 创建新基线
            baseline_id = f"baseline_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            baseline = PerformanceBaseline(
                skill_id=skill_id,
                baseline_id=baseline_id,
                metrics=aggregated_metrics,
                percentile_95={key: value * 1.05 for key, value in aggregated_metrics.items()},  # 5%容差
                percentile_99={key: value * 1.10 for key, value in aggregated_metrics.items()},  # 10%容差
                historical_data=[aggregated_metrics]
            )
            
            self.baselines[skill_id] = baseline
            self.logger.info(f"📊 建立新性能基线: {skill_id} ({baseline_id})")
            
        else:
            # 更新现有基线
            existing_baseline.historical_data.append(aggregated_metrics)
            
            # 保留最近20次测试数据
            if len(existing_baseline.historical_data) > 20:
                existing_baseline.historical_data = existing_baseline.historical_data[-20:]
            
            # 重新计算百分位值
            if len(existing_baseline.historical_data) >= 5:
                for key in aggregated_metrics.keys():
                    if key in existing_baseline.metrics:
                        values = [data.get(key, 0.0) for data in existing_baseline.historical_data]
                        if values:
                            existing_baseline.metrics[key] = statistics.mean(values)
                            sorted_values = sorted(values)
                            idx_95 = min(int(len(sorted_values) * 0.95), len(sorted_values) - 1)
                            idx_99 = min(int(len(sorted_values) * 0.99), len(sorted_values) - 1)
                            existing_baseline.percentile_95[key] = sorted_values[idx_95]
                            existing_baseline.percentile_99[key] = sorted_values[idx_99]
            
            existing_baseline.established_at = datetime.now()
            baseline = existing_baseline
            
            self.logger.info(f"📊 更新性能基线: {skill_id}")
        
        return baseline
    
    def _detect_regressions(self, current_metrics: Dict[str, Any],
                          old_baseline: PerformanceBaseline,
                          new_baseline: PerformanceBaseline) -> Tuple[bool, List[Dict[str, Any]]]:
        """检测性能回归"""
        regression_details = []
        regression_detected = False
        
        # 比较关键指标
        critical_metrics = ["correctness_rate", "reliability_score", "avg_performance_time"]
        
        for metric in critical_metrics:
            current_value = current_metrics.get(metric, 0.0)
            baseline_value = old_baseline.metrics.get(metric, 0.0)
            percentile_95 = old_baseline.percentile_95.get(metric, baseline_value * 1.05)
            
            # 检查是否超过95百分位（显著变差）
            if metric == "avg_performance_time":
                # 对于执行时间，值越大越差
                if current_value > percentile_95 * 1.2:  # 额外20%容差
                    regression = {
                        "metric": metric,
                        "current_value": current_value,
                        "baseline_value": baseline_value,
                        "percentile_95": percentile_95,
                        "regression_type": "performance_degradation",
                        "severity": "high" if current_value > baseline_value * 1.5 else "medium"
                    }
                    regression_details.append(regression)
                    regression_detected = True
            else:
                # 对于成功率，值越小越差
                if current_value < percentile_95 * 0.8:  # 低于80%的95百分位
                    regression = {
                        "metric": metric,
                        "current_value": current_value,
                        "baseline_value": baseline_value,
                        "percentile_95": percentile_95,
                        "regression_type": "quality_degradation",
                        "severity": "high" if current_value < baseline_value * 0.7 else "medium"
                    }
                    regression_details.append(regression)
                    regression_detected = True
        
        return regression_detected, regression_details
    
    def _generate_recommendations(self, overall_score: float,
                                aggregated_metrics: Dict[str, Any],
                                regression_details: List[Dict[str, Any]]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于综合得分
        if overall_score < 60:
            recommendations.append("技能性能较差，建议进行深度优化")
        elif overall_score < 80:
            recommendations.append("技能性能中等，有改进空间")
        else:
            recommendations.append("技能性能良好，继续保持")
        
        # 基于各维度得分
        if aggregated_metrics.get("correctness_rate", 0.0) < 0.9:
            recommendations.append("提高正确性测试通过率")
        
        if aggregated_metrics.get("reliability_score", 0.0) < 0.85:
            recommendations.append("加强可靠性，降低故障率")
        
        if aggregated_metrics.get("avg_performance_time", 0.0) > 3.0:
            recommendations.append("优化性能，降低平均执行时间")
        
        if aggregated_metrics.get("scalability_factor", 0.0) < 0.5:
            recommendations.append("提高可扩展性，支持更高并发")
        
        if aggregated_metrics.get("compatibility_score", 0.0) < 0.8:
            recommendations.append("提高兼容性，支持更多格式和版本")
        
        # 基于回归检测
        for regression in regression_details:
            if regression.get("severity") == "high":
                recommendations.append(f"⚠️ 高严重性回归: {regression.get('metric')} 显著下降")
            elif regression.get("severity") == "medium":
                recommendations.append(f"⚠️ 中严重性回归: {regression.get('metric')} 有所下降")
        
        return list(set(recommendations))  # 去重
    
    def get_benchmark_history(self, skill_id: str) -> List[BenchmarkResult]:
        """获取基准测试历史记录"""
        return self.test_history.get(skill_id, [])
    
    def get_baseline(self, skill_id: str) -> Optional[PerformanceBaseline]:
        """获取性能基线"""
        return self.baselines.get(skill_id)
    
    def clear_history(self, skill_id: Optional[str] = None):
        """清空历史记录"""
        if skill_id:
            if skill_id in self.test_history:
                del self.test_history[skill_id]
            if skill_id in self.baselines:
                del self.baselines[skill_id]
            self.logger.info(f"清空 {skill_id} 的历史记录")
        else:
            self.test_history.clear()
            self.baselines.clear()
            self.logger.info("清空所有历史记录")


# 模拟技能执行器（用于测试）
class MockSkillExecutor:
    """模拟技能执行器"""
    
    async def execute(self, skill_data: Any, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行技能"""
        # 模拟执行时间
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        test_type = input_data.get("test_type", "unknown")
        
        # 根据测试类型返回不同结果
        if test_type == "correctness":
            return {
                "success": True,
                "result": f"正确性测试结果: {input_data.get('data', 'N/A')}",
                "confidence": 0.85
            }
        elif test_type == "performance":
            return {
                "success": True,
                "execution_time": random.uniform(0.2, 2.0),
                "memory_used": random.uniform(50.0, 200.0)
            }
        elif test_type == "reliability":
            should_fail = input_data.get("should_fail", False)
            if should_fail and random.random() < 0.3:  # 30%概率失败
                return {
                    "success": False,
                    "error": "模拟可靠性测试失败"
                }
            else:
                return {
                    "success": True,
                    "result": "可靠性测试通过"
                }
        elif test_type == "scalability":
            return {
                "success": True,
                "concurrent_requests": input_data.get("level", 1) * 2,
                "throughput": random.uniform(10.0, 50.0)
            }
        elif test_type == "compatibility":
            return {
                "success": True,
                "format_supported": True,
                "version_compatible": True,
                "legacy_support": input_data.get("require_backward_compat", False)
            }
        else:
            return {
                "success": True,
                "result": f"通用测试结果: {test_type}"
            }


async def main():
    """主函数 - 测试基准测试系统"""
    import sys
    
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    
    # 创建基准测试系统
    benchmark_system = SkillBenchmarkSystem()
    
    # 模拟技能数据
    class MockSkillData:
        def __init__(self):
            self.skill_id = "test_skill_001"
            self.name = "测试技能"
            self.category = "test"
            self.version = "1.0"
    
    skill_data = MockSkillData()
    skill_executor = MockSkillExecutor()
    
    print("🚀 开始技能基准测试...")
    
    # 运行基准测试
    result = await benchmark_system.run_benchmark(
        skill_data=skill_data,
        skill_executor=skill_executor.execute
    )
    
    # 打印结果
    print(f"\n📊 基准测试结果:")
    print(f"  技能ID: {result.skill_id}")
    print(f"  测试ID: {result.benchmark_id}")
    print(f"  综合得分: {result.overall_score:.1f}/100")
    print(f"  总测试数: {result.aggregated_metrics.get('total_tests', 0)}")
    print(f"  通过测试: {result.aggregated_metrics.get('passed_tests', 0)}")
    print(f"  失败测试: {result.aggregated_metrics.get('failed_tests', 0)}")
    print(f"  总体成功率: {result.aggregated_metrics.get('overall_success_rate', 0.0):.1%}")
    
    print(f"\n📈 各维度指标:")
    print(f"  正确率: {result.aggregated_metrics.get('correctness_rate', 0.0):.1%}")
    print(f"  平均性能时间: {result.aggregated_metrics.get('avg_performance_time', 0.0):.2f}秒")
    print(f"  可靠性得分: {result.aggregated_metrics.get('reliability_score', 0.0):.1%}")
    print(f"  可扩展性因子: {result.aggregated_metrics.get('scalability_factor', 0.0):.2f}")
    print(f"  兼容性得分: {result.aggregated_metrics.get('compatibility_score', 0.0):.1%}")
    
    print(f"\n⚠️ 回归检测: {'是' if result.regression_detected else '否'}")
    if result.regression_details:
        print(f"  回归详情:")
        for reg in result.regression_details:
            print(f"    • {reg.get('metric')}: {reg.get('current_value'):.2f} "
                  f"(基线: {reg.get('baseline_value'):.2f})")
    
    print(f"\n💡 改进建议:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")
    
    print(f"\n{'='*60}")
    print("✅ 技能基准测试完成")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))