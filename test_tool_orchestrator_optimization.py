#!/usr/bin/env python3
"""
ToolOrchestrator优化效果测试脚本

测试内容：
1. 智能工具选择算法
2. 工具链编排执行
3. 提示词优化管理
4. 工具性能监控
"""

import asyncio
import time
import logging
from src.agents.tool_orchestrator import ToolOrchestrator, ToolCategory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_tool_orchestrator():
    """测试ToolOrchestrator功能"""
    print("=" * 60)
    print("🔧 ToolOrchestrator智能工具编排测试")
    print("=" * 60)

    # 初始化工具编排器
    orchestrator = ToolOrchestrator()

    # 注册测试工具
    print("\n📝 注册测试工具...")
    test_tools = [
        {
            "name": "knowledge_retrieval_tool",
            "category": ToolCategory.KNOWLEDGE_RETRIEVAL,
            "capabilities": ["search", "retrieve", "query"],
            "metadata": {"success_rate": 0.9, "avg_execution_time": 2.0}
        },
        {
            "name": "calculator_tool",
            "category": ToolCategory.COMPUTATION,
            "capabilities": ["calculate", "math", "compute"],
            "metadata": {"success_rate": 0.95, "avg_execution_time": 1.0}
        },
        {
            "name": "search_tool",
            "category": ToolCategory.SEARCH,
            "capabilities": ["web_search", "find", "lookup"],
            "metadata": {"success_rate": 0.85, "avg_execution_time": 3.0}
        },
        {
            "name": "analysis_tool",
            "category": ToolCategory.ANALYSIS,
            "capabilities": ["analyze", "summarize", "extract"],
            "metadata": {"success_rate": 0.8, "avg_execution_time": 4.0}
        }
    ]

    for tool_data in test_tools:
        await orchestrator.register_tool(
            tool_data["name"],
            tool_data["category"],
            tool_data["capabilities"],
            tool_data["metadata"]
        )

    # 测试智能工具选择
    print("\n🎯 测试智能工具选择...")
    test_scenarios = [
        {
            "task": "计算复杂的数学表达式",
            "capabilities": ["calculate", "math"],
            "expected_tool": "calculator_tool"
        },
        {
            "task": "从知识库中检索相关信息",
            "capabilities": ["search", "retrieve"],
            "expected_tool": "knowledge_retrieval_tool"
        },
        {
            "task": "在网络上搜索最新信息",
            "capabilities": ["web_search", "find"],
            "expected_tool": "search_tool"
        },
        {
            "task": "分析和总结文档内容",
            "capabilities": ["analyze", "summarize"],
            "expected_tool": "analysis_tool"
        }
    ]

    selection_results = []
    for scenario in test_scenarios:
        print(f"\n   任务: '{scenario['task']}'")

        start_time = time.time()
        result = await orchestrator.execute({
            "action": "select_tool",
            "task_description": scenario["task"],
            "required_capabilities": scenario["capabilities"]
        })
        execution_time = time.time() - start_time

        if result.success and result.data.get("selected_tool"):
            selected_tool = result.data["selected_tool"]
            expected_tool = scenario["expected_tool"]
            is_correct = selected_tool == expected_tool

            print(f"   ✅ 选择工具: {selected_tool} (期望: {expected_tool})")
            print(f"   🎯 选择正确: {'是' if is_correct else '否'}")
            print(".3f")

            selection_results.append({
                'task': scenario['task'],
                'selected': selected_tool,
                'expected': expected_tool,
                'correct': is_correct,
                'time': execution_time
            })
        else:
            print(f"   ❌ 工具选择失败: {result.error}")
            selection_results.append({
                'task': scenario['task'],
                'selected': None,
                'expected': scenario['expected_tool'],
                'correct': False,
                'time': execution_time
            })

    # 创建测试工具链
    print("\n🔗 创建测试工具链...")
    chain_steps = [
        {
            "tool_name": "knowledge_retrieval_tool",
            "parameters": {"query": "Python programming"},
            "execution_mode": "sequential",
            "max_retries": 2,
            "timeout_seconds": 30
        },
        {
            "tool_name": "analysis_tool",
            "parameters": {"action": "summarize"},
            "execution_mode": "sequential",
            "condition": "has_retrieved_data",
            "max_retries": 1,
            "timeout_seconds": 20
        }
    ]

    result = await orchestrator.execute({
        "action": "create_chain",
        "chain_name": "知识检索与分析链",
        "description": "先检索知识，然后进行分析总结",
        "steps": chain_steps
    })

    if result.success:
        chain_id = result.data["chain_id"]
        print(f"✅ 工具链已创建: {chain_id}")

        # 执行工具链
        print("\n▶️ 执行工具链...")
        execution_result = await orchestrator.execute({
            "action": "execute_chain",
            "chain_id": chain_id,
            "execution_context": {"has_retrieved_data": True}
        })

        if execution_result.success:
            exec_data = execution_result.data
            print(f"   ✅ 执行成功: {exec_data['successful_steps']}/{exec_data['total_steps']} 步骤")
            print(f"   🎯 成功率: {exec_data['success_rate']:.2f}")
            print(f"   ⏱️ 总耗时: {exec_data['total_execution_time']:.2f}秒")
        else:
            print(f"   ❌ 执行失败: {execution_result.error}")

    # 测试提示词优化
    print("\n💬 测试提示词优化...")
    performance_history = [
        {"success": True, "execution_time": 2.1, "quality_score": 0.9},
        {"success": False, "error": "timeout", "execution_time": 35.0, "quality_score": 0.3},
        {"success": True, "execution_time": 1.8, "quality_score": 0.85}
    ]

    result = await orchestrator.execute({
        "action": "optimize_prompt",
        "tool_name": "knowledge_retrieval_tool",
        "task_description": "检索Python相关知识",
        "performance_history": performance_history
    })

    if result.success and result.data.get("optimized_prompt"):
        optimized_prompt = result.data["optimized_prompt"]
        print("✅ 提示词已优化:")
        print(f"   {optimized_prompt}")
    else:
        print(f"   ❌ 提示词优化失败: {result.error}")

    # 获取统计信息
    print("\n📊 工具编排统计:")
    stats_result = await orchestrator.execute({"action": "stats"})

    if stats_result.success:
        stats = stats_result.data
        print(f"   注册工具数: {stats['total_tools']}")
        print(f"   工具链数: {stats['total_chains']}")
        print(f"   缓存大小: {stats['cache_size']}")
        print(f"   执行历史数: {stats['execution_history_size']}")
        print(f"   缓存命中率: {stats['cache_hit_rate']:.2f}")
        # 工具性能
        if 'tool_performance' in stats:
            print("   工具性能:")
            for tool_name, perf in stats['tool_performance'].items():
                print(f"     - {tool_name}: 成功率={perf['success_rate']:.2f}, 平均时间={perf['avg_execution_time']:.2f}秒")

    # 计算工具选择准确率
    if selection_results:
        correct_selections = sum(1 for r in selection_results if r['correct'])
        accuracy = correct_selections / len(selection_results) * 100
        avg_selection_time = sum(r['time'] for r in selection_results) / len(selection_results)

        print("\n🎯 工具选择评估:")
        print(f"   选择准确率: {accuracy:.1f}%")
        print(f"   平均选择时间: {avg_selection_time:.3f}秒")
    # 关闭工具编排器
    orchestrator.shutdown()

    print("\n✅ ToolOrchestrator测试完成！")

if __name__ == "__main__":
    asyncio.run(test_tool_orchestrator())
