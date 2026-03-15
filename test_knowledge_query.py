#!/usr/bin/env python3
"""
测试脚本：直接查询知识库，验证"Who was the 15th first lady of the United States?"是否能在知识库中找到
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_knowledge_query():
    """测试知识库查询"""
    try:
        # 导入知识库管理系统
        from knowledge_management_system.api.service_interface import get_knowledge_service
        
        # 获取知识库服务
        kms_service = get_knowledge_service()
        if not kms_service:
            print("❌ 知识库管理系统不可用")
            return
        
        print("✅ 知识库管理系统已初始化")
        
        # 测试查询
        test_queries = [
            "Who was the 15th first lady of the United States?",
            "15th first lady",
            "Harriet Lane",
            "first lady of the United States",
            "James Buchanan first lady",
        ]
        
        for query in test_queries:
            print(f"\n{'='*80}")
            print(f"🔍 测试查询: {query}")
            print(f"{'='*80}")
            
            # 查询知识库（使用多种配置）
            configs = [
                {
                    "name": "基础查询（无rerank，无graph）",
                    "top_k": 10,
                    "similarity_threshold": 0.3,
                    "use_rerank": False,
                    "use_graph": False,
                },
                {
                    "name": "启用rerank",
                    "top_k": 10,
                    "similarity_threshold": 0.3,
                    "use_rerank": True,
                    "use_graph": False,
                },
                {
                    "name": "启用知识图谱",
                    "top_k": 10,
                    "similarity_threshold": 0.3,
                    "use_rerank": True,
                    "use_graph": True,
                },
                {
                    "name": "低阈值查询",
                    "top_k": 20,
                    "similarity_threshold": 0.2,
                    "use_rerank": True,
                    "use_graph": True,
                },
            ]
            
            for config in configs:
                print(f"\n📋 配置: {config['name']}")
                print(f"   top_k: {config['top_k']}, threshold: {config['similarity_threshold']}")
                print(f"   use_rerank: {config['use_rerank']}, use_graph: {config['use_graph']}")
                
                try:
                    results = kms_service.query_knowledge(
                        query=query,
                        modality="text",
                        top_k=config['top_k'],
                        similarity_threshold=config['similarity_threshold'],
                        use_rerank=config['use_rerank'],
                        use_graph=config['use_graph'],
                    )
                    
                    if results:
                        print(f"   ✅ 找到 {len(results)} 个结果")
                        for i, result in enumerate(results[:3], 1):  # 只显示前3个
                            content = result.get('content', '')[:200]
                            score = result.get('similarity_score', 0.0)
                            knowledge_id = result.get('knowledge_id', 'unknown')
                            print(f"   {i}. [相似度: {score:.3f}] {knowledge_id}")
                            print(f"      {content}...")
                    else:
                        print(f"   ❌ 未找到结果")
                        
                except Exception as e:
                    print(f"   ❌ 查询失败: {e}")
        
        # 检查知识库大小
        print(f"\n{'='*80}")
        print("📊 知识库统计信息")
        print(f"{'='*80}")
        try:
            # 尝试获取知识库统计信息
            if hasattr(kms_service, 'get_statistics'):
                stats = kms_service.get_statistics()
                print(f"知识库统计: {stats}")
            else:
                print("无法获取知识库统计信息（方法不存在）")
        except Exception as e:
            print(f"获取统计信息失败: {e}")
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保知识库管理系统已正确安装")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_knowledge_query()

