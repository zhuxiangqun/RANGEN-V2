#!/usr/bin/env python3
"""
Agent Design Review - Agent 设计专项审查

对于需要生成新 Agent 的需求，进行专项审核:

审核维度:
1. Agent 定义 - 名称、职责、边界
2. 能力定义 - Tools、Skills、Interfaces
3. 集成点 - 与其他 Agent 的交互
4. 安全约束 - 权限、限制、Guardrails
5. 实现计划 - TDD 步骤、文件结构

Usage:
    from src.agents.agent_design_review import AgentDesignReview
    
    review = AgentDesignReview()
    result = review.review_design(generated_design)
    
    print(result.is_approved)
    print(result.issues)
    print(result.suggestions)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ReviewDimension(Enum):
    """审查维度"""
    DEFINITION = "definition"        # Agent 定义
    CAPABILITY = "capability"       # 能力定义
    INTEGRATION = "integration"     # 集成点
    SECURITY = "security"           # 安全约束
    IMPLEMENTATION = "implementation"  # 实现计划


class IssueSeverity(Enum):
    """问题严重程度"""
    BLOCKER = "blocker"    # 阻塞性问题 - 必须修复
    CRITICAL = "critical"  # 关键问题 - 强烈建议修复
    WARNING = "warning"     # 警告 - 建议修复
    INFO = "info"          # 信息 - 可选


@dataclass
class ReviewIssue:
    """审查问题"""
    dimension: ReviewDimension
    severity: IssueSeverity
    title: str
    description: str
    suggestion: str = ""
    evidence: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "suggestion": self.suggestion,
            "evidence": self.evidence
        }


@dataclass
class ReviewResult:
    """审查结果"""
    design_title: str
    is_approved: bool
    issues: List[ReviewIssue] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    dimension_scores: Dict[str, float] = field(default_factory=dict)
    blockers: List[ReviewIssue] = field(default_factory=list)
    criticals: List[ReviewIssue] = field(default_factory=list)
    warnings: List[ReviewIssue] = field(default_factory=list)
    
    def __post_init__(self):
        self.blockers = [i for i in self.issues if i.severity == IssueSeverity.BLOCKER]
        self.criticals = [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]
        self.warnings = [i for i in self.issues if i.severity == IssueSeverity.WARNING]
        self.is_approved = len(self.blockers) == 0 and len(self.criticals) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "design_title": self.design_title,
            "is_approved": self.is_approved,
            "blockers_count": len(self.blockers),
            "criticals_count": len(self.criticals),
            "warnings_count": len(self.warnings),
            "issues": [i.to_dict() for i in self.issues],
            "suggestions": self.suggestions,
            "dimension_scores": self.dimension_scores
        }


class AgentDesignReview:
    """
    Agent 设计专项审查器
    
    审核维度:
    1. DEFINITION - Agent 定义
    2. CAPABILITY - 能力定义
    3. INTEGRATION - 集成点
    4. SECURITY - 安全约束
    5. IMPLEMENTATION - 实现计划
    """
    
    # 必需元素检查清单
    REQUIRED_DEFINITION = [
        "agent_name",
        "purpose",
        "responsibilities",
        "boundaries"
    ]
    
    REQUIRED_CAPABILITY = [
        "tools",
        "skills",
        "input_contract",
        "output_contract"
    ]
    
    REQUIRED_SECURITY = [
        "permissions",
        "constraints",
        "guardrails"
    ]
    
    def __init__(self):
        self._current_review: Optional[ReviewResult] = None
        logger.info("AgentDesignReview 初始化")
    
    def review_design(self, design: Any) -> ReviewResult:
        """
        审查 Agent 设计
        
        Args:
            design: GeneratedDesign 或设计字典
            
        Returns:
            ReviewResult: 审查结果
        """
        title = getattr(design, 'title', 'Unknown') if hasattr(design, 'title') else design.get('title', 'Unknown')
        
        result = ReviewResult(
            design_title=title,
            is_approved=False
        )
        
        # 1. 审查 Agent 定义
        definition_issues = self._review_definition(design)
        result.issues.extend(definition_issues)
        
        # 2. 审查能力定义
        capability_issues = self._review_capability(design)
        result.issues.extend(capability_issues)
        
        # 3. 审查集成点
        integration_issues = self._review_integration(design)
        result.issues.extend(integration_issues)
        
        # 4. 审查安全约束
        security_issues = self._review_security(design)
        result.issues.extend(security_issues)
        
        # 5. 审查实现计划
        implementation_issues = self._review_implementation(design)
        result.issues.extend(implementation_issues)
        
        # 计算维度分数
        result.dimension_scores = self._calculate_scores(result.issues)
        
        # 生成建议
        result.suggestions = self._generate_suggestions(result)
        
        self._current_review = result
        
        return result
    
    def _review_definition(self, design: Any) -> List[ReviewIssue]:
        """审查 Agent 定义"""
        issues = []
        
        # 检查是否有 Agent 相关内容
        title = getattr(design, 'title', '') or ''
        overview = getattr(design, 'overview', '') or ''
        architecture = getattr(design, 'architecture', '') or ''
        
        content = (title + overview + architecture).lower()
        
        # 检查 Agent 名称
        if not title or len(title) < 3:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.DEFINITION,
                severity=IssueSeverity.BLOCKER,
                title="Agent 名称缺失或过短",
                description="Agent 必须有明确且有意义的名称",
                suggestion="提供清晰、有描述性的 Agent 名称"
            ))
        
        # 检查职责描述
        responsibility_keywords = ["职责", "功能", "负责", "responsibility", "function", "capability"]
        if not any(kw in content for kw in responsibility_keywords):
            issues.append(ReviewIssue(
                dimension=ReviewDimension.DEFINITION,
                severity=IssueSeverity.CRITICAL,
                title="缺少职责描述",
                description="设计应明确说明 Agent 的核心职责",
                suggestion="在设计中添加 Agent 职责描述"
            ))
        
        # 检查边界定义
        boundary_keywords = ["边界", "限制", "不能", "boundary", "limit", "cannot"]
        if not any(kw in content for kw in boundary_keywords):
            issues.append(ReviewIssue(
                dimension=ReviewDimension.DEFINITION,
                severity=IssueSeverity.WARNING,
                title="缺少边界定义",
                description="建议定义 Agent 的边界，明确它不应该做什么",
                suggestion="添加边界定义，说明 Agent 的限制"
            ))
        
        return issues
    
    def _review_capability(self, design: Any) -> List[ReviewIssue]:
        """审查能力定义"""
        issues = []
        
        components = getattr(design, 'components', []) or []
        file_structure = getattr(design, 'file_structure', []) or []
        
        # 检查是否有工具定义
        tool_indicators = ["tool", "技能", "capability", "ability"]
        has_tools = any(
            any(ind in (c.description or '').lower() for ind in tool_indicators)
            for c in components
        ) or any(
            'tool' in f.lower() for f in file_structure
        )
        
        if not has_tools and len(components) == 0:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.CAPABILITY,
                severity=IssueSeverity.BLOCKER,
                title="缺少能力定义",
                description="Agent 必须定义其能力（Tools、Skills）",
                suggestion="在设计中明确定义 Agent 的工具和能力"
            ))
        
        # 检查输入/输出契约
        api_endpoints = getattr(design, 'api_endpoints', []) or []
        if len(api_endpoints) == 0:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.CAPABILITY,
                severity=IssueSeverity.WARNING,
                title="缺少 API 端点定义",
                description="建议定义 Agent 的输入输出接口",
                suggestion="添加 API 端点或方法签名定义"
            ))
        
        return issues
    
    def _review_integration(self, design: Any) -> List[ReviewIssue]:
        """审查集成点"""
        issues = []
        
        overview = getattr(design, 'overview', '') or ''
        architecture = getattr(design, 'architecture', '') or ''
        
        content = (overview + architecture).lower()
        
        # 检查是否有集成点描述
        integration_keywords = ["集成", "交互", "接口", "integration", "interface", "interact", "communicate"]
        has_integration = any(kw in content for kw in integration_keywords)
        
        # 检查是否有依赖 Agent 提及
        dependency_keywords = ["agent", "coordinator", "orchestrator", "其他", "other"]
        has_dependencies = any(kw in content for kw in dependency_keywords)
        
        if not has_integration and has_dependencies:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.INTEGRATION,
                severity=IssueSeverity.WARNING,
                title="缺少集成点描述",
                description="设计应说明 Agent 如何与其他组件交互",
                suggestion="添加集成点说明"
            ))
        
        return issues
    
    def _review_security(self, design: Any) -> List[ReviewIssue]:
        """审查安全约束"""
        issues = []
        
        overview = getattr(design, 'overview', '') or ''
        architecture = getattr(design, 'architecture', '') or ''
        risks = getattr(design, 'risks', []) or []
        
        content = (overview + architecture).lower()
        
        # 检查是否有安全相关内容
        security_keywords = ["安全", "权限", "认证", "security", "permission", "auth", "constraint"]
        has_security = any(kw in content for kw in security_keywords)
        
        # 检查风险列表
        has_risk_assessment = len(risks) > 0
        
        if not has_security:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.SECURITY,
                severity=IssueSeverity.CRITICAL,
                title="缺少安全约束",
                description="Agent 设计必须包含安全约束",
                suggestion="添加权限、约束、Guardrails 定义"
            ))
        
        if not has_risk_assessment:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.SECURITY,
                severity=IssueSeverity.WARNING,
                title="缺少风险评估",
                description="建议评估 Agent 的潜在风险",
                suggestion="添加风险评估章节"
            ))
        
        return issues
    
    def _review_implementation(self, design: Any) -> List[ReviewIssue]:
        """审查实现计划"""
        issues = []
        
        file_structure = getattr(design, 'file_structure', []) or []
        
        # 检查文件结构
        if len(file_structure) == 0:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.IMPLEMENTATION,
                severity=IssueSeverity.BLOCKER,
                title="缺少文件结构",
                description="设计必须包含文件结构",
                suggestion="提供完整的文件结构定义"
            ))
        
        # 检查是否有测试文件
        has_test = any('test' in f.lower() for f in file_structure)
        if not has_test:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.IMPLEMENTATION,
                severity=IssueSeverity.CRITICAL,
                title="缺少测试计划",
                description="Agent 设计必须包含测试计划 (TDD)",
                suggestion="添加 tests/ 目录和测试文件定义"
            ))
        
        # 检查文件路径是否规范
        src_files = [f for f in file_structure if 'src/' in f]
        if len(src_files) == 0:
            issues.append(ReviewIssue(
                dimension=ReviewDimension.IMPLEMENTATION,
                severity=IssueSeverity.WARNING,
                title="文件路径不规范",
                description="建议使用 src/agents/ 作为根目录",
                suggestion="规范化文件路径"
            ))
        
        return issues
    
    def _calculate_scores(self, issues: List[ReviewIssue]) -> Dict[str, float]:
        """计算各维度分数"""
        scores = {}
        
        for dimension in ReviewDimension:
            dimension_issues = [i for i in issues if i.dimension == dimension]
            
            if not dimension_issues:
                scores[dimension.value] = 1.0
            else:
                blockers = len([i for i in dimension_issues if i.severity == IssueSeverity.BLOCKER])
                criticals = len([i for i in dimension_issues if i.severity == IssueSeverity.CRITICAL])
                warnings = len([i for i in dimension_issues if i.severity == IssueSeverity.WARNING])
                
                # 扣分计算
                score = 1.0 - (blockers * 0.5 + criticals * 0.25 + warnings * 0.1)
                scores[dimension.value] = max(0.0, score)
        
        return scores
    
    def _generate_suggestions(self, result: ReviewResult) -> List[str]:
        """生成建议"""
        suggestions = []
        
        if result.blockers:
            suggestions.append(f"🚫 必须修复 {len(result.blockers)} 个阻塞性问题")
        
        if result.criticals:
            suggestions.append(f"⚠️  强烈建议修复 {len(result.criticals)} 个关键问题")
        
        if result.warnings:
            suggestions.append(f"💡 建议修复 {len(result.warnings)} 个警告")
        
        # 分数低于 0.5 的维度
        low_scores = [
            f"  - {dim}: {score:.1f}"
            for dim, score in result.dimension_scores.items()
            if score < 0.5
        ]
        if low_scores:
            suggestions.append(f"📉 需要改进的维度:\n" + "\n".join(low_scores))
        
        if not suggestions:
            suggestions.append("✅ 设计审核通过!")
        
        return suggestions
    
    def get_review_report(self) -> str:
        """生成审查报告"""
        if not self._current_review:
            return "No review completed"
        
        result = self._current_review
        lines = []
        
        lines.append("=" * 60)
        lines.append(f"Agent 设计审查报告: {result.design_title}")
        lines.append("=" * 60)
        
        lines.append(f"\n📊 审查结果: {'✅ 通过' if result.is_approved else '❌ 未通过'}")
        
        lines.append(f"\n📈 维度分数:")
        for dim, score in result.dimension_scores.items():
            bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            lines.append(f"  {dim:15}: [{bar}] {score:.1f}")
        
        if result.blockers:
            lines.append(f"\n🚫 阻塞性问题 ({len(result.blockers)}):")
            for issue in result.blockers:
                lines.append(f"  - {issue.title}")
        
        if result.criticals:
            lines.append(f"\n⚠️ 关键问题 ({len(result.criticals)}):")
            for issue in result.criticals:
                lines.append(f"  - {issue.title}")
        
        if result.warnings:
            lines.append(f"\n💡 警告 ({len(result.warnings)}):")
            for issue in result.warnings:
                lines.append(f"  - {issue.title}")
        
        lines.append("\n" + "=" * 60)
        
        return "\n".join(lines)


# ============================================================================
# Demo / Tests
# ============================================================================

if __name__ == "__main__":
    print("=== AgentDesignReview Demo ===\n")
    
    from src.agents.ai_design_generator import GeneratedDesign, DesignComponent
    
    review = AgentDesignReview()
    
    # 测试不完整的设计
    incomplete_design = GeneratedDesign(
        title="Test",
        overview="A simple agent",
        components=[],
        file_structure=[]
    )
    
    print("1. 审查不完整的设计:")
    result = review.review_design(incomplete_design)
    print(f"   通过: {result.is_approved}")
    print(f"   阻塞: {len(result.blockers)}, 关键: {len(result.criticals)}, 警告: {len(result.warnings)}")
    print()
    
    # 测试完整的设计
    complete_design = GeneratedDesign(
        title="UserAuthAgent",
        overview="用户认证 Agent，负责登录注册功能。职责：验证用户身份，颁发 Token。边界：不能修改用户数据。",
        architecture="使用 JWT 进行认证，集成 UserService",
        components=[
            DesignComponent(name="auth_tools", description="认证工具集"),
            DesignComponent(name="security", description="安全约束")
        ],
        file_structure=[
            "src/agents/user_auth_agent.py",
            "tests/test_user_auth_agent.py"
        ],
        api_endpoints=[{"endpoint": "POST /auth/login"}],
        risks=[{"description": "Token 泄露风险"}]
    )
    
    print("2. 审查完整的设计:")
    result = review.review_design(complete_design)
    print(f"   通过: {result.is_approved}")
    print(f"   分数: {result.dimension_scores}")
    print()
    
    # 打印报告
    print("3. 审查报告:")
    print(review.get_review_report())
