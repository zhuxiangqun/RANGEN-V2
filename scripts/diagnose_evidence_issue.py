#!/usr/bin/env python3
"""
诊断脚本：检查知识库内容和证据处理问题
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

async def check_knowledge_base():
    """检查知识库内容"""
    print("=" * 80)
    print("1. 检查知识库内容")
    print("=" * 80)
    
    try:
        from knowledge_management_system.api.service_interface import KnowledgeManagementService
        kms = KnowledgeManagementService()
        
        # 测试查询1: NYC建筑物排名
        query1 = "List of tallest buildings in New York City ranking"
        print(f"\n查询1: {query1}")
        results1 = kms.query_knowledge(
            query=query1,
            modality="text",
            top_k=5,
            similarity_threshold=0.3,
            use_rerank=True
        )
        print(f"检索到 {len(results1)} 条结果")
        for i, result in enumerate(results1[:3], 1):
            content = result.get('content', '')
            score = result.get('similarity_score', 0)
            print(f"\n结果 {i} (相似度: {score:.3f}):")
            print(f"内容预览: {content[:300]}...")
            if "37th" in content or "823" in content or "ranking" in content.lower():
                print("✅ 包含排名相关信息！")
            if len(content) > 2000:
                print(f"⚠️ 内容较长 ({len(content)} 字符)，可能被截断")
        
        # 测试查询2: Charlotte Brontë
        query2 = "Charlotte Brontë Jane Eyre Dewey Decimal"
        print(f"\n查询2: {query2}")
        results2 = kms.query_knowledge(
            query=query2,
            modality="text",
            top_k=5,
            similarity_threshold=0.3,
            use_rerank=True
        )
        print(f"检索到 {len(results2)} 条结果")
        for i, result in enumerate(results2[:3], 1):
            content = result.get('content', '')
            score = result.get('similarity_score', 0)
            print(f"\n结果 {i} (相似度: {score:.3f}):")
            print(f"内容预览: {content[:300]}...")
        
    except Exception as e:
        print(f"❌ 检查知识库失败: {e}")
        import traceback
        traceback.print_exc()

def check_evidence_processing():
    """检查证据处理逻辑"""
    print("\n" + "=" * 80)
    print("2. 检查证据处理逻辑")
    print("=" * 80)
    
    # 模拟证据内容
    sample_evidence = """
## List of Tallest Buildings in New York City

As of August 2024, the tallest buildings in New York City are:

1. One World Trade Center: 1,776 feet (541 m)
2. Central Park Tower: 1,550 feet (472 m)
...
37. [Building name]: 823 feet (251 m)
38. ...
...
100. [Building name]: 500 feet (152 m)

This list includes all buildings over 500 feet in height.
"""
    
    print(f"\n原始证据长度: {len(sample_evidence)} 字符")
    
    # 检查处理逻辑
    query_complexity = 10  # 中等查询
    target_length = 1500
    
    print(f"目标长度限制: {target_length} 字符")
    print(f"原始长度: {len(sample_evidence)} 字符")
    
    if len(sample_evidence) > target_length:
        # 模拟截断
        truncated = sample_evidence[:target_length]
        print(f"\n⚠️ 截断后长度: {len(truncated)} 字符")
        print(f"⚠️ 丢失: {len(sample_evidence) - len(truncated)} 字符")
        
        # 检查是否包含关键信息
        if "37th" in truncated:
            print("✅ 截断后仍包含 '37th'")
        else:
            print("❌ 截断后丢失 '37th' 信息")
        
        if "823 feet" in truncated:
            print("✅ 截断后仍包含 '823 feet'")
        else:
            print("❌ 截断后丢失 '823 feet' 信息")

async def test_actual_retrieval():
    """测试实际检索"""
    print("\n" + "=" * 80)
    print("3. 测试实际检索（样本2查询）")
    print("=" * 80)
    
    query = "Imagine there is a building called Bronte tower whose height in feet is the same number as the dewey decimal classification for the Charlotte Bronte book that was published in 1847. Where would this building rank among tallest buildings in New York City, as of August 2024?"
    
    print(f"查询: {query[:100]}...")
    
    try:
        from knowledge_management_system.api.service_interface import KnowledgeManagementService
        kms = KnowledgeManagementService()
        
        results = kms.query_knowledge(
            query=query,
            modality="text",
            top_k=10,
            similarity_threshold=0.3,
            use_rerank=True
        )
        
        print(f"\n检索到 {len(results)} 条结果")
        
        for i, result in enumerate(results[:5], 1):
            content = result.get('content', '')
            score = result.get('similarity_score', 0)
            print(f"\n--- 结果 {i} (相似度: {score:.3f}) ---")
            print(f"内容长度: {len(content)} 字符")
            print(f"内容预览 (前500字符):")
            print(content[:500])
            print("...")
            
            # 检查关键词
            keywords = ["823", "37th", "ranking", "tallest", "NYC", "New York City", "Dewey Decimal", "Charlotte Brontë", "Jane Eyre"]
            found_keywords = [kw for kw in keywords if kw.lower() in content.lower()]
            if found_keywords:
                print(f"✅ 找到关键词: {', '.join(found_keywords)}")
            else:
                print("⚠️ 未找到相关关键词")
            
            # 检查是否有排名列表
            if "37th" in content or "37." in content or "37:" in content:
                print("✅ 包含排名信息！")
            if "823" in content or "eight hundred" in content.lower():
                print("✅ 包含高度信息！")
        
    except Exception as e:
        print(f"❌ 测试检索失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    import asyncio
    
    print("开始诊断知识库和证据处理问题...\n")
    
    await check_knowledge_base()
    check_evidence_processing()
    await test_actual_retrieval()
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

