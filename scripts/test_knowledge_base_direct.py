#!/usr/bin/env python3
"""
直接测试知识库查询 - 检查知识库内容和检索参数
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

# 设置环境变量
os.environ.setdefault('PYTHONPATH', project_root)

from src.utils.unified_centers import get_unified_center
from knowledge_management_system.api.service_interface import get_knowledge_service

async def test_knowledge_base_query(query: str, description: str):
    """直接测试知识库查询"""
    print(f"\n{'='*80}")
    print(f"测试查询: {description}")
    print(f"查询内容: {query}")
    print(f"{'='*80}")
    
    try:
        # 获取知识服务
        kms_service = get_knowledge_service()
        
        # 测试检索（使用不同的参数）
        test_configs = [
            {"top_k": 10, "similarity_threshold": 0.0, "use_rerank": True, "use_graph": False},
            {"top_k": 20, "similarity_threshold": 0.0, "use_rerank": True, "use_graph": False},
            {"top_k": 30, "similarity_threshold": 0.0, "use_rerank": True, "use_graph": False},
        ]
        
        for i, config in enumerate(test_configs, 1):
            print(f"\n--- 配置 {i}: top_k={config['top_k']}, threshold={config['similarity_threshold']} ---")
            
            results = kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=config['top_k'],
                similarity_threshold=config['similarity_threshold'],
                use_rerank=config['use_rerank'],
                use_graph=config['use_graph'],
                use_llamaindex=True
            )
            
            if results and len(results) > 0:
                print(f"✅ 检索成功: 找到 {len(results)} 条结果")
                
                # 显示前5条结果
                for j, result in enumerate(results[:5], 1):
                    content = result.get('content', '') or result.get('text', '')
                    similarity = result.get('similarity', 0.0) or result.get('similarity_score', 0.0) or 0.0
                    print(f"\n结果 {j}:")
                    print(f"  相似度: {similarity:.4f}")
                    print(f"  内容: {content[:200]}...")
            else:
                print(f"❌ 检索失败: 未找到任何结果")
                
    except Exception as e:
        print(f"❌ 检索异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("="*80)
    print("知识库内容和检索参数检查")
    print("="*80)
    
    # 测试查询列表（来自推理步骤）
    test_queries = [
        ("Who was the 15th first lady of the United States?", "步骤1: 查找第15位第一夫人"),
        ("What was the first name of the mother of the 15th first lady?", "步骤2: 查找第15位第一夫人的母亲的名字"),
        ("Who was the second assassinated president of the United States?", "步骤3: 查找第二位被暗杀的总统"),
        ("What was the maiden name of the mother of the second assassinated president?", "步骤4: 查找第二位被暗杀总统的母亲的娘家姓"),
        ("Harriet Lane", "简化查询1: Harriet Lane"),
        ("James Garfield", "简化查询2: James Garfield"),
        ("Ballou", "简化查询3: Ballou"),
    ]
    
    for query, description in test_queries:
        await test_knowledge_base_query(query, description)
        await asyncio.sleep(0.5)  # 避免过快请求
    
    print(f"\n{'='*80}")
    print("检查完成")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())

