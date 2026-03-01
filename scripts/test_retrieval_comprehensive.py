#!/usr/bin/env python3
"""
综合检索诊断测试 - 检查所有4个检查项
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

async def test_1_retrieval_logging():
    """检查1: 检查检索日志输出"""
    print("\n" + "="*80)
    print("【检查1】检查检索日志输出")
    print("="*80)
    
    try:
        from src.utils.research_logger import log_info
        from src.services.knowledge_retrieval_service import KnowledgeRetrievalService
        
        log_info("🔍 [检查1] 开始测试检索日志输出")
        print("✅ log_info函数可用")
        
        # 创建检索服务
        print("正在初始化检索服务...")
        service = KnowledgeRetrievalService()
        print("✅ 检索服务初始化成功")
        
        # 确保kms_service已初始化
        if not service.kms_service:
            print("⚠️ kms_service未初始化，尝试初始化...")
            await service._initialize_services()
        
        if not service.kms_service:
            print("❌ kms_service初始化失败，跳过测试")
            return
        
        # 测试查询
        query = "Who was the 15th first lady of the United States?"
        log_info(f"🔍 [检查1] 测试查询: {query}")
        print(f"测试查询: {query}")
        
        # 调用内部方法（直接测试检索逻辑）
        print("正在调用检索方法...")
        result = await service._get_kms_knowledge(query, {})
        
        if result:
            knowledge_count = len(result.get('knowledge', []))
            log_info(f"🔍 [检查1] 检索成功: 找到 {knowledge_count} 条结果")
            print(f"✅ 检索成功: 找到 {knowledge_count} 条结果")
        else:
            log_info(f"🔍 [检查1] 检索失败: 未找到结果")
            print(f"❌ 检索失败: 未找到结果")
        
        print("✅ 检查1完成: 请查看日志文件 research_system.log 确认日志输出")
        
    except Exception as e:
        print(f"❌ 检查1失败: {e}")
        import traceback
        traceback.print_exc()

async def test_2_retrieval_service_call():
    """检查2: 检查检索服务调用"""
    print("\n" + "="*80)
    print("【检查2】检查检索服务调用")
    print("="*80)
    
    try:
        from src.utils.unified_centers import get_unified_center
        from knowledge_management_system.api.service_interface import get_knowledge_service
        
        # 获取知识服务
        kms_service = get_knowledge_service()
        
        if not kms_service:
            print("❌ 知识服务不可用")
            return
        
        print("✅ 知识服务可用")
        
        # 测试调用
        query = "Who was the 15th first lady of the United States?"
        print(f"测试查询: {query}")
        
        results = kms_service.query_knowledge(
            query=query,
            modality="text",
            top_k=10,
            similarity_threshold=0.0,
            use_rerank=True,
            use_graph=False,
            use_llamaindex=True
        )
        
        if results:
            print(f"✅ 检索服务调用成功: 返回 {len(results)} 条结果")
            for i, result in enumerate(results[:3], 1):
                similarity = result.get('similarity', 0.0) or result.get('similarity_score', 0.0) or 0.0
                content = result.get('content', '')[:100]
                print(f"  结果{i}: 相似度={similarity:.4f}, 内容={content}...")
        else:
            print(f"❌ 检索服务调用失败: 未返回结果")
        
    except Exception as e:
        print(f"❌ 检查2失败: {e}")
        import traceback
        traceback.print_exc()

async def test_3_multi_hop_query():
    """检查3: 检查多跳查询处理"""
    print("\n" + "="*80)
    print("【检查3】检查多跳查询处理")
    print("="*80)
    
    try:
        from src.core.reasoning.evidence_processor import EvidenceProcessor
        
        processor = EvidenceProcessor()
        
        # 测试多跳查询检测
        test_queries = [
            "What was the first name of the mother of the 15th first lady?",
            "What is the maiden name of the second assassinated president's mother?",
        ]
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            is_multi_hop = processor._is_multi_hop_query(query)
            print(f"  是否多跳查询: {is_multi_hop}")
            
            if is_multi_hop:
                decomposed = await processor._decompose_multi_hop_query(query)
                print(f"  拆解结果: {len(decomposed)} 个步骤")
                for i, sub_query in enumerate(decomposed, 1):
                    print(f"    步骤{i}: {sub_query}")
        
        print("\n✅ 检查3完成")
        
    except Exception as e:
        print(f"❌ 检查3失败: {e}")
        import traceback
        traceback.print_exc()

async def test_4_direct_retrieval():
    """检查4: 直接测试检索服务"""
    print("\n" + "="*80)
    print("【检查4】直接测试检索服务")
    print("="*80)
    
    try:
        from src.utils.unified_centers import get_unified_center
        from knowledge_management_system.api.service_interface import get_knowledge_service
        
        kms_service = get_knowledge_service()
        
        if not kms_service:
            print("❌ 知识服务不可用")
            return
        
        # 测试查询列表
        test_queries = [
            "Who was the 15th first lady of the United States?",
            "Harriet Lane",
            "James Garfield",
            "Ballou",
        ]
        
        for query in test_queries:
            print(f"\n测试查询: {query}")
            
            results = kms_service.query_knowledge(
                query=query,
                modality="text",
                top_k=10,
                similarity_threshold=0.0,
                use_rerank=True,
                use_graph=False,
                use_llamaindex=True
            )
            
            if results:
                print(f"  ✅ 检索成功: {len(results)} 条结果")
                if results:
                    similarity = results[0].get('similarity', 0.0) or results[0].get('similarity_score', 0.0) or 0.0
                    print(f"  最高相似度: {similarity:.4f}")
            else:
                print(f"  ❌ 检索失败: 未找到结果")
        
        print("\n✅ 检查4完成")
        
    except Exception as e:
        print(f"❌ 检查4失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主函数"""
    print("="*80)
    print("综合检索诊断测试")
    print("="*80)
    
    # 执行所有检查
    await test_1_retrieval_logging()
    await test_2_retrieval_service_call()
    await test_3_multi_hop_query()
    await test_4_direct_retrieval()
    
    print("\n" + "="*80)
    print("所有检查完成")
    print("请查看日志文件: research_system.log")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())

