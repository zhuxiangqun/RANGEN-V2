"""
Audit Log Service Tests
Based on actual code: src/services/audit_log_service.py
"""
import pytest
from src.services.audit_log_service import (
    AuditLogger, AuditEventType, AuditSeverity, AuditSource, AuditEvent
)


class TestAuditLogger:
    def test_has_log_event_method(self):
        logger = AuditLogger.__new__(AuditLogger)
        assert hasattr(logger, 'log_event')


class TestAuditEnums:
    def test_audit_event_type_enum(self):
        assert AuditEventType.LOGIN_SUCCESS.value == "login_success"
        assert AuditEventType.LOGIN_FAILURE.value == "login_failure"
    
    def test_audit_severity_enum(self):
        assert AuditSeverity.INFO.value == "info"
        assert AuditSeverity.WARNING.value == "warning"


class TestAuditEvent:
    def test_can_create_audit_event(self):
        event = AuditEvent(
            event_id="evt_123",
            event_type=AuditEventType.LOGIN_SUCCESS,
            timestamp="2024-01-01T00:00:00",
            severity=AuditSeverity.INFO,
            source=AuditSource.AUTH_SERVICE
        )
        assert event.event_type == AuditEventType.LOGIN_SUCCESS
        assert event.event_id == "evt_123"
