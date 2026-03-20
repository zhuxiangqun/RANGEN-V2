#!/usr/bin/env python3
"""
BlockingReviewer - Critical 问题阻塞审查器

基于 Superpowers subagent-driven-development 的严格审查机制:
- CRITICAL/HIGH 问题阻塞合并
- MEDIUM 问题警告
- 确保只有符合质量标准的代码才能进入生产

Blocking Categories:
1. security: 安全漏洞
2. correctness: 逻辑错误
3. breaking_change: 破坏性变更
4. missing_test: 缺失测试
5. spec_violation: 规范违反

Usage:
    from src.agents.blocking_reviewer import BlockingReviewer
    
    reviewer = BlockingReviewer()
    result = reviewer.review(code, spec)
    
    if result.status == "blocked":
        print(f"🔴 BLOCKED: {result.summary}")
        for issue in result.issues:
            print(f"  - {issue.severity}: {issue.message}")
"""

import re
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)

# 最大审查迭代次数
MAX_REVIEW_ITERATIONS = 3


class IssueSeverity(Enum):
    """问题严重级别"""
    CRITICAL = "critical"  # 阻塞 - 必须修复
    HIGH = "high"          # 阻塞 - 应该修复
    MEDIUM = "medium"      # 警告 - 建议修复
    LOW = "low"            # 建议 - 可选修复


class IssueCategory(Enum):
    """问题分类"""
    SECURITY = "security"          # 安全漏洞
    CORRECTNESS = "correctness"    # 逻辑错误
    BREAKING_CHANGE = "breaking_change"  # 破坏性变更
    MISSING_TEST = "missing_test"  # 缺失测试
    SPEC_VIOLATION = "spec_violation"  # 规范违反
    STYLE = "style"              # 代码风格
    PERFORMANCE = "performance"  # 性能问题
    MAINTAINABILITY = "maintainability"  # 可维护性


@dataclass
class BlockingIssue:
    """阻塞性问题"""
    category: str           # 问题分类
    severity: str           # 严重级别
    message: str            # 问题描述
    line: Optional[int] = None    # 代码行号
    suggestion: Optional[str] = None  # 修复建议
    code_snippet: Optional[str] = None  # 相关代码片段
    blocking: bool = False   # 是否阻塞
    
    def __post_init__(self):
        # CRITICAL 和 HIGH 默认阻塞
        self.blocking = self.severity in ["critical", "high"]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BlockingReviewResult:
    """阻塞审查结果"""
    status: str  # "blocked", "pass", "warning", "needs_work"
    iteration: int
    issues: List[BlockingIssue] = field(default_factory=list)
    summary: str = ""
    timestamp: str = ""
    blocking_count: int = 0
    warning_count: int = 0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        self.blocking_count = sum(1 for i in self.issues if i.blocking)
        self.warning_count = sum(1 for i in self.issues if not i.blocking)
    
    def is_blocked(self) -> bool:
        return self.status == "blocked"
    
    def get_blocking_issues(self) -> List[BlockingIssue]:
        return [i for i in self.issues if i.blocking]
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "iteration": self.iteration,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary,
            "timestamp": self.timestamp,
            "blocking_count": self.blocking_count,
            "warning_count": self.warning_count
        }


