"""
Agent 自动化评审系统

核心功能：
- Agent 写代码 → Agent 审代码
- 自动化评审循环
- 人类只在关键节点介入
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class ReviewDecision(Enum):
    """评审决策"""
    APPROVE = "approve"          # 批准
    REQUEST_CHANGES = "request_changes"  # 要求修改
    NEEDS_HUMAN = "needs_human"  # 需要人工


@dataclass
class CodeChange:
    """代码变更"""
    file_path: str
    diff: str
    language: str = "python"
    

@dataclass
class ReviewComment:
    """评审意见"""
    line: Optional[int]
    comment: str
    severity: str  # info, warning, error
    category: str  # style, logic, security, performance
    

@dataclass
class ReviewResult:
    """评审结果"""
    change: CodeChange
    decision: ReviewDecision
    comments: List[ReviewComment]
    score: float  # 质量分数 0-100
    needs_human_review: bool
    summary: str
    
    def to_dict(self) -> Dict:
        return {
            "file": self.change.file_path,
            "decision": self.decision.value,
            "score": self.score,
            "needs_human": self.needs_human_review,
            "summary": self.summary,
            "comments": [
                {
                    "line": c.line,
                    "comment": c.comment,
                    "severity": c.severity,
                    "category": c.category
                }
                for c in self.comments
            ]
        }


class AgentReviewer:
    """
    Agent 代码评审器
    
    工作流程:
    1. Agent A 提交代码变更
    2. Agent Reviewer 评审
    3. 如果有问题 → 返回修改建议 → Agent A 修复 → 再次评审
    4. 如果通过 → 标记为需要人类审批或自动批准
    """
    
    def __init__(self, llm_service=None):
        self.llm_service = llm_service
        self.review_history: List[ReviewResult] = []
        
        # 评审规则
        self.rules = {
            "min_score": 70,          # 最低质量分数
            "max_iterations": 3,       # 最大评审轮次
            "auto_approve_threshold": 85,  # 自动批准阈值
        }
    
    def review(self, change: CodeChange) -> ReviewResult:
        """评审代码变更"""
        
        # 检查代码变更
        issues = self._check_basic_issues(change)
        
        # 如果有严重问题，直接返回
        if any(c.severity == "error" for c in issues):
            return ReviewResult(
                change=change,
                decision=ReviewDecision.REQUEST_CHANGES,
                comments=issues,
                score=50,
                needs_human_review=True,
                summary="发现严重问题，需要人工审查"
            )
        
        # 使用 LLM 进行深度评审
        if self.llm_service:
            llm_result = self._llm_review(change)
            issues.extend(llm_result.comments)
            score = llm_result.score
        else:
            # 简化评审
            score = self._calculate_score(issues)
        
        # 决策
        if score >= self.rules["auto_approve_threshold"]:
            decision = ReviewDecision.APPROVE
            needs_human = False
            summary = f"质量分数 {score}，自动批准"
        elif score >= self.rules["min_score"]:
            decision = ReviewDecision.APPROVE
            needs_human = True  # 仍需人类最终确认
            summary = f"质量分数 {score}，需要人类审批"
        else:
            decision = ReviewDecision.REQUEST_CHANGES
            needs_human = True
            summary = f"质量分数 {score}，需要修改"
        
        result = ReviewResult(
            change=change,
            decision=decision,
            comments=issues,
            score=score,
            needs_human_review=needs_human,
            summary=summary
        )
        
        self.review_history.append(result)
        return result
    
    def _check_basic_issues(self, change: CodeChange) -> List[ReviewComment]:
        """基础问题检查"""
        issues = []
        
        # 检查文件是否存在
        from pathlib import Path
        if not Path(change.file_path).exists():
            issues.append(ReviewComment(
                line=None,
                comment=f"文件 {change.file_path} 不存在",
                severity="error",
                category="logic"
            ))
        
        # 检查空 diff
        if not change.diff or change.diff.strip() == "":
            issues.append(ReviewComment(
                line=None,
                comment="代码变更为空",
                severity="error",
                category="logic"
            ))
        
        # 检查危险操作
        dangerous_patterns = [
            ("rm -rf", "危险命令: rm -rf"),
            ("eval(", "危险: eval() 可能导致代码注入"),
            ("exec(", "危险: exec() 可能导致代码注入"),
            ("pickle.load", "安全: pickle 不安全，考虑使用 json"),
            ("password", "安全: 硬编码密码，请使用环境变量"),
            ("api_key", "安全: 硬编码 API Key，请使用环境变量"),
        ]
        
        for pattern, msg in dangerous_patterns:
            if pattern in change.diff:
                issues.append(ReviewComment(
                    line=None,
                    comment=f"安全警告: {msg}",
                    severity="warning" if "password" not in pattern else "error",
                    category="security"
                ))
        
        return issues
    
    def _llm_review(self, change: CodeChange) -> ReviewResult:
        """使用 LLM 进行深度评审"""
        # 这里调用 LLM 进行代码评审
        # 返回结构化的评审结果
        
        prompt = f"""请评审以下代码变更:

文件: {change.file_path}
语言: {change.language}

代码差异:
{change.diff}

请从以下维度评审:
1. 代码风格
2. 逻辑正确性
3. 安全性
4. 性能
5. 可维护性

