#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心解决方案验证脚本
测试所有核心问题的解决方案
"""

import sys
import os
import time
import logging

# 添加src到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_dependency_injection():
    """测试依赖注入容器"""
    print("\n" + "="*60)
    print("🧪 测试1: 依赖注入容器")
    print("="*60)
    
    try:
        from src.core.dependency_injection_container import get_container
        
        container = get_container()
        print("✅ 依赖注入容器创建成功")
        
        # 注册测试服务
        class TestService:
            def __init__(self):
                self.name = "TestService"
        
        container.register_singleton(TestService, TestService)
        print("✅ 服务注册成功")
        
        # 获取服务
        service = container.get_service(TestService)
        print(f"✅ 服务获取成功: {service.name}")
        
        # 检查注册状态
        services = container.get_registered_services()
        print(f"✅ 已注册服务: {len(services)} 个")
        
        return True
        
    except Exception as e:
        print(f"❌ 依赖注入容器测试失败: {e}")
        return False


def test_ml_rl_synergy():
    """测试ML/RL协同机制"""
    print("\n" + "="*60)
    print("🧪 测试2: ML/RL协同机制")
    print("="*60)
    
    try:
        from src.ai.ml_rl_synergy_coordinator import MLRLSynergyCoordinator, SynergyMode
        
        coordinator = MLRLSynergyCoordinator()
        print("✅ ML/RL协同协调器创建成功")
        
        # 测试协同处理
        result = coordinator.coordinate("测试查询", {"urgency": "high"})
        print(f"✅ 协同处理成功: 得分 {result.synergy_score:.3f}")
        
        # 测试不同模式
        for mode in [SynergyMode.SEQUENTIAL, SynergyMode.PARALLEL, SynergyMode.ITERATIVE]:
            result = coordinator.coordinate("测试查询", mode=mode)
            print(f"✅ {mode.value} 模式测试成功")
        
        # 获取性能指标
        metrics = coordinator.get_performance_metrics()
        print(f"✅ 性能指标获取成功: {len(metrics)} 个指标")
        
        return True
        
    except Exception as e:
        print(f"❌ ML/RL协同机制测试失败: {e}")
        return False


def test_multi_step_reasoning():
    """测试多步推理引擎"""
    print("\n" + "="*60)
    print("🧪 测试3: 多步推理引擎")
    print("="*60)
    
    try:
        from src.ai.multi_step_reasoning_engine import MultiStepReasoningEngine, ReasoningType
        
        reasoning_engine = MultiStepReasoningEngine()
        print("✅ 多步推理引擎创建成功")
        
        # 测试推理
        result = reasoning_engine.reason("如果所有鸟都会飞，企鹅是鸟，那么企鹅会飞吗？")
        print(f"✅ 推理执行成功: {len(result.reasoning_chain)} 步")
        print(f"✅ 推理置信度: {result.total_confidence:.3f}")
        print(f"✅ 使用的推理类型: {[t.value for t in result.reasoning_types_used]}")
        
        # 测试不同推理类型
        result = reasoning_engine.reason("观察数据: 1,2,3,4,5 的模式是什么？", 
                                       target_reasoning_types=[ReasoningType.INDUCTIVE])
        print(f"✅ 归纳推理测试成功")
        
        # 获取性能指标
        metrics = reasoning_engine.get_performance_metrics()
        print(f"✅ 性能指标获取成功: {len(metrics)} 个指标")
        
        return True
        
    except Exception as e:
        print(f"❌ 多步推理引擎测试失败: {e}")
        return False


def test_business_logic_implementer():
    """测试业务逻辑实现器"""
    print("\n" + "="*60)
    print("🧪 测试4: 业务逻辑实现器")
    print("="*60)
    
    try:
        from src.core.business_logic_implementer import BusinessLogicImplementer, ImplementationPriority
        
        implementer = BusinessLogicImplementer()
        print("✅ 业务逻辑实现器创建成功")
        
        # 测试分析未实现方法
        analysis = implementer.analyze_unimplemented_methods("src/")
        print(f"✅ 未实现方法分析成功: {analysis['total_issues']} 个问题")
        
        # 测试创建实现计划
        plan = implementer.create_implementation_plan(analysis)
        print(f"✅ 实现计划创建成功: {plan['total_effort_hours']} 小时")
        
        # 测试实现关键功能
        results = implementer.implement_critical_functions()
        print(f"✅ 关键功能实现成功: {len(results['implemented'])} 个功能")
        
        # 获取实现状态
        status = implementer.get_implementation_status()
        print(f"✅ 实现状态获取成功: {status['implementation_rate']:.1%} 完成率")
        
        return True
        
    except Exception as e:
        print(f"❌ 业务逻辑实现器测试失败: {e}")
        return False


def test_hardcoded_data_cleaner():
    """测试硬编码数据清理器"""
    print("\n" + "="*60)
    print("🧪 测试5: 硬编码数据清理器")
    print("="*60)
    
    try:
        from src.core.hardcoded_data_cleaner import HardcodedDataCleaner
        
        cleaner = HardcodedDataCleaner()
        print("✅ 硬编码数据清理器创建成功")
        
        # 测试扫描硬编码数据
        scan_results = cleaner.scan_hardcoded_data("src/")
        print(f"✅ 硬编码数据扫描成功: {scan_results['total_issues']} 个问题")
        print(f"✅ 文件扫描: {scan_results['total_files_scanned']} 个文件")
        
        # 测试创建迁移计划
        migration_plan = cleaner.create_config_migration_plan(scan_results)
        print(f"✅ 迁移计划创建成功: {migration_plan['total_issues']} 个问题")
        
        # 测试生成报告
        report = cleaner.generate_report()
        print(f"✅ 清理报告生成成功: {len(report)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 硬编码数据清理器测试失败: {e}")
        return False


def test_system_bootstrap():
    """测试系统启动引导器"""
    print("\n" + "="*60)
    print("🧪 测试6: 系统启动引导器")
    print("="*60)
    
    try:
        from src.core.system_bootstrap import initialize_system, get_service, ILogger
        
        # 初始化系统
        success = initialize_system()
        if success:
            print("✅ 系统初始化成功")
        else:
            print("❌ 系统初始化失败")
            return False
        
        # 获取服务
        logger = get_service(ILogger)
        logger.info("系统启动测试成功")
        print("✅ 服务获取成功")
        
        return True
        
    except Exception as e:
        print(f"❌ 系统启动引导器测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 RANGEN核心解决方案验证测试")
    print("="*80)
    
    start_time = time.time()
    
    # 测试结果
    test_results = {
        'dependency_injection': test_dependency_injection(),
        'ml_rl_synergy': test_ml_rl_synergy(),
        'multi_step_reasoning': test_multi_step_reasoning(),
        'business_logic_implementer': test_business_logic_implementer(),
        'hardcoded_data_cleaner': test_hardcoded_data_cleaner(),
        'system_bootstrap': test_system_bootstrap()
    }
    
    # 统计结果
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    failed_tests = total_tests - passed_tests
    
    test_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"成功率: {passed_tests/total_tests:.1%}")
    print(f"测试耗时: {test_time:.3f}秒")
    
    print("\n📋 详细结果:")
    for test_name, result in test_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！核心解决方案验证成功！")
        return True
    else:
        print(f"\n⚠️  有 {failed_tests} 个测试失败，需要进一步调试")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
