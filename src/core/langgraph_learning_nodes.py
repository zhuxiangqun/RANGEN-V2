#!/usr/bin/env python3
"""
学习节点模块 - LangGraph集成

将学习聚合器、知识分布和持续学习功能集成到LangGraph工作流中：
- 学习聚合节点：从执行结果中学习模式和优化策略
- 知识分布节点：将学习到的知识分发给相关组件
- 持续学习节点：作为监控节点持续优化系统

使用场景:
- 持续学习和系统优化
- 从历史执行中学习模式
- 自适应工作流调整

重要: 本模块被 langgraph_unified_workflow.py 等12个文件引用!

与 ExecutionCoordinator 的关系:
- ExecutionCoordinator: 不使用本模块 (轻量模式)
- UnifiedResearchSystem: 使用本模块实现自学习功能 (12个引用!)
"""

import logging
"""
学习节点模块 - LangGraph集成

⚠️ DEPRECATED: 此模块已不再维护。
生产环境使用 src.core.execution_coordinator.ExecutionCoordinator。

将学习聚合器、知识分布和持续学习功能集成到LangGraph工作流中：
- 学习聚合节点：从执行结果中学习模式和优化策略
- 知识分布节点：将学习到的知识分发给相关组件
- 持续学习节点：作为监控节点持续优化系统
"""

import warnings
warnings.warn(
    "langgraph_learning_nodes is deprecated. Use ExecutionCoordinator instead.",
    DeprecationWarning,
    stacklevel=2
)

import logging
学习节点模块 - LangGraph集成

将学习聚合器、知识分布和持续学习功能集成到LangGraph工作流中：
- 学习聚合节点：从执行结果中学习模式和优化策略
- 知识分布节点：将学习到的知识分发给相关组件
- 持续学习节点：作为监控节点持续优化系统
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


def learning_aggregation_node(state: "ResearchSystemState") -> "ResearchSystemState":
    """学习聚合节点 - 从执行结果和反馈中聚合学习数据，优化系统性能"""
    start_time = time.time()

    try:
        # 初始化学习上下文
        if 'learning_system' not in state:
            state['learning_system'] = {
                'patterns': {},
                'strategies': {},
                'performance_history': [],
                'collaboration_insights': [],
                'optimization_opportunities': []
            }

        learning_ctx = state['learning_system']

        # 🚀 改进：从各个节点的学习数据中提取信息
        node_learning_data = state.get('node_learning_data', {})
        if node_learning_data:
            # 聚合各个节点的学习数据
            node_patterns = _aggregate_node_learning_patterns(node_learning_data)
            learning_ctx['patterns'].update(node_patterns)
            logger.info(f"✅ [学习聚合] 从 {len(node_learning_data)} 个节点聚合学习数据")

        # 从反馈中提取学习数据
        feedback_data = _extract_feedback_for_learning(state)

        # 聚合协作模式
        collaboration_patterns = _aggregate_collaboration_patterns(feedback_data, state)
        learning_ctx['patterns'].update(collaboration_patterns)

        # 生成优化策略
        optimization_strategies = _generate_optimization_strategies(feedback_data, collaboration_patterns)
        learning_ctx['strategies'].update(optimization_strategies)

        # 🚀 改进：基于节点学习数据生成节点特定的优化策略
        if node_learning_data:
            node_strategies = _generate_node_optimization_strategies(node_learning_data)
            learning_ctx['strategies'].update(node_strategies)

        # 记录性能历史
        performance_record = _create_performance_record(state)
        learning_ctx['performance_history'].append(performance_record)

        # 识别协作洞察
        collaboration_insights = _identify_collaboration_insights(state, feedback_data)
        learning_ctx['collaboration_insights'].extend(collaboration_insights)

        # 🚀 改进：从节点学习数据中识别节点特定的洞察
        if node_learning_data:
            node_insights = _identify_node_insights(node_learning_data)
            learning_ctx['collaboration_insights'].extend(node_insights)

        # 发现优化机会
        optimization_opportunities = _discover_optimization_opportunities(state, learning_ctx)
        learning_ctx['optimization_opportunities'].extend(optimization_opportunities)
        
        # 🚀 改进：从节点学习数据中发现节点特定的优化机会
        if node_learning_data:
            node_opportunities = _discover_node_optimization_opportunities(node_learning_data)
            learning_ctx['optimization_opportunities'].extend(node_opportunities)

        # 更新学习元数据
        learning_ctx['last_learning_update'] = datetime.now().isoformat()
        learning_ctx['total_learning_sessions'] = learning_ctx.get('total_learning_sessions', 0) + 1

        # 将学习结果存储到状态中，供后续节点使用
        state['learning_insights'] = {
            'new_patterns': len(collaboration_patterns),
            'new_strategies': len(optimization_strategies),
            'insights_count': len(collaboration_insights),
            'opportunities_count': len(optimization_opportunities)
        }

        # 记录性能指标
        execution_time = time.time() - start_time
        state = record_node_time(state, "learning_aggregation_node", execution_time)

        logger.info("✅ 学习聚合节点执行完成")
        logger.info(f"   → 新增模式: {len(collaboration_patterns)} 个")
        logger.info(f"   → 新增策略: {len(optimization_strategies)} 个")
        logger.info(f"   → 协作洞察: {len(collaboration_insights)} 个")

        return state

    except Exception as e:
        logger.error(f"❌ 学习聚合节点执行失败: {e}")
        state['error'] = f"学习聚合错误: {str(e)}"
        return state


