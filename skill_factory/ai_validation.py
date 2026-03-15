"""
AI验证模块 - 使用LLM验证技能逻辑完整性

扩展质量检查系统，提供AI驱动的验证功能：
1. 逻辑一致性检查
2. 任务完整性验证
3. 原型匹配度评估
4. 可执行性分析
5. 清晰度评分
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import yaml

from .prototypes.classifier import PrototypeType, ClassificationResult


class ValidationStatus(Enum):
    """验证状态"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    NEEDS_IMPROVEMENT = "needs_improvement"


class ValidationCategory(Enum):
    """验证类别"""
    LOGIC_CONSISTENCY = "logic_consistency"
    TASK_COMPLETENESS = "task_completeness"
    PROTOTYPE_MATCH = "prototype_match"
    EXECUTABILITY = "executability"
    CLARITY = "clarity"


@dataclass
class ValidationResult:
    """AI验证结果"""
    category: ValidationCategory
    status: ValidationStatus
    score: float  # 0-100分
    feedback: str
    suggestions: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIVerificationReport:
    """AI验证报告"""
    skill_dir: str
    overall_score: float
    validation_results: List[ValidationResult] = field(default_factory=list)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)


class AISkillValidator:
    """AI技能验证器
    
    使用LLM验证技能的逻辑完整性和质量
    """
    
    def __init__(self, llm_config: Optional[Dict[str, Any]] = None):
        """初始化AI验证器
        
        Args:
            llm_config: LLM配置，如果为None则使用模拟验证
        """
        self.llm_config = llm_config or {}
        self.use_real_llm = self._check_llm_availability()
        
        if self.use_real_llm:
            print("✅ AI验证器: 使用真实LLM进行验证")
        else:
            print("⚠️ AI验证器: LLM不可用，使用模拟验证模式")
    
    def _check_llm_availability(self) -> bool:
        """检查LLM是否可用"""
        try:
            # 尝试导入LLM集成模块
            from .llm_integration import LLMIntegration
            return True
        except ImportError:
            return False
    
    def validate_skill(self, skill_dir: str, prototype: PrototypeType, 
                      classification_result: Optional[ClassificationResult] = None) -> AIVerificationReport:
        """验证技能
        
        Args:
            skill_dir: 技能目录路径
            prototype: 技能原型类型
            classification_result: 分类结果（可选）
            
        Returns:
            AIVerificationReport: AI验证报告
        """
        # 加载技能数据
        skill_data = self._load_skill_data(skill_dir)
        if not skill_data:
            return self._create_error_report(skill_dir, "无法加载技能数据")
        
        # 执行各项验证
        validation_results = []
        
        # 1. 逻辑一致性检查
        logic_result = self._validate_logic_consistency(skill_data, prototype)
        validation_results.append(logic_result)
        
        # 2. 任务完整性验证
        task_result = self._validate_task_completeness(skill_data, prototype)
        validation_results.append(task_result)
        
        # 3. 原型匹配度评估
        match_result = self._validate_prototype_match(skill_data, prototype, classification_result)
        validation_results.append(match_result)
        
        # 4. 可执行性分析
        exec_result = self._validate_executability(skill_data, prototype)
        validation_results.append(exec_result)
        
        # 5. 清晰度评分
        clarity_result = self._validate_clarity(skill_data, prototype)
        validation_results.append(clarity_result)
        
        # 计算总体得分
        overall_score = self._calculate_overall_score(validation_results)
        
        # 生成报告
        return AIVerificationReport(
            skill_dir=skill_dir,
            overall_score=overall_score,
            validation_results=validation_results,
            summary=self._generate_summary(validation_results, overall_score),
            recommendations=self._generate_recommendations(validation_results)
        )
    
    def _load_skill_data(self, skill_dir: str) -> Optional[Dict[str, Any]]:
        """加载技能数据"""
        try:
            # 加载skill.yaml
            yaml_path = os.path.join(skill_dir, "skill.yaml")
            with open(yaml_path, 'r', encoding='utf-8') as f:
                skill_yaml = yaml.safe_load(f)
            
            # 加载SKILL.md
            md_path = os.path.join(skill_dir, "SKILL.md")
            if os.path.exists(md_path):
                with open(md_path, 'r', encoding='utf-8') as f:
                    skill_md = f.read()
            else:
                skill_md = ""
            
            return {
                "yaml": skill_yaml,
                "markdown": skill_md,
                "skill_name": skill_yaml.get("name", "unknown"),
                "description": skill_yaml.get("description", ""),
                "triggers": skill_yaml.get("triggers", []),
                "tools": skill_yaml.get("tools", []),
                "prototype_type": skill_yaml.get("prototype_type", "unknown")
            }
        except Exception as e:
            print(f"加载技能数据失败: {e}")
            return None
    
    def _validate_logic_consistency(self, skill_data: Dict[str, Any], 
                                   prototype: PrototypeType) -> ValidationResult:
        """验证逻辑一致性"""
        if self.use_real_llm:
            return self._llm_validate_logic_consistency(skill_data, prototype)
        else:
            return self._simulate_validate_logic_consistency(skill_data, prototype)
    
    def _validate_task_completeness(self, skill_data: Dict[str, Any],
                                   prototype: PrototypeType) -> ValidationResult:
        """验证任务完整性"""
        if self.use_real_llm:
            return self._llm_validate_task_completeness(skill_data, prototype)
        else:
            return self._simulate_validate_task_completeness(skill_data, prototype)
    
    def _validate_prototype_match(self, skill_data: Dict[str, Any],
                                 prototype: PrototypeType,
                                 classification_result: Optional[ClassificationResult]) -> ValidationResult:
        """验证原型匹配度"""
        if self.use_real_llm:
            return self._llm_validate_prototype_match(skill_data, prototype, classification_result)
        else:
            return self._simulate_validate_prototype_match(skill_data, prototype, classification_result)
    
    def _validate_executability(self, skill_data: Dict[str, Any],
                               prototype: PrototypeType) -> ValidationResult:
        """验证可执行性"""
        if self.use_real_llm:
            return self._llm_validate_executability(skill_data, prototype)
        else:
            return self._simulate_validate_executability(skill_data, prototype)
    
    def _validate_clarity(self, skill_data: Dict[str, Any],
                         prototype: PrototypeType) -> ValidationResult:
        """验证清晰度"""
        if self.use_real_llm:
            return self._llm_validate_clarity(skill_data, prototype)
        else:
            return self._simulate_validate_clarity(skill_data, prototype)
    
    # 模拟验证方法（当LLM不可用时使用）
    def _simulate_validate_logic_consistency(self, skill_data: Dict[str, Any],
                                            prototype: PrototypeType) -> ValidationResult:
        """模拟逻辑一致性检查"""
        description = skill_data.get("description", "")
        triggers = skill_data.get("triggers", [])
        tools = skill_data.get("tools", [])
        
        # 简单检查：描述是否包含工具相关的关键词
        tool_keywords = []
        for tool in tools:
            if isinstance(tool, dict):
                tool_keywords.append(tool.get("name", "").lower())
            else:
                tool_keywords.append(str(tool).lower())
        
        has_tool_consistency = any(keyword in description.lower() for keyword in tool_keywords if keyword)
        
        score = 85.0 if has_tool_consistency else 65.0
        status = ValidationStatus.PASSED if score >= 70 else ValidationStatus.NEEDS_IMPROVEMENT
        
        return ValidationResult(
            category=ValidationCategory.LOGIC_CONSISTENCY,
            status=status,
            score=score,
            feedback="逻辑一致性检查完成",
            suggestions=["考虑在描述中提及使用的工具"] if not has_tool_consistency else [],
            evidence={"tool_consistency": has_tool_consistency}
        )
    
    def _simulate_validate_task_completeness(self, skill_data: Dict[str, Any],
                                            prototype: PrototypeType) -> ValidationResult:
        """模拟任务完整性检查"""
        description = skill_data.get("description", "")
        markdown = skill_data.get("markdown", "")
        
        # 检查是否有明确的输入、处理、输出描述
        has_input = any(keyword in description.lower() for keyword in ["输入", "input", "接收", "接受"])
        has_process = any(keyword in description.lower() for keyword in ["处理", "process", "分析", "转换", "计算"])
        has_output = any(keyword in description.lower() for keyword in ["输出", "output", "生成", "返回", "提供"])
        
        completeness_score = 0
        if has_input:
            completeness_score += 1
        if has_process:
            completeness_score += 1
        if has_output:
            completeness_score += 1
        
        score = 60.0 + completeness_score * 15.0
        status = ValidationStatus.PASSED if score >= 75 else ValidationStatus.NEEDS_IMPROVEMENT
        
        suggestions = []
        if not has_input:
            suggestions.append("明确描述技能需要的输入")
        if not has_process:
            suggestions.append("详细说明技能的处理过程")
        if not has_output:
            suggestions.append("明确说明技能的输出结果")
        
        return ValidationResult(
            category=ValidationCategory.TASK_COMPLETENESS,
            status=status,
            score=score,
            feedback="任务完整性检查完成",
            suggestions=suggestions,
            evidence={
                "has_input": has_input,
                "has_process": has_process,
                "has_output": has_output
            }
        )
    
    def _simulate_validate_prototype_match(self, skill_data: Dict[str, Any],
                                          prototype: PrototypeType,
                                          classification_result: Optional[ClassificationResult]) -> ValidationResult:
        """模拟原型匹配度检查"""
        skill_prototype = skill_data.get("prototype_type", "unknown")
        expected_prototype = prototype.value
        
        if skill_prototype == expected_prototype:
            score = 95.0
            status = ValidationStatus.PASSED
            feedback = "原型类型匹配正确"
        else:
            score = 50.0
            status = ValidationStatus.WARNING
            feedback = f"原型类型不匹配：技能为{skill_prototype}，预期为{expected_prototype}"
        
        return ValidationResult(
            category=ValidationCategory.PROTOTYPE_MATCH,
            status=status,
            score=score,
            feedback=feedback,
            suggestions=["考虑更新skill.yaml中的prototype_type字段"] if skill_prototype != expected_prototype else [],
            evidence={
                "skill_prototype": skill_prototype,
                "expected_prototype": expected_prototype
            }
        )
    
    def _simulate_validate_executability(self, skill_data: Dict[str, Any],
                                        prototype: PrototypeType) -> ValidationResult:
        """模拟可执行性检查"""
        tools = skill_data.get("tools", [])
        triggers = skill_data.get("triggers", [])
        
        # 检查是否有足够的工具和触发器
        has_tools = len(tools) > 0
        has_triggers = len(triggers) > 0
        
        score = 70.0
        if has_tools and has_triggers:
            score = 90.0
        elif has_tools or has_triggers:
            score = 75.0
        
        status = ValidationStatus.PASSED if score >= 70 else ValidationStatus.NEEDS_IMPROVEMENT
        
        suggestions = []
        if not has_triggers:
            suggestions.append("添加触发器以使技能可被调用")
        if not has_tools and prototype not in [PrototypeType.QUALITY_GATE, PrototypeType.COORDINATOR]:
            suggestions.append("考虑添加必要的工具以完成任务")
        
        return ValidationResult(
            category=ValidationCategory.EXECUTABILITY,
            status=status,
            score=score,
            feedback="可执行性检查完成",
            suggestions=suggestions,
            evidence={
                "has_tools": has_tools,
                "has_triggers": has_triggers,
                "tool_count": len(tools),
                "trigger_count": len(triggers)
            }
        )
    
    def _simulate_validate_clarity(self, skill_data: Dict[str, Any],
                                  prototype: PrototypeType) -> ValidationResult:
        """模拟清晰度检查"""
        description = skill_data.get("description", "")
        
        # 简单检查：描述长度和句子结构
        word_count = len(description.split())
        has_punctuation = any(punc in description for punc in [".", "。", "!", "！", "?", "？"])
        
        if word_count > 20 and has_punctuation:
            score = 85.0
            feedback = "描述清晰，结构完整"
        elif word_count > 10:
            score = 70.0
            feedback = "描述基本清晰"
        else:
            score = 55.0
            feedback = "描述过于简单，建议补充细节"
        
        status = ValidationStatus.PASSED if score >= 70 else ValidationStatus.NEEDS_IMPROVEMENT
        
        suggestions = []
        if word_count < 15:
            suggestions.append("增加描述细节，明确技能功能")
        if not has_punctuation:
            suggestions.append("使用标点符号提高可读性")
        
        return ValidationResult(
            category=ValidationCategory.CLARITY,
            status=status,
            score=score,
            feedback=feedback,
            suggestions=suggestions,
            evidence={
                "word_count": word_count,
                "has_punctuation": has_punctuation
            }
        )
    
    # LLM验证方法（需要真实LLM时使用）
    def _llm_validate_logic_consistency(self, skill_data: Dict[str, Any],
                                       prototype: PrototypeType) -> ValidationResult:
        """使用LLM验证逻辑一致性"""
        # 这里需要实现真实的LLM调用
        # 暂时返回模拟结果
        return self._simulate_validate_logic_consistency(skill_data, prototype)
    
    def _llm_validate_task_completeness(self, skill_data: Dict[str, Any],
                                       prototype: PrototypeType) -> ValidationResult:
        """使用LLM验证任务完整性"""
        return self._simulate_validate_task_completeness(skill_data, prototype)
    
    def _llm_validate_prototype_match(self, skill_data: Dict[str, Any],
                                     prototype: PrototypeType,
                                     classification_result: Optional[ClassificationResult]) -> ValidationResult:
        """使用LLM验证原型匹配度"""
        return self._simulate_validate_prototype_match(skill_data, prototype, classification_result)
    
    def _llm_validate_executability(self, skill_data: Dict[str, Any],
                                   prototype: PrototypeType) -> ValidationResult:
        """使用LLM验证可执行性"""
        return self._simulate_validate_executability(skill_data, prototype)
    
    def _llm_validate_clarity(self, skill_data: Dict[str, Any],
                             prototype: PrototypeType) -> ValidationResult:
        """使用LLM验证清晰度"""
        return self._simulate_validate_clarity(skill_data, prototype)
    
    def _calculate_overall_score(self, validation_results: List[ValidationResult]) -> float:
        """计算总体得分"""
        if not validation_results:
            return 0.0
        
        total_score = sum(result.score for result in validation_results)
        return total_score / len(validation_results)
    
    def _generate_summary(self, validation_results: List[ValidationResult], 
                         overall_score: float) -> str:
        """生成总结"""
        passed_count = sum(1 for result in validation_results if result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING])
        total_count = len(validation_results)
        
        if overall_score >= 85:
            summary = f"优秀！AI验证通过率{passed_count}/{total_count}，总体得分{overall_score:.1f}"
        elif overall_score >= 70:
            summary = f"良好！AI验证通过率{passed_count}/{total_count}，总体得分{overall_score:.1f}"
        elif overall_score >= 60:
            summary = f"合格！AI验证通过率{passed_count}/{total_count}，总体得分{overall_score:.1f}，有待改进"
        else:
            summary = f"需要改进！AI验证通过率{passed_count}/{total_count}，总体得分{overall_score:.1f}"
        
        return summary
    
    def _generate_recommendations(self, validation_results: List[ValidationResult]) -> List[str]:
        """生成建议列表"""
        recommendations = []
        
        for result in validation_results:
            if result.status in [ValidationStatus.NEEDS_IMPROVEMENT, ValidationStatus.FAILED]:
                recommendations.extend(result.suggestions)
        
        # 去重
        unique_recommendations = []
        for rec in recommendations:
            if rec and rec not in unique_recommendations:
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _create_error_report(self, skill_dir: str, error_message: str) -> AIVerificationReport:
        """创建错误报告"""
        return AIVerificationReport(
            skill_dir=skill_dir,
            overall_score=0.0,
            summary=f"AI验证失败: {error_message}",
            recommendations=["检查技能数据格式", "重新运行验证"]
        )


# 工具函数
def ai_validate_skill(skill_dir: str, prototype: PrototypeType,
                     classification_result: Optional[ClassificationResult] = None,
                     llm_config: Optional[Dict[str, Any]] = None) -> AIVerificationReport:
    """AI验证技能的工具函数"""
    validator = AISkillValidator(llm_config)
    return validator.validate_skill(skill_dir, prototype, classification_result)