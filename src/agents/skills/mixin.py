"""
Skills Integration Mixin
========================
Mixin class to add Skills support to existing agents.

Usage:
    from src.agents.skills.mixin import SkillsMixin
    
    class MyAgent(ExpertAgent, SkillsMixin):
        def __init__(self, ...):
            super().__init__(...)
            self.init_skills()  # Initialize skills
"""

from typing import List, Dict, Any, Optional
import logging

from src.agents.skills import SkillRegistry, get_skill_registry
from src.agents.agent_skill_mapping import get_skills_for_agent

logger = logging.getLogger(__name__)


class SkillsMixin:
    """
    Mixin to add Skills support to existing agents.
    
    Usage:
        class MyAgent(ExpertAgent, SkillsMixin):
            def __init__(self, agent_name: str, ...):
                super().__init__(...)
                self.init_skills(agent_name)
    """
    
    def init_skills(self, agent_name: str, custom_skills: Optional[List[str]] = None) -> None:
        """
        Initialize skills for this agent.
        
        Args:
            agent_name: Name of the agent (for mapping)
            custom_skills: Optional custom skills list
        """
        self._skills_enabled = True
        self._agent_name = agent_name
        
        # Get skills from mapping or use custom
        if custom_skills:
            skill_names = custom_skills
        else:
            skill_names = get_skills_for_agent(agent_name)
        
        # Load skills from registry
        registry = get_skill_registry()
        self._skills = []
        
        for name in skill_names:
            skill = registry.get_skill(name)
            if skill:
                self._skills.append(skill)
            else:
                logger.warning("Skill not found: %s", name)
        
        logger.info("%s initialized with %d skills", agent_name, len(self._skills))
    
    def get_skills(self) -> List[Any]:
        """Get all enabled skills."""
        return getattr(self, '_skills', [])
    
    def get_skill_prompt_context(self) -> str:
        """Get combined prompt context from all skills."""
        contexts = []
        for skill in self.get_skills():
            if hasattr(skill, 'prompt_template') and skill.prompt_template:
                contexts.append(skill.prompt_template)
        
        return "\n\n".join(contexts)
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if agent has a specific skill."""
        for skill in self.get_skills():
            if skill.name == skill_name:
                return True
        return False
    
    async def execute_with_skills(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with skills enabled."""
        results = {
            "success": True,
            "skill_results": [],
            "final_result": None
        }
        
        # Execute each skill that can handle the context
        for skill in self.get_skills():
            try:
                result = await skill.execute(context)
                results["skill_results"].append({
                    "skill": skill.name,
                    "result": result
                })
            except Exception as e:
                logger.error("Skill %s failed: %s", skill.name, str(e))
                results["skill_results"].append({
                    "skill": skill.name,
                    "error": str(e)
                })
        
        return results


# Example usage function
def add_skills_to_agent(agent: Any, agent_name: str) -> None:
    """
    Helper function to add Skills to an existing agent instance.
    
    Args:
        agent: Agent instance
        agent_name: Name of the agent for skill mapping
    """
    if hasattr(agent, 'init_skills'):
        agent.init_skills(agent_name)
        logger.info("Added skills to %s", agent_name)
    else:
        logger.warning("Agent %s does not support SkillsMixin", agent_name)


__all__ = ['SkillsMixin', 'add_skills_to_agent']
