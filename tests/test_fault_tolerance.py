"""
Fault Tolerance Service Tests
Based on actual code: src/services/fault_tolerance_service.py
"""
import pytest
from src.services.fault_tolerance_service import (
    FaultToleranceService, ModelPriority, FailureType
)


class TestFaultToleranceService:
    def test_has_execute_with_fallback_method(self):
        service = FaultToleranceService.__new__(FaultToleranceService)
        assert hasattr(service, 'execute_with_fallback')


class TestFaultToleranceEnums:
    def test_model_priority_enum(self):
        assert ModelPriority.PRIMARY.value == "primary"
        assert ModelPriority.SECONDARY.value == "secondary"
        assert ModelPriority.FALLBACK.value == "fallback"
    
    def test_failure_type_enum(self):
        assert FailureType.TIMEOUT.value == "timeout"
        assert FailureType.RATE_LIMIT.value == "rate_limit"
