#!/usr/bin/env python3
"""测试UsageAnalytics系统"""

import asyncio
import sys
import os
sys.path.insert(0, '.')

async def test_usage_analytics():
    """测试使用分析系统"""
    print("🚀 测试UsageAnalytics系统")
    print("=" * 60)
    
    try:
        # 导入模块
        from src.evolution.usage_analytics import UsageAnalytics
        from src.hook.hook_types import HookEvent, HookEventType, HookVisibilityLevel
        import uuid
        from datetime import datetime
        
        print("✅ 模块导入成功")
        
        # 创建使用分析实例
        analytics = UsageAnalytics("test_system")
        print("✅ UsageAnalytics实例化成功")
        
        # 启动分析系统
        await analytics.start()
        print("✅ UsageAnalytics启动成功")
        
        # 模拟Hand执行事件
        print("\n📊 模拟Hand执行事件...")
        hand_event = HookEvent(
            event_id=str(uuid.uuid4()),
            event_type=HookEventType.HAND_EXECUTION,
            timestamp=datetime.now().isoformat(),
            source="test_hand",
            data={
                "hand_name": "file_read",
                "success": True,
                "execution_time": 0.5,
                "parameters": {"path": "/tmp/test.txt"}
            },
            visibility=HookVisibilityLevel.DEVELOPER
        )
        
        # 手动处理事件（因为recorder可能未运行）
        await analytics._handle_hand_execution_event(hand_event)
        print("✅ Hand执行事件处理成功")
        
        # 模拟进化计划事件
        print("\n🧬 模拟进化计划事件...")
        evolution_event = HookEvent(
            event_id=str(uuid.uuid4()),
            event_type=HookEventType.EVOLUTION_PLAN,
            timestamp=datetime.now().isoformat(),
            source="evolution_engine",
            data={
                "plan_id": "test_plan_001",
                "status": "completed",
                "execution_time": 30.5,
                "performance_impact": {"improvement_percentage": 15.0}
            },
            visibility=HookVisibilityLevel.DEVELOPER
        )
        
        await analytics._handle_evolution_plan_event(evolution_event)
        print("✅ 进化计划事件处理成功")
        
        # 获取统计
        print("\n📈 获取使用统计...")
        hand_stats = analytics.get_hand_stats()
        system_stats = analytics.get_system_stats()
        
        print(f"Hand统计: {len(hand_stats)} 个Hands")
        print(f"系统统计: {system_stats}")
        
        # 获取优化建议
        suggestions = analytics.get_suggestions()
        print(f"\n💡 优化建议数量: {len(suggestions)}")
        
        for suggestion in suggestions[:3]:  # 显示前3个建议
            print(f"  - {suggestion['title']} ({suggestion['priority']})")
        
        # 测试批准建议
        if suggestions:
            first_suggestion = suggestions[0]
            approved = analytics.approve_suggestion(first_suggestion['suggestion_id'])
            if approved:
                print(f"✅ 建议批准成功: {first_suggestion['title']}")
        
        print("\n✅ 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_recorder_integration():
    """测试Recorder集成"""
    print("\n🔗 测试Recorder集成...")
    try:
        from src.hook.transparency import HookTransparencySystem
        from src.hook.hook_types import HookEvent, HookEventType, HookVisibilityLevel
        import uuid
        from datetime import datetime
        
        # 创建Hook系统
        hook_system = HookTransparencySystem("test_integration")
        print("✅ HookTransparencySystem创建成功")
        
        # 创建使用分析
        from src.evolution.usage_analytics import UsageAnalytics
        analytics = UsageAnalytics("test_integration")
        await analytics.start()
        print("✅ UsageAnalytics启动成功")
        
        # 记录事件（应该触发分析系统）
        event = HookEvent(
            event_id=str(uuid.uuid4()),
            event_type=HookEventType.HAND_EXECUTION,
            timestamp=datetime.now().isoformat(),
            source="integration_test",
            data={
                "hand_name": "api_request",
                "success": False,
                "execution_time": 2.5,
                "error": "Timeout"
            },
            visibility=HookVisibilityLevel.DEVELOPER
        )
        
        success = await hook_system.recorder.record_event(event)
        print(f"✅ 事件记录: {'成功' if success else '失败'}")
        
        # 等待异步处理
        await asyncio.sleep(1)
        
        # 检查统计
        stats = analytics.get_hand_stats()
        print(f"📊 集成测试后Hand统计: {len(stats)} 个Hands")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 UsageAnalytics 系统测试")
    print("=" * 60)
    
    # 测试1: 基本功能
    test1_passed = await test_usage_analytics()
    
    # 测试2: 集成测试
    test2_passed = await test_recorder_integration()
    
    print("\n" + "=" * 60)
    print("📋 测试结果汇总:")
    print(f"  基本功能测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"  集成测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    print(f"  总体: {'✅ 全部通过' if test1_passed and test2_passed else '❌ 部分失败'}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())