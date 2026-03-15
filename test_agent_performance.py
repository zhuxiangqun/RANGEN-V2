#!/usr/bin/env python3
"""
测试核心Agent的性能表现
"""

import asyncio
import sys
import os
import time
from pathlib import Path
from typing import Dict, Any, List

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

async def test_reasoning_expert():
    """测试ReasoningExpert性能"""
    try:
        from src.agents.reasoning_expert import ReasoningExpert

        print("🧠 测试ReasoningExpert...")
        agent = ReasoningExpert()

        # 测试查询
        test_queries = [
            "如果今天是星期一，那么后天是星期几？",
            "分析人工智能的发展趋势",
            "解释量子计算的基本原理"
        ]

        results = []
        for query in test_queries:
            print(f"   测试查询: {query[:30]}...")

            start_time = time.time()
            context = {
                'query': query,
                'reasoning_type': 'logical_deduction',
                'max_parallel_paths': 2,
                'use_cache': False
            }

            result = await agent.execute(context)
            elapsed = time.time() - start_time

            success = result.success if hasattr(result, 'success') else False
            print(".2f"
            results.append({
                'query': query,
                'success': success,
                'time': elapsed
            })

        return results

    except Exception as e:
        print(f"❌ ReasoningExpert测试失败: {e}")
        return []

async def test_quality_controller():
    """测试QualityController性能"""
    try:
        from src.agents.quality_controller import QualityController

        print("🔍 测试QualityController...")
        agent = QualityController()

        # 测试内容
        test_contents = [
            "人工智能是计算机科学的一个分支，专注于创建智能机器。",
            "量子计算利用量子力学原理进行计算，可能比传统计算机更快。",
            "机器学习是人工智能的一个子领域，专注于让计算机从数据中学习。"
        ]

        results = []
        for content in test_contents:
            print(f"   测试内容: {content[:30]}...")

            start_time = time.time()
            context = {
                'action': 'assess_quality',
                'content': content,
                'validation_level': 'standard'
            }

            result = await agent.execute(context)
            elapsed = time.time() - start_time

            success = result.success if hasattr(result, 'success') else False
            print(".2f"
            results.append({
                'content': content[:30],
                'success': success,
                'time': elapsed
            })

        return results

    except Exception as e:
        print(f"❌ QualityController测试失败: {e}")
        return []

async def run_performance_tests():
    """运行性能测试"""
    print("🚀 开始核心Agent性能测试")
    print("=" * 60)

    # 测试ReasoningExpert
    reasoning_results = await test_reasoning_expert()

    print()

    # 测试QualityController
    quality_results = await test_quality_controller()

    print()
    print("=" * 60)
    print("📊 性能测试总结")

    # 统计ReasoningExpert结果
    if reasoning_results:
        reasoning_success = sum(1 for r in reasoning_results if r['success'])
        reasoning_avg_time = sum(r['time'] for r in reasoning_results) / len(reasoning_results)
        print("🧠 ReasoningExpert:")
        print(f"   成功率: {reasoning_success}/{len(reasoning_results)} ({reasoning_success/len(reasoning_results)*100:.1f}%)")
        print(".2f"
        # 检查是否有性能问题
        if reasoning_avg_time > 10.0:
            print("   ⚠️  平均响应时间较长，可能需要优化")
        else:
            print("   ✅ 性能表现良好"
    else:
        print("❌ ReasoningExpert测试失败")

    # 统计QualityController结果
    if quality_results:
        quality_success = sum(1 for r in quality_results if r['success'])
        quality_avg_time = sum(r['time'] for r in quality_results) / len(quality_results)
        print("🔍 QualityController:")
        print(f"   成功率: {quality_success}/{len(quality_results)} ({quality_success/len(quality_results)*100:.1f}%)")
        print(".2f"
        # 检查是否有性能问题
        if quality_avg_time > 5.0:
            print("   ⚠️  平均响应时间较长，可能需要优化")
        else:
            print("   ✅ 性能表现良好"
    else:
        print("❌ QualityController测试失败")

    # 总体评估
    print()
    print("🎯 优化建议:")
    if reasoning_results and quality_results:
        all_success = all(r['success'] for r in reasoning_results + quality_results)
        if all_success:
            print("✅ 所有Agent性能表现良好")
        else:
            print("⚠️  部分Agent存在问题，需要进一步优化")
    else:
        print("❌ 测试不完整，无法给出准确评估")

if __name__ == "__main__":
    asyncio.run(run_performance_tests())
