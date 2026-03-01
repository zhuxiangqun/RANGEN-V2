#!/usr/bin/env python3
"""
知识检索诊断脚本 - 测试为什么推理步骤无法检索到证据
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

from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

async def test_retrieval(query: str, description: str):
    """测试单个查询的检索"""
    print(f"\n{'='*80}")
    print(f"测试查询: {description}")
    print(f"查询内容: {query}")
    print(f"{'='*80}")
    
    try:
        knowledge_agent = KnowledgeRetrievalService()
        
        # 测试检索
        result = await knowledge_agent.retrieve_knowledge(query, top_k=15)
        
        if result and result.get('knowledge'):
            knowledge_list = result['knowledge']
            print(f"✅ 检索成功: 找到 {len(knowledge_list)} 条结果")
            
            # 显示前3条结果
            for i, item in enumerate(knowledge_list[:3], 1):
                content = item.get('content', '')[:200] if isinstance(item, dict) else str(item)[:200]
                similarity = item.get('similarity', 0.0) if isinstance(item, dict) else 0.0
                print(f"\n结果 {i}:")
                print(f"  相似度: {similarity:.3f}")
                print(f"  内容: {content}...")
        else:
            print(f"❌ 检索失败: 未找到任何结果")
            print(f"  返回结果: {result}")
            
    except Exception as e:
        print(f"❌ 检索异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("="*80)
    print("知识检索诊断测试")
    print("="*80)
    
    # 测试查询列表（来自推理步骤）
    test_queries = [
        ("Who was the 15th first lady of the United States?", "步骤1: 查找第15位第一夫人"),
        ("What was the first name of the mother of the 15th first lady?", "步骤2: 查找第15位第一夫人的母亲的名字"),
        ("Who was the second assassinated president of the United States?", "步骤3: 查找第二位被暗杀的总统"),
        ("What was the maiden name of the mother of the second assassinated president?", "步骤4: 查找第二位被暗杀总统的母亲的娘家姓"),
        ("15th first lady", "简化查询1: 第15位第一夫人"),
        ("Abigail Fillmore", "简化查询2: 阿比盖尔·菲尔莫尔"),
        ("second assassinated president", "简化查询3: 第二位被暗杀的总统"),
        ("James Garfield", "简化查询4: 詹姆斯·加菲尔德"),
        ("Ballou", "简化查询5: Ballou"),
    ]
    
    for query, description in test_queries:
        await test_retrieval(query, description)
        await asyncio.sleep(0.5)  # 避免过快请求
    
    print(f"\n{'='*80}")
    print("诊断测试完成")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())

