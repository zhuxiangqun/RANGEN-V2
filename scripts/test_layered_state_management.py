#!/usr/bin/env python3
"""
测试分层状态管理系统

验证P1阶段状态管理重构的完整实现：
1. 分层状态结构设计
2. 状态迁移和向后兼容
3. 状态操作和序列化
4. 性能优化
"""

import asyncio
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.layered_state_management import (
    BusinessState, CollaborationState, SystemState, UnifiedState,
    AgentState, StateMigrationManager, get_state_manager
)


async def test_business_state():
    """测试业务状态"""
    print("🧪 测试业务状态")
    print("-" * 30)

    # 创建业务状态
    business = BusinessState(
        query="What is machine learning?",
        context={"user_id": "user123"},
        route_path="complex",
        complexity_score=0.8
    )

    # 测试状态操作
    business.intermediate_steps.append({"step": "route_query", "result": "complex"})
    business.result = {"answer": "Machine learning is...", "confidence": 0.85}
    business.execution_time = 1.5
    business.update_timestamp()

    # 验证状态
    assert business.query == "What is machine learning?"
    assert business.route_path == "complex"
    assert business.complexity_score == 0.8
    assert len(business.intermediate_steps) == 1
    assert business.result["answer"] == "Machine learning is..."
    assert business.execution_time == 1.5

    # 测试序列化
    business_dict = business.to_dict()
    assert "query" in business_dict
    assert "execution_time" in business_dict

    # 测试反序列化
    business_restored = BusinessState.from_dict(business_dict)
    assert business_restored.query == business.query
    assert business_restored.route_path == business.route_path

    print("✅ 业务状态测试通过")


async def test_collaboration_state():
    """测试协作状态"""
    print("\n🧪 测试协作状态")
    print("-" * 30)

    # 创建协作状态
    collaboration = CollaborationState(
        session_id="session_001",
        collaboration_mode="multi_agent",
        coordination_strategy="sequential"
    )

    # 添加智能体
    agent1 = AgentState(
        agent_id="agent_knowledge",
        role="knowledge_retrieval",
        capabilities=["search", "retrieve"],
        status="active"
    )

    agent2 = AgentState(
        agent_id="agent_reasoning",
        role="reasoning",
        capabilities=["analyze", "reason"],
        status="active"
    )

    collaboration.add_agent(agent1)
    collaboration.add_agent(agent2)

    # 分配任务
    collaboration.assign_task("task_001", "agent_knowledge")
    collaboration.assign_task("task_002", "agent_reasoning")

    # 验证协作状态
    assert len(collaboration.participants) == 2
    assert len(collaboration.active_participants) == 2
    assert collaboration.collaboration_mode == "multi_agent"
    assert "agent_knowledge" in collaboration.task_assignments["task_001"]
    assert collaboration.get_agent_tasks("agent_knowledge") == ["task_001"]

    # 测试初始状态冲突（主要是能力不匹配）
    initial_conflicts = collaboration.detect_conflicts()
    print(f"初始冲突数量: {len(initial_conflicts)}")
    for i, c in enumerate(initial_conflicts):
        print(f"  冲突{i+1}: {c['conflict_type']} - {c.get('description', '')}")

    # 测试重复分配冲突 - 同一个任务分配给多个智能体
    collaboration.assign_task("task_001", "agent_reasoning")  # 重复分配task_001
    conflicts_after = collaboration.detect_conflicts()
    print(f"重复分配后冲突数量: {len(conflicts_after)}")

    duplicate_conflicts = [c for c in conflicts_after if c["conflict_type"] == "duplicate_assignment"]
    assert len(duplicate_conflicts) > 0, "应该检测到重复分配冲突"
    assert duplicate_conflicts[0]["conflict_type"] == "duplicate_assignment"
    print("✅ 检测到重复分配冲突")

    # 测试序列化
    collab_dict = collaboration.to_dict()
    assert "agent_states" in collab_dict
    assert "task_assignments" in collab_dict

    # 测试反序列化
    collab_restored = CollaborationState.from_dict(collab_dict)
    assert len(collab_restored.participants) == 2
    assert collab_restored.collaboration_mode == "multi_agent"

    print("✅ 协作状态测试通过")


