#!/usr/bin/env python3
"""
开发工作流审核系统 (DevWorkflowAudit)

集成到开发流程的代码审核系统:
- 代码执行前审核（危险操作、正则规范检查）
- 危险操作检测（eval/exec、rm -rf、DROP TABLE 等）
- 代码规范检查（import *、裸 except 等正则规则）
- 可选 Linter 集成（pylint/pyright，发现项目中的 linter 错误）
- 审核结果自动学习

注意: audit_code() 仅做「执行前安全 + 简单规范」检查，不做静态分析。
项目中的 pylint/pyright 等 linter 错误需通过 run_linter_checks() 或 CI 中
执行 pylint src/ / pyright src/ 发现。

使用方式:
    from src.core.dev_workflow_audit import DevWorkflowAudit

    audit = DevWorkflowAudit()
    result = await audit.audit_code("print('hello')")
    # 发现项目中的 linter 错误:
    linter_result = audit.run_linter_checks(["src/"])
"""

import asyncio
import re
import uuid
import logging
import subprocess
import os
from typing import Dict, Any, Optional, List, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# pylint 输出行格式: file:line:column: message (message-id)
_PYLINT_LINE_RE = re.compile(
    r"^(.+?):(\d+):(\d+):\s*(.+?)\s*\(([^)]+)\)$",
    re.MULTILINE,
)


class AuditLevel(Enum):
    """审核级别"""
    NONE = "none"           # 不审核
    BASIC = "basic"         # 基础审核 (危险操作)
    STANDARD = "standard"   # 标准审核 (基础 + 规范)
    STRICT = "strict"       # 严格审核 (所有规则)


