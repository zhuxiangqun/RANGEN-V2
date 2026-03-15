#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能趋势分析使用示例
演示如何使用增强的性能监控器进行趋势分析
"""

import time
import random
import logging
from datetime import datetime, timedelta
from tools.detection.monitoring.performance_monitor import (
    get_performance_monitor, 
    PerformanceMonitor,
    PerformanceTrend,
    TrendAnalysis
)

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simulate_performance_data():
    """模拟性能数据收集"""
    monitor = get_performance_monitor()
    
    logger.info("开始模拟性能数据收集...")
    
    # 模拟1小时的性能数据，每30秒收集一次
    for i in range(120):  # 120次收集，每次30秒
        # 模拟CPU使用率（逐渐上升趋势）
        cpu_usage = 20 + i * 0.5 + random.uniform(-5, 5)
        cpu_usage = max(0, min(100, cpu_usage))
        
        # 模拟内存使用率（稳定趋势）
        memory_usage = 60 + random.uniform(-10, 10)
        memory_usage = max(0, min(100, memory_usage))
        
        # 模拟响应时间（波动趋势）
        response_time = 0.2 + random.uniform(-0.1, 0.3)
        response_time = max(0.05, response_time)
        
        # 收集指标
        metrics = monitor.collect_system_metrics()
        
        # 添加自定义指标
        monitor.metrics_history.append(
            monitor.metrics_history[-1].__class__(
                name="custom_cpu_usage",
                value=cpu_usage,
                unit="%",
                timestamp=datetime.now(),
                level=monitor._get_performance_level('cpu_usage', cpu_usage),
                description="模拟CPU使用率"
            )
        )
        
        monitor.metrics_history.append(
            monitor.metrics_history[-1].__class__(
                name="custom_memory_usage", 
                value=memory_usage,
                unit="%",
                timestamp=datetime.now(),
                level=monitor._get_performance_level('memory_usage', memory_usage),
                description="模拟内存使用率"
            )
        )
        
        monitor.metrics_history.append(
            monitor.metrics_history[-1].__class__(
                name="custom_response_time",
                value=response_time,
                unit="s",
                timestamp=datetime.now(),
                level=monitor._get_performance_level('response_time', response_time),
                description="模拟响应时间"
            )
        )
        
        # 更新趋势数据
        monitor._update_trend_data([
            monitor.metrics_history[-3],
            monitor.metrics_history[-2], 
            monitor.metrics_history[-1]
        ])
        
        if i % 10 == 0:
            logger.info(f"已收集 {i+1} 次性能数据")
        
        time.sleep(0.1)  # 快速模拟，实际应该是30秒

def demonstrate_trend_analysis():
    """演示趋势分析功能"""
    monitor = get_performance_monitor()
    
    logger.info("开始趋势分析演示...")
    
    # 1. 分析整体趋势
    trend_analysis = monitor.analyze_trends("1h")
    
    print("\n" + "="*60)
    print("📊 性能趋势分析报告")
    print("="*60)
    print(f"分析时间: {trend_analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总体趋势: {trend_analysis.overall_trend}")
    print(f"趋势分数: {trend_analysis.trend_score:.2f}")
    print(f"分析指标数量: {len(trend_analysis.metric_trends)}")
    
    # 2. 显示各指标趋势
    print("\n📈 各指标趋势详情:")
    print("-" * 40)
    for trend in trend_analysis.metric_trends:
        print(f"指标: {trend.metric_name}")
        print(f"  趋势方向: {trend.trend_direction}")
        print(f"  趋势强度: {trend.trend_strength:.2f}")
        print(f"  变化百分比: {trend.change_percentage:.1f}%")
        if trend.prediction is not None:
            print(f"  预测值: {trend.prediction:.2f} (置信度: {trend.confidence:.1%})")
        print()
    
    # 3. 显示告警和建议
    if trend_analysis.alerts:
        print("🚨 性能告警:")
        print("-" * 20)
        for alert in trend_analysis.alerts:
            print(f"• {alert}")
        print()
    
    if trend_analysis.recommendations:
        print("💡 优化建议:")
        print("-" * 20)
        for rec in trend_analysis.recommendations:
            print(f"• {rec}")
        print()
    
    # 4. 获取趋势摘要
    summary = monitor.get_trend_summary()
    print("📋 趋势摘要:")
    print("-" * 20)
    print(f"告警数量: {summary['alerts_count']}")
    print(f"建议数量: {summary['recommendations_count']}")
    
    if summary['top_concerns']:
        print("主要关注点:")
        for concern in summary['top_concerns']:
            print(f"  • {concern['metric']}: {concern['trend']} ({concern['change']:.1f}%)")

def demonstrate_unified_center_integration():
    """演示统一中心系统集成"""
    from src.utils.unified_centers import get_unified_center
    
    logger.info("演示统一中心系统集成...")
    
    # 通过统一中心获取性能监控器
    monitor = get_unified_center('get_performance_monitor')
    
    if monitor:
        print("\n" + "="*60)
        print("🔗 统一中心系统集成演示")
        print("="*60)
        
        # 获取趋势摘要
        summary = monitor.get_trend_summary()
        print(f"通过统一中心获取的性能监控器正常工作")
        print(f"当前趋势分数: {summary['trend_score']:.2f}")
        print(f"总体趋势: {summary['overall_trend']}")
    else:
        print("❌ 无法从统一中心获取性能监控器")

if __name__ == "__main__":
    print("🚀 性能趋势分析演示程序")
    print("="*60)
    
    try:
        # 1. 模拟性能数据
        simulate_performance_data()
        
        # 2. 演示趋势分析
        demonstrate_trend_analysis()
        
        # 3. 演示统一中心集成
        demonstrate_unified_center_integration()
        
        print("\n✅ 演示完成！")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"\n❌ 演示失败: {e}")
