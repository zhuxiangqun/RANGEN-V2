#!/usr/bin/env python3
"""
MCP Management API Routes

Provides API endpoints for managing MCP servers
"""

from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

from src.services.logging_service import get_logger
from src.services.mcp_server_manager import get_mcp_server_manager
from src.services.mcp_config_service import get_mcp_config_service
from src.api.auth import require_admin, require_read

logger = get_logger(__name__)

router = APIRouter(prefix="/mcp", tags=["mcp"])


# Request/Response models
class MCPStatusResponse(BaseModel):
    """MCP status response"""
    enabled: bool
    server_count: int
    running_server_count: int
    config_loaded: bool


class MCPServerStatus(BaseModel):
    """MCP server status"""
    name: str
    status: str
    transport: str
    enabled: bool
    pid: Optional[int] = None
    start_time: Optional[float] = None
    request_count: int = 0
    error_count: int = 0
    last_request_time: Optional[float] = None
    error_message: Optional[str] = None
    http_endpoint: Optional[str] = None


class MCPServerActionRequest(BaseModel):
    """MCP server action request"""
    server_name: str
    action: str  # start, stop, restart, status


class MCPServerActionResponse(BaseModel):
    """MCP server action response"""
    success: bool
    message: str
    server_name: str
    action: str
    new_status: Optional[str] = None


