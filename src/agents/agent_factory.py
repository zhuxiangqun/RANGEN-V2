"""
Agent Factory with Skills Auto-Injection
======================================
Creates agents with automatic skills and tools injection.
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from src.agents.skills import SkillRegistry, SkillScope, get_skill_registry
from src.agents.tools import ToolRegistry, get_tool_registry
from src.agents.tools.tool_initializer import register_all_tools
from src.agents.workspace import AgentWorkspace, WorkspaceManager
from src.agents.agent_skill_mapping import get_skills_for_agent, get_tools_for_skill
from src.config.unified import get_config
from src.services.logging_service import get_logger

logger = get_logger(__name__)
from src.services.logging_service import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory for creating agents with automatic skills and tools injection.
    
    Usage:
        factory = AgentFactory()
        agent = factory.create_agent("rag_agent", workspace=ws)
    """
    
    def __init__(self, auto_register_tools: bool = True):
        self._skill_registry: Optional[SkillRegistry] = None
        self._tool_registry: Optional[ToolRegistry] = None
        self._workspace_manager: Optional[WorkspaceManager] = None
        
        if auto_register_tools:
            self._init_registries()
    
    def _init_registries(self):
        """Initialize registries."""
        # Skills
        try:
            self._skill_registry = get_skill_registry()
            logger.info(f"Loaded {len(self._skill_registry.list_skills())} skills")
        except Exception as e:
            logger.warning(f"Failed to load skill registry: {e}")
            self._skill_registry = SkillRegistry()
        
        # Tools
        try:
            self._tool_registry = get_tool_registry()
            register_all_tools(self._tool_registry)
            logger.info(f"Registered {len(self._tool_registry.list_tools())} tools")
        except Exception as e:
            logger.warning(f"Failed to register tools: {e}")
            self._tool_registry = ToolRegistry()
    
    @property
    def skill_registry(self) -> SkillRegistry:
        """Get skill registry."""
        if self._skill_registry is None:
            self._skill_registry = get_skill_registry()
        return self._skill_registry
    
    @property
    def tool_registry(self) -> ToolRegistry:
        """Get tool registry."""
        if self._tool_registry is None:
            self._tool_registry = get_tool_registry()
            register_all_tools(self._tool_registry)
        return self._tool_registry
    
    @property
    def workspace_manager(self) -> WorkspaceManager:
        """Get workspace manager."""
        if self._workspace_manager is None:
            self._workspace_manager = WorkspaceManager()
        return self._workspace_manager
    
    def get_skills_for_agent(self, agent_name: str) -> List[Any]:
        """Get enabled skills for an agent."""
        skill_names = get_skills_for_agent(agent_name)
        skills = []
        
        for name in skill_names:
            skill = self.skill_registry.get_skill(name)
            if skill:
                skills.append(skill)
            else:
                logger.warning(f"Skill not found: {name}")
        
        return skills
    
    def get_tools_for_agent(self, agent_name: str) -> List[Any]:
        """Get enabled tools for an agent."""
        skill_names = get_skills_for_agent(agent_name)
        tool_names = set()
        
        for skill_name in skill_names:
            tools = get_tools_for_skill(skill_name)
            tool_names.update(tools)
        
        tools = []
        for name in tool_names:
            tool = self.tool_registry.get_tool(name)
            if tool:
                tools.append(tool)
        
        return tools
    
    def create_agent_config(self, agent_name: str, workspace: Optional[AgentWorkspace] = None) -> Dict[str, Any]:
        """Create agent configuration with skills and tools."""
        skills = self.get_skills_for_agent(agent_name)
        tools = self.get_tools_for_agent(agent_name)
        
        config = {
            "agent_name": agent_name,
            "skills": skills,
            "skill_names": [s.name for s in skills],
            "tools": tools,
            "tool_names": [t.name if hasattr(t, 'name') else str(t) for t in tools],
            "workspace": workspace,
        }
        
        logger.info(f"Created config for {agent_name}: {len(skills)} skills, {len(tools)} tools")
        
        return config
    
    def list_available_agents(self) -> List[str]:
        """List all agents that can be created."""
        from src.agents.agent_skill_mapping import AGENT_SKILL_MAPPING
        return list(AGENT_SKILL_MAPPING.keys())


# Global factory instance
_agent_factory: Optional[AgentFactory] = None


def get_agent_factory() -> AgentFactory:
    """Get global agent factory instance."""
    global _agent_factory
    if _agent_factory is None:
        _agent_factory = AgentFactory()
    return _agent_factory


def create_agent_with_skills(
    agent_name: str,
    workspace: Optional[AgentWorkspace] = None,
    custom_skills: Optional[List[str]] = None,
    custom_tools: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to create agent with skills and tools.
    
    Returns:
        Dict with 'skills', 'tools', and 'config' keys
    """
    factory = get_agent_factory()
    
    # Get base config
    config = factory.create_agent_config(agent_name, workspace)
    
    # Add custom skills if provided
    if custom_skills:
        for skill_name in custom_skills:
            skill = factory.skill_registry.get_skill(skill_name)
            if skill and skill not in config['skills']:
                config['skills'].append(skill)
                config['skill_names'].append(skill_name)
    
    # Add custom tools if provided
    if custom_tools:
        for tool_name in custom_tools:
            tool = factory.tool_registry.get_tool(tool_name)
            if tool and tool not in config['tools']:
                config['tools'].append(tool)
                config['tool_names'].append(tool_name)
    
    return config


# Example usage
if __name__ == "__main__":
    factory = get_agent_factory()
    
    logger.info("=" * 70)
    logger.info("Agent Factory - Available Agents")
    logger.info("=" * 70)
    
    for agent_name in factory.list_available_agents():
        config = factory.create_agent_config(agent_name)
        logger.info(f"{agent_name}: Skills={len(config['skills'])}, Tools={len(config['tools'])}")
    
    logger.info("=" * 70)
if __name__ == "__main__":
    factory = get_agent_factory()
    
    print("=" * 70)
    print("Agent Factory - Available Agents")
    print("=" * 70)
    
    for agent_name in factory.list_available_agents():
        config = factory.create_agent_config(agent_name)
        print(f"\n{agent_name}:")
        print(f"  Skills: {len(config['skills'])} - {config['skill_names']}")
        print(f"  Tools:  {len(config['tools'])} - {config['tool_names']}")
    
    print("\n" + "=" * 70)
