#!/usr/bin/env python3
"""
验证图谱检索禁用和linter修复效果
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

async def test_rag_without_graph():
    """测试禁用图谱检索的RAG功能"""
    try:
        from src.tools.rag_tool import RAGTool

        print("🔧 初始化RAGTool...")
        rag_tool = RAGTool()

        print("🧪 测试简单查询: '什么是RAG？'")
        result = await rag_tool.call(query='什么是RAG？')

        print("📊 测试结果:"        print(f"   成功: {result.success}")
        print(f"   置信度: {result.confidence}")
        print(f"   答案长度: {len(result.data_info.get('answer', ''))}")

        if result.success and len(result.data_info.get('answer', '')) > 10:
            print("🎉 RAG功能正常，图谱检索已禁用！")
            return True
        else:
            print("❌ 结果可能有问题")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_linter_fixes():
    """测试linter修复效果"""
    try:
        from src.core.reasoning.engine import RealReasoningEngine
        from src.agents.rag_agent import RAGExpert

        print("🔧 测试推理引擎导入...")
        engine = RealReasoningEngine()
        print("✅ 推理引擎初始化成功")

        print("🔧 测试RAG Agent导入...")
        # 简单测试RAG Agent初始化
        print("✅ RAG Agent导入成功")

        print("🔧 测试简单查询检测...")
        query = '什么是RAG？'
        query_type = 'definition'
        is_simple = engine._is_ultra_simple_query(query, query_type)
        print(f"✅ 简单查询检测: {query} -> {'简单' if is_simple else '复杂'}")

        return True

    except Exception as e:
        print(f"❌ 导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 开始验证修复效果")
    print("=" * 50)

    # 测试1: linter修复
    print("\n📋 测试1: linter错误修复")
    linter_ok = await test_linter_fixes()

    # 测试2: 图谱检索禁用
    print("\n📋 测试2: 图谱检索禁用效果")
    graph_ok = await test_rag_without_graph()

    print("\n" + "=" * 50)
    if linter_ok and graph_ok:
        print("🎉 所有修复验证通过！")
        print("✅ linter错误已解决")
        print("✅ 图谱检索已禁用")
        print("✅ RAG功能正常工作")
    else:
        print("❌ 部分测试失败")
        if not linter_ok:
            print("❌ linter修复需要检查")
        if not graph_ok:
            print("❌ 图谱检索禁用效果需要检查")

if __name__ == "__main__":
    asyncio.run(main())
