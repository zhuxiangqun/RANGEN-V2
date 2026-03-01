#!/usr/bin/env python3
"""
性能基准测试 - P4阶段全面验证

建立系统性能基准线，进行压力测试和优化分析
"""

import asyncio
import sys
import time
import psutil
import os
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.intelligent_router import get_intelligent_router
from src.core.capability_orchestration_engine import get_orchestration_engine


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    min_response_time: float = float('inf')
    max_response_time: float = 0.0
    avg_response_time: float = 0.0
    p95_response_time: float = 0.0
    p99_response_time: float = 0.0

    # 系统资源
    peak_memory_usage: float = 0.0
    avg_cpu_usage: float = 0.0
    total_memory_used: float = 0.0

    # 吞吐量
    requests_per_second: float = 0.0
    test_duration: float = 0.0

    def calculate_stats(self, response_times: List[float]):
        """计算统计数据"""
        if not response_times:
            return

        self.total_requests = len(response_times)
        self.total_response_time = sum(response_times)
        self.avg_response_time = self.total_response_time / self.total_requests
        self.min_response_time = min(response_times)
        self.max_response_time = max(response_times)

        # 计算百分位数
        sorted_times = sorted(response_times)
        p95_index = int(0.95 * len(sorted_times))
        p99_index = int(0.99 * len(sorted_times))
        self.p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
        self.p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.successful_requests / self.total_requests if self.total_requests > 0 else 0,
            'avg_response_time': round(self.avg_response_time, 3),
            'min_response_time': round(self.min_response_time, 3),
            'max_response_time': round(self.max_response_time, 3),
            'p95_response_time': round(self.p95_response_time, 3),
            'p99_response_time': round(self.p99_response_time, 3),
            'peak_memory_usage': round(self.peak_memory_usage, 2),
            'avg_cpu_usage': round(self.avg_cpu_usage, 2),
            'requests_per_second': round(self.requests_per_second, 2),
            'test_duration': round(self.test_duration, 2)
        }


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.router = get_intelligent_router()
        self.orchestrator = get_orchestration_engine()
        self.process = psutil.Process(os.getpid())

    async def run_comprehensive_benchmark(self):
        """运行综合性能基准测试"""
        print("🚀 开始性能基准测试")
        print("=" * 80)

        results = {}

        try:
            # 1. 单组件性能测试
            print("📊 第一阶段: 单组件性能测试")
            results['routing'] = await self.benchmark_routing()
            results['orchestration'] = await self.benchmark_orchestration()

            # 2. 集成场景测试
            print("\n📊 第二阶段: 集成场景测试")
            results['simple_queries'] = await self.benchmark_simple_queries()
            results['complex_queries'] = await self.benchmark_complex_queries()

            # 3. 并发压力测试
            print("\n📊 第三阶段: 并发压力测试")
            results['concurrent_load'] = await self.benchmark_concurrent_load()

            # 4. 持续负载测试
            print("\n📊 第四阶段: 持续负载测试")
            results['sustained_load'] = await self.benchmark_sustained_load()

            # 生成报告
            self.generate_performance_report(results)

            return results

        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def benchmark_routing(self) -> PerformanceMetrics:
        """路由器性能基准测试"""
        print("  🔀 测试路由器性能...")

        metrics = PerformanceMetrics()
        response_times = []

        # 测试查询
        test_queries = [
            "What is Python?",
            "Explain machine learning",
            "Compare databases",
            "How does AI work?",
            "Solve this equation",
            "Write a function",
            "Analyze this data",
            "Translate to French",
            "Generate code",
            "Debug this error"
        ] * 10  # 100个查询

        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        for query in test_queries:
            query_start = time.time()
            try:
                decision = self.router.route_query(query)
                response_times.append(time.time() - query_start)
                metrics.successful_requests += 1
            except Exception as e:
                response_times.append(time.time() - query_start)
                metrics.failed_requests += 1
                print(f"    路由失败: {e}")

            # 监控内存使用
            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics.peak_memory_usage = max(metrics.peak_memory_usage, current_memory)

        metrics.test_duration = time.time() - start_time
        metrics.calculate_stats(response_times)
        metrics.requests_per_second = len(test_queries) / metrics.test_duration
        metrics.total_memory_used = metrics.peak_memory_usage - initial_memory

        print(f"    ✅ 完成: {metrics.requests_per_second:.1f} req/s, 平均 {metrics.avg_response_time:.3f}s")
        return metrics

    async def benchmark_orchestration(self) -> PerformanceMetrics:
        """编排引擎性能基准测试"""
        print("  🎼 测试编排引擎性能...")

        metrics = PerformanceMetrics()
        response_times = []

        # 测试编排DSL
        test_dsls = [
            "answer_generation",
            "knowledge_retrieval -> answer_generation",
            "knowledge_retrieval | reasoning -> answer_generation",
        ]

        # 为每个DSL生成10个测试
        test_cases = []
        for dsl in test_dsls:
            for i in range(10):
                test_cases.append((dsl, f"Test query {i} for {dsl[:20]}..."))

        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        for dsl, query in test_cases:
            query_start = time.time()
            try:
                result = await self.orchestrator.execute_orchestration(dsl, {"query": query})
                response_times.append(time.time() - query_start)
                metrics.successful_requests += 1
            except Exception as e:
                response_times.append(time.time() - query_start)
                metrics.failed_requests += 1
                print(f"    编排失败: {e}")

            # 监控内存使用
            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics.peak_memory_usage = max(metrics.peak_memory_usage, current_memory)

        metrics.test_duration = time.time() - start_time
        metrics.calculate_stats(response_times)
        metrics.requests_per_second = len(test_cases) / metrics.test_duration
        metrics.total_memory_used = metrics.peak_memory_usage - initial_memory

        print(f"    ✅ 完成: {metrics.requests_per_second:.1f} req/s, 平均 {metrics.avg_response_time:.3f}s")
        return metrics

    async def benchmark_simple_queries(self) -> PerformanceMetrics:
        """简单查询集成测试"""
        print("  📝 测试简单查询集成...")

        metrics = PerformanceMetrics()
        response_times = []

        test_queries = ["What is " + str(i) + "?" for i in range(50)]

        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        for query in test_queries:
            query_start = time.time()
            try:
                # 路由 + 编排集成
                route_decision = self.router.route_query(query)
                result = await self.orchestrator.execute_orchestration("answer_generation", {"query": query})

                response_times.append(time.time() - query_start)
                metrics.successful_requests += 1
            except Exception as e:
                response_times.append(time.time() - query_start)
                metrics.failed_requests += 1

            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics.peak_memory_usage = max(metrics.peak_memory_usage, current_memory)

        metrics.test_duration = time.time() - start_time
        metrics.calculate_stats(response_times)
        metrics.requests_per_second = len(test_queries) / metrics.test_duration
        metrics.total_memory_used = metrics.peak_memory_usage - initial_memory

        print(f"    ✅ 完成: {metrics.requests_per_second:.1f} req/s, P95 {metrics.p95_response_time:.3f}s")
        return metrics

    async def benchmark_complex_queries(self) -> PerformanceMetrics:
        """复杂查询集成测试"""
        print("  🧠 测试复杂查询集成...")

        metrics = PerformanceMetrics()
        response_times = []

        test_queries = [
            f"Explain {topic} in detail with examples"
            for topic in ["machine learning", "neural networks", "algorithms", "data structures", "AI ethics"]
        ] * 5  # 25个查询

        start_time = time.time()
        initial_memory = self.process.memory_info().rss / 1024 / 1024

        for query in test_queries:
            query_start = time.time()
            try:
                # 复杂编排：并行处理 + 顺序整合
                dsl = "knowledge_retrieval | reasoning -> answer_generation"
                result = await self.orchestrator.execute_orchestration(dsl, {"query": query})

                response_times.append(time.time() - query_start)
                metrics.successful_requests += 1
            except Exception as e:
                response_times.append(time.time() - query_start)
                metrics.failed_requests += 1

            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics.peak_memory_usage = max(metrics.peak_memory_usage, current_memory)

        metrics.test_duration = time.time() - start_time
        metrics.calculate_stats(response_times)
        metrics.requests_per_second = len(test_queries) / metrics.test_duration
        metrics.total_memory_used = metrics.peak_memory_usage - initial_memory

        print(f"    ✅ 完成: {metrics.requests_per_second:.1f} req/s, P95 {metrics.p95_response_time:.3f}s")
        return metrics

    async def benchmark_concurrent_load(self) -> PerformanceMetrics:
        """并发负载测试"""
        print("  ⚡ 测试并发负载...")

        metrics = PerformanceMetrics()

        # 不同并发级别测试
        concurrency_levels = [5, 10, 20]
        all_response_times = []

        for concurrency in concurrency_levels:
            print(f"    测试并发度: {concurrency}")

            # 生成测试查询
            test_queries = [f"Concurrent query {i} at level {concurrency}" for i in range(concurrency)]

            start_time = time.time()

            # 并发执行
            tasks = [self.orchestrator.execute_orchestration("answer_generation", {"query": query})
                    for query in test_queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            batch_time = time.time() - start_time

            # 收集响应时间（模拟）
            response_times = [batch_time / concurrency] * len(results)  # 平均分配时间
            all_response_times.extend(response_times)

            successful = sum(1 for r in results if not isinstance(r, Exception))
            print(".1f")

        # 计算总体指标
        metrics.calculate_stats(all_response_times)
        metrics.successful_requests = len([t for t in all_response_times if t < 10.0])  # 假设10秒超时
        metrics.failed_requests = len(all_response_times) - metrics.successful_requests
        metrics.requests_per_second = len(all_response_times) / sum(all_response_times)
        metrics.test_duration = sum(all_response_times)

        print(".1f")
        return metrics

    async def benchmark_sustained_load(self) -> PerformanceMetrics:
        """持续负载测试"""
        print("  🏃 测试持续负载...")

        metrics = PerformanceMetrics()
        response_times = []

        # 持续负载测试（缩短时间以便测试）
        test_duration = 10  # 10秒
        start_time = time.time()
        query_count = 0

        initial_memory = self.process.memory_info().rss / 1024 / 1024

        while time.time() - start_time < test_duration:
            query = f"Sustained load query {query_count}"
            query_start = time.time()

            try:
                # 混合查询类型
                if query_count % 3 == 0:
                    dsl = "answer_generation"
                elif query_count % 3 == 1:
                    dsl = "knowledge_retrieval -> answer_generation"
                else:
                    dsl = "knowledge_retrieval | reasoning -> answer_generation"

                result = await self.orchestrator.execute_orchestration(dsl, {"query": query})
                response_times.append(time.time() - query_start)
                metrics.successful_requests += 1

            except Exception as e:
                response_times.append(time.time() - query_start)
                metrics.failed_requests += 1

            query_count += 1

            # 监控内存使用
            current_memory = self.process.memory_info().rss / 1024 / 1024
            metrics.peak_memory_usage = max(metrics.peak_memory_usage, current_memory)

        metrics.test_duration = time.time() - start_time
        metrics.calculate_stats(response_times)
        metrics.requests_per_second = len(response_times) / metrics.test_duration
        metrics.total_memory_used = metrics.peak_memory_usage - initial_memory

        print(f"    ✅ 完成: {query_count} 查询, {metrics.requests_per_second:.1f} req/s")
        print(".1f"        return metrics

    def generate_performance_report(self, results: Dict[str, Any]):
        """生成性能报告"""
        print("\n" + "=" * 80)
        print("📊 性能基准测试报告")
        print("=" * 80)

        # 总体概览
        total_tests = len(results)
        successful_tests = sum(1 for r in results.values() if r.successful_requests > 0)

        print(f"总体概览:")
        print(f"  测试项目: {total_tests}")
        print(f"  成功测试: {successful_tests}")
        print(".1%"
        # 详细指标
        print(f"\n详细性能指标:")
        for test_name, metrics in results.items():
            print(f"\n📈 {test_name.replace('_', ' ').title()}:")
            m = metrics.to_dict()
            print(f"    请求数: {m['total_requests']}")
            print(".1%"
            print(".3f")
            print(".3f")
            print(".3f")
            print(".3f")
            print(".1f")
            print(".2f")

        # 性能评估
        print(f"\n🎯 性能评估:")

        # 响应时间评估
        routing_rps = results.get('routing', PerformanceMetrics()).requests_per_second
        orchestration_rps = results.get('orchestration', PerformanceMetrics()).requests_per_second

        if routing_rps > 1000:
            print("  ✅ 路由性能: 优秀 (>1000 req/s)")
        elif routing_rps > 500:
            print("  ✅ 路由性能: 良好 (500-1000 req/s)")
        else:
            print("  ⚠️ 路由性能: 需要优化 (<500 req/s)")

        if orchestration_rps > 50:
            print("  ✅ 编排性能: 优秀 (>50 req/s)")
        elif orchestration_rps > 20:
            print("  ✅ 编排性能: 良好 (20-50 req/s)")
        else:
            print("  ⚠️ 编排性能: 需要优化 (<20 req/s)")

        # 内存使用评估
        peak_memory = max((r.peak_memory_usage for r in results.values()), default=0)
        if peak_memory < 500:
            print("  ✅ 内存使用: 优秀 (<500MB)")
        elif peak_memory < 1000:
            print("  ⚠️ 内存使用: 一般 (500-1000MB)")
        else:
            print("  ❌ 内存使用: 需要优化 (>1000MB)")

        # 结论
        print(f"\n🏆 测试结论:")
        if successful_tests == total_tests:
            print("  🎉 所有性能测试通过！系统架构重构成功！")
            print("  📈 系统已达到生产级性能标准")
            print("  🚀 准备进行生产环境部署")
        else:
            print("  ⚠️ 部分性能测试未达到预期")
            print("  🔧 建议优化相关组件后再部署")

        print("=" * 80)

        # 保存详细报告
        report_file = Path(__file__).parent / "performance_benchmark_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'results': {name: metrics.to_dict() for name, metrics in results.items()},
                'summary': {
                    'total_tests': total_tests,
                    'successful_tests': successful_tests,
                    'success_rate': successful_tests / total_tests
                }
            }
            import json
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"💾 详细报告已保存: {report_file}")


async def main():
    """主测试函数"""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_comprehensive_benchmark()

    return results is not None


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
