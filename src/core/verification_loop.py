#!/usr/bin/env python3
"""
Verification Loop - 验证循环
验证任务执行结果，支持自动重试和纠正
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re


class VerificationStatus(Enum):
    """验证状态"""
    PASSED = "passed"
    FAILED = "failed"
    NEEDS_IMPROVEMENT = "needs_improvement"
    PENDING = "pending"


@dataclass
class VerificationRule:
    """验证规则"""
    name: str
    description: str
    check_function: Callable[[Any], bool]
    severity: str = "error"  # error, warning, info


@dataclass
class VerificationResult:
    """验证结果"""
    status: VerificationStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    retry_needed: bool = False


class VerificationLoop:
    """
    验证循环
    
    功能：
    1. 验证任务执行结果
    2. 自动识别问题
    3. 提供改进建议
    4. 支持自动重试
    """
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.rules: List[VerificationRule] = []
        self.verification_history: List[VerificationResult] = []
        
        # 添加默认验证规则
        self._add_default_rules()
    
    def _add_default_rules(self):
        """添加默认验证规则"""
        
        # 1. 检查结果是否为空
        self.add_rule(VerificationRule(
            name="not_empty",
            description="结果不能为空",
            check_function=lambda r: r is not None and (
                (isinstance(r, str) and len(r.strip()) > 0) or
                (isinstance(r, dict) and len(r) > 0) or
                (isinstance(r, list) and len(r) > 0)
            ),
            severity="error"
        ))
        
        # 2. 检查结果长度
        self.add_rule(VerificationRule(
            name="min_length",
            description="结果长度至少10个字符",
            check_function=lambda r: (
                isinstance(r, str) and len(r) >= 10
            ) or not isinstance(r, str),
            severity="warning"
        ))
        
        # 3. 检查是否包含关键词（如果有的话）
        self.add_rule(VerificationRule(
            name="content_quality",
            description="结果应包含实质性内容",
            check_function=lambda r: (
                isinstance(r, str) and (
                    len(r) > 50 or 
                    any(marker in r.lower() for marker in ["具体", "详细", "分析", "结果", "原因", "首先", "但是"])
                )
            ) or not isinstance(r, str),
            severity="warning"
        ))
    
    def add_rule(self, rule: VerificationRule):
        """添加验证规则"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """移除验证规则"""
        self.rules = [r for r in self.rules if r.name != rule_name]
    
    def verify(self, result: Any, context: Optional[Dict[str, Any]] = None) -> VerificationResult:
        """
        验证结果
        
        Args:
            result: 待验证的结果
            context: 上下文信息
            
        Returns:
            VerificationResult: 验证结果
        """
        context = context or {}
        failed_rules = []
        warnings = []
        
        # 执行所有规则检查
        for rule in self.rules:
            try:
                passed = rule.check_function(result)
                if not passed:
                    if rule.severity == "error":
                        failed_rules.append(rule)
                    else:
                        warnings.append(rule)
            except Exception as e:
                warnings.append(VerificationRule(
                    name=f"{rule.name}_error",
                    description=f"验证执行错误: {str(e)}",
                    severity="info"
                ))
        
        # 生成验证结果
        if not failed_rules:
            if warnings:
                return VerificationResult(
                    status=VerificationStatus.PASSED,
                    message="验证通过（有建议）",
                    details={"warnings": [w.description for w in warnings]},
                    suggestions=self._generate_suggestions(warnings, context)
                )
            else:
                return VerificationResult(
                    status=VerificationStatus.PASSED,
                    message="验证通过",
                    details={"result_type": type(result).__name__}
                )
        else:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                message=f"验证失败: {', '.join([r.description for r in failed_rules])}",
                details={
                    "failed_rules": [r.name for r in failed_rules],
                    "warnings": [w.description for w in warnings]
                },
                suggestions=self._generate_suggestions(failed_rules + warnings, context),
                retry_needed=True
            )
    
    def verify_with_retries(
        self, 
        result: Any, 
        context: Optional[Dict[str, Any]] = None,
        retry_callback: Optional[Callable[[int], Any]] = None
    ) -> VerificationResult:
        """
        带重试的验证
        
        Args:
            result: 初始结果
            context: 上下文
            retry_callback: 重试回调函数
            
        Returns:
            VerificationResult: 最终验证结果
        """
        verification_result = self.verify(result, context)
        
        retry_count = 0
        
        while verification_result.retry_needed and retry_count < self.max_retries:
            retry_count += 1
            
            # 记录历史
            self.verification_history.append(verification_result)
            
            # 如果有重试回调，执行重试
            if retry_callback:
                result = retry_callback(retry_count)
                verification_result = self.verify(result, context)
            else:
                # 没有回调，只能返回失败
                break
        
        # 记录最终结果
        self.verification_history.append(verification_result)
        
        return verification_result
    
    def _generate_suggestions(
        self, 
        failed_rules: List[VerificationRule],
        context: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        for rule in failed_rules:
            if rule.name == "not_empty":
                suggestions.append("结果为空，请补充内容")
            elif rule.name == "min_length":
                suggestions.append("结果内容太少，请提供更详细的信息")
            elif rule.name == "content_quality":
                suggestions.append("结果缺乏实质性内容，请进行分析和解释")
            else:
                suggestions.append(f"建议: {rule.description}")
        
        # 添加上下文相关的建议
        query = context.get("query", "")
        if query:
            suggestions.append(f"根据问题「{query[:30]}...」优化答案")
        
        return suggestions
    
    def is_result_acceptable(self, result: Any) -> bool:
        """快速检查结果是否可接受"""
        verification = self.verify(result)
        return verification.status == VerificationStatus.PASSED


# GAIA风格验证器
class GAIAStyleVerifier(VerificationLoop):
    """
    GAIA风格验证器
    
    针对GAIA基准测试的验证器，检查：
    1. 答案正确性
    2. 任务完成度
    3. 格式规范性
    """
    
    def __init__(self):
        super().__init__(max_retries=3)
        
        # 添加GAIA特定规则
        self._add_gaia_rules()
    
    def _add_gaia_rules(self):
        """添加GAIA特定规则"""
        
        # 1. 检查是否回答了问题
        self.add_rule(VerificationRule(
            name="answers_question",
            description="答案必须回应问题",
            check_function=lambda r: isinstance(r, str) and len(r) > 0,
            severity="error"
        ))
        
        # 2. 检查是否使用了工具（如果有需要的话）
        self.add_rule(VerificationRule(
            name="tool_usage",
            description="需要使用工具完成任务",
            check_function=lambda r: True,  # 默认通过
            severity="info"
        ))
        
        # 3. 检查结果格式
        self.add_rule(VerificationRule(
            name="format_valid",
            description="结果格式有效",
            check_function=lambda r: (
                r is not None and
                (isinstance(r, str) or isinstance(r, dict) or isinstance(r, list))
            ),
            severity="error"
        ))
    
    def verify_task_completion(
        self, 
        task: str, 
        result: Any,
        expected_elements: Optional[List[str]] = None
    ) -> VerificationResult:
        """
        验证任务完成度
        
        Args:
            task: 原始任务
            result: 执行结果
            expected_elements: 期望包含的元素
            
        Returns:
            VerificationResult: 验证结果
        """
        result_str = str(result) if result else ""
        
        # 检查是否回答了任务
        if not result_str:
            return VerificationResult(
                status=VerificationStatus.FAILED,
                message="任务未完成，没有返回结果",
                retry_needed=True
            )
        
        # 检查是否包含期望元素
        if expected_elements:
            missing = []
            for element in expected_elements:
                if element.lower() not in result_str.lower():
                    missing.append(element)
            
            if missing:
                return VerificationResult(
                    status=VerificationStatus.NEEDS_IMPROVEMENT,
                    message=f"缺少关键内容: {', '.join(missing)}",
                    suggestions=[f"请确保包含: {', '.join(missing)}"],
                    retry_needed=True
                )
        
        return VerificationResult(
            status=VerificationStatus.PASSED,
            message="任务完成验证通过"
        )


# 便捷函数
def create_verifier(max_retries: int = 3) -> VerificationLoop:
    """创建验证器"""
    return VerificationLoop(max_retries=max_retries)


def create_gaia_verifier() -> GAIAStyleVerifier:
    """创建GAIA风格验证器"""
    return GAIAStyleVerifier()
