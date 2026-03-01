"""
Enriched Few-shot Examples System
基于 Anthropic 原则的丰富示例系统

核心原则：
1. 多样化、典型的示例
2. 不要塞入大量边缘情况
3. 示例 = 价值千言的图片
4. 提供概念性指导，而非规则清单
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ExampleCategory(Enum):
    """示例分类"""
    RETRIEVAL = "retrieval"       # 信息检索
    REASONING = "reasoning"       # 推理分析
    ACTION = "action"             # 执行操作
    DECISION = "decision"         # 决策判断
    ERROR_RECOVERY = "error"      # 错误恢复


@dataclass
class FewShotExample:
    """Few-shot 示例"""
    category: ExampleCategory
    situation: str
    thought: str
    action: str
    action_input: str
    outcome: str  # 可选，说明为什么这样选择
    key_principle: str  # 核心原则


# 丰富的多样化示例集
ENRICHED_EXAMPLES: List[FewShotExample] = [
    # ========== RETRIEVAL 示例 ==========
    FewShotExample(
        category=ExampleCategory.RETRIEVAL,
        situation="用户问关于最新 AI 技术的问题",
        thought="这个问题需要最新的信息，我训练数据可能过时。",
        action="search",
        action_input="latest AI developments 2025",
        outcome="获取最新信息后回答",
        key_principle="不确定时先搜索，避免给出过时信息"
    ),
    
    FewShotExample(
        category=ExampleCategory.RETRIEVAL,
        situation="用户问特定代码文件的实现细节",
        thought="需要查看具体的代码实现。",
        action="retrieve",
        action_input="query='authentication flow', source='code', top_k=5",
        outcome="获取相关代码上下文",
        key_principle="代码问题优先检索内部代码库"
    ),
    
    # ========== REASONING 示例 ==========
    FewShotExample(
        category=ExampleCategory.REASONING,
        situation="用户问题涉及多个步骤和条件",
        thought="这个问题需要分解成多个子问题。",
        action="analyze",
        action_input="target='用户请求', analysis_type='logic', focus='依赖关系'",
        outcome="理清问题结构，逐步解决",
        key_principle="复杂问题先分解"
    ),
    
    FewShotExample(
        category=ExampleCategory.REASONING,
        situation="需要在多个可行方案中做选择",
        thought="有多种方法可以实现，需要分析各自的权衡。",
        action="plan",
        action_input="goal='实现用户需求', subtasks=True",
        outcome="生成有组织的计划",
        key_principle="不要盲目执行，先规划"
    ),
    
    # ========== ACTION 示例 ==========
    FewShotExample(
        category=ExampleCategory.ACTION,
        situation="已经分析清楚问题，需要执行代码",
        thought="方案已确定，现在执行。",
        action="execute",
        action_input="action='run_command', command='python test.py'",
        outcome="执行并获取结果",
        key_principle="想清楚再执行，不要试探性编码"
    ),
    
    FewShotExample(
        category=ExampleCategory.ACTION,
        situation="需要创建新文件来保存结果",
        thought="需要将结果持久化。",
        action="execute",
        action_input="action='create_file', path='results.md', code='# 结果内容'",
        outcome="文件创建成功",
        key_principle="重要结果及时保存"
    ),
    
    # ========== DECISION 示例 ==========
    FewShotExample(
        category=ExampleCategory.DECISION,
        situation="搜索结果与已有知识矛盾",
        thought="应以搜索结果为准，因为可能是最新信息。",
        action="Final Answer",
        action_input="根据最新搜索结果更新答案...",
        outcome="给出正确的新信息",
        key_principle="实时信息优先于训练知识"
    ),
    
    FewShotExample(
        category=ExampleCategory.DECISION,
        situation="工具返回错误，需要决定下一步",
        thought="错误可能是因为参数不对或者服务不可用。",
        action="analyze",
        action_input="target='错误信息', analysis_type='logic', focus='原因分析'",
        outcome="找到错误原因后重试或换方案",
        key_principle="错误是分析机会，不是放弃理由"
    ),
    
    # ========== ERROR RECOVERY 示例 ==========
    FewShotExample(
        category=ExampleCategory.ERROR_RECOVERY,
        situation="执行命令失败，错误是权限问题",
        thought="需要检查权限或者使用其他方式。",
        action="execute",
        action_input="action='run_command', command='ls -la'",
        outcome="确认权限后用正确方式执行",
        key_principle="权限问题不要反复尝试，换思路"
    ),
    
    FewShotExample(
        category=ExampleCategory.ERROR_RECOVERY,
        situation="检索结果为空",
        thought="可能关键词不对或者没有相关信息。",
        action="search",
        action_input="query='相关主题的更广泛查询'",
        outcome="用更宽泛的查询重试",
        key_principle="检索为空时不要放弃，调整策略"
    ),
]


def generate_few_shot_prompt(
    category: Optional[ExampleCategory] = None,
    max_examples: int = 5
) -> str:
    """
    生成 few-shot 示例 prompt
    
    根据类别选择合适的示例，控制数量避免过多
    """
    # 筛选示例
    if category:
        examples = [e for e in ENRICHED_EXAMPLES if e.category == category]
    else:
        examples = ENRICHED_EXAMPLES
    
    # 限制数量，确保多样化
    examples = examples[:max_examples]
    
    # 生成格式化的示例
    lines = [
        "## Decision Examples (Guided by Principles)",
        "",
        "Think about the situation, decide on the best action:",
        ""
    ]
    
    for i, ex in enumerate(examples, 1):
        lines.append(f"### Example {i}: {ex.category.value}")
        lines.append(f"**Situation**: {ex.situation}")
        lines.append(f"**Thought**: {ex.thought}")
        lines.append(f"**Action**: {ex.action}")
        lines.append(f"**Action Input**: {ex.action_input}")
        if ex.outcome:
            lines.append(f"**Outcome**: {ex.outcome}")
        lines.append(f"**Key Principle**: {ex.key_principle}")
        lines.append("")
    
    return "\n".join(lines)


def get_examples_for_situation(
    situation_type: str
) -> List[FewShotExample]:
    """根据情况类型获取相关示例"""
    mapping = {
        "search_needed": ExampleCategory.RETRIEVAL,
        "code_question": ExampleCategory.REASONING,
        "complex_task": ExampleCategory.REASONING,
        "execution": ExampleCategory.ACTION,
        "choice_needed": ExampleCategory.DECISION,
        "error": ExampleCategory.ERROR_RECOVERY,
    }
    
    category = mapping.get(situation_type)
    if category:
        return [e for e in ENRICHED_EXAMPLES if e.category == category]
    
    return ENRICHED_EXAMPLES[:3]


# 整合到 Prompt Manager 的工具函数
def get_integrated_few_shot(
    context_type: str = "general",
    max_tokens: int = 2000
) -> str:
    """
    获取整合的 few-shot 示例
    根据上下文类型和 token 限制返回合适的示例
    """
    # 映射上下文类型到示例类别
    type_mapping = {
        "research": [ExampleCategory.RETRIEVAL, ExampleCategory.REASONING],
        "coding": [ExampleCategory.ACTION, ExampleCategory.REASONING, ExampleCategory.ERROR_RECOVERY],
        "decision": [ExampleCategory.DECISION, ExampleCategory.REASONING],
        "general": None  # 所有类型
    }
    
    categories = type_mapping.get(context_type)
    
    if categories:
        examples = []
        for cat in categories:
            examples.extend([e for e in ENRICHED_EXAMPLES if e.category == cat])
    else:
        examples = ENRICHED_EXAMPLES
    
    # 按 token 限制截断
    # 估算：每个示例约 400 tokens
    max_examples = max(1, max_tokens // 400)
    examples = examples[:max_examples]
    
    return generate_few_shot_prompt(max_examples=max_examples)


# 给 Prompt Manager 用的新方法
class EnrichedPromptBuilder:
    """
    丰富的 Prompt 构建器
    整合了 context engineering 原则
    """
    
    @staticmethod
    def build_system_prompt(
        skill_context: str = "",
        tool_descriptions: str = "",
        use_enriched_examples: bool = True,
        context_type: str = "general"
    ) -> str:
        """构建系统 prompt"""
        
        parts = []
        
        # 1. 核心指令 - 简洁
        parts.append("""You are an autonomous AI agent that uses tools to accomplish tasks.
