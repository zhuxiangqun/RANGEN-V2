#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN系统完整使用示例
展示所有核心功能的使用方法和最佳实践
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, List, Any

# 添加src到路径
sys.path.insert(0, 'src')

# 导入核心模块
from utils.enhanced_system_integration import (
    get_enhanced_system_integration, process_query, get_system_capabilities
)
from utils.system_health_checker import run_system_health_check
from utils.system_monitor_optimizer import get_system_monitor, start_system_monitoring
from utils.mcp_protocol import get_mcp_handler, MCPContextType, MCPPriority
from utils.advanced_rag_infrastructure import get_rag_infrastructure
from utils.advanced_semantic_compression import (
    get_semantic_compressor, CompressionConfig, CompressionStrategy, CompressionLevel
)
from utils.enhanced_context_engineering import (
    get_enhanced_context_engineering, EnhancedContextRequest
)

class RANGENUsageExamples:
    """RANGEN系统使用示例类"""
    
    def __init__(self):
        self.integration = get_enhanced_system_integration()
        self.mcp_handler = get_mcp_handler()
        self.rag_infrastructure = get_rag_infrastructure()
        self.semantic_compressor = get_semantic_compressor()
        self.enhanced_context_engineering = get_enhanced_context_engineering()
        
    async def example_1_basic_query_processing(self):
        """示例1: 基础查询处理"""
        print("🔍 示例1: 基础查询处理")
        print("-" * 50)
        
        # 简单查询
        simple_query = "什么是人工智能？"
        print(f"查询: {simple_query}")
        
        response = await process_query(
            query=simple_query,
            user_id="example_user_1",
            use_enhanced_features=True
        )
        
        if response['success']:
            print(f"✅ 答案: {response['answer'][:100]}...")
            print(f"📊 置信度: {response['confidence']:.2f}")
            print(f"⏱️ 处理时间: {response['processing_time']:.3f}秒")
        else:
            print(f"❌ 处理失败: {response.get('error', '未知错误')}")
        
        print()
    
    async def example_2_complex_reasoning(self):
        """示例2: 复杂逻辑推理"""
        print("🧠 示例2: 复杂逻辑推理")
        print("-" * 50)
        
        complex_queries = [
            "If A is taller than B, and B is taller than C, who is the tallest?",
            "What is the capital of the country that has the largest population?",
            "Explain the relationship between machine learning and artificial intelligence",
            "How would you solve this puzzle: A farmer has 17 sheep, all but 9 die. How many are left?"
        ]
        
        for i, query in enumerate(complex_queries, 1):
            print(f"推理问题 {i}: {query}")
            
            response = await process_query(
                query=query,
                user_id=f"reasoning_user_{i}",
                use_enhanced_features=True
            )
            
            if response['success']:
                print(f"  ✅ 推理结果: {response['answer'][:150]}...")
                print(f"  📊 置信度: {response['confidence']:.2f}")
            else:
                print(f"  ❌ 推理失败: {response.get('error', '未知错误')}")
            print()
    
    async def example_3_context_management(self):
        """示例3: 上下文管理"""
        print("📝 示例3: 上下文管理")
        print("-" * 50)
        
        # 创建MCP上下文
        context = self.mcp_handler.create_context(
            context_type=MCPContextType.QUERY,
            content={
                'query': '请解释量子计算',
                'user_id': 'context_user',
                'session_id': 'session_123'
            },
            priority=MCPPriority.HIGH
        )
        
        print(f"✅ 创建上下文: {context.id}")
        print(f"📋 上下文类型: {context.type.value}")
        print(f"⚡ 优先级: {context.priority.value}")
        
        # 更新上下文
        updated = self.mcp_handler.update_context(
            context.id,
            {'additional_info': '用户对量子计算很感兴趣'}
        )
        
        if updated:
            print("✅ 上下文更新成功")
        
        # 获取上下文
        retrieved_context = self.mcp_handler.get_context(context.id)
        if retrieved_context:
            print(f"📖 检索上下文: {retrieved_context.content}")
        
        print()
    
    async def example_4_rag_infrastructure(self):
        """示例4: RAG基础设施使用"""
        print("🔍 示例4: RAG基础设施使用")
        print("-" * 50)
        
        # 处理RAG查询
        rag_query = "请详细解释深度学习的原理和应用"
        print(f"RAG查询: {rag_query}")
        
        result = await self.rag_infrastructure.process_query(
            query=rag_query,
            user_id="rag_user",
            context={'domain': 'machine_learning'}
        )
        
        print(f"✅ 查询ID: {result.query_id}")
        print(f"📄 答案: {result.content[:200]}...")
        print(f"📊 置信度: {result.confidence:.2f}")
        print(f"🔧 生成策略: {result.generation_strategy}")
        print(f"📚 检索文档数: {len(result.source_documents)}")
        
        # 获取性能指标
        metrics = self.rag_infrastructure.get_performance_metrics()
        print(f"📈 总查询数: {metrics['total_queries']}")
        print(f"✅ 成功查询数: {metrics['successful_queries']}")
        print(f"⏱️ 平均响应时间: {metrics['average_response_time']:.3f}秒")
        
        print()
    
    async def example_5_semantic_compression(self):
        """示例5: 语义压缩"""
        print("🗜️ 示例5: 语义压缩")
        print("-" * 50)
        
        # 长文本内容
        long_content = """
        人工智能（Artificial Intelligence，简称AI）是计算机科学的一个分支，
        它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
        
        人工智能从诞生以来，理论和技术日益成熟，应用领域也不断扩大。
        可以设想，未来人工智能带来的科技产品，将会是人类智慧的"容器"。
        人工智能可以对人的意识、思维的信息过程的模拟。
        人工智能不是人的智能，但能像人那样思考、也可能超过人的智能。
        
        深度学习是机器学习的一个子领域，它基于人工神经网络，特别是深层神经网络。
        深度学习已经在图像识别、语音识别、自然语言处理等领域取得了突破性进展。
        """
        
        print(f"📄 原始内容长度: {len(long_content)} 字符")
        
        # 创建压缩配置
        config = CompressionConfig(
            strategy=CompressionStrategy.SEMANTIC_SUMMARY,
            level=CompressionLevel.MEDIUM,
            target_ratio=0.6
        )
        
        # 执行压缩
        result = await self.semantic_compressor.compress(long_content, config)
        
        print(f"✅ 压缩后长度: {len(result.compressed_content)} 字符")
        print(f"📊 压缩比: {result.compression_ratio:.2f}")
        print(f"💾 信息保留率: {result.information_retention:.2f}")
        print(f"⭐ 质量评分: {result.quality_score:.2f}")
        print(f"📝 压缩内容: {result.compressed_content[:200]}...")
        
        # 获取压缩统计
        stats = self.semantic_compressor.get_compression_stats()
        print(f"📈 总压缩次数: {stats.get('total_compressions', 0)}")
        print(f"📊 平均压缩比: {stats.get('avg_compression_ratio', 0):.2f}")
        
        print()
    
    async def example_6_enhanced_context_engineering(self):
        """示例6: 增强上下文工程"""
        print("🔧 示例6: 增强上下文工程")
        print("-" * 50)
        
        # 创建增强上下文请求
        request = EnhancedContextRequest(
            query="请分析一下当前人工智能技术的发展趋势",
            user_id="context_eng_user",
            context_type=MCPContextType.QUERY,
            priority=MCPPriority.HIGH,
            metadata={
                'domain': 'artificial_intelligence',
                'complexity': 'high',
                'requires_reasoning': True
            }
        )
        
        print(f"📝 查询: {request.query}")
        print(f"👤 用户ID: {request.user_id}")
        print(f"📋 上下文类型: {request.context_type.value}")
        print(f"⚡ 优先级: {request.priority.value}")
        
        # 处理增强上下文请求
        response = await self.enhanced_context_engineering.process_enhanced_context(request)
        
        print(f"✅ 请求ID: {response.request_id}")
        print(f"📄 答案: {response.answer[:200]}...")
        print(f"📊 置信度: {response.confidence:.2f}")
        print(f"🗜️ 压缩比: {response.compression_ratio:.2f}")
        print(f"⭐ 质量评分: {response.quality_score:.2f}")
        print(f"⏱️ 处理时间: {response.processing_time:.3f}秒")
        
        print()
    
    async def example_7_system_monitoring(self):
        """示例7: 系统监控"""
        print("📊 示例7: 系统监控")
        print("-" * 50)
        
        # 启动系统监控
        monitor = get_system_monitor()
        monitor.start_monitoring()
        
        print("✅ 系统监控已启动")
        
        # 模拟一些查询以生成监控数据
        for i in range(5):
            response = await process_query(
                query=f"监控测试查询 {i+1}",
                user_id=f"monitor_user_{i+1}",
                use_enhanced_features=True
            )
            
            # 记录查询到监控系统
            monitor.record_query({
                'success': response['success'],
                'response_time': response['processing_time'],
                'confidence': response.get('confidence', 0)
            })
        
        # 获取当前状态
        status = monitor.get_current_status()
        print(f"📊 当前系统状态:")
        print(f"  CPU使用率: {status['current_metrics']['cpu_usage']:.1f}%")
        print(f"  内存使用率: {status['current_metrics']['memory_usage']:.1f}%")
        print(f"  查询数量: {status['current_metrics']['query_count']}")
        print(f"  成功率: {status['current_metrics']['success_rate']:.1f}%")
        print(f"  平均响应时间: {status['current_metrics']['avg_response_time']:.3f}秒")
        
        # 获取性能趋势
        trends = monitor.get_performance_trends(hours=1)
        if 'error' not in trends:
            print(f"📈 性能趋势 (最近1小时):")
            print(f"  CPU平均: {trends['cpu_trend']['average']:.1f}%")
            print(f"  内存平均: {trends['memory_trend']['average']:.1f}%")
            print(f"  响应时间平均: {trends['response_time_trend']['average']:.3f}秒")
        
        # 获取优化建议
        recommendations = monitor.get_optimization_recommendations()
        if recommendations:
            print(f"💡 优化建议:")
            for rec in recommendations:
                print(f"  - {rec['message']}")
        else:
            print("✅ 系统运行良好，无需特殊优化")
        
        print()
    
    async def example_8_system_health_check(self):
        """示例8: 系统健康检查"""
        print("🏥 示例8: 系统健康检查")
        print("-" * 50)
        
        # 运行健康检查
        health_report = await run_system_health_check()
        
        print(f"📊 系统健康状态: {health_report.overall_status.value.upper()}")
        print(f"📋 总检查项: {health_report.total_checks}")
        print(f"✅ 健康项: {health_report.healthy_checks}")
        print(f"⚠️ 警告项: {health_report.warning_checks}")
        print(f"❌ 严重项: {health_report.critical_checks}")
        
        # 显示详细结果
        print(f"\n📋 详细检查结果:")
        for result in health_report.check_results:
            status_icon = {
                'healthy': '✅',
                'warning': '⚠️',
                'critical': '❌',
                'unknown': '❓'
            }.get(result.status.value, '❓')
            
            print(f"  {status_icon} {result.component}: {result.message}")
        
        # 显示建议
        if health_report.recommendations:
            print(f"\n💡 系统建议:")
            for recommendation in health_report.recommendations:
                print(f"  - {recommendation}")
        
        print()
    
    async def example_9_system_capabilities(self):
        """示例9: 系统能力概览"""
        print("🎯 示例9: 系统能力概览")
        print("-" * 50)
        
        # 获取系统能力
        capabilities = get_system_capabilities()
        
        # ML/RL能力
        ml_rl = capabilities['ml_rl_capabilities']
        print("🤖 ML和RL协同能力:")
        print(f"  机器学习组件: {len([k for k, v in ml_rl['machine_learning'].items() if v])}/6 项")
        print(f"  强化学习组件: {len([k for k, v in ml_rl['reinforcement_learning'].items() if v])}/6 项")
        print(f"  协同机制: {len([k for k, v in ml_rl['synergy'].items() if v])}/4 项")
        
        # 上下文工程能力
        context_eng = capabilities['context_engineering_capabilities']
        print("\n📝 上下文工程能力:")
        print(f"  提示词工程: {len([k for k, v in context_eng['prompt_engineering'].items() if v])}/4 项")
        print(f"  上下文管理: {len([k for k, v in context_eng['context_management'].items() if v])}/5 项")
        print(f"  协同机制: {len([k for k, v in context_eng['synergy'].items() if v])}/3 项")
        
        # 推理能力
        reasoning = capabilities['reasoning_capabilities']
        print("\n🧠 推理能力:")
        print(f"  推理类型: {len([k for k, v in reasoning['reasoning_types'].items() if v])}/5 种")
        print(f"  推理引擎: {len([k for k, v in reasoning['reasoning_engines'].items() if v])}/4 个")
        print(f"  核心能力: {len([k for k, v in reasoning['capabilities'].items() if v])}/4 项")
        
        # 查询处理流程
        workflow = capabilities['query_processing_workflow']
        print("\n🔄 查询处理流程:")
        print(f"  处理阶段: {len(workflow['workflow_stages'])}/6 个")
        print(f"  增强功能: {len(workflow['enhanced_features'])}/4 项")
        
        print()
    
    async def example_10_batch_processing(self):
        """示例10: 批量处理"""
        print("📦 示例10: 批量处理")
        print("-" * 50)
        
        # 批量查询
        batch_queries = [
            "什么是机器学习？",
            "解释深度学习的基本概念",
            "人工智能在医疗领域的应用",
            "自然语言处理的发展历程",
            "计算机视觉的主要技术"
        ]
        
        print(f"📋 批量处理 {len(batch_queries)} 个查询")
        
        # 并发处理
        tasks = []
        for i, query in enumerate(batch_queries):
            task = process_query(
                query=query,
                user_id=f"batch_user_{i+1}",
                use_enhanced_features=True
            )
            tasks.append(task)
        
        # 等待所有任务完成
        start_time = datetime.now()
        results = await asyncio.gather(*tasks)
        end_time = datetime.now()
        
        # 统计结果
        successful_results = [r for r in results if r['success']]
        total_time = (end_time - start_time).total_seconds()
        
        print(f"✅ 成功处理: {len(successful_results)}/{len(batch_queries)}")
        print(f"⏱️ 总处理时间: {total_time:.3f}秒")
        print(f"📊 平均处理时间: {total_time/len(batch_queries):.3f}秒/查询")
        print(f"🚀 处理速度: {len(batch_queries)/total_time:.1f} 查询/秒")
        
        # 显示部分结果
        print(f"\n📄 部分结果:")
        for i, result in enumerate(successful_results[:3]):
            print(f"  {i+1}. {result['answer'][:100]}...")
            print(f"     置信度: {result['confidence']:.2f}")
        
        print()
    
    async def run_all_examples(self):
        """运行所有示例"""
        print("🚀 RANGEN系统完整使用示例")
        print("=" * 60)
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # 运行所有示例
            await self.example_1_basic_query_processing()
            await self.example_2_complex_reasoning()
            await self.example_3_context_management()
            await self.example_4_rag_infrastructure()
            await self.example_5_semantic_compression()
            await self.example_6_enhanced_context_engineering()
            await self.example_7_system_monitoring()
            await self.example_8_system_health_check()
            await self.example_9_system_capabilities()
            await self.example_10_batch_processing()
            
            print("🎉 所有示例运行完成！")
            print(f"⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
        except Exception as e:
            print(f"❌ 示例运行失败: {e}")
            import traceback
            traceback.print_exc()

async def main():
    """主函数"""
    examples = RANGENUsageExamples()
    await examples.run_all_examples()

if __name__ == "__main__":
    asyncio.run(main())
