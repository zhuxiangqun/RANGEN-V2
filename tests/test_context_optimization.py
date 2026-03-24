"""
Context Optimization Service Tests
Based on actual code: src/services/context_optimization_service.py
"""
import pytest
from src.services.context_optimization_service import (
    ContextOptimizationService, OptimizationStrategy, OptimizationResult
)


class TestContextOptimizationService:
    def test_has_optimize_context_method(self):
        service = ContextOptimizationService.__new__(ContextOptimizationService)
        assert hasattr(service, 'optimize_context')


class TestOptimizationEnums:
    def test_optimization_strategy_enum(self):
        assert OptimizationStrategy.TOKEN_REDUCTION.value == "token_reduction"
        assert OptimizationStrategy.CONTEXT_COMPRESSION.value == "context_compression"
