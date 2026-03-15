"""
测试S1级高级Agent：多Agent协作和自主运行
"""

import asyncio
import time
import logging
import sys
import os

# 将项目根目录添加到PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.multi_agent_coordinator import MultiAgentCoordinator
from src.agents.autonomous_runner import AutonomousRunner
from src.agents.rag_agent import RAGExpert
from src.agents.reasoning_expert import ReasoningExpert
from src.agents.agent_coordinator import AgentCoordinator
from src.utils.logging_helper import get_module_logger, ModuleType
from src.utils.unified_centers import get_unified_intelligent_center, get_unified_config_center

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_multi_agent_coordination():
    """测试多Agent协作协调器"""
    print("🔬 测试多Agent协作协调器")
    print("=" * 50)

    # 初始化统一中心
    get_unified_intelligent_center()
    get_unified_config_center()

    # 创建协调器
    coordinator = MultiAgentCoordinator()

    # 注册测试Agent
    print("📝 注册测试Agent...")
    rag_expert = RAGExpert()
    reasoning_expert = ReasoningExpert()
    agent_coordinator = AgentCoordinator()

    coordinator.register_agent(
        rag_expert,
        capabilities={"retrieval", "generation", "analysis"},
        expertise_levels={"retrieval": 0.9, "generation": 0.8, "analysis": 0.7},
        max_concurrent=3
    )

    coordinator.register_agent(
        reasoning_expert,
        capabilities={"logic", "planning", "analysis"},
        expertise_levels={"logic": 0.9, "planning": 0.8, "analysis": 0.8},
        max_concurrent=2
    )

    coordinator.register_agent(
        agent_coordinator,
        capabilities={"coordination", "task_management", "resource_allocation"},
        expertise_levels={"coordination": 0.95, "task_management": 0.9, "resource_allocation": 0.85},
        max_concurrent=5
    )

    # 启动协调器
    await coordinator.start()

    # 提交协作任务
    print("📋 提交协作任务...")
    test_tasks = [
        {
            "description": "分析用户查询并生成智能回复",
            "context": {"query": "什么是人工智能？", "type": "analysis"}
        },
        {
            "description": "优化系统性能并制定改进计划",
            "context": {"focus": "performance", "timeframe": "short_term"}
        },
        {
            "description": "设计新的协作算法并评估可行性",
            "context": {"domain": "collaboration", "complexity": "high"}
        }
    ]

    task_ids = []
    for i, task_data in enumerate(test_tasks):
        print(f"  任务 {i+1}: {task_data['description'][:30]}...")
        task_id = await coordinator.submit_collaboration_task(
            task_data["description"],
            task_data["context"]
        )
        task_ids.append(task_id)

    # 等待任务执行
    print("⏳ 等待协作任务执行...")
    await asyncio.sleep(15)  # 给任务一些执行时间

    # 获取协作统计
    stats = coordinator.get_collaboration_stats()
    print("\n📊 协作统计:")
    print(f"  处理任务数: {stats['total_tasks_processed']}")
    print(f"  成功率: {stats['success_rate']:.1%}")
    print(f"  平均执行时间: {stats['average_task_duration']:.2f}秒")
    print(f"  活跃任务: {stats['active_tasks']}")
    print(f"  注册Agent数: {stats['registered_agents']}")
    print(f"  当前效率: {stats['current_efficiency']:.3f}")

    # 停止协调器
    await coordinator.stop()

    print("✅ 多Agent协作协调器测试完成\n")

