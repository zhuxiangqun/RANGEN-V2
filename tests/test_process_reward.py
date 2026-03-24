"""
过程奖励服务测试
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.process_reward_service import (
    ProcessRewardService,
    StepValidationStatus,
    ErrorType,
    StepValidation,
    ProcessRewardResult,
    ReasoningStepValidator,
    VariableDefinitionValidator,
    ObjectiveFunctionValidator,
    ConstraintValidator,
    LogicValidator,
    get_process_reward_service
)


class TestProcessRewardService:
    """测试过程奖励服务"""

    def setup_method(self):
        """每个测试前设置"""
        self.service = ProcessRewardService()

    def test_service_initialization(self):
        """测试服务初始化"""
        assert self.service is not None
        assert len(self.service.validators) > 0
        assert self.service.confidence_threshold == 0.6

    def test_validate_reasoning_process(self):
        """测试验证推理过程"""
        reasoning_steps = [
            {'type': 'variable_definition', 'content': 'x = 10'},
            {'type': 'objective_function', 'content': 'minimize cost'},
            {'type': 'logic', 'content': 'Therefore x = 10'}
        ]
        
        result = self.service.validate_reasoning_process(reasoning_steps)
        
        assert isinstance(result, ProcessRewardResult)
        assert len(result.step_validations) == 3

    def test_validate_empty_steps(self):
        """测试空步骤验证"""
        result = self.service.validate_reasoning_process([])
        
        assert result.overall_confidence == 0.0
        assert result.is_valid is False

    def test_overall_confidence_calculation(self):
        """测试整体置信度计算"""
        reasoning_steps = [
            {'type': 'variable_definition', 'content': 'x = 10'},
            {'type': 'logic', 'content': 'Therefore x = 10'}
        ]
        
        result = self.service.validate_reasoning_process(reasoning_steps)
        
        assert 0.0 <= result.overall_confidence <= 1.0

    def test_feedback_generation(self):
        """测试反馈生成"""
        reasoning_steps = [
            {'type': 'invalid', 'content': 'This is wrong'}
        ]
        
        result = self.service.validate_reasoning_process(reasoning_steps)
        
        assert result.feedback is not None
        assert isinstance(result.feedback, str)

    def test_improvement_suggestions(self):
        """测试改进建议生成"""
        reasoning_steps = [
            {'type': 'variable_definition', 'content': '123invalid = 10'}
        ]
        
        result = self.service.validate_reasoning_process(reasoning_steps)
        
        assert isinstance(result.improvement_suggestions, list)

    def test_validation_history(self):
        """测试验证历史"""
        reasoning_steps = [
            {'type': 'variable_definition', 'content': 'x = 10'}
        ]
        
        self.service.validate_reasoning_process(reasoning_steps)
        
        summary = self.service.get_validation_summary()
        assert summary['total_validations'] >= 1

    def test_reset_history(self):
        """测试重置历史"""
        reasoning_steps = [
            {'type': 'variable_definition', 'content': 'x = 10'}
        ]
        
        self.service.validate_reasoning_process(reasoning_steps)
        self.service.reset_history()
        
        summary = self.service.get_validation_summary()
        assert summary['total_validations'] == 0

    def test_set_constraints(self):
        """测试设置约束"""
        constraints = [
            {'text': 'x > 0', 'type': 'inequality'},
            {'text': 'y = 5', 'type': 'equality'}
        ]
        
        self.service.set_constraints(constraints)
        
        assert len(self.service.constraints) == 2


class TestStepValidation:
    """测试步骤验证"""

    def test_validation_status_enum(self):
        """测试验证状态枚举"""
        assert StepValidationStatus.CORRECT.value == 'correct'
        assert StepValidationStatus.INCORRECT.value == 'incorrect'
        assert StepValidationStatus.PARTIAL.value == 'partial'

    def test_error_type_enum(self):
        """测试错误类型枚举"""
        assert ErrorType.VARIABLE_DEFINITION.value == 'variable_definition'
        assert ErrorType.LOGIC_ERROR.value == 'logic_error'

    def test_step_validation_to_dict(self):
        """测试步骤验证转字典"""
        validation = StepValidation(
            step_id=0,
            step_content='x = 10',
            status=StepValidationStatus.CORRECT,
            confidence=0.9
        )
        
        d = validation.to_dict()
        assert d['step_id'] == 0
        assert d['status'] == 'correct'


class TestValidators:
    """测试验证器"""

    def test_variable_definition_validator(self):
        """测试变量定义验证器"""
        validator = VariableDefinitionValidator()
        
        step = {'step_id': 0, 'content': 'x = 10'}
        result = validator.validate_step(step, {})
        
        assert result.status == StepValidationStatus.CORRECT

    def test_variable_definition_invalid(self):
        """测试无效变量定义"""
        validator = VariableDefinitionValidator()
        
        step = {'step_id': 0, 'content': '123invalid = 10'}
        result = validator.validate_step(step, {})
        
        assert result.status == StepValidationStatus.INCORRECT

    def test_objective_function_validator(self):
        """测试目标函数验证器"""
        validator = ObjectiveFunctionValidator()
        
        step = {'step_id': 0, 'content': 'minimize the cost function'}
        result = validator.validate_step(step, {})
        
        assert result.status == StepValidationStatus.CORRECT

    def test_objective_function_missing(self):
        """测试缺失目标函数"""
        validator = ObjectiveFunctionValidator()
        
        step = {'step_id': 0, 'content': 'some calculation'}
        result = validator.validate_step(step, {})
        
        assert result.status == StepValidationStatus.UNKNOWN

    def test_constraint_validator(self):
        """测试约束验证器"""
        validator = ConstraintValidator()
        validator.set_constraints([
            {'text': 'x > 0', 'type': 'inequality'}
        ])
        
        step = {'step_id': 0, 'content': 'x > 0'}
        result = validator.validate_step(step, {})
        
        assert result.status == StepValidationStatus.CORRECT

    def test_logic_validator(self):
        """测试逻辑验证器"""
        validator = LogicValidator()
        
        step = {
            'step_id': 0,
            'content': 'Therefore x = 10 because step 1'
        }
        context = {'previous_steps': [{'step_id': 1}]}
        
        result = validator.validate_step(step, context)
        
        assert result.status == StepValidationStatus.CORRECT


class TestProcessRewardResult:
    """测试过程奖励结果"""

    def test_result_to_dict(self):
        """测试结果转字典"""
        validation = StepValidation(
            step_id=0,
            step_content='test',
            status=StepValidationStatus.CORRECT,
            confidence=0.9
        )
        
        result = ProcessRewardResult(
            overall_confidence=0.9,
            step_validations=[validation],
            constraint_satisfactions={'x > 0': True},
            is_valid=True,
            feedback='Good',
            improvement_suggestions=[]
        )
        
        d = result.to_dict()
        assert d['overall_confidence'] == 0.9
        assert d['is_valid'] is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
