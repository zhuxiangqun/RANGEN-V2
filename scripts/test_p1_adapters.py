#!/usr/bin/env python3
"""
测试P1优先级适配器

验证所有P1优先级适配器的基本功能：
1. ReActAgentAdapter
2. KnowledgeRetrievalAgentAdapter
3. RAGAgentAdapter
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.adapters.react_agent_adapter import ReActAgentAdapter
from src.adapters.knowledge_retrieval_agent_adapter import KnowledgeRetrievalAgentAdapter
from src.adapters.rag_agent_adapter import RAGAgentAdapter


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


async def test_react_adapter() -> AdapterTestResult:
    """测试ReActAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="ReActAgentAdapter",
        source_agent="ReActAgent",
        target_agent="ReasoningExpert"
    )
    
    try:
        # 创建适配器
        adapter = ReActAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        # 测试上下文转换
        old_context = {
            "query": "测试查询：什么是人工智能？",
            "max_iterations": 5,
            "tools": ["search", "calculator"]
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "query" in adapted_context and
            "max_parallel_paths" in adapted_context and
            adapted_context.get("query") == old_context["query"]
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        # 测试目标Agent初始化
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id') and
            target_agent.agent_id == "reasoning_expert"
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        # 测试统计信息获取
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


async def test_knowledge_retrieval_adapter() -> AdapterTestResult:
    """测试KnowledgeRetrievalAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="KnowledgeRetrievalAgentAdapter",
        source_agent="KnowledgeRetrievalAgent",
        target_agent="RAGExpert"
    )
    
    try:
        # 创建适配器
        adapter = KnowledgeRetrievalAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        # 测试上下文转换
        old_context = {
            "query": "测试查询：什么是机器学习？",
            "type": "knowledge_retrieval",
            "max_results": 10,
            "threshold": 0.7
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "query" in adapted_context and
            "use_cache" in adapted_context and
            "_knowledge_retrieval_only" in adapted_context and
            adapted_context.get("query") == old_context["query"]
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        # 测试目标Agent初始化
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id') and
            target_agent.agent_id == "rag_expert"
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        # 测试统计信息获取
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


async def test_rag_adapter() -> AdapterTestResult:
    """测试RAGAgentAdapter"""
    result = AdapterTestResult(
        adapter_name="RAGAgentAdapter",
        source_agent="RAGAgent",
        target_agent="RAGExpert"
    )
    
    try:
        # 创建适配器
        adapter = RAGAgentAdapter()
        print(f"✅ [{result.adapter_name}] 适配器创建成功")
        
        # 测试上下文转换
        old_context = {
            "query": "测试查询：什么是深度学习？",
            "type": "rag",
            "use_cache": True,
            "use_parallel": True
        }
        adapted_context = adapter.adapt_context(old_context)
        result.context_adaptation = (
            "query" in adapted_context and
            "type" in adapted_context and
            adapted_context.get("query") == old_context["query"] and
            adapted_context.get("type") == old_context["type"]
        )
        print(f"   {'✅' if result.context_adaptation else '❌'} 上下文转换: {result.context_adaptation}")
        
        # 测试目标Agent初始化
        target_agent = adapter.target_agent
        result.agent_initialization = (
            target_agent is not None and
            hasattr(target_agent, 'agent_id') and
            target_agent.agent_id == "rag_expert"
        )
        print(f"   {'✅' if result.agent_initialization else '❌'} 目标Agent初始化: {result.agent_initialization}")
        
        # 测试统计信息获取
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
    print("P1优先级适配器验证测试")
    print("=" * 80)
    
    test_functions = [
        ("ReActAgentAdapter", test_react_adapter),
        ("KnowledgeRetrievalAgentAdapter", test_knowledge_retrieval_adapter),
        ("RAGAgentAdapter", test_rag_adapter),
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
        print("✅ 所有P1优先级适配器验证通过！")
    else:
        print(f"⚠️ {total_tests - passed_tests} 个适配器验证失败")
    print("=" * 80)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

