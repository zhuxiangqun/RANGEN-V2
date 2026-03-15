#!/usr/bin/env python3
"""
Demonstration of RANGEN API Authentication
"""
import os
import json
import asyncio
import httpx
from src.api.auth import AuthService, register_api_key

async def demo_authentication():
    """Demonstrate API authentication"""
    
    print("🔐 RANGEN API Authentication Demo")
    print("=" * 50)
    
    # 1. Create API keys with different permissions
    admin_key = AuthService.generate_api_key()
    user_key = AuthService.generate_api_key()
    
    register_api_key(admin_key, "admin_user", ["read", "write", "admin"])
    register_api_key(user_key, "regular_user", ["read", "write"])
    
    print(f"✅ Created Admin API Key: {admin_key}")
    print(f"✅ Created User API Key: {user_key}")
    print()
    
    # 2. Start server in background (for demo purposes)
    print("🚀 Starting server (this will fail if system not fully initialized)...")
    print("   Note: In production, run: python3 src/api/server.py")
    print()
    
    # 3. Demonstrate API calls
    base_url = "http://localhost:8000"
    
    async def test_endpoint(endpoint: str, api_key: str, description: str):
        """Test an endpoint with given API key"""
        headers = {"Authorization": f"Bearer {api_key}"}
        
        try:
            async with httpx.AsyncClient() as client:
                if endpoint.startswith("/chat"):
                    response = await client.post(
                        base_url + endpoint,
                        json={"query": "test query", "session_id": "demo"},
                        headers=headers
                    )
                else:
                    response = await client.get(base_url + endpoint, headers=headers)
                
                status = "✅" if response.status_code < 400 else "❌"
                print(f"{status} {description}: {response.status_code}")
                if response.status_code < 400:
                    print(f"   Response: {response.json()}")
                else:
                    print(f"   Error: {response.text}")
                print()
                
        except Exception as e:
            print(f"❌ {description}: Connection failed - {e}")
            print()
    
    print("📡 Testing API Endpoints:")
    print()
    
    # Test public endpoint (no auth needed)
    await test_endpoint("/health", "", "Public health check (no auth)")
    
    # Test with user API key
    await test_endpoint("/health/auth", user_key, "User: Authenticated health check")
    await test_endpoint("/auth/info", user_key, "User: Get auth info")
    await test_endpoint("/chat", user_key, "User: Chat endpoint")
    await test_endpoint("/diag", user_key, "User: Diagnostic endpoint (should fail)")
    
    # Test with admin API key
    await test_endpoint("/diag", admin_key, "Admin: Diagnostic endpoint")
    await test_endpoint("/auth/api-key", admin_key, "Admin: Create new API key")
    
    print("🔑 API Usage Examples:")
    print("=" * 30)
    print(f"curl -H \"Authorization: Bearer {user_key}\" \\")
    print(f"     -X POST http://localhost:8000/chat \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"query": "What is RANGEN?"}\'')
    print()
    
    print(f"curl -H \"Authorization: Bearer {admin_key}\" \\")
    print(f"     -X POST http://localhost:8000/auth/api-key \\")
    print('     -H "Content-Type: application/json" \\')
    print('     -d \'{"name": "new-app", "permissions": "read,write"}\'')
    print()

if __name__ == "__main__":
    asyncio.run(demo_authentication())