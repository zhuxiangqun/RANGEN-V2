#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强上下文工程集成示例
展示如何将新功能集成到现有的RANGEN系统中
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加src目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def integrate_with_existing_system():
    """与现有系统集成示例"""
    print("🔗 增强上下文工程与现有RANGEN系统集成示例")
    print("=" * 60)
    
    try:
        # 1. 导入现有系统组件
        from utils.unified_centers import get_unified_center
        from agents.base_agent import BaseAgent
        from utils.enhanced_context_engineering import (
            get_enhanced_context_engineering, EnhancedContextRequest
        )
        from utils.advanced_semantic_compression import (
            CompressionConfig, CompressionStrategy, CompressionLevel
        )
        
        print("✅ 成功导入现有系统组件")
        
        # 2. 创建增强上下文工程实例
        enhanced_ctx = get_enhanced_context_engineering()
        print("✅ 增强上下文工程实例创建成功")
        
        # 3. 模拟现有系统的查询处理
        print("\n📝 模拟现有系统查询处理流程")
        print("-" * 40)
        
        # 创建基础智能体
        base_agent = BaseAgent("EnhancedAgent")
        print(f"✅ 创建基础智能体: {base_agent.agent_name}")
        
        # 处理查询
        query = "请详细解释RANGEN系统的架构和核心功能"
        print(f"📋 处理查询: {query}")
        
        # 使用基础智能体处理
        basic_result = base_agent.process_query(query)
        print(f"✅ 基础智能体处理结果: {basic_result['result']}")
        
        # 4. 使用增强上下文工程处理相同查询
        print("\n🚀 使用增强上下文工程处理相同查询")
        print("-" * 40)
        
        # 创建增强请求
        enhanced_request = EnhancedContextRequest(
            query=query,
            user_id="integration_test_user",
            session_id="integration_session_001",
            compression_config=CompressionConfig(
                strategy=CompressionStrategy.SEMANTIC_SUMMARY,
                level=CompressionLevel.MEDIUM,
                target_ratio=0.7,
                preserve_structure=True,
                preserve_keywords=True,
                preserve_entities=True
            ),
            metadata={
                'integration_test': True,
                'original_agent': 'BaseAgent',
                'enhancement_level': 'full'
            }
        )
        
        # 处理增强请求
        enhanced_response = await enhanced_ctx.process_enhanced_context(enhanced_request)
        
        print(f"✅ 增强上下文工程处理结果:")
        print(f"   请求ID: {enhanced_response.request_id}")
        print(f"   答案长度: {len(enhanced_response.answer)}")
        print(f"   置信度: {enhanced_response.confidence:.2f}")
        print(f"   压缩比: {enhanced_response.compression_ratio:.2f}")
        print(f"   信息保留率: {enhanced_response.information_retention:.2f}")
        print(f"   质量评分: {enhanced_response.quality_score:.2f}")
        print(f"   处理时间: {enhanced_response.processing_time:.3f}秒")
        
        # 5. 对比处理结果
        print("\n📊 处理结果对比")
        print("-" * 40)
        
        print(f"基础智能体结果: {basic_result['result']}")
        print(f"增强上下文工程结果: {enhanced_response.answer[:100]}...")
        
        # 6. 展示系统状态
        print("\n📈 系统状态监控")
        print("-" * 40)
        
        status = enhanced_ctx.get_system_status()
        print(f"总请求数: {status['performance_metrics']['total_requests']}")
        print(f"成功请求数: {status['performance_metrics']['successful_requests']}")
        print(f"平均处理时间: {status['performance_metrics']['average_processing_time']:.3f}秒")
        print(f"平均质量评分: {status['performance_metrics']['average_quality_score']:.2f}")
        
        # 7. 展示学习洞察
        print("\n🧠 学习洞察")
        print("-" * 40)
        
        insights = enhanced_ctx.get_learning_insights()
        print(f"RAG学习指标: {insights['rag_learning']}")
        print(f"压缩学习指标: {insights['compression_learning']}")
        print(f"优化建议: {insights['recommendations']}")
        
        # 8. 模拟用户反馈
        print("\n👥 模拟用户反馈")
        print("-" * 40)
        
        await enhanced_ctx.add_user_feedback(
            response_id=enhanced_response.request_id,
            user_id="integration_test_user",
            rating=5,
            feedback_text="答案非常详细和准确，很有帮助",
            helpful=True,
            accuracy=True,
            completeness=True,
            clarity=True
        )
        print("✅ 用户反馈添加成功")
        
        # 9. 展示MCP协议集成
        print("\n🔌 MCP协议集成")
        print("-" * 40)
        
        mcp_status = status['mcp_status']
        print(f"MCP上下文总数: {mcp_status['total_contexts']}")
        print(f"MCP消息总数: {mcp_status['total_messages']}")
        print(f"上下文类型分布: {mcp_status['context_types']}")
        print(f"优先级分布: {mcp_status['priorities']}")
        
        # 10. 展示RAG基础设施集成
        print("\n🔍 RAG基础设施集成")
        print("-" * 40)
        
        rag_status = status['rag_status']
        print(f"RAG查询总数: {rag_status['total_queries']}")
        print(f"成功查询数: {rag_status['successful_queries']}")
        print(f"平均响应时间: {rag_status['average_response_time']:.3f}秒")
        print(f"生成质量: {rag_status['generation_quality']:.2f}")
        
        # 11. 展示语义压缩集成
        print("\n🗜️ 语义压缩集成")
        print("-" * 40)
        
        compression_status = status['compression_status']
        print(f"压缩操作总数: {compression_status['total_compressions']}")
        print(f"平均压缩比: {compression_status['avg_compression_ratio']:.2f}")
        print(f"平均信息保留率: {compression_status['avg_information_retention']:.2f}")
        print(f"平均质量评分: {compression_status['avg_quality_score']:.2f}")
        print(f"缓存大小: {compression_status['cache_size']}")
        
        print("\n🎉 集成示例完成！增强上下文工程成功集成到现有RANGEN系统中。")
        
        return True
        
    except Exception as e:
        print(f"❌ 集成示例失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def performance_comparison():
    """性能对比示例"""
    print("\n⚡ 性能对比示例")
    print("=" * 60)
    
    try:
        from utils.enhanced_context_engineering import process_context_query
        from utils.advanced_semantic_compression import CompressionLevel
        import time
        
        # 测试查询
        test_queries = [
            "什么是人工智能？",
            "请解释机器学习的原理",
            "深度学习和传统机器学习的区别是什么？",
            "自然语言处理有哪些应用？",
            "计算机视觉的发展趋势如何？"
        ]
        
        print(f"📋 测试查询数量: {len(test_queries)}")
        
        # 测试无压缩处理
        print("\n🔍 测试无压缩处理")
        start_time = time.time()
        
        no_compression_results = []
        for query in test_queries:
            response = await process_context_query(
                query=query,
                user_id="perf_test_user",
                compression_level=None  # 无压缩
            )
            no_compression_results.append(response)
        
        no_compression_time = time.time() - start_time
        
        # 测试中度压缩处理
        print("🗜️ 测试中度压缩处理")
        start_time = time.time()
        
        medium_compression_results = []
        for query in test_queries:
            response = await process_context_query(
                query=query,
                user_id="perf_test_user",
                compression_level=CompressionLevel.MEDIUM
            )
            medium_compression_results.append(response)
        
        medium_compression_time = time.time() - start_time
        
        # 测试重度压缩处理
        print("🔥 测试重度压缩处理")
        start_time = time.time()
        
        aggressive_compression_results = []
        for query in test_queries:
            response = await process_context_query(
                query=query,
                user_id="perf_test_user",
                compression_level=CompressionLevel.AGGRESSIVE
            )
            aggressive_compression_results.append(response)
        
        aggressive_compression_time = time.time() - start_time
        
        # 计算统计信息
        print("\n📊 性能对比结果")
        print("-" * 40)
        
        print(f"无压缩处理时间: {no_compression_time:.3f}秒")
        print(f"中度压缩处理时间: {medium_compression_time:.3f}秒")
        print(f"重度压缩处理时间: {aggressive_compression_time:.3f}秒")
        
        # 计算平均质量评分
        no_compression_avg_quality = sum(r.quality_score for r in no_compression_results) / len(no_compression_results)
        medium_compression_avg_quality = sum(r.quality_score for r in medium_compression_results) / len(medium_compression_results)
        aggressive_compression_avg_quality = sum(r.quality_score for r in aggressive_compression_results) / len(aggressive_compression_results)
        
        print(f"\n平均质量评分:")
        print(f"无压缩: {no_compression_avg_quality:.2f}")
        print(f"中度压缩: {medium_compression_avg_quality:.2f}")
        print(f"重度压缩: {aggressive_compression_avg_quality:.2f}")
        
        # 计算平均压缩比
        medium_compression_avg_ratio = sum(r.compression_ratio for r in medium_compression_results if r.compression_ratio) / len([r for r in medium_compression_results if r.compression_ratio])
        aggressive_compression_avg_ratio = sum(r.compression_ratio for r in aggressive_compression_results if r.compression_ratio) / len([r for r in aggressive_compression_results if r.compression_ratio])
        
        print(f"\n平均压缩比:")
        print(f"中度压缩: {medium_compression_avg_ratio:.2f}")
        print(f"重度压缩: {aggressive_compression_avg_ratio:.2f}")
        
        # 计算平均信息保留率
        medium_compression_avg_retention = sum(r.information_retention for r in medium_compression_results if r.information_retention) / len([r for r in medium_compression_results if r.information_retention])
        aggressive_compression_avg_retention = sum(r.information_retention for r in aggressive_compression_results if r.information_retention) / len([r for r in aggressive_compression_results if r.information_retention])
        
        print(f"\n平均信息保留率:")
        print(f"中度压缩: {medium_compression_avg_retention:.2f}")
        print(f"重度压缩: {aggressive_compression_avg_retention:.2f}")
        
        print("\n✅ 性能对比完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 性能对比失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    print("🚀 增强上下文工程集成示例")
    print("=" * 60)
    
    # 运行集成示例
    integration_success = await integrate_with_existing_system()
    
    # 运行性能对比
    performance_success = await performance_comparison()
    
    # 输出总结
    print("\n📋 示例总结")
    print("=" * 60)
    
    if integration_success and performance_success:
        print("🎉 所有示例运行成功！")
        print("✅ 增强上下文工程已成功集成到RANGEN系统")
        print("✅ 性能对比测试完成")
        print("\n💡 建议:")
        print("- 根据实际需求选择合适的压缩级别")
        print("- 定期监控系统性能和学习洞察")
        print("- 积极收集用户反馈以优化系统")
    else:
        print("⚠️ 部分示例运行失败，请检查相关功能")
    
    return integration_success and performance_success

if __name__ == "__main__":
    # 运行示例
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
