#!/usr/bin/env python3
"""
Enhanced Tool Registry with Policy Support
集成工具策略的增强版工具注册表
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field

from .tool_registry import ToolRegistry, get_tool_registry as get_base_registry
from .tool_policy import (
    ToolPolicy,
    ToolPolicyEngine,
    ToolApproval,
    ApprovalStatus,
    RiskLevel,
    get_tool_policy_engine
)

logger = logging.getLogger(__name__)


class PolicyEnabledToolRegistry:
    """
    集成工具策略的工具注册表
    
    新增功能:
    - 工具执行前的策略检查
    - 危险工具参数检测
    - 工具使用审批流程
    - 工具使用审计日志
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # 基础工具注册表
        self._base_registry = get_base_registry()
        
        # 工具策略引擎
        self._policy_engine = get_tool_policy_engine()
        
        # 策略启用状态
        self._policy_enabled = True
        
        # 审批回调
        self._approval_callbacks: List[Callable] = []
        
        # 注册审批回调
        self._register_approval_callback()
        
        logger.info("PolicyEnabledToolRegistry initialized")
    
    def _register_approval_callback(self):
        """注册审批回调"""
        def approval_callback(approval: ToolApproval):
            for cb in self._approval_callbacks:
                try:
                    cb(approval)
                except Exception as e:
                    logger.warning(f"Approval callback error: {e}")
        
        self._policy_engine.register_callback(approval_callback)
    
    # ==================== 原有接口兼容 ====================
    
    @property
    def _tools(self):
        """访问基础注册表的工具"""
        return self._base_registry._tools
    
    def register_tool(self, tool: Any) -> None:
        """注册工具（兼容原有接口）"""
        # 获取工具名称
        tool_name = getattr(tool, 'config', None)
        if tool_name:
            tool_name = tool_name.name
        else:
            tool_name = getattr(tool, 'tool_name', 'unknown')
        
        # 注册到基础注册表
        self._base_registry.register_tool(tool)
        
        # 如果工具需要审批，添加到策略引擎
        if hasattr(tool, 'requires_approval') and tool.requires_approval:
            logger.info(f"Tool {tool_name} requires approval")
        
        logger.info(f"Tool registered with policy: {tool_name}")
    
    def get_tool(self, name: str):
        """获取工具"""
        return self._base_registry.get_tool(name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return self._base_registry.list_tools()
    
    def get_all_tools(self):
        """获取所有工具实例"""
        return self._base_registry.get_all_tools()
    
    # ==================== 策略相关方法 ====================
    
    def is_policy_enabled(self) -> bool:
        """检查策略是否启用"""
        return self._policy_enabled
    
    def enable_policy(self):
        """启用策略"""
        self._policy_enabled = True
        logger.info("Tool policy enabled")
    
    def disable_policy(self):
        """禁用策略"""
        self._policy_enabled = False
        logger.info("Tool policy disabled")
    
    def set_policy(self, policy: ToolPolicy):
        """设置工具策略"""
        self._policy_engine.update_policy(policy)
        logger.info("Tool policy updated")
    
    def get_policy(self) -> ToolPolicy:
        """获取当前策略"""
        return self._policy_engine.policy
    
    async def check_tool_execution(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolApproval:
        """
        检查工具执行是否允许
        
        Args:
            tool_name: 工具名称
            tool_params: 工具参数
            context: 上下文信息
            
        Returns:
            ToolApproval: 审批结果
        """
        if not self._policy_enabled:
            # 策略未启用，直接批准
            return ToolApproval(
                approval_id="policy_disabled",
                tool_name=tool_name,
                tool_params=tool_params,
                status=ApprovalStatus.APPROVED,
                approver="system"
            )
        
        # 使用策略引擎评估
        approval = self._policy_engine.evaluate_tool(
            tool_name=tool_name,
            tool_params=tool_params,
            context=context or {}
        )
        
        return approval
    
    async def execute_with_policy(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        带策略检查的工具执行
        
        Args:
            tool_name: 工具名称
            tool_params: 工具参数
            context: 上下文信息
            **kwargs: 其他参数
            
        Returns:
            工具执行结果
        """
        # 检查策略
        approval = await self.check_tool_execution(
            tool_name=tool_name,
            tool_params=tool_params,
            context=context
        )
        
        # 如果未批准，抛出异常
        if approval.status not in [ApprovalStatus.APPROVED, ApprovalStatus.SKIPPED]:
            from ..tools.base_tool import ToolResult
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution not approved: {approval.rejection_reason}",
                execution_time=0.0
            )
        
        # 获取工具并执行
        tool = self.get_tool(tool_name)
        if not tool:
            from ..tools.base_tool import ToolResult
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool not found: {tool_name}",
                execution_time=0.0
            )
        
        # 执行工具
        try:
            result = await tool.execute(**tool_params)
            return result
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            from ..tools.base_tool import ToolResult
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=0.0
            )
    
    # ==================== 审批管理 ====================
    
    def approve_request(self, approval_id: str, approver: str = "admin") -> bool:
        """批准请求"""
        return self._policy_engine.approve(approval_id, approver)
    
    def reject_request(self, approval_id: str, reason: str, approver: str = "admin") -> bool:
        """拒绝请求"""
        return self._policy_engine.reject(approval_id, reason, approver)
    
    def get_pending_approvals(self) -> List[ToolApproval]:
        """获取待审批列表"""
        return self._policy_engine.get_pending_approvals()
    
    def get_approval_history(
        self,
        limit: int = 100,
        status: Optional[ApprovalStatus] = None
    ) -> List[ToolApproval]:
        """获取审批历史"""
        return self._policy_engine.get_approval_history(limit, status)
    
    def register_approval_callback(self, callback: Callable):
        """注册审批回调"""
        self._approval_callbacks.append(callback)
    
    def unregister_approval_callback(self, callback: Callable):
        """取消注册审批回调"""
        if callback in self._approval_callbacks:
            self._approval_callbacks.remove(callback)
    
    # ==================== 指标和审计 ====================
    
    def get_policy_metrics(self) -> Dict[str, Any]:
        """获取策略指标"""
        return self._policy_engine.get_metrics()
    
    def export_audit_log(self, path: str):
        """导出审计日志"""
        self._policy_engine.export_history(path)
    
    # ==================== 便捷方法 ====================
    
    def add_to_whitelist(self, tool_name: str):
        """添加工具到白名单"""
        policy = self._policy_engine.policy
        if tool_name not in policy.whitelist:
            policy.whitelist.append(tool_name)
            self._policy_engine.update_policy(policy)
    
    def add_to_blacklist(self, tool_name: str):
        """添加工具到黑名单"""
        policy = self._policy_engine.policy
        if tool_name not in policy.blacklist:
            policy.blacklist.append(tool_name)
            self._policy_engine.update_policy(policy)
    
    def remove_from_whitelist(self, tool_name: str):
        """从白名单移除"""
        policy = self._policy_engine.policy
        if tool_name in policy.whitelist:
            policy.whitelist.remove(tool_name)
            self._policy_engine.update_policy(policy)
    
    def remove_from_blacklist(self, tool_name: str):
        """从黑名单移除"""
        policy = self._policy_engine.policy
        if tool_name in policy.blacklist:
            policy.blacklist.remove(tool_name)
            self._policy_engine.update_policy(policy)
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """检查工具是否允许使用"""
        return self._policy_engine.policy.is_allowed(tool_name)
    
    def set_require_approval(self, require: bool):
        """设置是否需要审批"""
        policy = self._policy_engine.policy
        policy.require_approval = require
        self._policy_engine.update_policy(policy)


# 全局实例
_policy_enabled_registry: Optional[PolicyEnabledToolRegistry] = None


def get_policy_enabled_registry() -> PolicyEnabledToolRegistry:
    """获取策略启用的工具注册表"""
    global _policy_enabled_registry
    if _policy_enabled_registry is None:
        _policy_enabled_registry = PolicyEnabledToolRegistry()
    return _policy_enabled_registry


# 兼容原有接口
def get_tool_registry() -> PolicyEnabledToolRegistry:
    """获取工具注册表（兼容接口）"""
    return get_policy_enabled_registry()
