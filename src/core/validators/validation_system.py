#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强参数验证系统 - 受Paperclip验证系统启发的强大验证机制

设计原则：
1. 声明式验证：使用装饰器定义验证规则
2. 类型安全：充分利用Python类型提示
3. 异步支持：支持异步验证操作
4. 组合验证：支持验证规则组合和嵌套
5. 详细错误：提供详细的验证错误信息
6. 可扩展：易于添加自定义验证器

示例用法：

# 定义数据类
@dataclass
class ModelConfig:
    name: str
    cost_per_token: float
    max_tokens: int

# 定义验证规则
validator = Validator()
validator.add_rule("name", [
    Required(),
    Length(min=1, max=50),
    Regex(r"^[a-zA-Z0-9_-]+$")
])
validator.add_rule("cost_per_token", [
    Required(),
    Range(min=0.0, max=1.0)
])
validator.add_rule("max_tokens", [
    Required(),
    Integer(),
    Range(min=1, max=100000)
])

# 执行验证
config = ModelConfig(name="deepseek-reasoner", cost_per_token=0.014, max_tokens=32000)
errors = await validator.validate(config)
if errors:
    print(f"验证失败: {errors}")
else:
    print("验证通过")
"""

import re
import inspect
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union, Callable, Type, TypeVar, Generic
from dataclasses import dataclass, field, is_dataclass, asdict
from enum import Enum
from datetime import datetime
import threading
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ValidationError(Exception):
    """验证错误"""
    
    def __init__(self, field: str, message: str, value: Any = None, code: str = None):
        self.field = field
        self.message = message
        self.value = value
        self.code = code or "validation_error"
        super().__init__(f"{field}: {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value,
            "code": self.code,
            "timestamp": datetime.now().isoformat()
        }


class ValidationSeverity(Enum):
    """验证严重性级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """验证结果"""
    valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: ValidationError):
        """添加错误"""
        self.errors.append(error)
        self.valid = False
    
    def add_warning(self, warning: ValidationError):
        """添加警告"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "valid": self.valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "metadata": self.metadata,
            "timestamp": datetime.now().isoformat()
        }
    
    def __bool__(self):
        return self.valid
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


class ValidatorBase(ABC):
    """验证器基类"""
    
    @abstractmethod
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        """验证值"""
        pass
    
    def __call__(self, value: Any, field: str = "") -> ValidationResult:
        """同步调用验证器"""
        return asyncio.run(self.validate(value, field))


class ValidationRule(ValidatorBase):
    """验证规则包装器"""
    
    def __init__(
        self,
        validator: ValidatorBase,
        field: str = "",
        severity: ValidationSeverity = ValidationSeverity.ERROR,
        message: Optional[str] = None,
        condition: Optional[Callable[[Any], bool]] = None
    ):
        self.validator = validator
        self.field = field
        self.severity = severity
        self.custom_message = message
        self.condition = condition
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        """验证值"""
        # 使用规则字段名（如果提供）
        target_field = self.field or field
        
        # 检查条件
        if self.condition is not None:
            try:
                if not self.condition(value):
                    return ValidationResult(valid=True)
            except Exception as e:
                logger.error(f"验证条件执行失败: {e}")
                error = ValidationError(
                    field=target_field,
                    message=f"验证条件检查失败: {e}",
                    value=value,
                    code="condition_error"
                )
                result = ValidationResult(valid=False)
                result.add_error(error)
                return result
        
        # 执行验证
        result = await self.validator.validate(value, target_field)
        
        # 应用自定义消息
        if self.custom_message and result.has_errors:
            for error in result.errors:
                error.message = self.custom_message
        
        # 转换严重性级别
        if self.severity == ValidationSeverity.WARNING and result.has_errors:
            # 将错误转换为警告
            for error in result.errors:
                warning = ValidationError(
                    field=error.field,
                    message=error.message,
                    value=error.value,
                    code=error.code
                )
                result.warnings.append(warning)
            result.errors.clear()
            result.valid = True
        
        return result


# ============================================================================
# 内置验证器
# ============================================================================

class Required(ValidatorBase):
    """必需字段验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段是必需的"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is None:
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="required"
            )
            result.add_error(error)
        
        return result


