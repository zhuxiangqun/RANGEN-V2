"""
配置优化节点模块 - LangGraph集成

将配置优化器、反馈闭环和跨组件优化功能集成到LangGraph工作流中：
- 配置优化节点：使用LangGraph状态进行配置优化
- 反馈闭环节点：集成到执行流程的反馈收集
- 跨组件协调节点：协调不同组件间的配置调整
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def config_optimization_node(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    配置优化节点

    使用LangGraph状态管理系统进行配置优化。
    替代独立的配置优化器，集成到工作流执行流程中。

    Args:
        state: LangGraph工作流状态

    Returns:
        更新后的状态
    """
    start_time = time.time()

    try:
        # 初始化配置优化上下文
        if 'config_optimization' not in state:
            state['config_optimization'] = {
                'current_config': {},
                'optimization_history': [],
                'performance_metrics': {},
                'last_optimized': None
            }

        config_ctx = state['config_optimization']
        current_config_raw = config_ctx.get('current_config', {})
        # 🚀 修复：确保current_config是Dict类型
        current_config: Dict[str, Any] = current_config_raw if isinstance(current_config_raw, dict) else {}
        
        # 获取执行上下文用于优化
        execution_context = {
            'query_complexity': state.get('complexity_score', 0.0),
            'query_type': state.get('query_type', 'simple'),
            'agent_states': state.get('agent_states', {}),
            'node_execution_times': state.get('node_execution_times', {}),
            'errors': state.get('errors', []),
            'token_usage': state.get('token_usage', {})
        }
        
        # 执行配置优化
        optimized_config = _optimize_configuration(current_config, execution_context)
        
        # 更新配置和历史记录
        config_ctx['previous_config'] = current_config.copy()
        config_ctx['current_config'] = optimized_config
        config_ctx['last_optimized'] = datetime.now().isoformat()
        
        # 记录优化历史
        optimization_record = {
            'timestamp': datetime.now().isoformat(),
            'previous_config': current_config,
            'optimized_config': optimized_config,
            'execution_context': execution_context,
            'optimization_reason': _determine_optimization_reason(execution_context)
        }
        # 🚀 修复：确保optimization_history是List类型
        optimization_history = config_ctx.get('optimization_history', [])
        if not isinstance(optimization_history, list):
            optimization_history = []
        optimization_history.append(optimization_record)
        config_ctx['optimization_history'] = optimization_history
        
        # 更新性能指标
        config_ctx['performance_metrics'] = _calculate_config_performance_metrics(
            optimization_history
        )

        # 将优化后的配置应用到相关组件
        state = _apply_optimized_config(state, optimized_config)

        # 记录性能指标
        execution_time = time.time() - start_time
        state = record_node_time(state, "config_optimization_node", execution_time)

        logger.info(f"✅ 配置优化节点执行完成，优化了 {len(optimized_config)} 个配置项")
        return state

    except Exception as e:
        logger.error(f"❌ 配置优化节点执行失败: {e}")
        state['error'] = f"配置优化错误: {str(e)}"
        return state


