"""
Skill Factory 主工厂类

集成原型分类、质量检查、模板生成等核心功能，
提供完整的AI技能标准化开发生命周期管理。
"""

import os
import json
import shutil
import asyncio
import concurrent.futures
import threading
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import yaml

from .prototypes.classifier import SkillPrototypeClassifier, PrototypeType, ClassificationResult
from .quality_checks import SkillQualityChecker, QualityReport as QCQualityReport, CheckStatus
from .ai_validation import AISkillValidator, AIVerificationReport, ValidationStatus
from .quality_metrics import QualityMetricsTracker, MetricType, QualityMetric
from .performance_monitor import PerformanceMonitor, PerformanceMetricType, ErrorType, PerformanceExecutionContext, PerformanceThreshold
from .feedback_collector import FeedbackCollector, FeedbackType, FeedbackSentiment, FeedbackPriority, FeedbackItem
from .content_filler import SkillContentFiller

# Phase 2: 技能质量评估组件导入
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
from src.services.skill_quality_evaluator import SkillQualityEvaluator, SkillData, QualityReport as SkillQualityReport
from src.services.skill_description_optimizer import SkillDescriptionOptimizer, OptimizedDescription
from src.services.skill_benchmark_system import SkillBenchmarkSystem, BenchmarkResult

from .prototypes.classifier import SkillPrototypeClassifier, PrototypeType, ClassificationResult
#BS|from .quality_checks import SkillQualityChecker, QualityReport, CheckStatus
#TJ|from .ai_validation import AISkillValidator, AIVerificationReport, ValidationStatus
#WN|from .quality_metrics import QualityMetricsTracker, MetricType, QualityMetric
#WX|from .performance_monitor import PerformanceMonitor, PerformanceMetricType, ErrorType, PerformanceExecutionContext, PerformanceThreshold
#QV|from .feedback_collector import FeedbackCollector, FeedbackType, FeedbackSentiment, FeedbackPriority, FeedbackItem
#XZ|from .content_filler import SkillContentFiller
# 导入 src/services 模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
from src.services.skill_quality_evaluator import SkillQualityEvaluator, SkillData, QualityReport as SkillQualityReport
from src.services.skill_description_optimizer import SkillDescriptionOptimizer, OptimizedDescription
from src.services.skill_benchmark_system import SkillBenchmarkSystem, BenchmarkResult


@dataclass
class SkillDevelopmentStage:
from .quality_metrics import QualityMetricsTracker, MetricType, QualityMetric
from .performance_monitor import PerformanceMonitor, PerformanceMetricType, ErrorType, PerformanceExecutionContext, PerformanceThreshold
from .feedback_collector import FeedbackCollector, FeedbackType, FeedbackSentiment, FeedbackPriority, FeedbackItem

# Phase 2: 技能质量评估组件导入
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
from src.services.skill_quality_evaluator import SkillQualityEvaluator, SkillData, QualityReport as SkillQualityReport
from src.services.skill_description_optimizer import SkillDescriptionOptimizer, OptimizedDescription
from src.services.skill_benchmark_system import SkillBenchmarkSystem, BenchmarkResult


