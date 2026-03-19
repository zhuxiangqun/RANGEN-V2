#!/usr/bin/env python3
"""
Two-Stage Reviewer - 两阶段代码审查

借鉴 Superpowers subagent-driven-development skill 的两阶段审查:
- Stage 1: Spec Compliance Review (规范合规性审查)
- Stage 2: Code Quality Review (代码质量审查)

流程:
1. 实现者完成任务
2. Stage 1 审查: 检查是否符合规范
3. Stage 2 审查: 检查代码质量
4. 如果有问题 -> 修复 -> 重新审查
5. 最多 3 次迭代后，如果还有问题则上报给人类
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

# 最大审查迭代次数
MAX_REVIEW_ITERATIONS = 3


@dataclass
class ReviewIssue:
    """审查问题"""
    category: str  # spec, quality, style, security
    severity: str  # error, warning, suggestion
    message: str
    line: Optional[int] = None
    suggestion: Optional[str] = None


@dataclass
class ReviewResult:
    """审查结果"""
    status: str  # pass, fail, needs_work
    stage: str  # stage1, stage2
    iteration: int
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "stage": self.stage,
            "iteration": self.iteration,
            "issues": [asdict(i) for i in self.issues],
            "summary": self.summary,
            "timestamp": self.timestamp
        }


@dataclass 
class CombinedReviewResult:
    """两阶段综合审查结果"""
    stage1_result: ReviewResult
    stage2_result: Optional[ReviewResult] = None
    overall_status: str = "pending"  # pending, pass, needs_work, fail
    iteration: int = 0
    should_surface_to_human: bool = False
    
    def to_dict(self) -> Dict:
        result = {
            "stage1": self.stage1_result.to_dict(),
            "stage2": self.stage2_result.to_dict() if self.stage2_result else None,
            "overall_status": self.overall_status,
            "iteration": self.iteration,
            "should_surface_to_human": self.should_surface_to_human
        }
        return result


class TwoStageReviewer:
    """
    两阶段代码审查器
    
    Stage 1: Spec Compliance Review
    - 检查代码是否符合规范/规格说明书
    - 验证功能需求是否满足
    - 检查接口是否符合预期
    
    Stage 2: Code Quality Review
    - 代码可读性
    - 模式遵循
    - 错误处理
    - 安全性
    """
    
    def __init__(self):
        self._review_history: List[CombinedReviewResult] = []
        self._current_iteration = 0
        
        logger.info("TwoStageReviewer 初始化")
    
    def review_stage1_spec_compliance(
        self, 
        code: str, 
        spec: str = ""
    ) -> ReviewResult:
        """
        Stage 1: 规范合规性审查
        
        检查:
        1. 代码是否实现了规范中描述的功能
        2. 接口是否符合规范定义
        3. 返回值是否符合规范
        4. 是否有遗漏的需求
        """
        issues: List[ReviewIssue] = []
        
        # 如果没有规范，进行基本检查
        if not spec:
            issues.append(ReviewIssue(
                category="spec",
                severity="warning",
                message="没有提供规范文档，只能进行基本检查",
                suggestion="建议提供规范文档以进行更全面的审查"
            ))
        else:
            # 检查规范中的关键词是否在代码中
            spec_keywords = self._extract_keywords(spec)
            code_lower = code.lower()
            
            missing_keywords = []
            for keyword in spec_keywords:
                if keyword.lower() not in code_lower:
                    missing_keywords.append(keyword)
            
            if missing_keywords:
                issues.append(ReviewIssue(
                    category="spec",
                    severity="warning",
                    message=f"规范中的关键词可能在代码中缺失: {', '.join(missing_keywords[:5])}",
                    suggestion="确保代码实现了规范中的所有关键功能"
                ))
        
        # 基本代码结构检查
        if not code.strip():
            issues.append(ReviewIssue(
                category="spec",
                severity="error",
                message="代码为空"
            ))
        
        # 检查是否有 TODO/FIXME（可能表示未完成的功能）
        todo_matches = re.findall(r'(TODO|FIXME|HACK|XXX):*(.*)', code, re.IGNORECASE)
        if todo_matches:
            for match in todo_matches:
                issues.append(ReviewIssue(
                    category="spec",
                    severity="warning",
                    message=f"代码中仍有未完成项: {match[1].strip() if match[1] else 'TODO'}",
                    suggestion="在审查前完成所有 TODO 项"
                ))
        
        # 确定状态
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        
        if errors:
            status = "fail"
            summary = f"发现 {len(errors)} 个错误，{len(warnings)} 个警告"
        elif warnings:
            status = "needs_work"
            summary = f"发现 {len(warnings)} 个警告，建议改进"
        else:
            status = "pass"
            summary = "规范合规性审查通过"
        
        return ReviewResult(
            status=status,
            stage="stage1",
            iteration=self._current_iteration,
            issues=issues,
            summary=summary
        )
    
    def review_stage2_code_quality(
        self, 
        code: str
    ) -> ReviewResult:
        """
        Stage 2: 代码质量审查
        
        检查:
        1. 代码可读性 (命名, 注释)
        2. 模式遵循 (代码风格)
        3. 错误处理
        4. 安全性
        5. 性能考虑
        """
        issues: List[ReviewIssue] = []
        
        lines = code.split('\n')
        
        # 1. 检查长函数 (建议不超过 50 行)
        function_lengths = self._estimate_function_lengths(code)
        for func_name, length in function_lengths.items():
            if length > 50:
                issues.append(ReviewIssue(
                    category="quality",
                    severity="warning",
                    message=f"函数 '{func_name}' 过长 ({length} 行)，建议拆分为更小的函数",
                    suggestion="将长函数拆分为多个职责单一的子函数"
                ))
        
        # 2. 检查缺少注释的函数
        for func_name, length in function_lengths.items():
            if length > 10 and not self._has_docstring(code, func_name):
                issues.append(ReviewIssue(
                    category="quality",
                    severity="warning",
                    message=f"函数 '{func_name}' 没有文档字符串",
                    suggestion="为函数添加 docstring 说明其功能和参数"
                ))
        
        # 3. 检查裸 except
        if re.search(r'except\s*:', code):
            issues.append(ReviewIssue(
                category="quality",
                severity="warning",
                message="发现裸 except 子句，建议捕获具体异常类型",
                suggestion="使用 except SpecificException 而不是 except:"
            ))
        
        # 4. 检查 print 语句 (可能是调试遗留)
        print_matches = re.findall(r'print\s*\(', code)
        if len(print_matches) > 3:
            issues.append(ReviewIssue(
                category="quality",
                severity="suggestion",
                message=f"发现 {len(print_matches)} 处 print 语句，考虑使用日志替代",
                suggestion="使用 logging 模块代替 print 进行日志记录"
            ))
        
        # 5. 检查硬编码值
        hardcoded = self._find_hardcoded_values(code)
        if hardcoded:
            issues.append(ReviewIssue(
                category="quality",
                severity="suggestion",
                message=f"发现 {len(hardcoded)} 处可能的硬编码值",
                suggestion="将硬编码的值提取为常量或配置"
            ))
        
        # 6. 检查安全性问题
        security_issues = self._check_security_issues(code)
        issues.extend(security_issues)
        
        # 确定状态
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]
        
        if errors:
            status = "fail"
            summary = f"发现 {len(errors)} 个错误，{len(warnings)} 个警告"
        elif warnings:
            status = "needs_work"
            summary = f"发现 {len(warnings)} 个警告，建议改进"
        else:
            status = "pass"
            summary = "代码质量审查通过"
        
        return ReviewResult(
            status=status,
            stage="stage2",
            iteration=self._current_iteration,
            issues=issues,
            summary=summary
        )
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从规范中提取关键词"""
        # 简单实现：提取被引号包围的词和驼峰命名
        quoted = re.findall(r'["\']([A-Z][a-zA-Z]+)["\']', text)
        camel_case = re.findall(r'\b([A-Z][a-z]+[A-Z][a-zA-Z]+)\b', text)
        return list(set(quoted + camel_case))
    
    def _estimate_function_lengths(self, code: str) -> Dict[str, int]:
        """估算函数长度"""
        functions = {}
        
        # 匹配函数定义
        func_pattern = r'def\s+(\w+)\s*\([^)]*\):'
        matches = list(re.finditer(func_pattern, code))
        
        for i, match in enumerate(matches):
            func_name = match.group(1)
            start = match.start()
            
            # 找到下一个函数或文件结束
            if i + 1 < len(matches):
                end = matches[i + 1].start()
            else:
                end = len(code)
            
            # 计算行数
            func_code = code[start:end]
            lines = [l for l in func_code.split('\n') if l.strip() and not l.strip().startswith('#')]
            functions[func_name] = len(lines)
        
        return functions
    
    def _has_docstring(self, code: str, func_name: str) -> bool:
        """检查函数是否有文档字符串"""
        pattern = rf'def\s+{func_name}\s*\([^)]*\):\s*["\']'
        match = re.search(pattern, code)
        if match:
            # 检查是否有三引号紧跟
            start = match.end()
            return code[start:start+3] in ['"""', "'''"]
        return False
    
    def _find_hardcoded_values(self, code: str) -> List[str]:
        """查找硬编码值"""
        hardcoded = []
        
        # 查找魔法数字
        magic_numbers = re.findall(r'(?<!\w)\d{4,}(?!\w)', code)
        hardcoded.extend([f"数字: {n}" for n in magic_numbers[:3]])
        
        # 查找可能的硬编码路径
        paths = re.findall(r'["\'](?:/[\w/.-]+|C:\\[\w\\.-]+)["\']', code)
        hardcoded.extend([f"路径: {p}" for p in paths[:2]])
        
        return hardcoded
    
    def _check_security_issues(self, code: str) -> List[ReviewIssue]:
        """检查安全性问题"""
        issues = []
        
        # 检查 eval/exec 使用
        if 'eval(' in code:
            issues.append(ReviewIssue(
                category="security",
                severity="error",
                message="发现 eval() 使用，存在代码注入风险",
                suggestion="使用 ast.literal_eval 或其他安全方法替代"
            ))
        
        if 'exec(' in code:
            issues.append(ReviewIssue(
                category="security",
                severity="error",
                message="发现 exec() 使用，存在代码注入风险",
                suggestion="避免使用 exec()，考虑重新设计"
            ))
        
        # 检查 SQL 拼接 (简单的检查)
        if re.search(r'["\'].*%s.*["\'].*%', code) and ('sql' in code.lower() or 'query' in code.lower()):
            issues.append(ReviewIssue(
                category="security",
                severity="error",
                message="可能的 SQL 注入风险",
                suggestion="使用参数化查询"
            ))
        
        return issues
    
    def run_review(
        self, 
        code: str, 
        spec: str = ""
    ) -> CombinedReviewResult:
        """
        运行两阶段审查
        
        流程:
        1. Stage 1: 规范合规性审查
        2. Stage 2: 代码质量审查
        3. 综合判断结果
        """
        self._current_iteration += 1
        iteration = self._current_iteration
        
        logger.info(f"开始第 {iteration} 轮审查")
        
        # Stage 1: 规范合规性审查
        stage1_result = self.review_stage1_spec_compliance(code, spec)
        logger.info(f"Stage 1 结果: {stage1_result.status} - {stage1_result.summary}")
        
        # Stage 2: 代码质量审查
        stage2_result = self.review_stage2_code_quality(code)
        logger.info(f"Stage 2 结果: {stage2_result.status} - {stage2_result.summary}")
        
        # 综合判断
        combined = CombinedReviewResult(
            stage1_result=stage1_result,
            stage2_result=stage2_result,
            iteration=iteration
        )
        
        # 总体状态
        if stage1_result.status == "fail" or stage2_result.status == "fail":
            combined.overall_status = "fail"
        elif stage1_result.status == "needs_work" or stage2_result.status == "needs_work":
            combined.overall_status = "needs_work"
        else:
            combined.overall_status = "pass"
        
        # 是否需要上报给人类
        if iteration >= MAX_REVIEW_ITERATIONS and combined.overall_status != "pass":
            combined.should_surface_to_human = True
            logger.warning(f"达到最大迭代次数 ({MAX_REVIEW_ITERATIONS})，需要人类介入")
        
        self._review_history.append(combined)
        
        return combined
    
    def get_review_result(self, iteration: Optional[int] = None) -> Optional[CombinedReviewResult]:
        """
        获取审查结果
        
        Args:
            iteration: 如果指定，返回特定迭代的结果；否则返回最新的结果
        """
        if iteration is not None:
            for result in self._review_history:
                if result.iteration == iteration:
                    return result
            return None
        
        if self._review_history:
            return self._review_history[-1]
        
        return None
    
    def get_review_history(self) -> List[Dict]:
        """获取审查历史"""
        return [r.to_dict() for r in self._review_history]
    
    def reset(self):
        """重置审查器状态"""
        self._review_history = []
        self._current_iteration = 0
        logger.info("审查器状态已重置")
    
    def get_issues_summary(self) -> Dict[str, int]:
        """获取问题统计摘要"""
        all_issues = []
        
        for result in self._review_history:
            all_issues.extend(result.stage1_result.issues)
            if result.stage2_result:
                all_issues.extend(result.stage2_result.issues)
        
        summary = {
            "total": len(all_issues),
            "errors": len([i for i in all_issues if i.severity == "error"]),
            "warnings": len([i for i in all_issues if i.severity == "warning"]),
            "suggestions": len([i for i in all_issues if i.severity == "suggestion"]),
        }
        
        # 按类别统计
        for category in ["spec", "quality", "security"]:
            summary[category] = len([i for i in all_issues if i.category == category])
        
        return summary


# 全局单例
_reviewer: Optional[TwoStageReviewer] = None


def get_reviewer() -> TwoStageReviewer:
    """获取全局 TwoStageReviewer 实例"""
    global _reviewer
    if _reviewer is None:
        _reviewer = TwoStageReviewer()
    return _reviewer
