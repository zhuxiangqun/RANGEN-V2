#!/usr/bin/env python3
"""
Hook Points System - 7拦截点系统
基于OpenClaw架构的Agent循环拦截机制

7个拦截点:
1. before_reasoning - 思考前
2. after_reasoning - 思考后
3. before_act - 行动前
4. after_act - 行动后
5. before_observe - 观察前
6. after_observe - 观察后
7. before_exit - 退出前
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Hook类型枚举 - 7个拦截点"""
    
    # Agent循环核心拦截点
    BEFORE_REASONING = "before_reasoning"    # 思考前
    AFTER_REASONING = "after_reasoning"      # 思考后
    
    BEFORE_ACT = "before_act"                # 行动前
    AFTER_ACT = "after_act"                  # 行动后
    
    BEFORE_OBSERVE = "before_observe"        # 观察前
    AFTER_OBSERVE = "after_observe"          # 观察后
    
    BEFORE_EXIT = "before_exit"              # 退出前
    
    # 扩展拦截点
    ON_ERROR = "on_error"                    # 错误发生时
    ON_TIMEOUT = "on_timeout"                # 超时时
    ON_TOOL_CALL = "on_tool_call"            # 工具调用时


@dataclass
class HookContext:
    """Hook上下文 - 传递拦截点的上下文信息"""
    
    # 基础信息
    hook_type: HookType
    agent_id: str
    session_id: Optional[str] = None
    
    # 任务信息
    query: str = ""
    iteration: int = 0
    
    # 思考链
    thoughts: List[str] = field(default_factory=list)
    current_thought: str = ""
    
    # 行动链
    actions: List[Dict[str, Any]] = field(default_factory=list)
    current_action: Optional[Dict[str, Any]] = None
    
    # 观察链
    observations: List[Dict[str, Any]] = field(default_factory=list)
    current_observation: Optional[Dict[str, Any]] = None
    
    # 工具相关
    tool_name: str = ""
    tool_params: Dict[str, Any] = field(default_factory=dict)
    tool_result: Any = None
    
    # 状态
    task_complete: bool = False
    should_continue: bool = True
    should_skip_action: bool = False
    modified_action: Optional[Dict[str, Any]] = None
    modified_observation: Optional[Dict[str, Any]] = None
    modified_thought: Optional[str] = None
    
    # 错误信息
    error: Optional[str] = None
    error_count: int = 0
    
    # 性能监控
    start_time: float = field(default_factory=time.time)
    hook_execution_time: float = 0.0
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


# 类型定义
HookHandler = Callable[[HookContext], asyncio.coroutines]
HookAsyncHandler = Callable[[HookContext], Any]
T = TypeVar('T')


