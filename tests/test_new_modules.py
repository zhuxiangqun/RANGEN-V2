"""
Tests for RANGEN V2 New Modules
================================
Tests for Skills, Workspace, AgentFactory, and dependency resolver.
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestSkillsSystem:
    """Test Skills system."""
    
    def test_skill_registry_import(self):
        """Test SkillRegistry can be imported."""
        from agents.skills import SkillRegistry
        assert SkillRegistry is not None
    
    def test_skill_registry_creation(self):
        """Test SkillRegistry can be created."""
        from agents.skills import SkillRegistry
        registry = SkillRegistry()
        assert registry is not None
    
    def test_list_skills(self):
        """Test listing bundled skills."""
        from agents.skills import SkillRegistry, SkillScope
        registry = SkillRegistry()
        skills = registry.list_skills(SkillScope.BUNDLED)
        assert len(skills) > 0
    
    def test_get_skill(self):
        """Test getting a specific skill."""
        from agents.skills import SkillRegistry
        registry = SkillRegistry()
        skill = registry.get_skill("rag-retrieval")
        assert skill is not None
    
    def test_skill_prompt_template(self):
        """Test skill has prompt template."""
        from agents.skills import SkillRegistry
        registry = SkillRegistry()
        skill = registry.get_skill("rag-retrieval")
        assert skill is not None
        assert len(skill.prompt_template) > 0
    
    def test_skill_execution(self):
        """Test skill can execute."""
        import asyncio
        from agents.skills import SkillRegistry
        
        async def run():
            registry = SkillRegistry()
            skill = registry.get_skill("rag-retrieval")
            result = await skill.execute({"query": "test"})
            return result
        
        result = asyncio.run(run())
        assert result.get("success") is True


class TestWorkspaceSystem:
    """Test Workspace isolation system."""
    
    def test_workspace_import(self):
        """Test Workspace can be imported."""
        from agents.workspace import AgentWorkspace
        assert AgentWorkspace is not None
    
    def test_workspace_creation(self):
        """Test Workspace can be created."""
        from agents.workspace import AgentWorkspace
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = AgentWorkspace("test-ws", tmpdir)
            assert ws.workspace_id == "test-ws"
            ws.cleanup()
    
    def test_workspace_state(self):
        """Test workspace state management."""
        from agents.workspace import AgentWorkspace
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ws = AgentWorkspace("test-ws", tmpdir)
            ws.state["key"] = "value"
            assert ws.state["key"] == "value"
            ws.cleanup()
    
    def test_workspace_isolation(self):
        """Test workspace isolation."""
        from agents.workspace import AgentWorkspace
        import tempfile
        
        with tempfile.TemporaryDirectory() as tmpdir:
            ws1 = AgentWorkspace("ws1", tmpdir)
            ws2 = AgentWorkspace("ws2", tmpdir)
            
            ws1.state["data"] = "ws1"
            ws2.state["data"] = "ws2"
            
            assert ws1.state["data"] != ws2.state["data"]
            
            ws1.cleanup()
            ws2.cleanup()


class TestAgentMapping:
    """Test Agent-Skill mapping."""
    
    def test_mapping_import(self):
        """Test mapping can be imported."""
        from agents.agent_skill_mapping import AGENT_SKILL_MAPPING
        assert AGENT_SKILL_MAPPING is not None
    
    def test_mapping_count(self):
        """Test mapping has agents."""
        from agents.agent_skill_mapping import AGENT_SKILL_MAPPING
        assert len(AGENT_SKILL_MAPPING) > 0
    
    def test_rag_agent_mapping(self):
        """Test rag_agent has skills."""
        from agents.agent_skill_mapping import get_skills_for_agent
        skills = get_skills_for_agent("rag_agent")
        assert len(skills) > 0
        assert "rag-retrieval" in skills
    
    def test_tool_mapping(self):
        """Test tool mapping works."""
        from agents.agent_skill_mapping import get_tools_for_skill
        tools = get_tools_for_skill("rag-retrieval")
        assert len(tools) > 0


class TestAgentFactory:
    """Test Agent Factory."""
    
    def test_factory_import(self):
        """Test factory can be imported."""
        from agents.agent_factory import get_agent_factory
        assert get_agent_factory is not None
    
    def test_factory_creation(self):
        """Test factory can be created."""
        from agents.agent_factory import AgentFactory
        factory = AgentFactory(auto_register_tools=False)
        assert factory is not None
    
    def test_list_agents(self):
        """Test listing available agents."""
        from agents.agent_factory import get_agent_factory
        factory = get_agent_factory()
        agents = factory.list_available_agents()
        assert len(agents) > 0
    
    def test_create_agent_config(self):
        """Test creating agent config."""
        from agents.agent_factory import get_agent_factory
        factory = get_agent_factory()
        config = factory.create_agent_config("rag_agent")
        assert "skills" in config
        assert "tools" in config


class TestSkillsDependencyResolver:
    """Test Skills Dependency Resolver."""
    
    def test_resolver_import(self):
        """Test resolver can be imported."""
        from agents.skills.dependency_resolver import get_skills_resolver
        assert get_skills_resolver is not None
    
    def test_resolve_skills(self):
        """Test resolving skills with dependencies."""
        from agents.skills.dependency_resolver import get_skills_resolver
        resolver = get_skills_resolver()
        resolved = resolver.resolve_skills(["answer-generation"])
        assert "rag-retrieval" in resolved
        assert "answer-generation" in resolved
    
    def test_validate_dependencies(self):
        """Test validating dependencies."""
        from agents.skills.dependency_resolver import get_skills_resolver
        resolver = get_skills_resolver()
        validation = resolver.validate_dependencies(["answer-generation"])
        assert validation["valid"] is True


class TestUnifiedConfig:
    """Test Unified Config."""
    
    def test_config_import(self):
        """Test config can be imported."""
        from config.unified import UnifiedConfig
        assert UnifiedConfig is not None
    
    def test_config_creation(self):
        """Test config can be created."""
        from config.unified import UnifiedConfig
        config = UnifiedConfig()
        assert config is not None
    
    def test_config_load(self):
        """Test config can load."""
        from config.unified import UnifiedConfig
        config = UnifiedConfig()
        config.load("development")
        assert config.environment == "development"


class TestToolRegistration:
    """Test Tool Registration."""
    
    def test_tool_initializer_import(self):
        """Test tool initializer can be imported."""
        from agents.tools.tool_initializer import get_all_tools
        assert get_all_tools is not None
    
    def test_get_all_tools(self):
        """Test getting all tools."""
        from agents.tools.tool_initializer import get_all_tools
        tools = get_all_tools()
        assert len(tools) > 0
    
    def test_register_tools(self):
        """Test registering tools."""
        from agents.tools import ToolRegistry
        from agents.tools.tool_initializer import register_all_tools
        
        registry = ToolRegistry()
        register_all_tools(registry)
        
        tools = registry.list_tools()
        assert len(tools) > 0


class TestUnifiedErrors:
    """Test Unified Error Handling."""
    
    def test_unified_errors_import(self):
        """Test unified errors can be imported."""
        from utils.unified_errors import RangenError, ErrorCode
        assert RangenError is not None
        assert ErrorCode is not None
    
    def test_create_rangen_error(self):
        """Test creating RANGEN error."""
        from utils.unified_errors import RangenError, ErrorCode
        error = RangenError("Test error", code=ErrorCode.UNKNOWN)
        assert str(error) is not None
    
    def test_error_handler(self):
        """Test error handler."""
        from utils.unified_errors import get_error_handler
        handler = get_error_handler()
        assert handler is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
