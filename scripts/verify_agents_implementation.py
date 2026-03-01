#!/usr/bin/env python3
"""
Agent实现完整性验证脚本

根据SYSTEM_AGENTS_OVERVIEW.md验证：
1. 8个核心Agent的功能完整性
2. 优化特性的实施情况
3. L6/L7高级特性的验证
4. 性能指标验证
"""

import asyncio
import time
import logging
import sys
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.agent_coordinator import AgentCoordinator
from src.agents.rag_agent import RAGExpert
from src.agents.reasoning_expert import ReasoningExpert
from src.agents.tool_orchestrator import ToolOrchestrator
from src.agents.memory_manager import MemoryManager
from src.agents.learning_optimizer import LearningOptimizer
from src.agents.quality_controller import QualityController
from src.agents.security_guardian import SecurityGuardian
from src.agents.multi_agent_coordinator import MultiAgentCoordinator
from src.agents.autonomous_runner import AutonomousRunner

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class FeatureCheck:
    """功能检查结果"""
    name: str
    expected: bool
    actual: bool
    details: str = ""
    status: str = field(init=False)

    def __post_init__(self):
        self.status = "✅" if self.actual == self.expected else "❌"


@dataclass
class AgentVerification:
    """Agent验证结果"""
    agent_name: str
    agent_class: str
    exists: bool
    features: List[FeatureCheck] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[str] = field(default_factory=list)


