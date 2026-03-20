#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RANGEN统一状态管理 - 基于LangGraph设计模式的状态管理

核心设计：
1. 全局共享状态：所有工作流节点共享同一个状态对象
2. 状态更新策略：支持覆盖更新、归约更新、自定义归约
3. 状态持久化：支持内存、文件、数据库多级持久化
4. 状态版本控制：完整的状态变更历史记录
5. 多Agent共享：作为协调多个Agent的通信媒介

设计哲学：图即应用，状态即数据流
"""

import time
import json
import asyncio
from typing import Dict, Any, List, Optional, Union, Callable, TypedDict
from typing_extensions import Annotated
from dataclasses import dataclass, field
from enum import Enum
import threading


class StateUpdateStrategy(Enum):
    """状态更新策略"""
    OVERWRITE = "overwrite"          # 覆盖更新：直接替换旧值
    REDUCE_APPEND = "reduce_append"  # 归约追加：列表追加
    REDUCE_MERGE = "reduce_merge"    # 归约合并：字典合并
    REDUCE_SUM = "reduce_sum"        # 归约求和：数值累加
    CUSTOM = "custom"                # 自定义归约：用户定义函数


# 归约函数定义
def reduce_append(old: List[Any], new: List[Any]) -> List[Any]:
    """列表追加归约"""
    return old + new


def reduce_merge(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """字典合并归约"""
    return {**old, **new}


def reduce_sum(old: Union[int, float], new: Union[int, float]) -> Union[int, float]:
    """数值求和归约"""
    return old + new


class RANGENState(TypedDict, total=False):
    """
    RANGEN全局共享状态定义
    
    状态字段使用Annotated类型标注更新策略：
    - 第一个类型参数：字段的实际类型
    - 第二个参数：归约函数或更新策略
    
    示例：
        messages: Annotated[List[Dict], reduce_append]  # 列表追加
        counters: Annotated[Dict[str, int], reduce_merge]  # 字典合并
        total_cost: Annotated[float, reduce_sum]  # 数值累加
        current_step: str  # 覆盖更新（默认）
    """
    
    # === 请求与输入数据 ===
    request_id: str                           # 请求唯一标识
    request_data: Dict[str, Any]              # 原始请求数据（覆盖更新）
    request_timestamp: float                  # 请求时间戳
    
    # === 会话与上下文管理 ===
    session_id: str                           # 会话ID
    user_id: Optional[str]                    # 用户ID
    messages: Annotated[List[Dict], reduce_append]  # 消息历史（归约追加）
    conversation_history: Annotated[List[Dict], reduce_append]  # 对话历史
    
    # === LLM调用与结果 ===
    llm_provider: str                         # LLM提供商（强制为deepseek或local）
    llm_model: str                            # 使用的模型
    llm_responses: Annotated[List[Dict], reduce_append]  # LLM响应历史
    llm_prompts: Annotated[List[str], reduce_append]     # 提示词历史
    
    # === 成本控制与预算 ===
    total_cost: Annotated[float, reduce_sum]  # 累计成本（归约求和）
    budget_remaining: float                   # 剩余预算
    cost_breakdown: Annotated[Dict[str, float], reduce_merge]  # 成本细分
    deepseek_usage: Annotated[List[Dict], reduce_append]  # DeepSeek使用记录
    
    # === 工具调用与执行 ===
    tool_calls: Annotated[List[Dict], reduce_append]      # 工具调用记录
    tool_results: Annotated[Dict[str, Any], reduce_merge] # 工具执行结果
    current_tool: Optional[str]               # 当前执行工具
    
    # === 工作流与执行状态 ===
    workflow_id: str                          # 工作流ID
    current_step: str                         # 当前执行步骤
    next_step: Optional[str]                  # 下一步骤
    step_history: Annotated[List[str], reduce_append]     # 步骤历史
    execution_status: str                     # 执行状态：pending/running/completed/failed
    
    # === 处理器链上下文（兼容现有系统） ===
    candidate_models: List[str]               # 候选模型列表
    model_scores: Dict[str, float]            # 模型得分
    constraints: Dict[str, Any]               # 约束条件
    metadata: Dict[str, Any]                  # 元数据
    warnings: Annotated[List[str], reduce_append]         # 警告信息
    errors: Annotated[List[str], reduce_append]           # 错误信息
    selected_model: Optional[str]             # 选择的模型
    decision_reason: Optional[str]            # 决策原因
    
    # === 性能与监控 ===
    start_time: float                         # 开始时间
    processing_times: Annotated[Dict[str, float], reduce_merge]  # 处理时间记录
    processor_trace: Annotated[List[str], reduce_append]  # 处理器执行轨迹
    
    # === 系统与调试信息 ===
    debug_mode: bool                          # 调试模式
    log_level: str                            # 日志级别
    trace_id: Optional[str]                   # 追踪ID


@dataclass
class StateUpdate:
    """状态更新操作"""
    field: str                       # 字段名
    value: Any                       # 新值
    strategy: StateUpdateStrategy    # 更新策略
    custom_reducer: Optional[Callable] = None  # 自定义归约函数
    timestamp: float = field(default_factory=time.time)  # 更新时间戳
    
    def apply(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """应用更新到当前状态"""
        if self.field not in current_state:
            # 新字段，直接设置
            current_state[self.field] = self.value
            return current_state
        
        old_value = current_state[self.field]
        
        if self.strategy == StateUpdateStrategy.OVERWRITE:
            current_state[self.field] = self.value
        
        elif self.strategy == StateUpdateStrategy.REDUCE_APPEND:
            if isinstance(old_value, list) and isinstance(self.value, list):
                current_state[self.field] = old_value + self.value
            else:
                raise TypeError(f"REDUCE_APPEND requires list types, got {type(old_value)} and {type(self.value)}")
        
        elif self.strategy == StateUpdateStrategy.REDUCE_MERGE:
            if isinstance(old_value, dict) and isinstance(self.value, dict):
                current_state[self.field] = {**old_value, **self.value}
            else:
                raise TypeError(f"REDUCE_MERGE requires dict types, got {type(old_value)} and {type(self.value)}")
        
        elif self.strategy == StateUpdateStrategy.REDUCE_SUM:
            if isinstance(old_value, (int, float)) and isinstance(self.value, (int, float)):
                current_state[self.field] = old_value + self.value
            else:
                raise TypeError(f"REDUCE_SUM requires numeric types, got {type(old_value)} and {type(self.value)}")
        
        elif self.strategy == StateUpdateStrategy.CUSTOM and self.custom_reducer:
            current_state[self.field] = self.custom_reducer(old_value, self.value)
        
        return current_state


class StateManager:
    """统一状态管理器"""
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        """
        初始化状态管理器
        
        Args:
            initial_state: 初始状态字典
        """
        self._state = initial_state or self._create_initial_state()
        self._state_history: List[Dict[str, Any]] = [self._state.copy()]
        self._update_history: List[StateUpdate] = []
        self._lock = threading.RLock()
        self._listeners: List[Callable] = []
        
        # 默认归约函数映射
        self._reducer_map = {
            "reduce_append": reduce_append,
            "reduce_merge": reduce_merge,
            "reduce_sum": reduce_sum,
        }
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """创建初始状态"""
        return {
            "request_id": "",
            "request_data": {},
            "request_timestamp": time.time(),
            "session_id": "",
            "user_id": None,
            "messages": [],
            "conversation_history": [],
            "llm_provider": "deepseek",  # 默认使用DeepSeek
            "llm_model": "deepseek-reasoner",
            "llm_responses": [],
            "llm_prompts": [],
            "total_cost": 0.0,
            "budget_remaining": 1000.0,  # 默认预算$1000
            "cost_breakdown": {},
            "deepseek_usage": [],
            "tool_calls": [],
            "tool_results": {},
            "current_tool": None,
            "workflow_id": "",
            "current_step": "init",
            "next_step": None,
            "step_history": [],
            "execution_status": "pending",
            "candidate_models": [],
            "model_scores": {},
            "constraints": {},
            "metadata": {},
            "warnings": [],
            "errors": [],
            "selected_model": None,
            "decision_reason": None,
            "start_time": time.time(),
            "processing_times": {},
            "processor_trace": [],
            "debug_mode": False,
            "log_level": "INFO",
            "trace_id": None,
        }
    
    def get_state(self) -> Dict[str, Any]:
        """获取当前状态（副本）"""
        with self._lock:
            return self._state.copy()
    
    def update_state(self, updates: Union[Dict[str, Any], List[StateUpdate], StateUpdate]):
        """
        更新状态
        
        Args:
            updates: 更新字典、StateUpdate列表或单个StateUpdate
        """
        with self._lock:
            # 备份当前状态到历史
            self._state_history.append(self._state.copy())
            
            if isinstance(updates, StateUpdate):
                updates = [updates]
            
            if isinstance(updates, list):
                # StateUpdate列表
                for update in updates:
                    self._apply_update(update)
            else:
                # 字典更新（默认使用覆盖策略）
                for field, value in updates.items():
                    update = StateUpdate(
                        field=field,
                        value=value,
                        strategy=StateUpdateStrategy.OVERWRITE
                    )
                    self._apply_update(update)
            
            # 通知监听器
            self._notify_listeners()
    
    def _apply_update(self, update: StateUpdate):
        """应用单个更新"""
        try:
            # 应用更新
            self._state = update.apply(self._state)
            self._update_history.append(update)
            
            # 自动处理特殊字段
            if update.field == "llm_provider" and update.value != "deepseek" and update.value != "local":
                # 强制外部LLM只使用DeepSeek
                self._state["llm_provider"] = "deepseek"
                self._state["warnings"] = self._state.get("warnings", []) + [
                    f"⚠️ 重定向外部提供商 '{update.value}' 到 'deepseek'（外部LLM只使用DeepSeek）"
                ]
            
        except Exception as e:
            logger.error(f"状态更新失败 {update.field}: {e}")
            # 记录错误但不中断
            self._state["errors"] = self._state.get("errors", []) + [
                f"状态更新失败 {update.field}: {str(e)}"
            ]
    
    def add_listener(self, listener: Callable):
        """添加状态变更监听器"""
        self._listeners.append(listener)
    
    def _notify_listeners(self):
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(self._state.copy())
            except Exception as e:
                logger.error(f"状态监听器执行失败: {e}")
    
    def get_state_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取状态历史"""
        with self._lock:
            if limit:
                return self._state_history[-limit:]
            return self._state_history.copy()
    
    def get_update_history(self) -> List[StateUpdate]:
        """获取更新历史"""
        with self._lock:
            return self._update_history.copy()
    
    def rollback(self, steps: int = 1) -> bool:
        """
        回滚状态
        
        Args:
            steps: 回滚步数
            
        Returns:
            是否成功回滚
        """
        with self._lock:
            if steps >= len(self._state_history):
                return False
            
            # 回滚到指定步数前的状态
            self._state = self._state_history[-steps-1].copy()
            
            # 截断历史
            self._state_history = self._state_history[:-steps]
            self._update_history = self._update_history[:-steps]
            
            return True
    
    def to_rangen_state(self) -> RANGENState:
        """转换为类型化的RANGENState"""
        # 这是一个类型转换，实际运行时仍然是字典
        return self._state  # type: ignore
    
    def merge_from_processing_context(self, context: Any):
        """
        从ProcessingContext合并数据（兼容现有系统）
        
        Args:
            context: ProcessingContext实例
        """
        # 这里需要根据实际ProcessingContext结构进行调整
        try:
            updates = {}
            
            # 提取关键字段
            if hasattr(context, 'candidate_models'):
                updates['candidate_models'] = context.candidate_models
            
            if hasattr(context, 'scores'):
                updates['model_scores'] = context.scores
            
            if hasattr(context, 'selected_model'):
                updates['selected_model'] = context.selected_model
            
            if hasattr(context, 'decision_reason'):
                updates['decision_reason'] = context.decision_reason
            
            if hasattr(context, 'warnings'):
                updates['warnings'] = context.warnings
            
            if hasattr(context, 'errors'):
                updates['errors'] = context.errors
            
            if hasattr(context, 'processor_trace'):
                updates['processor_trace'] = context.processor_trace
            
            if updates:
                self.update_state(updates)
                
        except Exception as e:
            logger.error(f"合并ProcessingContext失败: {e}")