def feedback_collection_node(state: "ResearchSystemState") -> "ResearchSystemState":
    """反馈收集节点 - 收集执行结果和性能指标，用于后续优化"""
    try:
        # 初始化反馈上下文
        if 'feedback_loop' not in state or not isinstance(state.get('feedback_loop'), dict):
            state['feedback_loop'] = {
                'execution_results': [],
                'performance_feedback': [],
                'error_feedback': [],
                'user_feedback': [],
                'learning_opportunities': []
            }

        feedback_ctx = state['feedback_loop']

        # 确保关键列表字段存在且为列表，避免 KeyError / 类型错误
        for key in ['execution_results', 'performance_feedback', 'error_feedback', 'user_feedback', 'learning_opportunities']:
            value = feedback_ctx.get(key)
            if not isinstance(value, list):
                feedback_ctx[key] = [] if value is None else [value]

        # 🚀 改进：从主流程各个节点收集详细的执行数据
        execution_feedback = _collect_execution_feedback(state)
        # 收集主流程各个节点的执行数据
        node_feedback = _collect_node_execution_feedback(state)
        execution_feedback['node_details'] = node_feedback
        feedback_ctx['execution_results'].append({
            'timestamp': datetime.now().isoformat(),
            'feedback': execution_feedback
        })

        # 收集性能反馈
        performance_feedback = _collect_performance_feedback(state)
        feedback_ctx['performance_feedback'].append({
            'timestamp': datetime.now().isoformat(),
            'feedback': performance_feedback
        })

        # 收集错误反馈
        error_feedback = _collect_error_feedback(state)
        if error_feedback:
            feedback_ctx['error_feedback'].append({
                'timestamp': datetime.now().isoformat(),
                'feedback': error_feedback
            })

        # 识别学习机会
        learning_opportunities = _identify_learning_opportunities(state)
        feedback_ctx['learning_opportunities'].extend(learning_opportunities)

        # 更新配置优化上下文（为下次优化提供反馈）
        if 'config_optimization' in state:
            config_ctx = state['config_optimization']
            config_ctx['latest_feedback'] = {
                'execution_feedback': execution_feedback,
                'performance_feedback': performance_feedback,
                'error_feedback': error_feedback,
                'learning_opportunities': learning_opportunities
            }

        logger.info("✅ 反馈收集节点执行完成")
        logger.debug(f"   → 执行反馈: {len(execution_feedback)} 项")
        logger.debug(f"   → 性能反馈: {len(performance_feedback)} 项")
        logger.debug(f"   → 错误反馈: {len(error_feedback) if error_feedback else 0} 项")
        logger.debug(f"   → 学习机会: {len(learning_opportunities)} 项")

        return state

    except Exception as e:
        logger.error(f"❌ 反馈收集节点执行失败: {e}")
        state['error'] = f"反馈收集错误: {str(e)}"
        return state


def cross_component_coordination_node(state: "ResearchSystemState") -> "ResearchSystemState":
    """跨组件协调节点 - 协调不同组件间的配置调整，实现协同优化"""
    try:
        # 初始化跨组件协调上下文
        if 'cross_component_coordination' not in state:
            state['cross_component_coordination'] = {
                'component_configs': {},
                'coordination_history': [],
                'synergy_effects': [],
                'conflict_resolutions': []
            }

        coord_ctx = state['cross_component_coordination']

        # 获取各组件的当前配置
        component_configs = _gather_component_configs(state)

        # 分析组件间依赖关系
        dependencies = _analyze_component_dependencies(component_configs)

        # 识别协同机会
        synergy_opportunities = _identify_synergy_opportunities(component_configs, dependencies)

        # 解决配置冲突
        conflicts, resolutions = _resolve_config_conflicts(component_configs, dependencies)

        # 应用协同优化
        optimized_configs = _apply_synergy_optimizations(component_configs, synergy_opportunities)

        # 更新协调历史
        coordination_record = {
            'timestamp': datetime.now().isoformat(),
            'original_configs': component_configs,
            'optimized_configs': optimized_configs,
            'synergy_opportunities': synergy_opportunities,
            'conflicts': conflicts,
            'resolutions': resolutions
        }
        # 🚀 修复：确保coordination_history是List类型
        coordination_history = coord_ctx.get('coordination_history', [])
        if not isinstance(coordination_history, list):
            coordination_history = []
        coordination_history.append(coordination_record)
        coord_ctx['coordination_history'] = coordination_history
        coord_ctx['component_configs'] = optimized_configs

        # 记录协同效果
        synergy_effects = _calculate_synergy_effects(component_configs, optimized_configs)
        synergy_effects_list = coord_ctx.get('synergy_effects', [])
        if not isinstance(synergy_effects_list, list):
            synergy_effects_list = []
        synergy_effects_list.append({
            'timestamp': datetime.now().isoformat(),
            'effects': synergy_effects
        })
        coord_ctx['synergy_effects'] = synergy_effects_list

        # 将优化后的配置应用到状态
        state = _apply_coordinated_configs(state, optimized_configs)

        logger.info("✅ 跨组件协调节点执行完成")
        logger.info(f"   → 识别协同机会: {len(synergy_opportunities)} 个")
        logger.info(f"   → 解决配置冲突: {len(conflicts)} 个")

        return state

    except Exception as e:
        logger.error(f"❌ 跨组件协调节点执行失败: {e}")
        state['error'] = f"跨组件协调错误: {str(e)}"
        return state


