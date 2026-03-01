#!/usr/bin/env python3
"""
测试 CitationAgentAdapter

快速验证适配器是否正常工作。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.adapters.citation_agent_adapter import CitationAgentAdapter


async def test_adapter():
    """测试适配器基本功能"""
    print("=" * 80)
    print("测试 CitationAgentAdapter")
    print("=" * 80)
    
    # 创建适配器
    adapter = CitationAgentAdapter()
    print(f"✅ 适配器创建成功: {adapter.source} → {adapter.target}")
    
    # 测试上下文转换
    print("\n1. 测试上下文转换...")
    old_context = {
        "query": "测试查询",
        "answer": "这是一个测试答案",
        "knowledge": [
            {"content": "知识1", "source": "source1"},
            {"content": "知识2", "source": "source2"}
        ],
        "evidence": []
    }
    
    adapted_context = adapter.adapt_context(old_context)
    print(f"   原始上下文键: {list(old_context.keys())}")
    print(f"   转换后上下文键: {list(adapted_context.keys())}")
    print(f"   操作类型: {adapted_context.get('action')}")
    print(f"   内容: {adapted_context.get('content')[:30]}...")
    print(f"   来源数量: {len(adapted_context.get('sources', []))}")
    print("   ✅ 上下文转换成功")
    
    # 测试目标Agent初始化
    print("\n2. 测试目标Agent初始化...")
    target_agent = adapter.target_agent
    print(f"   目标Agent类型: {type(target_agent).__name__}")
    print(f"   目标Agent ID: {target_agent.agent_id}")
    print("   ✅ 目标Agent初始化成功")
    
    # 测试执行（简单测试，不实际调用）
    print("\n3. 测试适配器统计...")
    stats = adapter.get_migration_stats()
    print(f"   源Agent: {stats['source_agent']}")
    print(f"   目标Agent: {stats['target_agent']}")
    print(f"   总调用数: {stats['total_calls']}")
    print(f"   成功率: {stats['success_rate']:.2%}")
    print("   ✅ 统计信息获取成功")
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_adapter())

