#!/usr/bin/env python3
"""
MCP Integration Test

Tests the MCP server implementation and integration
"""

import asyncio
import sys
import os
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.logging_service import get_logger
from src.services.mcp_config_service import get_mcp_config_service
from src.services.mcp_server_manager import get_mcp_server_manager, initialize_mcp_server_manager

logger = get_logger("mcp-test")


async def test_config_service():
    """Test MCP config service"""
    print("\n=== Testing MCP Config Service ===")
    
    try:
        config_service = get_mcp_config_service()
        config = config_service.load_config()
        
        print(f"Configuration loaded: {config is not None}")
        print(f"MCP enabled: {config.enabled}")
        print(f"Log level: {config.log_level}")
        print(f"Server count: {len(config.servers)}")
        print(f"Client count: {len(config.clients)}")
        
        # List servers
        for server_name, server_config in config.servers.items():
            print(f"  Server: {server_name}")
            print(f"    Description: {server_config.description}")
            print(f"    Enabled: {server_config.enabled}")
            print(f"    Transport: {server_config.transport}")
            if server_config.http_enabled:
                print(f"    HTTP endpoint: {server_config.http_endpoint}")
        
        # List clients
        for client_name, client_config in config.clients.items():
            print(f"  Client: {client_name}")
            print(f"    Description: {client_config.description}")
            print(f"    Auto-connect: {client_config.auto_connect}")
            print(f"    Server URL: {client_config.server_url}")
        
        return True
        
    except Exception as e:
        print(f"Config service test failed: {e}")
        return False


async def test_server_manager():
    """Test MCP server manager"""
    print("\n=== Testing MCP Server Manager ===")
    
    try:
        # Initialize server manager
        manager = get_mcp_server_manager()
        initialized = await manager.initialize()
        
        print(f"Server manager initialized: {initialized}")
        
        if not initialized:
            print("Server manager not initialized, skipping further tests")
            return False
        
        # Get all server statuses
        statuses = await manager.get_all_server_statuses()
        print(f"Total servers: {len(statuses)}")
        
        # List server statuses
        for server_name, status in statuses.items():
            print(f"  Server: {server_name}")
            print(f"    Status: {status.get('status', 'unknown')}")
            print(f"    Enabled: {status.get('config', {}).get('enabled', False)}")
            print(f"    Transport: {status.get('config', {}).get('transport', 'unknown')}")
            
            if status.get('process', {}).get('pid'):
                print(f"    PID: {status.get('process', {}).get('pid')}")
            
            if status.get('error'):
                print(f"    Error: {status.get('error')}")
        
        # Test starting a server (if not running)
        for server_name in manager.servers:
            server = manager.servers[server_name]
            if server.status != "running" and server.config.enabled:
                print(f"\nStarting server: {server_name}")
                success = await manager.start_server(server_name)
                print(f"  Start successful: {success}")
                
                if success:
                    # Wait a bit for server to start
                    await asyncio.sleep(1)
                    
                    # Check status
                    status = await manager.get_server_status(server_name)
                    print(f"  New status: {status.get('status')}")
                    
                    # Stop the server
                    print(f"  Stopping server: {server_name}")
                    success = await manager.stop_server(server_name)
                    print(f"  Stop successful: {success}")
                
                break  # Just test one server
        
        return True
        
    except Exception as e:
        print(f"Server manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_api():
    """Test MCP API endpoints"""
    print("\n=== Testing MCP API ===")
    
    try:
        # Import API test client
        from fastapi.testclient import TestClient
        from src.api.server import app
        
        client = TestClient(app)
        
        # Test health endpoint
        print("Testing /mcp/health endpoint...")
        response = client.get("/mcp/health")
        print(f"  Status code: {response.status_code}")
        print(f"  Response: {response.json()}")
        
        # Test status endpoint (requires authentication)
        print("\nTesting /mcp/status endpoint...")
        response = client.get("/mcp/status")
        print(f"  Status code: {response.status_code}")
        # Note: This will likely return 401/403 due to missing auth
        
        # Test servers endpoint (requires authentication)
        print("\nTesting /mcp/servers endpoint...")
        response = client.get("/mcp/servers")
        print(f"  Status code: {response.status_code}")
        
        print("\nMCP API test completed (note: auth endpoints require authentication)")
        return True
        
    except ImportError as e:
        print(f"FastAPI test client not available: {e}")
        return False
    except Exception as e:
        print(f"API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_client():
    """Test MCP client connection"""
    print("\n=== Testing MCP Client ===")
    
    try:
        # Try to import MCP client
        from src.gateway.mcp import MCPConnection, MCPClient, MCPRegistry
        
        # Create a test connection
        connection = MCPConnection(
            name="test-connection",
            description="Test MCP Connection",
            transport="stdio",
            server_url="python -m src.agents.tools.mcp_local_server"
        )
        
        # Create client
        client = MCPClient(connection)
        
        # Try to connect
        print("Connecting to MCP server...")
        connected = await client.connect()
        print(f"  Connected: {connected}")
        
        if connected:
            # Try to list tools
            print("Listing tools...")
            tools = await client.list_tools()
            print(f"  Tools found: {len(tools)}")
            
            for tool in tools:
                print(f"    Tool: {tool.name}")
                print(f"      Description: {tool.description}")
            
            # Try to call a tool
            if tools:
                tool_name = tools[0].name
                print(f"\nCalling tool: {tool_name}")
                
                try:
                    result = await client.call_tool(tool_name, {})
                    print(f"  Result: {result}")
                except Exception as e:
                    print(f"  Tool call failed: {e}")
            
            # Disconnect
            await client.disconnect()
            print("Disconnected")
        
        return True
        
    except ImportError as e:
        print(f"MCP client not available: {e}")
        return False
    except Exception as e:
        print(f"MCP client test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all MCP integration tests"""
    print("Starting MCP Integration Tests...")
    print("=" * 50)
    
    test_results = []
    
    # Test config service
    test_results.append(("Config Service", await test_config_service()))
    
    # Test server manager
    test_results.append(("Server Manager", await test_server_manager()))
    
    # Test MCP API
    test_results.append(("MCP API", await test_mcp_api()))
    
    # Test MCP client
    test_results.append(("MCP Client", await test_mcp_client()))
    
    # Print summary
    print("\n" + "=" * 50)
    print("MCP Integration Test Summary")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)