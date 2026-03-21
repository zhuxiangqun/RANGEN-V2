"""
Schema验证器
验证推理步骤是否符合预期的JSON格式和结构
"""
import logging
from typing import Dict, List, Any

from .base_validator import BaseValidator, ValidationResult

logger = logging.getLogger(__name__)


class SchemaValidator(BaseValidator):
    """Schema格式验证器"""

    def __init__(self, name: str = "SchemaValidator"):
        super().__init__(name)

        # 定义期望的步骤结构
        self.required_step_fields = ['type', 'description']
        self.optional_step_fields = ['sub_query', 'dependencies', 'evidence_count']

        # 定义有效的步骤类型
        self.valid_step_types = [
            'information_gathering',
            'analysis',
            'comparison',
            'calculation',
            'synthesis',
            'verification',
            'answer_synthesis'
        ]

    def validate(self, steps: List[Dict[str, Any]], query: str) -> ValidationResult:
        """验证步骤的Schema格式"""
        if not isinstance(steps, list):
            return self._create_result(
                False,
                "推理步骤必须是列表格式",
                0.0
            )

        if not steps:
            return self._create_result(
                False,
                "至少需要一个推理步骤",
                0.1
            )

        try:
            errors = []
            warnings = []

            for i, step in enumerate(steps):
                step_errors, step_warnings = self._validate_single_step(step, i + 1)
                errors.extend(step_errors)
                warnings.extend(step_warnings)

            # 检查步骤逻辑流
            flow_errors = self._validate_step_flow(steps)
            errors.extend(flow_errors)

            # 生成验证结果
            if errors:
                return self._create_result(
                    is_valid=False,
                    reason=f"Schema验证失败: {len(errors)}个错误",
                    quality_score=max(0.1, 0.8 - len(errors) * 0.2),
                    errors=errors,
                    warnings=warnings
                )
            elif warnings:
                return self._create_result(
                    is_valid=True,
                    reason=f"Schema格式正确，但有{len(warnings)}个警告",
                    quality_score=0.9,
                    warnings=warnings
                )
            else:
                return self._create_result(
                    is_valid=True,
                    reason="Schema格式完全正确",
                    quality_score=1.0
                )

        except Exception as e:
            logger.error(f"Schema验证失败: {e}")
            return self._create_result(
                False,
                f"验证过程中发生错误: {str(e)}",
                0.1
            )

    def _validate_single_step(self, step: Dict[str, Any], step_index: int) -> tuple[List[str], List[str]]:
        """验证单个步骤"""
        errors = []
        warnings = []

        if not isinstance(step, dict):
            errors.append(f"步骤{step_index}: 必须是字典格式")
            return errors, warnings

        # 检查必需字段
        for field in self.required_step_fields:
            if field not in step:
                errors.append(f"步骤{step_index}: 缺少必需字段 '{field}'")
            elif not step[field]:
                errors.append(f"步骤{step_index}: 字段 '{field}' 不能为空")

        # 检查步骤类型
        step_type = step.get('type')
        if step_type and step_type not in self.valid_step_types:
            warnings.append(f"步骤{step_index}: 未知的步骤类型 '{step_type}'")

        # 检查描述长度
        description = step.get('description', '')
        if len(description) < 10:
            warnings.append(f"步骤{step_index}: 描述过短，可能不够清晰")
        elif len(description) > 200:
            warnings.append(f"步骤{step_index}: 描述过长，可能包含过多信息")

        # 检查子查询
        sub_query = step.get('sub_query')
        if sub_query:
            if len(sub_query) < 5:
                warnings.append(f"步骤{step_index}: 子查询过短")
            elif len(sub_query) > 150:
                warnings.append(f"步骤{step_index}: 子查询过长")

            # 检查子查询是否包含查询关键词
            query_keywords = ['what', 'who', 'where', 'when', 'how', 'why']
            if not any(keyword in sub_query.lower() for keyword in query_keywords):
                warnings.append(f"步骤{step_index}: 子查询不像是一个问题")

        return errors, warnings

    def _validate_step_flow(self, steps: List[Dict[str, Any]]) -> List[str]:
        """验证步骤的逻辑流"""
        errors = []

        # 检查是否有合成答案步骤
        has_synthesis = any(
            step.get('type') == 'answer_synthesis' or
            'synthesis' in step.get('description', '').lower()
            for step in steps
        )

        if not has_synthesis and len(steps) > 1:
            errors.append("多步骤推理应该包含答案合成步骤")

        # 检查步骤依赖关系
        for i, step in enumerate(steps):
            dependencies = step.get('dependencies', [])
            if dependencies:
                for dep in dependencies:
                    if isinstance(dep, int):
                        if dep < 1 or dep > len(steps):
                            errors.append(f"步骤{i+1}: 依赖的步骤{dep}不存在")
                        elif dep >= i + 1:
                            errors.append(f"步骤{i+1}: 不能依赖后续步骤{dep}")

        return errors

    def add_valid_step_type(self, step_type: str):
        """添加有效的步骤类型"""
        if step_type not in self.valid_step_types:
            self.valid_step_types.append(step_type)

    def remove_valid_step_type(self, step_type: str):
        """移除有效的步骤类型"""
        if step_type in self.valid_step_types:
            self.valid_step_types.remove(step_type)
