#!/usr/bin/env python3
"""
SubagentDispatcher - 精确上下文构造器

基于 Superpowers subagent-driven-development 的精确上下文传递:
- 根据任务类型构造精确的提示词
- 只包含相关的代码片段和模式
- 提供必要的约束和技能描述

Subagent Types:
1. CODER: 实现-focused, TDD-aware
2. REVIEWER: Critical-blocking aware
3. RESEARCHER: 知识检索
4. PLANNER: 任务分解 with TDD steps
5. TESTER: 测试覆盖 focus

Usage:
    from src.agents.subagent_dispatcher import SubagentDispatcher
    
    dispatcher = SubagentDispatcher()
    
    # 构造精确上下文
    bundle = dispatcher.dispatch(
        task="实现用户认证模块",
        subagent_type=SubagentType.CODER
    )
    
    print(bundle.prompt)
    print(f"Relevant files: {bundle.relevant_files}")
"""

import os
import re
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from enum import Enum

logger = logging.getLogger(__name__)


class SubagentType(Enum):
    """子代理类型"""
    CODER = "coder"            # 代码实现
    REVIEWER = "reviewer"       # 代码审查
    RESEARCHER = "researcher"   # 知识检索
    PLANNER = "planner"         # 任务规划
    TESTER = "tester"           # 测试编写


@dataclass
class PromptBundle:
    """提示词包"""
    subagent_type: str
    task: str
    prompt: str
    relevant_files: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "subagent_type": self.subagent_type,
            "task": self.task,
            "prompt": self.prompt,
            "relevant_files": self.relevant_files,
            "constraints": self.constraints,
            "patterns": self.patterns,
            "skills": self.skills,
            "metadata": self.metadata
        }


@dataclass
class ContextReference:
    """上下文引用"""
    file_path: str
    content: str
    line_start: int = 1
    line_end: int = -1
    relevance: float = 1.0  # 0.0 - 1.0


