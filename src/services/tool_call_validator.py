#!/usr/bin/env python3
"""
工具调用验证器 - 结合OR-PRM概念的步骤级验证
Tool Call Validator - Step-by-Step Validation with OR-PRM Concepts

增强工具调用的可靠性，提供：
1. 调用前参数验证
2. 调用后结果验证
3. 约束满足检查
4. 错误传播检测
"""

import logging
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import re
import json

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """验证级别"""
    NONE = "none"
    BASIC = "basic"
    STRICT = "strict"
    PARANOID = "paranoid"


class ParameterValidationStatus(Enum):
    """参数验证状态"""
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"
    UNKNOWN = "unknown"


class ToolCallValidationResult:
    """工具调用验证结果"""
    
    def __init__(
        self,
        is_valid: bool,
        validation_level: ValidationLevel,
        confidence: float,
        pre_validation: Optional[Dict[str, Any]] = None,
        post_validation: Optional[Dict[str, Any]] = None,
        constraint_checks: Optional[Dict[str, bool]] = None,
        error_details: Optional[List[Dict[str, Any]]] = None,
        suggestions: Optional[List[str]] = None
    ):
        self.is_valid = is_valid
        self.validation_level = validation_level
        self.confidence = confidence
        self.pre_validation = pre_validation or {}
        self.post_validation = post_validation or {}
        self.constraint_checks = constraint_checks or {}
        self.error_details = error_details or []
        self.suggestions = suggestions or []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "validation_level": self.validation_level.value,
            "confidence": self.confidence,
            "pre_validation": self.pre_validation,
            "post_validation": self.post_validation,
            "constraint_checks": self.constraint_checks,
            "error_details": self.error_details,
            "suggestions": self.suggestions
        }
    
    def __bool__(self) -> bool:
        return self.is_valid


@dataclass
class ParameterRule:
    """参数规则定义"""
    name: str
    param_type: str  # string, number, boolean, array, object
    required: bool = False
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    enum_values: Optional[List[Any]] = None
    custom_validator: Optional[Callable] = None
    
    def validate(self, value: Any) -> ParameterValidationStatus:
        """验证参数值"""
        # 必需检查
        if value is None or value == "":
            if self.required:
                return ParameterValidationStatus.INVALID
            return ParameterValidationStatus.UNKNOWN
        
        # 类型检查
        if self.param_type == "string":
            if not isinstance(value, str):
                return ParameterValidationStatus.INVALID
            # 模式检查
            if self.pattern and not re.match(self.pattern, value):
                return ParameterValidationStatus.INVALID
            # 枚举检查
            if self.enum_values and value not in self.enum_values:
                return ParameterValidationStatus.INVALID
        
        elif self.param_type == "number":
            if not isinstance(value, (int, float)):
                return ParameterValidationStatus.INVALID
            # 范围检查
            if self.min_value is not None and value < self.min_value:
                return ParameterValidationStatus.INVALID
            if self.max_value is not None and value > self.max_value:
                return ParameterValidationStatus.INVALID
        
        elif self.param_type == "boolean":
            if not isinstance(value, bool):
                return ParameterValidationStatus.INVALID
        
        elif self.param_type == "array":
            if not isinstance(value, list):
                return ParameterValidationStatus.INVALID
        
        elif self.param_type == "object":
            if not isinstance(value, dict):
                return ParameterValidationStatus.INVALID
        
        # 自定义验证
        if self.custom_validator:
            try:
                if not self.custom_validator(value):
                    return ParameterValidationStatus.WARNING
            except Exception:
                return ParameterValidationStatus.WARNING
        
        return ParameterValidationStatus.VALID


@dataclass
class ToolConstraint:
    """工具约束定义"""
    name: str
    description: str
    check_function: Callable[[Any], bool]
    severity: str = "error"  # error, warning, info
    
    def check(self, value: Any) -> bool:
        """检查约束是否满足"""
        try:
            return self.check_function(value)
        except Exception as e:
            logger.warning(f"约束检查失败 {self.name}: {e}")
            return False


