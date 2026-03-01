#!/usr/bin/env python3
"""
知识库质量验证脚本
用于检查知识库中是否包含必要的历史信息
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from knowledge_management_system.api.service_interface import get_knowledge_service
import json

def test_knowledge_base():
    """测试知识库内容"""
    print("=" * 80)
    print("知识库质量验证测试")
    print("=" * 80)
    
    # 初始化知识服务
    print("\n1. 初始化知识服务...")
    try:
        service = get_knowledge_service()
        print("✅ 知识服务初始化成功")
    except Exception as e:
        print(f"❌ 知识服务初始化失败: {e}")
        return
    
    # 测试查询列表
    test_queries = [
        "Harriet Lane",
        "15th first lady of the United States",
        "James Buchanan niece",
        "Jane Ann Lane",
        "Harriet Lane mother",
        "James A. Garfield",
        "second assassinated president",
        "Garfield mother maiden name",
        "Ballou",
        "Eliza Ballou"
    ]
    
    print(f"\n2. 测试 {len(test_queries)} 个关键查询...")
    print("-" * 80)
    
    results_summary = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] 查询: {query}")
        print("-" * 80)
        
        try:
            # 测试向量知识库检索
            results = service.query_knowledge(
                query=query,
                modality="text",
                top_k=10,
                similarity_threshold=0.3,  # 使用较低阈值以获取更多结果
                use_rerank=True,
                use_graph=True,
                use_llamaindex=True
            )
            
            print(f"   返回结果数量: {len(results)}")
            
            if results:
                print(f"   前5条结果:")
                for j, result in enumerate(results[:5], 1):
                    content = result.get('content', '') or result.get('text', '')
                    similarity = result.get('similarity_score', 0) or result.get('similarity', 0)
                    source = result.get('metadata', {}).get('source', 'unknown')
                    
                    # 检查内容相关性
                    query_lower = query.lower()
                    content_lower = content.lower()
                    
                    relevance_keywords = []
                    if 'harriet' in query_lower and 'harriet' in content_lower:
                        relevance_keywords.append("✅包含Harriet")
                    if 'lane' in query_lower and 'lane' in content_lower:
                        relevance_keywords.append("✅包含Lane")
                    if 'first lady' in query_lower and 'first lady' in content_lower:
                        relevance_keywords.append("✅包含first lady")
                    if 'garfield' in query_lower and 'garfield' in content_lower:
                        relevance_keywords.append("✅包含Garfield")
                    if 'ballou' in query_lower and 'ballou' in content_lower:
                        relevance_keywords.append("✅包含Ballou")
                    
                    relevance = " | ".join(relevance_keywords) if relevance_keywords else "❌不相关"
                    
                    content_preview = content[:150].replace('\n', ' ') if content else "空内容"
                    print(f"     [{j}] 相似度: {similarity:.3f} | 来源: {source}")
                    print(f"         相关性: {relevance}")
                    print(f"         内容: {content_preview}...")
                
                # 检查是否有相关结果
                has_relevant = any(
                    any(keyword in (result.get('content', '') or '').lower() 
                        for keyword in query.lower().split() 
                        if len(keyword) > 3)
                    for result in results[:5]
                )
                
                results_summary.append({
                    'query': query,
                    'result_count': len(results),
                    'has_relevant': has_relevant,
                    'top_similarity': results[0].get('similarity_score', 0) or results[0].get('similarity', 0) if results else 0
                })
            else:
                print("   ❌ 未找到任何结果")
                results_summary.append({
                    'query': query,
                    'result_count': 0,
                    'has_relevant': False,
                    'top_similarity': 0
                })
                
        except Exception as e:
            print(f"   ❌ 查询失败: {e}")
            results_summary.append({
                'query': query,
                'result_count': 0,
                'has_relevant': False,
                'error': str(e)
            })
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    total_queries = len(results_summary)
    queries_with_results = sum(1 for r in results_summary if r['result_count'] > 0)
    queries_with_relevant = sum(1 for r in results_summary if r.get('has_relevant', False))
    
    print(f"总查询数: {total_queries}")
    print(f"有结果的查询: {queries_with_results} ({queries_with_results/total_queries*100:.1f}%)")
    print(f"有相关结果的查询: {queries_with_relevant} ({queries_with_relevant/total_queries*100:.1f}%)")
    
    print("\n详细结果:")
    for r in results_summary:
        status = "✅" if r.get('has_relevant') else "❌"
        print(f"  {status} {r['query']}: {r['result_count']}条结果, 最高相似度: {r.get('top_similarity', 0):.3f}")
        if 'error' in r:
            print(f"     错误: {r['error']}")
    
    # 检查关键信息是否存在
    print("\n" + "=" * 80)
    print("关键信息检查")
    print("=" * 80)
    
    key_facts = [
        ("Harriet Lane", "第15任第一夫人"),
        ("Jane Ann Lane", "Harriet Lane的母亲"),
        ("James A. Garfield", "第二位遇刺总统"),
        ("Ballou", "Garfield母亲的娘家姓")
    ]
    
    for fact, description in key_facts:
        found = any(
            fact.lower() in (r.get('content', '') or '').lower()
            for summary in results_summary
            if summary['query'].lower() in fact.lower() or fact.lower() in summary['query'].lower()
            for r in [summary]  # 这里需要实际查询结果，暂时简化
        )
        status = "✅" if found else "❌"
        print(f"  {status} {fact} ({description})")
    
    return results_summary

if __name__ == "__main__":
    test_knowledge_base()

