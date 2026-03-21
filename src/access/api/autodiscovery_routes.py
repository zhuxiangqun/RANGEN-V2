#!/usr/bin/env python3
"""
Auto-Discovery API Routes

Provides API endpoints for automatic discovery and integration
of MCP servers, external agents, and APIs.
"""

import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from src.services.logging_service import get_logger
from src.services.autodiscovery_service import (
    get_auto_discovery_service,
    DiscoveryTarget,
    DiscoveredResource
)

logger = get_logger(__name__)

router = APIRouter(prefix="/autodiscovery", tags=["autodiscovery"])


# Request/Response models
class DiscoveryStatusResponse(BaseModel):
    """Discovery status response"""
    status: str
    target_count: int
    discovered_count: int
    last_discovery: str
    discovery_targets: List[Dict[str, Any]]


class DiscoveredResourceResponse(BaseModel):
    """Discovered resource response"""
    resource_id: str
    name: str
    resource_type: str
    endpoint: str
    protocol: str
    description: str
    capabilities: List[str]
    confidence: float
    metadata: Dict[str, Any]
    discovered_at: str


class DiscoveryTargetRequest(BaseModel):
    """Discovery target request"""
    name: str
    target_type: str = Field(..., description="network, url, semantic, predefined")
    value: str
    description: str = ""
    priority: int = Field(1, ge=1, le=5, description="Priority 1-5")


class DiscoveryTargetResponse(BaseModel):
    """Discovery target response"""
    name: str
    target_type: str
    value: str
    description: str
    priority: int


class AutoIntegrationRequest(BaseModel):
    """Auto-integration request"""
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)
    auto_connect: bool = True


class AutoIntegrationResult(BaseModel):
    """Auto-integration result"""
    resource_id: str
    name: str
    type: str
    endpoint: Optional[str] = None
    integrated: bool
    timestamp: str


class AutoIntegrationResponse(BaseModel):
    """Auto-integration response"""
    total_resources: int
    integrated_count: int
    results: List[AutoIntegrationResult]
    timestamp: str


class DiscoveryScanResponse(BaseModel):
    """Discovery scan response"""
    scan_id: str
    status: str
    discovered_count: int
    timestamp: str


# Helper function to convert discovered resources to response
def resource_to_response(resource: DiscoveredResource) -> DiscoveredResourceResponse:
    """Convert DiscoveredResource to API response"""
    return DiscoveredResourceResponse(
        resource_id=resource.resource_id,
        name=resource.name,
        resource_type=resource.resource_type,
        endpoint=resource.endpoint,
        protocol=resource.protocol,
        description=resource.description,
        capabilities=resource.capabilities,
        confidence=resource.confidence,
        metadata=resource.metadata,
        discovered_at=resource.discovered_at.isoformat()
    )


@router.get("/status", response_model=DiscoveryStatusResponse)
async def get_discovery_status() -> DiscoveryStatusResponse:
    """Get discovery service status"""
    try:
        service = get_auto_discovery_service()
        status = service.get_discovery_status()
        
        return DiscoveryStatusResponse(**status)
    except Exception as e:
        logger.error(f"Failed to get discovery status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get discovery status: {str(e)}"
        )


@router.get("/targets", response_model=List[DiscoveryTargetResponse])
async def get_discovery_targets() -> List[DiscoveryTargetResponse]:
    """Get all discovery targets"""
    try:
        service = get_auto_discovery_service()
        
        return [
            DiscoveryTargetResponse(
                name=target.name,
                target_type=target.target_type,
                value=target.value,
                description=target.description,
                priority=target.priority
            )
            for target in service.discovery_targets
        ]
    except Exception as e:
        logger.error(f"Failed to get discovery targets: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get discovery targets: {str(e)}"
        )


@router.post("/targets", response_model=DiscoveryTargetResponse)
async def add_discovery_target(request: DiscoveryTargetRequest) -> DiscoveryTargetResponse:
    """Add a new discovery target"""
    try:
        service = get_auto_discovery_service()
        
        # Create target
        target = DiscoveryTarget(
            name=request.name,
            target_type=request.target_type,
            value=request.value,
            description=request.description,
            priority=request.priority
        )
        
        # Check if target already exists
        for existing_target in service.discovery_targets:
            if existing_target.name == target.name:
                raise HTTPException(
                    status_code=400,
                    detail=f"Discovery target '{target.name}' already exists"
                )
        
        # Add target
        service.discovery_targets.append(target)
        
        logger.info(f"Added discovery target: {target.name}")
        
        return DiscoveryTargetResponse(
            name=target.name,
            target_type=target.target_type,
            value=target.value,
            description=target.description,
            priority=target.priority
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add discovery target: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add discovery target: {str(e)}"
        )