Think carefully about what to do, then act. Learn from outcomes.""")
        
        # 2. 决策原则 - 概念性指导
        parts.append("""
## Decision Principles

1. **Uncertainty → Search**: If unsure about facts, search first
2. **Complexity → Plan**: If task has multiple steps, plan first
3. **Errors → Analyze**: If something fails, understand why before retrying
4. **Ambiguity → Ask**: If unclear, ask for clarification
5. **Results → Remember**: Important outcomes should be noted
""")
        
        # 2. Skill context
        if skill_context:
            parts.append(f"\n## Skill Context\n{skill_context}")
        
        # 3. Enriched few-shot examples
        if use_enriched_examples:
            parts.append(f"\n{get_integrated_few_shot(context_type)}")
        
        # 4. Tool descriptions
        if tool_descriptions:
            parts.append(f"\n## Available Tools\n{tool_descriptions}")
        
        # 5. Response format
        parts.append("""
## Response Format

Think silently about your reasoning, then take action:
- Thought: [Your reasoning about what to do]
- Action: [Tool name or "Final Answer"]
- Action Input: [Tool input or final answer]
""")
        
        return "\n\n".join(parts)


# 导出
__all__ = [
    "FewShotExample",
    "ExampleCategory",
    "ENRICHED_EXAMPLES",
    "generate_few_shot_prompt",
    "get_examples_for_situation",
    "get_integrated_few_shot",
    "EnrichedPromptBuilder"
]
