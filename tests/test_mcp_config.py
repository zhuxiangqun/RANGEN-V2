"""
MCP Config Service Tests
Based on actual code: src/services/mcp_config_service.py
"""
import pytest
from src.services.mcp_config_service import (
    MCPConfigService, MCPServerConfig
)


class TestMCPConfigService:
    def test_has_load_config_method(self):
        service = MCPConfigService.__new__(MCPConfigService)
        assert hasattr(service, 'load_config')


class TestMCPConfig:
    def test_can_create_server_config(self):
        config = MCPServerConfig(
            name="test_server",
            description="Test MCP server"
        )
        assert config.name == "test_server"
        assert config.enabled == True
