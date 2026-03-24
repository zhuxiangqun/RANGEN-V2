"""
Routing Service Tests
Based on actual code: src/services/routing.py
"""
import pytest
from src.services.routing import (
    ModelRouter, TaskType, ModelProvider, 
    RoutingStrategy, ModelStatus, RoutingDecision, ModelConfig
)


class TestModelRouter:
    @pytest.fixture
    def router(self):
        return ModelRouter()
    
    def test_can_be_instantiated(self, router):
        assert router is not None
    
    def test_has_select_model_method(self, router):
        assert hasattr(router, 'select_model')


class TestEnums:
    def test_task_type_enum(self):
        assert TaskType.SIMPLE == "simple"
        assert TaskType.COMPLEX == "complex"
        assert TaskType.REASONING == "reasoning"
    
    def test_model_provider_enum(self):
        assert ModelProvider.DEEPSEEK == "deepseek"
        assert ModelProvider.OPENAI == "openai"
    
    def test_routing_strategy_enum(self):
        assert RoutingStrategy.COST_FIRST == "cost_first"
        assert RoutingStrategy.BALANCED == "balanced"


class TestRoutingDecision:
    def test_can_create_decision(self):
        config = ModelConfig(
            provider=ModelProvider.OPENAI,
            model_name="gpt-4",
            max_tokens=4096,
            temperature=0.7,
            cost_per_1k_input=0.03,
            cost_per_1k_output=0.06,
            capabilities=["chat", "code"],
            avg_latency=2.0
        )
        decision = RoutingDecision(
            model=config,
            strategy=RoutingStrategy.BALANCED,
            reason="Best match",
            confidence=0.9
        )
        assert decision.confidence == 0.9
        assert decision.strategy == RoutingStrategy.BALANCED