class RiskLevel(Enum):
    """风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CodeAuditResult:
    """代码审核结果"""
    audit_id: str
    passed: bool
    risk_level: RiskLevel
    issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    approved_code: Optional[str] = None
    sanitized_code: Optional[str] = None  # 消毒后的代码
    timestamp: datetime = field(default_factory=datetime.now)


class DangerousPattern:
    """危险模式"""
    
    # 模式定义: (正则, 风险等级, 描述, 修复建议)
    PATTERNS = [
        # 文件系统操作
        (r'rm\s+-rf\s+', RiskLevel.CRITICAL, "递归删除文件", "使用确认提示或只删除特定文件"),
        (r'shutil\.rmtree', RiskLevel.HIGH, "递归删除目录", "添加确认逻辑"),
        (r'os\.remove\(', RiskLevel.MEDIUM, "删除文件", "确认文件存在"),
        (r'os\.rmdir\(', RiskLevel.MEDIUM, "删除目录", "确认目录为空"),
        
        # 数据库操作
        (r'drop\s+table', RiskLevel.CRITICAL, "删除表", "使用DROP TABLE IF EXISTS并备份"),
        (r'delete\s+from\s+\w+\s*;?\s*$', RiskLevel.HIGH, "删除数据", "使用软删除或先SELECT确认"),
        (r'truncate\s+', RiskLevel.CRITICAL, "清空表", "使用DELETE替代"),
        (r'drop\s+database', RiskLevel.CRITICAL, "删除数据库", "禁止操作"),
        
        # 代码执行
        (r'eval\(', RiskLevel.CRITICAL, "eval执行", "使用ast.literal_eval或重新设计"),
        (r'exec\(', RiskLevel.CRITICAL, "exec执行", "使用安全的替代方案"),
        (r'compile\(', RiskLevel.HIGH, "动态编译", "验证输入来源"),
        
        # 系统命令
        (r'os\.system\(', RiskLevel.HIGH, "系统命令", "使用subprocess并限制命令"),
        (r'subprocess\.call\(', RiskLevel.MEDIUM, "子进程", "避免shell=True"),
        (r'subprocess\.run\(.*shell\s*=\s*True', RiskLevel.HIGH, "Shell执行", "使用shell=False"),
        
        # 网络操作
        (r'requests\.post\(.*auth\s*=', RiskLevel.MEDIUM, "HTTP认证", "验证凭证来源"),
        (r'urllib\.request\(', RiskLevel.LOW, "网络请求", "验证URL来源"),
        
        # 权限操作
        (r'chmod\s+777', RiskLevel.HIGH, "过度权限", "使用最小权限原则"),
        (r'chown\s+', RiskLevel.MEDIUM, "修改所有者", "确认操作必要"),
        
        # 环境操作
        (r'os\.environ\[', RiskLevel.MEDIUM, "环境变量", "验证变量名来源"),
        (r'sys\.exit\(', RiskLevel.LOW, "退出程序", "使用异常处理"),
    ]
    
    # 规范检查模式
    CODE_QUALITY_PATTERNS = [
        (r'from\s+\w+\s+import\s+\*', RiskLevel.MEDIUM, "避免import *", "明确列出导入"),
        (r'except:\s*$', RiskLevel.MEDIUM, "裸except", "指定异常类型"),
        (r'print\(', RiskLevel.LOW, "使用print", "使用logging"),
        (r'# TODO|# FIXME|# XXX', RiskLevel.LOW, "存在待办注释", "及时处理"),
        (r'assert\s+', RiskLevel.LOW, "生产环境断言", "使用条件检查"),
    ]


class DevWorkflowAudit:
    """开发工作流审核系统
    
    提供代码审核、质量检查、危险操作检测功能
    """
    
    def __init__(
        self,
        audit_level: AuditLevel = AuditLevel.STANDARD,
        chief_agent=None,
        auto_sanitize: bool = True
    ):
        """
        初始化审核系统
        
        Args:
            audit_level: 审核级别
            chief_agent: ChiefAgent实例 (用于深度审核)
            auto_sanitize: 是否自动消毒危险代码
        """
        self.audit_level = audit_level
        self.chief_agent = chief_agent
        self.auto_sanitize = auto_sanitize
        
        # 审核历史
        self.audit_history: List[CodeAuditResult] = []
        
        # 自定义规则
        self.custom_rules: List[Dict[str, Any]] = []
        
        # 统计
        self.stats = {
            "total_audits": 0,
            "passed": 0,
            "rejected": 0,
            "sanitized": 0
        }
        
        logger.info(f"DevWorkflowAudit initialized with level: {audit_level.value}")
    
    def add_custom_rule(
        self,
        name: str,
        pattern: str,
        risk_level: str,
        description: str,
        suggestion: str = ""
    ) -> None:
        """添加自定义审核规则"""
        self.custom_rules.append({
            "name": name,
            "pattern": pattern,
            "risk_level": RiskLevel(risk_level),
            "description": description,
            "suggestion": suggestion
        })
        logger.info(f"Added custom rule: {name}")
    
    async def audit_code(
        self,
        code: str,
        context: Optional[Dict[str, Any]] = None
    ) -> CodeAuditResult:
        """审核代码
        
        Args:
            code: 要审核的代码
            context: 上下文信息
            
        Returns:
            CodeAuditResult: 审核结果
        """
        context = context or {}
        audit_id = str(uuid.uuid4())[:8]
        
        issues = []
        suggestions = []
        risk_level = RiskLevel.SAFE
        sanitized_code = code
        
        # 1. 危险操作检测
        if self.audit_level != AuditLevel.NONE:
            dangerous_issues = self._check_dangerous_patterns(code)
            issues.extend(dangerous_issues)
            
            # 更新风险等级
            for issue in dangerous_issues:
                issue_risk = issue.get("risk_level", RiskLevel.LOW)
                if issue_risk == RiskLevel.CRITICAL:
                    risk_level = RiskLevel.CRITICAL
                    break
                elif issue_risk == RiskLevel.HIGH and risk_level != RiskLevel.CRITICAL:
                    risk_level = RiskLevel.HIGH
                elif issue_risk == RiskLevel.MEDIUM and risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
                    risk_level = RiskLevel.MEDIUM
        
        # 2. 代码质量检查
        if self.audit_level in [AuditLevel.STANDARD, AuditLevel.STRICT]:
            quality_issues = self._check_code_quality(code)
            issues.extend(quality_issues)
        
        # 3. 严格模式额外检查
        if self.audit_level == AuditLevel.STRICT:
            strict_issues = await self._strict_checks(code, context)
            issues.extend(strict_issues)
        
        # 4. 自定义规则检查
        if self.custom_rules:
            custom_issues = self._check_custom_rules(code)
            issues.extend(custom_issues)
        
        # 5. 消毒处理
        if self.auto_sanitize and issues:
            sanitized_code = self._sanitize_code(code, issues)
        
        # 6. 判断是否通过
        critical_or_high = any(
            i.get("risk_level") in [RiskLevel.CRITICAL, RiskLevel.HIGH] 
            for i in issues
        )
        passed = not critical_or_high
        
        # 7. 生成建议
        for issue in issues:
            if issue.get("suggestion"):
                suggestions.append(issue["suggestion"])
        
        # 创建结果
        result = CodeAuditResult(
            audit_id=audit_id,
            passed=passed,
            risk_level=risk_level,
            issues=issues,
            suggestions=suggestions[:5],  # 最多5条建议
            sanitized_code=sanitized_code if passed else None
        )
        
        # 记录历史
        self._record_result(result)
        
        # 更新统计
        self._update_stats(result)
        
        logger.info(
            f"Code audit result: {audit_id} - "
            f"{'PASSED' if passed else 'REJECTED'} ({risk_level.value})"
        )
        
        return result
    
    def _check_dangerous_patterns(self, code: str) -> List[Dict[str, Any]]:
        """检查危险模式"""
        issues = []
        
        for pattern, risk_level, description, suggestion in DangerousPattern.PATTERNS:
            matches = list(re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE))
            if matches:
                for match in matches:
                    issues.append({
                        "type": "dangerous",
                        "risk_level": risk_level,
                        "pattern": match.group(),
                        "line": code[:match.start()].count('\n') + 1,
                        "description": description,
                        "suggestion": suggestion
                    })
        
        return issues
    
    def _check_code_quality(self, code: str) -> List[Dict[str, Any]]:
        """检查代码质量"""
        issues = []
        
        for pattern, risk_level, description, suggestion in DangerousPattern.CODE_QUALITY_PATTERNS:
            matches = list(re.finditer(pattern, code, re.IGNORECASE))
            if matches:
                for match in matches:
                    issues.append({
                        "type": "quality",
                        "risk_level": risk_level,
                        "pattern": match.group()[:50],
                        "description": description,
                        "suggestion": suggestion
                    })
        
        return issues
    
    async def _strict_checks(
        self,
        code: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """严格检查 (使用LLM)"""
        issues = []
        
        # 如果有ChiefAgent，可以用LLM进行深度审核
        if self.chief_agent and hasattr(self.chief_agent, 'audit_agent'):
            try:
                llm_result = await self.chief_agent.audit_action(
                    source_agent="dev_workflow_audit",
                    target_agent="llm_reviewer",
                    action_type="code_review",
                    action_details={
                        "code": code,
                        "context": context,
                        "strict_mode": True
                    }
                )
                
                if llm_result and llm_result.decision.value == "rejected":
                    issues.append({
                        "type": "llm_review",
                        "risk_level": RiskLevel.HIGH,
                        "description": "LLM审核拒绝",
                        "suggestion": llm_result.reasons[0] if llm_result.reasons else "请检查代码"
                    })
            except Exception as e:
                logger.warning(f"LLM strict check failed: {e}")
        
        return issues
    
    def _check_custom_rules(self, code: str) -> List[Dict[str, Any]]:
        """检查自定义规则"""
        issues = []
        
        for rule in self.custom_rules:
            pattern = rule["pattern"]
            matches = list(re.finditer(pattern, code, re.IGNORECASE))
            if matches:
                for match in matches:
                    issues.append({
                        "type": "custom",
                        "risk_level": rule["risk_level"],
                        "rule_name": rule["name"],
                        "description": rule["description"],
                        "suggestion": rule.get("suggestion", "")
                    })
        
        return issues
    
    def _sanitize_code(self, code: str, issues: List[Dict[str, Any]]) -> str:
        """消毒代码 (简单实现)"""
        sanitized = code
        
        # 移除危险操作
        dangerous_patterns = [
            (r'eval\(', '# eval removed - use safe alternative'),
            (r'exec\(', '# exec removed'),
            (r'os\.system\(', '# os.system removed'),
        ]
        
        for pattern, replacement in dangerous_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _record_result(self, result: CodeAuditResult) -> None:
        """记录审核结果"""
        self.audit_history.append(result)
        
        # 保留最近1000条
        if len(self.audit_history) > 1000:
            self.audit_history = self.audit_history[-1000:]
    
    def _update_stats(self, result: CodeAuditResult) -> None:
        """更新统计"""
        self.stats["total_audits"] += 1
        if result.passed:
            self.stats["passed"] += 1
        else:
            self.stats["rejected"] += 1

        if result.sanitized_code and len(self.audit_history) >= 2:
            prev = self.audit_history[-2]
            prev_code = getattr(prev, "approved_code", None) or prev.sanitized_code
            if result.sanitized_code != prev_code:
                self.stats["sanitized"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取审核统计"""
        total = self.stats["total_audits"]
        return {
            **self.stats,
            "pass_rate": self.stats["passed"] / max(total, 1),
            "reject_rate": self.stats["rejected"] / max(total, 1)
        }
    
    def get_recent_issues(self, n: int = 10) -> List[Dict[str, Any]]:
        """获取最近的问题"""
        issues = []
        for result in self.audit_history[-n:]:
            issues.extend(result.issues)
        return issues

    def run_linter_checks(
        self,
        paths: List[str],
        linters: Optional[List[str]] = None,
        pylint_args: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """对指定路径运行 linter（如 pylint），发现项目中的静态检查错误。

        与 audit_code() 的区别:
        - audit_code(): 对「即将执行的代码片段」做危险模式+简单规范检查（正则）
        - run_linter_checks(): 对「源码文件/目录」运行 pylint/pyright，发现未定义变量、
          类型错误、风格问题等，即通常所说的 linter 错误。

        Args:
            paths: 文件或目录路径列表，如 ["src/", "tests/test_foo.py"]
            linters: 要运行的 linter，默认 ["pylint"]
            pylint_args: 传给 pylint 的额外参数，如 ["--disable=C0114"]

        Returns:
            {
                "issues": [{"file", "line", "column", "message", "symbol", "severity"}, ...],
                "summary": {"total": int, "by_file": {...}, "by_severity": {...}},
                "raw_output": str,
                "success": bool  # 进程是否成功执行（pylint 有发现时退出码非 0）
            }
        """
        linters = linters or ["pylint"]
        pylint_args = pylint_args or []
        all_issues: List[Dict[str, Any]] = []
        raw_outputs: List[str] = []

        for linter_name in linters:
            if linter_name == "pylint":
                out, issues, success = self._run_pylint(paths, pylint_args)
                raw_outputs.append(out)
                all_issues.extend(issues)
            elif linter_name == "pyright":
                out, issues, success = self._run_pyright(paths)
                raw_outputs.append(out)
                all_issues.extend(issues)
            else:
                logger.warning(f"Unknown linter: {linter_name}")

        by_file: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for i in all_issues:
            f = i.get("file", "")
            by_file[f] = by_file.get(f, 0) + 1
            s = i.get("severity", "unknown")
            by_severity[s] = by_severity.get(s, 0) + 1

        return {
            "issues": all_issues,
            "summary": {
                "total": len(all_issues),
                "by_file": by_file,
                "by_severity": by_severity,
            },
            "raw_output": "\n".join(raw_outputs),
            "success": len(all_issues) == 0,
        }

    def _run_pylint(
        self,
        paths: List[str],
        extra_args: List[str],
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """运行 pylint，解析输出为 issues。"""
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            return "", [], True

        cmd = [
            "pylint",
            "--output-format=text",
            "--reports=no",
            *extra_args,
            *paths,
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.getcwd(),
            )
        except FileNotFoundError:
            logger.warning("pylint 未安装或不在 PATH 中，跳过: pip install pylint")
            return "pylint not found", [], True
        except subprocess.TimeoutExpired:
            logger.warning("pylint 执行超时")
            return "timeout", [], False

        out = (result.stdout or "") + (result.stderr or "")
        issues = []
        for match in _PYLINT_LINE_RE.finditer(out):
            path_str, line_str, col_str, message, symbol = match.groups()
            issues.append({
                "type": "linter",
                "linter": "pylint",
                "file": path_str.strip(),
                "line": int(line_str),
                "column": int(col_str),
                "message": message.strip(),
                "symbol": symbol.strip(),
                "severity": "error" if symbol.startswith("E") else "warning",
            })
        return out, issues, result.returncode == 0

    def _run_pyright(
        self,
        paths: List[str],
    ) -> Tuple[str, List[Dict[str, Any]], bool]:
        """运行 pyright，解析 JSON 输出为 issues。"""
        paths = [p for p in paths if os.path.exists(p)]
        if not paths:
            return "", [], True

        cmd = ["pyright", "--outputjson", *paths]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.getcwd(),
            )
        except FileNotFoundError:
            logger.warning("pyright 未安装或不在 PATH 中，跳过: pip install pyright")
            return "pyright not found", [], True
        except subprocess.TimeoutExpired:
            logger.warning("pyright 执行超时")
            return "timeout", [], False

        out = (result.stdout or "") + (result.stderr or "")
        issues = []
        try:
            import json
            data = json.loads(result.stdout or "{}")
            for diag in data.get("generalDiagnostics", []):
                if isinstance(diag, dict):
                    r = diag.get("range") or {}
                    start = r.get("start") or {}
                    issues.append({
                        "type": "linter",
                        "linter": "pyright",
                        "file": diag.get("file", ""),
                        "line": start.get("line", 0) + 1,
                        "column": start.get("character", 0),
                        "message": diag.get("message", ""),
                        "symbol": diag.get("rule", ""),
                        "severity": diag.get("severity", "error"),
                    })
        except (json.JSONDecodeError, KeyError, TypeError):
            for line in out.splitlines():
                if "error" in line.lower() or "warning" in line.lower():
                    issues.append({
                        "type": "linter",
                        "linter": "pyright",
                        "file": "",
                        "line": 0,
                        "column": 0,
                        "message": line.strip(),
                        "symbol": "",
                        "severity": "error",
                    })
        return out, issues, result.returncode == 0

    async def learn_from_rejection(
        self,
        rejected_code: str,
        reason: str
    ) -> None:
        """从拒绝中学习 (集成自进化)"""
        if self.chief_agent and hasattr(self.chief_agent, '_self_evolving_mixin'):
            await self.chief_agent.force_reflect(
                task=f"代码审核拒绝: {reason}",
                result={"code": rejected_code[:200], "reason": reason},
                context={"source": "dev_workflow_audit"}
            )
        
        # 添加为自定义规则
        pattern = rejected_code[:50].replace("*", ".*")
        self.add_custom_rule(
            name=f"learned_{len(self.custom_rules)}",
            pattern=pattern,
            risk_level="high",
            description=f"从失败中学习: {reason}",
            suggestion="请按照审核建议修改代码"
        )


# ==================== 便捷函数 ====================

_default_audit: Optional[DevWorkflowAudit] = None


def get_dev_audit(
    audit_level: AuditLevel = AuditLevel.STANDARD,
    chief_agent=None
) -> DevWorkflowAudit:
    """获取默认的审核系统实例"""
    global _default_audit
    
    if _default_audit is None:
        _default_audit = DevWorkflowAudit(audit_level, chief_agent)
    
    return _default_audit


async def quick_audit(code: str) -> CodeAuditResult:
    """快速审核 (使用默认实例)"""
    audit = get_dev_audit()
    return await audit.audit_code(code)


# ==================== 集成到ChiefAgent ====================

async def audit_with_chief(
    chief_agent,
    code: str,
    action_type: str = "code_execution"
) -> CodeAuditResult:
    """使用ChiefAgent的审核系统进行审核
    
    Args:
        chief_agent: ChiefAgent实例
        code: 要审核的代码
        action_type: 操作类型
        
    Returns:
        CodeAuditResult: 审核结果
    """
    audit = DevWorkflowAudit(
        audit_level=AuditLevel.STRICT,
        chief_agent=chief_agent
    )
    
    return await audit.audit_code(code, {"action_type": action_type})
