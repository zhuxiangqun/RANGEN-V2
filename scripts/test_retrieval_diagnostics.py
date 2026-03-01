#!/usr/bin/env python3
"""
检索诊断测试脚本 - 检查检索日志、服务调用、多跳查询处理
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

# 设置日志级别为DEBUG，确保能看到所有日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.utils.research_logger import log_info
from src.services.knowledge_retrieval_service import KnowledgeRetrievalService

async def test_retrieval_with_logging(query: str, description: str):
    """测试检索并检查日志输出"""
    print(f"\n{'='*80}")
    print(f"测试: {description}")
    print(f"查询: {query}")
    print(f"{'='*80}")
    
    try:
        # 确保log_info可用
        log_info(f"🔍 [测试] 开始测试检索: {query}")
        
        # 创建检索服务
        retrieval_service = KnowledgeRetrievalService()
        
        # 测试检索
        result = await retrieval_service.retrieve_knowledge(query, top_k=10)
        
        log_info(f"🔍 [测试] 检索完成: {query}")
        
        if result and result.get('knowledge'):
            knowledge_list = result['knowledge']
            print(f"✅ 检索成功: 找到 {len(knowledge_list)} 条结果")
            log_info(f"🔍 [测试] 检索成功: {len(knowledge_list)} 条结果")
            
            # 显示前3条结果
            for i, item in enumerate(knowledge_list[:3], 1):
                content = item.get('content', '')[:200] if isinstance(item, dict) else str(item)[:200]
                similarity = item.get('similarity', 0.0) if isinstance(item, dict) else 0.0
                print(f"\n结果 {i}:")
                print(f"  相似度: {similarity:.4f}")
                print(f"  内容: {content}...")
                log_info(f"🔍 [测试] 结果 {i}: 相似度={similarity:.4f}")
        else:
            print(f"❌ 检索失败: 未找到任何结果")
            log_info(f"🔍 [测试] 检索失败: 未找到任何结果")
            print(f"  返回结果: {result}")
            
    except Exception as e:
        print(f"❌ 检索异常: {e}")
        log_info(f"🔍 [测试] 检索异常: {e}")
        import traceback
        traceback.print_exc()

async def test_multi_hop_query_decomposition():
    """测试多跳查询拆解"""
    print(f"\n{'='*80}")
    print("测试多跳查询拆解")
    print(f"{'='*80}")
    
    try:
        from src.core.reasoning.evidence_processor import EvidenceProcessor
        
        processor = EvidenceProcessor()
        
        # 测试多跳查询
        multi_hop_queries = [
            "What was the first name of the mother of the 15th first lady?",
            "What is the maiden name of the second assassinated president's mother?",
        ]
        
        for query in multi_hop_queries:
            print(f"\n测试查询: {query}")
            is_multi_hop = processor._is_multi_hop_query(query)
            print(f"  是否多跳查询: {is_multi_hop}")
            
            if is_multi_hop:
                decomposed = await processor._decompose_multi_hop_query(query)
                print(f"  拆解结果: {len(decomposed)} 个步骤")
                for i, sub_query in enumerate(decomposed, 1):
                    print(f"    步骤{i}: {sub_query}")
            
    except Exception as e:
        print(f"❌ 多跳查询测试异常: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("="*80)
    print("检索诊断测试")
    print("="*80)
    
    # 测试1: 检查检索日志输出
    print("\n【测试1】检查检索日志输出")
    test_queries = [
        ("Who was the 15th first lady of the United States?", "步骤1: 查找第15位第一夫人"),
        ("What was the first name of the mother of the 15th first lady?", "步骤2: 查找第15位第一夫人的母亲的名字"),
        ("Who was the second assassinated president of the United States?", "步骤3: 查找第二位被暗杀的总统"),
    ]
    
    for query, description in test_queries:
        await test_retrieval_with_logging(query, description)
        await asyncio.sleep(0.5)
    
    # 测试2: 检查多跳查询处理
    print("\n【测试2】检查多跳查询处理")
    await test_multi_hop_query_decomposition()
    
    print(f"\n{'='*80}")
    print("诊断测试完成")
    print("请检查日志文件: research_system.log")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())

