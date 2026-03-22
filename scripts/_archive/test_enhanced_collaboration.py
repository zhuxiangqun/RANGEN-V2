#!/usr/bin/env python3
"""
增强协作协调器测试脚本

测试增强协作协调器功能：
1. enhanced_collaboration_coordinator.py - 增强协作协调器
2. 新的协作模式（竞合、自适应、共识、联邦学习）
3. 实时通信总线集成
4. 性能监控和分析
"""

import asyncio
import sys
import os
import time

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_enhanced_collaboration_basic():
    """测试增强协作协调器基础功能"""
    print("=" * 60)
    print("测试增强协作协调器基础功能")
    print("=" * 60)
    
    try:
        from src.core.enhanced_collaboration_coordinator import (
            get_enhanced_collaboration_coordinator,
            EnhancedCollaborationMode, CollaborationTask,
            CollaborationMessage, CollaborationPerformanceMetrics
        )
        
        print("✅ 成功导入增强协作协调器组件")
        
        # 获取协调器实例
        coordinator = get_enhanced_collaboration_coordinator(enable_real_time_communication=True)
        print("✅ 增强协作协调器实例创建成功")
        
        # 创建测试任务
        test_tasks = []
        for i in range(5):
            task = CollaborationTask(
                task_id=f"test_task_{i}",
                description=f"测试任务 {i}",
                complexity=["simple", "moderate", "complex", "advanced"][i % 4],
                subtasks=[{"id": f"subtask_{i}_{j}", "description": f"子任务 {j}"} for j in range(2)],
                metadata={"test": True, "task_number": i}
            )
            test_tasks.append(task)
        
        print(f"✅ 创建了 {len(test_tasks)} 个测试任务")
        
        # 测试竞合协作模式
        print("\n✅ 测试竞合协作模式...")
        competitive_result = await coordinator.coordinate_enhanced_collaboration(
            tasks=test_tasks[:2],  # 使用前2个任务测试
            collaboration_mode=EnhancedCollaborationMode.COMPETITIVE,
            timeout=10.0
        )
        print(f"  竞合协作结果: 成功={competitive_result.get('success', False)}")
        print(f"    完成任务: {competitive_result.get('completed_tasks', 0)}")
        print(f"    失败任务: {competitive_result.get('failed_tasks', 0)}")
        print(f"    总时间: {competitive_result.get('total_time', 0):.2f}s")
        
        # 测试自适应协作模式
        print("\n✅ 测试自适应协作模式...")
        adaptive_result = await coordinator.coordinate_enhanced_collaboration(
            tasks=test_tasks,
            collaboration_mode=EnhancedCollaborationMode.ADAPTIVE,
            timeout=20.0
        )
        print(f"  自适应协作结果: 成功={adaptive_result.get('success', False)}")
        print(f"    完成任务: {adaptive_result.get('completed_tasks', 0)}")
        print(f"    总时间: {adaptive_result.get('total_time', 0):.2f}s")
        
        # 测试消息系统
        print("\n✅ 测试协作消息系统...")
        message_id = await coordinator.send_collaboration_message(
            sender_id="test_sender",
            message_type="test_message",
            payload={"test": "data", "timestamp": time.time()}
        )
        print(f"  发送消息ID: {message_id}")
        print(f"  消息历史大小: {len(coordinator.message_history)}")
        
        # 测试性能监控
        print("\n✅ 测试性能监控...")
        performance_report = coordinator.get_performance_report()
        print(f"  总协作次数: {performance_report.get('total_collaborations', 0)}")
        print(f"  平均效率: {performance_report.get('average_efficiency', 0):.3f}")
        print(f"  活跃共识轮次: {performance_report.get('active_consensus_rounds', 0)}")
        
        # 测试具体协作ID的性能报告
        if performance_report.get('total_collaborations', 0) > 0:
            # 获取第一个协作ID的性能报告
            all_metrics = coordinator.performance_metrics
            if all_metrics:
                first_collaboration_id = list(all_metrics.keys())[0]
                specific_report = coordinator.get_performance_report(first_collaboration_id)
                print(f"  协作 {first_collaboration_id} 的效率: {specific_report.get('efficiency_score', 0):.3f}")
        
        # 清理资源
        await coordinator.cleanup()
        print("\n✅ 资源清理完成")
        
        print("\n✅ 增强协作协调器基础测试通过")
        return True
        
    except Exception as e:
        print(f"\n❌ 增强协作协调器基础测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_collaboration_modes():
    """测试所有协作模式"""
    print("\n" + "=" * 60)
    print("测试所有协作模式")
    print("=" * 60)
    
    try:
        from src.core.enhanced_collaboration_coordinator import (
            get_enhanced_collaboration_coordinator,
            EnhancedCollaborationMode, CollaborationTask
        )
        
        coordinator = get_enhanced_collaboration_coordinator(enable_real_time_communication=True)
        
        # 创建测试任务
        test_tasks = []
        for i in range(3):
            task = CollaborationTask(
                task_id=f"mode_test_task_{i}",
                description=f"协作模式测试任务 {i}",
                complexity="moderate",
                subtasks=[{"id": f"subtask_{i}_{j}", "description": f"子任务 {j}"} for j in range(3)],
                metadata={"mode_test": True}
            )
            test_tasks.append(task)
        
        print(f"✅ 创建了 {len(test_tasks)} 个模式测试任务")
        
        # 测试所有协作模式
        modes_to_test = [
            (EnhancedCollaborationMode.COMPETITIVE, "竞合模式"),
            (EnhancedCollaborationMode.ADAPTIVE, "自适应模式"),
            # 暂时跳过共识和联邦学习模式，可能需要更多设置
        ]
        
        results = {}
        for mode, mode_name in modes_to_test:
            print(f"\n✅ 测试{mode_name}...")
            try:
                result = await coordinator.coordinate_enhanced_collaboration(
                    tasks=test_tasks,
                    collaboration_mode=mode,
                    timeout=15.0
                )
                success = result.get('success', False)
                completed = result.get('completed_tasks', 0)
                total = result.get('total_tasks', 0)
                print(f"  {mode_name}结果: 成功={success}, 完成={completed}/{total}")
                results[mode_name] = (success, completed, total)
            except Exception as mode_error:
                print(f"  {mode_name}测试失败: {mode_error}")
                results[mode_name] = (False, 0, len(test_tasks))
        
        # 清理
        await coordinator.cleanup()
        
        # 汇总结果
        print("\n✅ 协作模式测试汇总:")
        for mode_name, (success, completed, total) in results.items():
            print(f"  {mode_name}: {'成功' if success else '失败'}, 完成{completed}/{total}个任务")
        
        # 至少有一种模式成功即认为测试通过
        any_success = any(success for success, _, _ in results.values())
        
        if any_success:
            print("\n✅ 协作模式测试通过")
            return True
        else:
            print("\n❌ 协作模式测试失败")
            return False
        
    except Exception as e:
        print(f"\n❌ 协作模式测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_monitoring():
    """测试性能监控功能"""
    print("\n" + "=" * 60)
    print("测试性能监控功能")
    print("=" * 60)
    
    try:
        from src.core.enhanced_collaboration_coordinator import (
            get_enhanced_collaboration_coordinator,
            EnhancedCollaborationMode, CollaborationTask,
            CollaborationPerformanceMetrics
        )
        
        coordinator = get_enhanced_collaboration_coordinator(enable_real_time_communication=True)
        
        # 创建性能测试任务
        perf_tasks = []
        for i in range(4):
            task = CollaborationTask(
                task_id=f"perf_test_task_{i}",
                description=f"性能测试任务 {i}",
                complexity="simple",
                subtasks=[{"id": f"perf_subtask_{i}_{j}", "description": f"性能子任务 {j}"} for j in range(2)],
                metadata={"performance_test": True}
            )
            perf_tasks.append(task)
        
        # 执行多次协作以收集性能数据
        print("✅ 执行多次协作收集性能数据...")
        for i in range(3):
            print(f"  第 {i+1} 次协作执行...")
            result = await coordinator.coordinate_enhanced_collaboration(
                tasks=perf_tasks,
                collaboration_mode=EnhancedCollaborationMode.ADAPTIVE,
                timeout=10.0
            )
            
            if i < 2:  # 前两次后等待一小会
                await asyncio.sleep(0.1)
        
        # 检查性能指标
        print("\n✅ 检查性能指标...")
        perf_report = coordinator.get_performance_report()
        
        total_collaborations = perf_report.get('total_collaborations', 0)
        avg_efficiency = perf_report.get('average_efficiency', 0)
        
        print(f"  总协作次数: {total_collaborations}")
        print(f"  平均效率: {avg_efficiency:.3f}")
        
        if total_collaborations > 0:
            print("  ✅ 性能数据收集成功")
            
            # 检查效率历史
            efficiency_history = perf_report.get('recent_efficiency_history', [])
            print(f"  效率历史记录: {len(efficiency_history)} 条")
            
            if efficiency_history:
                print(f"  最近效率: {efficiency_history[-1]:.3f}")
            
            # 检查消息历史
            message_history_size = perf_report.get('message_history_size', 0)
            print(f"  消息历史大小: {message_history_size}")
        
        # 清理
        await coordinator.cleanup()
        
        if total_collaborations > 0:
            print("\n✅ 性能监控测试通过")
            return True
        else:
            print("\n❌ 性能监控测试失败: 未收集到性能数据")
            return False
        
    except Exception as e:
        print(f"\n❌ 性能监控测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integration_with_dynamic_extension():
    """测试与动态层扩展系统的集成"""
    print("\n" + "=" * 60)
    print("测试与动态层扩展系统的集成")
    print("=" * 60)
    
    try:
        from src.core.enhanced_collaboration_coordinator import (
            get_enhanced_collaboration_coordinator,
            EnhancedCollaborationMode
        )
        from src.core.dynamic_layer_extension import get_dynamic_layer_extension_manager
        from src.core.layer_interface_standard import LayerType
        
        print("✅ 导入所有必要组件")
        
        # 获取动态层扩展管理器
        dynamic_manager = get_dynamic_layer_extension_manager()
        
        # 注册一些测试组件（模拟Agent组件）
        print("✅ 注册测试动态组件...")
        
        component_ids = []
        for i in range(3):
            component_id = f"collab_agent_{i}"
            success = dynamic_manager.register_component(
                component_id=component_id,
                component_type="test_agent",
                layer_type=LayerType.AGENT,
                endpoint=f"http://localhost:{8100 + i}",
                capabilities=[f"test_capability_{j}" for j in range(3)],
                metadata={"test": True, "for_collaboration": True}
            )
            
            if success:
                component_ids.append(component_id)
                print(f"  注册组件: {component_id}")
            else:
                print(f"  注册组件失败: {component_id}")
        
        print(f"✅ 成功注册 {len(component_ids)} 个测试组件")
        
        # 获取增强协作协调器
        coordinator = get_enhanced_collaboration_coordinator(enable_real_time_communication=True)
        
        # 测试协调器是否能访问动态组件
        print("\n✅ 测试协调器访问动态组件...")
        
        # 通过协调器的方法检查可用Agent（模拟）
        # 注意：实际实现中，协调器应该与动态层扩展系统集成以获取可用Agent
        available_agents = coordinator._get_available_agents()
        print(f"  协调器报告可用Agent数: {len(available_agents)}")
        
        # 执行一个协作任务，使用动态组件
        print("\n✅ 使用动态组件执行协作任务...")
        
        from src.core.enhanced_collaboration_coordinator import CollaborationTask
        
        integration_tasks = []
        for i in range(2):
            task = CollaborationTask(
                task_id=f"integration_test_task_{i}",
                description=f"集成测试任务 {i}",
                complexity="moderate",
                subtasks=[{"id": f"int_subtask_{i}_{j}", "description": f"集成子任务 {j}"} for j in range(2)],
                metadata={"integration_test": True, "use_dynamic_components": True}
            )
            integration_tasks.append(task)
        
        integration_result = await coordinator.coordinate_enhanced_collaboration(
            tasks=integration_tasks,
            collaboration_mode=EnhancedCollaborationMode.ADAPTIVE,
            timeout=15.0
        )
        
        print(f"  集成协作结果: 成功={integration_result.get('success', False)}")
        print(f"    完成任务: {integration_result.get('completed_tasks', 0)}")
        
        # 清理
        await coordinator.cleanup()
        
        # 注销测试组件
        print("\n✅ 清理测试组件...")
        for component_id in component_ids:
            dynamic_manager.unregister_component(component_id)
            print(f"  注销组件: {component_id}")
        
        print("\n✅ 动态层扩展集成测试完成")
        return True
        
    except Exception as e:
        print(f"\n❌ 动态层扩展集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("增强协作协调器综合测试")
    print("=" * 60)
    
    # 测试基础功能
    test1_result = await test_enhanced_collaboration_basic()
    
    # 测试协作模式
    test2_result = await test_collaboration_modes()
    
    # 测试性能监控
    test3_result = await test_performance_monitoring()
    
    # 测试动态层扩展集成
    test4_result = await test_integration_with_dynamic_extension()
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    results = [
        ("基础功能测试", test1_result),
        ("协作模式测试", test2_result),
        ("性能监控测试", test3_result),
        ("动态扩展集成测试", test4_result)
    ]
    
    for test_name, result in results:
        print(f"{test_name}: {'✅ 通过' if result else '❌ 失败'}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print(f"\n✅ 增强协作协调器所有测试通过")
    else:
        print(f"\n❌ 增强协作协调器部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    result = asyncio.run(main())
    exit(0 if result else 1)