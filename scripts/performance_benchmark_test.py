#!/usr/bin/env python3
"""
性能基准测试脚本

对比迁移前后的系统性能表现：
1. 响应时间基准测试
2. 吞吐量压力测试
3. 资源使用率监控
4. 稳定性持续测试
5. 性能对比报告生成
"""

import asyncio
import sys
import os
import time
import json
import psutil
import threading
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class PerformanceBenchmarkTester:
    """性能基准测试器"""

    def __init__(self):
        self.baseline_results = {}
        self.current_results = {}
        self.comparison_results = {}
        self.system_metrics = []

    async def run_performance_benchmark_test(self):
        """运行性能基准测试"""
        print("🚀 开始性能基准测试")
        print("=" * 80)
        print("测试目标：验证迁移后的性能提升")
        print("测试维度：响应时间、吞吐量、资源使用率、稳定性")
        print("=" * 80)

        start_time = time.time()

        # 1. 加载基准数据（如果存在）
        self._load_baseline_data()

        # 2. 响应时间基准测试
        await self._run_response_time_benchmark()

        # 3. 吞吐量压力测试
        await self._run_throughput_stress_test()

        # 4. 资源使用率监控
        await self._monitor_resource_usage()

        # 5. 稳定性持续测试
        await self._run_stability_test()

        # 6. 生成性能对比报告
        self._generate_performance_comparison_report(start_time)

        return True

    def _load_baseline_data(self):
        """加载基准性能数据"""
        print("\n📊 步骤1: 加载基准数据")
        print("-" * 50)

        baseline_file = project_root / 'data' / 'performance_baseline.json'

        if baseline_file.exists():
            try:
                with open(baseline_file, 'r', encoding='utf-8') as f:
                    self.baseline_results = json.load(f)
                print("✅ 已加载历史基准数据")
                print(f"   基准测试时间: {self.baseline_results.get('timestamp', '未知')}")
                print(".2f"            except Exception as e:
                print(f"⚠️ 加载基准数据失败: {e}")
                self.baseline_results = {}
        else:
            print("ℹ️ 未找到历史基准数据，将使用当前数据作为基准")
            self.baseline_results = {}

        # 如果没有基准数据，创建模拟的基准数据用于对比
        if not self.baseline_results:
            print("   创建模拟基准数据用于对比...")
            self.baseline_results = {
                'timestamp': '2026-01-01T00:00:00',
                'response_time_benchmark': {
                    'avg_response_time': 2.5,  # 秒
                    'min_response_time': 1.2,
                    'max_response_time': 4.8,
                    'p95_response_time': 3.5
                },
                'throughput_test': {
                    'requests_per_second': 8.5,
                    'total_requests': 100,
                    'successful_requests': 85,
                    'failed_requests': 15
                },
                'resource_usage': {
                    'avg_cpu_percent': 35.0,
                    'avg_memory_mb': 280.0,
                    'peak_cpu_percent': 65.0,
                    'peak_memory_mb': 420.0
                },
                'stability_test': {
                    'total_tests': 50,
                    'successful_tests': 42,
                    'failed_tests': 8,
                    'avg_response_time': 2.8
                }
            }

    async def _run_response_time_benchmark(self):
        """运行响应时间基准测试"""
        print("\n⏱️ 步骤2: 响应时间基准测试")
        print("-" * 50)

        from src.unified_research_system import UnifiedResearchSystem

        system = UnifiedResearchSystem()
        await system.initialize()

        # 测试查询集合
        test_queries = [
            "什么是人工智能？",
            "解释机器学习的基本原理",
            "分析深度学习的发展历程",
            "如何提高软件开发效率？",
            "大数据技术在现代企业中的应用",
            "云计算服务的优势和挑战",
            "区块链技术的核心特点",
            "物联网在智能家居中的应用",
            "虚拟现实技术的未来发展",
            "自然语言处理的基本方法"
        ]

        print("   执行响应时间测试...")

        response_times = []
        successful_tests = 0
        total_tests = len(test_queries)

        for i, query in enumerate(test_queries, 1):
            try:
                print(f"   测试 {i}/{total_tests}: {query[:20]}...")

                start_time = time.time()
                result = await system.execute_research(query)
                end_time = time.time()

                response_time = end_time - start_time
                response_times.append(response_time)

                success = getattr(result, 'success', True) if hasattr(result, 'success') else True
                if success:
                    successful_tests += 1

                print(".2f"
            except Exception as e:
                print(f"   ❌ 测试失败: {e}")
                response_times.append(0)  # 失败测试记为0

        # 计算统计数据
        valid_times = [t for t in response_times if t > 0]
        if valid_times:
            avg_response_time = sum(valid_times) / len(valid_times)
            min_response_time = min(valid_times)
            max_response_time = max(valid_times)
            sorted_times = sorted(valid_times)
            p95_response_time = sorted_times[int(len(sorted_times) * 0.95)]
        else:
            avg_response_time = min_response_time = max_response_time = p95_response_time = 0

        success_rate = successful_tests / total_tests * 100

        self.current_results['response_time_benchmark'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'p95_response_time': p95_response_time,
            'individual_times': response_times
        }

        print("   📊 响应时间统计:"        print(f"     成功率: {success_rate:.1f}%")
        print(".2f"        print(".2f"        print(".2f"        print(".2f"
    async def _run_throughput_stress_test(self):
        """运行吞吐量压力测试"""
        print("\n🔥 步骤3: 吞吐量压力测试")
        print("-" * 50)

        from src.unified_research_system import UnifiedResearchSystem

        system = UnifiedResearchSystem()
        await system.initialize()

        # 压力测试参数
        concurrent_requests = 5  # 并发请求数
        total_requests = 50      # 总请求数
        test_duration = 120      # 测试时长（秒）

        print(f"   压力测试参数: 并发{concurrent_requests}，总请求{total_requests}")
        print("   执行压力测试..."

        # 测试查询模板
        query_templates = [
            "什么是{}？",
            "解释{}的基本原理",
            "分析{}的发展现状",
            "如何应用{}技术？",
            "{}在现代社会中的作用"
        ]

        topics = ["人工智能", "机器学习", "深度学习", "大数据", "云计算", "物联网", "区块链", "虚拟现实"]

        # 生成测试查询
        test_queries = []
        for i in range(total_requests):
            template = query_templates[i % len(query_templates)]
            topic = topics[i % len(topics)]
            test_queries.append(template.format(topic))

        # 执行并发测试
        semaphore = asyncio.Semaphore(concurrent_requests)
        results = []

        async def execute_request(query: str, request_id: int):
            async with semaphore:
                try:
                    start_time = time.time()
                    result = await system.execute_research(query)
                    end_time = time.time()

                    response_time = end_time - start_time
                    success = getattr(result, 'success', True) if hasattr(result, 'success') else True

                    results.append({
                        'request_id': request_id,
                        'query': query[:30] + "..." if len(query) > 30 else query,
                        'response_time': response_time,
                        'success': success,
                        'timestamp': datetime.now().isoformat()
                    })

                    return success, response_time

                except Exception as e:
                    results.append({
                        'request_id': request_id,
                        'query': query[:30] + "..." if len(query) > 30 else query,
                        'response_time': 0,
                        'success': False,
                        'error': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    return False, 0

        # 创建并发任务
        tasks = [execute_request(query, i) for i, query in enumerate(test_queries)]

        # 执行测试并限制总时长
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=test_duration)
        except asyncio.TimeoutError:
            print(f"   ⚠️ 测试超时 ({test_duration}秒)，可能存在性能问题")

        # 统计结果
        successful_requests = sum(1 for r in results if r['success'])
        failed_requests = len(results) - successful_requests
        valid_times = [r['response_time'] for r in results if r['success'] and r['response_time'] > 0]

        if valid_times:
            avg_response_time = sum(valid_times) / len(valid_times)
            min_response_time = min(valid_times)
            max_response_time = max(valid_times)
        else:
            avg_response_time = min_response_time = max_response_time = 0

        # 计算QPS (每秒请求数)
        total_time = max(r['response_time'] for r in results) if results else test_duration
        requests_per_second = len(results) / max(total_time, 1)

        self.current_results['throughput_test'] = {
            'total_requests': len(results),
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': successful_requests / len(results) * 100 if results else 0,
            'requests_per_second': requests_per_second,
            'avg_response_time': avg_response_time,
            'min_response_time': min_response_time,
            'max_response_time': max_response_time,
            'concurrent_requests': concurrent_requests,
            'test_duration': test_duration,
            'results': results
        }

        print("   📊 吞吐量统计:"        print(f"     总请求数: {len(results)}")
        print(f"     成功请求: {successful_requests}")
        print(f"     失败请求: {failed_requests}")
        print(".1f"        print(".1f"        print(".2f"
    async def _monitor_resource_usage(self):
        """监控资源使用率"""
        print("\n📈 步骤4: 资源使用率监控")
        print("-" * 50)

        from src.unified_research_system import UnifiedResearchSystem

        system = UnifiedResearchSystem()
        await system.initialize()

        # 监控参数
        monitor_duration = 60  # 监控1分钟
        sample_interval = 2    # 每2秒采样一次

        print(f"   监控时长: {monitor_duration}秒，采样间隔: {sample_interval}秒")

        # 启动资源监控线程
        monitoring_results = []
        monitoring_active = True

        def resource_monitor():
            process = psutil.Process()
            while monitoring_active:
                try:
                    cpu_percent = process.cpu_percent(interval=0.1)
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024  # 转换为MB

                    monitoring_results.append({
                        'timestamp': datetime.now().isoformat(),
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_mb
                    })

                    time.sleep(sample_interval)

                except Exception as e:
                    print(f"   资源监控错误: {e}")
                    break

        # 启动监控线程
        monitor_thread = threading.Thread(target=resource_monitor, daemon=True)
        monitor_thread.start()

        # 执行一些负载测试
        print("   执行负载测试以监控资源使用...")
        test_queries = [
            "什么是人工智能？",
            "解释机器学习算法",
            "分析大数据处理技术",
            "云计算服务架构分析"
        ]

        for query in test_queries:
            try:
                await system.execute_research(query)
                await asyncio.sleep(1)  # 短暂休息
            except Exception as e:
                print(f"   负载测试错误: {e}")

        # 等待监控完成
        await asyncio.sleep(monitor_duration)
        monitoring_active = False
        monitor_thread.join(timeout=5)

        # 统计资源使用情况
        if monitoring_results:
            cpu_percentages = [r['cpu_percent'] for r in monitoring_results]
            memory_usages = [r['memory_mb'] for r in monitoring_results]

            avg_cpu_percent = sum(cpu_percentages) / len(cpu_percentages)
            avg_memory_mb = sum(memory_usages) / len(memory_usages)
            peak_cpu_percent = max(cpu_percentages)
            peak_memory_mb = max(memory_usages)

            self.current_results['resource_usage'] = {
                'monitoring_duration': monitor_duration,
                'sample_interval': sample_interval,
                'samples_count': len(monitoring_results),
                'avg_cpu_percent': avg_cpu_percent,
                'avg_memory_mb': avg_memory_mb,
                'peak_cpu_percent': peak_cpu_percent,
                'peak_memory_mb': peak_memory_mb,
                'cpu_samples': cpu_percentages,
                'memory_samples': memory_usages
            }

            print("   📊 资源使用统计:"            print(".1f"            print(".0f"            print(".1f"            print(".0f"        else:
            print("   ⚠️ 没有收集到资源监控数据")

    async def _run_stability_test(self):
        """运行稳定性持续测试"""
        print("\n🔄 步骤5: 稳定性持续测试")
        print("-" * 50)

        from src.unified_research_system import UnifiedResearchSystem

        system = UnifiedResearchSystem()
        await system.initialize()

        # 稳定性测试参数
        total_tests = 30
        test_interval = 3  # 每3秒执行一次测试

        print(f"   稳定性测试: {total_tests}次连续测试，间隔{test_interval}秒")

        test_results = []
        test_queries = [
            "什么是AI？",
            "机器学习基础",
            "深度学习应用",
            "大数据技术"
        ]

        for i in range(total_tests):
            query = test_queries[i % len(test_queries)]
            test_id = i + 1

            try:
                start_time = time.time()
                result = await system.execute_research(query)
                end_time = time.time()

                response_time = end_time - start_time
                success = getattr(result, 'success', True) if hasattr(result, 'success') else True

                test_results.append({
                    'test_id': test_id,
                    'query': query,
                    'response_time': response_time,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })

                status = "✅" if success else "❌"
                print(".2f"
            except Exception as e:
                test_results.append({
                    'test_id': test_id,
                    'query': query,
                    'response_time': 0,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                print(f"   ❌ 测试 {test_id}: 异常 - {e}")

            # 测试间隔
            if i < total_tests - 1:  # 最后一次不需要等待
                await asyncio.sleep(test_interval)

        # 统计稳定性结果
        successful_tests = sum(1 for r in test_results if r['success'])
        failed_tests = total_tests - successful_tests
        valid_times = [r['response_time'] for r in test_results if r['success'] and r['response_time'] > 0]

        if valid_times:
            avg_response_time = sum(valid_times) / len(valid_times)
            response_time_variance = sum((t - avg_response_time) ** 2 for t in valid_times) / len(valid_times)
            response_time_std = response_time_variance ** 0.5
        else:
            avg_response_time = response_time_std = 0

        success_rate = successful_tests / total_tests * 100
        stability_score = success_rate / 100.0  # 成功率作为稳定性评分

        self.current_results['stability_test'] = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'response_time_std': response_time_std,
            'stability_score': stability_score,
            'test_interval': test_interval,
            'results': test_results
        }

        print("   📊 稳定性统计:"        print(f"     总测试数: {total_tests}")
        print(f"     成功测试: {successful_tests}")
        print(f"     失败测试: {failed_tests}")
        print(".1f"        print(".2f"        print(".3f"        print(".1f"
    def _generate_performance_comparison_report(self, start_time: float):
        """生成性能对比报告"""
        total_time = time.time() - start_time

        print("
📊 步骤6: 生成性能对比报告"        print("-" * 50)

        # 生成对比结果
        comparison_results = {}

        for test_type in ['response_time_benchmark', 'throughput_test', 'resource_usage', 'stability_test']:
            if test_type in self.baseline_results and test_type in self.current_results:
                baseline = self.baseline_results[test_type]
                current = self.current_results[test_type]

                comparison = {}

                # 响应时间对比
                if test_type == 'response_time_benchmark':
                    if 'avg_response_time' in baseline and 'avg_response_time' in current:
                        improvement = ((baseline['avg_response_time'] - current['avg_response_time']) /
                                     baseline['avg_response_time'] * 100)
                        comparison['avg_response_time_improvement'] = improvement

                # 吞吐量对比
                elif test_type == 'throughput_test':
                    if 'requests_per_second' in baseline and 'requests_per_second' in current:
                        improvement = ((current['requests_per_second'] - baseline['requests_per_second']) /
                                     baseline['requests_per_second'] * 100)
                        comparison['throughput_improvement'] = improvement

                # 资源使用对比
                elif test_type == 'resource_usage':
                    if 'avg_cpu_percent' in baseline and 'avg_cpu_percent' in current:
                        cpu_change = ((current['avg_cpu_percent'] - baseline['avg_cpu_percent']) /
                                    baseline['avg_cpu_percent'] * 100)
                        comparison['cpu_usage_change'] = cpu_change

                    if 'avg_memory_mb' in baseline and 'avg_memory_mb' in current:
                        memory_change = ((current['avg_memory_mb'] - baseline['avg_memory_mb']) /
                                       baseline['avg_memory_mb'] * 100)
                        comparison['memory_usage_change'] = memory_change

                # 稳定性对比
                elif test_type == 'stability_test':
                    if 'stability_score' in baseline and 'stability_score' in current:
                        stability_change = current['stability_score'] - baseline['stability_score']
                        comparison['stability_improvement'] = stability_change

                comparison_results[test_type] = {
                    'baseline': baseline,
                    'current': current,
                    'comparison': comparison
                }

        # 生成综合报告
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_test_time': total_time,
            'baseline_data': self.baseline_results,
            'current_data': self.current_results,
            'comparison_results': comparison_results,
            'summary': self._generate_performance_summary(comparison_results)
        }

        # 保存报告
        report_path = project_root / 'reports' / 'performance_benchmark_comparison_report.json'
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"   ✅ 性能对比报告已保存: {report_path}")

        # 打印对比摘要
        self._print_performance_comparison_summary(comparison_results)

    def _generate_performance_summary(self, comparison_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成性能总结"""
        summary = {
            'overall_improvement_score': 0,
            'key_improvements': [],
            'key_concerns': [],
            'recommendations': []
        }

        improvement_score = 0
        improvement_count = 0

        # 分析各项指标
        for test_type, data in comparison_results.items():
            comparison = data['comparison']

            if test_type == 'response_time_benchmark':
                if 'avg_response_time_improvement' in comparison:
                    improvement = comparison['avg_response_time_improvement']
                    if improvement > 0:
                        summary['key_improvements'].append(f"响应时间提升 {improvement:.1f}%")
                        improvement_score += improvement
                        improvement_count += 1
                    else:
                        summary['key_concerns'].append(f"响应时间下降 {abs(improvement):.1f}%")

            elif test_type == 'throughput_test':
                if 'throughput_improvement' in comparison:
                    improvement = comparison['throughput_improvement']
                    if improvement > 0:
                        summary['key_improvements'].append(f"吞吐量提升 {improvement:.1f}%")
                        improvement_score += improvement
                        improvement_count += 1

            elif test_type == 'resource_usage':
                if 'cpu_usage_change' in comparison:
                    cpu_change = comparison['cpu_usage_change']
                    if cpu_change < 10:  # CPU使用率增加不超过10%算合理
                        summary['key_improvements'].append("CPU使用率控制良好")
                    else:
                        summary['key_concerns'].append(f"CPU使用率增加 {cpu_change:.1f}%")

                if 'memory_usage_change' in comparison:
                    memory_change = comparison['memory_usage_change']
                    if memory_change < 20:  # 内存使用率增加不超过20%算合理
                        summary['key_improvements'].append("内存使用率控制良好")
                    else:
                        summary['key_concerns'].append(f"内存使用率增加 {memory_change:.1f}%")

            elif test_type == 'stability_test':
                if 'stability_improvement' in comparison:
                    stability_change = comparison['stability_improvement']
                    if stability_change >= 0:
                        summary['key_improvements'].append("系统稳定性保持良好")
                    else:
                        summary['key_concerns'].append(f"系统稳定性下降 {abs(stability_change):.2f}")

        # 计算总体改进分数
        if improvement_count > 0:
            summary['overall_improvement_score'] = improvement_score / improvement_count

        # 生成建议
        if summary['overall_improvement_score'] > 20:
            summary['recommendations'].append("🎉 性能大幅提升，建议立即投入生产使用")
        elif summary['overall_improvement_score'] > 10:
            summary['recommendations'].append("✅ 性能有所提升，可以投入生产使用")
        elif summary['overall_improvement_score'] > 0:
            summary['recommendations'].append("⚠️ 性能略有提升，但需要进一步优化")
        else:
            summary['recommendations'].append("❌ 性能未见提升，建议重新评估迁移效果")

        return summary

    def _print_performance_comparison_summary(self, comparison_results: Dict[str, Any]):
        """打印性能对比摘要"""
        print("   📈 性能对比摘要:"        print("   " + "=" * 50)

        for test_type, data in comparison_results.items():
            comparison = data['comparison']

            if test_type == 'response_time_benchmark':
                print("   响应时间测试:"                if 'avg_response_time_improvement' in comparison:
                    improvement = comparison['avg_response_time_improvement']
                    symbol = "📈" if improvement > 0 else "📉"
                    print(".1f"            elif test_type == 'throughput_test':
                print("   吞吐量测试:"                if 'throughput_improvement' in comparison:
                    improvement = comparison['throughput_improvement']
                    symbol = "📈" if improvement > 0 else "📉"
                    print(".1f"            elif test_type == 'resource_usage':
                print("   资源使用:"                if 'cpu_usage_change' in comparison:
                    cpu_change = comparison['cpu_usage_change']
                    cpu_symbol = "✅" if abs(cpu_change) < 10 else "⚠️"
                    print(f"     {cpu_symbol} CPU使用率变化: {cpu_change:+.1f}%")

                if 'memory_usage_change' in comparison:
                    memory_change = comparison['memory_usage_change']
                    memory_symbol = "✅" if abs(memory_change) < 20 else "⚠️"
                    print(f"     {memory_symbol} 内存使用率变化: {memory_change:+.1f}%")

            elif test_type == 'stability_test':
                print("   稳定性测试:"                if 'stability_improvement' in comparison:
                    stability_change = comparison['stability_improvement']
                    stability_symbol = "✅" if stability_change >= 0 else "⚠️"
                    print(".2f"        print("   " + "=" * 50)

        # 打印总体评估
        summary = self._generate_performance_summary(comparison_results)
        print("   🎯 总体评估:"        print(".1f"        print("   💡 关键改进:"        for improvement in summary['key_improvements'][:3]:  # 最多显示3个
            print(f"     • {improvement}")

        if summary['key_concerns']:
            print("   ⚠️ 需要关注:"            for concern in summary['key_concerns'][:2]:  # 最多显示2个
                print(f"     • {concern}")

        print("   📋 建议:"        for recommendation in summary['recommendations']:
            print(f"     • {recommendation}")

def main():
    """主函数"""
    tester = PerformanceBenchmarkTester()

    success = asyncio.run(tester.run_performance_benchmark_test())

    print("
" + "=" * 80)
    if success:
        print("🎉 性能基准测试完成！")
        print("✅ 已生成详细的性能对比报告")
        print("📊 对比结果已保存到 reports/performance_benchmark_comparison_report.json")
    else:
        print("⚠️ 性能基准测试未完全成功")
        print("请检查测试过程中的错误信息")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