class MCPToolInfo(BaseModel):
    """MCP tool information"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str


class MCPConnectionInfo(BaseModel):
    """MCP connection information"""
    name: str
    description: str
    transport: str
    server_url: str
    connected: bool
    tool_count: int


@router.get("/status", response_model=MCPStatusResponse)
async def get_mcp_status(
    auth_data: dict = Depends(require_read)
) -> MCPStatusResponse:
    """Get MCP system status"""
    try:
        config_service = get_mcp_config_service()
        config = config_service.config
        
        if not config:
            return MCPStatusResponse(
                enabled=False,
                server_count=0,
                running_server_count=0,
                config_loaded=False
            )
        
        # Get server status
        manager = get_mcp_server_manager()
        server_statuses = await manager.get_all_server_statuses()
        
        # Count running servers
        running_count = 0
        for server_name, status in server_statuses.items():
            if status.get("status") == "running":
                running_count += 1
        
        return MCPStatusResponse(
            enabled=config.enabled,
            server_count=len(server_statuses),
            running_server_count=running_count,
            config_loaded=True
        )
        
    except Exception as e:
        logger.error(f"Failed to get MCP status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MCP status: {e}")


@router.get("/servers", response_model=List[MCPServerStatus])
async def list_mcp_servers(
    auth_data: dict = Depends(require_read)
) -> List[MCPServerStatus]:
    """List all MCP servers and their status"""
    try:
        manager = get_mcp_server_manager()
        server_statuses = await manager.get_all_server_statuses()
        
        result = []
        for server_name, status in server_statuses.items():
            # Get config for additional info
            config_service = get_mcp_config_service()
            server_config = config_service.get_server_config(server_name)
            
            server_status = MCPServerStatus(
                name=server_name,
                status=status.get("status", "unknown"),
                transport=status.get("config", {}).get("transport", "unknown"),
                enabled=status.get("config", {}).get("enabled", False),
                pid=status.get("process", {}).get("pid"),
                start_time=status.get("process", {}).get("start_time"),
                request_count=status.get("statistics", {}).get("request_count", 0),
                error_count=status.get("statistics", {}).get("error_count", 0),
                last_request_time=status.get("statistics", {}).get("last_request_time"),
                error_message=status.get("error"),
                http_endpoint=status.get("config", {}).get("http_endpoint")
            )
            result.append(server_status)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list MCP servers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list MCP servers: {e}")


@router.post("/servers/{server_name}/{action}", response_model=MCPServerActionResponse)
async def manage_mcp_server(
    server_name: str,
    action: str,
    auth_data: dict = Depends(require_admin)
) -> MCPServerActionResponse:
    """Manage MCP server (start, stop, restart)"""
    if action not in ["start", "stop", "restart"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid action: {action}. Allowed: start, stop, restart"
        )
    
    try:
        manager = get_mcp_server_manager()
        
        if action == "start":
            success = await manager.start_server(server_name)
            message = f"MCP server '{server_name}' started" if success else f"Failed to start MCP server '{server_name}'"
        
        elif action == "stop":
            success = await manager.stop_server(server_name)
            message = f"MCP server '{server_name}' stopped" if success else f"Failed to stop MCP server '{server_name}'"
        
        elif action == "restart":
            success = await manager.restart_server(server_name)
            message = f"MCP server '{server_name}' restarted" if success else f"Failed to restart MCP server '{server_name}'"
        
        # Get new status
        new_status = None
        if server_name in manager.servers:
            new_status = manager.servers[server_name].status
        
        return MCPServerActionResponse(
            success=success,
            message=message,
            server_name=server_name,
            action=action,
            new_status=new_status
        )
        
    except Exception as e:
        logger.error(f"Failed to {action} MCP server '{server_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to {action} MCP server '{server_name}': {e}"
        )


@router.get("/tools", response_model=List[MCPToolInfo])
async def list_mcp_tools(
    auth_data: dict = Depends(require_read)
) -> List[MCPToolInfo]:
    """List all tools available through MCP"""
    try:
        # TODO: Implement tool listing from MCP connections
        # This requires connecting to MCP servers and calling tools/list
        
        # For now, return empty list
        return []
        
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list MCP tools: {e}")


@router.get("/connections", response_model=List[MCPConnectionInfo])
async def list_mcp_connections(
    auth_data: dict = Depends(require_read)
) -> List[MCPConnectionInfo]:
    """List all MCP connections"""
    try:
        config_service = get_mcp_config_service()
        config = config_service.config
        
        if not config:
            return []
        
        result = []
        for client_name, client_config in config.clients.items():
            # TODO: Check connection status and tool count
            # This requires MCPClient implementation
            
            connection_info = MCPConnectionInfo(
                name=client_name,
                description=client_config.description,
                transport=client_config.transport,
                server_url=client_config.server_url,
                connected=False,  # TODO: Implement connection check
                tool_count=0  # TODO: Implement tool count
            )
            result.append(connection_info)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to list MCP connections: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list MCP connections: {e}")


@router.get("/config")
async def get_mcp_config(
    auth_data: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """Get MCP configuration"""
    try:
        config_service = get_mcp_config_service()
        config = config_service.config
        
        if not config:
            return {"error": "Configuration not loaded"}
        
        # Convert config to dict
        config_dict = {
            "enabled": config.enabled,
            "log_level": config.log_level,
            "servers": {},
            "clients": {},
            "integration": {
                "auto_start_servers": config.integration.auto_start_servers,
                "auto_register_tools": config.integration.auto_register_tools,
                "enable_context_protocol": config.integration.enable_context_protocol,
                "pageindex_enabled": config.integration.pageindex_enabled,
                "pageindex_server_name": config.integration.pageindex_server_name,
                "pageindex_transport": config.integration.pageindex_transport
            },
            "security": {
                "authentication_enabled": config.security.authentication_enabled,
                "allowed_origins": config.security.allowed_origins
            },
            "monitoring": {
                "enabled": config.monitoring.enabled,
                "log_requests": config.monitoring.log_requests,
                "log_responses": config.monitoring.log_responses,
                "metrics_collection": config.monitoring.metrics_collection,
                "health_check_interval": config.monitoring.health_check_interval
            },
            "performance": {
                "max_concurrent_requests": config.performance.max_concurrent_requests,
                "request_timeout": config.performance.request_timeout,
                "cache_enabled": config.performance.cache_enabled,
                "cache_ttl": config.performance.cache_ttl
            }
        }
        
        # Add servers
        for server_name, server_config in config.servers.items():
            config_dict["servers"][server_name] = {
                "name": server_config.name,
                "description": server_config.description,
                "enabled": server_config.enabled,
                "transport": server_config.transport,
                "http_enabled": server_config.http_enabled,
                "http_host": server_config.http_host,
                "http_port": server_config.http_port,
                "http_endpoint": server_config.http_endpoint,
                "include_all_tools": server_config.include_all_tools,
                "excluded_tools": server_config.excluded_tools,
                "included_tools_only": server_config.included_tools_only
            }
        
        # Add clients
        for client_name, client_config in config.clients.items():
            config_dict["clients"][client_name] = {
                "name": client_config.name,
                "description": client_config.description,
                "transport": client_config.transport,
                "server_url": client_config.server_url,
                "auto_connect": client_config.auto_connect,
                "timeout": client_config.timeout,
                "retry_attempts": client_config.retry_attempts,
                "retry_delay": client_config.retry_delay
            }
        
        return config_dict
        
    except Exception as e:
        logger.error(f"Failed to get MCP config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MCP config: {e}")


# Health check endpoint
@router.get("/health")
async def mcp_health_check() -> Dict[str, Any]:
    """MCP health check"""
    try:
        config_service = get_mcp_config_service()
        config = config_service.config
        
        if not config:
            return {
                "status": "unhealthy",
                "error": "Configuration not loaded",
                "timestamp": datetime.now().isoformat()
            }
        
        manager = get_mcp_server_manager()
        server_statuses = await manager.get_all_server_statuses()
        
        # Check if any enabled server is not running
        issues = []
        for server_name, status in server_statuses.items():
            server_config = config_service.get_server_config(server_name)
            if server_config and server_config.enabled:
                if status.get("status") != "running":
                    issues.append(f"Server '{server_name}' is not running (status: {status.get('status')})")
        
        if issues:
            return {
                "status": "unhealthy",
                "issues": issues,
                "server_count": len(server_statuses),
                "enabled_server_count": len([s for s in config.servers.values() if s.enabled]),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "healthy",
            "server_count": len(server_statuses),
            "enabled_server_count": len([s for s in config.servers.values() if s.enabled]),
            "running_server_count": len([s for s in server_statuses.values() if s.get("status") == "running"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"MCP health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/restart")
async def mcp_restart():
    """Restart MCP server manager"""
    try:
        manager = get_mcp_server_manager()
        
        await manager.stop_all_servers()
        await manager.start_all_servers()
        
        return {
            "status": "success",
            "message": "MCP services restarted successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"MCP restart failed: {e}")
        return {
            "status": "error",
            "message": f"MCP restart failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }