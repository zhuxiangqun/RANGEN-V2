"""
Hook Points System - Agent循环拦截机制

7个拦截点:
1. before_reasoning - 思考前
2. after_reasoning - 思考后
3. before_act - 行动前
4. after_act - 行动后
5. before_observe - 观察前
6. after_observe - 观察后
7. before_exit - 退出前
"""

from .hook_system import (
    HookType,
    HookContext,
    HookResult,
    BaseHook,
    LoggingHook,
    ValidationHook,
    ContextCompressionHook,
    ToolPolicyHook,
    MetricsHook,
    HookManager,
    get_hook_manager,
    reset_hook_manager,
    create_hook,
    hook_wrapper
)

__all__ = [
    "HookType",
    "HookContext",
    "HookResult",
    "BaseHook",
    "LoggingHook",
    "ValidationHook",
    "ContextCompressionHook",
    "ToolPolicyHook",
    "MetricsHook",
    "HookManager",
    "get_hook_manager",
    "reset_hook_manager",
    "create_hook",
    "hook_wrapper"
]
