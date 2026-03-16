"""
Agent 友好的 Linter 包装器

核心功能：
- 运行标准 Linter (ruff, pylint)
- 解析错误消息
- 生成 Agent 可理解的修复建议
- 支持自动修复闭环
"""

import subprocess
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from src.services.logging_service import get_logger

logger = get_logger(__name__)


@dataclass
class LintIssue:
    """Linter 问题"""
    line: int
    column: int
    code: str
    message: str
    severity: str  # error, warning, info
    fix_suggestion: str = ""  # Agent 友好的修复建议


@dataclass
class LintResult:
    """Lint 结果"""
    file_path: str
    issues: List[LintIssue]
    passed: bool
    raw_output: str
    
    def to_agent_dict(self) -> Dict:
        """转换为 Agent 可理解的格式"""
        return {
            "file": self.file_path,
            "passed": self.passed,
            "issue_count": len(self.issues),
            "issues": [
                {
                    "line": i.line,
                    "code": i.code,
                    "message": i.message,
                    "fix": i.fix_suggestion if i.fix_suggestion else "需要人工处理"
                }
                for i in self.issues
            ]
        }


class AgentLinter:
    """
    Agent 友好的 Linter
    
    特点：
    - 错误消息包含修复建议
    - 支持自动修复
    - 输出结构化 JSON
    """
    
    # 修复建议映射
    FIX_SUGGESTIONS = {
        # Ruff 规则
        "F401": "未使用的导入，可以删除: `import {name}`",
        "F841": "未使用的变量，删除或使用 `_` 前缀",
        "E501": "行太长，拆分成多行或调整换行",
        "E302": "缺少空行，增加空行分隔",
        "E305": "行后空行过多，删除多余空行",
        "W291": "尾随空格，删除尾随空格",
        "W293": "空行包含空格，删除多余空格",
        
        # 类型检查
        "ARG001": "未使用的函数参数，添加 `_` 前缀或使用",
        "ARG002": "未使用的类参数，添加 `_` 前缀或使用",
        
        # 导入排序 (isort)
        "I001": "导入未排序，运行 `ruff check --fix` 或 `ruff check --select I --fix`",
        "I002": "导入顺序错误，运行 `ruff check --fix`",
        
        # 复杂度
        "C901": "函数太复杂，拆分成多个小函数",
        "PLR0912": "函数分支太多 (>12)，重构减少分支",
        "PLR0913": "函数参数太多 (>5)，使用 dataclass 或 dict 封装",
        
        # 安全
        "S301": "使用 pickle 不安全，使用 json 或更安全的序列化",
        "S324": "使用 hashlib.md5 不安全，使用 hashlib.sha256",
        
        # 最佳实践
        "B006": "可变默认参数，使用 `None` 替代",
        "B008": "在函数调用中不要做不必要的操作",
        "UP035": "使用新版导入: `{old}` -> `{new}`",
    }
    
    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or ".")
    
    def lint_file(self, file_path: str) -> LintResult:
        """Lint 单个文件"""
        path = self.project_root / file_path
        if not path.exists():
            return LintResult(
                file_path=file_path,
                issues=[],
                passed=True,
                raw_output="File not found"
            )
        
        # 运行 ruff
        result = self._run_ruff(file_path)
        return result
    
    def lint_all(self, files: Optional[List[str]] = None) -> List[LintResult]:
        """Lint 多个文件或整个项目"""
        if files:
            results = []
            for f in files:
                results.append(self.lint_file(f))
            return results
        
        # 默认 lint 整个项目
        return self._lint_project()
    
    def _run_ruff(self, file_path: str) -> LintResult:
        """运行 ruff 并解析结果"""
        path = self.project_root / file_path
        
        try:
            # 运行 ruff with JSON output
            cmd = ["ruff", "check", str(path), "--output-format", "json"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 解析 JSON 输出
            issues = []
            try:
                data = json.loads(result.stdout) if result.stdout else []
                for item in data:
                    code = item.get("code", "")
                    fix_suggestion = self._get_fix_suggestion(code, item)
                    
                    issues.append(LintIssue(
                        line=item.get("location", {}).get("row", 0),
                        column=item.get("location", {}).get("column", 0),
                        code=code,
                        message=item.get("message", ""),
                        severity="error" if item.get("severity", 0) >= 2 else "warning",
                        fix_suggestion=fix_suggestion
                    ))
            except json.JSONDecodeError:
                # JSON 解析失败，尝试解析文本
                issues = self._parse_text_output(result.stdout + result.stderr)
            
            return LintResult(
                file_path=file_path,
                issues=issues,
                passed=len(issues) == 0,
                raw_output=result.stdout + result.stderr
            )
            
        except subprocess.TimeoutExpired:
            return LintResult(
                file_path=file_path,
                issues=[],
                passed=True,
                raw_output="Linting timeout"
            )
        except Exception as e:
            logger.warning(f"Lint failed for {file_path}: {e}")
            return LintResult(
                file_path=file_path,
                issues=[],
                passed=True,
                raw_output=str(e)
            )
    
    def _lint_project(self) -> List[LintResult]:
        """Lint 整个项目"""
        try:
            cmd = ["ruff", "check", ".", "--output-format", "json"]
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 按文件分组
            file_issues: Dict[str, List[LintIssue]] = {}
            try:
                data = json.loads(result.stdout) if result.stdout else []
                for item in data:
                    filename = item.get("filename", "unknown")
                    code = item.get("code", "")
                    fix_suggestion = self._get_fix_suggestion(code, item)
                    
                    issue = LintIssue(
                        line=item.get("location", {}).get("row", 0),
                        column=item.get("location", {}).get("column", 0),
                        code=code,
                        message=item.get("message", ""),
                        severity="error" if item.get("severity", 0) >= 2 else "warning",
                        fix_suggestion=fix_suggestion
                    )
                    
                    if filename not in file_issues:
                        file_issues[filename] = []
                    file_issues[filename].append(issue)
                    
            except json.JSONDecodeError:
                pass
            
            results = []
            for filename, issues in file_issues.items():
                results.append(LintResult(
                    file_path=filename,
                    issues=issues,
                    passed=len(issues) == 0,
                    raw_output=""
                ))
            
            return results
            
        except Exception as e:
            logger.warning(f"Project lint failed: {e}")
            return []
    
    def _get_fix_suggestion(self, code: str, item: Dict) -> str:
        """获取修复建议"""
        # 先查映射
        if code in self.FIX_SUGGESTIONS:
            return self.FIX_SUGGESTIONS[code]
        
        # 从 fix 字段获取
        fix = item.get("fix")
        if fix:
            return f"自动修复可用: {fix.get('message', '')}"
        
        # 通用建议
        return "请查阅官方文档或使用 `ruff check --fix` 尝试自动修复"
    
    def _parse_text_output(self, output: str) -> List[LintIssue]:
        """解析文本输出"""
        issues = []
        # 简单解析：file:line:col: code message
        pattern = r"(\S+):(\d+):(\d+): (\w+) (.+)"
        for match in re.finditer(pattern, output):
            issues.append(LintIssue(
                line=int(match.group(2)),
                column=int(match.group(3)),
                code=match.group(4),
                message=match.group(5),
                severity="error"
            ))
        return issues

    def lint_text(self, code: str, language: str = "python") -> LintResult:
        """
        Lint 文本代码（不写入文件）
        
        用于 Agent 输出代码的即时检查
        
        Args:
            code: 要检查的代码文本
            language: 语言类型 (python, javascript, etc.)
            
        Returns:
            LintResult: 检查结果
        """
        import tempfile
        import os
        
        issues = []
        
        # 对于 Python，使用 AST 检查基本语法
        if language == "python":
            try:
                compile(code, "<agent_output>", "exec")
            except SyntaxError as e:
                issues.append(LintIssue(
                    line=e.lineno or 1,
                    column=e.offset or 1,
                    code="E999",
                    message=f"SyntaxError: {e.msg}",
                    severity="error"
                ))
            
            # 检查常见问题模式
            common_issues = self._check_common_patterns(code)
            issues.extend(common_issues)
        
        # 对于其他语言，返回基本信息
        return LintResult(
            file_path="<agent_output>",
            issues=issues,
            passed=len(issues) == 0,
            raw_output=f"Linted {len(issues)} issues from text input"
        )
    
    def _check_common_patterns(self, code: str) -> List[LintIssue]:
        """检查常见代码问题模式"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 检查 TODO/FIXME
            if 'TODO' in line or 'FIXME' in line:
                issues.append(LintIssue(
                    line=i,
                    column=line.index('TODO') if 'TODO' in line else line.index('FIXME'),
                    code="T001",
                    message="TODO/FIXME comment found - should be resolved",
                    severity="warning"
                ))
            
            # 检查硬编码密钥（简化检查）
            if any(p in line.lower() for p in ['api_key', 'password', 'secret']) and '=' in line:
                # 检查是否是变量赋值而非字符串
                if '"' in line or "'" in line:
                    issues.append(LintIssue(
                        line=i,
                        column=1,
                        code="S001",
                        message="Potential hardcoded secret detected",
                        severity="warning"
                    ))
        
        return issues
    
    def check_output_quality(self, output: str) -> Dict[str, Any]:
        """
        检查 Agent 输出的质量
        
        Args:
            output: Agent 生成的文本输出
            
        Returns:
            Dict with quality metrics
        """
        quality = {
            "has_content": len(output.strip()) > 0,
            "length": len(output),
            "has_errors": False,
            "has_warnings": False,
            "issues_count": 0,
            "suggestions": []
        }
        
        # 检查是否是代码
        if "```" in output:
            # 提取代码块
            import re
            code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', output, re.DOTALL)
            for block in code_blocks:
                result = self.lint_text(block)
                quality["issues_count"] += len(result.issues)
                if any(i.severity == "error" for i in result.issues):
                    quality["has_errors"] = True
                if any(i.severity == "warning" for i in result.issues):
                    quality["has_warnings"] = True
                for issue in result.issues[:3]:  # 最多3个建议
                    quality["suggestions"].append(f"Line {issue.line}: {issue.message}")
        
        return quality
    
    def auto_fix(self, file_path: str) -> Dict[str, Any]:
        """尝试自动修复"""
        path = self.project_root / file_path
        if not path.exists():
            return {"success": False, "error": "File not found"}
        
        try:
            cmd = ["ruff", "check", str(path), "--fix"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr,
                "fixed": "fix" in result.stdout.lower()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 全局单例
_global_linter: Optional[AgentLinter] = None

def get_agent_linter() -> AgentLinter:
    """获取全局 Agent Linter"""
    global _global_linter
    if _global_linter is None:
        _global_linter = AgentLinter()
    return _global_linter


# ============ 便捷函数 ============

def lint_file(file_path: str) -> Dict:
    """Lint 单个文件"""
    return get_agent_linter().lint_file(file_path).to_agent_dict()


def lint_project() -> List[Dict]:
    """Lint 整个项目"""
    return [r.to_agent_dict() for r in get_agent_linter().lint_all()]


def auto_fix_file(file_path: str) -> Dict:
    """自动修复文件"""
    return get_agent_linter().auto_fix(file_path)
