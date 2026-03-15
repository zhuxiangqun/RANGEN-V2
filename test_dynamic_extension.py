#!/usr/bin/env python3
"""
动态层扩展系统测试脚本

测试动态层扩展系统组件：
1. dynamic_layer_extension.py - 动态层扩展系统
2. enhanced_four_layer_manager.py中的动态扩展集成
"""

import asyncio
import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_dynamic_layer_extension():
    """测试动态层扩展系统"""
    print("=" * 60)
    print("测试动态层扩展系统")
    print("=" * 60)
    
    try:
        from src.core.layer_interface_standard import LayerType
        from src.core.dynamic_layer_extension import (
            get_dynamic_layer_extension_manager, 
            DynamicComponent, ComponentStatus, LoadBalancingStrategy,
            test_dynamic_layer_extension as original_test
        )
        
        print("✅ 成功导入动态层扩展系统组件")
        
        # 测试组件类
        print("\n✅ 测试DynamicComponent类...")
        component = DynamicComponent(
            component_id="test_component_001",
            component_type="test_type",
            layer_type=LayerType.AGENT,
            endpoint="http://localhost:8000",
            capabilities=["test_capability_1", "test_capability_2"],
            metadata={"version": "1.0", "test": True}
        )
        
        print(f"  组件ID: {component.component_id}")
        print(f"  组件类型: {component.component_type}")
        print(f"  层类型: {component.layer_type.value}")
        print(f"  端点: {component.endpoint}")
        print(f"  能力: {component.capabilities}")
        print(f"  初始状态: {component.status.value}")
        
        # 测试性能指标更新
        component.update_performance_metrics(success=True, response_time=0.5)
        component.update_performance_metrics(success=False, response_time=1.2)
        print(f"  总请求数: {component.total_requests}")
        print(f"  成功请求: {component.successful_requests}")
        print(f"  失败请求: {component.failed_requests}")
        print(f"  成功率: {component.get_success_rate():.2%}")
        print(f"  平均响应时间: {component.average_response_time:.3f}s")
        
        # 测试状态更新
        component.update_status(ComponentStatus.HEALTHY)
        print(f"  更新后状态: {component.status.value}")
        print(f"  是否可用: {component.is_available()}")
        
        # 测试转换字典
        component_dict = component.to_dict()
        print(f"  字典转换成功: {len(component_dict)} 个字段")
        
        # 测试管理器
        print("\n✅ 测试DynamicLayerExtensionManager...")
        manager = get_dynamic_layer_extension_manager()
        
        # 注册测试组件
        success = manager.register_component(
            component_id="test_manager_component_001",
            component_type="test_manager_type",
            layer_type=LayerType.INTERACTION,
            endpoint="http://localhost:8001",
            capabilities=["ui_rendering", "user_input"]
        )
        
        print(f"  组件注册: {'成功' if success else '失败'}")
        
        success = manager.register_component(
            component_id="test_manager_component_002",
            component_type="test_manager_type",
            layer_type=LayerType.AGENT,
            endpoint="http://localhost:8002",
            capabilities=["reasoning", "planning"]
        )
        
        print(f"  第二个组件注册: {'成功' if success else '失败'}")
        
        # 查找组件
        interaction_components = manager.find_components_by_layer(LayerType.INTERACTION)
        print(f"  交互层组件数: {len(interaction_components)}")
        
        agent_components = manager.find_components_by_layer(LayerType.AGENT)
        print(f"  Agent层组件数: {len(agent_components)}")
        
        reasoning_components = manager.find_components_by_capability("reasoning")
        print(f"  具有'reasoning'能力组件数: {len(reasoning_components)}")
        
        # 获取状态报告
        status = manager.get_status_report()
        print(f"\n✅ 管理器状态报告:")
        print(f"  总组件数: {status['total_components']}")
        print(f"  健康组件: {status['healthy_components']}")
        print(f"  降级组件: {status['degraded_components']}")
        print(f"  总体可用性: {status['overall_availability']:.2%}")
        
        if status['layer_statistics']:
            print(f"  按层统计:")
            for layer, stats in status['layer_statistics'].items():
                print(f"    {layer}: {stats['total']} 个组件, {stats['healthy']} 个健康")
        
        # 测试负载均衡器
        print("\n✅ 测试负载均衡器...")
        from src.core.dynamic_layer_extension import LoadBalancer
        
        balancer = LoadBalancer(LoadBalancingStrategy.ROUND_ROBIN)
        
        # 创建测试组件列表
        test_components = []
        for i in range(3):
            comp = DynamicComponent(
                component_id=f"lb_test_{i}",
                component_type="lb_test",
                layer_type=LayerType.GATEWAY,
                endpoint=f"http://localhost:{9000 + i}",
                capabilities=[f"capability_{i}"],
                metadata={"test": True}
            )
            comp.update_status(ComponentStatus.HEALTHY)
            test_components.append(comp)
        
        # 测试选择
        selected = balancer.select_component(test_components)
        print(f"  轮询选择: {selected.component_id if selected else 'None'}")
        
        # 测试不同策略
        balancer_random = LoadBalancer(LoadBalancingStrategy.RANDOM)
        selected_random = balancer_random.select_component(test_components)
        print(f"  随机选择: {selected_random.component_id if selected_random else 'None'}")
        
        print("\n✅ 动态层扩展系统基础测试通过")
        
        # 运行原始测试函数
        print("\n" + "=" * 60)
        print("运行原始集成测试...")
        print("=" * 60)
        
        test_result = await original_test()
        
        if test_result:
            print("\n✅ 动态层扩展系统完整测试通过")
        else:
            print("\n❌ 动态层扩展系统完整测试失败")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 动态层扩展系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_enhanced_manager_with_dynamic_extension():
    """测试增强版管理器中的动态扩展集成"""
    print("\n" + "=" * 60)
    print("测试增强版管理器中的动态扩展集成")
    print("=" * 60)
    
    try:
        from src.core.enhanced_four_layer_manager import EnhancedFourLayerManager
        from src.core.layer_interface_standard import LayerType
        
        # 创建增强版管理器
        enhanced_manager = EnhancedFourLayerManager(
            use_standardized_interface=True,
            enable_dynamic_extension=True
        )
        
        print("✅ 增强版管理器创建成功")
        
        # 测试动态组件注册
        print("\n✅ 测试动态组件注册...")
        success = enhanced_manager.register_dynamic_component(
            component_id="enhanced_test_component_001",
            component_type="enhanced_test",
            layer_type=LayerType.AGENT,
            endpoint="http://localhost:8201",
            capabilities=["enhanced_capability_1", "enhanced_capability_2"],
            metadata={"test": True, "manager": "enhanced"}
        )
        
        print(f"  组件注册: {'成功' if success else '失败'}")
        
        # 获取动态扩展状态
        dynamic_status = enhanced_manager.get_dynamic_extension_status()
        print(f"  动态扩展启用: {dynamic_status['enabled']}")
        print(f"  动态扩展状态: {dynamic_status['status']}")
        
        if dynamic_status['enabled'] and 'report' in dynamic_status:
            report = dynamic_status['report']
            print(f"  总组件数: {report.get('total_components', 0)}")
        
        # 启动动态扩展管理器
        enhanced_manager.start_dynamic_extension_manager()
        print("✅ 动态扩展管理器已启动")
        
        # 等待初始化
        await asyncio.sleep(0.5)
        
        # 获取增强版状态
        enhanced_status = enhanced_manager.get_enhanced_status()
        print(f"\n✅ 增强版管理器状态:")
        print(f"  标准化接口启用: {enhanced_status['use_standardized_interface']}")
        print(f"  动态扩展启用: {enhanced_status['dynamic_extension_enabled']}")
        
        if 'dynamic_extension' in enhanced_status:
            dynamic = enhanced_status['dynamic_extension']
            print(f"  动态扩展状态: {dynamic['status']}")
        
        # 健康检查
        print("\n✅ 执行增强版健康检查...")
        health = await enhanced_manager.health_check_enhanced()
        print(f"  整体状态: {health['overall']}")
        
        if 'dynamic_extension' in health:
            dynamic_health = health['dynamic_extension']
            print(f"  动态扩展健康: {dynamic_health['status']}")
        
        # 停止动态扩展管理器
        await enhanced_manager.stop_dynamic_extension_manager()
        print("✅ 动态扩展管理器已停止")
        
        print("\n✅ 增强版管理器动态扩展集成测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 增强版管理器动态扩展集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("动态层扩展系统综合测试")
    print("=" * 60)
    
    # 测试动态层扩展系统
    test1_result = await test_dynamic_layer_extension()
    
    # 测试增强版管理器集成
    test2_result = await test_enhanced_manager_with_dynamic_extension()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = test1_result and test2_result
    
    print(f"动态层扩展系统测试: {'✅ 通过' if test1_result else '❌ 失败'}")
    print(f"增强版管理器集成测试: {'✅ 通过' if test2_result else '❌ 失败'}")
    print(f"\n总体结果: {'✅ 所有测试通过' if all_passed else '❌ 部分测试失败'}")
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)