#!/usr/bin/env python3
"""
审核Agent原型 - 基于唐朝三省六部制的门下省审核机制

实现基础的Agent操作审核功能，包括：
1. 监控Agent通信
2. 检查宪法合规性
3. 批准/拒绝操作
4. 记录审核结果
"""

import asyncio
import time
import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .base_agent import BaseAgent
from .agent_models import AgentResult, ProcessingResult, AgentConfig
from src.services.logging_service import get_logger
from src.hook.transparency import HookTransparencySystem
from src.hook.hook_types import HookEventType, HookVisibilityLevel

logger = get_logger("audit_agent")


class AuditDecision(Enum):
    """审核决策"""
    APPROVED = "approved"       # 批准
    REJECTED = "rejected"       # 拒绝
    PENDING = "pending"         # 待审核
    CONDITIONAL = "conditional" # 有条件批准


class AuditSeverity(Enum):
    """审核严重程度"""
    LOW = "low"        # 低风险
    MEDIUM = "medium"  # 中风险
    HIGH = "high"      # 高风险
    CRITICAL = "critical" # 关键风险


@dataclass
class AuditRule:
    """审核规则"""
    rule_id: str
    name: str
    description: str
    condition: str  # 条件表达式或函数
    severity: AuditSeverity
    action: AuditDecision  # 违反规则的默认决策
    enabled: bool = True
    created_at: float = field(default_factory=time.time)


@dataclass
class AuditRequest:
    """审核请求"""
    request_id: str
    source_agent: str
    target_agent: str
    action_type: str  # 操作类型：communication, execution, modification, access
    action_details: Dict[str, Any]
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    priority: str = "normal"  # low, normal, high, critical


@dataclass
class AuditResult:
    """审核结果"""
    request_id: str
    decision: AuditDecision
    reasons: List[str]
    violated_rules: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    audit_score: float = 1.0  # 审核分数 0.0-1.0
    timestamp: float = field(default_factory=time.time)
    auditor_id: str = "audit_agent"
    metadata: Dict[str, Any] = field(default_factory=dict)


