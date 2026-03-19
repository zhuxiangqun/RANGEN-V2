#!/usr/bin/env python3
"""
Verdict - SOP学习质量控制的核心组件

Verdict 是一个证据包，用于验证执行结果的质量。
只有包含完整证据的 Verdict 才能触发 SOP 学习，以防止坏模式被固化。

借鉴 GenericAgent 的种子哲学和质量控制理念：
- Verdict 要求提供完整的推理链
- 验证结果必须有明确的证据支持
- 避免仅凭 "success=True" 就学习不确定的模式
"""

import hashlib
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class VerdictLevel(str, Enum):
    """Verdict 质量等级"""
    REJECTED = "rejected"              # 不完整/无效的 Verdict
    INCOMPLETE = "incomplete"          # 缺少部分证据
    PARTIAL = "partial"                # 部分验证通过
    COMPLETE = "complete"              # 完整的 Verdict
    HIGH_QUALITY = "high_quality"      # 高质量 Verdict


class EvidenceType(str, Enum):
    """证据类型"""
    REASONING_STEP = "reasoning_step"     # 推理步骤
    VALIDATION_RESULT = "validation_result"  # 验证结果
    OUTPUT_VERIFICATION = "output_verification"  # 输出验证
    CONTEXT_PRESERVATION = "context_preservation"  # 上下文保留
    ERROR_HANDLING = "error_handling"     # 错误处理
    LOGGING = "logging"                   # 日志记录


