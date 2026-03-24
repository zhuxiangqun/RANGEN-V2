"""
Reasoning Service Tests
Based on actual code: src/services/reasoning.py
"""
import pytest
from src.services.reasoning import (
    ReasoningService, ReasoningType, ReasoningStrategy,
    ReasoningStep, ReasoningResult, ReasoningEngine,
    DeductiveReasoningEngine, InductiveReasoningEngine,
    AbductiveReasoningEngine, CausalReasoningEngine,
    MultiHopReasoningEngine
)


class TestReasoningService:
    @pytest.fixture
    def reasoning_service(self):
        return ReasoningService()
    
    def test_can_be_instantiated(self, reasoning_service):
        assert reasoning_service is not None
    
    def test_has_reason_method(self, reasoning_service):
        assert hasattr(reasoning_service, 'reason')


class TestReasoningEnums:
    def test_reasoning_type_enum(self):
        assert ReasoningType.DEDUCTIVE == "deductive"
        assert ReasoningType.INDUCTIVE == "inductive"
        assert ReasoningType.MULTI_HOP == "multi_hop"
    
    def test_reasoning_strategy_enum(self):
        assert ReasoningStrategy.LOGICAL == "logical"
        assert ReasoningStrategy.PROBABILISTIC == "probabilistic"


class TestReasoningStep:
    def test_can_create_step(self):
        step = ReasoningStep(
            step_number=1,
            reasoning_type=ReasoningType.DEDUCTIVE,
            premise="All humans are mortal",
            conclusion="Socrates is mortal",
            confidence=0.95,
            evidence=["Socrates is a human"]
        )
        assert step.step_number == 1
        assert step.confidence == 0.95


class TestReasoningResult:
    def test_can_create_result(self):
        step = ReasoningStep(
            step_number=1,
            reasoning_type=ReasoningType.DEDUCTIVE,
            premise="test",
            conclusion="result",
            confidence=0.9,
            evidence=[]
        )
        result = ReasoningResult(
            reasoning_type=ReasoningType.DEDUCTIVE,
            conclusion="test conclusion",
            confidence=0.9,
            steps=[step],
            evidence=[],
            is_valid=True
        )
        assert result.is_valid == True
        assert result.confidence == 0.9


class TestDeductiveReasoningEngine:
    def test_can_be_instantiated(self):
        engine = DeductiveReasoningEngine()
        assert engine is not None
        assert engine.name == "deductive"
