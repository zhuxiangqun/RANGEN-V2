#!/usr/bin/env python3
"""
Hook-enabled ReAct Agent - 集成Hook系统的ReAct Agent

在ReAct循环的7个拦截点集成Hook:
1. before_reasoning - 思考前
2. after_reasoning - 思考后
3. before_act - 行动前
4. after_act - 行动后
5. before_observe - 观察前
6. after_observe - 观察后
7. before_exit - 退出前

使用场景:
- 调试和日志追踪
- 性能监控
- 埋点数据分析
- 自定义业务逻辑注入

注意: EnhancedExecutionCoordinator 也内置了 Hook 支持，可根据需求选择
"""

import time
"""
Hook-enabled ReAct Agent - 集成Hook系统的ReAct Agent

⚠️ DEPRECATED: 此模块已不再维护。
请使用 src.core.enhanced_execution_coordinator 代替 (已内置 Hook 支持)。

在ReAct循环的7个拦截点集成Hook:
1. before_reasoning - 思考前
2. after_reasoning - 思考后
3. before_act - 行动前
4. after_act - 行动后
5. before_observe - 观察前
6. after_observe - 观察后
7. before_exit - 退出前
"""

import warnings
warnings.warn(
    "HookedReActAgent is deprecated. Use EnhancedExecutionCoordinator instead.",
    DeprecationWarning,
    stacklevel=2
)

import time
"""
Hook-enabled ReAct Agent - 集成Hook系统的ReAct Agent

在ReAct循环的7个拦截点集成Hook:
1. before_reasoning - 思考前
2. after_reasoning - 思考后
3. before_act - 行动前
4. after_act - 行动后
5. before_observe - 观察前
6. after_observe - 观察后
7. before_exit - 退出前
"""

import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .react_agent import ReActAgent
from .hooks import (
    HookType,
    HookContext,
    HookResult,
    get_hook_manager,
    BaseHook,
    LoggingHook,
    ValidationHook,
    ContextCompressionHook,
    ToolPolicyHook,
    MetricsHook
)
from ..core.events import (
    EventType,
    create_event_stream,
    get_event_stream
)

logger = logging.getLogger(__name__)


