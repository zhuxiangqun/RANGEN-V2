#!/usr/bin/env python3
"""
Three-tier Prompt Structure - 三层提示结构

基于OpenClaw架构的提示工程设计:
- SOUL: Agent核心身份、价值观、行为准则
- AGENTS: Agent能力定义、技能描述
- TOOLS: 工具定义、使用说明

这样做的好处:
1. 模块化 - 身份、能力、工具分离，便于维护
2. 可配置 - 可以动态组合不同的SOUL/AGENTS/TOOLS
3. 可版本化 - 可以为不同场景创建不同的配置
4. 可扩展 - 易于添加新的能力或工具
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class PromptTier(Enum):
    """提示层级"""
    SOUL = "soul"       # 身份层
    AGENTS = "agents"   # 能力层
    TOOLS = "tools"     # 工具层


@dataclass
class SoulConfig:
    """SOUL配置 - Agent身份定义"""
    
    # 身份
    name: str = ""
    description: str = ""
    persona: str = ""
    
    # 价值观
    values: List[str] = field(default_factory=list)
    
    # 约束
    constraints: List[str] = field(default_factory=list)
    
    # 行为准则
    guidelines: List[str] = field(default_factory=list)
    
    # 沟通风格
    communication_style: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SoulConfig':
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            persona=data.get("persona", ""),
            values=data.get("values", []),
            constraints=data.get("constraints", []),
            guidelines=data.get("guidelines", []),
            communication_style=data.get("communication_style", "")
        )
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = []
        
        if self.name:
            md.append(f"# Identity: {self.name}")
        
        if self.description:
            md.append(f"\n## Description\n{self.description}")
        
        if self.persona:
            md.append(f"\n## Persona\n{self.persona}")
        
        if self.values:
            md.append("\n## Values")
            for value in self.values:
                md.append(f"- {value}")
        
        if self.constraints:
            md.append("\n## Constraints")
            for constraint in self.constraints:
                md.append(f"- {constraint}")
        
        if self.guidelines:
            md.append("\n## Guidelines")
            for guideline in self.guidelines:
                md.append(f"- {guideline}")
        
        if self.communication_style:
            md.append(f"\n## Communication Style\n{self.communication_style}")
        
        return "\n".join(md)


@dataclass
class AgentCapability:
    """Agent能力定义"""
    
    name: str
    description: str
    method: str = ""
    when_to_use: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)
    priority: int = 0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCapability':
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            method=data.get("method", ""),
            when_to_use=data.get("when_to_use", ""),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
            priority=data.get("priority", 0)
        )


@dataclass
class AgentsConfig:
    """AGENTS配置 - Agent能力定义"""
    
    # 核心能力
    core_capabilities: List[AgentCapability] = field(default_factory=list)
    
    # 扩展能力
    extended_capabilities: List[AgentCapability] = field(default_factory=list)
    
    # 能力组
    capability_groups: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentsConfig':
        """从字典创建"""
        core = [
            AgentCapability.from_dict(c) 
            for c in data.get("core_capabilities", [])
        ]
        extended = [
            AgentCapability.from_dict(c) 
            for c in data.get("extended_capabilities", [])
        ]
        
        return cls(
            core_capabilities=core,
            extended_capabilities=extended,
            capability_groups=data.get("capability_groups", {})
        )
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = ["# Capabilities"]
        
        if self.core_capabilities:
            md.append("\n## Core Capabilities")
            for cap in self.core_capabilities:
                md.append(f"\n### {cap.name}")
                md.append(f"- description: {cap.description}")
                if cap.method:
                    md.append(f"- method: {cap.method}")
                if cap.when_to_use:
                    md.append(f"- when_to_use: {cap.when_to_use}")
                if cap.examples:
                    md.append("- examples:")
                    for ex in cap.examples:
                        md.append(f"  - {ex}")
        
        if self.extended_capabilities:
            md.append("\n## Extended Capabilities")
            for cap in self.extended_capabilities:
                md.append(f"\n### {cap.name}")
                md.append(f"- description: {cap.description}")
        
        return "\n".join(md)
    
    def get_capabilities_for_context(self, context: str) -> List[AgentCapability]:
        """根据上下文获取相关能力"""
        relevant = []
        
        for cap in self.core_capabilities + self.extended_capabilities:
            # 简单匹配 - 实际可以使用更复杂的匹配算法
            if context.lower() in cap.when_to_use.lower() or context.lower() in cap.description.lower():
                relevant.append(cap)
        
        # 如果没有匹配的，返回核心能力
        if not relevant:
            relevant = self.core_capabilities
        
        return sorted(relevant, key=lambda c: c.priority, reverse=True)


@dataclass
class ToolDefinition:
    """工具定义"""
    
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    category: str = "general"
    requires_approval: bool = False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolDefinition':
        """从字典创建"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            parameters=data.get("parameters", {}),
            examples=data.get("examples", []),
            category=data.get("category", "general"),
            requires_approval=data.get("requires_approval", False)
        )
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = [f"## Tool: {self.name}"]
        md.append(f"\n- description: {self.description}")
        md.append(f"- category: {self.category}")
        
        if self.parameters:
            md.append("- parameters:")
            for param_name, param_info in self.parameters.items():
                required = "required" if param_info.get("required", False) else "optional"
                param_type = param_info.get("type", "any")
                description = param_info.get("description", "")
                md.append(f"  - {param_name} ({param_type}, {required}): {description}")
        
        if self.examples:
            md.append("- examples:")
            for ex in self.examples:
                md.append(f"  - {json.dumps(ex, ensure_ascii=False)}")
        
        return "\n".join(md)


