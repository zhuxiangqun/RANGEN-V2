#!/usr/bin/env python3
"""
Tool Policy System - 工具执行审批机制

基于OpenClaw架构的工具策略系统:
- 白名单/黑名单管理
- 工具执行审批流程
- 危险工具检测
- 使用审计日志
"""

import time
import json
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class ApprovalStatus(Enum):
    """审批状态"""
    PENDING = "pending"       # 待审批
    APPROVED = "approved"     # 已批准
    REJECTED = "rejected"    # 已拒绝
    SKIPPED = "skipped"      # 跳过（自动批准）


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"              # 低风险
    MEDIUM = "medium"        # 中风险
    HIGH = "high"            # 高风险
    CRITICAL = "critical"   # 极高风险


@dataclass
class ToolApproval:
    """工具审批记录"""
    
    approval_id: str
    tool_name: str
    tool_params: Dict[str, Any]
    requester: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    
    # 风险评估
    risk_level: RiskLevel = RiskLevel.LOW
    risk_reasons: List[str] = field(default_factory=list)
    
    # 审批信息
    approver: str = ""
    approval_time: Optional[datetime] = None
    rejection_reason: str = ""
    
    # 元数据
    request_time: datetime = field(default_factory=datetime.now)
    session_id: str = ""
    agent_id: str = ""
    
    def approve(self, approver: str = "auto"):
        """批准"""
        self.status = ApprovalStatus.APPROVED
        self.approver = approver
        self.approval_time = datetime.now()
    
    def reject(self, reason: str, approver: str = "auto"):
        """拒绝"""
        self.status = ApprovalStatus.REJECTED
        self.rejection_reason = reason
        self.approver = approver
        self.approval_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "approval_id": self.approval_id,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "requester": self.requester,
            "status": self.status.value,
            "risk_level": self.risk_level.value,
            "risk_reasons": self.risk_reasons,
            "approver": self.approver,
            "approval_time": self.approval_time.isoformat() if self.approval_time else None,
            "rejection_reason": self.rejection_reason,
            "request_time": self.request_time.isoformat(),
            "session_id": self.session_id,
            "agent_id": self.agent_id
        }


@dataclass
class ToolPolicy:
    """工具策略配置"""
    
    # 白名单/黑名单
    whitelist: List[str] = field(default_factory=list)  # 允许的工具
    blacklist: List[str] = field(default_factory=list)  # 禁止的工具
    
    # 审批设置
    require_approval: bool = False
    approval_threshold: RiskLevel = RiskLevel.MEDIUM  # 需要审批的风险等级
    
    # 自动批准设置
    auto_approve_safe: bool = True
    auto_approve_whitelist: bool = True
    
    # 危险工具检测
    dangerous_tools: Dict[str, List[str]] = field(default_factory=dict)  # tool -> 危险参数
    dangerous_patterns: List[str] = field(default_factory=list)  # 危险参数模式
    
    # 会话设置
    session_timeout: int = 300  # 审批超时时间（秒）
    max_pending_approvals: int = 10
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolPolicy':
        """从字典创建"""
        return cls(
            whitelist=data.get("whitelist", []),
            blacklist=data.get("blacklist", []),
            require_approval=data.get("require_approval", False),
            approval_threshold=RiskLevel(data.get("approval_threshold", "medium")),
            auto_approve_safe=data.get("auto_approve_safe", True),
            auto_approve_whitelist=data.get("auto_approve_whitelist", True),
            dangerous_tools=data.get("dangerous_tools", {}),
            dangerous_patterns=data.get("dangerous_patterns", []),
            session_timeout=data.get("session_timeout", 300),
            max_pending_approvals=data.get("max_pending_approvals", 10)
        )
    
    def is_allowed(self, tool_name: str) -> bool:
        """检查工具是否允许使用"""
        # 黑名单优先
        if tool_name in self.blacklist:
            return False
        
        # 白名单检查
        if self.whitelist and tool_name not in self.whitelist:
            return False
        
        return True
    
    def needs_approval(self, risk_level: RiskLevel) -> bool:
        """检查是否需要审批"""
        if not self.require_approval:
            return False
        
        # 风险等级比较
        risk_order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        return risk_order.index(risk_level) >= risk_order.index(self.approval_threshold)


