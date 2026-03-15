#!/usr/bin/env python3
"""
Routing Monitor API Routes

Provides API endpoints for monitoring routing decisions and statistics
for the priority routing engine.
"""

import time
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from datetime import datetime

from src.services.logging_service import get_logger
from src.agents.priority_routing_engine import get_priority_routing_engine
from src.agents.skills.enhanced_registry import get_enhanced_skill_registry
from src.agents.tools.tool_registry import get_tool_registry
from src.api.auth import require_read, require_admin

logger = get_logger(__name__)

router = APIRouter(prefix="/api/routing", tags=["routing-monitor"])


# Request/Response models
class RoutingStatisticsResponse(BaseModel):
    """Routing statistics response"""
    total_queries: int
    skill_routing_count: int
    tool_routing_count: int
    local_resource_count: int
    external_resource_count: int
    fallback_count: int
    avg_decision_time: float
    success_rate: float
    skill_routing_ratio: float
    local_resource_ratio: float
    timestamp: str


class RoutingDecision(BaseModel):
    """Routing decision entry"""
    query: str
    decision_type: str  # skill_routing, tool_routing, fallback
    selected_resource: Optional[str]
    selected_resource_type: Optional[str]  # skill, tool, none
    selected_resource_source: Optional[str]  # local, local_mcp, external_mcp, etc.
    priority_score: float
    semantic_score: float
    decision_time: float
    timestamp: str


class NetworkHealthStatus(BaseModel):
    """Network health status for a server"""
    server_name: str
    server_type: str  # local_mcp, external_mcp, custom_api
    latency: Optional[float]  # seconds
    is_available: bool
    last_check_time: str
    http_connectivity: Optional[bool]
    socket_connectivity: Optional[bool]
    error_message: Optional[str]


class RecentDecisionsResponse(BaseModel):
    """Recent routing decisions response"""
    decisions: List[RoutingDecision]
    total_count: int
    limit: int
    offset: int


class NetworkHealthResponse(BaseModel):
    """Network health response"""
    servers: List[NetworkHealthStatus]
    total_servers: int
    healthy_servers: int
    unhealthy_servers: int
    check_time: str


# Helper function to get routing engine instance
def get_routing_engine():
    """Get priority routing engine instance with required registries"""
    try:
        skill_registry = get_enhanced_skill_registry()
        tool_registry = get_tool_registry()
        return get_priority_routing_engine(skill_registry, tool_registry)
    except Exception as e:
        logger.error(f"Failed to get routing engine: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize routing engine: {str(e)}"
        )


@router.get("/statistics", response_model=RoutingStatisticsResponse)
async def get_routing_statistics() -> RoutingStatisticsResponse:
    """Get routing statistics"""
    try:
        engine = get_routing_engine()
        stats = engine.get_routing_statistics()
        
        # Format response
        return RoutingStatisticsResponse(
            total_queries=stats["total_queries"],
            skill_routing_count=stats["skill_routing_count"],
            tool_routing_count=stats["tool_routing_count"],
            local_resource_count=stats["local_resource_count"],
            external_resource_count=stats["external_resource_count"],
            fallback_count=stats["fallback_count"],
            avg_decision_time=stats["avg_decision_time"],
            success_rate=stats.get("success_rate", 0.85),
            skill_routing_ratio=stats.get("skill_routing_ratio", 0.0),
            local_resource_ratio=stats.get("local_resource_ratio", 0.0),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get routing statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get routing statistics: {str(e)}"
        )


@router.get("/decisions/recent", response_model=RecentDecisionsResponse)
async def get_recent_decisions(
    limit: int = 20,
    offset: int = 0
) -> RecentDecisionsResponse:
    """Get recent routing decisions"""
    try:
        engine = get_routing_engine()
        decisions = engine.get_recent_decisions(limit + offset)
        
        # Apply offset
        if offset > 0:
            decisions = decisions[offset:]
        
        # Format decisions
        formatted_decisions = []
        for decision in decisions:
            # Format timestamp if it's a float
            timestamp = decision.get("timestamp")
            if isinstance(timestamp, (int, float)):
                # Convert UNIX timestamp to ISO format
                from datetime import datetime
                timestamp_str = datetime.fromtimestamp(timestamp).isoformat()
            else:
                timestamp_str = str(timestamp) if timestamp else datetime.now().isoformat()
            
            formatted_decisions.append(RoutingDecision(
                query=decision.get("query", ""),
                decision_type=decision.get("decision_type", "unknown"),
                selected_resource=decision.get("selected_resource"),
                selected_resource_type=decision.get("selected_resource_type"),
                selected_resource_source=decision.get("selected_resource_source"),
                priority_score=decision.get("priority_score", 0.0),
                semantic_score=decision.get("semantic_score", 0.0),
                decision_time=decision.get("decision_time", 0.0),
                timestamp=timestamp_str
            ))
        
        return RecentDecisionsResponse(
            decisions=formatted_decisions,
            total_count=len(engine.routing_decisions),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to get recent decisions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recent decisions: {str(e)}"
        )


