"""
架构依赖方向测试 - Dependency Guardrails
==========================================

防止 Agent 在编写代码时破坏架构分层。

核心功能：
1. 定义架构依赖规则 - 哪些模块可以依赖哪些模块
2. 检测违规依赖 - 分析 import 语句检测跨层依赖
3. 拦截并提供修复建议 - 当 Agent 违反规则时立即拦截

原理：
- 当 Agent 尝试从 Core 层调用 UI 层时，直接阻断
- 提供清晰的架构规则说明，帮助 Agent 理解为什么这是违规的
"""

import re
import os
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class DependencyRule:
    """依赖规则"""
    from_module: str      # 来源模块 (如 "src.ui")
    to_module: str        # 目标模块 (如 "src.core")
    allowed: bool = True   # 是否允许
    reason: str = ""      # 规则说明
    severity: str = "error"  # error, warning, info


@dataclass
class DependencyViolation:
    """依赖违规"""
    file_path: str
    line_number: int
    from_module: str
    to_module: str
    import_statement: str
    rule: DependencyRule
    fix_suggestion: str


@dataclass
class DependencyCheckResult:
    """依赖检查结果"""
    passed: bool
    violations: List[DependencyViolation]
    checked_files: int
    total_imports: int
    
    def to_agent_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "violation_count": len(self.violations),
            "violations": [
                {
                    "file": v.file_path,
                    "line": v.line_number,
                    "from": v.from_module,
                    "to": v.to_module,
                    "import": v.import_statement,
                    "fix": v.fix_suggestion
                }
                for v in self.violations
            ],
            "summary": f"Checked {self.checked_files} files, {self.total_imports} imports, {len(self.violations)} violations"
        }


