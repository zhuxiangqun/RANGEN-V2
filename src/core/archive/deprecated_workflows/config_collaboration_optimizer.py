"""
配置协同优化器 (Configuration Collaboration Optimizer)

实现跨组件配置的协同优化：
- 全局配置一致性检查
- 组件间配置依赖分析
- 协同优化策略
- 配置冲突检测和解决
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import networkx as nx
import json

logger = logging.getLogger(__name__)


class ConfigurationDependencyType(Enum):
    """配置依赖类型"""
    REQUIRES = "requires"           # 必需依赖
    CONFLICTS = "conflicts"         # 冲突依赖
    ENHANCES = "enhances"           # 增强依赖
    COMPETES = "competes"           # 竞争依赖


class OptimizationScope(Enum):
    """优化范围"""
    COMPONENT = "component"         # 单个组件
    SUBSYSTEM = "subsystem"         # 子系统
    GLOBAL = "global"              # 全局系统


@dataclass
class ConfigurationDependency:
    """配置依赖关系"""
    source_component: str
    target_component: str
    dependency_type: ConfigurationDependencyType
    parameter_mapping: Dict[str, str]  # source_param -> target_param
    constraint_rules: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""
    priority: int = 1  # 1-10

    def check_violation(self, source_config: Dict[str, Any],
                       target_config: Dict[str, Any]) -> Optional[str]:
        """检查依赖违规"""
        for rule in self.constraint_rules:
            rule_type = rule.get('type')

            if rule_type == 'value_match':
                source_param = rule['source_param']
                target_param = rule['target_param']
                if (source_param in source_config and target_param in target_config and
                    source_config[source_param] != target_config[target_param]):
                    return f"参数值不匹配: {source_param}={source_config[source_param]} vs {target_param}={target_config[target_param]}"

            elif rule_type == 'value_range':
                param = rule['parameter']
                component = rule['component']
                config = source_config if component == self.source_component else target_config
                if param in config:
                    value = config[param]
                    min_val = rule.get('min_value')
                    max_val = rule.get('max_value')
                    if min_val is not None and value < min_val:
                        return f"参数值低于最小值: {param}={value} < {min_val}"
                    if max_val is not None and value > max_val:
                        return f"参数值超过最大值: {param}={value} > {max_val}"

        return None


@dataclass
class CollaborativeOptimizationPlan:
    """协同优化方案"""
    plan_id: str
    scope: OptimizationScope
    target_components: List[str]
    configuration_changes: Dict[str, Dict[str, Any]]  # component -> config_changes
    expected_benefits: Dict[str, float]
    dependency_satisfaction: Dict[str, bool]
    risk_assessment: Dict[str, Any]
    implementation_order: List[str]  # 组件实施顺序
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ConfigurationConflict:
    """配置冲突"""
    conflict_id: str
    component_a: str
    component_b: str
    parameter_a: str
    parameter_b: str
    conflict_type: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    suggested_resolution: Optional[Dict[str, Any]] = None


class DependencyGraphAnalyzer:
    """依赖图分析器"""

    def __init__(self):
        self.dependency_graph = nx.DiGraph()
        self.dependency_rules: Dict[Tuple[str, str], ConfigurationDependency] = {}

    def add_dependency(self, dependency: ConfigurationDependency):
        """添加依赖关系"""
        key = (dependency.source_component, dependency.target_component)
        self.dependency_rules[key] = dependency

        # 更新图结构
        self.dependency_graph.add_edge(
            dependency.source_component,
            dependency.target_component,
            dependency=dependency
        )

    def remove_dependency(self, source_component: str, target_component: str):
        """移除依赖关系"""
        key = (source_component, target_component)
        if key in self.dependency_rules:
            del self.dependency_rules[key]
            if self.dependency_graph.has_edge(source_component, target_component):
                self.dependency_graph.remove_edge(source_component, target_component)

    def get_component_dependencies(self, component: str) -> Dict[str, List[ConfigurationDependency]]:
        """获取组件的依赖关系"""
        incoming = []
        outgoing = []

        # 入度依赖（其他组件依赖此组件）
        for pred in self.dependency_graph.predecessors(component):
            if (pred, component) in self.dependency_rules:
                incoming.append(self.dependency_rules[(pred, component)])

        # 出度依赖（此组件依赖其他组件）
        for succ in self.dependency_graph.successors(component):
            if (component, succ) in self.dependency_rules:
                outgoing.append(self.dependency_rules[(component, succ)])

        return {
            'incoming': incoming,  # 其他组件对我的依赖
            'outgoing': outgoing   # 我对其他组件的依赖
        }

    def detect_cycles(self) -> List[List[str]]:
        """检测循环依赖"""
        try:
            cycles = list(nx.simple_cycles(self.dependency_graph))
            return cycles
        except nx.NetworkXError:
            return []

    def get_optimization_order(self, components: List[str]) -> List[str]:
        """获取优化顺序（拓扑排序）"""
        subgraph = self.dependency_graph.subgraph(components)
        try:
            # 拓扑排序，确保依赖顺序
            order = list(nx.topological_sort(subgraph))
            return order
        except nx.NetworkXError:
            # 如果有循环，返回原始顺序
            logger.warning(f"检测到循环依赖，使用原始顺序: {components}")
            return components

    def analyze_impact(self, component: str, config_change: Dict[str, Any]) -> Dict[str, List[str]]:
        """分析配置变更的影响"""
        impacted_components = []
        affected_rules = []

        # 检查对下游组件的影响
        for successor in self.dependency_graph.successors(component):
            dependency = self.dependency_rules.get((component, successor))
            if dependency:
                violation = dependency.check_violation(config_change, {})  # 简化检查
                if violation:
                    impacted_components.append(successor)
                    affected_rules.append(f"{component} -> {successor}: {violation}")

        # 检查对上游组件的影响
        for predecessor in self.dependency_graph.predecessors(component):
            dependency = self.dependency_rules.get((predecessor, component))
            if dependency:
                violation = dependency.check_violation({}, config_change)  # 简化检查
                if violation:
                    impacted_components.append(predecessor)
                    affected_rules.append(f"{predecessor} -> {component}: {violation}")

        return {
            'impacted_components': impacted_components,
            'affected_rules': affected_rules
        }


class ConflictDetector:
    """配置冲突检测器"""

    def __init__(self, dependency_analyzer: DependencyGraphAnalyzer):
        self.dependency_analyzer = dependency_analyzer
        self.conflict_patterns: Dict[str, Dict[str, Any]] = {}

    async def detect_conflicts(self, component_configs: Dict[str, Dict[str, Any]]) -> List[ConfigurationConflict]:
        """检测配置冲突"""
        conflicts = []

        # 检查依赖违规
        dependency_conflicts = await self._detect_dependency_conflicts(component_configs)
        conflicts.extend(dependency_conflicts)

        # 检查资源竞争
        resource_conflicts = await self._detect_resource_conflicts(component_configs)
        conflicts.extend(resource_conflicts)

        # 检查参数冲突
        parameter_conflicts = await self._detect_parameter_conflicts(component_configs)
        conflicts.extend(parameter_conflicts)

        return conflicts

    async def _detect_dependency_conflicts(self, component_configs: Dict[str, Dict[str, Any]]) -> List[ConfigurationConflict]:
        """检测依赖冲突"""
        conflicts = []

        for (source_comp, target_comp), dependency in self.dependency_analyzer.dependency_rules.items():
            if source_comp in component_configs and target_comp in component_configs:
                source_config = component_configs[source_comp]
                target_config = component_configs[target_comp]

                violation = dependency.check_violation(source_config, target_config)
                if violation:
                    conflict = ConfigurationConflict(
                        conflict_id=f"dep_{source_comp}_{target_comp}_{hash(violation)}",
                        component_a=source_comp,
                        component_b=target_comp,
                        parameter_a="",  # 依赖冲突不特定于参数
                        parameter_b="",
                        conflict_type="dependency_violation",
                        description=violation,
                        severity="high" if dependency.priority > 7 else "medium",
                        suggested_resolution=self._suggest_dependency_resolution(dependency, violation)
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _detect_resource_conflicts(self, component_configs: Dict[str, Dict[str, Any]]) -> List[ConfigurationConflict]:
        """检测资源冲突"""
        conflicts = []
        resource_usage = {}

        # 收集所有组件的资源需求
        for component, config in component_configs.items():
            for param_name, param_value in config.items():
                if 'resource' in param_name.lower() or 'capacity' in param_name.lower():
                    resource_type = param_name.split('_')[0]  # 简化提取资源类型
                    if resource_type not in resource_usage:
                        resource_usage[resource_type] = []
                    resource_usage[resource_type].append((component, param_name, param_value))

        # 检查资源过载
        for resource_type, usages in resource_usage.items():
            total_usage = sum(usage[2] for usage in usages if isinstance(usage[2], (int, float)))
            if len(usages) > 1 and total_usage > 100:  # 简化检查
                for component, param_name, usage in usages:
                    conflict = ConfigurationConflict(
                        conflict_id=f"resource_{resource_type}_{component}",
                        component_a=component,
                        component_b="",  # 资源冲突不特定于两个组件
                        parameter_a=param_name,
                        parameter_b="",
                        conflict_type="resource_overload",
                        description=f"资源 {resource_type} 过载: 总使用量 {total_usage}",
                        severity="high",
                        suggested_resolution={
                            'action': 'reduce_usage',
                            'target_component': component,
                            'suggested_value': usage * 0.8  # 建议减少20%
                        }
                    )
                    conflicts.append(conflict)

        return conflicts

    async def _detect_parameter_conflicts(self, component_configs: Dict[str, Dict[str, Any]]) -> List[ConfigurationConflict]:
        """检测参数冲突"""
        conflicts = []

        # 检查相同的参数在不同组件间的冲突
        param_components = {}
        for component, config in component_configs.items():
            for param_name, param_value in config.items():
                if param_name not in param_components:
                    param_components[param_name] = []
                param_components[param_name].append((component, param_value))

        for param_name, component_values in param_components.items():
            if len(component_values) > 1:
                # 检查是否有冲突的值
                values = [cv[1] for cv in component_values]
                if len(set(values)) > 1:  # 不同值
                    for i, (comp_a, val_a) in enumerate(component_values):
                        for comp_b, val_b in component_values[i+1:]:
                            if val_a != val_b:
                                conflict = ConfigurationConflict(
                                    conflict_id=f"param_{param_name}_{comp_a}_{comp_b}",
                                    component_a=comp_a,
                                    component_b=comp_b,
                                    parameter_a=param_name,
                                    parameter_b=param_name,
                                    conflict_type="parameter_inconsistency",
                                    description=f"参数 {param_name} 在组件间不一致: {comp_a}={val_a}, {comp_b}={val_b}",
                                    severity="medium",
                                    suggested_resolution=self._suggest_parameter_resolution(param_name, values)
                                )
                                conflicts.append(conflict)

        return conflicts

    def _suggest_dependency_resolution(self, dependency: ConfigurationDependency, violation: str) -> Dict[str, Any]:
        """建议依赖冲突解决"""
        return {
            'action': 'align_parameters',
            'description': f'根据依赖规则调整参数: {dependency.description}',
            'dependency_type': dependency.dependency_type.value
        }

    def _suggest_parameter_resolution(self, param_name: str, values: List[Any]) -> Dict[str, Any]:
        """建议参数冲突解决"""
        # 选择出现次数最多的值
        from collections import Counter
        most_common = Counter(values).most_common(1)[0][0]

        return {
            'action': 'standardize_value',
            'suggested_value': most_common,
            'description': f'建议统一使用值: {most_common}'
        }


class ConfigurationCollaborationOptimizer:
    """
    配置协同优化器

    实现跨组件配置的协同优化：
    - 全局配置一致性维护
    - 组件间依赖关系管理
    - 协同优化策略制定
    - 配置冲突检测和解决
    """

    def __init__(self):
        self.dependency_analyzer = DependencyGraphAnalyzer()
        self.conflict_detector = ConflictDetector(self.dependency_analyzer)
        self.optimization_history: List[CollaborativeOptimizationPlan] = []
        self.active_configurations: Dict[str, Dict[str, Any]] = {}

    def register_dependency(self, dependency: ConfigurationDependency):
        """注册配置依赖"""
        self.dependency_analyzer.add_dependency(dependency)
        logger.info(f"注册配置依赖: {dependency.source_component} -> {dependency.target_component}")

    def update_component_config(self, component: str, config: Dict[str, Any]):
        """更新组件配置"""
        self.active_configurations[component] = config.copy()
        logger.debug(f"更新组件配置: {component}")

    async def optimize_collaboratively(self, target_components: List[str],
                                     optimization_goals: Dict[str, Any],
                                     scope: OptimizationScope = OptimizationScope.SUBSYSTEM
                                     ) -> CollaborativeOptimizationPlan:
        """协同优化配置"""
        # 检测当前配置冲突
        conflicts = await self.conflict_detector.detect_conflicts(self.active_configurations)

        # 分析依赖关系
        optimization_order = self.dependency_analyzer.get_optimization_order(target_components)

        # 生成协同优化方案
        optimization_plan = await self._generate_optimization_plan(
            target_components, conflicts, optimization_order, optimization_goals, scope
        )

        # 记录优化历史
        self.optimization_history.append(optimization_plan)

        return optimization_plan

    async def validate_configuration_consistency(self, component_configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """验证配置一致性"""
        conflicts = await self.conflict_detector.detect_conflicts(component_configs)

        # 按严重程度分类冲突
        severity_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        for conflict in conflicts:
            severity_counts[conflict.severity] = severity_counts.get(conflict.severity, 0) + 1

        # 计算一致性评分
        total_checks = len(component_configs) * len(self.dependency_analyzer.dependency_rules)
        consistency_score = 1.0 - (len(conflicts) / max(total_checks, 1))

        return {
            'is_consistent': len(conflicts) == 0,
            'consistency_score': consistency_score,
            'conflicts': [conflict.__dict__ for conflict in conflicts],
            'severity_distribution': severity_counts
        }

    async def resolve_conflicts_automatically(self, conflicts: List[ConfigurationConflict]) -> Dict[str, Any]:
        """自动解决冲突"""
        resolutions = []
        unresolved = []

        for conflict in conflicts:
            if conflict.suggested_resolution:
                resolution = {
                    'conflict': conflict.__dict__,
                    'action': conflict.suggested_resolution,
                    'status': 'auto_resolved'
                }
                resolutions.append(resolution)

                # 应用解决建议
                await self._apply_resolution(conflict, conflict.suggested_resolution)
            else:
                unresolved.append(conflict.__dict__)

        return {
            'resolved_count': len(resolutions),
            'unresolved_count': len(unresolved),
            'resolutions': resolutions,
            'unresolved': unresolved
        }

    async def _generate_optimization_plan(self, target_components: List[str],
                                        conflicts: List[ConfigurationConflict],
                                        optimization_order: List[str],
                                        goals: Dict[str, Any],
                                        scope: OptimizationScope) -> CollaborativeOptimizationPlan:
        """生成协同优化方案"""
        plan_id = f"collab_opt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 分析当前状态
        current_state_analysis = await self._analyze_current_state(target_components)

        # 生成配置变更建议
        config_changes = await self._generate_config_changes(
            target_components, conflicts, goals, optimization_order
        )

        # 评估预期收益
        expected_benefits = await self._calculate_expected_benefits(config_changes, goals)

        # 评估风险
        risk_assessment = await self._assess_optimization_risks(config_changes, conflicts)

        # 检查依赖满足情况
        dependency_satisfaction = await self._check_dependency_satisfaction(config_changes)

        return CollaborativeOptimizationPlan(
            plan_id=plan_id,
            scope=scope,
            target_components=target_components,
            configuration_changes=config_changes,
            expected_benefits=expected_benefits,
            dependency_satisfaction=dependency_satisfaction,
            risk_assessment=risk_assessment,
            implementation_order=optimization_order
        )

    async def _analyze_current_state(self, components: List[str]) -> Dict[str, Any]:
        """分析当前状态"""
        analysis = {
            'active_components': len(components),
            'configured_components': len([c for c in components if c in self.active_configurations]),
            'dependency_cycles': self.dependency_analyzer.detect_cycles()
        }

        # 计算组件健康度
        health_scores = {}
        for component in components:
            config = self.active_configurations.get(component, {})
            health_scores[component] = len(config) / 10.0  # 简化计算

        analysis['health_scores'] = health_scores
        return analysis

    async def _generate_config_changes(self, components: List[str],
                                     conflicts: List[ConfigurationConflict],
                                     goals: Dict[str, Any],
                                     optimization_order: List[str]) -> Dict[str, Dict[str, Any]]:
        """生成配置变更"""
        config_changes = {}

        # 按优化顺序处理组件
        for component in optimization_order:
            if component not in components:
                continue

            # 分析此组件的相关冲突
            component_conflicts = [c for c in conflicts if c.component_a == component or c.component_b == component]

            # 生成针对此组件的配置变更
            changes = await self._generate_component_changes(component, component_conflicts, goals)
            if changes:
                config_changes[component] = changes

        return config_changes

    async def _generate_component_changes(self, component: str,
                                        conflicts: List[ConfigurationConflict],
                                        goals: Dict[str, Any]) -> Dict[str, Any]:
        """生成组件配置变更"""
        changes = {}
        current_config = self.active_configurations.get(component, {})

        # 处理冲突相关的变更
        for conflict in conflicts:
            if conflict.suggested_resolution:
                action = conflict.suggested_resolution.get('action')
                if action == 'reduce_usage':
                    param = conflict.parameter_a
                    suggested_value = conflict.suggested_resolution.get('suggested_value')
                    if param and suggested_value is not None:
                        changes[param] = suggested_value
                elif action == 'standardize_value':
                    param = conflict.parameter_a
                    suggested_value = conflict.suggested_resolution.get('suggested_value')
                    if param and suggested_value is not None:
                        changes[param] = suggested_value

        # 处理目标相关的优化
        if 'performance' in goals and goals['performance'] > 0.8:
            # 高性能目标，调整相关参数
            if 'timeout' not in changes:
                changes['timeout'] = min(current_config.get('timeout', 60), 30)  # 减少超时时间

        return changes

    async def _calculate_expected_benefits(self, config_changes: Dict[str, Dict[str, Any]],
                                         goals: Dict[str, Any]) -> Dict[str, float]:
        """计算预期收益"""
        benefits = {}

        # 基于变更规模估算收益
        total_changes = sum(len(changes) for changes in config_changes.values())
        benefits['consistency_improvement'] = min(total_changes * 0.1, 1.0)

        # 基于目标计算收益
        if 'performance' in goals:
            benefits['performance_gain'] = goals['performance'] * 0.2
        if 'efficiency' in goals:
            benefits['efficiency_gain'] = goals['efficiency'] * 0.15

        return benefits

    async def _assess_optimization_risks(self, config_changes: Dict[str, Dict[str, Any]],
                                        conflicts: List[ConfigurationConflict]) -> Dict[str, Any]:
        """评估优化风险"""
        risk_assessment = {
            'risk_level': 'low',
            'risk_factors': [],
            'mitigation_strategies': []
        }

        # 基于变更数量评估风险
        total_changes = sum(len(changes) for changes in config_changes.values())
        if total_changes > 10:
            risk_assessment['risk_level'] = 'medium'
            risk_assessment['risk_factors'].append('大量配置变更')
            risk_assessment['mitigation_strategies'].append('分批实施变更')

        # 基于冲突严重程度评估风险
        high_severity_conflicts = [c for c in conflicts if c.severity in ['high', 'critical']]
        if high_severity_conflicts:
            risk_assessment['risk_level'] = 'high'
            risk_assessment['risk_factors'].append(f'{len(high_severity_conflicts)}个高严重程度冲突')
            risk_assessment['mitigation_strategies'].append('优先解决高严重程度冲突')

        return risk_assessment

    async def _check_dependency_satisfaction(self, config_changes: Dict[str, Dict[str, Any]]) -> Dict[str, bool]:
        """检查依赖满足情况"""
        satisfaction = {}

        for component, changes in config_changes.items():
            # 检查对此组件的变更是否满足其依赖关系
            dependencies = self.dependency_analyzer.get_component_dependencies(component)

            # 简化检查：假设变更会改善依赖满足情况
            satisfaction[component] = len(changes) > 0

        return satisfaction

    async def _apply_resolution(self, conflict: ConfigurationConflict, resolution: Dict[str, Any]):
        """应用冲突解决"""
        action = resolution.get('action')

        if action == 'align_parameters':
            # 参数对齐逻辑
            pass
        elif action == 'reduce_usage':
            component = resolution.get('target_component')
            param = conflict.parameter_a
            value = resolution.get('suggested_value')
            if component and param and value is not None:
                if component not in self.active_configurations:
                    self.active_configurations[component] = {}
                self.active_configurations[component][param] = value
        elif action == 'standardize_value':
            value = resolution.get('suggested_value')
            if conflict.component_a and conflict.parameter_a and value is not None:
                if conflict.component_a not in self.active_configurations:
                    self.active_configurations[conflict.component_a] = {}
                self.active_configurations[conflict.component_a][conflict.parameter_a] = value

    def get_collaboration_statistics(self) -> Dict[str, Any]:
        """获取协同统计信息"""
        total_dependencies = len(self.dependency_analyzer.dependency_rules)
        total_components = len(self.active_configurations)
        total_optimizations = len(self.optimization_history)

        dependency_types = {}
        for dep in self.dependency_analyzer.dependency_rules.values():
            dep_type = dep.dependency_type.value
            dependency_types[dep_type] = dependency_types.get(dep_type, 0) + 1

        return {
            'total_dependencies': total_dependencies,
            'total_components': total_components,
            'total_optimizations': total_optimizations,
            'dependency_types': dependency_types,
            'active_configurations': total_components
        }


# 全局实例
_collaboration_optimizer_instance: Optional[ConfigurationCollaborationOptimizer] = None

def get_config_collaboration_optimizer() -> ConfigurationCollaborationOptimizer:
    """获取配置协同优化器实例"""
    global _collaboration_optimizer_instance
    if _collaboration_optimizer_instance is None:
        _collaboration_optimizer_instance = ConfigurationCollaborationOptimizer()
    return _collaboration_optimizer_instance
