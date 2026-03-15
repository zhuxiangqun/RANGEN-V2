#!/usr/bin/env python3
"""
Skill Factory - 完整的技能工厂实现

这个文件是原始factory.py的简化版，专注于核心功能
"""

import os
import sys
import yaml
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

# 尝试导入skill_factory模块
try:
    from .prototypes.classifier import SkillPrototypeClassifier, PrototypeType, ClassificationResult
    from .quality_checks import SkillQualityChecker, CheckStatus
    from .ai_validation import AISkillValidator, AIVerificationReport, ValidationStatus
    from .quality_metrics import QualityMetricsTracker, MetricType, QualityMetric
    from .performance_monitor import PerformanceMonitor, PerformanceMetricType, ErrorType
    from .feedback_collector import FeedbackCollector, FeedbackType, FeedbackSentiment
    from .content_filler import SkillContentFiller
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

try:
    from src.services.skill_quality_evaluator import SkillQualityEvaluator, SkillData
    from src.services.skill_description_optimizer import SkillDescriptionOptimizer
    from src.services.skill_benchmark_system import SkillBenchmarkSystem
except ImportError as e:
    print(f"Warning: src.services import failed: {e}")


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
    prototype: Any
    skill_dir: str
    development_stages: List[SkillDevelopmentStage] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillFactory:
    """
    Skill Factory 主类
    
    提供完整的AI技能标准化开发流程
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化各组件
        try:
            self.classifier = SkillPrototypeClassifier()
        except:
            self.classifier = None
            
        self.content_filler = SkillContentFiller()
        
        # 开发阶段定义
        self.development_stages = [
            {"name": "需求分析", "description": "分析技能需求，明确功能范围"},
            {"name": "原型分类", "description": "使用决策树分类技能到五大原型"},
            {"name": "模板生成", "description": "根据原型生成标准化模板"},
            {"name": "内容填充", "description": "填充模板内容，实现技能逻辑"},
            {"name": "质量检查", "description": "执行自动化质量检查"},
            {"name": "部署上线", "description": "部署技能到生产环境"}
        ]
    
    def create_skill(self, requirements: Dict[str, Any], output_dir: str) -> SkillFactoryResult:
        """创建新技能"""
        skill_id = requirements.get("name", f"skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        skill_dir = os.path.join(output_dir, skill_id)
        
        # 初始化结果
        result = SkillFactoryResult(
            success=False,
            skill_id=skill_id,
            prototype=None,
            skill_dir=skill_dir,
            development_stages=[]
        )
        
        try:
            # 阶段1: 创建目录
            os.makedirs(skill_dir, exist_ok=True)
            
            # 阶段2: 模板生成 (简化版)
            self._generate_simple_template(skill_dir, requirements)
            
            # 阶段3: 内容填充 (使用我们创建的内容填充器)
            filled = self.content_filler.fill_skill(
                skill_id,
                requirements.get("prototype_type", "mcp_integration"),
                requirements
            )
            
            # 保存填充后的内容到YAML
            self._save_filled_content(skill_dir, filled)
            
            result.prototype = requirements.get("prototype_type", "mcp_integration")
            result.success = True
            result.metadata["content_filling"] = {
                "filled": True,
                "has_tools": len(filled.get("tools", [])) > 0,
                "has_triggers": len(filled.get("triggers", [])) > 0,
                "triggers": filled.get("triggers", []),
                "tools_count": len(filled.get("tools", []))
            }
            
        except Exception as e:
            result.errors.append(str(e))
        
        return result
    
    def _generate_simple_template(self, skill_dir: str, requirements: Dict[str, Any]):
        """生成简单的skill.yaml模板"""
        skill_data = {
            "name": requirements.get("name", "unknown"),
            "version": "1.0.0",
            "description": requirements.get("description", ""),
            "prototype_type": requirements.get("prototype_type", "mcp_integration"),
            "triggers": [],
            "tools": [],
            "author": "SkillFactory",
            "scope": "custom"
        }
        
        yaml_path = os.path.join(skill_dir, "skill.yaml")
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(skill_data, f, allow_unicode=True, default_flow_style=False)
        
        # 创建SKILL.md
        md_path = os.path.join(skill_dir, "SKILL.md")
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(f"# {requirements.get('name', 'Skill')}\n\n")
            f.write(f"## 描述\n{requirements.get('description', '')}\n")
    
    def _save_filled_content(self, skill_dir: str, filled: Dict[str, Any]):
        """保存填充后的内容"""
        yaml_path = os.path.join(skill_dir, "skill.yaml")
        
        # 读取现有内容
        with open(yaml_path, 'r', encoding='utf-8') as f:
            skill_data = yaml.safe_load(f) or {}
        
        # 更新内容
        if filled.get("description"):
            skill_data["description"] = filled["description"]
        if filled.get("triggers"):
            skill_data["triggers"] = filled["triggers"]
        if filled.get("tools"):
            skill_data["tools"] = filled["tools"]
        if filled.get("prompt_template"):
            skill_data["prompt_template"] = filled["prompt_template"]
        
        # 保存
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(skill_data, f, allow_unicode=True, default_flow_style=False)


# 测试
if __name__ == "__main__":
    factory = SkillFactory()
    
    # 测试创建skill
    req = {
        "name": "calculator-skill",
        "description": "数学计算工具，执行各种数学运算",
        "prototype_type": "mcp_integration"
    }
    
    result = factory.create_skill(req, "src/agents/skills/bundled")
    
    print("=" * 60)
    print("SkillFactory 测试")
    print("=" * 60)
    print(f"成功: {result.success}")
    print(f"ID: {result.skill_id}")
    print(f"目录: {result.skill_dir}")
    print(f"元数据: {result.metadata}")
    print("=" * 60)
