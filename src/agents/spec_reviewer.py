#!/usr/bin/env python3
"""
Spec Reviewer - 规范合规性审查子Agent

借鉴 Superpowers subagent-driven-development skill 的 spec-reviewer:

核心职责:
1. 检查实现是否符合设计规范
2. 验证功能需求是否满足
3. 检查接口是否符合预期
4. 报告问题并按严重程度分级

审查结果:
- PASS: 完全符合规范
- NEEDS_WORK: 有问题需要修复
- FAIL: 严重问题，阻塞

严重程度分级:
- CRITICAL: 阻塞性问题，必须修复
- IMPORTANT: 重要问题，应该修复
- SUGGESTION: 建议，可选
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"   # 阻塞，必须修复
    IMPORTANT = "important" # 重要，应该修复
    SUGGESTION = "suggestion"  # 建议，可选


class IssueCategory(Enum):
    """问题类别"""
    SPEC = "spec"              # 规范合规
    FUNCTIONALITY = "functionality"  # 功能实现
    INTERFACE = "interface"    # 接口定义
    DATA = "data"              # 数据处理
    ERROR = "error"            # 错误处理
    SECURITY = "security"       # 安全性
    STYLE = "style"            # 代码风格


@dataclass
class SpecIssue:
    """规范问题"""
    severity: IssueSeverity
    category: IssueCategory
    message: str
    location: str = ""  # 文件:行号
    suggestion: str = ""
    spec_reference: str = ""  # 对应规范中的哪部分
    
    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
            "spec_reference": self.spec_reference,
        }


@dataclass
class SpecReviewResult:
    """规范审查结果"""
    status: str  # pass, needs_work, fail
    iteration: int
    issues: List[SpecIssue] = field(default_factory=list)
    summary: str = ""
    reviewed_at: str = ""
    
    def __post_init__(self):
        if not self.reviewed_at:
            self.reviewed_at = datetime.now().isoformat()
    
    def add_issue(
        self, 
        severity: IssueSeverity, 
        category: IssueCategory,
        message: str,
        location: str = "",
        suggestion: str = "",
        spec_reference: str = ""
    ):
        """添加问题"""
        self.issues.append(SpecIssue(
            severity=severity,
            category=category,
            message=message,
            location=location,
            suggestion=suggestion,
            spec_reference=spec_reference,
        ))
    
    def has_critical(self) -> bool:
        """是否有 CRITICAL 问题"""
        return any(i.severity == IssueSeverity.CRITICAL for i in self.issues)
    
    def has_important(self) -> bool:
        """是否有 IMPORTANT 问题"""
        return any(i.severity == IssueSeverity.IMPORTANT for i in self.issues)
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[SpecIssue]:
        """按严重程度筛选"""
        return [i for i in self.issues if i.severity == severity]
    
    def to_dict(self) -> Dict:
        return {
            "status": self.status,
            "iteration": self.iteration,
            "issues": [i.to_dict() for i in self.issues],
            "summary": self.summary,
            "reviewed_at": self.reviewed_at,
            "critical_count": len(self.get_issues_by_severity(IssueSeverity.CRITICAL)),
            "important_count": len(self.get_issues_by_severity(IssueSeverity.IMPORTANT)),
            "suggestion_count": len(self.get_issues_by_severity(IssueSeverity.SUGGESTION)),
        }


class DesignSpec:
    """设计规范 (从 hard_gate 导入或本地定义)"""
    def __init__(self, data: Dict):
        self.title = data.get('title', '')
        self.description = data.get('description', '')
        self.components = data.get('components', [])
        self.file_changes = data.get('file_changes', [])
        self.approved = data.get('approved', False)
        self.spec_file_path = data.get('spec_file_path', '')


class SpecReviewer:
    """
    规范合规性审查器
    
    使用方式:
    
    reviewer = SpecReviewer()
    
    # 设置设计规范
    reviewer.set_spec(design_spec)
    
    # 审查实现
    result = reviewer.review_implementation(
        file_path="src/auth/service.py",
        code_content="...",
    )
    
    if result.has_critical():
        print("CRITICAL 问题阻止合并!")
    """
    
    def __init__(self):
        self.spec: Optional[DesignSpec] = None
        self.iteration = 0
        logger.info("SpecReviewer 初始化")
    
    def set_spec(self, spec: DesignSpec):
        """设置设计规范"""
        self.spec = spec
        self.iteration = 0
        logger.info(f"SpecReviewer: 设置规范 '{spec.title}'")
    
    def set_spec_from_dict(self, spec_dict: Dict):
        """从字典设置设计规范"""
        self.spec = DesignSpec(spec_dict)
        self.iteration = 0
    
    def review_implementation(
        self, 
        file_path: str,
        code_content: str,
        context: Optional[Dict] = None
    ) -> SpecReviewResult:
        """
        审查实现是否符合规范
        
        Args:
            file_path: 文件路径
            code_content: 代码内容
            context: 额外上下文
            
        Returns:
            SpecReviewResult 审查结果
        """
        self.iteration += 1
        result = SpecReviewResult(
            status="pending",
            iteration=self.iteration,
        )
        
        if not self.spec:
            result.status = "needs_work"
            result.add_issue(
                IssueSeverity.CRITICAL,
                IssueCategory.SPEC,
                "没有设置设计规范",
                suggestion="先调用 set_spec() 设置规范"
            )
            return result
        
        # 1. 检查文件是否在设计范围内
        self._check_file_in_scope(file_path, result)
        
        # 2. 检查功能实现
        self._check_functionality(file_path, code_content, result)
        
        # 3. 检查接口定义
        self._check_interfaces(file_path, code_content, result)
        
        # 4. 检查错误处理
        self._check_error_handling(file_path, code_content, result)
        
        # 5. 生成总结
        self._generate_summary(result)
        
        return result
    
    def _check_file_in_scope(self, file_path: str, result: SpecReviewResult):
        """检查文件是否在设计范围内"""
        if not self.spec.file_changes:
            return
        
        # 检查文件是否匹配
        in_scope = False
        for designed_file in self.spec.file_changes:
            if designed_file in file_path or file_path.endswith(designed_file):
                in_scope = True
                break
        
        if not in_scope:
            result.add_issue(
                IssueSeverity.CRITICAL,
                IssueCategory.SPEC,
                f"文件 '{file_path}' 不在设计范围内",
                location=file_path,
                suggestion=f"设计范围内的文件: {', '.join(self.spec.file_changes)}",
                spec_reference="file_changes"
            )
    
    def _check_functionality(
        self, 
        file_path: str, 
        code: str, 
        result: SpecReviewResult
    ):
        """检查功能实现"""
        # 检查是否实现了设计的组件
        for component in self.spec.components:
            if component.lower() in code.lower():
                # 找到组件实现
                logger.debug(f"找到组件实现: {component}")
        
        # 检查是否有 TODO/FIXME (可能表示未完成的功能)
        todo_matches = re.findall(r'(TODO|FIXME|HACK):?\s*(.+)', code, re.IGNORECASE)
        for match in todo_matches:
            result.add_issue(
                IssueSeverity.IMPORTANT,
                IssueCategory.FUNCTIONALITY,
                f"未完成的任务: {match[1]}",
                location=f"{file_path}:TODO",
                suggestion="完成此任务或从规范中移除",
            )
        
        # 检查是否有 placeholder (占位符)
        if 'pass' in code and 'def ' in code:
            # 检查是否有空函数
            empty_funcs = re.findall(r'def (\w+)\([^)]*\):\s*pass', code)
            if empty_funcs:
                for func in empty_funcs:
                    result.add_issue(
                        IssueSeverity.CRITICAL,
                        IssueCategory.FUNCTIONALITY,
                        f"空函数未实现: {func}()",
                        location=f"{file_path}:{func}",
                        suggestion=f"实现 {func}() 函数或移除",
                    )
    
    def _check_interfaces(
        self, 
        file_path: str, 
        code: str, 
        result: SpecReviewResult
    ):
        """检查接口定义"""
        # 检查函数定义
        functions = re.findall(r'def (\w+)\([^)]*\)', code)
        
        # 检查是否有类型注解
        typed_functions = [f for f in functions if ': ' in code.split(f'def {f}')[1].split('\n')[0]]
        
        if functions and not typed_functions:
            result.add_issue(
                IssueSeverity.SUGGESTION,
                IssueCategory.INTERFACE,
                "函数缺少类型注解",
                suggestion="添加类型注解以提高代码可读性",
            )
        
        # 检查返回值
        for func in functions:
            func_match = re.search(rf'def {func}\([^)]*\)(?:-> ([^:]+))?:', code)
            if func_match:
                return_type = func_match.group(1).strip() if func_match.group(1) else None
                if not return_type:
                    result.add_issue(
                        IssueSeverity.SUGGESTION,
                        IssueCategory.INTERFACE,
                        f"函数 {func}() 缺少返回类型注解",
                        suggestion=f"添加返回类型注解: def {func}(...) -> ReturnType:",
                    )
    
    def _check_error_handling(
        self, 
        file_path: str, 
        code: str, 
        result: SpecReviewResult
    ):
        """检查错误处理"""
        # 检查是否有裸露的 except
        bare_except = re.findall(r'except\s*:', code)
        if bare_except:
            result.add_issue(
                IssueSeverity.IMPORTANT,
                IssueCategory.ERROR,
                "使用裸露的 except 子句",
                suggestion="使用具体的异常类型: except ValueError:",
            )
        
        # 检查是否有 raise
        raises = re.findall(r'raise\s+(\w+Error)', code)
        
        # 检查是否缺少 try-except
        if 'try:' not in code and 'except' not in code:
            # 检查是否有潜在需要错误处理的地方
            if any(keyword in code for keyword in ['request', 'fetch', 'load', 'parse']):
                result.add_issue(
                    IssueSeverity.SUGGESTION,
                    IssueCategory.ERROR,
                    "可能缺少错误处理",
                    suggestion="考虑添加 try-except 处理可能的异常",
                )
    
    def _generate_summary(self, result: SpecReviewResult):
        """生成审查总结"""
        critical = result.get_issues_by_severity(IssueSeverity.CRITICAL)
        important = result.get_issues_by_severity(IssueSeverity.IMPORTANT)
        suggestion = result.get_issues_by_severity(IssueSeverity.SUGGESTION)
        
        if critical:
            result.status = "fail"
            result.summary = f"发现 {len(critical)} 个 CRITICAL 问题，必须修复才能继续"
        elif important:
            result.status = "needs_work"
            result.summary = f"发现 {len(important)} 个 IMPORTANT 问题和 {len(suggestion)} 个建议"
        else:
            result.status = "pass"
            result.summary = "规范合规性审查通过"
    
    def review_files_batch(
        self,
        files: Dict[str, str],
        context: Optional[Dict] = None
    ) -> Dict[str, SpecReviewResult]:
        """
        批量审查多个文件
        
        Args:
            files: {文件路径: 代码内容} 字典
            
        Returns:
            {文件路径: 审查结果} 字典
        """
        results = {}
        for file_path, code in files.items():
            results[file_path] = self.review_implementation(file_path, code, context)
        return results
    
    def get_blocking_issues(self, results: Dict[str, SpecReviewResult]) -> List[SpecIssue]:
        """
        获取所有阻塞性问题
        
        Returns:
            所有 CRITICAL 问题的列表
        """
        blocking = []
        for result in results.values():
            blocking.extend(result.get_issues_by_severity(IssueSeverity.CRITICAL))
        return blocking


def create_spec_review_prompt(
    spec: Dict,
    file_path: str,
    code_content: str,
) -> str:
    """
    创建规范审查的 prompt 模板
    
    用于手动审查或调用其他 Agent 审查
    """
    spec_obj = DesignSpec(spec)
    
    prompt = f"""
