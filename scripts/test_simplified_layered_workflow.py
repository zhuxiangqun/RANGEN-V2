#!/usr/bin/env python3
"""
简化版分层工作流测试脚本

测试不依赖LangGraph的简化版分层架构工作流
"""

import asyncio
import logging
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_simplified_workflow():
    """测试简化版工作流"""

    logger.info("🚀 开始简化版分层工作流测试")

    try:
        # 导入简化版工作流
        from src.core.simplified_layered_workflow import get_simplified_workflow

        # 获取工作流实例
        workflow = get_simplified_workflow()
        logger.info("✅ 简化版分层工作流初始化成功")

        # 测试查询列表
        test_queries = [
            "什么是人工智能？",
            "比较Python和Java的优缺点",
            "如何设计一个高并发的Web服务？",
            "解释量子计算的基本原理"
        ]

        results = []

        for i, query in enumerate(test_queries, 1):
            logger.info(f"📋 测试查询 {i}/{len(test_queries)}: {query[:50]}...")

            start_time = time.time()

            try:
                # 处理查询
                result = await workflow.process_query(query)

                execution_time = time.time() - start_time

                # 记录结果
                test_result = {
                    "query": query,
                    "success": len(result.get("errors", [])) == 0,
                    "final_answer": result.get("final_answer", ""),
                    "quality_score": result.get("quality_score", 0.0),
                    "execution_time": execution_time,
                    "workflow_time": result.get("execution_time", 0),
                    "errors": result.get("errors", []),
                    "warnings": result.get("warnings", []),
                    "node_times": result.get("node_times", {}),
                    "metadata": result.get("metadata", {}),
                    "workflow_id": result.get("workflow_id")
                }

                results.append(test_result)

                logger.info(f"✅ 查询 {i} 处理完成")
                logger.info(f"   质量评分: {test_result['quality_score']:.2f}")
                logger.info(f"   执行时间: {execution_time:.2f}s")
                logger.info(f"   答案长度: {len(test_result['final_answer'])}")

                if test_result['errors']:
                    logger.warning(f"   错误: {test_result['errors']}")

            except Exception as e:
                logger.error(f"❌ 查询 {i} 处理失败: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "execution_time": time.time() - start_time
                })

        # 生成测试报告
        await generate_simplified_test_report(results)

        # 测试工作流管理功能
        await test_workflow_management(workflow)

    except ImportError as e:
        logger.error(f"❌ 导入失败: {e}")
        logger.info("ℹ️ 请确保所有依赖都已安装")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)


async def generate_simplified_test_report(results: list):
    """生成简化版测试报告"""

    logger.info("📊 生成简化版测试报告")

    total_queries = len(results)
    successful_queries = sum(1 for r in results if r.get("success", False))

    success_rate = successful_queries / total_queries * 100 if total_queries > 0 else 0

    quality_scores = [r.get("quality_score", 0) for r in results if r.get("success", False)]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    execution_times = [r.get("execution_time", 0) for r in results]
    avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0

    print("\n" + "="*80)
    print("🤖 简化版分层工作流测试报告")
    print("="*80)
    print(f"总查询数: {total_queries}")
    print(f"成功查询数: {successful_queries}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均质量评分: {avg_quality:.2f}")
    print(".2f")
    print()

    # 详细结果
    print("📋 详细结果:")
    print("-" * 80)

    for i, result in enumerate(results, 1):
        status = "✅" if result.get("success", False) else "❌"
        query_short = result["query"][:50] + "..." if len(result["query"]) > 50 else result["query"]
        quality = result.get("quality_score", 0)
        exec_time = result.get("execution_time", 0)

        print(f"{i:2d}. {status} {query_short}")
        print(".2f")
        if result.get("success", False):
            errors = result.get("errors", [])
            if errors:
                print(f"      错误: {errors[:2]}")  # 只显示前2个错误

    # 性能分析
    print("\n📈 性能分析:")
    print("-" * 80)

    if results:
        node_times = {}
        for result in results:
            if result.get("success", False) and "node_times" in result:
                for node, time_spent in result["node_times"].items():
                    if node not in node_times:
                        node_times[node] = []
                    node_times[node].append(time_spent)

        for node, times in node_times.items():
            avg_time = sum(times) / len(times)
            max_time = max(times)
            min_time = min(times)
            print(f"   {node}: 平均{avg_time:.2f}s, 最大{max_time:.2f}s, 最小{min_time:.2f}s")
    print("="*80)


async def test_workflow_management(workflow):
    """测试工作流管理功能"""

    logger.info("🔧 测试工作流管理功能")

    try:
        # 获取执行列表
        executions = workflow.list_executions(5)
        logger.info(f"✅ 获取执行列表: {len(executions)} 条记录")

        # 测试取消执行（如果有正在运行的）
        for execution in executions:
            if execution.state.name == "RUNNING":
                cancelled = workflow.cancel_execution(execution.workflow_id)
                if cancelled:
                    logger.info(f"✅ 成功取消执行: {execution.workflow_id}")
                break

        # 显示执行状态统计
        states = {}
        for execution in executions:
            state = execution.state.name
            states[state] = states.get(state, 0) + 1

        logger.info(f"📊 执行状态统计: {states}")

    except Exception as e:
        logger.error(f"❌ 工作流管理测试失败: {e}")


async def test_component_integration():
    """测试组件集成"""

    logger.info("🔧 测试组件集成")

    try:
        from src.core.simplified_layered_workflow import SimplifiedLayeredWorkflow

        # 创建工作流实例
        workflow = SimplifiedLayeredWorkflow()

        # 测试单个步骤
        context = {'query': '测试查询'}

        # 测试查询分析步骤
        result1 = await workflow._execute_query_analysis(context)
        logger.info(f"✅ 查询分析步骤测试通过: {result1.get('query_type')}")

        # 更新上下文
        context.update(result1)

        # 测试战略决策步骤
        result2 = await workflow._execute_strategic_decision(context)
        logger.info(f"✅ 战略决策步骤测试通过: {len(result2.get('strategic_plan', {}).tasks)} 个任务")

        logger.info("🎉 组件集成测试通过！")

    except Exception as e:
        logger.error(f"❌ 组件集成测试失败: {e}", exc_info=True)


async def main():
    """主函数"""

    print("🧪 简化版分层工作流测试套件")
    print("=" * 50)

    # 测试组件集成
    await test_component_integration()

    print()

    # 测试完整工作流
    await test_simplified_workflow()

    print("\n🎯 简化版测试完成！")


if __name__ == "__main__":
    # 设置异步事件循环策略（适用于某些环境）
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            # 如果已经在运行事件循环中，使用不同的方法
            loop = asyncio.get_event_loop()
            loop.create_task(main())
        else:
            raise
