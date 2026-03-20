#!/usr/bin/env python3
"""
直接测试工作流执行的脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_workflow_execution():
    """直接测试工作流执行"""
    print("=" * 60)
    print("🔍 工作流执行直接测试")
    print("=" * 60)

    try:
        # 1. 创建系统
        print("\n1. 创建UnifiedResearchSystem...")
        from src.unified_research_system import create_unified_research_system

        system = await create_unified_research_system()
        print("   ✅ 系统创建成功")

        # 2. 获取工作流
        print("\n2. 获取工作流对象...")
        if hasattr(system, '_unified_workflow') and system._unified_workflow:
            workflow_obj = system._unified_workflow
            if hasattr(workflow_obj, 'workflow') and workflow_obj.workflow:
                workflow = workflow_obj.workflow
                print(f"   ✅ 工作流对象获取成功: {type(workflow).__name__}")

                # 3. 准备测试数据
                print("\n3. 准备测试数据...")
                initial_state = {
                    "query": "测试查询：什么是人工智能？",
                    "context": {},
                    "route_path": "simple",
                    "complexity_score": 0.0,
                    "evidence": [],
                    "answer": None,
                    "confidence": 0.0,
                    "final_answer": None,
                    "knowledge": [],
                    "citations": [],
                    "task_complete": False,
                    "error": None,
                    "errors": [],
                    "execution_time": 0.0,
                    "node_execution_times": {},
                    "token_usage": {},
                    "api_calls": {},
                    "metadata": {},
                    "enhanced_context": {},
                    "generated_prompt": None,
                    "user_context": {},
                    "user_id": None,
                    "session_id": None,
                    "safety_check_passed": True,
                    "sensitive_topics": [],
                    "content_filter_applied": False,
                    "retry_count": 0,
                    "node_times": {},
                    "workflow_checkpoint_id": None
                }
                print(f"   ✅ 测试状态准备完成，包含 {len(initial_state)} 个字段")

                # 4. 测试astream_events
                print("\n4. 测试astream_events...")
                if hasattr(workflow, 'astream_events'):
                    print("   🎯 开始测试astream_events...")

                    event_count = 0
                    timeout_reached = False

                    async def timeout_check():
                        nonlocal timeout_reached
                        await asyncio.sleep(10.0)  # 10秒超时
                        timeout_reached = True
                        print("   ⏰ 10秒超时已到")

                    timeout_task = asyncio.create_task(timeout_check())

                    try:
                        async for event in workflow.astream_events(
                            initial_state,
                            config=None,
                            version="v2",
                            include_names=None,
                            include_types=["chain"]
                        ):
                            event_count += 1
                            event_name = event.get("event", "unknown")
                            event_data = event.get("data", {})

                            print(f"   📨 事件 {event_count}: {event_name}")
                            if isinstance(event_data, dict) and 'name' in event_data:
                                print(f"      节点: {event_data['name']}")

                            # 只测试前5个事件
                            if event_count >= 5:
                                print("   🛑 已收到5个事件，停止测试")
                                break

                            if timeout_reached:
                                break

                    except Exception as e:
                        print(f"   ❌ astream_events测试失败: {e}")

                    # 取消超时任务
                    if not timeout_task.done():
                        timeout_task.cancel()

                    print(f"   📊 astream_events测试结果: 收到 {event_count} 个事件")

                    if event_count == 0 and not timeout_reached:
                        print("   ❌ astream_events立即返回，没有产生任何事件")
                    elif event_count == 0 and timeout_reached:
                        print("   ❌ astream_events在10秒内没有产生任何事件")
                    else:
                        print("   ✅ astream_events工作正常")

                else:
                    print("   ❌ 工作流不支持astream_events")

                # 5. 测试astream（降级方案）
                if hasattr(workflow, 'astream'):
                    print("\n5. 测试astream（降级方案）...")
                    print("   🎯 开始测试astream...")

                    event_count = 0
                    timeout_reached = False

                    async def timeout_check():
                        nonlocal timeout_reached
                        await asyncio.sleep(10.0)
                        timeout_reached = True
                        print("   ⏰ 10秒超时已到")

                    timeout_task = asyncio.create_task(timeout_check())

                    try:
                        async for event in workflow.astream(initial_state, config=None):
                            event_count += 1
                            print(f"   📨 astream事件 {event_count}: {type(event)}")

                            if isinstance(event, dict):
                                node_names = list(event.keys())
                                print(f"      包含节点: {node_names[:3]}...")  # 只显示前3个

                            # 只测试前3个事件
                            if event_count >= 3:
                                print("   🛑 已收到3个astream事件，停止测试")
                                break

                            if timeout_reached:
                                break

                    except Exception as e:
                        print(f"   ❌ astream测试失败: {e}")

                    # 取消超时任务
                    if not timeout_task.done():
                        timeout_task.cancel()

                    print(f"   📊 astream测试结果: 收到 {event_count} 个事件")

                    if event_count == 0 and not timeout_reached:
                        print("   ❌ astream立即返回，没有产生任何事件")
                    elif event_count == 0 and timeout_reached:
                        print("   ❌ astream在10秒内没有产生任何事件")
                    else:
                        print("   ✅ astream工作正常")

            else:
                print("   ❌ workflow_obj没有workflow属性")
        else:
            print("   ❌ 系统没有_unified_workflow")

        await system.shutdown()

        print("\n" + "=" * 60)
        print("🎯 测试完成")
        print("💡 如果两个流方法都无法产生事件，说明工作流配置有问题")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_execution())
