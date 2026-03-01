"""
SkillsAwareAgent
==============
Base agent class with Skills, Prompt, and Workspace integration.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import asyncio

from src.agents.skills import get_skill_registry, SkillScope
from src.agents.skills.prompt_builder import get_skill_prompt_builder, PromptContext
from src.agents.workspace import AgentWorkspace
from src.prompts.prompt_manager import get_prompt_manager
from src.config.unified import get_config


class SkillsAwareAgent(ABC):
    """
    Base agent class that integrates Skills, Prompt Engineering, and Workspace.
    
    Features:
    - Dynamic prompt generation from Skills
    - Workspace isolation
    - Tool calling support
    - Session context management
    """
    
    def __init__(
        self,
        agent_id: str,
        workspace: Optional[AgentWorkspace] = None,
        enabled_skills: Optional[List[str]] = None,
        prompt_template: str = "reasoning_agent_system"
    ):
        self.agent_id = agent_id
        self.workspace = workspace
        self.enabled_skills = enabled_skills or []
        self.prompt_template = prompt_template
        
        # Initialize components
        self.config = get_config()
        self.skill_registry = get_skill_registry()
        self.prompt_builder = get_skill_prompt_builder()
        self.prompt_manager = get_prompt_manager()
        
        # State
        self._is_initialized = False
    
    async def initialize(self):
        """Initialize agent resources"""
        if self._is_initialized:
            return
        
        # Load enabled skills
        for skill_name in self.enabled_skills:
            skill = self.skill_registry.get_skill(skill_name)
            if not skill:
                # Try to load from path
                self.skill_registry.load_skill_from_path(
                    f"./skills/{skill_name}",
                    SkillScope.WORKSPACE
                )
        
        self._is_initialized = True
    
    def build_system_prompt(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Build system prompt with Skills integration.
        
        Args:
            query: User query
            context: Optional additional context
            
        Returns:
            Formatted system prompt
        """
        # Build prompt context
        prompt_context = PromptContext(
            query=query,
            workspace_id=self.workspace.workspace_id if self.workspace else "",
            enabled_skills=self.enabled_skills,
            history=context.get("history", []) if context else []
        )
        
        # Get base template
        base_prompt = self.prompt_manager.get_prompt(self.prompt_template)
        
        # Build with Skills
        return self.prompt_builder.build_system_prompt(base_prompt, prompt_context)
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        Get available tools from Skills in LLM-compatible format.
        
        Returns:
            List of tool definitions for Tool Calling
        """
        return self.prompt_builder.get_available_tools(self.enabled_skills)
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute agent with given query.
        
        Args:
            query: User query
            context: Optional execution context
            
        Returns:
            Execution result
        """
        if not self._is_initialized:
            await self.initialize()
        
        # Build prompt
        system_prompt = self.build_system_prompt(query, context)
        
        # Get tools
        tools = self.get_available_tools()
        
        # Execute with LLM (to be implemented by subclass)
        result = await self._execute_with_llm(
            query=query,
            system_prompt=system_prompt,
            tools=tools,
            context=context or {}
        )
        
        # Update workspace if available
        if self.workspace:
            self.workspace.add_memory({
                "role": "user",
                "content": query
            })
            self.workspace.add_memory({
                "role": "assistant",
                "content": result.get("response", "")
            })
        
        return result
    
    @abstractmethod
    async def _execute_with_llm(
        self,
        query: str,
        system_prompt: str,
        tools: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Internal method to execute with LLM.
        Must be implemented by subclass.
        
        Args:
            query: User query
            system_prompt: Built system prompt
            tools: Available tools
            context: Execution context
            
        Returns:
            LLM response
        """
        pass
    
    def add_skill(self, skill_name: str):
        """Enable a skill for this agent"""
        if skill_name not in self.enabled_skills:
            self.enabled_skills.append(skill_name)
    
    def remove_skill(self, skill_name: str):
        """Disable a skill for this agent"""
        if skill_name in self.enabled_skills:
            self.enabled_skills.remove(skill_name)
    
    def list_enabled_skills(self) -> List[str]:
        """List enabled skills"""
        return self.enabled_skills.copy()
    
    def __repr__(self) -> str:
        return f"SkillsAwareAgent(id={self.agent_id}, skills={self.enabled_skills}, workspace={self.workspace.workspace_id if self.workspace else None})"


class SimpleSkillsAgent(SkillsAwareAgent):
    """
    Simple implementation of SkillsAwareAgent for testing.
    Uses mock LLM responses.
    """
    
    async def _execute_with_llm(
        self,
        query: str,
        system_prompt: str,
        tools: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Mock response for testing
        return {
            "response": f"Mock response for: {query}",
            "system_prompt": system_prompt[:100] + "...",
            "tools_used": len(tools),
            "workspace_id": self.workspace.workspace_id if self.workspace else None
        }
