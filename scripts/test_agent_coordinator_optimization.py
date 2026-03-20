#!/usr/bin/env python3
"""
AgentCoordinator优化效果测试脚本

测试内容：
1. 智能任务分配算法
2. 负载均衡机制
3. 冲突检测与解决
"""

import asyncio
import time
import logging
from src.agents.agent_coordinator import AgentCoordinator, Task, TaskPriority, AgentStatus

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_agent_coordinator():
    """测试AgentCoordinator功能"""
    print("=" * 60)
    print("🎯 AgentCoordinator智能协调测试")
    print("=" * 60)

    # 初始化协调器
    coordinator = AgentCoordinator()

    # 注册测试Agent
    print("\n📝 注册测试Agent...")

    # Agent 1: RAG专家
    await coordinator.execute({
        "action": "register_agent",
        "agent_id": "rag_expert",
        "capabilities": ["retrieval", "generation", "analysis"],
        "specialization_scores": {"knowledge": 0.9, "reasoning": 0.7}
    })

    # Agent 2: 推理专家
    await coordinator.execute({
        "action": "register_agent",
        "agent_id": "reasoning_expert",
        "capabilities": ["logic", "planning", "analysis"],
        "specialization_scores": {"reasoning": 0.95, "logic": 0.9}
    })

    # Agent 3: 工具专家
    await coordinator.execute({
        "action": "register_agent",
        "agent_id": "tool_expert",
        "capabilities": ["tool_use", "api_call", "computation"],
        "specialization_scores": {"tool": 0.85, "computation": 0.8}
    })

    print("✅ 已注册3个测试Agent")

    # 提交测试任务
    print("\n📋 提交测试任务...")

    tasks_data = [
        {
            "id": "task_1",
            "description": "分析用户查询并提供知识检索",
            "requirements": {"capabilities": ["retrieval", "analysis"], "domain": "knowledge"},
            "priority": "HIGH",
            "estimated_complexity": 2.0
        },
        {
            "id": "task_2",
            "description": "执行复杂逻辑推理",
            "requirements": {"capabilities": ["logic", "planning"], "domain": "reasoning"},
            "priority": "NORMAL",
            "estimated_complexity": 3.0,
            "dependencies": {"task_1"}  # 依赖task_1
        },
        {
            "id": "task_3",
            "description": "调用外部工具获取数据",
            "requirements": {"capabilities": ["tool_use", "api_call"], "domain": "tool"},
            "priority": "LOW",
            "estimated_complexity": 1.5
        },
        {
            "id": "task_4",
            "description": "生成综合分析报告",
            "requirements": {"capabilities": ["analysis", "generation"], "domain": "knowledge"},
            "priority": "HIGH",
            "estimated_complexity": 2.5,
            "dependencies": {"task_2", "task_3"}  # 依赖task_2和task_3
        }
    ]

    submitted_tasks = []
    for task_data in tasks_data:
        # 转换枚举
        task_data_copy = task_data.copy()
        task_data_copy["priority"] = TaskPriority[task_data["priority"]]
        task_data_copy["dependencies"] = set(task_data.get("dependencies", []))

        result = await coordinator.execute({
            "action": "submit_task",
            "task": task_data_copy
        })

        if result.success:
            task_id = result.data["task_id"]
            submitted_tasks.append(task_id)
            print(f"✅ 任务已提交: {task_id} - {task_data['description'][:30]}...")
        else:
            print(f"❌ 任务提交失败: {task_data['id']} - {result.error}")

    # 等待任务分配和执行
    print("\n⏳ 等待任务分配和执行...")
    await asyncio.sleep(2)

    # 获取统计信息
    stats_result = await coordinator.execute({"action": "get_stats"})
    if stats_result.success:
        stats = stats_result.data
        print("\n📊 当前统计:")
        print(f"   活跃Agent: {stats['active_agents']}")
        print(f"   待处理任务: {stats['pending_tasks']}")
        print(f"   平均负载: {stats['current_load_avg']:.2f}")
        print(f"   已处理任务: {stats['tasks_processed']}")
        print(f"   负载均衡操作: {stats['load_balance_operations']}")
        print(f"   解决冲突: {stats['conflicts_resolved']}")

    # 模拟任务完成
    print("\n🎯 模拟任务完成...")
    for task_id in submitted_tasks:
        # 随机成功/失败
        success = time.time() % 2 > 0.3  # 70%成功率
        coordinator.mark_task_completed(task_id, success)
        print(f"✅ 任务完成: {task_id} ({'成功' if success else '失败'})")

        # 小延迟模拟现实情况
        await asyncio.sleep(0.1)

    # 最终统计
    print("\n📈 最终统计:")
    final_stats = await coordinator.execute({"action": "get_stats"})
    if final_stats.success:
        stats = final_stats.data
        print(f"   总处理任务: {stats['tasks_processed'] + stats['tasks_failed']}")
        print(f"   成功率: {(stats['tasks_processed'] / (stats['tasks_processed'] + stats['tasks_failed']) * 100):.1f}%" if (stats['tasks_processed'] + stats['tasks_failed']) > 0 else '0%')
        print(f"   负载均衡操作: {stats['load_balance_operations']}")
        print(f"   解决冲突: {stats['conflicts_resolved']}")

    # 关闭协调器
    coordinator.shutdown()

    print("\n✅ AgentCoordinator测试完成！")

if __name__ == "__main__":
    asyncio.run(test_agent_coordinator())
