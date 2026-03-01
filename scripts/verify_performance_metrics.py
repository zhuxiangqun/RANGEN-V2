#!/usr/bin/env python3
"""
性能指标验证脚本

根据SYSTEM_AGENTS_OVERVIEW.md验证优化效果指标：
- 响应速度: 25-35秒 → 8-15秒 (50-60%↑)
- 准确率: 75-85% → 85-95% (10-20%↑)
- 系统稳定性: 95% → 99.5% (4.5%↑)
"""

import asyncio
import time
import logging
import sys
import os
import json
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass, field

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.rag_agent import RAGExpert
from src.agents.agent_coordinator import AgentCoordinator
from src.agents.reasoning_expert import ReasoningExpert

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    agent_name: str
    test_count: int = 0
    success_count: int = 0
    total_time: float = 0.0
    avg_time: float = 0.0
    min_time: float = float('inf')
    max_time: float = 0.0
    cache_hits: int = 0
    errors: List[str] = field(default_factory=list)


class PerformanceVerifier:
    """性能验证器"""

    def __init__(self):
        self.metrics: Dict[str, PerformanceMetrics] = {}
        self.test_queries = [
            "什么是机器学习？",
            "Python中如何实现多线程？",
            "深度学习和机器学习的区别是什么？",
            "什么是人工智能？",
            "如何优化数据库查询性能？",
        ]

    async def test_rag_expert_performance(self):
        """测试RAGExpert性能"""
        print("\n" + "=" * 80)
        print("🚀 测试 RAGExpert 性能")
        print("=" * 80)

        metrics = PerformanceMetrics(agent_name="RAGExpert")
        agent = RAGExpert()

        print(f"\n📝 执行 {len(self.test_queries)} 个测试查询...")

        for i, query in enumerate(self.test_queries, 1):
            print(f"  查询 {i}/{len(self.test_queries)}: {query[:30]}...", end=" ")

            try:
                start_time = time.time()
                context = {
                    "query": query,
                    "use_cache": True,
                    "use_parallel": True,
                    "max_results": 5
                }

                result = await agent.execute(context)
                execution_time = time.time() - start_time

                metrics.test_count += 1
                metrics.total_time += execution_time
                metrics.min_time = min(metrics.min_time, execution_time)
                metrics.max_time = max(metrics.max_time, execution_time)

                if result.success:
                    metrics.success_count += 1
                    print(f"✅ {execution_time:.2f}秒")
                else:
                    metrics.errors.append(f"查询{i}失败: {result.error}")
                    print(f"❌ {execution_time:.2f}秒")

                # 检查缓存
                if hasattr(result, 'metadata') and result.metadata and result.metadata.get('cache_used'):
                    metrics.cache_hits += 1

            except Exception as e:
                metrics.errors.append(f"查询{i}异常: {str(e)}")
                print(f"❌ 异常: {str(e)[:50]}")

        if metrics.test_count > 0:
            metrics.avg_time = metrics.total_time / metrics.test_count

        self.metrics["RAGExpert"] = metrics
        return metrics

    async def test_agent_coordinator_performance(self):
        """测试AgentCoordinator性能"""
        print("\n" + "=" * 80)
        print("🚀 测试 AgentCoordinator 性能")
        print("=" * 80)

        metrics = PerformanceMetrics(agent_name="AgentCoordinator")
        agent = AgentCoordinator()

        # 注册一些测试Agent
        try:
            from src.agents.rag_agent import RAGExpert
            rag_expert = RAGExpert()
            agent.register_agent(
                rag_expert,
                capabilities={"retrieval", "generation"},
                max_concurrent=3
            )
        except Exception as e:
            logger.warning(f"注册Agent失败: {e}")

        print(f"\n📝 执行 {len(self.test_queries)} 个测试任务...")

        for i, query in enumerate(self.test_queries, 1):
            print(f"  任务 {i}/{len(self.test_queries)}: {query[:30]}...", end=" ")

            try:
                start_time = time.time()
                context = {
                    "query": query,
                    "type": "test"
                }

                result = await agent.execute(context)
                execution_time = time.time() - start_time

                metrics.test_count += 1
                metrics.total_time += execution_time
                metrics.min_time = min(metrics.min_time, execution_time)
                metrics.max_time = max(metrics.max_time, execution_time)

                if result.success:
                    metrics.success_count += 1
                    print(f"✅ {execution_time:.2f}秒")
                else:
                    metrics.errors.append(f"任务{i}失败: {result.error}")
                    print(f"❌ {execution_time:.2f}秒")

            except Exception as e:
                metrics.errors.append(f"任务{i}异常: {str(e)}")
                print(f"❌ 异常: {str(e)[:50]}")

        if metrics.test_count > 0:
            metrics.avg_time = metrics.total_time / metrics.test_count

        self.metrics["AgentCoordinator"] = metrics
        return metrics

    async def test_reasoning_expert_performance(self):
        """测试ReasoningExpert性能"""
        print("\n" + "=" * 80)
        print("🚀 测试 ReasoningExpert 性能")
        print("=" * 80)

        metrics = PerformanceMetrics(agent_name="ReasoningExpert")
        agent = ReasoningExpert()

        # 使用较少的测试查询（推理较慢）
        test_queries = self.test_queries[:3]

        print(f"\n📝 执行 {len(test_queries)} 个测试查询...")

        for i, query in enumerate(test_queries, 1):
            print(f"  查询 {i}/{len(test_queries)}: {query[:30]}...", end=" ")

            try:
                start_time = time.time()
                context = {
                    "query": query,
                    "use_cache": True
                }

                result = await agent.execute(context)
                execution_time = time.time() - start_time

                metrics.test_count += 1
                metrics.total_time += execution_time
                metrics.min_time = min(metrics.min_time, execution_time)
                metrics.max_time = max(metrics.max_time, execution_time)

                if result.success:
                    metrics.success_count += 1
                    print(f"✅ {execution_time:.2f}秒")
                else:
                    metrics.errors.append(f"查询{i}失败: {result.error}")
                    print(f"❌ {execution_time:.2f}秒")

                # 检查缓存
                if hasattr(result, 'metadata') and result.metadata and result.metadata.get('cache_used'):
                    metrics.cache_hits += 1

            except Exception as e:
                metrics.errors.append(f"查询{i}异常: {str(e)}")
                print(f"❌ 异常: {str(e)[:50]}")

        if metrics.test_count > 0:
            metrics.avg_time = metrics.total_time / metrics.test_count

        self.metrics["ReasoningExpert"] = metrics
        return metrics

    def generate_report(self) -> str:
        """生成性能报告"""
        report_lines = []
        report_lines.append("\n" + "=" * 80)
        report_lines.append("📊 性能指标验证报告")
        report_lines.append("=" * 80)
        report_lines.append(f"\n生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 文档中的目标指标
        target_metrics = {
            "响应速度": {"before": "25-35秒", "after": "8-15秒", "improvement": "50-60%↑"},
            "准确率": {"before": "75-85%", "after": "85-95%", "improvement": "10-20%↑"},
            "系统稳定性": {"before": "95%", "after": "99.5%", "improvement": "4.5%↑"},
        }

        report_lines.append("\n" + "-" * 80)
        report_lines.append("🎯 目标性能指标（来自文档）")
        report_lines.append("-" * 80)
        for metric_name, targets in target_metrics.items():
            report_lines.append(f"\n{metric_name}:")
            report_lines.append(f"  优化前: {targets['before']}")
            report_lines.append(f"  优化后: {targets['after']}")
            report_lines.append(f"  提升幅度: {targets['improvement']}")

        # 实际测试结果
        report_lines.append("\n" + "-" * 80)
        report_lines.append("📈 实际测试结果")
        report_lines.append("-" * 80)

        for agent_name, metrics in self.metrics.items():
            report_lines.append(f"\n【{agent_name}】")
            report_lines.append(f"  测试次数: {metrics.test_count}")
            report_lines.append(f"  成功次数: {metrics.success_count}")
            if metrics.test_count > 0:
                success_rate = (metrics.success_count / metrics.test_count) * 100
                report_lines.append(f"  成功率: {success_rate:.1f}%")
            if metrics.avg_time > 0:
                report_lines.append(f"  平均响应时间: {metrics.avg_time:.2f}秒")
                report_lines.append(f"  最小响应时间: {metrics.min_time:.2f}秒")
                report_lines.append(f"  最大响应时间: {metrics.max_time:.2f}秒")
            if metrics.cache_hits > 0:
                report_lines.append(f"  缓存命中次数: {metrics.cache_hits}")

            if metrics.errors:
                report_lines.append(f"  错误数: {len(metrics.errors)}")
                for error in metrics.errors[:3]:  # 只显示前3个错误
                    report_lines.append(f"    - {error[:60]}")

        # 对比分析
        report_lines.append("\n" + "-" * 80)
        report_lines.append("📊 对比分析")
        report_lines.append("-" * 80)

        # 计算总体指标
        total_tests = sum(m.test_count for m in self.metrics.values())
        total_success = sum(m.success_count for m in self.metrics.values())
        total_time = sum(m.total_time for m in self.metrics.values())
        total_cache_hits = sum(m.cache_hits for m in self.metrics.values())

        if total_tests > 0:
            overall_success_rate = (total_success / total_tests) * 100
            overall_avg_time = total_time / total_tests

            report_lines.append(f"\n总体指标:")
            report_lines.append(f"  总测试次数: {total_tests}")
            report_lines.append(f"  总成功次数: {total_success}")
            report_lines.append(f"  总体成功率: {overall_success_rate:.1f}%")
            report_lines.append(f"  平均响应时间: {overall_avg_time:.2f}秒")
            report_lines.append(f"  总缓存命中: {total_cache_hits}")

            # 与目标对比
            report_lines.append(f"\n与目标对比:")
            if overall_avg_time <= 15:
                report_lines.append(f"  ✅ 响应时间达标 (目标: 8-15秒, 实际: {overall_avg_time:.2f}秒)")
            elif overall_avg_time <= 25:
                report_lines.append(f"  🟡 响应时间接近目标 (目标: 8-15秒, 实际: {overall_avg_time:.2f}秒)")
            else:
                report_lines.append(f"  ❌ 响应时间未达标 (目标: 8-15秒, 实际: {overall_avg_time:.2f}秒)")

            if overall_success_rate >= 85:
                report_lines.append(f"  ✅ 准确率达标 (目标: 85-95%, 实际: {overall_success_rate:.1f}%)")
            elif overall_success_rate >= 75:
                report_lines.append(f"  🟡 准确率接近目标 (目标: 85-95%, 实际: {overall_success_rate:.1f}%)")
            else:
                report_lines.append(f"  ❌ 准确率未达标 (目标: 85-95%, 实际: {overall_success_rate:.1f}%)")

        # 建议
        report_lines.append("\n" + "-" * 80)
        report_lines.append("💡 建议")
        report_lines.append("-" * 80)

        if total_tests > 0:
            if overall_avg_time > 15:
                report_lines.append("\n⚠️ 响应时间需要优化:")
                report_lines.append("  - 检查缓存机制是否正常工作")
                report_lines.append("  - 验证并行处理是否启用")
                report_lines.append("  - 考虑增加缓存命中率")

            if overall_success_rate < 85:
                report_lines.append("\n⚠️ 准确率需要提升:")
                report_lines.append("  - 检查错误日志，分析失败原因")
                report_lines.append("  - 优化Agent的错误处理机制")
                report_lines.append("  - 验证输入数据的质量")

        return "\n".join(report_lines)

    async def run_verification(self):
        """运行性能验证"""
        print("🚀 开始性能指标验证...")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 测试各个Agent
        await self.test_rag_expert_performance()
        await self.test_agent_coordinator_performance()
        await self.test_reasoning_expert_performance()

        # 生成报告
        report = self.generate_report()
        print(report)

        # 保存报告
        report_file = Path(__file__).parent.parent / "comprehensive_eval_results" / "performance_metrics_verification_report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 性能报告已保存到: {report_file}")

        return report


async def main():
    """主函数"""
    verifier = PerformanceVerifier()
    await verifier.run_verification()


if __name__ == "__main__":
    asyncio.run(main())