返回 JSON 格式:
{{
    "score": 0-100,
    "issues": [
        {{"line": 行号, "comment": 问题描述, "severity": "info/warning/error", "category": "风格/逻辑/安全/性能"}}
    ],
    "summary": "总结"
}}
"""
        # 实际使用时调用 LLM
        # 这里返回模拟结果
        return ReviewResult(
            change=change,
            decision=ReviewDecision.APPROVE,
            comments=[],
            score=85,
            needs_human_review=False,
            summary="LLM 评审通过"
        )
    
    def _calculate_score(self, issues: List[ReviewComment]) -> float:
        """计算质量分数"""
        base_score = 100
        
        # 扣分
        for issue in issues:
            if issue.severity == "error":
                base_score -= 20
            elif issue.severity == "warning":
                base_score -= 5
            else:
                base_score -= 1
        
        return max(0, base_score)
    
    def auto_review_loop(self, change: CodeChange) -> ReviewResult:
        """自动化评审循环"""
        iteration = 0
        current_change = change
        result = self.review(current_change)  # 初始化 result
        
        while iteration < self.rules["max_iterations"]:
            result = self.review(current_change)
            
            if result.decision == ReviewDecision.APPROVE:
                return result
            
            logger.info(f"Review iteration {iteration + 1}: {result.summary}")
            
            iteration += 1
        
        # 超过最大轮次，返回最后一次结果
        return result


class AgentReviewSystem:
    """
    Agent 评审系统
    
    管理多个 Agent 之间的评审循环
    """
    
    def __init__(self):
        self.reviewer = AgentReviewer()
        self.pending_reviews: List[CodeChange] = []
        self.completed_reviews: List[ReviewResult] = []
    
    def submit_for_review(self, change: CodeChange) -> str:
        """提交代码变更供评审"""
        review_id = f"review_{len(self.completed_reviews)}_{datetime.now().timestamp()}"
        self.pending_reviews.append(change)
        return review_id
    
    def process_pending(self) -> List[ReviewResult]:
        """处理所有待评审"""
        results = []
        while self.pending_reviews:
            change = self.pending_reviews.pop(0)
            result = self.reviewer.auto_review_loop(change)
            results.append(result)
            self.completed_reviews.append(result)
        return results
    
    def get_stats(self) -> Dict:
        """获取评审统计"""
        if not self.completed_reviews:
            return {"total": 0, "approved": 0, "rejected": 0}
        
        approved = sum(1 for r in self.completed_reviews 
                      if r.decision == ReviewDecision.APPROVE)
        rejected = sum(1 for r in self.completed_reviews 
                      if r.decision == ReviewDecision.REQUEST_CHANGES)
        
        avg_score = sum(r.score for r in self.completed_reviews) / len(self.completed_reviews)
        
        return {
            "total": len(self.completed_reviews),
            "approved": approved,
            "rejected": rejected,
            "avg_score": avg_score,
            "pending": len(self.pending_reviews)
        }
    
    def review_text(self, content: str, content_type: str = "code") -> ReviewResult:
        """
        评审文本内容（不写入文件）
        
        Args:
            content: 要评审的文本内容
            content_type: 内容类型 ("code", "answer", "explanation")
            
        Returns:
            ReviewResult: 评审结果
        """
        change = CodeChange(
            file_path="<agent_output>",
            diff=content
        )
        
        # 使用现有的 reviewer 进行评审
        return self.reviewer.auto_review_loop(change)
    
    def check_output_correctness(self, output: str, expected: Optional[str] = None) -> Dict[str, Any]:
        """
        检查 Agent 输出的正确性
        
        Args:
            output: Agent 生成的输出
            expected: 预期的输出（如果有）
            
        Returns:
            Dict with correctness metrics
        """
        correctness = {
            "has_output": len(output.strip()) > 0,
            "length": len(output),
            "sentences_count": 0,
            "has_hallucination_risk": False,
            "confidence": 0.0,
            "issues": []
        }
        
        # 统计句子数
        import re
        sentences = re.split(r'[.!?]+', output)
        correctness["sentences_count"] = len([s for s in sentences if s.strip()])
        
        # 检查幻觉风险模式
        hallucination_patterns = [
            r"I am not sure",
            r"might be",
            r"could be",
            r"possibly",
            r"perhaps"
        ]
        risk_count = sum(1 for p in hallucination_patterns if re.search(p, output, re.I))
        correctness["has_hallucination_risk"] = risk_count > 2
        
        # 如果有预期输出，进行简单比较
        if expected:
            # 简化比较：检查关键词重叠
            output_words = set(output.lower().split())
            expected_words = set(expected.lower().split())
            overlap = len(output_words & expected_words) / max(len(expected_words), 1)
            correctness["keyword_overlap"] = overlap
            correctness["confidence"] = min(overlap * 1.2, 1.0)
        
        return correctness


# 全局单例
_global_review_system: Optional[AgentReviewSystem] = None

def get_review_system() -> AgentReviewSystem:
    """获取全局评审系统"""
    global _global_review_system
    if _global_review_system is None:
        _global_review_system = AgentReviewSystem()
    return _global_review_system


# ============ 便捷函数 ============

def review_code(file_path: str, diff: str) -> Dict:
    """快速评审代码"""
    change = CodeChange(file_path=file_path, diff=diff)
    result = get_review_system().reviewer.review(change)
    return result.to_dict()


def submit_review(change: CodeChange) -> str:
    """提交代码供评审"""
    return get_review_system().submit_for_review(change)
