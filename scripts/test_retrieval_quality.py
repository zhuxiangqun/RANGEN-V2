#!/usr/bin/env python3
"""
测试知识检索质量
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载.env文件')
except ImportError:
    print('⚠️ python-dotenv未安装')

async def test_retrieval_quality():
    """测试知识检索质量"""
    try:
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

        print("🔧 初始化知识检索服务...")
        service = KnowledgeRetrievalService()

        # 测试查询
        queries = [
            "什么是RAG？",
            "RAG的优势是什么？",
            "Retrieval-Augmented Generation"
        ]

        for query in queries:
            print(f"\n🧪 测试查询: '{query}'")

            # 执行检索
            result = await service.retrieve_knowledge(query, top_k=5)

            if result and result.get('sources'):
                print(f"✅ 检索成功，返回 {len(result['sources'])} 条结果")

                # 检查前3条结果的相关性
                for i, source in enumerate(result['sources'][:3]):
                    content = source.get('content', '')[:200]
                    similarity = source.get('similarity', 0)
                    print(f"  结果{i+1}: 相似度={similarity:.3f}")
                    print(f"    内容预览: {content}...")

                    # 检查是否包含相关关键词
                    query_lower = query.lower()
                    content_lower = content.lower()

                    if 'rag' in query_lower:
                        has_rag = 'rag' in content_lower or '检索增强生成' in content_lower
                        if not has_rag:
                            print("    ❌ 内容不包含RAG相关信息！"                        else:
                            print("    ✅ 内容包含RAG相关信息"
            else:
                print("❌ 检索失败或无结果"
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_retrieval_quality())