class NotEmpty(ValidatorBase):
    """非空验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段不能为空"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is None or (hasattr(value, '__len__') and len(value) == 0):
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="not_empty"
            )
            result.add_error(error)
        
        return result


class TypeValidator(ValidatorBase):
    """类型验证器"""
    
    def __init__(self, expected_type: Type, message: Optional[str] = None):
        self.expected_type = expected_type
        self.message = message or f"字段必须是 {expected_type.__name__} 类型"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None and not isinstance(value, self.expected_type):
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="type_mismatch"
            )
            result.add_error(error)
        
        return result


class String(ValidatorBase):
    """字符串验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段必须是字符串"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None and not isinstance(value, str):
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="not_string"
            )
            result.add_error(error)
        
        return result


class Integer(ValidatorBase):
    """整数验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段必须是整数"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not isinstance(value, int):
                # 尝试转换
                try:
                    int(value)
                except (ValueError, TypeError):
                    error = ValidationError(
                        field=field,
                        message=self.message,
                        value=value,
                        code="not_integer"
                    )
                    result.add_error(error)
        
        return result


class Float(ValidatorBase):
    """浮点数验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段必须是浮点数"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not isinstance(value, (int, float)):
                # 尝试转换
                try:
                    float(value)
                except (ValueError, TypeError):
                    error = ValidationError(
                        field=field,
                        message=self.message,
                        value=value,
                        code="not_float"
                    )
                    result.add_error(error)
        
        return result


class Boolean(ValidatorBase):
    """布尔值验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段必须是布尔值"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None and not isinstance(value, bool):
            # 尝试转换常见布尔表示
            if str(value).lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                error = ValidationError(
                    field=field,
                    message=self.message,
                    value=value,
                    code="not_boolean"
                )
                result.add_error(error)
        
        return result


class ListValidator(ValidatorBase):
    """列表验证器"""
    
    def __init__(self, item_validator: Optional[ValidatorBase] = None, message: Optional[str] = None):
        self.item_validator = item_validator
        self.message = message or "字段必须是列表"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not isinstance(value, list):
                error = ValidationError(
                    field=field,
                    message=self.message,
                    value=value,
                    code="not_list"
                )
                result.add_error(error)
            elif self.item_validator:
                # 验证列表中的每个项
                for i, item in enumerate(value):
                    item_result = await self.item_validator.validate(item, f"{field}[{i}]")
                    if not item_result.valid:
                        result.errors.extend(item_result.errors)
                        result.warnings.extend(item_result.warnings)
                        result.valid = False
        
        return result


class DictValidator(ValidatorBase):
    """字典验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message or "字段必须是字典"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None and not isinstance(value, dict):
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="not_dict"
            )
            result.add_error(error)
        
        return result


class Length(ValidatorBase):
    """长度验证器"""
    
    def __init__(self, min: Optional[int] = None, max: Optional[int] = None, message: Optional[str] = None):
        self.min = min
        self.max = max
        self.message = message
        
        if not message:
            parts = []
            if min is not None:
                parts.append(f"至少 {min} 个字符")
            if max is not None:
                parts.append(f"最多 {max} 个字符")
            self.message = f"长度必须" + (" " + "且".join(parts) if parts else "符合要求")
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not hasattr(value, '__len__'):
                error = ValidationError(
                    field=field,
                    message="无法计算长度",
                    value=value,
                    code="no_length"
                )
                result.add_error(error)
            else:
                length = len(value)
                if self.min is not None and length < self.min:
                    error = ValidationError(
                        field=field,
                        message=f"长度必须至少为 {self.min}，当前为 {length}",
                        value=value,
                        code="min_length"
                    )
                    result.add_error(error)
                
                if self.max is not None and length > self.max:
                    error = ValidationError(
                        field=field,
                        message=f"长度必须最多为 {self.max}，当前为 {length}",
                        value=value,
                        code="max_length"
                    )
                    result.add_error(error)
        
        return result


