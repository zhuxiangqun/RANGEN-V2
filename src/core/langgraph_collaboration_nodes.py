"""
协作节点模块 - LangGraph集成

将通信中间件、冲突检测和任务分配功能集成到LangGraph工作流中：
- 协作通信节点：使用LangGraph状态传递替代独立消息队列
- 任务分配路由节点：使用条件路由替代独立分配器
- 冲突检测验证节点：作为工作流验证步骤
"""

import logging
import time
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime

logger = logging.getLogger(__name__)


def agent_collaboration_node(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    智能体协作通信节点

    使用LangGraph状态管理系统替代独立的通信中间件。
    处理智能体间的消息传递、状态同步和协作上下文管理。

    Args:
        state: LangGraph工作流状态

    Returns:
        更新后的状态
    """
    start_time = time.time()

    try:
        # 初始化协作状态（如果不存在）
        if 'agent_states' not in state:
            state['agent_states'] = {}

        if 'collaboration_context' not in state:
            state['collaboration_context'] = {
                'session_id': f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'participants': [],
                'shared_knowledge': {},
                'collaboration_goals': [],
                'start_time': datetime.now().isoformat()
            }

        if 'agent_messages' not in state:
            state['agent_messages'] = []

        if 'agent_performance' not in state:
            state['agent_performance'] = {}

        # 基于查询复杂度决定是否需要多智能体协作
        complexity_score = state.get('complexity_score', 0.0)
        query_type = state.get('query_type', 'simple')

        # 对于复杂查询，初始化多智能体协作
        if complexity_score > 0.6 or query_type in ['complex', 'multi_agent']:
            state = _initialize_multi_agent_collaboration(state)
        else:
            # 简单查询使用单智能体模式
            state = _handle_single_agent_mode(state)

        # 处理智能体间消息传递
        state = _process_agent_communication(state)

        # 更新协作上下文
        state = _update_collaboration_context(state)

        # 记录性能指标
        execution_time = time.time() - start_time
        state = record_node_time(state, "agent_collaboration_node", execution_time)

        logger.info(f"✅ 智能体协作节点执行完成，协作模式: {'multi_agent' if complexity_score > 0.6 else 'single_agent'}")
        return state

    except Exception as e:
        logger.error(f"❌ 智能体协作节点执行失败: {e}")
        state['error'] = f"智能体协作节点错误: {str(e)}"
        return state


def _initialize_multi_agent_collaboration(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    初始化多智能体协作

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    # 定义智能体角色和能力
    agent_definitions = {
        'knowledge_retrieval_agent': {
            'role': 'knowledge_retrieval',
            'capabilities': ['search', 'retrieve', 'filter'],
            'specialization': 'information_gathering',
            'status': 'idle'
        },
        'reasoning_agent': {
            'role': 'reasoning',
            'capabilities': ['analyze', 'reason', 'infer'],
            'specialization': 'logical_reasoning',
            'status': 'idle'
        },
        'answer_generation_agent': {
            'role': 'answer_generation',
            'capabilities': ['generate', 'format', 'summarize'],
            'specialization': 'content_creation',
            'status': 'idle'
        },
        'citation_agent': {
            'role': 'citation',
            'capabilities': ['cite', 'reference', 'validate'],
            'specialization': 'source_validation',
            'status': 'idle'
        }
    }

    # 初始化智能体状态
    for agent_id, agent_info in agent_definitions.items():
        state['agent_states'][agent_id] = {
            **agent_info,
            'last_active': datetime.now().isoformat(),
            'performance_metrics': {
                'response_time': 0.0,
                'success_rate': 1.0,
                'task_completion_rate': 1.0
            },
            'current_task': None,
            'message_queue': []
        }

    # 更新协作上下文
    state['collaboration_context']['participants'] = list(agent_definitions.keys())
    state['collaboration_context']['collaboration_mode'] = 'multi_agent'
    state['collaboration_context']['agent_roles'] = agent_definitions

    # 发送初始化消息
    init_message = {
        'message_id': f"init_{datetime.now().strftime('%H%M%S')}",
        'sender': 'collaboration_coordinator',
        'receiver': 'all_agents',
        'type': 'collaboration_init',
        'content': {
            'query': state['query'],
            'complexity_score': state.get('complexity_score', 0.0),
            'collaboration_goals': ['analyze_query', 'gather_evidence', 'generate_reasoning', 'create_answer']
        },
        'timestamp': datetime.now().isoformat(),
        'priority': 'high'
    }

    state['agent_messages'].append(init_message)

    logger.info(f"🔄 初始化多智能体协作，参与者: {list(agent_definitions.keys())}")
    return state


def _handle_single_agent_mode(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    处理单智能体模式

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    # 单智能体模式下，简化协作上下文
    state['collaboration_context']['participants'] = ['chief_agent']
    state['collaboration_context']['collaboration_mode'] = 'single_agent'

    # 初始化首席智能体状态
    state['agent_states']['chief_agent'] = {
        'role': 'chief_agent',
        'capabilities': ['coordinate', 'process', 'respond'],
        'specialization': 'unified_processing',
        'status': 'active',
        'last_active': datetime.now().isoformat(),
        'performance_metrics': {
            'response_time': 0.0,
            'success_rate': 1.0,
            'task_completion_rate': 1.0
        },
        'current_task': 'process_query',
        'message_queue': []
    }

    return state


def _process_agent_communication(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    处理智能体间通信

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    messages = state.get('agent_messages', [])

    # 处理待处理的消息
    for message in messages:
        if message.get('processed', False):
            continue

        receiver = message.get('receiver')

        if receiver == 'all_agents':
            # 广播消息
            for agent_id in state['agent_states'].keys():
                if agent_id != message.get('sender'):
                    _deliver_message_to_agent(state, message, agent_id)
        elif receiver in state['agent_states']:
            # 点对点消息
            _deliver_message_to_agent(state, message, receiver)
        else:
            logger.warning(f"未知消息接收者: {receiver}")

        # 标记消息为已处理
        message['processed'] = True
        message['processed_at'] = datetime.now().isoformat()

    return state


def _deliver_message_to_agent(state: "ResearchSystemState", message: Dict[str, Any], agent_id: str):
    """
    向智能体投递消息

    Args:
        state: 当前状态
        message: 消息内容
        agent_id: 智能体ID
    """
    if agent_id not in state['agent_states']:
        logger.warning(f"智能体 {agent_id} 不存在")
        return

    # 添加到智能体的消息队列
    agent_state = state['agent_states'][agent_id]
    agent_state['message_queue'].append(message)

    # 更新智能体状态
    agent_state['last_active'] = datetime.now().isoformat()
    agent_state['status'] = 'active'

    # 记录消息接收
    logger.debug(f"📨 消息投递: {message.get('type')} -> {agent_id}")


def _update_collaboration_context(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    更新协作上下文

    Args:
        state: 当前状态

    Returns:
        更新后的状态
    """
    context = state['collaboration_context']

    # 更新参与者状态
    active_participants = []
    for agent_id, agent_state in state['agent_states'].items():
        if agent_state.get('status') == 'active':
            active_participants.append(agent_id)

    context['active_participants'] = active_participants
    context['total_messages'] = len(state.get('agent_messages', []))
    context['last_updated'] = datetime.now().isoformat()

    # 更新共享知识
    shared_knowledge = context.get('shared_knowledge', {})

    # 从智能体状态收集共享知识
    for agent_id, agent_state in state['agent_states'].items():
        agent_knowledge = agent_state.get('contributions', {})
        for key, value in agent_knowledge.items():
            if key not in shared_knowledge or \
               value.get('timestamp', '') > shared_knowledge[key].get('timestamp', ''):
                shared_knowledge[key] = {
                    **value,
                    'source_agent': agent_id,
                    'shared_at': datetime.now().isoformat()
                }

    context['shared_knowledge'] = shared_knowledge

    return state


def task_allocation_router(state: "ResearchSystemState") -> Literal["knowledge_retrieval", "reasoning_path", "answer_generation", "single_agent_flow"]:
    """
    任务分配路由节点

    使用条件路由替代独立的智能任务分配器。
    基于查询特征和智能体状态进行智能路由决策。

    Args:
        state: LangGraph工作流状态

    Returns:
        下一个节点的路由决策
    """
    try:
        complexity_score = state.get('complexity_score', 0.0)
        query_type = state.get('query_type', 'simple')
        agent_states = state.get('agent_states', {})

        # 获取智能体可用性和性能
        available_agents = {
            agent_id: agent_state
            for agent_id, agent_state in agent_states.items()
            if agent_state.get('status') == 'active'
        }

        if not available_agents:
            # 没有可用的智能体，使用单智能体模式
            logger.info("⚠️ 没有可用的智能体，使用单智能体模式")
            return "single_agent_flow"

        # 基于复杂度进行路由决策
        decision = "single_agent_flow"  # 默认决策

        if complexity_score > 0.8:
            # 非常复杂的查询：使用完整的多智能体流程
            if _check_agent_availability(available_agents, ['knowledge_retrieval_agent', 'reasoning_agent', 'answer_generation_agent']):
                logger.info("🔀 复杂查询：路由到多智能体完整流程")
                decision = "knowledge_retrieval"
            else:
                logger.warning("⚠️ 复杂查询但智能体不可用，回退到单智能体")
                decision = "single_agent_flow"

        elif complexity_score > 0.5:
            # 中等复杂度：使用推理路径
            if _check_agent_availability(available_agents, ['reasoning_agent']):
                logger.info("🔀 中等复杂度：路由到推理路径")
                decision = "reasoning_path"
            else:
                decision = "single_agent_flow"

        elif query_type == 'factual' or 'what' in state['query'].lower():
            # 事实性问题：优先使用知识检索
            if _check_agent_availability(available_agents, ['knowledge_retrieval_agent']):
                logger.info("🔀 事实性问题：路由到知识检索")
                decision = "knowledge_retrieval"
            else:
                decision = "single_agent_flow"

        else:
            # 默认使用答案生成
            if _check_agent_availability(available_agents, ['answer_generation_agent']):
                logger.info("🔀 默认路径：路由到答案生成")
                decision = "answer_generation"
            else:
                decision = "single_agent_flow"

        # 在状态中记录任务分配决策
        state['task_allocation_decision'] = decision
        return decision

    except Exception as e:
        logger.error(f"❌ 任务分配路由失败: {e}")
        # 出错时回退到单智能体模式
        return "single_agent_flow"


def _check_agent_availability(agent_states: Dict[str, Dict[str, Any]], required_agents: List[str]) -> bool:
    """
    检查智能体可用性

    Args:
        agent_states: 智能体状态字典
        required_agents: 需要的智能体列表

    Returns:
        是否所有需要的智能体都可用
    """
    for agent_id in required_agents:
        if agent_id not in agent_states:
            return False

        agent_state = agent_states[agent_id]
        if agent_state.get('status') != 'active':
            return False

        # 检查性能指标
        performance = agent_state.get('performance_metrics', {})
        success_rate = performance.get('success_rate', 1.0)
        if success_rate < 0.7:  # 成功率低于70%认为不可用
            return False

    return True


def conflict_detection_validator(state: "ResearchSystemState") -> "ResearchSystemState":
    """
    冲突检测验证节点

    作为工作流验证步骤，检测和解决协作冲突。
    替代独立的冲突检测与解决系统。

    Args:
        state: LangGraph工作流状态

    Returns:
        更新后的状态
    """
    try:
        conflicts = []

        # 检测任务分配冲突
        allocation_conflicts = _detect_task_allocation_conflicts(state)
        conflicts.extend(allocation_conflicts)

        # 检测资源竞争冲突
        resource_conflicts = _detect_resource_conflicts(state)
        conflicts.extend(resource_conflicts)

        # 检测智能体过载冲突
        overload_conflicts = _detect_agent_overload_conflicts(state)
        conflicts.extend(overload_conflicts)

        # 存储检测到的冲突
        state['collaboration_conflicts'] = conflicts

        # 设置任务分配决策，用于后续路由（从任务分配路由器传递过来）
        # 如果状态中已有决策，保持不变；否则设置为默认值
        if 'task_allocation_decision' not in state:
            state['task_allocation_decision'] = 'single_agent_flow'

        if conflicts:
            logger.warning(f"⚠️ 检测到 {len(conflicts)} 个协作冲突")

            # 尝试自动解决冲突
            resolved_conflicts, unresolved_conflicts = _resolve_collaboration_conflicts(conflicts, state)

            if unresolved_conflicts:
                # 有无法自动解决的冲突，标记需要人工干预
                state['error'] = f"检测到 {len(unresolved_conflicts)} 个无法自动解决的冲突"
                logger.error(f"❌ 存在无法自动解决的冲突: {len(unresolved_conflicts)} 个")
                # 冲突无法解决时，回退到单智能体模式
                state['task_allocation_decision'] = 'single_agent_flow'
            else:
                logger.info(f"✅ 所有冲突已自动解决: {len(resolved_conflicts)} 个")
        else:
            logger.info("✅ 未检测到协作冲突")

        return state

    except Exception as e:
        logger.error(f"❌ 冲突检测验证失败: {e}")
        state['error'] = f"冲突检测错误: {str(e)}"
        return state


def _detect_task_allocation_conflicts(state: "ResearchSystemState") -> List[Dict[str, Any]]:
    """检测任务分配冲突"""
    conflicts = []
    task_assignments = state.get('task_assignments', {})

    # 检查重复分配
    assigned_tasks = {}
    for task_id, agent_id in task_assignments.items():
        if task_id in assigned_tasks:
            conflicts.append({
                'conflict_type': 'duplicate_assignment',
                'severity': 'high',
                'description': f"任务 {task_id} 被重复分配给 {assigned_tasks[task_id]} 和 {agent_id}",
                'affected_tasks': [task_id],
                'affected_agents': [assigned_tasks[task_id], agent_id],
                'suggested_resolution': 'reassign_to_higher_priority_agent'
            })
        else:
            assigned_tasks[task_id] = agent_id

    # 检查能力不匹配
    agent_states = state.get('agent_states', {})
    for task_id, agent_id in task_assignments.items():
        if agent_id in agent_states:
            agent_caps = set(agent_states[agent_id].get('capabilities', []))
            # 根据任务ID推断所需能力（简化逻辑）
            required_caps = _infer_required_capabilities(task_id)

            if not required_caps.issubset(agent_caps):
                conflicts.append({
                    'conflict_type': 'capability_mismatch',
                    'severity': 'medium',
                    'description': f"智能体 {agent_id} 缺少任务 {task_id} 所需的能力",
                    'affected_tasks': [task_id],
                    'affected_agents': [agent_id],
                    'missing_capabilities': list(required_caps - agent_caps),
                    'suggested_resolution': 'reassign_to_capable_agent'
                })

    return conflicts


def _detect_resource_conflicts(state: "ResearchSystemState") -> List[Dict[str, Any]]:
    """检测资源冲突"""
    conflicts = []
    agent_states = state.get('agent_states', {})

    # 简化的资源冲突检测（可以扩展）
    resource_usage = {}

    for agent_id, agent_state in agent_states.items():
        # 假设每个活跃智能体占用1个资源单位
        if agent_state.get('status') == 'active':
            resource_usage[agent_id] = 1

    total_usage = sum(resource_usage.values())
    if total_usage > 4:  # 假设系统最多支持4个并发智能体
        conflicts.append({
            'conflict_type': 'resource_overload',
            'severity': 'medium',
            'description': f"系统资源过载: {total_usage} 个活跃智能体超过限制",
            'affected_agents': list(resource_usage.keys()),
            'current_usage': total_usage,
            'limit': 4,
            'suggested_resolution': 'reduce_concurrent_agents'
        })

    return conflicts


def _detect_agent_overload_conflicts(state: "ResearchSystemState") -> List[Dict[str, Any]]:
    """检测智能体过载冲突"""
    conflicts = []
    agent_states = state.get('agent_states', {})

    for agent_id, agent_state in agent_states.items():
        message_queue_len = len(agent_state.get('message_queue', []))

        if message_queue_len > 10:  # 消息队列过长
            conflicts.append({
                'conflict_type': 'agent_overload',
                'severity': 'high',
                'description': f"智能体 {agent_id} 消息队列过载: {message_queue_len} 条消息",
                'affected_agents': [agent_id],
                'queue_length': message_queue_len,
                'suggested_resolution': 'redistribute_tasks'
            })

    return conflicts


def _infer_required_capabilities(task_id: str) -> set:
    """推断任务所需的能力（简化逻辑）"""
    if 'knowledge' in task_id.lower() or 'retrieve' in task_id.lower():
        return {'search', 'retrieve'}
    elif 'reasoning' in task_id.lower() or 'analyze' in task_id.lower():
        return {'analyze', 'reason'}
    elif 'answer' in task_id.lower() or 'generate' in task_id.lower():
        return {'generate', 'format'}
    elif 'citation' in task_id.lower() or 'cite' in task_id.lower():
        return {'cite', 'validate'}
    else:
        return {'process'}


def _resolve_collaboration_conflicts(conflicts: List[Dict[str, Any]], state: "ResearchSystemState") -> tuple:
    """解决协作冲突"""
    resolved = []
    unresolved = []

    for conflict in conflicts:
        conflict_type = conflict.get('conflict_type')

        if conflict_type == 'duplicate_assignment':
            # 解决重复分配：保留给更适合的智能体
            if _resolve_duplicate_assignment(conflict, state):
                resolved.append(conflict)
            else:
                unresolved.append(conflict)

        elif conflict_type == 'capability_mismatch':
            # 解决能力不匹配：重新分配给有能力的智能体
            if _resolve_capability_mismatch(conflict, state):
                resolved.append(conflict)
            else:
                unresolved.append(conflict)

        elif conflict_type == 'resource_overload':
            # 解决资源过载：减少并发智能体
            if _resolve_resource_overload(conflict, state):
                resolved.append(conflict)
            else:
                unresolved.append(conflict)

        elif conflict_type == 'agent_overload':
            # 解决智能体过载：重新分配任务
            if _resolve_agent_overload(conflict, state):
                resolved.append(conflict)
            else:
                unresolved.append(conflict)

        else:
            # 未知冲突类型
            unresolved.append(conflict)

    return resolved, unresolved


def _resolve_duplicate_assignment(conflict: Dict[str, Any], state: "ResearchSystemState") -> bool:
    """解决重复分配冲突"""
    affected_agents = conflict.get('affected_agents', [])
    affected_task = conflict.get('affected_tasks', [None])[0]

    if not affected_agents or not affected_task:
        return False

    # 选择性能更好的智能体
    agent_performance = state.get('agent_performance', {})
    best_agent = max(affected_agents,
                    key=lambda a: agent_performance.get(a, {}).get('success_rate', 0.5))

    # 重新分配任务
    task_assignments = state.get('task_assignments', {})
    task_assignments[affected_task] = best_agent

    logger.info(f"✅ 解决重复分配冲突: 任务 {affected_task} 分配给 {best_agent}")
    return True


def _resolve_capability_mismatch(conflict: Dict[str, Any], state: "ResearchSystemState") -> bool:
    """解决能力不匹配冲突"""
    affected_agent = conflict.get('affected_agents', [None])[0]
    affected_task = conflict.get('affected_tasks', [None])[0]
    missing_caps = conflict.get('missing_capabilities', [])

    if not affected_agent or not affected_task:
        return False

    # 寻找有合适能力的智能体
    agent_states = state.get('agent_states', {})
    suitable_agents = []

    for agent_id, agent_state in agent_states.items():
        if agent_id != affected_agent:
            agent_caps = set(agent_state.get('capabilities', []))
            if set(missing_caps).issubset(agent_caps):
                suitable_agents.append(agent_id)

    if suitable_agents:
        # 选择第一个合适的智能体
        new_agent = suitable_agents[0]
        task_assignments = state.get('task_assignments', {})
        task_assignments[affected_task] = new_agent

        logger.info(f"✅ 解决能力不匹配冲突: 任务 {affected_task} 从 {affected_agent} 重新分配给 {new_agent}")
        return True

    return False


def _resolve_resource_overload(conflict: Dict[str, Any], state: "ResearchSystemState") -> bool:
    """解决资源过载冲突"""
    affected_agents = conflict.get('affected_agents', [])

    if len(affected_agents) <= 4:  # 已经在限制内
        return True

    # 暂停部分智能体（简化策略）
    agents_to_pause = affected_agents[4:]  # 保留前4个

    for agent_id in agents_to_pause:
        if agent_id in state['agent_states']:
            state['agent_states'][agent_id]['status'] = 'paused'

    logger.info(f"✅ 解决资源过载冲突: 暂停 {len(agents_to_pause)} 个智能体")
    return True


def _resolve_agent_overload(conflict: Dict[str, Any], state: "ResearchSystemState") -> bool:
    """解决智能体过载冲突"""
    affected_agent = conflict.get('affected_agents', [None])[0]

    if not affected_agent:
        return False

    # 重新分配任务（简化策略：清空消息队列）
    if affected_agent in state['agent_states']:
        state['agent_states'][affected_agent]['message_queue'] = []
        logger.info(f"✅ 解决智能体过载冲突: 清空 {affected_agent} 的消息队列")
        return True

    return False


# 为了避免循环导入，在文件末尾导入
from src.core.langgraph_unified_workflow import ResearchSystemState, record_node_time
