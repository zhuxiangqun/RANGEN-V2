"""
Metrics Service Tests
Based on actual code: src/services/metrics_service.py
"""
import pytest
from src.services.metrics_service import MetricsService


class TestMetricsService:
    @pytest.fixture
    def metrics_service(self):
        return MetricsService()
    
    def test_can_be_instantiated(self, metrics_service):
        assert metrics_service is not None
    
    def test_has_record_method(self, metrics_service):
        assert hasattr(metrics_service, 'record')
