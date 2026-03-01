#!/usr/bin/env python3
"""
诊断步骤1检索失败的原因
"""
import asyncio
import sys
import os
import logging

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

# 设置环境变量
os.environ.setdefault('PYTHONPATH', project_root)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.utils.research_logger import log_info
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

async def test_step1_queries():
    """测试步骤1相关的查询"""
    print("\n" + "="*80)
    print("诊断步骤1检索失败原因")
    print("="*80)
    
    # 步骤1的实际查询（从日志中提取）
    step1_queries = [
        "What is the first name of the 15th first lady of the United States' mother?",
        "Who was the 15th first lady of the United States?",
        "Who was the 15th first lady?",
        "15th first lady of the United States",
        "Harriet Lane",
        "James Buchanan first lady",
    ]
    
    service = KnowledgeRetrievalService()
    
    for i, query in enumerate(step1_queries, 1):
        print(f"\n{'='*80}")
        print(f"测试查询 {i}/{len(step1_queries)}: {query}")
        print(f"{'='*80}")
        
        try:
            log_info(f"🔍 [诊断] 测试查询: {query}")
            
            # 测试检索
            result = await service.retrieve_knowledge(query, top_k=20)
            
            if result and result.get('knowledge'):
                knowledge_list = result['knowledge']
                print(f"✅ 检索成功: 找到 {len(knowledge_list)} 条结果")
                log_info(f"✅ [诊断] 检索成功: {len(knowledge_list)} 条结果")
                
                # 显示前5条结果
                for j, item in enumerate(knowledge_list[:5], 1):
                    content = item.get('content', '')[:300] if isinstance(item, dict) else str(item)[:300]
                    similarity = item.get('similarity', 0.0) if isinstance(item, dict) else 0.0
                    print(f"\n结果 {j}:")
                    print(f"  相似度: {similarity:.4f}")
                    print(f"  内容: {content}...")
                    log_info(f"  结果 {j}: 相似度={similarity:.4f}, 内容={content[:100]}...")
                    
                    # 检查是否包含关键信息
                    content_lower = content.lower()
                    if 'harriet' in content_lower or 'lane' in content_lower:
                        print(f"  ✅ 包含Harriet Lane相关信息")
                    if 'jane' in content_lower:
                        print(f"  ✅ 包含Jane相关信息")
                    if '15th' in content_lower or 'fifteenth' in content_lower:
                        print(f"  ✅ 包含15th相关信息")
            else:
                print(f"❌ 检索失败: 未找到任何结果")
                log_info(f"❌ [诊断] 检索失败: 未找到任何结果")
                if result:
                    print(f"  返回结果类型: {type(result)}")
                    print(f"  返回结果keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                
        except Exception as e:
            print(f"❌ 检索异常: {e}")
            log_info(f"❌ [诊断] 检索异常: {e}")
            import traceback
            traceback.print_exc()
        
        await asyncio.sleep(0.5)  # 避免过快请求
    
    print(f"\n{'='*80}")
    print("诊断完成")
    print("请检查日志文件: research_system.log")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(test_step1_queries())

