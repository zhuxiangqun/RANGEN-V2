#!/usr/bin/env python3
"""
检查知识库中关于第15位第一夫人的信息
"""

import sys
import os
import asyncio

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json

async def check_15th_first_lady():
    """检查知识库中关于第15位第一夫人的信息"""
    
    print("="*80)
    print("检查知识库中关于第15位第一夫人的信息")
    print("="*80)
    
    # 初始化知识检索服务
    try:
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        service = KnowledgeRetrievalService()
        print("✅ 知识检索服务初始化成功")
    except Exception as e:
        print(f"❌ 知识检索服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 获取知识库服务
    try:
        kms_service = service.kms_service
        if not kms_service:
            print("❌ 知识库服务不可用")
            return
        print("✅ 知识库服务获取成功")
    except Exception as e:
        print(f"❌ 知识库服务获取失败: {e}")
        return
    
    # 测试查询列表
    test_queries = [
        "Who was the 15th first lady of the United States?",
        "15th first lady of the United States",
        "Harriet Lane",
        "Jane Pierce",
        "Sarah Polk",
        "15th president first lady",
        "James Buchanan first lady",
        "Franklin Pierce first lady",
    ]
    
    print("\n" + "="*80)
    print("执行查询测试")
    print("="*80)
    
    results_summary = {}
    
    for query in test_queries:
        print(f"\n📝 查询: {query}")
        print("-" * 80)
        
        try:
            # 直接使用知识库服务查询
            results = kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=10,
                similarity_threshold=0.0,  # 不设置阈值，获取所有结果
                use_rerank=True,
                use_graph=False
            )
            
            if results and len(results) > 0:
                sources = results
                print(f"✅ 找到 {len(sources)} 条结果")
                
                # 分析结果
                relevant_results = []
                for i, source in enumerate(sources[:5]):  # 只显示前5条
                    content = source.get('content', '')
                    similarity = source.get('similarity_score', source.get('similarity', 0.0))
                    confidence = source.get('confidence', similarity)
                    
                    # 检查是否包含关键信息
                    has_harriet = 'Harriet' in content or 'harriet' in content.lower()
                    has_lane = 'Lane' in content or 'lane' in content.lower()
                    has_jane_pierce = 'Jane Pierce' in content or 'jane pierce' in content.lower()
                    has_sarah_polk = 'Sarah Polk' in content or 'sarah polk' in content.lower()
                    has_15th = '15th' in content or 'fifteenth' in content.lower() or '15' in content
                    has_buchanan = 'Buchanan' in content or 'buchanan' in content.lower()
                    has_pierce = 'Pierce' in content or 'pierce' in content.lower()
                    
                    print(f"\n  结果 {i+1}:")
                    print(f"    相似度: {similarity:.4f}")
                    print(f"    置信度: {confidence:.4f}")
                    print(f"    内容预览: {content[:200]}...")
                    
                    # 标记关键信息
                    markers = []
                    if has_harriet:
                        markers.append("✅ Harriet")
                    if has_lane:
                        markers.append("✅ Lane")
                    if has_jane_pierce:
                        markers.append("✅ Jane Pierce")
                    if has_sarah_polk:
                        markers.append("⚠️ Sarah Polk (错误)")
                    if has_15th:
                        markers.append("✅ 15th")
                    if has_buchanan:
                        markers.append("✅ Buchanan")
                    if has_pierce:
                        markers.append("✅ Pierce")
                    
                    if markers:
                        print(f"    标记: {', '.join(markers)}")
                    
                    # 如果包含相关信息，记录
                    if has_harriet or has_lane or has_jane_pierce or has_sarah_polk or has_15th:
                        relevant_results.append({
                            'rank': i+1,
                            'similarity': similarity,
                            'confidence': confidence,
                            'content_preview': content[:200],
                            'has_harriet': has_harriet,
                            'has_lane': has_lane,
                            'has_jane_pierce': has_jane_pierce,
                            'has_sarah_polk': has_sarah_polk,
                            'has_15th': has_15th,
                            'has_buchanan': has_buchanan,
                            'has_pierce': has_pierce,
                        })
                
                results_summary[query] = {
                    'total_results': len(sources),
                    'relevant_results': relevant_results
                }
            else:
                print(f"❌ 未找到结果")
                results_summary[query] = {
                    'total_results': 0,
                    'relevant_results': []
                }
                
        except Exception as e:
            print(f"❌ 查询失败: {e}")
            import traceback
            traceback.print_exc()
            results_summary[query] = {
                'error': str(e)
            }
    
    # 总结
    print("\n" + "="*80)
    print("查询结果总结")
    print("="*80)
    
    # 统计
    total_queries = len(test_queries)
    successful_queries = sum(1 for r in results_summary.values() if 'error' not in r)
    queries_with_harriet = sum(1 for r in results_summary.values() 
                               if 'relevant_results' in r and 
                               any(res.get('has_harriet') for res in r['relevant_results']))
    queries_with_sarah_polk = sum(1 for r in results_summary.values() 
                                 if 'relevant_results' in r and 
                                 any(res.get('has_sarah_polk') for res in r['relevant_results']))
    queries_with_jane_pierce = sum(1 for r in results_summary.values() 
                                  if 'relevant_results' in r and 
                                  any(res.get('has_jane_pierce') for res in r['relevant_results']))
    
    print(f"\n总查询数: {total_queries}")
    print(f"成功查询数: {successful_queries}")
    print(f"包含Harriet Lane的查询数: {queries_with_harriet}")
    print(f"包含Sarah Polk的查询数: {queries_with_sarah_polk} ⚠️")
    print(f"包含Jane Pierce的查询数: {queries_with_jane_pierce}")
    
    # 分析问题
    print("\n" + "="*80)
    print("问题分析")
    print("="*80)
    
    if queries_with_sarah_polk > 0:
        print("\n⚠️ 发现问题: 知识库中包含Sarah Polk的信息")
        print("   这可能导致系统错误地识别第15位第一夫人为Sarah Polk")
        print("   正确应该是: Harriet Lane (James Buchanan的侄女)")
        print("   或者: Jane Pierce (Franklin Pierce的妻子，第14位第一夫人)")
        
        # 找出哪些查询返回了Sarah Polk
        print("\n   包含Sarah Polk的查询:")
        for query, result in results_summary.items():
            if 'relevant_results' in result:
                for res in result['relevant_results']:
                    if res.get('has_sarah_polk'):
                        print(f"     - {query} (排名: {res['rank']}, 相似度: {res['similarity']:.4f})")
    
    if queries_with_harriet > 0:
        print("\n✅ 好消息: 知识库中包含Harriet Lane的信息")
        print("   这是正确的第15位第一夫人（James Buchanan的侄女）")
    
    if queries_with_jane_pierce > 0:
        print("\n✅ 知识库中包含Jane Pierce的信息")
        print("   这是第14位第一夫人（Franklin Pierce的妻子）")
        print("   注意: 如果系统混淆了第14和第15位，可能导致错误")
    
    # 保存结果到文件
    output_file = "knowledge_base_15th_first_lady_check.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"\n✅ 查询结果已保存到: {output_file}")

if __name__ == "__main__":
    asyncio.run(check_15th_first_lady())

