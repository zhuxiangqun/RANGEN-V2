#!/usr/bin/env python3
"""
轻量级RAG测试脚本
专门测试轻量级模式是否正常工作
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# 🚀 必须在所有导入之前设置环境变量
os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'
os.environ['USE_NEW_AGENTS'] = 'true'

print("🔧 环境变量设置:")
print(f"   USE_LIGHTWEIGHT_RAG = {os.environ.get('USE_LIGHTWEIGHT_RAG')}")
print(f"   USE_NEW_AGENTS = {os.environ.get('USE_NEW_AGENTS')}")

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def test_lightweight_rag():
    """测试轻量级RAG模式"""
    print("\n🚀 开始轻量级RAG测试")
    print("=" * 50)

    step = 1

    # 1. 测试RAGTool初始化
    print(f"\n📋 步骤{step}: 测试RAGTool初始化")
    print("-" * 30)

    try:
        from src.agents.tools.rag_tool import RAGTool

        print("🔧 创建RAGTool实例...")
        rag_tool = RAGTool()
        print("✅ RAGTool初始化成功")

        # 检查环境变量是否生效
        print("🔍 检查环境变量...")
        lightweight_env = os.environ.get('USE_LIGHTWEIGHT_RAG', 'false')
        print(f"   USE_LIGHTWEIGHT_RAG = {lightweight_env}")

    except Exception as e:
        print(f"❌ RAGTool初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    step += 1

    # 2. 测试_get_rag_agent方法
    print(f"\n📋 步骤{step}: 测试Agent获取")
    print("-" * 30)

    try:
        print("🔧 获取RAG Agent...")
        start_time = time.time()
        rag_agent = rag_tool._get_rag_agent()
        get_time = time.time() - start_time

        print(f"   获取时间: {get_time:.2f}s")
        print(f"   Agent类型: {type(rag_agent).__name__}")

        # 检查是否是轻量级模式
        if hasattr(rag_agent, '_lightweight_mode'):
            print(f"   轻量级模式: {rag_agent._lightweight_mode}")
        else:
            print("   ⚠️ 没有找到轻量级模式标记")

    except Exception as e:
        print(f"❌ Agent获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    step += 1

    # 3. 测试实际调用
    print(f"\n📋 步骤{step}: 测试实际调用")
    print("-" * 30)

    try:
        test_query = "Hello"
        print(f"🧪 测试查询: {test_query}")

        print("⚡ 开始调用...")
        start_time = time.time()
        result = await rag_tool.call(query=test_query)
        call_time = time.time() - start_time

        if result.success:
            print(f"   调用时间: {call_time:.2f}s")
            data = result.data
            if isinstance(data, dict):
                print(f"   数据类型: {type(data)}")
                print(f"   轻量级模式: {data.get('lightweight_mode', 'N/A')}")
                print(f"   回答预览: {data.get('answer', 'N/A')[:50]}...")
            else:
                print(f"   数据: {data}")
        else:
            print(f"❌ 调用失败: {result.error}")

    except Exception as e:
        print(f"❌ 调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 总结
    print(f"\n📊 测试总结")
    print("=" * 50)
    print("✅ 轻量级RAG测试完成！")
    print("\n检查结果:")
    print("- 如果看到'轻量级模式: True'，说明模式生效")
    print("- 如果看到模拟回答，说明轻量级模式工作正常")
    print("- 如果超时或加载知识库，说明模式未生效")

    return True

if __name__ == '__main__':
    asyncio.run(test_lightweight_rag())
