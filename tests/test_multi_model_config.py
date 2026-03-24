"""
Multi-Model Config Service Tests
Based on actual code: src/services/multi_model_config_service.py
"""
import pytest
from src.services.multi_model_config_service import (
    MultiModelConfigService, ModelProvider, RoutingStrategy
)


class TestMultiModelConfigService:
    def test_has_get_model_config_method(self):
        service = MultiModelConfigService.__new__(MultiModelConfigService)
        assert hasattr(service, 'get_model_config')


class TestMultiModelEnums:
    def test_model_provider_enum(self):
        assert ModelProvider.DEEPSEEK.value == "deepseek"
        assert ModelProvider.OPENAI.value == "openai"
    
    def test_routing_strategy_enum(self):
        assert RoutingStrategy.COST_FIRST.value == "cost_first"
        assert RoutingStrategy.PERFORMANCE_FIRST.value == "performance_first"