class SubagentDispatcher:
    """
    子代理调度器
    
    功能:
    - 根据任务类型选择合适的提示词模板
    - 构造精确的上下文 (只包含相关代码)
    - 提供必要的约束和技能描述
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        
        # 提示词模板
        self._templates = {
            SubagentType.CODER: self._coder_template,
            SubagentType.REVIEWER: self._reviewer_template,
            SubagentType.RESEARCHER: self._researcher_template,
            SubagentType.PLANNER: self._planner_template,
            SubagentType.TESTER: self._tester_template,
        }
        
        # 约束规则
        self._default_constraints = [
            "遵循现有代码风格",
            "不引入新的依赖",
            "保持向后兼容",
            "添加必要的类型注解",
            "遵循 TDD 流程"
        ]
        
        # 搜索模式
        self._search_patterns = {
            "function": r'(?:def |async def )(\w+)\s*\([^)]*\).*:',
            "class": r'class (\w+)[\(:]',
            "import": r'^import |^from \w+ import ',
            "test": r'def test_',
            "type_hint": r'-> \w+:',
        }
    
    def dispatch(
        self,
        task: str,
        subagent_type: SubagentType,
        relevant_files: Optional[List[str]] = None,
        additional_constraints: Optional[List[str]] = None,
        spec: Optional[str] = None
    ) -> PromptBundle:
        """
        调度子代理
        
        Args:
            task: 任务描述
            subagent_type: 子代理类型
            relevant_files: 相关的文件列表
            additional_constraints: 额外的约束
            spec: 规范文档
            
        Returns:
            PromptBundle: 完整的提示词包
        """
        # 获取模板
        template_func = self._templates.get(subagent_type)
        if not template_func:
            raise ValueError(f"Unknown subagent type: {subagent_type}")
        
        # 构造上下文
        context_files = self._construct_context(relevant_files or [])
        
        # 合并约束
        constraints = self._default_constraints.copy()
        if additional_constraints:
            constraints.extend(additional_constraints)
        
        # 提取模式
        patterns = self._extract_patterns(context_files)
        
        # 生成提示词
        prompt = template_func(
            task=task,
            context_files=context_files,
            constraints=constraints,
            patterns=patterns,
            spec=spec
        )
        
        return PromptBundle(
            subagent_type=subagent_type.value,
            task=task,
            prompt=prompt,
            relevant_files=[f.file_path for f in context_files],
            constraints=constraints,
            patterns=patterns,
            skills=self._get_skills(subagent_type),
            metadata={
                "context_count": len(context_files),
                "created_at": datetime.now().isoformat()
            }
        )
    
    def _construct_context(self, files: List[str]) -> List[ContextReference]:
        """
        构造精确的上下文
        
        只读取相关文件的关键部分，避免上下文溢出
        """
        context_files = []
        
        for file_path in files:
            try:
                full_path = os.path.join(self.base_path, file_path)
                if not os.path.exists(full_path):
                    logger.warning(f"File not found: {file_path}")
                    continue
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取关键部分
                extracted = self._extract_key_sections(content, file_path)
                
                context_files.append(ContextReference(
                    file_path=file_path,
                    content=extracted,
                    relevance=self._calculate_relevance(content, file_path)
                ))
                
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        
        # 按相关性排序
        context_files.sort(key=lambda x: x.relevance, reverse=True)
        
        return context_files[:10]  # 最多 10 个文件
    
    def _extract_key_sections(self, content: str, file_path: str) -> str:
        """提取关键部分"""
        lines = content.split('\n')
        
        # 如果文件太长，提取关键部分
        if len(lines) > 200:
            # 提取导入、类定义、函数定义
            key_lines = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # 导入
                if stripped.startswith('import ') or stripped.startswith('from '):
                    key_lines.append((i, line))
                # 类定义
                elif stripped.startswith('class '):
                    key_lines.append((i, line))
                # 函数定义
                elif stripped.startswith('def ') or stripped.startswith('async def '):
                    key_lines.append((i, line))
                # 类型注解
                elif ' -> ' in line and ':' in line:
                    key_lines.append((i, line))
            
            # 重新组装
            if key_lines:
                result = []
                for line_num, line in key_lines:
                    # 添加前后几行上下文
                    start = max(0, line_num - 2)
                    end = min(len(lines), line_num + 10)
                    result.append(f"// Line {line_num}")
                    result.extend(lines[start:end])
                    result.append("")
                return '\n'.join(result)
        
        return content
    
    def _calculate_relevance(self, content: str, file_path: str) -> float:
        """计算文件相关性"""
        score = 0.5  # 基础分数
        
        # 文件名匹配
        if 'agent' in file_path.lower():
            score += 0.2
        if 'test' in file_path.lower():
            score += 0.1
        if '__init__' in file_path:
            score -= 0.1
        
        # 内容丰富度
        lines = content.split('\n')
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        if len(code_lines) > 50:
            score += 0.1
        if len(code_lines) < 10:
            score -= 0.1
        
        return min(1.0, max(0.0, score))
    
    def _extract_patterns(self, context_files: List[ContextReference]) -> List[str]:
        """提取代码模式"""
        patterns = []
        
        for cf in context_files:
            content = cf.content
            
            # 函数模式
            for match in re.finditer(self._search_patterns['function'], content):
                patterns.append(f"def {match.group(1)}(...)")
            
            # 类模式
            for match in re.finditer(self._search_patterns['class'], content):
                patterns.append(f"class {match.group(1)}")
            
            # 导入模式
            imports = re.findall(r'from (\w+) import', content)
            for imp in imports[:5]:  # 最多 5 个
                patterns.append(f"from {imp} import ...")
        
        # 去重
        return list(set(patterns))[:20]  # 最多 20 个模式
    
    def _get_skills(self, subagent_type: SubagentType) -> List[str]:
        """获取技能描述"""
        skills_map = {
            SubagentType.CODER: [
                "Python",
                "TDD (Test-Driven Development)",
                "Code Review",
                "Type Hints"
            ],
            SubagentType.REVIEWER: [
                "Security Analysis",
                "Code Quality",
                "Best Practices",
                "Critical Thinking"
            ],
            SubagentType.RESEARCHER: [
                "Information Retrieval",
                "Code Analysis",
                "Documentation",
                "Technical Writing"
            ],
            SubagentType.PLANNER: [
                "Task Breakdown",
                "Dependency Analysis",
                "Risk Assessment",
                "Agile Methodologies"
            ],
            SubagentType.TESTER: [
                "Unit Testing",
                "Integration Testing",
                "Test Coverage",
                "pytest"
            ]
        }
        return skills_map.get(subagent_type, [])
    
    def _coder_template(
        self,
        task: str,
        context_files: List[ContextReference],
        constraints: List[str],
        patterns: List[str],
        spec: Optional[str] = None
    ) -> str:
        """Coder 提示词模板"""
        template = f"""## Task
{task}

## Context

### Relevant Code
"""
        for cf in context_files:
            template += f"\n// File: {cf.file_path}\n"
            template += cf.content[:2000]  # 限制上下文长度
            template += "\n\n"
        
        if patterns:
            template += "### Patterns\n"
            for p in patterns[:10]:
                template += f"- {p}\n"
            template += "\n"
        
        if spec:
            template += f"## Specification\n{spec}\n\n"
        
        template += "## Constraints\n"
        for c in constraints:
            template += f"- {c}\n"
        template += "\n"
        
        template += """## Requirements

1. **TDD Flow**: 
   - Write test FIRST (RED)
   - Write minimal code to pass (GREEN)
   - Refactor if needed (REFACTOR)

