"""
Autoscaling Service Tests
Based on actual code: src/services/autoscaling_service.py
"""
import pytest
from src.services.autoscaling_service import (
    AutoscalingService, ScalingDecision, ScalingTarget,
    SystemMetric, ScalingRule, ScalingHistoryEntry
)


class TestAutoscalingService:
    @pytest.fixture
    def autoscaling_service(self):
        return AutoscalingService()
    
    def test_can_be_instantiated(self, autoscaling_service):
        assert autoscaling_service is not None
    
    def test_has_start_monitoring_method(self, autoscaling_service):
        assert hasattr(autoscaling_service, 'start_monitoring')


class TestAutoscalingEnums:
    def test_scaling_decision_enum(self):
        assert ScalingDecision.SCALE_OUT.value == "scale_out"
        assert ScalingDecision.SCALE_IN.value == "scale_in"
        assert ScalingDecision.NO_ACTION.value == "no_action"
    
    def test_scaling_target_enum(self):
        assert ScalingTarget.AGENT_INSTANCES.value == "agent_instances"
        assert ScalingTarget.WORKER_THREADS.value == "worker_threads"


class TestSystemMetric:
    def test_can_create_metric(self):
        from datetime import datetime
        metric = SystemMetric(
            name="cpu_usage",
            value=80.5,
            unit="percent",
            timestamp=datetime.now(),
            source="system"
        )
        assert metric.name == "cpu_usage"
        assert metric.value == 80.5


class TestScalingRule:
    def test_can_create_rule(self):
        rule = ScalingRule(
            name="cpu_high",
            target=ScalingTarget.AGENT_INSTANCES,
            metric_name="cpu_usage",
            operator=">",
            threshold=80.0,
            action=ScalingDecision.SCALE_OUT
        )
        assert rule.name == "cpu_high"
        assert rule.threshold == 80.0