def _optimize_configuration(current_config: Dict[str, Any], execution_context: Dict[str, Any]) -> Dict[str, Any]:
    """执行配置优化逻辑"""
    optimized_config = current_config.copy()

    # 基于执行上下文进行优化
    complexity_score = execution_context.get('complexity_score', 0.0)
    execution_times = execution_context.get('node_execution_times', {})
    errors = execution_context.get('errors', [])

    # 优化超时配置
    if complexity_score > 0.7:
        # 复杂查询增加超时时间
        optimized_config['timeout'] = min(current_config.get('timeout', 30) * 1.5, 120)
    elif complexity_score < 0.3:
        # 简单查询减少超时时间
        optimized_config['timeout'] = max(current_config.get('timeout', 30) * 0.8, 10)

    # 优化重试配置
    if errors:
        # 有错误时增加重试次数
        optimized_config['max_retries'] = min(current_config.get('max_retries', 3) + 1, 5)
    else:
        # 无错误时减少重试次数
        optimized_config['max_retries'] = max(current_config.get('max_retries', 3) - 1, 1)

    # 优化并发配置
    avg_execution_time = sum(execution_times.values()) / len(execution_times) if execution_times else 0
    if avg_execution_time > 10:  # 执行较慢
        optimized_config['concurrency'] = max(current_config.get('concurrency', 3) - 1, 1)
    elif avg_execution_time < 2:  # 执行较快
        optimized_config['concurrency'] = min(current_config.get('concurrency', 3) + 1, 10)

    return optimized_config


def _determine_optimization_reason(execution_context: Dict[str, Any]) -> str:
    """确定优化原因"""
    reasons = []

    if execution_context.get('complexity_score', 0) > 0.7:
        reasons.append("高复杂度查询")
    if execution_context.get('errors'):
        reasons.append("执行错误")
    if execution_context.get('node_execution_times'):
        avg_time = sum(execution_context['node_execution_times'].values()) / len(execution_context['node_execution_times'])
        if avg_time > 10:
            reasons.append("执行时间过长")
        elif avg_time < 2:
            reasons.append("执行时间过短")

    return ", ".join(reasons) if reasons else "定期优化"


def _calculate_config_performance_metrics(history: List[Dict[str, Any]]) -> Dict[str, float]:
    """计算配置性能指标"""
    if not history:
        return {}

    recent_history = history[-10:]  # 最近10次优化

    # 计算优化成功率（简化逻辑）
    success_count = sum(1 for record in recent_history if record.get('optimized_config'))
    success_rate = success_count / len(recent_history) if recent_history else 0

    # 计算平均改进幅度（简化逻辑）
    improvements = []
    for i in range(1, len(recent_history)):
        prev_config = recent_history[i-1].get('optimized_config', {})
        curr_config = recent_history[i].get('optimized_config', {})

        # 简单的改进计算（实际应该基于性能指标）
        if prev_config and curr_config:
            improvement = len(curr_config) - len(prev_config)  # 配置项数量变化
            improvements.append(improvement)

    avg_improvement = sum(improvements) / len(improvements) if improvements else 0

    return {
        'optimization_success_rate': success_rate,
        'average_improvement': avg_improvement,
        'total_optimizations': len(history)
    }


def _apply_optimized_config(state: "ResearchSystemState", optimized_config: Dict[str, Any]) -> "ResearchSystemState":
    """应用优化后的配置"""
    # 将配置应用到相关状态字段
    for key, value in optimized_config.items():
        if key == 'timeout':
            state['global_timeout'] = value
        elif key == 'max_retries':
            state['max_retries'] = value
        elif key == 'concurrency':
            state['concurrency_limit'] = value
        else:
            # 其他配置项存储在配置上下文中
            if 'applied_configs' not in state:
                state['applied_configs'] = {}
            state['applied_configs'][key] = value

    return state