# 规范合规性审查

## 设计规范
标题: {spec_obj.title}
描述: {spec_obj.description}

涉及组件:
{chr(10).join(f'- {c}' for c in spec_obj.components)}

涉及文件:
{chr(10).join(f'- {f}' for f in spec_obj.file_changes)}

## 待审查代码
文件: {file_path}

```{code_content[:2000]}```

## 审查要求

请检查以下方面:

### 1. 规范合规性 (CRITICAL)
- [ ] 文件是否在设计范围内
- [ ] 实现的组件是否与设计一致

### 2. 功能实现 (IMPORTANT)
- [ ] 所有设计的组件是否已实现
- [ ] 是否有未完成的 TODO/FIXME

### 3. 接口定义 (IMPORTANT)
- [ ] 函数签名是否符合预期
- [ ] 是否有类型注解

### 4. 错误处理 (SUGGESTION)
- [ ] 是否有适当的错误处理
- [ ] 异常是否具体

## 输出格式

请按以下格式输出审查结果:

```
## 审查结果: PASS / NEEDS_WORK / FAIL

### CRITICAL 问题 (阻塞)
- [文件:行号] 问题描述
  建议: 修复方法

### IMPORTANT 问题 (重要)
- [文件:行号] 问题描述
  建议: 修复方法

### 建议
- 问题描述
```
"""
    return prompt


__all__ = [
    'SpecReviewer',
    'SpecReviewResult', 
    'SpecIssue',
    'IssueSeverity',
    'IssueCategory',
    'DesignSpec',
    'create_spec_review_prompt',
]


if __name__ == '__main__':
    # 演示用法
    print("=== SpecReviewer 演示 ===\n")
    
    # 创建设计规范
    spec = DesignSpec({
        'title': '用户认证',
        'description': '实现用户登录功能',
        'components': ['认证服务', '用户模型'],
        'file_changes': ['src/auth/service.py', 'src/auth/models.py'],
    })
    
    # 创建审查器
    reviewer = SpecReviewer()
    reviewer.set_spec(spec)
    
    # 待审查代码
    test_code = '''
from typing import Optional

def authenticate(username: str, password: str):
    """用户认证"""
    # TODO: 实现认证逻辑
    pass

def get_user(user_id: int):
    """获取用户"""
    return {"id": user_id, "name": "test"}
'''
    
    # 审查
    result = reviewer.review_implementation(
        file_path="src/auth/service.py",
        code_content=test_code,
    )
    
    # 输出结果
    print(f"审查状态: {result.status}")
    print(f"总结: {result.summary}\n")
    
    if result.issues:
        print("问题列表:")
        for issue in result.issues:
            emoji = "🔴" if issue.severity == IssueSeverity.CRITICAL else "🟡" if issue.severity == IssueSeverity.IMPORTANT else "🟢"
            print(f"  {emoji} [{issue.severity.value}] {issue.message}")
            if issue.suggestion:
                print(f"      建议: {issue.suggestion}")
    
    print("\n=== SpecReviewer 演示完成 ===")
