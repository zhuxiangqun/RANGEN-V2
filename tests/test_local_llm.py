"""
Local LLM Service Tests
Based on actual code: src/services/local_llm_service.py
"""
import pytest
from src.services.local_llm_service import LocalLLMService


class TestLocalLLMService:
    def test_has_generate_response_method(self):
        service = LocalLLMService.__new__(LocalLLMService)
        assert hasattr(service, 'generate_response')
    
    def test_has_generate_hyde_method(self):
        service = LocalLLMService.__new__(LocalLLMService)
        assert hasattr(service, 'generate_hyde')
