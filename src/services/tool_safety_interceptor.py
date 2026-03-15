#!/usr/bin/env python3
"""
工具安全拦截器 - Agent生产级安全底座
Tool Safety Interceptor - Agent Production Safety Foundation

参考文章核心观点：
"很多框架从意图到执行中间零拦截——模型一次幻觉就可能造成不可逆后果"

核心功能：
1. 危险操作识别与标记
2. 调用前参数校验
3. 执行前二次确认
4. 执行结果验证
5. 审计日志记录
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class DangerLevel(Enum):
    """危险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OperationCategory(Enum):
    """操作类别"""
    READ = "read"           # 读取操作
    WRITE = "write"         # 写入操作
    DELETE = "delete"       # 删除操作
    EXECUTE = "execute"     # 执行操作
    MONEY = "money"         # 金钱相关
    PRIVILEGE = "privilege" # 权限相关
    EXTERNAL = "external"   # 外部调用


@dataclass
class SafetyCheckResult:
    """安全检查结果"""
    is_safe: bool
    danger_level: DangerLevel
    operation_category: OperationCategory
    require_confirmation: bool
    confirmation_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)


@dataclass
class SafetyRule:
    """安全规则定义"""
    name: str
    danger_level: DangerLevel
    operation_category: OperationCategory
    keywords: List[str]  # 匹配的关键词
    patterns: List[str]  # 正则表达式模式
    require_confirmation: bool = False
    confirmation_prompt: str = "此操作可能存在风险，是否继续？"
    auto_block: bool = False
    block_reason: str = ""
    custom_validator: Optional[Callable] = None