def _collect_execution_feedback(state: "ResearchSystemState") -> Dict[str, Any]:
    """收集执行结果反馈"""
    feedback = {
        'success': state.get('task_complete', False),
        'total_execution_time': state.get('execution_time', 0),
        'node_execution_times': state.get('node_execution_times', {}),
        'final_answer_quality': _assess_answer_quality(state),
        'route_path': state.get('route_path', 'unknown')
    }

    return feedback


def _collect_performance_feedback(state: "ResearchSystemState") -> Dict[str, Any]:
    """收集性能反馈"""
    feedback = {
        'token_usage': state.get('token_usage', {}),
        'api_calls': state.get('api_calls', {}),
        'node_execution_times': state.get('node_execution_times', {}),
        'memory_usage': state.get('memory_usage', {}),
        'cpu_usage': state.get('cpu_usage', {})
    }

    return feedback


def _collect_error_feedback(state: "ResearchSystemState") -> Optional[Dict[str, Any]]:
    """收集错误反馈"""
    errors = state.get('errors', [])
    if not errors:
        return None

    feedback = {
        'error_count': len(errors),
        'error_categories': list(set(error.get('category', 'unknown') for error in errors)),
        'most_common_error': _find_most_common_error(errors),
        'error_nodes': list(set(error.get('node', 'unknown') for error in errors))
    }

    return feedback


def _identify_learning_opportunities(state: "ResearchSystemState") -> List[Dict[str, Any]]:
    """识别学习机会"""
    opportunities = []

    # 基于错误识别学习机会
    errors = state.get('errors', [])
    for error in errors:
        if error.get('category') in ['retryable', 'temporary']:
            opportunities.append({
                'type': 'error_pattern_learning',
                'error_category': error['category'],
                'error_message': error.get('message', ''),
                'learning_action': 'improve_error_handling'
            })

    # 基于性能识别学习机会
    execution_times = state.get('node_execution_times', {})
    slow_nodes = [node for node, time in execution_times.items() if time > 10]
    if slow_nodes:
        opportunities.append({
            'type': 'performance_optimization',
            'slow_nodes': slow_nodes,
            'learning_action': 'optimize_slow_components'
        })

    return opportunities


def _collect_node_execution_feedback(state: "ResearchSystemState") -> Dict[str, Any]:
    """🚀 改进：从主流程各个节点收集详细的执行数据"""
    node_feedback = {}
    
    # 收集主流程关键节点的执行数据
    main_flow_nodes = [
        'memory_agent', 'knowledge_retrieval_agent', 'reasoning_agent',
        'answer_generation_agent', 'citation_agent', 'synthesize'
    ]
    
    node_execution_times = state.get('node_execution_times', {})
    node_times = state.get('node_times', {})
    
    for node_name in main_flow_nodes:
        node_data = {
            'executed': node_name in node_execution_times or node_name in node_times,
            'execution_time': node_execution_times.get(node_name) or node_times.get(node_name, 0),
            'has_output': False
        }
        
        # 检查节点是否有输出
        if node_name == 'memory_agent':
            node_data['has_output'] = bool(state.get('user_context') or state.get('session_context'))
        elif node_name == 'knowledge_retrieval_agent':
            node_data['has_output'] = bool(state.get('knowledge') or state.get('evidence'))
        elif node_name == 'reasoning_agent':
            node_data['has_output'] = bool(state.get('reasoning_answer') or state.get('reasoning_result'))
        elif node_name == 'answer_generation_agent':
            node_data['has_output'] = bool(state.get('answer') or state.get('generated_answer'))
        elif node_name == 'citation_agent':
            node_data['has_output'] = bool(state.get('citations'))
        elif node_name == 'synthesize':
            node_data['has_output'] = bool(state.get('final_answer') or state.get('synthesized_answer'))
        
        node_feedback[node_name] = node_data
    
    # 收集路由决策数据
    node_feedback['routing'] = {
        'route_path': state.get('route_path', 'unknown'),
        'complexity_score': state.get('complexity_score', 0.0),
        'needs_reasoning_chain': state.get('needs_reasoning_chain', False),
        'task_allocation_decision': state.get('task_allocation_decision', 'unknown')
    }
    
    # 收集主流程执行路径
    node_feedback['execution_path'] = [
        node for node in main_flow_nodes
        if node_feedback[node]['executed']
    ]
    
    return node_feedback