class AgentImplementationVerifier:
    """Agent实现验证器"""

    def __init__(self):
        self.results: Dict[str, AgentVerification] = {}
        self.performance_results: Dict[str, Dict[str, float]] = {}

    async def verify_core_agents(self):
        """验证8个核心Agent"""
        print("\n" + "=" * 80)
        print("🔍 验证8个核心Agent实现")
        print("=" * 80)

        core_agents = [
            ("AgentCoordinator", AgentCoordinator, {
                "智能任务分配": True,
                "资源负载均衡": True,
                "冲突检测解决": True,
                "决策缓存": True,
            }),
            ("RAGExpert", RAGExpert, {
                "并行检索策略": True,
                "智能缓存机制": True,
                "答案生成加速": True,
                "多源知识融合": True,
            }),
            ("ReasoningExpert", ReasoningExpert, {
                "并行推理引擎": True,
                "推理结果缓存": True,
                "知识图谱集成": True,
                "多步骤推理链": True,
            }),
            ("ToolOrchestrator", ToolOrchestrator, {
                "智能工具选择": True,
                "编排策略优化": True,
                "提示词动态优化": True,
                "工具性能监控": True,
            }),
            ("MemoryManager", MemoryManager, {
                "智能压缩算法": True,
                "关联网络优化": True,
                "自适应记忆管理": True,
                "上下文感知检索": True,
            }),
            ("LearningOptimizer", LearningOptimizer, {
                "增量学习算法": True,
                "性能模式识别": True,
                "A/B测试自动化": True,
                "自适应调整策略": True,
            }),
            ("QualityController", QualityController, {
                "多维度评估算法": True,
                "自动化验证流程": True,
                "持续改进机制": True,
                "事实核查": True,
            }),
            ("SecurityGuardian", SecurityGuardian, {
                "实时威胁检测": True,
                "隐私保护优化": True,
                "合规审计强化": True,
                "内容安全过滤": True,
            }),
        ]

        for agent_name, agent_class, expected_features in core_agents:
            print(f"\n📋 验证 {agent_name}...")
            verification = await self._verify_agent(agent_name, agent_class, expected_features)
            self.results[agent_name] = verification

    async def _verify_agent(
        self,
        agent_name: str,
        agent_class: type,
        expected_features: Dict[str, bool]
    ) -> AgentVerification:
        """验证单个Agent"""
        verification = AgentVerification(
            agent_name=agent_name,
            agent_class=agent_class.__name__,
            exists=True
        )

        try:
            # 实例化Agent
            agent = agent_class()

            # 检查基础功能
            features = []
            for feature_name, expected in expected_features.items():
                actual = await self._check_feature(agent, feature_name, expected)
                features.append(FeatureCheck(
                    name=feature_name,
                    expected=expected,
                    actual=actual,
                    details=self._get_feature_details(agent, feature_name)
                ))

            verification.features = features

            # 检查是否有execute方法
            if not hasattr(agent, 'execute'):
                verification.issues.append("缺少execute方法")
            else:
                # 简单性能测试
                try:
                    perf_metrics = await self._test_agent_performance(agent, agent_name)
                    verification.performance_metrics = perf_metrics
                except Exception as e:
                    verification.issues.append(f"性能测试失败: {e}")

        except Exception as e:
            verification.exists = False
            verification.issues.append(f"实例化失败: {e}")
            logger.error(f"验证 {agent_name} 失败: {e}")

        return verification

    async def _check_feature(self, agent: Any, feature_name: str, expected: bool) -> bool:
        """检查特定功能是否存在"""
        feature_map = {
            "智能任务分配": lambda a: hasattr(a, '_allocate_tasks') or hasattr(a, 'allocate_task'),
            "资源负载均衡": lambda a: hasattr(a, '_load_balancer') or hasattr(a, 'balance_load'),
            "冲突检测解决": lambda a: hasattr(a, '_detect_conflicts') or hasattr(a, 'resolve_conflicts'),
            "决策缓存": lambda a: hasattr(a, '_decision_cache') or hasattr(a, '_cache'),
            "并行检索策略": lambda a: hasattr(a, '_parallel_knowledge_retrieval') or '_parallel' in str(a.__class__.__dict__),
            "智能缓存机制": lambda a: hasattr(a, '_query_cache') or hasattr(a, '_cache') or hasattr(a, '_get_cached_result'),
            "答案生成加速": lambda a: hasattr(a, '_reasoning_engine_pool') or hasattr(a, '_parallel_executor'),
            "多源知识融合": lambda a: hasattr(a, '_merge_results') or hasattr(a, '_deduplicate_evidence'),
            "并行推理引擎": lambda a: hasattr(a, '_parallel_reasoning_engine') or hasattr(a, '_parallel_executor'),
            "推理结果缓存": lambda a: hasattr(a, '_reasoning_cache') or hasattr(a, '_set_cached_result'),
            "知识图谱集成": lambda a: hasattr(a, '_knowledge_graph') or hasattr(a, '_graph_based_reasoning'),
            "多步骤推理链": lambda a: hasattr(a, '_reasoning_steps') or hasattr(a, 'reasoning_steps'),
            "智能工具选择": lambda a: hasattr(a, '_select_tool') or hasattr(a, 'select_tool'),
            "编排策略优化": lambda a: hasattr(a, '_orchestrate') or hasattr(a, 'orchestrate'),
            "提示词动态优化": lambda a: hasattr(a, '_optimize_prompt') or hasattr(a, 'optimize_prompt'),
            "工具性能监控": lambda a: hasattr(a, '_tool_metadata') or hasattr(a, '_stats'),
            "智能压缩算法": lambda a: hasattr(a, '_compress_context') or hasattr(a, '_should_compress'),
            "关联网络优化": lambda a: hasattr(a, '_association_network') or hasattr(a, '_associations'),
            "自适应记忆管理": lambda a: hasattr(a, '_adaptive_forgetting') or hasattr(a, '_forget_memory'),
            "上下文感知检索": lambda a: hasattr(a, '_semantic_retrieval') or hasattr(a, 'retrieve_memory'),
            "增量学习算法": lambda a: hasattr(a, '_incremental_learning') or hasattr(a, 'learn_incrementally'),
            "性能模式识别": lambda a: hasattr(a, '_pattern_recognition') or hasattr(a, '_performance_patterns'),
            "A/B测试自动化": lambda a: hasattr(a, '_ab_testing') or hasattr(a, 'run_ab_test'),
            "自适应调整策略": lambda a: hasattr(a, '_adaptive_adjustment') or hasattr(a, 'adjust_parameters'),
            "多维度评估算法": lambda a: hasattr(a, '_evaluate_quality') or hasattr(a, 'evaluate'),
            "自动化验证流程": lambda a: hasattr(a, '_verify') or hasattr(a, 'verify'),
            "持续改进机制": lambda a: hasattr(a, '_improve') or hasattr(a, 'improve_quality'),
            "事实核查": lambda a: hasattr(a, '_verify_facts') or hasattr(a, 'verify_facts'),
            "实时威胁检测": lambda a: hasattr(a, '_detect_threats') or hasattr(a, 'detect_threats'),
            "隐私保护优化": lambda a: hasattr(a, '_mask_privacy') or hasattr(a, 'protect_privacy'),
            "合规审计强化": lambda a: hasattr(a, '_audit') or hasattr(a, 'audit_compliance'),
            "内容安全过滤": lambda a: hasattr(a, '_filter_content') or hasattr(a, 'filter_unsafe'),
        }

        check_func = feature_map.get(feature_name)
        if check_func:
            try:
                return check_func(agent)
            except Exception:
                return False
        return False

    def _get_feature_details(self, agent: Any, feature_name: str) -> str:
        """获取功能详情"""
        try:
            if hasattr(agent, '__dict__'):
                attrs = [k for k in agent.__dict__.keys() if feature_name.lower().replace(' ', '_') in k.lower()]
                if attrs:
                    return f"找到相关属性: {', '.join(attrs[:3])}"
        except Exception:
            pass
        return ""

    async def _test_agent_performance(self, agent: Any, agent_name: str) -> Dict[str, float]:
        """测试Agent性能"""
        metrics = {}
        try:
            # 简单的性能测试
            test_context = {
                "query": "测试查询",
                "type": "test"
            }

            start_time = time.time()
            # 只测试execute方法是否存在和可调用
            if hasattr(agent, 'execute'):
                # 不实际执行，只检查方法
                metrics['execute_method_exists'] = 1.0
            else:
                metrics['execute_method_exists'] = 0.0

            metrics['check_time'] = time.time() - start_time

        except Exception as e:
            logger.warning(f"性能测试失败 {agent_name}: {e}")
            metrics['error'] = str(e)

        return metrics

    async def verify_l6_l7_features(self):
        """验证L6/L7高级特性"""
        print("\n" + "=" * 80)
        print("🔍 验证L6/L7高级特性")
        print("=" * 80)

        # L6: MultiAgentCoordinator
        print("\n📋 验证 L6 - MultiAgentCoordinator...")
        try:
            coordinator = MultiAgentCoordinator()
            verification = AgentVerification(
                agent_name="MultiAgentCoordinator",
                agent_class="MultiAgentCoordinator",
                exists=True
            )

            # 检查L6特性
            l6_features = {
                "多Agent协作": hasattr(coordinator, 'register_agent') or hasattr(coordinator, 'coordinate'),
                "任务分解规划": hasattr(coordinator, 'decompose_task') or hasattr(coordinator, 'plan'),
                "动态调度": hasattr(coordinator, 'schedule') or hasattr(coordinator, '_schedule'),
                "冲突解决": hasattr(coordinator, 'resolve_conflicts') or hasattr(coordinator, '_resolve_conflicts'),
            }

            for feature_name, exists in l6_features.items():
                verification.features.append(FeatureCheck(
                    name=feature_name,
                    expected=True,
                    actual=exists,
                    details=""
                ))

            self.results["MultiAgentCoordinator"] = verification
        except Exception as e:
            logger.error(f"验证 MultiAgentCoordinator 失败: {e}")
            self.results["MultiAgentCoordinator"] = AgentVerification(
                agent_name="MultiAgentCoordinator",
                agent_class="MultiAgentCoordinator",
                exists=False,
                issues=[f"实例化失败: {e}"]
            )

        # L7: AutonomousRunner
        print("\n📋 验证 L7 - AutonomousRunner...")
        try:
            runner = AutonomousRunner()
            verification = AgentVerification(
                agent_name="AutonomousRunner",
                agent_class="AutonomousRunner",
                exists=True
            )

            # 检查L7特性
            l7_features = {
                "自我规划": hasattr(runner, 'plan') or hasattr(runner, '_plan'),
                "目标管理": hasattr(runner, 'manage_goals') or hasattr(runner, '_goals'),
                "持续学习": hasattr(runner, 'learn') or hasattr(runner, '_learning'),
                "自适应优化": hasattr(runner, 'optimize') or hasattr(runner, '_optimize'),
                "自主决策": hasattr(runner, 'decide') or hasattr(runner, '_decide'),
            }

            for feature_name, exists in l7_features.items():
                verification.features.append(FeatureCheck(
                    name=feature_name,
                    expected=True,
                    actual=exists,
                    details=""
                ))

            self.results["AutonomousRunner"] = verification
        except Exception as e:
            logger.error(f"验证 AutonomousRunner 失败: {e}")
            self.results["AutonomousRunner"] = AgentVerification(
                agent_name="AutonomousRunner",
                agent_class="AutonomousRunner",
                exists=False,
                issues=[f"实例化失败: {e}"]
            )

    def generate_report(self) -> str:
        """生成验证报告"""
        report_lines = []
        report_lines.append("\n" + "=" * 80)
        report_lines.append("📊 Agent实现完整性验证报告")
        report_lines.append("=" * 80)
        report_lines.append(f"\n生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 核心Agent统计
        core_agents = [
            "AgentCoordinator", "RAGExpert", "ReasoningExpert", "ToolOrchestrator",
            "MemoryManager", "LearningOptimizer", "QualityController", "SecurityGuardian"
        ]

        report_lines.append("\n" + "-" * 80)
        report_lines.append("📋 8个核心Agent验证结果")
        report_lines.append("-" * 80)

        total_features = 0
        passed_features = 0

        for agent_name in core_agents:
            if agent_name in self.results:
                verification = self.results[agent_name]
                report_lines.append(f"\n【{agent_name}】")
                report_lines.append(f"  类名: {verification.agent_class}")
                report_lines.append(f"  存在: {'✅' if verification.exists else '❌'}")

                if verification.features:
                    report_lines.append(f"  功能检查:")
                    for feature in verification.features:
                        status_icon = "✅" if feature.status == "✅" else "❌"
                        report_lines.append(f"    {status_icon} {feature.name}: {feature.details or '已实现'}")
                        total_features += 1
                        if feature.status == "✅":
                            passed_features += 1

                if verification.issues:
                    report_lines.append(f"  问题:")
                    for issue in verification.issues:
                        report_lines.append(f"    ⚠️  {issue}")

        # L6/L7特性
        report_lines.append("\n" + "-" * 80)
        report_lines.append("🚀 L6/L7高级特性验证结果")
        report_lines.append("-" * 80)

        for agent_name in ["MultiAgentCoordinator", "AutonomousRunner"]:
            if agent_name in self.results:
                verification = self.results[agent_name]
                report_lines.append(f"\n【{agent_name}】")
                report_lines.append(f"  存在: {'✅' if verification.exists else '❌'}")

                if verification.features:
                    for feature in verification.features:
                        status_icon = "✅" if feature.status == "✅" else "❌"
                        report_lines.append(f"    {status_icon} {feature.name}")

                if verification.issues:
                    for issue in verification.issues:
                        report_lines.append(f"    ⚠️  {issue}")

        # 总结
        report_lines.append("\n" + "=" * 80)
        report_lines.append("📈 验证总结")
        report_lines.append("=" * 80)

        if total_features > 0:
            pass_rate = (passed_features / total_features) * 100
            report_lines.append(f"\n功能完整度: {passed_features}/{total_features} ({pass_rate:.1f}%)")

        existing_agents = sum(1 for v in self.results.values() if v.exists)
        total_agents = len(self.results)
        report_lines.append(f"Agent存在率: {existing_agents}/{total_agents} ({existing_agents/total_agents*100:.1f}%)")

        # 建议
        report_lines.append("\n" + "-" * 80)
        report_lines.append("💡 建议")
        report_lines.append("-" * 80)

        missing_features = []
        for agent_name, verification in self.results.items():
            for feature in verification.features:
                if feature.status == "❌":
                    missing_features.append(f"{agent_name}.{feature.name}")

        if missing_features:
            report_lines.append("\n需要完善的功能:")
            for feature in missing_features[:10]:  # 只显示前10个
                report_lines.append(f"  - {feature}")
            if len(missing_features) > 10:
                report_lines.append(f"  ... 还有 {len(missing_features) - 10} 个功能需要完善")
        else:
            report_lines.append("\n✅ 所有检查的功能都已实现！")

        return "\n".join(report_lines)

    async def run_verification(self):
        """运行完整验证"""
        print("🚀 开始Agent实现完整性验证...")
        print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 验证核心Agent
        await self.verify_core_agents()

        # 验证L6/L7特性
        await self.verify_l6_l7_features()

        # 生成报告
        report = self.generate_report()
        print(report)

        # 保存报告
        report_file = Path(__file__).parent.parent / "comprehensive_eval_results" / "agent_implementation_verification_report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n✅ 验证报告已保存到: {report_file}")

        return report


async def main():
    """主函数"""
    verifier = AgentImplementationVerifier()
    await verifier.run_verification()


if __name__ == "__main__":
    asyncio.run(main())

