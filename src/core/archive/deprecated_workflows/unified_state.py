"""
统一状态定义 - ExtendedAgentState

目标: 统一 4 种现有的状态定义，提供一个标准化的状态接口

现有状态定义:
- AgentState (execution_coordinator.py) - 10 字段, 生产使用
- ResearchSystemState (langgraph_unified_workflow.py) - 60+ 字段, 未使用
- LayeredWorkflowState (langgraph_layered_workflow.py) - 15 字段
- SimplifiedBusinessState (simplified_business_workflow.py) - 10 字段

设计原则:
- 保持 AgentState 的简洁性 (生产验证)
- 添加必要的高级字段
- 避免过度设计
"""

from typing import Dict, Any, TypedDict, Annotated, Literal, Optional, List
from datetime import datetime
import operator


class ExtendedAgentState(TypedDict):
    """
    统一状态定义 - 生产就绪版本
    
    字段说明:
    - 核心字段 (前10个): 与 AgentState 完全兼容
    - 扩展字段: 添加必要的高级功能
    """
    
    # === 核心字段 (与 AgentState 兼容) ===
    query: str                          # 用户查询
    context: Dict[str, Any]             # 上下文
    route: str                          # 路由路径
    steps: Annotated[list, operator.add] # 执行步骤
    final_answer: str                   # 最终答案
    error: str                          # 错误信息
    quality_score: float               # 质量分数
    quality_passed: bool               # 质量是否通过
    quality_feedback: str              # 质量反馈
    retry_count: int                   # 重试次数
    
    # === 扩展字段 (新增) ===
    
    # 用户上下文
    user_id: Optional[str]              # 用户ID
    session_id: Optional[str]          # 会话ID
    
    # 执行信息
    route_path: Optional[Literal["simple", "complex", "multi_agent", "reasoning_chain"]]
    query_type: Optional[str]           # 查询类型
    complexity_score: Optional[float]   # 复杂度分数 (0-1)
    
    # 安全控制
    safety_check_passed: Optional[bool] # 安全检查是否通过
    sensitive_topics: Optional[List[str]] # 敏感话题
    
    # 证据和引用
    evidence: Optional[List[Dict[str, Any]]]  # 收集的证据
    citations: Optional[List[Dict[str, Any]]]  # 引用
    
    # 性能监控
    node_execution_times: Optional[Dict[str, float]]  # 节点执行时间
    token_usage: Optional[Dict[str, int]]              # Token 使用量
    api_calls: Optional[Dict[str, int]]               # API 调用次数
    
    # 推理路径
    reasoning_steps: Optional[List[Dict[str, Any]]]   # 推理步骤
    current_step_index: Optional[int]                  # 当前步骤索引
    
    # 协作信息
    agent_states: Optional[Dict[str, Dict[str, Any]]]  # Agent 状态
    collaboration_context: Optional[Dict[str, Any]]     # 协作上下文
    
    # 元数据
    created_at: Optional[datetime]    # 创建时间
    updated_at: Optional[datetime]    # 更新时间
    
    # 任务状态
    task_complete: Optional[bool]     # 任务是否完成
    errors: Optional[List[Dict[str, Any]]]  # 错误列表


def create_extended_state(initial: Dict[str, Any] = None) -> ExtendedAgentState:
    """创建 ExtendedAgentState 实例"""
    default: ExtendedAgentState = {
        # 核心字段
        "query": "",
        "context": {},
        "route": "direct",
        "steps": [],
        "final_answer": "",
        "error": "",
        "quality_score": 0.0,
        "quality_passed": False,
        "quality_feedback": "",
        "retry_count": 0,
        
        # 扩展字段
        "user_id": None,
        "session_id": None,
        "route_path": "simple",
        "query_type": "general",
        "complexity_score": 0.0,
        "safety_check_passed": True,
        "sensitive_topics": [],
        "evidence": [],
        "citations": [],
        "node_execution_times": {},
        "token_usage": {},
        "api_calls": {},
        "reasoning_steps": [],
        "current_step_index": 0,
        "agent_states": {},
        "collaboration_context": {},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "task_complete": False,
        "errors": [],
    }
    
    if initial:
        default.update(initial)
    
    return default


def convert_to_agent_state(extended: ExtendedAgentState) -> Dict[str, Any]:
    """
    将 ExtendedAgentState 转换为 AgentState (向后兼容)
    
    用于与现有代码兼容
    """
    return {
        "query": extended.get("query", ""),
        "context": extended.get("context", {}),
        "route": extended.get("route", "direct"),
        "steps": extended.get("steps", []),
        "final_answer": extended.get("final_answer", ""),
        "error": extended.get("error", ""),
        "quality_score": extended.get("quality_score", 0.0),
        "quality_passed": extended.get("quality_passed", False),
        "quality_feedback": extended.get("quality_feedback", ""),
        "retry_count": extended.get("retry_count", 0),
    }


def convert_from_agent_state(agent_state: Dict[str, Any]) -> ExtendedAgentState:
    """
    将 AgentState 转换为 ExtendedAgentState (向后兼容)
    
    用于与现有代码兼容
    """
    extended = create_extended_state(agent_state)
    return extended
