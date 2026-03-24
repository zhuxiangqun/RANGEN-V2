"""
Database Service Tests
Based on actual code: src/services/database.py
"""
import pytest
from src.services.database import DatabaseService


class TestDatabaseService:
    def test_is_singleton(self):
        """Test that DatabaseService is a singleton"""
        db1 = DatabaseService()
        db2 = DatabaseService()
        assert db1 is db2
    
    def test_has_get_connection_method(self):
        service = DatabaseService.__new__(DatabaseService)
        assert hasattr(service, 'get_connection')
    
    def test_has_initialize_method(self):
        service = DatabaseService.__new__(DatabaseService)
        assert hasattr(service, 'initialize')