async def test_system_state():
    """测试系统状态"""
    print("\n🧪 测试系统状态")
    print("-" * 30)

    # 创建系统状态
    system = SystemState()

    # 添加执行反馈
    system.add_execution_feedback({
        "query": "test query",
        "success": True,
        "execution_time": 1.2
    })

    # 添加性能反馈
    system.add_performance_feedback({
        "node_execution_times": {"node1": 0.5, "node2": 0.7},
        "memory_usage": 150 * 1024 * 1024  # 150MB
    })

    # 更新配置
    system.update_config({"timeout": 30, "max_retries": 3}, "performance_optimization")

    # 添加学习洞察
    system.add_learning_insight({
        "type": "performance_pattern",
        "description": "Slow execution detected",
        "recommendation": "Increase timeout"
    })

    # 验证系统状态
    assert len(system.execution_feedback) == 1
    assert len(system.performance_feedback) == 1
    assert system.current_config["timeout"] == 30
    assert len(system.config_history) == 1
    assert len(system.learning_insights) == 1

    # 测试序列化
    system_dict = system.to_dict()
    assert "current_config" in system_dict
    assert "execution_feedback" in system_dict

    # 测试反序列化
    system_restored = SystemState.from_dict(system_dict)
    assert system_restored.current_config["timeout"] == 30
    assert len(system_restored.execution_feedback) == 1

    print("✅ 系统状态测试通过")


async def test_unified_state():
    """测试统一状态容器"""
    print("\n🧪 测试统一状态容器")
    print("-" * 30)

    # 创建各层状态
    business = BusinessState(
        query="How does AI work?",
        route_path="complex",
        complexity_score=0.9
    )

    collaboration = CollaborationState(collaboration_mode="multi_agent")
    agent = AgentState("agent_001", "knowledge_agent", ["search"])
    collaboration.add_agent(agent)

    system = SystemState()
    system.update_config({"cache_enabled": True})

    # 创建统一状态
    unified = UnifiedState(
        business=business,
        collaboration=collaboration,
        system=system
    )

    # 验证统一状态
    assert unified.business.query == "How does AI work?"
    assert unified.collaboration.collaboration_mode == "multi_agent"
    assert unified.system.current_config["cache_enabled"] == True
    assert unified.version == "1.0"

    # 测试序列化
    unified_dict = unified.to_dict()
    assert "business" in unified_dict
    assert "collaboration" in unified_dict
    assert "system" in unified_dict

    # 测试反序列化
    unified_restored = UnifiedState.from_dict(unified_dict)
    assert unified_restored.business.query == unified.business.query
    assert unified_restored.collaboration.collaboration_mode == unified.collaboration.collaboration_mode

    # 测试LangGraph兼容性
    langgraph_state = unified.to_langgraph_state()
    assert "query" in langgraph_state
    assert "agent_states" in langgraph_state
    assert "config_optimization" in langgraph_state

    # 测试从LangGraph状态迁移
    unified_from_langgraph = UnifiedState.from_langgraph_state(langgraph_state)
    assert unified_from_langgraph.business.query == unified.business.query

    print("✅ 统一状态容器测试通过")


async def test_state_migration():
    """测试状态迁移"""
    print("\n🧪 测试状态迁移")
    print("-" * 30)

    migration_manager = get_state_manager()

    # 创建遗留状态（模拟旧的ResearchSystemState）
    legacy_state = {
        "query": "What is Python?",
        "context": {"user": "test_user"},
        "route_path": "simple",
        "complexity_score": 0.3,
        "result": {"answer": "Python is a programming language"},
        "agent_states": {
            "agent_001": {
                "agent_id": "agent_001",
                "role": "test_agent",
                "capabilities": ["test"],
                "status": "active"
            }
        },
        "collaboration_context": {"mode": "single"},
        "config_optimization": {"timeout": 30},
        "learning_system": {"patterns": {}}
    }

    # 测试迁移到分层状态
    unified_state = migration_manager.migrate_legacy_state(legacy_state)
    assert unified_state.business.query == "What is Python?"
    assert unified_state.business.route_path == "simple"
    assert unified_state.collaboration.agent_states["agent_001"].role == "test_agent"
    assert unified_state.system.current_config == {"timeout": 30}

    # 测试向后兼容
    backward_compatible = migration_manager.create_backward_compatible_state(unified_state)
    assert "query" in backward_compatible
    assert "agent_states" in backward_compatible
    assert "config_optimization" in backward_compatible

    # 测试状态完整性验证
    unified_integrity = migration_manager.validate_state_integrity(unified_state)
    legacy_integrity = migration_manager.validate_state_integrity(legacy_state)

    if not unified_integrity:
        print(f"⚠️ 分层状态完整性验证失败")
        print(f"  查询: {unified_state.business.query}")
        if unified_state.collaboration:
            print(f"  协作状态存在: {len(unified_state.collaboration.agent_states)} 个智能体")
            for aid, astate in unified_state.collaboration.agent_states.items():
                in_participants = aid in unified_state.collaboration.participants
                print(f"    智能体 {aid}: in_participants={in_participants}")

    assert unified_integrity, "分层状态完整性验证失败"
    assert legacy_integrity, "遗留状态完整性验证失败"

    # 测试状态大小优化
    # 添加一些旧数据
    for i in range(60):
        unified_state.system.add_learning_insight({"test": f"insight_{i}"})
        unified_state.system.add_execution_feedback({"test": f"feedback_{i}"})

    # 优化前
    insights_before = len(unified_state.system.learning_insights)
    feedback_before = len(unified_state.system.execution_feedback)

    # 优化后
    unified_state = migration_manager.optimize_state_size(unified_state)
    insights_after = len(unified_state.system.learning_insights)
    feedback_after = len(unified_state.system.execution_feedback)

    assert insights_after <= 50  # 应该被限制
    assert feedback_after <= 50  # 应该被限制

    print("✅ 状态迁移测试通过")


