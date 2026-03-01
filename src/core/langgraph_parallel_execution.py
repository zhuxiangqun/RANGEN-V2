"""
LangGraph 并行执行优化模块

实现节点并行执行，提升工作流性能
"""
import logging
from typing import Dict, Any, List, Optional
from src.core.langgraph_unified_workflow import ResearchSystemState

logger = logging.getLogger(__name__)


def merge_parallel_states(states: List[ResearchSystemState]) -> ResearchSystemState:
    """合并并行执行的状态
    
    Args:
        states: 并行执行的状态列表
    
    Returns:
        合并后的状态
    """
    if not states:
        # 返回一个最小有效状态
        return {
            "query": "",
            "context": {},
            "route_path": "simple",
            "complexity_score": 0.0,
            "evidence": [],
            "answer": None,
            "confidence": 0.0,
            "final_answer": None,
            "knowledge": [],
            "citations": [],
            "task_complete": False,
            "error": None,
            "errors": [],
            "execution_time": 0.0,
            "user_context": {},
            "user_id": None,
            "session_id": None,
            "query_type": "general",
            "safety_check_passed": True,
            "sensitive_topics": [],
            "content_filter_applied": False,
            "retry_count": 0,
            "node_execution_times": {},
            "token_usage": {},
            "api_calls": {},
            "metadata": {},
            "workflow_checkpoint_id": None,
            "enhanced_context": {},
            "generated_prompt": None,
            "context_fragments": [],
            "prompt_template": None,
            "query_complexity": None,
            "query_length": 0,
            "scheduling_strategy": {},
            "reasoning_answer": []
        }
    
    if len(states) == 1:
        return states[0]
    
    # 合并所有状态（创建副本）
    # 使用类型转换确保返回类型正确
    merged_state: ResearchSystemState = {**states[0]}  # type: ignore[assignment]
    
    # 合并列表字段（evidence, knowledge, citations）
    for state in states[1:]:
        # 合并证据
        if 'evidence' in state and state['evidence']:
            merged_state.setdefault('evidence', []).extend(state['evidence'])
        
        # 合并知识
        if 'knowledge' in state and state['knowledge']:
            merged_state.setdefault('knowledge', []).extend(state['knowledge'])
        
        # 合并引用
        if 'citations' in state and state['citations']:
            merged_state.setdefault('citations', []).extend(state['citations'])
        
        # 合并上下文片段
        if 'context_fragments' in state and state['context_fragments']:
            merged_state.setdefault('context_fragments', []).extend(state['context_fragments'])
        
        # 合并元数据
        if 'metadata' in state and state['metadata']:
            merged_state.setdefault('metadata', {}).update(state['metadata'])
        
        # 合并节点执行时间
        if 'node_execution_times' in state and state['node_execution_times']:
            merged_state.setdefault('node_execution_times', {}).update(state['node_execution_times'])
        
        # 合并 token 使用
        if 'token_usage' in state and state['token_usage']:
            for key, value in state['token_usage'].items():
                merged_state.setdefault('token_usage', {})[key] = merged_state['token_usage'].get(key, 0) + value
        
        # 合并 API 调用
        if 'api_calls' in state and state['api_calls']:
            for key, value in state['api_calls'].items():
                merged_state.setdefault('api_calls', {})[key] = merged_state['api_calls'].get(key, 0) + value
    
    logger.debug(f"✅ [并行合并] 合并了 {len(states)} 个并行状态")
    return merged_state


async def parallel_merge_node(state: ResearchSystemState) -> ResearchSystemState:
    """并行合并节点 - 用于合并并行执行的结果
    
    注意：这个节点主要用于演示并行执行的概念
    在实际使用中，LangGraph 会自动处理并行节点的状态合并
    """
    # 在元数据中标记已合并（而不是直接在状态中）
    metadata = state.get('metadata', {})
    if metadata.get('_parallel_merged', False):
        return state
    
    # 标记已合并（存储在元数据中）
    metadata['_parallel_merged'] = True
    state['metadata'] = metadata
    logger.debug("✅ [并行合并] 并行执行结果已合并")
    return state
