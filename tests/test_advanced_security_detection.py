"""
高级安全检测服务测试
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.advanced_security_detection_service import (
    AdvancedSecurityDetectionService,
    ThreatType,
    DetectionRuleType,
    ThreatIndicator,
    SecurityDetectionRule
)
from src.services.audit_log_service import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditSource
)


class TestAdvancedSecurityDetectionService:
    """测试高级安全检测服务"""

    def setup_method(self):
        """每个测试前设置"""
        self.service = AdvancedSecurityDetectionService()

    def test_service_initialization(self):
        """测试服务初始化"""
        assert len(self.service.detection_rules) > 0
        assert self.service.stats['events_processed'] == 0

    def test_brute_force_detection(self):
        """测试暴力破解检测"""
        events = []
        
        for i in range(6):
            event = AuditEvent(
                event_id=f'event_{i}',
                event_type=AuditEventType.LOGIN_FAILURE,
                user_id='test_user',
                ip_address='192.168.1.100',
                timestamp=datetime.now(),
                source=AuditSource.API
            )
            events.append(event)
        
        threats = self.service._detect_brute_force(events)
        assert threats is not None
        assert threats.threat_type == ThreatType.BRUTE_FORCE_ATTACK

    def test_no_brute_force_with_success(self):
        """测试成功登录不触发暴力破解检测"""
        events = []
        
        for i in range(3):
            event = AuditEvent(
                event_id=f'event_{i}',
                event_type=AuditEventType.LOGIN_FAILURE,
                user_id='test_user',
                ip_address='192.168.1.100',
                timestamp=datetime.now(),
                source=AuditSource.API
            )
            events.append(event)
        
        event = AuditEvent(
            event_id='success',
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id='test_user',
            ip_address='192.168.1.100',
            timestamp=datetime.now(),
            source=AuditSource.API
        )
        events.append(event)
        
        threats = self.service._detect_brute_force(events)
        assert threats is None

    def test_user_profile_update(self):
        """测试用户画像更新"""
        event = AuditEvent(
            event_id='login',
            event_type=AuditEventType.LOGIN_SUCCESS,
            user_id='test_user',
            ip_address='192.168.1.100',
            user_agent='Mozilla/5.0',
            timestamp=datetime.now(),
            source=AuditSource.API
        )
        
        self.service._update_user_profile(event)
        
        assert 'test_user' in self.service.user_profiles
        profile = self.service.user_profiles['test_user']
        assert '192.168.1.100' in profile.ip_addresses

    def test_api_abuse_detection(self):
        """测试API滥用检测"""
        events = []
        
        for i in range(101):
            event = AuditEvent(
                event_id=f'event_{i}',
                event_type=AuditEventType.API_KEY_USAGE,
                user_id='test_user',
                ip_address='192.168.1.100',
                timestamp=datetime.now(),
                source=AuditSource.API,
                metadata={'endpoint': '/api/data'}
            )
            events.append(event)
        
        threats = self.service._detect_api_abuse(events)
        assert threats is not None
        assert threats.threat_type == ThreatType.API_ABUSE

    def test_analyze_events(self):
        """测试事件分析"""
        events = [
            AuditEvent(
                event_id='login',
                event_type=AuditEventType.LOGIN_SUCCESS,
                user_id='test_user',
                ip_address='192.168.1.100',
                timestamp=datetime.now(),
                source=AuditSource.API
            )
        ]
        
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            threats = loop.run_until_complete(self.service.analyze_events(events))
        finally:
            loop.close()
        
        assert isinstance(threats, list)

    def test_enable_rule(self):
        """测试启用/禁用规则"""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                self.service.enable_rule('rule_brute_force', False)
            )
        finally:
            loop.close()
        
        assert result is True
        
        rule = next(r for r in self.service.detection_rules if r.rule_id == 'rule_brute_force')
        assert rule.enabled is False

    def test_user_risk_score(self):
        """测试用户风险评分"""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            risk_info = loop.run_until_complete(
                self.service.get_user_risk_score('unknown_user')
            )
        finally:
            loop.close()
        
        assert risk_info['user_id'] == 'unknown_user'
        assert risk_info['risk_score'] == 0.0


class TestSecurityDetectionRules:
    """测试安全检测规则"""

    def test_rule_creation(self):
        """测试规则创建"""
        rule = SecurityDetectionRule(
            rule_id='test_rule',
            name='Test Rule',
            description='Test description',
            rule_type=DetectionRuleType.THRESHOLD_BASED,
            threshold=10,
            time_window_seconds=300
        )
        
        assert rule.rule_id == 'test_rule'
        assert rule.enabled is True
        assert rule.threshold == 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
