#!/usr/bin/env python3
"""
Stop Hook 机制 - 阻止Agent过早退出
对齐 Ralph Loop 范式

核心功能:
- 定义可验证的完成条件
- 在Agent认为"完成"时进行拦截
- 基于客观标准而非主观判断
"""
import re
import subprocess
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CriterionType(str, Enum):
    """完成条件类型"""
    COMMAND = "command"        # Shell命令 (pytest, coverage等)
    FILE_EXISTS = "file_exists"  # 文件存在
    FILE_PATTERN = "file_pattern" # 文件模式匹配
    JSON_PATH = "json_path"    # JSON路径值
    CUSTOM = "custom"          # 自定义函数


class ComparisonOperator(str, Enum):
    """比较操作符"""
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    LESS = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    MATCHES = "matches"  # 正则匹配


@dataclass
class CompletionCriterion:
    """完成条件定义"""
    criterion_id: str
    type: CriterionType
    
    # 条件内容
    expression: str  # 例如: "pytest tests/ -v", "coverage > 80%"
    operator: Optional[ComparisonOperator] = None
    expected_value: Optional[Any] = None
    
    # 配置
    required: bool = True  # 是否必需
    retry_on_fail: bool = True  # 失败是否重试
    timeout: int = 60  # 超时秒数
    
    # 描述
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"Verify: {self.expression}"


@dataclass
class CriterionResult:
    """条件验证结果"""
    criterion_id: str
    success: bool
    actual_value: Any = None
    expected_value: Any = None
    message: str = ""
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "criterion_id": self.criterion_id,
            "success": self.success,
            "actual_value": self.actual_value,
            "expected_value": self.expected_value,
            "message": self.message,
            "error": self.error
        }