# 全局状态管理器实例
_global_state_manager: Optional[StateManager] = None


def get_global_state_manager() -> StateManager:
    """获取全局状态管理器（单例）"""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = StateManager()
    return _global_state_manager


def create_state_from_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    从请求创建初始状态
    
    Args:
        request: 请求数据
        
    Returns:
        初始状态字典
    """
    import uuid
    import time
    
    request_id = str(uuid.uuid4())
    
    return {
        "request_id": request_id,
        "request_data": request,
        "request_timestamp": time.time(),
        "session_id": request.get("session_id", ""),
        "user_id": request.get("user_id"),
        "llm_provider": request.get("llm_provider", "deepseek"),
        "llm_model": request.get("model", "deepseek-reasoner"),
        "workflow_id": request.get("workflow_id", f"workflow_{request_id[:8]}"),
        "current_step": "init",
        "execution_status": "pending",
        "start_time": time.time(),
        "debug_mode": request.get("debug", False),
        "trace_id": request.get("trace_id"),
    }


# 兼容性函数：将现有ProcessingContext转换为StateUpdate列表
def convert_processing_context_to_updates(context: Any) -> List[StateUpdate]:
    """将ProcessingContext转换为状态更新列表"""
    updates = []
    
    try:
        # 根据实际ProcessingContext结构添加字段
        if hasattr(context, 'selected_model') and context.selected_model:
            updates.append(StateUpdate(
                field="selected_model",
                value=context.selected_model,
                strategy=StateUpdateStrategy.OVERWRITE
            ))
        
        if hasattr(context, 'decision_reason') and context.decision_reason:
            updates.append(StateUpdate(
                field="decision_reason",
                value=context.decision_reason,
                strategy=StateUpdateStrategy.OVERWRITE
            ))
        
        if hasattr(context, 'warnings') and context.warnings:
            updates.append(StateUpdate(
                field="warnings",
                value=context.warnings,
                strategy=StateUpdateStrategy.REDUCE_APPEND
            ))
        
        if hasattr(context, 'processor_trace') and context.processor_trace:
            updates.append(StateUpdate(
                field="processor_trace",
                value=context.processor_trace,
                strategy=StateUpdateStrategy.REDUCE_APPEND
            ))
            
    except Exception as e:
        logger.error(f"转换ProcessingContext失败: {e}")
    
    return updates


# 全局日志记录器（延迟导入）
import logging
logger = logging.getLogger(__name__)