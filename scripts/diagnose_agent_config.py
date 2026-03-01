#!/usr/bin/env python3
"""
Agent配置诊断脚本
检查RAGExpert和ReasoningExpert的配置和推理引擎状态
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ['USE_LIGHTWEIGHT_RAG'] = 'false'  # 确保不使用轻量级模式

async def diagnose_agents():
    """诊断Agent配置"""
    print("🔍 开始Agent配置诊断...")
    print("=" * 60)

    try:
        # 导入Agent类
        from src.agents.rag_agent import RAGExpert
        from src.agents.reasoning_expert import ReasoningExpert

        print("✅ Agent模块导入成功")

        # 诊断RAGExpert
        print("\n🏗️ 诊断RAGExpert配置...")
        print("-" * 40)

        try:
            rag_agent = RAGExpert()
            print("✅ RAGExpert初始化成功")

            # 检查关键属性
            attrs_to_check = [
                '_lightweight_mode',
                '_knowledge_retrieval_service',
                '_reasoning_engine_pool',
                '_reasoning_engine',
                'config_center',
                'threshold_manager'
            ]

            for attr in attrs_to_check:
                value = getattr(rag_agent, attr, 'NOT_SET')
                if attr == '_lightweight_mode':
                    status = "❌ 轻量级模式" if value else "✅ 正常模式"
                    print(f"  {attr}: {value} - {status}")
                elif value is None:
                    print(f"  {attr}: None - ⚠️ 未初始化")
                else:
                    print(f"  {attr}: {type(value).__name__} - ✅ 已初始化")

            # 检查推理引擎池
            if hasattr(rag_agent, '_reasoning_engine_pool') and rag_agent._reasoning_engine_pool:
                try:
                    engine = await rag_agent._reasoning_engine_pool.get_engine()
                    print(f"  推理引擎获取: ✅ 成功 - {type(engine).__name__}")
                    await rag_agent._reasoning_engine_pool.return_engine(engine)
                except Exception as e:
                    print(f"  推理引擎获取: ❌ 失败 - {e}")
            else:
                print("  推理引擎池: ❌ 未初始化")

        except Exception as e:
            print(f"❌ RAGExpert初始化失败: {e}")
            import traceback
            traceback.print_exc()

        # 诊断ReasoningExpert
        print("\n🧠 诊断ReasoningExpert配置...")
        print("-" * 40)

        try:
            reasoning_agent = ReasoningExpert()
            print("✅ ReasoningExpert初始化成功")

            # 检查关键属性
            attrs_to_check = [
                '_reasoning_cache',
                '_parallel_executor',
                '_knowledge_graph',
                'config_center',
                'threshold_manager'
            ]

            for attr in attrs_to_check:
                value = getattr(reasoning_agent, attr, 'NOT_SET')
                if value is None:
                    print(f"  {attr}: None - ⚠️ 未初始化")
                else:
                    print(f"  {attr}: {type(value).__name__} - ✅ 已初始化")

            # 检查推理引擎
            if hasattr(reasoning_agent, '_reasoning_engine') and reasoning_agent._reasoning_engine:
                print(f"  推理引擎: ✅ 已初始化 - {type(reasoning_agent._reasoning_engine).__name__}")
            else:
                print("  推理引擎: ❌ 未初始化")

        except Exception as e:
            print(f"❌ ReasoningExpert初始化失败: {e}")
            import traceback
            traceback.print_exc()

        # 测试简单执行
        print("\n🧪 测试Agent执行...")
        print("-" * 40)

        # 测试RAGExpert
        try:
            test_context = {
                "query": "什么是机器学习？",
                "use_cache": False,
                "use_parallel": False
            }
            result = await rag_agent.execute(test_context)
            print(f"RAGExpert测试结果:")
            print(f"  成功: {result.success}")
            print(f"  耗时: {result.processing_time:.2f}秒")
            if not result.success:
                print(f"  错误: {result.error}")
        except Exception as e:
            print(f"RAGExpert执行测试失败: {e}")

        # 测试ReasoningExpert
        try:
            test_context = {
                "query": "分析机器学习的优缺点",
                "reasoning_type": "causal",
                "complexity": "moderate"
            }
            result = await reasoning_agent.execute(test_context)
            print(f"ReasoningExpert测试结果:")
            print(f"  成功: {result.success}")
            print(f"  耗时: {result.processing_time:.2f}秒")
            if not result.success:
                print(f"  错误: {result.error}")
            else:
                print(f"  数据类型: {type(result.data)}")
                if result.data:
                    print(f"  数据长度: {len(str(result.data))} 字符")
        except Exception as e:
            print(f"ReasoningExpert执行测试失败: {e}")

    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("🔍 Agent配置诊断完成")
    return True

if __name__ == "__main__":
    import asyncio
    asyncio.run(diagnose_agents())