@router.delete("/targets/{target_name}")
async def remove_discovery_target(target_name: str) -> Dict[str, Any]:
    """Remove a discovery target"""
    try:
        service = get_auto_discovery_service()
        
        # Find and remove target
        for i, target in enumerate(service.discovery_targets):
            if target.name == target_name:
                service.discovery_targets.pop(i)
                logger.info(f"Removed discovery target: {target_name}")
                return {
                    "success": True,
                    "message": f"Discovery target '{target_name}' removed"
                }
        
        raise HTTPException(
            status_code=404,
            detail=f"Discovery target '{target_name}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove discovery target: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove discovery target: {str(e)}"
        )


@router.get("/resources", response_model=List[DiscoveredResourceResponse])
async def get_discovered_resources() -> List[DiscoveredResourceResponse]:
    """Get all discovered resources"""
    try:
        service = get_auto_discovery_service()
        
        resources = list(service.discovered_resources.values())
        
        return [
            resource_to_response(resource)
            for resource in resources
        ]
    except Exception as e:
        logger.error(f"Failed to get discovered resources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get discovered resources: {str(e)}"
        )


@router.post("/scan", response_model=DiscoveryScanResponse)
async def start_discovery_scan(background_tasks: BackgroundTasks) -> DiscoveryScanResponse:
    """Start a new discovery scan (async)"""
    try:
        service = get_auto_discovery_service()
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Schedule discovery scan in background
        background_tasks.add_task(_run_discovery_scan, service)
        
        logger.info(f"Started discovery scan: {scan_id}")
        
        return DiscoveryScanResponse(
            scan_id=scan_id,
            status="started",
            discovered_count=len(service.discovered_resources),
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to start discovery scan: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start discovery scan: {str(e)}"
        )


async def _run_discovery_scan(service):
    """Run discovery scan in background"""
    try:
        logger.info("Starting background discovery scan...")
        discovered = await service.discover_resources()
        logger.info(f"Background discovery scan completed: {len(discovered)} resources found")
    except Exception as e:
        logger.error(f"Background discovery scan failed: {e}")


@router.post("/auto-integrate", response_model=AutoIntegrationResponse)
async def auto_integrate_resources(
    request: AutoIntegrationRequest = AutoIntegrationRequest()
) -> AutoIntegrationResponse:
    """Auto-integrate discovered resources"""
    try:
        service = get_auto_discovery_service()
        
        # Run auto-integration
        results = await service.auto_integrate_resources(
            confidence_threshold=request.confidence_threshold
        )
        
        # Convert results
        integration_results = []
        for result in results:
            integration_results.append(AutoIntegrationResult(**result))
        
        logger.info(f"Auto-integrated {len(results)} resources")
        
        return AutoIntegrationResponse(
            total_resources=len(service.discovered_resources),
            integrated_count=len(results),
            results=integration_results,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Failed to auto-integrate resources: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to auto-integrate resources: {str(e)}"
        )


@router.post("/discover-and-integrate")
async def discover_and_integrate(
    background_tasks: BackgroundTasks,
    confidence_threshold: float = 0.5
) -> Dict[str, Any]:
    """Discover and auto-integrate resources in one go (async)"""
    try:
        scan_id = f"full_scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Schedule full discovery and integration in background
        background_tasks.add_task(_run_full_discovery_and_integration, confidence_threshold)
        
        logger.info(f"Started full discovery and integration scan: {scan_id}")
        
        return {
            "scan_id": scan_id,
            "status": "started",
            "message": "Discovery and auto-integration started in background",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start discovery and integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start discovery and integration: {str(e)}"
        )


async def _run_full_discovery_and_integration(confidence_threshold: float):
    """Run full discovery and integration in background"""
    try:
        logger.info("Starting full discovery and integration...")
        
        service = get_auto_discovery_service()
        
        # Step 1: Discover resources
        logger.info("Step 1: Discovering resources...")
        discovered = await service.discover_resources()
        logger.info(f"Discovered {len(discovered)} resources")
        
        # Step 2: Auto-integrate resources
        logger.info("Step 2: Auto-integrating resources...")
        integrated = await service.auto_integrate_resources(
            confidence_threshold=confidence_threshold
        )
        logger.info(f"Auto-integrated {len(integrated)} resources")
        
        logger.info("Full discovery and integration completed")
        
    except Exception as e:
        logger.error(f"Full discovery and integration failed: {e}")