def _assess_answer_quality(state: "ResearchSystemState") -> str:
    """评估答案质量（简化逻辑）"""
    if state.get('error'):
        return 'error'
    elif state.get('final_answer') and len(state.get('citations', [])) > 0:
        return 'high'
    elif state.get('final_answer'):
        return 'medium'
    else:
        return 'low'


def _find_most_common_error(errors: List[Dict[str, Any]]) -> str:
    """找出最常见的错误"""
    if not errors:
        return 'none'
    
    error_counts: Dict[str, int] = {}
    for error in errors:
        category = error.get('category', 'unknown')
        error_counts[category] = error_counts.get(category, 0) + 1

    # 🚀 修复：使用lambda函数作为key参数
    if error_counts:
        return max(error_counts.keys(), key=lambda k: error_counts[k])
    return 'none'


def _gather_component_configs(state: "ResearchSystemState") -> Dict[str, Dict[str, Any]]:
    """收集各组件的配置"""
    configs = {}

    # 从智能体状态收集配置
    agent_states = state.get('agent_states', {})
    for agent_id, agent_state in agent_states.items():
        configs[f"agent_{agent_id}"] = agent_state.get('config', {})

    # 从配置优化上下文收集配置
    config_optimization = state.get('config_optimization', {})
    configs['global_config'] = config_optimization.get('current_config', {})

    # 从协作上下文收集配置
    collaboration_context = state.get('collaboration_context', {})
    configs['collaboration_config'] = collaboration_context.get('config', {})

    return configs


