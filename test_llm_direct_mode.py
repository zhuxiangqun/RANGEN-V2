#!/usr/bin/env python3
"""
测试LLM直接回答模式
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    print('✅ 已加载.env文件')
except ImportError:
    print('⚠️ python-dotenv未安装')

async def test_llm_direct_mode():
    """测试LLM直接回答模式"""
    try:
        from src.agents.rag_agent import RAGExpert

        print("🔧 初始化RAGExpert...")
        rag_agent = RAGExpert()

        # 测试查询 - 应该触发LLM直接回答模式
        query = "什么是人工智能？"  # 这是一个简单查询，应该触发直接回答

        print(f"🧪 测试查询: '{query}'")

        # 模拟上下文，强制使用LLM直接模式
        context = {
            'use_llm_direct': True,  # 强制使用LLM直接回答
            'query': query
        }

        result = await rag_agent.execute(context)

        print("📊 测试结果:")
        print(f"   成功: {result.success}")
        print(f"   置信度: {result.confidence}")
        if result.data and 'answer' in result.data:
            print(f"   答案: {result.data['answer'][:200]}...")
        else:
            print("   答案: 无")

        # 检查是否使用了LLM直接模式
        if hasattr(result, 'data') and result.data:
            llm_direct = result.data.get('llm_direct_mode', False)
            print(f"   使用LLM直接模式: {llm_direct}")

        return result

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    asyncio.run(test_llm_direct_mode())
