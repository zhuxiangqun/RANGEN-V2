"""
Logging Service Tests
Based on actual code: src/services/logging_service.py
"""
import pytest
from src.services.logging_service import get_logger


class TestLoggingService:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test_logger")
        assert logger is not None
    
    def test_get_logger_has_basic_methods(self):
        logger = get_logger("test_logger")
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
