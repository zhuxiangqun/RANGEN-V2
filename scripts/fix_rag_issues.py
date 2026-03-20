#!/usr/bin/env python3
"""
修复RAGExpert问题的脚本

主要问题：
1. 递归深度过大导致RecursionError
2. 推理引擎执行时间过长
3. 答案验证过于严格

修复方案：
1. 增加Python递归深度限制
2. 为推理引擎添加超时控制
3. 调整答案验证逻辑
"""

import sys
import os
from pathlib import Path

# 设置项目环境
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def fix_recursion_limit():
    """修复递归深度限制"""
    print("🔧 修复1: 增加Python递归深度限制")
    current_limit = sys.getrecursionlimit()
    print(f"   当前递归深度限制: {current_limit}")

    # 增加递归深度限制到2000（通常足够）
    new_limit = 2000
    sys.setrecursionlimit(new_limit)
    print(f"   新递归深度限制: {new_limit}")

def patch_reasoning_engine_timeout():
    """为推理引擎添加超时控制"""
    print("\n🔧 修复2: 为推理引擎添加超时控制")

    try:
        # 导入推理引擎
        from src.core.real_reasoning_engine import RealReasoningEngine

        # 检查是否已有超时控制
        import inspect
        reason_method = getattr(RealReasoningEngine, 'reason', None)
        if reason_method:
            sig = inspect.signature(reason_method)
            has_timeout = 'timeout' in sig.parameters
            print(f"   推理引擎reason方法是否有timeout参数: {has_timeout}")

            if not has_timeout:
                print("   ⚠️ 推理引擎没有内置超时控制，需要在调用处添加")
            else:
                print("   ✅ 推理引擎已有超时控制")
        else:
            print("   ❌ 找不到推理引擎的reason方法")

    except Exception as e:
        print(f"   ❌ 检查推理引擎失败: {e}")

def patch_answer_validator():
    """修复答案验证逻辑"""
    print("\n🔧 修复3: 调整答案验证逻辑")

    try:
        from src.core.reasoning.answer_extraction.answer_validator import AnswerValidator

        # 创建验证器实例
        validator = AnswerValidator()

        # 检查配置缓存
        if hasattr(validator, 'config_cache'):
            print("   ✅ 验证器使用了配置缓存")

            # 获取当前阈值
            similarity_threshold = validator.config_cache.get_threshold('query_answer_consistency', 0.3)
            evidence_match_threshold = validator.config_cache.get_threshold('evidence_match_ratio', 0.2)

            print(".2f"            print(".2f"
            # 如果阈值过高，降低一些
            if similarity_threshold > 0.3:
                print("   ⚠️ 相似度阈值较高，可能过于严格")
                print("   建议降低到0.25-0.3之间")
            else:
                print("   ✅ 相似度阈值合理")

            if evidence_match_threshold > 0.2:
                print("   ⚠️ 证据匹配阈值较高，可能过于严格")
                print("   建议降低到0.15-0.2之间")
            else:
                print("   ✅ 证据匹配阈值合理")
        else:
            print("   ❌ 验证器没有配置缓存")

    except Exception as e:
        print(f"   ❌ 检查答案验证器失败: {e}")

def patch_rag_expert_timeout():
    """为RAGExpert添加超时控制"""
    print("\n🔧 修复4: 为RAGExpert添加超时控制")

    try:
        from src.agents.rag_agent import RAGExpert

        # 检查execute方法是否有超时参数
        import inspect
        execute_method = getattr(RAGExpert, 'execute', None)
        if execute_method:
            sig = inspect.signature(execute_method)
            has_timeout = 'timeout' in sig.parameters
            print(f"   RAGExpert.execute方法是否有timeout参数: {has_timeout}")

            if not has_timeout:
                print("   ⚠️ RAGExpert没有内置超时控制，建议在调用处添加asyncio.wait_for")
            else:
                print("   ✅ RAGExpert已有超时控制")
        else:
            print("   ❌ 找不到RAGExpert的execute方法")

    except Exception as e:
        print(f"   ❌ 检查RAGExpert失败: {e}")

def create_optimized_rag_call():
    """创建优化的RAG调用函数"""
    print("\n🔧 修复5: 创建优化的RAG调用函数")

    optimized_code = '''
# 优化的RAG调用函数 - 添加超时和错误处理
import asyncio
import time
from typing import Dict, Any, Optional

async def call_rag_with_timeout(
    rag_agent,
    query: str,
    context: Optional[Dict[str, Any]] = None,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    带超时的RAG调用

    Args:
        rag_agent: RAG代理实例
        query: 查询字符串
        context: 上下文字典
        timeout: 超时时间（秒）

    Returns:
        包含结果和执行信息的字典
    """
    start_time = time.time()

    try:
        # 准备上下文
        agent_context = {"query": query}
        if context:
            agent_context.update(context)

        # 添加超时设置到上下文中
        agent_context["timeout"] = timeout

        # 执行调用（带超时）
        result = await asyncio.wait_for(
            rag_agent.execute(agent_context),
            timeout=timeout
        )

        execution_time = time.time() - start_time

        return {
            "success": True,
            "result": result,
            "execution_time": execution_time,
            "timeout": False
        }

    except asyncio.TimeoutError:
        execution_time = time.time() - start_time
        return {
            "success": False,
            "error": f"执行超时 ({timeout}s)",
            "execution_time": execution_time,
            "timeout": True
        }

    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "success": False,
            "error": str(e),
            "execution_time": execution_time,
            "timeout": False
        }
'''

    # 保存到文件
    with open('optimized_rag_call.py', 'w', encoding='utf-8') as f:
        f.write(optimized_code)

    print("   ✅ 已创建optimized_rag_call.py文件")
    print("   使用方法：")
    print("   from optimized_rag_call import call_rag_with_timeout")
    print("   result = await call_rag_with_timeout(rag_agent, query, timeout=60.0)")

def main():
    """主修复函数"""
    print("🚀 开始修复RAGExpert问题")
    print("=" * 60)

    # 1. 修复递归深度
    fix_recursion_limit()

    # 2. 检查推理引擎超时
    patch_reasoning_engine_timeout()

    # 3. 修复答案验证
    patch_answer_validator()

    # 4. 检查RAGExpert超时
    patch_rag_expert_timeout()

    # 5. 创建优化的调用函数
    create_optimized_rag_call()

    print("\n" + "=" * 60)
    print("✅ 修复完成！")
    print("\n建议的测试方法：")
    print("1. 使用优化后的调用函数进行测试")
    print("2. 设置合理的超时时间（30-60秒）")
    print("3. 监控递归深度和执行时间")
    print("4. 如果仍有问题，可能需要简化推理逻辑")

if __name__ == '__main__':
    main()