class ToolCallValidator:
    """
    工具调用验证器
    
    提供类似于OR-PRM的工具调用步骤验证：
    1. 调用前：参数验证、依赖检查
    2. 调用后：结果验证、约束满足
    3. 错误检测：异常传播、状态一致性
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 验证级别
        self.validation_level = ValidationLevel(
            self.config.get("validation_level", "strict")
        )
        
        # 置信度阈值
        self.confidence_threshold = self.config.get(
            "confidence_threshold", 0.6
        )
        
        # 参数规则库
        self.parameter_rules: Dict[str, List[ParameterRule]] = {}
        
        # 约束库
        self.constraints: Dict[str, List[ToolConstraint]] = {}
        
        # 验证历史
        self.validation_history: List[ToolCallValidationResult] = []
        
        logger.info(
            f"工具调用验证器初始化: 级别={self.validation_level.value}"
        )
    
    def register_parameter_rules(
        self, 
        tool_name: str, 
        rules: List[ParameterRule]
    ):
        """注册工具参数规则"""
        self.parameter_rules[tool_name] = rules
        logger.debug(f"注册参数规则: {tool_name}")
    
    def register_constraint(
        self,
        tool_name: str,
        constraint: ToolConstraint
    ):
        """注册工具约束"""
        if tool_name not in self.constraints:
            self.constraints[tool_name] = []
        self.constraints[tool_name].append(constraint)
        logger.debug(f"注册约束: {tool_name}.{constraint.name}")
    
    def validate_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        pre_call: bool = True,
        post_result: Optional[Any] = None
    ) -> ToolCallValidationResult:
        """
        验证工具调用
        
        Args:
            tool_name: 工具名称
            parameters: 调用参数
            pre_call: 是否为调用前验证
            post_result: 调用后结果（如果pre_call=False）
            
        Returns:
            ToolCallValidationResult: 验证结果
        """
        if self.validation_level == ValidationLevel.NONE:
            return ToolCallValidationResult(
                is_valid=True,
                validation_level=self.validation_level,
                confidence=1.0
            )
        
        # 初始化结果
        pre_validation = {}
        post_validation = {}
        constraint_checks = {}
        error_details = []
        suggestions = []
        
        # 调用前验证
        if pre_call:
            # 参数验证
            param_result = self._validate_parameters(tool_name, parameters)
            pre_validation = param_result["result"]
            error_details.extend(param_result.get("errors", []))
            suggestions.extend(param_result.get("suggestions", []))
            
            # 约束预检查
            constraint_result = self._check_constraints(
                tool_name, parameters, pre_call=True
            )
            constraint_checks.update(constraint_result)
        
        # 调用后验证
        if not pre_call and post_result is not None:
            # 结果验证
            result_validation = self._validate_result(tool_name, post_result)
            post_validation = result_validation["result"]
            error_details.extend(result_validation.get("errors", []))
            
            # 约束后检查
            constraint_result = self._check_constraints(
                tool_name, {"result": post_result}, pre_call=False
            )
            constraint_checks.update(constraint_result)
        
        # 计算置信度
        confidence = self._calculate_confidence(
            pre_validation, post_validation, constraint_checks
        )
        
        # 判断有效性
        is_valid = (
            confidence >= self.confidence_threshold and
            len([e for e in error_details if e.get("severity") == "error"]) == 0
        )
        
        result = ToolCallValidationResult(
            is_valid=is_valid,
            validation_level=self.validation_level,
            confidence=confidence,
            pre_validation=pre_validation,
            post_validation=post_validation,
            constraint_checks=constraint_checks,
            error_details=error_details,
            suggestions=suggestions
        )
        
        # 记录历史
        self.validation_history.append(result)
        
        return result
    
    def _validate_parameters(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证参数"""
        result = {
            "status": "valid",
            "validated_params": {},
            "errors": [],
            "suggestions": []
        }
        
        # 获取规则
        rules = self.parameter_rules.get(tool_name, [])
        
        if not rules:
            # 无规则，使用基本验证
            return result
        
        # 逐参数验证
        for rule in rules:
            param_value = parameters.get(rule.name)
            status = rule.validate(param_value)
            
            result["validated_params"][rule.name] = {
                "value": param_value,
                "status": status.value
            }
            
            if status == ParameterValidationStatus.INVALID:
                result["status"] = "invalid"
                result["errors"].append({
                    "parameter": rule.name,
                    "severity": "error",
                    "message": f"参数 {rule.name} 验证失败"
                })
                result["suggestions"].append(
                    f"请检查参数 {rule.name} 的值是否符合要求"
                )
            elif status == ParameterValidationStatus.WARNING:
                if result["status"] != "invalid":
                    result["status"] = "warning"
                result["suggestions"].append(
                    f"参数 {rule.name} 可能存在问题，建议检查"
                )
        
        return result
    
    def _validate_result(
        self,
        tool_name: str,
        result: Any
    ) -> Dict[str, Any]:
        """验证工具调用结果"""
        validation = {
            "status": "valid",
            "result": {},
            "errors": []
        }
        
        # 基本类型检查
        if result is None:
            validation["status"] = "invalid"
            validation["errors"].append({
                "type": "result",
                "severity": "error",
                "message": "工具返回结果为空"
            })
            return validation
        
        # 检查结果结构
        if isinstance(result, dict):
            # 检查错误字段
            if "error" in result:
                validation["status"] = "invalid"
                validation["errors"].append({
                    "type": "result",
                    "severity": "error",
                    "message": f"工具返回错误: {result.get('error')}"
                })
            
            # 检查必需字段
            if "data" not in result and "result" not in result:
                validation["errors"].append({
                    "type": "result_structure",
                    "severity": "warning",
                    "message": "结果缺少标准数据字段"
                })
        
        validation["result"] = {
            "type": type(result).__name__,
            "has_error": "error" in (result if isinstance(result, dict) else {}),
            "size": len(str(result))
        }
        
        return validation
    
    def _check_constraints(
        self,
        tool_name: str,
        context: Dict[str, Any],
        pre_call: bool = True
    ) -> Dict[str, bool]:
        """检查约束"""
        constraints = self.constraints.get(tool_name, [])
        results = {}
        
        for constraint in constraints:
            satisfied = constraint.check(context)
            results[f"{constraint.name}"] = satisfied
            
            if not satisfied and constraint.severity == "error":
                logger.warning(
                    f"约束未满足 [{tool_name}]: {constraint.name}"
                )
        
        return results
    
    def _calculate_confidence(
        self,
        pre_validation: Dict[str, Any],
        post_validation: Dict[str, Any],
        constraint_checks: Dict[str, bool]
    ) -> float:
        """计算置信度"""
        confidence = 1.0
        
        # 基于参数验证结果
        if pre_validation:
            param_status = pre_validation.get("status", "valid")
            if param_status == "invalid":
                confidence -= 0.4
            elif param_status == "warning":
                confidence -= 0.2
        
        # 基于结果验证
        if post_validation:
            result_status = post_validation.get("status", "valid")
            if result_status == "invalid":
                confidence -= 0.5
            elif result_status == "warning":
                confidence -= 0.2
        
        # 基于约束检查
        if constraint_checks:
            satisfied = sum(1 for v in constraint_checks.values() if v)
            total = len(constraint_checks)
            constraint_score = satisfied / total if total > 0 else 1.0
            confidence = confidence * 0.5 + constraint_score * 0.5
        
        return max(0.0, min(1.0, round(confidence, 3)))
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证统计"""
        if not self.validation_history:
            return {
                "total_validations": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0
            }
        
        total = len(self.validation_history)
        successes = sum(1 for r in self.validation_history if r.is_valid)
        
        return {
            "total_validations": total,
            "success_rate": round(successes / total, 3),
            "avg_confidence": round(
                sum(r.confidence for r in self.validation_history) / total,
                3
            ),
            "recent_results": [
                r.to_dict() for r in self.validation_history[-5:]
            ]
        }


# 全局单例
_tool_call_validator: Optional[ToolCallValidator] = None


def get_tool_call_validator(
    config: Optional[Dict[str, Any]] = None
) -> ToolCallValidator:
    """获取工具调用验证器单例"""
    global _tool_call_validator
    
    if _tool_call_validator is None:
        _tool_call_validator = ToolCallValidator(config)
    
    return _tool_call_validator
