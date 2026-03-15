#!/usr/bin/env python3
"""
简化的RAGExpert成功率测试
"""

import os
import asyncio
import time
from datetime import datetime

# 设置轻量级模式
os.environ['USE_LIGHTWEIGHT_RAG'] = 'true'

async def test_rag_expert_simple():
    """简化的RAGExpert测试"""
    print("🚀 RAGExpert 简易成功率测试")
    print("=" * 60)

    # 导入RAGExpert
    try:
        from src.agents.rag_agent import RAGExpert
        print("✅ RAGExpert 导入成功")
    except ImportError as e:
        print(f"❌ RAGExpert 导入失败: {e}")
        return

    # 初始化RAGExpert
    try:
        rag_agent = RAGExpert()
        print("✅ RAGExpert 初始化成功")
    except Exception as e:
        print(f"❌ RAGExpert 初始化失败: {e}")
        return

    # 测试查询
    test_queries = [
        "What was the age difference between Mike Tyson and Tyson Fury?",
        "Who was the United States President when Chile won their first Copa America?",
        "What painting was stolen from The Louvre exactly 56 years before Joan Baez's birth?"
    ]

    print(f"\n📋 测试查询数量: {len(test_queries)}")
    print("\n🔍 开始测试...")

    results = []
    start_time = time.time()

    for i, query in enumerate(test_queries, 1):
        print(f"\n测试 {i}/{len(test_queries)}:")
        print(f"查询: {query[:60]}{'...' if len(query) > 60 else ''}")

        try:
            # 创建任务
            task = {
                "task_type": "rag_query",
                "query": query,
                "context": {
                    "use_knowledge_base": True
                }
            }

            # 执行查询
            query_start = time.time()
            result = await rag_agent.execute(task)
            query_time = time.time() - query_start

            # 分析结果
            if hasattr(result, 'success'):
                success = result.success
                confidence = getattr(result, 'confidence', 0.0)
                answer = result.data.get("answer", "") if hasattr(result, 'data') and result.data else ""
            else:
                # 兼容旧格式
                success = result.get("success", False) if result else False
                confidence = result.get("confidence", 0.0) if result else 0.0
                answer = result.get("answer", "") if result else ""

            status = "✅ 成功" if success else "❌ 失败"
            print(f"结果: {status}")
            print(".2f")
            if answer:
                print(f"答案: {answer[:100]}{'...' if len(answer) > 100 else ''}")

            results.append({
                "query": query,
                "success": success,
                "confidence": confidence,
                "response_time": query_time,
                "answer": answer
            })

        except Exception as e:
            print(f"结果: ❌ 异常 - {str(e)[:50]}")
            results.append({
                "query": query,
                "success": False,
                "confidence": 0.0,
                "response_time": 0.0,
                "answer": "",
                "error": str(e)
            })

    # 计算统计
    total_time = time.time() - start_time
    successful = sum(1 for r in results if r["success"])
    success_rate = successful / len(results) * 100

    print(f"\n{'='*60}")
    print("📊 测试结果统计:")
    print(f"总查询数: {len(results)}")
    print(f"成功查询: {successful}")
    print(".1f")
    print(".2f")
    print(".2f")

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"rag_simple_test_{timestamp}.json"

    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_queries": len(results),
                "successful_queries": successful,
                "success_rate": success_rate,
                "total_time": total_time,
                "avg_response_time": sum(r["response_time"] for r in results) / len(results)
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n💾 结果已保存到: {filename}")

    # 最终评估
    if success_rate >= 80:
        print("🎉 RAGExpert 表现优秀!")
    elif success_rate >= 60:
        print("👍 RAGExpert 表现良好!")
    else:
        print("⚠️ RAGExpert 需要优化!")

    return success_rate

async def main():
    """主函数"""
    try:
        success_rate = await test_rag_expert_simple()
        print(f"\n✅ 测试完成! 成功率: {success_rate:.1f}%")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
