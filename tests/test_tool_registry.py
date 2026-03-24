"""
Tool Registry Tests
Based on actual code: src/services/tool_registry.py
"""
import pytest
from unittest.mock import MagicMock, patch
from src.services.tool_registry import ToolRegistry


class TestToolRegistry:
    @pytest.fixture
    def tool_registry(self):
        with patch('src.services.tool_registry.get_database'):
            return ToolRegistry()
    
    def test_can_be_instantiated(self, tool_registry):
        assert tool_registry is not None
    
    def test_has_discover_tools_method(self, tool_registry):
        assert hasattr(tool_registry, 'discover_tools')


class TestToolRegistryMethods:
    def test_has_sync_tools_method(self):
        registry = ToolRegistry.__new__(ToolRegistry)
        assert hasattr(registry, 'sync_tools')