class ToolPolicyEngine:
    """工具策略引擎"""
    
    def __init__(self, policy: Optional[ToolPolicy] = None):
        self.policy = policy or ToolPolicy()
        
        # 审批请求队列
        self._pending_approvals: Dict[str, ToolApproval] = {}
        self._approval_history: List[ToolApproval] = []
        self._max_history = 10000
        
        # 审批回调
        self._approval_callbacks: List[Callable] = []
        
        # 锁
        self._lock = threading.RLock()
        
        # 指标
        self._total_requests = 0
        self._approved_count = 0
        self._rejected_count = 0
        
        self.logger = logging.getLogger(__name__)
    
    def evaluate_tool(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ToolApproval:
        """
        评估工具请求
        
        Args:
            tool_name: 工具名称
            tool_params: 工具参数
            context: 上下文信息
            
        Returns:
            ToolApproval: 审批记录
        """
        import uuid
        
        self._total_requests += 1
        context = context or {}
        
        approval = ToolApproval(
            approval_id=str(uuid.uuid4()),
            tool_name=tool_name,
            tool_params=tool_params,
            requester=context.get("requester", "system"),
            session_id=context.get("session_id", ""),
            agent_id=context.get("agent_id", "")
        )
        
        # 1. 黑名单检查
        if tool_name in self.policy.blacklist:
            approval.risk_level = RiskLevel.CRITICAL
            approval.risk_reasons.append(f"Tool '{tool_name}' is in blacklist")
            approval.reject("Tool is blacklisted")
            self._rejected_count += 1
            self._record_approval(approval)
            return approval
        
        # 2. 白名单检查
        if self.policy.whitelist:
            if tool_name not in self.policy.whitelist:
                approval.risk_level = RiskLevel.MEDIUM
                approval.risk_reasons.append(f"Tool '{tool_name}' is not in whitelist")
            else:
                approval.risk_level = RiskLevel.LOW
                if self.policy.auto_approve_whitelist:
                    approval.status = ApprovalStatus.SKIPPED
                    approval.approve("auto")
                    self._approved_count += 1
                    self._record_approval(approval)
                    return approval
        
        # 3. 危险参数检查
        risk_level, risk_reasons = self._evaluate_risk(tool_name, tool_params)
        approval.risk_level = risk_level
        approval.risk_reasons = risk_reasons
        
        # 4. 确定审批状态
        if not approval.risk_reasons:  # 无风险
            approval.risk_level = RiskLevel.LOW
        
        # 需要审批
        if self.policy.needs_approval(approval.risk_level):
            if self.policy.auto_approve_safe and approval.risk_level == RiskLevel.LOW:
                approval.status = ApprovalStatus.SKIPPED
                approval.approve("auto")
            else:
                # 加入待审批队列
                approval.status = ApprovalStatus.PENDING
                self._add_pending_approval(approval)
        else:
            # 自动批准
            approval.approve("auto")
        
        if approval.status == ApprovalStatus.APPROVED:
            self._approved_count += 1
        elif approval.status == ApprovalStatus.REJECTED:
            self._rejected_count += 1
        
        self._record_approval(approval)
        return approval
    
    def _evaluate_risk(
        self,
        tool_name: str,
        tool_params: Dict[str, Any]
    ) -> tuple[RiskLevel, List[str]]:
        """评估风险"""
        risk_level = RiskLevel.LOW
        risk_reasons = []
        
        # 检查危险工具配置
        if tool_name in self.policy.dangerous_tools:
            dangerous_params = self.policy.dangerous_tools[tool_name]
            for param in dangerous_params:
                if param in tool_params:
                    risk_level = RiskLevel.HIGH
                    risk_reasons.append(f"Dangerous parameter '{param}' in tool '{tool_name}'")
        
        # 检查危险模式
        for pattern in self.policy.dangerous_patterns:
            params_str = json.dumps(tool_params)
            if pattern in params_str:
                risk_level = RiskLevel.HIGH
                risk_reasons.append(f"Dangerous pattern '{pattern}' detected")
        
        return risk_level, risk_reasons
    
    def _add_pending_approval(self, approval: ToolApproval):
        """添加待审批"""
        with self._lock:
            # 检查是否超过最大待审批数
            if len(self._pending_approvals) >= self.policy.max_pending_approvals:
                self.logger.warning("Max pending approvals reached")
                approval.reject("Too many pending approvals")
                return
            
            self._pending_approvals[approval.approval_id] = approval
            
            # 触发回调
            for callback in self._approval_callbacks:
                try:
                    callback(approval)
                except Exception as e:
                    self.logger.error(f"Approval callback failed: {e}")
    
    def _record_approval(self, approval: ToolApproval):
        """记录审批"""
        with self._lock:
            self._approval_history.append(approval)
            if len(self._approval_history) > self._max_history:
                self._approval_history = self._approval_history[-self._max_history:]
    
    def approve(self, approval_id: str, approver: str = "admin") -> bool:
        """
        批准请求
        
        Args:
            approval_id: 审批ID
            approver: 审批人
            
        Returns:
            是否成功
        """
        with self._lock:
            if approval_id not in self._pending_approvals:
                return False
            
            approval = self._pending_approvals[approval_id]
            approval.approve(approver)
            self._approved_count += 1
            
            del self._pending_approvals[approval_id]
            return True
    
    def reject(self, approval_id: str, reason: str, approver: str = "admin") -> bool:
        """
        拒绝请求
        
        Args:
            approval_id: 审批ID
            reason: 拒绝原因
            approver: 审批人
            
        Returns:
            是否成功
        """
        with self._lock:
            if approval_id not in self._pending_approvals:
                return False
            
            approval = self._pending_approvals[approval_id]
            approval.reject(reason, approver)
            self._rejected_count += 1
            
            del self._pending_approvals[approval_id]
            return True
    
    def get_pending_approvals(self) -> List[ToolApproval]:
        """获取待审批列表"""
        with self._lock:
            return list(self._pending_approvals.values())
    
    def get_approval_history(
        self,
        limit: int = 100,
        status: Optional[ApprovalStatus] = None
    ) -> List[ToolApproval]:
        """获取审批历史"""
        with self._lock:
            history = self._approval_history
            if status:
                history = [a for a in history if a.status == status]
            return history[-limit:]
    
    def register_callback(self, callback: Callable):
        """注册审批回调"""
        self._approval_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable):
        """取消注册"""
        if callback in self._approval_callbacks:
            self._approval_callbacks.remove(callback)
    
    def update_policy(self, policy: ToolPolicy):
        """更新策略"""
        with self._lock:
            self.policy = policy
            self.logger.info("Tool policy updated")
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        with self._lock:
            return {
                "total_requests": self._total_requests,
                "approved": self._approved_count,
                "rejected": self._rejected_count,
                "pending": len(self._pending_approvals),
                "approval_rate": (
                    self._approved_count / self._total_requests 
                    if self._total_requests > 0 else 0
                ),
                "rejection_rate": (
                    self._rejected_count / self._total_requests 
                    if self._total_requests > 0 else 0
                )
            }
    
    def export_history(self, path: str):
        """导出历史到文件"""
        with self._lock:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(
                    [a.to_dict() for a in self._approval_history],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            self.logger.info(f"Exported approval history to {path}")


# 全局工具策略引擎
_tool_policy_engine: Optional[ToolPolicyEngine] = None


def get_tool_policy_engine() -> ToolPolicyEngine:
    """获取全局工具策略引擎"""
    global _tool_policy_engine
    if _tool_policy_engine is None:
        _tool_policy_engine = ToolPolicyEngine()
    return _tool_policy_engine


def reset_tool_policy_engine():
    """重置工具策略引擎"""
    global _tool_policy_engine
    _tool_policy_engine = None
