#!/usr/bin/env python3
"""
Component Design Review - 组件设计专项审查

支持三种组件类型的专项审查:
1. Agent - 智能体
2. Skill - 技能
3. Tool - 工具

每种类型有不同的审查维度

Usage:
    from src.agents.component_design_review import ComponentDesignReview
    
    review = ComponentDesignReview()
    
    # Agent 审查
    result = review.review_design(design, component_type="agent")
    
    # Skill 审查
    result = review.review_design(design, component_type="skill")
    
    # Tool 审查
    result = review.review_design(design, component_type="tool")
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """组件类型"""
    AGENT = "agent"
    SKILL = "skill"
    TOOL = "tool"
    UNKNOWN = "unknown"


class ReviewDimension(Enum):
    """审查维度"""
    # Agent 维度
    DEFINITION = "definition"
    CAPABILITY = "capability"
    INTEGRATION = "integration"
    SECURITY = "security"
    IMPLEMENTATION = "implementation"
    
    # Skill 维度
    TRIGGER = "trigger"
    WORKFLOW = "workflow"
    TOOL_COMPOSITION = "tool_composition"
    
    # Tool 维度
    PARAMETERS = "parameters"
    ERROR_HANDLING = "error_handling"
    RETURN_VALUE = "return_value"
    SAFETY = "safety"


class IssueSeverity(Enum):
    """问题严重程度"""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ReviewIssue:
    """审查问题"""
    dimension: str
    severity: IssueSeverity
    title: str
    description: str
    suggestion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion
        }


@dataclass
class ReviewResult:
    """审查结果"""
    component_type: str
    component_name: str
    is_approved: bool
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    issues: List[ReviewIssue] = field(default_factory=list)
    
    @property
    def blockers(self) -> List[ReviewIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.BLOCKER]
    
    @property
    def criticals(self) -> List[ReviewIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]
    
    @property
    def warnings(self) -> List[ReviewIssue]:
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]
    
    def __post_init__(self):
        self.is_approved = len(self.blockers) == 0 and len(self.criticals) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "component_name": self.component_name,
            "is_approved": self.is_approved,
            "dimension_scores": self.dimension_scores,
            "blockers_count": len(self.blockers),
            "criticals_count": len(self.criticals),
            "warnings_count": len(self.warnings),
            "issues": [i.to_dict() for i in self.issues]
        }


class ComponentDesignReview:
    """
    组件设计专项审查器
    
    根据组件类型进行针对性审查:
    - Agent: 职责、能力、集成、安全
    - Skill: 触发、工作流、工具组合
    - Tool: 参数、错误处理、安全
    """
    
    def __init__(self):
        self._current_result: Optional[ReviewResult] = None
        logger.info("ComponentDesignReview 初始化")
    
    def detect_component_type(self, design: Any) -> ComponentType:
        """检测组件类型"""
        title = getattr(design, 'title', '') or ''
        overview = getattr(design, 'overview', '') or ''
        architecture = getattr(design, 'architecture', '') or ''
        content = (title + overview + architecture).lower()
        
        # Agent 关键词
        agent_keywords = ["agent", "智能体", "reasoning", "推理", "决策", "coordinator"]
        if any(kw in content for kw in agent_keywords):
            return ComponentType.AGENT
        
        # Skill 关键词
        skill_keywords = ["skill", "技能", "workflow", "工作流", "trigger", "触发", "compose"]
        if any(kw in content for kw in skill_keywords):
            return ComponentType.SKILL
        
        # Tool 关键词
        tool_keywords = ["tool", "工具", "function", "api", "endpoint", "接口"]
        if any(kw in content for kw in tool_keywords):
            return ComponentType.TOOL
        
        return ComponentType.UNKNOWN
    
    def review_design(self, design: Any, component_type: Optional[str] = None) -> ReviewResult:
        """
        审查组件设计
        
        Args:
            design: 设计对象
            component_type: 组件类型 (agent/skill/tool)，如果为 None 则自动检测
            
        Returns:
            ReviewResult: 审查结果
        """
        # 自动检测或使用指定类型
        if component_type is None:
            detected = self.detect_component_type(design)
            component_type = detected.value
        
        name = getattr(design, 'title', 'Unknown') or 'Unknown'
        
        result = ReviewResult(
            component_type=component_type,
            component_name=name,
            is_approved=False
        )
        
        # 根据类型选择审查方法
        if component_type == "agent":
            self._review_agent(design, result)
        elif component_type == "skill":
            self._review_skill(design, result)
        elif component_type == "tool":
            self._review_tool(design, result)
        else:
            self._review_generic(design, result)
        
        # 计算维度分数
        result.dimension_scores = self._calculate_scores(result.issues)
        
        self._current_result = result
        return result
    
    def _review_agent(self, design: Any, result: ReviewResult):
        """审查 Agent 设计"""
        issues = []
        
        # 1. Agent 定义审查
        issues.extend(self._review_agent_definition(design))
        
        # 2. 能力定义审查
        issues.extend(self._review_agent_capability(design))
        
        # 3. 集成点审查
        issues.extend(self._review_agent_integration(design))
        
        # 4. 安全约束审查
        issues.extend(self._review_agent_security(design))
        
        # 5. 实现计划审查
        issues.extend(self._review_agent_implementation(design))
        
        result.issues = issues
    
    def _review_agent_definition(self, design: Any) -> List[ReviewIssue]:
        """Agent 定义审查"""
        issues = []
        title = getattr(design, 'title', '') or ''
        
        if len(title) < 3:
            issues.append(ReviewIssue(
                dimension="definition",
                severity=IssueSeverity.BLOCKER,
                title="Agent 名称缺失",
                description="Agent 必须有明确的名称",
                suggestion="提供有意义的 Agent 名称"
            ))
        
        overview = getattr(design, 'overview', '') or ''
        if not overview:
            issues.append(ReviewIssue(
                dimension="definition",
                severity=IssueSeverity.CRITICAL,
                title="缺少功能描述",
                description="Agent 的核心功能必须有描述",
                suggestion="在 overview 中描述 Agent 功能"
            ))
        
        return issues
    
    def _review_agent_capability(self, design: Any) -> List[ReviewIssue]:
        """Agent 能力审查"""
        issues = []
        components = getattr(design, 'components', []) or []
        file_structure = getattr(design, 'file_structure', []) or []
        
        if len(components) == 0 and len(file_structure) == 0:
            issues.append(ReviewIssue(
                dimension="capability",
                severity=IssueSeverity.BLOCKER,
                title="缺少能力定义",
                description="必须定义 Agent 的能力 (Tools/Skills)",
                suggestion="在 components 中定义 Agent 能力"
            ))
        
        return issues
    
    def _review_agent_integration(self, design: Any) -> List[ReviewIssue]:
        """Agent 集成审查"""
        issues = []
        overview = getattr(design, 'overview', '') or ''
        content = overview.lower()
        
        if 'agent' in content and 'integration' not in content:
            issues.append(ReviewIssue(
                dimension="integration",
                severity=IssueSeverity.WARNING,
                title="缺少集成点说明",
                description="应说明与其他 Agent 的交互方式",
                suggestion="添加集成点描述"
            ))
        
        return issues
    
    def _review_agent_security(self, design: Any) -> List[ReviewIssue]:
        """Agent 安全审查"""
        issues = []
        risks = getattr(design, 'risks', []) or []
        overview = getattr(design, 'overview', '') or ''
        content = overview.lower()
        
        security_keywords = ["安全", "security", "permission", "auth"]
        if not any(kw in content for kw in security_keywords):
            issues.append(ReviewIssue(
                dimension="security",
                severity=IssueSeverity.CRITICAL,
                title="缺少安全约束",
                description="Agent 必须有安全约束",
                suggestion="添加权限和安全约束定义"
            ))
        
        if len(risks) == 0:
            issues.append(ReviewIssue(
                dimension="security",
                severity=IssueSeverity.WARNING,
                title="缺少风险评估",
                description="建议评估 Agent 的潜在风险",
                suggestion="添加 risks 列表"
            ))
        
        return issues
    
    def _review_agent_implementation(self, design: Any) -> List[ReviewIssue]:
        """Agent 实现审查"""
        issues = []
        file_structure = getattr(design, 'file_structure', []) or []
        
        if len(file_structure) == 0:
            issues.append(ReviewIssue(
                dimension="implementation",
                severity=IssueSeverity.BLOCKER,
                title="缺少文件结构",
                description="必须提供文件结构",
                suggestion="定义完整的文件结构"
            ))
        
        has_test = any('test' in f.lower() for f in file_structure)
        if not has_test:
            issues.append(ReviewIssue(
                dimension="implementation",
                severity=IssueSeverity.CRITICAL,
                title="缺少测试计划",
                description="Agent 必须有测试计划 (TDD)",
                suggestion="添加 tests/ 目录"
            ))
        
        return issues
    
    def _review_skill(self, design: Any, result: ReviewResult):
        """审查 Skill 设计"""
        issues = []
        
        # 1. 触发条件审查
        issues.extend(self._review_skill_trigger(design))
        
        # 2. 工作流审查
        issues.extend(self._review_skill_workflow(design))
        
        # 3. 工具组合审查
        issues.extend(self._review_skill_composition(design))
        
        # 4. 实现审查
        issues.extend(self._review_skill_implementation(design))
        
        result.issues = issues
    
    def _review_skill_trigger(self, design: Any) -> List[ReviewIssue]:
        """Skill 触发条件审查"""
        issues = []
        overview = getattr(design, 'overview', '') or ''
        content = overview.lower()
        
        trigger_keywords = ["trigger", "触发", "when", "条件"]
        if not any(kw in content for kw in trigger_keywords):
            issues.append(ReviewIssue(
                dimension="trigger",
                severity=IssueSeverity.BLOCKER,
                title="缺少触发条件",
                description="Skill 必须定义触发条件",
                suggestion="在 overview 中描述何时触发此 Skill"
            ))
        
        return issues
    
    def _review_skill_workflow(self, design: Any) -> List[ReviewIssue]:
        """Skill 工作流审查"""
        issues = []
        architecture = getattr(design, 'architecture', '') or ''
        overview = getattr(design, 'overview', '') or ''
        content = (architecture + overview).lower()
        
        workflow_keywords = ["workflow", "工作流", "step", "步骤", "流程"]
        if not any(kw in content for kw in workflow_keywords):
            issues.append(ReviewIssue(
                dimension="workflow",
                severity=IssueSeverity.CRITICAL,
                title="缺少工作流定义",
                description="Skill 必须定义执行流程",
                suggestion="描述 Skill 的执行步骤"
            ))
        
        return issues
    
    def _review_skill_composition(self, design: Any) -> List[ReviewIssue]:
        """Skill 工具组合审查"""
        issues = []
        components = getattr(design, 'components', []) or []
        file_structure = getattr(design, 'file_structure', []) or []
        
        tool_indicators = ['tool', 'service', 'api']
        has_tools = any(
            any(ind in (c.description or '').lower() for ind in tool_indicators)
            for c in components
        ) or any(ind in ' '.join(file_structure).lower() for ind in tool_indicators)
        
        if not has_tools:
            issues.append(ReviewIssue(
                dimension="tool_composition",
                severity=IssueSeverity.BLOCKER,
                title="缺少工具组合",
                description="Skill 必须组合可用的工具",
                suggestion="定义 Skill 使用的工具"
            ))
        
        return issues
    
    def _review_skill_implementation(self, design: Any) -> List[ReviewIssue]:
        """Skill 实现审查"""
        issues = []
        file_structure = getattr(design, 'file_structure', []) or []
        
        if len(file_structure) == 0:
            issues.append(ReviewIssue(
                dimension="implementation",
                severity=IssueSeverity.BLOCKER,
                title="缺少文件结构",
                description="必须提供文件结构",
                suggestion="定义 Skill 文件结构"
            ))
        
        has_skill_file = any('skill' in f.lower() for f in file_structure)
        if not has_skill_file:
            issues.append(ReviewIssue(
                dimension="implementation",
                severity=IssueSeverity.WARNING,
                title="缺少 Skill 定义文件",
                description="建议有专门的 Skill 定义",
                suggestion="添加 src/agents/skills/xxx.py"
            ))
        
        return issues
    
    def _review_tool(self, design: Any, result: ReviewResult):
        """审查 Tool 设计"""
        issues = []
        
        # 1. 参数定义审查
        issues.extend(self._review_tool_parameters(design))
        
        # 2. 错误处理审查
        issues.extend(self._review_tool_error_handling(design))
        
        # 3. 返回值审查
        issues.extend(self._review_tool_return_value(design))
        
        # 4. 安全性审查
        issues.extend(self._review_tool_safety(design))
        
        result.issues = issues
    
    def _review_tool_parameters(self, design: Any) -> List[ReviewIssue]:
        """Tool 参数审查"""
        issues = []
        api_endpoints = getattr(design, 'api_endpoints', []) or []
        overview = getattr(design, 'overview', '') or ''
        content = overview.lower()
        
        param_keywords = ["param", "parameter", "参数", "input", "输入"]
        if len(api_endpoints) == 0 and not any(kw in content for kw in param_keywords):
            issues.append(ReviewIssue(
                dimension="parameters",
                severity=IssueSeverity.BLOCKER,
                title="缺少参数定义",
                description="Tool 必须定义输入参数",
                suggestion="定义参数名称、类型、是否必需"
            ))
        
        return issues
    
    def _review_tool_error_handling(self, design: Any) -> List[ReviewIssue]:
        """Tool 错误处理审查"""
        issues = []
        overview = getattr(design, 'overview', '') or ''
        architecture = getattr(design, 'architecture', '') or ''
        content = (overview + architecture).lower()
        
        error_keywords = ["error", "异常", "exception", "失败", "handle"]
        if not any(kw in content for kw in error_keywords):
            issues.append(ReviewIssue(
                dimension="error_handling",
                severity=IssueSeverity.CRITICAL,
                title="缺少错误处理",
                description="Tool 必须定义错误处理",
                suggestion="描述可能的错误及处理方式"
            ))
        
        return issues
    
    def _review_tool_return_value(self, design: Any) -> List[ReviewIssue]:
        """Tool 返回值审查"""
        issues = []
        overview = getattr(design, 'overview', '') or ''
        content = overview.lower()
        
        return_keywords = ["return", "返回", "output", "输出", "result"]
        if not any(kw in content for kw in return_keywords):
            issues.append(ReviewIssue(
                dimension="return_value",
                severity=IssueSeverity.CRITICAL,
                title="缺少返回值定义",
                description="Tool 必须定义返回值",
                suggestion="定义返回值类型和格式"
            ))
        
        return issues
    
    def _review_tool_safety(self, design: Any) -> List[ReviewIssue]:
        """Tool 安全性审查"""
        issues = []
        overview = getattr(design, 'overview', '') or ''
        content = overview.lower()
        
        dangerous_keywords = ["delete", "remove", "drop", "exec", "eval", "rm ", "destroy"]
        if any(kw in content for kw in dangerous_keywords):
            issues.append(ReviewIssue(
                dimension="safety",
                severity=IssueSeverity.CRITICAL,
                title="潜在危险操作",
                description="Tool 包含可能危险的操作",
                suggestion="添加安全约束和使用限制"
            ))
        
        risks = getattr(design, 'risks', []) or []
        if len(risks) == 0 and any(kw in content for kw in dangerous_keywords):
            issues.append(ReviewIssue(
                dimension="safety",
                severity=IssueSeverity.WARNING,
                title="缺少风险评估",
                description="危险操作需要风险评估",
                suggestion="添加 risks 列表"
            ))
        
        return issues
    
    def _review_generic(self, design: Any, result: ReviewResult):
        """通用审查"""
        issues = []
        file_structure = getattr(design, 'file_structure', []) or []
        
        if len(file_structure) == 0:
            issues.append(ReviewIssue(
                dimension="implementation",
                severity=IssueSeverity.BLOCKER,
                title="缺少文件结构",
                description="必须提供文件结构",
                suggestion="定义文件结构"
            ))
        
        result.issues = issues
    
    def _calculate_scores(self, issues: List[ReviewIssue]) -> Dict[str, float]:
        """计算维度分数"""
        dimensions = set(i.dimension for i in issues)
        scores = {}
        
        for dim in dimensions:
            dim_issues = [i for i in issues if i.dimension == dim]
            blockers = len([i for i in dim_issues if i.severity == IssueSeverity.BLOCKER])
            criticals = len([i for i in dim_issues if i.severity == IssueSeverity.CRITICAL])
            warnings = len([i for i in dim_issues if i.severity == IssueSeverity.WARNING])
            
            score = 1.0 - (blockers * 0.5 + criticals * 0.25 + warnings * 0.1)
            scores[dim] = max(0.0, score)
        
        return scores
    
    def get_review_report(self) -> str:
        """生成审查报告"""
        if not self._current_result:
            return "No review completed"
        
        r = self._current_result
        lines = []
        
        lines.append("=" * 60)
        lines.append(f"组件设计审查报告: {r.component_name} ({r.component_type})")
        lines.append("=" * 60)
        
        lines.append(f"\n📊 审查结果: {'✅ 通过' if r.is_approved else '❌ 未通过'}")
        
        if r.dimension_scores:
            lines.append(f"\n📈 维度分数:")
            for dim, score in r.dimension_scores.items():
                bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                color = "🟢" if score >= 0.7 else ("🟡" if score >= 0.5 else "🔴")
                lines.append(f"  {color} {dim:20}: [{bar}] {score:.1f}")
        
        if r.blockers:
            lines.append(f"\n🚫 阻塞性问题 ({len(r.blockers)}):")
            for issue in r.blockers:
                lines.append(f"  - {issue.title}")
        
        if r.criticals:
            lines.append(f"\n⚠️ 关键问题 ({len(r.criticals)}):")
            for issue in r.criticals:
                lines.append(f"  - {issue.title}")
        
        if r.warnings:
            lines.append(f"\n💡 警告 ({len(r.warnings)}):")
            for issue in r.warnings:
                lines.append(f"  - {issue.title}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)


# ============================================================================
# Demo / Tests
# ============================================================================

if __name__ == "__main__":
    print("=== ComponentDesignReview Demo ===\n")
    
    review = ComponentDesignReview()
    
    # 创建简单的设计对象
    class MockDesign:
        def __init__(self, title, overview, components=None, file_structure=None, risks=None):
            self.title = title
            self.overview = overview
            self.components = components or []
            self.file_structure = file_structure or []
            self.risks = risks or []
    
    # 测试 Agent
    print("1. Agent 审查:")
    agent_design = MockDesign(
        title="UserAuthAgent",
        overview="用户认证 Agent，负责登录注册",
        file_structure=["src/agents/auth.py", "tests/test_auth.py"],
        risks=[{"description": "Token 泄露风险"}]
    )
    result = review.review_design(agent_design, "agent")
    print(f"   类型: {result.component_type}")
    print(f"   通过: {result.is_approved}")
    print(f"   分数: {result.dimension_scores}")
    print()
    
    # 测试 Skill
    print("2. Skill 审查:")
    skill_design = MockDesign(
        title="DataProcessSkill",
        overview="数据处理 Skill，当数据需要转换时触发，使用工作流处理",
        file_structure=["src/agents/skills/data_process.py"]
    )
    result = review.review_design(skill_design, "skill")
    print(f"   类型: {result.component_type}")
    print(f"   通过: {result.is_approved}")
    print(f"   阻塞: {len(result.blockers)}, 关键: {len(result.criticals)}")
    print()
    
    # 测试 Tool
    print("3. Tool 审查:")
    tool_design = MockDesign(
        title="FileDeleteTool",
        overview="删除文件 Tool，输入文件路径，处理错误和返回值",
        file_structure=["src/tools/file_delete.py"]
    )
    result = review.review_design(tool_design, "tool")
    print(f"   类型: {result.component_type}")
    print(f"   通过: {result.is_approved}")
    print(f"   阻塞: {len(result.blockers)}, 关键: {len(result.criticals)}")
    print()
    
    # 自动检测
    print("4. 自动检测:")
    test_design = MockDesign(
        title="TestSkill",
        overview="测试 Skill 用于自动化测试，触发条件为需要测试时",
        file_structure=["src/skills/test.py"]
    )
    detected = review.detect_component_type(test_design)
    print(f"   检测类型: {detected.value}")
