#!/usr/bin/env python3
"""
Enhanced Prompt Manager with Three-tier Support
集成三层提示结构的增强版提示管理器
"""

import os
from typing import Dict, Any, Optional, List
from string import Template

from .three_tier import (
    ThreeTierPromptBuilder,
    SoulConfig,
    AgentCapability,
    AgentsConfig,
    ToolDefinition,
    ToolsConfig,
    get_prompt_builder as get_three_tier_builder
)

from src.services.logging_service import get_logger

logger = get_logger(__name__)


class EnhancedPromptManager:
    """
    增强版提示管理器 - 支持三层提示结构
    
    新增功能:
    - 三层提示构建 (SOUL/AGENTS/TOOLS)
    - 提示版本管理
    - 提示模板继承
    - 动态提示组合
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # 原有提示
        self._prompts: Dict[str, str] = {}
        self._load_prompts()
        
        # 三层提示构建器
        self._three_tier_builder: Optional[ThreeTierPromptBuilder] = None
        self._init_three_tier_builder()
        
        # 提示版本
        self._prompt_versions: Dict[str, str] = {}
        
        # 提示历史
        self._prompt_history: List[Dict[str, Any]] = []
        
        logger.info("EnhancedPromptManager initialized with Three-tier support")
    
    def _load_prompts(self):
        """加载原有提示模板"""
        self._prompts["reasoning_agent_system"] = """
You are a highly intelligent ReAct (Reasoning+Acting) agent.
Your goal is to answer the user's query by breaking it down, reasoning step-by-step, and using tools when necessary.

{skill_context}

TOOLS AVAILABLE:
{tool_descriptions}

RESPONSE FORMAT:
You MUST output your response in the following strictly structured format:

Thought: [Your reasoning process about what to do next]
Action: [The name of the tool to use, or "Final Answer" if you are done]
Action Input: [The input for the tool, or the final answer text]

EXAMPLES:

User: What is the boiling point of water at sea level?
Thought: The user is asking for a scientific fact. I know this directly.
Action: Final Answer
Action Input: The boiling point of water at sea level is 100 degrees Celsius (212 degrees Fahrenheit).

User: Who is the CEO of DeepMind?
Thought: I need to check the current CEO of DeepMind. I will use the search tool.
Action: retrieval_tool
Action Input: current CEO of DeepMind

---
Current User Query: {query}
Context: {context}
"""

        self._prompts["chat_system"] = """
You are a helpful AI assistant.

{skill_context}

AVAILABLE TOOLS:
{tool_descriptions}

User: {query}
"""

        self._prompts["react_no_tools"] = """
You are a reasoning agent.
{skill_context}

Think step by step about: {query}

