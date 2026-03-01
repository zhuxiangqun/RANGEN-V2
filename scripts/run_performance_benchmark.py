#!/usr/bin/env python3
"""
运行性能基准测试
全面评估系统性能表现
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.benchmark.performance_benchmark_system import (
    get_benchmark_system,
    run_performance_benchmark,
    run_full_performance_test
)


def print_header():
    """打印头部信息"""
    print("\n" + "="*80)
    print("🧪 性能基准测试系统")
    print("="*80)


def print_available_scenarios():
    """打印可用的测试场景"""
    print("\n📋 可用测试场景")
    print("-" * 50)

    scenarios = [
        ("light_load", "轻负载测试", "5并发用户，100个请求，5分钟"),
        ("medium_load", "中负载测试", "20并发用户，500个请求，10分钟"),
        ("heavy_load", "重负载测试", "50并发用户，1000个请求，15分钟"),
        ("spike_load", "峰值负载测试", "100并发用户，2000个请求，20分钟")
    ]

    for name, desc, details in scenarios:
        print(f"• {name}: {desc}")
        print(f"    {details}")

    print("\n💡 建议按顺序运行: light_load → medium_load → heavy_load")


def run_single_scenario(scenario_name: str):
    """运行单个测试场景"""
    print(f"\n🚀 运行场景: {scenario_name}")
    print("-" * 50)

    result = asyncio.run(run_performance_benchmark(scenario_name))

    if result:
        print("✅ 测试完成！")
        display_benchmark_results(result)
    else:
        print("❌ 测试失败")


def display_benchmark_results(result):
    """显示基准测试结果"""
    print("\n📊 性能指标")
    print("-" * 40)

    m = result.metrics

    print("响应时间:")
    print(f"  平均响应时间: {m.avg_response_time:.2f}秒")
    print(f"  最快响应时间: {m.min_response_time:.2f}秒")
    print(f"  最慢响应时间: {m.max_response_time:.2f}秒")
    print(f"  P95响应时间: {m.p95_response_time:.2f}秒")
    print(f"  中位数响应时间: {m.median_response_time:.2f}秒")
    print("\n吞吐量:")
    print(f"  每秒请求数: {m.requests_per_second:.2f}")
    print(f"  总请求数: {m.total_requests}")
    print(f"  成功请求: {m.successful_requests}")
    print(f"  失败请求: {m.failed_requests}")

    print("\n系统资源:")
    print(f"  平均CPU使用率: {m.avg_cpu_usage:.1f}%")
    print(f"  峰值CPU使用率: {m.max_cpu_usage:.1f}%")
    print("\n错误统计:")
    print(f"  成功率: {m.success_rate:.1f}%")
    print(f"  错误率: {m.error_rate:.1f}%")
    print("\n🧠 Agent性能")
    print("-" * 40)

    for agent_name, perf in result.agent_performance.items():
        print(f"• {agent_name}:")
        print(f"  调用次数: {perf['calls']}")
        print(f"  平均响应时间: {perf['avg_time']:.2f}秒")
        print(f"  成功率: {perf['success_rate']:.1f}%")
    print("\n🏥 系统健康")
    print("-" * 40)

    health = result.system_health
    status_emoji = {
        'healthy': '🟢',
        'warning': '🟡',
        'critical': '🔴',
        'unknown': '⚪'
    }

    status = health.get('overall_status', 'unknown')
    print(f"整体状态: {status_emoji.get(status, '⚪')} {status.upper()}")

    if 'cpu_usage' in health:
        print(f"  CPU使用率: {health['cpu_usage']:.1f}%")
    if 'memory_usage' in health:
        print(f"  内存使用率: {health['memory_usage']:.1f}%")
    print("\n💡 建议")
    print("-" * 40)

    for rec in result.recommendations:
        print(f"• {rec}")


def run_full_test():
    """运行完整测试"""
    print("\n🚀 运行完整性能测试")
    print("⚠️  这将运行所有测试场景，可能需要较长时间")
    print("-" * 60)

    # 确认运行
    try:
        confirm = input("确认运行完整测试? (y/N): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return
    except (EOFError, KeyboardInterrupt):
        print("已取消")
        return

    print("\n开始完整性能测试...")
    report = asyncio.run(run_full_performance_test())

    print("\n🎉 完整测试完成！")
    print("=" * 60)

    display_full_test_report(report)


def display_full_test_report(report):
    """显示完整测试报告"""
    print("📋 测试汇总")
    print("-" * 40)

    print(f"测试场景数: {report.get('total_scenarios', 0)}")
    print(f"平均响应时间: {report.get('avg_response_time', 0):.2f}秒")
    print(f"最佳场景: {report.get('best_scenario', 'N/A')}")
    print(f"最差场景: {report.get('worst_scenario', 'N/A')}")

    print("\n🔍 性能瓶颈")
    print("-" * 40)
    bottlenecks = report.get('bottlenecks', [])
    if bottlenecks:
        for bottleneck in bottlenecks:
            print(f"• {bottleneck}")
    else:
        print("未发现明显瓶颈")

    print("\n💡 总体建议")
    print("-" * 40)
    recommendations = report.get('recommendations', [])
    for rec in recommendations:
        print(f"• {rec}")

    # 保存报告
    save_full_report(report)


def save_full_report(report):
    """保存完整报告"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_performance_report_{timestamp}.json"
        filepath = Path("reports/performance_benchmarks") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)

        print(f"\n✅ 完整报告已保存: {filepath}")
        print(f"   路径: {filepath}")

    except Exception as e:
        print(f"❌ 保存报告失败: {e}")


def print_menu():
    """打印菜单"""
    print("\n🎮 操作菜单")
    print("-" * 50)
    print("1. 查看可用场景")
    print("2. 运行轻负载测试 (light_load)")
    print("3. 运行中负载测试 (medium_load)")
    print("4. 运行重负载测试 (heavy_load)")
    print("5. 运行峰值负载测试 (spike_load)")
    print("6. 运行完整性能测试 (所有场景)")
    print("0. 退出")
    print("-" * 50)


async def main():
    """主函数"""
    print_header()

    while True:
        print_menu()

        try:
            choice = input("请选择操作 (0-6): ").strip()

            if choice == "0":
                print("\n👋 再见！")
                break
            elif choice == "1":
                print_available_scenarios()
            elif choice == "2":
                await run_single_scenario("light_load")
            elif choice == "3":
                await run_single_scenario("medium_load")
            elif choice == "4":
                await run_single_scenario("heavy_load")
            elif choice == "5":
                await run_single_scenario("spike_load")
            elif choice == "6":
                await run_full_test()
            else:
                print("❌ 无效选择，请重新输入")

            input("\n按回车键继续...")

        except (KeyboardInterrupt, EOFError):
            print("\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"❌ 操作异常: {e}")
            input("\n按回车键继续...")


def run_async_main():
    """安全运行异步主函数"""
    try:
        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            print("⚠️  检测到已在运行的事件循环中...")

            # 尝试使用nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
                print("✅ 使用 nest_asyncio 兼容模式")
                asyncio.run(main())
            except ImportError:
                print("❌ nest_asyncio 未安装，无法在当前环境中运行异步测试")
                print("💡 建议解决方案：")
                print("   1. 安装 nest_asyncio: pip install nest_asyncio")
                print("   2. 或使用同步版本: python3 scripts/run_performance_benchmark_sync.py")
                print("   3. 或在新的Python进程中运行")
                return

        except RuntimeError:
            # 没有运行中的事件循环，可以安全运行
            asyncio.run(main())

    except KeyboardInterrupt:
        print("\n👋 用户中断")
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_async_main()
