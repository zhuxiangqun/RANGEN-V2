#!/usr/bin/env python3
"""
Auto-Discovery Service for MCP Servers and External Resources

Provides automated discovery and integration of MCP servers,
OpenAI/GitHub agents, and custom APIs based on semantic analysis
and network scanning.
"""

import asyncio
import json
import socket
import urllib.parse
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp

# Optional imports for enhanced discovery
try:
    import nmap  # Network scanning
    NMAP_AVAILABLE = True
except ImportError:
    NMAP_AVAILABLE = False
    nmap = None

try:
    from semantic_search import SemanticSearcher  # Hypothetical semantic search module
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    SemanticSearcher = None

from src.services.logging_service import get_logger
from src.services.external_integration import (
    get_external_service, 
    ExternalSourceType,
    ExternalCapability,
    MCPEndpoint
)

logger = get_logger(__name__)


@dataclass
class DiscoveryTarget:
    """Discovery target configuration"""
    name: str
    target_type: str  # network, url, semantic, predefined
    value: str  # IP range, URL, keyword, etc.
    description: str = ""
    priority: int = 1  # 1-5, higher = more important


@dataclass
class DiscoveredResource:
    """Discovered resource information"""
    resource_id: str
    name: str
    resource_type: str  # mcp_server, openai_agent, github_agent, custom_api
    endpoint: str
    protocol: str = "unknown"
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0-1.0 confidence score
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)


