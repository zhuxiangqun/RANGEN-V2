#!/usr/bin/env python3
"""
Requirement Discovery Agent - 需求发现 Brainstorming Skill

借鉴 Superpowers 的 Brainstorming Skill 方法论:

流程:
1. Problem → 问题陈述
2. Clarification → 5W1H 追问澄清
3. Requirements → 结构化需求
4. Spec → 规范文档

核心原理:
- 从模糊的问题陈述中提取清晰的需求
- 通过追问消除歧义
- 生成可验证的规范
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RequirementPriority(Enum):
    """需求优先级"""
    CRITICAL = "critical"  # 必须实现
    HIGH = "high"          # 强烈建议
    MEDIUM = "medium"      # 建议实现
    LOW = "low"           # 可选


class RequirementType(Enum):
    """需求类型"""
    FUNCTIONAL = "functional"      # 功能性需求
    NON_FUNCTIONAL = "non_functional"  # 非功能性需求
    TECHNICAL = "technical"        # 技术需求
    UX = "ux"                     # 用户体验需求
    SECURITY = "security"          # 安全需求


@dataclass
class Requirement:
    """需求项"""
    id: str
    title: str
    description: str
    priority: RequirementPriority
    type: RequirementType
    acceptance_criteria: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    estimated_effort: str = ""  # 小/中/大
    status: str = "pending"


@dataclass
class ClarificationQuestion:
    """澄清问题"""
    question: str
    category: str  # What, Why, Who, When, Where, How
    answered: bool = False
    answer: str = ""


@dataclass
class DiscoveredRequirements:
    """发现的需求集合"""
    original_problem: str
    clarifications: List[ClarificationQuestion] = field(default_factory=list)
    requirements: List[Requirement] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    spec_document: str = ""
    created_at: datetime = field(default_factory=datetime.now)


class RequirementDiscoveryAgent:
    """
    需求发现 Agent
    
    从问题陈述中发现、澄清并结构化需求
    
    使用方法:
    agent = RequirementDiscoveryAgent()
    result = agent.discover_requirements("我需要一个用户管理系统")
    spec = agent.generate_spec(result)
    """
    
    # 5W1H 追问模板
    CLARIFICATION_TEMPLATES = {
        "What": [
            "具体要实现什么功能？",
            "这个系统的核心职责是什么？",
            "有哪些主要的业务流程？",
        ],
        "Why": [
            "为什么要做这个系统？",
            "解决什么问题或痛点？",
            "成功标准是什么？",
        ],
        "Who": [
            "谁是主要用户？",
            "用户有哪些角色/权限？",
            "有多少用户会使用这个系统？",
        ],
        "When": [
            "什么时候需要上线？",
            "有哪些关键时间节点？",
            "系统需要 7x24 运行吗？",
        ],
        "Where": [
            "系统部署在哪里？",
            "有哪些集成点？",
            "数据存储在哪里？",
        ],
        "How": [
            "如何衡量系统成功？",
            "如何进行用户认证？",
            "预期的使用量是多少？",
        ],
    }
    
    def __init__(self):
        self._current_discovery: Optional[DiscoveredRequirements] = None
        logger.info("RequirementDiscoveryAgent 初始化")
    
    def discover_requirements(self, problem_statement: str) -> DiscoveredRequirements:
        """
        从问题陈述中发现需求
        
        Args:
            problem_statement: 原始问题陈述
            
        Returns:
            DiscoveredRequirements: 包含所有发现的需求
        """
        logger.info(f"开始需求发现: {problem_statement[:50]}...")
        
        # 初始化
        self._current_discovery = DiscoveredRequirements(
            original_problem=problem_statement
        )
        
        # 1. 生成澄清问题
        self._generate_clarification_questions()
        
        # 2. 分析问题并提取需求
        self._extract_requirements()
        
        # 3. 识别假设
        self._identify_assumptions()
        
        # 4. 评估风险
        self._assess_risks()
        
        logger.info(f"需求发现完成: {len(self._current_discovery.requirements)} 个需求")
        return self._current_discovery
    
    def _generate_clarification_questions(self):
        """生成澄清问题 (5W1H)"""
        questions = []
        
        for category, templates in self.CLARIFICATION_TEMPLATES.items():
            for template in templates:
                questions.append(ClarificationQuestion(
                    question=template,
                    category=category
                ))
        
        self._current_discovery.clarifications = questions
        logger.debug(f"生成 {len(questions)} 个澄清问题")
    
    def clarify_ambiguities(self, answers: Dict[str, str]) -> List[ClarificationQuestion]:
        """
        回答澄清问题
        
        Args:
            answers: {question_id: answer} 格式的回答
            
        Returns:
            更新后的问题列表
        """
        if not self._current_discovery:
            raise ValueError("需要先调用 discover_requirements")
        
        for i, question in enumerate(self._current_discovery.clarifications):
            q_id = f"q_{i}"
            if q_id in answers or question.question in answers:
                answer = answers.get(q_id) or answers.get(question.question, "")
                question.answered = True
                question.answer = answer
        
        # 重新提取需求（基于新的信息）
        self._extract_requirements()
        
        return self._current_discovery.clarifications
    
    def _extract_requirements(self):
        """从问题陈述中提取需求"""
        problem = self._current_discovery.original_problem.lower()
        requirements = []
        
        # 基础需求识别（简单规则，实际应该用 LLM）
        requirement_id = 1
        
        # 功能性需求识别
        if "用户" in problem or "user" in problem:
            requirements.append(Requirement(
                id=f"REQ-{requirement_id:03d}",
                title="用户管理功能",
                description="系统应支持用户注册、登录、信息管理",
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                acceptance_criteria=[
                    "用户可以注册新账户",
                    "用户可以登录系统",
                    "用户可以查看和编辑个人信息",
                ]
            ))
            requirement_id += 1
        
        if "管理" in problem or "manage" in problem or "admin" in problem:
            requirements.append(Requirement(
                id=f"REQ-{requirement_id:03d}",
                title="管理功能",
                description="系统应提供管理界面",
                priority=RequirementPriority.MEDIUM,
                type=RequirementType.FUNCTIONAL,
                acceptance_criteria=[
                    "管理员可以查看用户列表",
                    "管理员可以启用/禁用用户",
                ]
            ))
            requirement_id += 1
        
        if "api" in problem or "接口" in problem:
            requirements.append(Requirement(
                id=f"REQ-{requirement_id:03d}",
                title="API 接口",
                description="提供 RESTful API 接口",
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                acceptance_criteria=[
                    "提供用户 CRUD API",
                    "API 支持认证",
                ]
            ))
            requirement_id += 1
        
        # 非功能性需求识别
        if "快" in problem or "fast" in problem or "性能" in problem:
            requirements.append(Requirement(
                id=f"REQ-{requirement_id:03d}",
                title="性能要求",
                description="系统应满足性能指标",
                priority=RequirementPriority.HIGH,
                type=RequirementType.NON_FUNCTIONAL,
                acceptance_criteria=[
                    "API 响应时间 < 200ms",
                    "支持 100 并发用户",
                ]
            ))
            requirement_id += 1
        
        if "安全" in problem or "secure" in problem or "auth" in problem:
            requirements.append(Requirement(
                id=f"REQ-{requirement_id:03d}",
                title="安全要求",
                description="系统应满足安全标准",
                priority=RequirementPriority.CRITICAL,
                type=RequirementType.SECURITY,
                acceptance_criteria=[
                    "密码加密存储",
                    "防止 SQL 注入",
                    "防止 XSS 攻击",
                ]
            ))
            requirement_id += 1
        
        # 默认需求
        if not requirements:
            requirements.append(Requirement(
                id=f"REQ-{requirement_id:03d}",
                title="核心功能",
                description="实现问题陈述中描述的核心功能",
                priority=RequirementPriority.HIGH,
                type=RequirementType.FUNCTIONAL,
                acceptance_criteria=[
                    "功能按规范实现",
                    "通过功能测试",
                ]
            ))
        
        self._current_discovery.requirements = requirements
    
    def _identify_assumptions(self):
        """识别假设"""
        assumptions = []
        
        # 基于问题陈述识别常见假设
        problem = self._current_discovery.original_problem
        
        if "用户" in problem:
            assumptions.append("假设用户有独立的账户")
        
        if "管理" in problem:
            assumptions.append("假设存在管理员角色")
        
        if "web" in problem.lower() or "网站" in problem:
            assumptions.append("假设使用浏览器作为客户端")
        
        # 添加默认假设
        assumptions.extend([
            "假设使用关系型数据库",
            "假设使用 REST API",
            "假设系统需要日志记录",
        ])
        
        self._current_discovery.assumptions = assumptions
    
    def _assess_risks(self):
        """评估风险"""
        risks = []
        requirements = self._current_discovery.requirements
        
        # 风险评估
        critical_count = sum(1 for r in requirements if r.priority == RequirementPriority.CRITICAL)
        if critical_count > 3:
            risks.append("高风险: 关键需求过多，可能影响交付时间")
        
        security_reqs = [r for r in requirements if r.type == RequirementType.SECURITY]
        if not security_reqs and "用户" in self._current_discovery.original_problem:
            risks.append("中风险: 用户系统但未明确安全需求")
        
        if not risks:
            risks.append("低风险: 需求清晰，可以开始实现")
        
        self._current_discovery.risks = risks
    
    def validate_assumptions(self) -> Dict[str, bool]:
        """
        验证假设
        
        返回:
            {assumption: is_valid} 格式的字典
        """
        if not self._current_discovery:
            raise ValueError("需要先调用 discover_requirements")
        
        validation = {}
        for assumption in self._current_discovery.assumptions:
            # 简化验证，实际应该询问用户
            validation[assumption] = True
        
        return validation
    
    def generate_spec(self, discovery: DiscoveredRequirements = None) -> str:
        """
        生成 Markdown 规范文档
        
        Args:
            discovery: 可选，使用指定的需求发现结果
            
        Returns:
            Markdown 格式的规范文档
        """
        if discovery:
            self._current_discovery = discovery
        
        if not self._current_discovery:
            raise ValueError("需要先调用 discover_requirements")
        
        d = self._current_discovery
        lines = [
            "# 需求规范文档",
            "",
            f"**创建时间**: {d.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 1. 原始问题",
            "",
            d.original_problem,
            "",
            "---",
            "",
            "## 2. 澄清问题",
            "",
        ]
        
        # 添加澄清问题
        for i, q in enumerate(d.clarifications, 1):
            status = "✅" if q.answered else "❓"
            lines.append(f"{status} **{q.category}**: {q.question}")
            if q.answered:
                lines.append(f"   - 回答: {q.answer}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 3. 需求列表",
            "",
        ])
        
        # 按优先级分组
        for priority in RequirementPriority:
            priority_reqs = [r for r in d.requirements if r.priority == priority]
            if priority_reqs:
                lines.append(f"### {priority.value.upper()}")
                lines.append("")
                for req in priority_reqs:
                    lines.append(f"#### {req.id}: {req.title}")
                    lines.append(f"**类型**: {req.type.value}")
                    if req.description:
                        lines.append(f"**描述**: {req.description}")
                    if req.estimated_effort:
                        lines.append(f"**工作量**: {req.estimated_effort}")
                    lines.append("")
                    lines.append("**验收标准**:")
                    for criterion in req.acceptance_criteria:
                        lines.append(f"- [ ] {criterion}")
                    lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 4. 假设条件",
            "",
        ])
        
        for assumption in d.assumptions:
            lines.append(f"- {assumption}")
        
        lines.extend([
            "",
            "---",
            "",
            "## 5. 风险评估",
            "",
        ])
        
        for risk in d.risks:
            emoji = "🔴" if "高风险" in risk else ("🟡" if "中风险" in risk else "🟢")
            lines.append(f"{emoji} {risk}")
        
        lines.extend([
            "",
            "---",
            "",
            "## 6. 下一步行动",
            "",
            "- [ ] 确认需求清单",
            "- [ ] 评估工作量",
            "- [ ] 制定开发计划",
            "- [ ] 开始实现",
        ])
        
        spec = "\n".join(lines)
        self._current_discovery.spec_document = spec
        return spec
    
    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典格式"""
        if not self._current_discovery:
            raise ValueError("需要先调用 discover_requirements")
        
        d = self._current_discovery
        return {
            "original_problem": d.original_problem,
            "clarifications": [
                {
                    "question": q.question,
                    "category": q.category,
                    "answered": q.answered,
                    "answer": q.answer,
                }
                for q in d.clarifications
            ],
            "requirements": [
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "priority": r.priority.value,
                    "type": r.type.value,
                    "acceptance_criteria": r.acceptance_criteria,
                    "dependencies": r.dependencies,
                    "estimated_effort": r.estimated_effort,
                    "status": r.status,
                }
                for r in d.requirements
            ],
            "assumptions": d.assumptions,
            "risks": d.risks,
            "created_at": d.created_at.isoformat(),
        }


# 全局单例
_agent: Optional[RequirementDiscoveryAgent] = None


def get_requirement_discovery_agent() -> RequirementDiscoveryAgent:
    """获取全局需求发现 Agent"""
    global _agent
    if _agent is None:
        _agent = RequirementDiscoveryAgent()
    return _agent