class Range(ValidatorBase):
    """范围验证器"""
    
    def __init__(self, min: Optional[float] = None, max: Optional[float] = None, message: Optional[str] = None):
        self.min = min
        self.max = max
        self.message = message
        
        if not message:
            parts = []
            if min is not None:
                parts.append(f"最小值为 {min}")
            if max is not None:
                parts.append(f"最大值为 {max}")
            self.message = f"值必须" + (" " + "且".join(parts) if parts else "在有效范围内")
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            # 尝试转换为数值
            try:
                numeric_value = float(value)
            except (ValueError, TypeError):
                error = ValidationError(
                    field=field,
                    message="必须是数值",
                    value=value,
                    code="not_numeric"
                )
                result.add_error(error)
                return result
            
            if self.min is not None and numeric_value < self.min:
                error = ValidationError(
                    field=field,
                    message=f"必须大于等于 {self.min}，当前为 {numeric_value}",
                    value=value,
                    code="min_value"
                )
                result.add_error(error)
            
            if self.max is not None and numeric_value > self.max:
                error = ValidationError(
                    field=field,
                    message=f"必须小于等于 {self.max}，当前为 {numeric_value}",
                    value=value,
                    code="max_value"
                )
                result.add_error(error)
        
        return result


class Regex(ValidatorBase):
    """正则表达式验证器"""
    
    def __init__(self, pattern: str, message: Optional[str] = None, flags: int = 0):
        self.pattern = pattern
        self.regex = re.compile(pattern, flags)
        self.message = message or f"必须匹配模式: {pattern}"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not isinstance(value, str):
                error = ValidationError(
                    field=field,
                    message="必须是字符串才能进行正则匹配",
                    value=value,
                    code="not_string_for_regex"
                )
                result.add_error(error)
            elif not self.regex.match(value):
                error = ValidationError(
                    field=field,
                    message=self.message,
                    value=value,
                    code="regex_mismatch"
                )
                result.add_error(error)
        
        return result


