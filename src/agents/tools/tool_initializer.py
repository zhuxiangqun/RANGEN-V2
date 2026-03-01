"""
Tool Registration Utility
========================
Auto-register existing RANGEN tools to ToolRegistry.
"""

from typing import Dict, Any, Optional
from src.agents.tools import (
    RAGTool, SearchTool, CalculatorTool, KnowledgeRetrievalTool,
    ReasoningTool, AnswerGenerationTool, CitationTool, MultimodalTool,
    BrowserTool, ToolRegistry, get_tool_registry
)
from src.agents.tools.real_search_tool import RealSearchTool, BingSearchTool
from src.agents.tools.web_search_tool import WebSearchTool
from src.agents.tools.file_hand_tool import FileReadHandTool
from src.services.logging_service import get_logger

logger = get_logger(__name__)


TOOL_SKILL_MAPPING = {
    "rag_tool": ["rag-retrieval", "query-analysis"],
    "knowledge_retrieval": ["rag-retrieval", "knowledge-graph"],
    "search": ["web-search", "research-workflow"],
    "web_search": ["web-search", "research-workflow", "duckduckgo"],
    "real_search": ["web-search", "research-workflow", "real-time-search"],
    "reasoning": ["reasoning-chain"],
    "answer_generation": ["answer-generation", "citation-generation"],
    "citation": ["citation-generation", "fact-check"],
    "calculator": [],
    "multimodal": [],
    "browser": ["browser-automation", "web-scraping"],
    "file_read": ["file-operation", "hands"],
}


def get_all_tools() -> Dict[str, Any]:
    """Get all available tool instances (including Hands-backed file_read)."""
    return {
        "rag_tool": RAGTool(),
        "knowledge_retrieval": KnowledgeRetrievalTool(),
        "search": SearchTool(),
        "web_search": WebSearchTool(),
        "real_search": RealSearchTool(),
        "reasoning": ReasoningTool(),
        "answer_generation": AnswerGenerationTool(),
        "citation": CitationTool(),
        "calculator": CalculatorTool(),
        "multimodal": MultimodalTool(),
        "browser": BrowserTool(),
        "file_read": FileReadHandTool(),
    }


def register_all_tools(registry: Optional[ToolRegistry] = None) -> ToolRegistry:
    """Register all RANGEN tools to the registry."""
    if registry is None:
        registry = get_tool_registry()
    
    tools = get_all_tools()
    
    for tool_name, tool_instance in tools.items():
        try:
            registry.register_tool(tool_instance)
            logger.info(f"Registered tool: {tool_name}")
        except Exception as e:
            logger.warning(f"Failed to register {tool_name}: {e}")
    
    return registry


def get_tools_for_skill(skill_name: str, registry: Optional[ToolRegistry] = None) -> list:
    """Get tools associated with a specific skill."""
    if registry is None:
        registry = get_tool_registry()
    
    associated_tools = []
    for tool_name, skills in TOOL_SKILL_MAPPING.items():
        if skill_name in skills:
            tool = registry.get_tool(tool_name)
            if tool:
                associated_tools.append(tool)
    
    return associated_tools


def initialize_tools() -> ToolRegistry:
    """Initialize and register all tools. Call this at system startup."""
    logger.info("Initializing RANGEN tools...")
    registry = register_all_tools()
    logger.info(f"Registered {len(registry.list_tools())} tools total")
    return registry


# Auto-initialize on import
try:
    _initialized_registry = initialize_tools()
except Exception as e:
    logger.warning(f"Failed to auto-initialize tools: {e}")
    _initialized_registry = None
