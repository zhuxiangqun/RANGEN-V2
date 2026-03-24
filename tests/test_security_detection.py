"""
Security Detection Service Tests
Based on actual code: src/services/security_detection_service.py
"""
import pytest
from src.services.security_detection_service import (
    SecurityDetectionService, ThreatType, ThreatIndicator
)


class TestSecurityDetectionService:
    def test_has_detect_method(self):
        service = SecurityDetectionService.__new__(SecurityDetectionService)
        assert hasattr(service, 'detect')


class TestThreatEnums:
    def test_threat_type_enum(self):
        assert ThreatType.BRUTE_FORCE_ATTACK.value == "brute_force_attack"
        assert ThreatType.SUSPICIOUS_ACTIVITY.value == "suspicious_activity"
