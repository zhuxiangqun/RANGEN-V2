#!/usr/bin/env python3
"""
RAGExpert执行过程详细调试脚本

分析RAGExpert执行过程中的每个步骤，找出超时和错误的原因
"""

import os
import sys
import asyncio
import time
import logging
from pathlib import Path

# 设置详细日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_rag_execution.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# 确保移除轻量级模式
if 'USE_LIGHTWEIGHT_RAG' in os.environ:
    del os.environ['USE_LIGHTWEIGHT_RAG']
os.environ['USE_NEW_AGENTS'] = 'true'

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

async def debug_rag_execution():
    """详细调试RAGExpert执行过程"""

    print("🔍 开始RAGExpert执行过程详细调试")
    print("=" * 60)

    step = 1

    # 1. 初始化RAGExpert
    print(f"\n📋 步骤{step}: 初始化RAGExpert")
    print("-" * 40)

    try:
        from src.agents.rag_agent import RAGExpert

        print("🔧 创建RAGExpert实例...")
        start_time = time.time()
        rag_expert = RAGExpert()
        init_time = time.time() - start_time

        print(".2f"        print(f"   轻量级模式: {getattr(rag_expert, '_lightweight_mode', '未设置')}")

        # 检查关键组件
        components = [
            ('_parallel_executor', '并行执行器'),
            ('_knowledge_retrieval_service', '知识检索服务'),
            ('_reasoning_engine_pool', '推理引擎池'),
            ('_reasoning_engine', '推理引擎实例')
        ]

        for attr, name in components:
            has_component = hasattr(rag_expert, attr) and getattr(rag_expert, attr) is not None
            print(f"   {name}: {'✅' if has_component else '❌'}")

    except Exception as e:
        print(f"❌ RAGExpert初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return

    step += 1

    # 2. 测试简单查询（避免复杂推理）
    print(f"\n📋 步骤{step}: 测试简单查询")
    print("-" * 40)

    simple_query = "RAG是什么？"
    print(f"🧪 简单查询: {simple_query}")
    print("💡 使用30秒超时，避免复杂推理")

    try:
        start_time = time.time()

        # 设置较短的超时
        context = {
            "query": simple_query,
            "max_iterations": 1,  # 限制推理步数
            "use_tools": False,
            "enable_knowledge_retrieval": True,
            "timeout": 30.0  # 内部超时
        }

        print("⚡ 开始执行...")
        result = await asyncio.wait_for(
            rag_expert.execute(context),
            timeout=30.0
        )

        execution_time = time.time() - start_time

        print(".2f"        print(f"   成功: {result.success}")
        print(f"   错误: {result.error}")

        if hasattr(result, 'data') and result.data:
            data = result.data if isinstance(result.data, dict) else {}
            print(f"   数据类型: {type(result.data)}")
            if isinstance(data, dict):
                sources = data.get('sources', [])
                answer = data.get('answer', '')
                reasoning = data.get('reasoning', '')
                print(f"   证据数量: {len(sources)}")
                print(f"   答案长度: {len(answer)}")
                print(f"   推理长度: {len(reasoning)}")

                if len(answer) > 0:
                    print(f"   答案预览: {answer[:100]}...")
                else:
                    print("   ⚠️ 没有答案内容")

        if hasattr(result, 'processing_time'):
            print(".3f"
    except asyncio.TimeoutError:
        execution_time = time.time() - start_time
        print(".2f"        print("❌ 执行超时，这表明RAGExpert存在严重性能问题")
        return
    except Exception as e:
        execution_time = time.time() - start_time
        print(".2f"        print(f"❌ 执行异常: {e}")
        import traceback
        traceback.print_exc()
        return

    step += 1

    # 3. 分析执行日志
    print(f"\n📋 步骤{step}: 分析执行日志")
    print("-" * 40)

    print("📄 检查debug_rag_execution.log文件中的详细日志...")
    print("🔍 查找关键问题：")
    print("   - 是否有递归调用？")
    print("   - 是否有API超时？")
    print("   - 是否有验证失败？")
    print("   - 是否有推理引擎问题？")

    # 读取日志文件
    log_file = Path("debug_rag_execution.log")
    if log_file.exists():
        with open(log_file, 'r') as f:
            log_content = f.read()

        # 分析关键问题
        issues = []

        if "recursion" in log_content.lower() or "maximum recursion depth" in log_content.lower():
            issues.append("🔴 递归深度过大 - 推理过程可能陷入循环")

        if "timeout" in log_content.lower():
            issues.append("🔴 API调用超时 - 外部服务响应慢")

        if "validation" in log_content.lower() and "fail" in log_content.lower():
            issues.append("🟡 答案验证失败 - 验证逻辑过于严格")

        if "evidence" in log_content.lower() and "match" in log_content.lower():
            issues.append("🟡 证据匹配率低 - 检索或推理质量问题")

        if len(log_content) > 10000:
            issues.append("🟡 日志过长 - 执行过程过于复杂")

        if not issues:
            issues.append("✅ 未发现明显问题")

        print("📊 发现的问题:")
        for issue in issues:
            print(f"   {issue}")

        print(f"\n📈 日志统计:")
        print(f"   总字符数: {len(log_content)}")
        print(f"   行数: {len(log_content.splitlines())}")
        print(f"   ERROR数量: {log_content.count('ERROR')}")
        print(f"   WARNING数量: {log_content.count('WARNING')}")

    else:
        print("❌ 日志文件不存在")

    step += 1

    # 4. 结论和建议
    print(f"\n📋 步骤{step}: 结论和建议")
    print("-" * 40)

    if execution_time > 30:
        print("❌ 主要问题：执行时间过长")
        print("   建议：")
        print("   1. 检查推理引擎的递归深度限制")
        print("   2. 简化查询处理流程")
        print("   3. 优化知识检索性能")
        print("   4. 检查外部API调用超时设置")
    elif not result.success:
        print("❌ 主要问题：执行失败")
        print("   建议：")
        print("   1. 检查错误信息和日志")
        print("   2. 验证API配置")
        print("   3. 检查知识库连接")
    else:
        print("✅ 执行基本正常")
        print("   但仍需检查日志中的警告信息")

    print("\n🏁 调试完成")

if __name__ == '__main__':
    asyncio.run(debug_rag_execution())
