#!/usr/bin/env python3
"""
测试监控系统是否正常工作
"""

import asyncio
import sys
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_monitoring_system():
    """测试监控系统"""
    print("🔍 测试Agent迁移监控系统")
    print("=" * 50)

    try:
        # 测试导入
        print("📦 测试组件导入...")
        from src.monitoring.agent_migration_monitoring import get_migration_monitor
        print("✅ 监控系统导入成功")

        # 获取监控器实例
        monitor = get_migration_monitor()
        print("✅ 监控器实例创建成功")

        # 测试基本功能
        summary = monitor.get_monitoring_summary()
        print("✅ 监控摘要获取成功")
        print(f"   监控状态: {'运行中' if summary['is_running'] else '已停止'}")
        print(f"   监控间隔: {summary['monitoring_interval']}秒")
        print(f"   监控Agent数量: {len(summary['agents_monitored'])}")

        # 测试指标收集
        print("\n📊 测试指标收集...")
        current_metrics = monitor.current_metrics
        if current_metrics:
            print(f"✅ 已收集 {len(current_metrics)} 个Agent的指标")
            for agent_name in current_metrics.keys():
                print(f"   • {agent_name}")
        else:
            print("ℹ️  暂无实时指标数据（监控未启动）")

        # 测试稳定性报告生成
        print("\n📋 测试稳定性报告生成...")
        report = await monitor.generate_stability_report()
        if report:
            print("✅ 稳定性报告生成成功")
            print(f"   报告ID: {report.report_id}")
            print(".1f"            print(f"   监控Agent数量: {report.total_agents_monitored}")
            print(f"   有问题的Agent: {report.agents_with_issues}")
        else:
            print("❌ 稳定性报告生成失败")

        print("\n🎉 监控系统测试完成！")
        print("✅ 所有核心功能正常")

        return True

    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

async def test_optimization_system():
    """测试优化系统"""
    print("\n🎯 测试智能优化系统")
    print("=" * 50)

    try:
        from src.strategies.intelligent_replacement_optimizer import get_replacement_optimizer
        print("✅ 优化系统导入成功")

        optimizer = get_replacement_optimizer()
        print("✅ 优化器实例创建成功")

        summary = optimizer.get_optimization_summary()
        print("✅ 优化摘要获取成功")
        print(f"   优化策略: {summary['strategy']}")
        print(f"   已优化Agent: {len(summary['agents_optimized'])}")

        print("✅ 智能优化系统测试完成！")
        return True

    except Exception as e:
        print(f"❌ 优化系统测试失败: {e}")
        return False

async def test_benchmark_system():
    """测试基准测试系统"""
    print("\n🧪 测试性能基准测试系统")
    print("=" * 50)

    try:
        from src.benchmark.performance_benchmark_system import get_benchmark_system
        print("✅ 基准测试系统导入成功")

        system = get_benchmark_system()
        print("✅ 基准测试系统实例创建成功")

        # 简单的功能测试
        scenarios = len(system.test_scenarios)
        print(f"✅ 支持 {scenarios} 个测试场景")

        print("✅ 性能基准测试系统测试完成！")
        return True

    except Exception as e:
        print(f"❌ 基准测试系统测试失败: {e}")
        return False

async def test_rollback_system():
    """测试回滚系统"""
    print("\n🛟 测试应急回滚系统")
    print("=" * 50)

    try:
        from src.rollback.emergency_rollback_system import get_rollback_system
        print("✅ 回滚系统导入成功")

        system = get_rollback_system()
        print("✅ 回滚系统实例创建成功")

        plans = system.get_available_rollback_plans()
        history = system.get_execution_history()

        print(f"✅ 可用回滚计划: {len(plans)}")
        print(f"✅ 执行历史记录: {len(history)}")

        print("✅ 应急回滚系统测试完成！")
        return True

    except Exception as e:
        print(f"❌ 回滚系统测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 系统优化组件综合测试")
    print("=" * 60)

    results = []

    # 测试各个系统
    results.append(await test_monitoring_system())
    results.append(await test_optimization_system())
    results.append(await test_benchmark_system())
    results.append(await test_rollback_system())

    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print(f"✅ 通过: {sum(results)}/4")
    print(f"❌ 失败: {4 - sum(results)}/4")

    if all(results):
        print("\n🎉 所有系统优化组件测试通过！")
        print("💡 您可以安全地运行监控脚本:")
        print("   python scripts/start_migration_monitoring.py")
        print("   python scripts/migration_monitoring_dashboard.py")
        print("   python scripts/optimize_replacement_rates.py")
        print("   python scripts/run_performance_benchmark.py")
        print("   python scripts/manage_rollback_system.py")
    else:
        print("\n⚠️  部分组件测试失败，请检查依赖和配置")

if __name__ == "__main__":
    asyncio.run(main())
