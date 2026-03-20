#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试增强上下文工程功能
验证MCP协议、RAG基础设施和语义压缩的集成
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_protocol():
    """测试MCP协议功能"""
    print("🧪 测试MCP协议功能")
    print("=" * 50)
    
    try:
        from src.utils.mcp_protocol import get_mcp_handler, MCPContextType, MCPPriority
        
        mcp_handler = get_mcp_handler()
        
        # 创建测试上下文
        context = mcp_handler.create_context(
            context_type=MCPContextType.QUERY,
            content={
                'query': '测试查询',
                'user_id': 'test_user',
                'metadata': {'test': True}
            },
            metadata={'source': 'test'},
            priority=MCPPriority.HIGH
        )
        
        print(f"✅ 创建MCP上下文成功: {context.id}")
        
        # 获取上下文
        retrieved_context = mcp_handler.get_context(context.id)
        if retrieved_context:
            print(f"✅ 获取MCP上下文成功: {retrieved_context.content}")
        else:
            print("❌ 获取MCP上下文失败")
        
        # 获取协议统计
        stats = mcp_handler.get_protocol_stats()
        print(f"✅ MCP协议统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP协议测试失败: {e}")
        return False

async def test_rag_infrastructure():
    """测试RAG基础设施功能"""
    print("\n🧪 测试RAG基础设施功能")
    print("=" * 50)
    
    try:
        from src.utils.advanced_rag_infrastructure import get_rag_infrastructure
        
        rag = get_rag_infrastructure()
        
        # 测试查询处理
        test_query = "什么是人工智能？"
        result = await rag.process_query(test_query, user_id="test_user")
        
        print(f"✅ RAG查询处理成功")
        print(f"   查询ID: {result.query_id}")
        print(f"   答案: {result.content[:100]}...")
        print(f"   置信度: {result.confidence}")
        print(f"   生成策略: {result.generation_strategy}")
        
        # 添加用户反馈
        feedback = rag.add_feedback(
            answer_id=result.answer_id,
            user_id="test_user",
            rating=4,
            feedback_text="答案很有帮助",
            helpful=True,
            accuracy=True,
            completeness=True,
            clarity=True
        )
        
        print(f"✅ 用户反馈添加成功: {feedback.feedback_id}")
        
        # 获取性能指标
        metrics = rag.get_performance_metrics()
        print(f"✅ RAG性能指标: {metrics}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG基础设施测试失败: {e}")
        return False

async def test_semantic_compression():
    """测试语义压缩功能"""
    print("\n🧪 测试语义压缩功能")
    print("=" * 50)
    
    try:
        from src.utils.advanced_semantic_compression import (
            get_semantic_compressor, CompressionConfig, 
            CompressionStrategy, CompressionLevel
        )
        
        compressor = get_semantic_compressor()
        
        # 测试内容
        test_content = """
        人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
        人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
        可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。
        人工智能可以对人的意识、思维的信息过程的模拟。
        人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。
        """
        
        # 创建压缩配置
        config = CompressionConfig(
            strategy=CompressionStrategy.SEMANTIC_SUMMARY,
            level=CompressionLevel.MEDIUM,
            target_ratio=0.7
        )
        
        # 执行压缩
        result = await compressor.compress(test_content, config)
        
        print(f"✅ 语义压缩成功")
        print(f"   原始长度: {len(result.original_content)}")
        print(f"   压缩后长度: {len(result.compressed_content)}")
        print(f"   压缩比: {result.compression_ratio:.2f}")
        print(f"   信息保留率: {result.information_retention:.2f}")
        print(f"   质量评分: {result.quality_score:.2f}")
        print(f"   关键短语: {result.key_phrases[:5]}")
        
        # 获取压缩统计
        stats = compressor.get_compression_stats()
        print(f"✅ 压缩统计: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 语义压缩测试失败: {e}")
        return False

async def test_enhanced_context_engineering():
    """测试增强上下文工程集成功能"""
    print("\n🧪 测试增强上下文工程集成功能")
    print("=" * 50)
    
    try:
        from src.utils.enhanced_context_engineering import (
            get_enhanced_context_engineering, EnhancedContextRequest,
            process_context_query
        )
        from src.utils.advanced_semantic_compression import CompressionLevel
        
        enhanced_ctx = get_enhanced_context_engineering()
        
        # 测试1: 基本查询处理
        print("测试1: 基本查询处理")
        request1 = EnhancedContextRequest(
            query="请解释什么是机器学习",
            user_id="test_user",
            session_id="test_session"
        )
        
        response1 = await enhanced_ctx.process_enhanced_context(request1)
        
        print(f"✅ 基本查询处理成功")
        print(f"   请求ID: {response1.request_id}")
        print(f"   答案: {response1.answer[:100]}...")
        print(f"   置信度: {response1.confidence}")
        print(f"   处理时间: {response1.processing_time:.2f}秒")
        
        # 测试2: 带压缩的查询处理
        print("\n测试2: 带压缩的查询处理")
        response2 = await process_context_query(
            query="请详细解释深度学习的原理和应用",
            user_id="test_user",
            compression_level=CompressionLevel.MEDIUM
        )
        
        print(f"✅ 压缩查询处理成功")
        print(f"   压缩比: {response2.compression_ratio:.2f}")
        print(f"   信息保留率: {response2.information_retention:.2f}")
        print(f"   质量评分: {response2.quality_score:.2f}")
        
        # 测试3: 批量处理
        print("\n测试3: 批量处理")
        batch_requests = [
            EnhancedContextRequest(query="什么是神经网络"),
            EnhancedContextRequest(query="什么是自然语言处理"),
            EnhancedContextRequest(query="什么是计算机视觉")
        ]
        
        batch_responses = await enhanced_ctx.batch_process(batch_requests)
        
        print(f"✅ 批量处理成功: {len(batch_responses)}个响应")
        for i, resp in enumerate(batch_responses):
            print(f"   响应{i+1}: {resp.answer[:50]}...")
        
        # 测试4: 系统状态
        print("\n测试4: 系统状态")
        status = enhanced_ctx.get_system_status()
        print(f"✅ 系统状态获取成功")
        print(f"   总请求数: {status['performance_metrics']['total_requests']}")
        print(f"   成功率: {status['performance_metrics']['successful_requests']}")
        print(f"   平均处理时间: {status['performance_metrics']['average_processing_time']:.2f}秒")
        
        # 测试5: 学习洞察
        print("\n测试5: 学习洞察")
        insights = enhanced_ctx.get_learning_insights()
        print(f"✅ 学习洞察获取成功")
        print(f"   建议数量: {len(insights['recommendations'])}")
        for rec in insights['recommendations']:
            print(f"   - {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ 增强上下文工程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试增强上下文工程功能")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(await test_mcp_protocol())
    test_results.append(await test_rag_infrastructure())
    test_results.append(await test_semantic_compression())
    test_results.append(await test_enhanced_context_engineering())
    
    # 输出测试结果
    print("\n📊 测试结果总结")
    print("=" * 60)
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {total_tests - passed_tests}")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 所有测试通过！增强上下文工程功能正常工作。")
    else:
        print(f"\n⚠️ 有 {total_tests - passed_tests} 个测试失败，请检查相关功能。")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