def knowledge_distribution_node(state: "ResearchSystemState") -> "ResearchSystemState":
    """知识分布节点 - 将学习到的知识和洞察分发给相关组件"""
    try:
        learning_ctx = state.get('learning_system', {})
        learning_insights = state.get('learning_insights', {})

        if not learning_ctx:
            logger.warning("⚠️ 没有学习上下文，跳过知识分布")
            return state

        # 初始化知识分布记录
        if 'knowledge_distribution' not in state:
            state['knowledge_distribution'] = {
                'distributed_knowledge': [],
                'recipient_updates': {},
                'distribution_history': []
            }

        dist_ctx = state['knowledge_distribution']

        # 识别需要更新的组件
        recipients = _identify_knowledge_recipients(state)

        # 分发学习到的模式
        pattern_updates = _distribute_patterns(learning_ctx.get('patterns', {}), recipients)
        dist_ctx['recipient_updates'].update(pattern_updates)

        # 分发优化策略
        strategy_updates = _distribute_strategies(learning_ctx.get('strategies', {}), recipients)
        dist_ctx['recipient_updates'].update(strategy_updates)

        # 分发协作洞察
        insight_updates = _distribute_insights(learning_ctx.get('collaboration_insights', []), recipients)
        dist_ctx['recipient_updates'].update(insight_updates)

        # 更新组件状态
        state = _update_component_states_with_knowledge(state, dist_ctx['recipient_updates'])

        # 记录分布历史
        distribution_record = {
            'timestamp': datetime.now().isoformat(),
            'patterns_distributed': len(pattern_updates),
            'strategies_distributed': len(strategy_updates),
            'insights_distributed': len(insight_updates),
            'recipients': list(recipients.keys())
        }
        dist_ctx['distribution_history'].append(distribution_record)

        logger.info("✅ 知识分布节点执行完成")
        logger.info(f"   → 更新组件: {len(recipients)} 个")
        logger.info(f"   → 分发知识: {len(pattern_updates) + len(strategy_updates) + len(insight_updates)} 项")

        return state

    except Exception as e:
        logger.error(f"❌ 知识分布节点执行失败: {e}")
        state['error'] = f"知识分布错误: {str(e)}"
        return state


def node_learning_monitor(state: "ResearchSystemState") -> "ResearchSystemState":
    """节点学习监控节点 - 监控节点执行情况，应用学习结果并优化后续节点执行策略"""
    try:
        # 获取当前执行的节点信息（从状态中推断）
        node_execution_times = state.get('node_execution_times', {})
        if not node_execution_times:
            return state
        
        # 找到最近执行的节点
        last_node = None
        last_time = 0
        for node_name, exec_time in node_execution_times.items():
            if exec_time > last_time:
                last_time = exec_time
                last_node = node_name
        
        if not last_node:
            return state
        
        # 🚀 快速学习：从最近执行的节点中学习
        node_learning_data = state.get('node_learning_data', {})
        if last_node in node_learning_data:
            node_stats = node_learning_data[last_node]
            
            # 快速应用学习结果（如果节点成功率低，可以调整后续节点）
            if node_stats.get('success_rate', 1.0) < 0.5:
                # 节点成功率低，可以调整后续节点的超时或重试策略
                if 'metadata' not in state:
                    state['metadata'] = {}
                state['metadata'][f'{last_node}_low_success'] = True
                state['metadata']['suggested_timeout_increase'] = True
        
        # 🚀 快速学习：应用学习到的路由优化
        learning_ctx = state.get('learning_system', {})
        if learning_ctx:
            learned_routing_preference = state.get('learned_routing_preference')
            if learned_routing_preference:
                # 应用学习到的路由偏好
                if 'metadata' not in state:
                    state['metadata'] = {}
                state['metadata']['learned_routing_applied'] = True
        
        logger.debug(f"✅ [节点学习监控] 节点 {last_node} 学习监控完成")
        
        return state
        
    except Exception as e:
        logger.debug(f"⚠️ [节点学习监控] 学习监控失败: {e}")
        return state


def continuous_learning_monitor(state: "ResearchSystemState") -> "ResearchSystemState":
    """持续学习监控节点 - 持续分析系统性能并触发学习更新，实现持续优化"""
    try:
        # 初始化持续学习上下文
        if 'continuous_learning' not in state:
            state['continuous_learning'] = {
                'monitoring_cycles': 0,
                'performance_trends': [],
                'learning_triggers': [],
                'system_health_metrics': {},
                'adaptive_actions': []
            }

        cont_learn_ctx = state['continuous_learning']
        cont_learn_ctx['monitoring_cycles'] += 1

        # 收集系统健康指标
        health_metrics = _collect_system_health_metrics(state)
        cont_learn_ctx['system_health_metrics'] = health_metrics

        # 分析性能趋势
        performance_trend = _analyze_performance_trends(state, cont_learn_ctx)
        cont_learn_ctx['performance_trends'].append({
            'timestamp': datetime.now().isoformat(),
            'trend': performance_trend
        })

        # 检查学习触发条件
        learning_triggers = _check_learning_triggers(state, cont_learn_ctx)
        if learning_triggers:
            cont_learn_ctx['learning_triggers'].extend(learning_triggers)
            # 设置学习触发标志
            state['learning_triggered'] = True
            state['learning_trigger_reasons'] = learning_triggers

        # 执行自适应行动
        adaptive_actions = _execute_adaptive_actions(state, cont_learn_ctx)
        cont_learn_ctx['adaptive_actions'].extend(adaptive_actions)

        # 更新监控元数据
        cont_learn_ctx['last_monitoring'] = datetime.now().isoformat()

        logger.info("✅ 持续学习监控节点执行完成")
        logger.info(f"   → 监控周期: {cont_learn_ctx['monitoring_cycles']}")
        logger.info(f"   → 学习触发: {len(learning_triggers)} 次")

        return state

    except Exception as e:
        logger.error(f"❌ 持续学习监控节点执行失败: {e}")
        state['error'] = f"持续学习监控错误: {str(e)}"
        return state


