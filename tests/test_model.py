"""
Model Service Tests
Based on actual code: src/services/model_service.py
"""
import pytest
from src.services.model_service import ModelProviderService


class TestModelProviderService:
    def test_has_create_provider_method(self):
        service = ModelProviderService.__new__(ModelProviderService)
        assert hasattr(service, 'create_provider')
    
    def test_has_get_provider_method(self):
        service = ModelProviderService.__new__(ModelProviderService)
        assert hasattr(service, 'get_provider')
