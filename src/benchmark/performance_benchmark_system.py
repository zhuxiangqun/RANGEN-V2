#!/usr/bin/env python3
"""
性能基准测试系统
全面评估Agent迁移后的系统性能表现
"""

import asyncio
import time
import logging
import json
import psutil
import statistics
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import threading
import concurrent.futures

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    timestamp: datetime

    # 响应时间指标
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p95_response_time: float
    p99_response_time: float

    # 吞吐量指标
    requests_per_second: float
    total_requests: int
    successful_requests: int
    failed_requests: int

    # 系统资源指标
    avg_cpu_usage: float
    max_cpu_usage: float
    avg_memory_usage: float
    max_memory_usage: float

    # 错误指标
    error_rate: float
    timeout_rate: float

    # 业务指标
    avg_answer_quality: float = 0.0  # 答案质量评分
    avg_answer_length: float = 0.0   # 答案长度


@dataclass
class BenchmarkScenario:
    """基准测试场景"""
    name: str
    description: str
    concurrent_users: int
    total_requests: int
    request_types: List[str]  # 查询类型分布
    duration_minutes: int


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    scenario: BenchmarkScenario
    start_time: datetime
    end_time: datetime
    metrics: PerformanceMetrics
    agent_performance: Dict[str, Dict[str, Any]]  # 各Agent的性能数据
    system_health: Dict[str, Any]  # 系统健康状态
    recommendations: List[str]


