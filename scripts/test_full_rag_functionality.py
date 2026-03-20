#!/usr/bin/env python3
"""
完整RAG功能测试脚本
确保移除轻量级模式，测试真正的RAG功能
"""

import os
import sys
import asyncio
import time
from pathlib import Path

# 🚀 确保移除轻量级模式（不要设置USE_LIGHTWEIGHT_RAG）
# 明确删除环境变量，如果存在的话
if 'USE_LIGHTWEIGHT_RAG' in os.environ:
    del os.environ['USE_LIGHTWEIGHT_RAG']

os.environ['USE_NEW_AGENTS'] = 'true'

print("🔧 环境变量设置:")
print(f"   USE_LIGHTWEIGHT_RAG = {os.environ.get('USE_LIGHTWEIGHT_RAG', 'not_set')}")
print(f"   USE_NEW_AGENTS = {os.environ.get('USE_NEW_AGENTS', 'not_set')}")
if os.environ.get('USE_LIGHTWEIGHT_RAG') == 'true':
    print("⚠️  警告：USE_LIGHTWEIGHT_RAG仍然设置为true，将继续测试但可能仍使用轻量级模式")

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def test_full_rag():
    """测试完整RAG功能"""
    print("\n🚀 开始完整RAG功能测试")
    print("=" * 50)
    print("⚠️  确保：USE_LIGHTWEIGHT_RAG未设置，将测试完整RAG功能")
    print("   预期会加载知识库和模型，可能需要几分钟...")
    print("   注意：初始化过程中可能会有一些组件加载失败的警告，这是正常的")
    print("   只要RAGExpert本身能正常工作，这些警告不会影响测试结果")

    step = 1

    # 1. 测试RAGTool初始化
    print(f"\n📋 步骤{step}: 测试RAGTool初始化")
    print("-" * 30)

    try:
        from src.agents.tools.rag_tool import RAGTool

        print("🔧 创建RAGTool实例...")
        rag_tool = RAGTool()
        print("✅ RAGTool初始化成功")

        # 强制清除缓存，确保使用当前环境变量
        print("🔄 清除缓存...")
        rag_tool._rag_agent = None

    except Exception as e:
        print(f"❌ RAGTool初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    step += 1

    # 2. 测试Agent获取（完整模式）
    print(f"\n📋 步骤{step}: 测试Agent获取（完整模式）")
    print("-" * 30)

    try:
        print("🔧 获取RAG Agent（完整模式）...")
        start_time = time.time()

        # 这应该触发完整初始化
        rag_agent = rag_tool._get_rag_agent()

        get_time = time.time() - start_time
        print(f"   获取时间: {get_time:.2f}s")
        print(f"   Agent类型: {type(rag_agent).__name__}")

        # 检查是否是完整模式（不应该有轻量级标记）
        if hasattr(rag_agent, '_lightweight_mode'):
            if rag_agent._lightweight_mode:
                print("❌ 错误：仍在使用轻量级模式！")
                print("   诊断信息：")
                print(f"   - USE_LIGHTWEIGHT_RAG环境变量: {os.environ.get('USE_LIGHTWEIGHT_RAG', 'not_set')}")
                print("   - 建议：检查是否从其他地方继承了环境变量")
                print("   - 尝试：unset USE_LIGHTWEIGHT_RAG 或重启shell")
                return False
            else:
                print("✅ 已正确使用完整模式（有标记但为False）")
        else:
            print("✅ 未检测到轻量级模式标记，应该是完整模式")

        # 进一步验证：检查是否有真正的初始化组件
        has_real_components = (
            hasattr(rag_agent, '_parallel_executor') and rag_agent._parallel_executor is not None
        )
        if has_real_components:
            print("✅ 检测到完整模式的组件（并行执行器等）")
        else:
            print("⚠️  未检测到完整模式的组件，可能仍然是轻量级模式")

    except Exception as e:
        print(f"❌ Agent获取失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    step += 1

    # 3. 测试实际调用（完整功能）
    print(f"\n📋 步骤{step}: 测试实际调用（完整功能）")
    print("-" * 30)

    try:
        test_query = "什么是RAG？"
        print(f"🧪 测试查询: {test_query}")
        print("⚠️  完整模式，设置120秒超时")
        print("💡 预期会进行知识检索和LLM推理...")
        print("🔍 将进行严格的质量检查...")

        start_time = time.time()
        result = await asyncio.wait_for(
            rag_tool.call(query=test_query),
            timeout=120.0
        )
        call_time = time.time() - start_time

        # 🚨 严格检查：超时本身就是失败
        if call_time > 120.0:
            print(f"❌ 执行时间过长: {call_time:.2f}s (>120s)，这表明系统存在严重性能问题")
            return False

        if result.success:
            print(f"   调用时间: {call_time:.2f}s")
            data = result.data

            # 🚨 质量检查1：数据格式必须正确
            if not isinstance(data, dict):
                print(f"❌ 返回数据格式错误: 期望dict，实际{type(data)}")
                return False

            print(f"   数据类型: {type(data)}")
            sources = data.get('sources', [])
            answer = data.get('answer', '')
            evidence = data.get('evidence', [])

            print(f"   检索到 {len(sources)} 条sources")
            print(f"   检索到 {len(evidence)} 条evidence")
            print(f"   答案长度: {len(answer)} 字符")

            # 🚨 质量检查2：轻量级模式检查
            if data.get('lightweight_mode', False):
                print("❌ 错误：返回了轻量级模式的结果！")
                return False
            else:
                print("✅ 返回完整模式的结果")

            # 🚨 质量检查3：内容质量检查
            if len(sources) == 0 and len(evidence) == 0:
                print("❌ 严重错误：没有检索到任何证据！")
                print("   这表明知识库或检索系统存在问题")
                return False

            if len(answer) < 20:
                print(f"❌ 严重错误：答案过短 ({len(answer)}字符)，没有实质内容")
                print("   这表明LLM生成或推理过程存在问题")
                return False

            # 🚨 质量检查4：答案内容合理性检查
            if "模拟" in answer or "mock" in answer.lower():
                print("❌ 错误：答案包含模拟数据，说明使用了轻量级模式")
                return False

            if "RAG" not in answer and "检索增强生成" not in answer:
                print("❌ 错误：答案不包含'RAG'关键词，可能没有正确回答问题")
                return False

            print("✅ 成功检索到证据")
            print("✅ 生成的答案有实质内容")
            print(f"   答案预览: {answer[:100]}...")

            # 🚨 质量检查5：性能检查
            if call_time > 60.0:
                print(f"⚠️  警告：执行时间较长 ({call_time:.2f}s)，可能存在性能问题")
                print("   但由于是完整功能测试，暂时接受")

        else:
            print(f"❌ 调用失败: {result.error}")
            return False

    except asyncio.TimeoutError:
        print("❌ 调用超时（>120秒），系统存在严重性能或功能问题")
        return False
    except Exception as e:
        print(f"❌ 调用异常: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 总结
    print(f"\n📊 测试总结")
    print("=" * 50)
    print("✅ 完整RAG功能测试完成！")

    print("\n🔍 测试结果分析:")
    if 'rag_agent' in locals() and hasattr(rag_agent, '_lightweight_mode') and not rag_agent._lightweight_mode:
        print("✅ 成功使用完整模式")
    else:
        print("❌ 仍在使用轻量级模式")

    if 'result' in locals() and result.success and isinstance(result.data, dict):
        sources_count = len(result.data.get('sources', []))
        answer_length = len(result.data.get('answer', ''))
        print(f"✅ 检索到 {sources_count} 条证据")
        print(f"✅ 生成 {answer_length} 字符的答案")
        if sources_count > 0 and answer_length > 100:
            print("🎉 完整RAG功能工作正常！")
        else:
            print("⚠️  RAG功能可能需要进一步配置")

    return True

if __name__ == '__main__':
    success = asyncio.run(test_full_rag())
    if success:
        print("\n🏆 完整RAG功能测试成功！")
    else:
        print("\n❌ 完整RAG功能测试失败！")
        sys.exit(1)
