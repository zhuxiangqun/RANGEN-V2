"""
Skill Prompt Builder
===================
Integrates Skills with Prompt Engineering.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from src.agents.skills import (
    Skill, SkillRegistry, SkillScope, get_skill_registry, ToolSchema
)
from src.config.unified import get_config


@dataclass
class PromptContext:
    """Prompt 构建上下文"""
    query: str
    history: List[Dict[str, Any]] = None
    workspace_id: str = ""
    enabled_skills: List[str] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []
        if self.enabled_skills is None:
            self.enabled_skills = []


class SkillPromptBuilder:
    """
    将 Skills 集成到提示词工程的构建器。
    
    功能：
    1. 从 Skills 动态生成工具描述
    2. 合并 Skills 的 prompt template
    3. 基于启用的 Skills 构建上下文
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry or get_skill_registry()
    
    def get_tool_descriptions(self, skill_names: List[str] = None) -> str:
        """
        从 Skills 生成工具描述文本。
        
        Args:
            skill_names: 要包含的技能名称列表，None 表示全部
            
        Returns:
            格式化的工具描述字符串
        """
        if skill_names is None:
            # 获取所有 skills
            skills = []
            for scope in [SkillScope.BUNDLED, SkillScope.WORKSPACE, SkillScope.MANAGED]:
                skills.extend(self.registry.list_skills(scope))
        else:
            skills = [self.registry.get_skill(name) for name in skill_names]
            skills = [s for s in skills if s is not None]
        
        if not skills:
            return "No tools available."
        
        lines = ["AVAILABLE TOOLS:"]
        for skill in skills:
            schemas = skill.get_schemas()
            if schemas:
                for schema in schemas:
                    lines.append(f"\n  - {schema.name}")
                    lines.append(f"    Description: {schema.description}")
                    if schema.parameters:
                        params = ", ".join(schema.parameters.keys())
                        lines.append(f"    Parameters: {params}")
            else:
                # 没有 schema 的 skill 也显示
                lines.append(f"\n  - {skill.name}")
                lines.append(f"    Description: {skill.metadata.description}")
        
        return "\n".join(lines)
    
    def get_skill_prompts(self, skill_names: List[str] = None) -> str:
        """
        获取 Skills 的 prompt template 合并文本。
        """
        if skill_names is None:
            skills = []
            for scope in [SkillScope.BUNDLED, SkillScope.WORKSPACE, SkillScope.MANAGED]:
                for meta in self.registry.list_skills(scope):
                    skill = self.registry.get_skill(meta.name, scope)
                    if skill:
                        skills.append(skill)
        else:
            skills = [self.registry.get_skill(name) for name in skill_names]
            skills = [s for s in skills if s]
        
        if not skills:
            return ""
        
        prompts = []
        for skill in skills:
            if skill.prompt_template:
                prompts.append(f"\n--- {skill.name.upper()} ---\n{skill.prompt_template}")
        
        return "\n".join(prompts)
    
    def build_system_prompt(
        self,
        base_template: str,
        context: PromptContext
    ) -> str:
        """
        构建完整的系统提示词。
        
        Args:
            base_template: 基础提示词模板
            context: 构建上下文
            
        Returns:
            完整的系统提示词
        """
        # 获取工具描述
        tool_descriptions = self.get_tool_descriptions(context.enabled_skills)
        
        # 获取 skills prompt
        skill_prompts = self.get_skill_prompts(context.enabled_skills)
        
        # 格式化基础模板
        try:
            prompt = base_template.format(
                query=context.query,
                tool_descriptions=tool_descriptions,
                skill_context=skill_prompts,
                context=self._format_history(context.history)
            )
        except KeyError:
            # 兼容旧的模板格式
            prompt = base_template.format(
                query=context.query,
                tool_descriptions=tool_descriptions
            )
            if skill_prompts:
                prompt += f"\n\n{skill_prompts}"
        
        return prompt
    
    def _format_history(self, history: List[Dict[str, Any]]) -> str:
        """格式化对话历史"""
        if not history:
            return "No previous context."
        
        lines = []
        for msg in history[-5:]:  # 最近 5 条
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # 截断
            lines.append(f"{role}: {content}")
        
        return "\n".join(lines)
    
    def get_available_tools(self, skill_names: List[str] = None) -> Dict[str, Any]:
        """
        获取可用工具的完整定义（用于 Tool Calling）。
        """
        if skill_names is None:
            skills = []
            for scope in [SkillScope.BUNDLED, SkillScope.WORKSPACE, SkillScope.MANAGED]:
                for meta in self.registry.list_skills(scope):
                    skill = self.registry.get_skill(meta.name, scope)
                    if skill:
                        skills.append(skill)
        else:
            skills = [self.registry.get_skill(name) for name in skill_names]
            skills = [s for s in skills if s]
        
        tools = []
        for skill in skills:
            schemas = skill.get_schemas()
            for schema in schemas:
                tools.append({
                    "name": schema.name,
                    "description": schema.description,
                    "parameters": schema.parameters
                })
        
        return tools


# 全局实例
_skill_prompt_builder: Optional[SkillPromptBuilder] = None


def get_skill_prompt_builder() -> SkillPromptBuilder:
    """获取全局 SkillPromptBuilder 实例"""
    global _skill_prompt_builder
    if _skill_prompt_builder is None:
        _skill_prompt_builder = SkillPromptBuilder()
    return _skill_prompt_builder


# 使用示例
"""
# 1. 定义基础 Agent prompt
BASE_AGENT_PROMPT = '''
You are an intelligent agent with access to tools.

{tool_descriptions}

{skill_context}

User Query: {query}
'''

# 2. 构建提示词
builder = get_skill_prompt_builder()
context = PromptContext(
    query="查找关于量子计算的最新研究",
    enabled_skills=["research", "web_search"]
)

system_prompt = builder.build_system_prompt(BASE_AGENT_PROMPT, context)

# 3. 获取工具定义（用于 Tool Calling）
tools = builder.get_available_tools(["research", "web_search"])
# [
#   {"name": "search", "description": "...", "parameters": {...}},
#   ...
# ]
"""
