#!/usr/bin/env python3
"""
Review Pipeline - 分级评审流程实现

基于 Harrison Chase 文章洞见：
- 评审从"附属动作"升级为"主流程"
- 分级评审机制：L0 → L1 → L2 → L3

文章核心观点：
"问题不在 'AI 做得太快'，而在 '错误方向太容易显得像一个差不多能上线的版本'"
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json


class ReviewLevel(Enum):
    """评审级别"""
    L0_AUTO = "l0_auto"       # 自动检查（格式、语法、安全）
    L1_SELF = "l1_self"       # Builder 自检
    L2_PEER = "l2_peer"       # Reviewer 评审
    L3_EXPERT = "l3_expert"   # 专家评审


class ReviewResult(Enum):
    """评审结果"""
    PASS = "pass"             # 通过
    PASS_WITH_WARNINGS = "pass_with_warnings"  # 有警告通过
    NEEDS_REVISION = "needs_revision"  # 需要修改
    BLOCKED = "blocked"       # 阻塞


@dataclass
class ReviewCriteria:
    """评审标准"""
    name: str                  # 标准名称
    description: str           # 标准描述
    weight: float = 1.0        # 权重
    required: bool = True     # 是否必须
    checker: Optional[Callable] = None  # 检查函数


@dataclass
class ReviewFinding:
    """评审发现"""
    level: ReviewResult        # 严重程度
    category: str              # 分类
    message: str              # 发现内容
    location: Optional[str] = None  # 位置
    suggestion: Optional[str] = None  # 建议
    blocking: bool = False    # 是否阻塞


@dataclass
class ReviewReport:
    """评审报告"""
    review_id: str
    artifact_name: str        # 被评审产物
    review_level: ReviewLevel # 评审级别
    
    # 结果
    result: ReviewResult
    score: float = 0.0        # 评分 0-100
    
    # 详细发现
    findings: List[ReviewFinding] = field(default_factory=list)
    
    # 元数据
    reviewed_by: str = "system"
    reviewed_at: str = ""
    context: Dict[str, Any] = field(default_factory=dict)  # 上下文
    
    # 意图说明（来自 ADR 原则）
    intent_statement: str = ""  # "这次要解决的用户问题是什么"
    temp_implementation: str = ""  # 哪些是临时实现
    
    def __post_init__(self):
        if not self.reviewed_at:
            self.reviewed_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "review_id": self.review_id,
            "artifact_name": self.artifact_name,
            "review_level": self.review_level.value,
            "result": self.result.value,
            "score": self.score,
            "findings": [
                {
                    "level": f.level.value,
                    "category": f.category,
                    "message": f.message,
                    "location": f.location,
                    "suggestion": f.suggestion,
                    "blocking": f.blocking
                }
                for f in self.findings
            ],
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at,
            "intent_statement": self.intent_statement,
            "temp_implementation": self.temp_implementation
        }


class ReviewPipeline:
    """
    分级评审流水线
    
    基于 ADR-003: 评审升级为主流程
    """
    
    # 默认评审标准
    DEFAULT_CRITERIA = {
        ReviewLevel.L0_AUTO: [
            ReviewCriteria(
                name="format_check",
                description="输出格式是否符合预期",
                weight=1.0,
                required=True
            ),
            ReviewCriteria(
                name="syntax_check",
                description="代码语法是否正确",
                weight=1.0,
                required=True
            ),
            ReviewCriteria(
                name="security_check",
                description="是否存在安全风险",
                weight=2.0,
                required=True
            ),
        ],
        ReviewLevel.L1_SELF: [
            ReviewCriteria(
                name="self_validation",
                description="Builder 自检是否完成",
                weight=1.0,
                required=True
            ),
            ReviewCriteria(
                name="test_coverage",
                description="是否有基本测试覆盖",
                weight=1.0,
                required=False
            ),
        ],
        ReviewLevel.L2_PEER: [
            ReviewCriteria(
                name="quality_assessment",
                description="输出质量评估",
                weight=2.0,
                required=True
            ),
            ReviewCriteria(
                name="context_understanding",
                description="是否理解任务上下文",
                weight=2.0,
                required=True
            ),
            ReviewCriteria(
                name="intent_alignment",
                description="是否符合意图说明",
                weight=3.0,
                required=True
            ),
        ],
        ReviewLevel.L3_EXPERT: [
            ReviewCriteria(
                name="architecture_review",
                description="架构设计评审",
                weight=3.0,
                required=True
            ),
            ReviewCriteria(
                name="risk_assessment",
                description="风险评估",
                weight=2.0,
                required=True
            ),
        ]
    }
    
    def __init__(
        self,
        name: str = "default",
        criteria_override: Dict[ReviewLevel, List[ReviewCriteria]] = None
    ):
        self.name = name
        self.criteria = criteria_override or self.DEFAULT_CRITERIA.copy()
        self._review_history: List[ReviewReport] = []
    
    def add_criteria(self, level: ReviewLevel, criteria: ReviewCriteria):
        """添加评审标准"""
        if level not in self.criteria:
            self.criteria[level] = []
        self.criteria[level].append(criteria)
    
    async def review(
        self,
        artifact_name: str,
        artifact_content: Any,
        level: ReviewLevel,
        context: Dict[str, Any] = None,
        intent_statement: str = "",
        temp_implementation: str = ""
    ) -> ReviewReport:
        """
        执行评审
        
        Args:
            artifact_name: 被评审产物名称
            artifact_content: 被评审内容
            level: 评审级别
            context: 上下文信息
            intent_statement: 意图说明
            temp_implementation: 临时实现说明
        """
        review_id = f"rev_{artifact_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        report = ReviewReport(
            review_id=review_id,
            artifact_name=artifact_name,
            review_level=level,
            result=ReviewResult.PASS,  # 默认通过
            context=context or {},
            intent_statement=intent_statement,
            temp_implementation=temp_implementation
        )
        
        # 获取该级别的评审标准
        criteria_list = self.criteria.get(level, [])
        
        # 执行每个标准的检查
        total_weight = 0
        earned_weight = 0
        has_blocking = False
        
        for criteria in criteria_list:
            total_weight += criteria.weight
            
            # 执行检查
            finding = await self._check_criteria(
                criteria, artifact_content, context
            )
            
            if finding:
                report.findings.append(finding)
                
                if finding.blocking:
                    has_blocking = True
                
                # 根据发现调整评分
                if finding.level == ReviewResult.PASS:
                    earned_weight += criteria.weight
                elif finding.level == ReviewResult.PASS_WITH_WARNINGS:
                    earned_weight += criteria.weight * 0.7
                elif finding.level == ReviewResult.NEEDS_REVISION:
                    earned_weight += criteria.weight * 0.3
                # BLOCKED 不加分
        
        # 计算最终评分
        if total_weight > 0:
            report.score = (earned_weight / total_weight) * 100
        
        # 确定评审结果
        if has_blocking:
            report.result = ReviewResult.BLOCKED
        elif report.score >= 80:
            report.result = ReviewResult.PASS
        elif report.score >= 50:
            report.result = ReviewResult.PASS_WITH_WARNINGS
        else:
            report.result = ReviewResult.NEEDS_REVISION
        
        # 保存历史
        self._review_history.append(report)
        
        return report
    
    async def _check_criteria(
        self,
        criteria: ReviewCriteria,
        artifact_content: Any,
        context: Dict[str, Any]
    ) -> Optional[ReviewFinding]:
        """检查单个标准"""
        # 如果有自定义检查函数，执行它
        if criteria.checker:
            try:
                result = await criteria.checker(artifact_content, context)
                if result is True:
                    return None  # 通过
                elif isinstance(result, ReviewFinding):
                    return result
                elif isinstance(result, dict):
                    return ReviewFinding(**result)
            except Exception as e:
                return ReviewFinding(
                    level=ReviewResult.NEEDS_REVISION,
                    category="checker_error",
                    message=f"检查器错误: {str(e)}",
                    blocking=True
                )
        
        # 默认检查逻辑（可扩展）
        return None
    
    def get_history(
        self,
        artifact_name: str = None,
        level: ReviewLevel = None
    ) -> List[ReviewReport]:
        """获取评审历史"""
        history = self._review_history
        
        if artifact_name:
            history = [r for r in history if r.artifact_name == artifact_name]
        
        if level:
            history = [r for r in history if r.review_level == level]
        
        return history
    
    def get_summary(self) -> Dict:
        """获取评审统计"""
        total = len(self._review_history)
        if total == 0:
            return {"total": 0}
        
        by_result = {}
        by_level = {}
        
        for r in self._review_history:
            # 按结果统计
            result_key = r.result.value
            by_result[result_key] = by_result.get(result_key, 0) + 1
            
            # 按级别统计
            level_key = r.review_level.value
            by_level[level_key] = by_level.get(level_key, 0) + 1
        
        return {
            "total": total,
            "by_result": by_result,
            "by_level": by_level,
            "avg_score": sum(r.score for r in self._review_history) / total
        }


# === 便捷函数 ===

def create_default_pipeline() -> ReviewPipeline:
    """创建默认评审流水线"""
    return ReviewPipeline(name="default")


async def quick_review(
    artifact_name: str,
    artifact_content: Any,
    level: ReviewLevel = ReviewLevel.L0_AUTO
) -> ReviewReport:
    """快速评审（单级别）"""
    pipeline = create_default_pipeline()
    return await pipeline.review(artifact_name, artifact_content, level)
