"""
Monitoring Service Tests
Based on actual code: src/services/monitoring.py
"""
import pytest
from src.services.monitoring import (
    MonitoringService, MetricCategory, MetricUnit,
    HealthStatus, AlertLevel, Alert, HealthCheckResult
)


class TestMonitoringService:
    @pytest.fixture
    def monitoring_service(self):
        return MonitoringService()
    
    def test_can_be_instantiated(self, monitoring_service):
        assert monitoring_service is not None
    
    def test_has_collect_metrics_method(self, monitoring_service):
        assert hasattr(monitoring_service, 'collect_metrics')


class TestMonitoringEnums:
    def test_metric_category_enum(self):
        assert MetricCategory.CPU == "cpu"
        assert MetricCategory.MEMORY == "memory"
    
    def test_health_status_enum(self):
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.CRITICAL == "critical"


class TestHealthCheckResult:
    def test_can_create_health_check_result(self):
        result = HealthCheckResult(
            service="test_service",
            status=HealthStatus.HEALTHY,
            message="OK",
            details={"cpu": 50},
            timestamp=1234567890.0
        )
        assert result.status == HealthStatus.HEALTHY
        assert result.service == "test_service"