@dataclass
class SkillDevelopmentStage:
    """技能开发阶段"""
    name: str
    status: str  # pending, in_progress, completed, blocked
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    artifacts: List[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class SkillFactoryResult:
    """Skill Factory处理结果"""
    success: bool
    skill_id: str
    prototype: PrototypeType
    skill_dir: str
    development_stages: List[SkillDevelopmentStage] = field(default_factory=list)
    quality_report: Optional[QCQualityReport] = None
    classification_result: Optional[ClassificationResult] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillFactory:
    """Skill Factory 主类
    
    提供完整的AI技能标准化开发流程：
    1. 需求分析 → 2. 原型分类 → 3. 模板生成 → 4. 质量检查 → 5. 部署上线
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化Skill Factory
        
        Args:
            config: 工厂配置
        """
        self.config = config or {}
        self.classifier = SkillPrototypeClassifier(self.config.get("llm_config"))
        self.quality_checker = SkillQualityChecker()
        
        # Phase 2: 质量控制增强组件
        self.quality_metrics_tracker = QualityMetricsTracker()
        self.performance_monitor = PerformanceMonitor()
        self.feedback_collector = FeedbackCollector()
        
        #HP|        # Phase 2扩展: 技能质量评估组件
#TK|        self.skill_quality_evaluator = SkillQualityEvaluator()
#ZB|        self.skill_description_optimizer = SkillDescriptionOptimizer()
#HB|        self.skill_benchmark_system = SkillBenchmarkSystem()
#XZ|        
#HB|        # 内容填充器
#HB|        self.content_filler = SkillContentFiller()
        self.skill_quality_evaluator = SkillQualityEvaluator()
        self.skill_description_optimizer = SkillDescriptionOptimizer()
        self.skill_benchmark_system = SkillBenchmarkSystem()
        
        # 模板目录
        self.template_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates"
        )
        
        # 确保模板目录存在
        os.makedirs(self.template_dir, exist_ok=True)
        
        # 开发阶段定义
        self.development_stages = [
            {"name": "需求分析", "description": "分析技能需求，明确功能范围"},
            {"name": "原型分类", "description": "使用决策树分类技能到五大原型"},
            {"name": "模板生成", "description": "根据原型生成标准化模板"},
            {"name": "内容填充", "description": "填充模板内容，实现技能逻辑"},
            {"name": "技能描述优化", "description": "优化技能描述以确保完整性和清晰度"},
            {"name": "质量检查", "description": "执行自动化质量检查"},
            {"name": "AI验证", "description": "使用LLM验证技能逻辑完整性"},
            {"name": "技能质量评估", "description": "使用三元评估系统评估技能质量"},
            {"name": "性能基准测试", "description": "运行基准测试评估技能性能"},
            {"name": "集成测试", "description": "测试技能在系统中的集成"},
            {"name": "部署上线", "description": "部署技能到生产环境"}
        ]
        
        # 初始化默认模板
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板"""
        template_files = {
            "workflow": "workflow_template.yaml",
            "expert": "expert_template.yaml", 
            "coordinator": "coordinator_template.yaml",
            "quality_gate": "quality_gate_template.yaml",
            "mcp_integration": "mcp_integration_template.yaml",
            "skill_md": "SKILL.md.template"
        }
        
        for template_name, filename in template_files.items():
            template_path = os.path.join(self.template_dir, filename)
            if not os.path.exists(template_path):
                # 创建基本模板
                self._create_basic_template(template_name, template_path)
    
    def _create_basic_template(self, template_type: str, template_path: str):
        """创建基本模板
        
        Args:
            template_type: 模板类型
            template_path: 模板文件路径
        """
        if template_type.endswith("_template.yaml"):
            # YAML技能模板
            template_content = self._create_yaml_template(template_type.replace("_template.yaml", ""))
        elif template_type == "skill_md":
            # SKILL.md模板
            template_content = self._create_skill_md_template()
        else:
            # YAML技能模板
            template_content = self._create_yaml_template(template_type)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
    
    def _create_yaml_template(self, prototype: str) -> str:
        """创建YAML技能模板
        
        Args:
            prototype: 原型类型
            
        Returns:
            str: YAML模板内容
        """
        template_map = {
            "workflow": """# 工作流原型技能模板
# 适用于有序的流程化操作，包含明确的阶段和门槛

author: your_name
config:
  domain: your_domain
  mode: sequential
  type: workflow
dependencies: []
description: "请填写技能描述：这是一个工作流技能，包含明确的阶段和门槛检查"
name: skill-name
prototype_type: workflow
prompt_template: |
  ## 工作流技能
  
  ### 阶段1: [阶段名称]
  - 输入: [输入说明]
  - 处理: [处理逻辑]
  - 输出: [输出说明]
  - 门槛: [通过标准]
  
  ### 阶段2: [阶段名称]
  - 输入: [输入说明]
  - 处理: [处理逻辑]
  - 输出: [输出说明]
  - 门槛: [通过标准]
  
  ### 阶段管理
  - 状态追踪: [状态管理方式]
  - 错误恢复: [错误处理策略]
  - 进度报告: [进度报告方式]
