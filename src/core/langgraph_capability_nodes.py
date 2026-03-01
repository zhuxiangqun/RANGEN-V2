"""
能力节点模块 - LangGraph集成

将能力插件框架适配到LangGraph节点接口：
- 能力节点工厂：从插件创建LangGraph节点
- 组合能力子图：将组合能力转换为子图架构
- 标准化接口适配：对接状态协议
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable, Type
from datetime import datetime

logger = logging.getLogger(__name__)


def create_capability_node(capability_plugin) -> Callable[["ResearchSystemState"], "ResearchSystemState"]:
    """
    从能力插件创建LangGraph节点

    Args:
        capability_plugin: 能力插件实例

    Returns:
        LangGraph节点函数
    """
    def capability_node(state: "ResearchSystemState") -> "ResearchSystemState":
        """生成的能力节点函数"""
        start_time = time.time()

        try:
            # 初始化能力上下文
            if 'capability_execution' not in state:
                state['capability_execution'] = {
                    'active_capabilities': [],
                    'execution_history': [],
                    'capability_states': {}
                }

            cap_ctx = state['capability_execution']

            # 准备执行上下文
            execution_context = _prepare_execution_context(state, capability_plugin)

            # 执行能力
            result = capability_plugin.execute(execution_context)

            # 更新能力状态
            capability_id = getattr(capability_plugin, 'capability_id', str(id(capability_plugin)))
            cap_ctx['active_capabilities'].append(capability_id)
            cap_ctx['capability_states'][capability_id] = {
                'status': 'completed',
                'last_execution': datetime.now().isoformat(),
                'result': result,
                'execution_time': time.time() - start_time
            }

            # 记录执行历史
            execution_record = {
                'capability_id': capability_id,
                'capability_name': getattr(capability_plugin, 'name', 'unknown'),
                'execution_time': time.time() - start_time,
                'timestamp': datetime.now().isoformat(),
                'result_summary': str(result)[:100] if result else None
            }
            cap_ctx['execution_history'].append(execution_record)

            # 将执行结果合并到状态
            state = _merge_capability_result(state, result, capability_plugin)

            # 记录节点性能
            execution_time = time.time() - start_time
            state = record_node_time(state, f"capability_{capability_id}", execution_time)

            logger.info(f"✅ 能力节点执行完成: {getattr(capability_plugin, 'name', 'unknown')}")
            return state

        except Exception as e:
            logger.error(f"❌ 能力节点执行失败: {e}")
            state['error'] = f"能力执行错误: {str(e)}"
            return state

    # 🚀 增强：设置节点元数据，确保动态生成的docstring清晰明确
    capability_node.__name__ = f"capability_{getattr(capability_plugin, 'name', 'unknown')}"
    plugin_name = getattr(capability_plugin, 'name', 'unknown')
    plugin_desc = getattr(capability_plugin, 'description', None)
    if plugin_desc:
        capability_node.__doc__ = f"能力节点({plugin_name}) - {plugin_desc}"
    else:
        capability_node.__doc__ = f"能力节点({plugin_name}) - 执行能力插件功能"

    return capability_node


def create_composite_capability_subgraph(composite_capability) -> "StateGraph":
    """
    从组合能力创建LangGraph子图

    Args:
        composite_capability: 组合能力实例

    Returns:
        LangGraph子图
    """
    try:
        from langgraph.graph import StateGraph

        # 创建子图状态类型（继承主状态）
        class CompositeCapabilityState(ResearchSystemState):
            """组合能力子图状态"""
            composite_context: Dict[str, Any]
            component_results: Dict[str, Any]
            execution_order: List[str]

        # 创建子图
        subgraph = StateGraph(CompositeCapabilityState)

        # 初始化子图节点
        subgraph.add_node("composite_init", _composite_init_node)

        # 添加组件能力节点
        component_nodes = {}
        for component in composite_capability.components:
            node_func = create_capability_node(component)
            node_name = f"component_{component.name}"
            subgraph.add_node(node_name, node_func)
            component_nodes[component.name] = node_name

        # 添加组合协调节点
        subgraph.add_node("composite_coordinate", _composite_coordinate_node)

        # 设置执行顺序边
        execution_order = getattr(composite_capability, 'execution_order', [])

        # 从初始化到第一个组件
        if execution_order:
            subgraph.add_edge("composite_init", f"component_{execution_order[0]}")

            # 设置组件间的顺序执行
            for i in range(len(execution_order) - 1):
                current_component = execution_order[i]
                next_component = execution_order[i + 1]
                subgraph.add_edge(f"component_{current_component}", f"component_{next_component}")

            # 从最后一个组件到协调节点
            subgraph.add_edge(f"component_{execution_order[-1]}", "composite_coordinate")

        # 设置子图入口和出口
        subgraph.set_entry_point("composite_init")
        subgraph.set_finish_point("composite_coordinate")

        logger.info(f"✅ 组合能力子图创建完成: {getattr(composite_capability, 'name', 'unknown')}")
        return subgraph

    except Exception as e:
        logger.error(f"❌ 创建组合能力子图失败: {e}")
        raise


def standardized_interface_adapter(state: "ResearchSystemState") -> "ResearchSystemState":
    """标准化接口适配器节点 - 将各种能力插件的接口标准化，与LangGraph状态协议对接"""
    try:
        # 初始化标准化上下文
        if 'standardized_interfaces' not in state:
            state['standardized_interfaces'] = {
                'adapted_capabilities': {},
                'interface_mappings': {},
                'compatibility_matrix': {}
            }

        std_ctx = state['standardized_interfaces']

        # 扫描当前状态中的能力执行结果
        capability_execution = state.get('capability_execution', {})
        capability_states = capability_execution.get('capability_states', {})

        # 为每个能力创建标准化接口
        for capability_id, cap_state in capability_states.items():
            if capability_id not in std_ctx['adapted_capabilities']:
                # 创建标准化适配器
                adapter = _create_standardized_adapter(capability_id, cap_state)
                std_ctx['adapted_capabilities'][capability_id] = adapter

                # 记录接口映射
                std_ctx['interface_mappings'][capability_id] = {
                    'original_interface': _infer_original_interface(cap_state),
                    'standardized_interface': 'CapabilityInterface',
                    'adaptation_rules': adapter.get('adaptation_rules', {})
                }

        # 更新兼容性矩阵
        std_ctx['compatibility_matrix'] = _build_compatibility_matrix(std_ctx['adapted_capabilities'])

        logger.info("✅ 标准化接口适配完成")
        return state

    except Exception as e:
        logger.error(f"❌ 标准化接口适配失败: {e}")
        state['error'] = f"接口适配错误: {str(e)}"
        return state


def _prepare_execution_context(state: "ResearchSystemState", capability_plugin) -> Dict[str, Any]:
    """准备能力执行上下文"""
    context = {
        'query': state.get('query', ''),
        'context': state.get('context', {}),
        'state': state,  # 传递完整状态以供能力访问
        'capability_metadata': {
            'id': getattr(capability_plugin, 'capability_id', str(id(capability_plugin))),
            'name': getattr(capability_plugin, 'name', 'unknown'),
            'version': getattr(capability_plugin, 'version', '1.0'),
            'capabilities': getattr(capability_plugin, 'capabilities', [])
        }
    }

    # 添加相关状态信息
    if hasattr(capability_plugin, 'required_state_keys'):
        for key in capability_plugin.required_state_keys:
            if key in state:
                context[key] = state[key]

    return context


def _merge_capability_result(state: "ResearchSystemState", result: Any, capability_plugin) -> "ResearchSystemState":
    """将能力执行结果合并到状态 - 增强主流程结果"""
    if result is None:
        return state

    capability_name = getattr(capability_plugin, 'name', 'unknown')

    # 🚀 改进：能力节点应该增强主流程的结果，而不是独立生成答案
    # 首先获取主流程的现有结果
    main_answer = state.get('final_answer') or state.get('answer') or state.get('synthesized_answer', '')
    main_evidence = state.get('evidence', [])
    main_knowledge = state.get('knowledge', [])
    main_reasoning = state.get('reasoning_answer', '') or state.get('reasoning_result', '')

    # 根据能力类型决定如何增强主流程结果
    if capability_name == 'knowledge_retrieval':
        # 🚀 增强：合并知识检索结果到主流程的证据和知识
        if 'evidence' not in state:
            state['evidence'] = []
        if isinstance(result, list):
            # 去重合并：只添加新的证据
            existing_evidence_ids = {e.get('id') for e in state['evidence'] if isinstance(e, dict) and 'id' in e}
            for item in result:
                if isinstance(item, dict) and item.get('id') not in existing_evidence_ids:
                    state['evidence'].append(item)
                elif not isinstance(item, dict):
                    state['evidence'].append(item)
        elif isinstance(result, dict):
            if result.get('id') not in existing_evidence_ids:
                state['evidence'].append(result)
        
        # 更新知识库
        if 'knowledge' not in state:
            state['knowledge'] = []
        if isinstance(result, (list, dict)):
            knowledge_items = result if isinstance(result, list) else [result]
            for item in knowledge_items:
                if isinstance(item, dict) and item not in state['knowledge']:
                    state['knowledge'].append(item)
        
        logger.info(f"✅ [能力增强] 知识检索能力增强了主流程: 新增 {len(result) if isinstance(result, list) else 1} 条证据")

    elif capability_name == 'reasoning':
        # 🚀 增强：合并推理结果，增强主流程的推理答案
        if isinstance(result, dict):
            reasoning_content = result.get('reasoning') or result.get('final_answer') or result.get('answer', '')
            if reasoning_content:
                if main_reasoning:
                    combined = f"{main_reasoning}\n\n[能力增强推理]:\n{reasoning_content}"
                else:
                    combined = reasoning_content
                state.setdefault('reasoning_answer', [])
                state['reasoning_answer'].append(str(combined))
                state['reasoning_result'] = {
                    'main_reasoning': main_reasoning,
                    'enhanced_reasoning': reasoning_content,
                    'enhancement_source': 'capability_reasoning'
                } if main_reasoning else reasoning_content
                logger.info("✅ [能力增强] 推理能力增强了主流程的推理结果")
        elif isinstance(result, str):
            if main_reasoning:
                combined = f"{main_reasoning}\n\n[能力增强推理]:\n{result}"
            else:
                combined = result
            state.setdefault('reasoning_answer', [])
            state['reasoning_answer'].append(str(combined))
            logger.info("✅ [能力增强] 推理能力增强了主流程的推理结果")

    elif capability_name == 'answer_generation':
        # 🚀 增强：合并答案生成结果，增强主流程的最终答案
        if isinstance(result, dict):
            enhanced_answer = result.get('answer') or result.get('final_answer', '')
        elif isinstance(result, str):
            enhanced_answer = result
        else:
            enhanced_answer = str(result)
        
        if enhanced_answer:
            # 如果主流程已有答案，进行增强合并
            if main_answer:
                # 智能合并：如果能力答案更详细或补充了主答案，则合并
                if len(enhanced_answer) > len(main_answer) * 1.2 or enhanced_answer not in main_answer:
                    state['final_answer'] = f"{main_answer}\n\n[能力增强补充]:\n{enhanced_answer}"
                    state['answer'] = state['final_answer']  # 同步更新
                    state['capability_enhanced'] = True
                    logger.info("✅ [能力增强] 答案生成能力增强了主流程的最终答案")
                else:
                    logger.info("ℹ️ [能力增强] 能力答案与主流程答案相似，跳过增强")
            else:
                # 主流程没有答案，使用能力生成的答案
                state['final_answer'] = enhanced_answer
                state['answer'] = enhanced_answer
                logger.info("✅ [能力增强] 主流程无答案，使用能力生成的答案")

    elif capability_name == 'citation':
        # 🚀 增强：合并引用结果
        if 'citations' not in state:
            state['citations'] = []
        existing_citation_ids = {c.get('id') for c in state['citations'] if isinstance(c, dict) and 'id' in c}
        if isinstance(result, list):
            for item in result:
                if isinstance(item, dict) and item.get('id') not in existing_citation_ids:
                    state['citations'].append(item)
                elif not isinstance(item, dict):
                    state['citations'].append(item)
        elif isinstance(result, dict):
            if result.get('id') not in existing_citation_ids:
                state['citations'].append(result)
        logger.info(f"✅ [能力增强] 引用能力增强了主流程: 新增 {len(result) if isinstance(result, list) else 1} 条引用")

    else:
        # 默认合并到通用结果
        if 'capability_results' not in state:
            state['capability_results'] = {}
        state['capability_results'][capability_name] = result
        logger.info(f"✅ [能力增强] 能力 {capability_name} 结果已保存到 capability_results")

    # 标记能力增强已执行
    if 'capability_enhancements' not in state:
        state['capability_enhancements'] = []
    state['capability_enhancements'].append({
        'capability': capability_name,
        'timestamp': datetime.now().isoformat(),
        'enhanced_fields': ['answer', 'evidence', 'knowledge', 'reasoning', 'citations']
    })

    return state


def _composite_init_node(state):
    """组合能力初始化节点"""
    if 'composite_context' not in state:
        state['composite_context'] = {
            'start_time': datetime.now().isoformat(),
            'component_sequence': [],
            'intermediate_results': {}
        }

    if 'component_results' not in state:
        state['component_results'] = {}

    if 'execution_order' not in state:
        state['execution_order'] = []

    logger.info("🔄 组合能力子图初始化完成")
    return state


def _composite_coordinate_node(state):
    """组合能力协调节点"""
    composite_context = state.get('composite_context', {})
    component_results = state.get('component_results', {})

    # 合并组件结果
    final_result = _merge_component_results(component_results, composite_context)

    # 更新组合上下文
    composite_context['end_time'] = datetime.now().isoformat()
    composite_context['final_result'] = final_result
    composite_context['component_count'] = len(component_results)

    # 将最终结果添加到主状态
    state['composite_capability_result'] = final_result

    logger.info(f"✅ 组合能力协调完成，合并了 {len(component_results)} 个组件结果")
    return state


def _merge_component_results(component_results: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """合并组件执行结果"""
    merged_result = {
        'component_results': component_results,
        'merge_timestamp': datetime.now().isoformat(),
        'total_components': len(component_results)
    }

    # 根据组件类型进行智能合并
    evidence_results = []
    reasoning_results = []
    answer_results = []
    citation_results = []

    for comp_name, result in component_results.items():
        if isinstance(result, dict):
            if 'evidence' in result or comp_name == 'knowledge_retrieval':
                evidence_results.append(result)
            elif 'reasoning' in result or comp_name == 'reasoning':
                reasoning_results.append(result)
            elif 'answer' in result or comp_name == 'answer_generation':
                answer_results.append(result)
            elif 'citations' in result or comp_name == 'citation':
                citation_results.append(result)

    # 合并同类型结果
    if evidence_results:
        merged_result['evidence'] = _merge_evidence(evidence_results)

    if reasoning_results:
        merged_result['reasoning'] = _merge_reasoning(reasoning_results)

    if answer_results:
        merged_result['answer'] = _merge_answers(answer_results)

    if citation_results:
        merged_result['citations'] = _merge_citations(citation_results)

    return merged_result


def _merge_evidence(evidence_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """合并证据结果"""
    merged = []
    seen_sources = set()

    for evidence_item in evidence_list:
        if isinstance(evidence_item, list):
            for item in evidence_item:
                source = item.get('source', str(id(item)))
                if source not in seen_sources:
                    merged.append(item)
                    seen_sources.add(source)
        elif isinstance(evidence_item, dict):
            source = evidence_item.get('source', str(id(evidence_item)))
            if source not in seen_sources:
                merged.append(evidence_item)
                seen_sources.add(source)

    return merged


def _merge_reasoning(reasoning_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """合并推理结果"""
    if not reasoning_list:
        return {}

    # 取最新的推理结果作为主要结果
    latest_reasoning = reasoning_list[-1]

    # 合并推理步骤
    all_steps = []
    for reasoning in reasoning_list:
        steps = reasoning.get('steps', [])
        all_steps.extend(steps)

    return {
        'primary_reasoning': latest_reasoning,
        'all_steps': all_steps,
        'merged_from': len(reasoning_list)
    }


def _merge_answers(answer_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """合并答案结果"""
    if not answer_list:
        return {}

    # 选择置信度最高的答案
    best_answer = max(answer_list, key=lambda x: x.get('confidence', 0))

    return {
        'best_answer': best_answer,
        'alternative_answers': answer_list,
        'answer_count': len(answer_list)
    }


def _merge_citations(citation_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """合并引用结果"""
    merged = []
    seen_citations = set()

    for citation_item in citation_list:
        if isinstance(citation_item, list):
            for item in citation_item:
                citation_key = (item.get('source', ''), item.get('page', ''), item.get('text', '')[:50])
                if citation_key not in seen_citations:
                    merged.append(item)
                    seen_citations.add(citation_key)
        elif isinstance(citation_item, dict):
            citation_key = (citation_item.get('source', ''), citation_item.get('page', ''), citation_item.get('text', '')[:50])
            if citation_key not in seen_citations:
                merged.append(citation_item)
                seen_citations.add(citation_key)

    return merged


def _create_standardized_adapter(capability_id: str, cap_state: Dict[str, Any]) -> Dict[str, Any]:
    """创建标准化适配器"""
    adapter = {
        'capability_id': capability_id,
        'adaptation_rules': {},
        'interface_mapping': {}
    }

    # 分析执行结果结构
    result = cap_state.get('result')
    if result is None:
        adapter['adaptation_rules']['null_result_handling'] = 'pass_through'
        return adapter

    # 创建适配规则
    if isinstance(result, dict):
        adapter['adaptation_rules']['result_type'] = 'dict'
        adapter['interface_mapping'] = _map_dict_interface(result)

    elif isinstance(result, list):
        adapter['adaptation_rules']['result_type'] = 'list'
        adapter['interface_mapping'] = _map_list_interface(result)

    elif isinstance(result, str):
        adapter['adaptation_rules']['result_type'] = 'string'
        adapter['interface_mapping'] = _map_string_interface(result)

    else:
        adapter['adaptation_rules']['result_type'] = 'primitive'
        adapter['interface_mapping'] = _map_primitive_interface(result)

    return adapter


def _infer_original_interface(cap_state: Dict[str, Any]) -> str:
    """推断原始接口类型"""
    result = cap_state.get('result')

    if result is None:
        return 'null_interface'

    if isinstance(result, dict):
        keys = list(result.keys())
        if 'evidence' in keys:
            return 'knowledge_retrieval_interface'
        elif 'reasoning' in keys:
            return 'reasoning_interface'
        elif 'answer' in keys:
            return 'answer_generation_interface'
        elif 'citations' in keys:
            return 'citation_interface'
        else:
            return 'generic_dict_interface'

    elif isinstance(result, list):
        return 'list_interface'

    elif isinstance(result, str):
        return 'string_interface'

    else:
        return 'primitive_interface'


def _map_dict_interface(result_dict: Dict[str, Any]) -> Dict[str, str]:
    """映射字典接口"""
    mapping = {}

    for key, value in result_dict.items():
        if isinstance(value, str):
            mapping[key] = 'string'
        elif isinstance(value, (int, float)):
            mapping[key] = 'number'
        elif isinstance(value, bool):
            mapping[key] = 'boolean'
        elif isinstance(value, list):
            mapping[key] = 'list'
        elif isinstance(value, dict):
            mapping[key] = 'dict'
        else:
            mapping[key] = 'object'

    return mapping


def _map_list_interface(result_list: List[Any]) -> Dict[str, str]:
    """映射列表接口"""
    if not result_list:
        return {'element_type': 'empty'}

    # 分析列表元素类型
    element_types = set()
    for item in result_list[:5]:  # 只分析前5个元素
        if isinstance(item, str):
            element_types.add('string')
        elif isinstance(item, (int, float)):
            element_types.add('number')
        elif isinstance(item, bool):
            element_types.add('boolean')
        elif isinstance(item, dict):
            element_types.add('dict')
        elif isinstance(item, list):
            element_types.add('list')
        else:
            element_types.add('object')

    return {
        'element_types': list(element_types),
        'list_length': len(result_list)
    }


def _map_string_interface(result_str: str) -> Dict[str, str]:
    """映射字符串接口"""
    return {
        'content_type': 'text',
        'length': len(result_str),
        'encoding': 'utf-8'  # 假设
    }


def _map_primitive_interface(result) -> Dict[str, str]:
    """映射原始类型接口"""
    return {
        'primitive_type': type(result).__name__,
        'value': str(result)
    }


def _build_compatibility_matrix(adapted_capabilities: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """构建兼容性矩阵"""
    capability_ids = list(adapted_capabilities.keys())
    compatibility_matrix = {}

    for i, cap_id1 in enumerate(capability_ids):
        compatibility_matrix[cap_id1] = {}

        for j, cap_id2 in enumerate(capability_ids):
            if i == j:
                compatibility_matrix[cap_id1][cap_id2] = 1.0  # 自兼容
            else:
                # 计算两个能力的兼容性
                compat_score = _calculate_capability_compatibility(
                    adapted_capabilities[cap_id1],
                    adapted_capabilities[cap_id2]
                )
                compatibility_matrix[cap_id1][cap_id2] = compat_score

    return compatibility_matrix


def _calculate_capability_compatibility(cap1: Dict[str, Any], cap2: Dict[str, Any]) -> float:
    """计算两个能力的兼容性分数"""
    # 简化的兼容性计算
    rules1 = cap1.get('adaptation_rules', {})
    rules2 = cap2.get('adaptation_rules', {})

    # 类型兼容性
    type1 = rules1.get('result_type', 'unknown')
    type2 = rules2.get('result_type', 'unknown')

    if type1 == type2:
        base_score = 0.8  # 同类型高兼容
    elif {type1, type2} <= {'dict', 'list'}:
        base_score = 0.6  # 结构化类型中等兼容
    elif type1 == 'string' or type2 == 'string':
        base_score = 0.4  # 与字符串类型低兼容
    else:
        base_score = 0.2  # 其他类型低兼容

    # 接口映射兼容性
    mapping1 = cap1.get('interface_mapping', {})
    mapping2 = cap2.get('interface_mapping', {})

    # 如果有共同的接口字段，增加兼容性
    common_fields = set(mapping1.keys()) & set(mapping2.keys())
    if common_fields:
        field_bonus = len(common_fields) * 0.1
        base_score = min(1.0, base_score + field_bonus)

    return base_score


# 为了避免循环导入，在文件末尾导入
from src.core.langgraph_unified_workflow import ResearchSystemState, record_node_time