class StopHook:
    """Stop Hook - 阻止Agent过早退出
    
    在Agent认为"完成"时进行拦截，
    基于客观标准验证是否真正完成
    """
    
    def __init__(self):
        self.criteria: Dict[str, CompletionCriterion] = {}
        self.results: List[CriterionResult] = []
        self.custom_checkers: Dict[str, Callable] = {}
        
        logger.info("StopHook initialized")
    
    def add_criterion(self, criterion: CompletionCriterion):
        """添加完成条件"""
        self.criteria[criterion.criterion_id] = criterion
        logger.info(f"Added criterion: {criterion.criterion_id} - {criterion.expression}")
    
    def add_criteria_from_list(self, criteria_strings: List[str]):
        """从字符串列表添加条件
        
        支持格式:
        - "pytest tests/ -v"
        - "coverage > 80"
        - "file_exists: tests/test_*.py"
        - "json_path: $.version == 1.0.0"
        """
        for i, expr in enumerate(criteria_strings):
            criterion = self._parse_criterion_string(expr, i)
            if criterion:
                self.add_criterion(criterion)
    
    def _parse_criterion_string(self, expr: str, index: int) -> Optional[CompletionCriterion]:
        """解析条件字符串"""
        expr = expr.strip()
        
        # 文件存在检查
        if expr.startswith("file_exists:"):
            file_path = expr.replace("file_exists:", "").strip()
            return CompletionCriterion(
                criterion_id=f"criterion_{index}",
                type=CriterionType.FILE_EXISTS,
                expression=file_path,
                description=f"Check file exists: {file_path}"
            )
        
        # 文件模式匹配
        if expr.startswith("file_pattern:"):
            pattern = expr.replace("file_pattern:", "").strip()
            return CompletionCriterion(
                criterion_id=f"criterion_{index}",
                type=CriterionType.FILE_PATTERN,
                expression=pattern,
                description=f"Check file pattern: {pattern}"
            )
        
        # JSON路径检查
        if expr.startswith("json_path:"):
            json_expr = expr.replace("json_path:", "").strip()
            return CompletionCriterion(
                criterion_id=f"criterion_{index}",
                type=CriterionType.JSON_PATH,
                expression=json_expr,
                description=f"Check JSON: {json_expr}"
            )
        
        # Shell命令 (默认)
        if ">" in expr or "<" in expr or "==" in expr or "!=" in expr:
            # 解析比较表达式
            match = re.match(r"(.+?)\s*(>=|<=|==|!=|>|<)\s*(.+)", expr)
            if match:
                cmd, op, expected = match.groups()
                return CompletionCriterion(
                    criterion_id=f"criterion_{index}",
                    type=CriterionType.COMMAND,
                    expression=cmd.strip(),
                    operator=ComparisonOperator(op),
                    expected_value=self._parse_value(expected.strip()),
                    description=f"Verify: {expr}"
                )
        
        # 简单命令
        return CompletionCriterion(
            criterion_id=f"criterion_{index}",
            type=CriterionType.COMMAND,
            expression=expr,
            description=f"Run: {expr}"
        )
    
    def _parse_value(self, value_str: str) -> Any:
        """解析值"""
        value_str = value_str.strip()
        
        # 数字
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass
        
        # 布尔
        if value_str.lower() in ("true", "yes", "on"):
            return True
        if value_str.lower() in ("false", "no", "off"):
            return False
        
        # 字符串
        return value_str
    
    def register_custom_checker(self, name: str, checker: Callable):
        """注册自定义检查器"""
        self.custom_checkers[name] = checker
        logger.info(f"Registered custom checker: {name}")
    
    def should_continue(self, state: Dict[str, Any]) -> bool:
        """判断是否继续执行
        
        Returns:
            True = 应该继续 (未完成)
            False = 可以停止 (已完成)
        """
        if not self.criteria:
            # 没有定义条件，默认继续
            logger.debug("No criteria defined, defaulting to continue")
            return True
        
        self.results = []
        all_required_met = True
        
        for criterion_id, criterion in self.criteria.items():
            result = self._verify_criterion(criterion, state)
            self.results.append(result)
            
            if not result.success and criterion.required:
                all_required_met = False
            
            # 记录验证结果
            logger.info(
                f"Criterion {criterion_id}: "
                f"{'✓' if result.success else '✗'} {result.message}"
            )
        
        # 如果所有必需条件都满足，可以停止
        should_continue = not all_required_met
        
        if not should_continue:
            logger.info("All required criteria met - can stop")
        else:
            logger.info(f"Criteria not met - should continue ({len(self.results)} criteria)")
        
        return should_continue
    
    def _verify_criterion(self, criterion: CompletionCriterion, 
                        state: Dict[str, Any]) -> CriterionResult:
        """验证单个条件"""
        try:
            if criterion.type == CriterionType.COMMAND:
                return self._verify_command(criterion)
            elif criterion.type == CriterionType.FILE_EXISTS:
                return self._verify_file_exists(criterion)
            elif criterion.type == CriterionType.FILE_PATTERN:
                return self._verify_file_pattern(criterion)
            elif criterion.type == CriterionType.JSON_PATH:
                return self._verify_json_path(criterion, state)
            elif criterion.type == CriterionType.CUSTOM:
                return self._verify_custom(criterion, state)
            else:
                return CriterionResult(
                    criterion_id=criterion.criterion_id,
                    success=False,
                    error=f"Unknown criterion type: {criterion.type}"
                )
        except Exception as e:
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=False,
                error=str(e)
            )
    
    def _verify_command(self, criterion: CompletionCriterion) -> CriterionResult:
        """验证命令条件"""
        cmd = criterion.expression
        
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=criterion.timeout
            )
            
            actual_value = result.returncode
            
            # 如果没有比较操作符，只检查返回码
            if criterion.operator is None:
                success = result.returncode == 0
                return CriterionResult(
                    criterion_id=criterion.criterion_id,
                    success=success,
                    actual_value=actual_value,
                    message=f"Command exit code: {actual_value}"
                )
            
            # 执行比较
            success = self._compare(
                actual_value, 
                criterion.operator, 
                criterion.expected_value
            )
            
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=success,
                actual_value=actual_value,
                expected_value=criterion.expected_value,
                message=f"Command: {cmd} -> {actual_value} {criterion.operator} {criterion.expected_value}"
            )
            
        except subprocess.TimeoutExpired:
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=False,
                error=f"Command timeout after {criterion.timeout}s"
            )
        except Exception as e:
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=False,
                error=str(e)
            )
    
    def _verify_file_exists(self, criterion: CompletionCriterion) -> CriterionResult:
        """验证文件存在"""
        import os
        file_path = criterion.expression
        
        exists = os.path.exists(file_path)
        
        return CriterionResult(
            criterion_id=criterion.criterion_id,
            success=exists,
            actual_value=exists,
            message=f"File exists: {file_path}"
        )
    
    def _verify_file_pattern(self, criterion: CompletionCriterion) -> CriterionResult:
        """验证文件模式"""
        import os
        from pathlib import Path
        
        pattern = criterion.expression
        path = Path(".")
        
        # 查找匹配文件
        matches = list(path.glob(pattern))
        
        return CriterionResult(
            criterion_id=criterion.criterion_id,
            success=len(matches) > 0,
            actual_value=len(matches),
            message=f"Pattern {pattern}: {len(matches)} files found"
        )
    
    def _verify_json_path(self, criterion: CompletionCriterion, 
                         state: Dict[str, Any]) -> CriterionResult:
        """验证JSON路径"""
        # 简化实现：直接检查state中的值
        # 格式: "key == value" 或 "key > value"
        expr = criterion.expression
        
        # 解析表达式
        match = re.match(r"\$\.(\w+)\s*(==|!=|>|<|>=|<=)\s*(.+)", expr)
        if not match:
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=False,
                error=f"Invalid JSON path expression: {expr}"
            )
        
        key, op, expected_str = match.groups()
        expected = self._parse_value(expected_str)
        
        # 获取实际值
        actual = state.get(key)
        
        # 比较
        success = self._compare(actual, ComparisonOperator(op), expected)
        
        return CriterionResult(
            criterion_id=criterion.criterion_id,
            success=success,
            actual_value=actual,
            expected_value=expected,
            message=f"State.{key}: {actual} {op} {expected}"
        )
    
    def _verify_custom(self, criterion: CompletionCriterion,
                      state: Dict[str, Any]) -> CriterionResult:
        """验证自定义条件"""
        if criterion.expression not in self.custom_checkers:
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=False,
                error=f"Custom checker not found: {criterion.expression}"
            )
        
        checker = self.custom_checkers[criterion.expression]
        
        try:
            result = checker(state)
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=result,
                message=f"Custom check: {criterion.expression}"
            )
        except Exception as e:
            return CriterionResult(
                criterion_id=criterion.criterion_id,
                success=False,
                error=str(e)
            )
    
    def _compare(self, actual: Any, operator: ComparisonOperator, 
                 expected: Any) -> bool:
        """执行比较"""
        if operator == ComparisonOperator.EQUAL:
            return actual == expected
        elif operator == ComparisonOperator.NOT_EQUAL:
            return actual != expected
        elif operator == ComparisonOperator.GREATER:
            return actual > expected
        elif operator == ComparisonOperator.LESS:
            return actual < expected
        elif operator == ComparisonOperator.GREATER_EQUAL:
            return actual >= expected
        elif operator == ComparisonOperator.LESS_EQUAL:
            return actual <= expected
        elif operator == ComparisonOperator.CONTAINS:
            return expected in actual if actual else False
        elif operator == ComparisonOperator.MATCHES:
            return re.match(expected, str(actual)) is not None
        
        return False
    
    def get_results(self) -> List[CriterionResult]:
        """获取验证结果"""
        return self.results
    
    def get_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        if not self.results:
            return {"total": 0, "passed": 0, "failed": 0}
        
        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        
        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(self.results) if self.results else 0,
            "results": [r.to_dict() for r in self.results]
        }
    
    def clear(self):
        """清除所有条件"""
        self.criteria.clear()
        self.results.clear()
    
    def export_criteria(self) -> str:
        """导出条件配置"""
        data = {
            "criteria": [
                {
                    "criterion_id": c.criterion_id,
                    "type": c.type.value,
                    "expression": c.expression,
                    "operator": c.operator.value if c.operator else None,
                    "expected_value": c.expected_value,
                    "required": c.required,
                    "description": c.description
                }
                for c in self.criteria.values()
            ]
        }
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def import_criteria(self, criteria_json: str):
        """导入条件配置"""
        data = json.loads(criteria_json)
        
        for cdata in data.get("criteria", []):
            criterion = CompletionCriterion(
                criterion_id=cdata["criterion_id"],
                type=CriterionType(cdata["type"]),
                expression=cdata["expression"],
                operator=ComparisonOperator(cdata["operator"]) if cdata.get("operator") else None,
                expected_value=cdata.get("expected_value"),
                required=cdata.get("required", True),
                description=cdata.get("description", "")
            )
            self.add_criterion(criterion)


# 便捷函数
def create_stop_hook(criteria: List[str] = None) -> StopHook:
    """创建StopHook实例"""
    hook = StopHook()
    
    if criteria:
        hook.add_criteria_from_list(criteria)
    
    return hook


def should_continue_with_criteria(criteria: List[str], state: Dict[str, Any]) -> bool:
    """快速检查是否继续"""
    hook = create_stop_hook(criteria)
    return hook.should_continue(state)
