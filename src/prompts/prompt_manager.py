"""
Prompt Manager Service
Handles loading, formatting, and managing system prompts.
Now supports Skills integration.
"""

import os
from typing import Dict, Any, Optional, List
from string import Template
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class PromptManager:
    """Manages system prompts with optional Skills integration."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PromptManager, cls).__new__(cls)
            cls._instance._prompts = {}
            cls._instance._load_prompts()
        return cls._instance
    
    def _load_prompts(self):
        """Load prompts from file system or define defaults"""
        
        # Default prompt templates with Skills placeholders
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

        # Simple chat prompt
        self._prompts["chat_system"] = """
You are a helpful AI assistant.

{skill_context}

AVAILABLE TOOLS:
{tool_descriptions}

User: {query}
"""

        # ReAct prompt without tools
        self._prompts["react_no_tools"] = """
You are a reasoning agent.
{skill_context}

Think step by step about: {query}

Show your reasoning:
"""
    
    def get_prompt(self, name: str, **kwargs) -> str:
        """Get and format a prompt template"""
        template_str = self._prompts.get(name)
        if not template_str:
            logger.warning(f"Prompt template '{name}' not found.")
            return ""
        
        # Set defaults
        kwargs.setdefault('tool_descriptions', 'No tools available.')
        kwargs.setdefault('skill_context', '')
        kwargs.setdefault('context', 'No context.')
        kwargs.setdefault('query', '')
        
        try:
            return template_str.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing parameter for prompt '{name}': {e}")
            return template_str
    
    def get_prompt_with_skills(
        self,
        name: str,
        skill_names: List[str] = None,
        **kwargs
    ) -> str:
        """
        Get prompt with Skills integration.
        
        Args:
            name: Prompt template name
            skill_names: List of skill names to include, None for all
            **kwargs: Additional template variables
        """
        # Try to import Skills related modules
        try:
            from src.agents.skills.prompt_builder import get_skill_prompt_builder
            builder = get_skill_prompt_builder()
            
            # Get Skills tool descriptions and prompts
            tool_descriptions = builder.get_tool_descriptions(skill_names)
            skill_context = builder.get_skill_prompts(skill_names)
            
            kwargs.setdefault('tool_descriptions', tool_descriptions)
            kwargs.setdefault('skill_context', skill_context)
            
        except ImportError:
            # If Skills not installed, use defaults
            kwargs.setdefault('tool_descriptions', kwargs.get('tool_descriptions', 'No tools available.'))
            kwargs.setdefault('skill_context', '')
            logger.warning("Skills not available, using basic prompt.")
        
        return self.get_prompt(name, **kwargs)
    
    def get_tools_for_llm(self, skill_names: List[str] = None) -> List[Dict[str, Any]]:
        """
        Get tools in LLM-compatible format for Tool Calling.
        
        Returns:
            List of tool definitions compatible with OpenAI function calling
        """
        try:
            from src.agents.skills.prompt_builder import get_skill_prompt_builder
            builder = get_skill_prompt_builder()
            return builder.get_available_tools(skill_names)
        except ImportError:
            return []
    
    def update_prompt(self, name: str, template: str):
        """Update a prompt template dynamically (e.g. from config)"""
        self._prompts[name] = template
    
    def list_prompts(self) -> List[str]:
        """List all available prompt templates"""
        return list(self._prompts.keys())
    
    def add_prompt(self, name: str, template: str):
        """Add a new prompt template"""
        self._prompts[name] = template


# Global accessor
def get_prompt_manager() -> PromptManager:
    return PromptManager()
