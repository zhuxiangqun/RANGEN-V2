"""
性能基准测试系统

提供全面的性能测试、基准建立、瓶颈分析和优化建议
"""

import asyncio
import logging
import time
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import psutil


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    operation_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    avg_response_time: float = 0.0
    p50_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    total_duration: float = 0.0

    # 资源使用情况
    cpu_usage_start: float = 0.0
    cpu_usage_end: float = 0.0
    memory_usage_start: float = 0.0
    memory_usage_end: float = 0.0
    peak_memory_usage: float = 0.0

    # 详细响应时间分布
    response_times: List[float] = field(default_factory=list)


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    name: str
    description: str
    operation: Callable
    concurrent_users: int = 10
    total_requests: int = 1000
    ramp_up_time: float = 10.0  # 爬坡时间（秒）
    test_duration: float = 60.0  # 测试持续时间（秒）
    timeout: float = 30.0  # 单请求超时时间
    warmup_requests: int = 50  # 预热请求数


@dataclass
class PerformanceReport:
    """性能报告"""
    benchmark_name: str
    timestamp: float
    config: BenchmarkConfig
    metrics: PerformanceMetrics
    recommendations: List[str] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)


class PerformanceBenchmark:
    """
    性能基准测试器

    执行压力测试、负载测试，收集详细的性能指标
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._executor = ThreadPoolExecutor(max_workers=50)

    async def run_benchmark(self, config: BenchmarkConfig) -> PerformanceReport:
        """
        运行性能基准测试

        Args:
            config: 测试配置

        Returns:
            PerformanceReport: 性能报告
        """
        self.logger.info(f"🚀 开始性能基准测试: {config.name}")

        start_time = time.time()

        # 初始化指标收集
        metrics = PerformanceMetrics(operation_name=config.name)

        # 收集初始资源使用情况
        metrics.cpu_usage_start, metrics.memory_usage_start = self._get_resource_usage()

        try:
            # 预热阶段
            if config.warmup_requests > 0:
                self.logger.info(f"🔥 预热阶段: {config.warmup_requests} 个请求")
                await self._warmup_phase(config, config.warmup_requests)

            # 主测试阶段
            self.logger.info(f"⚡ 主测试阶段: {config.concurrent_users} 并发用户, {config.total_requests} 总请求")
            response_times = await self._main_test_phase(config, metrics)

            # 计算统计指标
            self._calculate_statistics(metrics, response_times, start_time)

            # 生成建议
            recommendations = self._generate_recommendations(metrics)
            bottlenecks = self._identify_bottlenecks(metrics)

            # 收集最终资源使用情况
            metrics.cpu_usage_end, metrics.memory_usage_end = self._get_resource_usage()
            metrics.peak_memory_usage = max(metrics.memory_usage_start, metrics.memory_usage_end)

            report = PerformanceReport(
                benchmark_name=config.name,
                timestamp=time.time(),
                config=config,
                metrics=metrics,
                recommendations=recommendations,
                bottlenecks=bottlenecks
            )

            self.logger.info(f"✅ 性能基准测试完成: {config.name}")
            return report

        except Exception as e:
            self.logger.error(f"❌ 性能基准测试失败: {e}", exc_info=True)

            # 返回失败报告
            return PerformanceReport(
                benchmark_name=config.name,
                timestamp=time.time(),
                config=config,
                metrics=metrics,
                recommendations=[f"测试失败: {e}"],
                bottlenecks=["测试执行失败"]
            )

    async def _warmup_phase(self, config: BenchmarkConfig, warmup_requests: int):
        """预热阶段"""
        semaphore = asyncio.Semaphore(config.concurrent_users)

        async def warmup_request():
            async with semaphore:
                try:
                    await asyncio.wait_for(
                        config.operation(),
                        timeout=config.timeout
                    )
                except Exception:
                    pass  # 预热阶段忽略错误

        # 执行预热请求
        tasks = [warmup_request() for _ in range(warmup_requests)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # 短暂等待系统稳定
        await asyncio.sleep(2)

    async def _main_test_phase(self, config: BenchmarkConfig, metrics: PerformanceMetrics) -> List[float]:
        """主测试阶段"""
        response_times = []
        semaphore = asyncio.Semaphore(config.concurrent_users)

        async def test_request():
            async with semaphore:
                start_time = time.time()
                try:
                    await asyncio.wait_for(
                        config.operation(),
                        timeout=config.timeout
                    )
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    metrics.successful_requests += 1
                    return response_time
                except asyncio.TimeoutError:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    metrics.failed_requests += 1
                    return response_time
                except Exception:
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    metrics.failed_requests += 1
                    return response_time

        # 控制测试持续时间或总请求数
        test_start_time = time.time()
        completed_requests = 0

        while (time.time() - test_start_time < config.test_duration and
               completed_requests < config.total_requests):

            # 批量提交请求
            batch_size = min(50, config.total_requests - completed_requests)
            tasks = [test_request() for _ in range(batch_size)]

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                completed_requests += batch_size
            except Exception as e:
                self.logger.warning(f"批量请求异常: {e}")
                break

        metrics.total_requests = len(response_times)
        return response_times

    def _calculate_statistics(self, metrics: PerformanceMetrics, response_times: List[float], start_time: float):
        """计算统计指标"""
        if not response_times:
            return

        # 基本统计
        metrics.min_response_time = min(response_times)
        metrics.max_response_time = max(response_times)
        metrics.avg_response_time = statistics.mean(response_times)

        # 百分位数
        sorted_times = sorted(response_times)
        metrics.p50_response_time = statistics.median(sorted_times)
        metrics.p95_response_time = self._percentile(sorted_times, 95)
        metrics.p99_response_time = self._percentile(sorted_times, 99)

        # QPS
        total_duration = time.time() - start_time
        metrics.requests_per_second = len(response_times) / total_duration if total_duration > 0 else 0
        metrics.total_duration = total_duration

        # 错误率
        total_requests = metrics.successful_requests + metrics.failed_requests
        metrics.error_rate = metrics.failed_requests / total_requests if total_requests > 0 else 0

        # 保存详细响应时间
        metrics.response_times = response_times

    def _percentile(self, sorted_data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not sorted_data:
            return 0.0

        k = (len(sorted_data) - 1) * (percentile / 100.0)
        f = int(k)
        c = k - f

        if f + 1 < len(sorted_data):
            return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
        else:
            return sorted_data[f]

    def _get_resource_usage(self) -> tuple[float, float]:
        """获取资源使用情况"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_percent = psutil.virtual_memory().percent
            return cpu_percent, memory_percent
        except ImportError:
            return 0.0, 0.0

    def _generate_recommendations(self, metrics: PerformanceMetrics) -> List[str]:
        """生成性能优化建议"""
        recommendations = []

        # 响应时间分析
        if metrics.avg_response_time > 5.0:
            recommendations.append("平均响应时间过长，建议优化业务逻辑或增加缓存")

        if metrics.p95_response_time > 10.0:
            recommendations.append("95%响应时间过长，存在性能瓶颈，建议进行深度性能分析")

        # 错误率分析
        if metrics.error_rate > 0.1:
            recommendations.append("错误率过高，建议检查错误处理和系统稳定性")

        # QPS分析
        if metrics.requests_per_second < 10:
            recommendations.append("QPS较低，建议优化并发处理或系统架构")

        # 资源使用分析
        if metrics.peak_memory_usage > 80:
            recommendations.append("内存使用率过高，建议优化内存管理或增加内存资源")

        if not recommendations:
            recommendations.append("性能表现良好，继续保持")

        return recommendations

    def _identify_bottlenecks(self, metrics: PerformanceMetrics) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []

        # 分析响应时间分布
        if metrics.p99_response_time > metrics.p50_response_time * 3:
            bottlenecks.append("响应时间分布不均匀，可能存在某些请求处理异常缓慢")

        # 分析成功率
        if metrics.error_rate > 0.05:
            bottlenecks.append("存在一定比例的请求失败，需要检查系统稳定性")

        # 分析资源使用
        if metrics.cpu_usage_end > 80:
            bottlenecks.append("CPU使用率过高，可能存在计算密集型操作")

        if metrics.memory_usage_end > 85:
            bottlenecks.append("内存使用率过高，可能存在内存泄漏")

        if not bottlenecks:
            bottlenecks.append("未发现明显性能瓶颈")

        return bottlenecks