class HookedReActAgent(ReActAgent):
    """
    集成Hook系统的ReAct Agent
    
    在ReAct循环的各个关键点执行Hook，实现:
    - 日志记录
    - 验证检查
    - 上下文压缩
    - 工具策略审批
    - 指标收集
    - 事件流发布
    """
    
    def __init__(
        self,
        agent_name: str = "HookedReActAgent",
        use_intelligent_config: bool = True,
        enable_hooks: bool = True,
        enable_event_stream: bool = True
    ):
        """
        初始化HookedReActAgent
        
        Args:
            agent_name: Agent名称
            use_intelligent_config: 使用智能配置
            enable_hooks: 启用Hook系统
            enable_event_stream: 启用事件流
        """
        super().__init__(agent_name, use_intelligent_config)
        
        self.enable_hooks = enable_hooks
        self.enable_event_stream = enable_event_stream
        
        # Hook管理器
        self._hook_manager = None
        self._init_hooks()
        
        # 事件流
        self._event_stream = None
        if self.enable_event_stream:
            self._init_event_stream()
        
        # 会话ID
        self._session_id = None
        
        self.module_logger.info(f"✅ HookedReActAgent初始化完成 | Hooks: {enable_hooks} | Events: {enable_event_stream}")
    
    def _init_hooks(self):
        """初始化Hook系统"""
        if not self.enable_hooks:
            return
        
        try:
            self._hook_manager = get_hook_manager()
            
            # 可以在这里注册自定义Hook
            # 示例:
            # custom_hook = MyCustomHook()
            # self._hook_manager.register_hook(custom_hook, [HookType.BEFORE_REASONING])
            
            self.module_logger.info("✅ Hook系统初始化完成")
        except Exception as e:
            self.module_logger.warning(f"⚠️ Hook系统初始化失败: {e}")
            self.enable_hooks = False
    
    def _init_event_stream(self):
        """初始化事件流"""
        if not self.enable_event_stream:
            return
        
        try:
            self._event_stream = create_event_stream()
            self.module_logger.info(f"✅ 事件流初始化完成: {self._event_stream.session_id}")
        except Exception as e:
            self.module_logger.warning(f"⚠️ 事件流初始化失败: {e}")
            self.enable_event_stream = False
        """初始化事件流"""
       ._event_stream = create_event_stream()
            self.module_logger try:
            self.info(f"✅ 事件流初始化完成: {self._event_stream.session_id}")
        except Exception as e:
            self.module_logger.warning(f"⚠️ 事件流初始化失败: {e}")
            self.enable_event_stream = False
    
    def set_session_id(self, session_id: str):
        """设置会话ID"""
        self._session_id = session_id
        if self.enable_event_stream and self._event_stream:
            # 切换到指定会话的事件流
            self._event_stream = get_event_stream(session_id) or create_event_stream(session_id)
    
    async def _emit_event(
        self,
        event_type: EventType,
        content: str = "",
        data: Optional[Dict[str, Any]] = None,
        iteration: int = 0,
        is_final: bool = False
    ):
        """发送事件"""
        if not self.enable_event_stream or not self._event_stream:
            return
        
        try:
            await self._event_stream.emit_simple(
                event_type=event_type,
                content=content,
                data=data or {},
                agent_id=self.agent_id,
                iteration=iteration,
                is_final=is_final
            )
        except Exception as e:
            self.module_logger.warning(f"⚠️ 事件发送失败: {e}")
    
    async def _run_hooks(
        self,
        hook_type: HookType,
        context_data: Dict[str, Any]
    ) -> HookContext:
        """运行Hook"""
        if not self.enable_hooks or not self._hook_manager:
            # 返回默认上下文
            return HookContext(
                hook_type=hook_type,
                agent_id=self.agent_id,
                **context_data
            )
        
        # 创建Hook上下文
        context = HookContext(
            hook_type=hook_type,
            agent_id=self.agent_id,
            session_id=self._session_id,
            **context_data
        )
        
        try:
            # 执行Hook
            context = await self._hook_manager.execute_hooks(context, [hook_type])
        except Exception as e:
            self.module_logger.warning(f"⚠️ Hook执行失败 ({hook_type.value}): {e}")
        
        return context
    
    async def execute(self, context: Dict[str, Any]) -> 'AgentResult':
        """
        执行ReAct循环（集成Hook和事件流）
        
        Args:
            context: 上下文，必须包含'query'字段
            
        Returns:
            AgentResult: 执行结果
        """
        start_time = time.time()
        
        # 提取查询和会话ID
        query = context.get('query', '')
        self._session_id = context.get('session_id', self._session_id)
        
        # 发送开始事件
        await self._emit_event(
            EventType.AGENT_START,
            content=f"Agent开始执行: {query[:50]}...",
            data={"query": query}
        )
        
        # 创建Hook上下文数据
        hook_context_data = {
            "query": query,
            "session_id": self._session_id,
            "iteration": 0
        }
        
        # ===== HOOK: before_reasoning (思考前) =====
        await self._run_hooks(HookType.BEFORE_REASONING, hook_context_data)
        
        # 调用原始execute方法（已修改为包含Hook）
        result = await self._execute_with_hooks(context)
        
        # 发送完成事件
        await self._emit_event(
            EventType.AGENT_COMPLETE,
            content="Agent执行完成",
            iteration=result.metadata.get("react_iterations", 0) if result.metadata else 0,
            is_final=True,
            data={
                "success": result.success,
                "confidence": result.confidence,
                "processing_time": result.processing_time
            }
        )
        
        # ===== HOOK: before_exit (退出前) =====
        await self._run_hooks(
            HookType.BEFORE_EXIT,
            {
                "query": query,
                "session_id": self._session_id,
                "iteration": result.metadata.get("react_iterations", 0) if result.metadata else 0,
                "task_complete": result.success,
                "observations": self.observations,
                "thoughts": self.thoughts,
                "actions": [a.to_dict() for a in self.actions]
            }
        )
        
        return result
    
    async def _execute_with_hooks(self, context: Dict[str, Any]):
        """
        集成Hook的ReAct循环执行
        
        这是原始execute方法的Hook版本
        """
        from .base_agent import AgentResult
        
        start_time = time.time()
        
        try:
            # 提取查询
            query = context.get('query', '')
            if not query:
                return AgentResult(
                    success=False,
                    data=None,
                    error="查询为空",
                    confidence=0.0,
                    processing_time=time.time() - start_time
                )
            
            self.module_logger.info(f"🧠 HookedReAct Agent开始执行: {query[:100]}...")
            
            # 重置状态
            self.observations = []
            self.thoughts = []
            self.actions = []
            
            # 动态调整最大迭代次数
            max_iterations = self._get_dynamic_max_iterations(query)
            
            # ReAct循环
            iteration = 0
            task_complete = False
            error_count = 0
            
            # ===== HOOK: before_reasoning (首次思考前) =====
            await self._run_hooks(
                HookType.BEFORE_REASONING,
                {
                    "query": query,
                    "iteration": iteration,
                    "thoughts": self.thoughts,
                    "observations": self.observations,
                    "actions": [a.to_dict() for a in self.actions]
                }
            )
            
            while iteration < max_iterations and not task_complete:
                self.module_logger.info(f"🔄 ReAct循环迭代 {iteration + 1}/{max_iterations}")
                
                # ===== HOOK: before_reasoning (每次思考前) =====
                hook_ctx = await self._run_hooks(
                    HookType.BEFORE_REASONING,
                    {
                        "query": query,
                        "iteration": iteration,
                        "thoughts": self.thoughts,
                        "observations": self.observations,
                        "actions": [a.to_dict() for a in self.actions]
                    }
                )
                
                # 检查是否跳过思考
                if hook_ctx.should_skip_action:
                    self.module_logger.info("⚠️ Hook请求跳过思考阶段")
                    break
                
                # 思考（Reason）
                thought = await self._think(query, self.observations)
                self.thoughts.append(thought)
                
                # 发送思考事件
                await self._emit_event(
                    EventType.AGENT_THINKING,
                    content=thought,
                    iteration=iteration
                )
                
                # ===== HOOK: after_reasoning (思考后) =====
                await self._run_hooks(
                    HookType.AFTER_REASONING,
                    {
                        "query": query,
                        "current_thought": thought,
                        "iteration": iteration,
                        "thoughts": self.thoughts,
                        "observations": self.observations
                    }
                )
                
                # 判断是否完成
                task_complete = self._is_task_complete(thought, self.observations)
                if task_complete:
                    self.module_logger.info("✅ 任务完成，退出循环")
                    break
                
                # 检查是否已有RAG答案
                has_valid_rag_answer = self._has_valid_rag_answer(self.observations)
                if has_valid_rag_answer:
                    self.module_logger.info("✅ 已检测到有效的RAG答案")
                    task_complete = True
                    break
                
                # 规划行动（Plan Action）
                action = await self._plan_action(thought, query, self.observations)
                
                if not action or not action.tool_name:
                    self.module_logger.warning("⚠️ 无法规划行动，退出循环")
                    break
                
                self.actions.append(action)
                
                # ===== HOOK: before_act (行动前) =====
                await self._run_hooks(
                    HookType.BEFORE_ACT,
                    {
                        "query": query,
                        "current_action": action.to_dict(),
                        "iteration": iteration,
                        "thoughts": self.thoughts,
                        "observations": self.observations
                    }
                )
                
                # 发送行动事件
                await self._emit_event(
                    EventType.AGENT_ACTION,
                    content=f"执行工具: {action.tool_name}",
                    data={"tool_name": action.tool_name, "params": action.params},
                    iteration=iteration
                )
                
                # 行动（Act）
                observation = await self._act(action)
                self.observations.append(observation)
                
                # 发送观察事件
                await self._emit_event(
                    EventType.AGENT_OBSERVATION,
                    content=f"观察结果: {observation.get('success')}",
                    data=observation,
                    iteration=iteration
                )
                
                # ===== HOOK: after_act (行动后) =====
                await self._run_hooks(
                    HookType.AFTER_ACT,
                    {
                        "query": query,
                        "current_action": action.to_dict(),
                        "current_observation": observation,
                        "iteration": iteration,
                        "thoughts": self.thoughts,
                        "observations": self.observations,
                        "error_count": error_count
                    }
                )
                
                # ===== HOOK: after_observe (观察后) =====
                await self._run_hooks(
                    HookType.AFTER_OBSERVE,
                    {
                        "query": query,
                        "current_observation": observation,
                        "iteration": iteration,
                        "thoughts": self.thoughts,
                        "observations": self.observations
                    }
                )
                
                # 错误处理
                if not observation.get('success', True):
                    error_count += 1
                    self.module_logger.warning(f"⚠️ 行动失败，错误计数: {error_count}")
                    
                    if error_count >= self.max_error_retry:
                        self.module_logger.warning(f"🔄 达到最大错误阈值，触发重规划...")
                        self.observations = []
                        self.thoughts = []
                        self.actions = []
                        error_count = 0
                else:
                    if error_count > 0:
                        self.module_logger.info(f"✅ 行动成功，重置错误计数")
                        error_count = 0
                
                iteration += 1
            
            # 生成最终答案
            final_answer = await self._synthesize_answer(query, self.observations, self.thoughts)
            
            processing_time = time.time() - start_time
            
            # 判断成功
            has_successful_observations = any(
                obs.get('success') and obs.get('data') 
                for obs in self.observations
            )
            
            is_fallback_message = final_answer == "抱歉，无法获取足够的信息来回答这个问题。"
            final_answer_lower = final_answer.lower().strip() if final_answer else ""
            is_unable_to_determine = final_answer and final_answer_lower in ["unable to determine", "无法确定", "不确定"]
            
            actual_success = (
                has_successful_observations and 
                not is_fallback_message and 
                not is_unable_to_determine
            )
            
            # 计算置信度
            if actual_success:
                successful_count = sum(1 for obs in self.observations if obs.get('success') and obs.get('data'))
                confidence = min(0.8 + (successful_count - 1) * 0.05, 0.95)
            else:
                confidence = 0.3
            
            # 发送答案事件
            await self._emit_event(
                EventType.AGENT_ANSWER,
                content=final_answer[:500],  # 限制长度
                iteration=iteration,
                data={
                    "confidence": confidence,
                    "success": actual_success
                }
            )
            
            self.module_logger.info(f"✅ HookedReAct Agent执行完成，迭代次数: {iteration}，耗时: {processing_time:.2f}秒")
            
            from .base_agent import AgentResult
            return AgentResult(
                success=actual_success,
                data={
                    "answer": final_answer,
                    "thoughts": self.thoughts,
                    "actions": [a.to_dict() for a in self.actions],
                    "observations": self.observations,
                    "iterations": iteration
                },
                confidence=confidence,
                processing_time=processing_time,
                metadata={
                    "react_iterations": iteration,
                    "tools_used": [a.tool_name for a in self.actions],
                    "task_completed": task_complete
                }
            )
            
        except Exception as e:
            self.module_logger.error(f"❌ HookedReAct Agent执行失败: {e}", exc_info=True)
            
            # 发送错误事件
            await self._emit_event(
                EventType.AGENT_ERROR,
                content=f"执行错误: {str(e)}",
                is_final=True,
                data={"error": str(e)}
            )
            
            from .base_agent import AgentResult
            return AgentResult(
                success=False,
                data=None,
                error=str(e),
                confidence=0.0,
                processing_time=time.time() - start_time
            )


def create_hooked_react_agent(
    agent_name: str = "HookedReActAgent",
    enable_hooks: bool = True,
    enable_event_stream: bool = True
) -> HookedReActAgent:
    """
    创建HookedReActAgent的便捷函数
    
    Args:
        agent_name: Agent名称
        enable_hooks: 启用Hook系统
        enable_event_stream: 启用事件流
        
    Returns:
        HookedReActAgent实例
    """
    return HookedReActAgent(
        agent_name=agent_name,
        enable_hooks=enable_hooks,
        enable_event_stream=enable_event_stream
    )
