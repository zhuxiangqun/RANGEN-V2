"""
Agent-Skill Mapping
==================
Maps RANGEN agents to their corresponding skills.
"""

from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Agent to Skills mapping
AGENT_SKILL_MAPPING = {
    "rag_agent": [
        "rag-retrieval",
        "query-analysis", 
        "knowledge-graph",
        "answer-generation",
    ],
    "reasoning_agent": [
        "reasoning-chain",
        "query-analysis",
        "tool-execution",
    ],
    "retrieval_agent": [
        "rag-retrieval",
        "query-analysis",
        "web-search",
    ],
    "citation_agent": [
        "citation-generation",
        "fact-check",
    ],
    "validation_agent": [
        "validation",
        "quality-control",
        "security-validation",
    ],
    "expert_agent": [
        "research-workflow",
        "fact-check",
        "summarization",
    ],
    "chief_agent": [
        "multi-agent-coordination",
        "context-management",
        "session-management",
    ],
    # Additional Agents
    "react_agent": [
        "reasoning-chain",
        "tool-execution",
        "query-analysis",
    ],
    "security_guardian": [
        "security-validation",
        "validation",
    ],
    "quality_controller": [
        "quality-control",
        "validation",
        "fact-check",
    ],
    "learning_optimizer": [
        "performance-optimization",
        "tool-execution",
    ],
    "memory_manager": [
        "context-management",
        "session-management",
    ],
    "execution_coordinator": [
        "multi-agent-coordination",
        "tool-execution",
    ],
}


# Skills to Tools mapping
SKILL_TOOL_MAPPING = {
    "rag-retrieval": ["rag_tool", "knowledge_retrieval"],
    "query-analysis": ["search"],
    "knowledge-graph": ["knowledge_retrieval"],
    "answer-generation": ["answer_generation"],
    "citation-generation": ["citation"],
    "reasoning-chain": ["reasoning"],
    "web-search": ["search"],
    "fact-check": ["search"],
    "research-workflow": ["search", "reasoning"],
    "tool-execution": ["calculator", "multimodal"],
}


def get_skills_for_agent(agent_name: str) -> List[str]:
    """Get skills for a specific agent."""
    return AGENT_SKILL_MAPPING.get(agent_name, [])


def get_tools_for_skill(skill_name: str) -> List[str]:
    """Get tools for a specific skill."""
    return SKILL_TOOL_MAPPING.get(skill_name, [])


def get_agent_skill_tool_chain(agent_name: str) -> Dict[str, List[str]]:
    """Get complete chain: Agent -> Skills -> Tools."""
    skills = get_skills_for_agent(agent_name)
    tools = []
    for skill in skills:
        tools.extend(get_tools_for_skill(skill))
    
    return {
        "agent": agent_name,
        "skills": skills,
        "tools": list(set(tools)),  # Remove duplicates
    }


def list_all_agents() -> List[str]:
    """List all agents with skill mappings."""
    return list(AGENT_SKILL_MAPPING.keys())


# Print mapping summary
def print_agent_skill_summary():
    """Print summary of agent-skill-tool chain."""
    logger.info("=" * 70)
    logger.info("Agent -> Skills -> Tools Mapping")
    logger.info("=" * 70)
    
    for agent in list_all_agents():
        chain = get_agent_skill_tool_chain(agent)
        logger.info(f"{agent}: Skills={chain['skills']}, Tools={chain['tools']}")
    
    logger.info("=" * 70)


if __name__ == "__main__":
    print_agent_skill_summary()