class BlockingReviewer:
    """
    阻塞式代码审查器
    
    规则:
    - CRITICAL/HIGH 问题: 阻塞合并 (status="blocked")
    - MEDIUM 问题: 警告 (status="warning")
    - LOW 问题: 建议 (包含在结果中)
    - 无问题: status="pass"
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 阻塞关键词模式
        self._security_patterns = [
            (r'sql\s*\+.*["\']', "potential SQL injection"),
            (r'eval\s*\(', "use of eval() is dangerous"),
            (r'exec\s*\(', "use of exec() is dangerous"),
            (r'os\.system\s*\(', "use of os.system() is dangerous"),
            (r'subprocess.*shell\s*=\s*True', "shell=True is dangerous"),
            (r'password\s*=\s*["\'][^"\']+["\']', "hardcoded password detected"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "hardcoded API key detected"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "hardcoded secret detected"),
            (r'\.format\s*\(.*["\'].*{.*}', "potential format string vulnerability"),
            (r'pickle\.loads?', "use of pickle is unsafe"),
        ]
        
        self._correctness_patterns = [
            (r'==\s*(True|False|None)\s*(and|or)', "comparison precedence issue"),
            (r'if\s+\w+\s+is\s+["\']', "use == instead of is for string comparison"),
            (r'return\s+.*\s+\w+\s*=\s*', "assignment in return statement"),
            (r'\w+\s*=\s*None\s*(and|or)\s*\w+', "None comparison issue"),
            (r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(', "loop over range(len()) anti-pattern"),
        ]
        
        self._breaking_change_patterns = [
            (r'def\s+\w+\s*\([^)]*\)\s*:', "function definition"),
            (r'class\s+\w+\s*[\(:]', "class definition"),
            (r'@abstractmethod', "abstract method"),
            (r'async\s+def', "async function change"),
        ]
        
        # 编译正则表达式
        self._compiled_security = [
            (re.compile(p, re.IGNORECASE), msg) 
            for p, msg in self._security_patterns
        ]
        self._compiled_correctness = [
            (re.compile(p, re.IGNORECASE), msg) 
            for p, msg in self._correctness_patterns
        ]
        self._compiled_breaking = [
            (re.compile(p), msg) 
            for p, msg in self._breaking_change_patterns
        ]
    
    def review(
        self, 
        code: str, 
        spec: Optional[str] = None,
        iteration: int = 1,
        require_tests: bool = True
    ) -> BlockingReviewResult:
        """
        审查代码并返回阻塞结果
        
        Args:
            code: 要审查的代码
            spec: 可选的规范文档
            iteration: 审查迭代次数
            require_tests: 是否要求测试
            
        Returns:
            BlockingReviewResult: 审查结果
        """
        issues = []
        
        # 1. 安全审查
        security_issues = self._check_security(code)
        issues.extend(security_issues)
        
        # 2. 正确性审查
        correctness_issues = self._check_correctness(code)
        issues.extend(correctness_issues)
        
        # 3. 破坏性变更检查
        breaking_issues = self._check_breaking_changes(code)
        issues.extend(breaking_issues)
        
        # 4. 规范审查 (如果提供了规范)
        if spec:
            spec_issues = self._check_spec_compliance(code, spec)
            issues.extend(spec_issues)
        
        # 5. 测试检查
        if require_tests:
            test_issues = self._check_test_coverage(code)
            issues.extend(test_issues)
        
        # 确定状态
        blocking_issues = [i for i in issues if i.blocking]
        
        if blocking_issues:
            status = "blocked"
            summary = f"🔴 BLOCKED: Found {len(blocking_issues)} blocking issue(s)"
        elif any(i.severity == "medium" for i in issues):
            status = "warning"
            summary = f"⚠️  WARNING: Found {len(issues)} issue(s) - review recommended"
        elif issues:
            status = "needs_work"
            summary = f"📋 NEEDS WORK: Found {len(issues)} issue(s) - fix warnings"
        else:
            status = "pass"
            summary = "✅ PASSED: No blocking issues found"
        
        return BlockingReviewResult(
            status=status,
            iteration=iteration,
            issues=issues,
            summary=summary
        )
    
    def _check_security(self, code: str) -> List[BlockingIssue]:
        """检查安全漏洞"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for pattern, msg in self._compiled_security:
                if pattern.search(line):
                    issues.append(BlockingIssue(
                        category=IssueCategory.SECURITY.value,
                        severity=IssueSeverity.CRITICAL.value,
                        message=f"Security: {msg}",
                        line=line_num,
                        code_snippet=line.strip(),
                        suggestion=self._get_security_suggestion(msg)
                    ))
        
        return issues
    
    def _check_correctness(self, code: str) -> List[BlockingIssue]:
        """检查逻辑错误"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 跳过注释
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            
            for pattern, msg in self._compiled_correctness:
                if pattern.search(line):
                    issues.append(BlockingIssue(
                        category=IssueCategory.CORRECTNESS.value,
                        severity=IssueSeverity.HIGH.value,
                        message=f"Correctness: {msg}",
                        line=line_num,
                        code_snippet=line.strip(),
                        suggestion=self._get_correctness_suggestion(msg)
                    ))
        
        return issues
    
    def _check_breaking_changes(self, code: str) -> List[BlockingIssue]:
        """检查破坏性变更"""
        issues = []
        lines = code.split('\n')
        
        # 检查是否有新增的公开接口
        for line_num, line in enumerate(lines, 1):
            for pattern, msg in self._compiled_breaking:
                if pattern.search(line):
                    issues.append(BlockingIssue(
                        category=IssueCategory.BREAKING_CHANGE.value,
                        severity=IssueSeverity.MEDIUM.value,
                        message=f"Breaking change: {msg}",
                        line=line_num,
                        code_snippet=line.strip(),
                        suggestion="Ensure backward compatibility or update version"
                    ))
        
        return issues
    
    def _check_spec_compliance(self, code: str, spec: str) -> List[BlockingIssue]:
        """检查规范合规性"""
        issues = []
        
        # 检查 spec 中定义的关键功能是否实现
        required_pattern = r'(?:功能|feature|requirement|require)[:：]\s*([^\n]+)'
        for match in re.finditer(required_pattern, spec, re.IGNORECASE):
            requirement = match.group(1).strip()
            # 检查代码中是否包含这个功能的关键字
            keywords = [w for w in requirement.split() if len(w) > 3]
            if keywords:
                found = any(kw.lower() in code.lower() for kw in keywords[:3])
                if not found:
                    issues.append(BlockingIssue(
                        category=IssueCategory.SPEC_VIOLATION.value,
                        severity=IssueSeverity.HIGH.value,
                        message=f"Spec violation: Missing implementation for '{requirement}'",
                        suggestion=f"Implement the required feature: {requirement}"
                    ))
        
        return issues
    
    def _check_test_coverage(self, code: str) -> List[BlockingIssue]:
        """检查测试覆盖率"""
        issues = []
        
        # 检查是否有测试相关的代码
        has_code = bool(code.strip())
        has_test_indicators = any([
            'test' in code.lower(),
            'unittest' in code.lower(),
            'pytest' in code.lower(),
            'assert' in code.lower(),
        ])
        
        # 如果是生产代码但没有测试指标
        production_indicators = ['def ', 'class ', 'async def ']
        is_production = any(ind in code for ind in production_indicators)
        
        if is_production and not has_test_indicators and not code.startswith('#'):
            issues.append(BlockingIssue(
                category=IssueCategory.MISSING_TEST.value,
                severity=IssueSeverity.HIGH.value,
                message="Missing test: Production code requires tests",
                suggestion="Add tests before implementing this code"
            ))
        
        return issues
    
    def _get_security_suggestion(self, issue: str) -> str:
        """获取安全问题的修复建议"""
        suggestions = {
            "SQL injection": "Use parameterized queries or ORM",
            "eval()": "Use ast.literal_eval() or safer alternatives",
            "exec()": "Avoid dynamic code execution",
            "os.system()": "Use subprocess.run() with list arguments",
            "shell=True": "Use shell=False and pass arguments as list",
            "hardcoded password": "Use environment variables or secrets manager",
            "hardcoded API key": "Use environment variables or secrets manager",
            "hardcoded secret": "Use environment variables or secrets manager",
            "format string": "Use f-strings or .format() with named arguments only",
            "pickle": "Use json or safer serialization"
        }
        
        for key, suggestion in suggestions.items():
            if key in issue:
                return suggestion
        return "Review security best practices"
    
    def _get_correctness_suggestion(self, issue: str) -> str:
        """获取正确性问题的修复建议"""
        suggestions = {
            "comparison precedence": "Use parentheses to clarify precedence",
            "string comparison": "Use == instead of is for string comparison",
            "assignment in return": "Separate assignment and return",
            "None comparison": "Use 'is None' or 'is not None' explicitly",
            "range(len())": "Use enumerate() or direct iteration"
        }
        
        for key, suggestion in suggestions.items():
            if key in issue:
                return suggestion
        return "Review Python best practices"
    
    def review_file(
        self, 
        file_path: str, 
        spec: Optional[str] = None
    ) -> BlockingReviewResult:
        """审查文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            return self.review(code, spec)
        except FileNotFoundError:
            return BlockingReviewResult(
                status="blocked",
                iteration=1,
                issues=[BlockingIssue(
                    category="correctness",
                    severity="critical",
                    message=f"File not found: {file_path}"
                )],
                summary=f"🔴 BLOCKED: File not found: {file_path}"
            )
        except Exception as e:
            return BlockingReviewResult(
                status="blocked",
                iteration=1,
                issues=[BlockingIssue(
                    category="correctness",
                    severity="critical",
                    message=f"Error reading file: {str(e)}"
                )],
                summary=f"🔴 BLOCKED: Error reading file: {str(e)}"
            )


