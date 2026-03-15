#!/usr/bin/env python3
"""
验证修复效果的简单测试
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

async def test_simple_query():
    """测试简单查询是否能正常工作"""
    try:
        from src.tools.rag_tool import RAGTool

        print("🔧 初始化RAGTool...")
        rag_tool = RAGTool()

        print("🧪 测试简单查询: '什么是RAG？'")
        result = await rag_tool.call(query='什么是RAG？')

        print(f"✅ 查询成功完成")
        print(f"   成功: {result.success}")
        print(f"   置信度: {result.confidence}")
        print(f"   答案长度: {len(result.data_info.get('answer', ''))}")

        if result.success and len(result.data_info.get('answer', '')) > 10:
            print("🎉 简单查询修复成功！")
            return True
        else:
            print("❌ 答案可能有问题")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_query())
    if success:
        print("\n✅ 所有修复验证通过！")
    else:
        print("\n❌ 修复验证失败，需要进一步调试")
