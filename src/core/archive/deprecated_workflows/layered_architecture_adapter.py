"""
分层架构适配器：LayeredArchitectureAdapter

提供新旧架构间的向后兼容性，支持平滑迁移。
能够在分层架构和传统架构间动态切换。
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

from .layered_architecture_types import (
    StrategicPlan, ExecutionParams, ExecutionResult, QueryAnalysis,
    SystemState, TaskDefinition, TaskResult
)
from ..agents.strategic_chief_agent_wrapper import StrategicChiefAgentWrapper as StrategicChiefAgent
from ..agents.tactical_optimizer import TacticalOptimizer
from ..agents.execution_coordinator import ExecutionCoordinator
from ..agents.chief_agent_wrapper import ChiefAgentWrapper as ChiefAgent

logger = logging.getLogger(__name__)


@dataclass
class CompatibilityMetrics:
    """兼容性指标"""
    layered_architecture_calls: int = 0
    legacy_architecture_calls: int = 0
    migration_candidates: int = 0
    performance_comparison: Dict[str, float] = field(default_factory=dict)
    error_rates: Dict[str, float] = field(default_factory=dict)


@dataclass
class AdapterConfiguration:
    """适配器配置"""
    use_new_architecture: bool = True
    enable_performance_comparison: bool = False
    fallback_to_legacy: bool = True
    migration_threshold: float = 0.8  # 性能阈值，超过此值推荐迁移
    gradual_rollout_percentage: float = 100.0  # 新架构使用百分比


class LayeredArchitectureAdapter:
    """
    分层架构适配器：提供向后兼容

    支持在新分层架构和传统架构间平滑切换，
    提供A/B测试能力和渐进式迁移支持。
    """

    def __init__(self, config: Optional[AdapterConfiguration] = None):
        self.config = config or AdapterConfiguration()
        self.metrics = CompatibilityMetrics()

        # 初始化新架构组件
        self.strategic_agent = StrategicChiefAgent()
        self.tactical_optimizer = TacticalOptimizer()
        self.execution_coordinator = ExecutionCoordinator()

        # 初始化旧架构组件
        self.legacy_chief_agent = ChiefAgent()

        # 性能比较缓存
        self.performance_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(f"分层架构适配器初始化: 新架构={'启用' if self.config.use_new_architecture else '禁用'}")

    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        统一查询处理接口

        支持新旧架构的透明切换和性能比较。
        """
        try:
            # 决定使用哪种架构
            use_new_architecture = self._should_use_new_architecture(query, context)

            if use_new_architecture:
                result = await self._process_with_layered_architecture(query, context)
                self.metrics.layered_architecture_calls += 1
            else:
                result = await self._process_with_legacy_architecture(query, context)
                self.metrics.legacy_architecture_calls += 1

            # 性能比较（如果启用）
            if self.config.enable_performance_comparison:
                await self._compare_architectures(query, context)

            # 添加架构信息到结果
            result['architecture_used'] = 'layered' if use_new_architecture else 'legacy'
            result['adapter_metrics'] = self._get_current_metrics()

            return result

        except Exception as e:
            logger.error(f"查询处理失败: {e}")

            # 如果新架构失败且允许回退，则使用旧架构
            if self.config.fallback_to_legacy and self.config.use_new_architecture:
                logger.info("新架构处理失败，回退到旧架构")
                try:
                    result = await self._process_with_legacy_architecture(query, context)
                    result['architecture_used'] = 'legacy_fallback'
                    result['fallback_reason'] = str(e)
                    return result
                except Exception as legacy_error:
                    logger.error(f"旧架构回退也失败: {legacy_error}")
                    raise legacy_error
            else:
                raise e

    async def _process_with_layered_architecture(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用分层架构处理查询"""
        try:
            logger.info("🎯 使用分层架构处理查询")

            # 准备查询分析（简化版，实际应该调用查询分析器）
            query_analysis = self._prepare_query_analysis(query, context)

            # 1. 战略决策
            logger.debug("📋 执行战略决策")
            strategic_plan = await self.strategic_agent.decide_strategy(query_analysis)

            # 2. 战术优化
            logger.debug("⚙️ 执行战术优化")
            execution_params = await self.tactical_optimizer.optimize_execution(strategic_plan, query_analysis)

            # 3. 执行协调
            logger.debug("🎭 执行协调")
            execution_result = await self.execution_coordinator.coordinate_execution(strategic_plan, execution_params)

            # 构建结果
            result = {
                'success': True,
                'answer': execution_result.final_answer,
                'quality_score': execution_result.quality_score,
                'execution_metrics': execution_result.execution_metrics,
                'task_results': execution_result.task_results,
                'strategic_plan': strategic_plan,
                'execution_params': execution_params,
                'architecture_details': {
                    'strategic_decisions': len(strategic_plan.tasks),
                    'tactical_optimizations': len(execution_params.timeouts),
                    'execution_tasks': len(execution_result.task_results)
                }
            }

            logger.info(f"✅ 分层架构处理完成，质量评分: {execution_result.quality_score:.2f}")
            return result

        except Exception as e:
            logger.error(f"分层架构处理失败: {e}")
            raise

    async def _process_with_legacy_architecture(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """使用传统架构处理查询"""
        try:
            logger.info("🏛️ 使用传统架构处理查询")

            # 准备旧架构期望的状态格式
            legacy_state = self._convert_to_legacy_state(query, context)

            # 调用旧的Chief Agent
            result = await self.legacy_chief_agent.execute(legacy_state)

            # 转换结果格式
            converted_result = {
                'success': result.success,
                'answer': result.data.get('answer', '') if result.data else '',
                'quality_score': result.data.get('quality_score', 0.7) if result.data else 0.7,
                'execution_metrics': result.metadata or {},
                'task_results': result.data.get('task_results', {}) if result.data else {},
                'legacy_format': True
            }

            logger.info("✅ 传统架构处理完成")
            return converted_result

        except Exception as e:
            logger.error(f"传统架构处理失败: {e}")
            raise

    async def _compare_architectures(self, query: str, context: Optional[Dict[str, Any]] = None) -> None:
        """比较两种架构的性能"""
        try:
            query_hash = str(hash(query + str(context)))

            # 如果已经有比较结果，跳过
            if query_hash in self.performance_cache:
                return

            # 并行执行两种架构
            layered_task = asyncio.create_task(self._process_with_layered_architecture(query, context))
            legacy_task = asyncio.create_task(self._process_with_legacy_architecture(query, context))

            results = await asyncio.gather(layered_task, legacy_task, return_exceptions=True)

            layered_result = results[0] if not isinstance(results[0], Exception) else None
            legacy_result = results[1] if not isinstance(results[1], Exception) else None

            # 计算性能指标
            comparison = {}
            if layered_result and legacy_result:
                layered_time = layered_result.get('execution_metrics', {}).get('total_time', 0)
                legacy_time = legacy_result.get('execution_metrics', {}).get('total_time', 0)

                if layered_time > 0 and legacy_time > 0:
                    comparison['performance_ratio'] = legacy_time / layered_time
                    comparison['quality_difference'] = (
                        layered_result.get('quality_score', 0) - legacy_result.get('quality_score', 0)
                    )

            self.performance_cache[query_hash] = {
                'layered_result': layered_result,
                'legacy_result': legacy_result,
                'comparison': comparison,
                'timestamp': asyncio.get_event_loop().time()
            }

            # 更新全局指标
            if comparison:
                self.metrics.performance_comparison = comparison

        except Exception as e:
            logger.error(f"架构性能比较失败: {e}")

    def _should_use_new_architecture(self, query: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """决定是否使用新架构"""
        if not self.config.use_new_architecture:
            return False

        # 渐进式发布控制
        import random
        if random.random() * 100 > self.config.gradual_rollout_percentage:
            return False

        # 基于查询复杂度决定（简单查询可以继续使用旧架构）
        query_complexity = self._assess_query_complexity(query, context)
        if query_complexity < 0.3:  # 简单查询
            return False

        # 基于性能历史决定
        if self.config.enable_performance_comparison and self.performance_cache:
            avg_performance_ratio = sum(
                comp.get('performance_ratio', 1.0)
                for comp in [item['comparison'] for item in self.performance_cache.values()]
                if 'performance_ratio' in comp
            ) / len(self.performance_cache)

            if avg_performance_ratio < self.config.migration_threshold:
                logger.info(f"性能不足，暂时使用旧架构 (性能比: {avg_performance_ratio:.2f})")
                return False

        return True

    def _assess_query_complexity(self, query: str, context: Optional[Dict[str, Any]] = None) -> float:
        """评估查询复杂度"""
        complexity = 0.0

        # 基于查询长度
        query_length = len(query)
        if query_length > 200:
            complexity += 0.3
        elif query_length > 50:
            complexity += 0.2

        # 基于关键词
        complex_keywords = ['compare', 'analyze', 'explain', 'why', 'how', 'multiple', 'complex']
        query_lower = query.lower()
        keyword_count = sum(1 for keyword in complex_keywords if keyword in query_lower)
        complexity += min(keyword_count * 0.1, 0.4)

        # 基于上下文
        if context:
            if context.get('requires_reasoning', False):
                complexity += 0.2
            if context.get('multimodal', False):
                complexity += 0.1

        return min(complexity, 1.0)

    def _prepare_query_analysis(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """准备查询分析（简化版）"""
        # 这里应该调用完整的查询分析器
        # 暂时提供简化实现
        complexity = self._assess_query_complexity(query, context)

        return QueryAnalysis(
            query=query,
            complexity_score=complexity,
            requires_reasoning=complexity > 0.5,
            estimated_difficulty='high' if complexity > 0.7 else 'medium' if complexity > 0.4 else 'low',
            context=context or {}
        )

    def _convert_to_legacy_state(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """转换为旧架构期望的状态格式"""
        return {
            'query': query,
            'context': context or {},
            'query_analysis': self._prepare_query_analysis(query, context).__dict__
        }

    def _get_current_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        total_calls = self.metrics.layered_architecture_calls + self.metrics.legacy_architecture_calls

        return {
            'layered_calls': self.metrics.layered_architecture_calls,
            'legacy_calls': self.metrics.legacy_architecture_calls,
            'total_calls': total_calls,
            'layered_percentage': (
                self.metrics.layered_architecture_calls / total_calls * 100
                if total_calls > 0 else 0
            )
        }

    def get_migration_recommendations(self) -> Dict[str, Any]:
        """获取迁移建议"""
        recommendations = {
            'ready_for_full_migration': False,
            'current_adoption_rate': 0.0,
            'performance_benefits': {},
            'risks_identified': [],
            'next_steps': []
        }

        total_calls = self.metrics.layered_architecture_calls + self.metrics.legacy_architecture_calls
        if total_calls > 100:  # 需要足够的样本
            adoption_rate = self.metrics.layered_architecture_calls / total_calls

            # 性能分析
            if self.performance_cache:
                avg_performance_ratio = sum(
                    comp.get('performance_ratio', 1.0)
                    for comp in [item['comparison'] for item in self.performance_cache.values()]
                    if 'performance_ratio' in comp
                ) / len([comp for comp in [item['comparison'] for item in self.performance_cache.values()]
                        if 'performance_ratio' in comp])

                recommendations['performance_benefits'] = {
                    'avg_performance_ratio': avg_performance_ratio,
                    'performance_improved': avg_performance_ratio > 1.0
                }

                if avg_performance_ratio > 1.05:  # 性能提升5%以上
                    recommendations['ready_for_full_migration'] = True

            recommendations['current_adoption_rate'] = adoption_rate

            if adoption_rate > 0.8:  # 80%以上的查询使用新架构
                recommendations['next_steps'].append("考虑完全迁移到新架构")
            elif adoption_rate > 0.5:  # 50%以上
                recommendations['next_steps'].append("继续渐进式迁移，增加新架构使用比例")
            else:
                recommendations['next_steps'].append("继续测试新架构，收集性能数据")

        return recommendations

    def switch_architecture(self, use_new: bool) -> None:
        """切换架构"""
        old_setting = self.config.use_new_architecture
        self.config.use_new_architecture = use_new

        logger.info(f"架构切换: {'新架构' if use_new else '旧架构'} (之前: {'新架构' if old_setting else '旧架构'})")

    def configure_rollout(self, percentage: float) -> None:
        """配置渐进式发布百分比"""
        old_percentage = self.config.gradual_rollout_percentage
        self.config.gradual_rollout_percentage = max(0.0, min(100.0, percentage))

        logger.info(f"渐进式发布配置更新: {old_percentage}% -> {self.config.gradual_rollout_percentage}%")

    async def cleanup(self) -> None:
        """清理资源"""
        # 清理性能缓存
        cutoff_time = asyncio.get_event_loop().time() - 3600  # 1小时前
        self.performance_cache = {
            k: v for k, v in self.performance_cache.items()
            if v.get('timestamp', 0) > cutoff_time
        }

        logger.info("适配器资源清理完成")


# 全局适配器实例
_adapter_instance = None

def get_layered_architecture_adapter(config: Optional[AdapterConfiguration] = None) -> LayeredArchitectureAdapter:
    """获取分层架构适配器实例"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = LayeredArchitectureAdapter(config)
    return _adapter_instance
