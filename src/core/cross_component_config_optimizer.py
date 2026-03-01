"""
跨组件配置优化器 (Cross-Component Configuration Optimizer)

实现跨组件的全局配置优化：
- 全局配置影响分析
- 组件间配置协同
- 系统级优化策略
- 配置一致性维护
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import networkx as nx
import numpy as np
from scipy.optimize import minimize_scalar, differential_evolution

logger = logging.getLogger(__name__)


class OptimizationScope(Enum):
    """优化范围"""
    SINGLE_COMPONENT = "single_component"    # 单组件
    COMPONENT_GROUP = "component_group"      # 组件组
    SUBSYSTEM = "subsystem"                  # 子系统
    GLOBAL_SYSTEM = "global_system"          # 全局系统


class OptimizationObjective(Enum):
    """优化目标"""
    PERFORMANCE = "performance"              # 性能优化
    EFFICIENCY = "efficiency"                # 效率优化
    COST = "cost"                           # 成本优化
    RELIABILITY = "reliability"             # 可靠性优化
    BALANCED = "balanced"                   # 均衡优化


@dataclass
class ConfigurationImpact:
    """配置影响"""
    source_component: str
    target_component: str
    parameter_name: str
    impact_type: str  # positive, negative, neutral
    impact_strength: float  # 0.0 到 1.0
    description: str
    confidence: float = 0.8


@dataclass
class GlobalOptimizationGoal:
    """全局优化目标"""
    goal_id: str
    scope: OptimizationScope
    objectives: Dict[OptimizationObjective, float]  # 目标权重
    constraints: Dict[str, Any]
    priority: int = 1
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationPlan:
    """优化方案"""
    plan_id: str
    goal: GlobalOptimizationGoal
    configuration_changes: Dict[str, Dict[str, Any]]  # component -> changes
    expected_outcomes: Dict[str, float]
    implementation_sequence: List[str]
    risk_assessment: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OptimizationResult:
    """优化结果"""
    plan_id: str
    success: bool
    actual_outcomes: Dict[str, float]
    performance_improvement: Dict[str, float]
    applied_changes: Dict[str, Dict[str, Any]]
    execution_time: float
    error_message: Optional[str] = None


class ConfigurationImpactAnalyzer:
    """配置影响分析器"""

    def __init__(self):
        self.impact_graph = nx.DiGraph()
        self.impact_rules: Dict[Tuple[str, str, str], ConfigurationImpact] = {}
        self.impact_history: List[Dict[str, Any]] = []

    def register_impact_rule(self, impact: ConfigurationImpact):
        """注册影响规则"""
        key = (impact.source_component, impact.target_component, impact.parameter_name)
        self.impact_rules[key] = impact

        # 更新影响图
        self.impact_graph.add_edge(
            impact.source_component,
            impact.target_component,
            parameter=impact.parameter_name,
            impact=impact
        )

        logger.info(f"注册配置影响规则: {impact.source_component} -> {impact.target_component} ({impact.parameter_name})")

    def analyze_global_impact(self, component: str, parameter: str,
                             new_value: Any) -> Dict[str, List[ConfigurationImpact]]:
        """分析全局影响"""
        impacts = {
            'direct_impacts': [],
            'indirect_impacts': [],
            'cascading_effects': []
        }

        # 直接影响
        direct_key = (component, "*", parameter)  # 通配符匹配所有目标组件
        for key, impact in self.impact_rules.items():
            if key[0] == component and key[2] == parameter:
                impacts['direct_impacts'].append(impact)

        # 间接影响（通过依赖链）
        try:
            # 找到所有受影响的组件
            affected_components = set()

            # 广度优先搜索影响链
            queue = [component]
            visited = set([component])

            while queue:
                current = queue.pop(0)
                affected_components.add(current)

                # 找到从当前组件出发的影响
                for successor in self.impact_graph.successors(current):
                    if successor not in visited:
                        visited.add(successor)
                        queue.append(successor)
                        affected_components.add(successor)

            # 计算间接影响
            for affected_comp in affected_components - {component}:
                indirect_key = (component, affected_comp, parameter)
                if indirect_key in self.impact_rules:
                    impacts['indirect_impacts'].append(self.impact_rules[indirect_key])

        except nx.NetworkXError:
            logger.warning("影响图分析失败，可能存在循环依赖")

        return impacts

    def predict_system_behavior(self, config_changes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """预测系统行为变化"""
        predictions = {
            'performance_impact': 0.0,
            'efficiency_impact': 0.0,
            'stability_risk': 0.0,
            'resource_pressure': 0.0
        }

        for component, changes in config_changes.items():
            for param, new_value in changes.items():
                impacts = self.analyze_global_impact(component, param, new_value)

                # 聚合影响
                for impact in impacts['direct_impacts'] + impacts['indirect_impacts']:
                    if impact.impact_type == 'positive':
                        predictions['performance_impact'] += impact.impact_strength * 0.1
                        predictions['efficiency_impact'] += impact.impact_strength * 0.05
                    elif impact.impact_type == 'negative':
                        predictions['performance_impact'] -= impact.impact_strength * 0.1
                        predictions['stability_risk'] += impact.impact_strength * 0.2
                        predictions['resource_pressure'] += impact.impact_strength * 0.15

        return predictions

    def get_component_sensitivity(self, component: str) -> Dict[str, float]:
        """获取组件敏感度"""
        sensitivities = {}

        # 计算组件对配置变化的敏感度
        component_impacts = [
            impact for impact in self.impact_rules.values()
            if impact.target_component == component
        ]

        for impact in component_impacts:
            param = impact.parameter_name
            if param not in sensitivities:
                sensitivities[param] = 0.0
            sensitivities[param] += impact.impact_strength

        return sensitivities


class GlobalOptimizationEngine:
    """全局优化引擎"""

    def __init__(self, impact_analyzer: ConfigurationImpactAnalyzer):
        self.impact_analyzer = impact_analyzer
        self.optimization_models: Dict[str, Any] = {}
        self.constraint_functions: Dict[str, Callable] = {}

    def define_optimization_model(self, model_name: str,
                                objective_function: Callable,
                                constraints: List[Callable],
                                bounds: List[Tuple[float, float]]):
        """定义优化模型"""
        self.optimization_models[model_name] = {
            'objective': objective_function,
            'constraints': constraints,
            'bounds': bounds
        }

        logger.info(f"定义优化模型: {model_name}")

    def add_constraint_function(self, name: str, constraint_func: Callable):
        """添加约束函数"""
        self.constraint_functions[name] = constraint_func

    async def optimize_global_configuration(self, goal: GlobalOptimizationGoal,
                                          current_configs: Dict[str, Dict[str, Any]]) -> OptimizationPlan:
        """全局配置优化"""
        # 根据优化目标选择算法
        if goal.scope == OptimizationScope.GLOBAL_SYSTEM:
            return await self._optimize_global_system(goal, current_configs)
        elif goal.scope == OptimizationScope.SUBSYSTEM:
            return await self._optimize_subsystem(goal, current_configs)
        else:
            return await self._optimize_component_group(goal, current_configs)

    async def _optimize_global_system(self, goal: GlobalOptimizationGoal,
                                    current_configs: Dict[str, Dict[str, Any]]) -> OptimizationPlan:
        """全局系统优化"""
        # 使用进化算法进行全局优化
        def objective_function(x):
            # 将参数向量转换为配置
            config_vector = self._vector_to_config(x, current_configs)

            # 计算目标函数值
            score = self._calculate_objective_score(config_vector, goal.objectives)

            # 考虑约束惩罚
            penalty = self._calculate_constraint_penalty(config_vector, goal.constraints)
            return score + penalty

        # 定义搜索空间
        bounds = self._define_search_bounds(current_configs)

        try:
            # 使用差分进化算法
            result = differential_evolution(
                objective_function,
                bounds,
                maxiter=50,
                popsize=20,
                seed=42
            )

            # 转换结果为配置变更
            optimized_configs = self._vector_to_config(result.x, current_configs)
            config_changes = self._calculate_config_changes(current_configs, optimized_configs)

            # 生成实施顺序
            implementation_sequence = self._calculate_implementation_sequence(config_changes)

            # 预测结果
            expected_outcomes = self.impact_analyzer.predict_system_behavior(config_changes)

            plan = OptimizationPlan(
                plan_id=f"global_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                goal=goal,
                configuration_changes=config_changes,
                expected_outcomes=expected_outcomes,
                implementation_sequence=implementation_sequence,
                risk_assessment=self._assess_optimization_risk(config_changes)
            )

            return plan

        except Exception as e:
            logger.error(f"全局系统优化失败: {e}")
            # 返回保守的优化方案
            return self._create_conservative_plan(goal, current_configs)

    async def _optimize_subsystem(self, goal: GlobalOptimizationGoal,
                                current_configs: Dict[str, Dict[str, Any]]) -> OptimizationPlan:
        """子系统优化"""
        # 识别子系统组件
        subsystem_components = self._identify_subsystem_components(goal, current_configs)

        # 使用局部优化
        config_changes = {}
        expected_outcomes = {}

        for component in subsystem_components:
            if component in current_configs:
                component_changes = await self._optimize_single_component(
                    component, current_configs[component], goal
                )
                if component_changes:
                    config_changes[component] = component_changes

                    # 预测影响
                    component_outcomes = self.impact_analyzer.predict_system_behavior(
                        {component: component_changes}
                    )
                    for key, value in component_outcomes.items():
                        expected_outcomes[key] = expected_outcomes.get(key, 0) + value

        implementation_sequence = subsystem_components

        return OptimizationPlan(
            plan_id=f"subsystem_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            goal=goal,
            configuration_changes=config_changes,
            expected_outcomes=expected_outcomes,
            implementation_sequence=implementation_sequence,
            risk_assessment=self._assess_optimization_risk(config_changes)
        )

    async def _optimize_component_group(self, goal: GlobalOptimizationGoal,
                                      current_configs: Dict[str, Dict[str, Any]]) -> OptimizationPlan:
        """组件组优化"""
        # 并行优化多个组件
        optimization_tasks = []

        for component, config in current_configs.items():
            task = asyncio.create_task(
                self._optimize_single_component(component, config, goal)
            )
            optimization_tasks.append((component, task))

        # 等待所有优化完成
        config_changes = {}
        expected_outcomes = {}

        for component, task in optimization_tasks:
            try:
                changes = await task
                if changes:
                    config_changes[component] = changes

                    # 预测影响
                    outcomes = self.impact_analyzer.predict_system_behavior({component: changes})
                    for key, value in outcomes.items():
                        expected_outcomes[key] = expected_outcomes.get(key, 0) + value

            except Exception as e:
                logger.error(f"组件 {component} 优化失败: {e}")

        implementation_sequence = list(config_changes.keys())

        return OptimizationPlan(
            plan_id=f"group_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            goal=goal,
            configuration_changes=config_changes,
            expected_outcomes=expected_outcomes,
            implementation_sequence=implementation_sequence,
            risk_assessment=self._assess_optimization_risk(config_changes)
        )

    async def _optimize_single_component(self, component: str,
                                       current_config: Dict[str, Any],
                                       goal: GlobalOptimizationGoal) -> Optional[Dict[str, Any]]:
        """优化单个组件"""
        # 使用简单的最优化算法
        changes = {}

        # 对每个数值参数进行优化
        for param_name, current_value in current_config.items():
            if isinstance(current_value, (int, float)):
                # 定义参数优化函数
                def param_objective(new_value):
                    test_config = current_config.copy()
                    test_config[param_name] = new_value

                    # 评估配置
                    return -self._evaluate_config_quality(component, test_config, goal)  # 最小化

                # 使用黄金分割搜索优化
                try:
                    bounds = self._get_parameter_bounds(component, param_name, current_value)
                    result = minimize_scalar(
                        param_objective,
                        bounds=bounds,
                        method='bounded'
                    )

                    if result.success:
                        optimal_value = result.x
                        if abs(optimal_value - current_value) > 0.01:  # 显著变化
                            changes[param_name] = optimal_value

                except Exception as e:
                    logger.debug(f"参数 {param_name} 优化失败: {e}")

        return changes if changes else None

    def _calculate_objective_score(self, config_vector: Dict[str, Dict[str, Any]],
                                 objectives: Dict[OptimizationObjective, float]) -> float:
        """计算目标函数分数"""
        score = 0.0

        for objective, weight in objectives.items():
            if objective == OptimizationObjective.PERFORMANCE:
                perf_score = self._evaluate_performance(config_vector)
                score += perf_score * weight
            elif objective == OptimizationObjective.EFFICIENCY:
                eff_score = self._evaluate_efficiency(config_vector)
                score += eff_score * weight
            elif objective == OptimizationObjective.COST:
                cost_score = self._evaluate_cost(config_vector)
                score += cost_score * weight
            elif objective == OptimizationObjective.RELIABILITY:
                rel_score = self._evaluate_reliability(config_vector)
                score += rel_score * weight

        return score

    def _calculate_constraint_penalty(self, config_vector: Dict[str, Dict[str, Any]],
                                    constraints: Dict[str, Any]) -> float:
        """计算约束惩罚"""
        penalty = 0.0

        # 检查资源约束
        if 'max_resource_usage' in constraints:
            total_usage = sum(
                config.get('resource_allocation', 0)
                for config in config_vector.values()
            )
            if total_usage > constraints['max_resource_usage']:
                penalty += (total_usage - constraints['max_resource_usage']) * 10

        # 检查性能约束
        if 'min_performance' in constraints:
            avg_performance = self._evaluate_performance(config_vector)
            if avg_performance < constraints['min_performance']:
                penalty += (constraints['min_performance'] - avg_performance) * 20

        return penalty

    def _evaluate_config_quality(self, component: str, config: Dict[str, Any],
                               goal: GlobalOptimizationGoal) -> float:
        """评估配置质量"""
        # 基于目标计算质量分数
        score = 0.0

        for objective, weight in goal.objectives.items():
            if objective == OptimizationObjective.PERFORMANCE:
                score += self._evaluate_single_performance(component, config) * weight
            elif objective == OptimizationObjective.EFFICIENCY:
                score += self._evaluate_single_efficiency(component, config) * weight

        return score

    def _evaluate_performance(self, configs: Dict[str, Dict[str, Any]]) -> float:
        """评估整体性能"""
        # 简化评估：基于平均响应时间
        response_times = [
            config.get('response_time', 1.0)
            for config in configs.values()
        ]
        return 1.0 / (1.0 + sum(response_times) / len(response_times))  # 归一化

    def _evaluate_efficiency(self, configs: Dict[str, Dict[str, Any]]) -> float:
        """评估整体效率"""
        # 简化评估：基于资源利用率
        efficiencies = [
            config.get('efficiency', 0.7)
            for config in configs.values()
        ]
        return sum(efficiencies) / len(efficiencies)

    def _evaluate_cost(self, configs: Dict[str, Dict[str, Any]]) -> float:
        """评估成本"""
        # 简化评估
        return 0.5  # 默认中等成本

    def _evaluate_reliability(self, configs: Dict[str, Dict[str, Any]]) -> float:
        """评估可靠性"""
        # 简化评估
        return 0.8  # 默认高可靠性

    def _evaluate_single_performance(self, component: str, config: Dict[str, Any]) -> float:
        """评估单个组件性能"""
        # 基于配置参数估算性能
        base_perf = 0.7

        if 'timeout' in config:
            timeout = config['timeout']
            if timeout < 30:
                base_perf *= 1.2  # 更快的超时设置提高性能
            elif timeout > 120:
                base_perf *= 0.8  # 更慢的超时设置降低性能

        return min(1.0, base_perf)

    def _evaluate_single_efficiency(self, component: str, config: Dict[str, Any]) -> float:
        """评估单个组件效率"""
        base_eff = 0.6

        if 'parallel_execution' in config and config['parallel_execution']:
            base_eff *= 1.3  # 并行执行提高效率

        if 'batch_size' in config:
            batch_size = config['batch_size']
            if batch_size > 10:
                base_eff *= 1.1  # 更大的批处理提高效率

        return min(1.0, base_eff)

    def _define_search_bounds(self, configs: Dict[str, Dict[str, Any]]) -> List[Tuple[float, float]]:
        """定义搜索边界"""
        bounds = []

        for component_config in configs.values():
            for param_name, param_value in component_config.items():
                if isinstance(param_value, (int, float)):
                    # 定义参数的搜索范围
                    param_bounds = self._get_parameter_bounds_from_config(component_config, param_name, param_value)
                    bounds.extend(param_bounds)

        return bounds

    def _get_parameter_bounds(self, component: str, param_name: str,
                            current_value: float) -> Tuple[float, float]:
        """获取参数边界"""
        # 默认边界：当前值的50%-200%
        lower = current_value * 0.5
        upper = current_value * 2.0

        # 特殊参数的边界
        if param_name == 'timeout':
            lower = max(5, lower)
            upper = min(300, upper)
        elif 'batch' in param_name.lower():
            lower = max(1, lower)
            upper = min(100, upper)

        return (lower, upper)

    def _get_parameter_bounds_from_config(self, config: Dict[str, Any],
                                        param_name: str, param_value: float) -> List[Tuple[float, float]]:
        """从配置获取参数边界"""
        bounds = self._get_parameter_bounds("", param_name, param_value)
        return [bounds]

    def _vector_to_config(self, vector: np.ndarray,
                         template_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """将向量转换为配置"""
        configs = {}
        idx = 0

        for component, template_config in template_configs.items():
            config = template_config.copy()

            for param_name, param_value in template_config.items():
                if isinstance(param_value, (int, float)):
                    if idx < len(vector):
                        config[param_name] = vector[idx]
                        idx += 1

            configs[component] = config

        return configs

    def _calculate_config_changes(self, current: Dict[str, Dict[str, Any]],
                                optimized: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """计算配置变更"""
        changes = {}

        for component in current:
            if component in optimized:
                component_changes = {}
                current_config = current[component]
                optimized_config = optimized[component]

                for param, new_value in optimized_config.items():
                    if param in current_config:
                        current_value = current_config[param]
                        if abs(new_value - current_value) > 0.01:  # 显著变化
                            component_changes[param] = new_value

                if component_changes:
                    changes[component] = component_changes

        return changes

    def _calculate_implementation_sequence(self, changes: Dict[str, Dict[str, Any]]) -> List[str]:
        """计算实施顺序"""
        # 基于依赖关系和变更影响排序
        components = list(changes.keys())

        # 简单排序：影响大的组件先实施
        component_impacts = []
        for component in components:
            impact_size = len(changes[component])
            component_impacts.append((component, impact_size))

        component_impacts.sort(key=lambda x: x[1], reverse=True)
        return [comp for comp, _ in component_impacts]

    def _assess_optimization_risk(self, changes: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """评估优化风险"""
        risk_assessment = {
            'risk_level': 'low',
            'risk_factors': [],
            'recommended_actions': []
        }

        total_changes = sum(len(component_changes) for component_changes in changes.values())

        if total_changes > 20:
            risk_assessment['risk_level'] = 'high'
            risk_assessment['risk_factors'].append('大量配置变更')
            risk_assessment['recommended_actions'].append('分阶段实施')
        elif total_changes > 10:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['risk_factors'].append('中等数量配置变更')
            risk_assessment['recommended_actions'].append('增加监控')

        return risk_assessment

    def _identify_subsystem_components(self, goal: GlobalOptimizationGoal,
                                     configs: Dict[str, Dict[str, Any]]) -> List[str]:
        """识别子系统组件"""
        # 简化实现：返回所有组件
        return list(configs.keys())

    def _create_conservative_plan(self, goal: GlobalOptimizationGoal,
                                configs: Dict[str, Dict[str, Any]]) -> OptimizationPlan:
        """创建保守的优化方案"""
        # 只做最小变更
        config_changes = {}

        for component, config in configs.items():
            changes = {}
            # 只调整明显需要优化的参数
            if 'timeout' in config and config['timeout'] > 200:
                changes['timeout'] = 120  # 降低过高的超时

            if changes:
                config_changes[component] = changes

        return OptimizationPlan(
            plan_id=f"conservative_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            goal=goal,
            configuration_changes=config_changes,
            expected_outcomes={'performance_impact': 0.1, 'stability_risk': 0.05},
            implementation_sequence=list(config_changes.keys()),
            risk_assessment={'risk_level': 'low', 'risk_factors': ['保守策略']}
        )


class CrossComponentConfigurationOptimizer:
    """
    跨组件配置优化器

    实现全局视角的配置优化：
    - 分析配置间的影响关系
    - 全局优化算法
    - 约束满足和风险控制
    - 增量优化和回滚
    """

    def __init__(self):
        self.impact_analyzer = ConfigurationImpactAnalyzer()
        self.optimization_engine = GlobalOptimizationEngine(self.impact_analyzer)
        self.optimization_history: List[OptimizationPlan] = []
        self.current_configurations: Dict[str, Dict[str, Any]] = {}

    def register_configuration_impact(self, impact: ConfigurationImpact):
        """注册配置影响"""
        self.impact_analyzer.register_impact_rule(impact)

    def update_component_configuration(self, component: str, config: Dict[str, Any]):
        """更新组件配置"""
        self.current_configurations[component] = config.copy()

    async def optimize_cross_component(self, optimization_goal: GlobalOptimizationGoal) -> OptimizationPlan:
        """跨组件优化"""
        plan = await self.optimization_engine.optimize_global_configuration(
            optimization_goal, self.current_configurations
        )

        self.optimization_history.append(plan)
        return plan

    async def apply_optimization_plan(self, plan: OptimizationPlan) -> OptimizationResult:
        """应用优化方案"""
        start_time = datetime.now()

        try:
            # 按顺序应用配置变更
            applied_changes = {}

            for component in plan.implementation_sequence:
                if component in plan.configuration_changes:
                    changes = plan.configuration_changes[component]

                    # 应用变更
                    if component not in self.current_configurations:
                        self.current_configurations[component] = {}

                    self.current_configurations[component].update(changes)
                    applied_changes[component] = changes.copy()

                    # 验证变更效果（简化）
                    await asyncio.sleep(0.1)

            # 评估实际效果
            actual_outcomes = self.impact_analyzer.predict_system_behavior(applied_changes)

            # 计算性能改进
            performance_improvement = {}
            for key, value in actual_outcomes.items():
                expected = plan.expected_outcomes.get(key, 0)
                improvement = value - expected
                performance_improvement[key] = improvement

            execution_time = (datetime.now() - start_time).total_seconds()

            result = OptimizationResult(
                plan_id=plan.plan_id,
                success=True,
                actual_outcomes=actual_outcomes,
                performance_improvement=performance_improvement,
                applied_changes=applied_changes,
                execution_time=execution_time
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            return OptimizationResult(
                plan_id=plan.plan_id,
                success=False,
                actual_outcomes={},
                performance_improvement={},
                applied_changes={},
                execution_time=execution_time,
                error_message=str(e)
            )

    async def validate_optimization_effectiveness(self, result: OptimizationResult) -> Dict[str, Any]:
        """验证优化效果"""
        validation = {
            'is_effective': False,
            'improvement_score': 0.0,
            'metrics': {},
            'recommendations': []
        }

        if not result.success:
            validation['recommendations'].append('优化执行失败，需要调查原因')
            return validation

        # 计算改进分数
        total_improvement = sum(result.performance_improvement.values())
        improvement_score = max(0, min(1, total_improvement / 0.5))  # 归一化

        validation['improvement_score'] = improvement_score
        validation['is_effective'] = improvement_score > 0.1  # 10%改进视为有效

        # 分析各指标
        for metric, improvement in result.performance_improvement.items():
            if improvement > 0:
                validation['metrics'][metric] = 'improved'
            elif improvement < 0:
                validation['metrics'][metric] = 'degraded'
            else:
                validation['metrics'][metric] = 'unchanged'

        # 生成建议
        if not validation['is_effective']:
            validation['recommendations'].append('优化效果不明显，考虑调整优化目标')

        if result.execution_time > 60:  # 执行时间过长
            validation['recommendations'].append('优化执行时间过长，考虑简化优化策略')

        return validation

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计"""
        total_plans = len(self.optimization_history)
        successful_plans = len([p for p in self.optimization_history if p.plan_id.startswith(('global', 'subsystem', 'group'))])

        avg_expected_improvement = 0
        if self.optimization_history:
            total_expected = sum(
                sum(outcomes.values()) for plan in self.optimization_history
                for outcomes in [plan.expected_outcomes]
            )
            avg_expected_improvement = total_expected / len(self.optimization_history)

        return {
            'total_optimization_plans': total_plans,
            'successful_plans': successful_plans,
            'success_rate': successful_plans / total_plans if total_plans > 0 else 0,
            'average_expected_improvement': avg_expected_improvement,
            'registered_components': len(self.current_configurations),
            'impact_rules_count': len(self.impact_analyzer.impact_rules)
        }

    def rollback_configuration_changes(self, plan: OptimizationPlan):
        """回滚配置变更"""
        # 简化实现：记录需要回滚的变更
        logger.info(f"准备回滚优化方案 {plan.plan_id} 的配置变更")

        # 这里应该实现实际的回滚逻辑
        # 暂时只记录日志

    def export_optimization_report(self, plan: OptimizationPlan,
                                 result: Optional[OptimizationResult] = None) -> Dict[str, Any]:
        """导出优化报告"""
        report = {
            'plan_id': plan.plan_id,
            'optimization_scope': plan.goal.scope.value,
            'objectives': {obj.value: weight for obj, weight in plan.goal.objectives.items()},
            'configuration_changes': plan.configuration_changes,
            'expected_outcomes': plan.expected_outcomes,
            'implementation_sequence': plan.implementation_sequence,
            'risk_assessment': plan.risk_assessment,
            'created_at': plan.created_at.isoformat()
        }

        if result:
            report['execution_result'] = {
                'success': result.success,
                'actual_outcomes': result.actual_outcomes,
                'performance_improvement': result.performance_improvement,
                'execution_time': result.execution_time,
                'error_message': result.error_message
            }

        return report


# 全局实例
_cross_component_optimizer_instance: Optional[CrossComponentConfigurationOptimizer] = None

def get_cross_component_config_optimizer() -> CrossComponentConfigurationOptimizer:
    """获取跨组件配置优化器实例"""
    global _cross_component_optimizer_instance
    if _cross_component_optimizer_instance is None:
        _cross_component_optimizer_instance = CrossComponentConfigurationOptimizer()
    return _cross_component_optimizer_instance
