#!/usr/bin/env python3
"""
测试P2优先级适配器

验证所有P2优先级适配器的基本功能：
1. ChiefAgentAdapter
2. AnswerGenerationAgentAdapter
3. PromptEngineeringAgentAdapter
4. ContextEngineeringAgentAdapter
5. MemoryAgentAdapter
6. OptimizedKnowledgeRetrievalAgentAdapter
7. EnhancedAnalysisAgentAdapter
8. LearningSystemAdapter
9. IntelligentStrategyAgentAdapter
10. FactVerificationAgentAdapter
11. IntelligentCoordinatorAgentAdapter
12. StrategicChiefAgentAdapter
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.adapters.chief_agent_adapter import ChiefAgentAdapter
from src.adapters.answer_generation_agent_adapter import AnswerGenerationAgentAdapter
from src.adapters.prompt_engineering_agent_adapter import PromptEngineeringAgentAdapter
from src.adapters.context_engineering_agent_adapter import ContextEngineeringAgentAdapter
from src.adapters.memory_agent_adapter import MemoryAgentAdapter
from src.adapters.optimized_knowledge_retrieval_agent_adapter import OptimizedKnowledgeRetrievalAgentAdapter
from src.adapters.enhanced_analysis_agent_adapter import EnhancedAnalysisAgentAdapter
from src.adapters.learning_system_adapter import LearningSystemAdapter
from src.adapters.intelligent_strategy_agent_adapter import IntelligentStrategyAgentAdapter
from src.adapters.fact_verification_agent_adapter import FactVerificationAgentAdapter
from src.adapters.intelligent_coordinator_agent_adapter import IntelligentCoordinatorAgentAdapter
from src.adapters.strategic_chief_agent_adapter import StrategicChiefAgentAdapter


@dataclass
class AdapterTestResult:
    """适配器测试结果"""
    adapter_name: str
    source_agent: str
    target_agent: str
    context_adaptation: bool = False
    agent_initialization: bool = False
    stats_retrieval: bool = False
    overall_success: bool = False
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def calculate_success(self):
        """计算总体成功状态"""
        self.overall_success = (
            self.context_adaptation and
            self.agent_initialization and
            self.stats_retrieval and
            len(self.errors) == 0
        )


async def test_chief_agent_adapter() -> AdapterTestResult:
    """测试ChiefAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="ChiefAgentAdapter",
        source_agent="ChiefAgent",
        target_agent="AgentCoordinator"
    )
    
    try:
        adapter = ChiefAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "query": "测试查询：协调多个Agent完成任务",
            "session_id": "test_session_001",
            "dependencies": {}
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "task" in adapted_context and
            adapted_context.get("action") == "submit_task"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_answer_generation_adapter() -> AdapterTestResult:
    """测试AnswerGenerationAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="AnswerGenerationAgentAdapter",
        source_agent="AnswerGenerationAgent",
        target_agent="RAGExpert"
    )
    
    try:
        adapter = AnswerGenerationAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "query": "测试查询：生成答案",
            "knowledge": [{"content": "知识1"}],
            "evidence": [],
            "dependencies": {}
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "query" in adapted_context and
            "_answer_generation_only" in adapted_context and
            adapted_context.get("query") == old_context["query"]
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_prompt_engineering_adapter() -> AdapterTestResult:
    """测试PromptEngineeringAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="PromptEngineeringAgentAdapter",
        source_agent="PromptEngineeringAgent",
        target_agent="ToolOrchestrator"
    )
    
    try:
        adapter = PromptEngineeringAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "task_type": "generate_prompt",
            "query": "测试查询",
            "template_name": "test_template",
            "query_type": "question"
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "tool_name" in adapted_context and
            adapted_context.get("action") == "optimize_prompt"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_context_engineering_adapter() -> AdapterTestResult:
    """测试ContextEngineeringAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="ContextEngineeringAgentAdapter",
        source_agent="ContextEngineeringAgent",
        target_agent="MemoryManager"
    )
    
    try:
        adapter = ContextEngineeringAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "task_type": "get_context",
            "session_id": "test_session",
            "max_fragments": 10
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "limit" in adapted_context and
            adapted_context.get("action") == "retrieve"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_memory_agent_adapter() -> AdapterTestResult:
    """测试MemoryAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="MemoryAgentAdapter",
        source_agent="MemoryAgent",
        target_agent="MemoryManager"
    )
    
    try:
        adapter = MemoryAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "task_type": "retrieve",
            "session_id": "test_session",
            "max_fragments": 10
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "limit" in adapted_context and
            adapted_context.get("action") == "retrieve"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_optimized_knowledge_retrieval_adapter() -> AdapterTestResult:
    """测试OptimizedKnowledgeRetrievalAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="OptimizedKnowledgeRetrievalAgentAdapter",
        source_agent="OptimizedKnowledgeRetrievalAgent",
        target_agent="RAGExpert"
    )
    
    try:
        adapter = OptimizedKnowledgeRetrievalAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "query": "测试查询",
            "max_results": 10,
            "threshold": 0.7,
            "optimization_params": {"use_cache": True}
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "query" in adapted_context and
            "_knowledge_retrieval_only" in adapted_context and
            adapted_context.get("query") == old_context["query"]
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_enhanced_analysis_adapter() -> AdapterTestResult:
    """测试EnhancedAnalysisAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="EnhancedAnalysisAgentAdapter",
        source_agent="EnhancedAnalysisAgent",
        target_agent="ReasoningExpert"
    )
    
    try:
        adapter = EnhancedAnalysisAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "query": "测试查询：分析数据",
            "analysis_type": "deep",
            "data": {}
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "query" in adapted_context and
            adapted_context.get("query") == old_context["query"]
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_learning_system_adapter() -> AdapterTestResult:
    """测试LearningSystemAdapter"""
    result = AdapterTestResult(
        adapter_name="LearningSystemAdapter",
        source_agent="LearningSystem",
        target_agent="LearningOptimizer"
    )
    
    try:
        adapter = LearningSystemAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "action": "learn",
            "model_id": "test_model",
            "data": {"sample": "data"}
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            adapted_context.get("action") == "incremental_learning"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_intelligent_strategy_adapter() -> AdapterTestResult:
    """测试IntelligentStrategyAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="IntelligentStrategyAgentAdapter",
        source_agent="IntelligentStrategyAgent",
        target_agent="AgentCoordinator"
    )
    
    try:
        adapter = IntelligentStrategyAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "query": "测试查询：制定策略",
            "strategy_type": "optimization",
            "goals": []
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "task" in adapted_context and
            adapted_context.get("action") == "submit_task"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_fact_verification_adapter() -> AdapterTestResult:
    """测试FactVerificationAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="FactVerificationAgentAdapter",
        source_agent="FactVerificationAgent",
        target_agent="QualityController"
    )
    
    try:
        adapter = FactVerificationAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "answer": "测试答案",
            "query": "测试查询",
            "evidence": [],
            "facts": []
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "content" in adapted_context and
            adapted_context.get("action") == "validate_content"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_intelligent_coordinator_adapter() -> AdapterTestResult:
    """测试IntelligentCoordinatorAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="IntelligentCoordinatorAgentAdapter",
        source_agent="IntelligentCoordinatorAgent",
        target_agent="AgentCoordinator"
    )
    
    try:
        adapter = IntelligentCoordinatorAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "action": "submit_task",
            "task": {"id": "test_task", "description": "测试任务"},
            "agents": []
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "task" in adapted_context and
            adapted_context.get("action") == "submit_task"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def test_strategic_chief_adapter() -> AdapterTestResult:
    """测试StrategicChiefAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="StrategicChiefAgentAdapter",
        source_agent="StrategicChiefAgent",
        target_agent="AgentCoordinator"
    )
    
    try:
        adapter = StrategicChiefAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        old_context = {
            "query": "测试查询：战略决策",
            "strategic_goal": "优化系统性能",
            "resources": {}
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "action" in adapted_context and
            "task" in adapted_context and
            adapted_context.get("action") == "submit_task"
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id')
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        stats = adapter.get_migration_stats()
        result.stats_retrieval = (
            stats.get("source_agent") == result.source_agent and
            stats.get("target_agent") == result.target_agent
        )
        print(f"   {'✅' if result.stats_retrieval else '❌'} 统计信息获取: {result.stats_retrieval}")
        
    except Exception as e:
        result.errors.append(str(e))
        print(f"   ❌ 错误: {e}")
    
    result.calculate_success()
    return result


async def main():
    """主测试函数"""
    print("=" * 80)
    print("P2优先级适配器验证测试")
    print("=" * 80)
    
    test_functions = [
        ("ChiefAgentAdapter", test_chief_agent_adapter),
        ("AnswerGenerationAgentAdapter", test_answer_generation_adapter),
        ("PromptEngineeringAgentAdapter", test_prompt_engineering_adapter),
        ("ContextEngineeringAgentAdapter", test_context_engineering_adapter),
        ("MemoryAgentAdapter", test_memory_agent_adapter),
        ("OptimizedKnowledgeRetrievalAgentAdapter", test_optimized_knowledge_retrieval_adapter),
        ("EnhancedAnalysisAgentAdapter", test_enhanced_analysis_adapter),
        ("LearningSystemAdapter", test_learning_system_adapter),
        ("IntelligentStrategyAgentAdapter", test_intelligent_strategy_adapter),
        ("FactVerificationAgentAdapter", test_fact_verification_adapter),
        ("IntelligentCoordinatorAgentAdapter", test_intelligent_coordinator_adapter),
        ("StrategicChiefAgentAdapter", test_strategic_chief_adapter),
    ]
    
    results = []
    
    for name, test_func in test_functions:
        print(f"\n测试 {name}:")
        print("-" * 80)
        result = await test_func()
        results.append(result)
        print(f"   总体结果: {'✅ 通过' if result.overall_success else '❌ 失败'}")
        if result.errors:
            print(f"   错误: {', '.join(result.errors)}")
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("测试汇总")
    print("=" * 80)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.overall_success)
    
    print(f"\n总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {total_tests - passed_tests}")
    
    print("\n详细结果:")
    for result in results:
        status = "✅" if result.overall_success else "❌"
        print(f"  {status} {result.adapter_name}: {result.source_agent} → {result.target_agent}")
        if result.errors:
            for error in result.errors:
                print(f"     错误: {error}")
    
    print("\n" + "=" * 80)
    if passed_tests == total_tests:
        print("✅ 所有P2优先级适配器验证通过！")
    else:
        print(f"⚠️ {total_tests - passed_tests} 个适配器验证失败")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

