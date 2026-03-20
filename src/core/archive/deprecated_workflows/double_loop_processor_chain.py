#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双层循环处理器链 - 基于Agentic Coding架构模式改进

设计理念：
1. 外层循环（Session Loop）：会话生命周期管理，负责状态持久化、超时控制、退出判断
2. 内层循环（Execution Loop）：单次LLM调用执行，负责工具调用、Doom loop检测、上下文压缩
3. 信号机制：continue/stop/compact三种信号控制循环流程
4. Doom loop检测：连续3次相同工具调用触发告警，防止资源浪费
5. 状态统一管理：与RANGENState集成，支持状态持久化和回滚

参考架构：OpenCode的双层循环设计
"""

import asyncio
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
import uuid

from src.core.rangen_state import (
    RANGENState,
    StateManager,
    get_global_state_manager,
    create_state_from_request,
    StateUpdate,
    StateUpdateStrategy
)

# 导入现有处理器链（向后兼容）
from src.core.processor_chain import (
    ProcessorChain,
    ProcessingContext,
    BaseProcessor,
    ProcessorResult
)

logger = logging.getLogger(__name__)


class LoopSignal(Enum):
    """循环信号"""
    CONTINUE = "continue"    # 继续下一轮循环
    STOP = "stop"            # 正常停止
    COMPACT = "compact"      # 需要压缩上下文后继续
    ERROR = "error"          # 错误停止


class DoomLoopDetector:
    """死循环检测器"""
    
    def __init__(self, max_repeat_calls: int = 3):
        """
        初始化死循环检测器
        
        Args:
            max_repeat_calls: 最大重复调用次数，超过则触发告警
        """
        self.max_repeat_calls = max_repeat_calls
        self.tool_call_history: List[str] = []  # 工具调用历史
        self.consecutive_identical_calls = 0     # 连续相同调用次数
        self.last_tool: Optional[str] = None
        
    def record_tool_call(self, tool_name: str) -> Optional[str]:
        """
        记录工具调用，返回警告信息（如果检测到死循环）
        
        Args:
            tool_name: 工具名称
            
        Returns:
            警告信息或None
        """
        self.tool_call_history.append(tool_name)
        
        if tool_name == self.last_tool:
            self.consecutive_identical_calls += 1
        else:
            self.consecutive_identical_calls = 1
            self.last_tool = tool_name
        
        if self.consecutive_identical_calls >= self.max_repeat_calls:
            warning = f"⚠️ Doom loop检测：连续 {self.consecutive_identical_calls} 次调用相同工具 '{tool_name}'"
            logger.warning(warning)
            return warning
        
        return None
    
    def reset(self):
        """重置检测器状态"""
        self.tool_call_history = []
        self.consecutive_identical_calls = 0
        self.last_tool = None


@dataclass
class SessionConfig:
    """会话配置"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    max_iterations: int = 20                     # 最大迭代次数
    timeout_seconds: int = 300                   # 超时时间（秒）
    enable_doom_loop_detection: bool = True      # 启用死循环检测
    enable_context_compaction: bool = True       # 启用上下文压缩
    context_compaction_threshold: int = 10       # 上下文压缩阈值（消息数量）
    state_persistence_interval: int = 5          # 状态持久化间隔（迭代次数）
    
    # DeepSeek成本控制
    budget_limit: float = 1000.0                 # 预算限制（美元）
    cost_warning_threshold: float = 0.8          # 成本警告阈值（预算的80%）


@dataclass
class SessionState:
    """会话状态"""
    config: SessionConfig
    start_time: float = field(default_factory=time.time)
    iteration_count: int = 0
    last_state_persist_iteration: int = 0
    doom_loop_detector: DoomLoopDetector = field(default_factory=DoomLoopDetector)
    context_messages_count: int = 0
    signals: List[LoopSignal] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def elapsed_time(self) -> float:
        """已用时间（秒）"""
        return time.time() - self.start_time
    
    @property
    def should_timeout(self) -> bool:
        """是否应该超时"""
        return self.elapsed_time > self.config.timeout_seconds
    
    @property
    def should_persist_state(self) -> bool:
        """是否应该持久化状态"""
        return (self.iteration_count - self.last_state_persist_iteration) >= \
               self.config.state_persistence_interval
    
    def record_iteration(self):
        """记录迭代"""
        self.iteration_count += 1
    
    def record_signal(self, signal: LoopSignal):
        """记录信号"""
        self.signals.append(signal)
    
    def record_error(self, error: str):
        """记录错误"""
        self.errors.append(error)
    
    def should_compact_context(self, current_message_count: int) -> bool:
        """判断是否需要压缩上下文"""
        if not self.config.enable_context_compaction:
            return False
        return current_message_count >= self.config.context_compaction_threshold