class AutoDiscoveryService:
    """Automatic discovery service for external resources"""
    
    def __init__(self):
        self.external_service = get_external_service()
        self.discovery_targets: List[DiscoveryTarget] = []
        self.discovered_resources: Dict[str, DiscoveredResource] = {}
        self.semantic_searcher = None  # Will be initialized if available
        self.nm = None  # Nmap scanner
        
        # Default discovery targets
        self._load_default_targets()
        
        # Initialize components
        self._initialize_components()
    
    def _load_default_targets(self):
        """Load default discovery targets"""
        # Common MCP server ports and protocols
        default_targets = [
            DiscoveryTarget(
                name="localhost_mcp",
                target_type="network",
                value="127.0.0.1",
                description="Local MCP servers",
                priority=5
            ),
            DiscoveryTarget(
                name="common_mcp_ports",
                target_type="predefined",
                value="mcp_ports",
                description="Common MCP server ports (3000-3010, 8000-8010)",
                priority=4
            ),
            DiscoveryTarget(
                name="semantic_ai_tools",
                target_type="semantic",
                value="AI assistant, MCP server, tool integration",
                description="Semantic search for AI tools and MCP servers",
                priority=3
            ),
            DiscoveryTarget(
                name="openai_ecosystem",
                target_type="url",
                value="https://platform.openai.com",
                description="OpenAI ecosystem tools and agents",
                priority=3
            ),
            DiscoveryTarget(
                name="github_ecosystem", 
                target_type="url",
                value="https://api.github.com",
                description="GitHub ecosystem tools and agents",
                priority=3
            )
        ]
        
        self.discovery_targets.extend(default_targets)
        logger.info(f"Loaded {len(default_targets)} default discovery targets")
    
    def _initialize_components(self):
        """Initialize discovery components"""
        # Initialize Nmap scanner if available
        if NMAP_AVAILABLE and nmap is not None:
            try:
                self.nm = nmap.PortScanner()
                logger.info("Nmap scanner initialized")
            except Exception as e:
                logger.warning(f"Nmap initialization failed: {e}")
                self.nm = None
        else:
            logger.warning("Nmap not available, network scanning limited")
            self.nm = None
        
        # Initialize semantic searcher if available
        if SEMANTIC_SEARCH_AVAILABLE and SemanticSearcher is not None:
            try:
                self.semantic_searcher = SemanticSearcher()
                logger.info("Semantic searcher initialized")
            except Exception as e:
                logger.warning(f"Semantic searcher initialization failed: {e}")
                self.semantic_searcher = None
        else:
            logger.warning("Semantic search not available, using basic discovery")
            self.semantic_searcher = None
    
    async def discover_resources(self) -> List[DiscoveredResource]:
        """Discover resources from all targets"""
        discovered = []
        
        logger.info(f"Starting resource discovery with {len(self.discovery_targets)} targets")
        
        # Discover from each target in parallel
        tasks = []
        for target in self.discovery_targets:
            task = self._discover_from_target(target)
            tasks.append(task)
        
        # Run discovery tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Discovery error: {result}")
                continue
            if result:
                discovered.extend(result)
        
        # Remove duplicates and update cache
        unique_resources = self._deduplicate_resources(discovered)
        
        logger.info(f"Discovered {len(unique_resources)} unique resources")
        return unique_resources
    
    async def _discover_from_target(self, target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover resources from a specific target"""
        discovered = []
        
        try:
            if target.target_type == "network":
                discovered.extend(await self._discover_network(target))
            elif target.target_type == "url":
                discovered.extend(await self._discover_url(target))
            elif target.target_type == "semantic":
                discovered.extend(await self._discover_semantic(target))
            elif target.target_type == "predefined":
                discovered.extend(await self._discover_predefined(target))
        except Exception as e:
            logger.error(f"Error discovering from target {target.name}: {e}")
        
        return discovered
    
    async def _discover_network(self, target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover resources via network scanning"""
        discovered = []
        
        if not self.nm:
            logger.warning("Network scanning not available (nmap missing)")
            return discovered
        
        try:
            # Scan common MCP ports
            ports = "3000-3010,8000-8010,8080-8090,9000-9010"
            logger.info(f"Scanning {target.value} ports {ports}")
            
            # Perform scan (this can be slow)
            scan_result = self.nm.scan(hosts=target.value, ports=ports, arguments='-sV')
            
            for host in scan_result.get('scan', {}).values():
                host_ip = host.get('addresses', {}).get('ipv4')
                if not host_ip:
                    continue
                
                for port, port_info in host.get('tcp', {}).items():
                    if port_info.get('state') == 'open':
                        service = port_info.get('name', '').lower()
                        version = port_info.get('version', '')
                        
                        # Check if this looks like an MCP server
                        if self._is_mcp_service(service, version):
                            resource = DiscoveredResource(
                                resource_id=f"mcp_{host_ip}_{port}",
                                name=f"MCP Server {host_ip}:{port}",
                                resource_type="mcp_server",
                                endpoint=f"http://{host_ip}:{port}",
                                protocol=service,
                                description=f"MCP server detected on {host_ip}:{port}",
                                capabilities=["mcp_server"],
                                confidence=0.7,
                                metadata={
                                    "host": host_ip,
                                    "port": port,
                                    "service": service,
                                    "version": version
                                }
                            )
                            discovered.append(resource)
                            logger.info(f"Discovered MCP server: {host_ip}:{port}")
        
        except Exception as e:
            logger.error(f"Network scan error: {e}")
        
        return discovered
    
    async def _discover_url(self, target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover resources via URL exploration"""
        discovered = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try to discover OpenAI agents
                if "openai" in target.value.lower():
                    discovered.extend(await self._discover_openai_agents(session, target))
                
                # Try to discover GitHub agents
                if "github" in target.value.lower():
                    discovered.extend(await self._discover_github_agents(session, target))
                
                # Try generic API discovery
                discovered.extend(await self._discover_generic_apis(session, target))
        
        except Exception as e:
            logger.error(f"URL discovery error for {target.value}: {e}")
        
        return discovered
    
    async def _discover_semantic(self, target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover resources via semantic search"""
        discovered = []
        
        if not self.semantic_searcher:
            logger.warning("Semantic search not available")
            return discovered
        
        try:
            # This is a placeholder - actual implementation would use
            # vector search, LLM analysis, or web scraping
            # For now, return some simulated discoveries
            
            simulated_resources = [
                DiscoveredResource(
                    resource_id=f"semantic_ai_tool_{i}",
                    name=f"AI Tool {i}",
                    resource_type="custom_api",
                    endpoint=f"https://api.aitool{i}.example.com",
                    protocol="https",
                    description=f"AI tool discovered via semantic search for '{target.value}'",
                    capabilities=["ai_tool", "api"],
                    confidence=0.5,
                    metadata={"discovery_method": "semantic"}
                )
                for i in range(3)  # Simulate 3 discoveries
            ]
            
            discovered.extend(simulated_resources)
            logger.info(f"Semantic discovery found {len(simulated_resources)} resources")
        
        except Exception as e:
            logger.error(f"Semantic discovery error: {e}")
        
        return discovered
    
    async def _discover_predefined(self, target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover resources from predefined lists"""
        discovered = []
        
        if target.value == "mcp_ports":
            # Check common MCP server ports on localhost
            common_ports = [3000, 3001, 8000, 8001, 8080, 8081, 9000, 9001]
            
            for port in common_ports:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', port))
                    sock.close()
                    
                    if result == 0:
                        resource = DiscoveredResource(
                            resource_id=f"local_mcp_{port}",
                            name=f"Local MCP Server on port {port}",
                            resource_type="mcp_server",
                            endpoint=f"http://127.0.0.1:{port}",
                            protocol="http",
                            description=f"MCP server detected on localhost:{port}",
                            capabilities=["mcp_server"],
                            confidence=0.6,
                            metadata={"port": port, "host": "127.0.0.1"}
                        )
                        discovered.append(resource)
                        logger.info(f"Discovered local MCP server on port {port}")
                
                except Exception as e:
                    continue
        
        return discovered
    
    async def _discover_openai_agents(self, session: aiohttp.ClientSession, 
                                     target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover OpenAI GPTs agents"""
        discovered = []
        
        # This is a placeholder - actual implementation would use
        # OpenAI API or web scraping to discover GPTs
        
        simulated_agents = [
            DiscoveredResource(
                resource_id="openai_gpt_coding_assistant",
                name="OpenAI GPT Coding Assistant",
                resource_type="openai_agent",
                endpoint="https://chat.openai.com/g/g-abc123-coding-assistant",
                protocol="openai",
                description="OpenAI GPT specialized in coding assistance",
                capabilities=["coding", "debugging", "code_review"],
                confidence=0.8,
                metadata={"platform": "openai", "type": "gpt"}
            ),
            DiscoveredResource(
                resource_id="openai_gpt_research_assistant",
                name="OpenAI GPT Research Assistant",
                resource_type="openai_agent",
                endpoint="https://chat.openai.com/g/g-def456-research-assistant",
                protocol="openai",
                description="OpenAI GPT specialized in research and analysis",
                capabilities=["research", "analysis", "summarization"],
                confidence=0.8,
                metadata={"platform": "openai", "type": "gpt"}
            )
        ]
        
        discovered.extend(simulated_agents)
        logger.info(f"Discovered {len(simulated_agents)} OpenAI agents")
        
        return discovered
    
    async def _discover_github_agents(self, session: aiohttp.ClientSession,
                                     target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover GitHub Copilot agents"""
        discovered = []
        
        # This is a placeholder - actual implementation would use
        # GitHub API to discover Copilot integrations
        
        simulated_agents = [
            DiscoveredResource(
                resource_id="github_copilot_chat",
                name="GitHub Copilot Chat",
                resource_type="github_agent",
                endpoint="https://github.com/features/copilot",
                protocol="github",
                description="GitHub Copilot AI assistant for developers",
                capabilities=["code_completion", "code_explanation", "debugging"],
                confidence=0.9,
                metadata={"platform": "github", "type": "copilot"}
            )
        ]
        
        discovered.extend(simulated_agents)
        logger.info(f"Discovered {len(simulated_agents)} GitHub agents")
        
        return discovered
    
    async def _discover_generic_apis(self, session: aiohttp.ClientSession,
                                    target: DiscoveryTarget) -> List[DiscoveredResource]:
        """Discover generic APIs"""
        discovered = []
        
        try:
            # Try to fetch the URL and analyze response
            async with session.get(target.value, timeout=5) as response:
                if response.status == 200:
                    content_type = response.headers.get('Content-Type', '')
                    
                    # Check if it looks like an API
                    if 'application/json' in content_type or 'api' in target.value.lower():
                        resource = DiscoveredResource(
                            resource_id=f"api_{hash(target.value)}",
                            name=f"API at {target.value}",
                            resource_type="custom_api",
                            endpoint=target.value,
                            protocol="https",
                            description=f"API discovered at {target.value}",
                            capabilities=["api"],
                            confidence=0.5,
                            metadata={
                                "url": target.value,
                                "content_type": content_type,
                                "status": response.status
                            }
                        )
                        discovered.append(resource)
                        logger.info(f"Discovered API at {target.value}")
        
        except Exception as e:
            # Ignore connection errors
            pass
        
        return discovered
    
    def _is_mcp_service(self, service: str, version: str) -> bool:
        """Check if a service looks like an MCP server"""
        mcp_indicators = [
            'mcp', 'model-context', 'llm', 'ai', 'assistant',
            'openai', 'anthropic', 'claude', 'chatgpt'
        ]
        
        service_lower = service.lower()
        version_lower = version.lower()
        
        # Check service name and version for MCP indicators
        for indicator in mcp_indicators:
            if indicator in service_lower or indicator in version_lower:
                return True
        
        # Check for common MCP server patterns
        if service_lower in ['http', 'https', 'tcp'] and 'api' in version_lower:
            return True
        
        return False
    
    def _deduplicate_resources(self, resources: List[DiscoveredResource]) -> List[DiscoveredResource]:
        """Remove duplicate resources and update cache"""
        unique_resources = []
        seen_endpoints = set()
        
        for resource in resources:
            # Use endpoint as unique identifier
            if resource.endpoint not in seen_endpoints:
                seen_endpoints.add(resource.endpoint)
                unique_resources.append(resource)
                
                # Update cache
                self.discovered_resources[resource.resource_id] = resource
        
        return unique_resources
    
    async def auto_integrate_resources(self, confidence_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Automatically integrate discovered resources above confidence threshold"""
        integrated = []
        
        # Get all discovered resources
        resources = list(self.discovered_resources.values())
        
        logger.info(f"Attempting auto-integration of {len(resources)} discovered resources")
        
        for resource in resources:
            if resource.confidence < confidence_threshold:
                continue
            
            try:
                integration_result = await self._integrate_resource(resource)
                if integration_result:
                    integrated.append(integration_result)
                    logger.info(f"Auto-integrated resource: {resource.name}")
            except Exception as e:
                logger.error(f"Failed to auto-integrate {resource.name}: {e}")
        
        return integrated
    
    async def _integrate_resource(self, resource: DiscoveredResource) -> Optional[Dict[str, Any]]:
        """Integrate a discovered resource into the system"""
        
        if resource.resource_type == "mcp_server":
            # Add as MCP endpoint
            endpoint = self.external_service.add_mcp_endpoint(
                name=resource.name,
                url=resource.endpoint,
                transport="http",
                server_type="external"
            )
            
            # Try to connect
            success = self.external_service.connect_mcp_endpoint(resource.name)
            
            return {
                "resource_id": resource.resource_id,
                "name": resource.name,
                "type": "mcp_server",
                "endpoint": resource.endpoint,
                "integrated": success,
                "timestamp": datetime.now().isoformat()
            }
        
        elif resource.resource_type == "openai_agent":
            # Import as OpenAI agent
            capability = self.external_service.import_openai_agent(
                agent_id=resource.resource_id,
                name=resource.name,
                description=resource.description
            )
            
            return {
                "resource_id": resource.resource_id,
                "name": resource.name,
                "type": "openai_agent",
                "integrated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        elif resource.resource_type == "github_agent":
            # Import as GitHub agent
            capability = self.external_service.import_github_copilot(
                agent_id=resource.resource_id,
                name=resource.name,
                description=resource.description
            )
            
            return {
                "resource_id": resource.resource_id,
                "name": resource.name,
                "type": "github_agent",
                "integrated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        elif resource.resource_type == "custom_api":
            # Add as custom API
            capability = self.external_service.add_custom_api(
                name=resource.name,
                base_url=resource.endpoint,
                description=resource.description
            )
            
            return {
                "resource_id": resource.resource_id,
                "name": resource.name,
                "type": "custom_api",
                "endpoint": resource.endpoint,
                "integrated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        return None
    
    def get_discovery_status(self) -> Dict[str, Any]:
        """Get discovery service status"""
        return {
            "status": "active",
            "target_count": len(self.discovery_targets),
            "discovered_count": len(self.discovered_resources),
            "last_discovery": max(
                [r.discovered_at for r in self.discovered_resources.values()] 
                or [datetime.now()]
            ).isoformat(),
            "discovery_targets": [
                {
                    "name": t.name,
                    "type": t.target_type,
                    "value": t.value,
                    "priority": t.priority
                }
                for t in self.discovery_targets
            ]
        }


# Global instance
_auto_discovery_service: Optional[AutoDiscoveryService] = None


def get_auto_discovery_service() -> AutoDiscoveryService:
    """Get auto-discovery service instance"""
    global _auto_discovery_service
    if _auto_discovery_service is None:
        _auto_discovery_service = AutoDiscoveryService()
    return _auto_discovery_service