Show your reasoning:
"""
    
    def _init_three_tier_builder(self):
        """初始化三层提示构建器"""
        try:
            self._three_tier_builder = get_three_tier_builder()
            logger.info("Three-tier prompt builder initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize three-tier builder: {e}")
    
    # ==================== 原有方法兼容 ====================
    
    def get_prompt(self, name: str, **kwargs) -> str:
        """获取和格式化提示模板"""
        template_str = self._prompts.get(name)
        if not template_str:
            logger.warning(f"Prompt template '{name}' not found.")
            return ""
        
        kwargs.setdefault('tool_descriptions', 'No tools available.')
        kwargs.setdefault('skill_context', '')
        kwargs.setdefault('context', 'No context.')
        kwargs.setdefault('query', '')
        
        try:
            return template_str.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing parameter for prompt '{name}': {e}")
            return template_str
    
    def get_prompt_with_skills(self, name: str, skill_names: List[str] = None, **kwargs) -> str:
        """获取带Skills的提示"""
        try:
            from src.agents.skills.prompt_builder import get_skill_prompt_builder
            builder = get_skill_prompt_builder()
            
            tool_descriptions = builder.get_tool_descriptions(skill_names)
            skill_context = builder.get_skill_prompts(skill_names)
            
            kwargs.setdefault('tool_descriptions', tool_descriptions)
            kwargs.setdefault('skill_context', skill_context)
        except ImportError:
            kwargs.setdefault('tool_descriptions', 'No tools available.')
            kwargs.setdefault('skill_context', '')
            logger.warning("Skills not available, using basic prompt.")
        
        return self.get_prompt(name, **kwargs)
    
    def get_tools_for_llm(self, skill_names: List[str] = None) -> List[Dict[str, Any]]:
        """获取LLM格式的工具"""
        try:
            from src.agents.skills.prompt_builder import get_skill_prompt_builder
            builder = get_skill_prompt_builder()
            return builder.get_available_tools(skill_names)
        except ImportError:
            return []
    
    def update_prompt(self, name: str, template: str):
        """动态更新提示模板"""
        self._prompts[name] = template
    
    def list_prompts(self) -> List[str]:
        """列出所有提示模板"""
        return list(self._prompts.keys())
    
    def add_prompt(self, name: str, template: str):
        """添加新提示模板"""
        self._prompts[name] = template
    
    # ==================== 三层提示方法 ====================
    
    def get_three_tier_builder(self) -> ThreeTierPromptBuilder:
        """获取三层提示构建器"""
        if self._three_tier_builder is None:
            self._init_three_tier_builder()
        return self._three_tier_builder
    
    def build_three_tier_system_prompt(
        self,
        context: Optional[str] = None,
        include_tools: bool = True,
        include_capabilities: bool = True
    ) -> str:
        """
        构建三层系统提示
        
        Args:
            context: 上下文信息
            include_tools: 是否包含工具定义
            include_capabilities: 是否包含能力定义
            
        Returns:
            完整的系统提示
        """
        if self._three_tier_builder is None:
            logger.warning("Three-tier builder not initialized, using basic prompt")
            return self.get_prompt("reasoning_agent_system")
        
        return self._three_tier_builder.build_system_prompt(
            context=context,
            include_tools=include_tools,
            include_capabilities=include_capabilities
        )
    
    def build_three_tier_thinking_prompt(self, query: str, context: str) -> str:
        """构建思考提示"""
        if self._three_tier_builder is None:
            return f"Think step by step about: {query}"
        return self._three_tier_builder.build_thinking_prompt(query, context)
    
    def build_three_tier_action_prompt(
        self,
        thought: str,
        query: str,
        observations: str
    ) -> str:
        """构建行动提示"""
        if self._three_tier_builder is None:
            return f"Based on thought: {thought}, decide next action"
        return self._three_tier_builder.build_action_prompt(thought, query, observations)
    
    def build_three_tier_answer_prompt(
        self,
        query: str,
        observations: List[Dict[str, Any]]
    ) -> str:
        """构建答案提示"""
        if self._three_tier_builder is None:
            return f"Answer the query: {query}"
        return self._three_tier_builder.build_final_answer_prompt(query, observations)
    
    def update_soul(self, soul: SoulConfig):
        """更新SOUL配置"""
        if self._three_tier_builder:
            self._three_tier_builder.update_soul(soul)
            logger.info("SOUL config updated")
    
    def update_agents(self, agents: AgentsConfig):
        """更新AGENTS配置"""
        if self._three_tier_builder:
            self._three_tier_builder.update_agents(agents)
            logger.info("AGENTS config updated")
    
    def update_tools(self, tools: ToolsConfig):
        """更新TOOLS配置"""
        if self._three_tier_builder:
            self._three_tier_builder.update_tools(tools)
            logger.info("TOOLS config updated")
    
    def add_capability(self, capability: AgentCapability):
        """添加能力"""
        if self._three_tier_builder:
            self._three_tier_builder.add_capability(capability)
            logger.info(f"Capability added: {capability.name}")
    
    def add_tool(self, tool: ToolDefinition):
        """添加工具"""
        if self._three_tier_builder:
            self._three_tier_builder.add_tool(tool)
            logger.info(f"Tool added: {tool.name}")
    
    # =================提示版本管理 =================
    
    def save_prompt_version(self, name: str, version: str = "default"):
        """保存提示版本"""
        if name in self._prompts:
            self._prompt_versions[f"{name}:{version}"] = self._prompts[name]
            logger.info(f"Saved prompt version: {name}:{version}")
    
    def load_prompt_version(self, name: str, version: str = "default") -> bool:
        """加载提示版本"""
        key = f"{name}:{version}"
        if key in self._prompt_versions:
            self._prompts[name] = self._prompt_versions[key]
            logger.info(f"Loaded prompt version: {key}")
            return True
        return False
    
    def list_prompt_versions(self, name: str) -> List[str]:
        """列出提示版本"""
        prefix = f"{name}:"
        return [k[len(prefix):] for k in self._prompt_versions.keys() if k.startswith(prefix)]
    
    # =================提示历史 =================
    
    def record_prompt_usage(self, name: str, context: Dict[str, Any]):
        """记录提示使用"""
        import time
        self._prompt_history.append({
            "name": name,
            "timestamp": time.time(),
            "context": context
        })
        
        # 保留最近1000条
        if len(self._prompt_history) > 1000:
            self._prompt_history = self._prompt_history[-1000:]
    
    def get_prompt_usage_stats(self) -> Dict[str, Any]:
        """获取提示使用统计"""
        from collections import Counter
        names = [p["name"] for p in self._prompt_history]
        return {
            "total_usage": len(self._prompt_history),
            "by_name": Counter(names)
        }
    
    # =================便捷方法 =================
    
    def use_three_tier_mode(self, enable: bool = True):
        """切换到三层提示模式"""
        if enable and self._three_tier_builder is None:
            self._init_three_tier_builder()
    
    def get_prompt_for_agent(
        self,
        agent_type: str = "react",
        use_three_tier: bool = False,
        **kwargs
    ) -> str:
        """
        获取Agent使用的提示
        
        Args:
            agent_type: Agent类型
            use_three_tier: 是否使用三层提示
            **kwargs: 提示参数
            
        Returns:
            格式化后的提示
        """
        prompt_name = f"{agent_type}_system"
        
        if use_three_tier:
            return self.build_three_tier_system_prompt(
                context=kwargs.get("context"),
                include_tools=kwargs.get("include_tools", True),
                include_capabilities=kwargs.get("include_capabilities", True)
            )
        
        return self.get_prompt_with_skills(prompt_name, **kwargs)


# 全局实例
_enhanced_prompt_manager: Optional[EnhancedPromptManager] = None


def get_enhanced_prompt_manager() -> EnhancedPromptManager:
    """获取增强版提示管理器"""
    global _enhanced_prompt_manager
    if _enhanced_prompt_manager is None:
        _enhanced_prompt_manager = EnhancedPromptManager()
    return _enhanced_prompt_manager


# 兼容原有接口
def get_prompt_manager() -> EnhancedPromptManager:
    """获取提示管理器（兼容接口）"""
    return get_enhanced_prompt_manager()
