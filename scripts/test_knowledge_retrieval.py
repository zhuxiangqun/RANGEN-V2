#!/usr/bin/env python3
"""
测试知识库检索功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_knowledge_retrieval():
    """测试知识库检索功能"""
    try:
        from src.memory.enhanced_faiss_memory import EnhancedFAISSMemory

        print("🔄 初始化FAISS内存...")
        memory = EnhancedFAISSMemory()

        print("🔍 测试机器学习知识检索...")

        # 测试查询
        queries = [
            "什么是机器学习？",
            "机器学习的优点",
            "机器学习的缺点"
        ]

        for query in queries:
            print(f"\n📝 查询: {query}")
            try:
                results = memory.search(query, top_k=3)
                if results:
                    print(f"✅ 找到 {len(results)} 条相关知识:")
                    for i, result in enumerate(results[:2]):  # 只显示前2条
                        content = result.get('content', '')[:100] + "..." if len(result.get('content', '')) > 100 else result.get('content', '')
                        score = result.get('score', 0)
                        title = result.get('title', 'Unknown')
                        print(f"  {i+1}. [{title}] 相关度: {score:.3f}")
                        print(f"     {content}")
                else:
                    print("❌ 未找到相关知识")

            except Exception as e:
                print(f"❌ 检索失败: {e}")

        print("\n🎉 知识库检索测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_knowledge_retrieval())
