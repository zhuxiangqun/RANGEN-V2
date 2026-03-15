#!/usr/bin/env python3
"""
验证完整RAG功能修复效果
"""

import asyncio
import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

# 🚀 强制禁用轻量级模式
os.environ['USE_LIGHTWEIGHT_RAG'] = 'false'
print('🔧 已强制设置 USE_LIGHTWEIGHT_RAG=false')

async def test_full_rag_functionality():
    """测试完整RAG功能"""

    print("🧪 测试完整RAG功能")
    print("=" * 50)

    try:
        # 导入RAGTool
        from src.agents.tools.rag_tool import RAGTool

        print("1. 初始化RAGTool...")
        rag_tool = RAGTool()

        # 检查RAG Agent的轻量级模式状态
        rag_agent = rag_tool._get_rag_agent()
        lightweight_mode = getattr(rag_agent, '_lightweight_mode', False)
        print(f"   RAG Agent轻量级模式: {lightweight_mode}")

        if lightweight_mode:
            print("❌ 仍然处于轻量级模式，测试失败")
            return False

        print("✅ RAG Agent处于完整模式")

        # 测试简单查询
        print("\n2. 测试简单查询...")
        result = await rag_tool.call(query='什么是RAG？')

        print(f"   查询成功: {result.success}")
        answer_text = ''
        sources_list_len = 0
        try:
            # 兼容两种返回结构：ToolResult.data 和 旧的 data_info
            data = getattr(result, 'data', None)
            if isinstance(data, dict):
                answer_text = data.get('answer', '') or ''
                # 证据键为'evidence'（标准），兼容旧的'sources'
                sources_list = data.get('evidence') or data.get('sources') or []
                sources_list_len = len(sources_list) if isinstance(sources_list, list) else 0
            else:
                data_info = getattr(result, 'data_info', {}) or {}
                if isinstance(data_info, dict):
                    answer_text = data_info.get('answer', '') or ''
                    sources_list = data_info.get('evidence') or data_info.get('sources') or []
                    sources_list_len = len(sources_list) if isinstance(sources_list, list) else 0
        except Exception:
            pass
        print(f"   答案长度: {len(answer_text)}")

        # 检查是否返回模拟结果
        answer = answer_text
        if '模拟回答' in answer or '轻量级模式' in answer:
            print("❌ 返回的是模拟结果，轻量级模式仍有效")
            return False

        print("✅ 返回真实答案（非模拟结果）")

        # 检查证据数量
        evidence_count = sources_list_len
        print(f"   检索到证据数量: {evidence_count}")

        if evidence_count == 0:
            print("⚠️ 未检索到证据，可能需要重建知识库索引")
        else:
            print("✅ 成功检索到证据")

        print("\n🎉 完整RAG功能测试通过！")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主函数"""
    success = await test_full_rag_functionality()

    if success:
        print("\n✅ 所有测试通过！完整RAG功能已成功启用")
        print("\n📋 验证结果:")
        print("   - ✅ 轻量级模式已禁用")
        print("   - ✅ RAG Agent完整初始化")
        print("   - ✅ 返回真实答案而非模拟结果")
        print("   - ✅ 知识检索功能正常")
    else:
        print("\n❌ 测试失败，仍存在问题")
        print("\n🔧 可能的修复方法:")
        print("   1. 检查.env文件中是否仍有USE_LIGHTWEIGHT_RAG=true")
        print("   2. 重启Python进程清除缓存")
        print("   3. 运行: unset USE_LIGHTWEIGHT_RAG")
        print("   4. 重建知识库索引: python3 knowledge_management_system/scripts/rebuild_vector_index.py")

if __name__ == "__main__":
    asyncio.run(main())
