"""
Knowledge Retrieval Tests
Based on actual code: src/services/retrieval.py
"""
import pytest
from src.services.retrieval import RetrievalService, RetrievalMethod, RetrievalResult, RetrievalChunk


class TestRetrievalService:
    @pytest.fixture
    def retrieval_service(self):
        return RetrievalService()
    
    def test_can_be_instantiated(self, retrieval_service):
        assert retrieval_service is not None
    
    def test_has_retrieve_method(self, retrieval_service):
        assert hasattr(retrieval_service, 'retrieve')
        assert hasattr(retrieval_service, 'add_documents')
        assert hasattr(retrieval_service, 'build_index')


class TestRetrievalResult:
    def test_can_create_result(self):
        chunk = RetrievalChunk(
            text="test text",
            score=0.9,
            source="test",
            metadata={}
        )
        result = RetrievalResult(
            query="test query",
            method=RetrievalMethod.SEMANTIC,
            chunks=[chunk],
            total_found=1,
            processing_time=0.1
        )
        assert result.query == "test query"
        assert len(result.chunks) == 1
