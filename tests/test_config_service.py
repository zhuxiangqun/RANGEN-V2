"""
Config Service Tests
Based on actual code: src/services/config_service.py
"""
import pytest
from src.services.config_service import ConfigService


class TestConfigService:
    def test_can_be_instantiated(self):
        service = ConfigService()
        assert service is not None
    
    def test_is_singleton(self):
        service1 = ConfigService()
        service2 = ConfigService()
        assert service1 is service2