def _aggregate_node_learning_patterns(node_learning_data: Dict[str, Any]) -> Dict[str, Any]:
    """聚合各个节点的学习模式"""
    patterns = {}
    
    for node_name, node_stats in node_learning_data.items():
        # 节点性能模式
        if node_stats.get('success_rate', 0) > 0.8:
            pattern_key = f"{node_name}_high_success_pattern"
            patterns[pattern_key] = {
                'type': 'node_performance_pattern',
                'node_name': node_name,
                'success_rate': node_stats['success_rate'],
                'avg_execution_time': node_stats.get('avg_execution_time', 0.0),
                'occurrences': node_stats.get('success_count', 0)
            }
        elif node_stats.get('success_rate', 0) < 0.5:
            pattern_key = f"{node_name}_low_success_pattern"
            patterns[pattern_key] = {
                'type': 'node_performance_pattern',
                'node_name': node_name,
                'success_rate': node_stats['success_rate'],
                'avg_execution_time': node_stats.get('avg_execution_time', 0.0),
                'occurrences': node_stats.get('failure_count', 0)
            }
        
        # 节点执行时间模式
        avg_time = node_stats.get('avg_execution_time', 0.0)
        if avg_time > 5.0:
            pattern_key = f"{node_name}_slow_execution_pattern"
            patterns[pattern_key] = {
                'type': 'node_execution_time_pattern',
                'node_name': node_name,
                'time_category': 'slow',
                'avg_execution_time': avg_time,
                'occurrences': node_stats.get('success_count', 0) + node_stats.get('failure_count', 0)
            }
        elif avg_time < 1.0:
            pattern_key = f"{node_name}_fast_execution_pattern"
            patterns[pattern_key] = {
                'type': 'node_execution_time_pattern',
                'node_name': node_name,
                'time_category': 'fast',
                'avg_execution_time': avg_time,
                'occurrences': node_stats.get('success_count', 0) + node_stats.get('failure_count', 0)
            }
    
    return patterns


def _generate_node_optimization_strategies(node_learning_data: Dict[str, Any]) -> Dict[str, Any]:
    """基于节点学习数据生成节点特定的优化策略"""
    strategies = {}
    
    for node_name, node_stats in node_learning_data.items():
        # 低成功率节点的优化策略
        if node_stats.get('success_rate', 0) < 0.5:
            strategies[f"{node_name}_reliability_optimization"] = {
                'type': 'node_reliability_strategy',
                'node_name': node_name,
                'description': f'优化节点 {node_name} 的可靠性',
                'current_success_rate': node_stats['success_rate'],
                'optimization_actions': [
                    'increase_retry_count',
                    'improve_error_handling',
                    'add_fallback_mechanism'
                ]
            }
        
        # 慢执行节点的优化策略
        avg_time = node_stats.get('avg_execution_time', 0.0)
        if avg_time > 5.0:
            strategies[f"{node_name}_performance_optimization"] = {
                'type': 'node_performance_strategy',
                'node_name': node_name,
                'description': f'优化节点 {node_name} 的性能',
                'current_avg_time': avg_time,
                'optimization_actions': [
                    'increase_timeout',
                    'optimize_algorithm',
                    'add_caching'
                ]
            }
    
    return strategies


