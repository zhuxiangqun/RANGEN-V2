#!/usr/bin/env python3
"""
过程奖励服务 - OR-PRM概念实现
Process Reward Service - OR-PRM Concept Implementation

基于ICLR 2026论文OR-PRM: A Process Reward Model for Algorithmic Problem in Operations Research
提供步骤级推理验证、结构化反馈和约束满足检查

核心功能：
1. 步骤级验证：验证每个推理步骤的正确性
2. 结构化反馈：不仅返回分数，还提供错误描述和修正建议
3. 约束满足检查：验证解决方案是否满足约束条件
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import re

logger = logging.getLogger(__name__)


class StepValidationStatus(Enum):
    """推理步骤验证状态"""
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class ErrorType(Enum):
    """错误类型分类"""
    VARIABLE_DEFINITION = "variable_definition"
    OBJECTIVE_FUNCTION = "objective_function"
    CONSTRAINT_VIOLATION = "constraint_violation"
    LOGIC_ERROR = "logic_error"
    COMPUTATION_ERROR = "computation_error"
    FORMAT_ERROR = "format_error"
    REASONING_ERROR = "reasoning_error"


@dataclass
class StepValidation:
    """单步验证结果"""
    step_id: int
    step_content: str
    status: StepValidationStatus
    confidence: float
    error_type: Optional[ErrorType] = None
    error_description: Optional[str] = None
    correction_suggestion: Optional[str] = None
    related_constraints: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "step_content": self.step_content,
            "status": self.status.value,
            "confidence": self.confidence,
            "error_type": self.error_type.value if self.error_type else None,
            "error_description": self.error_description,
            "correction_suggestion": self.correction_suggestion,
            "related_constraints": self.related_constraints
        }


@dataclass
class ProcessRewardResult:
    """过程奖励模型结果"""
    overall_confidence: float
    step_validations: List[StepValidation]
    constraint_satisfactions: Dict[str, bool]
    is_valid: bool
    feedback: str
    improvement_suggestions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_confidence": self.overall_confidence,
            "step_validations": [sv.to_dict() for sv in self.step_validations],
            "constraint_satisfactions": self.constraint_satisfactions,
            "is_valid": self.is_valid,
            "feedback": self.feedback,
            "improvement_suggestions": self.improvement_suggestions
        }


class ReasoningStepValidator(ABC):
    """推理步骤验证器基类"""
    
    @abstractmethod
    def validate_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> StepValidation:
        """验证单个推理步骤"""
        pass
    
    @abstractmethod
    def get_step_type(self) -> str:
        """获取步骤类型"""
        pass


class VariableDefinitionValidator(ReasoningStepValidator):
    """变量定义验证器"""
    
    def get_step_type(self) -> str:
        return "variable_definition"
    
    def validate_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> StepValidation:
        """验证变量定义是否正确"""
        step_id = step.get("step_id", 0)
        content = step.get("content", "")
        
        # 检查变量定义模式
        var_pattern = r'(\w+)\s*=\s*(.+?)(?:;|$)'
        matches = re.findall(var_pattern, content)
        
        if not matches:
            return StepValidation(
                step_id=step_id,
                step_content=content,
                status=StepValidationStatus.UNKNOWN,
                confidence=0.5,
                error_type=ErrorType.VARIABLE_DEFINITION,
                error_description="未找到变量定义",
                correction_suggestion="请明确定义变量"
            )
        
        # 验证变量名合法性
        for var_name, var_value in matches:
            if not var_name.isidentifier():
                return StepValidation(
                    step_id=step_id,
                    step_content=content,
                    status=StepValidationStatus.INCORRECT,
                    confidence=0.3,
                    error_type=ErrorType.VARIABLE_DEFINITION,
                    error_description=f"变量名 '{var_name}' 不合法",
                    correction_suggestion="使用合法的Python标识符"
                )
        
        return StepValidation(
            step_id=step_id,
            step_content=content,
            status=StepValidationStatus.CORRECT,
            confidence=0.9,
            related_constraints=["variable_naming", "type_consistency"]
        )


class ObjectiveFunctionValidator(ReasoningStepValidator):
    """目标函数验证器"""
    
    def get_step_type(self) -> str:
        return "objective_function"
    
    def validate_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> StepValidation:
        """验证目标函数"""
        step_id = step.get("step_id", 0)
        content = step.get("content", "")
        
        # 检查目标函数关键词
        objective_keywords = ["minimize", "maximize", "min", "max", "优化", "目标"]
        has_objective = any(kw in content.lower() for kw in objective_keywords)
        
        if not has_objective:
            return StepValidation(
                step_id=step_id,
                step_content=content,
                status=StepValidationStatus.UNKNOWN,
                confidence=0.5,
                error_type=ErrorType.OBJECTIVE_FUNCTION,
                error_description="未找到目标函数定义",
                correction_suggestion="请明确目标函数（最小化/最大化）"
            )
        
        return StepValidation(
            step_id=step_id,
            step_content=content,
            status=StepValidationStatus.CORRECT,
            confidence=0.85,
            related_constraints=["objective_clarity", "optimization_direction"]
        )


class ConstraintValidator(ReasoningStepValidator):
    """约束条件验证器"""
    
    def __init__(self):
        self.constraints: List[Dict[str, Any]] = []
    
    def get_step_type(self) -> str:
        return "constraint"
    
    def set_constraints(self, constraints: List[Dict[str, Any]]):
        """设置约束条件"""
        self.constraints = constraints
    
    def validate_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> StepValidation:
        """验证约束满足情况"""
        step_id = step.get("step_id", 0)
        content = step.get("content", "")
        
        # 提取步骤中涉及的约束
        violated_constraints = []
        satisfied_constraints = []
        
        for constraint in self.constraints:
            constraint_text = constraint.get("text", "")
            constraint_type = constraint.get("type", "")
            
            # 简单检查：约束关键词是否出现在步骤中
            if any(kw in content for kw in constraint_text.split()):
                # 进一步检查是否被满足
                if self._check_constraint_satisfaction(content, constraint):
                    satisfied_constraints.append(constraint_text)
                else:
                    violated_constraints.append(constraint_text)
        
        if violated_constraints:
            return StepValidation(
                step_id=step_id,
                step_content=content,
                status=StepValidationStatus.INCORRECT,
                confidence=0.4,
                error_type=ErrorType.CONSTRAINT_VIOLATION,
                error_description=f"违反约束: {', '.join(violated_constraints)}",
                correction_suggestion="请修正以满足约束条件",
                related_constraints=violated_constraints
            )
        
        return StepValidation(
            step_id=step_id,
            step_content=content,
            status=StepValidationStatus.CORRECT,
            confidence=0.9 if satisfied_constraints else 0.7,
            related_constraints=satisfied_constraints
        )
    
    def _check_constraint_satisfaction(self, content: str, constraint: Dict[str, Any]) -> bool:
        """检查约束是否被满足"""
        constraint_type = constraint.get("type", "")
        
        # 简化实现：基于约束类型的启发式检查
        if constraint_type == "equality":
            return "=" in content or "==" in content
        elif constraint_type == "inequality":
            return any(op in content for op in [">=", "<=", ">", "<"])
        elif constraint_type == "boundary":
            return any(kw in content for kw in ["范围", "区间", "bound", "limit"])
        
        return True  # 默认认为满足


class LogicValidator(ReasoningStepValidator):
    """逻辑验证器"""
    
    def get_step_type(self) -> str:
        return "logic"
    
    def validate_step(self, step: Dict[str, Any], context: Dict[str, Any]) -> StepValidation:
        """验证推理逻辑"""
        step_id = step.get("step_id", 0)
        content = step.get("content", "")
        previous_steps = context.get("previous_steps", [])
        
        # 检查逻辑连接词
        logic_connectors = ["因此", "所以", "因为", "hence", "therefore", "because", "thus"]
        has_connector = any(conn in content for conn in logic_connectors)
        
        # 检查是否引用了前序步骤
        references_prev = any(
            str(prev.get("step_id")) in content 
            for prev in previous_steps
        )
        
        if has_connector and references_prev:
            return StepValidation(
                step_id=step_id,
                step_content=content,
                status=StepValidationStatus.CORRECT,
                confidence=0.85
            )
        elif not references_prev and len(previous_steps) > 0:
            return StepValidation(
                step_id=step_id,
                step_content=content,
                status=StepValidationStatus.PARTIAL,
                confidence=0.6,
                error_type=ErrorType.LOGIC_ERROR,
                error_description="推理未明确引用前序步骤",
                correction_suggestion="请在推理中明确引用前序步骤"
            )
        
        return StepValidation(
            step_id=step_id,
            step_content=content,
            status=StepValidationStatus.UNKNOWN,
            confidence=0.5
        )


class ProcessRewardService:
    """
    过程奖励服务
    
    提供类似于OR-PRM的过程监督功能：
    1. 步骤级验证
    2. 结构化反馈
    3. 约束满足检查
    4. DPO风格的偏好优化
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化验证器
        self.validators: Dict[str, ReasoningStepValidator] = {
            "variable_definition": VariableDefinitionValidator(),
            "objective_function": ObjectiveFunctionValidator(),
            "constraint": ConstraintValidator(),
            "logic": LogicValidator()
        }
        
        # 置信度阈值
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.6
        )
        self.high_confidence = self.config.get("high_confidence", 0.8)
        
        # 约束列表
        self.constraints: List[Dict[str, Any]] = []
        
        # 验证历史
        self.validation_history: List[ProcessRewardResult] = []
        
        logger.info(
            f"过程奖励服务初始化完成: 阈值={self.confidence_threshold}"
        )
    
    def set_constraints(self, constraints: List[Dict[str, Any]]):
        """设置约束条件"""
        self.constraints = constraints
        # 更新约束验证器
        constraint_validator = self.validators.get("constraint")
        if isinstance(constraint_validator, ConstraintValidator):
            constraint_validator.set_constraints(constraints)
    
    def validate_reasoning_process(
        self, 
        reasoning_steps: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> ProcessRewardResult:
        """
        验证推理过程
        
        Args:
            reasoning_steps: 推理步骤列表
            context: 上下文信息
            
        Returns:
            ProcessRewardResult: 验证结果
        """
        context = context or {}
        context["previous_steps"] = []
        
        step_validations: List[StepValidation] = []
        constraint_satisfactions: Dict[str, bool] = {}
        
        # 逐步验证
        for i, step in enumerate(reasoning_steps):
            step["step_id"] = i
            step_type = step.get("type", "logic")
            
            # 选择合适的验证器
            validator = self.validators.get(
                step_type, 
                self.validators["logic"]
            )
            
            # 验证步骤
            validation = validator.validate_step(step, context)
            step_validations.append(validation)
            
            # 更新上下文
            context["previous_steps"].append(step)
        
        # 统计约束满足情况
        for constraint in self.constraints:
            constraint_text = constraint.get("text", "")
            satisfied = any(
                constraint_text in val.related_constraints 
                and val.status == StepValidationStatus.CORRECT
                for val in step_validations
            )
            constraint_satisfactions[constraint_text] = satisfied
        
        # 计算整体置信度
        overall_confidence = self._calculate_overall_confidence(
            step_validations, 
            constraint_satisfactions
        )
        
        # 判断是否有效
        is_valid = overall_confidence >= self.confidence_threshold
        
        # 生成反馈
        feedback = self._generate_feedback(
            overall_confidence, 
            step_validations,
            constraint_satisfactions
        )
        
        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions(
            step_validations,
            constraint_satisfactions
        )
        
        result = ProcessRewardResult(
            overall_confidence=overall_confidence,
            step_validations=step_validations,
            constraint_satisfactions=constraint_satisfactions,
            is_valid=is_valid,
            feedback=feedback,
            improvement_suggestions=improvement_suggestions
        )
        
        # 记录历史
        self.validation_history.append(result)
        
        return result
    
    def _calculate_overall_confidence(
        self,
        step_validations: List[StepValidation],
        constraint_satisfactions: Dict[str, bool]
    ) -> float:
        """计算整体置信度"""
        if not step_validations:
            return 0.0
        
        # 步骤置信度加权平均
        step_confidences = [sv.confidence for sv in step_validations]
        avg_step_confidence = sum(step_confidences) / len(step_confidences)
        
        # 约束满足率
        if constraint_satisfactions:
            constraint_score = sum(
                1 for v in constraint_satisfactions.values() if v
            ) / len(constraint_satisfactions)
        else:
            constraint_score = 1.0
        
        # 综合置信度
        overall = (
            avg_step_confidence * 0.6 + 
            constraint_score * 0.4
        )
        
        return round(overall, 3)
    
    def _generate_feedback(
        self,
        overall_confidence: float,
        step_validations: List[StepValidation],
        constraint_satisfactions: Dict[str, bool]
    ) -> str:
        """生成结构化反馈"""
        if overall_confidence >= self.high_confidence:
            return "推理过程正确，置信度高"
        elif overall_confidence >= self.confidence_threshold:
            return "推理过程基本正确，但存在一些问题需要关注"
        else:
            # 收集错误信息
            errors = [
                f"步骤{sv.step_id}: {sv.error_description}"
                for sv in step_validations
                if sv.status == StepValidationStatus.INCORRECT
            ]
            
            violated = [
                f"'{c}'"
                for c, v in constraint_satisfactions.items()
                if not v
            ]
            
            feedback_parts = ["推理过程存在问题:"]
            if errors:
                feedback_parts.append(" - " + "; ".join(errors[:3]))
            if violated:
                feedback_parts.append(f" - 违反约束: {', '.join(violated)}")
            
            return "\n".join(feedback_parts)
    
    def _generate_improvement_suggestions(
        self,
        step_validations: List[StepValidation],
        constraint_satisfactions: Dict[str, bool]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于错误步骤生成建议
        incorrect_steps = [
            sv for sv in step_validations
            if sv.status == StepValidationStatus.INCORRECT
        ]
        
        for sv in incorrect_steps:
            if sv.correction_suggestion:
                suggestions.append(sv.correction_suggestion)
        
        # 基于约束违反生成建议
        violated_constraints = [
            c for c, v in constraint_satisfactions.items()
            if not v
        ]
        
        if violated_constraints:
            suggestions.append(
                f"请检查并满足以下约束: {', '.join(violated_constraints[:3])}"
            )
        
        # 基于部分正确步骤生成建议
        partial_steps = [
            sv for sv in step_validations
            if sv.status == StepValidationStatus.PARTIAL
        ]
        
        for sv in partial_steps:
            if sv.correction_suggestion:
                suggestions.append(
                    f"步骤{sv.step_id}建议: {sv.correction_suggestion}"
                )
        
        return suggestions[:5]  # 最多5条建议
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证统计摘要"""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0
            }
        
        total = len(self.validation_history)
        successes = sum(1 for r in self.validation_history if r.is_valid)
        avg_confidence = sum(
            r.overall_confidence for r in self.validation_history
        ) / total
        
        return {
            "total_validations": total,
            "success_rate": round(successes / total, 3),
            "avg_confidence": round(avg_confidence, 3),
            "recent_results": [
                r.to_dict() for r in self.validation_history[-5:]
            ]
        }
    
    def reset_history(self):
        """重置验证历史"""
        self.validation_history = []
        logger.info("验证历史已重置")


# 全局单例
_process_reward_service: Optional[ProcessRewardService] = None


def get_process_reward_service(
    config: Optional[Dict[str, Any]] = None
) -> ProcessRewardService:
    """获取过程奖励服务单例"""
    global _process_reward_service
    
    if _process_reward_service is None:
        _process_reward_service = ProcessRewardService(config)
    
    return _process_reward_service


def create_process_reward_service(
    config: Optional[Dict[str, Any]] = None
) -> ProcessRewardService:
    """创建新的过程奖励服务实例"""
    return ProcessRewardService(config)