class HookResult:
    """Hook执行结果"""
    
    def __init__(
        self,
        success: bool = True,
        modified_context: Optional[HookContext] = None,
        error: Optional[str] = None,
        should_continue: bool = True,
        should_skip_action: bool = False,
        custom_data: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.modified_context = modified_context
        self.error = error
        self.should_continue = should_continue
        self.should_skip_action = should_skip_action
        self.custom_data = custom_data or {}
    
    @classmethod
    def default(cls) -> 'HookResult':
        """默认结果 - 不修改任何内容"""
        return cls(success=True)
    
    @classmethod
    def stop(cls, reason: str = "Hook requested stop") -> 'HookResult':
        """停止结果 - 停止Agent循环"""
        return cls(success=True, should_continue=False, custom_data={"reason": reason})
    
    @classmethod
    def skip_action(cls) -> 'HookResult':
        """跳过行动 - 跳过当前行动"""
        return cls(success=True, should_skip_action=True)
    
    @classmethod
    def error_result(cls, error: str) -> 'HookResult':
        """错误结果"""
        return cls(success=False, error=error, should_continue=False)


class BaseHook(ABC):
    """Hook基类 - 所有Hook的抽象基类"""
    
    def __init__(self, name: str, hook_type: HookType, priority: int = 0):
        """
        初始化Hook
        
        Args:
            name: Hook名称
            hook_type: Hook类型
            priority: 优先级（数字越大越先执行）
        """
        self.name = name
        self.hook_type = hook_type
        self.priority = priority
        self.enabled = True
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    async def execute(self, context: HookContext) -> HookResult:
        """
        执行Hook逻辑
        
        Args:
            context: Hook上下文
            
        Returns:
            HookResult: 执行结果
        """
        pass
    
    def _update_metrics(self, execution_time: float):
        """更新执行指标"""
        self.execution_count += 1
        self.total_execution_time += execution_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取Hook指标"""
        avg_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 else 0
        )
        return {
            "name": self.name,
            "hook_type": self.hook_type.value,
            "priority": self.priority,
            "enabled": self.enabled,
            "execution_count": self.execution_count,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": avg_time
        }


class LoggingHook(BaseHook):
    """日志Hook - 记录每个拦截点的详细信息"""
    
    def __init__(self, log_level: int = logging.INFO):
        super().__init__("logging_hook", HookType.BEFORE_REASONING, priority=-100)
        self.log_level = log_level
    
    async def execute(self, context: HookContext) -> HookResult:
        """执行日志记录"""
        # 根据hook类型生成日志
        hook_type = context.hook_type
        
        if hook_type == HookType.BEFORE_REASONING:
            self.logger.log(
                self.log_level,
                f"[{context.agent_id}] 思考开始 | Query: {context.query[:50]}... | Iteration: {context.iteration}"
            )
        elif hook_type == HookType.AFTER_REASONING:
            self.logger.log(
                self.log_level,
                f"[{context.agent_id}] 思考完成 | Thought: {context.current_thought[:50]}..."
            )
        elif hook_type == HookType.BEFORE_ACT:
            self.logger.log(
                self.log_level,
                f"[{context.agent_id}] 行动开始 | Tool: {context.tool_name} | Params: {context.tool_params}"
            )
        elif hook_type == HookType.AFTER_ACT:
            success = context.current_observation.get('success', False) if context.current_observation else False
            self.logger.log(
                self.log_level,
                f"[{context.agent_id}] 行动完成 | Success: {success}"
            )
        elif hook_type == HookType.BEFORE_EXIT:
            self.logger.log(
                self.log_level,
                f"[{context.agent_id}] 退出 | Iterations: {context.iteration} | Thoughts: {len(context.thoughts)}"
            )
        
        return HookResult.default()


class ValidationHook(BaseHook):
    """验证Hook - 验证行动和观察结果"""
    
    def __init__(self, max_iterations: int = 10, max_errors: int = 3):
        super().__init__("validation_hook", HookType.AFTER_ACT, priority=50)
        self.max_iterations = max_iterations
        self.max_errors = max_errors
    
    async def execute(self, context: HookContext) -> HookResult:
        """执行验证"""
        # 检查迭代次数
        if context.iteration >= self.max_iterations:
            self.logger.warning(f"达到最大迭代次数: {self.max_iterations}")
            return HookResult.stop("Max iterations reached")
        
        # 检查错误次数
        if context.error_count >= self.max_errors:
            self.logger.warning(f"达到最大错误次数: {self.max_errors}")
            return HookResult.stop("Max errors reached")
        
        # 检查行动结果
        if context.current_observation:
            if not context.current_observation.get('success', True):
                self.logger.warning(f"行动失败: {context.current_observation.get('error')}")
        
        return HookResult.default()


class ContextCompressionHook(BaseHook):
    """上下文压缩Hook - 防止token溢出"""
    
    def __init__(
        self,
        max_thoughts: int = 20,
        max_observations: int = 20,
        compress_threshold: float = 0.8
    ):
        super().__init__("context_compression_hook", HookType.AFTER_OBSERVE, priority=30)
        self.max_thoughts = max_thoughts
        self.max_observations = max_observations
        self.compress_threshold = compress_threshold
    
    async def execute(self, context: HookContext) -> HookResult:
        """执行上下文压缩"""
        # 压缩思考
        if len(context.thoughts) > self.max_thoughts:
            # 保留最近的思考和关键思考
            context.thoughts = context.thoughts[-self.max_thoughts:]
            self.logger.info(f"压缩思考历史: {len(context.thoughts)}")
        
        # 压缩观察
        if len(context.observations) > self.max_observations:
            # 保留成功的观察
            successful_observations = [
                obs for obs in context.observations 
                if obs.get('success', False)
            ]
            context.observations = successful_observations[-self.max_observations:]
            self.logger.info(f"压缩观察历史: {len(context.observations)}")
        
        return HookResult.default()


class ToolPolicyHook(BaseHook):
    """工具策略Hook - 工具执行审批机制"""
    
    def __init__(self, policy_config: Optional[Dict[str, Any]] = None):
        super().__init__("tool_policy_hook", HookType.BEFORE_ACT, priority=100)
        self.policy_config = policy_config or {}
        self.approved_tools = self.policy_config.get("approved_tools", [])
        self.blocked_tools = self.policy_config.get("blocked_tools", [])
        self.require_approval = self.policy_config.get("require_approval", False)
        self.approval_queue: Dict[str, bool] = {}
    
    async def execute(self, context: HookContext) -> HookResult:
        """执行工具策略检查"""
        tool_name = context.tool_name
        
        # 检查是否被阻止
        if tool_name in self.blocked_tools:
            self.logger.warning(f"工具被阻止: {tool_name}")
            return HookResult.skip_action()
        
        # 检查是否需要审批
        if self.require_approval and tool_name not in self.approved_tools:
            # 模拟审批流程（实际应该调用UI或API）
            if tool_name not in self.approval_queue:
                self.logger.info(f"工具需要审批: {tool_name}")
                # 自动批准白名单外的工具（简化版本）
                self.approval_queue[tool_name] = True
            
            if not self.approval_queue.get(tool_name, False):
                return HookResult.skip_action()
        
        return HookResult.default()


class MetricsHook(BaseHook):
    """指标Hook - 收集执行指标"""
    
    def __init__(self):
        super().__init__("metrics_hook", HookType.BEFORE_EXIT, priority=-50)
        self.metrics: List[Dict[str, Any]] = []
    
    async def execute(self, context: HookContext) -> HookResult:
        """收集指标"""
        execution_time = time.time() - context.start_time
        
        metric = {
            "agent_id": context.agent_id,
            "session_id": context.session_id,
            "query": context.query[:100],
            "iterations": context.iteration,
            "total_thoughts": len(context.thoughts),
            "total_actions": len(context.actions),
            "total_observations": len(context.observations),
            "execution_time": execution_time,
            "task_complete": context.task_complete,
            "error_count": context.error_count,
            "timestamp": context.timestamp.isoformat()
        }
        
        self.metrics.append(metric)
        
        # 保留最近1000条指标
        if len(self.metrics) > 1000:
            self.metrics = self.metrics[-1000:]
        
        return HookResult.default()
    
    def get_metrics(self) -> List[Dict[str, Any]]:
        """获取收集的指标"""
        return self.metrics


class HookManager:
    """Hook管理器 - 管理所有Hook的注册和执行"""
    
    def __init__(self):
        self._hooks: Dict[HookType, List[BaseHook]] = {
            hook_type: [] for hook_type in HookType
        }
        self._global_hooks: List[BaseHook] = []
        self.logger = logging.getLogger(__name__)
    
    def register_hook(self, hook: BaseHook, hook_types: Optional[List[HookType]] = None):
        """
        注册Hook
        
        Args:
            hook: Hook实例
            hook_types: 要注册的Hook类型列表，如果为None则使用hook.hook_type
        """
        if hook_types is None:
            hook_types = [hook.hook_type]
        
        for hook_type in hook_types:
            if hook_type not in self._hooks:
                self._hooks[hook_type] = []
            self._hooks[hook_type].append(hook)
        
        self.logger.info(f"注册Hook: {hook.name} -> {[t.value for t in hook_types]}")
    
    def register_global_hook(self, hook: BaseHook):
        """注册全局Hook（所有类型都执行）"""
        self._global_hooks.append(hook)
        self.logger.info(f"注册全局Hook: {hook.name}")
    
    def unregister_hook(self, name: str):
        """注销Hook"""
        # 从类型特定Hook中移除
        for hook_type, hooks in self._hooks.items():
            self._hooks[hook_type] = [h for h in hooks if h.name != name]
        
        # 从全局Hook中移除
        self._global_hooks = [h for h in self._global_hooks if h.name != name]
        self.logger.info(f"注销Hook: {name}")
    
    def enable_hook(self, name: str):
        """启用Hook"""
        self._find_hook(name).enabled = True
    
    def disable_hook(self, name: str):
        """禁用Hook"""
        self._find_hook(name).enabled = False
    
    def _find_hook(self, name: str) -> Optional[BaseHook]:
        """查找Hook"""
        for hooks in self._hooks.values():
            for hook in hooks:
                if hook.name == name:
                    return hook
        for hook in self._global_hooks:
            if hook.name == name:
                return hook
        return None
    
    async def execute_hooks(
        self,
        context: HookContext,
        hook_types: List[HookType]
    ) -> HookContext:
        """
        执行指定类型的Hook
        
        Args:
            context: Hook上下文
            hook_types: 要执行的Hook类型列表
            
        Returns:
            更新后的HookContext
        """
        # 收集所有要执行的Hook
        hooks_to_execute: List[BaseHook] = []
        
        for hook_type in hook_types:
            # 添加类型特定的Hook
            if hook_type in self._hooks:
                hooks_to_execute.extend(self._hooks[hook_type])
        
        # 添加全局Hook
        hooks_to_execute.extend(self._global_hooks)
        
        # 按优先级排序
        hooks_to_execute.sort(key=lambda h: h.priority, reverse=True)
        
        # 执行Hook
        for hook in hooks_to_execute:
            if not hook.enabled:
                continue
            
            try:
                start_time = time.time()
                result = await hook.execute(context)
                execution_time = time.time() - start_time
                hook._update_metrics(execution_time)
                
                # 处理Hook结果
                if not result.success:
                    self.logger.error(f"Hook执行失败: {hook.name}, Error: {result.error}")
                    context.error = result.error
                    context.should_continue = False
                    break
                
                if not result.should_continue:
                    self.logger.info(f"Hook请求停止: {hook.name}, Reason: {result.custom_data.get('reason')}")
                    context.should_continue = False
                    break
                
                if result.should_skip_action:
                    context.should_skip_action = True
                
                # 应用修改的上下文
                if result.modified_context:
                    context = result.modified_context
                
            except Exception as e:
                self.logger.error(f"Hook执行异常: {hook.name}, Error: {e}", exc_info=True)
                context.error = str(e)
        
        context.hook_execution_time = time.time() - context.start_time
        return context
    
    def get_hooks_info(self) -> Dict[str, Any]:
        """获取所有Hook的信息"""
        info = {
            "hooks_by_type": {},
            "global_hooks": [],
            "total_hooks": 0
        }
        
        for hook_type, hooks in self._hooks.items():
            if hooks:
                info["hooks_by_type"][hook_type.value] = [
                    h.get_metrics() for h in hooks
                ]
                info["total_hooks"] += len(hooks)
        
        info["global_hooks"] = [h.get_metrics() for h in self._global_hooks]
        info["total_hooks"] += len(self._global_hooks)
        
        return info


# 全局Hook管理器实例
_hook_manager: Optional[HookManager] = None


def get_hook_manager() -> HookManager:
    """获取全局Hook管理器"""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
        # 注册默认Hook
        _register_default_hooks()
    return _hook_manager


def _register_default_hooks():
    """注册默认Hook"""
    global _hook_manager
    if _hook_manager is None:
        return
    
    # 注册日志Hook
    logging_hook = LoggingHook()
    _hook_manager.register_hook(logging_hook, [
        HookType.BEFORE_REASONING,
        HookType.AFTER_REASONING,
        HookType.BEFORE_ACT,
        HookType.AFTER_ACT,
        HookType.BEFORE_EXIT
    ])
    
    # 注册验证Hook
    validation_hook = ValidationHook()
    _hook_manager.register_hook(validation_hook, [
        HookType.AFTER_ACT,
        HookType.BEFORE_EXIT
    ])
    
    # 注册上下文压缩Hook
    compression_hook = ContextCompressionHook()
    _hook_manager.register_hook(compression_hook, [
        HookType.AFTER_OBSERVE
    ])
    
    # 注册指标Hook
    metrics_hook = MetricsHook()
    _hook_manager.register_hook(metrics_hook, [
        HookType.BEFORE_EXIT
    ])


def reset_hook_manager():
    """重置Hook管理器"""
    global _hook_manager
    _hook_manager = None


# 便捷函数：创建自定义Hook
def create_hook(
    name: str,
    hook_type: HookType,
    priority: int = 0
) -> Callable[[Callable], type]:
    """
    装饰器：创建自定义Hook
    
    Usage:
        @create_hook("my_custom_hook", HookType.BEFORE_REASONING, priority=10)
        class MyCustomHook(BaseHook):
            async def execute(self, context: HookContext) -> HookResult:
                # 自定义逻辑
                return HookResult.default()
    """
    def decorator(cls: type) -> type:
        # 创建类实例
        return cls(name, hook_type, priority)
    return decorator


# 装饰器版本：用于同步函数
def hook_wrapper(hook_type: HookType):
    """
    装饰器：将函数转换为Hook
    
    Usage:
        @hook_wrapper(HookType.BEFORE_REASONING)
        async def my_hook(context: HookContext) -> HookResult:
            print("Before reasoning!")
            return HookResult.default()
    """
    def decorator(func: HookAsyncHandler) -> BaseHook:
        class FunctionHook(BaseHook):
            def __init__(self):
                super().__init__(func.__name__, hook_type, priority=0)
                self._func = func
            
            async def execute(self, context: HookContext) -> HookResult:
                try:
                    result = await self._func(context)
                    if result is None:
                        return HookResult.default()
                    return result
                except Exception as e:
                    self.logger.error(f"Hook函数执行失败: {e}")
                    return HookResult.error_result(str(e))
        
        return FunctionHook()
    return decorator