class PerformanceOptimizer:
    """
    性能优化器

    基于性能测试结果提供具体的优化建议和自动化优化
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def analyze_bottlenecks(self, report: PerformanceReport) -> Dict[str, Any]:
        """分析性能瓶颈"""
        analysis = {
            "bottlenecks": report.bottlenecks,
            "severity_score": self._calculate_severity_score(report),
            "optimization_priority": self._determine_optimization_priority(report),
            "actionable_insights": self._generate_actionable_insights(report)
        }

        return analysis

    def _calculate_severity_score(self, report: PerformanceReport) -> float:
        """计算严重程度分数 (0-10)"""
        score = 0.0
        metrics = report.metrics

        # 响应时间权重
        if metrics.avg_response_time > 5.0:
            score += 3.0
        if metrics.p95_response_time > 10.0:
            score += 2.0

        # 错误率权重
        score += metrics.error_rate * 5.0

        # QPS权重（反向）
        if metrics.requests_per_second < 10:
            score += 2.0

        # 资源使用权重
        if metrics.peak_memory_usage > 80:
            score += 1.5
        if metrics.cpu_usage_end > 80:
            score += 1.5

        return min(score, 10.0)

    def _determine_optimization_priority(self, report: PerformanceReport) -> str:
        """确定优化优先级"""
        severity = self._calculate_severity_score(report)

        if severity >= 7.0:
            return "critical"  # 紧急
        elif severity >= 4.0:
            return "high"      # 高
        elif severity >= 2.0:
            return "medium"    # 中
        else:
            return "low"       # 低

    def _generate_actionable_insights(self, report: PerformanceReport) -> List[Dict[str, Any]]:
        """生成可操作的优化建议"""
        insights = []
        metrics = report.metrics

        # 响应时间优化建议
        if metrics.avg_response_time > 2.0:
            insights.append({
                "type": "response_time",
                "title": "优化响应时间",
                "description": f"平均响应时间 {metrics.avg_response_time:.2f}s 过长",
                "actions": [
                    "检查数据库查询性能",
                    "优化缓存策略",
                    "减少网络调用",
                    "使用异步处理"
                ],
                "estimated_impact": "medium"
            })

        # 并发处理优化建议
        if metrics.requests_per_second < 20:
            insights.append({
                "type": "concurrency",
                "title": "提升并发处理能力",
                "description": f"QPS仅为 {metrics.requests_per_second:.1f}",
                "actions": [
                    "增加线程池大小",
                    "使用异步IO",
                    "优化锁竞争",
                    "考虑分布式架构"
                ],
                "estimated_impact": "high"
            })

        # 错误处理优化建议
        if metrics.error_rate > 0.05:
            insights.append({
                "type": "error_handling",
                "title": "改进错误处理",
                "description": f"错误率达到 {metrics.error_rate:.1%}",
                "actions": [
                    "添加重试机制",
                    "改进错误恢复",
                    "增强监控告警",
                    "优化异常处理"
                ],
                "estimated_impact": "medium"
            })

        # 资源优化建议
        if metrics.peak_memory_usage > 70:
            insights.append({
                "type": "resource_optimization",
                "title": "优化资源使用",
                "description": f"内存使用率达 {metrics.peak_memory_usage:.1f}%",
                "actions": [
                    "修复内存泄漏",
                    "优化数据结构",
                    "使用对象池",
                    "增加内存资源"
                ],
                "estimated_impact": "medium"
            })

        if not insights:
            insights.append({
                "type": "general",
                "title": "性能表现良好",
                "description": "当前性能指标在可接受范围内",
                "actions": ["继续监控", "定期性能测试"],
                "estimated_impact": "low"
            })

        return insights


class BenchmarkSuite:
    """
    基准测试套件

    预定义常用性能测试场景
    """

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.benchmark = PerformanceBenchmark()
        self.optimizer = PerformanceOptimizer()

    async def run_full_suite(self, target_operation: Callable) -> Dict[str, Any]:
        """运行完整测试套件"""

        self.logger.info("🧪 开始运行性能测试套件")

        test_configs = [
            BenchmarkConfig(
                name="light_load_test",
                description="轻负载测试：模拟正常使用场景",
                operation=target_operation,
                concurrent_users=5,
                total_requests=200,
                test_duration=30
            ),
            BenchmarkConfig(
                name="medium_load_test",
                description="中负载测试：模拟高峰期场景",
                operation=target_operation,
                concurrent_users=20,
                total_requests=1000,
                test_duration=60
            ),
            BenchmarkConfig(
                name="heavy_load_test",
                description="重负载测试：模拟压力场景",
                operation=target_operation,
                concurrent_users=50,
                total_requests=2000,
                test_duration=120
            )
        ]

        results = {}
        reports = []

        for config in test_configs:
            self.logger.info(f"📊 执行测试: {config.name}")
            report = await self.benchmark.run_benchmark(config)
            reports.append(report)
            results[config.name] = report

            # 输出关键指标
            metrics = report.metrics
            self.logger.info(f"   ✅ 完成: {metrics.total_requests} 请求")
            self.logger.info(".2f")
            self.logger.info(".1f")
            self.logger.info(".1%")
        # 分析结果
            analysis = self.optimizer.analyze_bottlenecks(report)
            self.logger.info(f"   📋 优化建议: {len(analysis['actionable_insights'])} 条")

        # 生成综合报告
        summary = self._generate_suite_summary(reports)

        return {
            "results": results,
            "summary": summary,
            "reports": reports
        }

    def _generate_suite_summary(self, reports: List[PerformanceReport]) -> Dict[str, Any]:
        """生成测试套件总结"""

        if not reports:
            return {}

        # 计算平均指标
        avg_qps = statistics.mean([r.metrics.requests_per_second for r in reports])
        avg_response_time = statistics.mean([r.metrics.avg_response_time for r in reports])
        avg_error_rate = statistics.mean([r.metrics.error_rate for r in reports])

        # 找出最佳和最差表现
        best_report = min(reports, key=lambda r: r.metrics.avg_response_time)
        worst_report = max(reports, key=lambda r: r.metrics.avg_response_time)

        # 总体评估
        overall_score = self._calculate_overall_score(reports)

        return {
            "total_tests": len(reports),
            "average_qps": avg_qps,
            "average_response_time": avg_response_time,
            "average_error_rate": avg_error_rate,
            "best_performance": best_report.benchmark_name,
            "worst_performance": worst_report.benchmark_name,
            "overall_score": overall_score,
            "recommendations": self._generate_suite_recommendations(reports)
        }

    def _calculate_overall_score(self, reports: List[PerformanceReport]) -> float:
        """计算总体性能分数 (0-100)"""
        if not reports:
            return 0.0

        scores = []

        for report in reports:
            metrics = report.metrics

            # 响应时间分数 (0-40分)
            response_score = max(0, 40 - metrics.avg_response_time * 4)

            # QPS分数 (0-30分)
            qps_score = min(30, metrics.requests_per_second * 3)

            # 错误率分数 (0-30分)
            error_score = max(0, 30 - metrics.error_rate * 300)

            total_score = response_score + qps_score + error_score
            scores.append(total_score)

        return statistics.mean(scores)

    def _generate_suite_recommendations(self, reports: List[PerformanceReport]) -> List[str]:
        """生成套件级别建议"""
        recommendations = []

        # 分析负载承受能力
        qps_values = [r.metrics.requests_per_second for r in reports]
        if statistics.mean(qps_values) < 50:
            recommendations.append("系统QPS较低，建议优化并发处理能力")

        # 分析稳定性
        error_rates = [r.metrics.error_rate for r in reports]
        if statistics.mean(error_rates) > 0.05:
            recommendations.append("错误率较高，建议加强系统稳定性")

        # 分析扩展性
        heavy_load = next((r for r in reports if "heavy" in r.benchmark_name), None)
        if heavy_load and heavy_load.metrics.requests_per_second < 20:
            recommendations.append("重负载下性能下降明显，建议考虑水平扩展")

        if not recommendations:
            recommendations.append("性能表现良好，建议定期进行性能监控")

        return recommendations


# 全局性能基准测试实例
_performance_benchmark_instance = None

def get_performance_benchmark() -> PerformanceBenchmark:
    """获取性能基准测试器实例"""
    global _performance_benchmark_instance
    if _performance_benchmark_instance is None:
        _performance_benchmark_instance = PerformanceBenchmark()
    return _performance_benchmark_instance

def get_performance_optimizer() -> PerformanceOptimizer:
    """获取性能优化器实例"""
    return PerformanceOptimizer()

def get_benchmark_suite() -> BenchmarkSuite:
    """获取基准测试套件实例"""
    return BenchmarkSuite()