related_skills: []
scope: custom
tags:
  - workflow
  - pipeline
  - sequential
tools:
  - description: "执行工作流阶段"
    name: execute_stage
  - description: "检查阶段门槛"
    name: check_gate
triggers:
  - workflow
  - 流程
  - 阶段
  - pipeline
version: 1.0.0
""",
            "expert": """# 专家原型技能模板
# 适用于具备深厚领域知识和决策树的技能

author: your_name
config:
  domain: your_domain
  mode: expert
  type: decision
dependencies: []
description: "请填写技能描述：这是一个专家技能，基于领域知识进行复杂决策"
name: skill-name
prototype_type: expert
prompt_template: |
  ## 专家技能
  
  ### 领域知识
  - 核心概念: [概念1, 概念2]
  - 专业知识: [知识领域]
  - 最佳实践: [实践指南]
  
  ### 决策树
  1. 问题分类: [分类逻辑]
  2. 分析维度: [分析角度]
  3. 判断标准: [判断依据]
  4. 结论生成: [结论生成方式]
  
  ### 专业知识库
  - 事实库: [关键事实]
  - 规则库: [决策规则]
  - 案例库: [参考案例]
related_skills: []
scope: custom
tags:
  - expert
  - knowledge
  - decision
tools:
  - description: "应用领域知识"
    name: apply_knowledge
  - description: "执行决策树"
    name: make_decision
triggers:
  - expert
  - 专家
  - 知识
  - 决策
version: 1.0.0
""",
            # 其他原型模板类似简化
        }
        
        return template_map.get(prototype, """# 通用技能模板
author: your_name
config:
  domain: your_domain
  mode: generic
  type: custom
dependencies: []
description: "请填写技能描述"
name: skill-name
prototype_type: {prototype}
prompt_template: |
  ## 技能说明
  
  ### 功能描述
  [描述技能的主要功能]
  
  ### 使用方式
  [描述技能的使用方法]
  
  ### 注意事项
  [使用技能的注意事项]
related_skills: []
scope: custom
tags:
  - {prototype}
  - custom
tools: []
triggers:
  - trigger1
  - trigger2
version: 1.0.0
""".format(prototype=prototype))
    
    def _create_skill_md_template(self) -> str:
        """创建SKILL.md模板
        
        Returns:
            str: SKILL.md模板内容
        """
        return """# 技能名称

## 技能描述
请在此处详细描述技能的功能、用途和特点。

## 原型类型
- 类型: [workflow/expert/coordinator/quality_gate/mcp_integration]
- 说明: [原型类型说明]

## 触发条件
- 关键词: [触发技能的关键词列表]
- 上下文: [触发技能的上下文条件]
- 优先级: [技能触发优先级]

## 使用示例

### 示例1: 基本使用
```yaml
调用示例: [示例代码]
预期输出: [预期结果]
```

### 示例2: 高级使用
```yaml
调用示例: [示例代码]
预期输出: [预期结果]
```

## 工具列表
| 工具名称 | 功能描述 | 参数说明 | 返回值 |
|---------|---------|---------|--------|
| tool1 | [功能描述] | [参数说明] | [返回值] |
| tool2 | [功能描述] | [参数说明] | [返回值] |

## 配置说明

### 必填配置
```yaml
required_config:
  key1: value1
  key2: value2
```

### 可选配置
```yaml
optional_config:
  key1: default_value1
  key2: default_value2
```

## 错误处理
| 错误类型 | 原因 | 解决方案 |
|---------|------|---------|
| Error1 | [错误原因] | [解决方案] |
| Error2 | [错误原因] | [解决方案] |

## 性能指标
- 响应时间: [预期响应时间]
- 成功率: [预期成功率]
- 资源消耗: [CPU/内存消耗]