async def test_autonomous_runner():
    """测试自主运行Agent"""
    print("🤖 测试自主运行Agent")
    print("=" * 50)

    # 初始化统一中心
    get_unified_intelligent_center()
    get_unified_config_center()

    # 创建自主运行Agent
    autonomous_runner = AutonomousRunner()

    # 设置多Agent协调器（可选）
    coordinator = MultiAgentCoordinator()
    autonomous_runner.set_multi_agent_coordinator(coordinator)

    # 启动自主运行Agent
    await autonomous_runner.start()

    print("🎯 生成自主目标...")

    # 生成不同的自主目标
    goal_types = ["performance_optimization", "learning_enhancement", "system_health_maintenance"]
    generated_goals = []

    for goal_type in goal_types:
        goal_id = await autonomous_runner.generate_autonomous_goal(
            goal_type,
            {"urgent": False, "time_limit_hours": 48}
        )
        if goal_id:
            generated_goals.append(goal_id)
            print(f"  ✅ 目标生成: {goal_id} ({goal_type})")

    # 等待自主目标执行
    print("⏳ 等待自主目标执行...")
    await asyncio.sleep(20)  # 给目标一些执行时间

    # 获取自主运行状态
    status = autonomous_runner.get_autonomous_status()
    print("\n📊 自主运行状态:")
    print(f"  活跃目标: {status['active_goals']}")
    print(f"  已完成目标: {status['completed_goals']}")
    print(f"  学习洞察: {status['learning_insights']}")
    print(f"  已应用洞察: {status['applied_insights']}")
    print(f"  进化动作: {status['evolutionary_actions']}")
    print(f"  自主决策: {status['autonomous_decisions']}")
    print(f"  系统效率: {status['system_efficiency']:.3f}")
    print(f"  总目标达成: {status['total_goals_achieved']}")

    # 手动触发进化
    print("🔬 手动触发系统进化...")
    evolution_result = await autonomous_runner.execute({"task_type": "evolution_trigger"})
    print(f"  进化结果: {evolution_result.data if evolution_result.success else evolution_result.error}")

    # 停止自主运行Agent
    await autonomous_runner.stop()

    print("✅ 自主运行Agent测试完成\n")

async def test_integrated_s1_system():
    """测试S1级集成系统"""
    print("🔗 测试S1级集成系统")
    print("=" * 50)

    # 初始化所有组件
    get_unified_intelligent_center()
    get_unified_config_center()

    # 创建多Agent协调器
    coordinator = MultiAgentCoordinator()

    # 注册Agent
    rag_expert = RAGExpert()
    reasoning_expert = ReasoningExpert()
    agent_coordinator = AgentCoordinator()

    coordinator.register_agent(rag_expert.agent_id, rag_expert, {"retrieval", "generation"}, {"retrieval": 0.9}, 3)
    coordinator.register_agent(reasoning_expert.agent_id, reasoning_expert, {"logic", "analysis"}, {"logic": 0.9}, 2)
    coordinator.register_agent(agent_coordinator.agent_id, agent_coordinator, {"coordination"}, {"coordination": 0.95}, 5)

    # 创建自主运行Agent并连接协调器
    autonomous_runner = AutonomousRunner()
    autonomous_runner.set_multi_agent_coordinator(coordinator)

    # 启动所有组件
    await coordinator.start()
    await autonomous_runner.start()

    print("🚀 启动集成测试...")

    # 测试端到端协作流程
    complex_task = {
        "description": "设计并实现一个智能问答系统，包含知识检索、推理分析和答案生成能力",
        "context": {
            "domain": "ai_system_design",
            "complexity": "advanced",
            "requirements": ["scalability", "accuracy", "reliability"],
            "timeframe": "2_weeks"
        }
    }

    print(f"📋 提交复杂协作任务: {complex_task['description'][:50]}...")

    # 通过自主运行Agent处理复杂任务
    autonomous_result = await autonomous_runner.execute({
        "task_type": "goal_generation",
        "goal_type": "capability_expansion",
        "context": complex_task
    })

    if autonomous_result.success:
        goal_id = autonomous_result.data.get("goal_id")
        print(f"  ✅ 自主目标生成: {goal_id}")

        # 等待目标执行
        await asyncio.sleep(10)

        # 获取最终状态
        final_status = autonomous_runner.get_autonomous_status()
        collab_stats = coordinator.get_collaboration_stats()

        print("\n🎯 集成测试结果:")
        print(f"  自主目标达成: {final_status['total_goals_achieved']}")
        print(f"  协作任务处理: {collab_stats['total_tasks_processed']}")
        print(f"  系统效率: {final_status['system_efficiency']:.3f}")
        print(f"  学习洞察发现: {final_status['learning_insights']}")

    # 停止所有组件
    await autonomous_runner.stop()
    await coordinator.stop()

    print("✅ S1级集成系统测试完成\n")

async def main():
    """主测试函数"""
    print("🧪 S1级高级Agent系统测试")
    print("=" * 60)

    start_time = time.time()

    try:
        # 测试多Agent协作
        await test_multi_agent_coordination()

        # 测试自主运行
        await test_autonomous_runner()

        # 测试集成系统
        await test_integrated_s1_system()

        total_time = time.time() - start_time
        print("🎉 所有S1级测试完成！")
        print(f"⏱️ 总测试时间: {total_time:.2f}秒")
        print("✅ L6多Agent协作和L7自主运行能力验证成功")

    except Exception as e:
        logger.error(f"❌ 测试过程中出现异常: {e}", exc_info=True)
        print("❌ 测试失败")

if __name__ == "__main__":
    asyncio.run(main())
