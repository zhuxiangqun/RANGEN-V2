#!/usr/bin/env python3
"""
智能替换率优化脚本
自动分析和调整所有逐步替换Agent的替换率
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 设置项目环境
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.strategies.intelligent_replacement_optimizer import (
    get_replacement_optimizer,
    optimize_all_agents_replacement_rates,
    OptimizationStrategy
)


async def run_replacement_rate_optimization(strategy: OptimizationStrategy = OptimizationStrategy.BALANCED):
    """运行替换率优化"""
    print("🚀 开始智能替换率优化")
    print("=" * 60)
    print(f"优化策略: {strategy.value}")
    print("-" * 30)

    # 获取优化器
    optimizer = get_replacement_optimizer(strategy)

    # 显示当前配置
    config = optimizer.config
    print(f"最大调整幅度: {config.get('max_adjustment_per_step', 0):.1%}")
    print(f"最小置信度阈值: {config.get('min_confidence_threshold', 0):.1f}")
    print(f"监控窗口: {config.get('monitoring_window_hours', 0)}小时")
    print(f"稳定性观察时间: {config.get('stability_required_hours', 0)}小时")
    print()

    # 执行优化
    print("📊 正在分析和优化替换率...")
    results = await optimize_all_agents_replacement_rates()

    # 显示结果
    print("✅ 优化完成！")
    print("\n📋 优化结果汇总")
    print("-" * 50)

    total_adjustments = 0
    successful_optimizations = 0

    for agent_name, agent_results in results.items():
        if agent_results:
            result = agent_results[0]  # 最新的结果
            successful_optimizations += 1

            print(f"\n🤖 {agent_name}")
            print(f"   当前替换率: {result.current_rate:.1%}")
            print(f"   建议替换率: {result.recommended_rate:.1%}")
            print(f"   调整方向: {result.adjustment_direction.value}")
            print(f"   置信度: {result.confidence_score:.2f}")

            if result.current_rate != result.recommended_rate:
                total_adjustments += 1
                change = result.recommended_rate - result.current_rate
                print(f"   调整幅度: {'+' if change > 0 else ''}{change:.1%}")

            print(f"   推理: {result.reasoning[0] if result.reasoning else '无'}")

            # 显示预期影响
            impact = result.expected_impact
            print(f"   预期影响:")
            print(f"     响应时间变化: {impact.get('response_time_change_seconds', 0):+.2f}秒")
            print(f"     成功率变化: {impact.get('success_rate_change_percent', 0):+.1f}%")
            print(f"     风险等级: {impact.get('risk_level', 'unknown')}")
        else:
            print(f"\n❌ {agent_name} - 优化失败")

    # 汇总统计
    print(f"\n{'='*60}")
    print("📈 优化统计")
    print(f"总计Agent: {len(results)}")
    print(f"成功优化: {successful_optimizations}")
    print(f"需要调整: {total_adjustments}")
    print(f"保持不变: {successful_optimizations - total_adjustments}")

    # 保存详细报告
    await save_optimization_report(results, strategy)

    # 生成建议
    recommendations = generate_final_recommendations(results)

    if recommendations:
        print("\n💡 执行建议")
        print("-" * 30)
        for rec in recommendations:
            print(f"• {rec}")

    return results


async def save_optimization_report(results: Dict[str, List], strategy: OptimizationStrategy):
    """保存优化报告"""
    try:
        report_dir = Path("reports/replacement_optimization")
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"replacement_optimization_report_{timestamp}.json"
        filepath = report_dir / filename

        report_data = {
            'timestamp': timestamp,
            'strategy': strategy.value,
            'optimization_results': {}
        }

        for agent_name, agent_results in results.items():
            if agent_results:
                result = agent_results[0]
                report_data['optimization_results'][agent_name] = {
                    'current_rate': result.current_rate,
                    'recommended_rate': result.recommended_rate,
                    'adjustment_direction': result.adjustment_direction.value,
                    'confidence_score': result.confidence_score,
                    'reasoning': result.reasoning,
                    'expected_impact': result.expected_impact
                }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2, default=str)

        print(f"✅ 详细报告已保存: {filepath}")
        print(f"   路径: {filepath}")

    except Exception as e:
        print(f"❌ 保存报告失败: {e}")


def generate_final_recommendations(results: Dict[str, List]) -> List[str]:
    """生成最终建议"""
    recommendations = []

    # 统计调整类型
    increases = 0
    decreases = 0
    holds = 0

    for agent_results in results.values():
        if agent_results:
            direction = agent_results[0].adjustment_direction.value
            if direction == 'increase':
                increases += 1
            elif direction == 'decrease':
                decreases += 1
            else:
                holds += 1

    if increases > decreases:
        recommendations.append("整体趋势乐观，建议逐步增加多个Agent的替换率")
    elif decreases > increases:
        recommendations.append("系统压力较大，建议谨慎调整，优先减少高风险Agent的替换率")
    else:
        recommendations.append("系统运行稳定，建议保持当前替换率，持续监控")

    # 检查高风险调整
    high_risk_adjustments = []
    for agent_name, agent_results in results.items():
        if agent_results:
            impact = agent_results[0].expected_impact
            if impact.get('risk_level') == 'high':
                high_risk_adjustments.append(agent_name)

    if high_risk_adjustments:
        recommendations.append(f"以下Agent调整风险较高，建议谨慎执行: {', '.join(high_risk_adjustments)}")

    # 时间建议
    recommendations.append("建议在系统负载较低的时间段（如夜间）执行替换率调整")
    recommendations.append("调整后持续监控24小时，确认系统稳定性")

    return recommendations


def print_usage():
    """打印使用说明"""
    print("智能替换率优化工具")
    print("=" * 40)
    print("用法: python optimize_replacement_rates.py [策略]")
    print()
    print("策略选项:")
    print("  conservative    保守策略 - 缓慢调整，风险最小")
    print("  balanced       平衡策略 - 适度调整，默认选项")
    print("  aggressive     激进策略 - 快速调整，风险较高")
    print("  performance_based 性能驱动策略 - 基于性能指标调整")
    print()
    print("示例:")
    print("  python optimize_replacement_rates.py balanced")
    print("  python optimize_replacement_rates.py conservative")


async def main():
    """主函数"""
    if len(sys.argv) > 1:
        strategy_name = sys.argv[1].lower()

        strategy_map = {
            'conservative': OptimizationStrategy.CONSERVATIVE,
            'balanced': OptimizationStrategy.BALANCED,
            'aggressive': OptimizationStrategy.AGGRESSIVE,
            'performance_based': OptimizationStrategy.PERFORMANCE_BASED
        }

        if strategy_name in strategy_map:
            strategy = strategy_map[strategy_name]
        else:
            print(f"❌ 未知策略: {strategy_name}")
            print_usage()
            sys.exit(1)
    else:
        strategy = OptimizationStrategy.BALANCED
        print("ℹ️ 未指定策略，使用默认平衡策略")

    await run_replacement_rate_optimization(strategy)


if __name__ == "__main__":
    asyncio.run(main())