def _identify_node_insights(node_learning_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从节点学习数据中识别节点特定的洞察"""
    insights = []
    
    for node_name, node_stats in node_learning_data.items():
        success_rate = node_stats.get('success_rate', 0)
        avg_time = node_stats.get('avg_execution_time', 0.0)
        
        # 高成功率洞察
        if success_rate > 0.9:
            insights.append({
                'type': 'node_excellence',
                'node_name': node_name,
                'insight': f'节点 {node_name} 表现优秀，成功率 {success_rate:.2%}',
                'success_rate': success_rate,
                'confidence': 0.9
            })
        
        # 性能瓶颈洞察
        if avg_time > 10.0:
            insights.append({
                'type': 'node_bottleneck',
                'node_name': node_name,
                'insight': f'节点 {node_name} 可能是性能瓶颈，平均执行时间 {avg_time:.2f}秒',
                'avg_execution_time': avg_time,
                'confidence': 0.8
            })
    
    return insights


def _discover_node_optimization_opportunities(node_learning_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从节点学习数据中发现节点特定的优化机会"""
    opportunities = []
    
    for node_name, node_stats in node_learning_data.items():
        success_rate = node_stats.get('success_rate', 0)
        avg_time = node_stats.get('avg_execution_time', 0.0)
        failure_count = node_stats.get('failure_count', 0)
        total_executions = node_stats.get('success_count', 0) + failure_count
        
        # 可靠性优化机会
        if success_rate < 0.7 and total_executions > 5:
            opportunities.append({
                'type': 'node_reliability_improvement',
                'node_name': node_name,
                'description': f'节点 {node_name} 成功率较低 ({success_rate:.2%})，需要改进',
                'severity': 'high' if success_rate < 0.5 else 'medium',
                'current_success_rate': success_rate,
                'suggested_actions': ['improve_error_handling', 'add_retry_mechanism', 'optimize_logic']
            })
        
        # 性能优化机会
        if avg_time > 5.0 and total_executions > 5:
            opportunities.append({
                'type': 'node_performance_improvement',
                'node_name': node_name,
                'description': f'节点 {node_name} 执行时间较长 ({avg_time:.2f}秒)，需要优化',
                'severity': 'high' if avg_time > 10.0 else 'medium',
                'current_avg_time': avg_time,
                'suggested_actions': ['optimize_algorithm', 'add_caching', 'increase_timeout']
            })
    
    return opportunities


def _extract_feedback_for_learning(state: "ResearchSystemState") -> Dict[str, Any]:
    """从状态中提取用于学习的反馈数据"""
    feedback_data = {}

    # 提取执行反馈
    execution_feedback = state.get('feedback_loop', {}).get('execution_results', [])
    if execution_feedback:
        feedback_data['execution_feedback'] = execution_feedback[-1]  # 最新的执行反馈

    # 提取性能反馈
    performance_feedback = state.get('feedback_loop', {}).get('performance_feedback', [])
    if performance_feedback:
        feedback_data['performance_feedback'] = performance_feedback[-1]  # 最新的性能反馈

    # 提取错误反馈
    error_feedback = state.get('feedback_loop', {}).get('error_feedback')
    if error_feedback:
        feedback_data['error_feedback'] = error_feedback

    # 提取协作冲突
    collaboration_conflicts = state.get('collaboration_conflicts', [])
    if collaboration_conflicts:
        feedback_data['collaboration_conflicts'] = collaboration_conflicts

    # 提取任务分配决策
    task_allocation_decision = state.get('task_allocation_decision')
    if task_allocation_decision:
        feedback_data['task_allocation_decision'] = task_allocation_decision

    return feedback_data


def _aggregate_collaboration_patterns(feedback_data: Dict[str, Any], state: "ResearchSystemState") -> Dict[str, Any]:
    """聚合协作模式"""
    patterns = {}

    # 分析任务分配模式
    task_decision = feedback_data.get('task_allocation_decision')
    complexity_score = state.get('complexity_score', 0.0)

    if task_decision and complexity_score is not None:
        pattern_key = f"complexity_{complexity_score:.1f}_to_{task_decision}"
        patterns[pattern_key] = {
            'type': 'task_allocation_pattern',
            'complexity_range': (complexity_score - 0.1, complexity_score + 0.1),
            'preferred_allocation': task_decision,
            'confidence': 0.8,
            'occurrences': 1
        }

    # 分析协作冲突模式
    conflicts = feedback_data.get('collaboration_conflicts', [])
    if conflicts:
        for conflict in conflicts:
            conflict_type = conflict.get('conflict_type', 'unknown')
            pattern_key = f"conflict_{conflict_type}_pattern"
            if pattern_key not in patterns:
                patterns[pattern_key] = {
                    'type': 'conflict_pattern',
                    'conflict_type': conflict_type,
                    'frequency': 1,
                    'common_resolution': conflict.get('suggested_resolution'),
                    'occurrences': 1
                }
            else:
                patterns[pattern_key]['frequency'] += 1
                patterns[pattern_key]['occurrences'] += 1

    # 分析性能模式
    execution_feedback = feedback_data.get('execution_feedback', {})
    if execution_feedback.get('success'):
        exec_time = execution_feedback.get('total_execution_time', 0)
        if exec_time > 0:
            time_category = 'slow' if exec_time > 10 else 'fast' if exec_time < 2 else 'normal'
            pattern_key = f"performance_{time_category}_pattern"
            patterns[pattern_key] = {
                'type': 'performance_pattern',
                'time_category': time_category,
                'avg_execution_time': exec_time,
                'occurrences': 1
            }

    return patterns


def _generate_optimization_strategies(feedback_data: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
    """生成优化策略"""
    strategies = {}

    # 基于任务分配模式生成策略
    allocation_patterns = {k: v for k, v in patterns.items() if v['type'] == 'task_allocation_pattern'}
    if allocation_patterns:
        strategies['task_allocation_optimization'] = {
            'type': 'allocation_strategy',
            'description': '基于复杂度优化任务分配',
            'patterns': list(allocation_patterns.keys()),
            'optimization_actions': [
                'cache_allocation_decisions',
                'preallocate_for_common_complexity_ranges'
            ]
        }

    # 基于冲突模式生成策略
    conflict_patterns = {k: v for k, v in patterns.items() if v['type'] == 'conflict_pattern'}
    if conflict_patterns:
        strategies['conflict_prevention'] = {
            'type': 'conflict_strategy',
            'description': '预防常见协作冲突',
            'patterns': list(conflict_patterns.keys()),
            'optimization_actions': [
                'adjust_resource_allocation',
                'implement_conflict_avoidance_rules'
            ]
        }

    # 基于性能模式生成策略
    performance_patterns = {k: v for k, v in patterns.items() if v['type'] == 'performance_pattern'}
    if performance_patterns:
        slow_patterns = [k for k, v in performance_patterns.items() if v['time_category'] == 'slow']
        if slow_patterns:
            strategies['performance_optimization'] = {
                'type': 'performance_strategy',
                'description': '优化慢执行路径',
                'patterns': slow_patterns,
                'optimization_actions': [
                    'increase_timeout_for_slow_paths',
                    'optimize_resource_allocation'
                ]
            }

    return strategies


def _create_performance_record(state: "ResearchSystemState") -> Dict[str, Any]:
    """创建性能记录"""
    return {
        'timestamp': datetime.now().isoformat(),
        'execution_time': state.get('execution_time', 0),
        'node_execution_times': state.get('node_execution_times', {}),
        'token_usage': state.get('token_usage', {}),
        'api_calls': state.get('api_calls', {}),
        'errors': len(state.get('errors', [])),
        'complexity_score': state.get('complexity_score', 0.0),
        'task_allocation_decision': state.get('task_allocation_decision', 'unknown')
    }


def _identify_collaboration_insights(state: "ResearchSystemState", feedback_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """识别协作洞察"""
    insights = []

    # 分析智能体协作效果
    agent_states = state.get('agent_states', {})
    active_agents = [aid for aid, astate in agent_states.items() if astate.get('status') == 'active']

    if len(active_agents) > 1:
        # 多智能体协作洞察
        execution_success = feedback_data.get('execution_feedback', {}).get('success', False)
        if execution_success:
            insights.append({
                'type': 'collaboration_effectiveness',
                'insight': f'多智能体协作成功: {len(active_agents)} 个智能体参与',
                'participants': active_agents,
                'outcome': 'success',
                'confidence': 0.9
            })
        else:
            insights.append({
                'type': 'collaboration_issues',
                'insight': f'多智能体协作存在问题: {len(active_agents)} 个智能体参与',
                'participants': active_agents,
                'outcome': 'issues_detected',
                'confidence': 0.7
            })

    # 分析任务分配效率
    task_decision = feedback_data.get('task_allocation_decision')
    conflicts = feedback_data.get('collaboration_conflicts', [])

    if task_decision == 'single_agent_flow' and not conflicts:
        insights.append({
            'type': 'allocation_efficiency',
            'insight': '单智能体模式避免了协作冲突',
            'allocation_decision': task_decision,
            'conflicts_avoided': len(conflicts),
            'confidence': 0.8
        })

    return insights


def _discover_optimization_opportunities(state: "ResearchSystemState", learning_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """发现优化机会"""
    opportunities = []

    # 分析性能历史
    performance_history = learning_ctx.get('performance_history', [])
    if len(performance_history) >= 5:
        # 检查性能趋势
        recent_times = [p['execution_time'] for p in performance_history[-5:]]
        avg_time = sum(recent_times) / len(recent_times)

        if avg_time > 15:
            opportunities.append({
                'type': 'performance_optimization',
                'description': f'执行时间过长 (平均 {avg_time:.2f}秒)',
                'severity': 'high',
                'suggested_actions': ['optimize_slow_nodes', 'increase_resources']
            })

    # 分析错误模式
    error_history = [p for p in performance_history if p['errors'] > 0]
    if len(error_history) / len(performance_history) > 0.3:  # 30%的执行有错误
        opportunities.append({
            'type': 'reliability_improvement',
            'description': f'错误率过高 ({len(error_history)}/{len(performance_history)})',
            'severity': 'high',
            'suggested_actions': ['improve_error_handling', 'add_retry_mechanisms']
        })

    # 分析资源使用模式
    token_usage_history = [p.get('token_usage', {}) for p in performance_history[-10:]]
    if token_usage_history:
        total_tokens = sum(sum(usage.values()) for usage in token_usage_history)
        if total_tokens > 100000:  # 高token消耗
            opportunities.append({
                'type': 'resource_optimization',
                'description': f'Token消耗过高 (总计 {total_tokens})',
                'severity': 'medium',
                'suggested_actions': ['optimize_prompts', 'implement_caching']
            })

    return opportunities


def _identify_knowledge_recipients(state: "ResearchSystemState") -> Dict[str, List[str]]:
    """识别知识接收者"""
    recipients = {}

    # 智能体作为接收者
    agent_states = state.get('agent_states', {})
    for agent_id, agent_state in agent_states.items():
        capabilities = agent_state.get('capabilities', [])
        recipients[agent_id] = capabilities

    # 配置优化器作为接收者
    recipients['config_optimizer'] = ['optimization_strategies', 'performance_patterns']

    # 协作协调器作为接收者
    recipients['collaboration_coordinator'] = ['collaboration_patterns', 'conflict_resolutions']

    return recipients


def _distribute_patterns(patterns: Dict[str, Any], recipients: Dict[str, List[str]]) -> Dict[str, Any]:
    """分发模式"""
    updates = {}

    for recipient_id, capabilities in recipients.items():
        relevant_patterns = {}

        for pattern_key, pattern in patterns.items():
            # 根据接收者的能力匹配相关模式
            if 'task_allocation' in pattern_key and 'process' in capabilities:
                relevant_patterns[pattern_key] = pattern
            elif 'conflict' in pattern_key and 'validate' in capabilities:
                relevant_patterns[pattern_key] = pattern
            elif 'performance' in pattern_key and 'optimize' in capabilities:
                relevant_patterns[pattern_key] = pattern

        if relevant_patterns:
            updates[recipient_id] = {
                'type': 'pattern_update',
                'patterns': relevant_patterns,
                'update_count': len(relevant_patterns)
            }

    return updates


def _distribute_strategies(strategies: Dict[str, Any], recipients: Dict[str, List[str]]) -> Dict[str, Any]:
    """分发策略"""
    updates = {}

    for recipient_id, capabilities in recipients.items():
        relevant_strategies = {}

        for strategy_key, strategy in strategies.items():
            # 根据接收者的能力匹配相关策略
            if 'allocation' in strategy_key and 'coordinate' in capabilities:
                relevant_strategies[strategy_key] = strategy
            elif 'conflict' in strategy_key and 'validate' in capabilities:
                relevant_strategies[strategy_key] = strategy
            elif 'performance' in strategy_key and 'optimize' in capabilities:
                relevant_strategies[strategy_key] = strategy

        if relevant_strategies:
            updates[f"{recipient_id}_strategies"] = {
                'type': 'strategy_update',
                'strategies': relevant_strategies,
                'update_count': len(relevant_strategies)
            }

    return updates


def _distribute_insights(insights: List[Dict[str, Any]], recipients: Dict[str, List[str]]) -> Dict[str, Any]:
    """分发洞察"""
    updates = {}

    for recipient_id, capabilities in recipients.items():
        relevant_insights = []

        for insight in insights:
            # 根据接收者的能力匹配相关洞察
            if insight['type'] == 'collaboration_effectiveness' and 'coordinate' in capabilities:
                relevant_insights.append(insight)
            elif insight['type'] == 'allocation_efficiency' and 'process' in capabilities:
                relevant_insights.append(insight)

        if relevant_insights:
            updates[f"{recipient_id}_insights"] = {
                'type': 'insight_update',
                'insights': relevant_insights,
                'update_count': len(relevant_insights)
            }

    return updates


def _update_component_states_with_knowledge(state: "ResearchSystemState", updates: Dict[str, Any]) -> "ResearchSystemState":
    """🚀 改进：使用知识更新组件状态，并将学习结果应用到主流程"""
    for update_key, update_data in updates.items():
        if update_key.startswith('agent_') and not update_key.endswith('_strategies') and not update_key.endswith('_insights'):
            # 更新智能体状态
            agent_id = update_key[5:]  # 移除 'agent_' 前缀
            if agent_id in state.get('agent_states', {}):
                agent_state = state['agent_states'][agent_id]

                # 添加学习到的模式
                if 'patterns' in update_data:
                    if 'learned_patterns' not in agent_state:
                        agent_state['learned_patterns'] = {}
                    agent_state['learned_patterns'].update(update_data['patterns'])

                agent_state['last_knowledge_update'] = datetime.now().isoformat()
        
        # 🚀 改进：将学习结果应用到主流程的配置和决策
        elif update_key == 'config_optimizer_strategies' or update_key == 'config_optimizer':
            # 应用优化策略到主流程配置
            strategies = update_data.get('strategies', {})
            if strategies:
                # 应用任务分配优化策略
                if 'task_allocation_optimization' in strategies:
                    strategy = strategies['task_allocation_optimization']
                    # 更新路由决策逻辑（通过更新配置参数）
                    if 'optimization_actions' in strategy:
                        state['learned_routing_optimizations'] = strategy['optimization_actions']
                        logger.info(f"✅ [学习应用] 应用任务分配优化策略: {strategy['optimization_actions']}")
                
                # 应用性能优化策略
                if 'performance_optimization' in strategies:
                    strategy = strategies['performance_optimization']
                    # 更新超时和重试配置
                    if 'optimization_actions' in strategy:
                        if 'increase_timeout_for_slow_paths' in strategy['optimization_actions']:
                            current_timeout = state.get('global_timeout', 30)
                            state['global_timeout'] = min(current_timeout * 1.2, 120)
                            logger.info(f"✅ [学习应用] 增加超时时间: {state['global_timeout']}秒")
        
        elif update_key == 'collaboration_coordinator_strategies' or update_key == 'collaboration_coordinator':
            # 应用协作优化策略
            strategies = update_data.get('strategies', {})
            if strategies and 'conflict_prevention' in strategies:
                strategy = strategies['conflict_prevention']
                # 更新冲突预防规则
                if 'optimization_actions' in strategy:
                    state['learned_conflict_prevention'] = strategy['optimization_actions']
                    logger.info(f"✅ [学习应用] 应用冲突预防策略: {strategy['optimization_actions']}")
    
    # 🚀 改进：将学习到的模式应用到路由决策
    learning_ctx = state.get('learning_system', {})
    patterns = learning_ctx.get('patterns', {})
    
    # 应用任务分配模式到路由决策
    allocation_patterns = {k: v for k, v in patterns.items() if v.get('type') == 'task_allocation_pattern'}
    if allocation_patterns:
        # 找到最匹配的模式
        complexity_score = state.get('complexity_score', 0.0)
        for pattern_key, pattern in allocation_patterns.items():
            complexity_range = pattern.get('complexity_range', (0, 10))
            if complexity_range[0] <= complexity_score <= complexity_range[1]:
                preferred_allocation = pattern.get('preferred_allocation')
                if preferred_allocation:
                    # 更新路由决策偏好
                    state['learned_routing_preference'] = preferred_allocation
                    logger.info(f"✅ [学习应用] 应用学习到的路由偏好: {preferred_allocation} (复杂度: {complexity_score:.2f})")
                    break
    
    # 🚀 改进：将学习到的性能模式应用到配置
    performance_patterns = {k: v for k, v in patterns.items() if v.get('type') == 'performance_pattern'}
    if performance_patterns:
        slow_patterns = [k for k, v in performance_patterns.items() if v.get('time_category') == 'slow']
        if slow_patterns:
            # 检测到慢执行模式，调整配置
            current_timeout = state.get('global_timeout', 30)
            state['global_timeout'] = min(current_timeout * 1.3, 120)
            logger.info(f"✅ [学习应用] 基于慢执行模式调整超时: {state['global_timeout']}秒")
    
    return state


def _collect_system_health_metrics(state: "ResearchSystemState") -> Dict[str, Any]:
    """收集系统健康指标"""
    metrics = {}

    # 智能体健康
    agent_states = state.get('agent_states', {})
    active_agents = sum(1 for astate in agent_states.values() if astate.get('status') == 'active')
    total_agents = len(agent_states)
    metrics['agent_health'] = active_agents / total_agents if total_agents > 0 else 0

    # 错误率
    errors = state.get('errors', [])
    total_operations = state.get('api_calls', {}).get('total', 1)
    metrics['error_rate'] = len(errors) / total_operations

    # 性能指标
    execution_time = state.get('execution_time', 0)
    metrics['avg_execution_time'] = execution_time
    metrics['performance_score'] = 1.0 / (1.0 + execution_time)  # 简单性能评分

    # 资源使用
    token_usage = state.get('token_usage', {})
    total_tokens = sum(token_usage.values())
    metrics['total_token_usage'] = total_tokens

    return metrics


def _analyze_performance_trends(state: "ResearchSystemState", cont_learn_ctx: Dict[str, Any]) -> Dict[str, Any]:
    """分析性能趋势"""
    trend = {}

    # 分析执行时间趋势
    performance_history = cont_learn_ctx.get('performance_history', [])
    if len(performance_history) >= 3:
        recent_times = [p['trend'].get('avg_execution_time', 0) for p in performance_history[-3:]]
        if recent_times[-1] > recent_times[0] * 1.2:
            trend['execution_time_trend'] = 'increasing'
            trend['severity'] = 'warning'
        elif recent_times[-1] < recent_times[0] * 0.8:
            trend['execution_time_trend'] = 'improving'
            trend['severity'] = 'positive'
        else:
            trend['execution_time_trend'] = 'stable'
            trend['severity'] = 'neutral'

    # 分析错误率趋势
    if len(performance_history) >= 3:
        recent_errors = [p['trend'].get('error_rate', 0) for p in performance_history[-3:]]
        if recent_errors[-1] > recent_errors[0] * 1.5:
            trend['error_rate_trend'] = 'increasing'
            trend['severity'] = 'critical'
        elif recent_errors[-1] < recent_errors[0] * 0.5:
            trend['error_rate_trend'] = 'improving'
            trend['severity'] = 'positive'

    return trend


def _check_learning_triggers(state: "ResearchSystemState", cont_learn_ctx: Dict[str, Any]) -> List[str]:
    """检查学习触发条件"""
    triggers = []

    health_metrics = cont_learn_ctx.get('system_health_metrics', {})

    # 触发条件1: 错误率过高
    error_rate = health_metrics.get('error_rate', 0)
    if error_rate > 0.2:  # 20%错误率
        triggers.append(f"高错误率触发学习: {error_rate:.2%}")

    # 触发条件2: 性能下降
    performance_trends = cont_learn_ctx.get('performance_trends', [])
    if performance_trends:
        latest_trend = performance_trends[-1]['trend']
        if latest_trend.get('execution_time_trend') == 'increasing':
            triggers.append("执行时间增加触发学习")

    # 触发条件3: 智能体健康下降
    agent_health = health_metrics.get('agent_health', 1.0)
    if agent_health < 0.7:  # 70%健康度
        triggers.append(f"智能体健康下降触发学习: {agent_health:.2%}")

    # 触发条件4: 定期学习（每10个周期）
    monitoring_cycles = cont_learn_ctx.get('monitoring_cycles', 0)
    if monitoring_cycles % 10 == 0:
        triggers.append(f"定期学习触发: 第{monitoring_cycles}个监控周期")

    return triggers


def _execute_adaptive_actions(state: "ResearchSystemState", cont_learn_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """执行自适应行动"""
    actions = []

    health_metrics = cont_learn_ctx.get('system_health_metrics', {})

    # 自适应行动1: 基于错误率调整重试策略
    error_rate = health_metrics.get('error_rate', 0)
    if error_rate > 0.1:
        actions.append({
            'action_type': 'config_adjustment',
            'target': 'retry_policy',
            'adjustment': 'increase_max_retries',
            'reason': f'错误率过高: {error_rate:.2%}'
        })
        # 更新状态
        state['max_retries'] = min(state.get('max_retries', 3) + 1, 5)

    # 自适应行动2: 基于性能调整超时
    avg_time = health_metrics.get('avg_execution_time', 0)
    if avg_time > 20:
        actions.append({
            'action_type': 'config_adjustment',
            'target': 'timeout',
            'adjustment': 'increase_timeout',
            'reason': f'执行时间过长: {avg_time:.2f}秒'
        })
        # 更新状态
        state['global_timeout'] = min(state.get('global_timeout', 30) + 10, 120)

    return actions


# 为了避免循环导入，在文件末尾导入
from src.core.langgraph_unified_workflow import ResearchSystemState, record_node_time


# ==================== 学习辅助函数 - 用于在各个节点中集成学习功能 ====================

def collect_node_learning_data(state: "ResearchSystemState", node_name: str, 
                               execution_time: float, success: bool, 
                               node_data: Optional[Dict[str, Any]] = None) -> None:
    """收集节点学习数据 - 在各个节点中调用，用于收集学习数据
    
    Args:
        state: 工作流状态
        node_name: 节点名称
        execution_time: 执行时间
        success: 是否成功
        node_data: 节点特定的数据（可选）
    """
    try:
        # 初始化节点学习数据
        if 'node_learning_data' not in state:
            state['node_learning_data'] = {}
        
        node_learning_data = state['node_learning_data']
        
        # 收集节点执行数据
        if node_name not in node_learning_data:
            node_learning_data[node_name] = {
                'execution_history': [],
                'success_count': 0,
                'failure_count': 0,
                'total_execution_time': 0.0,
                'avg_execution_time': 0.0,
                'success_rate': 0.0,
                'last_execution': None
            }
        
        node_stats = node_learning_data[node_name]
        
        # 记录执行历史
        execution_record = {
            'timestamp': time.time(),
            'execution_time': execution_time,
            'success': success,
            'node_data': node_data or {}
        }
        node_stats['execution_history'].append(execution_record)
        
        # 限制历史记录数量（最多保留100条）
        if len(node_stats['execution_history']) > 100:
            node_stats['execution_history'] = node_stats['execution_history'][-100:]
        
        # 更新统计信息
        if success:
            node_stats['success_count'] += 1
        else:
            node_stats['failure_count'] += 1
        
        node_stats['total_execution_time'] += execution_time
        total_executions = node_stats['success_count'] + node_stats['failure_count']
        node_stats['avg_execution_time'] = node_stats['total_execution_time'] / total_executions if total_executions > 0 else 0.0
        node_stats['success_rate'] = node_stats['success_count'] / total_executions if total_executions > 0 else 0.0
        node_stats['last_execution'] = execution_record
        
        logger.debug(f"✅ [学习数据收集] 节点 {node_name} 学习数据已收集: success={success}, time={execution_time:.2f}s")
        
    except Exception as e:
        logger.warning(f"⚠️ [学习数据收集] 节点 {node_name} 学习数据收集失败: {e}")


def apply_learned_insights(state: "ResearchSystemState", node_name: str) -> Dict[str, Any]:
    """应用学习到的洞察 - 在各个节点中调用，用于应用学习结果
    
    Args:
        state: 工作流状态
        node_name: 节点名称
    
    Returns:
        学习洞察字典，包含优化建议和配置调整
    """
    try:
        learning_ctx = state.get('learning_system', {})
        if not learning_ctx:
            return {}
        
        insights = {}
        
        # 获取节点特定的学习模式
        patterns = learning_ctx.get('patterns', {})
        strategies = learning_ctx.get('strategies', {})
        
        # 应用性能优化策略
        performance_strategies = {k: v for k, v in strategies.items() if v.get('type') == 'performance_strategy'}
        if performance_strategies:
            # 检查是否有针对该节点的性能优化建议
            node_performance_patterns = {k: v for k, v in patterns.items() 
                                       if v.get('type') == 'performance_pattern' and node_name in k}
            if node_performance_patterns:
                insights['performance_optimization'] = {
                    'suggested_timeout': state.get('global_timeout', 30) * 1.2,
                    'suggested_retry_count': state.get('max_retries', 3) + 1
                }
        
        # 应用任务分配优化策略
        allocation_strategies = {k: v for k, v in strategies.items() if v.get('type') == 'allocation_strategy'}
        if allocation_strategies:
            # 检查是否有针对该节点的任务分配优化建议
            learned_routing_preference = state.get('learned_routing_preference')
            if learned_routing_preference:
                insights['routing_optimization'] = {
                    'preferred_route': learned_routing_preference,
                    'confidence': 0.8
                }
        
        # 应用冲突预防策略
        conflict_strategies = {k: v for k, v in strategies.items() if v.get('type') == 'conflict_strategy'}
        if conflict_strategies:
            learned_conflict_prevention = state.get('learned_conflict_prevention', [])
            if learned_conflict_prevention:
                insights['conflict_prevention'] = {
                    'prevention_rules': learned_conflict_prevention
                }
        
        if insights:
            logger.debug(f"✅ [学习应用] 节点 {node_name} 学习洞察已应用: {list(insights.keys())}")
        
        return insights
        
    except Exception as e:
        logger.warning(f"⚠️ [学习应用] 节点 {node_name} 学习洞察应用失败: {e}")
        return {}


def learn_from_node_execution(state: "ResearchSystemState", node_name: str, 
                              execution_result: Dict[str, Any]) -> None:
    """从节点执行中学习 - 在各个节点中调用，用于实时学习
    
    Args:
        state: 工作流状态
        node_name: 节点名称
        execution_result: 执行结果
    """
    try:
        # 初始化学习上下文
        if 'learning_system' not in state:
            state['learning_system'] = {
                'patterns': {},
                'strategies': {},
                'performance_history': [],
                'collaboration_insights': [],
                'optimization_opportunities': []
            }
        
        learning_ctx = state['learning_system']
        
        # 创建学习经验
        experience = {
            'type': 'node_execution',
            'node_name': node_name,
            'data': {
                'query': state.get('query', ''),
                'complexity_score': state.get('complexity_score', 0.0),
                'route_path': state.get('route_path', 'unknown'),
                'execution_result': execution_result
            },
            'outcome': {
                'success': execution_result.get('success', False),
                'execution_time': execution_result.get('execution_time', 0.0),
                'confidence': execution_result.get('confidence', 0.0),
                'timestamp': time.time()
            }
        }
        
        # 尝试使用LearningSystem进行学习（如果可用）
        try:
            from src.agents.learning_system_wrapper import LearningSystemWrapper as LearningSystem
            # 注意：这里不创建新实例，而是使用状态中已有的学习系统
            # 如果系统中有学习系统实例，可以通过状态传递
            if 'learning_system_instance' in state:
                learning_system = state['learning_system_instance']
                if learning_system and hasattr(learning_system, 'integrate_experience'):
                    learning_system.integrate_experience(experience)
                    logger.debug(f"✅ [实时学习] 节点 {node_name} 经验已整合到学习系统")
        except Exception as e:
            logger.debug(f"⚠️ [实时学习] 学习系统不可用: {e}")
        
        # 直接更新学习上下文（即使LearningSystem不可用）
        # 分析执行模式
        if execution_result.get('success'):
            # 成功模式
            pattern_key = f"{node_name}_success_pattern"
            if pattern_key not in learning_ctx['patterns']:
                learning_ctx['patterns'][pattern_key] = {
                    'type': 'node_success_pattern',
                    'node_name': node_name,
                    'success_rate': 1.0,
                    'occurrences': 1,
                    'avg_execution_time': execution_result.get('execution_time', 0.0)
                }
            else:
                pattern = learning_ctx['patterns'][pattern_key]
                pattern['occurrences'] += 1
                pattern['success_rate'] = (pattern['success_rate'] * (pattern['occurrences'] - 1) + 1.0) / pattern['occurrences']
                pattern['avg_execution_time'] = (pattern['avg_execution_time'] * (pattern['occurrences'] - 1) + 
                                                 execution_result.get('execution_time', 0.0)) / pattern['occurrences']
        else:
            # 失败模式
            pattern_key = f"{node_name}_failure_pattern"
            if pattern_key not in learning_ctx['patterns']:
                learning_ctx['patterns'][pattern_key] = {
                    'type': 'node_failure_pattern',
                    'node_name': node_name,
                    'failure_rate': 1.0,
                    'occurrences': 1,
                    'error_type': execution_result.get('error', 'unknown')
                }
            else:
                pattern = learning_ctx['patterns'][pattern_key]
                pattern['occurrences'] += 1
                pattern['failure_rate'] = (pattern['failure_rate'] * (pattern['occurrences'] - 1) + 1.0) / pattern['occurrences']
        
        logger.debug(f"✅ [实时学习] 节点 {node_name} 学习数据已更新")
        
    except Exception as e:
        logger.warning(f"⚠️ [实时学习] 节点 {node_name} 学习失败: {e}")
