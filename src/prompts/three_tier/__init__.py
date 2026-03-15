"""
Three-tier Prompt Structure - 三层提示结构

基于OpenClaw架构的提示工程设计:
- SOUL: Agent核心身份、价值观、行为准则
- AGENTS: Agent能力定义、技能描述
- TOOLS: 工具定义、使用说明
"""

from .three_tier_prompts import (
    PromptTier,
    SoulConfig,
    AgentCapability,
    AgentsConfig,
    ToolDefinition,
    ToolsConfig,
    ThreeTierPromptBuilder,
    get_prompt_builder,
    reset_prompt_builder
)

__all__ = [
    "PromptTier",
    "SoulConfig",
    "AgentCapability",
    "AgentsConfig",
    "ToolDefinition",
    "ToolsConfig",
    "ThreeTierPromptBuilder",
    "get_prompt_builder",
    "reset_prompt_builder"
]