class AuditAgent(BaseAgent):
    """
    审核Agent - 实现门下省审核机制
    
    负责审核Agent间通信、操作执行和系统变更，
    确保符合宪法规则和系统策略。
    """
    
    def __init__(self, agent_id: str = "audit_agent", 
                 capabilities: Optional[List[str]] = None,
                 config: Optional[AgentConfig] = None):
        """初始化审核Agent"""
        if capabilities is None:
            capabilities = [
                "communication_audit",
                "execution_audit", 
                "constitution_compliance",
                "risk_assessment",
                "decision_logging"
            ]
        
        super().__init__(agent_id, capabilities, config)
        
        # 审核规则库
        self.audit_rules: Dict[str, AuditRule] = {}
        
        # 审核历史
        self.audit_history: List[AuditResult] = []
        
        # Hook系统集成
        self.hook_system = HookTransparencySystem("audit_system")
        
        # 初始化默认规则
        self._initialize_default_rules()
        
        # 性能统计
        self.audit_stats = {
            "total_requests": 0,
            "approved": 0,
            "rejected": 0,
            "conditional": 0,
            "pending": 0,
            "average_audit_time": 0.0
        }
        
        logger.info(f"审核Agent {agent_id} 初始化完成")
    
    def _initialize_default_rules(self):
        """初始化默认审核规则"""
        # 宪法合规性规则
        self.add_audit_rule(
            rule_id="constitution_001",
            name="宪法基本合规",
            description="检查操作是否符合宪法基本原则",
            condition="check_constitution_compliance",
            severity=AuditSeverity.CRITICAL,
            action=AuditDecision.REJECTED
        )
        
        # 通信权限规则
        self.add_audit_rule(
            rule_id="communication_001",
            name="跨域通信权限",
            description="检查Agent间跨域通信是否获得授权",
            condition="check_communication_permission",
            severity=AuditSeverity.HIGH,
            action=AuditDecision.REJECTED
        )
        
        # 资源访问规则
        self.add_audit_rule(
            rule_id="resource_001",
            name="敏感资源访问",
            description="检查对敏感资源的访问权限",
            condition="check_resource_access",
            severity=AuditSeverity.HIGH,
            action=AuditDecision.REJECTED
        )
        
        # 操作频率规则
        self.add_audit_rule(
            rule_id="frequency_001",
            name="操作频率限制",
            description="检查操作频率是否超出限制",
            condition="check_operation_frequency",
            severity=AuditSeverity.MEDIUM,
            action=AuditDecision.CONDITIONAL
        )
        
        # 数据完整性规则
        self.add_audit_rule(
            rule_id="integrity_001",
            name="数据完整性检查",
            description="检查操作数据的完整性",
            condition="check_data_integrity",
            severity=AuditSeverity.MEDIUM,
            action=AuditDecision.REJECTED
        )
        
        logger.info(f"已加载 {len(self.audit_rules)} 个默认审核规则")
    
    def add_audit_rule(self, rule_id: str, name: str, description: str,
                      condition: str, severity: AuditSeverity,
                      action: AuditDecision, enabled: bool = True) -> bool:
        """添加审核规则"""
        try:
            rule = AuditRule(
                rule_id=rule_id,
                name=name,
                description=description,
                condition=condition,
                severity=severity,
                action=action,
                enabled=enabled
            )
            
            self.audit_rules[rule_id] = rule
            logger.info(f"添加审核规则: {name} ({rule_id})")
            return True
            
        except Exception as e:
            logger.error(f"添加审核规则失败: {e}")
            return False
    
    def remove_audit_rule(self, rule_id: str) -> bool:
        """移除审核规则"""
        if rule_id in self.audit_rules:
            del self.audit_rules[rule_id]
            logger.info(f"移除审核规则: {rule_id}")
            return True
        return False
    
    def enable_audit_rule(self, rule_id: str, enabled: bool = True) -> bool:
        """启用/禁用审核规则"""
        if rule_id in self.audit_rules:
            self.audit_rules[rule_id].enabled = enabled
            status = "启用" if enabled else "禁用"
            logger.info(f"{status}审核规则: {rule_id}")
            return True
        return False
    
    async def audit_request(self, request: AuditRequest) -> AuditResult:
        """审核请求"""
        start_time = time.time()
        self.audit_stats["total_requests"] += 1
        
        logger.info(f"开始审核请求: {request.request_id} "
                   f"[{request.source_agent} -> {request.target_agent}]")
        
        try:
            # 初始化审核结果
            decision = AuditDecision.APPROVED
            reasons = []
            violated_rules = []
            recommendations = []
            audit_score = 1.0
            
            # 应用所有启用的审核规则
            for rule_id, rule in self.audit_rules.items():
                if not rule.enabled:
                    continue
                
                # 检查规则条件
                rule_violated = await self._check_rule_condition(
                    rule.condition, request
                )
                
                if rule_violated:
                    violated_rules.append(rule_id)
                    reasons.append(f"违反规则: {rule.name} - {rule.description}")
                    
                    # 根据规则严重程度调整决策
                    if rule.severity == AuditSeverity.CRITICAL:
                        decision = rule.action
                        audit_score *= 0.3
                    elif rule.severity == AuditSeverity.HIGH:
                        if decision != AuditDecision.REJECTED:
                            decision = rule.action
                        audit_score *= 0.5
                    elif rule.severity == AuditSeverity.MEDIUM:
                        if decision == AuditDecision.APPROVED:
                            decision = rule.action
                        audit_score *= 0.7
                    elif rule.severity == AuditSeverity.LOW:
                        if decision == AuditDecision.APPROVED:
                            decision = AuditDecision.CONDITIONAL
                        audit_score *= 0.9
            
            # 生成建议
            if decision == AuditDecision.REJECTED:
                recommendations.append("操作被拒绝，请检查合规性")
            elif decision == AuditDecision.CONDITIONAL:
                recommendations.append("操作有条件批准，请遵循附加条件")
            
            # 计算最终审核分数
            if violated_rules:
                audit_score = max(0.0, audit_score - 0.1 * len(violated_rules))
            
            # 创建审核结果
            result = AuditResult(
                request_id=request.request_id,
                decision=decision,
                reasons=reasons,
                violated_rules=violated_rules,
                recommendations=recommendations,
                audit_score=audit_score,
                auditor_id=self.agent_id,
                metadata={
                    "source_agent": request.source_agent,
                    "target_agent": request.target_agent,
                    "action_type": request.action_type,
                    "processing_time": time.time() - start_time
                }
            )
            
            # 记录审核历史
            self.audit_history.append(result)
            
            # 更新统计
            if decision == AuditDecision.APPROVED:
                self.audit_stats["approved"] += 1
            elif decision == AuditDecision.REJECTED:
                self.audit_stats["rejected"] += 1
            elif decision == AuditDecision.CONDITIONAL:
                self.audit_stats["conditional"] += 1
            
            # 记录Hook事件
            await self._record_audit_event(request, result)
            
            # 记录日志
            log_level = logging.INFO if decision == AuditDecision.APPROVED else logging.WARNING
            logger.log(log_level, 
                      f"审核完成: {request.request_id} -> {decision.value} "
                      f"(分数: {audit_score:.2f}, 违反规则: {len(violated_rules)})")
            
            return result
            
        except Exception as e:
            logger.error(f"审核请求失败: {e}")
            
            # 返回错误结果
            return AuditResult(
                request_id=request.request_id,
                decision=AuditDecision.REJECTED,
                reasons=[f"审核过程出错: {str(e)}"],
                audit_score=0.0,
                auditor_id=self.agent_id,
                metadata={"error": str(e)}
            )
    
    async def _check_rule_condition(self, condition: str, request: AuditRequest) -> bool:
        """检查规则条件"""
        try:
            # 根据条件名称调用相应的检查方法
            if condition == "check_constitution_compliance":
                return await self._check_constitution_compliance(request)
            elif condition == "check_communication_permission":
                return await self._check_communication_permission(request)
            elif condition == "check_resource_access":
                return await self._check_resource_access(request)
            elif condition == "check_operation_frequency":
                return await self._check_operation_frequency(request)
            elif condition == "check_data_integrity":
                return await self._check_data_integrity(request)
            else:
                # 默认情况下，假设条件为布尔表达式
                # 这里可以扩展为解析表达式
                logger.warning(f"未知的规则条件: {condition}")
                return False
                
        except Exception as e:
            logger.error(f"检查规则条件失败: {e}")
            return False
    
    async def _check_constitution_compliance(self, request: AuditRequest) -> bool:
        """检查宪法合规性"""
        # 简化实现：检查操作类型是否符合宪法原则
        action_type = request.action_type
        
        # 定义违反宪法的操作类型
        unconstitutional_actions = [
            "system_shutdown",
            "constitution_modification",
            "agent_deletion",
            "privilege_escalation"
        ]
        
        if action_type in unconstitutional_actions:
            # 检查是否有特殊授权
            if request.context.get("constitution_approved", False):
                return False
            return True
        
        return False
    
    async def _check_communication_permission(self, request: AuditRequest) -> bool:
        """检查通信权限"""
        source_agent = request.source_agent
        target_agent = request.target_agent
        
        # 简化实现：检查跨域通信
        # 假设Agent ID格式为"domain.agent_name"
        source_domain = source_agent.split('.')[0] if '.' in source_agent else "default"
        target_domain = target_agent.split('.')[0] if '.' in target_agent else "default"
        
        if source_domain != target_domain:
            # 跨域通信需要特殊权限
            if not request.context.get("cross_domain_permission", False):
                return True
        
        return False
    
    async def _check_resource_access(self, request: AuditRequest) -> bool:
        """检查资源访问权限"""
        action_details = request.action_details
        
        # 检查是否访问敏感资源
        sensitive_resources = [
            "system_config",
            "user_data",
            "api_keys",
            "database"
        ]
        
        accessed_resource = action_details.get("resource", "")
        if any(resource in accessed_resource for resource in sensitive_resources):
            # 检查是否有访问权限
            if not request.context.get("resource_permission", False):
                return True
        
        return False
    
    async def _check_operation_frequency(self, request: AuditRequest) -> bool:
        """检查操作频率"""
        source_agent = request.source_agent
        action_type = request.action_type
        
        # 简化实现：检查最近的操作次数
        recent_audits = [
            audit for audit in self.audit_history[-100:] 
            if audit.metadata.get("source_agent") == source_agent
            and time.time() - audit.timestamp < 60  # 最近60秒
        ]
        
        # 如果最近操作次数过多，则违反规则
        if len(recent_audits) > 10:  # 10次/分钟
            return True
        
        return False
    
    async def _check_data_integrity(self, request: AuditRequest) -> bool:
        """检查数据完整性"""
        action_details = request.action_details
        
        # 简化实现：检查必要字段
        required_fields = ["action", "target", "timestamp"]
        
        for field in required_fields:
            if field not in action_details:
                return True
        
        return False
    
    async def _record_audit_event(self, request: AuditRequest, result: AuditResult):
        """记录审核事件到Hook系统"""
        try:
            event_data = {
                "request_id": request.request_id,
                "source_agent": request.source_agent,
                "target_agent": request.target_agent,
                "action_type": request.action_type,
                "decision": result.decision.value,
                "audit_score": result.audit_score,
                "violated_rules": result.violated_rules,
                "reasons": result.reasons,
                "processing_time": result.metadata.get("processing_time", 0)
            }
            
            await self.hook_system.recorder.record_event(
                event_type=HookEventType.AUDIT_COMPLETED,
                source=self.agent_id,
                data=event_data,
                visibility=HookVisibilityLevel.SYSTEM
            )
            
        except Exception as e:
            logger.error(f"记录审核事件失败: {e}")
    
    async def get_audit_history(self, limit: int = 50) -> List[AuditResult]:
        """获取审核历史"""
        return self.audit_history[-limit:] if self.audit_history else []
    
    async def get_audit_stats(self) -> Dict[str, Any]:
        """获取审核统计"""
        stats = self.audit_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["approval_rate"] = stats["approved"] / stats["total_requests"]
            stats["rejection_rate"] = stats["rejected"] / stats["total_requests"]
        else:
            stats["approval_rate"] = 0.0
            stats["rejection_rate"] = 0.0
        
        stats["total_rules"] = len(self.audit_rules)
        stats["enabled_rules"] = sum(1 for r in self.audit_rules.values() if r.enabled)
        stats["audit_history_count"] = len(self.audit_history)
        
        return stats
    
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResult:
        """处理查询 - 实现BaseAgent抽象方法"""
        try:
            context = context or {}
            
            # 解析查询类型
            if query.startswith("audit "):
                # 模拟审核请求
                request = AuditRequest(
                    request_id=f"test_{int(time.time())}",
                    source_agent=context.get("source_agent", "test_source"),
                    target_agent=context.get("target_agent", "test_target"),
                    action_type=context.get("action_type", "test_action"),
                    action_details=context.get("action_details", {}),
                    context=context
                )
                
                result = await self.audit_request(request)
                
                return AgentResult(
                    success=True,
                    data={
                        "audit_result": {
                            "decision": result.decision.value,
                            "score": result.audit_score,
                            "violated_rules": result.violated_rules,
                            "reasons": result.reasons
                        }
                    },
                    confidence=0.9,
                    processing_time=0.0,
                    metadata={"query_type": "audit_request"}
                )
                
            elif query == "get_stats":
                # 获取统计信息
                stats = await self.get_audit_stats()
                
                return AgentResult(
                    success=True,
                    data=stats,
                    confidence=0.95,
                    processing_time=0.0,
                    metadata={"query_type": "audit_stats"}
                )
                
            elif query == "get_rules":
                # 获取规则列表
                rules_list = [
                    {
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "description": rule.description,
                        "severity": rule.severity.value,
                        "enabled": rule.enabled
                    }
                    for rule in self.audit_rules.values()
                ]
                
                return AgentResult(
                    success=True,
                    data={"rules": rules_list, "count": len(rules_list)},
                    confidence=0.95,
                    processing_time=0.0,
                    metadata={"query_type": "audit_rules"}
                )
                
            else:
                # 默认响应
                return AgentResult(
                    success=True,
                    data={
                        "message": "审核Agent就绪",
                        "capabilities": self.capabilities,
                        "stats": await self.get_audit_stats()
                    },
                    confidence=0.8,
                    processing_time=0.0,
                    metadata={"query_type": "general"}
                )
                
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            return AgentResult(
                success=False,
                data=None,
                confidence=0.0,
                processing_time=0.0,
                error=str(e)
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        stats = await self.get_audit_stats()
        
        health_status = "healthy"
        if stats.get("rejection_rate", 0) > 0.5:  # 拒绝率超过50%
            health_status = "warning"
        elif stats.get("total_requests", 0) == 0:
            health_status = "idle"
        
        return {
            "agent_id": self.agent_id,
            "status": health_status,
            "audit_stats": stats,
            "rules_count": len(self.audit_rules),
            "history_count": len(self.audit_history),
            "timestamp": time.time()
        }


# 创建审核Agent的辅助函数
def create_audit_agent(agent_id: str = "audit_agent") -> AuditAgent:
    """创建审核Agent实例"""
    return AuditAgent(agent_id=agent_id)


async def test_audit_agent():
    """测试审核Agent"""
    print("测试审核Agent...")
    
    agent = create_audit_agent()
    
    # 测试审核请求
    request = AuditRequest(
        request_id="test_001",
        source_agent="research.agent1",
        target_agent="execution.agent2",
        action_type="data_access",
        action_details={
            "resource": "user_data",
            "operation": "read"
        },
        context={
            "cross_domain_permission": False,
            "resource_permission": False
        }
    )
    
    result = await agent.audit_request(request)
    print(f"审核结果: {result.decision.value}")
    print(f"审核分数: {result.audit_score}")
    print(f"违反规则: {result.violated_rules}")
    
    # 获取统计信息
    stats = await agent.get_audit_stats()
    print(f"审核统计: {stats}")
    
    return agent


if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_audit_agent())