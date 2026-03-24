"""
Multimodal Service Tests
Based on actual code: src/services/multimodal_service.py
"""
import pytest
from src.services.multimodal_service import (
    MultimodalService, ModalityType, MultimodalTaskType
)


class TestMultimodalService:
    def test_has_encode_method(self):
        service = MultimodalService.__new__(MultimodalService)
        assert hasattr(service, 'encode')
    
    def test_has_analyze_method(self):
        service = MultimodalService.__new__(MultimodalService)
        assert hasattr(service, 'analyze')


class TestModalityEnums:
    def test_modality_type_enum(self):
        assert ModalityType.TEXT.value == "text"
        assert ModalityType.IMAGE.value == "image"
        assert ModalityType.AUDIO.value == "audio"
    
    def test_task_type_enum(self):
        assert MultimodalTaskType.ENCODE.value == "encode"
        assert MultimodalTaskType.ANALYZE.value == "analyze"