class Email(ValidatorBase):
    """邮箱验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        self.regex = re.compile(self.pattern)
        self.message = message or "必须是有效的邮箱地址"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not isinstance(value, str):
                error = ValidationError(
                    field=field,
                    message="必须是字符串",
                    value=value,
                    code="not_string"
                )
                result.add_error(error)
            elif not self.regex.match(value):
                error = ValidationError(
                    field=field,
                    message=self.message,
                    value=value,
                    code="invalid_email"
                )
                result.add_error(error)
        
        return result


class URL(ValidatorBase):
    """URL验证器"""
    
    def __init__(self, message: Optional[str] = None):
        self.pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        self.regex = re.compile(self.pattern)
        self.message = message or "必须是有效的URL"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            if not isinstance(value, str):
                error = ValidationError(
                    field=field,
                    message="必须是字符串",
                    value=value,
                    code="not_string"
                )
                result.add_error(error)
            elif not self.regex.match(value):
                error = ValidationError(
                    field=field,
                    message=self.message,
                    value=value,
                    code="invalid_url"
                )
                result.add_error(error)
        
        return result


class InList(ValidatorBase):
    """值在列表中验证器"""
    
    def __init__(self, allowed_values: List[Any], message: Optional[str] = None):
        self.allowed_values = allowed_values
        self.message = message or f"必须是以下值之一: {allowed_values}"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None and value not in self.allowed_values:
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="not_in_list"
            )
            result.add_error(error)
        
        return result


class CustomValidator(ValidatorBase):
    """自定义验证器"""
    
    def __init__(self, validator_func: Callable[[Any], Union[bool, ValidationResult]], message: Optional[str] = None):
        self.validator_func = validator_func
        self.message = message
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            try:
                validation_result = self.validator_func(value)
                
                if isinstance(validation_result, ValidationResult):
                    return validation_result
                elif not validation_result:
                    error = ValidationError(
                        field=field,
                        message=self.message or "验证失败",
                        value=value,
                        code="custom_validation_failed"
                    )
                    result.add_error(error)
            
            except Exception as e:
                error = ValidationError(
                    field=field,
                    message=f"自定义验证器执行失败: {e}",
                    value=value,
                    code="custom_validator_error"
                )
                result.add_error(error)
        
        return result


class AsyncCustomValidator(ValidatorBase):
    """异步自定义验证器"""
    
    def __init__(self, validator_func: Callable[[Any], Any], message: Optional[str] = None):
        self.validator_func = validator_func
        self.message = message
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        if value is not None:
            try:
                if inspect.iscoroutinefunction(self.validator_func):
                    validation_result = await self.validator_func(value)
                else:
                    validation_result = self.validator_func(value)
                
                if isinstance(validation_result, ValidationResult):
                    return validation_result
                elif not validation_result:
                    error = ValidationError(
                        field=field,
                        message=self.message or "验证失败",
                        value=value,
                        code="async_custom_validation_failed"
                    )
                    result.add_error(error)
            
            except Exception as e:
                error = ValidationError(
                    field=field,
                    message=f"异步自定义验证器执行失败: {e}",
                    value=value,
                    code="async_custom_validator_error"
                )
                result.add_error(error)
        
        return result


class CompositeValidator(ValidatorBase):
    """复合验证器（所有验证器必须通过）"""
    
    def __init__(self, validators: List[ValidatorBase]):
        self.validators = validators
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        result = ValidationResult(valid=True)
        
        for validator in self.validators:
            validator_result = await validator.validate(value, field)
            
            if not validator_result.valid:
                result.errors.extend(validator_result.errors)
                result.warnings.extend(validator_result.warnings)
                result.valid = False
        
        return result


class AnyOfValidator(ValidatorBase):
    """任意验证器通过即可"""
    
    def __init__(self, validators: List[ValidatorBase], message: Optional[str] = None):
        self.validators = validators
        self.message = message or "至少需要一个验证器通过"
    
    async def validate(self, value: Any, field: str = "") -> ValidationResult:
        all_errors = []
        all_warnings = []
        
        for validator in self.validators:
            validator_result = await validator.validate(value, field)
            
            if validator_result.valid:
                # 至少有一个验证器通过
                result = ValidationResult(valid=True)
                result.warnings.extend(validator_result.warnings)
                result.warnings.extend(all_warnings)
                return result
            else:
                all_errors.extend(validator_result.errors)
                all_warnings.extend(validator_result.warnings)
        
        # 所有验证器都失败
        result = ValidationResult(valid=False)
        result.errors.extend(all_errors)
        result.warnings.extend(all_warnings)
        
        # 添加汇总错误
        if self.message and not any(e.code == "any_of_failed" for e in result.errors):
            error = ValidationError(
                field=field,
                message=self.message,
                value=value,
                code="any_of_failed"
            )
            result.add_error(error)
        
        return result


# ============================================================================
# 验证器构建器
# ============================================================================

class Validator:
    """验证器主类"""
    
    def __init__(self):
        self.rules: Dict[str, List[ValidationRule]] = {}
        self._lock = threading.RLock()
    
    def add_rule(self, field: str, validators: Union[ValidatorBase, List[ValidatorBase]], **kwargs) -> 'Validator':
        """添加验证规则"""
        with self._lock:
            if field not in self.rules:
                self.rules[field] = []
            
            if not isinstance(validators, list):
                validators = [validators]
            
            for validator in validators:
                if isinstance(validator, ValidationRule):
                    rule = validator
                else:
                    rule = ValidationRule(validator, **kwargs)
                
                self.rules[field].append(rule)
        
        return self
    
    def remove_rule(self, field: str, validator_index: Optional[int] = None) -> 'Validator':
        """移除验证规则"""
        with self._lock:
            if field in self.rules:
                if validator_index is not None:
                    if 0 <= validator_index < len(self.rules[field]):
                        del self.rules[field][validator_index]
                else:
                    del self.rules[field]
        
        return self
    
    async def validate_field(self, field: str, value: Any) -> ValidationResult:
        """验证单个字段"""
        with self._lock:
            field_rules = self.rules.get(field, [])
        
        result = ValidationResult(valid=True)
        
        for rule in field_rules:
            rule_result = await rule.validate(value, field)
            
            if not rule_result.valid:
                result.errors.extend(rule_result.errors)
                result.warnings.extend(rule_result.warnings)
                result.valid = False
        
        return result
    
    async def validate(self, data: Union[Dict[str, Any], Any]) -> ValidationResult:
        """验证数据"""
        result = ValidationResult(valid=True)
        
        # 处理不同类型的数据
        if isinstance(data, dict):
            # 字典数据
            for field, value in data.items():
                field_result = await self.validate_field(field, value)
                if not field_result.valid:
                    result.errors.extend(field_result.errors)
                    result.warnings.extend(field_result.warnings)
                    result.valid = False
        elif is_dataclass(data):
            # 数据类
            data_dict = asdict(data)
            for field, value in data_dict.items():
                field_result = await self.validate_field(field, value)
                if not field_result.valid:
                    result.errors.extend(field_result.errors)
                    result.warnings.extend(field_result.warnings)
                    result.valid = False
        else:
            # 单个值
            field_result = await self.validate_field("value", data)
            if not field_result.valid:
                result.errors.extend(field_result.errors)
                result.warnings.extend(field_result.warnings)
                result.valid = False
        
        return result
    
    def validate_sync(self, data: Union[Dict[str, Any], Any]) -> ValidationResult:
        """同步验证数据"""
        return asyncio.run(self.validate(data))
    
    def get_rules(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有规则"""
        with self._lock:
            rules_info = {}
            for field, field_rules in self.rules.items():
                rules_info[field] = []
                for rule in field_rules:
                    rule_info = {
                        "validator_type": type(rule.validator).__name__,
                        "severity": rule.severity.value,
                        "field": rule.field,
                    }
                    rules_info[field].append(rule_info)
            return rules_info


