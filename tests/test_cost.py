"""
Cost Service Tests
Based on actual code: src/services/cost.py
"""
import pytest
from src.services.cost import (
    CostService, LLMProvider, CostAlertLevel,
    TokenUsage, CostRecord, BudgetLimit, CostAlert
)


class TestCostService:
    @pytest.fixture
    def cost_service(self):
        return CostService()
    
    def test_can_be_instantiated(self, cost_service):
        assert cost_service is not None
    
    def test_has_track_usage_method(self, cost_service):
        assert hasattr(cost_service, 'track_usage')


class TestCostEnums:
    def test_llm_provider_enum(self):
        assert LLMProvider.DEEPSEEK == "deepseek"
        assert LLMProvider.OPENAI == "openai"
    
    def test_cost_alert_level_enum(self):
        assert CostAlertLevel.INFO == "info"
        assert CostAlertLevel.WARNING == "warning"
        assert CostAlertLevel.CRITICAL == "critical"


class TestTokenUsage:
    def test_can_create_token_usage(self):
        usage = TokenUsage(
            provider=LLMProvider.DEEPSEEK,
            model="deepseek-chat",
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            timestamp=1234567890.0
        )
        assert usage.provider == LLMProvider.DEEPSEEK
        assert usage.total_tokens == 150


class TestCostRecord:
    def test_can_create_cost_record(self):
        record = CostRecord(
            provider=LLMProvider.DEEPSEEK,
            model="deepseek-chat",
            input_cost=0.001,
            output_cost=0.002,
            total_cost=0.003,
            tokens=150,
            timestamp=1234567890.0
        )
        assert record.total_cost == 0.003
        assert record.tokens == 150