class DependencyGuard:
    """
    架构依赖守卫
    
    强制执行架构分层规则，防止跨层依赖。
    """
    
    # 默认架构分层规则
    DEFAULT_RULES = [
        # UI 层不能依赖外部世界
        DependencyRule("src/ui", "src/external", False, "UI层禁止直接访问外部服务", "error"),
        
        # Service 层可以调用任何层（除了 UI 层）
        DependencyRule("src/services", "src/ui", False, "Service层禁止调用UI层", "error"),
        DependencyRule("src/services", "src/gateway", False, "Service层禁止调用Gateway层", "error"),
        
        # Core 层是最底层，禁止调用上层
        DependencyRule("src/core", "src/services", False, "Core层禁止调用Service层", "error"),
        DependencyRule("src/core", "src/agents", False, "Core层禁止调用Agent层", "error"),
        DependencyRule("src/core", "src/ui", False, "Core层禁止调用UI层", "error"),
        DependencyRule("src/core", "src/gateway", False, "Core层禁止调用Gateway层", "error"),
        
        # Agent 层可以调用 Core 和 Services
        DependencyRule("src/agents", "src/ui", False, "Agent层禁止调用UI层", "error"),
        DependencyRule("src/agents", "src/gateway", False, "Agent层禁止调用Gateway层", "error"),
        
        # Gateway 层只能依赖 Core
        DependencyRule("src/gateway", "src/services", False, "Gateway层禁止调用Service层", "error"),
        DependencyRule("src/gateway", "src/agents", False, "Gateway层禁止调用Agent层", "error"),
        DependencyRule("src/gateway", "src/ui", False, "Gateway层禁止调用UI层", "error"),
        
        # API 层可以调用所有业务层
        DependencyRule("src/api", "src/ui", False, "API层禁止调用UI层", "error"),
    ]
    
    def __init__(
        self,
        project_root: str = ".",
        rules: List[DependencyRule] = None,
        auto_discover: bool = True
    ):
        self.project_root = Path(project_root)
        self.rules = rules or self.DEFAULT_RULES.copy()
        
        # 构建规则索引
        self._rule_index: Dict[Tuple[str, str], DependencyRule] = {}
        for rule in self.rules:
            key = (rule.from_module, rule.to_module)
            self._rule_index[key] = rule
        
        # 自动发现项目模块
        self._discovered_modules: Set[str] = set()
        if auto_discover:
            self._discover_modules()
    
    def _discover_modules(self):
        """自动发现项目中的模块"""
        src_dir = self.project_root / "src"
        if not src_dir.exists():
            return
        
        for item in src_dir.rglob("*"):
            if item.is_dir() and not item.name.startswith("_"):
                rel_path = item.relative_to(src_dir.parent)
                module_name = str(rel_path).replace(os.sep, ".")
                self._discovered_modules.add(module_name)
    
    def _extract_imports(self, file_path: Path) -> List[Tuple[int, str]]:
        """从文件中提取所有 import 语句"""
        imports = []
        
        if not file_path.exists():
            return imports
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # 跳过注释
                    if line.startswith('#'):
                        continue
                    
                    # 检测 import 语句
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append((line_num, line))
        
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
        
        return imports
    
    def _parse_module_from_import(self, import_stmt: str) -> Optional[str]:
        """从 import 语句解析模块名"""
        # from xxx import yyy
        match = re.match(r'from\s+([\w.]+)', import_stmt)
        if match:
            return match.group(1)
        
        # import xxx
        match = re.match(r'import\s+([\w.]+)', import_stmt)
        if match:
            return match.group(1)
        
        return None
    
    def _matches_rule(
        self,
        from_module: str,
        to_module: str
    ) -> Optional[DependencyRule]:
        """检查是否匹配规则"""
        # 精确匹配
        key = (from_module, to_module)
        if key in self._rule_index:
            return self._rule_index[key]
        
        # 前缀匹配
        for rule_key, rule in self._rule_index.items():
            if to_module.startswith(rule_key[1]) and not rule.allowed:
                return rule
        
        return None
    
    def check_file(self, file_path: str) -> DependencyCheckResult:
        """
        检查单个文件的依赖违规
        
        Args:
            file_path: 文件路径 (如 "src/agents/smart_conversation_agent.py")
            
        Returns:
            DependencyCheckResult: 检查结果
        """
        path = self.project_root / file_path
        
        # 确定源模块
        src_dir = self.project_root / "src"
        try:
            rel_path = path.relative_to(src_dir.parent)
        except ValueError:
            rel_path = path
        
        parts = rel_path.parts
        if len(parts) >= 2 and parts[0] == "src":
            from_module = ".".join(parts[:2])  # 如 "src.agents"
        else:
            from_module = parts[0] if parts else ""
        
        violations = []
        imports = self._extract_imports(path)
        
        for line_num, import_stmt in imports:
            to_module = self._parse_module_from_import(import_stmt)
            
            if not to_module:
                continue
            
            # 跳过内置模块和外部依赖
            if not to_module.startswith("src."):
                continue
            
            # 检查规则
            rule = self._matches_rule(from_module, to_module)
            if rule and not rule.allowed:
                violation = DependencyViolation(
                    file_path=file_path,
                    line_number=line_num,
                    from_module=from_module,
                    to_module=to_module,
                    import_statement=import_stmt,
                    rule=rule,
                    fix_suggestion=self._generate_fix(rule, import_stmt)
                )
                violations.append(violation)
        
        return DependencyCheckResult(
            passed=len(violations) == 0,
            violations=violations,
            checked_files=1,
            total_imports=len(imports)
        )
    
    def check_all(self, files: List[str] = None) -> DependencyCheckResult:
        """
        检查多个文件或整个项目
        
        Args:
            files: 文件列表，如果为空则检查整个 src 目录
        """
        if not files:
            src_dir = self.project_root / "src"
            if src_dir.exists():
                files = [str(p.relative_to(self.project_root)) 
                        for p in src_dir.rglob("*.py")
                        if not p.name.startswith("_")]
            else:
                files = []
        
        all_violations = []
        total_imports = 0
        
        for file_path in files:
            result = self.check_file(file_path)
            all_violations.extend(result.violations)
            total_imports += result.total_imports
        
        return DependencyCheckResult(
            passed=len(all_violations) == 0,
            violations=all_violations,
            checked_files=len(files),
            total_imports=total_imports
        )
    
    def _generate_fix(self, rule: DependencyRule, import_stmt: str) -> str:
        """生成修复建议"""
        return (
            f"🚫 架构违规: {rule.reason}\n\n"
            f"   当前依赖: {rule.from_module} -> {rule.to_module}\n\n"
            f"   解决方案:\n"
            f"   1. 如果 {rule.to_module} 需要被 {rule.from_module} 使用，\n"
            f"      考虑在 {rule.from_module} 中定义接口，让 {rule.to_module} 实现\n"
            f"   2. 检查是否可以通过中间层解耦\n"
            f"   3. 如果确实需要调用，考虑重构到共同的上一层\n\n"
            f"   原始导入: {import_stmt}"
        )
    
    def get_architecture_rules(self) -> List[Dict[str, Any]]:
        """获取架构规则说明"""
        return [
            {
                "from": r.from_module,
                "to": r.to_module,
                "allowed": r.allowed,
                "reason": r.reason,
                "severity": r.severity
            }
            for r in self.rules
        ]
    
    def add_rule(
        self,
        from_module: str,
        to_module: str,
        allowed: bool = False,
        reason: str = "",
        severity: str = "error"
    ):
        """添加自定义规则"""
        rule = DependencyRule(
            from_module=from_module,
            to_module=to_module,
            allowed=allowed,
            reason=reason,
            severity=severity
        )
        self.rules.append(rule)
        self._rule_index[(from_module, to_module)] = rule


# 单例
_dependency_guard: Optional[DependencyGuard] = None

def get_dependency_guard(project_root: str = ".") -> DependencyGuard:
    """获取依赖守卫单例"""
    global _dependency_guard
    if _dependency_guard is None:
        _dependency_guard = DependencyGuard(project_root)
    return _dependency_guard