class ToolSafetyInterceptor:
    """
    工具安全拦截器
    
    提供生产级工具调用安全保障：
    1. 危险操作识别
    2. 参数校验
    3. 二次确认
    4. 执行拦截
    5. 审计日志
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 危险等级阈值
        self.block_threshold = DangerLevel(
            self.config.get("block_threshold", "high")
        )
        
        # 确认阈值
        self.confirm_threshold = DangerLevel(
            self.config.get("confirm_threshold", "medium")
        )
        
        # 安全规则库
        self.rules: List[SafetyRule] = []
        self._init_default_rules()
        
        # 审计日志
        self.audit_log: List[Dict[str, Any]] = []
        
        # 统计
        self.stats = {
            "total_checks": 0,
            "blocked": 0,
            "confirmed": 0,
            "warnings": 0
        }
        
        logger.info("工具安全拦截器初始化完成")
    
    def _init_default_rules(self):
        """初始化默认安全规则"""
        
        # 删除操作规则
        self.register_rule(SafetyRule(
            name="delete_operation",
            danger_level=DangerLevel.HIGH,
            operation_category=OperationCategory.DELETE,
            keywords=["delete", "remove", "drop", "truncate", "删除", "移除", "撤销"],
            patterns=[r"delete[_\w]*", r"remove[_\w]*", r"drop[_\w]*"],
            require_confirmation=True,
            confirmation_prompt="此操作将永久删除数据，是否继续？",
            auto_block=False
        ))
        
        # 金钱操作规则
        self.register_rule(SafetyRule(
            name="money_operation",
            danger_level=DangerLevel.CRITICAL,
            operation_category=OperationCategory.MONEY,
            keywords=["payment", "pay", "transfer", "refund", "purchase", 
                     "支付", "转账", "退款", "购买", "充值", "提现"],
            patterns=[r"payment", r"transfer.*money", r"refund"],
            require_confirmation=True,
            confirmation_prompt="此操作涉及金钱交易，是否继续？",
            auto_block=False
        ))
        
        # 写入操作规则
        self.register_rule(SafetyRule(
            name="write_operation",
            danger_level=DangerLevel.MEDIUM,
            operation_category=OperationCategory.WRITE,
            keywords=["write", "update", "create", "insert", "set",
                     "写入", "更新", "创建", "修改", "设置"],
            patterns=[r"write[_\w]*", r"update[_\w]*", r"create[_\w]*"],
            require_confirmation=False,
            warnings=["此操作会修改数据"]
        ))
        
        # 执行操作规则
        self.register_rule(SafetyRule(
            name="execute_operation",
            danger_level=DangerLevel.MEDIUM,
            operation_category=OperationCategory.EXECUTE,
            keywords=["execute", "run", "shell", "bash", "cmd", "eval", "exec",
                     "执行", "运行", "命令"],
            patterns=[r"exec(ute)?[_\w]*", r"shell[_\w]*", r"bash", r"eval\("],
            require_confirmation=True,
            confirmation_prompt="此操作将执行系统命令，是否继续？",
            auto_block=False
        ))
        
        # 权限操作规则
        self.register_rule(SafetyRule(
            name="privilege_operation",
            danger_level=DangerLevel.HIGH,
            operation_category=OperationCategory.PRIVILEGE,
            keywords=["admin", "root", "sudo", "grant", "revoke", "permission",
                     "管理员", "权限", "授权"],
            patterns=[r"sudo", r"grant[_\w]*", r"admin[_\w]*"],
            require_confirmation=True,
            confirmation_prompt="此操作将修改权限，是否继续？",
            auto_block=False
        ))
        
        # 外部调用规则
        self.register_rule(SafetyRule(
            name="external_call",
            danger_level=DangerLevel.LOW,
            operation_category=OperationCategory.EXTERNAL,
            keywords=["webhook", "http", "https", "api", "callback",
                     "回调", "外部接口"],
            patterns=[r"https?://", r"webhook", r"callback"],
            require_confirmation=False,
            warnings=["此操作将访问外部资源"]
        ))
    
    def register_rule(self, rule: SafetyRule):
        """注册安全规则"""
        self.rules.append(rule)
        logger.debug(f"注册安全规则: {rule.name}")
    
    async def check(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> SafetyCheckResult:
        """
        执行安全检查
        
        Args:
            tool_name: 工具名称
            parameters: 调用参数
            user_id: 用户ID
            context: 额外上下文
            
        Returns:
            SafetyCheckResult: 检查结果
        """
        self.stats["total_checks"] += 1
        
        context = context or {}
        
        # 1. 匹配安全规则
        matched_rules = self._match_rules(tool_name, parameters)
        
        # 2. 确定最高危险等级
        max_danger = DangerLevel.SAFE
        operation_category = OperationCategory.READ
        
        for rule in matched_rules:
            if self._danger_to_int(rule.danger_level) > self._danger_to_int(max_danger):
                max_danger = rule.danger_level
            operation_category = rule.operation_category
        
        # 3. 生成警告
        warnings = []
        for rule in matched_rules:
            warnings.extend(rule.warnings)
        
        # 4. 判断是否需要确认
        require_confirmation = (
            max_danger in [DangerLevel.HIGH, DangerLevel.CRITICAL] or
            any(r.require_confirmation for r in matched_rules)
        )
        
        # 5. 判断是否需要拦截
        blocked = False
        block_reason = None
        
        for rule in matched_rules:
            if rule.auto_block:
                blocked = True
                block_reason = rule.block_reason
                self.stats["blocked"] += 1
                break
        
        # 检查危险等级是否超过阈值
        if self._danger_to_int(max_danger) >= self._danger_to_int(self.block_threshold):
            blocked = True
            block_reason = f"危险等级超过阈值: {max_danger.value}"
            self.stats["blocked"] += 1
        
        # 6. 生成建议
        suggestions = self._generate_suggestions(matched_rules, parameters)
        
        # 7. 记录审计日志
        self._log_audit(
            tool_name=tool_name,
            parameters=parameters,
            user_id=user_id,
            result=SafetyCheckResult(
                is_safe=not blocked,
                danger_level=max_danger,
                operation_category=operation_category,
                require_confirmation=require_confirmation,
                warnings=warnings,
                blocked=blocked,
                block_reason=block_reason,
                suggestions=suggestions
            )
        )
        
        # 统计
        if require_confirmation and not blocked:
            self.stats["confirmed"] += 1
        if warnings:
            self.stats["warnings"] += 1
        
        # 构建确认消息
        confirmation_message = None
        if require_confirmation and not blocked:
            for rule in matched_rules:
                if rule.require_confirmation:
                    confirmation_message = rule.confirmation_prompt
                    break
        
        return SafetyCheckResult(
            is_safe=not blocked,
            danger_level=max_danger,
            operation_category=operation_category,
            require_confirmation=require_confirmation,
            confirmation_message=confirmation_message,
            warnings=warnings,
            blocked=blocked,
            block_reason=block_reason,
            suggestions=suggestions
        )
    
    def _match_rules(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> List[SafetyRule]:
        """匹配适用的安全规则"""
        matched = []
        
        tool_name_lower = tool_name.lower()
        params_str = str(parameters).lower()
        
        for rule in self.rules:
            # 检查关键词
            keyword_match = any(
                kw.lower() in tool_name_lower or kw.lower() in params_str
                for kw in rule.keywords
            )
            
            # 检查正则模式
            pattern_match = False
            for pattern in rule.patterns:
                if re.search(pattern, tool_name_lower) or re.search(pattern, params_str):
                    pattern_match = True
                    break
            
            if keyword_match or pattern_match:
                matched.append(rule)
        
        return matched
    
    def _danger_to_int(self, level: DangerLevel) -> int:
        """危险等级转数值"""
        mapping = {
            DangerLevel.SAFE: 0,
            DangerLevel.LOW: 1,
            DangerLevel.MEDIUM: 2,
            DangerLevel.HIGH: 3,
            DangerLevel.CRITICAL: 4
        }
        return mapping.get(level, 0)
    
    def _generate_suggestions(
        self,
        matched_rules: List[SafetyRule],
        parameters: Dict[str, Any]
    ) -> List[str]:
        """生成安全建议"""
        suggestions = []
        
        for rule in matched_rules:
            if rule.operation_category == OperationCategory.DELETE:
                suggestions.append("建议先备份数据")
                suggestions.append("考虑使用软删除而非永久删除")
            elif rule.operation_category == OperationCategory.MONEY:
                suggestions.append("建议增加人工审核流程")
                suggestions.append("建议记录操作日志")
            elif rule.operation_category == OperationCategory.EXECUTE:
                suggestions.append("建议在沙箱环境中执行")
                suggestions.append("限制执行权限和范围")
        
        return suggestions[:3]  # 最多3条
    
    def _log_audit(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: Optional[str],
        result: SafetyCheckResult
    ):
        """记录审计日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "user_id": user_id,
            "is_safe": result.is_safe,
            "danger_level": result.danger_level.value,
            "operation_category": result.operation_category.value,
            "require_confirmation": result.require_confirmation,
            "blocked": result.blocked,
            "block_reason": result.block_reason
        }
        
        self.audit_log.append(log_entry)
        
        # 保留最近1000条
        if len(self.audit_log) > 1000:
            self.audit_log = self.audit_log[-1000:]
        
        # 记录危险操作日志
        if result.blocked or result.danger_level in [DangerLevel.HIGH, DangerLevel.CRITICAL]:
            logger.warning(f"安全拦截: {tool_name}, 危险等级: {result.danger_level.value}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "audit_log_size": len(self.audit_log),
            "rules_count": len(self.rules)
        }
    
    def get_audit_log(
        self,
        limit: int = 100,
        blocked_only: bool = False
    ) -> List[Dict[str, Any]]:
        """获取审计日志"""
        logs = self.audit_log
        
        if blocked_only:
            logs = [l for l in logs if l["blocked"]]
        
        return logs[-limit:]
    
    def reset_stats(self):
        """重置统计"""
        self.stats = {
            "total_checks": 0,
            "blocked": 0,
            "confirmed": 0,
            "warnings": 0
        }


# 全局单例
_safety_interceptor: Optional[ToolSafetyInterceptor] = None


def get_safety_interceptor(
    config: Optional[Dict[str, Any]] = None
) -> ToolSafetyInterceptor:
    """获取工具安全拦截器单例"""
    global _safety_interceptor
    
    if _safety_interceptor is None:
        _safety_interceptor = ToolSafetyInterceptor(config)
    
    return _safety_interceptor
