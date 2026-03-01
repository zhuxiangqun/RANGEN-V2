"""
Test API Authentication
"""
import pytest
import requests
import json
from fastapi.testclient import TestClient
from src.api.server import app
from src.api.auth import register_api_key, AuthService

client = TestClient(app)

class TestAPIAuthentication:
    """Test API authentication endpoints"""
    
    def setup_method(self):
        """Setup test API key"""
        self.test_api_key = AuthService.generate_api_key()
        register_api_key(self.test_api_key, "test_user", ["read", "write"])
    
    def test_public_health_endpoint(self):
        """Test public health endpoint (no auth required)"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data
    
    def test_protected_health_endpoint_with_auth(self):
        """Test protected health endpoint with valid auth"""
        headers = {"Authorization": f"Bearer {self.test_api_key}"}
        response = client.get("/health/auth", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["authenticated_as"] == "test_user"
    
    def test_protected_health_endpoint_without_auth(self):
        """Test protected health endpoint without auth"""
        response = client.get("/health/auth")
        assert response.status_code == 401
    
    def test_chat_endpoint_with_auth(self):
        """Test chat endpoint with valid auth"""
        headers = {"Authorization": f"Bearer {self.test_api_key}"}
        chat_data = {
            "query": "test query",
            "session_id": "test_session"
        }
        response = client.post("/chat", json=chat_data, headers=headers)
        # Should return 503 (system not initialized) or 200 if initialized
        assert response.status_code in [200, 503]
    
    def test_chat_endpoint_without_auth(self):
        """Test chat endpoint without auth"""
        chat_data = {
            "query": "test query",
            "session_id": "test_session"
        }
        response = client.post("/chat", json=chat_data)
        assert response.status_code == 401
    
    def test_diag_endpoint_without_auth(self):
        """Test diagnostic endpoint without auth"""
        response = client.get("/diag")
        assert response.status_code == 401
    
    def test_auth_info_endpoint(self):
        """Test auth info endpoint"""
        headers = {"Authorization": f"Bearer {self.test_api_key}"}
        response = client.get("/auth/info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated_as"] == "test_user"
        assert data["auth_type"] == "api_key"
        assert "read" in data["permissions"]
        assert "write" in data["permissions"]
    
    def test_invalid_api_key(self):
        """Test with invalid API key"""
        headers = {"Authorization": "Bearer invalid_key"}
        response = client.get("/health/auth", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_auth_header(self):
        """Test with malformed auth header"""
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/health/auth", headers=headers)
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])