@router.get("/health")
async def discovery_health_check() -> Dict[str, Any]:
    """Discovery system health check"""
    try:
        service = get_auto_discovery_service()
        
        return {
            "status": "healthy",
            "service_initialized": True,
            "target_count": len(service.discovery_targets),
            "discovered_count": len(service.discovered_resources),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Discovery health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post("/trigger/agent-demand")
async def trigger_agent_demand_integration(
    query: str,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Trigger auto-discovery based on agent demand
    
    This endpoint simulates an agent requesting a capability
    and triggering auto-discovery to find and integrate it.
    """
    try:
        # Analyze query to determine what to look for
        capabilities_needed = _analyze_query_for_capabilities(query)
        
        # Create temporary discovery target based on query
        service = get_auto_discovery_service()
        
        target_name = f"agent_demand_{datetime.now().strftime('%H%M%S')}"
        target = DiscoveryTarget(
            name=target_name,
            target_type="semantic",
            value=query,
            description=f"Agent demand: {query}",
            priority=5  # High priority for agent demands
        )
        
        # Add temporary target
        service.discovery_targets.append(target)
        
        # Schedule discovery and integration
        background_tasks.add_task(
            _handle_agent_demand,
            service,
            target_name,
            capabilities_needed,
            query
        )
        
        logger.info(f"Triggered agent demand integration for query: {query}")
        
        return {
            "success": True,
            "message": f"Agent demand integration triggered for: {query}",
            "capabilities_needed": capabilities_needed,
            "target_name": target_name,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to trigger agent demand integration: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to trigger agent demand integration: {str(e)}"
        )


def _analyze_query_for_capabilities(query: str) -> List[str]:
    """Analyze query to determine needed capabilities"""
    query_lower = query.lower()
    
    capabilities = []
    
    # Simple keyword-based analysis
    if any(word in query_lower for word in ["code", "programming", "debug", "write code"]):
        capabilities.append("coding")
    
    if any(word in query_lower for word in ["research", "analyze", "summarize", "find information"]):
        capabilities.append("research")
    
    if any(word in query_lower for word in ["translate", "language", "中文", "english"]):
        capabilities.append("translation")
    
    if any(word in query_lower for word in ["search", "find", "look up", "google"]):
        capabilities.append("search")
    
    if any(word in query_lower for word in ["file", "document", "read", "write"]):
        capabilities.append("file_operations")
    
    if any(word in query_lower for word in ["math", "calculate", "compute", "statistics"]):
        capabilities.append("math")
    
    # If no specific capabilities detected, add generic ones
    if not capabilities:
        capabilities = ["general_assistance", "information_processing"]
    
    return capabilities


async def _handle_agent_demand(
    service,
    target_name: str,
    capabilities_needed: List[str],
    original_query: str
):
    """Handle agent demand integration in background"""
    try:
        logger.info(f"Handling agent demand for capabilities: {capabilities_needed}")
        
        # Step 1: Discover resources
        discovered = await service.discover_resources()
        logger.info(f"Discovered {len(discovered)} resources for agent demand")
        
        # Step 2: Filter resources by needed capabilities
        relevant_resources = []
        for resource in discovered:
            # Check if resource has any of the needed capabilities
            resource_capabilities = [c.lower() for c in resource.capabilities]
            needed_capabilities = [c.lower() for c in capabilities_needed]
            
            if any(needed_cap in ' '.join(resource_capabilities) 
                   for needed_cap in needed_capabilities):
                relevant_resources.append(resource)
        
        logger.info(f"Found {len(relevant_resources)} relevant resources")
        
        # Step 3: Auto-integrate relevant resources
        if relevant_resources:
            # Temporarily set high confidence threshold for agent demands
            integrated = await service.auto_integrate_resources(confidence_threshold=0.3)
            logger.info(f"Integrated {len(integrated)} resources for agent demand")
        
        # Step 4: Remove temporary target
        for i, target in enumerate(service.discovery_targets):
            if target.name == target_name:
                service.discovery_targets.pop(i)
                logger.info(f"Removed temporary target: {target_name}")
                break
        
        logger.info(f"Agent demand handling completed for: {original_query}")
        
    except Exception as e:
        logger.error(f"Agent demand handling failed: {e}")