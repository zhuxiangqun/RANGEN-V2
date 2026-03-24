"""
Intent Understanding Service Tests
Based on actual code: src/services/intent_understanding_service.py
"""
import pytest
from src.services.intent_understanding_service import (
    IntentUnderstandingService, IntentType, IntentResult
)


class TestIntentUnderstandingService:
    @pytest.fixture
    def intent_service(self):
        return IntentUnderstandingService()
    
    def test_can_be_instantiated(self, intent_service):
        assert intent_service is not None
    
    def test_has_understand_method(self, intent_service):
        assert hasattr(intent_service, 'understand')


class TestIntentEnums:
    def test_intent_type_enum(self):
        assert IntentType.QUERY.value == "query"
        assert IntentType.ACTION.value == "action"
        assert IntentType.CREATION.value == "creation"
        assert IntentType.DIAGNOSIS.value == "diagnosis"


class TestIntentResult:
    def test_can_create_result(self):
        result = IntentResult(
            intent=IntentType.QUERY,
            confidence=0.95,
            entities={"key": "value"}
        )
        assert result.intent == IntentType.QUERY
        assert result.confidence == 0.95
