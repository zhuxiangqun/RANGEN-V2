"""
Security Service Tests
Based on actual code: src/services/security.py
"""
import pytest
from src.services.security import (
    SecurityService, SecurityLevel, ThreatType,
    DangerLevel, AuditEventType, AuditSeverity, AuditEvent
)


class TestSecurityService:
    @pytest.fixture
    def security_service(self):
        return SecurityService()
    
    def test_can_be_instantiated(self, security_service):
        assert security_service is not None
    
    def test_has_check_request_method(self, security_service):
        assert hasattr(security_service, 'check_request')


class TestSecurityEnums:
    def test_security_level_enum(self):
        assert SecurityLevel.LOW == "low"
        assert SecurityLevel.HIGH == "high"
    
    def test_threat_type_enum(self):
        assert ThreatType.INJECTION == "injection"
        assert ThreatType.XSS == "xss"
    
    def test_danger_level_enum(self):
        assert DangerLevel.SAFE == "safe"
        assert DangerLevel.HIGH == "high"


class TestAuditEvent:
    def test_can_create_audit_event(self):
        event = AuditEvent(
            event_type=AuditEventType.LOGIN,
            severity=AuditSeverity.INFO,
            source="web",
            user="user123",
            action="login",
            result="success",
            timestamp=1234567890.0
        )
        assert event.event_type == AuditEventType.LOGIN
        assert event.user == "user123"
