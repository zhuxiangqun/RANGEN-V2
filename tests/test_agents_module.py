"""
Agent Module Tests
Based on actual code: src/agents/
"""
import pytest


class TestAgents:
    def test_agent_builder_exists(self):
        from src.agents.agent_builder import AgentBuilder
        assert AgentBuilder is not None
    
    def test_agent_models_exists(self):
        from src.agents.agent_models import AgentConfig
        assert AgentConfig is not None