@dataclass
class ToolsConfig:
    """TOOLS配置 - 工具定义"""
    
    tools: List[ToolDefinition] = field(default_factory=list)
    tool_groups: Dict[str, List[str]] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolsConfig':
        """从字典创建"""
        tools = [
            ToolDefinition.from_dict(t) 
            for t in data.get("tools", [])
        ]
        
        return cls(
            tools=tools,
            tool_groups=data.get("tool_groups", {})
        )
    
    def to_markdown(self) -> str:
        """转换为Markdown格式"""
        md = ["# Tool Definitions"]
        
        for tool in self.tools:
            md.append(f"\n{tool.to_markdown()}")
        
        return "\n".join(md)
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tools_by_category(self, category: str) -> List[ToolDefinition]:
        """按类别获取工具"""
        return [t for t in self.tools if t.category == category]


class ThreeTierPromptBuilder:
    """三层提示构建器"""
    
    def __init__(
        self,
        soul: Optional[SoulConfig] = None,
        agents: Optional[AgentsConfig] = None,
        tools: Optional[ToolsConfig] = None
    ):
        self.soul = soul or SoulConfig()
        self.agents = agents or AgentsConfig()
        self.tools = tools or ToolsConfig()
        
        self._system_prompt_cache: Dict[str, str] = {}
    
    @classmethod
    def from_files(
        cls,
        soul_path: Optional[str] = None,
        agents_path: Optional[str] = None,
        tools_path: Optional[str] = None
    ) -> 'ThreeTierPromptBuilder':
        """从文件加载配置"""
        soul = cls._load_soul(soul_path)
        agents = cls._load_agents(agents_path)
        tools = cls._load_tools(tools_path)
        
        return cls(soul=soul, agents=agents, tools=tools)
    
    @classmethod
    def _load_soul(cls, path: Optional[str]) -> SoulConfig:
        """加载SOUL配置"""
        if not path:
            return cls._default_soul()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            return SoulConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"加载SOUL配置失败: {e}，使用默认配置")
            return cls._default_soul()
    
    @classmethod
    def _load_agents(cls, path: Optional[str]) -> AgentsConfig:
        """加载AGENTS配置"""
        if not path:
            return cls._default_agents()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            return AgentsConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"加载AGENTS配置失败: {e}，使用默认配置")
            return cls._default_agents()
    
    @classmethod
    def _load_tools(cls, path: Optional[str]) -> ToolsConfig:
        """加载TOOLS配置"""
        if not path:
            return cls._default_tools()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.endswith('.yaml') or path.endswith('.yml'):
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)
            return ToolsConfig.from_dict(data)
        except Exception as e:
            logger.warning(f"加载TOOLS配置失败: {e}，使用默认配置")
            return cls._default_tools()
    
    @staticmethod
    def _default_soul() -> SoulConfig:
        """默认SOUL配置"""
        return SoulConfig(
            name="RANGEN Assistant",
            description="A helpful AI assistant specialized in research and knowledge retrieval",
            persona="You are a professional, knowledgeable, and helpful AI assistant.",
            values=[
                "Provide accurate and reliable information",
                "Be transparent about limitations",
                "Respect user privacy and security",
                "Continuously improve and learn"
            ],
            constraints=[
                "Never reveal sensitive information",
                "Ask for clarification when uncertain",
                "Admit when you don't know something",
                "Follow safety guidelines"
            ],
            guidelines=[
                "Break down complex problems into steps",
                "Use tools when appropriate",
                "Verify information before presenting",
                "Provide clear explanations"
            ],
            communication_style="Professional, clear, and concise"
        )
    
    @staticmethod
    def _default_agents() -> AgentsConfig:
        """默认AGENTS配置"""
        return AgentsConfig(
            core_capabilities=[
                AgentCapability(
                    name="research",
                    description="Search and synthesize information from knowledge bases",
                    method="research(query, sources)",
                    when_to_use="When user needs detailed information or factual answers",
                    priority=10
                ),
                AgentCapability(
                    name="reasoning",
                    description="Logical analysis and step-by-step reasoning",
                    method="reasoning(problem, context)",
                    when_to_use="When user asks for analysis or explanation",
                    priority=9
                ),
                AgentCapability(
                    name="code_review",
                    description="Review code for bugs and security issues",
                    method="review_code(file_path, language)",
                    when_to_use="When user asks to review code",
                    priority=8
                )
            ],
            extended_capabilities=[
                AgentCapability(
                    name="data_analysis",
                    description="Analyze and visualize data",
                    method="analyze_data(data, options)",
                    when_to_use="When user needs data analysis",
                    priority=5
                ),
                AgentCapability(
                    name="writing",
                    description="Generate and edit text content",
                    method="write(content_type, requirements)",
                    when_to_use="When user needs content generation",
                    priority=5
                )
            ]
        )
    
    @staticmethod
    def _default_tools() -> ToolsConfig:
        """默认TOOLS配置"""
        return ToolsConfig(
            tools=[
                ToolDefinition(
                    name="rag",
                    description="Search knowledge base for relevant information",
                    parameters={
                        "query": {
                            "type": "string",
                            "required": True,
                            "description": "The search query"
                        }
                    },
                    examples=[{"query": "What is machine learning?"}],
                    category="knowledge"
                ),
                ToolDefinition(
                    name="search",
                    description="Search the web for information",
                    parameters={
                        "query": {
                            "type": "string",
                            "required": True,
                            "description": "The search query"
                        },
                        "num_results": {
                            "type": "integer",
                            "required": False,
                            "description": "Number of results to return"
                        }
                    },
                    examples=[{"query": "latest AI news", "num_results": 5}],
                    category="search"
                ),
                ToolDefinition(
                    name="calculator",
                    description="Perform mathematical calculations",
                    parameters={
                        "expression": {
                            "type": "string",
                            "required": True,
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    examples=[{"expression": "2+2*3"}],
                    category="utility"
                ),
                ToolDefinition(
                    name="code_executor",
                    description="Execute code in a sandboxed environment",
                    parameters={
                        "code": {
                            "type": "string",
                            "required": True,
                            "description": "Code to execute"
                        },
                        "language": {
                            "type": "string",
                            "required": True,
                            "description": "Programming language"
                        }
                    },
                    examples=[{"code": "print('Hello')", "language": "python"}],
                    category="execution",
                    requires_approval=True
                )
            ],
            tool_groups={
                "knowledge": ["rag"],
                "search": ["search"],
                "utility": ["calculator"],
                "execution": ["code_executor"]
            }
        )
    
    def build_system_prompt(
        self,
        context: Optional[str] = None,
        include_tools: bool = True,
        include_capabilities: bool = True
    ) -> str:
        """
        构建完整的系统提示词
        
        Args:
            context: 上下文信息
            include_tools: 是否包含工具定义
            include_capabilities: 是否包含能力定义
            
        Returns:
            完整的系统提示词
        """
        prompt_parts = []
        
        # 1. SOUL层
        prompt_parts.append(self.soul.to_markdown())
        
        # 2. AGENTS层
        if include_capabilities:
            prompt_parts.append("\n")
            prompt_parts.append(self.agents.to_markdown())
        
        # 3. TOOLS层
        if include_tools:
            prompt_parts.append("\n")
            prompt_parts.append(self.tools.to_markdown())
        
        # 4. 上下文
        if context:
            prompt_parts.append(f"\n# Current Context\n{context}")
        
        return "\n".join(prompt_parts)
    
    def build_thinking_prompt(self, query: str, context: str) -> str:
        """构建思考提示词"""
        return f"""Based on the following information, think about the next step:

Task: {query}

Context: {context}

Capabilities:
{chr(10).join(f"- {c.name}: {c.description}" for c in self.agents.core_capabilities)}

Think step by step and provide your reasoning.
"""
    
    def build_action_prompt(
        self,
        thought: str,
        query: str,
        observations: str
    ) -> str:
        """构建行动提示词"""
        tools_schema = {}
        for tool in self.tools.tools:
            tools_schema[tool.name] = tool.parameters
        
        return f"""Based on the following information, decide the next action:

Task: {query}
Thought: {thought}
Observations: {observations}

Available Tools:
{json.dumps(tools_schema, indent=2, ensure_ascii=False)}

Return the action plan in JSON format:
{{
    "tool_name": "tool_name",
    "params": {{"parameter_name": "parameter_value"}},
    "reasoning": "reason for choosing this tool"
}}

**CRITICAL REQUIREMENTS**:
1. Return ONLY JSON, no other content.
2. If no tool is needed, use "final_answer" as tool_name.
"""
    
    def build_final_answer_prompt(
        self,
        query: str,
        observations: List[Dict[str, Any]]
    ) -> str:
        """构建最终答案提示词"""
        observations_text = "\n".join([
            f"- {obs.get('tool_name', 'unknown')}: {obs.get('data', '')[:200]}"
            for obs in observations if obs.get('success')
        ])
        
        return f"""Based on all the observations, provide a final answer to the user's query.

Original Query: {query}

Observations:
{observations_text}

Provide a comprehensive and accurate answer.
"""
    
    def update_soul(self, soul: SoulConfig):
        """更新SOUL配置"""
        self.soul = soul
        self._system_prompt_cache.clear()
    
    def update_agents(self, agents: AgentsConfig):
        """更新AGENTS配置"""
        self.agents = agents
        self._system_prompt_cache.clear()
    
    def update_tools(self, tools: ToolsConfig):
        """更新TOOLS配置"""
        self.tools = tools
        self._system_prompt_cache.clear()
    
    def add_capability(self, capability: AgentCapability):
        """添加能力"""
        self.agents.extended_capabilities.append(capability)
        self._system_prompt_cache.clear()
    
    def add_tool(self, tool: ToolDefinition):
        """添加工具"""
        self.tools.tools.append(tool)
        self._system_prompt_cache.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "soul": {
                "name": self.soul.name,
                "description": self.soul.description,
                "persona": self.soul.persona,
                "values": self.soul.values,
                "constraints": self.soul.constraints,
                "guidelines": self.soul.guidelines,
                "communication_style": self.soul.communication_style
            },
            "agents": {
                "core_capabilities": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "method": c.method,
                        "when_to_use": c.when_to_use,
                        "priority": c.priority
                    }
                    for c in self.agents.core_capabilities
                ],
                "extended_capabilities": [
                    {
                        "name": c.name,
                        "description": c.description,
                        "method": c.method,
                        "when_to_use": c.when_to_use,
                        "priority": c.priority
                    }
                    for c in self.agents.extended_capabilities
                ]
            },
            "tools": {
                "tools": [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                        "category": t.category,
                        "requires_approval": t.requires_approval
                    }
                    for t in self.tools.tools
                ]
            }
        }


# 全局实例
_prompt_builder: Optional[ThreeTierPromptBuilder] = None


def get_prompt_builder() -> ThreeTierPromptBuilder:
    """获取全局提示构建器"""
    global _prompt_builder
    if _prompt_builder is None:
        _prompt_builder = ThreeTierPromptBuilder()
    return _prompt_builder


def reset_prompt_builder():
    """重置提示构建器"""
    global _prompt_builder
    _prompt_builder = None