# ============================================================================
# 与声明式配置的集成
# ============================================================================

def validate_config(config_validator: Validator):
    """配置验证装饰器"""
    def decorator(cls):
        # 保存原始验证方法（如果有）
        original_validate = getattr(cls, 'validate', None)
        
        async def enhanced_validate(self, config_data: Dict[str, Any]) -> ValidationResult:
            # 使用配置验证器
            validation_result = await config_validator.validate(config_data)
            
            # 调用原始验证方法（如果有）
            if original_validate:
                original_result = await original_validate(self, config_data)
                if not original_result.valid:
                    validation_result.errors.extend(original_result.errors)
                    validation_result.warnings.extend(original_result.warnings)
                    validation_result.valid = False
            
            return validation_result
        
        # 添加验证方法
        cls.validate = enhanced_validate
        
        # 添加验证器属性
        cls.config_validator = config_validator
        
        return cls
    
    return decorator


# ============================================================================
# 预定义验证器工厂
# ============================================================================

class ValidatorFactory:
    """验证器工厂"""
    
    @staticmethod
    def create_llm_model_validator() -> Validator:
        """创建LLM模型验证器"""
        validator = Validator()
        
        validator.add_rule("name", [
            Required(),
            String(),
            Length(min=1, max=100),
            Regex(r"^[a-zA-Z0-9_.-]+$", message="名称只能包含字母、数字、点、下划线和短横线")
        ])
        
        validator.add_rule("provider", [
            Required(),
            String(),
            Length(min=1, max=50)
        ])
        
        validator.add_rule("cost_per_token", [
            Required(),
            Float(),
            Range(min=0.0, max=1.0, message="每token成本必须在0到1之间")
        ])
        
        validator.add_rule("max_tokens", [
            Required(),
            Integer(),
            Range(min=1, max=1000000, message="最大token数必须在1到1000000之间")
        ])
        
        validator.add_rule("temperature", [
            Float(),
            Range(min=0.0, max=2.0, message="温度必须在0到2之间")
        ])
        
        validator.add_rule("timeout", [
            Integer(),
            Range(min=1, max=300, message="超时时间必须在1到300秒之间")
        ])
        
        validator.add_rule("max_retries", [
            Integer(),
            Range(min=0, max=10, message="最大重试次数必须在0到10之间")
        ])
        
        validator.add_rule("enabled", [
            Boolean()
        ])
        
        return validator
    
    @staticmethod
    def create_routing_strategy_validator() -> Validator:
        """创建路由策略验证器"""
        validator = Validator()
        
        validator.add_rule("name", [
            Required(),
            String(),
            Length(min=1, max=100)
        ])
        
        validator.add_rule("description", [
            String(),
            Length(max=500)
        ])
        
        validator.add_rule("processors", [
            ListValidator(item_validator=String())
        ])
        
        validator.add_rule("cost_weight", [
            Float(),
            Range(min=0.0, max=1.0, message="成本权重必须在0到1之间")
        ])
        
        validator.add_rule("performance_weight", [
            Float(),
            Range(min=0.0, max=1.0, message="性能权重必须在0到1之间")
        ])
        
        validator.add_rule("quality_weight", [
            Float(),
            Range(min=0.0, max=1.0, message="质量权重必须在0到1之间")
        ])
        
        validator.add_rule("priority", [
            Integer(),
            Range(min=1, max=10, message="优先级必须在1到10之间")
        ])
        
        validator.add_rule("enabled", [
            Boolean()
        ])
        
        return validator
    
    @staticmethod
    def create_processor_validator() -> Validator:
        """创建处理器验证器"""
        validator = Validator()
        
        validator.add_rule("name", [
            Required(),
            String(),
            Length(min=1, max=100)
        ])
        
        validator.add_rule("description", [
            String(),
            Length(max=500)
        ])
        
        validator.add_rule("async_execution", [
            Boolean()
        ])
        
        validator.add_rule("timeout", [
            Float(),
            Range(min=0.1, max=300.0, message="超时时间必须在0.1到300秒之间")
        ])
        
        validator.add_rule("max_retries", [
            Integer(),
            Range(min=0, max=10, message="最大重试次数必须在0到10之间")
        ])
        
        validator.add_rule("enabled", [
            Boolean()
        ])
        
        return validator


# ============================================================================
# 全局验证器实例
# ============================================================================

_llm_model_validator = None
_routing_strategy_validator = None
_processor_validator = None


def get_llm_model_validator() -> Validator:
    """获取LLM模型验证器"""
    global _llm_model_validator
    if _llm_model_validator is None:
        _llm_model_validator = ValidatorFactory.create_llm_model_validator()
    return _llm_model_validator


def get_routing_strategy_validator() -> Validator:
    """获取路由策略验证器"""
    global _routing_strategy_validator
    if _routing_strategy_validator is None:
        _routing_strategy_validator = ValidatorFactory.create_routing_strategy_validator()
    return _routing_strategy_validator


def get_processor_validator() -> Validator:
    """获取处理器验证器"""
    global _processor_validator
    if _processor_validator is None:
        _processor_validator = ValidatorFactory.create_processor_validator()
    return _processor_validator