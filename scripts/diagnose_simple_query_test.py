#!/usr/bin/env python3
"""
诊断 Simple 查询快速路径测试错误
分析日志并找出失败原因
"""

import sys
import re
from pathlib import Path

def analyze_test_logs():
    """分析测试日志"""
    print("=" * 80)
    print("🔍 Simple 查询快速路径测试诊断")
    print("=" * 80)
    
    # 常见错误模式
    error_patterns = {
        "知识检索失败": [
            r"⚠️ \[快速路径\] 知识检索失败",
            r"KnowledgeRetrievalService.*失败",
            r"知识检索服务.*错误"
        ],
        "未检索到知识": [
            r"⚠️ \[快速路径\] 未检索到知识",
            r"检索到 0 条知识"
        ],
        "LLM调用失败": [
            r"⚠️ \[快速路径\] LLM调用失败",
            r"LLM.*错误",
            r"API.*错误",
            r"timeout",
            r"Connection.*error"
        ],
        "LLM返回空答案": [
            r"⚠️ \[快速路径\] LLM返回空答案"
        ],
        "回退到完整序列": [
            r"⚠️ \[快速路径\] 回退到完整智能体序列",
            r"回退到完整智能体序列"
        ],
        "状态字段缺失": [
            r"KeyError",
            r"AttributeError.*state",
            r"缺少.*字段"
        ],
        "超时": [
            r"TimeoutError",
            r"测试超时",
            r"asyncio\.TimeoutError"
        ]
    }
    
    print("\n📋 常见错误类型和解决方案：")
    print("-" * 80)
    
    for error_type, patterns in error_patterns.items():
        print(f"\n🔴 {error_type}:")
        print(f"   模式: {', '.join(patterns[:2])}...")
        
        if error_type == "知识检索失败":
            print("   💡 可能原因:")
            print("      - 知识库未初始化或为空")
            print("      - 向量数据库连接失败")
            print("      - 检索服务配置错误")
            print("   🔧 解决方案:")
            print("      - 检查知识库是否已构建: python scripts/build_vector_knowledge_base.sh")
            print("      - 检查向量数据库连接配置")
            print("      - 查看 KnowledgeRetrievalService 日志")
        
        elif error_type == "未检索到知识":
            print("   💡 可能原因:")
            print("      - 查询与知识库内容不匹配")
            print("      - 检索阈值设置过高")
            print("      - 知识库内容不足")
            print("   🔧 解决方案:")
            print("      - 检查知识库内容: python scripts/test_knowledge_query.py")
            print("      - 降低检索阈值")
            print("      - 使用更通用的查询测试")
        
        elif error_type == "LLM调用失败":
            print("   💡 可能原因:")
            print("      - API密钥未设置或无效")
            print("      - 网络连接问题")
            print("      - API限流或超时")
            print("   🔧 解决方案:")
            print("      - 检查环境变量: echo $DEEPSEEK_API_KEY")
            print("      - 检查网络连接")
            print("      - 查看 LLMIntegration 日志")
        
        elif error_type == "LLM返回空答案":
            print("   💡 可能原因:")
            print("      - LLM返回格式异常")
            print("      - 提示词问题")
            print("   🔧 解决方案:")
            print("      - 检查 LLM 返回内容")
            print("      - 优化提示词")
        
        elif error_type == "回退到完整序列":
            print("   💡 说明:")
            print("      - 快速路径失败，系统自动回退到完整智能体序列")
            print("      - 这是正常的容错机制")
            print("   🔧 解决方案:")
            print("      - 检查快速路径失败的具体原因（见上方）")
            print("      - 如果回退成功，测试仍然可以通过")
        
        elif error_type == "状态字段缺失":
            print("   💡 可能原因:")
            print("      - 测试状态缺少必需字段")
            print("      - 状态结构不匹配")
            print("   🔧 解决方案:")
            print("      - 检查 initial_state 是否包含所有必需字段")
            print("      - 查看 ResearchSystemState 定义")
        
        elif error_type == "超时":
            print("   💡 可能原因:")
            print("      - 网络延迟")
            print("      - LLM API响应慢")
            print("      - 知识检索耗时过长")
            print("   🔧 解决方案:")
            print("      - 增加超时时间（已设置为5分钟）")
            print("      - 检查网络连接")
            print("      - 使用更快的LLM模型")
    
    print("\n" + "=" * 80)
    print("📝 诊断步骤：")
    print("=" * 80)
    print("1. 运行测试并查看详细日志:")
    print("   pytest tests/test_chief_agent_unified_architecture.py::TestChiefAgentUnifiedArchitecture::test_simple_query_fast_path -v -s")
    print()
    print("2. 检查关键日志信息:")
    print("   - 查找 '⚡ [快速路径]' 日志")
    print("   - 查找 '⚠️' 警告信息")
    print("   - 查找 '❌' 错误信息")
    print()
    print("3. 验证知识库:")
    print("   python scripts/test_knowledge_query.py")
    print()
    print("4. 验证LLM配置:")
    print("   python -c \"import os; print('API Key:', 'SET' if os.getenv('DEEPSEEK_API_KEY') else 'NOT SET')\"")
    print()
    print("5. 单独测试快速路径:")
    print("   python -c \"")
    print("   import asyncio")
    print("   from src.services.knowledge_retrieval_service import KnowledgeRetrievalService")
    print("   service = KnowledgeRetrievalService()")
    print("   result = asyncio.run(service.execute({'query': 'What is the capital of France?'}, {}))")
    print("   print('Success:', result.success if result else False)")
    print("   \"")
    print()
    print("=" * 80)

if __name__ == "__main__":
    analyze_test_logs()