# ============================================================================
# Demo / Tests
# ============================================================================

if __name__ == "__main__":
    print("=== BlockingReviewer Demo ===\n")
    
    reviewer = BlockingReviewer()
    
    # Test 1: Security Issue
    print("1. Security Issue Test:")
    code_with_security = '''
def query_database(user_input):
    query = "SELECT * FROM users WHERE name = '" + user_input + "'"
    return execute(query)
'''
    result = reviewer.review(code_with_security)
    print(f"   Status: {result.status}")
    print(f"   Issues: {len(result.issues)}")
    for issue in result.issues:
        print(f"   - [{issue.severity}] {issue.message}")
        if issue.suggestion:
            print(f"     Suggestion: {issue.suggestion}")
    print()
    
    # Test 2: Correctness Issue
    print("2. Correctness Issue Test:")
    code_with_correctness = '''
def process_data(items):
    for i in range(len(items)):
        print(items[i])
'''
    result = reviewer.review(code_with_correctness)
    print(f"   Status: {result.status}")
    print(f"   Issues: {len(result.issues)}")
    for issue in result.issues:
        print(f"   - [{issue.severity}] {issue.message}")
    print()
    
    # Test 3: Missing Test
    print("3. Missing Test Issue:")
    production_code = '''
class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, item):
        self.data.append(item)
        return len(self.data)
'''
    result = reviewer.review(production_code)
    print(f"   Status: {result.status}")
    print(f"   Blocking: {result.blocking_count}")
    print(f"   Warnings: {result.warning_count}")
    print()
    
    # Test 4: Clean Code
    print("4. Clean Code Test:")
    clean_code = '''
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b


# Tests would be in a separate file
'''
    result = reviewer.review(clean_code, require_tests=False)
    print(f"   Status: {result.status}")
    print(f"   Issues: {len(result.issues)}")
    print()
    
    # Test 5: Spec Compliance
    print("5. Spec Compliance Test:")
    spec = """
功能: 用户认证
- 登录功能
- 登出功能
- 密码重置
"""
    partial_impl = '''
def login(username, password):
    """User login."""
    pass

def logout():
    """User logout."""
    pass
'''
    result = reviewer.review(partial_impl, spec=spec)
    print(f"   Status: {result.status}")
    for issue in result.issues:
        print(f"   - [{issue.severity}] {issue.message}")
    print()
    
    # Test 6: Combined Review
    print("6. Combined Review Result:")
    combined_code = '''
import pickle
import os

def load_config(path):
    with open(path, 'rb') as f:
        return pickle.load(f)

password = "hardcoded123"

def process():
    os.system("rm -rf /")
'''
    result = reviewer.review(combined_code)
    print(f"   Status: {result.status}")
    print(f"   Blocking Issues: {result.blocking_count}")
    for issue in result.get_blocking_issues():
        print(f"   🔴 [{issue.severity}] {issue.message} (line {issue.line})")
    print(f"\n   Summary: {result.summary}")
    print()
    
    print("=== Demo Complete ===")
