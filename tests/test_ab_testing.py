"""
AB Testing Service Tests
Based on actual code: src/services/ab_testing_service.py
"""
import pytest
from src.services.ab_testing_service import (
    ABTestingService, ExperimentStatus, VariantType,
    ExperimentConfig, VariantResult, ExperimentResult
)


class TestABTestingService:
    @pytest.fixture
    def ab_service(self):
        return ABTestingService()
    
    def test_can_be_instantiated(self, ab_service):
        assert ab_service is not None
    
    def test_has_create_experiment_method(self, ab_service):
        assert hasattr(ab_service, 'create_experiment')


class TestABTestingEnums:
    def test_experiment_status_enum(self):
        assert ExperimentStatus.DRAFT.value == "draft"
        assert ExperimentStatus.RUNNING.value == "running"
        assert ExperimentStatus.COMPLETED.value == "completed"
    
    def test_variant_type_enum(self):
        assert VariantType.ROUTING_STRATEGY.value == "routing_strategy"
        assert VariantType.MODEL_SELECTION.value == "model_selection"


class TestExperimentConfig:
    def test_can_create_config(self):
        config = ExperimentConfig(
            experiment_id="exp_1",
            name="test_exp",
            variant_type=VariantType.ROUTING_STRATEGY,
            description="Test experiment",
            variants=[{"name": "control"}, {"name": "treatment"}]
        )
        assert config.name == "test_exp"
        assert config.variant_type == VariantType.ROUTING_STRATEGY