class PerformanceBenchmarkSystem:
    """性能基准测试系统"""

    def __init__(self):
        self.is_running = False
        self.results: List[BenchmarkResult] = []

        # 测试配置
        self.test_scenarios = self._define_test_scenarios()

        # 数据存储
        self.data_dir = Path("data/performance_benchmarks")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        logger.info("性能基准测试系统初始化完成")

    def _define_test_scenarios(self) -> List[BenchmarkScenario]:
        """定义测试场景"""
        return [
            BenchmarkScenario(
                name="light_load",
                description="轻负载测试 - 模拟正常使用",
                concurrent_users=5,
                total_requests=100,
                request_types=["simple_question", "analysis_query"],
                duration_minutes=5
            ),
            BenchmarkScenario(
                name="medium_load",
                description="中负载测试 - 模拟高峰期",
                concurrent_users=20,
                total_requests=500,
                request_types=["simple_question", "analysis_query", "complex_reasoning"],
                duration_minutes=10
            ),
            BenchmarkScenario(
                name="heavy_load",
                description="重负载测试 - 压力测试",
                concurrent_users=50,
                total_requests=1000,
                request_types=["simple_question", "analysis_query", "complex_reasoning", "multi_step_task"],
                duration_minutes=15
            ),
            BenchmarkScenario(
                name="spike_load",
                description="峰值负载测试 - 突发高负载",
                concurrent_users=100,
                total_requests=2000,
                request_types=["simple_question", "analysis_query"],
                duration_minutes=20
            )
        ]

    async def run_benchmark_scenario(self, scenario_name: str) -> Optional[BenchmarkResult]:
        """
        运行指定的基准测试场景

        Args:
            scenario_name: 场景名称

        Returns:
            测试结果
        """
        scenario = next((s for s in self.test_scenarios if s.name == scenario_name), None)
        if not scenario:
            logger.error(f"未找到测试场景: {scenario_name}")
            return None

        print(f"🚀 开始运行基准测试场景: {scenario.name}")
        print(f"📝 描述: {scenario.description}")
        print(f"👥 并发用户: {scenario.concurrent_users}")
        print(f"📊 总请求数: {scenario.total_requests}")
        print(f"⏱️  持续时间: {scenario.duration_minutes}分钟")
        print("-" * 60)

        start_time = datetime.now()

        try:
            # 运行测试
            metrics, agent_performance = await self._execute_benchmark(scenario)

            # 检查系统健康状态
            system_health = await self._check_system_health()

            # 生成建议
            recommendations = self._generate_recommendations(metrics, agent_performance, system_health)

            end_time = datetime.now()

            result = BenchmarkResult(
                scenario=scenario,
                start_time=start_time,
                end_time=end_time,
                metrics=metrics,
                agent_performance=agent_performance,
                system_health=system_health,
                recommendations=recommendations
            )

            self.results.append(result)

            # 保存结果
            self._save_benchmark_result(result)

            print("✅ 基准测试完成！")
            return result

        except Exception as e:
            logger.error(f"基准测试异常: {e}", exc_info=True)
            return None

    async def _execute_benchmark(self, scenario: BenchmarkScenario) -> Tuple[PerformanceMetrics, Dict[str, Dict[str, Any]]]:
        """执行基准测试"""
        print("执行测试中...")

        # 测试参数
        concurrent_users = scenario.concurrent_users
        total_requests = scenario.total_requests
        duration_seconds = scenario.duration_minutes * 60

        # 监控数据收集
        response_times = []
        request_results = []
        system_metrics = []

        # 启动系统监控
        monitoring_stop = threading.Event()
        monitor_thread = threading.Thread(
            target=self._monitor_system_resources,
            args=(system_metrics, monitoring_stop)
        )
        monitor_thread.start()

        try:
            # 创建测试查询
            test_queries = self._generate_test_queries(scenario, total_requests)

            # 执行并发测试
            start_time = time.time()

            semaphore = asyncio.Semaphore(concurrent_users)

            async def execute_request(query: Dict[str, Any]) -> Tuple[float, bool, Any]:
                async with semaphore:
                    request_start = time.time()
                    try:
                        # 模拟API调用
                        success, result = await self._simulate_api_call(query)
                        request_time = time.time() - request_start
                        return request_time, success, result
                    except Exception as e:
                        request_time = time.time() - request_start
                        return request_time, False, str(e)

            # 批量执行请求
            tasks = [execute_request(query) for query in test_queries]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            end_time = time.time()
            total_duration = end_time - start_time

            # 处理结果
            successful_requests = 0
            failed_requests = 0
            timeouts = 0

            for result in results:
                if isinstance(result, Exception):
                    failed_requests += 1
                    response_times.append(5.0)  # 异常请求按5秒计算
                else:
                    request_time, success, _ = result
                    response_times.append(request_time)

                    if success:
                        successful_requests += 1
                    else:
                        failed_requests += 1

                    if request_time > 30:  # 30秒超时
                        timeouts += 1

            # 计算统计指标
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)

                # 计算百分位数
                sorted_times = sorted(response_times)
                p95_index = int(len(sorted_times) * 0.95)
                p99_index = int(len(sorted_times) * 0.99)

                p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
                p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
            else:
                avg_response_time = min_response_time = max_response_time = p95_response_time = p99_response_time = 0

            # 计算吞吐量
            requests_per_second = len(results) / total_duration if total_duration > 0 else 0

            # 计算系统资源使用情况
            if system_metrics:
                cpu_usages = [m['cpu'] for m in system_metrics]
                memory_usages = [m['memory'] for m in system_metrics]

                avg_cpu_usage = statistics.mean(cpu_usages)
                max_cpu_usage = max(cpu_usages)
                avg_memory_usage = statistics.mean(memory_usages)
                max_memory_usage = max(memory_usages)
            else:
                avg_cpu_usage = max_cpu_usage = avg_memory_usage = max_memory_usage = 0

            # 计算错误率
            total_requests = len(results)
            error_rate = failed_requests / total_requests if total_requests > 0 else 0
            timeout_rate = timeouts / total_requests if total_requests > 0 else 0

            metrics = PerformanceMetrics(
                timestamp=datetime.now(),
                avg_response_time=avg_response_time,
                min_response_time=min_response_time,
                max_response_time=max_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                requests_per_second=requests_per_second,
                total_requests=total_requests,
                successful_requests=successful_requests,
                failed_requests=failed_requests,
                avg_cpu_usage=avg_cpu_usage,
                max_cpu_usage=max_cpu_usage,
                avg_memory_usage=avg_memory_usage,
                max_memory_usage=max_memory_usage,
                error_rate=error_rate,
                timeout_rate=timeout_rate
            )

            # 模拟Agent性能数据（实际应该从监控系统获取）
            agent_performance = {
                'ReasoningExpert': {'calls': 80, 'avg_time': 2.1, 'success_rate': 0.95},
                'RAGExpert': {'calls': 75, 'avg_time': 1.8, 'success_rate': 0.96},
                'AgentCoordinator': {'calls': 60, 'avg_time': 1.5, 'success_rate': 0.98},
                'QualityController': {'calls': 55, 'avg_time': 1.2, 'success_rate': 0.97}
            }

            return metrics, agent_performance

        finally:
            # 停止系统监控
            monitoring_stop.set()
            monitor_thread.join(timeout=5)

    def _monitor_system_resources(self, metrics_list: List[Dict[str, float]], stop_event: threading.Event):
        """监控系统资源使用情况"""
        while not stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent

                metrics_list.append({
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    'timestamp': time.time()
                })

                time.sleep(5)  # 每5秒收集一次

            except Exception as e:
                logger.error(f"系统资源监控异常: {e}")
                time.sleep(1)

    def _generate_test_queries(self, scenario: BenchmarkScenario, total_requests: int) -> List[Dict[str, Any]]:
        """生成测试查询"""
        queries = []

        # 根据请求类型分布生成查询
        type_weights = {
            'simple_question': 0.4,
            'analysis_query': 0.3,
            'complex_reasoning': 0.2,
            'multi_step_task': 0.1
        }

        query_templates = {
            'simple_question': [
                "什么是机器学习？",
                "Python是什么编程语言？",
                "云计算的基本概念是什么？",
                "数据库的作用是什么？"
            ],
            'analysis_query': [
                "分析当前AI发展趋势",
                "比较不同编程语言的优缺点",
                "解释深度学习的原理",
                "讨论软件工程的最佳实践"
            ],
            'complex_reasoning': [
                "如何设计一个高可用的分布式系统？",
                "分析机器学习模型过拟合的原因和解决方案",
                "讨论微服务架构的优势和挑战",
                "如何优化数据库查询性能？"
            ],
            'multi_step_task': [
                "请分析当前AI市场的竞争格局，并预测未来发展趋势",
                "设计一个完整的用户认证和授权系统，包括前端、后端和数据库设计",
                "分析一个软件项目的风险，并制定相应的风险缓解策略"
            ]
        }

        for i in range(total_requests):
            # 随机选择查询类型
            query_type = self._weighted_choice(scenario.request_types, type_weights)

            # 随机选择查询模板
            templates = query_templates.get(query_type, ["默认查询"])
            query_text = self._random_choice(templates)

            queries.append({
                'id': f"query_{i+1}",
                'type': query_type,
                'text': query_text,
                'timestamp': datetime.now().isoformat()
            })

        return queries

    def _weighted_choice(self, items: List[str], weights: Dict[str, float]) -> str:
        """加权随机选择"""
        import random

        # 过滤出有效的项目
        valid_items = [item for item in items if item in weights]
        if not valid_items:
            return items[0] if items else "simple_question"

        # 计算权重
        total_weight = sum(weights.get(item, 0) for item in valid_items)
        if total_weight == 0:
            return self._random_choice(valid_items)

        # 随机选择
        r = random.uniform(0, total_weight)
        cumulative = 0

        for item in valid_items:
            cumulative += weights.get(item, 0)
            if r <= cumulative:
                return item

        return valid_items[-1]

    def _random_choice(self, items: List[str]) -> str:
        """随机选择"""
        import random
        return random.choice(items) if items else "默认查询"

    async def _simulate_api_call(self, query: Dict[str, Any]) -> Tuple[bool, Any]:
        """模拟API调用"""
        # 模拟不同的响应时间和成功率
        import random

        query_type = query.get('type', 'simple_question')

        # 根据查询类型设置不同的基础响应时间
        base_times = {
            'simple_question': 1.0,
            'analysis_query': 2.0,
            'complex_reasoning': 3.0,
            'multi_step_task': 4.0
        }

        base_time = base_times.get(query_type, 2.0)

        # 添加随机变化
        response_time = base_time + random.uniform(-0.5, 1.0)
        response_time = max(0.5, response_time)  # 最小0.5秒

        # 模拟成功率
        success_rates = {
            'simple_question': 0.98,
            'analysis_query': 0.95,
            'complex_reasoning': 0.90,
            'multi_step_task': 0.85
        }

        success_rate = success_rates.get(query_type, 0.95)
        success = random.random() < success_rate

        # 模拟处理
        await asyncio.sleep(response_time * 0.1)  # 模拟部分处理时间

        if success:
            return True, {
                'query_id': query['id'],
                'response_time': response_time,
                'answer': f"这是对'{query['text']}'的回答",
                'quality_score': random.uniform(0.7, 1.0)
            }
        else:
            return False, f"处理查询失败: {query['text']}"

    async def _check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        try:
            # 检查系统资源
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # 检查进程状态（简化）
            health_status = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_usage': disk.percent,
                'overall_status': 'healthy'
            }

            # 评估整体健康状态
            if cpu_percent > 90 or memory.percent > 90:
                health_status['overall_status'] = 'critical'
            elif cpu_percent > 80 or memory.percent > 80:
                health_status['overall_status'] = 'warning'
            else:
                health_status['overall_status'] = 'healthy'

            return health_status

        except Exception as e:
            logger.error(f"系统健康检查异常: {e}")
            return {'overall_status': 'unknown', 'error': str(e)}

    def _generate_recommendations(self, metrics: PerformanceMetrics,
                                agent_performance: Dict[str, Dict[str, Any]],
                                system_health: Dict[str, Any]) -> List[str]:
        """生成性能建议"""
        recommendations = []

        # 基于响应时间
        if metrics.avg_response_time > 3.0:
            recommendations.append("平均响应时间过长，建议优化Agent处理逻辑或增加缓存")

        if metrics.p95_response_time > 5.0:
            recommendations.append("P95响应时间过高，可能存在性能瓶颈，建议进行深度性能分析")

        # 基于错误率
        if metrics.error_rate > 0.1:
            recommendations.append("错误率偏高，建议检查Agent稳定性并增加错误处理")

        # 基于资源使用
        if metrics.max_cpu_usage > 85:
            recommendations.append("CPU使用率过高，建议优化计算密集型操作或考虑水平扩展")

        if metrics.max_memory_usage > 85:
            recommendations.append("内存使用率过高，建议检查内存泄漏并优化内存使用")

        # 基于系统健康
        if system_health.get('overall_status') == 'critical':
            recommendations.append("系统负载严重，建议立即采取降载措施")

        # 基于吞吐量
        if metrics.requests_per_second < 10:
            recommendations.append("吞吐量较低，建议优化并发处理能力")

        # 如果没有问题
        if not recommendations:
            recommendations.append("系统性能表现良好，继续保持监控")

        return recommendations

    def _save_benchmark_result(self, result: BenchmarkResult):
        """保存基准测试结果"""
        try:
            timestamp = result.start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_{result.scenario.name}_{timestamp}.json"
            filepath = self.data_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    'scenario': {
                        'name': result.scenario.name,
                        'description': result.scenario.description,
                        'concurrent_users': result.scenario.concurrent_users,
                        'total_requests': result.scenario.total_requests,
                        'duration_minutes': result.scenario.duration_minutes
                    },
                    'time_range': {
                        'start': result.start_time.isoformat(),
                        'end': result.end_time.isoformat(),
                        'duration_seconds': (result.end_time - result.start_time).total_seconds()
                    },
                    'metrics': {
                        'avg_response_time': result.metrics.avg_response_time,
                        'min_response_time': result.metrics.min_response_time,
                        'max_response_time': result.metrics.max_response_time,
                        'p95_response_time': result.metrics.p95_response_time,
                        'p99_response_time': result.metrics.p99_response_time,
                        'requests_per_second': result.metrics.requests_per_second,
                        'total_requests': result.metrics.total_requests,
                        'successful_requests': result.metrics.successful_requests,
                        'failed_requests': result.metrics.failed_requests,
                        'avg_cpu_usage': result.metrics.avg_cpu_usage,
                        'max_cpu_usage': result.metrics.max_cpu_usage,
                        'avg_memory_usage': result.metrics.avg_memory_usage,
                        'max_memory_usage': result.metrics.max_memory_usage,
                        'error_rate': result.metrics.error_rate,
                        'timeout_rate': result.metrics.timeout_rate
                    },
                    'agent_performance': result.agent_performance,
                    'system_health': result.system_health,
                    'recommendations': result.recommendations
                }, f, ensure_ascii=False, indent=2, default=str)

            logger.info(f"基准测试结果已保存: {filepath}")

        except Exception as e:
            logger.error(f"保存基准测试结果异常: {e}")

    async def run_all_scenarios(self) -> List[BenchmarkResult]:
        """运行所有测试场景"""
        results = []

        for scenario in self.test_scenarios:
            print(f"\n{'='*80}")
            result = await self.run_benchmark_scenario(scenario.name)
            if result:
                results.append(result)

            # 场景间休息
            if scenario != self.test_scenarios[-1]:
                print("⏱️  场景间休息30秒...")
                await asyncio.sleep(30)

        return results

    def generate_performance_report(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """生成性能报告"""
        if not results:
            return {'error': '没有可用的测试结果'}

        # 汇总统计
        summary = {
            'total_scenarios': len(results),
            'overall_performance_score': 0,
            'best_scenario': None,
            'worst_scenario': None,
            'performance_trends': [],
            'bottlenecks': [],
            'recommendations': []
        }

        # 计算总体性能评分
        performance_scores = []
        for result in results:
            score = self._calculate_performance_score(result.metrics)
            performance_scores.append(score)

        summary['overall_performance_score'] = statistics.mean(performance_scores) if performance_scores else 0

        # 识别最佳和最差场景
        if results:
            scored_results = [(self._calculate_performance_score(r.metrics), r) for r in results]
            scored_results.sort(key=lambda x: x[0])

            summary['best_scenario'] = scored_results[-1][1].scenario.name
            summary['worst_scenario'] = scored_results[0][1].scenario.name

        # 识别瓶颈
        summary['bottlenecks'] = self._identify_bottlenecks(results)

        # 生成建议
        summary['recommendations'] = self._generate_overall_recommendations(results)

        return summary

    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> float:
        """计算性能评分"""
        # 基于多个指标计算综合评分
        response_time_score = max(0, 1 - (metrics.avg_response_time - 1) / 4)  # 1-5秒范围
        throughput_score = min(1.0, metrics.requests_per_second / 50)  # 50 RPS为基准
        error_score = 1 - metrics.error_rate
        resource_score = 1 - (metrics.avg_cpu_usage + metrics.avg_memory_usage) / 200  # 资源使用评分

        # 加权平均
        weights = [0.3, 0.3, 0.2, 0.2]
        scores = [response_time_score, throughput_score, error_score, resource_score]

        return sum(w * s for w, s in zip(weights, scores))

    def _identify_bottlenecks(self, results: List[BenchmarkResult]) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []

        # 检查是否有明显的性能下降模式
        response_times = [r.metrics.avg_response_time for r in results]
        if len(response_times) > 1:
            if response_times[-1] > response_times[0] * 1.5:
                bottlenecks.append("响应时间随负载增加显著上升，可能存在扩展性问题")

        # 检查资源使用
        for result in results:
            if result.metrics.max_cpu_usage > 90:
                bottlenecks.append(f"{result.scenario.name}场景CPU使用率过高，可能存在计算瓶颈")

            if result.metrics.max_memory_usage > 90:
                bottlenecks.append(f"{result.scenario.name}场景内存使用率过高，可能存在内存泄漏")

        # 检查错误率
        for result in results:
            if result.metrics.error_rate > 0.15:
                bottlenecks.append(f"{result.scenario.name}场景错误率过高，需要检查稳定性")

        if not bottlenecks:
            bottlenecks.append("未发现明显的性能瓶颈")

        return bottlenecks

    def _generate_overall_recommendations(self, results: List[BenchmarkResult]) -> List[str]:
        """生成总体建议"""
        recommendations = []

        if results:
            # 基于整体性能评分
            avg_score = statistics.mean([self._calculate_performance_score(r.metrics) for r in results])

            if avg_score > 0.8:
                recommendations.append("系统整体性能表现优秀，建议继续监控并逐步增加替换率")
            elif avg_score > 0.6:
                recommendations.append("系统性能表现良好，但仍有优化空间")
            else:
                recommendations.append("系统性能需要改进，建议优先解决性能瓶颈")

            # 检查趋势
            response_times = [r.metrics.avg_response_time for r in results]
            if len(response_times) >= 2:
                trend = statistics.linear_regression(range(len(response_times)), response_times)[0]
                if trend > 0.1:
                    recommendations.append("响应时间呈上升趋势，建议关注系统扩展性")

        recommendations.extend([
            "建议定期运行性能基准测试以监控趋势变化",
            "考虑实施自动扩缩容以应对负载波动",
            "优化数据库查询和缓存策略以提升响应速度"
        ])

        return recommendations


# 全局基准测试系统实例
_benchmark_system = None


def get_benchmark_system() -> PerformanceBenchmarkSystem:
    """获取全局基准测试系统实例"""
    global _benchmark_system
    if _benchmark_system is None:
        _benchmark_system = PerformanceBenchmarkSystem()
    return _benchmark_system


async def run_performance_benchmark(scenario: str = "medium_load") -> Optional[BenchmarkResult]:
    """运行性能基准测试"""
    system = get_benchmark_system()
    return await system.run_benchmark_scenario(scenario)


async def run_full_performance_test() -> Dict[str, Any]:
    """运行完整性能测试"""
    system = get_benchmark_system()
    results = await system.run_all_scenarios()
    report = system.generate_performance_report(results)
    return report