2. **Code Quality**:
   - Follow existing patterns
   - Add type hints
   - Keep functions small (< 50 lines)

3. **Output Format**:
   ```
   # Test (test_xxx.py)
   def test_xxx():
       ...
   
   # Implementation (xxx.py)
   def xxx():
       ...
   ```

Implement the solution following TDD principles.
"""
        return template
    
    def _reviewer_template(
        self,
        task: str,
        context_files: List[ContextReference],
        constraints: List[str],
        patterns: List[str],
        spec: Optional[str] = None
    ) -> str:
        """Reviewer 提示词模板"""
        template = f"""## Task
Review the following code implementation for: {task}

## Context

### Code to Review
"""
        for cf in context_files:
            template += f"\n// File: {cf.file_path}\n"
            template += cf.content[:3000]
            template += "\n\n"
        
        if spec:
            template += f"## Specification\n{spec}\n\n"
        
        template += """## Review Criteria

### BLOCKING Issues (Must Fix)
1. **Security**: SQL injection, hardcoded secrets, unsafe operations
2. **Correctness**: Logic errors, type mismatches, edge cases
3. **Breaking Changes**: API changes, interface modifications
4. **Missing Tests**: No test coverage for production code
5. **Spec Violation**: Not meeting requirements

### WARNING Issues (Should Fix)
1. **Performance**: Inefficient algorithms, unnecessary loops
2. **Maintainability**: Complex functions, poor naming
3. **Style**: Inconsistent formatting

## Output Format

```
## Review Result

### Status: [PASS / BLOCKED / NEEDS_WORK]

### Blocking Issues
- [CRITICAL/HIGH] Issue description
  - Location: line X
  - Suggestion: ...

### Warnings
- [MEDIUM/LOW] Issue description
  - Suggestion: ...

### Summary
Brief summary of the review.
```

Review critically. Block merging for any blocking issues.
"""
        return template
    
    def _researcher_template(
        self,
        task: str,
        context_files: List[ContextReference],
        constraints: List[str],
        patterns: List[str],
        spec: Optional[str] = None
    ) -> str:
        """Researcher 提示词模板"""
        template = f"""## Task
Research and gather information for: {task}

## Context
"""
        for cf in context_files:
            template += f"\n// Reference: {cf.file_path}\n"
            template += cf.content[:1500] + "\n"
        
        if patterns:
            template += "\n### Known Patterns\n"
            for p in patterns[:5]:
                template += f"- {p}\n"
        
        template += """

## Research Guidelines

1. **Understand the Domain**:
   - Identify key concepts
   - Find related implementations
   - Document patterns

2. **Analyze Existing Code**:
   - How similar features are implemented
   - Common patterns and anti-patterns
   - Error handling approaches

3. **Provide Actionable Insights**:
   - List of relevant files
   - Recommended approaches
   - Potential risks and mitigations

## Output Format

```
## Research Results

### Key Findings
- ...

### Relevant Files
- file1.py
- file2.py

### Recommendations
1. ...
2. ...

### Risks
- ...
```
"""
        return template
    
    def _planner_template(
        self,
        task: str,
        context_files: List[ContextReference],
        constraints: List[str],
        patterns: List[str],
        spec: Optional[str] = None
    ) -> str:
        """Planner 提示词模板"""
        template = f"""## Task
Create a detailed task plan for: {task}

## Context
"""
        for cf in context_files:
            template += f"\n// Related: {cf.file_path}\n"
            template += cf.content[:1000] + "\n"
        
        if spec:
            template += f"\n## Specification\n{spec}\n"
        
        template += """

## Plan Requirements

### Task Breakdown
Break down into atomic tasks (each 5-15 minutes):

### TDD Steps
Each task must follow TDD:
1. **RED**: Write failing test
2. **GREEN**: Write minimal code to pass
3. **REFACTOR**: Improve if needed

### Dependencies
- Task dependencies
- External dependencies
- Test dependencies

## Output Format

```
## Implementation Plan

### Phase 1: Foundation
- [ ] Task 1.1: Description (TDD: test_xxx)
- [ ] Task 1.2: Description (TDD: test_yyy)

### Phase 2: Core Feature
- [ ] Task 2.1: Description (TDD: test_zzz)

### Dependencies
- Phase 1 must complete before Phase 2

### Estimated Time
- Phase 1: X minutes
- Phase 2: Y minutes
```

Create a comprehensive, TDD-focused plan.
"""
        return template
    
    def _tester_template(
        self,
        task: str,
        context_files: List[ContextReference],
        constraints: List[str],
        patterns: List[str],
        spec: Optional[str] = None
    ) -> str:
        """Tester 提示词模板"""
        template = f"""## Task
Write comprehensive tests for: {task}

## Context

### Code Under Test
"""
        for cf in context_files:
            template += f"\n// File: {cf.file_path}\n"
            template += cf.content[:2000]
            template += "\n\n"
        
        if spec:
            template += f"## Specification\n{spec}\n\n"
        
        template += """
## Test Requirements

### Coverage Goals
- Unit tests for all public functions
- Edge case coverage
- Error handling tests
- Integration tests if applicable

### Test Structure
```python
import pytest
from module import function

class TestFunction:
    def test_basic_case(self):
        # Arrange
        # Act
        # Assert
    
    def test_edge_case(self):
        ...
    
    def test_error_case(self):
        with pytest.raises(Exception):
            function(invalid_input)
```

### Quality Criteria
- Tests are independent
- Descriptive test names
- Clear arrange-act-assert pattern
- No test logic (if/else)

## Output Format

Provide complete test code with:
1. Necessary imports
2. Test class for each function
3. Multiple test cases per function
4. Edge and error cases

Write production-ready tests.
"""
        return template
    
    def construct_context(
        self,
        task: str,
        files: List[str],
        max_context_lines: int = 500
    ) -> str:
        """
        构造简洁的上下文字符串
        
        用于快速生成提示词
        """
        context_files = self._construct_context(files)
        
        result = f"## Task: {task}\n\n## Relevant Code:\n"
        
        total_lines = 0
        for cf in context_files:
            if total_lines + cf.content.count('\n') > max_context_lines:
                break
            
            result += f"\n### {cf.file_path}\n"
            result += cf.content[:3000]  # 每个文件最多 3000 字符
            result += "\n"
            total_lines += cf.content.count('\n')
        
        return result
    
    def get_prompt_template(self, subagent_type: SubagentType) -> str:
        """获取提示词模板"""
        template_func = self._templates.get(subagent_type)
        if not template_func:
            raise ValueError(f"Unknown subagent type: {subagent_type}")
        
        # 返回模板签名作为示例
        return f"""Template for {subagent_type.value}:

Args:
- task: str - 任务描述
- context_files: List[ContextReference] - 上下文文件
- constraints: List[str] - 约束列表
- patterns: List[str] - 代码模式
- spec: Optional[str] - 规范文档

Returns:
- str: 格式化后的提示词
"""


# ============================================================================
# Demo / Tests
# ============================================================================

if __name__ == "__main__":
    print("=== SubagentDispatcher Demo ===\n")
    
    dispatcher = SubagentDispatcher()
    
    # Test 1: CODER dispatch
    print("1. CODER Dispatch:")
    bundle = dispatcher.dispatch(
        task="实现用户认证模块",
        subagent_type=SubagentType.CODER,
        relevant_files=["src/agents/base_agent.py"],
        additional_constraints=["使用 bcrypt 加密"]
    )
    print(f"   Type: {bundle.subagent_type}")
    print(f"   Files: {len(bundle.relevant_files)}")
    print(f"   Constraints: {len(bundle.constraints)}")
    print(f"   Skills: {bundle.skills[:2]}")
    print()
    
    # Test 2: REVIEWER dispatch
    print("2. REVIEWER Dispatch:")
    bundle = dispatcher.dispatch(
        task="审查登录模块安全性",
        subagent_type=SubagentType.REVIEWER
    )
    print(f"   Type: {bundle.subagent_type}")
    print(f"   Prompt length: {len(bundle.prompt)} chars")
    print()
    
    # Test 3: PLANNER dispatch
    print("3. PLANNER Dispatch:")
    bundle = dispatcher.dispatch(
        task="实现订单处理系统",
        subagent_type=SubagentType.PLANNER
    )
    print(f"   Type: {bundle.subagent_type}")
    print(f"   Constraints: {bundle.constraints}")
    print()
    
    # Test 4: Context construction
    print("4. Context Construction:")
    context = dispatcher.construct_context(
        task="添加缓存功能",
        files=["src/agents/base_agent.py"]
    )
    print(f"   Context length: {len(context)} chars")
    print()
    
    # Test 5: Template retrieval
    print("5. Prompt Templates Available:")
    for st in SubagentType:
        template = dispatcher.get_prompt_template(st)
        print(f"   - {st.value}: {template.split(chr(10))[0]}")
    print()
    
    # Test 6: Full dispatch example
    print("6. Full CODER Prompt Example:")
    bundle = dispatcher.dispatch(
        task="实现数据验证器",
        subagent_type=SubagentType.CODER,
        spec="## 需求\n- 验证邮箱格式\n- 验证手机号\n- 验证密码强度"
    )
    print("   [Prompt Preview]")
    print(bundle.prompt[:500] + "...")
    print()
    
    print("=== Demo Complete ===")