async def test_performance_comparison():
    """测试性能对比"""
    print("\n📊 性能对比测试")
    print("-" * 30)

    # 创建大规模状态进行性能测试
    large_unified_state = UnifiedState(
        business=BusinessState(query="Large test query"),
        collaboration=CollaborationState(),
        system=SystemState()
    )

    # 添加大量数据
    for i in range(100):
        agent = AgentState(f"agent_{i}", f"role_{i}", ["cap1", "cap2"])
        large_unified_state.collaboration.add_agent(agent)
        large_unified_state.system.add_execution_feedback({"test": f"feedback_{i}"})
        large_unified_state.system.add_learning_insight({"test": f"insight_{i}"})

    # 测试序列化性能
    start_time = time.time()
    serialized = large_unified_state.to_dict()
    serialize_time = time.time() - start_time

    # 测试反序列化性能
    start_time = time.time()
    deserialized = UnifiedState.from_dict(serialized)
    deserialize_time = time.time() - start_time

    # 测试LangGraph转换性能
    start_time = time.time()
    langgraph_format = large_unified_state.to_langgraph_state()
    conversion_time = time.time() - start_time

    print(".4f")
    print(".4f")
    print(".4f")
    print(f"序列化数据大小: {len(str(serialized))} 字符")

    # 验证转换结果
    assert len(deserialized.collaboration.agent_states) == 100
    assert len(langgraph_format["agent_states"]) == 100

    # 性能基准
    assert serialize_time < 1.0, f"序列化过慢: {serialize_time}s"
    assert deserialize_time < 1.0, f"反序列化过慢: {deserialize_time}s"
    assert conversion_time < 0.5, f"转换过慢: {conversion_time}s"

    print("✅ 性能对比测试通过")


async def test_integration_with_workflows():
    """测试与工作流的集成"""
    print("\n🔗 测试与工作流集成")
    print("-" * 30)

    from src.core.simplified_business_workflow import SimplifiedBusinessWorkflow

    # 创建工作流
    workflow = SimplifiedBusinessWorkflow()

    # 创建分层状态
    unified_state = UnifiedState(
        business=BusinessState(
            query="Integration test query",
            context={"test": True}
        )
    )

    # 执行工作流
    result = await workflow.execute(unified_state.business.query, unified_state.business.context)

    # 验证结果
    assert result["route_path"] in ["simple", "medium", "complex"]
    assert "result" in result
    assert "answer" in result["result"]

    print("✅ 工作流集成测试通过")


async def main():
    """主测试函数"""
    print("🚀 开始分层状态管理系统测试")
    print("=" * 60)

    try:
        await test_business_state()
        await test_collaboration_state()
        await test_system_state()
        await test_unified_state()
        await test_state_migration()
        await test_performance_comparison()
        await test_integration_with_workflows()

        print("\n" + "=" * 60)
        print("🎉 分层状态管理系统测试完成！")
        print("✅ 所有测试通过")
        print("✅ 状态分层设计成功")
        print("✅ 状态迁移和向后兼容实现")
        print("✅ 性能优化达成")
        print("🏆 P1阶段状态管理重构完成！")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
