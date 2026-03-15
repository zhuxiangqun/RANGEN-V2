"""
Skill Factory 集成服务

将 Skill Factory 创建的新技能集成到现有 RANGEN 系统中：
1. 自动注册新技能到 EnhancedSkillRegistry
2. 提供 API 接口用于工厂操作
3. 与现有技能触发系统集成
"""

import os
import time
import shutil
import dataclasses
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

from .enhanced_registry import EnhancedSkillMetadata, ToolConfig
from .skill_trigger import SkillTrigger

# 导入 Skill Factory
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
try:
    from skill_factory.factory import SkillFactory
    from skill_factory.prototypes.classifier import SkillPrototypeClassifier, PrototypeType
    from skill_factory.quality_checks.checker import SkillQualityChecker
    SKILL_FACTORY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Skill Factory not available: {e}")
    SKILL_FACTORY_AVAILABLE = False


@dataclass
class FactoryIntegrationConfig:
    """工厂集成配置"""
    output_dir: str = "./skill_factory/output"
    bundled_skills_dir: str = "./src/agents/skills/bundled"
    enable_auto_registration: bool = True
    enable_quality_checks: bool = True
    enable_prototype_classification: bool = True


class SkillFactoryIntegration:
    """
    Skill Factory 集成服务
    
    功能：
    1. 使用 Skill Factory 创建新技能
    2. 自动将生成的技能注册到现有系统
    3. 提供统一的 API 接口
    4. 与现有技能触发机制集成
    """
    
    def __init__(self, config: Optional[FactoryIntegrationConfig] = None):
        self.config = config or FactoryIntegrationConfig()
        
        if not SKILL_FACTORY_AVAILABLE:
            raise ImportError("Skill Factory is not available. Please ensure skill_factory module is installed.")
        
        # 初始化 Skill Factory
        self.factory = SkillFactory()
        
        # 确保输出目录存在
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # 初始化技能注册表引用（将在使用时动态获取）
        self._skill_registry = None
        self._skill_trigger = None
    
    def _get_skill_registry(self):
        """获取技能注册表（延迟初始化）"""
        if self._skill_registry is None:
            from .enhanced_registry import get_enhanced_skill_registry
            self._skill_registry = get_enhanced_skill_registry()
        return self._skill_registry
    
    def _get_skill_trigger(self):
        """获取技能触发器（延迟初始化）"""
        if self._skill_trigger is None:
            from .skill_trigger import get_skill_trigger
            self._skill_trigger = get_skill_trigger()
        return self._skill_trigger
    
    def create_and_register_skill(self, requirements: Dict[str, Any], skill_name: str) -> Dict[str, Any]:
        """
        创建并注册新技能
        
        Args:
            requirements: 技能需求描述
            skill_name: 技能名称
            
        Returns:
            创建结果（包含元数据和状态）
        """
        if not SKILL_FACTORY_AVAILABLE:
            return {
                "success": False,
                "error": "Skill Factory is not available",
                "skill_name": skill_name
            }
        
        try:
            # 1. 使用 Skill Factory 创建技能
            print(f"使用 Skill Factory 创建技能: {skill_name}")
            result = self.factory.create_skill(requirements, self.config.output_dir)
            
            if not result.success:
                return {
                    "success": False,
                    "error": f"Skill Factory failed: {result.error}",
                    "skill_name": skill_name
                }
            
            # 2. 验证生成的技能文件
            skill_dir = Path(self.config.output_dir) / skill_name
            if not skill_dir.exists():
                return {
                    "success": False,
                    "error": f"Generated skill directory not found: {skill_dir}",
                    "skill_name": skill_name
                }
            
            # 3. 运行质量检查
            if self.config.enable_quality_checks:
                from skill_factory.quality_checks.checker import SkillQualityChecker
                checker = SkillQualityChecker()
                quality_report = checker.check_skill(str(skill_dir))
                
                if quality_report.overall_status.value != "passed":
                    # 收集失败的错误信息
                    failed_checks = [check for check in quality_report.checks if check.status.value == "failed"]
                    error_messages = [check.message for check in failed_checks]
                    
                    return {
                        "success": False,
                        "error": f"Quality check failed: {', '.join(error_messages)}",
                        "skill_name": skill_name,
                        "quality_report": self._quality_report_to_dict(quality_report)
                    }
            
            # 4. 复制到 bundled_skills 目录
            bundled_skill_dir = Path(self.config.bundled_skills_dir) / skill_name
            if bundled_skill_dir.exists():
                # 备份现有技能
                backup_dir = bundled_skill_dir.with_suffix(f".backup.{int(time.time())}")
                shutil.move(str(bundled_skill_dir), str(backup_dir))
            
            shutil.copytree(str(skill_dir), str(bundled_skill_dir))
            
            # 5. 触发技能注册表重新加载
            if self.config.enable_auto_registration:
                self._register_skill_to_registry(str(bundled_skill_dir))
            
            return {
                "success": True,
                "skill_name": skill_name,
                "prototype_type": result.prototype.value if hasattr(result.prototype, 'value') else str(result.prototype),
                "skill_dir": str(bundled_skill_dir),
                "quality_report": self._quality_report_to_dict(quality_report) if self.config.enable_quality_checks and quality_report else None,
                "factory_result": self._factory_result_to_dict(result)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating and registering skill: {str(e)}",
                "skill_name": skill_name
            }
    
    def _register_skill_to_registry(self, skill_dir: str):
        """
        注册技能到增强版注册表
        
        Note: EnhancedSkillRegistry 会自动扫描 bundled_skills 目录，
              所以我们只需要触发重新加载即可
        """
        # 由于 EnhancedSkillRegistry 在初始化时已经加载了所有技能，
        # 而新技能文件已经复制到 bundled_skills 目录，
        # 我们需要重新初始化注册表或触发重新扫描
        
        # 当前实现中，EnhancedSkillRegistry 是单例且不会自动重新加载
        # 我们可以创建一个新的注册表实例或添加重新加载方法
        # 暂时先记录日志，后续可以增强注册表的功能
        print(f"Skill registered to bundled_skills directory: {skill_dir}")
        print("Note: EnhancedSkillRegistry may need to be restarted to load the new skill")
    
    def analyze_and_classify_requirements(self, requirements_text: str) -> Dict[str, Any]:
        """
        分析需求文本并分类技能原型
        
        Args:
            requirements_text: 需求描述文本
            
        Returns:
            分析结果（原型分类和详细分析）
        """
        if not SKILL_FACTORY_AVAILABLE:
            return {
                "success": False,
                "error": "Skill Factory is not available",
                "analysis": None
            }
        
        try:
            # 使用 Skill Factory 的分类器
            classifier = SkillPrototypeClassifier()
            
            # 使用 classify 方法分析需求
            classification_result = classifier.classify(requirements_text)
            
            # 将 ClassificationResult 转换为字典
            analysis_result = {
                "prototype_type": classification_result.prototype.value,
                "confidence": classification_result.confidence,
                "decision_path": classification_result.decision_path,
                "reasoning": classification_result.reasoning,
                "template_suggestions": classification_result.template_suggestions
            }
            
            return {
                "success": True,
                "analysis": analysis_result,
                "recommended_prototype": classification_result.prototype.value,
                "confidence": classification_result.confidence
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error analyzing requirements: {str(e)}",
                "analysis": None
            }
    
    def get_available_prototypes(self) -> List[Dict[str, Any]]:
        """
        获取可用的技能原型列表
        
        Returns:
            原型列表
        """
        if not SKILL_FACTORY_AVAILABLE:
            return []
        
        prototypes = []
        for prototype in PrototypeType:
            prototypes.append({
                "id": prototype.value,
                "name": prototype.value,
                "description": self._get_prototype_description(prototype),
                "use_cases": self._get_prototype_use_cases(prototype)
            })
        
        return prototypes
    
    def _get_prototype_description(self, prototype: PrototypeType) -> str:
        """获取原型描述"""
        descriptions = {
            PrototypeType.WORKFLOW: "包含明确、有序工作流程阶段的技能",
            PrototypeType.EXPERT: "需要深度专业知识和复杂决策的技能",
            PrototypeType.COORDINATOR: "协调多个子任务或资源的技能",
            PrototypeType.QUALITY_GATE: "专注于质量验证和检查的技能",
            PrototypeType.MCP_INTEGRATION: "集成外部MCP工具或API的技能"
        }
        return descriptions.get(prototype, "未知原型")
    
    def _get_prototype_use_cases(self, prototype: PrototypeType) -> List[str]:
        """获取原型用例"""
        use_cases = {
            PrototypeType.WORKFLOW: [
                "多步骤数据处理",
                "顺序执行任务",
                "工作流自动化"
            ],
            PrototypeType.EXPERT: [
                "专业领域咨询",
                "复杂问题解决",
                "深度分析报告"
            ],
            PrototypeType.COORDINATOR: [
                "多智能体协作",
                "资源分配调度",
                "任务分解协调"
            ],
            PrototypeType.QUALITY_GATE: [
                "代码质量检查",
                "文档验证",
                "安全合规审计"
            ],
            PrototypeType.MCP_INTEGRATION: [
                "外部API集成",
                "第三方工具调用",
                "数据源连接"
            ]
        }
        return use_cases.get(prototype, [])
    
    def run_quality_check(self, skill_dir: str) -> Dict[str, Any]:
        """
        运行质量检查
        
        Args:
            skill_dir: 技能目录路径
            
        Returns:
            质量检查报告
        """
        if not SKILL_FACTORY_AVAILABLE:
            return {
                "success": False,
                "error": "Skill Factory is not available",
                "report": None
            }
        
        try:
            from skill_factory.quality_checks.checker import SkillQualityChecker
            checker = SkillQualityChecker()
            report = checker.check_skill(skill_dir)
            
            return {
                "success": True,
                "report": self._quality_report_to_dict(report),
                "passed": report.overall_status.value == "passed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error running quality check: {str(e)}",
                "report": None
            }
    
    def _quality_report_to_dict(self, report) -> Dict[str, Any]:
        """将QualityReport转换为字典"""
        return {
            "skill_dir": report.skill_dir,
            "overall_status": report.overall_status.value,
            "summary": report.summary,
            "checks": [
                {
                    "name": check.name,
                    "status": check.status.value,
                    "message": check.message
                }
                for check in report.checks
            ],
            "recommendations": report.recommendations
        }
    
    def _factory_result_to_dict(self, result) -> Dict[str, Any]:
        """将SkillFactoryResult转换为字典"""
        return {
            "success": result.success,
            "skill_id": result.skill_id,
            "prototype": result.prototype.value if hasattr(result.prototype, 'value') else str(result.prototype),
            "skill_dir": result.skill_dir,
            "development_stages": [
                {
                    "name": stage.name,
                    "status": stage.status,
                    "start_time": str(stage.start_time) if stage.start_time else None,
                    "end_time": str(stage.end_time) if stage.end_time else None,
                    "artifacts": stage.artifacts,
                    "notes": stage.notes
                }
                for stage in result.development_stages
            ],
            "errors": result.errors,
            "warnings": result.warnings,
            "metadata": result.metadata
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取工厂统计信息
        
        Returns:
            统计信息
        """
        if not SKILL_FACTORY_AVAILABLE:
            return {
                "success": False,
                "error": "Skill Factory is not available",
                "statistics": None
            }
        
        try:
            # 统计输出目录中的技能
            output_dir = Path(self.config.output_dir)
            skills = []
            
            if output_dir.exists():
                for item in output_dir.iterdir():
                    if item.is_dir():
                        skill_yaml = item / "skill.yaml"
                        if skill_yaml.exists():
                            skills.append(item.name)
            
            # 统计 bundled_skills 目录中的工厂生成技能
            bundled_dir = Path(self.config.bundled_skills_dir)
            bundled_skills = []
            
            if bundled_dir.exists():
                for item in bundled_dir.iterdir():
                    if item.is_dir():
                        # 检查是否有工厂生成的标记（例如：包含 factory_generated: true 的 skill.yaml）
                        skill_yaml = item / "skill.yaml"
                        if skill_yaml.exists():
                            bundled_skills.append(item.name)
            
            return {
                "success": True,
                "statistics": {
                    "total_generated": len(skills),
                    "generated_skills": skills,
                    "total_registered": len(bundled_skills),
                    "registered_skills": bundled_skills,
                    "factory_available": True
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting statistics: {str(e)}",
                "statistics": None
            }


# 全局单例
_factory_integration: Optional[SkillFactoryIntegration] = None


def get_factory_integration() -> SkillFactoryIntegration:
    """获取 Skill Factory 集成服务单例"""
    global _factory_integration
    
    if _factory_integration is None:
        config = FactoryIntegrationConfig()
        _factory_integration = SkillFactoryIntegration(config)
    
    return _factory_integration


def is_skill_factory_available() -> bool:
    """检查 Skill Factory 是否可用"""
    return SKILL_FACTORY_AVAILABLE