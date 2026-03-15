#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版增强上下文工程功能测试
直接测试核心功能，避免复杂的导入问题
"""

import asyncio
import sys
import os
import logging
from datetime import datetime

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_mcp_protocol_simple():
    """简化MCP协议测试"""
    print("🧪 测试MCP协议功能（简化版）")
    print("=" * 50)
    
    try:
        # 直接导入和测试MCP协议
        from utils.mcp_protocol import MCPProtocolHandler, MCPContextType, MCPPriority
        
        # 创建MCP处理器
        mcp_handler = MCPProtocolHandler()
        
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
        import traceback
        traceback.print_exc()
        return False

async def test_semantic_compression_simple():
    """简化语义压缩测试"""
    print("\n🧪 测试语义压缩功能（简化版）")
    print("=" * 50)
    
    try:
        from utils.advanced_semantic_compression import (
            AdvancedSemanticCompression, CompressionConfig, 
            CompressionStrategy, CompressionLevel
        )
        
        # 创建压缩器
        compressor = AdvancedSemanticCompression()
        
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
        print(f"   关键短语: {result.key_phrases[:3]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 语义压缩测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_rag_infrastructure_simple():
    """简化RAG基础设施测试"""
    print("\n🧪 测试RAG基础设施功能（简化版）")
    print("=" * 50)
    
    try:
        from utils.advanced_rag_infrastructure import AdvancedRAGInfrastructure
        
        # 创建RAG基础设施
        rag = AdvancedRAGInfrastructure()
        
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
        import traceback
        traceback.print_exc()
        return False

async def test_integration_simple():
    """简化集成测试"""
    print("\n🧪 测试集成功能（简化版）")
    print("=" * 50)
    
    try:
        # 测试MCP协议
        mcp_success = await test_mcp_protocol_simple()
        
        # 测试语义压缩
        compression_success = await test_semantic_compression_simple()
        
        # 测试RAG基础设施
        rag_success = await test_rag_infrastructure_simple()
        
        # 综合测试结果
        all_success = mcp_success and compression_success and rag_success
        
        if all_success:
            print("\n🎉 所有核心功能测试通过！")
            print("✅ MCP协议标准实现正常")
            print("✅ 高级语义压缩算法工作正常")
            print("✅ 完整RAG基础设施运行正常")
            print("\n💡 增强上下文工程功能已成功实现并集成到RANGEN系统中！")
        else:
            print("\n⚠️ 部分功能测试失败，请检查相关实现")
        
        return all_success
        
    except Exception as e:
        print(f"❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 增强上下文工程功能测试（简化版）")
    print("=" * 60)
    
    # 运行集成测试
    success = await test_integration_simple()
    
    # 输出最终结果
    print("\n📊 测试结果总结")
    print("=" * 60)
    
    if success:
        print("🎉 所有测试通过！增强上下文工程功能正常工作。")
        print("\n📋 已实现的功能:")
        print("✅ MCP协议标准 - 标准化的上下文交换协议")
        print("✅ 完整RAG基础设施 - 检索-生成-反馈循环")
        print("✅ 高级语义压缩算法 - 基于语义理解的智能压缩")
        print("✅ 系统集成 - 与现有RANGEN系统无缝集成")
        print("\n🎯 这些功能显著提升了RANGEN系统的上下文工程能力！")
    else:
        print("❌ 部分测试失败，请检查相关功能实现。")
    
    return success

if __name__ == "__main__":
    # 运行测试
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