@dataclass
class ReasoningStep:
    """推理步骤 - 记录 AI 的思考过程"""
    step_id: str
    thought: str                          # 思考内容
    action: Optional[str] = None           # 采取的行动
    observation: Optional[str] = None      # 观察结果
    confidence: float = 1.0               # 置信度 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.step_id:
            content = f"{self.thought}_{time.time()}"
            self.step_id = hashlib.md5(content.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReasoningStep":
        return cls(**data)


@dataclass
class ValidationResult:
    """验证结果 - 记录验证检查的结果"""
    check_name: str                        # 检查名称
    passed: bool                           # 是否通过
    expected: Optional[Any] = None         # 期望值
    actual: Optional[Any] = None           # 实际值
    message: str = ""                      # 说明信息
    severity: str = "info"                 # 严重程度: info, warning, error
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ValidationResult":
        return cls(**data)


@dataclass
class OutputVerification:
    """输出验证 - 验证执行输出是否正确"""
    output_type: str                       # 输出类型
    schema_valid: bool                     # 是否符合 schema
    value_check: Optional[Dict[str, Any]] = None  # 值检查结果
    quality_score: float = 0.0             # 质量分数 0-1
    issues: List[str] = field(default_factory=list)  # 发现的问题
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OutputVerification":
        return cls(**data)


@dataclass
class ContextPreservation:
    """上下文保留 - 验证执行过程中上下文是否被正确保留"""
    context_key: str                       # 上下文键
    preserved: bool                         # 是否被保留
    original_value: Optional[Any] = None    # 原始值
    final_value: Optional[Any] = None       # 最终值
    transformation_applied: str = ""        # 应用了何种转换
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextPreservation":
        return cls(**data)


@dataclass
class Verdict:
    """
    Verdict - 执行结果的完整证据包
    
    Verdict 是 SOP 学习的门票。只有包含完整证据的 Verdict 才能触发学习。
    
    证据包包含：
    1. reasoning_steps - 推理链，记录 AI 的思考过程
    2. validation_results - 验证结果，证明输出是正确的
    3. output_verification - 输出验证，验证输出符合预期
    4. context_preservation - 上下文保留，验证关键信息没有丢失
    """
    verdict_id: str
    execution_id: str                       # 关联的执行记录 ID
    created_at: float = field(default_factory=time.time)
    
    # 核心证据
    reasoning_steps: List[ReasoningStep] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    output_verification: Optional[OutputVerification] = None
    context_preservation: List[ContextPreservation] = field(default_factory=list)
    
    # 质量评估
    confidence_score: float = 0.0          # 总体置信度 0-1
    quality_level: VerdictLevel = VerdictLevel.REJECTED
    
    # 元数据
    task_description: str = ""
    executor_info: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.verdict_id:
            content = f"{self.execution_id}_{self.created_at}"
            self.verdict_id = hashlib.md5(content.encode()).hexdigest()[:16]
    
    def add_reasoning_step(self, thought: str, action: Optional[str] = None,
                          observation: Optional[str] = None, confidence: float = 1.0) -> ReasoningStep:
        """添加推理步骤"""
        step = ReasoningStep(
            step_id="",
            thought=thought,
            action=action,
            observation=observation,
            confidence=confidence
        )
        self.reasoning_steps.append(step)
        return step
    
    def add_validation(self, check_name: str, passed: bool,
                      expected: Any = None, actual: Any = None,
                      message: str = "", severity: str = "info") -> ValidationResult:
        """添加验证结果"""
        result = ValidationResult(
            check_name=check_name,
            passed=passed,
            expected=expected,
            actual=actual,
            message=message,
            severity=severity
        )
        self.validation_results.append(result)
        return result
    
    def set_output_verification(self, output_type: str, schema_valid: bool = True,
                              quality_score: float = 0.0) -> OutputVerification:
        """设置输出验证"""
        self.output_verification = OutputVerification(
            output_type=output_type,
            schema_valid=schema_valid,
            quality_score=quality_score
        )
        return self.output_verification
    
    def add_context_preservation(self, key: str, preserved: bool,
                                original: Any = None, final: Any = None) -> ContextPreservation:
        """添加上下文保留记录"""
        preservation = ContextPreservation(
            context_key=key,
            preserved=preserved,
            original_value=original,
            final_value=final
        )
        self.context_preservation.append(preservation)
        return preservation
    
    def is_complete(self) -> bool:
        """检查 Verdict 是否完整"""
        return (
            len(self.reasoning_steps) > 0 and
            len(self.validation_results) > 0 and
            self.output_verification is not None
        )
    
    def is_valid(self) -> bool:
        """检查 Verdict 是否有效（可触发学习）"""
        return (
            self.is_complete() and
            self.quality_level in [VerdictLevel.COMPLETE, VerdictLevel.HIGH_QUALITY] and
            self.confidence_score >= 0.7
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """获取 Verdict 摘要"""
        validation_passed = sum(1 for v in self.validation_results if v.passed)
        validation_total = len(self.validation_results)
        
        return {
            "verdict_id": self.verdict_id,
            "execution_id": self.execution_id,
            "quality_level": self.quality_level.value,
            "confidence_score": self.confidence_score,
            "is_complete": self.is_complete(),
            "is_valid": self.is_valid(),
            "reasoning_steps_count": len(self.reasoning_steps),
            "validation_passed": f"{validation_passed}/{validation_total}",
            "has_output_verification": self.output_verification is not None,
            "context_preserved_count": len(self.context_preservation),
            "created_at": datetime.fromtimestamp(self.created_at).isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 转换枚举
        data["quality_level"] = self.quality_level.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Verdict":
        """从字典创建"""
        # 处理枚举转换
        if "quality_level" in data and isinstance(data["quality_level"], str):
            data["quality_level"] = VerdictLevel(data["quality_level"])
        return cls(**data)


class VerdictValidator:
    """
    Verdict 验证器 - 验证 Verdict 是否包含完整证据
    
    验证规则：
    1. 推理步骤必须存在且有实际内容
    2. 验证结果必须有明确的通过/失败
    3. 输出验证必须存在
    4. 置信度必须达到阈值
    """
    
    def __init__(self, min_confidence: float = 0.7, min_reasoning_steps: int = 1,
                 min_validation_results: int = 1):
        self.logger = logging.getLogger(__name__)
        
        # 验证阈值
        self.min_confidence = min_confidence
        self.min_reasoning_steps = min_reasoning_steps
        self.min_validation_results = min_validation_results
    
    def validate(self, verdict: Verdict) -> Tuple[bool, List[str]]:
        """
        验证 Verdict 是否完整
        
        Args:
            verdict: 要验证的 Verdict
            
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # 1. 检查推理步骤
        if not verdict.reasoning_steps:
            errors.append("缺少推理步骤 (reasoning_steps)")
        elif len(verdict.reasoning_steps) < self.min_reasoning_steps:
            errors.append(f"推理步骤不足 (需要至少 {self.min_reasoning_steps} 个)")
        else:
            # 检查每个推理步骤是否有实际内容
            for i, step in enumerate(verdict.reasoning_steps):
                if not step.thought or len(step.thought.strip()) < 10:
                    errors.append(f"推理步骤 {i+1} 内容过短或为空")
        
        # 2. 检查验证结果
        if not verdict.validation_results:
            errors.append("缺少验证结果 (validation_results)")
        elif len(verdict.validation_results) < self.min_validation_results:
            errors.append(f"验证结果不足 (需要至少 {self.min_validation_results} 个)")
        else:
            # 检查是否有明确的验证
            has_explicit_validation = any(
                v.passed and v.check_name for v in verdict.validation_results
            )
            if not has_explicit_validation:
                errors.append("验证结果缺少明确的检查名称或通过状态")
        
        # 3. 检查输出验证
        if verdict.output_verification is None:
            errors.append("缺少输出验证 (output_verification)")
        elif not verdict.output_verification.schema_valid:
            errors.append("输出不符合预期 schema")
        
        # 4. 检查置信度
        if verdict.confidence_score < self.min_confidence:
            errors.append(f"置信度过低 ({verdict.confidence_score:.2f} < {self.min_confidence})")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.logger.debug(f"Verdict {verdict.verdict_id} 验证通过")
        else:
            self.logger.warning(f"Verdict {verdict.verdict_id} 验证失败: {errors}")
        
        return is_valid, errors
    
    def assess_quality_level(self, verdict: Verdict) -> VerdictLevel:
        """
        评估 Verdict 的质量等级
        
        Args:
            verdict: 要评估的 Verdict
            
        Returns:
            VerdictLevel
        """
        score = 0.0
        max_score = 0.0
        
        # 推理步骤评分 (30%)
        max_score += 0.3
        if verdict.reasoning_steps:
            step_count = len(verdict.reasoning_steps)
            # 1-3 个步骤得 0.1-0.2，3+ 得 0.3
            score += min(0.3, 0.1 * step_count)
        
        # 验证结果评分 (30%)
        max_score += 0.3
        if verdict.validation_results:
            passed_count = sum(1 for v in verdict.validation_results if v.passed)
            total_count = len(verdict.validation_results)
            if total_count > 0:
                score += 0.3 * (passed_count / total_count)
        
        # 输出验证评分 (20%)
        max_score += 0.2
        if verdict.output_verification:
            score += 0.2 * verdict.output_verification.quality_score
        
        # 上下文保留评分 (10%)
        max_score += 0.1
        if verdict.context_preservation:
            preserved_count = sum(1 for c in verdict.context_preservation if c.preserved)
            total_count = len(verdict.context_preservation)
            if total_count > 0:
                score += 0.1 * (preserved_count / total_count)
        
        # 置信度评分 (10%)
        max_score += 0.1
        score += 0.1 * verdict.confidence_score
        
        # 计算归一化分数
        normalized_score = score / max_score if max_score > 0 else 0.0
        
        # 确定质量等级
        if normalized_score >= 0.9:
            return VerdictLevel.HIGH_QUALITY
        elif normalized_score >= 0.7:
            return VerdictLevel.COMPLETE
        elif normalized_score >= 0.5:
            return VerdictLevel.PARTIAL
        elif normalized_score >= 0.3:
            return VerdictLevel.INCOMPLETE
        else:
            return VerdictLevel.REJECTED
    
    def check_reasoning_quality(self, reasoning_steps: List[ReasoningStep]) -> float:
        """
        检查推理链的质量
        
        Args:
            reasoning_steps: 推理步骤列表
            
        Returns:
            质量分数 0-1
        """
        if not reasoning_steps:
            return 0.0
        
        quality = 0.0
        
        # 1. 步骤数量 (20%)
        step_count = len(reasoning_steps)
        quality += min(0.2, 0.05 * step_count)
        
        # 2. 步骤内容长度 (30%)
        total_length = sum(len(step.thought or "") for step in reasoning_steps)
        avg_length = total_length / len(reasoning_steps)
        if avg_length > 50:
            quality += 0.3
        elif avg_length > 20:
            quality += 0.2
        else:
            quality += 0.1
        
        # 3. 步骤之间的连贯性 (30%)
        # 检查是否有 action/observation 形成了完整的 ReAct 循环
        has_action = any(step.action for step in reasoning_steps)
        has_observation = any(step.observation for step in reasoning_steps)
        if has_action and has_observation:
            quality += 0.3
        elif has_action or has_observation:
            quality += 0.15
        
        # 4. 置信度一致性 (20%)
        confidences = [step.confidence for step in reasoning_steps]
        if confidences:
            avg_confidence = sum(confidences) / len(confidences)
            # 如果大部分步骤置信度高于 0.7，认为质量较高
            high_conf_count = sum(1 for c in confidences if c >= 0.7)
            if high_conf_count / len(confidences) >= 0.7:
                quality += 0.2
        
        return min(quality, 1.0)
    
    def is_evidence_complete(self, evidence: Dict[str, Any]) -> bool:
        """
        检查证据包是否完整
        
        Args:
            evidence: 证据字典
            
        Returns:
            是否完整
        """
        required_keys = ["reasoning_steps", "validation_results", "output_verification"]
        
        for key in required_keys:
            if key not in evidence:
                return False
            if key == "reasoning_steps" and not evidence[key]:
                return False
            if key == "validation_results" and not evidence[key]:
                return False
        
        return True


# 全局验证器实例
_verdict_validator: Optional[VerdictValidator] = None


def get_verdict_validator() -> VerdictValidator:
    """获取 Verdict 验证器实例"""
    global _verdict_validator
    if _verdict_validator is None:
        _verdict_validator = VerdictValidator()
    return _verdict_validator


def create_minimal_verdict(execution_id: str, task_description: str = "",
                           reasoning: str = "", passed: bool = True) -> Verdict:
    """
    创建最小化的 Verdict（用于快速测试或简单场景）
    
    注意：最小化的 Verdict 可能无法通过验证，建议使用完整证据。
    """
    verdict = Verdict(
        verdict_id="",
        execution_id=execution_id,
        task_description=task_description
    )
    
    # 添加一个推理步骤
    if reasoning:
        verdict.add_reasoning_step(reasoning)
    
    # 添加一个验证结果
    verdict.add_validation(
        check_name="success_check",
        passed=passed,
        message="Task completed" if passed else "Task failed"
    )
    
    # 添加输出验证
    verdict.set_output_verification(
        output_type="result",
        schema_valid=passed,
        quality_score=1.0 if passed else 0.0
    )
    
    # 评估质量等级
    validator = get_verdict_validator()
    verdict.quality_level = validator.assess_quality_level(verdict)
    verdict.confidence_score = verdict.quality_level.value in ["complete", "high_quality"] and 0.8 or 0.5
    
    return verdict