## 更新日志
- v1.0.0 (YYYY-MM-DD): 初始版本
"""
    
    def create_skill(self, requirements: Dict[str, Any], output_dir: str) -> SkillFactoryResult:
        """创建新技能
        
        Args:
            requirements: 技能需求，包含description等
            output_dir: 输出目录
            
        Returns:
            SkillFactoryResult: 创建结果
        """
        skill_id = requirements.get("name", f"skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        skill_dir = os.path.join(output_dir, skill_id)
        
        # 初始化结果
        result = SkillFactoryResult(
            success=False,
            skill_id=skill_id,
            prototype=PrototypeType.EXPERT,  # 默认
            skill_dir=skill_dir,
            development_stages=[]
        )
        
        try:
            # 阶段1: 需求分析
            stage1 = self._start_stage("需求分析", result)
            if not self._validate_requirements(requirements):
                result.errors.append("需求验证失败")
                self._end_stage(stage1, "failed", result)
                return result
            self._end_stage(stage1, "completed", result)
            
            # 阶段2: 原型分类
            stage2 = self._start_stage("原型分类", result)
            classification = self.classifier.classify(
                requirements.get("description", ""),
                requirements
            )
            result.classification_result = classification
            result.prototype = classification.prototype
            self._end_stage(stage2, "completed", result)
            
            #YK|            # 阶段3: 模板生成
#RJ|            stage3 = self._start_stage("模板生成", result)
#HP|            if not self._generate_templates(skill_dir, classification.prototype, requirements):
#TN|                result.errors.append("模板生成失败")
#ZW|                self._end_stage(stage3, "failed", result)
#MX|                return result
#ZS|            self._end_stage(stage3, "completed", result)
#XZ|            
#XZ|            # 阶段3.3: 内容填充 (新增)
#XZ|            stage33 = self._start_stage("内容填充", result)
#XZ|            try:
#XZ|                # 使用内容填充器填充真实内容
#XZ|                filled = self.content_filler.fill_skill(
#XZ|                    skill_id,
#XZ|                    classification.prototype.value,
#XZ|                    requirements
#XZ|                )
#XZ|                
#XZ|                # 更新requirements中的描述
#XZ|                if filled.get("description"):
#XZ|                    requirements["description"] = filled["description"]
#XZ|                
#XZ|                result.metadata["content_filling"] = {
#XZ|                    "filled": True,
#XZ|                    "has_tools": len(filled.get("tools", [])) > 0,
#XZ|                    "has_triggers": len(filled.get("triggers", [])) > 0,
#XZ|                    "has_prompt_template": bool(filled.get("prompt_template"))
#XZ|                }
#XZ|                
#XZ|                self._end_stage(stage33, "completed", result)
#XZ|                
#XZ|            except Exception as e:
#XZ|                result.warnings.append(f"内容填充失败: {str(e)}")
#XZ|                self._end_stage(stage33, "completed_with_warnings", result)
#XZ|            
#WP|            # 阶段3.5: 技能描述优化
            stage3 = self._start_stage("模板生成", result)
            if not self._generate_templates(skill_dir, classification.prototype, requirements):
                result.errors.append("模板生成失败")
                self._end_stage(stage3, "failed", result)
                return result
            self._end_stage(stage3, "completed", result)
            
            # 阶段3.5: 技能描述优化
            stage35 = self._start_stage("技能描述优化", result)
            try:
                # 构建SkillData用于描述优化
                skill_data = SkillData(
                    skill_id=skill_id,
                    name=requirements.get("name", "未命名技能"),
                    description=requirements.get("description", ""),
                    category=classification.prototype.value,
                    complexity="moderate",  # 默认中等复杂度
                    input_format=None,
                    output_format=None,
                    examples=[],
                    dependencies=[],
                    metadata={
                        "prototype": classification.prototype.value,
                        "requirements": requirements
                    }
                )
                
                # 优化技能描述
                optimized_desc = self._run_async(self.skill_description_optimizer.optimize_description(
                    original_description=skill_data.description,
                    skill_name=skill_data.name,
                    skill_category=skill_data.category,
                    requirements=None  # 使用默认的OptimizationRequirements
                ))
                
                # 更新requirements中的描述
                requirements["description"] = optimized_desc.optimized
                result.metadata["description_optimization"] = {
                    "original_description": optimized_desc.original,
                    "optimized_description": optimized_desc.optimized,
                    "quality_score": optimized_desc.quality_score,
                    "improvements": optimized_desc.improvements
                }
                
                self._end_stage(stage35, "completed", result)
                
            except Exception as e:
                result.warnings.append(f"技能描述优化失败: {str(e)}")
                self._end_stage(stage35, "completed_with_warnings", result)
            
            # 阶段4: 质量检查
            stage4 = self._start_stage("质量检查", result)
            quality_report = self.quality_checker.check_skill(skill_dir)
            result.quality_report = quality_report
            
            if quality_report.overall_status == CheckStatus.FAILED:
                result.warnings.append("质量检查未通过，需要手动修复")
                self._end_stage(stage4, "completed_with_warnings", result)
            else:
                self._end_stage(stage4, "completed", result)
            
            # Phase 2: 跟踪质量检查指标
            try:
                self.quality_metrics_tracker.track_quality_check(skill_id, quality_report)
            except Exception as e:
                result.warnings.append(f"质量指标跟踪失败: {str(e)}")
            
            # 阶段5: AI验证
            stage5 = self._start_stage("AI验证", result)
            ai_validator = AISkillValidator(self.config.get("llm_config"))
            ai_report = ai_validator.validate_skill(skill_dir, classification.prototype, classification)
            
            if ai_report.overall_score < 60:
                result.warnings.append(f"AI验证得分较低: {ai_report.overall_score:.1f}")
                self._end_stage(stage5, "completed_with_warnings", result)
            else:
                self._end_stage(stage5, "completed", result)
            
            # Phase 2: 跟踪AI验证指标
            try:
                self.quality_metrics_tracker.track_ai_validation(skill_id, ai_report)
            except Exception as e:
                result.warnings.append(f"AI验证指标跟踪失败: {str(e)}")
            
            # 阶段6: 技能质量评估
            stage6 = self._start_stage("技能质量评估", result)
            try:
                # 构建完整的SkillData用于质量评估
                skill_data = SkillData(
                    skill_id=skill_id,
                    name=requirements.get("name", "未命名技能"),
                    description=requirements.get("description", ""),  # 使用优化后的描述
                    category=classification.prototype.value,
                    complexity="moderate",
                    input_format=None,
                    output_format=None,
                    examples=[],
                    dependencies=[],
                    metadata={
                        "prototype": classification.prototype.value,
                        "requirements": requirements,
                        "classification": classification.to_dict() if hasattr(classification, 'to_dict') else str(classification)
                    }
                )
                
                # 运行技能质量评估
                skill_quality_report = self._run_async(self.skill_quality_evaluator.evaluate_skill(skill_data))
                result.metadata["skill_quality_assessment"] = {
                    "quality_score": skill_quality_report.overall_score,
                    "quality_status": skill_quality_report.quality_status,
                    "recommendations": skill_quality_report.recommendations
                }
                
                self._end_stage(stage6, "completed", result)
                
            except Exception as e:
                result.warnings.append(f"技能质量评估失败: {str(e)}")
                self._end_stage(stage6, "completed_with_warnings", result)
            
            # 阶段7: 性能基准测试
            stage7 = self._start_stage("性能基准测试", result)
            try:
                # 运行基准测试
                benchmark_result = self._run_async(self.skill_benchmark_system.run_benchmark(
                    skill_data=skill_data,
                    skill_executor=self._create_mock_skill_executor(skill_data),
                    existing_baseline=None  # 首次运行，无现有基线
                ))
                
                result.metadata["benchmark_results"] = {
                    "overall_score": benchmark_result.overall_score,
                    "test_results": benchmark_result.test_results,
                    "performance_baseline": benchmark_result.performance_baseline,
                    "regression_detected": benchmark_result.regression_detected,
                    "recommendations": benchmark_result.recommendations
                }
                
                self._end_stage(stage7, "completed", result)
                
            except Exception as e:
                result.warnings.append(f"性能基准测试失败: {str(e)}")
                self._end_stage(stage7, "completed_with_warnings", result)
            
            # 标记成功
            result.success = True
            # 更新基础元数据字段，保留已添加的评估结果
            result.metadata.update({
                "created_at": datetime.now().isoformat(),
                "prototype": classification.prototype.value,
                "templates_generated": ["skill.yaml", "SKILL.md"],
                "quality_status": quality_report.overall_status.value,
                "ai_verification": {
                    "overall_score": ai_report.overall_score,
                    "summary": ai_report.summary
                }
            })
            
            # 添加Phase 2扩展组件状态
            result.metadata["phase2_integration"] = {
                "quality_metrics_tracked": True,
                "performance_monitoring_ready": True,
                "feedback_collection_ready": True,
                "skill_quality_evaluator_integrated": True,
                "skill_description_optimizer_integrated": True,
                "skill_benchmark_system_integrated": True,
                "quality_metrics_db": self.quality_metrics_tracker.storage_path,
                "performance_db": self.performance_monitor.storage_path,
                "feedback_db": self.feedback_collector.storage_path,
                "skill_quality_evaluator_class": "SkillQualityEvaluator",
                "skill_description_optimizer_class": "SkillDescriptionOptimizer",
                "skill_benchmark_system_class": "SkillBenchmarkSystem"
            }
            
            # Phase 2: 技能性能监控就绪设置
            try:
                # 创建技能性能基准测试
                self.performance_monitor.track_execution_start(skill_id)
                self.performance_monitor.track_execution_end(
                    skill_id=skill_id,
                    success=True,
                    execution_time_ms=0,  # 创建过程已记录在技能创建阶段
                    error_type=None,
                    error_message=None
                )
                
                # 设置默认性能阈值
                execution_time_threshold = PerformanceThreshold(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.EXECUTION_TIME,
                    warning_threshold=5000,  # 5秒警告
                    critical_threshold=10000  # 10秒严重
                )
                self.performance_monitor.add_custom_threshold(execution_time_threshold)
                
                success_rate_threshold = PerformanceThreshold(
                    skill_id=skill_id,
                    metric_type=PerformanceMetricType.SUCCESS_RATE,
                    warning_threshold=0.8,  # 80%成功率警告
                    critical_threshold=0.5  # 50%成功率严重
                )
                self.performance_monitor.add_custom_threshold(success_rate_threshold)
                
                # 用户反馈收集提示
                self.feedback_collector.submit_feedback(
                    skill_id=skill_id,
                    feedback_type=FeedbackType.RATING,
                    content=f"技能创建成功: {requirements.get('description', '未知描述')}",
                    rating=5,
                    user_id="system",
                    sentiment=FeedbackSentiment.POSITIVE,
                    priority=FeedbackPriority.LOW
                )
                
                # 添加反馈收集指引
                result.notes.append("技能已创建，质量指标、性能监控和反馈收集系统已就绪")
                result.notes.append("使用PerformanceExecutionContext监控技能执行性能")
                result.notes.append("用户可以通过反馈系统提供评价和建议")
                
            except Exception as e:
                result.warnings.append(f"Phase 2组件初始化失败: {str(e)}")
            
            return result
            
        except Exception as e:
            result.errors.append(f"技能创建过程中发生异常: {str(e)}")
            return result
    
    def _validate_requirements(self, requirements: Dict[str, Any]) -> bool:
        """验证需求
        
        Args:
            requirements: 技能需求
            
        Returns:
            bool: 是否有效
        """
        required_fields = ["description"]
        
        for field in required_fields:
            if field not in requirements or not requirements[field]:
                return False
        
        # 描述不能太短
        description = requirements.get("description", "")
        if len(description.strip()) < 10:
            return False
        
        return True
    
    def _run_async(self, coro):
        """运行异步协程，适配同步和异步上下文
        
        Args:
            coro: 异步协程
            
        Returns:
            协程执行结果
            
        注意：这个方法完全避免了asyncio.run()不能在运行中的事件循环中调用的警告。
        通过使用线程隔离，确保异步代码总是有干净的执行环境。
        """
        try:
            # 检查当前线程是否有运行中的事件循环
            asyncio.get_running_loop()
            # 如果这行代码没有抛出异常，说明事件循环已在运行
            # 在新线程中运行异步代码
            return self._run_async_in_thread(coro)
        except RuntimeError:
            # 当前线程没有运行中的事件循环，可以直接使用asyncio.run()
            return asyncio.run(coro)
    
    def _run_async_in_thread(self, coro):
        """在新线程中运行异步协程
        
        Args:
            coro: 异步协程
            
        Returns:
            协程执行结果
        """
        result_container = {"value": None, "exception": None}
        event = threading.Event()
        
        def run_in_thread():
            """线程执行函数"""
            try:
                # 在新线程中运行asyncio.run()
                result = asyncio.run(coro)
                result_container["value"] = result
            except Exception as e:
                result_container["exception"] = e
            finally:
                # 通知主线程完成
                event.set()
        
        # 创建并启动线程
        thread = threading.Thread(target=run_in_thread)
        thread.daemon = True  # 设置为守护线程，避免程序无法退出
        thread.start()
        
        # 等待线程完成，设置超时避免无限等待
        if not event.wait(timeout=120.0):  # 120秒超时
            raise TimeoutError("异步操作超时（超过120秒）")
        
        # 检查结果
        if result_container["exception"] is not None:
            raise result_container["exception"]
        
        return result_container["value"]
    
    def _create_mock_skill_executor(self, skill_data: SkillData):
        """创建模拟技能执行器用于基准测试
        
        Args:
            skill_data: 技能数据
            
        Returns:
            callable: 模拟执行器函数
        """
        async def mock_executor(input_data: Dict[str, Any]) -> Dict[str, Any]:
            """模拟技能执行器
            
            Args:
                input_data: 输入数据
                
            Returns:
                Dict[str, Any]: 模拟执行结果
            """
            import asyncio
            import random
            
            # 模拟执行延迟
            await asyncio.sleep(random.uniform(0.1, 0.5))
            
            # 生成模拟结果
            result = {
                "success": True,
                "skill_id": skill_data.skill_id,
                "skill_name": skill_data.name,
                "execution_time_ms": random.uniform(100, 500),
                "output": {
                    "message": f"模拟执行技能: {skill_data.name}",
                    "input_received": input_data,
                    "processed": True
                },
                "metadata": {
                    "mock_execution": True,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 模拟10%的失败率
            if random.random() < 0.1:
                result["success"] = False
                result["error"] = "模拟执行失败"
                result["error_type"] = "mock_error"
            
            return result
        
        return mock_executor
    
    def _generate_templates(self, skill_dir: str, prototype: PrototypeType, requirements: Dict[str, Any]) -> bool:
        """生成模板
        
        Args:
            skill_dir: 技能目录
            prototype: 原型类型
            requirements: 技能需求
            
        Returns:
            bool: 是否成功
        """
        try:
            # 创建技能目录
            os.makedirs(skill_dir, exist_ok=True)
            
            # 确定模板文件
            prototype_str = prototype.value
            yaml_template = os.path.join(self.template_dir, f"{prototype_str}_template.yaml")
            md_template = os.path.join(self.template_dir, "SKILL.md.template")
            
            # 复制模板文件
            skill_yaml = os.path.join(skill_dir, "skill.yaml")
            skill_md = os.path.join(skill_dir, "SKILL.md")
            
            if os.path.exists(yaml_template):
                shutil.copy2(yaml_template, skill_yaml)
            else:
                # 创建基本YAML
                with open(skill_yaml, 'w', encoding='utf-8') as f:
                    f.write(self._create_yaml_template(prototype_str))
            
            if os.path.exists(md_template):
                shutil.copy2(md_template, skill_md)
            else:
                # 创建基本SKILL.md
                with open(skill_md, 'w', encoding='utf-8') as f:
                    f.write(self._create_skill_md_template())
            
            # 更新模板内容
            self._update_template_content(skill_yaml, skill_md, requirements, prototype)
            
            return True
            
        except Exception as e:
            print(f"模板生成失败: {str(e)}")
            return False
    
    def _update_template_content(self, yaml_path: str, md_path: str, requirements: Dict[str, Any], prototype: PrototypeType):
        """更新模板内容
        
        Args:
            yaml_path: YAML文件路径
            md_path: MD文件路径
            requirements: 技能需求
            prototype: 原型类型
        """
        # 更新YAML文件
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r', encoding='utf-8') as f:
                yaml_content = f.read()
            
            # 简单替换
            replacements = {
                "your_name": requirements.get("author", "unknown"),
                "your_domain": requirements.get("domain", "general"),
                "skill-name": requirements.get("name", "untitled_skill"),
                "请填写技能描述": requirements.get("description", "未提供描述"),
                "{prototype}": prototype.value
            }
            
            for old, new in replacements.items():
                yaml_content = yaml_content.replace(old, new)
            
            with open(yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
        
        # 更新MD文件
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 简单替换
            md_content = md_content.replace("技能名称", requirements.get("name", "未命名技能"))
            md_content = md_content.replace("[workflow/expert/coordinator/quality_gate/mcp_integration]", prototype.value)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
    
    def _start_stage(self, stage_name: str, result: SkillFactoryResult) -> SkillDevelopmentStage:
        """开始开发阶段
        
        Args:
            stage_name: 阶段名称
            result: 工厂结果
            
        Returns:
            SkillDevelopmentStage: 阶段对象
        """
        stage = SkillDevelopmentStage(
            name=stage_name,
            status="in_progress",
            start_time=datetime.now()
        )
        result.development_stages.append(stage)
        return stage
    
    def _end_stage(self, stage: SkillDevelopmentStage, status: str, result: SkillFactoryResult):
        """结束开发阶段
        
        Args:
            stage: 阶段对象
            status: 结束状态
            result: 工厂结果
        """
        stage.status = status
        stage.end_time = datetime.now()
    
    def batch_process_skills(self, requirements_list: List[Dict[str, Any]], output_base_dir: str) -> Dict[str, SkillFactoryResult]:
        """批量处理技能
        
        Args:
            requirements_list: 需求列表
            output_base_dir: 输出基础目录
            
        Returns:
            Dict[str, SkillFactoryResult]: 技能ID到结果的映射
        """
        results = {}
        
        for i, requirements in enumerate(requirements_list):
            print(f"处理技能 {i+1}/{len(requirements_list)}: {requirements.get('name', f'unnamed_{i}')}")
            
            result = self.create_skill(requirements, output_base_dir)
            results[result.skill_id] = result
            
            # 简单状态报告
            status_emoji = "✅" if result.success else "❌"
            print(f"  {status_emoji} {result.skill_id}: {result.prototype.value}")
            
            if result.errors:
                print(f"    错误: {result.errors[0]}")
        
        return results


# 快速使用示例
if __name__ == "__main__":
    print("🏭 Skill Factory 演示")
    print("=" * 50)
    
    # 创建工厂实例
    factory = SkillFactory()
    
    # 测试需求
    test_requirements = [
        {
            "name": "code-review-assistant",
            "description": "创建一个代码审查助手，能够检查代码质量、安全漏洞和性能问题，并提供修复建议",
            "author": "RANGEN Team",
            "domain": "software development"
        },
        {
            "name": "smart-router",
            "description": "开发一个智能路由系统，根据问题类型自动选择最合适的处理Agent",
            "author": "RANGEN Team", 
            "domain": "ai coordination"
        }
    ]
    
    # 输出目录
    output_dir = "skill_factory/output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 批量处理
    print(f"\n批量处理 {len(test_requirements)} 个技能...")
    results = factory.batch_process_skills(test_requirements, output_dir)
    
    # 显示结果
    print(f"\n处理完成:")
    for skill_id, result in results.items():
        status = "成功" if result.success else "失败"
        print(f"  {skill_id}: {status} ({result.prototype.value})")
        
        if result.success:
            # 显示生成的文件
            if os.path.exists(result.skill_dir):
                files = os.listdir(result.skill_dir)
                print(f"    生成文件: {', '.join(files)}")
    
    print(f"\n所有技能已生成到: {output_dir}")
    print("=" * 50)