#!/usr/bin/env python3
"""
RAGExpert 成功率测试脚本
测试检索增强生成任务的成功率和性能
"""

import sys
import os
import json
import time
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 设置轻量级模式避免复杂初始化
os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'

def load_test_queries():
    """加载测试查询"""
    return [
        {
            "query": "What was the age difference between Mike Tyson and Tyson Fury on the respective days on which they lost their first professional boxing matches?",
            "expected_type": "numerical",
            "complexity": "high"
        },
        {
            "query": "Who was the United States President when Chile won their first Copa America?",
            "expected_type": "entity",
            "complexity": "medium"
        },
        {
            "query": "What painting was stolen from The Louvre exactly 56 years before the birth of activist and songwriter Joan Baez's mother?",
            "expected_type": "entity",
            "complexity": "high"
        },
        {
            "query": "How many years after the founding of the 50th most populous US city did Frank Fox receive UK Patent 1344259?",
            "expected_type": "numerical",
            "complexity": "very_high"
        },
        {
            "query": "In what city were the Summer Olympic Games held in the year the RMS Titanic sank?",
            "expected_type": "entity",
            "complexity": "medium"
        }
    ]

async def test_rag_expert():
    """测试RAGExpert功能"""
    print("🚀 RAGExpert 成功率测试")
    print("=" * 80)

    # 导入RAGExpert
    try:
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert 导入成功")
    except ImportError as e:
        print(f"❌ RAGExpert 导入失败: {e}")
        return None

    # 初始化RAGExpert
    try:
        rag_agent = RAGExpert()
        print("✅ RAGExpert 初始化成功")
    except Exception as e:
        print(f"❌ RAGExpert 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None

    # 加载测试查询
    test_queries = load_test_queries()
    print(f"📋 准备测试查询: {len(test_queries)} 个")

    # 执行测试
    results = []
    total_start_time = time.time()

    for i, query_data in enumerate(test_queries, 1):
        query = query_data["query"]
        expected_type = query_data["expected_type"]
        complexity = query_data["complexity"]

        print(f"\n🔍 测试 {i}/{len(test_queries)}: {complexity.upper()} 复杂度")
        print(f"   查询: {query[:80]}{'...' if len(query) > 80 else ''}")

        query_start_time = time.time()

        try:
            # 创建任务
            task = {
                "task_type": "rag_query",
                "query": query,
                "context": {
                    "expected_answer_type": expected_type,
                    "complexity": complexity,
                    "use_knowledge_base": True
                }
            }

            # 执行任务
            result = await rag_agent.execute(task)

            query_time = time.time() - query_start_time

            # 分析结果
            success = result.get("success", False) if result else False
            confidence = result.get("confidence", 0.0) if result else 0.0
            answer = result.get("answer", "") if result else ""

            print(".2f")
            print(f"   答案: {answer[:100]}{'...' if len(answer) > 100 else ''}")

            # 质量评估
            quality_score = evaluate_answer_quality(answer, expected_type, query)

            test_result = {
                "query_id": i,
                "query": query,
                "expected_type": expected_type,
                "complexity": complexity,
                "success": success,
                "confidence": confidence,
                "answer": answer,
                "response_time": query_time,
                "quality_score": quality_score,
                "error": None
            }

        except Exception as e:
            query_time = time.time() - query_start_time
            print(".2f")
            print(f"   错误: {str(e)[:100]}")

            test_result = {
                "query_id": i,
                "query": query,
                "expected_type": expected_type,
                "complexity": complexity,
                "success": False,
                "confidence": 0.0,
                "answer": "",
                "response_time": query_time,
                "quality_score": 0,
                "error": str(e)
            }

        results.append(test_result)

    total_time = time.time() - total_start_time

    # 计算统计结果
    return analyze_results(results, total_time)

def evaluate_answer_quality(answer: str, expected_type: str, query: str) -> float:
    """评估答案质量"""
    if not answer or not answer.strip():
        return 0.0

    score = 0.5  # 基础分数：有答案

    # 类型匹配度
    if expected_type == "numerical" and any(char.isdigit() for char in answer):
        score += 0.2
    elif expected_type == "entity" and len(answer.split()) <= 5:
        score += 0.2

    # 答案长度合理性
    word_count = len(answer.split())
    if 1 <= word_count <= 20:
        score += 0.1

    # 避免通用回答
    generic_responses = ["i don't know", "unknown", "unclear", "not specified"]
    if not any(generic in answer.lower() for generic in generic_responses):
        score += 0.1

    # 信息密度
    if len(answer) > 10:
        score += 0.1

    return min(score, 1.0)

def analyze_results(results: List[Dict], total_time: float):
    """分析测试结果"""

    print("\n" + "=" * 80)
    print("📊 RAGExpert 测试结果分析")
    print("=" * 80)

    if not results:
        print("❌ 无测试结果")
        return None

    # 基本统计
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    success_rate = successful_tests / total_tests * 100

    print(f"🎯 测试概况:")
    print(f"   总测试数: {total_tests}")
    print(f"   成功测试: {successful_tests}")
    print(f"   成功率: {success_rate:.1f}%")
    print(".2f"
    # 性能指标
    response_times = [r["response_time"] for r in results]
    avg_response_time = np.mean(response_times)
    median_response_time = np.median(response_times)
    max_response_time = np.max(response_times)

    print(f"\n⚡ 性能指标:")
    print(".2f"    print(".2f"    print(".2f"
    # 质量分析
    quality_scores = [r["quality_score"] for r in results]
    avg_quality = np.mean(quality_scores)

    print(f"\n⭐ 质量指标:")
    print(".2f")
    print(f"   质量分布: {np.percentile(quality_scores, 25):.2f} | {np.percentile(quality_scores, 50):.2f} | {np.percentile(quality_scores, 75):.2f}")

    # 复杂度分析
    complexity_stats = {}
    for result in results:
        complexity = result["complexity"]
        if complexity not in complexity_stats:
            complexity_stats[complexity] = {"total": 0, "success": 0}
        complexity_stats[complexity]["total"] += 1
        if result["success"]:
            complexity_stats[complexity]["success"] += 1

    print(f"\n🎯 复杂度分析:")
    for complexity, stats in complexity_stats.items():
        success_rate = stats["success"] / stats["total"] * 100
        print(".1f")
    # 置信度分析
    confidences = [r["confidence"] for r in results if r["success"]]
    if confidences:
        avg_confidence = np.mean(confidences)
        print(f"\n🎖️ 置信度分析:")
        print(".2f")
        print(f"   置信度分布: {np.percentile(confidences, 25):.2f} | {np.percentile(confidences, 50):.2f} | {np.percentile(confidences, 75):.2f}")

    # 保存详细结果
    output_file = f"rag_expert_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_tests": total_tests,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "avg_quality_score": avg_quality,
                "total_time": total_time
            },
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 详细结果已保存到: {output_file}")

    # 最终评估
    print("\n" + "=" * 80)
    if success_rate >= 80:
        print("🎉 RAGExpert 性能优秀！")
        grade = "A"
    elif success_rate >= 60:
        print("👍 RAGExpert 性能良好！")
        grade = "B"
    elif success_rate >= 40:
        print("⚠️ RAGExpert 性能一般，需要优化")
        grade = "C"
    else:
        print("❌ RAGExpert 性能不佳，需要改进")
        grade = "D"

    print(f"📈 综合评分: {grade} (成功率: {success_rate:.1f}%)")

    return {
        "success_rate": success_rate,
        "avg_response_time": avg_response_time,
        "avg_quality_score": avg_quality,
        "grade": grade,
        "total_tests": total_tests,
        "results": results
    }

async def main():
    """主函数"""
    try:
        results = await test_rag_expert()
        if results:
            print("\n✅ RAGExpert 成功率测试完成！"            return 0
        else:
            print("\n❌ RAGExpert 测试失败！")
            return 1
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
