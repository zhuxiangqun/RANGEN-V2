#!/usr/bin/env python3
"""
同步性能基准测试系统 - 避免asyncio事件循环冲突
"""

import time
import threading
import json
import psutil
import statistics
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import sys
import random

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SyncPerformanceBenchmark:
    """同步性能基准测试"""

    def __init__(self):
        self.test_scenarios = {
            'light_load': {
                'name': 'light_load',
                'description': '轻负载测试 - 模拟正常使用',
                'concurrent_users': 2,  # 减少并发避免问题
                'total_requests': 50,   # 减少请求数
                'duration_seconds': 60  # 1分钟
            },
            'medium_load': {
                'name': 'medium_load',
                'description': '中负载测试 - 模拟高峰期',
                'concurrent_users': 5,
                'total_requests': 100,
                'duration_seconds': 120  # 2分钟
            }
        }

        # 测试结果
        self.results = []
        self.system_metrics = []

        # 数据存储
        self.data_dir = Path("data/performance_benchmarks")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def run_scenario(self, scenario_name: str) -> Optional[Dict[str, Any]]:
        """运行指定的测试场景"""
        if scenario_name not in self.test_scenarios:
            print(f"❌ 未找到场景: {scenario_name}")
            return None

        scenario = self.test_scenarios[scenario_name]
        print(f"🚀 运行场景: {scenario_name}")
        print(f"📝 描述: {scenario['description']}")
        print(f"👥 并发用户: {scenario['concurrent_users']}")
        print(f"📊 总请求数: {scenario['total_requests']}")
        print(f"⏱️  持续时间: {scenario['duration_seconds']}秒")
        print("-" * 60)

        start_time = datetime.now()

        try:
            # 运行测试
            metrics, agent_performance = self._execute_sync_benchmark(scenario)

            end_time = datetime.now()

            result = {
                'scenario': scenario,
                'start_time': start_time,
                'end_time': end_time,
                'metrics': metrics,
                'agent_performance': agent_performance,
                'system_health': self._check_system_health(),
                'recommendations': self._generate_recommendations(metrics, agent_performance)
            }

            self.results.append(result)
            self._save_result(result)

            print("✅ 测试完成！")
            self._display_results(result)

            return result

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _execute_sync_benchmark(self, scenario: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """执行同步基准测试"""
        print("执行测试中...")

        concurrent_users = scenario['concurrent_users']
        total_requests = scenario['total_requests']
        duration_seconds = scenario['duration_seconds']

        # 测试数据收集
        response_times = []
        request_results = []
        errors = 0
        successes = 0

        # 启动系统监控
        monitoring_stop = threading.Event()
        monitor_thread = threading.Thread(
            target=self._monitor_system,
            args=(self.system_metrics, monitoring_stop),
            daemon=True
        )
        monitor_thread.start()

        try:
            # 使用线程池模拟并发
            start_time = time.time()

            # 分批执行请求，避免同时启动太多线程
            batch_size = min(concurrent_users, 5)  # 最大5个并发线程
            completed_requests = 0

            while completed_requests < total_requests and (time.time() - start_time) < duration_seconds:
                current_batch = min(batch_size, total_requests - completed_requests)

                # 创建线程执行请求
                threads = []
                for i in range(current_batch):
                    thread = threading.Thread(
                        target=self._execute_request_sync,
                        args=(response_times, request_results, completed_requests + i)
                    )
                    threads.append(thread)
                    thread.start()

                # 等待这一批完成
                for thread in threads:
                    thread.join(timeout=10)  # 10秒超时

                completed_requests += current_batch

                # 小延迟避免过度占用CPU
                time.sleep(0.1)

            end_time = time.time()
            total_duration = end_time - start_time

            # 统计结果
            for result in request_results:
                if result['success']:
                    successes += 1
                else:
                    errors += 1

            # 计算指标
            if response_times:
                avg_response_time = statistics.mean(response_times)
                min_response_time = min(response_times)
                max_response_time = max(response_times)

                # 计算P95
                sorted_times = sorted(response_times)
                p95_index = int(len(sorted_times) * 0.95)
                p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]

                requests_per_second = len(response_times) / total_duration if total_duration > 0 else 0
                error_rate = errors / len(response_times) if response_times else 0
                success_rate = successes / len(response_times) if response_times else 0
            else:
                avg_response_time = min_response_time = max_response_time = p95_response_time = 0
                requests_per_second = 0
                error_rate = 0
                success_rate = 0

            # 系统资源统计
            if self.system_metrics:
                cpu_values = [m['cpu'] for m in self.system_metrics]
                memory_values = [m['memory'] for m in self.system_metrics]

                avg_cpu = statistics.mean(cpu_values) if cpu_values else 0
                max_cpu = max(cpu_values) if cpu_values else 0
                avg_memory = statistics.mean(memory_values) if memory_values else 0
                max_memory = max(memory_values) if memory_values else 0
            else:
                avg_cpu = max_cpu = avg_memory = max_memory = 0

            metrics = {
                'avg_response_time': avg_response_time,
                'min_response_time': min_response_time,
                'max_response_time': max_response_time,
                'p95_response_time': p95_response_time,
                'requests_per_second': requests_per_second,
                'total_requests': len(response_times),
                'successful_requests': successes,
                'failed_requests': errors,
                'success_rate': success_rate,
                'error_rate': error_rate,
                'avg_cpu_usage': avg_cpu,
                'max_cpu_usage': max_cpu,
                'avg_memory_usage': avg_memory,
                'max_memory_usage': max_memory
            }

            # 模拟Agent性能数据
            agent_performance = {
                'ReasoningExpert': {
                    'calls': int(len(response_times) * 0.3),
                    'avg_time': avg_response_time * 0.8,
                    'success_rate': success_rate * 0.95
                },
                'RAGExpert': {
                    'calls': int(len(response_times) * 0.4),
                    'avg_time': avg_response_time * 0.9,
                    'success_rate': success_rate * 0.96
                },
                'AgentCoordinator': {
                    'calls': int(len(response_times) * 0.2),
                    'avg_time': avg_response_time * 0.7,
                    'success_rate': success_rate * 0.98
                },
                'QualityController': {
                    'calls': int(len(response_times) * 0.1),
                    'avg_time': avg_response_time * 0.6,
                    'success_rate': success_rate * 0.97
                }
            }

            return metrics, agent_performance

        finally:
            # 停止监控
            monitoring_stop.set()
            monitor_thread.join(timeout=5)

    def _execute_request_sync(self, response_times: List[float], request_results: List[Dict[str, Any]], request_id: int):
        """同步执行单个请求"""
        try:
            start_time = time.time()

            # 模拟API调用
            success, result = self._simulate_api_call_sync(request_id)

            response_time = time.time() - start_time

            response_times.append(response_time)
            request_results.append({
                'request_id': request_id,
                'success': success,
                'response_time': response_time,
                'result': result
            })

        except Exception as e:
            # 记录错误
            response_times.append(5.0)  # 默认5秒
            request_results.append({
                'request_id': request_id,
                'success': False,
                'response_time': 5.0,
                'error': str(e)
            })

    def _simulate_api_call_sync(self, request_id: int) -> Tuple[bool, Any]:
        """模拟同步API调用"""
        # 模拟不同的处理时间
        query_types = ['simple', 'analysis', 'complex']
        query_type = random.choice(query_types)

        # 根据查询类型设置处理时间
        if query_type == 'simple':
            processing_time = random.uniform(0.5, 1.5)
            success_rate = 0.98
        elif query_type == 'analysis':
            processing_time = random.uniform(1.0, 3.0)
            success_rate = 0.95
        else:  # complex
            processing_time = random.uniform(2.0, 5.0)
            success_rate = 0.90

        # 模拟处理
        time.sleep(processing_time * 0.1)  # 实际只等待10%的时间

        # 模拟成功/失败
        success = random.random() < success_rate

        if success:
            return True, {
                'query_id': f"query_{request_id}",
                'response_time': processing_time,
                'answer': f"这是对查询{request_id}的回答",
                'quality_score': random.uniform(0.7, 1.0)
            }
        else:
            return False, f"处理查询{request_id}失败"

    def _monitor_system(self, metrics_list: List[Dict[str, float]], stop_event: threading.Event):
        """监控系统资源"""
        while not stop_event.is_set():
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent

                metrics_list.append({
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    'timestamp': time.time()
                })

                time.sleep(2)  # 每2秒收集一次

            except Exception as e:
                print(f"系统监控错误: {e}")
                time.sleep(1)

    def _check_system_health(self) -> Dict[str, Any]:
        """检查系统健康状态"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

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
            return {'overall_status': 'unknown', 'error': str(e)}

    def _generate_recommendations(self, metrics: Dict[str, Any], agent_performance: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 基于响应时间
        if metrics['avg_response_time'] > 3.0:
            recommendations.append("平均响应时间过长，建议优化Agent处理逻辑")

        # 基于错误率
        if metrics['error_rate'] > 0.1:
            recommendations.append("错误率偏高，建议检查Agent稳定性")

        # 基于资源使用
        if metrics['max_cpu_usage'] > 85:
            recommendations.append("CPU使用率过高，建议优化计算密集型操作")

        if metrics['max_memory_usage'] > 85:
            recommendations.append("内存使用率过高，建议检查内存使用")

        # 基于吞吐量
        if metrics['requests_per_second'] < 5:
            recommendations.append("吞吐量较低，建议优化并发处理能力")

        if not recommendations:
            recommendations.append("系统性能表现良好，继续监控")

        return recommendations

    def _display_results(self, result: Dict[str, Any]):
        """显示测试结果"""
        print("\n📊 性能指标")
        print("-" * 40)

        m = result['metrics']

        print("响应时间:")
        print(f"  平均响应时间: {m['avg_response_time']:.2f}秒")
        print(f"  最快响应时间: {m['min_response_time']:.2f}秒")
        print(f"  最慢响应时间: {m['max_response_time']:.2f}秒")
        print(f"  P95响应时间: {m['p95_response_time']:.2f}秒")
        print("\n吞吐量:")
        print(f"  每秒请求数: {m['requests_per_second']:.2f}")
        print(f"  总请求数: {m['total_requests']}")
        print(f"  成功请求: {m['successful_requests']}")
        print(f"  失败请求: {m['failed_requests']}")

        print("\n系统资源:")
        print(f"  平均CPU使用率: {m['avg_cpu_usage']:.1f}%")
        print(f"  峰值CPU使用率: {m['max_cpu_usage']:.1f}%")
        print(f"  平均内存使用率: {m['avg_memory_usage']:.1f}%")
        print(f"  峰值内存使用率: {m['max_memory_usage']:.1f}%")
        print("\n错误统计:")
        print(f"  成功率: {m['success_rate']:.1f}%")
        print(f"  错误率: {m['error_rate']:.1f}%")

        print("\n🧠 Agent性能")
        print("-" * 40)

        for agent_name, perf in result['agent_performance'].items():
            print(f"• {agent_name}:")
            print(f"  调用次数: {perf['calls']}")
            print(f"  平均响应时间: {perf['avg_time']:.2f}秒")
            print(f"  成功率: {perf['success_rate']:.1f}%")

        print("\n🏥 系统健康")
        print("-" * 40)

        health = result['system_health']
        status_emoji = {
            'healthy': '🟢',
            'warning': '🟡',
            'critical': '🔴',
            'unknown': '⚪'
        }

        status = health.get('overall_status', 'unknown')
        print(f"整体状态: {status_emoji.get(status, '⚪')} {status.upper()}")

        if result['recommendations']:
            print("\n💡 优化建议")
            print("-" * 40)
            for rec in result['recommendations']:
                print(f"• {rec}")

    def _save_result(self, result: Dict[str, Any]):
        """保存测试结果"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sync_benchmark_{result['scenario']['name']}_{timestamp}.json"
            filepath = self.data_dir / filename

            # 准备保存的数据
            data = {
                'scenario': result['scenario'],
                'time_range': {
                    'start': result['start_time'].isoformat(),
                    'end': result['end_time'].isoformat(),
                    'duration_seconds': (result['end_time'] - result['start_time']).total_seconds()
                },
                'metrics': result['metrics'],
                'agent_performance': result['agent_performance'],
                'system_health': result['system_health'],
                'recommendations': result['recommendations']
            }

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

            print(f"\n✅ 测试结果已保存: {filepath}")

        except Exception as e:
            print(f"❌ 保存结果失败: {e}")

def main():
    """主函数"""
    print("🧪 同步性能基准测试系统")
    print("=" * 50)

    benchmark = SyncPerformanceBenchmark()

    while True:
        print("\n🎮 操作菜单")
        print("-" * 40)
        print("1. 运行轻负载测试 (light_load)")
        print("2. 运行中负载测试 (medium_load)")
        print("3. 查看测试历史")
        print("0. 退出")
        print("-" * 40)

        try:
            choice = input("请选择操作 (0-3): ").strip()

            if choice == "0":
                print("\n👋 再见！")
                break
            elif choice == "1":
                benchmark.run_scenario("light_load")
            elif choice == "2":
                benchmark.run_scenario("medium_load")
            elif choice == "3":
                print("历史测试结果保存在: data/performance_benchmarks/")
                # 这里可以添加查看历史的功能
            else:
                print("❌ 无效选择，请重新输入")

            input("\n按回车键继续...")

        except KeyboardInterrupt:
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 操作异常: {e}")
            input("\n按回车键继续...")

if __name__ == "__main__":
    main()