@router.get("/network/health", response_model=NetworkHealthResponse)
async def get_network_health() -> NetworkHealthResponse:
    """Get network health status for all MCP servers"""
    try:
        engine = get_routing_engine()
        
        # Get server list from tool registry
        tool_registry = get_tool_registry()
        all_tools = tool_registry.get_all_tools()
        
        # Extract unique server names from MCP tools
        server_names = set()
        for tool in all_tools:
            tool_id = tool.get("id", "").lower()
            if tool_id.startswith("mcp_"):
                # Extract server name from tool ID format: mcp_{server_name}_{tool_name}
                parts = tool_id.split('_')
                if len(parts) >= 2 and parts[0] == 'mcp':
                    server_names.add(parts[1])
        
        # Check health for each server
        servers_health = []
        healthy_count = 0
        unhealthy_count = 0
        
        for server_name in server_names:
            try:
                # Determine server type from tools
                server_type = "unknown"
                for tool in all_tools:
                    if f"mcp_{server_name}_" in tool.get("id", "").lower():
                        source = tool.get("source", "").lower()
                        if "local" in source:
                            server_type = "local_mcp"
                        elif "external" in source:
                            server_type = "external_mcp"
                        break
                
                # Check network health
                health_result = engine.check_network_health(server_name)
                
                # Format check time
                check_time = health_result.get("check_time")
                if isinstance(check_time, (int, float)):
                    check_time_str = datetime.fromtimestamp(check_time).isoformat()
                else:
                    check_time_str = str(check_time) if check_time else datetime.now().isoformat()
                
                # Determine if server is available
                is_available = health_result.get("is_available", False)
                if is_available:
                    healthy_count += 1
                else:
                    unhealthy_count += 1
                
                servers_health.append(NetworkHealthStatus(
                    server_name=server_name,
                    server_type=server_type,
                    latency=health_result.get("latency"),
                    is_available=is_available,
                    last_check_time=check_time_str,
                    http_connectivity=health_result.get("http_connectivity"),
                    socket_connectivity=health_result.get("socket_connectivity"),
                    error_message=health_result.get("error_message")
                ))
            except Exception as e:
                logger.warning(f"Failed to check health for server {server_name}: {e}")
                # Add server as unhealthy
                unhealthy_count += 1
                servers_health.append(NetworkHealthStatus(
                    server_name=server_name,
                    server_type="unknown",
                    latency=None,
                    is_available=False,
                    last_check_time=datetime.now().isoformat(),
                    http_connectivity=None,
                    socket_connectivity=None,
                    error_message=str(e)
                ))
        
        return NetworkHealthResponse(
            servers=servers_health,
            total_servers=len(server_names),
            healthy_servers=healthy_count,
            unhealthy_servers=unhealthy_count,
            check_time=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to get network health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get network health: {str(e)}"
        )


@router.post("/decisions/clear", status_code=200)
async def clear_routing_decisions(
    auth_data: dict = Depends(require_admin)
) -> Dict[str, Any]:
    """Clear all routing decisions (admin only)"""
    try:
        engine = get_routing_engine()
        
        # Check if decisions exist
        count = len(engine.routing_decisions)
        
        # Clear decisions
        engine.routing_decisions = []
        
        # Reset stats
        engine.routing_stats = {
            "total_queries": 0,
            "skill_routing_count": 0,
            "tool_routing_count": 0,
            "local_resource_count": 0,
            "external_resource_count": 0,
            "fallback_count": 0,
            "avg_decision_time": 0.0,
            "success_rate": 0.0
        }
        
        logger.info(f"Cleared {count} routing decisions")
        
        return {
            "success": True,
            "message": f"Cleared {count} routing decisions",
            "cleared_count": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear routing decisions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear routing decisions: {str(e)}"
        )


@router.get("/health", response_model=Dict[str, Any])
async def routing_health_check() -> Dict[str, Any]:
    """Routing system health check"""
    try:
        engine = get_routing_engine()
        
        return {
            "status": "healthy",
            "engine_initialized": True,
            "monitoring_enabled": engine.monitoring_enabled,
            "dynamic_priority_adjustment": engine.dynamic_priority_adjustment,
            "total_decisions": len(engine.routing_decisions),
            "routing_stats": engine.routing_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Routing health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Routing health check failed: {str(e)}"
        )