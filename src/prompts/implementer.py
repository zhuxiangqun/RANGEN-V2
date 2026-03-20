#!/usr/bin/env python3
"""
Implementer Prompt Templates - 子Agent实现者Prompt模板

借鉴 Superpowers subagent-driven-development skill 的 implementer prompt:

核心理念:
1. 精确上下文 - 不继承父会话历史
2. 完整任务描述 - 包含所有必要信息
3. TDD 强制 - 必须先写测试
4. 精确文件路径 - 明确知道操作哪个文件

使用方式:

from src.prompts.implementer import (
    create_implementer_prompt,
    create_spec_context,
    create_tdd_context,
)

prompt = create_implementer_prompt(
    task_id="task-1",
    task_description="实现用户认证服务",
    spec_context=spec_context,
    files=["src/auth/service.py", "src/auth/models.py"],
    verification="运行测试",
)

# 传递给子Agent
subagent.execute(prompt)
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class ImplementerTask:
    """实现任务"""
    task_id: str
    title: str
    description: str
    files: List[str] = field(default_factory=list)  # Create/Modify/Test 文件
    steps: List[Dict] = field(default_factory=list)  # 验证步骤
    context: Dict = field(default_factory=dict)  # 额外上下文
    estimated_time: str = "2-5 分钟"
    
    def to_prompt_section(self) -> str:
        """转换为 prompt 段落"""
        section = f"""
## 任务: {self.title}

**任务ID**: {self.task_id}
**预计时间**: {self.estimated_time}

### 任务描述
{self.description}
"""
        if self.files:
            section += f"""
### 涉及文件
"""
            for f in self.files:
                section += f"- `{f}`\n"
        
        if self.steps:
            section += f"""
### 验证步骤
"""
            for i, step in enumerate(self.steps, 1):
                section += f"{i}. {step.get('description', '')}\n"
        
        return section


@dataclass
class SpecContext:
    """设计规范上下文"""
    title: str
    description: str
    components: List[str] = field(default_factory=list)
    file_changes: List[str] = field(default_factory=list)
    questions_and_answers: List[Dict] = field(default_factory=list)
    approved: bool = False
    spec_file_path: str = ""
    
    def to_prompt_section(self) -> str:
        """转换为 prompt 段落"""
        section = f"""
## 设计规范 (已批准)

**标题**: {self.title}
**描述**: {self.description}
"""
        if self.approved:
            section += "\n✅ **此设计已获得批准**\n"
        
        if self.components:
            section += f"""
### 组件
"""
            for c in self.components:
                section += f"- {c}\n"
        
        if self.questions_and_answers:
            section += f"""
### 需求讨论摘要
"""
            for qa in self.questions_and_answers[-5:]:  # 最近5条
                if 'question' in qa:
                    section += f"- Q: {qa['question']}\n"
                    if 'answer' in qa:
                        section += f"  A: {qa['answer']}\n"
        
        return section


@dataclass
class TDDContext:
    """TDD 上下文"""
    enabled: bool = True
    test_file_pattern: str = "tests/test_{module}.py"
    production_file_pattern: str = "src/{module}.py"
    
    def to_prompt_section(self) -> str:
        """转换为 prompt 段落"""
        if not self.enabled:
            return ""
        
        return """
## TDD 要求

**铁律**: "NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST"

### TDD 流程

1. **RED**: 写一个失败的测试
   - 测试应该描述期望的行为
   - 运行测试，确认失败

2. **GREEN**: 写最小代码让测试通过
   - 只写能让测试通过的最少代码
   - 不要过度设计

3. **REFACTOR**: 重构
   - 在测试通过后改进代码质量
   - 保持测试仍然通过

### 测试文件位置
```python
# 测试文件: {test_file_pattern}
# 生产文件: {production_file_pattern}
```

### 重要提醒
- 先写测试，再写实现
- 如果先写了实现代码，必须删除重新开始
- 测试必须验证真实行为，不是 mock
""".format(
            test_file_pattern=self.test_file_pattern,
            production_file_pattern=self.production_file_pattern,
        )


def create_spec_context(
    title: str,
    description: str,
    components: Optional[List[str]] = None,
    file_changes: Optional[List[str]] = None,
    questions: Optional[List[Dict]] = None,
    approved: bool = False,
    spec_file_path: str = "",
) -> SpecContext:
    """创建设计规范上下文"""
    return SpecContext(
        title=title,
        description=description,
        components=components or [],
        file_changes=file_changes or [],
        questions_and_answers=questions or [],
        approved=approved,
        spec_file_path=spec_file_path,
    )


def create_tdd_context(
    enabled: bool = True,
    test_pattern: str = "test_{name}.py",
    prod_pattern: str = "src/{name}.py",
) -> TDDContext:
    """创建 TDD 上下文"""
    return TDDContext(
        enabled=enabled,
        test_file_pattern=test_pattern,
        production_file_pattern=prod_pattern,
    )


def create_implementer_prompt(
    task: ImplementerTask,
    spec: Optional[SpecContext] = None,
    tdd: Optional[TDDContext] = None,
    additional_context: Optional[Dict] = None,
    model_hint: str = "standard",
) -> str:
    """
    创建完整的 implementer prompt
    
    Args:
        task: 实现任务
        spec: 设计规范上下文 (可选)
        tdd: TDD 上下文 (可选)
        additional_context: 额外上下文
        model_hint: 建议使用的模型 ("fast", "standard", "capable")
        
    Returns:
        完整的 prompt 字符串
    """
    # 模型选择提示
    model_hints = {
        "fast": "使用快速/便宜的模型，因为这是机械实现任务",
        "standard": "使用标准模型",
        "capable": "使用最强模型，因为需要设计判断",
    }
    
    prompt = f"""# 实现者 Prompt

你是一个实现者 Agent，负责完成以下任务。

**重要**: 你不继承任何父会话的历史。你获得的上下文都在这个 prompt 中。

---

{model_hints.get(model_hint, '')}

"""
    
    # 添加设计规范
    if spec:
        prompt += spec.to_prompt_section()
    
    # 添加任务
    prompt += task.to_prompt_section()
    
    # 添加 TDD 上下文
    if tdd:
        prompt += tdd.to_prompt_section()
    
    # 添加额外上下文
    if additional_context:
        prompt += """
## 额外上下文
"""
        for key, value in additional_context.items():
            prompt += f"""
### {key}
{value}
"""
    
    # 添加执行指南
    prompt += """
---

## 执行指南

### 你应该做的事情:
1. 阅读设计规范和任务描述
2. 如果有问题，在开始实现前提问
3. 遵循 TDD 流程 (如果启用)
4. 实现代码
5. 写/更新测试
6. 运行测试确保通过
7. 提交代码

### 你不应该做的事情:
1. 不要读取计划文件 (上下文已提供)
2. 不要假设任何未提供的信息
3. 不要跳过 TDD 流程
4. 不要提交有测试失败的代码

### 状态报告
完成每个阶段后，报告:
- DONE: 任务完成
- DONE_WITH_CONCERNS: 完成但有疑问
- NEEDS_CONTEXT: 需要更多信息
- BLOCKED: 被阻塞

---
"""
    
    return prompt


def create_implementer_prompt_from_dict(
    task_dict: Dict,
    spec_dict: Optional[Dict] = None,
) -> str:
    """
    从字典创建 implementer prompt
    
    便捷函数，用于快速创建 prompt
    """
    # 转换任务
    task = ImplementerTask(
        task_id=task_dict.get('task_id', ''),
        title=task_dict.get('title', ''),
        description=task_dict.get('description', ''),
        files=task_dict.get('files', []),
        steps=task_dict.get('steps', []),
        context=task_dict.get('context', {}),
        estimated_time=task_dict.get('estimated_time', '2-5 分钟'),
    )
    
    # 转换规范
    spec = None
    if spec_dict:
        spec = create_spec_context(
            title=spec_dict.get('title', ''),
            description=spec_dict.get('description', ''),
            components=spec_dict.get('components', []),
            file_changes=spec_dict.get('file_changes', []),
            questions=spec_dict.get('questions', []),
            approved=spec_dict.get('approved', False),
        )
    
    # 创建 TDD 上下文
    tdd = create_tdd_context(enabled=task_dict.get('tdd_enabled', True))
    
    return create_implementer_prompt(
        task=task,
        spec=spec,
        tdd=tdd,
        additional_context=task_dict.get('additional_context'),
        model_hint=task_dict.get('model_hint', 'standard'),
    )


# ==================== 便捷函数 ====================

def create_simple_task(
    title: str,
    description: str,
    files: List[str],
) -> str:
    """
    创建简单任务的 prompt
    
    用于快速创建不需要复杂上下文的任务
    """
    task = ImplementerTask(
        task_id="simple-task",
        title=title,
        description=description,
        files=files,
    )
    
    return create_implementer_prompt(task=task)


# ==================== 导出 ====================

__all__ = [
    'ImplementerTask',
    'SpecContext',
    'TDDContext',
    'create_implementer_prompt',
    'create_implementer_prompt_from_dict',
    'create_spec_context',
    'create_tdd_context',
    'create_simple_task',
]


if __name__ == '__main__':
    # 演示用法
    print("=== Implementer Prompt 模板演示 ===\n")
    
    # 创建设计规范
    spec = create_spec_context(
        title="用户认证系统",
        description="实现基本的用户名密码认证",
        components=["认证服务", "用户模型", "会话管理"],
        file_changes=["src/auth/service.py", "src/auth/models.py", "tests/test_auth.py"],
        questions=[
            {"question": "需要第三方登录吗?", "answer": "暂时不需要"},
            {"question": "密码如何存储?", "answer": "使用 bcrypt 哈希"},
        ],
        approved=True,
    )
    
    # 创建任务
    task = ImplementerTask(
        task_id="task-1",
        title="实现认证服务",
        description="实现 authenticate() 函数，支持用户名密码验证",
        files=["src/auth/service.py"],
        steps=[
            {"description": "写失败的测试", "verification": "测试应该失败"},
            {"description": "实现 authenticate 函数", "verification": "测试应该通过"},
            {"description": "提交代码", "verification": "git commit"},
        ],
        estimated_time="3 分钟",
    )
    
    # 创建 TDD 上下文
    tdd = create_tdd_context()
    
    # 生成 prompt
    prompt = create_implementer_prompt(
        task=task,
        spec=spec,
        tdd=tdd,
    )
    
    print("生成的 Prompt:")
    print("=" * 60)
    print(prompt[:2000] + "..." if len(prompt) > 2000 else prompt)
    print("=" * 60)
    
    print("\n=== Implementer Prompt 模板演示完成 ===")
