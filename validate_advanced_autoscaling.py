#!/usr/bin/env python3
"""
验证高级自动扩缩容服务
"""

import sys
import asyncio
from datetime import datetime

def test_imports():
    """测试导入"""
    print("1. 测试导入...")
    try:
        from src.services.advanced_autoscaling_service import (
            AdvancedAutoscalingService,
            AdvancedScalingRule,
            RuleConditionType,
            ScalingDecision,
            ScalingTarget,
            MetricTrend,
            create_advanced_autoscaling_service
        )
        print("   ✅ 高级服务导入成功")
        
        from src.services.autoscaling_service import SystemMetric
        print("   ✅ 基础服务导入成功")
        
        return True
    except Exception as e:
        print(f"   ❌ 导入失败: {e}")
        return False

def test_service_creation():
    """测试服务创建"""
    print("\n2. 测试服务创建...")
    try:
        from src.services.advanced_autoscaling_service import create_advanced_autoscaling_service
        
        config = {
            "initial_agent_instances": 2,
            "initial_worker_threads": 4
        }
        
        service = create_advanced_autoscaling_service(config)
        print(f"   ✅ 服务创建成功: {service.__class__.__name__}")
        print(f"   ✅ 当前代理实例: {service.current_agent_instances}")
        print(f"   ✅ 高级规则数量: {len(service.advanced_rules)}")
        
        # 检查规则类型
        rule_types = set()
        for rule in service.advanced_rules:
            rule_types.add(rule.condition_type.value)
        
        print(f"   ✅ 规则类型: {', '.join(rule_types)}")
        
        return True
    except Exception as e:
        print(f"   ❌ 服务创建失败: {e}")
        return False

def test_metric_handling():
    """测试指标处理"""
    print("\n3. 测试指标处理...")
    try:
        from src.services.advanced_autoscaling_service import create_advanced_autoscaling_service
        from src.services.autoscaling_service import SystemMetric
        
        service = create_advanced_autoscaling_service()
        
        # 创建测试指标
        timestamp = datetime.now()
        metrics = [
            SystemMetric(name="cpu_percent", value=65.5, unit="percent", 
                        timestamp=timestamp, source="psutil"),
            SystemMetric(name="memory_percent", value=45.2, unit="percent", 
                        timestamp=timestamp, source="psutil"),
        ]
        
        # 测试指标历史更新
        service._update_metric_history(metrics)
        
        cpu_history = service.metric_history.get("cpu_percent", [])
        print(f"   ✅ 指标历史更新: {len(cpu_history)} 条CPU记录")
        
        # 测试组合指标计算
        composite_value = service._calculate_composite_metric(["cpu_percent", "memory_percent"])
        print(f"   ✅ 组合指标计算: {composite_value:.2f}")
        
        return True
    except Exception as e:
        print(f"   ❌ 指标处理失败: {e}")
        return False

async def test_async_functions():
    """测试异步函数"""
    print("\n4. 测试异步函数...")
    try:
        from src.services.advanced_autoscaling_service import create_advanced_autoscaling_service
        from src.services.autoscaling_service import SystemMetric
        
        service = create_advanced_autoscaling_service()
        
        # 添加历史数据用于趋势分析
        timestamp = datetime.now()
        for i in range(10):
            metrics = [
                SystemMetric(name="cpu_percent", value=50.0 + i * 3.0, unit="percent", 
                            timestamp=timestamp, source="psutil")
            ]
            service._update_metric_history(metrics)
        
        # 测试趋势分析
        analysis = await service._analyze_metric_trend("cpu_percent")
        if analysis:
            print(f"   ✅ 趋势分析成功: {analysis.trend.value} (斜率: {analysis.slope:.3f})")
        else:
            print("   ⚠️ 趋势分析返回None（可能数据不足）")
        
        # 测试规则评估
        test_metrics = [
            SystemMetric(name="cpu_percent", value=65.5, unit="percent", 
                        timestamp=datetime.now(), source="psutil"),
        ]
        
        decisions = await service._evaluate_scaling_rules(test_metrics)
        print(f"   ✅ 规则评估完成: {len(decisions)} 条决策")
        
        return True
    except Exception as e:
        print(f"   ❌ 异步函数测试失败: {e}")
        return False

def test_di_integration():
    """测试依赖注入集成"""
    print("\n5. 测试依赖注入集成...")
    try:
        from src.di.bootstrap import bootstrap_application
        
        bootstrap = bootstrap_application()
        
        # 尝试获取高级扩缩容服务
        from src.services.advanced_autoscaling_service import AdvancedAutoscalingService
        service = bootstrap.get_service(AdvancedAutoscalingService)
        
        if service:
            print("   ✅ 依赖注入集成成功")
            print(f"   ✅ 服务类型: {service.__class__.__name__}")
            print(f"   ✅ 规则数量: {len(service.advanced_rules)}")
        else:
            print("   ⚠️ 依赖注入服务获取失败")
            
        return service is not None
    except Exception as e:
        print(f"   ❌ 依赖注入集成失败: {e}")
        return False

async def main():
    """主函数"""
    print("=" * 60)
    print("高级自动扩缩容服务验证")
    print("=" * 60)
    
    results = []
    
    # 运行同步测试
    results.append(test_imports())
    results.append(test_service_creation())
    results.append(test_metric_handling())
    
    # 运行异步测试
    results.append(await test_async_functions())
    
    # 运行DI测试
    results.append(test_di_integration())
    
    # 总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r)
    
    print(f"总测试: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("✅ 所有测试通过!")
        return 0
    else:
        print("⚠️ 部分测试失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)