class InnerExecutionLoop:
    """内层循环：单次LLM调用执行"""
    
    def __init__(self, processor_chain: ProcessorChain, state_manager: StateManager):
        """
        初始化内层循环
        
        Args:
            processor_chain: 处理器链
            state_manager: 状态管理器
        """
        self.processor_chain = processor_chain
        self.state_manager = state_manager
        
    async def execute_step(self, session_state: SessionState) -> Tuple[LoopSignal, Dict[str, Any]]:
        """
        执行单步
        
        Args:
            session_state: 会话状态
            
        Returns:
            (信号, 执行结果)
        """
        try:
            # 1. 从状态管理器获取当前状态
            current_state = self.state_manager.get_state()
            
            # 2. 检查预算限制（DeepSeek成本控制）
            budget_check = self._check_budget(current_state)
            if not budget_check["allowed"]:
                logger.warning(f"预算超支：{budget_check['message']}")
                return LoopSignal.STOP, {"error": budget_check["message"]}
            
            # 3. 创建ProcessingContext（兼容现有系统）
            processing_context = self._create_processing_context(current_state)
            
            # 4. 执行处理器链
            result_context = await self.processor_chain.execute(processing_context)
            
            # 5. 记录工具调用（用于Doom loop检测）
            if session_state.config.enable_doom_loop_detection:
                tool_name = self._extract_tool_from_context(result_context)
                if tool_name:
                    warning = session_state.doom_loop_detector.record_tool_call(tool_name)
                    if warning:
                        # 将警告添加到状态
                        self.state_manager.update_state({
                            "warnings": [warning]
                        })
            
            # 6. 更新状态管理器
            self._update_state_from_context(result_context)
            
            # 7. 判断是否需要压缩上下文
            if session_state.should_compact_context(session_state.context_messages_count):
                logger.info("上下文达到压缩阈值，触发压缩")
                return LoopSignal.COMPACT, {"action": "context_compaction"}
            
            # 8. 判断是否完成任务
            if self._is_task_complete(result_context):
                return LoopSignal.STOP, {"status": "completed", "result": result_context.to_dict()}
            
            # 默认继续
            return LoopSignal.CONTINUE, {"status": "in_progress", "iteration": session_state.iteration_count}
            
        except Exception as e:
            logger.error(f"内层循环执行失败: {e}")
            session_state.record_error(str(e))
            return LoopSignal.ERROR, {"error": str(e)}
    
    def _check_budget(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        检查预算限制
        
        Args:
            state: 当前状态
            
        Returns:
            检查结果
        """
        total_cost = state.get("total_cost", 0.0)
        budget_limit = state.get("budget_remaining", 1000.0)
        
        if total_cost >= budget_limit:
            return {
                "allowed": False,
                "message": f"总成本 ${total_cost:.2f} 超过预算限制 ${budget_limit:.2f}"
            }
        
        # 检查是否接近预算限制（警告）
        warning_threshold = budget_limit * 0.8
        if total_cost >= warning_threshold:
            logger.warning(f"成本接近预算限制：${total_cost:.2f} / ${budget_limit:.2f}")
        
        return {"allowed": True, "message": "预算检查通过"}
    
    def _create_processing_context(self, state: Dict[str, Any]) -> ProcessingContext:
        """从状态创建ProcessingContext"""
        # 这里需要根据实际状态结构调整
        context = ProcessingContext(
            request=state.get("request_data", {}),
            available_models=state.get("candidate_models", [])
        )
        
        # 复制其他字段
        if "selected_model" in state:
            context.selected_model = state["selected_model"]
        if "decision_reason" in state:
            context.decision_reason = state["decision_reason"]
        if "warnings" in state:
            context.warnings = state["warnings"]
        if "errors" in state:
            context.errors = state["errors"]
        
        return context
    
    def _extract_tool_from_context(self, context: ProcessingContext) -> Optional[str]:
        """从上下文中提取工具名称"""
        # 这里需要根据实际上下文结构实现
        # 例如，可以从metadata或特定字段中提取
        if hasattr(context, 'metadata') and context.metadata:
            return context.metadata.get("last_tool")
        return None
    
    def _update_state_from_context(self, context: ProcessingContext):
        """将ProcessingContext更新回状态管理器"""
        updates = {}
        
        if hasattr(context, 'selected_model') and context.selected_model:
            updates["selected_model"] = context.selected_model
        
        if hasattr(context, 'decision_reason') and context.decision_reason:
            updates["decision_reason"] = context.decision_reason
        
        if hasattr(context, 'warnings') and context.warnings:
            updates["warnings"] = context.warnings
        
        if hasattr(context, 'errors') and context.errors:
            updates["errors"] = context.errors
        
        if hasattr(context, 'processor_trace') and context.processor_trace:
            updates["processor_trace"] = context.processor_trace
        
        if updates:
            self.state_manager.update_state(updates)
    
    def _is_task_complete(self, context: ProcessingContext) -> bool:
        """判断任务是否完成"""
        return getattr(context, 'final_decision', False)


class OuterSessionLoop:
    """外层循环：会话生命周期管理"""
    
    def __init__(self, config: Optional[SessionConfig] = None):
        """
        初始化外层循环
        
        Args:
            config: 会话配置
        """
        self.config = config or SessionConfig()
        self.session_state = SessionState(self.config)
        self.state_manager = get_global_state_manager()
        
    async def run_session(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行会话
        
        Args:
            request: 请求数据
            
        Returns:
            会话结果
        """
        logger.info(f"开始会话 {self.config.session_id}")
        
        try:
            # 1. 初始化状态
            initial_state = create_state_from_request(request)
            self.state_manager.update_state(initial_state)
            
            # 2. 创建处理器链（这里可以动态配置）
            processor_chain = self._create_processor_chain()
            
            # 3. 创建内层循环
            inner_loop = InnerExecutionLoop(processor_chain, self.state_manager)
            
            # 4. 主循环
            while not self._should_exit_session():
                # 记录迭代
                self.session_state.record_iteration()
                
                # 执行内层循环
                signal, result = await inner_loop.execute_step(self.session_state)
                self.session_state.record_signal(signal)
                
                # 处理信号
                if signal == LoopSignal.STOP:
                    logger.info("收到停止信号，结束会话")
                    return self._build_session_result(True, result)
                
                elif signal == LoopSignal.COMPACT:
                    logger.info("收到压缩信号，执行上下文压缩")
                    await self._compact_context()
                    continue
                
                elif signal == LoopSignal.ERROR:
                    logger.error("收到错误信号")
                    if not self._handle_error(result.get("error")):
                        return self._build_session_result(False, result)
                    continue
                
                # LoopSignal.CONTINUE 继续循环
                
                # 检查是否需要持久化状态
                if self.session_state.should_persist_state:
                    await self._persist_state()
                    self.session_state.last_state_persist_iteration = self.session_state.iteration_count
            
            # 5. 超时或其他退出条件
            return self._build_session_result(False, {"reason": "session_timeout"})
            
        except Exception as e:
            logger.error(f"会话执行失败: {e}")
            return self._build_session_result(False, {"error": str(e)})
    
    def _should_exit_session(self) -> bool:
        """判断是否应该退出会话"""
        # 超时检查
        if self.session_state.should_timeout:
            logger.warning(f"会话超时：{self.session_state.elapsed_time:.1f}s")
            return True
        
        # 最大迭代次数检查
        if self.session_state.iteration_count >= self.config.max_iterations:
            logger.warning(f"达到最大迭代次数：{self.session_state.iteration_count}")
            return True
        
        # 错误数量检查
        if len(self.session_state.errors) > 10:
            logger.warning(f"错误过多：{len(self.session_state.errors)}")
            return True
        
        return False
    
    def _create_processor_chain(self) -> ProcessorChain:
        """创建处理器链"""
        # 这里可以根据配置动态创建处理器链
        chain = ProcessorChain(f"session_{self.config.session_id[:8]}")
        
        # 可以添加默认处理器或从配置加载
        # 例如：chain.add_processor(SomeProcessor())
        
        return chain
    
    async def _compact_context(self):
        """压缩上下文"""
        # 这里实现上下文压缩逻辑
        # 例如：使用LLM总结历史消息，减少token数量
        logger.info("执行上下文压缩")
        
        # 更新状态中的消息计数
        self.state_manager.update_state({
            "context_messages_count": 0
        })
        self.session_state.context_messages_count = 0
    
    async def _persist_state(self):
        """持久化状态"""
        # 这里可以将状态保存到数据库或文件系统
        logger.debug(f"持久化状态（迭代 {self.session_state.iteration_count}）")
        
        # 使用状态管理器的现有功能
        # 可以添加额外的持久化逻辑
    
    def _handle_error(self, error: Optional[str]) -> bool:
        """处理错误，返回是否继续"""
        if not error:
            return True
        
        self.session_state.record_error(error)
        
        # 根据错误类型决定是否继续
        # 可恢复错误：返回True，不可恢复错误：返回False
        recoverable_errors = ["timeout", "connection", "rate limit"]
        
        if any(err_keyword in error.lower() for err_keyword in recoverable_errors):
            logger.warning(f"可恢复错误：{error}")
            return True
        else:
            logger.error(f"不可恢复错误：{error}")
            return False
    
    def _build_session_result(self, success: bool, details: Dict[str, Any]) -> Dict[str, Any]:
        """构建会话结果"""
        return {
            "session_id": self.config.session_id,
            "success": success,
            "iterations": self.session_state.iteration_count,
            "elapsed_time": self.session_state.elapsed_time,
            "signals": [s.value for s in self.session_state.signals],
            "errors": self.session_state.errors,
            "details": details,
            "final_state": self.state_manager.get_state() if success else None
        }


class DoubleLoopProcessorChain:
    """双层循环处理器链（主入口类）"""
    
    def __init__(self, config: Optional[SessionConfig] = None):
        """
        初始化双层循环处理器链
        
        Args:
            config: 会话配置
        """
        self.config = config or SessionConfig()
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理请求（主入口方法）
        
        Args:
            request: 请求数据
            
        Returns:
            处理结果
        """
        # 创建外层循环并运行会话
        outer_loop = OuterSessionLoop(self.config)
        result = await outer_loop.run_session(request)
        
        return result
    
    def register_processor(self, processor: BaseProcessor):
        """注册处理器（向后兼容）"""
        # 这里可以维护一个处理器注册表，供内层循环使用
        logger.info(f"注册处理器：{processor.name}")
        # 实际注册逻辑需要在运行时动态配置处理器链


# 兼容性包装器：将现有ProcessorChain包装为双层循环
def wrap_processor_chain_with_double_loop(
    processor_chain: ProcessorChain,
    config: Optional[SessionConfig] = None
) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    将现有ProcessorChain包装为双层循环处理器
    
    Args:
        processor_chain: 现有的处理器链
        config: 会话配置
        
    Returns:
        异步处理函数
    """
    async def async_wrapper(request: Dict[str, Any]) -> Dict[str, Any]:
        # 创建状态管理器
        state_manager = get_global_state_manager()
        
        # 创建内层循环
        inner_loop = InnerExecutionLoop(processor_chain, state_manager)
        
        # 创建会话状态
        session_config = config or SessionConfig()
        session_state = SessionState(session_config)
        
        # 初始化状态
        initial_state = create_state_from_request(request)
        state_manager.update_state(initial_state)
        
        # 执行单次迭代（简单包装）
        signal, result = await inner_loop.execute_step(session_state)
        
        return {
            "signal": signal.value,
            "result": result,
            "state": state_manager.get_state()
        }
    
    return async_wrapper


# 快速使用示例
async def example_usage():
    """使用示例"""
    # 方式1：直接使用双层循环
    double_loop = DoubleLoopProcessorChain()
    result = await double_loop.process({
        "query": "分析用户需求",
        "user_id": "user123",
        "debug": True
    })
    print(f"结果：{result}")
    
    # 方式2：包装现有处理器链
    from src.core.processor_chain import ProcessorChain
    existing_chain = ProcessorChain("default")
    # 添加处理器...
    
    wrapped = wrap_processor_chain_with_double_loop(existing_chain)
    result = await wrapped({"query": "测试"})
    print(f"包装结果：{result}")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(example_usage())