def _analyze_component_dependencies(configs: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """分析组件间依赖关系"""
    dependencies = {}

    # 简化的依赖分析（实际应该基于配置内容）
    for component_id in configs.keys():
        if component_id.startswith('agent_'):
            # 智能体依赖全局配置
            dependencies[component_id] = ['global_config']
        elif component_id == 'global_config':
            dependencies[component_id] = []
        elif component_id == 'collaboration_config':
            # 协作配置依赖所有智能体配置
            agent_configs = [cid for cid in configs.keys() if cid.startswith('agent_')]
            dependencies[component_id] = agent_configs

    return dependencies


def _identify_synergy_opportunities(configs: Dict[str, Dict[str, Any]], dependencies: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """识别协同机会"""
    opportunities = []

    # 检查配置一致性
    timeout_configs = {}
    for component_id, config in configs.items():
        if 'timeout' in config:
            timeout_configs[component_id] = config['timeout']

    if len(set(timeout_configs.values())) > 1:
        opportunities.append({
            'type': 'config_consistency',
            'components': list(timeout_configs.keys()),
            'config_key': 'timeout',
            'current_values': timeout_configs,
            'optimization': 'align_timeout_values'
        })

    # 检查资源分配协同
    concurrency_configs = {}
    for component_id, config in configs.items():
        if 'concurrency' in config:
            concurrency_configs[component_id] = config['concurrency']

    total_concurrency = sum(concurrency_configs.values())
    if total_concurrency > 10:  # 假设系统总并发限制为10
        opportunities.append({
            'type': 'resource_optimization',
            'components': list(concurrency_configs.keys()),
            'total_concurrency': total_concurrency,
            'limit': 10,
            'optimization': 'balance_concurrency_allocation'
        })

    return opportunities


def _resolve_config_conflicts(configs: Dict[str, Dict[str, Any]], dependencies: Dict[str, List[str]]) -> tuple:
    """解决配置冲突"""
    conflicts = []
    resolutions = []

    # 检测端口冲突（示例）
    ports = {}
    for component_id, config in configs.items():
        if 'port' in config:
            port = config['port']
            if port in ports:
                conflicts.append({
                    'type': 'port_conflict',
                    'components': [ports[port], component_id],
                    'conflicting_value': port
                })
            else:
                ports[port] = component_id

    # 解决端口冲突
    for conflict in conflicts:
        if conflict['type'] == 'port_conflict':
            # 简单的解决策略：为第二个组件分配新端口
            component_id = conflict['components'][1]
            new_port = conflict['conflicting_value'] + 1
            configs[component_id]['port'] = new_port
            resolutions.append({
                'conflict': conflict,
                'resolution': f"将 {component_id} 的端口从 {conflict['conflicting_value']} 改为 {new_port}"
            })

    return conflicts, resolutions


def _apply_synergy_optimizations(configs: Dict[str, Dict[str, Any]], opportunities: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """应用协同优化"""
    optimized_configs = {cid: config.copy() for cid, config in configs.items()}

    for opportunity in opportunities:
        if opportunity['type'] == 'config_consistency':
            # 对齐超时配置
            timeout_values = [optimized_configs[cid].get('timeout', 30) for cid in opportunity['components']]
            avg_timeout = sum(timeout_values) / len(timeout_values)

            for component_id in opportunity['components']:
                optimized_configs[component_id]['timeout'] = int(avg_timeout)

        elif opportunity['type'] == 'resource_optimization':
            # 平衡并发分配
            components = opportunity['components']
            target_total = opportunity['limit']
            equal_share = target_total // len(components)

            for component_id in components:
                optimized_configs[component_id]['concurrency'] = equal_share

    return optimized_configs


def _calculate_synergy_effects(original_configs: Dict[str, Dict[str, Any]], optimized_configs: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
    """计算协同效果"""
    effects = {}

    # 计算配置一致性改进
    original_consistency = _calculate_config_consistency(original_configs)
    optimized_consistency = _calculate_config_consistency(optimized_configs)
    effects['consistency_improvement'] = optimized_consistency - original_consistency

    # 计算资源利用效率改进
    original_efficiency = _calculate_resource_efficiency(original_configs)
    optimized_efficiency = _calculate_resource_efficiency(optimized_configs)
    effects['efficiency_improvement'] = optimized_efficiency - original_efficiency

    return effects


def _calculate_config_consistency(configs: Dict[str, Dict[str, Any]]) -> float:
    """计算配置一致性（0-1之间）"""
    # 简化的计算：检查超时配置的标准差
    timeouts = [config.get('timeout', 30) for config in configs.values()]
    if len(timeouts) <= 1:
        return 1.0

    mean_timeout = sum(timeouts) / len(timeouts)
    variance = sum((t - mean_timeout) ** 2 for t in timeouts) / len(timeouts)
    std_dev = variance ** 0.5

    # 将标准差转换为一致性分数（越小越一致）
    max_expected_std = 30  # 假设最大预期标准差
    consistency = max(0, 1 - (std_dev / max_expected_std))

    return consistency


def _calculate_resource_efficiency(configs: Dict[str, Dict[str, Any]]) -> float:
    """计算资源利用效率（0-1之间）"""
    # 简化的计算：并发配置的总和与限制的比率
    total_concurrency = sum(config.get('concurrency', 1) for config in configs.values())
    max_concurrency = 10  # 假设系统最大并发

    efficiency = min(1.0, total_concurrency / max_concurrency)
    return efficiency


def _apply_coordinated_configs(state: "ResearchSystemState", optimized_configs: Dict[str, Dict[str, Any]]) -> "ResearchSystemState":
    """应用协调后的配置"""
    # 更新智能体配置
    for component_id, config in optimized_configs.items():
        if component_id.startswith('agent_'):
            agent_id = component_id[6:]  # 移除 'agent_' 前缀
            if agent_id in state['agent_states']:
                state['agent_states'][agent_id]['config'] = config

    # 更新全局配置
    if 'global_config' in optimized_configs:
        if 'config_optimization' not in state:
            state['config_optimization'] = {}
        state['config_optimization']['current_config'] = optimized_configs['global_config']

    # 更新协作配置
    if 'collaboration_config' in optimized_configs:
        state['collaboration_context']['config'] = optimized_configs['collaboration_config']

    return state


# 为了避免循环导入，在文件末尾导入
from src.core.langgraph_unified_workflow import ResearchSystemState, record_node_time
